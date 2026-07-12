"""
train_h1_cnn_svm.py
────────────────────
H1 — CNN + SVM

Flujo:
  1. Escanear train y test.
  2. Dividir train original en entrenamiento y validación.
  3. Balancear únicamente el subconjunto de entrenamiento.
  4. Entrenar CNN usando validación real sin aumento.
  5. Crear y guardar el extractor CNN.
  6. Extraer embeddings CNN de las imágenes reales de train + validación.
  7. Entrenar SVM sobre embeddings.
  8. Evaluar sobre test real sin aumento.
  9. Generar reportes y guardar modelos.
"""

import io
import sys
import time
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import label_binarize
from sklearn.svm import SVC
from tensorflow.keras import layers
from tensorflow.keras import models as keras_models


# ─────────────────────────────────────────────
# Configuración UTF-8
# ─────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
    )


# Permitir importaciones desde src/
SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))


from mantenedor import (
    BATCH_SIZE,
    CLASS_NAMES,
    CNN_EXTRACTOR_PATH,
    CNN_SVM_PATH,
    H1_CNN_SVM_REPORTS_DIR,
    IMG_SIZE,
    MODELS_DIR,
    SEED,
    TEST_DIR,
    TRAIN_DIR,
)
from evaluacion_visual import (
    save_confusion_matrix,
    save_normalized_confusion_matrix,
    save_precision_recall_curves,
    save_roc_curves,
)


# ─────────────────────────────────────────────
# Configuración general
# ─────────────────────────────────────────────
NUM_CLASSES = len(CLASS_NAMES)
EPOCHS_CNN = 20
VAL_RATIO = 0.15
TARGET_PER_CLASS = 1500

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

NOMBRE_MODELO = "H1 — CNN + SVM"

CNN_LEARNING_RATE = 5e-4
CNN_PATIENCE = 5

SVM_KERNEL = "rbf"
SVM_C = 10.0
SVM_GAMMA = "scale"
SVM_CLASS_WEIGHT = "balanced"


def configurar_semillas() -> None:
    """
    Configura semillas para mejorar la reproducibilidad.
    """
    np.random.seed(SEED)
    tf.random.set_seed(SEED)


def escanear_directorio(
    split_dir: Path,
) -> tuple[list[str], list[int], list[str]]:
    """
    Obtiene rutas, etiquetas numéricas y nombres
    de imágenes para un directorio train o test.
    """
    paths: list[str] = []
    labels: list[int] = []
    filenames: list[str] = []

    for indice, clase in enumerate(CLASS_NAMES):
        clase_dir = split_dir / clase

        if not clase_dir.exists():
            print(
                f"⚠️ No existe el directorio de clase: "
                f"{clase_dir}"
            )
            continue

        imagenes = sorted(
            archivo
            for archivo in clase_dir.iterdir()
            if archivo.is_file()
            and archivo.suffix.lower() in IMAGE_EXTENSIONS
        )

        paths.extend(
            str(archivo)
            for archivo in imagenes
        )

        labels.extend(
            [indice] * len(imagenes)
        )

        filenames.extend(
            archivo.name
            for archivo in imagenes
        )

    return paths, labels, filenames


def validar_datos(
    train_paths: list[str],
    train_labels: list[int],
    val_paths: list[str],
    val_labels: list[int],
    test_paths: list[str],
    test_labels: list[int],
) -> None:
    """
    Valida que los conjuntos contengan datos y
    que rutas y etiquetas tengan igual tamaño.
    """
    conjuntos = {
        "train": (train_paths, train_labels),
        "validación": (val_paths, val_labels),
        "test": (test_paths, test_labels),
    }

    for nombre, (paths, labels) in conjuntos.items():
        if len(paths) == 0:
            raise ValueError(
                f"El conjunto {nombre} está vacío."
            )

        if len(paths) != len(labels):
            raise ValueError(
                f"El conjunto {nombre} tiene diferente "
                "cantidad de rutas y etiquetas."
            )

    clases_train = set(train_labels)
    clases_val = set(val_labels)
    clases_test = set(test_labels)

    clases_esperadas = set(
        range(NUM_CLASSES)
    )

    if clases_train != clases_esperadas:
        raise ValueError(
            "El entrenamiento no contiene todas las clases."
        )

    if clases_val != clases_esperadas:
        raise ValueError(
            "La validación no contiene todas las clases."
        )

    if clases_test != clases_esperadas:
        raise ValueError(
            "El test no contiene todas las clases."
        )


def agrupar_rutas_por_clase(
    paths: list[str],
    labels: list[int],
) -> dict:
    """
    Agrupa las rutas del subconjunto de entrenamiento
    según su clase.
    """
    resultado = {
        clase: {
            "idx": indice,
            "rutas": [],
        }
        for indice, clase in enumerate(CLASS_NAMES)
    }

    for path, label in zip(paths, labels):
        clase = CLASS_NAMES[int(label)]
        resultado[clase]["rutas"].append(path)

    return resultado


