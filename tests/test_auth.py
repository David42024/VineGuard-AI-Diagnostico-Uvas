"""Flujo de autenticación: login, logout, refresh y /me."""

from backend.core.security import create_access_token


def test_login_success(auth_client):
    resp = auth_client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "admin"
    assert body["user"]["active"] is True
    # La cookie de sesión debe quedar fijada
    assert "token" in auth_client.cookies


def test_login_wrong_password(auth_client):
    resp = auth_client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "incorrecta",
    })
    assert resp.status_code == 401
    assert "Credenciales inválidas" in resp.json()["message"]


def test_login_unknown_user(auth_client):
    resp = auth_client.post("/api/v1/auth/login", json={
        "username": "fantasma",
        "password": "x",
    })
    assert resp.status_code == 401


def test_login_inactive_user(auth_client):
    from backend.database.session import SessionLocal
    from backend.database.models import UserModel
    from backend.core.security import hash_password

    db = SessionLocal()
    try:
        db.add(UserModel(username="inactivo", name="Inactivo",
                         password_hash=hash_password("pass123"), role="client", active=0))
        db.commit()
    finally:
        db.close()

    resp = auth_client.post("/api/v1/auth/login", json={
        "username": "inactivo",
        "password": "pass123",
    })
    assert resp.status_code == 401


def test_me_authenticated(client, client_auth):
    resp = client.get("/api/v1/auth/me", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "cliente"
    assert body["role"] == "client"


def test_me_without_token(client, no_auth):
    resp = client.get("/api/v1/auth/me", headers=no_auth)
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json()["message"]


def test_me_with_invalid_token(client):
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer token-invalido"})
    assert resp.status_code == 401


def test_logout_clears_cookie(auth_client):
    auth_client.post("/api/v1/auth/login", json={
        "username": "cliente",
        "password": "cliente123",
    })
    assert "token" in auth_client.cookies
    resp = auth_client.post("/api/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Sesión cerrada exitosamente"
    assert not auth_client.cookies.get("token")


def test_logout_requires_auth(client, no_auth):
    resp = client.post("/api/v1/auth/logout", headers=no_auth)
    assert resp.status_code == 401


def test_refresh_rotates_token(auth_client, client_auth):
    resp = auth_client.post("/api/v1/auth/refresh", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["username"] == "cliente"
    assert "token" in auth_client.cookies


def test_refresh_requires_auth(client, no_auth):
    resp = client.post("/api/v1/auth/refresh", headers=no_auth)
    assert resp.status_code == 401


def test_token_from_wrong_secret_is_rejected(client):
    from jose import jwt as jose_jwt
    token = jose_jwt.encode(
        {"sub": "admin", "role": "admin"},
        "otro-secreto",
        algorithm="HS256",
    )
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
