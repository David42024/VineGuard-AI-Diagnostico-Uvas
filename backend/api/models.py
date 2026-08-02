import sys
import csv
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, status

from backend.core.security import get_current_user, TokenData
from backend.schemas.models import (
    ModelInfo,
    ModelMetrics,
    ModelRanking,
    BestModelResponse,
    ModelTestResponse,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.mantenedor import MODELOS_DIR, MODELS_DIR
from src.model_registry import MODEL_KEYS, MODEL_DISPLAY_NAMES, MODEL_TYPES, MODEL_REPORT_DIRS
from src.services.prediction_service import (
    get_model_status,
    load_single_model,
    predict_from_image,
    DISEASE_CLASSES,
)

router = APIRouter(prefix="/api/v1/models", tags=["models"])


def _read_csv_metrics(file_path: Path) -> Optional[dict]:
    if not file_path.exists():
        return None
    try:
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                out = {}
                for k, v in row.items():
                    k_clean = k.strip().lower().replace(" ", "_").replace("-", "_")
                    try:
                        out[k_clean] = float(v) if v else None
                    except ValueError:
                        out[k_clean] = v
                return out
    except Exception:
        return None


@router.get("", response_model=list[ModelInfo])
def list_models(current_user: TokenData = Depends(get_current_user)):
    model_status = get_model_status()
    results = []
    for mk in MODEL_KEYS:
        status_info = model_status.get(mk, {})
        available = status_info.get("disponible", False)
        reports_dir = MODEL_REPORT_DIRS.get(mk)
        metrics = None
        if reports_dir:
            resultados_file = reports_dir / f"resultados_{reports_dir.name}.csv"
            if not resultados_file.exists():
                resultados_file = reports_dir / f"resultados_{mk.lower()}.csv"
            raw = _read_csv_metrics(resultados_file)
            if raw:
                metrics = ModelMetrics(
                    accuracy=raw.get("accuracy"),
                    balanced_accuracy=raw.get("balanced_accuracy"),
                    precision=raw.get("precision"),
                    recall=raw.get("recall"),
                    f1_score=raw.get("f1_score") or raw.get("f1_macro"),
                    mcc=raw.get("mcc"),
                    auc_macro=raw.get("auc_macro"),
                    auc_micro=raw.get("auc_micro"),
                )
        results.append(ModelInfo(
            id=mk,
            name=MODEL_DISPLAY_NAMES.get(mk, mk),
            type=MODEL_TYPES.get(mk, "Unknown"),
            status="available" if available else "unavailable",
            available=available,
            metrics=metrics,
            reports_dir=str(reports_dir) if reports_dir else None,
        ))
    return results


@router.post("/test", response_model=ModelTestResponse)
def test_model(
    file: UploadFile = File(...),
    model_key: str = Form(...),
    current_user: TokenData = Depends(get_current_user),
):
    if model_key not in MODEL_KEYS:
        raise HTTPException(status_code=400, detail=f"Modelo inválido: {model_key}")

    from PIL import Image
    import tempfile
    import shutil

    ext = Path(file.filename or "image.jpg").suffix.lower()
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
    try:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)
        tmp.close()
        pil_image = Image.open(tmp_path).convert("RGB")
        load_single_model(model_key)
        result = predict_from_image(pil_image, model_key)
        return ModelTestResponse(
            model_key=result["model_key"],
            predicted_class=result["predicted_class"],
            confidence=result.get("confidence"),
            probabilities=result.get("probabilities"),
            inference_time_ms=result.get("inference_time_ms", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@router.get("/ranking", response_model=list[ModelRanking])
def get_ranking(current_user: TokenData = Depends(get_current_user)):
    ranking_file = MODELOS_DIR / "ranking_modelos.csv"
    if not ranking_file.exists():
        raise HTTPException(status_code=404, detail="Archivo de ranking no encontrado")
    items = []
    with open(ranking_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            items.append(ModelRanking(
                ranking=int(row["ranking"]),
                modelo=row["modelo"],
                accuracy=float(row["accuracy"]),
                f1_score=float(row["f1_macro"]),
                mcc=float(row["mcc"]),
                acc_ci_inf=float(row["acc_ci_inf"]),
                acc_ci_sup=float(row["acc_ci_sup"]),
                f1_ci_inf=float(row["f1_ci_inf"]),
                f1_ci_sup=float(row["f1_ci_sup"]),
                mcc_ci_inf=float(row["mcc_ci_inf"]),
                mcc_ci_sup=float(row["mcc_ci_sup"]),
            ))
    return items


@router.get("/best", response_model=BestModelResponse)
def get_best(current_user: TokenData = Depends(get_current_user)):
    # Try rich JSON first
    MODELO_FINAL_JSON = MODELS_DIR / "modelo_final" / "modelo_final.json"
    if MODELO_FINAL_JSON.exists():
        try:
            import json
            with open(MODELO_FINAL_JSON, encoding="utf-8") as f:
                data = json.load(f)
            return BestModelResponse(
                model_name=data.get("modelo_ganador", "Unknown"),
                accuracy=data.get("metricas_test", {}).get("accuracy", 0.0),
                f1_score=data.get("metricas_test", {}).get("f1_macro", 0.0),
                mcc=data.get("metricas_test", {}).get("mcc", 0.0),
                selection_criteria="; ".join(data.get("criterio_seleccion", [])),
                modelo_ganador=data.get("modelo_ganador"),
                fecha_seleccion=data.get("fecha_seleccion"),
                criterio_seleccion=data.get("criterio_seleccion"),
                metricas_test=data.get("metricas_test"),
                victorias_significativas_holm=data.get("victorias_significativas_holm"),
                requiere_reentrenamiento=data.get("requiere_reentrenamiento"),
                artefactos=[
                    {"tipo": a["tipo"], "nombre_archivo": a["nombre_archivo"]}
                    for a in data.get("artefactos", [])
                ],
            )
        except Exception:
            pass

    # Fallback to legacy mejor_modelo.txt
    best_file = MODELOS_DIR / "mejor_modelo.txt"
    if not best_file.exists():
        raise HTTPException(status_code=404, detail="Archivo de mejor modelo no encontrado")
    content = best_file.read_text(encoding="utf-8")
    lines = [l.strip() for l in content.split("\n") if l.strip()]
    model_name = "Unknown"
    accuracy = 0.0
    f1_score = 0.0
    mcc = 0.0
    criteria = ""
    for i, line in enumerate(lines):
        if line.startswith("Mejor modelo"):
            model_name = line.split(":")[-1].strip()
        elif line.startswith("Accuracy"):
            try:
                accuracy = float(line.split(":")[-1].strip())
            except ValueError:
                pass
        elif line.startswith("F1-macro") or line.startswith("F1"):
            try:
                f1_score = float(line.split(":")[-1].strip())
            except ValueError:
                pass
        elif line.startswith("MCC"):
            try:
                mcc = float(line.split(":")[-1].strip())
            except ValueError:
                pass
        elif line.startswith("Criterio") or line.startswith("-"):
            criteria += line + "\n"
    return BestModelResponse(
        model_name=model_name,
        accuracy=accuracy,
        f1_score=f1_score,
        mcc=mcc,
        selection_criteria=criteria.strip(),
        details=content,
    )


@router.get("/{model_id}", response_model=ModelInfo)
def get_model(model_id: str, current_user: TokenData = Depends(get_current_user)):
    if model_id not in MODEL_KEYS:
        raise HTTPException(status_code=404, detail="Modelo no encontrado")
    model_status = get_model_status()
    status_info = model_status.get(model_id, {})
    available = status_info.get("disponible", False)
    reports_dir = MODEL_REPORT_DIRS.get(model_id)
    metrics = None
    if reports_dir:
        resultados_file = reports_dir / f"resultados_{reports_dir.name}.csv"
        if not resultados_file.exists():
            resultados_file = reports_dir / f"resultados_{model_id.lower()}.csv"
        raw = _read_csv_metrics(resultados_file)
        if raw:
            metrics = ModelMetrics(
                accuracy=raw.get("accuracy"),
                balanced_accuracy=raw.get("balanced_accuracy"),
                precision=raw.get("precision"),
                recall=raw.get("recall"),
                f1_score=raw.get("f1_score") or raw.get("f1_macro"),
                mcc=raw.get("mcc"),
                auc_macro=raw.get("auc_macro"),
                auc_micro=raw.get("auc_micro"),
            )
    return ModelInfo(
        id=model_id,
        name=MODEL_DISPLAY_NAMES.get(model_id, model_id),
        type=MODEL_TYPES.get(model_id, "Unknown"),
        status="available" if available else "unavailable",
        available=available,
        metrics=metrics,
        reports_dir=str(reports_dir) if reports_dir else None,
    )