def cargar_imagen(
    path: tf.Tensor,
    label: tf.Tensor,
) -> tuple[tf.Tensor, tf.Tensor]:
    """
    Lee una imagen, fuerza RGB, redimensiona y normaliza.
    """
    raw = tf.io.read_file(path)

    imagen = tf.image.decode_image(
        raw,
        channels=3,
        expand_animations=False,
    )

    imagen.set_shape(
        [None, None, 3]
    )

    imagen = tf.image.resize(
        imagen,
        IMG_SIZE,
    )

    imagen = tf.cast(
        imagen,
        tf.float32,
    ) / 255.0

    label_one_hot = tf.one_hot(
        label,
        NUM_CLASSES,
    )

    return imagen, label_one_hot


def construir_dataset(
    paths: list[str],
    labels: list[int],
    shuffle: bool = False,
) -> tf.data.Dataset:
    """
    Construye un dataset sin oversampling.
    Se usa para validación, test y extracción
    de embeddings de imágenes reales.
    """
    dataset = tf.data.Dataset.from_tensor_slices(
        (
            tf.constant(paths),
            tf.constant(
                labels,
                dtype=tf.int32,
            ),
        )
    )

    dataset = dataset.map(
        cargar_imagen,
        num_parallel_calls=tf.data.AUTOTUNE,
    )

    if shuffle:
        dataset = dataset.shuffle(
            buffer_size=len(paths),
            seed=SEED,
            reshuffle_each_iteration=True,
        )

    dataset = dataset.batch(
        BATCH_SIZE,
        drop_remainder=False,
    )

    dataset = dataset.prefetch(
        tf.data.AUTOTUNE
    )

    return dataset


def construir_dataset_balanceado(
    rutas_por_clase: dict,
) -> tf.data.Dataset:
    """
    Genera un conjunto efectivo de TARGET_PER_CLASS
    rutas por clase usando muestreo con reemplazo.

    El aumento visual se aplica posteriormente dentro
    del modelo CNN mediante capas de data augmentation.
    """
    generador = np.random.default_rng(
        SEED
    )

    all_paths: list[str] = []
    all_labels: list[int] = []

    for clase, informacion in rutas_por_clase.items():
        rutas = informacion["rutas"]
        indice = informacion["idx"]

        if len(rutas) == 0:
            raise ValueError(
                f"La clase {clase} no tiene imágenes "
                "en el subconjunto de entrenamiento."
            )

        sampled = generador.choice(
            rutas,
            size=TARGET_PER_CLASS,
            replace=len(rutas) < TARGET_PER_CLASS,
        )

        all_paths.extend(
            sampled.tolist()
        )

        all_labels.extend(
            [indice] * TARGET_PER_CLASS
        )

    permutacion = generador.permutation(
        len(all_paths)
    )

    all_paths = [
        all_paths[indice]
        for indice in permutacion
    ]

    all_labels = [
        all_labels[indice]
        for indice in permutacion
    ]

    return construir_dataset(
        all_paths,
        all_labels,
        shuffle=True,
    )


def mostrar_balanceo(
    rutas_por_clase: dict,
) -> None:
    """
    Muestra el balanceo del subconjunto de entrenamiento.
    """
    print("\n" + "=" * 60)
    print("  BALANCEO DINÁMICO DE ENTRENAMIENTO")
    print("=" * 60)

    print(
        f"  {'Clase':<18}"
        f"{'Reales':>10}"
        f"{'Aumentadas':>12}"
        f"{'Total efectivo':>17}"
    )

    print(
        "  " + "─" * 57
    )

    total_reales = 0
    total_aumentadas = 0
    total_efectivo = 0

    for clase, informacion in rutas_por_clase.items():
        cantidad_real = len(
            informacion["rutas"]
        )

        cantidad_aumentada = max(
            0,
            TARGET_PER_CLASS - cantidad_real,
        )

        total_reales += cantidad_real
        total_aumentadas += cantidad_aumentada
        total_efectivo += TARGET_PER_CLASS

        print(
            f"  {clase:<18}"
            f"{cantidad_real:>10}"
            f"{cantidad_aumentada:>12}"
            f"{TARGET_PER_CLASS:>17}"
        )

    print(
        "  " + "─" * 57
    )

    print(
        f"  {'TOTAL':<18}"
        f"{total_reales:>10}"
        f"{total_aumentadas:>12}"
        f"{total_efectivo:>17}"
    )


