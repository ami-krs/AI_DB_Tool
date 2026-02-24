"""Client helpers for optional external FastAPI backend."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests
import streamlit as st


def backend_api_enabled() -> bool:
    """Return True when Streamlit should call external backend API."""
    raw = (os.getenv("USE_BACKEND_API") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def backend_api_base_url() -> str:
    """Resolve backend base URL from env or session state."""
    return (
        os.getenv("BACKEND_API_URL")
        or st.session_state.get("api_server_url")
        or "http://localhost:8000"
    ).rstrip("/")


def _headers() -> Dict[str, str]:
    token = (os.getenv("BACKEND_API_TOKEN") or "").strip()
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
