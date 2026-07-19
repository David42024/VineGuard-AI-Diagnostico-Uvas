import sys
import math
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.security import get_current_user, TokenData
from backend.database.session import get_db
from backend.repositories.diagnostic_repository import DiagnosticRepository
from backend.repositories.report_repository import ReportRepository
from backend.repositories.user_repository import UserRepository

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.mantenedor import ESTADISTICA_DIR, MODELOS_DIR, CROSS_VALIDATION_DIR, COMPARATIVOS_DIR

router = APIRouter(prefix="/api/v1/statistics", tags=["statistics"])


# ── Normalization helpers ───────────────────────────────────────────

def _to_float(val, default=None):
    if val is None:
        return default
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default


def _normalize_ranking(rows):
    if not rows:
        return []
    out = []
    for r in rows:
        out.append({
            "ranking": int(r.get("ranking", 0)),
            "modelo": r.get("modelo", ""),
            "accuracy": _to_float(r.get("accuracy")),
            "balancedAccuracy": _to_float(r.get("balanced_accuracy")),
            "precisionMacro": _to_float(r.get("precision")),
            "recallMacro": _to_float(r.get("recall")),
            "f1Macro": _to_float(r.get("f1_score") or r.get("f1_macro")),
            "mcc": _to_float(r.get("mcc")),
            "aucMacro": _to_float(r.get("auc_macro")),
            "inferenceTimeMs": _to_float(r.get("tiempo_inferencia_ms")),
        })
    return out


def _normalize_cv_resultados(rows):
    if not rows:
        return []
    out = []
    for r in rows:
        out.append({
            "modelo": r.get("modelo", ""),
            "nFolds": int(r.get("n_folds", 0)),
            "accuracyMean": _to_float(r.get("accuracy_mean")),
            "accuracyStd": _to_float(r.get("accuracy_std")),
            "balancedAccuracyMean": _to_float(r.get("balanced_accuracy_mean")),
            "balancedAccuracyStd": _to_float(r.get("balanced_accuracy_std")),
            "precisionMacroMean": _to_float(r.get("precision_macro_mean")),
            "precisionMacroStd": _to_float(r.get("precision_macro_std")),
            "recallMacroMean": _to_float(r.get("recall_macro_mean")),
            "recallMacroStd": _to_float(r.get("recall_macro_std")),
            "f1MacroMean": _to_float(r.get("f1_macro_mean") or r.get("f1_weighted_mean")),
            "f1MacroStd": _to_float(r.get("f1_macro_std") or r.get("f1_weighted_std")),
            "mccMean": _to_float(r.get("mcc_mean")),
            "mccStd": _to_float(r.get("mcc_std")),
            "trainingTimeMeanS": _to_float(r.get("tiempo_entrenamiento_mean_s")),
            "inferenceTimeMeanMs": _to_float(r.get("tiempo_inferencia_mean_ms")),
        })
    return out


def _normalize_cv_folds(rows):
    if not rows:
        return []
    out = []
    for r in rows:
        out.append({
            "modelo": r.get("modelo", ""),
            "fold": int(r.get("fold", 0)),
            "nTrain": int(r.get("n_train", 0)),
            "nValidacion": int(r.get("n_validacion", 0)),
            "accuracy": _to_float(r.get("accuracy")),
            "balancedAccuracy": _to_float(r.get("balanced_accuracy")),
            "f1Macro": _to_float(r.get("f1_macro")),
            "mcc": _to_float(r.get("mcc")),
        })
    return out


def _normalize_bootstrap(rows):
    if not rows:
        return []
    out = []
    for r in rows:
        out.append({
            "modelo": r.get("modelo", ""),
            "accuracyMean": _to_float(r.get("acc_media")),
            "accuracyCiLow": _to_float(r.get("acc_ci_inf")),
            "accuracyCiHigh": _to_float(r.get("acc_ci_sup")),
            "f1MacroMean": _to_float(r.get("f1_media")),
            "f1MacroCiLow": _to_float(r.get("f1_ci_inf")),
            "f1MacroCiHigh": _to_float(r.get("f1_ci_sup")),
            "mccMean": _to_float(r.get("mcc_media")),
            "mccCiLow": _to_float(r.get("mcc_ci_inf")),
            "mccCiHigh": _to_float(r.get("mcc_ci_sup")),
        })
    return out


def _normalize_mcnemar_holm(rows):
    if not rows:
        return []
    out = []
    for r in rows:
        n1_label = r.get("n1", "")
        n2_label = r.get("n2", "")
        b = int(r.get("b", 0) or 0)
        c = int(r.get("c", 0) or 0)
        if b > c:
            favorecido = n1_label
        elif c > b:
            favorecido = n2_label
        else:
            favorecido = "Empate"
        out.append({
            "modelo1": n1_label,
            "modelo2": n2_label,
            "b": b,
            "c": c,
            "pRaw": _to_float(r.get("p_raw")),
            "pHolm": _to_float(r.get("p_holm")),
            "significativo": r.get("significativo", "No") == "Sí",
            "favorecido": favorecido,
        })
    return out


