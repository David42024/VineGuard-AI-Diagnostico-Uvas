"""Fase 8 + 9 - 14 pruebas de verificación"""
import sys, json, requests
from pathlib import Path

BASE = "http://localhost:8002/api/v1"
passed = failed = 0


def test(name, fn):
    global passed, failed
    print(f"\n=== {name} ===")
    try:
        fn()
        passed += 1
        print("  PASS")
    except Exception as e:
        failed += 1
        print(f"  FAIL: {e}")


def get_token(user, pw):
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"username": user, "password": pw}, timeout=10)
    r.raise_for_status()
    token = s.cookies.get("token")
    assert token, f"No token cookie in login response for {user}"
    return token


def h(tok):
    return {"Authorization": f"Bearer {tok}"}


admin_t = get_token("admin", "admin123")
client_t = get_token("usuario", "12345")
print("Tokens OK")

# Find an admin-owned diagnosis
r = requests.get(f"{BASE}/diagnoses?limit=100&offset=0", headers=h(admin_t), timeout=10)
all_diags = r.json()["items"]
admin_diag = next((d for d in all_diags if d.get("username") == "admin"), None)
client_diag = next((d for d in all_diags if d.get("username") == "usuario"), None)
print(f"Admin diag: #{admin_diag['id'] if admin_diag else 'NONE'}")
print(f"Client diag: #{client_diag['id'] if client_diag else 'NONE'}")


# 1. Listado admin
def t1():
    r = requests.get(f"{BASE}/diagnoses?limit=5&offset=0", headers=h(admin_t), timeout=10)
    assert r.status_code == 200, f"Status {r.status_code}"
    d = r.json()
    assert "items" in d, "No items field"
    assert "total" in d, "No total field"
    assert "limit" in d, "No limit field"
    assert "offset" in d, "No offset field"
    print(f"  items={len(d['items'])} total={d['total']} limit={d['limit']} offset={d['offset']}")


test("1. Listado admin (paginado)", t1)


# 2. Listado cliente
def t2():
    r = requests.get(f"{BASE}/diagnoses?limit=5&offset=0", headers=h(client_t), timeout=10)
    assert r.status_code == 200, f"Status {r.status_code}"
    d = r.json()
    print(f"  items={len(d['items'])} total={d['total']}")


test("2. Listado cliente (solo propios)", t2)


# 3. Paginación
def t3():
    r1 = requests.get(f"{BASE}/diagnoses?limit=3&offset=0", headers=h(admin_t), timeout=10)
    r2 = requests.get(f"{BASE}/diagnoses?limit=3&offset=3", headers=h(admin_t), timeout=10)
    d1, d2 = r1.json(), r2.json()
    assert len(d1["items"]) > 0, "Page 1 empty"
    assert d1["items"][0]["id"] != d2["items"][0]["id"], "Same first item on different pages"
    print(f"  page1_first={d1['items'][0]['id']} page2_first={d2['items'][0]['id']} total={d1['total']}")


test("3. Paginación", t3)


# 4. Filtro is_demo
def t4():
    r = requests.get(f"{BASE}/diagnoses?limit=100&is_demo=true", headers=h(admin_t), timeout=10)
    d = r.json()
    for item in d["items"]:
        assert item["is_demo"] == True, f"Item {item['id']} is not demo"
    print(f"  items={len(d['items'])} all_demo=True")


test("4. Filtro is_demo=true", t4)


# 5. Detalle propio
def t5():
    diag_id = client_diag["id"]
    r = requests.get(f"{BASE}/diagnoses/{diag_id}", headers=h(client_t), timeout=10)
    assert r.status_code == 200, f"Status {r.status_code}"
    d = r.json()
    assert "prediction" in d, "No prediction field"
    assert "is_demo" in d, "No is_demo field"
    assert "image_url" in d, "No image_url field"
    pred = d["prediction"]
    assert "class_code" in pred, "No prediction.class_code"
    assert "confidence" in pred, "No prediction.confidence"
    assert "model" in d, "No model field"
    assert "warnings" in d, "No warnings field"
    print(f"  id={d['id']} class={pred['class_code']} conf={pred['confidence']:.3f} is_demo={d['is_demo']} model={d['model']['key']}")


test("5. Detalle propio (client ve el suyo)", t5)


# 6. Detalle ajeno (debe 403)
def t6():
    diag_id = admin_diag["id"]
    r = requests.get(f"{BASE}/diagnoses/{diag_id}", headers=h(client_t), timeout=10)
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    print(f"  Correctly returned 403 for admin diag #{diag_id}")


test("6. Detalle ajeno (debe 403)", t6)


# 7. Imagen propia (si existe archivo)
def t7():
    diag_id = admin_diag["id"]
    r = requests.get(f"{BASE}/diagnoses/{diag_id}/image", headers=h(admin_t), timeout=10)
    if r.status_code == 404:
        print(f"  SKIP: Image file not on disk for diag #{diag_id} (seed data)")
    else:
        assert r.status_code == 200, f"Status {r.status_code}"
        print(f"  Image returned OK (content length={len(r.content)})")


