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
from pathlib import Path

import numpy as np
import joblib
from PIL import Image

try:
    from skimage.feature import local_binary_pattern
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False
    print("⚠️  scikit-image no encontrado. Se omitirán las features LBP.")

from sklearn.preprocessing import StandardScaler

# ─── Configuración ───────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import TRAIN_DIR, TEST_DIR, IMG_SIZE, CLASS_NAMES, SCALER_PATH, MODELS_DIR

# Parámetros LBP
LBP_RADIUS = 3
LBP_N_POINTS = 24       # 8 * LBP_RADIUS
LBP_METHOD = "uniform"
LBP_N_BINS = LBP_N_POINTS + 2   # bins para modo uniform

# Parámetros histograma de color (HSV)
HIST_BINS = 64


def extraer_caracteristicas_imagen(img_path: Path) -> np.ndarray:
    """
    Extrae el vector de características de una imagen.

    Returns
    -------
    np.ndarray de forma (n_features,)
    """
    # Cargar y redimensionar
    img = Image.open(img_path).convert("RGB").resize(IMG_SIZE)
    img_array = np.array(img, dtype=np.float32)

    features = []

    # ── 1. Estadísticas por canal RGB (media, std, varianza) ─────────────────
    for canal in range(3):
        ch = img_array[:, :, canal]
        features.extend([ch.mean(), ch.std(), ch.var()])

    # ── 2. Histograma de color en espacio HSV ──────────────────────────────
    img_hsv = img.convert("HSV") if hasattr(img, "convert") else img
    try:
        img_hsv = np.array(Image.fromarray(img_array.astype(np.uint8)).convert("HSV"),
                           dtype=np.float32)
        for canal in range(3):
            hist, _ = np.histogram(img_hsv[:, :, canal],
                                   bins=HIST_BINS, range=(0, 256))
            hist = hist.astype(np.float32)
            total = hist.sum()
            if total > 0:
                hist /= total           # normalizar a distribución
            features.extend(hist.tolist())
    except Exception:
        # Fallback: histograma RGB si HSV falla
        for canal in range(3):
            hist, _ = np.histogram(img_array[:, :, canal],
                                   bins=HIST_BINS, range=(0, 256))
            hist = hist.astype(np.float32)
            total = hist.sum()
            if total > 0:
                hist /= total
            features.extend(hist.tolist())

    # ── 3. LBP de textura ──────────────────────────────────────────────────
    if HAS_SKIMAGE:
        img_gray = np.array(img.convert("L"), dtype=np.uint8)
        lbp = local_binary_pattern(img_gray, LBP_N_POINTS, LBP_RADIUS,
                                   method=LBP_METHOD)
        lbp_hist, _ = np.histogram(lbp.ravel(), bins=LBP_N_BINS,
                                   range=(0, LBP_N_BINS))
        lbp_hist = lbp_hist.astype(np.float32)
        total = lbp_hist.sum()
        if total > 0:
            lbp_hist /= total
        features.extend(lbp_hist.tolist())

    return np.array(features, dtype=np.float32)


def cargar_split(split_dir: Path):
    """
    Carga imágenes de un split (train o test) y extrae características.

    Returns
    -------
    X : np.ndarray, shape (n_samples, n_features)
    y : np.ndarray, shape (n_samples,) — índice de clase
    """
    X, y = [], []

    for idx, clase in enumerate(CLASS_NAMES):
        clase_dir = split_dir / clase
        if not clase_dir.exists():
            print(f"  ⚠️  Carpeta no encontrada: {clase_dir}")
            continue

        imagenes = sorted([
            p for p in clase_dir.iterdir()
            if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
        ])

        print(f"  📂 {clase}: {len(imagenes)} imágenes", end="", flush=True)

        for img_path in imagenes:
            try:
                feats = extraer_caracteristicas_imagen(img_path)
                X.append(feats)
                y.append(idx)
            except Exception as e:
                print(f"\n    ⚠️  Error en {img_path.name}: {e}")

        print(f" ✓")

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int32)


def load_features(fit_scaler: bool = True):
    """
    Extrae características de train y test, normaliza con StandardScaler
    y guarda el scaler en models/scaler.pkl.

    Parameters
    ----------
    fit_scaler : bool
        Si True, ajusta y guarda el scaler con los datos de train.
        Si False, carga el scaler existente desde disco.

    Returns
    -------
    X_train, y_train, X_test, y_test
    """
    print("\n🔍 Extrayendo características de TRAIN...")
    X_train, y_train = cargar_split(TRAIN_DIR)

    print("\n🔍 Extrayendo características de TEST...")
    X_test, y_test = cargar_split(TEST_DIR)

    print(f"\n📊 Dimensiones:")
    print(f"   X_train: {X_train.shape}")
    print(f"   X_test:  {X_test.shape}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if fit_scaler:
        print("\n⚙️  Ajustando StandardScaler con datos de train...")
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
        joblib.dump(scaler, SCALER_PATH)
        print(f"   ✅ Scaler guardado en: {SCALER_PATH}")
    else:
        if SCALER_PATH.exists():
            print(f"\n⚙️  Cargando scaler desde: {SCALER_PATH}")
            scaler = joblib.load(SCALER_PATH)
            X_train = scaler.transform(X_train)
            X_test = scaler.transform(X_test)
        else:
            print("⚠️  No se encontró scaler.pkl. Datos no normalizados.")

    return X_train, y_train, X_test, y_test


def extract_single_image_features(img_path_or_pil) -> np.ndarray:
    """
    Extrae y normaliza características de una sola imagen.
    Carga el scaler desde models/scaler.pkl.

    Parameters
    ----------
    img_path_or_pil : str | Path | PIL.Image

    Returns
    -------
    np.ndarray de forma (1, n_features)
    """
    if isinstance(img_path_or_pil, (str, Path)):
        img_path = Path(img_path_or_pil)
        feats = extraer_caracteristicas_imagen(img_path)
    else:
        # PIL Image
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        img_path_or_pil.save(tmp_path)
        feats = extraer_caracteristicas_imagen(Path(tmp_path))
        os.unlink(tmp_path)

    feats = feats.reshape(1, -1)

    if SCALER_PATH.exists():
        scaler = joblib.load(SCALER_PATH)
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
