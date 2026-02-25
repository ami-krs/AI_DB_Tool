"""
Simple SQLite-backed user store for email/password auth.
Passwords are hashed with bcrypt via passlib.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Optional

# Optional: use passlib for bcrypt; fallback to no auth if not installed
try:
    from passlib.hash import bcrypt

    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

ROOT_DIR = Path(__file__).resolve().parents[1]
AUTH_DB_PATH = Path(os.environ.get("AUTH_DB_PATH", str(ROOT_DIR / "data" / "auth.db")))

# Bcrypt supports at most 72 bytes; truncate to avoid error
BCRYPT_MAX_PASSWORD_BYTES = 72


def _truncate_password_for_bcrypt(password: str) -> str:
    encoded = password.encode("utf-8")[:BCRYPT_MAX_PASSWORD_BYTES]
    return encoded.decode("utf-8", errors="ignore")


def _get_conn():
    AUTH_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(AUTH_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create users table if it does not exist."""
    conn = _get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def register(email: str, password: str, name: Optional[str] = None) -> dict:
    """Register a new user. Returns user dict or raises ValueError."""
    if not HAS_BCRYPT:
        raise ValueError("Auth not available: install passlib[bcrypt]")
    email = email.strip().lower()
    if not email or "@" not in email:
        raise ValueError("Invalid email")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    password_hash = bcrypt.hash(_truncate_password_for_bcrypt(password))
    from datetime import datetime

    created_at = datetime.utcnow().isoformat()
    conn = _get_conn()
    try:
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, name, created_at) VALUES (?, ?, ?, ?)",
            (email, password_hash, (name or "").strip() or None, created_at),
        )
        conn.commit()
        row = conn.execute("SELECT id, email, name, created_at FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row) if row else {"email": email, "name": name}
    except sqlite3.IntegrityError:
        raise ValueError("Email already registered")
    finally:
        conn.close()


def verify_user(email: str, password: str) -> Optional[dict]:
    """Verify credentials. Returns user dict (without password) or None."""
    if not HAS_BCRYPT:
        return None
    email = email.strip().lower()
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT id, email, password_hash, name, created_at FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        if not row or not bcrypt.verify(_truncate_password_for_bcrypt(password), row["password_hash"]):
            return None
        return {"id": row["id"], "email": row["email"], "name": row["name"], "created_at": row["created_at"]}
    finally:
        conn.close()


init_db()