def construir_cnn() -> tf.keras.Model:
    """
    Construye la CNN empleada como clasificador
    y extractor de embeddings.
    """
    data_augmentation = keras_models.Sequential(
        [
            layers.RandomFlip(
                "horizontal"
            ),
            layers.RandomRotation(
                0.08
            ),
            layers.RandomZoom(
                0.10
            ),
            layers.RandomContrast(
                0.10
            ),
        ],
        name="data_augmentation",
    )

    inputs = layers.Input(
        shape=IMG_SIZE + (3,),
        name="input_image",
    )

    x = data_augmentation(
        inputs
    )

    x = layers.Conv2D(
        32,
        kernel_size=3,
        activation="relu",
        padding="same",
    )(x)

    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(
        64,
        kernel_size=3,
        activation="relu",
        padding="same",
    )(x)

    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.Conv2D(
        128,
        kernel_size=3,
        activation="relu",
        padding="same",
    )(x)

    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D()(x)

    x = layers.GlobalAveragePooling2D()(x)

    features = layers.Dense(
        256,
        activation="relu",
        name="feature_layer",
    )(x)

    x = layers.Dropout(
        0.5
    )(features)

    outputs = layers.Dense(
        NUM_CLASSES,
        activation="softmax",
        name="output",
    )(x)

    return tf.keras.Model(
        inputs=inputs,
        outputs=outputs,
        name="cnn_classifier",
    )


def crear_extractor(
    cnn: tf.keras.Model,
) -> tf.keras.Model:
    """
    Crea un modelo que termina en feature_layer.
    """
    return tf.keras.Model(
        inputs=cnn.input,
        outputs=cnn.get_layer(
            "feature_layer"
        ).output,
        name="cnn_extractor",
    )


