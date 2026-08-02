"""CRUD de usuarios con control de permisos (solo administradores)."""


def test_list_users_requires_admin(client, client_auth):
    resp = client.get("/api/v1/users", headers=client_auth)
    assert resp.status_code == 403
    assert resp.json()["message"] == "Solo administradores"


def test_list_users_as_admin(client, admin_auth):
    resp = client.get("/api/v1/users", headers=admin_auth)
    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list)
    usernames = {u["username"] for u in users}
    assert {"admin", "cliente", "otro"}.issubset(usernames)


def test_create_user_as_admin(client, admin_auth):
    resp = client.post("/api/v1/users", headers=admin_auth, json={
        "name": "Usuario Nuevo",
        "username": "nuevo1",
        "password": "pass123",
        "role": "client",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == "nuevo1"
    assert body["role"] == "client"
    assert body["active"] is True
    # No debe filtrar el hash de la contraseña
    assert "password" not in body and "password_hash" not in body


def test_create_user_duplicate_username(client, admin_auth):
    resp = client.post("/api/v1/users", headers=admin_auth, json={
        "name": "Duplicado",
        "username": "cliente",
        "password": "pass123",
    })
    assert resp.status_code == 400
    assert "ya existe" in resp.json()["message"]


def test_create_user_forbidden_for_client(client, client_auth):
    resp = client.post("/api/v1/users", headers=client_auth, json={
        "name": "X",
        "username": "nope",
        "password": "x",
    })
    assert resp.status_code == 403


def test_create_user_requires_auth(client, no_auth):
    resp = client.post("/api/v1/users", headers=no_auth, json={
        "name": "X",
        "username": "nope",
        "password": "x",
    })
    assert resp.status_code == 401


def test_get_user_by_id(client, admin_auth, client_auth):
    # crear un usuario y luego consultarlo
    created = client.post("/api/v1/users", headers=admin_auth, json={
        "name": "Para Consultar",
        "username": "consultar1",
        "password": "pass123",
    }).json()
    resp = client.get(f"/api/v1/users/{created['id']}", headers=admin_auth)
    assert resp.status_code == 200
    assert resp.json()["username"] == "consultar1"


def test_get_user_not_found(client, admin_auth):
    resp = client.get("/api/v1/users/999999", headers=admin_auth)
    assert resp.status_code == 404


def test_update_user(client, admin_auth):
    created = client.post("/api/v1/users", headers=admin_auth, json={
        "name": "Antes",
        "username": "editar1",
        "password": "pass123",
    }).json()
    resp = client.patch(f"/api/v1/users/{created['id']}", headers=admin_auth, json={
        "name": "Después",
        "role": "client",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Después"


def test_update_user_invalid_role(client, admin_auth):
    created = client.post("/api/v1/users", headers=admin_auth, json={
        "name": "Rol",
        "username": "rol1",
        "password": "pass123",
    }).json()
    resp = client.patch(f"/api/v1/users/{created['id']}", headers=admin_auth, json={
        "role": "superadmin",
    })
    assert resp.status_code == 400
    assert resp.json()["message"] == "Rol inválido"


def test_update_user_not_found(client, admin_auth):
    resp = client.patch("/api/v1/users/999999", headers=admin_auth, json={"name": "X"})
    assert resp.status_code == 404


def test_delete_user(client, admin_auth):
    created = client.post("/api/v1/users", headers=admin_auth, json={
        "name": "Para Borrar",
        "username": "borrar1",
        "password": "pass123",
    }).json()
    resp = client.delete(f"/api/v1/users/{created['id']}", headers=admin_auth)
    assert resp.status_code == 204
    # Ya no existe
    resp = client.get(f"/api/v1/users/{created['id']}", headers=admin_auth)
    assert resp.status_code == 404


def test_delete_main_admin_forbidden(client, admin_auth):
    resp = client.delete("/api/v1/users/1", headers=admin_auth)
    if resp.status_code == 404:
        # El admin no tiene id 1 en este entorno; buscar el id real
        users = client.get("/api/v1/users", headers=admin_auth).json()
        admin_id = next(u["id"] for u in users if u["username"] == "admin")
        resp = client.delete(f"/api/v1/users/{admin_id}", headers=admin_auth)
    assert resp.status_code == 400
    assert "administrador principal" in resp.json()["message"]


def test_delete_user_not_found(client, admin_auth):
    resp = client.delete("/api/v1/users/999999", headers=admin_auth)
    assert resp.status_code == 404


def test_crud_forbidden_for_client(client, client_auth):
    assert client.get("/api/v1/users", headers=client_auth).status_code == 403
    assert client.patch("/api/v1/users/1", headers=client_auth, json={"name": "x"}).status_code == 403
    assert client.delete("/api/v1/users/2", headers=client_auth).status_code == 403
