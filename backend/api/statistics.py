import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.security import get_current_user, TokenData
from backend.database.session import get_db
from backend.repositories.diagnostic_repository import DiagnosticRepository
from backend.repositories.report_repository import ReportRepository

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.mantenedor import ESTADISTICA_DIR, MODELOS_DIR, CROSS_VALIDATION_DIR

router = APIRouter(prefix="/api/v1/statistics", tags=["statistics"])


@router.get("/summary")
def get_summary(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    report_repo = ReportRepository()
    diag_repo = DiagnosticRepository(db)

    stats = diag_repo.get_admin_stats()
    distribution = diag_repo.get_disease_distribution()
    diagnostics_by_date = diag_repo.get_diagnostics_by_date(30)

    return {
        "general_stats": stats,
        "disease_distribution": distribution,
        "diagnostics_by_date": diagnostics_by_date,
        "best_model": report_repo.get_best_model(),
        "ranking": report_repo.get_ranking(),
        "cross_validation": report_repo.get_cross_validation(),
    }


@router.get("/model-comparison")
def get_model_comparison(current_user: TokenData = Depends(get_current_user)):
    report_repo = ReportRepository()
    return {
        "ranking": report_repo.get_model_comparison_ranking(),
        "effect_size": report_repo.get_effect_size(),
        "diebold_mariano": report_repo.get_diebold_mariano(),
    }


@router.get("/cross-validation")
def get_cross_validation(current_user: TokenData = Depends(get_current_user)):
    report_repo = ReportRepository()
    return {
        "resultados": report_repo.get_cross_validation(),
        "por_fold": report_repo.get_cross_validation_by_fold(),
    }


@router.get("/bootstrap")
def get_bootstrap(current_user: TokenData = Depends(get_current_user)):
    report_repo = ReportRepository()
    return {"bootstrap_intervals": report_repo.get_bootstrap_intervals() or []}


@router.get("/mcnemar")
def get_mcnemar(current_user: TokenData = Depends(get_current_user)):
    report_repo = ReportRepository()
    return {
        "resultados": report_repo.get_mcnemar_results() or [],
        "holm_posthoc": report_repo.get_mcnemar_holm() or [],
    }


@router.get("/cochran")
def get_cochran(current_user: TokenData = Depends(get_current_user)):
    report_repo = ReportRepository()
    return {"cochran_q": report_repo.get_cochran_q()}
