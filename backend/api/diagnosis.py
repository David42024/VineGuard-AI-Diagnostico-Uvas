import sys
import json
import shutil
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

logger = logging.getLogger("vinguard.api.diagnosis")

from backend.core.config import settings
from backend.core.security import get_current_user, TokenData
from backend.schemas.diagnosis import (
    DiagnosisResponse,
    DiagnosisListItem,
    PaginatedDiagnoses,
    PredictionDetail,
    ConsensusInfo,
    PredictionInfo,
    ModelInfoDiagnosis,
)
from backend.database.session import get_db
from backend.database.models import DiagnosticModel
from backend.repositories.diagnostic_repository import DiagnosticRepository
from backend.repositories.user_repository import UserRepository
from backend.repositories.audit_repository import AuditRepository

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.services.prediction_service import (
    predict_from_image,
    predict_consensus,
    load_single_model,
    load_all_models,
    DISEASE_CLASSES,
    DISEASE_INFO,
)
from src.model_registry import MODEL_DISPLAY_NAMES, MODEL_KEYS

router = APIRouter(prefix="/api/v1/diagnoses", tags=["diagnoses"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
LIMIT_MIN = 1
LIMIT_MAX = 100


def _resolve_model_info(model_used: Optional[str]) -> ModelInfoDiagnosis:
    """Map model_used (key or display name) to ModelInfoDiagnosis."""
    if not model_used:
        return ModelInfoDiagnosis(key="unknown", name="Desconocido")
    key = model_used.strip()
    if key in MODEL_DISPLAY_NAMES:
        return ModelInfoDiagnosis(key=key, name=MODEL_DISPLAY_NAMES[key])
    import re
    m = re.search(r"\(([A-Z0-9]+)\)", model_used)
    if m:
        extracted = m.group(1)
        if extracted in MODEL_DISPLAY_NAMES:
            return ModelInfoDiagnosis(key=extracted, name=MODEL_DISPLAY_NAMES[extracted])
    return ModelInfoDiagnosis(key=key, name=model_used)


def _get_user_id(username: str, db: Session) -> Optional[int]:
    user = UserRepository(db).get_by_username(username)
    return user.id if user else None


def _get_user_by_id(user_id: int, db: Session) -> Optional[dict]:
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        return None
    return {"id": user.id, "name": user.name, "username": user.username, "role": user.role}


def _save_upload(file: UploadFile) -> Path:
    upload_dir = settings.STORAGE_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "image.jpg").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Extensión no permitida: {ext}")
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = upload_dir / unique_name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    from PIL import Image, UnidentifiedImageError
    try:
        with Image.open(dest) as img:
            img.verify()
    except (UnidentifiedImageError, OSError):
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida")
    return dest


def _build_disease_info(predicted_class: str) -> dict:
    info = DISEASE_INFO.get(predicted_class, {})
    return {
        "health_status": info.get("health_status", "unknown"),
        "risk_level": info.get("risk_level", "unknown"),
        "display_name_en": info.get("display_name_en", predicted_class),
        "display_name_es": info.get("display_name_es", predicted_class),
        "scientific_name": info.get("scientific_name", ""),
    }


@router.post("", response_model=DiagnosisResponse, status_code=status.HTTP_201_CREATED)
def create_diagnosis(
    file: UploadFile = File(...),
    model_key: str = Form("consensus"),
    is_demo: bool = Form(False),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = _get_user_id(current_user.sub, db)
    if not user_id:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    image_path = _save_upload(file)
    from PIL import Image
    pil_image = Image.open(image_path).convert("RGB")

    mode = "single"
    mode_label = ""
    predictions_list = []
    consensus_out = None

    if model_key == "consensus":
        mode = "consensus"
        mode_label = "Consenso de 5 modelos"
        load_all_models()
        consensus = predict_consensus(pil_image)
        if consensus["status"] == "error":
            raise HTTPException(status_code=500, detail=consensus.get("error", "Error en predicción"))

        result_class = consensus["predicted_class"]
        confidence = consensus["confidence"]
        used_model = "consensus"
        inf_time = sum(r.get("inference_time_ms", 0) for r in consensus.get("individual_results", []))

        raw_probs_list = None

        for r in consensus.get("individual_results", []):
            predictions_list.append(PredictionDetail(
                model_key=r["model_key"],
                model_name=r.get("model_name", r["model_key"]),
                predicted_class=r["predicted_class"],
                confidence=r.get("confidence"),
                probabilities=r.get("probabilities"),
                inference_time_ms=r.get("inference_time_ms"),
                status=r.get("status", "success"),
            ).model_dump())

        consensus_out = ConsensusInfo(
            status=consensus["status"],
            predicted_class=consensus["predicted_class"],
            confidence=consensus["confidence"],
            confidence_description=consensus.get("confidence_description", ""),
            agreement_level=consensus["agreement_level"],
            agreeing_models=consensus["agreeing_models"],
            total_models=consensus["total_models"],
            vote_distribution=consensus.get("vote_distribution"),
            tie_breaker=consensus.get("tie_breaker"),
        )
    elif model_key == "best_model":
        mode = "best_model"
        mode_label = "Mejor Modelo"
        from src.mantenedor import MODELS_DIR
        from src.predecir_imagen import _extractores, _modelos, _cargar_modelo_h1
        import tensorflow as tf
        import joblib
        import json as _json

        modelo_final_json = MODELS_DIR / "modelo_final" / "modelo_final.json"
        resolved_key = "H1"
        resolved_name = "H1 - CNN + SVM"

        if modelo_final_json.exists():
            with open(modelo_final_json, encoding="utf-8") as f:
                data = _json.load(f)
            winner_label = data.get("modelo_ganador", "")
            if "H2" in winner_label:
                resolved_key = "H2"
                resolved_name = "H2 - MobileNetV2 + RF"
            # Load final artifacts from modelo_final/
            final_dir = MODELS_DIR / "modelo_final"
            final_extractor = final_dir / "h1_cnn_feature_extractor.h5"
            final_svm = final_dir / "h1_svm_classifier.pkl"
            if final_extractor.exists() and final_svm.exists():
                tf.get_logger().setLevel("ERROR")
                _extractores["H1_extractor"] = tf.keras.models.load_model(
                    str(final_extractor), compile=False
                )
                _modelos["H1_svm"] = joblib.load(str(final_svm))
                _modelos["H1"] = _modelos["H1_svm"]
            else:
                _cargar_modelo_h1()
        else:
            _cargar_modelo_h1()

        result = predict_from_image(pil_image, resolved_key)
        result_class = result["predicted_class"]
        confidence = result["confidence"]
        used_model = resolved_key
        inf_time = result["inference_time_ms"]
        raw_probs_list = result.get("probabilities")
    elif model_key == "all":
        mode = "compare_all"
        mode_label = "Todos los Modelos"
        load_all_models()
        consensus = predict_consensus(pil_image)
        if consensus["status"] == "error":
            raise HTTPException(status_code=500, detail=consensus.get("error", "Error en predicción"))
        result_class = consensus["predicted_class"]
        confidence = consensus["confidence"]
        used_model = "all"
        inf_time = sum(r.get("inference_time_ms", 0) for r in consensus.get("individual_results", []))
        raw_probs_list = None
        for r in consensus.get("individual_results", []):
            predictions_list.append(PredictionDetail(
                model_key=r["model_key"],
                model_name=r.get("model_name", r["model_key"]),
                predicted_class=r["predicted_class"],
                confidence=r.get("confidence"),
                probabilities=r.get("probabilities"),
                inference_time_ms=r.get("inference_time_ms"),
                status=r.get("status", "success"),
            ).model_dump())
        consensus_out = ConsensusInfo(
            status=consensus["status"],
            predicted_class=consensus["predicted_class"],
            confidence=consensus["confidence"],
            confidence_description=consensus.get("confidence_description", ""),
            agreement_level=consensus["agreement_level"],
            agreeing_models=consensus["agreeing_models"],
            total_models=consensus["total_models"],
            vote_distribution=consensus.get("vote_distribution"),
            tie_breaker=consensus.get("tie_breaker"),
        )
    elif model_key == "all":
        load_all_models()
        consensus = predict_consensus(pil_image)
        if consensus["status"] == "error":
            raise HTTPException(status_code=500, detail=consensus.get("error", "Error en predicción"))
        result_class = consensus["predicted_class"]
        confidence = consensus["confidence"]
        predictions_list = []
        for r in consensus.get("individual_results", []):
            predictions_list.append(PredictionDetail(
                model_key=r["model_key"],
                model_name=r.get("model_name", r["model_key"]),
                predicted_class=r["predicted_class"],
                confidence=r.get("confidence"),
                probabilities=r.get("probabilities"),
                inference_time_ms=r.get("inference_time_ms"),
                status=r.get("status", "success"),
            ).model_dump())
        used_model = "all"
        inf_time = sum(r.get("inference_time_ms", 0) for r in consensus.get("individual_results", []))
        raw_probs_list = None
        consensus_out = None
    else:
        if model_key not in MODEL_KEYS:
            raise HTTPException(status_code=400, detail=f"model_key inválido: {model_key}. Valores válidos: {', '.join(MODEL_KEYS)}")
        load_single_model(model_key)
        result = predict_from_image(pil_image, model_key)
        result_class = result["predicted_class"]
        confidence = result["confidence"]
        used_model = result["model_key"]
        inf_time = result["inference_time_ms"]
        raw_probs_list = result.get("probabilities")
        mode_label = MODEL_DISPLAY_NAMES.get(model_key, model_key)

    probabilities_dict = {}
    if raw_probs_list:
        probabilities_dict = dict(zip(DISEASE_CLASSES, raw_probs_list))

    diag_repo = DiagnosticRepository(db)
    audit_repo = AuditRepository(db)

    diag_id = diag_repo.create(
        user_id=user_id,
        filename=file.filename or "unknown",
        result=result_class,
        confidence=confidence or 0.0,
        model_used=used_model,
        probabilities=probabilities_dict,
        inference_time_ms=inf_time or 0.0,
        image_path=str(image_path),
        is_demo=is_demo,
    )

    logger.info(f"[API] Diagnóstico #{diag_id} creado — usuario={current_user.sub} resultado={result_class} confianza={confidence:.2f} demo={is_demo}")
    print(f"\n[API] Diagnóstico #{diag_id} guardado en DB exitosamente")
    print(f"[API]    └── Resultado: {result_class}")
    print(f"[API]    └── Confianza: {confidence:.2%}")
    print(f"[API]    └── Modo: {mode}")
    print(f"[API]    └── Modelo: {used_model}")
    print(f"[API]    └── Usuario: {current_user.sub}")
    print(f"[API]    └── Demo: {is_demo}\n")

    audit_repo.log(user_id, "diagnosis", f"Diagnóstico creado: {result_class} ({confidence:.2f}) demo={is_demo}")

    disease_info = _build_disease_info(result_class)
    probs_dict = None
    if raw_probs_list is not None:
        probs_dict = dict(zip(DISEASE_CLASSES, [float(p) for p in raw_probs_list]))

    warnings = []
    if confidence is not None and confidence < 0.5:
        warnings.append("Baja confianza en la predicción")

    # Build model info for the response based on mode
    if mode == "consensus":
        model_info = ModelInfoDiagnosis(key="consensus", name="Consenso de 5 modelos", version="1.0.0")
    elif mode == "best_model":
        model_info = ModelInfoDiagnosis(key="best_model", name=resolved_name if model_key == "best_model" else used_model, version="1.0.0")
    elif mode == "compare_all":
        model_info = ModelInfoDiagnosis(key="all", name="Todos los Modelos", version="1.0.0")
    else:
        model_info = _resolve_model_info(used_model)

    return DiagnosisResponse(
        id=diag_id,
        created_at=datetime.now(),
        status="completed",
        mode=mode,
        mode_label=mode_label,
        is_demo=is_demo,
        image_url=f"/api/v1/diagnoses/{diag_id}/image",
        prediction=PredictionInfo(
            class_code=result_class,
            display_name=disease_info.get("display_name_es", result_class),
            confidence=confidence or 0.0,
            health_status=disease_info.get("health_status", "unknown"),
            risk_level=disease_info.get("risk_level", "unknown"),
        ),
        model=model_info,
        probabilities=probs_dict,
        inference_time_ms=inf_time,
        consensus=consensus_out,
        predictions=predictions_list if predictions_list else None,
        warnings=warnings,
    )


@router.get("", response_model=PaginatedDiagnoses)
def list_diagnoses(
    limit: int = Query(20, ge=LIMIT_MIN, le=LIMIT_MAX),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, max_length=200),
    class_code: Optional[str] = Query(None),
    model_key: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    is_demo: Optional[bool] = Query(None),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    diag_repo = DiagnosticRepository(db)

    def _build_item(r: dict) -> DiagnosisListItem:
        created = None
        try:
            ts = r.get("timestamp")
            if isinstance(ts, str):
                created = datetime.fromisoformat(ts)
            elif ts is not None:
                created = ts
        except (ValueError, TypeError):
            created = None
        return DiagnosisListItem(
            id=r["id"],
            created_at=created,
            filename=r.get("filename"),
            result=r["result"],
            confidence=r.get("confidence"),
            model_used=r.get("model_used"),
            inference_time_ms=r.get("inference_time_ms"),
            status=r.get("status", "completed"),
            user_name=r.get("user_name"),
            username=r.get("username"),
            image_url=f"/api/v1/diagnoses/{r['id']}/image" if r.get("image_path") else None,
            is_demo=bool(r.get("is_demo", 0)),
        )

    if current_user.role == "admin":
        rows = diag_repo.list_all(
            limit=limit, offset=offset,
            search=search, class_code=class_code, model_key=model_key,
            date_from=date_from, date_to=date_to, is_demo=is_demo,
        )
        total = diag_repo.count_filtered(
            search=search, class_code=class_code, model_key=model_key,
            date_from=date_from, date_to=date_to, is_demo=is_demo,
        )
    else:
        user_id = _get_user_id(current_user.sub, db)
        if not user_id:
            return PaginatedDiagnoses(items=[], total=0, limit=limit, offset=offset)
        rows = diag_repo.list_by_user(
            user_id, limit=limit, offset=offset,
            search=search, class_code=class_code, model_key=model_key,
            date_from=date_from, date_to=date_to, is_demo=is_demo,
        )
        total = diag_repo.count_filtered(
            user_id=user_id,
            search=search, class_code=class_code, model_key=model_key,
            date_from=date_from, date_to=date_to, is_demo=is_demo,
        )

    return PaginatedDiagnoses(
        items=[_build_item(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{diag_id}", response_model=DiagnosisResponse)
def get_diagnosis(
    diag_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    diag_repo = DiagnosticRepository(db)
    diag = diag_repo.get_by_id(diag_id)
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")

    if current_user.role != "admin" and diag.user_id != _get_user_id(current_user.sub, db):
        raise HTTPException(status_code=403, detail="No autorizado")

    probs = None
    if diag.probabilities:
        try:
            probs_data = json.loads(diag.probabilities)
            if isinstance(probs_data, dict):
                probs = {cls: float(probs_data.get(cls, 0.0)) for cls in DISEASE_CLASSES}
            elif isinstance(probs_data, list):
                probs = {cls: float(probs_data[i]) if i < len(probs_data) else 0.0 for i, cls in enumerate(DISEASE_CLASSES)}
        except (json.JSONDecodeError, TypeError):
            probs = None

    disease_info = _build_disease_info(diag.result)
    warnings = []
    if diag.confidence is not None and diag.confidence < 0.5:
        warnings.append("Baja confianza en la predicción")

    return DiagnosisResponse(
        id=diag.id,
        created_at=diag.timestamp,
        status=diag.status or "completed",
        is_demo=bool(diag.is_demo),
        image_url=f"/api/v1/diagnoses/{diag.id}/image" if diag.image_path else None,
        prediction=PredictionInfo(
            class_code=diag.result,
            display_name=disease_info.get("display_name_es", diag.result),
            confidence=diag.confidence or 0.0,
            health_status=disease_info.get("health_status", "unknown"),
            risk_level=disease_info.get("risk_level", "unknown"),
        ),
        model=_resolve_model_info(diag.model_used),
        probabilities=probs,
        inference_time_ms=diag.inference_time_ms,
        warnings=warnings,
    )


@router.get("/{diag_id}/image")
def get_diagnosis_image(
    diag_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    diag_repo = DiagnosticRepository(db)
    diag = diag_repo.get_by_id(diag_id)
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")

    if current_user.role != "admin" and diag.user_id != _get_user_id(current_user.sub, db):
        raise HTTPException(status_code=403, detail="No autorizado")

    if not diag.image_path or not Path(diag.image_path).exists():
        raise HTTPException(status_code=404, detail="Imagen no disponible")

    media_type = "image/jpeg"
    ext = Path(diag.image_path).suffix.lower()
    mime_map = {".png": "image/png", ".webp": "image/webp", ".bmp": "image/bmp"}
    media_type = mime_map.get(ext, "image/jpeg")

    return FileResponse(
        path=diag.image_path,
        media_type=media_type,
        filename=diag.filename or Path(diag.image_path).name,
    )


@router.delete("/{diag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_diagnosis(
    diag_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    diag_repo = DiagnosticRepository(db)
    audit_repo = AuditRepository(db)

    diag = diag_repo.get_by_id(diag_id)
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")

    user_id = _get_user_id(current_user.sub, db)

    if current_user.role != "admin" and diag.user_id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado para eliminar este diagnóstico")

    if current_user.role == "admin":
        diag_repo.soft_delete(diag_id, deleted_by=user_id)
    else:
        diag_repo.soft_delete(diag_id, user_id=user_id, deleted_by=user_id)

    audit_repo.log(user_id, "delete_diagnosis", f"Diagnóstico {diag_id} eliminado")


@router.post("/{diag_id}/repeat", response_model=DiagnosisResponse)
def repeat_diagnosis(
    diag_id: int,
    model_key: str = Form("consensus"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    diag_repo = DiagnosticRepository(db)
    audit_repo = AuditRepository(db)
    diag = diag_repo.get_by_id(diag_id)
    if not diag:
        raise HTTPException(status_code=404, detail="Diagnóstico original no encontrado")

    if current_user.role != "admin" and diag.user_id != _get_user_id(current_user.sub, db):
        raise HTTPException(status_code=403, detail="No autorizado")

    if not diag.image_path or not Path(diag.image_path).exists():
        raise HTTPException(status_code=400, detail="Imagen original no disponible")

    from PIL import Image
    pil_image = Image.open(diag.image_path).convert("RGB")

    user_id = _get_user_id(current_user.sub, db)

    if model_key == "consensus":
        load_all_models()
        consensus = predict_consensus(pil_image)
        if consensus["status"] == "error":
            raise HTTPException(status_code=500, detail=consensus.get("error", "Error en predicción"))
        primary = consensus["primary_result"]
        result_class = consensus["predicted_class"]
        confidence = consensus["confidence"]
        used_model = primary["model_key"]
        inf_time = primary["inference_time_ms"]
        raw_probs_list = primary.get("probabilities")
    else:
        load_single_model(model_key)
        result = predict_from_image(pil_image, model_key)
        result_class = result["predicted_class"]
        confidence = result["confidence"]
        used_model = result["model_key"]
        inf_time = result["inference_time_ms"]
        raw_probs_list = result.get("probabilities")

    probabilities_dict = {}
    if raw_probs_list:
        probabilities_dict = dict(zip(DISEASE_CLASSES, raw_probs_list))

    new_id = diag_repo.create(
        user_id=user_id,
        filename=diag.filename or "unknown",
        result=result_class,
        confidence=confidence or 0.0,
        model_used=used_model,
        probabilities=probabilities_dict,
        inference_time_ms=inf_time or 0.0,
        image_path=diag.image_path,
        is_demo=bool(diag.is_demo),
    )

    audit_repo.log(user_id, "repeat_diagnosis", f"Diagnóstico repetido {diag_id} -> {new_id}")

    probs_dict = None
    if raw_probs_list is not None:
        probs_dict = dict(zip(DISEASE_CLASSES, [float(p) for p in raw_probs_list]))

    disease_info = _build_disease_info(result_class)
    warnings = []
    if confidence is not None and confidence < 0.5:
        warnings.append("Baja confianza en la predicción")

    return DiagnosisResponse(
        id=new_id,
        created_at=datetime.now(),
        status="completed",
        is_demo=bool(diag.is_demo),
        image_url=f"/api/v1/diagnoses/{new_id}/image" if diag.image_path else None,
        prediction=PredictionInfo(
            class_code=result_class,
            display_name=disease_info.get("display_name_es", result_class),
            confidence=confidence or 0.0,
            health_status=disease_info.get("health_status", "unknown"),
            risk_level=disease_info.get("risk_level", "unknown"),
        ),
        model=_resolve_model_info(used_model),
        probabilities=probs_dict,
        inference_time_ms=inf_time,
        warnings=warnings,
    )
