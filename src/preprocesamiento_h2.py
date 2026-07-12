"""
preprocesamiento_h2.py
-----------------
Módulo compartido para preprocesamiento de imágenes y extracción de embeddings
para el modelo H2 (MobileNetV2 congelada + Random Forest).
"""

import time
import numpy as np
import tensorflow as tf
from pathlib import Path

from mantenedor import (
    CLASS_NAMES,
    IMG_SIZE,
    BATCH_SIZE
)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


def escanear_directorio(directorio: Path) -> tuple[list[str], list[int]]:
    """
    Escanea un directorio (TRAIN_DIR o TEST_DIR) y devuelve rutas de imágenes y etiquetas.
    """
    rutas = []
    etiquetas = []

    for indice, clase in enumerate(CLASS_NAMES):
        clase_dir = directorio / clase
        if not clase_dir.exists():
            raise FileNotFoundError(
                f"No existe el directorio: {clase_dir}"
            )

        imagenes = sorted(
            archivo
            for archivo in clase_dir.iterdir()
            if archivo.is_file()
            and archivo.suffix.lower() in IMAGE_EXTENSIONS
        )

        if len(imagenes) == 0:
            raise ValueError(
                f"La clase {clase} no tiene imágenes."
            )

        rutas.extend(
            str(imagen)
            for imagen in imagenes
        )

        etiquetas.extend(
            [indice] * len(imagenes)
        )

    return rutas, etiquetas


def cargar_imagen_mobilenet(
    ruta: tf.Tensor,
    etiqueta: tf.Tensor,
) -> tuple[tf.Tensor, tf.Tensor]:
    """
    Lee y transforma una imagen al formato esperado por MobileNetV2.
    """
    contenido = tf.io.read_file(ruta)
    imagen = tf.image.decode_image(
        contenido,
        channels=3,
        expand_animations=False,
    )
    imagen.set_shape([None, None, 3])
    imagen = tf.image.resize(imagen, IMG_SIZE)
    imagen = tf.cast(imagen, tf.float32)
    imagen = tf.keras.applications.mobilenet_v2.preprocess_input(imagen)
    return imagen, etiqueta


def construir_dataset_h2(
    rutas: list[str],
    etiquetas: list[int],
) -> tf.data.Dataset:
    """
    Construye un dataset de TensorFlow para extraer embeddings de MobileNetV2.
    """
    dataset = tf.data.Dataset.from_tensor_slices(
        (
            tf.constant(rutas),
            tf.constant(etiquetas, dtype=tf.int32),
        )
    )

    dataset = dataset.map(
        cargar_imagen_mobilenet,
        num_parallel_calls=tf.data.AUTOTUNE,
    )

    dataset = dataset.batch(
        BATCH_SIZE,
        drop_remainder=False,
    )

    dataset = dataset.prefetch(
        tf.data.AUTOTUNE
    )

    return dataset


def crear_extractor_h2() -> tf.keras.Model:
    """
    Crea MobileNetV2 preentrenada y congelada.
    """
    extractor = tf.keras.applications.MobileNetV2(
        input_shape=IMG_SIZE + (3,),
        include_top=False,
        weights="imagenet",
        pooling="avg",
    )

    extractor.trainable = False
    return extractor


def extraer_embeddings(
    directorio: Path,
    extractor: tf.keras.Model,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extrae embeddings reales de 1280 dimensiones para todas las imágenes
    del directorio especificado.
    """
    print(f"🔄 Preparando embeddings para H2 desde {directorio}...")

    rutas, etiquetas = escanear_directorio(directorio)
    dataset = construir_dataset_h2(rutas, etiquetas)

    embeddings_batches = []
    etiquetas_batches = []

    inicio = time.perf_counter()

    for imagenes_batch, etiquetas_batch in dataset:
        embeddings = extractor(
            imagenes_batch,
            training=False,
        )

        embeddings_batches.append(
            embeddings.numpy()
        )

        etiquetas_batches.append(
            etiquetas_batch.numpy()
        )

    tiempo = time.perf_counter() - inicio

    X_h2 = np.concatenate(
        embeddings_batches,
        axis=0,
    ).astype(
        np.float32
    )

    y_h2 = np.concatenate(
        etiquetas_batches,
        axis=0,
    ).astype(
        np.int32
    )

    print(f"  ✅ Embeddings H2: {X_h2.shape}")
    print(f"  ✅ Tiempo de extracción: {tiempo:.2f}s")

    return X_h2, y_h2


def extraer_embedding_una_imagen(ruta_imagen: Path, extractor: tf.keras.Model) -> np.ndarray:
    """
    Extrae el embedding de 1280 dimensiones para una sola imagen.
    """
    img_tensor = tf.convert_to_tensor(str(ruta_imagen), dtype=tf.string)
    img_preproc, _ = cargar_imagen_mobilenet(img_tensor, tf.constant(0))
    # Añadir dimensión de batch
    img_batch = tf.expand_dims(img_preproc, 0)
    embedding = extractor.predict(img_batch, verbose=0)
    return embedding.astype(np.float32)
