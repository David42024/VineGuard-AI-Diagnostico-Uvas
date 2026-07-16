import sys
from pathlib import Path
from typing import Optional

_SRC_DIR = Path(__file__).resolve().parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from mantenedor import (
    CLASS_NAMES,
    IMG_SIZE,
    MODELS_DIR,
    M1_SVM_TUNING_PATH,
    M2_RF_TUNING_PATH,
    M3_KNN_TUNING_PATH,
    H2_RF_TUNING_PATH,
    H2_EXTRACTOR_TUNING_PATH,
    CNN_EXTRACTOR_PATH,
    CNN_SVM_PATH,
    M1_SVM_REPORTS_DIR,
    M2_RF_REPORTS_DIR,
    M3_KNN_REPORTS_DIR,
    H1_CNN_SVM_REPORTS_DIR,
    H2_TRANSFER_RF_REPORTS_DIR,
)

MODEL_KEYS = ["M1", "M2", "M3", "H1", "H2"]

MODEL_DISPLAY_NAMES = {
    "M1": "M1 - SVM",
    "M2": "M2 - Random Forest",
    "M3": "M3 - KNN",
    "H1": "H1 - CNN + SVM",
    "H2": "H2 - Transfer + RF",
}

MODEL_TYPES = {
    "M1": "Classic ML (SVM)",
    "M2": "Classic ML (Random Forest)",
    "M3": "Classic ML (KNN)",
    "H1": "Hybrid (CNN + SVM)",
    "H2": "Hybrid (Transfer + RF)",
}

MODEL_REPORT_DIRS = {
    "M1": M1_SVM_REPORTS_DIR,
    "M2": M2_RF_REPORTS_DIR,
    "M3": M3_KNN_REPORTS_DIR,
    "H1": H1_CNN_SVM_REPORTS_DIR,
    "H2": H2_TRANSFER_RF_REPORTS_DIR,
}

MODEL_ARTIFACTS = {
    "M1": [
        ("modelo_entrenado", M1_SVM_TUNING_PATH),
    ],
    "M2": [
        ("modelo_entrenado", M2_RF_TUNING_PATH),
    ],
    "M3": [
        ("modelo_entrenado", M3_KNN_TUNING_PATH),
    ],
    "H1": [
        ("extractor_cnn", CNN_EXTRACTOR_PATH),
        ("clasificador_svm", CNN_SVM_PATH),
    ],
    "H2": [
        ("extractor_transfer", H2_EXTRACTOR_TUNING_PATH),
        ("clasificador_rf", H2_RF_TUNING_PATH),
    ],
}


def get_model_paths(model_key: str) -> list[tuple[str, Path]]:
    return MODEL_ARTIFACTS.get(model_key, [])


def check_model_files(model_key: str) -> dict[str, bool]:
    artifacts = get_model_paths(model_key)
    return {name: path.exists() for name, path in artifacts}


def get_missing_files(model_key: str) -> list[str]:
    return [name for name, path in MODEL_ARTIFACTS.get(model_key, []) if not path.exists()]


def all_models_available() -> dict[str, bool]:
    return {mk: all(p.exists() for _, p in paths) for mk, paths in MODEL_ARTIFACTS.items()}


def get_model_artifact_path(model_key: str, artifact_name: str) -> Optional[Path]:
    for name, path in MODEL_ARTIFACTS.get(model_key, []):
        if name == artifact_name:
            return path
    return None
