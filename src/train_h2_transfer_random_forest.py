import sys
import time
import random
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np
import pandas as pd
import joblib
from PIL import Image
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, matthews_corrcoef, balanced_accuracy_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import (
    TRAIN_DIR, TEST_DIR, MODELS_DIR, MODELOS_DIR,
    IMG_SIZE, BATCH_SIZE, SEED, CLASS_NAMES,
    TRANSFER_EXTRACTOR_PATH, TRANSFER_RF_PATH,
)
from preprocesamiento_aumento import pipeline_preprocesamiento, pipeline_aumento
from evaluacion_visual import save_confusion_matrix, save_roc_curves
from mantenedor import TARGET_TRAIN_SAMPLES_PER_CLASS

NUM_CLASSES = len(CLASS_NAMES)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def cargar_test_sin_aumento(split_dir: Path):
    X_list, y_list = [], []
    for idx, clase in enumerate(CLASS_NAMES):
        clase_dir = split_dir / clase
        if not clase_dir.exists():
            continue
        for img_path in sorted(clase_dir.iterdir()):
            if not img_path.is_file() or img_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            try:
                pil_img = Image.open(img_path).convert("RGB")
                arr = pipeline_preprocesamiento(pil_img)
                feats = _pil_to_mobilenet_input(arr)
                X_list.append(feats)
                y_list.append(idx)
            except Exception as e:
                print(f"\n    ⚠️  Error en {img_path.name}: {e}")
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    return X, y


