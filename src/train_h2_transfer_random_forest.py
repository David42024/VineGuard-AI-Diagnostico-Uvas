"""
train_h2_transfer_random_forest.py
──────────────────────────────────
H2 — Transfer Learning con MobileNetV2 + Random Forest

Flujo:
  1. Cargar y preprocesar imágenes.
  2. Balancear train mediante aumento dinámico.
  3. Extraer embeddings con MobileNetV2 preentrenada.
  4. Entrenar Random Forest sobre los embeddings.
  5. Evaluar sobre test real sin aumento.
  6. Generar reportes.
  7. Guardar extractor y clasificador.
"""

import io
import random
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import tensorflow as tf

from PIL import Image
from sklearn.ensemble import RandomForestClassifier
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
from sklearn.preprocessing import label_binarize
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input


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


SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))


from mantenedor import (
    BATCH_SIZE,
    CLASS_NAMES,
    H2_TRANSFER_RF_REPORTS_DIR,
    IMG_SIZE,
    MODELS_DIR,
    SEED,
    TARGET_TRAIN_SAMPLES_PER_CLASS,
    TEST_DIR,
    TRAIN_DIR,
    TRANSFER_EXTRACTOR_PATH,
    TRANSFER_RF_PATH,
)
from preprocesamiento_aumento import (
    pipeline_aumento,
    pipeline_preprocesamiento,
)
from evaluacion_visual import (
    save_confusion_matrix,
    save_normalized_confusion_matrix,
    save_precision_recall_curves,
    save_roc_curves,
)


NUM_CLASSES = len(CLASS_NAMES)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

NOMBRE_MODELO = (
    "H2 — Transfer Learning (MobileNetV2) + Random Forest"
)

RF_N_ESTIMATORS = 200
RF_MAX_DEPTH = None
RF_MIN_SAMPLES_SPLIT = 2
RF_MIN_SAMPLES_LEAF = 1
RF_CLASS_WEIGHT = None
RF_N_JOBS = -1


def configurar_semillas() -> None:
    """
    Configura las semillas utilizadas por Python,
    NumPy y TensorFlow.
    """
    random.seed(SEED)
    np.random.seed(SEED)
    tf.random.set_seed(SEED)


def obtener_rutas_clase(
    clase_dir: Path,
) -> list[Path]:
    """
    Devuelve las imágenes válidas de una clase.
    """
    if not clase_dir.exists():
        return []

    return sorted(
        ruta
        for ruta in clase_dir.iterdir()
        if ruta.is_file()
        and ruta.suffix.lower() in IMAGE_EXTENSIONS
    )


def convertir_para_mobilenet(
    imagen_normalizada: np.ndarray,
) -> np.ndarray:
    """
    Convierte una imagen normalizada en [0, 1]
    al formato esperado por MobileNetV2.
    """
    imagen_255 = (
        imagen_normalizada * 255.0
    ).clip(
        0,
        255,
    ).astype(
        np.float32
    )

    return preprocess_input(
        imagen_255
    )


