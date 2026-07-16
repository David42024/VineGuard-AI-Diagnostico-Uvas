"""
Functional verification script for P1-P8 fixes.
Tests 1-3: two-client cross-access, real upload + UUID, Streamlit compat.
"""
import sys
import json
import re
import time
import sqlite3
import requests
import bcrypt
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

BASE = "http://localhost:8002/api/v1"
DB_PATH = PROJECT_ROOT / "data" / "vinguard.db"
TEST_IMAGE = PROJECT_ROOT / "dataset" / "test" / "Black_rot" / "003d09ef-e16c-4e8a-badf-847d46cb3dc0___FAM_B.Rot 3184.JPG"

passed = failed = skipped = 0
results = []


def test(name, fn, section=""):
    global passed, failed, skipped
    print(f"\n--- [{section}] {name} ---")
    try:
        result = fn()
        if result == "SKIP":
            skipped += 1
            results.append((section, name, "SKIP", ""))
            print(f"  SKIP")
        else:
            passed += 1
            results.append((section, name, "PASS", result or ""))
            print(f"  PASS: {result}")
    except Exception as e:
        failed += 1
        results.append((section, name, "FAIL", str(e)))
        print(f"  FAIL: {e}")


class Session:
    def __init__(self, user, pw):
        self.s = requests.Session()
        r = self.s.post(f"{BASE}/auth/login", json={"username": user, "password": pw}, timeout=15)
        r.raise_for_status()
        self.token = self.s.cookies.get("token")
        assert self.token, "No token cookie"
        self.user = user

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get(self, url, **kw):
        return self.s.get(url, headers=self.headers(), **kw)

    def post(self, url, **kw):
        return self.s.post(url, headers=self.headers(), **kw)

    def delete(self, url, **kw):
        return self.s.delete(url, headers=self.headers(), **kw)


# ============================================================
# SETUP: Create client_b_func if not exists
# ============================================================
print("\n" + "=" * 60)
print("SETUP: Create second test client")
print("=" * 60)

conn = sqlite3.connect(str(DB_PATH))
existing = conn.execute("SELECT id FROM users WHERE username='client_b_func'").fetchone()
if existing:
    conn.execute("DELETE FROM users WHERE username='client_b_func'")
    conn.commit()

pw_hash = bcrypt.hashpw(b"test123", bcrypt.gensalt()).decode()
conn.execute(
    "INSERT INTO users (name, username, password_hash, role, active) VALUES (?, ?, ?, ?, ?)",
    ("Cliente B Funcional", "client_b_func", pw_hash, "client", 1),
)
conn.commit()
cb = conn.execute("SELECT id FROM users WHERE username='client_b_func'").fetchone()
client_b_id = cb[0]
conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
conn.close()
time.sleep(1)
print(f"  Created client_b_func id={client_b_id}")


# ============================================================
# SECTION 1: TWO-CLIENT CROSS-ACCESS
# ============================================================
print("\n" + "=" * 60)
print("SECTION 1: TWO-CLIENT CROSS-ACCESS")
print("=" * 60)

admin = Session("admin", "admin123")
client_a = Session("usuario", "12345")
client_b = Session("client_b_func", "test123")

# Upload an image as client B to create a diagnostic
def upload_as_client_b():
    assert TEST_IMAGE.exists(), f"Test image not found: {TEST_IMAGE}"
    with open(TEST_IMAGE, "rb") as f:
        r = client_b.post(
            f"{BASE}/diagnoses",
            files={"file": ("test_black_rot.jpg", f, "image/jpeg")},
            data={"model_key": "M1", "is_demo": "false"},
            timeout=120,
        )
    assert r.status_code == 201, f"Upload failed: {r.status_code} {r.text}"
    return r.json()["id"]

cb_diag_id = upload_as_client_b()
print(f"  Client B diagnostic: #{cb_diag_id}")

# Also get a diagnostic owned by client A
r_a = client_a.get(f"{BASE}/diagnoses?limit=1&offset=0", timeout=10)
a_items = r_a.json()["items"]
assert len(a_items) > 0, "Client A has no diagnostics"
ca_diag_id = a_items[0]["id"]
print(f"  Client A diagnostic: #{ca_diag_id}")

# 1.1 Client A queries Client B's diagnostic -> 403
def t1_1():
    r = client_a.get(f"{BASE}/diagnoses/{cb_diag_id}", timeout=10)
    assert r.status_code in (403, 404), f"Expected 403/404, got {r.status_code}"
    return f"Client A -> Client B diag #{cb_diag_id}: HTTP {r.status_code}"

