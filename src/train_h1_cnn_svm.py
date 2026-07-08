import sys
import time
from pathlib import Path
from collections import Counter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from tensorflow.keras import layers, models as keras_models
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, matthews_corrcoef, balanced_accuracy_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import (
    TRAIN_DIR, TEST_DIR, MODELS_DIR, MODELOS_DIR,
    IMG_SIZE, BATCH_SIZE, SEED, CLASS_NAMES,
    CNN_EXTRACTOR_PATH, CNN_SVM_PATH,
)
from evaluacion_visual import save_confusion_matrix, save_roc_curves

NUM_CLASSES = len(CLASS_NAMES)
EPOCHS_CNN = 20
VAL_RATIO = 0.15
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def escanear_directorio(split_dir: Path):
    paths, labels = [], []
    for idx, clase in enumerate(CLASS_NAMES):
        clase_dir = split_dir / clase
        if not clase_dir.exists():
            continue
        imgs = [str(p) for p in sorted(clase_dir.iterdir()) if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        paths.extend(imgs)
        labels.extend([idx] * len(imgs))
    return paths, labels


def cargar_imagen(path, label):
    raw = tf.io.read_file(path)
    img = tf.image.decode_image(raw, channels=3, expand_animations=False)
    img = tf.image.resize(img, IMG_SIZE)
    img = tf.cast(img, tf.float32)
    label_oh = tf.one_hot(label, NUM_CLASSES)
    return img, label_oh


def construir_dataset(paths, labels, shuffle=False):
    ds = tf.data.Dataset.from_tensor_slices((tf.constant(paths), tf.constant(labels, dtype=tf.int32)))
    ds = ds.map(cargar_imagen, num_parallel_calls=tf.data.AUTOTUNE)
    if shuffle:
        ds = ds.shuffle(buffer_size=len(paths), seed=SEED, reshuffle_each_iteration=True)
    ds = ds.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)
    return ds


def construir_cnn():
    data_aug = keras_models.Sequential([
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.08),
        layers.RandomZoom(0.1),
        layers.RandomContrast(0.1),
    ], name="data_augmentation")

    model = keras_models.Sequential([
        layers.Input(shape=IMG_SIZE + (3,)),
        data_aug,
        layers.Rescaling(1.0 / 255),
        layers.Conv2D(32, 3, activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(),
        layers.Conv2D(64, 3, activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(),
        layers.Conv2D(128, 3, activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(),
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation="relu", name="feature_layer"),
        layers.Dropout(0.5),
        layers.Dense(NUM_CLASSES, activation="softmax", name="output"),
    ], name="cnn_classifier")
    return model


def extraer_features_tf(extractor, dataset):
    X_list, y_list = [], []
    for batch_imgs, batch_labels in dataset:
        feats = extractor(batch_imgs, training=False)
        X_list.append(feats.numpy())
        y_list.append(np.argmax(batch_labels.numpy(), axis=1))
    return np.concatenate(X_list, axis=0), np.concatenate(y_list, axis=0)


def mostrar_metricas(y_test, y_pred, nombre_modelo="CNN + SVM", tiempo_entrenamiento=0, tiempo_inferencia=0):
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
    cm_df.to_csv(MODELOS_DIR / "confusion_h1_cnn_svm.csv")

    resumen = pd.DataFrame([{
        "modelo": nombre_modelo, "accuracy": round(acc, 4), "balanced_accuracy": round(bal_acc, 4),
        "precision": round(prec, 4), "recall": round(rec, 4), "f1_score": round(f1, 4),
        "mcc": round(mcc, 4), "tiempo_entrenamiento_s": round(tiempo_entrenamiento, 2),
        "tiempo_inferencia_ms": round(tiempo_inferencia, 2)
    }])
    resumen.to_csv(MODELOS_DIR / "resultados_h1_cnn_svm.csv", index=False)
    print(f"  Métricas guardadas en reports/modelos/")
    return acc, prec, rec, f1, mcc, bal_acc, cm


def main():
    print("=" * 60)
    print("  H1 — Entrenamiento CNN + SVM — VineGuard AI")
    print("=" * 60)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tf.random.set_seed(SEED)
    np.random.seed(SEED)

    start_total = time.time()

    print("\n🔄 Escaneando directorios...")
    all_train_paths, all_train_labels = escanear_directorio(TRAIN_DIR)
    test_paths, test_labels = escanear_directorio(TEST_DIR)

    train_paths, val_paths, train_labels, val_labels = train_test_split(
        all_train_paths, all_train_labels, test_size=VAL_RATIO,
        stratify=all_train_labels, random_state=SEED,
    )

    print("\n🔄 Construyendo tf.data.Datasets...")
    train_ds = construir_dataset(train_paths, train_labels, shuffle=True)
    val_ds = construir_dataset(val_paths, val_labels, shuffle=False)
    test_ds = construir_dataset(test_paths, test_labels, shuffle=False)

    print(f"\n🚀 Entrenando CNN ({EPOCHS_CNN} épocas)...")
    cnn = construir_cnn()
    cnn.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=5e-4),
                loss="categorical_crossentropy", metrics=["accuracy"])

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6),
    ]

    history = cnn.fit(train_ds, validation_data=val_ds, epochs=EPOCHS_CNN, callbacks=callbacks)

    best_val_acc = max(history.history.get("val_accuracy", [0]))
    print(f"\n   ✅ Mejor val_accuracy: {best_val_acc:.4f}")

    print("\n⚙️  Creando extractor CNN...")
    extractor = tf.keras.Model(inputs=cnn.input, outputs=cnn.get_layer("feature_layer").output, name="cnn_extractor")
    extractor.save(str(CNN_EXTRACTOR_PATH))
    print(f"   Extractor guardado: {CNN_EXTRACTOR_PATH}")

    print("\n🔍 Extrayendo features para SVM...")
    X_train_fit, y_train_fit = extraer_features_tf(extractor, train_ds)
    X_val, y_val = extraer_features_tf(extractor, val_ds)
    X_train_svm = np.concatenate([X_train_fit, X_val], axis=0)
    y_train_svm = np.concatenate([y_train_fit, y_val], axis=0)
    X_test, y_test = extraer_features_tf(extractor, test_ds)

    print(f"   X_train_svm: {X_train_svm.shape}, X_test: {X_test.shape}")

    start_train = time.time()
    print("\n🚀 Entrenando SVM sobre features CNN...")
    svm = SVC(kernel="rbf", C=10.0, gamma="scale", probability=True, class_weight="balanced", random_state=SEED)
    svm.fit(X_train_svm, y_train_svm)
    tiempo_entrenamiento = time.time() - start_total
    print("   ✅ SVM entrenado.")

    start_infer = time.time()
    y_pred = svm.predict(X_test)
    y_score = svm.predict_proba(X_test)
    tiempo_inferencia = (time.time() - start_infer) / len(y_pred) * 1000

    mostrar_metricas(y_test, y_pred, "H1 — CNN + SVM", tiempo_entrenamiento, tiempo_inferencia)

    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    save_confusion_matrix(y_test, y_pred, CLASS_NAMES, MODELOS_DIR / "confusion_h1_cnn_svm.png")
    save_roc_curves(y_test, y_score, CLASS_NAMES, MODELOS_DIR / "roc_h1_cnn_svm.png")

    joblib.dump(svm, CNN_SVM_PATH)
    print(f"\n💾 SVM guardado en: {CNN_SVM_PATH}")
    print("\n✅ Proceso completado.")


if __name__ == "__main__":
    main()