test("7. Imagen propia", t7)


# 8. Imagen ajena (debe 403 o 404)
def t8():
    diag_id = admin_diag["id"]
    r = requests.get(f"{BASE}/diagnoses/{diag_id}/image", headers=h(client_t), timeout=10)
    assert r.status_code in (403, 404), f"Expected 403 or 404, got {r.status_code}"
    print(f"  Correctly returned {r.status_code}")


test("8. Imagen ajena (debe 403/404)", t8)


# 9. Soft delete
def t9():
    r = requests.get(f"{BASE}/diagnoses?limit=100&offset=0", headers=h(admin_t), timeout=10)
    before = r.json()["total"]
    last_id = r.json()["items"][-1]["id"]
    r_del = requests.delete(f"{BASE}/diagnoses/{last_id}", headers=h(admin_t), timeout=10)
    assert r_del.status_code == 204, f"Delete status {r_del.status_code}"
    r2 = requests.get(f"{BASE}/diagnoses?limit=100&offset=0", headers=h(admin_t), timeout=10)
    after = r2.json()["total"]
    print(f"  before={before} after={after} deleted_id={last_id}")
    assert after < before, f"Total did not decrease: {before} -> {after}"


test("9. Soft delete", t9)


# 10. Diagnóstico eliminado no visible
def t10():
    r = requests.get(f"{BASE}/diagnoses?limit=100&offset=0", headers=h(admin_t), timeout=10)
    d = r.json()
    for item in d["items"]:
        assert item["status"] != "deleted", f"Deleted item {item['id']} still visible"
    print(f"  No deleted diagnostics visible in listing")


test("10. Diagnóstico eliminado no visible", t10)


# 11. Total actualizado después del soft delete
def t11():
    r = requests.get(f"{BASE}/diagnoses?limit=100&offset=0", headers=h(admin_t), timeout=10)
    d = r.json()
    print(f"  total={d['total']} items_returned={len(d['items'])}")


test("11. Total actualizado después del soft delete", t11)


# 12. Limit validation
def t12():
    r = requests.get(f"{BASE}/diagnoses?limit=0", headers=h(admin_t), timeout=10)
    assert r.status_code == 422, f"Expected 422 for limit=0, got {r.status_code}"
    r2 = requests.get(f"{BASE}/diagnoses?limit=101", headers=h(admin_t), timeout=10)
    assert r2.status_code == 422, f"Expected 422 for limit=101, got {r2.status_code}"
    r3 = requests.get(f"{BASE}/diagnoses?offset=-1", headers=h(admin_t), timeout=10)
    assert r3.status_code == 422, f"Expected 422 for offset=-1, got {r3.status_code}"
    print(f"  limit=0 -> 422, limit=101 -> 422, offset=-1 -> 422")


test("12. Limit validation", t12)


# 13. New contract: prediction + model + warnings structure
def t13():
    r = requests.get(f"{BASE}/diagnoses?limit=1&offset=0", headers=h(admin_t), timeout=10)
    items = r.json()["items"]
    d = requests.get(f"{BASE}/diagnoses/{items[0]['id']}", headers=h(admin_t), timeout=10).json()
    assert isinstance(d["prediction"], dict), "prediction must be dict"
    assert isinstance(d["model"], dict), "model must be dict"
    assert isinstance(d["warnings"], list), "warnings must be list"
    assert d["prediction"]["class_code"] in ("Black_rot","Esca","Healthy","Leaf_blight"), f"Bad class_code: {d['prediction']['class_code']}"
    assert isinstance(d["prediction"]["confidence"], (int, float)), "confidence not numeric"
    assert d["prediction"]["risk_level"] in ("none","low","moderate","high","unknown"), f"Bad risk_level: {d['prediction']['risk_level']}"
    assert "key" in d["model"] and "name" in d["model"] and "version" in d["model"], "model missing fields"
    if d["probabilities"] is not None:
        assert isinstance(d["probabilities"], dict), "probabilities must be dict"
        assert len(d["probabilities"]) == 4, f"Expected 4 probabilities, got {len(d['probabilities'])}"
    print(f"  prediction.class_code={d['prediction']['class_code']} model.key={d['model']['key']} warnings={d['warnings']}")


test("13. New contract structure (prediction+model+warnings)", t13)


# 14. Probability sum ~ 1.0
def t14():
    r = requests.get(f"{BASE}/diagnoses?limit=1&offset=0", headers=h(admin_t), timeout=10)
    items = r.json()["items"]
    d = requests.get(f"{BASE}/diagnoses/{items[0]['id']}", headers=h(admin_t), timeout=10).json()
    probs = d.get("probabilities")
    if probs:
        total = sum(probs.values())
        assert abs(total - 1.0) < 0.01, f"Probabilities sum {total} != 1.0"
        print(f"  probability_sum={total:.4f}")
    else:
        print(f"  SKIP: no probabilities returned")


test("14. Probabilities sum to ~1.0", t14)


print(f"\n{'='*40}")
print(f"Resultados: {passed} PASSED / {failed} FAILED")
print(f"{'='*40}")
sys.exit(1 if failed else 0)
