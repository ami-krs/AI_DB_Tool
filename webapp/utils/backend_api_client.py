"""Client helpers for optional external FastAPI backend."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests
import streamlit as st


def _get_backend_config(key: str) -> str:
    """Get config from env or Streamlit secrets (for Streamlit Cloud)."""
    val = (os.getenv(key) or "").strip()
    if val:
        return val
    try:
        if hasattr(st, "secrets") and st.secrets:
            # st.secrets supports dict-like and attribute access
            secret = st.secrets.get(key) if hasattr(st.secrets, "get") else getattr(st.secrets, key, None)
            if secret is not None:
                return str(secret).strip()
    except Exception:
        pass
    return ""


def backend_api_enabled() -> bool:
    """Return True when Streamlit should call external backend API."""
    raw = _get_backend_config("USE_BACKEND_API").lower()
    return raw in {"1", "true", "yes", "on"}


def backend_api_base_url() -> str:
    """Resolve backend base URL from env, secrets, or session state."""
    url = (
        _get_backend_config("BACKEND_API_URL")
        or st.session_state.get("api_server_url")
        or "http://localhost:8000"
    )
    return url.rstrip("/")


def _headers() -> Dict[str, str]:
    token = _get_backend_config("BACKEND_API_TOKEN")
    return {"X-API-Token": token} if token else {}


def backend_api_chat(
    user_message: str,
    include_sql: bool = True,
    schema_context: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 90,
) -> Dict[str, Any]:
    """Call external backend chat endpoint."""
    payload: Dict[str, Any] = {
        "user_message": user_message,
        "include_sql": include_sql,
        "schema_context": schema_context,
    }
    response = requests.post(
        f"{backend_api_base_url()}/v1/chat",
        json=payload,
        headers=_headers(),
        timeout=timeout_seconds,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Backend chat failed: {response.status_code} {response.text}")
    return response.json()
