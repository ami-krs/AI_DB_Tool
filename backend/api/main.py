"""
FastAPI backend for AI DB Tool.

This service is designed to run separately from Streamlit and provide:
- Chatbot responses (SQL + advisory)
- Query execution
- Schema retrieval
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure project root is on sys.path when running as a standalone backend service.
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ai_db_tool.ai.chatbot import SQLChatbot
from ai_db_tool.connectors.base import DatabaseConfig, DatabaseManager

from backend.smart_import import smart_import  # noqa: E402

load_dotenv()


class DBConfigPayload(BaseModel):
    db_type: str
    host: str = ""
    port: int = 0
    database: str
    username: str = ""
    password: str = ""
    extra_params: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    user_message: str
    include_sql: bool = True
    schema_context: Optional[Dict[str, Any]] = None


class QueryExecuteRequest(BaseModel):
    db_config: DBConfigPayload
    query: str = Field(min_length=1)


class SchemaRequest(BaseModel):
    db_config: DBConfigPayload


class ImportTableRequest(BaseModel):
    db_config: DBConfigPayload
    table_name: str = Field(min_length=1)
    rows: List[Dict[str, Any]] = Field(min_length=1)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _serialize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [{k: _serialize_value(v) for k, v in row.items()} for row in rows]


def _build_config(payload: DBConfigPayload) -> DatabaseConfig:
    return DatabaseConfig(
        db_type=payload.db_type,
        host=payload.host,
        port=payload.port,
        database=payload.database,
        username=payload.username,
        password=payload.password,
        extra_params=payload.extra_params,
    )


def _get_api_key() -> Optional[str]:
    return os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")


def _auth_guard(x_api_token: Optional[str]) -> None:
    expected = os.getenv("API_AUTH_TOKEN", "").strip()
    if expected and x_api_token != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


app = FastAPI(title="AI DB Tool Backend API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


def _is_upload_intent(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    upload = any(x in t for x in ["upload", "import", "load"])
    file_terms = any(x in t for x in ["file", "csv", "excel", "xlsx", "xls"])
    table_terms = any(x in t for x in ["table", "database", "db"])
    return upload and file_terms and table_terms


def _infer_table_from_message(user_message: str, schema_context: Optional[Dict[str, Any]]) -> Optional[str]:
    if not schema_context or not user_message:
        return None
    tables = schema_context.get("tables") or []
    if not tables:
        return None
    names = []
    for t in tables:
        if isinstance(t, dict):
            names.append(str(t.get("table_name", "")).strip())
        else:
            names.append(str(t).strip())
    names = [n for n in names if n]
    text = (user_message or "").strip().lower()
    best = None
    best_len = 0
    for n in names:
        if not n:
            continue
        n_lower = n.lower()
        if n_lower in text or n_lower.replace("_", " ") in text:
            if len(n_lower) > best_len:
                best = n
                best_len = len(n_lower)
    return best


@app.post("/v1/chat")
def chat(request: ChatRequest, x_api_token: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _auth_guard(x_api_token)
    api_key = _get_api_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured on backend")

    provider = "openai" if os.getenv("OPENAI_API_KEY") else "anthropic"
    chatbot = SQLChatbot(api_key=api_key, provider=provider)
    if request.schema_context:
        chatbot.set_schema_context(request.schema_context)

    response = chatbot.chat(request.user_message, include_sql=request.include_sql)
    if _is_upload_intent(request.user_message):
        response["show_upload_panel"] = True
        response["upload_target_table"] = _infer_table_from_message(
            request.user_message, request.schema_context
        )
        # Replace AI response so we don't show COPY FROM file SQL; direct user to upload panel
        table_hint = response.get("upload_target_table") or "the selected"
        response["response"] = (
            f"Use the **Upload** panel below to load your CSV into the table. "
            f"Choose the target table ({table_hint}), select your file, then click **Load file to table**. "
            f"Column names are matched automatically (case-insensitive) and primary key conflicts are handled for you. "
            f"Do not use COPY or a file path — the app uploads the file from your device."
        )
        response["sql_query"] = None
        if "error" in response:
            del response["error"]
    return response


@app.post("/v1/query/execute")
def execute_query(
    request: QueryExecuteRequest,
    x_api_token: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    _auth_guard(x_api_token)
    dbm = DatabaseManager()
    cfg = _build_config(request.db_config)
    if not dbm.connect(cfg):
        raise HTTPException(status_code=400, detail="Failed to connect to database")

    query = (request.query or "").strip()
    is_select_like = query.upper().startswith(("SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN", "PRAGMA"))

    try:
        if is_select_like:
            df = dbm.execute_query(query)
            rows = _serialize_rows(df.to_dict(orient="records"))
            return {
                "kind": "result_set",
                "columns": list(df.columns),
                "rows": rows,
                "row_count": len(rows),
            }
        affected = dbm.execute_non_query(query)
        return {
            "kind": "non_query",
            "affected_rows": affected,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        dbm.disconnect()


@app.post("/v1/schema")
def schema(request: SchemaRequest, x_api_token: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    _auth_guard(x_api_token)
    dbm = DatabaseManager()
    cfg = _build_config(request.db_config)
    if not dbm.connect(cfg):
        raise HTTPException(status_code=400, detail="Failed to connect to database")
    try:
        base = dbm.get_database_info()
        tables = dbm.get_tables()
        full_tables: List[Dict[str, Any]] = []
        for table_name in tables:
            try:
                full_tables.append(dbm.get_table_schema(table_name))
            except Exception:
                full_tables.append({"table_name": table_name, "columns": []})
        base["tables"] = full_tables
        base["total_tables"] = len(full_tables)
        # Chatbot expects db_type for SQL dialect (PostgreSQL vs SQLite etc.)
        base["db_type"] = base.get("database_type") or cfg.db_type or "unknown"
        return base
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        dbm.disconnect()


@app.post("/v1/import")
def import_table(
    request: ImportTableRequest,
    x_api_token: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """Import rows into a table. rows: list of dicts with keys = table column names."""
    _auth_guard(x_api_token)
    dbm = DatabaseManager()
    cfg = _build_config(request.db_config)
    if not dbm.connect(cfg):
        raise HTTPException(status_code=400, detail="Failed to connect to database")
    if not request.rows:
        raise HTTPException(status_code=400, detail="No rows to import")
    columns = list(request.rows[0].keys())
    if not columns:
        raise HTTPException(status_code=400, detail="Row has no columns")
    try:
        inserted = dbm.insert_rows(request.table_name, columns, request.rows)
        return {"inserted": inserted, "table": request.table_name}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        dbm.disconnect()


@app.post("/v1/import/smart")
def import_smart(
    request: ImportTableRequest,
    x_api_token: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """
    Smart import: auto-map CSV columns to table columns (case-insensitive)
    and handle primary key duplicates (remap numeric PKs, skip duplicate rows).
    rows: list of dicts with keys = CSV/upload column names (any case).
    """
    _auth_guard(x_api_token)
    dbm = DatabaseManager()
    cfg = _build_config(request.db_config)
    if not dbm.connect(cfg):
        raise HTTPException(status_code=400, detail="Failed to connect to database")
    if not request.rows:
        raise HTTPException(status_code=400, detail="No rows to import")
    try:
        result = smart_import(
            dbm,
            request.table_name,
            request.rows,
            db_type=cfg.db_type or "postgresql",
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        dbm.disconnect()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
