"""Generación y descarga de reportes (docx, pdf, xlsx)."""


def _generate_docx(client, auth, diagnosis_id) -> str:
    """Genera un reporte docx y devuelve su download_url."""
    resp = client.post(
        f"/api/v1/reports/diagnosis/{diagnosis_id}",
        json={"format": "docx"},
        headers=auth,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["message"] == "Reporte generado exitosamente"
    assert body["filename"].endswith(".docx")
    assert body["download_url"].startswith("/api/v1/reports/")
    return body["download_url"]


def test_list_reports(client, client_auth):
    resp = client.get("/api/v1/reports", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert "reports" in body
    assert isinstance(body["reports"], list)


def test_list_reports_requires_auth(client, no_auth):
    resp = client.get("/api/v1/reports", headers=no_auth)
    assert resp.status_code == 401


def test_generate_docx(client, client_auth, sample_diagnosis):
    _generate_docx(client, client_auth, sample_diagnosis)


def test_generate_pdf(client, client_auth, sample_diagnosis):
    resp = client.post(
        f"/api/v1/reports/diagnosis/{sample_diagnosis}",
        json={"format": "pdf"},
        headers=client_auth,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["filename"].endswith(".pdf")


def test_generate_xlsx(client, client_auth, sample_diagnosis):
    resp = client.post(
        f"/api/v1/reports/diagnosis/{sample_diagnosis}",
        json={"format": "xlsx"},
        headers=client_auth,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["filename"].endswith(".xlsx")


def test_generate_report_unknown_format_defaults_docx(client, client_auth, sample_diagnosis):
    resp = client.post(
        f"/api/v1/reports/diagnosis/{sample_diagnosis}",
        json={"format": "odt"},
        headers=client_auth,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["filename"].endswith(".docx")


def test_generate_report_not_found(client, client_auth):
    resp = client.post(
        "/api/v1/reports/diagnosis/999999",
        json={"format": "docx"},
        headers=client_auth,
    )
    assert resp.status_code == 404
    assert "Diagnóstico no encontrado" in resp.json()["message"]


def test_generate_report_forbidden_for_other_user(client, other_auth, sample_diagnosis):
    resp = client.post(
        f"/api/v1/reports/diagnosis/{sample_diagnosis}",
        json={"format": "docx"},
        headers=other_auth,
    )
    assert resp.status_code == 403


def test_generate_report_requires_auth(client, no_auth, sample_diagnosis):
    resp = client.post(
        f"/api/v1/reports/diagnosis/{sample_diagnosis}",
        json={"format": "docx"},
        headers=no_auth,
    )
    assert resp.status_code == 401


def test_download_generated_report(client, client_auth, sample_diagnosis):
    url = _generate_docx(client, client_auth, sample_diagnosis)
    resp = client.get(url, headers=client_auth)
    assert resp.status_code == 200
    assert "vnd.openxmlformats-officedocument.wordprocessingml" in resp.headers["content-type"]
    assert len(resp.content) > 1000


def test_download_report_not_found(client, client_auth):
    resp = client.get("/api/v1/reports/noexiste/download", headers=client_auth)
    assert resp.status_code == 404
