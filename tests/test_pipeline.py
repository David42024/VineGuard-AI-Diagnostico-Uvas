"""Estado y etapas del pipeline de ML."""

EXPECTED_STAGE_IDS = [
    "eda",
    "preprocessing",
    "tuning",
    "models",
    "cross_validation",
    "statistics",
]


def test_pipeline_status(client, client_auth):
    resp = client.get("/api/v1/pipeline/status", headers=client_auth)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_stages"] == len(EXPECTED_STAGE_IDS)
    assert 0 <= body["completed_stages"] <= body["total_stages"]
    assert 0 <= body["progress_pct"] <= 100
    assert [s["id"] for s in body["stages"]] == EXPECTED_STAGE_IDS


def test_pipeline_stages(client, client_auth):
    resp = client.get("/api/v1/pipeline/stages", headers=client_auth)
    assert resp.status_code == 200
    stages = resp.json()["stages"]
    assert len(stages) == len(EXPECTED_STAGE_IDS)
    for stage in stages:
        assert "id" in stage
        assert "name" in stage
        assert "completed" in stage
        assert isinstance(stage["report_files"], list)
        assert stage["directory"]


def test_pipeline_requires_auth(client, no_auth):
    assert client.get("/api/v1/pipeline/status", headers=no_auth).status_code == 401
    assert client.get("/api/v1/pipeline/stages", headers=no_auth).status_code == 401
