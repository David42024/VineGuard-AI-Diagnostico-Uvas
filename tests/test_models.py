"""Catálogo de modelos: listado, detalle, ranking y mejor modelo."""

from src.model_registry import MODEL_KEYS


def test_list_models(client, client_auth):
    resp = client.get("/api/v1/models", headers=client_auth)
    assert resp.status_code == 200
    models = resp.json()
    assert len(models) == len(MODEL_KEYS)
    assert {m["id"] for m in models} == set(MODEL_KEYS)
    for m in models:
        assert m["name"]
        assert m["type"]
        assert m["status"] in ("available", "unavailable")


def test_list_models_requires_auth(client, no_auth):
    resp = client.get("/api/v1/models", headers=no_auth)
    assert resp.status_code == 401


def test_get_model(client, client_auth):
    resp = client.get("/api/v1/models/M1", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "M1"
    assert body["name"] == "M1 - SVM"


def test_get_model_not_found(client, client_auth):
    resp = client.get("/api/v1/models/ZZ", headers=client_auth)
    assert resp.status_code == 404
    assert resp.json()["message"] == "Modelo no encontrado"


def test_get_model_requires_auth(client, no_auth):
    resp = client.get("/api/v1/models/M1", headers=no_auth)
    assert resp.status_code == 401


def test_model_ranking(client, client_auth):
    resp = client.get("/api/v1/models/ranking", headers=client_auth)
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list) and len(items) >= 1
    for item in items:
        assert item["ranking"] >= 1
        assert item["modelo"]
        assert item["accuracy"] is not None


def test_best_model(client, client_auth):
    resp = client.get("/api/v1/models/best", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_name"]
    assert "accuracy" in body


def test_model_test_invalid_key(client, client_auth, valid_png):
    resp = client.post(
        "/api/v1/models/test",
        files={"file": ("hoja.png", valid_png, "image/png")},
        data={"model_key": "Z99"},
        headers=client_auth,
    )
    assert resp.status_code == 400
    assert "Modelo inválido" in resp.json()["message"]


def test_model_test_requires_auth(client, no_auth, valid_png):
    resp = client.post(
        "/api/v1/models/test",
        files={"file": ("hoja.png", valid_png, "image/png")},
        data={"model_key": "M1"},
        headers=no_auth,
    )
    assert resp.status_code == 401