def _normalize_effect_size(rows):
    if not rows:
        return []
    out = []
    for r in rows:
        m1 = r.get("modelo_1", "")
        diff_mcc = _to_float(r.get("diff_mcc_modelo1_menos_modelo2"))
        favorecido = m1 if (diff_mcc and diff_mcc > 0) else (r.get("modelo_2", "") if (diff_mcc and diff_mcc < 0) else "Empate")
        out.append({
            "modelo1": m1,
            "modelo2": r.get("modelo_2", ""),
            "diffAccuracy": _to_float(r.get("diff_accuracy_modelo1_menos_modelo2")),
            "diffF1Macro": _to_float(r.get("diff_f1_macro_modelo1_menos_modelo2")),
            "diffMcc": diff_mcc,
            "oddsRatio": _to_float(r.get("odds_ratio_mcnemar_cc")),
            "favorecido": favorecido,
        })
    return out


# ── Endpoints ──────────────────────────────────────────────────────


@router.get("/summary")
def get_summary(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    report_repo = ReportRepository()
    diag_repo = DiagnosticRepository(db)

    stats = diag_repo.get_admin_stats(exclude_demo=False)
    distribution = diag_repo.get_disease_distribution()
    diagnostics_by_date = diag_repo.get_diagnostics_by_date(30)

    best_model = report_repo.get_best_model()
    ranking = report_repo.get_ranking()
    cross_val_raw = report_repo.get_cross_validation()

    cross_val_clean = []
    if cross_val_raw:
        for row in cross_val_raw:
            clean = {}
            for k, v in row.items():
                key = k.replace("\u2013", "-").replace("\u2014", "-").strip().replace(" ", "_").lower()
                clean[key] = v
            cross_val_clean.append(clean)

    return {
        "general_stats": stats,
        "disease_distribution": distribution,
        "diagnostics_by_date": diagnostics_by_date,
        "best_model": best_model,
        "ranking": ranking,
        "cross_validation": cross_val_clean,
    }


@router.get("/my-summary")
def get_my_summary(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(current_user.sub)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    diag_repo = DiagnosticRepository(db)
    stats = diag_repo.get_user_stats(user.id)
    return {
        "total_diagnostics": stats["total"],
        "healthy_pct": round((stats["healthy"] / stats["total"] * 100) if stats["total"] else 0),
        "diseased_pct": round((stats["diseased"] / stats["total"] * 100) if stats["total"] else 0),
        "today_diagnostics": stats["today"],
        "last_diagnosis": stats["last_diagnosis"],
    }


@router.get("/model-comparison")
def get_model_comparison(current_user: TokenData = Depends(get_current_user)):
    report_repo = ReportRepository()
    raw = report_repo.get_model_comparison()
    effect_raw = report_repo.get_effect_size()
    return {
        "comparison": _normalize_ranking(raw),
        "effectSize": _normalize_effect_size(effect_raw),
    }


@router.get("/cross-validation")
def get_cross_validation(current_user: TokenData = Depends(get_current_user)):
    report_repo = ReportRepository()
    raw = report_repo.get_cross_validation()
    folds_raw = report_repo.get_cross_validation_by_fold()
    return {
        "resultados": _normalize_cv_resultados(raw),
        "porFold": _normalize_cv_folds(folds_raw),
    }


@router.get("/bootstrap")
def get_bootstrap(current_user: TokenData = Depends(get_current_user)):
    report_repo = ReportRepository()
    raw = report_repo.get_bootstrap_intervals() or []
    return {"bootstrap": _normalize_bootstrap(raw)}


@router.get("/mcnemar")
def get_mcnemar(current_user: TokenData = Depends(get_current_user)):
    report_repo = ReportRepository()
    holm_raw = report_repo.get_mcnemar_holm() or []
    return {
        "holmPosthoc": _normalize_mcnemar_holm(holm_raw),
    }


@router.get("/cochran")
def get_cochran(current_user: TokenData = Depends(get_current_user)):
    report_repo = ReportRepository()
    raw = report_repo.get_cochran_q()
    if not raw:
        return {"cochranQ": None}
    return {
        "cochranQ": {
            "estadisticoQ": _to_float(raw.get("estadistico_Q")),
            "pValue": _to_float(raw.get("p_value")),
            "interpretacion": raw.get("interpretacion", ""),
            "k": int(raw.get("k", 0)),
            "n": int(raw.get("n", 0)),
        }
    }
