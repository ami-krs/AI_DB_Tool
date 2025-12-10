"""CodeMirror editor Streamlit component wrapper."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

import streamlit.components.v1 as components

# Use absolute path for better compatibility with Streamlit Cloud
_COMPONENT_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "codemirror_editor_component", "build"
    )
)

# Check if component directory and required files exist
_component_available = (
    os.path.exists(_COMPONENT_DIR) and
    os.path.exists(os.path.join(_COMPONENT_DIR, "index.html")) and
    os.path.exists(os.path.join(_COMPONENT_DIR, "manifest.json"))
)

if not _component_available:
    _codemirror_component = None
else:
    try:
        _codemirror_component = components.declare_component(
            "codemirror_editor",
            path=_COMPONENT_DIR,
        )
    except Exception as e:
        # Log error but don't crash - app can still work with textarea
        import warnings
        warnings.warn(f"Failed to load CodeMirror component: {e}")
        _codemirror_component = None


def codemirror_editor(
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
    """Render the CodeMirror editor with AI autocomplete."""

    if _codemirror_component is None:
        raise ImportError(
            "CodeMirror editor component not found. "
            "The component build directory may be missing. "
            "Please ensure 'webapp/components/codemirror_editor_component/build' exists."
        )

    component_key = key or f"codemirror_{uuid4().hex}"

    component_value = _codemirror_component(
        value=value,
        height=height,
        language=language,
        theme=theme,
        apiUrl=api_url,
        databaseType=database_type or "",
        schemaInfo=schema_info or {},
        tables=tables or [],
        config=config or {},
        componentId=component_key,
        key=component_key,
        default=value,
    )

    return component_value if component_value is not None else value
