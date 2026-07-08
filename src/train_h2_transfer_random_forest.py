import sys
import time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np
import pandas as pd
import joblib
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
from evaluacion_visual import save_confusion_matrix, save_roc_curves

NUM_CLASSES = len(CLASS_NAMES)


def crear_extractor_mobilenet():
    base_model = MobileNetV2(input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet", pooling=None)
    base_model.trainable = False
    inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
    x = base_model(inputs, training=False)
    outputs = layers.GlobalAveragePooling2D()(x)
    extractor = tf.keras.Model(inputs=inputs, outputs=outputs, name="transfer_extractor")
    return extractor


def cargar_imagenes_como_array(split_dir: Path):
    X_list, y_list = [], []
    for idx, clase in enumerate(CLASS_NAMES):
        clase_dir = split_dir / clase
        if not clase_dir.exists():
            continue
        imagenes = sorted([p for p in clase_dir.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}])
        print(f"  📂 {clase}: {len(imagenes)} imágenes", end="", flush=True)
        for img_path in imagenes:
            try:
                img = tf.keras.utils.load_img(img_path, target_size=IMG_SIZE)
                img_array = tf.keras.utils.img_to_array(img)
                img_array = preprocess_input(img_array)
                X_list.append(img_array)
                y_list.append(idx)
            except Exception as e:
                print(f"\n    ⚠️  Error en {img_path.name}: {e}")
        print(" ✓")
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    return X, y


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
    cm_df = pd.DataFrame(cm, index=CLASS_NAMES, columns=CLASS_NAMES)
    cm_df.to_csv(MODELOS_DIR / "confusion_h2_transfer_rf.csv")

    resumen = pd.DataFrame([{
        "modelo": nombre_modelo, "accuracy": round(acc, 4), "balanced_accuracy": round(bal_acc, 4),
        "precision": round(prec, 4), "recall": round(rec, 4), "f1_score": round(f1, 4),
        "mcc": round(mcc, 4), "tiempo_entrenamiento_s": round(tiempo_entrenamiento, 2),
        "tiempo_inferencia_ms": round(tiempo_inferencia, 2)
    }])
    resumen.to_csv(MODELOS_DIR / "resultados_h2_transfer_rf.csv", index=False)
    print(f"  Métricas guardadas en reports/modelos/")
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

    print("\n🔍 Cargando imágenes de TRAIN...")
    X_train_imgs, y_train = cargar_imagenes_como_array(TRAIN_DIR)
    print(f"   Forma: {X_train_imgs.shape}")

    print("\n🔍 Cargando imágenes de TEST...")
    X_test_imgs, y_test = cargar_imagenes_como_array(TEST_DIR)
    print(f"   Forma: {X_test_imgs.shape}")

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
