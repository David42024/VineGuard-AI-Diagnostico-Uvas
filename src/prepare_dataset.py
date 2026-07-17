"""
prepare_dataset.py
──────────────────
Divide el dataset original en:
  • 80 % train
  • 20 % test

No se crea carpeta 'val'. Los modelos que necesiten validación interna
usan validation_split durante el entrenamiento.
"""

import shutil
import random
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from mantenedor import (
    DATASET_ORIGINAL_DIR,
    DATASET_DIR,
    TRAIN_DIR,
    TEST_DIR,
    SEED,
    CLASS_FOLDER_MAP,
    MAX_IMAGES_PER_CLASS,
)

TRAIN_RATIO = 0.80
TEST_RATIO = 0.20

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def limpiar_dataset():
    """Elimina el dataset procesado y recrea las carpetas train y test."""
    if DATASET_DIR.exists():
        shutil.rmtree(DATASET_DIR)

    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)


def obtener_imagenes(carpeta):
    """Retorna lista de imágenes válidas dentro de una carpeta."""
    return [
        img for img in carpeta.iterdir()
        if img.is_file() and img.suffix.lower() in IMAGE_EXTENSIONS
    ]


def copiar_split(imagenes, destino):
    """Copia una lista de imágenes al directorio destino."""
    destino.mkdir(parents=True, exist_ok=True)
    for img in imagenes:
        shutil.copy2(img, destino / img.name)


def verificar_solapamiento():
    """Verifica que no haya imágenes repetidas entre train y test."""
    train_names = {
        (p.parent.name, p.name)
        for p in TRAIN_DIR.rglob("*")
        if p.is_file()
    }

    test_names = {
        (p.parent.name, p.name)
        for p in TEST_DIR.rglob("*")
        if p.is_file()
    }

    overlap = train_names & test_names

    if overlap:
        raise RuntimeError(
            f"Se detectaron {len(overlap)} imágenes repetidas entre train y test."
        )

    print("\n✅ Solapamiento entre train y test: 0")


def preparar_dataset():
    random.seed(SEED)

    if not DATASET_ORIGINAL_DIR.exists():
        raise FileNotFoundError(
            f"No existe la carpeta: {DATASET_ORIGINAL_DIR}\n"
            "Crea dataset_original/ y coloca dentro las carpetas originales."
        )

    limpiar_dataset()

    resumen = []

    for carpeta_original, clase_limpia in CLASS_FOLDER_MAP.items():
        origen = DATASET_ORIGINAL_DIR / carpeta_original

        if not origen.exists():
            print(f"⚠️  No se encontró la carpeta: {origen}")
            continue

        imagenes = obtener_imagenes(origen)

        if not imagenes:
            print(f"⚠️  La carpeta {origen} no tiene imágenes válidas.")
            continue

        random.shuffle(imagenes)

        total_original = len(imagenes)

        # Limitar la cantidad de imágenes por clase
        if MAX_IMAGES_PER_CLASS is not None:
            imagenes = imagenes[:MAX_IMAGES_PER_CLASS]

        total_usado = len(imagenes)

        train_end = int(total_usado * TRAIN_RATIO)

        train_imgs = imagenes[:train_end]
        test_imgs = imagenes[train_end:]

        copiar_split(train_imgs, TRAIN_DIR / clase_limpia)
        copiar_split(test_imgs, TEST_DIR / clase_limpia)

        resumen.append((
            clase_limpia,
            len(train_imgs),
            len(test_imgs),
            total_usado,
            total_original,
        ))

    verificar_solapamiento()

    print("\n✅ Dataset preparado correctamente\n")
    print(f"{'Clase':<18} {'Train':>6} {'Test':>6} {'Usadas':>8} {'Originales':>10}")
    print("─" * 52)

    for clase, train, test, total_usado, total_original in resumen:
        print(f"{clase:<18} {train:>6} {test:>6} {total_usado:>8} {total_original:>10}")

    total_train = sum(r[1] for r in resumen)
    total_test = sum(r[2] for r in resumen)
    total_usado_global = sum(r[3] for r in resumen)

    print("─" * 52)
    print(f"{'TOTAL':<18} {total_train:>6} {total_test:>6} {total_usado_global:>8}")

    train_pct = total_train / total_usado_global * 100
    test_pct = total_test / total_usado_global * 100

    print(f"\n📊 Proporción real: {train_pct:.2f}% train / {test_pct:.2f}% test")
    print(f"\n📁 Train: {TRAIN_DIR}")
    print(f"📁 Test:  {TEST_DIR}")


if __name__ == "__main__":
    preparar_dataset()