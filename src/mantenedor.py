from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_ORIGINAL_DIR = BASE_DIR / "dataset_original"
DATASET_DIR = BASE_DIR / "dataset"

TRAIN_DIR = DATASET_DIR / "train"
TEST_DIR = DATASET_DIR / "test"

MODELS_DIR = BASE_DIR / "models"
# ─── Escaladores de características clásicas ───────────────────────────
SCALER_PATH = MODELS_DIR / "scaler.pkl"

# Escaladores específicos de los modelos clásicos anteriores.
# Los modelos ajustados mediante tuning ya incluyen el scaler
# dentro del Pipeline, pero se conservan estas rutas por compatibilidad.
SVM_SCALER_PATH = MODELS_DIR / "scaler_svm.pkl"
KNN_SCALER_PATH = MODELS_DIR / "scaler_knn.pkl"

# ─── Rutas de modelos clásicos ──────────────────────────────────────────
SVM_MODEL_PATH = MODELS_DIR / "svm_model.pkl"
RF_MODEL_PATH = MODELS_DIR / "random_forest_model.pkl"
KNN_MODEL_PATH = MODELS_DIR / "knn_model.pkl"


REPORTS_DIR = BASE_DIR / "reports"
EDA_DIR = REPORTS_DIR / "eda"
MODELOS_DIR = REPORTS_DIR / "modelos"
TUNING_DIR = MODELOS_DIR / "tuning"
ESTADISTICA_DIR = REPORTS_DIR / "estadistica"
PREPROCESSING_DIR = REPORTS_DIR / "preprocessing"

# ─── Artefactos del tuning (fuente única de verdad para nombres de archivo) ──
M1_SVM_TUNING_PATH = TUNING_DIR / "mejor_m1_svm_tuning.pkl"
M2_RF_TUNING_PATH = TUNING_DIR / "mejor_m2_random_forest_tuning.pkl"
M3_KNN_TUNING_PATH = TUNING_DIR / "mejor_m3_knn_tuning.pkl"
H2_RF_TUNING_PATH = TUNING_DIR / "mejor_h2_transfer_rf_tuning.pkl"
H2_EXTRACTOR_TUNING_PATH = TUNING_DIR / "transfer_feature_extractor.keras"

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42

# ─── Hiperparámetros de modelos clásicos (fuente única) ────────────────
M1_SVM_KERNEL = "rbf"
M1_SVM_C = 10.0
M1_SVM_GAMMA = "scale"
M1_SVM_CLASS_WEIGHT = "balanced"

M2_RF_N_ESTIMATORS = 200
M2_RF_MAX_DEPTH = None
M2_RF_MIN_SAMPLES_SPLIT = 2
M2_RF_MIN_SAMPLES_LEAF = 1
M2_RF_CLASS_WEIGHT = None

M3_KNN_N_NEIGHBORS = 5
M3_KNN_METRIC = "euclidean"
M3_KNN_WEIGHTS = "distance"
M3_KNN_ALGORITHM = "auto"
M3_KNN_P = 2

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

MAX_IMAGES_PER_CLASS = None
TARGET_TRAIN_SAMPLES_PER_CLASS = 1500

CLASS_NAMES = ["Black_rot", "Esca", "Healthy", "Leaf_blight"]

CLASS_FOLDER_MAP = {
    "Grape___Black_rot": "Black_rot",
    "Grape___Esca_(Black_Measles)": "Esca",
    "Grape___healthy": "Healthy",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "Leaf_blight",
}

CNN_EXTRACTOR_PATH = MODELS_DIR / "cnn_feature_extractor.h5"
CNN_SVM_PATH = MODELS_DIR / "cnn_svm_model.pkl"
TRANSFER_EXTRACTOR_PATH = MODELS_DIR / "transfer_feature_extractor.h5"
TRANSFER_RF_PATH = MODELS_DIR / "transfer_random_forest_model.pkl"

# ─── Directorios de reportes por modelo ────────────────────────────────
M1_SVM_REPORTS_DIR = MODELOS_DIR / "m1_svm"
M2_RF_REPORTS_DIR = MODELOS_DIR / "m2_random_forest"
M3_KNN_REPORTS_DIR = MODELOS_DIR / "m3_knn"
H1_CNN_SVM_REPORTS_DIR = MODELOS_DIR / "h1_cnn_svm"
H2_TRANSFER_RF_REPORTS_DIR = MODELOS_DIR / "h2_transfer_rf"
COMPARATIVOS_DIR = MODELOS_DIR / "comparativos"
CROSS_VALIDATION_DIR = MODELOS_DIR / "cross_validation"
CROSS_VALIDATION_RESULTADOS_PATH = CROSS_VALIDATION_DIR / "cross_validation_resultados.csv"