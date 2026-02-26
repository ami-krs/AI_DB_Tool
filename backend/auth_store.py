"""
Simple SQLite-backed user store for email/password auth.
Passwords are hashed with the bcrypt library (no passlib).
"""

from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

try:
    import bcrypt

    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

ROOT_DIR = Path(__file__).resolve().parents[1]
# Default to /data/auth.db so it can live on a persistent disk (e.g. Render disk mounted at /data).
# Can be overridden with AUTH_DB_PATH env var.
AUTH_DB_PATH = Path(os.environ.get("AUTH_DB_PATH", "/data/auth.db"))

# Bcrypt supports at most 72 bytes
BCRYPT_MAX_PASSWORD_BYTES = 72


def _password_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:BCRYPT_MAX_PASSWORD_BYTES]


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
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                token TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def register(email: str, password: str, name: Optional[str] = None) -> dict:
    """Register a new user. Returns user dict or raises ValueError."""
    if not HAS_BCRYPT:
        raise ValueError("Auth not available: install bcrypt")
    email = email.strip().lower()
    if not email or "@" not in email:
        raise ValueError("Invalid email")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters")
    password_hash = bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("ascii")
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
        if not row:
            return None
        stored = row["password_hash"]
        if isinstance(stored, str):
            stored = stored.encode("ascii")
        if not bcrypt.checkpw(_password_bytes(password), stored):
            return None
        return {"id": row["id"], "email": row["email"], "name": row["name"], "created_at": row["created_at"]}
    finally:
        conn.close()


def set_password(email: str, new_password: str) -> None:
    """Set a new password for an existing user."""
    if not HAS_BCRYPT:
        raise ValueError("Auth not available: install bcrypt")
    email = email.strip().lower()
    if not email or "@" not in email:
        raise ValueError("Invalid email")
    if not new_password or len(new_password) < 6:
        raise ValueError("Password must be at least 6 characters")
    password_hash = bcrypt.hashpw(_password_bytes(new_password), bcrypt.gensalt()).decode("ascii")
    conn = _get_conn()
    try:
        cur = conn.execute(
            "UPDATE users SET password_hash = ? WHERE email = ?",
            (password_hash, email),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise ValueError("User not found")
    finally:
        conn.close()


# Reset token expiry (e.g. 1 hour)
RESET_TOKEN_EXPIRY_HOURS = 1


def create_reset_token(email: str) -> Optional[str]:
    """
    Create a password-reset token for the given email only if the user exists.
    Returns the token (to put in the email link) or None if user not found.
    """
    email = email.strip().lower()
    if not email or "@" not in email:
        return None
    conn = _get_conn()
    try:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not row:
            return None
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.utcnow() + timedelta(hours=RESET_TOKEN_EXPIRY_HOURS)).isoformat()
        conn.execute(
            "INSERT INTO password_reset_tokens (token, email, expires_at) VALUES (?, ?, ?)",
            (token, email, expires_at),
        )
        conn.commit()
        return token
    finally:
        conn.close()


def consume_reset_token(token: str) -> Optional[str]:
    """
    Validate the reset token and return the associated email if valid.
    Deletes the token (one-time use). Returns None if invalid or expired.
    """
    if not token or len(token) < 16:
        return None
    conn = _get_conn()
    try:
        row = conn.execute(
            "SELECT email, expires_at FROM password_reset_tokens WHERE token = ?",
            (token,),
        ).fetchone()
        if not row:
            return None
        try:
            expires_at = datetime.fromisoformat(row["expires_at"])
        except (ValueError, TypeError):
            conn.execute("DELETE FROM password_reset_tokens WHERE token = ?", (token,))
            conn.commit()
            return None
        if datetime.utcnow() > expires_at:
            conn.execute("DELETE FROM password_reset_tokens WHERE token = ?", (token,))
            conn.commit()
            return None
        email = row["email"]
        conn.execute("DELETE FROM password_reset_tokens WHERE token = ?", (token,))
        conn.commit()
        return email
    finally:
        conn.close()


init_db()
