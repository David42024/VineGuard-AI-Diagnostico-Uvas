"""Endpoints de sistema: /health, documentación y manejo de errores globales."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "VineGuard AI API"
    assert "version" in data


def test_openapi_schema(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["info"]["title"] == "VineGuard AI API"
    assert "/api/v1/auth/login" in schema["paths"]
    assert "/api/v1/diagnoses" in schema["paths"]


def test_docs_page(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_unknown_route_returns_404(client):
    resp = client.get("/api/v1/no-existe")
    assert resp.status_code == 404


def test_health_and_docs_are_public(client):
    """Estos endpoints no requieren autenticación."""
    assert client.get("/health").status_code == 200
    assert client.get("/openapi.json").status_code == 200
