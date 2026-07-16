import sys
from pathlib import Path

from fastapi import APIRouter, Depends

from backend.core.security import get_current_user, TokenData

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.mantenedor import (
    REPORTS_DIR,
    EDA_DIR,
    MODELOS_DIR,
    TUNING_DIR,
    ESTADISTICA_DIR,
    PREPROCESSING_DIR,
    CROSS_VALIDATION_DIR,
)

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])

PIPELINE_STAGES = [
    {
        "id": "eda",
        "name": "EDA (Análisis Exploratorio)",
        "dir": EDA_DIR,
        "check_files": ["resumen_dataset.csv", "distribucion_clases.png"],
    },
    {
        "id": "preprocessing",
        "name": "Preprocesamiento",
        "dir": PREPROCESSING_DIR,
        "check_files": ["ejemplos_aumento_datos.png"],
    },
    {
        "id": "tuning",
        "name": "Tuning de Hiperparámetros",
        "dir": TUNING_DIR,
        "check_files": ["mejores_hiperparametros.csv", "comparacion_mejores_hiperparametros.png"],
    },
    {
        "id": "models",
        "name": "Modelos ML Clásicos",
        "dir": MODELOS_DIR,
        "check_files": ["ranking_modelos.csv"],
    },
    {
        "id": "cross_validation",
        "name": "Validación Cruzada",
        "dir": CROSS_VALIDATION_DIR,
        "check_files": ["cross_validation_resultados.csv", "cross_validation_por_fold.csv"],
    },
    {
        "id": "statistics",
        "name": "Estadística",
        "dir": ESTADISTICA_DIR,
        "check_files": ["mcnemar_resultados.csv", "intervalos_confianza_bootstrap.csv"],
    },
]


def _check_stage(stage: dict) -> dict:
    sdir = stage["dir"]
    files = stage["check_files"]
    completed = all((sdir / f).exists() for f in files)
    existing_files = []
    missing_files = []
    for f in files:
        if (sdir / f).exists():
            existing_files.append(f)
        else:
            missing_files.append(f)
    return {
        "id": stage["id"],
        "name": stage["name"],
        "completed": completed,
        "existing_files": existing_files,
        "missing_files": missing_files,
    }


@router.get("/status")
def get_pipeline_status(current_user: TokenData = Depends(get_current_user)):
    stages = [_check_stage(s) for s in PIPELINE_STAGES]
    total = len(stages)
    completed = sum(1 for s in stages if s["completed"])
    return {
        "total_stages": total,
        "completed_stages": completed,
        "progress_pct": round(completed / total * 100, 1) if total else 0,
        "stages": stages,
    }


@router.get("/stages")
def get_pipeline_stages(current_user: TokenData = Depends(get_current_user)):
    stages = []
    for s in PIPELINE_STAGES:
        info = _check_stage(s)
        report_files = []
        if s["dir"].exists():
            report_files = sorted(
                [str(f.relative_to(REPORTS_DIR)) for f in s["dir"].iterdir() if f.is_file()]
            )
        info["report_files"] = report_files
        info["directory"] = str(s["dir"])
        stages.append(info)
    return {"stages": stages}
