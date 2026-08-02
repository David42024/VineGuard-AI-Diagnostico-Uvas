"""Pruebas de extremo a extremo con inferencia ML real (TensorFlow / scikit-learn).

Estos tests cargan los artefactos entrenados reales de models/ y ejecutan
predicciones reales. Están marcados como 'slow' y 'live'.
"""

import io
import pytest
from PIL import Image

pytestmark = [pytest.mark.slow, pytest.mark.live]


def _png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (224, 224), (60, 120, 60)).save(buf, format="PNG")
    return buf.getvalue()


def test_live_diagnosis_m1(client, client_auth):
    """Crea un diagnóstico real con el modelo M1 (SVM)."""
    resp = client.post(
        "/api/v1/diagnoses",
        files={"file": ("vid.png", _png_bytes(), "image/png")},
        data={"model_key": "M1"},
        headers=client_auth,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert body["prediction"]["class_code"] in ("Black_rot", "Esca", "Healthy", "Leaf_blight")
    assert body["probabilities"] is not None
    assert body["inference_time_ms"] > 0


def test_live_diagnosis_consensus(client, client_auth):
    """Crea un diagnóstico real con el consenso de los 5 modelos."""
    resp = client.post(
        "/api/v1/diagnoses",
        files={"file": ("vid.png", _png_bytes(), "image/png")},
        data={"model_key": "consensus"},
        headers=client_auth,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["mode"] == "consensus"
    assert body["consensus"] is not None
    assert body["consensus"]["total_models"] == 5
    assert len(body["predictions"]) == 5


def test_live_model_test_m1(client, client_auth):
    """Prueba el endpoint de testeo de un modelo individual."""
    resp = client.post(
        "/api/v1/models/test",
        files={"file": ("vid.png", _png_bytes(), "image/png")},
        data={"model_key": "M1"},
        headers=client_auth,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["model_key"] == "M1"
    assert body["predicted_class"] in ("Black_rot", "Esca", "Healthy", "Leaf_blight")
    assert body["confidence"] is not None


def test_live_diagnosis_best_model(client, client_auth):
    """Crea un diagnóstico real con el 'Mejor Modelo' (H1, CNN + SVM)."""
    resp = client.post(
        "/api/v1/diagnoses",
        files={"file": ("vid.png", _png_bytes(), "image/png")},
        data={"model_key": "best_model"},
        headers=client_auth,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["mode"] == "best_model"
    assert body["prediction"]["class_code"] in ("Black_rot", "Esca", "Healthy", "Leaf_blight")
