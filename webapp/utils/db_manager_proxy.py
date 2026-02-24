"""Backend API powered drop-in replacement for DatabaseManager."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from config.database_config import get_persistent_sqlite_path
from utils.backend_api_client import backend_api_base_url


class BackendDatabaseManagerProxy:
    """Implements DatabaseManager-like methods via external FastAPI."""

    def __init__(self):
        self.config = None
        self._connected = False
        self._last_schema: Optional[Dict[str, Any]] = None

    def _headers(self) -> Dict[str, str]:
        import os

        token = (os.getenv("BACKEND_API_TOKEN") or "").strip()
        return {"X-API-Token": token} if token else {}

    def _config_payload(self) -> Dict[str, Any]:
        if self.config is None:
            raise ValueError("No configuration provided")
        if is_dataclass(self.config):
            payload = asdict(self.config)
        else:
            payload = dict(self.config)
        if payload.get("db_type") == "sqlite":
            payload["database"] = get_persistent_sqlite_path()
            payload["host"] = ""
            payload["port"] = 0
            payload["username"] = ""
            payload["password"] = ""
        return payload

    def _post(self, path: str, payload: Dict[str, Any], timeout: int = 90) -> Dict[str, Any]:
        url = f"{backend_api_base_url()}{path}"
        response = requests.post(url, json=payload, headers=self._headers(), timeout=timeout)
        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json().get("detail", detail)
            except Exception:
                pass
            raise ValueError(str(detail))
        return response.json()

    def connect(self, config: Optional[Any] = None, connection_id: str = "default") -> bool:
        if config is not None:
            self.config = config
        schema = self._post("/v1/schema", {"db_config": self._config_payload()}, timeout=120)
        self._last_schema = schema
        self._connected = True
        return True

    def disconnect(self, connection_id: str = "default"):
        self._connected = False

    def get_engine(self, connection_id: str = "default"):
        return None

    def execute_query(self, query: str, connection_id: str = "default") -> pd.DataFrame:
        result = self._post(
            "/v1/query/execute",
            {"db_config": self._config_payload(), "query": query},
            timeout=180,
        )
        if result.get("kind") != "result_set":
            raise ValueError("Query did not return a result set")
        rows = result.get("rows", []) or []
        columns = result.get("columns", []) or []
        return pd.DataFrame(rows, columns=columns if columns else None)

    def execute_non_query(self, query: str, connection_id: str = "default") -> int:
        result = self._post(
            "/v1/query/execute",
            {"db_config": self._config_payload(), "query": query},
            timeout=180,
        )
        if result.get("kind") == "non_query":
            return int(result.get("affected_rows") or 0)
        return 0

    def get_database_info(self, connection_id: str = "default") -> Dict[str, Any]:
        schema = self._post("/v1/schema", {"db_config": self._config_payload()}, timeout=120)
        self._last_schema = schema
        return schema

    def get_tables(self, connection_id: str = "default") -> List[str]:
        schema = self.get_database_info(connection_id)
        tables = schema.get("tables", []) if isinstance(schema, dict) else []
        names: List[str] = []
        for t in tables:
            if isinstance(t, dict):
                names.append(str(t.get("table_name", "")))
            else:
                names.append(str(t))
        return [n for n in names if n]

    def get_table_schema(self, table_name: str, connection_id: str = "default") -> Dict[str, Any]:
        schema = self.get_database_info(connection_id)
        for t in schema.get("tables", []):
            if isinstance(t, dict) and str(t.get("table_name")) == str(table_name):
                return t
        return {"table_name": table_name, "columns": [], "primary_keys": [], "foreign_keys": []}
