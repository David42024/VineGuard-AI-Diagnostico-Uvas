"""Endpoints de estadísticas: resúmenes, comparaciones y tests estadísticos."""


def test_summary_requires_admin(client, client_auth):
    resp = client.get("/api/v1/statistics/summary", headers=client_auth)
    assert resp.status_code == 403


def test_summary_as_admin(client, admin_auth):
    resp = client.get("/api/v1/statistics/summary", headers=admin_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert "general_stats" in body
    assert "disease_distribution" in body
    assert "diagnostics_by_date" in body
    assert "ranking" in body


def test_my_summary(client, client_auth):
    resp = client.get("/api/v1/statistics/my-summary", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_diagnostics"] >= 0
    assert body["healthy_pct"] >= 0
    assert body["diseased_pct"] >= 0
    assert body["today_diagnostics"] >= 0


def test_model_comparison(client, client_auth):
    resp = client.get("/api/v1/statistics/model-comparison", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert "comparison" in body
    assert "effectSize" in body


def test_cross_validation(client, client_auth):
    resp = client.get("/api/v1/statistics/cross-validation", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert "resultados" in body
    assert "porFold" in body


def test_bootstrap(client, client_auth):
    resp = client.get("/api/v1/statistics/bootstrap", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert "bootstrap" in body


def test_mcnemar(client, client_auth):
    resp = client.get("/api/v1/statistics/mcnemar", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert "holmPosthoc" in body


def test_cochran(client, client_auth):
    resp = client.get("/api/v1/statistics/cochran", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert "cochranQ" in body


def test_statistics_requires_auth(client, no_auth):
    assert client.get("/api/v1/statistics/summary", headers=no_auth).status_code == 401
    assert client.get("/api/v1/statistics/bootstrap", headers=no_auth).status_code == 401
    assert client.get("/api/v1/statistics/cochran", headers=no_auth).status_code == 401
