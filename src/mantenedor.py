from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_ORIGINAL_DIR = BASE_DIR / "dataset_original"
DATASET_DIR = BASE_DIR / "dataset"

TRAIN_DIR = DATASET_DIR / "train"
VAL_DIR = DATASET_DIR / "val"
TEST_DIR = DATASET_DIR / "test"

MODELS_DIR = BASE_DIR / "models"

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42

# Cantidad máxima de imágenes por clase
MAX_IMAGES_PER_CLASS = 150

CLASS_NAMES = ["Black_rot", "Esca", "Healthy", "Leaf_blight"]

CLASS_FOLDER_MAP = {
    "Grape___Black_rot": "Black_rot",
    "Grape___Esca_(Black_Measles)": "Esca",
    "Grape___healthy": "Healthy",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "Leaf_blight",
}