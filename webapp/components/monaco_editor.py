"""
Monaco Editor component wrapper.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import streamlit.components.v1 as components

# Use absolute path for better compatibility with Streamlit Cloud
_COMPONENT_DIR = Path(__file__).resolve().parent / "monaco_editor_component" / "build"

# Check if component directory and required files exist
_component_available = (
    _COMPONENT_DIR.exists() and
    (_COMPONENT_DIR / "index.html").exists() and
    (_COMPONENT_DIR / "manifest.json").exists()
)

if not _component_available:
    _monaco_component = None
else:
    try:
        _monaco_component = components.declare_component(
            "monaco_editor",
            path=str(_COMPONENT_DIR),
        )
    except Exception as e:
        # Log error but don't crash - app can still work with textarea
        import warnings
        warnings.warn(f"Failed to load Monaco component: {e}")
        _monaco_component = None


def monaco_editor(
    value: str = "",
    height: int = 300,
    language: str = "sql",
    theme: str = "vs",
    api_url: str = "http://localhost:8000",
    database_type: Optional[str] = None,
    schema_info: Optional[Dict[str, Any]] = None,
    tables: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None,
) -> str:
    """Render the Monaco editor with AI autocomplete."""

    if _monaco_component is None:
        raise ImportError(
            "Monaco editor component not found. "
            "The component build directory may be missing. "
            "Please ensure 'webapp/components/monaco_editor_component/build' exists."
        )

    component_key = key or f"monaco_{uuid4().hex}"

    component_value = _monaco_component(
        value=value,
        height=height,
        language=language,
        theme=theme,
        apiUrl=api_url,
        databaseType=database_type or "",
        schemaInfo=schema_info or {},
        tables=tables or [],
        componentId=component_key,
        config=config or {},
        default=value,
        key=component_key,
    )

    return component_value if component_value is not None else value