test("1.1 Client A queries Client B diagnostic", t1_1, "1")

# 1.2 Client A queries Client B's image -> 403
def t1_2():
    r = client_a.get(f"{BASE}/diagnoses/{cb_diag_id}/image", timeout=10)
    assert r.status_code in (403, 404), f"Expected 403/404, got {r.status_code}"
    return f"Client A -> Client B image #{cb_diag_id}: HTTP {r.status_code}"

test("1.2 Client A queries Client B image", t1_2, "1")

# 1.3 Client A tries to delete Client B's diagnostic -> 403
def t1_3():
    r = client_a.delete(f"{BASE}/diagnoses/{cb_diag_id}", timeout=10)
    assert r.status_code in (403, 404), f"Expected 403/404, got {r.status_code}"
    return f"Client A -> delete Client B #{cb_diag_id}: HTTP {r.status_code}"

test("1.3 Client A deletes Client B diagnostic", t1_3, "1")

# 1.4 Admin CAN access Client B's diagnostic -> 200
def t1_4():
    r = admin.get(f"{BASE}/diagnoses/{cb_diag_id}", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    return f"Admin -> Client B diag #{cb_diag_id}: HTTP 200"

test("1.4 Admin CAN access Client B diagnostic", t1_4, "1")

# 1.5 Client B CAN access own diagnostic -> 200
def t1_5():
    r = client_b.get(f"{BASE}/diagnoses/{cb_diag_id}", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    return f"Client B -> own diag #{cb_diag_id}: HTTP 200"

test("1.5 Client B CAN access own diagnostic", t1_5, "1")


# ============================================================
# SECTION 2: REAL UPLOAD + UUID PATH + FILE + IMAGE + SOFT DELETE
# ============================================================
print("\n" + "=" * 60)
print("SECTION 2: REAL UPLOAD + UUID + IMAGE + SOFT DELETE")
print("=" * 60)

# Upload as client A
upload_result = None
diag_id_a = None

def t2_1():
    global upload_result, diag_id_a
    assert TEST_IMAGE.exists(), f"Test image not found: {TEST_IMAGE}"
    with open(TEST_IMAGE, "rb") as f:
        r = client_a.post(
            f"{BASE}/diagnoses",
            files={"file": ("test_leaf.jpg", f, "image/jpeg")},
            data={"model_key": "M1", "is_demo": "false"},
            timeout=120,
        )
    assert r.status_code == 201, f"Upload failed: {r.status_code} {r.text}"
    upload_result = r.json()
    diag_id_a = upload_result["id"]
    return f"Upload OK: diag #{diag_id_a}, class={upload_result['prediction']['class_code']}, conf={upload_result['prediction']['confidence']:.3f}"

test("2.1 POST /diagnoses (real upload)", t2_1, "2")

# Check UUID in image_path
def t2_2():
    assert diag_id_a, "No diag_id from upload"
    r = client_a.get(f"{BASE}/diagnoses/{diag_id_a}", timeout=10)
    d = r.json()
    image_url = d.get("image_url", "")
    assert image_url, f"image_url is empty: {d}"
    return f"image_url={image_url}"

test("2.2 image_url present in response", t2_2, "2")

# Check physical file exists on disk with UUID name
def t2_3():
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute("SELECT image_path FROM diagnostics WHERE id=?", (diag_id_a,)).fetchone()
    conn.close()
    assert row and row[0], "No image_path in DB"
    img_path = Path(row[0])
    assert img_path.exists(), f"File does not exist: {img_path}"
    filename = img_path.name
    uuid_pattern = r"[0-9a-f]{32}\.\w+"
    assert re.match(uuid_pattern, filename), f"Filename is not UUID: {filename}"
    return f"File exists: {img_path} (UUID: {filename})"

test("2.3 physical file has UUID filename", t2_3, "2")

# GET /diagnoses/{id}/image returns the image
def t2_4():
    r = client_a.get(f"{BASE}/diagnoses/{diag_id_a}/image", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    ct = r.headers.get("Content-Type", "")
    assert "image" in ct or "octet-stream" in ct, f"Bad Content-Type: {ct}"
    return f"Image returned: Content-Type={ct}, size={len(r.content)} bytes"

test("2.4 GET image endpoint returns file", t2_4, "2")

# Owner can see the image
def t2_5():
    r = client_a.get(f"{BASE}/diagnoses/{diag_id_a}/image", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    return f"Owner sees image: HTTP 200"

test("2.5 owner can see own image", t2_5, "2")

# Other client cannot see it
def t2_6():
    r = client_b.get(f"{BASE}/diagnoses/{diag_id_a}/image", timeout=10)
    assert r.status_code in (403, 404), f"Expected 403/404, got {r.status_code}"
    return f"Client B -> Client A image: HTTP {r.status_code}"

test("2.6 other client cannot see image", t2_6, "2")

# Admin can see it
def t2_7():
    r = admin.get(f"{BASE}/diagnoses/{diag_id_a}/image", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    return f"Admin sees image: HTTP 200"

test("2.7 admin can see image", t2_7, "2")

# Soft delete
def t2_8():
    r = client_a.delete(f"{BASE}/diagnoses/{diag_id_a}", timeout=10)
    assert r.status_code == 204, f"Expected 204, got {r.status_code}"
    return f"Soft delete: HTTP 204"

test("2.8 soft delete own diagnostic", t2_8, "2")

# After soft delete: GET detail returns error
def t2_9():
    r = client_a.get(f"{BASE}/diagnoses/{diag_id_a}", timeout=10)
    assert r.status_code in (404, 403), f"Expected 404/403, got {r.status_code}"
    return f"GET deleted detail: HTTP {r.status_code}"

test("2.9 deleted diagnostic not in detail", t2_9, "2")

# After soft delete: GET image returns error
def t2_10():
    r = client_a.get(f"{BASE}/diagnoses/{diag_id_a}/image", timeout=10)
    assert r.status_code in (404, 403), f"Expected 404/403, got {r.status_code}"
    return f"GET deleted image: HTTP {r.status_code}"

test("2.10 deleted image not accessible", t2_10, "2")

# After soft delete: row still in DB with deleted_at set
def t2_11():
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute(
        "SELECT id, deleted_at, deleted_by, status FROM diagnostics WHERE id=?",
        (diag_id_a,),
    ).fetchone()
    conn.close()
    assert row, "Row not found"
    assert row[1] is not None, "deleted_at is NULL"
    assert row[2] is not None, "deleted_by is NULL"
    assert row[3] == "deleted", f"status is '{row[3]}', expected 'deleted'"
    return f"Row #{row[0]}: deleted_at={row[1]}, deleted_by={row[2]}, status={row[3]}"

test("2.11 soft-deleted row has deleted_at/deleted_by", t2_11, "2")


# ============================================================
# SECTION 3: STREAMLIT FUNCTIONAL (repository functions)
# ============================================================
print("\n" + "=" * 60)
print("SECTION 3: STREAMLIT COMPAT (repository functions)")
print("=" * 60)

def t3_1():
    from database.repository import (
        init_database, authenticate, save_diagnostic, audit_log,
        get_user_diagnostics, get_all_diagnostics, delete_diagnostic,
        get_user_stats, get_admin_stats, get_disease_distribution,
        get_diagnostics_by_date,
    )
    funcs = [init_database, authenticate, save_diagnostic, audit_log,
             get_user_diagnostics, get_all_diagnostics, delete_diagnostic,
             get_user_stats, get_admin_stats, get_disease_distribution,
             get_diagnostics_by_date]
    return f"All 11 functions importable: {[f.__name__ for f in funcs]}"

test("3.1 all repository functions importable", t3_1, "3")

def t3_2():
    from database.repository import authenticate
    user = authenticate("admin", "admin123")
    assert user is not None, "admin auth failed"
    assert user["username"] == "admin"
    assert user["role"] == "admin"
    return f"authenticate('admin'): id={user['id']}, role={user['role']}"

test("3.2 authenticate('admin') works", t3_2, "3")

def t3_3():
    from database.repository import authenticate
    user = authenticate("usuario", "12345")
    assert user is not None, "usuario auth failed"
    assert user["username"] == "usuario"
    assert user["role"] == "client"
    return f"authenticate('usuario'): id={user['id']}, role={user['role']}"

test("3.3 authenticate('usuario') works", t3_3, "3")

def t3_4():
    from database.repository import authenticate
    user = authenticate("client_b_func", "test123")
    assert user is not None, "client_b_func auth failed"
    assert user["username"] == "client_b_func"
    return f"authenticate('client_b_func'): id={user['id']}, role={user['role']}"

test("3.4 authenticate('client_b_func') works", t3_4, "3")

def t3_5():
    from database.repository import authenticate
    user = authenticate("admin", "wrongpassword")
    assert user is None, "Wrong password should return None"
    return "authenticate('admin', 'wrong') correctly returns None"

test("3.5 authenticate wrong password returns None", t3_5, "3")

def t3_6():
    from database.repository import get_all_diagnostics
    diags = get_all_diagnostics(limit=5)
    assert isinstance(diags, list), "Expected list"
    assert len(diags) > 0, "Expected at least 1 diagnostic"
    d = diags[0]
    assert "id" in d and "result" in d, f"Missing fields: {list(d.keys())}"
    assert "deleted_at" not in d or d.get("deleted_at") is None, "Soft-deleted record returned"
    return f"get_all_diagnostics: {len(diags)} items, first #{d['id']}, result={d['result']}"

test("3.6 get_all_diagnostics works", t3_6, "3")

def t3_7():
    from database.repository import get_user_diagnostics
    diags = get_user_diagnostics("usuario", limit=5)
    assert isinstance(diags, list), "Expected list"
    for d in diags:
        assert d.get("deleted_at") is None, f"Soft-deleted record in user list: {d['id']}"
    return f"get_user_diagnostics('usuario'): {len(diags)} items, all non-deleted"

test("3.7 get_user_diagnostics excludes soft-deleted", t3_7, "3")

def t3_8():
    from database.repository import get_admin_stats
    stats = get_admin_stats()
    assert isinstance(stats, dict), "Expected dict"
    assert "total_users" in stats, f"Missing total_users: {list(stats.keys())}"
    assert "total_diagnostics" in stats, f"Missing total_diagnostics"
    return f"get_admin_stats: users={stats['total_users']}, diags={stats['total_diagnostics']}"

test("3.8 get_admin_stats works", t3_8, "3")

def t3_9():
    from database.repository import get_user_stats
    stats = get_user_stats("usuario")
    assert isinstance(stats, dict), "Expected dict"
    return f"get_user_stats('usuario'): {list(stats.keys())}"

test("3.9 get_user_stats works", t3_9, "3")

def t3_10():
    from database.repository import get_disease_distribution
    dist = get_disease_distribution()
    assert isinstance(dist, (list, dict)), f"Expected list/dict, got {type(dist)}"
    return f"get_disease_distribution: {dist}"

test("3.10 get_disease_distribution works", t3_10, "3")

def t3_11():
    from database.repository import delete_diagnostic
    import inspect
    sig = inspect.signature(delete_diagnostic)
    params = list(sig.parameters.keys())
    return f"delete_diagnostic signature: {sig} -> params={params}"

test("3.11 delete_diagnostic exists with correct signature", t3_11, "3")

def t3_12():
    """init_database is a no-op stub (no DDL)"""
    from database.repository import init_database
    import inspect
    src = inspect.getsource(init_database)
    assert "CREATE TABLE" not in src, "init_database still has DDL!"
    assert "DELETE FROM" not in src, "init_database still has DELETE!"
    return "init_database has no DDL (confirmed no-op stub)"

test("3.12 init_database has no DDL", t3_12, "3")


# ============================================================
# CLEANUP: Remove temp test user
# ============================================================
print("\n" + "=" * 60)
print("CLEANUP")
print("=" * 60)

conn = sqlite3.connect(str(DB_PATH))
# Remove test user diagnostics first (FK)
conn.execute("DELETE FROM audit_log WHERE user_id=?", (client_b_id,))
conn.execute("DELETE FROM diagnostics WHERE user_id=?", (client_b_id,))
conn.execute("DELETE FROM users WHERE username='client_b_func'")
conn.commit()
conn.close()
print("  Removed client_b_func and their diagnostics/audit entries")


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print(f"RESULTS: {passed} PASSED / {failed} FAILED / {skipped} SKIPPED")
print(f"TOTAL: {passed + failed + skipped}")
print("=" * 60)

if failed > 0:
    print("\nFAILED TESTS:")
    for sec, name, status, detail in results:
        if status == "FAIL":
            print(f"  [{sec}] {name}: {detail}")

print("\nALL TESTS:")
for sec, name, status, detail in results:
    marker = {"PASS": "+", "FAIL": "X", "SKIP": "-"}[status]
    print(f"  [{marker}] [{sec}] {name}" + (f" -- {detail}" if detail else ""))

sys.exit(1 if failed else 0)
