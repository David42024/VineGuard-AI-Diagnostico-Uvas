"""SQLite persistence layer for VineGuard AI.

Streamlit adapter — reads via raw sqlite3 for backward compatibility.
Schema is owned by SQLAlchemy + Alembic; this file NEVER creates or
alters tables.

All write operations that modify the schema (INSERT/UPDATE/DELETE on
diagnostics) use soft delete consistent with the FastAPI layer.
"""

import sqlite3
import json
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.core.password_utils import hash_password, verify_password

logger = logging.getLogger("vinguard.db")

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "vinguard.db"


def init_database():
    """Compatibility stub — schema is owned by SQLAlchemy + Alembic.

    This function only ensures the data directory exists.  It does NOT
    create or alter any tables.  Table creation is handled exclusively
    by ``backend.database.database.init_db()`` and Alembic migrations.
    """
    DB_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("[DB] init_database() called — no-op (schema managed by SQLAlchemy + Alembic)")


def _get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _is_sha256_hash(h: str) -> bool:
    return len(h) == 64 and all(c in "0123456789abcdef" for c in h)


def _upgrade_hash(conn: sqlite3.Connection, user_id: int, password: str):
    new_hash = hash_password(password)
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (new_hash, user_id),
    )
    conn.commit()


def authenticate(username: str, password: str) -> Optional[dict]:
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT id, name, username, role, active, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not row or not row["active"]:
            return None

        stored_hash = row["password_hash"]

        try:
            if verify_password(password, stored_hash):
                conn.execute(
                    "UPDATE users SET last_login = datetime('now') WHERE id = ?",
                    (row["id"],),
                )
                conn.commit()
                audit_log(row["id"], "login", "Inicio de sesión exitoso")
                return dict(row)
        except Exception:
            pass

        if _is_sha256_hash(stored_hash):
            if hashlib.sha256(password.encode()).hexdigest() == stored_hash:
                _upgrade_hash(conn, row["id"], password)
                conn.execute(
                    "UPDATE users SET last_login = datetime('now') WHERE id = ?",
                    (row["id"],),
                )
                conn.commit()
                audit_log(row["id"], "login", "Hash migrado de SHA-256 a bcrypt")
                return dict(row)

        return None
    finally:
        conn.close()


def audit_log(user_id: int, action: str, detail: str = ""):
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO audit_log (user_id, action, detail) VALUES (?, ?, ?)",
            (user_id, action, detail),
        )
        conn.commit()
    finally:
        conn.close()


def save_diagnostic(user_id: int, filename: str, result: str, confidence: float,
                    model_used: str, probabilities: dict, inference_time_ms: float,
                    image_path: Optional[str] = None):
    conn = _get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO diagnostics
               (user_id, filename, image_path, result, confidence, model_used, probabilities, inference_time_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, filename, image_path, result, confidence, model_used,
             json.dumps(probabilities), inference_time_ms),
        )
        conn.commit()
        diag_id = cur.lastrowid
        logger.info(f"[DB] Diagnóstico #{diag_id} guardado: {result} ({confidence:.2f}) modelo={model_used} usuario={user_id}")
        print(f"[DB] Diagnóstico #{diag_id} guardado: {result} ({confidence:.2%}) — {model_used}")
        return diag_id
    except Exception as e:
        logger.error(f"[DB] Error guardando diagnóstico: {e}")
        print(f"[DB] Error guardando diagnóstico: {e}")
        raise
    finally:
        conn.close()


def get_user_diagnostics(user_id: int, limit: int = 50) -> list[dict]:
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT id, timestamp, filename, result, confidence, model_used,
                      inference_time_ms, status
               FROM diagnostics WHERE user_id = ? AND deleted_at IS NULL
               ORDER BY timestamp DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_diagnostics(limit: int = 200) -> list[dict]:
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT d.id, d.timestamp, d.filename, d.result, d.confidence,
                      d.model_used, d.status, u.name as user_name, u.username
               FROM diagnostics d JOIN users u ON d.user_id = u.id
               WHERE d.deleted_at IS NULL
               ORDER BY d.timestamp DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_diagnostic(diag_id: int, user_id: Optional[int] = None):
    """Soft delete — mirrors FastAPI behavior. Never executes DELETE FROM."""
    conn = _get_connection()
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        if user_id:
            conn.execute(
                """UPDATE diagnostics
                   SET deleted_at = ?, deleted_by = ?, status = 'deleted'
                   WHERE id = ? AND user_id = ? AND deleted_at IS NULL""",
                (now, user_id, diag_id, user_id),
            )
        else:
            conn.execute(
                """UPDATE diagnostics
                   SET deleted_at = ?, status = 'deleted'
                   WHERE id = ? AND deleted_at IS NULL""",
                (now, diag_id),
            )
        conn.commit()
    finally:
        conn.close()


def get_user_stats(user_id: int) -> dict:
    conn = _get_connection()
    try:
        total = conn.execute(
            "SELECT COUNT(*) as c FROM diagnostics WHERE user_id = ? AND deleted_at IS NULL",
            (user_id,),
        ).fetchone()["c"]
        healthy = conn.execute(
            "SELECT COUNT(*) as c FROM diagnostics WHERE user_id = ? AND result = 'Healthy' AND deleted_at IS NULL",
            (user_id,),
        ).fetchone()["c"]
        today = conn.execute(
            "SELECT COUNT(*) as c FROM diagnostics WHERE user_id = ? AND date(timestamp) = date('now') AND deleted_at IS NULL",
            (user_id,),
        ).fetchone()["c"]
        last = conn.execute(
            "SELECT result, confidence, timestamp FROM diagnostics WHERE user_id = ? AND deleted_at IS NULL ORDER BY timestamp DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return {
            "total": total,
            "healthy": healthy,
            "diseased": total - healthy,
            "today": today,
            "last_diagnosis": dict(last) if last else None,
        }
    finally:
        conn.close()


def get_admin_stats() -> dict:
    conn = _get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) as c FROM diagnostics WHERE deleted_at IS NULL").fetchone()["c"]
        today = conn.execute(
            "SELECT COUNT(*) as c FROM diagnostics WHERE date(timestamp) = date('now') AND deleted_at IS NULL"
        ).fetchone()["c"]
        healthy = conn.execute(
            "SELECT COUNT(*) as c FROM diagnostics WHERE result = 'Healthy' AND deleted_at IS NULL"
        ).fetchone()["c"]
        users = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
        return {
            "total_diagnostics": total,
            "today_diagnostics": today,
            "healthy_pct": (healthy / total * 100) if total else 0,
            "diseased_pct": ((total - healthy) / total * 100) if total else 0,
            "total_users": users,
        }
    finally:
        conn.close()


def get_disease_distribution() -> dict:
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT result, COUNT(*) as c FROM diagnostics WHERE deleted_at IS NULL GROUP BY result ORDER BY c DESC"
        ).fetchall()
        return {r["result"]: r["c"] for r in rows}
    finally:
        conn.close()


def get_diagnostics_by_date(days: int = 30) -> list[dict]:
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT date(timestamp) as date, COUNT(*) as count
               FROM diagnostics WHERE timestamp >= datetime('now', ?) AND deleted_at IS NULL
               GROUP BY date(timestamp) ORDER BY date""",
            (f"-{days} days",),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