def extraer_embeddings(
    extractor: tf.keras.Model,
    dataset: tf.data.Dataset,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extrae embeddings CNN y etiquetas numéricas.
    """
    features_batches = []
    labels_batches = []

    for batch_images, batch_labels in dataset:
        embeddings = extractor(
            batch_images,
            training=False,
        )

        features_batches.append(
            embeddings.numpy()
        )

        labels_batches.append(
            np.argmax(
                batch_labels.numpy(),
                axis=1,
            )
        )

    if not features_batches:
        raise ValueError(
            "No se pudieron extraer embeddings."
        )

    X = np.concatenate(
        features_batches,
        axis=0,
    )

    y = np.concatenate(
        labels_batches,
        axis=0,
    )

    return X, y


def alinear_probabilidades(
    modelo: SVC,
    probabilidades: np.ndarray,
) -> np.ndarray:
    """
    Asegura que las columnas de predict_proba sigan
    el orden definido por CLASS_NAMES.
    """
    probabilidades_alineadas = np.zeros(
        (
            probabilidades.shape[0],
            NUM_CLASSES,
        ),
        dtype=np.float64,
    )

    for posicion, clase_modelo in enumerate(
        modelo.classes_
    ):
        probabilidades_alineadas[
            :,
            int(clase_modelo),
        ] = probabilidades[:, posicion]

    return probabilidades_alineadas


def calcular_metricas(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    y_score: np.ndarray,
) -> dict:
    """
    Calcula métricas globales y matriz de confusión.
    """
    metricas = {
        "accuracy": accuracy_score(
            y_test,
            y_pred,
        ),
        "balanced_accuracy": balanced_accuracy_score(
            y_test,
            y_pred,
        ),
        "precision": precision_score(
            y_test,
            y_pred,
            average="weighted",
            zero_division=0,
        ),
        "recall": recall_score(
            y_test,
            y_pred,
            average="weighted",
            zero_division=0,
        ),
        "f1_score": f1_score(
            y_test,
            y_pred,
            average="weighted",
            zero_division=0,
        ),
        "mcc": matthews_corrcoef(
            y_test,
            y_pred,
        ),
        "confusion_matrix": confusion_matrix(
            y_test,
            y_pred,
            labels=range(NUM_CLASSES),
        ),
    }

    y_bin = label_binarize(
        y_test,
        classes=range(NUM_CLASSES),
    )

    try:
        metricas["auc_macro"] = roc_auc_score(
            y_bin,
            y_score,
            multi_class="ovr",
            average="macro",
        )

        metricas["auc_micro"] = roc_auc_score(
            y_bin,
            y_score,
            multi_class="ovr",
            average="micro",
        )

    except ValueError as error:
        print(
            f"⚠️ No se pudo calcular AUC: {error}"
        )

        metricas["auc_macro"] = 0.0
        metricas["auc_micro"] = 0.0

    return metricas


def guardar_historial_cnn(
    historial: tf.keras.callbacks.History,
) -> None:
    """
    Guarda el historial de entrenamiento y sus gráficas.
    """
    history_df = pd.DataFrame(
        historial.history
    )

    history_df.index = (
        history_df.index + 1
    )

    history_df.index.name = "epoca"

    history_df.to_csv(
        H1_CNN_SVM_REPORTS_DIR
        / "historial_cnn_h1.csv"
    )

    if {
        "accuracy",
        "val_accuracy",
    }.issubset(history_df.columns):
        plt.figure(
            figsize=(8, 5)
        )

        plt.plot(
            history_df.index,
            history_df["accuracy"],
            label="Entrenamiento",
        )

        plt.plot(
            history_df.index,
            history_df["val_accuracy"],
            label="Validación",
        )

        plt.xlabel("Época")
        plt.ylabel("Accuracy")
        plt.title(
            "Accuracy de entrenamiento y validación — H1"
        )
        plt.legend()
        plt.tight_layout()

        plt.savefig(
            H1_CNN_SVM_REPORTS_DIR
            / "curva_accuracy_cnn_h1.png",
            dpi=300,
        )

        plt.close()

    if {
        "loss",
        "val_loss",
    }.issubset(history_df.columns):
        plt.figure(
            figsize=(8, 5)
        )

        plt.plot(
            history_df.index,
            history_df["loss"],
            label="Entrenamiento",
        )

        plt.plot(
            history_df.index,
            history_df["val_loss"],
            label="Validación",
        )

        plt.xlabel("Época")
        plt.ylabel("Loss")
        plt.title(
            "Pérdida de entrenamiento y validación — H1"
        )
        plt.legend()
        plt.tight_layout()

        plt.savefig(
            H1_CNN_SVM_REPORTS_DIR
            / "curva_loss_cnn_h1.png",
            dpi=300,
        )

        plt.close()


def mostrar_resultados(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    metricas: dict,
    tiempo_preparacion_s: float,
    tiempo_entrenamiento_cnn_s: float,
    tiempo_extraccion_embeddings_s: float,
    tiempo_entrenamiento_svm_s: float,
    tiempo_inferencia_ms: float,
) -> None:
    """
    Muestra resultados principales en consola.
    """
    cm = metricas["confusion_matrix"]

    print("\n" + "=" * 60)
    print(f"  📊 RESULTADOS — {NOMBRE_MODELO}")
    print("=" * 60)

    print(
        f"  Accuracy          : "
        f"{metricas['accuracy']:.4f} "
        f"({metricas['accuracy']:.2%})"
    )

    print(
        f"  Balanced Accuracy : "
        f"{metricas['balanced_accuracy']:.4f}"
    )

    print(
        f"  Precision         : "
        f"{metricas['precision']:.4f}"
    )

    print(
        f"  Recall            : "
        f"{metricas['recall']:.4f}"
    )

    print(
        f"  F1-Score          : "
        f"{metricas['f1_score']:.4f}"
    )

    print(
        f"  MCC               : "
        f"{metricas['mcc']:.4f}"
    )

    print(
        f"  AUC Macro         : "
        f"{metricas['auc_macro']:.4f}"
    )

    print(
        f"  AUC Micro         : "
        f"{metricas['auc_micro']:.4f}"
    )

    print(
        "  Preparación de datasets             : "
        f"{tiempo_preparacion_s:.2f}s"
    )

    print(
        "  Entrenamiento CNN                   : "
        f"{tiempo_entrenamiento_cnn_s:.2f}s"
    )

    print(
        "  Extracción de embeddings            : "
        f"{tiempo_extraccion_embeddings_s:.2f}s"
    )

    print(
        "  Entrenamiento SVM                   : "
        f"{tiempo_entrenamiento_svm_s:.2f}s"
    )

    print(
        "  Inferencia SVM promedio por muestra : "
        f"{tiempo_inferencia_ms:.4f}ms"
    )

    print("\n  Reporte por clase:")

    print(
        classification_report(
            y_test,
            y_pred,
            labels=range(NUM_CLASSES),
            target_names=CLASS_NAMES,
            zero_division=0,
        )
    )

    print("  Matriz de Confusión:")

    encabezado = "         " + "  ".join(
        f"{clase[:8]:>8}"
        for clase in CLASS_NAMES
    )

    print(encabezado)

    for indice, fila in enumerate(cm):
        valores = "  ".join(
            f"{valor:>8}"
            for valor in fila
        )

        print(
            f"  {CLASS_NAMES[indice][:8]:>8}  "
            f"{valores}"
        )

    print("=" * 60)


def guardar_reportes_evaluacion(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    y_score: np.ndarray,
    test_filenames: list[str],
    metricas: dict,
) -> None:
    """
    Guarda CSV, matrices, curvas y predicciones.
    """
    reporte = classification_report(
        y_test,
        y_pred,
        labels=range(NUM_CLASSES),
        target_names=CLASS_NAMES,
        zero_division=0,
        output_dict=True,
    )

    pd.DataFrame(
        reporte
    ).transpose().to_csv(
        H1_CNN_SVM_REPORTS_DIR
        / "reporte_clasificacion_h1_cnn_svm.csv"
    )

    pd.DataFrame(
        metricas["confusion_matrix"],
        index=CLASS_NAMES,
        columns=CLASS_NAMES,
    ).to_csv(
        H1_CNN_SVM_REPORTS_DIR
        / "confusion_h1_cnn_svm.csv"
    )

    save_confusion_matrix(
        y_test,
        y_pred,
        CLASS_NAMES,
        H1_CNN_SVM_REPORTS_DIR
        / "confusion_h1_cnn_svm.png",
    )

    save_normalized_confusion_matrix(
        y_test,
        y_pred,
        CLASS_NAMES,
        H1_CNN_SVM_REPORTS_DIR
        / "confusion_normalizada_h1_cnn_svm.png",
    )

    save_roc_curves(
        y_test,
        y_score,
        CLASS_NAMES,
        H1_CNN_SVM_REPORTS_DIR
        / "roc_h1_cnn_svm.png",
    )

    save_precision_recall_curves(
        y_test,
        y_score,
        CLASS_NAMES,
        H1_CNN_SVM_REPORTS_DIR
        / "precision_recall_h1_cnn_svm.png",
    )

    predicciones_df = pd.DataFrame({
        "archivo": test_filenames,
        "clase_real": [
            CLASS_NAMES[int(etiqueta)]
            for etiqueta in y_test
        ],
        "clase_predicha": [
            CLASS_NAMES[int(etiqueta)]
            for etiqueta in y_pred
        ],
        "prob_Black_rot": y_score[:, 0],
        "prob_Esca": y_score[:, 1],
        "prob_Healthy": y_score[:, 2],
        "prob_Leaf_blight": y_score[:, 3],
        "correcto": (
            np.asarray(y_test)
            == np.asarray(y_pred)
        ),
    })

    predicciones_df.to_csv(
        H1_CNN_SVM_REPORTS_DIR
        / "predicciones_h1_cnn_svm.csv",
        index=False,
    )


def obtener_tamano_mb(
    ruta: Path,
) -> float:
    """
    Obtiene el tamaño de un archivo o directorio.
    """
    if not ruta.exists():
        return 0.0

    if ruta.is_file():
        return (
            ruta.stat().st_size
            / (1024 * 1024)
        )

    total_bytes = sum(
        archivo.stat().st_size
        for archivo in ruta.rglob("*")
        if archivo.is_file()
    )

    return total_bytes / (1024 * 1024)


def guardar_resumen_final(
    metricas: dict,
    mejor_val_accuracy: float,
    epocas_ejecutadas: int,
    tiempo_preparacion_s: float,
    tiempo_entrenamiento_cnn_s: float,
    tiempo_guardado_extractor_s: float,
    tiempo_extraccion_embeddings_s: float,
    tiempo_entrenamiento_svm_s: float,
    tiempo_evaluacion_s: float,
    tiempo_inferencia_ms: float,
    tiempo_guardado_svm_s: float,
    tiempo_total_s: float,
    n_train_cnn: int,
    n_val_cnn: int,
    n_train_svm: int,
    n_test: int,
    n_features: int,
    extractor_size_mb: float,
    svm_size_mb: float,
) -> None:
    """
    Guarda el resumen definitivo del modelo híbrido.
    """
    resumen = {
        "modelo": NOMBRE_MODELO,

        "accuracy": round(
            metricas["accuracy"],
            4,
        ),
        "balanced_accuracy": round(
            metricas["balanced_accuracy"],
            4,
        ),
        "precision": round(
            metricas["precision"],
            4,
        ),
        "recall": round(
            metricas["recall"],
            4,
        ),
        "f1_score": round(
            metricas["f1_score"],
            4,
        ),
        "mcc": round(
            metricas["mcc"],
            4,
        ),
        "auc_macro": round(
            metricas["auc_macro"],
            4,
        ),
        "auc_micro": round(
            metricas["auc_micro"],
            4,
        ),

        "mejor_val_accuracy_cnn": round(
            mejor_val_accuracy,
            4,
        ),
        "epocas_cnn_ejecutadas": epocas_ejecutadas,

        "tiempo_preparacion_datasets_s": round(
            tiempo_preparacion_s,
            2,
        ),
        "tiempo_entrenamiento_cnn_s": round(
            tiempo_entrenamiento_cnn_s,
            2,
        ),
        "tiempo_guardado_extractor_s": round(
            tiempo_guardado_extractor_s,
            4,
        ),
        "tiempo_extraccion_embeddings_s": round(
            tiempo_extraccion_embeddings_s,
            2,
        ),
        "tiempo_entrenamiento_svm_s": round(
            tiempo_entrenamiento_svm_s,
            2,
        ),
        "tiempo_evaluacion_s": round(
            tiempo_evaluacion_s,
            2,
        ),
        "tiempo_inferencia_ms": round(
            tiempo_inferencia_ms,
            4,
        ),
        "tiempo_guardado_svm_s": round(
            tiempo_guardado_svm_s,
            4,
        ),
        "tiempo_total_proceso_s": round(
            tiempo_total_s,
            2,
        ),

        "n_muestras_train_cnn_efectivas": n_train_cnn,
        "n_muestras_validacion_cnn": n_val_cnn,
        "n_muestras_train_svm_reales": n_train_svm,
        "n_muestras_test": n_test,
        "n_features_embedding": n_features,

        "extractor_size_mb": round(
            extractor_size_mb,
            3,
        ),
        "svm_size_mb": round(
            svm_size_mb,
            3,
        ),
        "tamano_total_modelos_mb": round(
            extractor_size_mb + svm_size_mb,
            3,
        ),

        "semilla": SEED,

        "img_height": IMG_SIZE[0],
        "img_width": IMG_SIZE[1],
        "batch_size": BATCH_SIZE,
        "epochs_max": EPOCHS_CNN,
        "val_ratio": VAL_RATIO,
        "target_per_class": TARGET_PER_CLASS,
        "learning_rate": CNN_LEARNING_RATE,

        "svm_kernel": SVM_KERNEL,
        "svm_C": SVM_C,
        "svm_gamma": SVM_GAMMA,
        "svm_class_weight": SVM_CLASS_WEIGHT,
    }

    pd.DataFrame(
        [resumen]
    ).to_csv(
        H1_CNN_SVM_REPORTS_DIR
        / "resultados_h1_cnn_svm.csv",
        index=False,
    )


def mostrar_resumen_tiempos(
    tiempo_preparacion_s: float,
    tiempo_entrenamiento_cnn_s: float,
    tiempo_guardado_extractor_s: float,
    tiempo_extraccion_embeddings_s: float,
    tiempo_entrenamiento_svm_s: float,
    tiempo_evaluacion_s: float,
    tiempo_inferencia_ms: float,
    tiempo_guardado_svm_s: float,
    tiempo_total_s: float,
) -> None:
    """
    Muestra el resumen de tiempos.
    """
    print("\n" + "=" * 60)
    print("  RESUMEN DE TIEMPOS")
    print("=" * 60)

    print(
        "  Preparación de datasets             : "
        f"{tiempo_preparacion_s:.2f} s"
    )

    print(
        "  Entrenamiento CNN                   : "
        f"{tiempo_entrenamiento_cnn_s:.2f} s"
    )

    print(
        "  Guardado del extractor CNN          : "
        f"{tiempo_guardado_extractor_s:.4f} s"
    )

    print(
        "  Extracción de embeddings            : "
        f"{tiempo_extraccion_embeddings_s:.2f} s"
    )

    print(
        "  Entrenamiento SVM                   : "
        f"{tiempo_entrenamiento_svm_s:.2f} s"
    )

    print(
        "  Evaluación completa y reportes      : "
        f"{tiempo_evaluacion_s:.2f} s"
    )

    print(
        "  Inferencia SVM promedio por muestra : "
        f"{tiempo_inferencia_ms:.4f} ms"
    )

    print(
        "  Guardado del SVM                    : "
        f"{tiempo_guardado_svm_s:.4f} s"
    )

    print(
        "  Tiempo total del proceso            : "
        f"{tiempo_total_s:.2f} s"
    )

    print("=" * 60)


def main() -> None:
    print("=" * 60)
    print("  H1 — Entrenamiento CNN + SVM — VineGuard AI")
    print("=" * 60)

    configurar_semillas()

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    H1_CNN_SVM_REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CNN_EXTRACTOR_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    CNN_SVM_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    inicio_total = time.perf_counter()

    # ─────────────────────────────────────────────
    # 1. Escaneo, división y datasets
    # ─────────────────────────────────────────────
    inicio_preparacion = time.perf_counter()

    print("\n🔄 Escaneando directorios...")

    all_paths, all_labels, all_filenames = (
        escanear_directorio(
            TRAIN_DIR
        )
    )

    test_paths, test_labels, test_filenames = (
        escanear_directorio(
            TEST_DIR
        )
    )

    (
        train_paths,
        val_paths,
        train_labels,
        val_labels,
    ) = train_test_split(
        all_paths,
        all_labels,
        test_size=VAL_RATIO,
        stratify=all_labels,
        random_state=SEED,
    )

    validar_datos(
        train_paths,
        train_labels,
        val_paths,
        val_labels,
        test_paths,
        test_labels,
    )

    rutas_train_por_clase = agrupar_rutas_por_clase(
        train_paths,
        train_labels,
    )

    mostrar_balanceo(
        rutas_train_por_clase
    )

    print("\n🔄 Construyendo tf.data.Datasets...")

    train_ds = construir_dataset_balanceado(
        rutas_train_por_clase
    )

    val_ds = construir_dataset(
        val_paths,
        val_labels,
        shuffle=False,
    )

    test_ds = construir_dataset(
        test_paths,
        test_labels,
        shuffle=False,
    )

    tiempo_preparacion = (
        time.perf_counter()
        - inicio_preparacion
    )

    print("\n📋 Preprocesamiento:")
    print(
        "   - Entrenamiento CNN: RGB + resize + "
        "normalización + oversampling + data augmentation"
    )
    print(
        f"   - Entrenamiento balanceado a "
        f"{TARGET_PER_CLASS} muestras por clase"
    )
    print(
        "   - Validación: imágenes reales, sin aumento"
    )
    print(
        "   - Test: imágenes reales, sin aumento"
    )
    print(
        "   - Imágenes aumentadas guardadas físicamente: No"
    )

    print(
        f"   ✅ Preparación completada en "
        f"{tiempo_preparacion:.2f}s"
    )

    # ─────────────────────────────────────────────
    # 2. Entrenamiento CNN
    # ─────────────────────────────────────────────
    print(
        f"\n🚀 Entrenando CNN "
        f"({EPOCHS_CNN} épocas máximas)..."
    )

    cnn = construir_cnn()

    cnn.compile(
        optimizer=tf.keras.optimizers.Adam(
            learning_rate=CNN_LEARNING_RATE
        ),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=CNN_PATIENCE,
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-6,
            verbose=1,
        ),
    ]

    inicio_entrenamiento_cnn = time.perf_counter()

    historial = cnn.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_CNN,
        callbacks=callbacks,
        verbose=1,
    )

    tiempo_entrenamiento_cnn = (
        time.perf_counter()
        - inicio_entrenamiento_cnn
    )

    guardar_historial_cnn(
        historial
    )

    val_accuracy_history = historial.history.get(
        "val_accuracy",
        [0.0],
    )

    mejor_val_accuracy = max(
        val_accuracy_history
    )

    epocas_ejecutadas = len(
        historial.history.get(
            "loss",
            [],
        )
    )

    print(
        f"\n   ✅ Mejor val_accuracy: "
        f"{mejor_val_accuracy:.4f}"
    )

    print(
        f"   ✅ Épocas ejecutadas: "
        f"{epocas_ejecutadas}"
    )

    print(
        f"   ✅ Entrenamiento CNN completado en "
        f"{tiempo_entrenamiento_cnn:.2f}s"
    )

    # ─────────────────────────────────────────────
    # 3. Crear y guardar extractor
    # ─────────────────────────────────────────────
    print("\n⚙️ Creando extractor CNN...")

    extractor = crear_extractor(
        cnn
    )

    inicio_guardado_extractor = time.perf_counter()

    extractor.save(
        str(CNN_EXTRACTOR_PATH)
    )

    tiempo_guardado_extractor = (
        time.perf_counter()
        - inicio_guardado_extractor
    )

    extractor_size_mb = obtener_tamano_mb(
        CNN_EXTRACTOR_PATH
    )

    print(
        f"   ✅ Extractor guardado en: "
        f"{CNN_EXTRACTOR_PATH}"
    )

    # ─────────────────────────────────────────────
    # 4. Extracción de embeddings
    # ─────────────────────────────────────────────
    print(
        "\n🔍 Extrayendo embeddings CNN "
        "de train y test..."
    )

    inicio_embeddings = time.perf_counter()

    # Después de seleccionar los mejores pesos de la CNN,
    # se usan todas las imágenes reales de train original
    # para ajustar el clasificador SVM.
    train_full_ds = construir_dataset(
        all_paths,
        all_labels,
        shuffle=False,
    )

    X_train_svm, y_train_svm = extraer_embeddings(
        extractor,
        train_full_ds,
    )

    X_test, y_test = extraer_embeddings(
        extractor,
        test_ds,
    )

    tiempo_extraccion_embeddings = (
        time.perf_counter()
        - inicio_embeddings
    )

    if X_train_svm.shape[1] != X_test.shape[1]:
        raise ValueError(
            "Train y test tienen distinta dimensión "
            "de embeddings."
        )

    print(
        f"   X_train_svm: {X_train_svm.shape}"
    )

    print(
        f"   X_test:      {X_test.shape}"
    )

    print(
        f"   ✅ Embeddings extraídos en "
        f"{tiempo_extraccion_embeddings:.2f}s"
    )

    # ─────────────────────────────────────────────
    # 5. Entrenamiento SVM
    # ─────────────────────────────────────────────
    print("\n🚀 Entrenando SVM sobre embeddings CNN...")

    svm = SVC(
        kernel=SVM_KERNEL,
        C=SVM_C,
        gamma=SVM_GAMMA,
        probability=True,
        class_weight=SVM_CLASS_WEIGHT,
        random_state=SEED,
    )

    inicio_entrenamiento_svm = time.perf_counter()

    svm.fit(
        X_train_svm,
        y_train_svm,
    )

    tiempo_entrenamiento_svm = (
        time.perf_counter()
        - inicio_entrenamiento_svm
    )

    print(
        f"   ✅ SVM entrenado en "
        f"{tiempo_entrenamiento_svm:.2f}s"
    )

    # ─────────────────────────────────────────────
    # 6. Evaluación completa
    # Incluye inferencia, métricas, gráficos y CSV.
    # ─────────────────────────────────────────────
    inicio_evaluacion = time.perf_counter()

    inicio_inferencia = time.perf_counter()

    y_pred = svm.predict(
        X_test
    )

    probabilidades_originales = svm.predict_proba(
        X_test
    )

    duracion_inferencia = (
        time.perf_counter()
        - inicio_inferencia
    )

    tiempo_inferencia_ms = (
        duracion_inferencia
        / len(y_pred)
    ) * 1000

    y_score = alinear_probabilidades(
        svm,
        probabilidades_originales,
    )

    metricas = calcular_metricas(
        y_test,
        y_pred,
        y_score,
    )

    mostrar_resultados(
        y_test=y_test,
        y_pred=y_pred,
        metricas=metricas,
        tiempo_preparacion_s=tiempo_preparacion,
        tiempo_entrenamiento_cnn_s=tiempo_entrenamiento_cnn,
        tiempo_extraccion_embeddings_s=tiempo_extraccion_embeddings,
        tiempo_entrenamiento_svm_s=tiempo_entrenamiento_svm,
        tiempo_inferencia_ms=tiempo_inferencia_ms,
    )

    guardar_reportes_evaluacion(
        y_test=y_test,
        y_pred=y_pred,
        y_score=y_score,
        test_filenames=test_filenames,
        metricas=metricas,
    )

    tiempo_evaluacion = (
        time.perf_counter()
        - inicio_evaluacion
    )

    # ─────────────────────────────────────────────
    # 7. Guardado final del SVM
    # ─────────────────────────────────────────────
    inicio_guardado_svm = time.perf_counter()

    joblib.dump(
        svm,
        CNN_SVM_PATH,
    )

    tiempo_guardado_svm = (
        time.perf_counter()
        - inicio_guardado_svm
    )

    svm_size_mb = obtener_tamano_mb(
        CNN_SVM_PATH
    )

    # El total incluye todas las etapas anteriores.
    tiempo_total = (
        time.perf_counter()
        - inicio_total
    )

    # ─────────────────────────────────────────────
    # 8. Resumen definitivo
    # ─────────────────────────────────────────────
    guardar_resumen_final(
        metricas=metricas,
        mejor_val_accuracy=mejor_val_accuracy,
        epocas_ejecutadas=epocas_ejecutadas,
        tiempo_preparacion_s=tiempo_preparacion,
        tiempo_entrenamiento_cnn_s=tiempo_entrenamiento_cnn,
        tiempo_guardado_extractor_s=tiempo_guardado_extractor,
        tiempo_extraccion_embeddings_s=tiempo_extraccion_embeddings,
        tiempo_entrenamiento_svm_s=tiempo_entrenamiento_svm,
        tiempo_evaluacion_s=tiempo_evaluacion,
        tiempo_inferencia_ms=tiempo_inferencia_ms,
        tiempo_guardado_svm_s=tiempo_guardado_svm,
        tiempo_total_s=tiempo_total,
        n_train_cnn=TARGET_PER_CLASS * NUM_CLASSES,
        n_val_cnn=len(val_paths),
        n_train_svm=X_train_svm.shape[0],
        n_test=X_test.shape[0],
        n_features=X_train_svm.shape[1],
        extractor_size_mb=extractor_size_mb,
        svm_size_mb=svm_size_mb,
    )

    mostrar_resumen_tiempos(
        tiempo_preparacion_s=tiempo_preparacion,
        tiempo_entrenamiento_cnn_s=tiempo_entrenamiento_cnn,
        tiempo_guardado_extractor_s=tiempo_guardado_extractor,
        tiempo_extraccion_embeddings_s=tiempo_extraccion_embeddings,
        tiempo_entrenamiento_svm_s=tiempo_entrenamiento_svm,
        tiempo_evaluacion_s=tiempo_evaluacion,
        tiempo_inferencia_ms=tiempo_inferencia_ms,
        tiempo_guardado_svm_s=tiempo_guardado_svm,
        tiempo_total_s=tiempo_total,
    )

    print(
        f"\n💾 Extractor CNN guardado en: "
        f"{CNN_EXTRACTOR_PATH}"
    )

    print(
        f"💾 SVM guardado en: "
        f"{CNN_SVM_PATH}"
    )

    print(
        f"📁 Reportes guardados en: "
        f"{H1_CNN_SVM_REPORTS_DIR}"
    )

    print("\n✅ Proceso completado.")


if __name__ == "__main__":
    main()