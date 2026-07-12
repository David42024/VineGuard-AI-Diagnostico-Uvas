"""
extract_features.py
───────────────────
Extrae características manuales de imágenes para modelos clásicos (SVM, RF, KNN).

Características extraídas por imagen:
  • Histograma de color HSV  → 64 bins × 3 canales = 192 features
  • LBP (Local Binary Pattern) → 26 features (radio=3, n_points=24)
  • Estadísticas por canal RGB → media, std, varianza × 3 = 9 features
  Total: ~227 features por imagen

Uso independiente:
  python src/extract_features.py

Como módulo (importar desde los scripts de entrenamiento):
  from extract_features import load_features
  X_train, y_train, X_test, y_test = load_features()
"""

import sys
import random
from pathlib import Path

import numpy as np
import joblib
from PIL import Image

try:
    from skimage.feature import local_binary_pattern
except ImportError as e:
    raise ImportError(
        "scikit-image es requerido para extraer las features LBP. "
        "El pipeline de entrenamiento y el scaler asumen 227 features por "
        "imagen (192 color + 26 LBP + 9 estadísticas); omitir LBP produciría "
        "un vector de 201 features, incompatible con los modelos ya "
        "entrenados. Instala con: pip install scikit-image"
    ) from e

from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import TRAIN_DIR, TEST_DIR, IMG_SIZE, CLASS_NAMES, SCALER_PATH, SVM_SCALER_PATH, KNN_SCALER_PATH, MODELS_DIR, TARGET_TRAIN_SAMPLES_PER_CLASS
from preprocesamiento_aumento import pipeline_preprocesamiento, pipeline_aumento

LBP_RADIUS = 3
LBP_N_POINTS = 24
LBP_METHOD = "uniform"
LBP_N_BINS = LBP_N_POINTS + 2
HIST_BINS = 64

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def extraer_caracteristicas_desde_array(img_array: np.ndarray) -> np.ndarray:
    img_uint8 = (img_array * 255).clip(0, 255).astype(np.uint8)
    pil_img = Image.fromarray(img_uint8)
    img_255 = np.array(pil_img, dtype=np.float32)
    features = []
    for canal in range(3):
        ch = img_255[:, :, canal]
        features.extend([ch.mean(), ch.std(), ch.var()])
    try:
        img_hsv = np.array(pil_img.convert("HSV"), dtype=np.float32)
        for canal in range(3):
            hist, _ = np.histogram(img_hsv[:, :, canal], bins=HIST_BINS, range=(0, 256))
            hist = hist.astype(np.float32)
            total = hist.sum()
            if total > 0:
                hist /= total
            features.extend(hist.tolist())
    except Exception:
        for canal in range(3):
            hist, _ = np.histogram(img_255[:, :, canal], bins=HIST_BINS, range=(0, 256))
            hist = hist.astype(np.float32)
            total = hist.sum()
            if total > 0:
                hist /= total
            features.extend(hist.tolist())
    img_gray = np.array(pil_img.convert("L"), dtype=np.uint8)
    lbp = local_binary_pattern(img_gray, LBP_N_POINTS, LBP_RADIUS, method=LBP_METHOD)
    lbp_hist, _ = np.histogram(lbp.ravel(), bins=LBP_N_BINS, range=(0, LBP_N_BINS))
    lbp_hist = lbp_hist.astype(np.float32)
    total = lbp_hist.sum()
    if total > 0:
        lbp_hist /= total
    features.extend(lbp_hist.tolist())

    assert len(features) == 227, \
        f"Se esperaban 227 features, se obtuvieron {len(features)}. Revisa el pipeline de extracción."

    return np.array(features, dtype=np.float32)


def extraer_caracteristicas_imagen(img_path: Path) -> np.ndarray:
    with Image.open(img_path) as img:
        arr = pipeline_preprocesamiento(img)
    return extraer_caracteristicas_desde_array(arr)


def _obtener_rutas_por_clase(split_dir: Path):
    rutas_por_clase = {}
    for idx, clase in enumerate(CLASS_NAMES):
        clase_dir = split_dir / clase
        if not clase_dir.exists():
            continue
        rutas = sorted([p for p in clase_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS])
        rutas_por_clase[clase] = {"idx": idx, "rutas": rutas}
    return rutas_por_clase


