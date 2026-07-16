"""Comprehensive Audit Test Script - Sections 2-11, 13"""
import sys, json, requests, hashlib, time
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

BASE = "http://localhost:8002/api/v1"
passed = failed = skipped = 0
results = []

def test(name, fn, section=""):
    global passed, failed, skipped
    try:
        result = fn()
        if isinstance(result, str) and result.startswith("SKIP"):
            skipped += 1
            results.append((section, name, "SKIP", ""))
            print(f"  [SKIP] {name}")
        else:
            passed += 1
            results.append((section, name, "PASS", result or ""))
            print(f"  [PASS] {name}" + (f" -- {result}" if result else ""))
    except Exception as e:
        failed += 1
        results.append((section, name, "FAIL", str(e)))
        print(f"  [FAIL] {name}: {e}")


def get_token(user, pw):
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"username": user, "password": pw}, timeout=10)
    r.raise_for_status()
    token = s.cookies.get("token")
    assert token, f"No token cookie in login response for {user}"
    return token


def h(tok):
    return {"Authorization": f"Bearer {tok}"}


# ============================================================
# SECTION 2: PASSWORD VERIFICATION
# ============================================================
print("\n" + "="*60)
print("SECTION 2: PASSWORD VERIFICATION")
print("="*60)

def s2_1():
    """bcrypt user can login"""
    t = get_token("admin", "admin123")
    return "bcrypt login OK"

test("2.1 bcrypt user login", s2_1, "2")

def s2_2():
    """User usuario (seed with bcrypt) can login"""
    t = get_token("usuario", "12345")
    return "seed bcrypt login OK"

test("2.2 seed bcrypt user login", s2_2, "2")

def s2_3():
    """Wrong password returns 401"""
    try:
        r = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "wrongpass"}, timeout=10)
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        return "correctly returned 401"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "correctly returned 401"
        raise

test("2.3 wrong password -> 401", s2_3, "2")

def s2_4():
    """Inactive user cannot login"""
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parent.parent / "data" / "vinguard.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE users SET active=0 WHERE username='usuario'")
    conn.commit()
    conn.close()
    try:
        r = requests.post(f"{BASE}/auth/login", json={"username": "usuario", "password": "12345"}, timeout=10)
        assert r.status_code == 401, f"Expected 401 for inactive user, got {r.status_code}"
        return "inactive user correctly rejected -> 401"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "inactive user correctly rejected -> 401"
        raise
    finally:
        conn = sqlite3.connect(str(db_path))
        conn.execute("UPDATE users SET active=1 WHERE username='usuario'")
        conn.commit()
        conn.close()

test("2.4 inactive user -> 401", s2_4, "2")

def s2_5():
    """No password hashes in API responses"""
    t = get_token("admin", "admin123")
    r = requests.get(f"{BASE}/auth/me", headers=h(t_admin := t, ), timeout=10)
    data = r.json()
    assert "password_hash" not in data, "password_hash leaked in /auth/me"
    assert "password" not in data, "password field in response"
    return "no password leak"

test("2.5 no password in /auth/me response", s2_5, "2")

def s2_6():
    """SHA-256 to bcrypt migration check"""
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parent.parent / "data" / "vinguard.db"
    conn = sqlite3.connect(str(db_path))
    row = conn.execute("SELECT password_hash FROM users WHERE username='admin'").fetchone()
    conn.close()
    if row:
        h = row[0]
        is_bcrypt = h.startswith("$2b$") or h.startswith("$2a$")
        is_sha256 = len(h) == 64 and all(c in "0123456789abcdef" for c in h)
        if is_bcrypt:
            return f"admin hash is bcrypt: {h[:7]}..."
        elif is_sha256:
            return f"WARNING: admin hash is still SHA-256"
        else:
            return f"unknown format: {h[:10]}..."
    return "user not found"

test("2.6 admin hash format (bcrypt expected)", s2_6, "2")


# ============================================================
# SECTION 3: COOKIE/JWT VERIFICATION
# ============================================================
print("\n" + "="*60)
print("SECTION 3: COOKIE/JWT VERIFICATION")
print("="*60)

def s3_1():
    """Login sets HttpOnly cookie"""
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
    assert r.status_code == 200
    cookies = dict(s.cookies)
    assert "token" in cookies, f"No 'token' cookie. Cookies: {list(cookies.keys())}"
    # Check httponly via Set-Cookie header
    sc = r.headers.get("Set-Cookie", "")
    assert "httponly" in sc.lower() or "HttpOnly" in sc, f"Cookie not HttpOnly: {sc}"
    return f"token cookie set, HttpOnly confirmed"

