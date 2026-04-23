"""
utils/db.py — Centralized database layer for CareerAI Pro.
Uses SQLite with WAL mode for better concurrency and performance.
"""

import logging
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")


# ─────────────────────────── connection helpers ────────────────────────────

@contextmanager
def get_connection():
    """Context manager that yields a WAL-mode SQLite connection."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA cache_size=-8000")   # 8 MB page cache
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ───────────────────────────── schema init ─────────────────────────────────

def init_db() -> None:
    """Create all tables if they don't exist and run any pending migrations."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                name          TEXT NOT NULL,
                email         TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS job_applications (
                id           TEXT PRIMARY KEY,
                user_id      TEXT NOT NULL,
                job_title    TEXT,
                company      TEXT,
                location     TEXT,
                apply_link   TEXT,
                status       TEXT DEFAULT 'Saved',
                notes        TEXT,
                applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS job_cache (
                cache_key  TEXT PRIMARY KEY,
                jobs_json  TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT NOT NULL,
                role       TEXT NOT NULL,
                content    TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS ats_history (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT NOT NULL,
                role       TEXT,
                score      INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS env_config (
                key        TEXT PRIMARY KEY,
                value      TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id);
            CREATE INDEX IF NOT EXISTS idx_jobs_user ON job_applications(user_id);
            CREATE INDEX IF NOT EXISTS idx_ats_user  ON ats_history(user_id);
        """)
    _load_env_into_db()


def _load_env_into_db() -> None:
    """Sync .env values into env_config table for runtime access."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path) as f:
        lines = f.readlines()
    with get_connection() as conn:
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            conn.execute(
                "INSERT INTO env_config(key, value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key.strip(), val.strip()),
            )


def get_env_value(key: str) -> Optional[str]:
    """Retrieve a runtime config value; falls back to OS environment."""
    try:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM env_config WHERE key=?", (key,)
            ).fetchone()
            if row:
                return row["value"]
    except Exception:
        pass
    return os.environ.get(key)


def set_env_value(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO env_config(key, value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP",
            (key, value),
        )


# ───────────────────────────── user queries ────────────────────────────────

def create_user(name: str, email: str, password_hash: str) -> str:
    uid = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users(id, name, email, password_hash) VALUES(?,?,?,?)",
            (uid, name, email, password_hash),
        )
    return uid


def get_user_by_email(email: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email=?", (email,)
        ).fetchone()
        return dict(row) if row else None


# ──────────────────────────── chat history ─────────────────────────────────

def save_chat_message(user_id: str, role: str, content: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_history(user_id, role, content) VALUES(?,?,?)",
            (user_id, role, content),
        )


def get_chat_history(user_id: str, limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT role, content, created_at FROM chat_history "
            "WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def clear_chat_history(user_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))


# ───────────────────────────── ATS history ─────────────────────────────────

def save_ats_score(user_id: str, role: str, score: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO ats_history(user_id, role, score) VALUES(?,?,?)",
            (user_id, role, score),
        )


def get_ats_history(user_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT score, role, created_at FROM ats_history "
            "WHERE user_id=? ORDER BY id DESC LIMIT 20",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────── job applications ─────────────────────────────

def save_job(user_id: str, job: dict) -> str:
    jid = str(uuid.uuid4())
    with get_connection() as conn:
        # Prevent duplicates for same user + job title + company
        existing = conn.execute(
            "SELECT id FROM job_applications WHERE user_id=? AND job_title=? AND company=?",
            (user_id, job.get("title", ""), job.get("company", "")),
        ).fetchone()
        if existing:
            raise ValueError("Job already saved.")
        conn.execute(
            """INSERT INTO job_applications
               (id, user_id, job_title, company, location, apply_link, status, applied_date)
               VALUES(?,?,?,?,?,?,'Saved', CURRENT_TIMESTAMP)""",
            (
                jid, user_id,
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                job.get("apply_link", ""),
            ),
        )
    return jid


def list_jobs(user_id: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM job_applications WHERE user_id=? ORDER BY applied_date DESC",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def update_job(job_id: str, status: str, notes: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE job_applications SET status=?, notes=? WHERE id=?",
            (status, notes, job_id),
        )


def delete_job(job_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM job_applications WHERE id=?", (job_id,))


def get_job_stats(user_id: str) -> dict:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM job_applications "
            "WHERE user_id=? GROUP BY status",
            (user_id,),
        ).fetchall()
    return {r["status"]: r["cnt"] for r in rows}


# ───────────────────────────── job cache ───────────────────────────────────

def get_cached_jobs(cache_key: str) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT jobs_json FROM job_cache WHERE cache_key=? AND expires_at > CURRENT_TIMESTAMP",
            (cache_key,),
        ).fetchone()
    return row["jobs_json"] if row else None


def set_cached_jobs(cache_key: str, jobs_json: str, ttl_minutes: int = 30) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO job_cache(cache_key, jobs_json, expires_at) VALUES(?,?, "
            "datetime('now', '+' || ? || ' minutes')) "
            "ON CONFLICT(cache_key) DO UPDATE SET jobs_json=excluded.jobs_json, "
            "expires_at=excluded.expires_at",
            (cache_key, jobs_json, ttl_minutes),
        )


def cleanup_expired_cache() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM job_cache WHERE expires_at <= CURRENT_TIMESTAMP")
