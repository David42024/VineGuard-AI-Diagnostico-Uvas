"""Configuración aislada de la suite de pruebas del backend FastAPI.

Aislamiento:
  - Base de datos SQLite temporal (nueva por sesión), nunca toca data/vinguard.db.
  - Storage de uploads/reportes en directorio temporal.
  - Los endpoints que leen artefactos (models/, reports/) trabajan sobre los
    archivos reales del proyecto (solo lectura).

IMPORTANTE: las variables de entorno se fijan ANTES de importar cualquier
módulo de backend, porque `backend.core.config.settings` y
`backend.database.session.engine` se construyen al importar.
"""

import io
import os
import tempfile
from pathlib import Path

import pytest

_TMP_ROOT = Path(tempfile.mkdtemp(prefix="vinguard_pytest_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP_ROOT / 'test.db').as_posix()}"
os.environ["STORAGE_DIR"] = str(_TMP_ROOT / "storage")

# --- Imports del proyecto (después de fijar el entorno) ---
from fastapi.testclient import TestClient  # noqa: E402

from backend.main import app  # noqa: E402
from backend.database.base import Base  # noqa: E402
from backend.database.session import engine, SessionLocal  # noqa: E402
from backend.database.models import UserModel  # noqa: E402
from backend.core.security import create_access_token, hash_password  # noqa: E402

import database.repository as _legacy_repo  # noqa: E402

# El login (database.repository.authenticate) usa sqlite3 crudo con una ruta
# fija; la redirigimos a la base temporal para compartir el mismo archivo.
_legacy_repo.DB_DIR = _TMP_ROOT
_legacy_repo.DB_PATH = _TMP_ROOT / "test.db"

SEED_USERS = [
    dict(username="admin", password="admin123", name="Administrador", role="admin"),
    dict(username="cliente", password="cliente123", name="Cliente Demo", role="client"),
    dict(username="otro", password="otro123", name="Cliente Secundario", role="client"),
]


@pytest.fixture(scope="session", autouse=True)
def _db_session():
    """Crea las tablas y siembra usuarios en la base temporal."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for u in SEED_USERS:
            if not db.query(UserModel).filter(UserModel.username == u["username"]).first():
                db.add(UserModel(
                    username=u["username"],
                    name=u["name"],
                    password_hash=hash_password(u["password"]),
                    role=u["role"],
                ))
        db.commit()
    finally:
        db.close()
    Path(os.environ["STORAGE_DIR"]).mkdir(parents=True, exist_ok=True)
    yield
    engine.dispose()


@pytest.fixture(scope="session")
def client():
    """Cliente HTTP sin contexto (no ejecuta lifespan/alembic)."""
    return TestClient(app)


@pytest.fixture()
def auth_client():
    """Cliente fresco por test, con cookies aisladas (para login/logout/refresh)."""
    return TestClient(app)


def _auth_headers(username: str, role: str) -> dict:
    token = create_access_token({"sub": username, "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_auth():
    return _auth_headers("admin", "admin")


@pytest.fixture()
def client_auth():
    return _auth_headers("cliente", "client")


@pytest.fixture()
def other_auth():
    return _auth_headers("otro", "client")


@pytest.fixture()
def no_auth():
    return {}


def _make_png_bytes(color=(40, 110, 40)) -> bytes:
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (224, 224), color).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture()
def valid_png():
    """PNG válido de 224x224 (pasa la validación PIL del backend)."""
    return _make_png_bytes()


@pytest.fixture()
def invalid_file():
    """Bytes que NO son una imagen válida."""
    return b"esto no es una imagen jpg/png de verdad"


def apply_prediction_mocks(mp: pytest.MonkeyPatch) -> None:
    """Sustituye la inferencia ML en backend.api.diagnosis por datos fijos."""
    import backend.api.diagnosis as diag

    individual = [
        {
            "model_key": mk,
            "model_name": mk,
            "predicted_class": "Black_rot",
            "confidence": 0.9,
            "probabilities": [0.9, 0.05, 0.03, 0.02],
            "inference_time_ms": 12.0,
            "status": "success",
        }
        for mk in ["M1", "M2", "M3", "H1", "H2"]
    ]
    consensus = {
        "status": "success",
        "predicted_class": "Black_rot",
        "confidence": 0.9,
        "confidence_description": "Promedio de probabilidades de la clase ganadora",
        "agreement_level": "high",
        "agreeing_models": 5,
        "total_models": 5,
        "vote_distribution": {"Black_rot": 5},
        "primary_result": {
            "model_key": "M1",
            "model_name": "M1 - SVM",
            "probabilities": [0.9, 0.05, 0.03, 0.02],
        },
        "individual_results": individual,
    }

    def _fake_consensus(_image):
        return consensus

    def _fake_load_all():
        return {}

    def _fake_load_single(_key):
        return True

    def _fake_predict(_image, model_key):
        return {
            "model_key": model_key,
            "model_name": model_key,
            "predicted_class": "Black_rot",
            "confidence": 0.9,
            "probabilities": [0.9, 0.05, 0.03, 0.02],
            "inference_time_ms": 10.0,
        }

    mp.setattr(diag, "load_all_models", _fake_load_all)
    mp.setattr(diag, "load_single_model", _fake_load_single)
    mp.setattr(diag, "predict_consensus", _fake_consensus)
    mp.setattr(diag, "predict_from_image", _fake_predict)


@pytest.fixture()
def mock_prediction(monkeypatch):
    apply_prediction_mocks(monkeypatch)
    return monkeypatch


@pytest.fixture(scope="session")
def sample_diagnosis(client) -> int:
    """Crea un diagnóstico bajo el usuario 'cliente' usando predicción simulada.

    Devuelve el id para que los tests de lectura/consulta lo usen.
    No se elimina nunca (los tests de borrado crean el suyo propio).
    """
    mp = pytest.MonkeyPatch()
    apply_prediction_mocks(mp)
    resp = client.post(
        "/api/v1/diagnoses",
        files={"file": ("hoja.png", _make_png_bytes(), "image/png")},
        data={"model_key": "M1"},
        headers=_auth_headers("cliente", "client"),
    )
    mp.undo()
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
