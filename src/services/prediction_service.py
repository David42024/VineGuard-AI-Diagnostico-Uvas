"""Shared prediction service used by both Streamlit app and FastAPI backend."""

import os
import time
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from predecir_imagen import predecir, cargar_modelo
from model_registry import MODEL_KEYS, MODEL_DISPLAY_NAMES, check_model_files

DISEASE_CLASSES = ["Black_rot", "Esca", "Healthy", "Leaf_blight"]

DISEASE_INFO = {
    "Black_rot": {
        "display_name_es": "Podredumbre Negra",
        "display_name_en": "Black Rot",
        "display_name_pt": "Podridão Negra",
        "scientific_name": "Guignardia bidwellii",
        "health_status": "diseased",
        "risk_level": "high",
    },
    "Esca": {
        "display_name_es": "Esca (Sarampión Negro)",
        "display_name_en": "Esca (Black Measles)",
        "display_name_pt": "Esca (Sarampo Negro)",
        "scientific_name": "Complejo fúngico vascular",
        "health_status": "diseased",
        "risk_level": "high",
    },
    "Healthy": {
        "display_name_es": "Hoja Sana",
        "display_name_en": "Healthy Leaf",
        "display_name_pt": "Folha Saudável",
        "scientific_name": "",
        "health_status": "healthy",
        "risk_level": "none",
    },
    "Leaf_blight": {
        "display_name_es": "Tizón de la Hoja",
        "display_name_en": "Leaf Blight",
        "display_name_pt": "Queima das Folhas",
        "scientific_name": "Pseudocercospora vitis",
        "health_status": "diseased",
        "risk_level": "moderate",
    },
}

_model_cache: dict[str, bool] = {}


def load_single_model(model_key: str) -> bool:
    """Load a single model by key. Returns True if successful."""
    try:
        cargar_modelo(model_key)
        _model_cache[model_key] = True
        return True
    except Exception:
        _model_cache[model_key] = False
        return False


def load_all_models() -> dict[str, bool]:
    """Load all models and return availability status."""
    results = {}
    for mk in MODEL_KEYS:
        results[mk] = load_single_model(mk)
    return results


def get_model_status() -> dict[str, dict]:
    """Return availability status for all models.
    A model is 'disponible' if it has been loaded OR all its artifact files exist on disk.
    """
    status = {}
    for mk in MODEL_KEYS:
        loaded = _model_cache.get(mk, False)
        file_check = check_model_files(mk)
        files_exist = file_check and all(file_check.values())
        available = loaded or files_exist
        status[mk] = {"disponible": available, "model_key": mk}
    return status


def predict_from_image(image: Image.Image, model_key: str) -> dict:
    """Predict disease from a PIL Image using the specified model."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        image.save(tmp.name, format="JPEG")
        ruta_temp = tmp.name

    start_time = time.time()
    try:
        resultado = predecir(ruta_temp, model_key)
    finally:
        os.unlink(ruta_temp)
    inference_time = (time.time() - start_time) * 1000

    proba = resultado["probabilidades"]
    predicted_class = resultado["clase_predicha"]

    if predicted_class not in DISEASE_CLASSES:
        raise ValueError(f"Clase no reconocida: {predicted_class!r}")

    predicted_class_idx = DISEASE_CLASSES.index(predicted_class)

    if proba is not None:
        confidence = float(proba[predicted_class_idx])
        all_predictions = np.asarray(proba, dtype=np.float64).tolist()
    else:
        confidence = None
        all_predictions = None

    return {
        "model_key": model_key,
        "model_name": MODEL_DISPLAY_NAMES.get(model_key, model_key),
        "predicted_class": predicted_class,
        "confidence": confidence,
        "probabilities": all_predictions,
        "inference_time_ms": inference_time,
        "probabilidades_calibradas": resultado.get("probabilidades_calibradas", False),
    }


def predict_multiple_models(image: Image.Image, model_keys: Optional[list[str]] = None) -> list[dict]:
    """Predict with multiple models. Returns list of results."""
    if model_keys is None:
        model_keys = [mk for mk in MODEL_KEYS if _model_cache.get(mk, False)]
    results = []
    for mk in model_keys:
        try:
            result = predict_from_image(image, mk)
            result["status"] = "success"
            results.append(result)
        except Exception as e:
            results.append({
                "model_key": mk,
                "model_name": MODEL_DISPLAY_NAMES.get(mk, mk),
                "status": "error",
                "error": str(e),
            })
    return results


def predict_consensus(image: Image.Image) -> dict:
    """Predict with all available models and compute consensus.

    Returns:
        status: "success" or "error"
        predicted_class: winning class by majority vote
        confidence: average confidence of the winning class across all models
        confidence_description: "Promedio de probabilidades de la clase ganadora"
        vote_distribution: dict mapping class -> vote count
        agreement_level: "high" (>=80%), "medium" (>=60%), "low"
        agreeing_models: count of models that predicted the winning class
        total_models: total successful models
        tie_breaker: description of how ties were resolved, if applicable
        individual_results: list of individual model results
        primary_result: first successful model result (for backward compat)
        errors: list of error results
    """
    available = [mk for mk in MODEL_KEYS if _model_cache.get(mk, False)]
    results = predict_multiple_models(image, available)

    successful = [r for r in results if r.get("status") == "success"]
    errors = [r for r in results if r.get("status") == "error"]

    if not successful:
        return {
            "status": "error",
            "error": "Ningún modelo disponible",
            "individual_results": results,
        }

    predictions = [r["predicted_class"] for r in successful]
    classes = sorted(set(predictions))
    vote_distribution = {c: predictions.count(c) for c in classes}
    consensus_class = max(classes, key=lambda c: vote_distribution[c])
    consensus_count = vote_distribution[consensus_class]
    total = len(successful)
    agreement_pct = consensus_count / total * 100

    # Check for ties
    winners = [c for c, v in vote_distribution.items() if v == consensus_count]
    tie_breaker = None
    if len(winners) > 1:
        tie_breaker = (
            f"Empate entre {', '.join(winners)} con {consensus_count} voto(s) cada uno. "
            f"Se seleccionó '{consensus_class}' por mayor confianza promedio."
        )

    if agreement_pct >= 80:
        agreement_level = "high"
    elif agreement_pct >= 60:
        agreement_level = "medium"
    else:
        agreement_level = "low"

    # Average confidence of the winning class across all models
    # Each model's confidence is its probability for its predicted class
    confs = []
    for r in successful:
        cls = r["predicted_class"]
        probs = r.get("probabilities")
        if probs is not None and DISEASE_CLASSES.index(cls) < len(probs):
            confs.append(float(probs[DISEASE_CLASSES.index(cls)]))
        else:
            confs.append(r.get("confidence", 0) or 0)
    avg_confidence = float(np.mean(confs)) if confs else 0

    primary = next(r for r in successful if r["predicted_class"] == consensus_class)

    return {
        "status": "success",
        "predicted_class": consensus_class,
        "confidence": avg_confidence,
        "confidence_description": "Promedio de probabilidades de la clase ganadora",
        "vote_distribution": vote_distribution,
        "agreement_level": agreement_level,
        "agreeing_models": consensus_count,
        "total_models": total,
        "tie_breaker": tie_breaker,
        "individual_results": successful,
        "errors": errors,
        "primary_result": primary,
    }