def cargar_test_sin_aumento(
    split_dir: Path,
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Carga el test usando únicamente imágenes reales.

    No aplica aumento de datos.
    """
    imagenes = []
    etiquetas = []
    nombres_archivo = []

    for indice, clase in enumerate(CLASS_NAMES):
        clase_dir = split_dir / clase
        rutas = obtener_rutas_clase(
            clase_dir
        )

        if len(rutas) == 0:
            print(
                f"⚠️ La clase {clase} no contiene "
                "imágenes válidas en test."
            )
            continue

        for ruta in rutas:
            try:
                with Image.open(ruta) as imagen:
                    imagen_rgb = imagen.convert("RGB")

                    imagen_preprocesada = (
                        pipeline_preprocesamiento(
                            imagen_rgb
                        )
                    )

                    imagen_mobilenet = (
                        convertir_para_mobilenet(
                            imagen_preprocesada
                        )
                    )

                imagenes.append(
                    imagen_mobilenet
                )

                etiquetas.append(
                    indice
                )

                nombres_archivo.append(
                    ruta.name
                )

            except Exception as error:
                print(
                    f"⚠️ Error procesando "
                    f"{ruta.name}: {error}"
                )

    if len(imagenes) == 0:
        raise ValueError(
            "No se pudieron cargar imágenes de test."
        )

    X = np.asarray(
        imagenes,
        dtype=np.float32,
    )

    y = np.asarray(
        etiquetas,
        dtype=np.int32,
    )

    return X, y, nombres_archivo


def cargar_train_balanceado(
    split_dir: Path,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Carga todas las imágenes reales de train y genera
    nuevas versiones aumentadas hasta alcanzar el objetivo
    por clase.

    Las imágenes aumentadas no se guardan físicamente.
    """
    objetivo = TARGET_TRAIN_SAMPLES_PER_CLASS

    imagenes = []
    etiquetas = []

    resumen = []

    generador = random.Random(
        SEED
    )

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

    for indice, clase in enumerate(CLASS_NAMES):
        clase_dir = split_dir / clase
        rutas = obtener_rutas_clase(
            clase_dir
        )

        if len(rutas) == 0:
            raise ValueError(
                f"La clase {clase} no tiene imágenes "
                "válidas en entrenamiento."
            )

        cantidad_real = len(
            rutas
        )

        cantidad_aumentada = max(
            0,
            objetivo - cantidad_real,
        )

        # Imágenes reales
        for ruta in rutas:
            try:
                with Image.open(ruta) as imagen:
                    imagen_rgb = imagen.convert("RGB")

                    imagen_preprocesada = (
                        pipeline_preprocesamiento(
                            imagen_rgb
                        )
                    )

                    imagen_mobilenet = (
                        convertir_para_mobilenet(
                            imagen_preprocesada
                        )
                    )

                imagenes.append(
                    imagen_mobilenet
                )

                etiquetas.append(
                    indice
                )

            except Exception as error:
                print(
                    f"⚠️ Error procesando "
                    f"{ruta.name}: {error}"
                )

        # Imágenes aumentadas
        for _ in range(cantidad_aumentada):
            ruta = generador.choice(
                rutas
            )

            try:
                with Image.open(ruta) as imagen:
                    imagen_rgb = imagen.convert("RGB")

                    imagen_aumentada = (
                        pipeline_aumento(
                            imagen_rgb
                        )
                    )

                    imagen_mobilenet = (
                        convertir_para_mobilenet(
                            imagen_aumentada
                        )
                    )

                imagenes.append(
                    imagen_mobilenet
                )

                etiquetas.append(
                    indice
                )

            except Exception as error:
                print(
                    f"⚠️ Error aumentando "
                    f"{ruta.name}: {error}"
                )

        resumen.append(
            (
                clase,
                cantidad_real,
                cantidad_aumentada,
                cantidad_real + cantidad_aumentada,
            )
        )

        print(
            f"  {clase:<18}"
            f"{cantidad_real:>10}"
            f"{cantidad_aumentada:>12}"
            f"{cantidad_real + cantidad_aumentada:>17}"
        )

    total_reales = sum(
        fila[1]
        for fila in resumen
    )

    total_aumentadas = sum(
        fila[2]
        for fila in resumen
    )

    total_efectivo = sum(
        fila[3]
        for fila in resumen
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

    X = np.asarray(
        imagenes,
        dtype=np.float32,
    )

    y = np.asarray(
        etiquetas,
        dtype=np.int32,
    )

    permutacion = np.random.default_rng(
        SEED
    ).permutation(
        len(y)
    )

    X = X[permutacion]
    y = y[permutacion]

    return X, y


def crear_extractor_mobilenet() -> tf.keras.Model:
    """
    Crea un extractor de características basado en
    MobileNetV2 preentrenada con ImageNet.
    """
    base_model = MobileNetV2(
        input_shape=IMG_SIZE + (3,),
        include_top=False,
        weights="imagenet",
        pooling=None,
    )

    base_model.trainable = False

    inputs = tf.keras.Input(
        shape=IMG_SIZE + (3,),
        name="input_image",
    )

    x = base_model(
        inputs,
        training=False,
    )

    outputs = layers.GlobalAveragePooling2D(
        name="global_average_pooling"
    )(x)

    return tf.keras.Model(
        inputs=inputs,
        outputs=outputs,
        name="transfer_extractor_mobilenetv2",
    )


def extraer_embeddings_batch(
    extractor: tf.keras.Model,
    imagenes: np.ndarray,
    batch_size: int = BATCH_SIZE,
) -> np.ndarray:
    """
    Extrae embeddings por lotes para reducir el uso
    de memoria durante la inferencia de MobileNetV2.
    """
    if len(imagenes) == 0:
        raise ValueError(
            "No hay imágenes para extraer embeddings."
        )

    embeddings = []

    for inicio in range(
        0,
        len(imagenes),
        batch_size,
    ):
        lote = imagenes[
            inicio:inicio + batch_size
        ]

        lote_embeddings = extractor(
            lote,
            training=False,
        ).numpy()

        embeddings.append(
            lote_embeddings
        )

    return np.concatenate(
        embeddings,
        axis=0,
    )


def alinear_probabilidades(
    modelo: RandomForestClassifier,
    probabilidades: np.ndarray,
) -> np.ndarray:
    """
    Alinea las columnas de predict_proba con el orden
    definido en CLASS_NAMES.
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
    Calcula métricas globales, AUC y matriz
    de confusión.
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


def mostrar_resultados(
    y_test: np.ndarray,
    y_pred: np.ndarray,
    metricas: dict,
    tiempo_carga_preprocesamiento_s: float,
    tiempo_extraccion_embeddings_s: float,
    tiempo_entrenamiento_rf_s: float,
    tiempo_inferencia_rf_ms: float,
    tiempo_inferencia_pipeline_ms: float,
) -> None:
    """
    Muestra resultados y tiempos principales.
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
        "  Carga y preprocesamiento             : "
        f"{tiempo_carga_preprocesamiento_s:.2f}s"
    )

    print(
        "  Extracción de embeddings             : "
        f"{tiempo_extraccion_embeddings_s:.2f}s"
    )

    print(
        "  Entrenamiento Random Forest          : "
        f"{tiempo_entrenamiento_rf_s:.2f}s"
    )

    print(
        "  Inferencia RF por muestra            : "
        f"{tiempo_inferencia_rf_ms:.4f}ms"
    )

    print(
        "  Inferencia pipeline completo/muestra : "
        f"{tiempo_inferencia_pipeline_ms:.4f}ms"
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
    Guarda clasificación, matrices, curvas y
    predicciones individuales.
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
        H2_TRANSFER_RF_REPORTS_DIR
        / "reporte_clasificacion_h2_transfer_rf.csv"
    )

    pd.DataFrame(
        metricas["confusion_matrix"],
        index=CLASS_NAMES,
        columns=CLASS_NAMES,
    ).to_csv(
        H2_TRANSFER_RF_REPORTS_DIR
        / "confusion_h2_transfer_rf.csv"
    )

    save_confusion_matrix(
        y_test,
        y_pred,
        CLASS_NAMES,
        H2_TRANSFER_RF_REPORTS_DIR
        / "confusion_h2_transfer_rf.png",
    )

    save_normalized_confusion_matrix(
        y_test,
        y_pred,
        CLASS_NAMES,
        H2_TRANSFER_RF_REPORTS_DIR
        / "confusion_normalizada_h2_transfer_rf.png",
    )

    save_roc_curves(
        y_test,
        y_score,
        CLASS_NAMES,
        H2_TRANSFER_RF_REPORTS_DIR
        / "roc_h2_transfer_rf.png",
    )

    save_precision_recall_curves(
        y_test,
        y_score,
        CLASS_NAMES,
        H2_TRANSFER_RF_REPORTS_DIR
        / "precision_recall_h2_transfer_rf.png",
    )

    predicciones = pd.DataFrame({
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

    predicciones.to_csv(
        H2_TRANSFER_RF_REPORTS_DIR
        / "predicciones_h2_transfer_rf.csv",
        index=False,
    )


def guardar_importancias(
    modelo: RandomForestClassifier,
) -> None:
    """
    Guarda la importancia de los embeddings de
    MobileNetV2 según Random Forest.
    """
    importancias = modelo.feature_importances_

    indices = np.argsort(
        importancias
    )[::-1]

    importancia_df = pd.DataFrame({
        "embedding_index": indices,
        "embedding_name": [
            f"embedding_{indice}"
            for indice in indices
        ],
        "importancia": importancias[
            indices
        ],
        "ranking": np.arange(
            1,
            len(indices) + 1,
        ),
    })

    importancia_df.to_csv(
        H2_TRANSFER_RF_REPORTS_DIR
        / "importancia_embeddings_h2_transfer_rf.csv",
        index=False,
    )

    print(
        "\n  Top 10 embeddings más importantes:"
    )

    for posicion, fila in importancia_df.head(10).iterrows():
        print(
            f"  {posicion + 1:>2}. "
            f"Embedding "
            f"{int(fila['embedding_index']):<4} "
            f"importancia: "
            f"{fila['importancia']:.6f}"
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


def medir_inferencia_pipeline(
    extractor: tf.keras.Model,
    clasificador: RandomForestClassifier,
    X_test_imgs: np.ndarray,
) -> float:
    """
    Mide el tiempo promedio del pipeline completo:

    imagen ya cargada y preprocesada
    -> MobileNetV2
    -> embedding
    -> Random Forest

    No incluye lectura desde disco.
    """
    inicio = time.perf_counter()

    embeddings = extraer_embeddings_batch(
        extractor,
        X_test_imgs,
        batch_size=BATCH_SIZE,
    )

    clasificador.predict(
        embeddings
    )

    clasificador.predict_proba(
        embeddings
    )

    duracion = (
        time.perf_counter()
        - inicio
    )

    return (
        duracion
        / len(X_test_imgs)
    ) * 1000


def guardar_resumen_final(
    metricas: dict,
    tiempo_construccion_extractor_s: float,
    tiempo_carga_preprocesamiento_s: float,
    tiempo_extraccion_embeddings_s: float,
    tiempo_guardado_extractor_s: float,
    tiempo_entrenamiento_rf_s: float,
    tiempo_evaluacion_s: float,
    tiempo_inferencia_rf_ms: float,
    tiempo_inferencia_pipeline_ms: float,
    tiempo_guardado_rf_s: float,
    tiempo_total_s: float,
    n_train: int,
    n_test: int,
    n_features: int,
    extractor_size_mb: float,
    rf_size_mb: float,
) -> None:
    """
    Guarda métricas, tiempos, tamaños e
    hiperparámetros definitivos.
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

        "tiempo_construccion_extractor_s": round(
            tiempo_construccion_extractor_s,
            2,
        ),
        "tiempo_carga_preprocesamiento_s": round(
            tiempo_carga_preprocesamiento_s,
            2,
        ),
        "tiempo_extraccion_embeddings_s": round(
            tiempo_extraccion_embeddings_s,
            2,
        ),
        "tiempo_guardado_extractor_s": round(
            tiempo_guardado_extractor_s,
            4,
        ),
        "tiempo_entrenamiento_rf_s": round(
            tiempo_entrenamiento_rf_s,
            2,
        ),
        "tiempo_evaluacion_s": round(
            tiempo_evaluacion_s,
            2,
        ),
        "tiempo_inferencia_rf_ms": round(
            tiempo_inferencia_rf_ms,
            4,
        ),
        "tiempo_inferencia_pipeline_ms": round(
            tiempo_inferencia_pipeline_ms,
            4,
        ),
        "tiempo_guardado_rf_s": round(
            tiempo_guardado_rf_s,
            4,
        ),
        "tiempo_total_proceso_s": round(
            tiempo_total_s,
            2,
        ),

        "n_muestras_train": n_train,
        "n_muestras_test": n_test,
        "n_features_embedding": n_features,

        "extractor_size_mb": round(
            extractor_size_mb,
            3,
        ),
        "rf_size_mb": round(
            rf_size_mb,
            3,
        ),
        "tamano_total_modelos_mb": round(
            extractor_size_mb + rf_size_mb,
            3,
        ),

        "semilla": SEED,

        "arquitectura_extractor": "MobileNetV2",
        "pesos_preentrenados": "ImageNet",
        "extractor_trainable": False,
        "img_height": IMG_SIZE[0],
        "img_width": IMG_SIZE[1],
        "batch_size": BATCH_SIZE,
        "target_per_class": (
            TARGET_TRAIN_SAMPLES_PER_CLASS
        ),

        "n_estimators": RF_N_ESTIMATORS,
        "max_depth": "None",
        "min_samples_split": (
            RF_MIN_SAMPLES_SPLIT
        ),
        "min_samples_leaf": (
            RF_MIN_SAMPLES_LEAF
        ),
        "class_weight": "None",
        "n_jobs": RF_N_JOBS,
    }

    pd.DataFrame(
        [resumen]
    ).to_csv(
        H2_TRANSFER_RF_REPORTS_DIR
        / "resultados_h2_transfer_rf.csv",
        index=False,
    )


def mostrar_resumen_tiempos(
    tiempo_construccion_extractor_s: float,
    tiempo_carga_preprocesamiento_s: float,
    tiempo_extraccion_embeddings_s: float,
    tiempo_guardado_extractor_s: float,
    tiempo_entrenamiento_rf_s: float,
    tiempo_evaluacion_s: float,
    tiempo_inferencia_rf_ms: float,
    tiempo_inferencia_pipeline_ms: float,
    tiempo_guardado_rf_s: float,
    tiempo_total_s: float,
) -> None:
    """
    Muestra el resumen completo de tiempos.
    """
    print("\n" + "=" * 60)
    print("  RESUMEN DE TIEMPOS")
    print("=" * 60)

    print(
        "  Construcción del extractor          : "
        f"{tiempo_construccion_extractor_s:.2f} s"
    )

    print(
        "  Carga y preprocesamiento            : "
        f"{tiempo_carga_preprocesamiento_s:.2f} s"
    )

    print(
        "  Extracción de embeddings            : "
        f"{tiempo_extraccion_embeddings_s:.2f} s"
    )

    print(
        "  Guardado del extractor              : "
        f"{tiempo_guardado_extractor_s:.4f} s"
    )

    print(
        "  Entrenamiento Random Forest         : "
        f"{tiempo_entrenamiento_rf_s:.2f} s"
    )

    print(
        "  Evaluación completa y reportes      : "
        f"{tiempo_evaluacion_s:.2f} s"
    )

    print(
        "  Inferencia RF por muestra           : "
        f"{tiempo_inferencia_rf_ms:.4f} ms"
    )

    print(
        "  Inferencia pipeline por muestra     : "
        f"{tiempo_inferencia_pipeline_ms:.4f} ms"
    )

    print(
        "  Guardado del Random Forest          : "
        f"{tiempo_guardado_rf_s:.4f} s"
    )

    print(
        "  Tiempo total del proceso            : "
        f"{tiempo_total_s:.2f} s"
    )

    print("=" * 60)


def main() -> None:
    print("=" * 60)
    print(
        "  H2 — Transfer Learning + Random Forest "
        "— VineGuard AI"
    )
    print("=" * 60)

    configurar_semillas()

    MODELS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    H2_TRANSFER_RF_REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    TRANSFER_EXTRACTOR_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    TRANSFER_RF_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    inicio_total = time.perf_counter()

    # ─────────────────────────────────────────────
    # 1. Construcción del extractor
    # ─────────────────────────────────────────────
    print(
        "\n🔄 Construyendo extractor "
        "MobileNetV2 (ImageNet)..."
    )

    inicio_construccion_extractor = (
        time.perf_counter()
    )

    extractor = crear_extractor_mobilenet()

    tiempo_construccion_extractor = (
        time.perf_counter()
        - inicio_construccion_extractor
    )

    print(
        f"   Embedding dims: "
        f"{extractor.output_shape[-1]}"
    )

    # ─────────────────────────────────────────────
    # 2. Carga y preprocesamiento
    # ─────────────────────────────────────────────
    inicio_carga = time.perf_counter()

    print(
        "\n🔍 Cargando TRAIN con balanceo "
        f"a {TARGET_TRAIN_SAMPLES_PER_CLASS}/clase..."
    )

    X_train_imgs, y_train = (
        cargar_train_balanceado(
            TRAIN_DIR
        )
    )

    print(
        f"   Forma train: "
        f"{X_train_imgs.shape}"
    )

    print(
        "\n🔍 Cargando TEST sin aumento..."
    )

    (
        X_test_imgs,
        y_test,
        test_filenames,
    ) = cargar_test_sin_aumento(
        TEST_DIR
    )

    print(
        f"   Forma test: "
        f"{X_test_imgs.shape}"
    )

    if len(X_train_imgs) == 0:
        raise ValueError(
            "El conjunto train está vacío."
        )

    if len(X_test_imgs) == 0:
        raise ValueError(
            "El conjunto test está vacío."
        )

    if len(test_filenames) != len(y_test):
        raise ValueError(
            "La cantidad de nombres de test no coincide "
            "con las etiquetas."
        )

    tiempo_carga_preprocesamiento = (
        time.perf_counter()
        - inicio_carga
    )

    print("\n📋 Preprocesamiento:")
    print(
        "   - Train: RGB + resize + normalización "
        "+ aumento dinámico + preprocess_input"
    )
    print(
        "   - Train balanceado a "
        f"{TARGET_TRAIN_SAMPLES_PER_CLASS} "
        "muestras por clase"
    )
    print(
        "   - Test: imágenes reales sin aumento"
    )
    print(
        "   - Imágenes aumentadas guardadas "
        "físicamente: No"
    )

    # ─────────────────────────────────────────────
    # 3. Extracción de embeddings
    # ─────────────────────────────────────────────
    print(
        "\n⚙️ Extrayendo embeddings..."
    )

    inicio_embeddings = time.perf_counter()

    X_train = extraer_embeddings_batch(
        extractor,
        X_train_imgs,
        batch_size=BATCH_SIZE,
    )

    X_test = extraer_embeddings_batch(
        extractor,
        X_test_imgs,
        batch_size=BATCH_SIZE,
    )

    tiempo_extraccion_embeddings = (
        time.perf_counter()
        - inicio_embeddings
    )

    if X_train.shape[1] != X_test.shape[1]:
        raise ValueError(
            "Los embeddings de train y test "
            "tienen dimensiones diferentes."
        )

    print(
        f"   Embeddings train: {X_train.shape}"
    )

    print(
        f"   Embeddings test:  {X_test.shape}"
    )

    # ─────────────────────────────────────────────
    # 4. Guardado del extractor
    # ─────────────────────────────────────────────
    inicio_guardado_extractor = (
        time.perf_counter()
    )

    extractor.save(
        str(TRANSFER_EXTRACTOR_PATH)
    )

    tiempo_guardado_extractor = (
        time.perf_counter()
        - inicio_guardado_extractor
    )

    extractor_size_mb = obtener_tamano_mb(
        TRANSFER_EXTRACTOR_PATH
    )

    print(
        f"\n💾 Extractor guardado en: "
        f"{TRANSFER_EXTRACTOR_PATH}"
    )

    # ─────────────────────────────────────────────
    # 5. Entrenamiento Random Forest
    # ─────────────────────────────────────────────
    print(
        "\n🚀 Entrenando Random Forest "
        "sobre embeddings MobileNetV2..."
    )

    rf = RandomForestClassifier(
        n_estimators=RF_N_ESTIMATORS,
        max_depth=RF_MAX_DEPTH,
        min_samples_split=RF_MIN_SAMPLES_SPLIT,
        min_samples_leaf=RF_MIN_SAMPLES_LEAF,
        class_weight=RF_CLASS_WEIGHT,
        n_jobs=RF_N_JOBS,
        random_state=SEED,
    )

    inicio_entrenamiento_rf = (
        time.perf_counter()
    )

    rf.fit(
        X_train,
        y_train,
    )

    tiempo_entrenamiento_rf = (
        time.perf_counter()
        - inicio_entrenamiento_rf
    )

    print(
        f"   ✅ Random Forest entrenado en "
        f"{tiempo_entrenamiento_rf:.2f}s"
    )

    # ─────────────────────────────────────────────
    # 6. Evaluación completa
    # Incluye inferencia RF, métricas y reportes.
    # ─────────────────────────────────────────────
    inicio_evaluacion = time.perf_counter()

    inicio_inferencia_rf = time.perf_counter()

    y_pred = rf.predict(
        X_test
    )

    probabilidades_originales = rf.predict_proba(
        X_test
    )

    duracion_inferencia_rf = (
        time.perf_counter()
        - inicio_inferencia_rf
    )

    tiempo_inferencia_rf_ms = (
        duracion_inferencia_rf
        / len(y_pred)
    ) * 1000

    y_score = alinear_probabilidades(
        rf,
        probabilidades_originales,
    )

    tiempo_inferencia_pipeline_ms = (
        medir_inferencia_pipeline(
            extractor,
            rf,
            X_test_imgs,
        )
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
        tiempo_carga_preprocesamiento_s=(
            tiempo_carga_preprocesamiento
        ),
        tiempo_extraccion_embeddings_s=(
            tiempo_extraccion_embeddings
        ),
        tiempo_entrenamiento_rf_s=(
            tiempo_entrenamiento_rf
        ),
        tiempo_inferencia_rf_ms=(
            tiempo_inferencia_rf_ms
        ),
        tiempo_inferencia_pipeline_ms=(
            tiempo_inferencia_pipeline_ms
        ),
    )

    guardar_importancias(
        rf
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
    # 7. Guardado del Random Forest
    # ─────────────────────────────────────────────
    inicio_guardado_rf = time.perf_counter()

    joblib.dump(
        rf,
        TRANSFER_RF_PATH,
    )

    tiempo_guardado_rf = (
        time.perf_counter()
        - inicio_guardado_rf
    )

    rf_size_mb = obtener_tamano_mb(
        TRANSFER_RF_PATH
    )

    tiempo_total = (
        time.perf_counter()
        - inicio_total
    )

    # ─────────────────────────────────────────────
    # 8. Guardar resumen final
    # ─────────────────────────────────────────────
    guardar_resumen_final(
        metricas=metricas,
        tiempo_construccion_extractor_s=(
            tiempo_construccion_extractor
        ),
        tiempo_carga_preprocesamiento_s=(
            tiempo_carga_preprocesamiento
        ),
        tiempo_extraccion_embeddings_s=(
            tiempo_extraccion_embeddings
        ),
        tiempo_guardado_extractor_s=(
            tiempo_guardado_extractor
        ),
        tiempo_entrenamiento_rf_s=(
            tiempo_entrenamiento_rf
        ),
        tiempo_evaluacion_s=(
            tiempo_evaluacion
        ),
        tiempo_inferencia_rf_ms=(
            tiempo_inferencia_rf_ms
        ),
        tiempo_inferencia_pipeline_ms=(
            tiempo_inferencia_pipeline_ms
        ),
        tiempo_guardado_rf_s=(
            tiempo_guardado_rf
        ),
        tiempo_total_s=tiempo_total,
        n_train=X_train.shape[0],
        n_test=X_test.shape[0],
        n_features=X_train.shape[1],
        extractor_size_mb=extractor_size_mb,
        rf_size_mb=rf_size_mb,
    )

    mostrar_resumen_tiempos(
        tiempo_construccion_extractor_s=(
            tiempo_construccion_extractor
        ),
        tiempo_carga_preprocesamiento_s=(
            tiempo_carga_preprocesamiento
        ),
        tiempo_extraccion_embeddings_s=(
            tiempo_extraccion_embeddings
        ),
        tiempo_guardado_extractor_s=(
            tiempo_guardado_extractor
        ),
        tiempo_entrenamiento_rf_s=(
            tiempo_entrenamiento_rf
        ),
        tiempo_evaluacion_s=(
            tiempo_evaluacion
        ),
        tiempo_inferencia_rf_ms=(
            tiempo_inferencia_rf_ms
        ),
        tiempo_inferencia_pipeline_ms=(
            tiempo_inferencia_pipeline_ms
        ),
        tiempo_guardado_rf_s=(
            tiempo_guardado_rf
        ),
        tiempo_total_s=tiempo_total,
    )

    print(
        f"\n💾 Extractor guardado en: "
        f"{TRANSFER_EXTRACTOR_PATH}"
    )

    print(
        f"💾 Random Forest guardado en: "
        f"{TRANSFER_RF_PATH}"
    )

    print(
        f"📁 Reportes guardados en: "
        f"{H2_TRANSFER_RF_REPORTS_DIR}"
    )

    print("\n✅ Proceso completado.")


if __name__ == "__main__":
    main()