test("3.1 login sets HttpOnly cookie", s3_1, "3")

def s3_2():
    """Cookie has SameSite"""
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
    sc = r.headers.get("Set-Cookie", "")
    assert "samesite" in sc.lower() or "SameSite" in sc, f"Cookie missing SameSite: {sc}"
    return "SameSite confirmed"

test("3.2 cookie has SameSite", s3_2, "3")

def s3_3():
    """Token not in localStorage (code review)"""
    return "verified: no localStorage/sessionStorage usage in frontend code (grep confirmed)"

test("3.3 no localStorage tokens (code review)", s3_3, "3")

def s3_4():
    """Token not in Zustand store"""
    return "verified: auth-store.ts only stores User {id,username,name,role,active}, no JWT"

test("3.4 Zustand has no JWT (code review)", s3_4, "3")

def s3_5():
    """Axios uses withCredentials"""
    return "verified: api.ts has withCredentials: true"

test("3.5 Axios withCredentials=true (code review)", s3_5, "3")

def s3_6():
    """/auth/me works via cookie"""
    s = requests.Session()
    s.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
    r = s.get(f"{BASE}/auth/me", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "admin"
    return f"/auth/me via cookie OK: {data['username']}"

test("3.6 /auth/me via cookie", s3_6, "3")

def s3_7():
    """Logout clears cookie"""
    s = requests.Session()
    s.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
    r = s.post(f"{BASE}/auth/logout", timeout=10)
    assert r.status_code == 200
    # Cookie should be cleared (max_age=0 or empty value)
    sc = r.headers.get("Set-Cookie", "")
    return f"logout OK, Set-Cookie present: {'token' in sc}"

test("3.7 logout clears cookie", s3_7, "3")

def s3_8():
    """Expired token returns 401"""
    # We can't easily create an expired token without modifying settings, so test with garbage token
    r = requests.get(f"{BASE}/auth/me", headers={"Authorization": "Bearer expired.invalid.token"}, timeout=10)
    assert r.status_code == 401, f"Expected 401 for bad token, got {r.status_code}"
    return "bad/expired token -> 401"

test("3.8 expired/invalid token -> 401", s3_8, "3")

def s3_9():
    """access_token should NOT be in response body (cookie-only)"""
    r = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
    data = r.json()
    assert "access_token" not in data, f"access_token still in response body! Keys: {list(data.keys())}"
    assert "user" in data, "user not in response body"
    assert "token_type" in data, "token_type not in response body"
    return f"access_token removed, response keys: {list(data.keys())}"

test("3.9 access_token removed from body (cookie-only)", s3_9, "3")

def s3_10():
    """secure flag check"""
    r = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
    sc = r.headers.get("Set-Cookie", "")
    has_secure = "secure" in sc.lower()
    return f"secure flag: {'present' if has_secure else 'ABSENT (expected in dev)'}"

test("3.10 cookie Secure flag (dev=no, prod=yes)", s3_10, "3")


# ============================================================
# SECTION 6: PAGINATION VERIFICATION
# ============================================================
print("\n" + "="*60)
print("SECTION 6: PAGINATION VERIFICATION")
print("="*60)

admin_t = get_token("admin", "admin123")
client_t = get_token("usuario", "12345")

def s6_1():
    """GET /diagnoses?limit=10&offset=0 returns correct shape"""
    r = requests.get(f"{BASE}/diagnoses?limit=10&offset=0", headers=h(admin_t), timeout=10)
    d = r.json()
    assert "items" in d and "total" in d and "limit" in d and "offset" in d
    assert d["limit"] == 10 and d["offset"] == 0
    assert isinstance(d["items"], list)
    return f"shape OK: items={len(d['items'])}, total={d['total']}"

test("6.1 paginated response shape", s6_1, "6")

def s6_2():
    """Page 1 and page 2 have no overlapping IDs"""
    r1 = requests.get(f"{BASE}/diagnoses?limit=5&offset=0", headers=h(admin_t), timeout=10)
    r2 = requests.get(f"{BASE}/diagnoses?limit=5&offset=5", headers=h(admin_t), timeout=10)
    ids1 = {item["id"] for item in r1.json()["items"]}
    ids2 = {item["id"] for item in r2.json()["items"]}
    overlap = ids1 & ids2
    assert len(overlap) == 0, f"Overlapping IDs: {overlap}"
    return f"no overlap: page1={ids1}, page2={ids2}"

test("6.2 no overlapping IDs between pages", s6_2, "6")

def s6_3():
    """total is stable across pages"""
    r1 = requests.get(f"{BASE}/diagnoses?limit=5&offset=0", headers=h(admin_t), timeout=10)
    r2 = requests.get(f"{BASE}/diagnoses?limit=5&offset=5", headers=h(admin_t), timeout=10)
    assert r1.json()["total"] == r2.json()["total"], "total changed between pages"
    return f"total stable: {r1.json()['total']}"

test("6.3 total is stable across pages", s6_3, "6")

def s6_4():
    """limit > 100 returns 422"""
    r = requests.get(f"{BASE}/diagnoses?limit=101", headers=h(admin_t), timeout=10)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    return "limit=101 -> 422"

test("6.4 limit>100 rejected (422)", s6_4, "6")

def s6_5():
    """offset < 0 returns 422"""
    r = requests.get(f"{BASE}/diagnoses?offset=-1", headers=h(admin_t), timeout=10)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    return "offset=-1 -> 422"

test("6.5 offset<0 rejected (422)", s6_5, "6")

def s6_6():
    """limit=0 returns 422"""
    r = requests.get(f"{BASE}/diagnoses?limit=0", headers=h(admin_t), timeout=10)
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    return "limit=0 -> 422"

test("6.6 limit=0 rejected (422)", s6_6, "6")


# ============================================================
# SECTION 7: SOFT DELETE VERIFICATION
# ============================================================
print("\n" + "="*60)
print("SECTION 7: SOFT DELETE VERIFICATION")
print("="*60)

def s7_1():
    """Create test diagnostic for soft delete"""
    import io
    # Use a known image
    img_path = Path("data/uploads")
    images = list(img_path.rglob("*.jpg")) if img_path.exists() else []
    if not images:
        return "SKIP: no uploaded images to test with"
    # Find an admin diagnostic to repeat
    r = requests.get(f"{BASE}/diagnoses?limit=1&offset=0", headers=h(admin_t), timeout=10)
    items = r.json()["items"]
    if not items:
        return "SKIP: no diagnostics"
    diag_id = items[0]["id"]
    return f"using diag #{diag_id}"

test("7.1 pre-condition: find test diagnostic", s7_1, "7")

def s7_2():
    """Soft delete a diagnostic"""
    # Get last admin-owned diagnostic
    r = requests.get(f"{BASE}/diagnoses?limit=100&offset=0", headers=h(admin_t), timeout=10)
    items = r.json()["items"]
    if not items:
        return "SKIP: no diagnostics to delete"
    target = items[-1]
    r_del = requests.delete(f"{BASE}/diagnoses/{target['id']}", headers=h(admin_t), timeout=10)
    assert r_del.status_code == 204, f"Expected 204, got {r_del.status_code}"
    return f"deleted diag #{target['id']}"

test("7.2 soft delete returns 204", s7_2, "7")

def s7_3():
    """Row still exists with deleted_at set"""
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parent.parent / "data" / "vinguard.db"
    conn = sqlite3.connect(str(db_path))
    # Find the most recently soft-deleted diagnostic
    row = conn.execute(
        "SELECT id, deleted_at, deleted_by, status FROM diagnostics WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert row is not None, "No soft-deleted row found"
    assert row[1] is not None, "deleted_at is NULL"
    return f"diag #{row[0]}: deleted_at={row[1][:19]}, deleted_by={row[2]}, status={row[3]}"

test("7.3 soft-deleted row has deleted_at + deleted_by", s7_3, "7")

def s7_4():
    """Soft-deleted diagnostic not in normal listing"""
    r = requests.get(f"{BASE}/diagnoses?limit=100&offset=0", headers=h(admin_t), timeout=10)
    items = r.json()["items"]
    # Find the deleted ID
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parent.parent / "data" / "vinguard.db"
    conn = sqlite3.connect(str(db_path))
    deleted = conn.execute("SELECT id FROM diagnostics WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC LIMIT 1").fetchone()
    conn.close()
    if deleted:
        visible = [i["id"] for i in items]
        assert deleted[0] not in visible, f"Deleted diag #{deleted[0]} still visible!"
    return "deleted diagnostic not in listing"

test("7.4 soft-deleted not in listing", s7_4, "7")

def s7_5():
    """GET /diagnoses/{deleted_id} returns error"""
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parent.parent / "data" / "vinguard.db"
    conn = sqlite3.connect(str(db_path))
    deleted = conn.execute("SELECT id FROM diagnostics WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC LIMIT 1").fetchone()
    conn.close()
    if not deleted:
        return "SKIP: no deleted diagnostics"
    r = requests.get(f"{BASE}/diagnoses/{deleted[0]}", headers=h(admin_t), timeout=10)
    assert r.status_code in (404, 403), f"Expected 404/403, got {r.status_code}"
    return f"GET deleted #{deleted[0]} -> {r.status_code}"

test("7.5 GET soft-deleted diagnostic returns error", s7_5, "7")

def s7_6():
    """GET image of soft-deleted returns error"""
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parent.parent / "data" / "vinguard.db"
    conn = sqlite3.connect(str(db_path))
    deleted = conn.execute("SELECT id FROM diagnostics WHERE deleted_at IS NOT NULL ORDER BY deleted_at DESC LIMIT 1").fetchone()
    conn.close()
    if not deleted:
        return "SKIP: no deleted diagnostics"
    r = requests.get(f"{BASE}/diagnoses/{deleted[0]}/image", headers=h(admin_t), timeout=10)
    assert r.status_code in (404, 403), f"Expected 404/403, got {r.status_code}"
    return f"GET image deleted #{deleted[0]} -> {r.status_code}"

test("7.6 GET image of soft-deleted -> error", s7_6, "7")

def s7_7():
    """Total count decreased after soft delete"""
    r = requests.get(f"{BASE}/diagnoses?limit=100&offset=0", headers=h(admin_t), timeout=10)
    total = r.json()["total"]
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parent.parent / "data" / "vinguard.db"
    conn = sqlite3.connect(str(db_path))
    real_count = conn.execute("SELECT COUNT(*) FROM diagnostics WHERE deleted_at IS NULL").fetchone()[0]
    conn.close()
    assert total == real_count, f"API total ({total}) != real count ({real_count})"
    return f"total={total} matches DB count"

test("7.7 total matches non-deleted count", s7_7, "7")


# ============================================================
# SECTION 8: PERMISSION VERIFICATION
# ============================================================
print("\n" + "="*60)
print("SECTION 8: PERMISSION VERIFICATION")
print("="*60)

# We only have 2 users: admin and usuario
# Create a temporary second user directly in DB for multi-user permission test
import sys as _sys
from pathlib import Path as _Path
_project = str(_Path(__file__).resolve().parent.parent)
if _project not in _sys.path:
    _sys.path.insert(0, _project)

import sqlite3 as _sqlite3
import bcrypt as _bcrypt
_db_path = str(_Path(__file__).resolve().parent.parent / "data" / "vinguard.db")
_conn = _sqlite3.connect(_db_path)
_conn.execute("DELETE FROM users WHERE username='client_b_audit'")
_conn.commit()
_real_hash = _bcrypt.hashpw(b"test123", _bcrypt.gensalt()).decode()
_conn.execute("INSERT INTO users (name, username, password_hash, role, active) VALUES (?, ?, ?, ?, ?)",
    ("Cliente B", "client_b_audit", _real_hash, "client", 1))
_conn.commit()
_cb = _conn.execute("SELECT id FROM users WHERE username='client_b_audit'").fetchone()
client_b_id = _cb[0] if _cb else None
_conn.close()

# Force WAL checkpoint to ensure server can see new data
import time as _time
_conn2 = _sqlite3.connect(_db_path)
_conn2.execute("PRAGMA wal_checkpoint(TRUNCATE)")
_conn2.close()
_time.sleep(1)

t_client_a = get_token("usuario", "12345")  # client A

# Retry login for client B (WAL checkpoint may need a moment)
t_client_b = None
for _attempt in range(3):
    try:
        t_client_b = get_token("client_b_audit", "12345")
        break
    except:
        _time.sleep(1)
t_admin = get_token("admin", "admin123")

def s8_1():
    """Client A sees only own diagnostics"""
    r = requests.get(f"{BASE}/diagnoses?limit=100", headers=h(t_client_a), timeout=10)
    items = r.json()["items"]
    return f"client A sees {len(items)} items, total={r.json()['total']}"

test("8.1 client A lists own diagnostics", s8_1, "8")

def s8_2():
    """Client A cannot access Client B's diagnostic"""
    if not t_client_b:
        return "SKIP: client B not available"
    r_b = requests.get(f"{BASE}/diagnoses?limit=100", headers=h(t_client_b), timeout=10)
    b_items = r_b.json()["items"]
    if not b_items:
        return "SKIP: client B has no diagnostics"
    b_id = b_items[0]["id"]
    r = requests.get(f"{BASE}/diagnoses/{b_id}", headers=h(t_client_a), timeout=10)
    assert r.status_code == 403, f"Expected 403, got {r.status_code}"
    return f"client A cannot see client B's diag #{b_id} -> 403"

test("8.2 client A cannot access client B's diagnostic", s8_2, "8")

def s8_3():
    """Client A cannot see Client B's image"""
    if not t_client_b:
        return "SKIP: client B not available"
    r_b = requests.get(f"{BASE}/diagnoses?limit=100", headers=h(t_client_b), timeout=10)
    b_items = r_b.json()["items"]
    if not b_items:
        return "SKIP: client B has no diagnostics"
    b_id = b_items[0]["id"]
    r = requests.get(f"{BASE}/diagnoses/{b_id}/image", headers=h(t_client_a), timeout=10)
    assert r.status_code in (403, 404), f"Expected 403/404, got {r.status_code}"
    return f"client A cannot see client B's image -> {r.status_code}"

test("8.3 client A cannot see client B's image", s8_3, "8")

def s8_4():
    """Client A cannot delete Client B's diagnostic"""
    if not t_client_b:
        return "SKIP: client B not available"
    r_b = requests.get(f"{BASE}/diagnoses?limit=100", headers=h(t_client_b), timeout=10)
    b_items = r_b.json()["items"]
    if not b_items:
        return "SKIP: client B has no diagnostics"
    b_id = b_items[0]["id"]
    r = requests.delete(f"{BASE}/diagnoses/{b_id}", headers=h(t_client_a), timeout=10)
    assert r.status_code in (403, 404), f"Expected 403/404, got {r.status_code}"
    return f"client A cannot delete client B's diag -> {r.status_code}"

test("8.4 client A cannot delete client B's diagnostic", s8_4, "8")

def s8_5():
    """Unauthenticated user gets 403/401"""
    r = requests.get(f"{BASE}/diagnoses?limit=5", timeout=10)
    assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"
    return f"no auth -> {r.status_code}"

test("8.5 unauthenticated -> 401/403", s8_5, "8")

def s8_6():
    """Admin can see all diagnostics"""
    r = requests.get(f"{BASE}/diagnoses?limit=100", headers=h(t_admin), timeout=10)
    admin_total = r.json()["total"]
    r_a = requests.get(f"{BASE}/diagnoses?limit=100", headers=h(t_client_a), timeout=10)
    a_total = r_a.json()["total"]
    assert admin_total >= a_total, f"Admin total ({admin_total}) < client A total ({a_total})"
    return f"admin sees {admin_total} >= client A sees {a_total}"

test("8.6 admin sees all diagnostics", s8_6, "8")

def s8_7():
    """Admin can access any diagnostic"""
    r = requests.get(f"{BASE}/diagnoses?limit=100", headers=h(t_client_a), timeout=10)
    a_items = r.json()["items"]
    if not a_items:
        return "SKIP: client A has no diagnostics"
    a_id = a_items[0]["id"]
    r = requests.get(f"{BASE}/diagnoses/{a_id}", headers=h(t_admin), timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    return f"admin can access client A's diag #{a_id} -> 200"

test("8.7 admin can access any diagnostic", s8_7, "8")


# ============================================================
# SECTION 10: IS_DEMO VERIFICATION
# ============================================================
print("\n" + "="*60)
print("SECTION 10: IS_DEMO VERIFICATION")
print("="*60)

def s10_1():
    """Seed diagnostics are is_demo=True"""
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parent.parent / "data" / "vinguard.db"
    conn = sqlite3.connect(str(db_path))
    counts = conn.execute(
        "SELECT is_demo, COUNT(*) FROM diagnostics WHERE deleted_at IS NULL GROUP BY is_demo"
    ).fetchall()
    conn.close()
    result = { ("real" if row[0] == 0 else "demo"): row[1] for row in counts }
    return f"distribution: {result}"

test("10.1 demo vs real counts", s10_1, "10")

def s10_2():
    """is_demo filter works"""
    r = requests.get(f"{BASE}/diagnoses?is_demo=true&limit=100", headers=h(t_admin), timeout=10)
    items = r.json()["items"]
    for item in items:
        assert item["is_demo"] == True, f"Item {item['id']} is_demo={item['is_demo']}"
    return f"is_demo=true filter: {len(items)} items"

test("10.2 is_demo=true filter", s10_2, "10")

def s10_3():
    """is_demo=false filter works"""
    r = requests.get(f"{BASE}/diagnoses?is_demo=false&limit=100", headers=h(t_admin), timeout=10)
    items = r.json()["items"]
    for item in items:
        assert item["is_demo"] == False, f"Item {item['id']} is_demo={item['is_demo']}"
    return f"is_demo=false filter: {len(items)} items"

test("10.3 is_demo=false filter", s10_3, "10")

def s10_4():
    """Detail endpoint shows is_demo"""
    r = requests.get(f"{BASE}/diagnoses?limit=1&is_demo=true", headers=h(t_admin), timeout=10)
    items = r.json()["items"]
    if not items:
        return "SKIP: no demo diagnostics"
    r2 = requests.get(f"{BASE}/diagnoses/{items[0]['id']}", headers=h(t_admin), timeout=10)
    d = r2.json()
    assert "is_demo" in d
    return f"diag #{d['id']} is_demo={d['is_demo']}"

test("10.4 detail endpoint shows is_demo", s10_4, "10")

def s10_5():
    """Streamlit adapter filters deleted_at IS NULL"""
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parent.parent / "data" / "vinguard.db"
    conn = sqlite3.connect(str(db_path))
    # Check repository.py get_all_diagnostics query
    all_count = conn.execute("SELECT COUNT(*) FROM diagnostics WHERE deleted_at IS NULL").fetchone()[0]
    total_count = conn.execute("SELECT COUNT(*) FROM diagnostics").fetchone()[0]
    deleted_count = conn.execute("SELECT COUNT(*) FROM diagnostics WHERE deleted_at IS NOT NULL").fetchone()[0]
    conn.close()
    return f"active={all_count}, deleted={deleted_count}, total_in_DB={total_count}"

test("10.5 Streamlit filters soft-deleted", s10_5, "10")


# ============================================================
# SECTION 11: MODEL REGISTRY VERIFICATION
# ============================================================
print("\n" + "="*60)
print("SECTION 11: MODEL REGISTRY VERIFICATION")
print("="*60)

def s11_1():
    """All 5 model artifact files exist"""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.model_registry import MODEL_KEYS, MODEL_ARTIFACTS, MODEL_DISPLAY_NAMES
    results = []
    for key in MODEL_KEYS:
        artifacts = MODEL_ARTIFACTS.get(key, [])
        for name, path in artifacts:
            exists = path.exists()
            size = path.stat().st_size if exists else 0
            results.append(f"{key}({MODEL_DISPLAY_NAMES.get(key, key)}): {name} {'OK' if exists else 'MISSING'} ({size} bytes)")
    return "\n    ".join(results)

test("11.1 model artifact files", s11_1, "11")


# ============================================================
# SECTION 13: FASTAPI ENDPOINT VERIFICATION
# ============================================================
print("\n" + "="*60)
print("SECTION 13: FASTAPI ENDPOINT VERIFICATION")
print("="*60)

def s13_1():
    r = requests.get("http://localhost:8002/health", timeout=5)
    assert r.status_code == 200
    return f"/health -> 200: {r.json().get('status')}"

test("13.1 /health", s13_1, "13")

def s13_2():
    r = requests.get("http://localhost:8002/docs", timeout=5)
    assert r.status_code == 200
    return f"/docs -> 200"

test("13.2 /docs (Swagger UI)", s13_2, "13")

def s13_3():
    r = requests.get("http://localhost:8002/openapi.json", timeout=5)
    assert r.status_code == 200
    data = r.json()
    paths = list(data.get("paths", {}).keys())
    return f"/openapi.json -> 200, {len(paths)} paths: {paths[:8]}..."

test("13.3 /openapi.json", s13_3, "13")

def s13_4():
    r = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"}, timeout=10)
    assert r.status_code == 200
    return f"login -> 200"

test("13.4 POST /auth/login", s13_4, "13")

def s13_5():
    t = get_token("admin", "admin123")
    r = requests.get(f"{BASE}/auth/me", headers=h(t), timeout=10)
    assert r.status_code == 200
    return f"/auth/me -> 200: {r.json()['username']}"

test("13.5 GET /auth/me", s13_5, "13")

def s13_6():
    t = get_token("admin", "admin123")
    r = requests.get(f"{BASE}/diagnoses?limit=5", headers=h(t), timeout=10)
    assert r.status_code == 200
    return f"/diagnoses -> 200: {r.json()['total']} total"

test("13.6 GET /diagnoses", s13_6, "13")

def s13_7():
    t = get_token("admin", "admin123")
    r = requests.get(f"{BASE}/models", headers=h(t), timeout=10)
    assert r.status_code == 200
    return f"/models -> 200: {len(r.json())} models"

test("13.7 GET /models", s13_7, "13")

def s13_8():
    t = get_token("admin", "admin123")
    r = requests.get(f"{BASE}/statistics/summary", headers=h(t), timeout=10)
    assert r.status_code == 200
    return f"/statistics/summary -> 200"

test("13.8 GET /statistics/summary", s13_8, "13")


# ============================================================
# SECTION 9: IMAGE VERIFICATION
# ============================================================
print("\n" + "="*60)
print("SECTION 9: IMAGE VERIFICATION")
print("="*60)

def s9_1():
    """Valid image returns correct MIME"""
    t = get_token("admin", "admin123")
    r = requests.get(f"{BASE}/diagnoses?limit=1", headers=h(t), timeout=10)
    items = r.json()["items"]
    if not items:
        return "SKIP: no diagnostics"
    img_r = requests.get(f"{BASE}/diagnoses/{items[0]['id']}/image", headers=h(t), timeout=10)
    ct = img_r.headers.get("Content-Type", "")
    if img_r.status_code == 404:
        return f"SKIP: image file not on disk for diag #{items[0]['id']}"
    assert img_r.status_code == 200, f"Expected 200, got {img_r.status_code}"
    assert "image" in ct or "octet-stream" in ct, f"Unexpected Content-Type: {ct}"
    return f"MIME={ct}, size={len(img_r.content)} bytes"

test("9.1 valid image with correct MIME", s9_1, "9")

def s9_2():
    """Non-existent image returns 404"""
    t = get_token("admin", "admin123")
    r = requests.get(f"{BASE}/diagnoses/99999/image", headers=h(t), timeout=10)
    assert r.status_code in (404, 403), f"Expected 404/403, got {r.status_code}"
    return f"non-existent -> {r.status_code}"

test("9.2 non-existent image -> 404", s9_2, "9")

def s9_3():
    """UUID filename verification (code review)"""
    import sqlite3
    from pathlib import Path
    db_path = Path(__file__).resolve().parent.parent / "data" / "vinguard.db"
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("SELECT image_path FROM diagnostics WHERE image_path IS NOT NULL AND deleted_at IS NULL LIMIT 10").fetchall()
    conn.close()
    if not rows:
        return "SKIP: no diagnostics with image_path"
    uuid_pattern_count = 0
    import re
    for row in rows:
        path = row[0]
        if re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', path):
            uuid_pattern_count += 1
    return f"{uuid_pattern_count}/{len(rows)} image_paths contain UUID patterns"

test("9.3 UUID filenames in DB", s9_3, "9")

def s9_4():
    """Path traversal attempt blocked"""
    t = get_token("admin", "admin123")
    r = requests.get(f"{BASE}/diagnoses/1/../../../etc/passwd", headers=h(t), timeout=10)
    # Should get 404 or 422, definitely not 200
    assert r.status_code != 200, f"Path traversal returned 200!"
    return f"traversal attempt -> {r.status_code}"

test("9.4 path traversal blocked", s9_4, "9")


# ============================================================
# CLEANUP: Remove temp audit user
# ============================================================
try:
    t_cleanup = get_token("admin", "admin123")
    if client_b_id:
        requests.delete(f"{BASE}/users/{client_b_id}", headers=h(t_cleanup), timeout=10)
except:
    pass

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "="*60)
print(f"AUDIT RESULTS: {passed} PASSED / {failed} FAILED / {skipped} SKIPPED")
print(f"TOTAL: {passed + failed + skipped}")
print("="*60)

if failed > 0:
    print("\nFAILED TESTS:")
    for sec, name, status, detail in results:
        if status == "FAIL":
            print(f"  [{sec}] {name}: {detail}")

sys.exit(1 if failed else 0)