def _cargar_test_sin_aumento() -> tuple:
    rutas_test = _obtener_rutas_por_clase(TEST_DIR)
    X_list, y_list, filenames_list = [], [], []
    for clase in CLASS_NAMES:
        info = rutas_test.get(clase)
        if info is None:
            continue
        idx = info["idx"]
        for ruta in info["rutas"]:
            feats = extraer_caracteristicas_imagen(ruta)
            X_list.append(feats)
            y_list.append(idx)
            filenames_list.append(ruta.name)
    X_test = np.array(X_list, dtype=np.float32)
    y_test = np.array(y_list, dtype=np.int32)
    filenames_test = np.array(filenames_list, dtype=str)
    return X_test, y_test, filenames_test


def cargar_balanceado() -> tuple:
    random.seed(42)
    np.random.seed(42)

    rutas_train = _obtener_rutas_por_clase(TRAIN_DIR)
    target = TARGET_TRAIN_SAMPLES_PER_CLASS
    X_train_list, y_train_list = [], []
    resumen = []

    print("=" * 60)
    print("  BALANCEO DINÁMICO DE ENTRENAMIENTO")
    print("=" * 60)
    print(f"  {'Clase':<18} {'Reales':>8} {'Aumentadas':>10} {'Total efectivo':>14}")
    print(f"  {'─'*50}")

    for clase in CLASS_NAMES:
        info = rutas_train.get(clase)
        if info is None:
            continue
        idx = info["idx"]
        rutas = info["rutas"]
        n_reales = len(rutas)
        if n_reales == 0:
            raise ValueError(f"La clase {clase} no contiene imágenes de entrenamiento.")

        if n_reales > target:
            rutas_usar = random.sample(rutas, target)
            n_faltan = 0
        else:
            rutas_usar = rutas
            n_faltan = target - n_reales

        for ruta in rutas_usar:
            with Image.open(ruta) as img:
                arr = pipeline_preprocesamiento(img)
            feats = extraer_caracteristicas_desde_array(arr)
            X_train_list.append(feats)
            y_train_list.append(idx)

        if n_faltan > 0:
            rutas_dup = (rutas * (n_faltan // n_reales + 2))[:n_faltan]
            random.shuffle(rutas_dup)
            for ruta in rutas_dup:
                with Image.open(ruta) as img:
                    arr_aug = pipeline_aumento(img)
                feats = extraer_caracteristicas_desde_array(arr_aug)
                X_train_list.append(feats)
                y_train_list.append(idx)

        n_usadas_reales = len(rutas_usar)
        resumen.append((clase, n_usadas_reales, n_faltan, target))
        print(f"  {clase:<18} {n_usadas_reales:>8} {n_faltan:>10} {target:>14}")

    total_reales = sum(r[1] for r in resumen)
    total_aumentadas = sum(r[2] for r in resumen)
    total_efectivo = total_reales + total_aumentadas

    print(f"  {'─'*50}")
    print(f"  {'TOTAL':<18} {total_reales:>8} {total_aumentadas:>10} {total_efectivo:>14}")
    print()

    X_train = np.array(X_train_list, dtype=np.float32)
    y_train = np.array(y_train_list, dtype=np.int32)
    perm = np.random.permutation(len(y_train))
    X_train, y_train = X_train[perm], y_train[perm]

    print("🔍 Cargando TEST (solo imágenes reales, sin aumento)...")
    X_test, y_test, filenames_test = _cargar_test_sin_aumento()

    print(f"\n📊 Dimensiones:")
    print(f"   X_train: {X_train.shape}")
    print(f"   X_test:  {X_test.shape}")

    print(f"\n📋 Resumen de preprocesamiento:")
    print(f"   - Entrenamiento: RGB + redimensionamiento + normalización + aumento dinámico")
    print(f"   - Prueba:       RGB + redimensionamiento + normalización")
    print(f"   - Imágenes aumentadas guardadas físicamente: No")
    print(f"   - Aumento aplicado en TEST: No")
    print(f"   - Total efectivo entrenamiento: {total_efectivo} muestras ({target}/clase)")

    resumen_dict = {
        "detalle": resumen,
        "total_reales": total_reales,
        "total_aumentadas": total_aumentadas,
        "total_efectivo": total_efectivo,
    }

    return X_train, y_train, X_test, y_test, filenames_test, resumen_dict


def load_features(fit_scaler: bool = True, augment_train: bool = True, apply_scaler: bool = True, scaler_path: Path = SCALER_PATH):
    if augment_train:
        X_train, y_train, X_test, y_test, filenames_test, _ = cargar_balanceado()
        from collections import Counter
        conteos = Counter(y_train)
        for i, cls in enumerate(CLASS_NAMES):
            assert conteos[i] == TARGET_TRAIN_SAMPLES_PER_CLASS, \
                f"{cls} tiene {conteos[i]} muestras, se esperaban {TARGET_TRAIN_SAMPLES_PER_CLASS}"
        assert len(np.unique(y_train)) == len(CLASS_NAMES)
        print("   ✅ Validaciones: todas las clases balanceadas")
        print("   ✅ Test sin aumento — solo preprocesamiento básico")
    else:
        print("🔍 Cargando TRAIN (sin aumento)...")
        rutas_train = _obtener_rutas_por_clase(TRAIN_DIR)
        X_train_list, y_train_list = [], []
        for clase in CLASS_NAMES:
            info = rutas_train.get(clase)
            if info is None:
                continue
            idx = info["idx"]
            for ruta in info["rutas"]:
                feats = extraer_caracteristicas_imagen(ruta)
                X_train_list.append(feats)
                y_train_list.append(idx)
        X_train = np.array(X_train_list, dtype=np.float32)
        y_train = np.array(y_train_list, dtype=np.int32)
        print(f"   Train: {X_train.shape}")
        print("🔍 Cargando TEST (sin aumento)...")
        X_test, y_test, filenames_test = _cargar_test_sin_aumento()
        print(f"   Test: {X_test.shape}")
        print("   ℹ️  Train cargado con su distribución original, sin balanceo")

    assert len(np.unique(y_train)) == len(CLASS_NAMES), \
        "No se encontraron todas las clases en entrenamiento."

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if apply_scaler:
        if fit_scaler:
            print(f"\n⚙️  Ajustando StandardScaler con datos de train...")
            scaler = StandardScaler()
            X_train = scaler.fit_transform(X_train)
            X_test = scaler.transform(X_test)
            joblib.dump(scaler, scaler_path)
            print(f"   ✅ Scaler guardado en: {scaler_path}")
        else:
            if scaler_path.exists():
                print(f"\n⚙️  Cargando scaler desde: {scaler_path}")
                scaler = joblib.load(scaler_path)
                X_train = scaler.transform(X_train)
                X_test = scaler.transform(X_test)
            else:
                print("⚠️  No se encontró scaler.pkl. Datos no estandarizados.")

    return X_train, y_train, X_test, y_test, filenames_test


def extract_single_image_features(img_path_or_pil, apply_scaler: bool = True, scaler_path: Path = SCALER_PATH) -> np.ndarray:
    if isinstance(img_path_or_pil, (str, Path)):
        feats = extraer_caracteristicas_imagen(Path(img_path_or_pil))
    else:
        arr = pipeline_preprocesamiento(img_path_or_pil)
        feats = extraer_caracteristicas_desde_array(arr)
    feats = feats.reshape(1, -1)
    if apply_scaler:
        if not scaler_path.exists():
            raise FileNotFoundError(f"No se encontró el scaler requerido: {scaler_path}")
        scaler = joblib.load(scaler_path)
        feats = scaler.transform(feats)
    return feats


if __name__ == "__main__":
    print("=" * 60)
    print("  Extracción de Características — VineGuard AI")
    print("=" * 60)
    X_train, y_train, X_test, y_test = load_features(fit_scaler=True)
    print(f"\n✅ Extracción completada.")
    print(f"   Train: {X_train.shape[0]} muestras, {X_train.shape[1]} features")
    print(f"   Test:  {X_test.shape[0]} muestras")
