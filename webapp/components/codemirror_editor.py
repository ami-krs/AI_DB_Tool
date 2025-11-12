"""CodeMirror editor Streamlit component wrapper."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from uuid import uuid4

import streamlit.components.v1 as components

_COMPONENT_DIR = os.path.join(
    os.path.dirname(__file__), "codemirror_editor_component", "build"
)

_codemirror_component = components.declare_component(
    "codemirror_editor",
    path=_COMPONENT_DIR,
)


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