def cargar_train_balanceado(split_dir: Path):
    target = TARGET_TRAIN_SAMPLES_PER_CLASS
    X_list, y_list = [], []
    resumen = []
    random.seed(SEED)
    np.random.seed(SEED)

    print("=" * 49)
    print(f"  {'Clase':<18} {'Reales':>8} {'Aumentos':>9} {'Total':>6}")
    print(f"  {'─'*47}")

    for idx, clase in enumerate(CLASS_NAMES):
        clase_dir = split_dir / clase
        if not clase_dir.exists():
            continue
        rutas = sorted([p for p in clase_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS])
        n_reales = len(rutas)
        n_faltan = max(0, target - n_reales)

        for ruta in rutas:
            pil_img = Image.open(ruta).convert("RGB")
            arr = pipeline_preprocesamiento(pil_img)
            feats = _pil_to_mobilenet_input(arr)
            X_list.append(feats)
            y_list.append(idx)

        if n_faltan > 0:
            rutas_dup = (rutas * (n_faltan // n_reales + 2))[:n_faltan]
            random.shuffle(rutas_dup)
            for ruta in rutas_dup:
                pil_img = Image.open(ruta).convert("RGB")
                arr_aug = pipeline_aumento(pil_img)
                feats = _pil_to_mobilenet_input(arr_aug)
                X_list.append(feats)
                y_list.append(idx)

        resumen.append((clase, n_reales, n_faltan, target))
        print(f"  {clase:<18} {n_reales:>8} {n_faltan:>9} {target:>6}")

    total_reales = sum(r[1] for r in resumen)
    total_aumentadas = sum(r[2] for r in resumen)
    total_efectivo = total_reales + total_aumentadas
    print(f"  {'─'*47}")
    print(f"  {'TOTAL':<18} {total_reales:>8} {total_aumentadas:>9} {total_efectivo:>6}")
    print()

    perm = np.random.permutation(len(y_list))
    X_list = [X_list[i] for i in perm]
    y_list = [y_list[i] for i in perm]
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    return X, y


def _pil_to_mobilenet_input(arr: np.ndarray) -> np.ndarray:
    arr_255 = (arr * 255).clip(0, 255).astype(np.float32)
    return preprocess_input(arr_255)


def crear_extractor_mobilenet():
    base_model = MobileNetV2(input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet", pooling=None)
    base_model.trainable = False
    inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
    x = base_model(inputs, training=False)
    outputs = layers.GlobalAveragePooling2D()(x)
    extractor = tf.keras.Model(inputs=inputs, outputs=outputs, name="transfer_extractor")
    return extractor





def extraer_embeddings_batch(extractor, X, batch_size=32):
    embeddings = []
    for i in range(0, len(X), batch_size):
        batch = X[i: i + batch_size]
        emb = extractor(batch, training=False).numpy()
        embeddings.append(emb)
    return np.concatenate(embeddings, axis=0)


def mostrar_metricas(y_test, y_pred, nombre_modelo="Transfer + RF", tiempo_entrenamiento=0, tiempo_inferencia=0):
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    mcc = matthews_corrcoef(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)

    print("\n" + "=" * 60)
    print(f"  📊 RESULTADOS — {nombre_modelo}")
    print("=" * 60)
    print(f"  Accuracy          : {acc:.4f}  ({acc:.2%})")
    print(f"  Balanced Accuracy : {bal_acc:.4f}")
    print(f"  Precision         : {prec:.4f}")
    print(f"  Recall            : {rec:.4f}")
    print(f"  F1-Score          : {f1:.4f}")
    print(f"  MCC               : {mcc:.4f}")
    print(f"  Tiempo entrenamiento: {tiempo_entrenamiento:.2f}s")
    print(f"  Tiempo inferencia   : {tiempo_inferencia:.2f}ms")
    print("\n  Reporte por clase:")
    print(classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0))
    print("  Matriz de Confusión:")
    header = "         " + "  ".join(f"{c[:8]:>8}" for c in CLASS_NAMES)
    print(header)
    for i, row in enumerate(cm):
        row_str = "  ".join(f"{v:>8}" for v in row)
        print(f"  {CLASS_NAMES[i][:8]:>8}  {row_str}")
    print("=" * 60)

    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    reporte = classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0, output_dict=True)
    reporte_df = pd.DataFrame(reporte).transpose()
    ruta_reporte = MODELOS_DIR / "reporte_clasificacion_h2_transfer_rf.csv"
    reporte_df.to_csv(ruta_reporte)
    print(f"  Reporte por clase guardado: {ruta_reporte}")

    cm_df = pd.DataFrame(cm, index=CLASS_NAMES, columns=CLASS_NAMES)
    cm_df.to_csv(MODELOS_DIR / "confusion_h2_transfer_rf.csv")

    resumen = pd.DataFrame([{
        "modelo": nombre_modelo, "accuracy": round(acc, 4), "balanced_accuracy": round(bal_acc, 4),
        "precision": round(prec, 4), "recall": round(rec, 4), "f1_score": round(f1, 4),
        "mcc": round(mcc, 4), "tiempo_entrenamiento_s": round(tiempo_entrenamiento, 2),
        "tiempo_inferencia_ms": round(tiempo_inferencia, 2)
    }])
    ruta_resumen = MODELOS_DIR / "resultados_h2_transfer_rf.csv"
    resumen.to_csv(ruta_resumen, index=False)
    print(f"  Métricas generales guardadas: {ruta_resumen}")
    return acc, prec, rec, f1, mcc, bal_acc, cm


def main():
    print("=" * 60)
    print("  H2 — Entrenamiento Transfer Learning + RF — VineGuard AI")
    print("=" * 60)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tf.random.set_seed(SEED)
    start_total = time.time()

    print("\n🔄 Construyendo extractor MobileNetV2 (ImageNet)...")
    extractor = crear_extractor_mobilenet()
    print(f"   Embedding dims: {extractor.output_shape[-1]}")

    print("\n🔍 Cargando TRAIN con balanceo a 1500/clase...")
    X_train_imgs, y_train = cargar_train_balanceado(TRAIN_DIR)
    print(f"   Forma: {X_train_imgs.shape}")

    print("\n🔍 Cargando TEST (sin aumento)...")
    X_test_imgs, y_test = cargar_test_sin_aumento(TEST_DIR)
    print(f"   Forma: {X_test_imgs.shape}")

    print("\n📋 Preprocesamiento:")
    print("   - Entrenamiento: RGB + redimensionamiento + normalización + aumento dinámico (PIL) balanceado")
    print(f"   - Entrenamiento balanceado a {TARGET_TRAIN_SAMPLES_PER_CLASS} muestras/clase (oversampling con reemplazo)")
    print("   - Prueba:        RGB + redimensionamiento + normalización + preprocess_input (solo imágenes reales)")
    print("   - Imágenes aumentadas guardadas físicamente: No")

    print("\n⚙️  Extrayendo embeddings...")
    X_train = extraer_embeddings_batch(extractor, X_train_imgs, batch_size=BATCH_SIZE)
    X_test = extraer_embeddings_batch(extractor, X_test_imgs, batch_size=BATCH_SIZE)
    print(f"   Embeddings train: {X_train.shape}, test: {X_test.shape}")

    del X_train_imgs, X_test_imgs

    extractor.save(str(TRANSFER_EXTRACTOR_PATH))
    print(f"\n💾 Extractor guardado en: {TRANSFER_EXTRACTOR_PATH}")

    print("\n🚀 Entrenando Random Forest sobre embeddings MobileNetV2...")
    start_train = time.time()
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=None, class_weight="balanced", n_jobs=-1, random_state=SEED,
    )
    rf.fit(X_train, y_train)
    tiempo_entrenamiento = time.time() - start_total
    print("   ✅ Random Forest entrenado.")

    start_infer = time.time()
    y_pred = rf.predict(X_test)
    y_score = rf.predict_proba(X_test)
    tiempo_inferencia = (time.time() - start_infer) / len(y_pred) * 1000

    mostrar_metricas(y_test, y_pred, "H2 — Transfer Learning (MobileNetV2) + RF", tiempo_entrenamiento, tiempo_inferencia)

    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    save_confusion_matrix(y_test, y_pred, CLASS_NAMES, MODELOS_DIR / "confusion_h2_transfer_rf.png")
    save_roc_curves(y_test, y_score, CLASS_NAMES, MODELOS_DIR / "roc_h2_transfer_rf.png")

    joblib.dump(rf, TRANSFER_RF_PATH)
    print(f"\n💾 Random Forest guardado en: {TRANSFER_RF_PATH}")
    print("\n✅ Proceso completado.")


if __name__ == "__main__":
    main()
