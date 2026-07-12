from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_ORIGINAL_DIR = BASE_DIR / "dataset_original"
DATASET_DIR = BASE_DIR / "dataset"

TRAIN_DIR = DATASET_DIR / "train"
TEST_DIR = DATASET_DIR / "test"

MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
EDA_DIR = REPORTS_DIR / "eda"
MODELOS_DIR = REPORTS_DIR / "modelos"
ESTADISTICA_DIR = REPORTS_DIR / "estadistica"
PREPROCESSING_DIR = REPORTS_DIR / "preprocessing"

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42

MAX_IMAGES_PER_CLASS = None
TARGET_TRAIN_SAMPLES_PER_CLASS = 1500

CLASS_NAMES = ["Black_rot", "Esca", "Healthy", "Leaf_blight"]

CLASS_FOLDER_MAP = {
    "Grape___Black_rot": "Black_rot",
    "Grape___Esca_(Black_Measles)": "Esca",
    "Grape___healthy": "Healthy",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "Leaf_blight",
}

SCALER_PATH = MODELS_DIR / "scaler.pkl"
SVM_SCALER_PATH = MODELS_DIR / "svm_scaler.pkl"
KNN_SCALER_PATH = MODELS_DIR / "knn_scaler.pkl"
SVM_MODEL_PATH = MODELS_DIR / "svm_model.pkl"
RF_MODEL_PATH = MODELS_DIR / "random_forest_model.pkl"
KNN_MODEL_PATH = MODELS_DIR / "knn_model.pkl"

CNN_EXTRACTOR_PATH = MODELS_DIR / "cnn_feature_extractor.h5"
CNN_SVM_PATH = MODELS_DIR / "cnn_svm_model.pkl"

TRANSFER_EXTRACTOR_PATH = MODELS_DIR / "transfer_feature_extractor.h5"
TRANSFER_RF_PATH = MODELS_DIR / "transfer_random_forest_model.pkl"