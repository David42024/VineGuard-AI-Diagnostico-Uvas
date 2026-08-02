"""Endpoints de diagnóstico: creación, consulta, imagen, borrado lógico y repetición."""

import io
from PIL import Image


def _upload_files(client, auth, model_key="M1", filename="hoja.png", content=None, is_demo=False):
    if content is None:
        buf = io.BytesIO()
        Image.new("RGB", (224, 224), (30, 90, 30)).save(buf, format="PNG")
        content = buf.getvalue()
    data = {"model_key": model_key}
    if is_demo:
        data["is_demo"] = "true"
    return client.post(
        "/api/v1/diagnoses",
        files={"file": (filename, content, "image/png" if filename.endswith(".png") else "image/jpeg")},
        data=data,
        headers=auth,
    )


# ── Creación ───────────────────────────────────────────────────────────

def test_create_diagnosis_single(client, client_auth, valid_png, mock_prediction):
    resp = client.post(
        "/api/v1/diagnoses",
        files={"file": ("hoja.png", valid_png, "image/png")},
        data={"model_key": "M1"},
        headers=client_auth,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert body["mode"] == "single"
    assert body["prediction"]["class_code"] == "Black_rot"
    assert body["model"]["key"] == "M1"
    assert body["image_url"] == f"/api/v1/diagnoses/{body['id']}/image"


def test_create_diagnosis_consensus(client, client_auth, valid_png, mock_prediction):
    resp = client.post(
        "/api/v1/diagnoses",
        files={"file": ("hoja.png", valid_png, "image/png")},
        data={"model_key": "consensus"},
        headers=client_auth,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["mode"] == "consensus"
    assert body["consensus"] is not None
    assert body["consensus"]["total_models"] == 5
    assert body["predictions"] is not None and len(body["predictions"]) == 5


def test_create_diagnosis_invalid_model_key(client, client_auth, valid_png, mock_prediction):
    resp = _upload_files(client, client_auth, model_key="Z99")
    assert resp.status_code == 400
    assert "model_key inválido" in resp.json()["message"]


def test_create_diagnosis_all_models(client, client_auth, valid_png, mock_prediction):
    resp = client.post(
        "/api/v1/diagnoses",
        files={"file": ("hoja.png", valid_png, "image/png")},
        data={"model_key": "all"},
        headers=client_auth,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["mode"] == "compare_all"
    assert len(body["predictions"]) == 5


def test_create_diagnosis_invalid_image(client, client_auth, invalid_file, mock_prediction):
    resp = client.post(
        "/api/v1/diagnoses",
        files={"file": ("falso.png", invalid_file, "image/png")},
        data={"model_key": "M1"},
        headers=client_auth,
    )
    assert resp.status_code == 400
    assert "no es una imagen válida" in resp.json()["message"]


def test_create_diagnosis_bad_extension(client, client_auth, mock_prediction):
    resp = client.post(
        "/api/v1/diagnoses",
        files={"file": ("malware.exe", b"datos", "application/octet-stream")},
        data={"model_key": "M1"},
        headers=client_auth,
    )
    assert resp.status_code == 400
    assert "Extensión no permitida" in resp.json()["message"]


def test_create_diagnosis_requires_auth(client, no_auth, valid_png, mock_prediction):
    resp = client.post(
        "/api/v1/diagnoses",
        files={"file": ("hoja.png", valid_png, "image/png")},
        data={"model_key": "M1"},
        headers=no_auth,
    )
    assert resp.status_code == 401


# ── Listado ────────────────────────────────────────────────────────────

def test_list_diagnoses_client_sees_only_own(client, client_auth, sample_diagnosis):
    resp = client.get("/api/v1/diagnoses", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert any(item["id"] == sample_diagnosis for item in body["items"])


def test_list_diagnoses_other_user_sees_empty(client, other_auth, sample_diagnosis):
    resp = client.get("/api/v1/diagnoses", headers=other_auth)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_list_diagnoses_admin_sees_all(client, admin_auth, sample_diagnosis):
    resp = client.get("/api/v1/diagnoses", headers=admin_auth)
    assert resp.status_code == 200
    assert any(item["id"] == sample_diagnosis for item in resp.json()["items"])


def test_list_diagnoses_requires_auth(client, no_auth):
    resp = client.get("/api/v1/diagnoses", headers=no_auth)
    assert resp.status_code == 401


def test_list_diagnoses_pagination_and_search(client, client_auth, mock_prediction, valid_png):
    # Crear un diagnóstico con nombre distinguible
    buf = io.BytesIO()
    Image.new("RGB", (224, 224), (200, 10, 10)).save(buf, format="PNG")
    created = client.post(
        "/api/v1/diagnoses",
        files={"file": ("vid_especial.png", buf.getvalue(), "image/png")},
        data={"model_key": "M2"},
        headers=client_auth,
    )
    assert created.status_code == 201
    diag_id = created.json()["id"]

    # Búsqueda por nombre de archivo
    resp = client.get("/api/v1/diagnoses", headers=client_auth, params={"search": "vid_especial"})
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["items"]]
    assert diag_id in ids

    # Filtro por clase
    resp = client.get("/api/v1/diagnoses", headers=client_auth, params={"class_code": "Black_rot"})
    assert resp.status_code == 200
    assert all(item["result"] == "Black_rot" for item in resp.json()["items"])


# ── Detalle e imagen ───────────────────────────────────────────────────

def test_get_diagnosis_detail(client, client_auth, sample_diagnosis):
    resp = client.get(f"/api/v1/diagnoses/{sample_diagnosis}", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == sample_diagnosis
    assert "probabilities" in body
    assert body["probabilities"]["Black_rot"] is not None


def test_get_diagnosis_forbidden_for_other_user(client, other_auth, sample_diagnosis):
    resp = client.get(f"/api/v1/diagnoses/{sample_diagnosis}", headers=other_auth)
    assert resp.status_code == 403


def test_get_diagnosis_admin_can_see_any(client, admin_auth, sample_diagnosis):
    resp = client.get(f"/api/v1/diagnoses/{sample_diagnosis}", headers=admin_auth)
    assert resp.status_code == 200


def test_get_diagnosis_not_found(client, client_auth):
    resp = client.get("/api/v1/diagnoses/999999", headers=client_auth)
    assert resp.status_code == 404


def test_get_diagnosis_image(client, client_auth, sample_diagnosis):
    resp = client.get(f"/api/v1/diagnoses/{sample_diagnosis}/image", headers=client_auth)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/")


def test_get_diagnosis_image_forbidden(client, other_auth, sample_diagnosis):
    resp = client.get(f"/api/v1/diagnoses/{sample_diagnosis}/image", headers=other_auth)
    assert resp.status_code == 403


def test_get_diagnosis_image_not_found(client, client_auth):
    resp = client.get("/api/v1/diagnoses/999999/image", headers=client_auth)
    assert resp.status_code == 404


# ── Borrado (soft delete) ──────────────────────────────────────────────

def test_delete_diagnosis_soft_delete(client, client_auth, mock_prediction, valid_png):
    created = client.post(
        "/api/v1/diagnoses",
        files={"file": ("borrar.png", valid_png, "image/png")},
        data={"model_key": "M1"},
        headers=client_auth,
    )
    assert created.status_code == 201
    diag_id = created.json()["id"]

    resp = client.delete(f"/api/v1/diagnoses/{diag_id}", headers=client_auth)
    assert resp.status_code == 204

    # Ya no aparece en el listado ni en detalle
    resp = client.get(f"/api/v1/diagnoses/{diag_id}", headers=client_auth)
    assert resp.status_code == 404
    resp = client.get("/api/v1/diagnoses", headers=client_auth, params={"search": "borrar"})
    assert all(item["id"] != diag_id for item in resp.json()["items"])

    # Sigue existiendo físicamente (soft delete)
    from backend.database.session import SessionLocal
    from backend.database.models import DiagnosticModel
    db = SessionLocal()
    try:
        row = db.query(DiagnosticModel).filter(DiagnosticModel.id == diag_id).first()
        assert row is not None and row.deleted_at is not None
    finally:
        db.close()


def test_delete_diagnosis_forbidden_for_other_user(client, other_auth, sample_diagnosis):
    resp = client.delete(f"/api/v1/diagnoses/{sample_diagnosis}", headers=other_auth)
    assert resp.status_code == 403


def test_delete_diagnosis_admin_can_delete(client, admin_auth, client_auth, mock_prediction, valid_png):
    created = client.post(
        "/api/v1/diagnoses",
        files={"file": ("admin_borra.png", valid_png, "image/png")},
        data={"model_key": "M1"},
        headers=client_auth,
    )
    diag_id = created.json()["id"]
    resp = client.delete(f"/api/v1/diagnoses/{diag_id}", headers=admin_auth)
    assert resp.status_code == 204


def test_delete_diagnosis_not_found(client, client_auth):
    resp = client.delete("/api/v1/diagnoses/999999", headers=client_auth)
    assert resp.status_code == 404


# ── Repetición ─────────────────────────────────────────────────────────

def test_repeat_diagnosis(client, client_auth, mock_prediction, valid_png):
    created = client.post(
        "/api/v1/diagnoses",
        files={"file": ("repetir.png", valid_png, "image/png")},
        data={"model_key": "M1"},
        headers=client_auth,
    )
    assert created.status_code == 201
    diag_id = created.json()["id"]

    resp = client.post(f"/api/v1/diagnoses/{diag_id}/repeat", headers=client_auth,
                       data={"model_key": "M1"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] != diag_id
    assert resp.json()["prediction"]["class_code"] == "Black_rot"


def test_repeat_diagnosis_not_found(client, client_auth, mock_prediction):
    resp = client.post("/api/v1/diagnoses/999999/repeat", headers=client_auth,
                       data={"model_key": "M1"})
    assert resp.status_code == 404


def test_repeat_diagnosis_forbidden(client, other_auth, sample_diagnosis, mock_prediction):
    resp = client.post(f"/api/v1/diagnoses/{sample_diagnosis}/repeat", headers=other_auth,
                       data={"model_key": "M1"})
    assert resp.status_code == 403
