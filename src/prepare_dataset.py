import shutil
import random

from mantenedor import (
    DATASET_ORIGINAL_DIR,
    DATASET_DIR,
    TRAIN_DIR,
    VAL_DIR,
    TEST_DIR,
    SEED,
    CLASS_FOLDER_MAP,
    MAX_IMAGES_PER_CLASS,
)

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def limpiar_dataset():
    if DATASET_DIR.exists():
        shutil.rmtree(DATASET_DIR)

    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    VAL_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)


def obtener_imagenes(carpeta):
    return [
        img for img in carpeta.iterdir()
        if img.is_file() and img.suffix.lower() in IMAGE_EXTENSIONS
    ]


def copiar_split(imagenes, destino):
    destino.mkdir(parents=True, exist_ok=True)

    for img in imagenes:
        shutil.copy2(img, destino / img.name)


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
            print(f"⚠️ No se encontró la carpeta: {origen}")
            continue

        imagenes = obtener_imagenes(origen)

        if not imagenes:
            print(f"⚠️ La carpeta {origen} no tiene imágenes válidas.")
            continue

        random.shuffle(imagenes)

        total_original = len(imagenes)

        # Limitar la cantidad de imágenes por clase
        if MAX_IMAGES_PER_CLASS is not None:
            imagenes = imagenes[:MAX_IMAGES_PER_CLASS]

        total_usado = len(imagenes)

        train_end = int(total_usado * TRAIN_RATIO)
        val_end = train_end + int(total_usado * VAL_RATIO)

        train_imgs = imagenes[:train_end]
        val_imgs = imagenes[train_end:val_end]
        test_imgs = imagenes[val_end:]

        copiar_split(train_imgs, TRAIN_DIR / clase_limpia)
        copiar_split(val_imgs, VAL_DIR / clase_limpia)
        copiar_split(test_imgs, TEST_DIR / clase_limpia)

        resumen.append((
            clase_limpia,
            len(train_imgs),
            len(val_imgs),
            len(test_imgs),
            total_usado,
            total_original
        ))

    print("\n✅ Dataset preparado correctamente\n")
    print("Clase\t\tTrain\tVal\tTest\tUsadas\tOriginales")
    print("-" * 75)

    for clase, train, val, test, total_usado, total_original in resumen:
        print(
            f"{clase:12}\t{train}\t{val}\t{test}\t{total_usado}\t{total_original}"
        )


if __name__ == "__main__":
    preparar_dataset()