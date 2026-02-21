"""Page modules for different sections of the application"""
import streamlit as st
import pandas as pd
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from utils.query_execution import (
    execute_query, execute_generated_query, show_table_details, 
    show_common_queries, generate_sql_query, optimize_query, 
    debug_query, save_query_to_history, split_sql_statements, execute_single_statement
)
from utils.helpers import get_api_key
from ui.components import render_sql_editor
from shared import CODEMIRROR_AVAILABLE, MONACO_EDITOR_AVAILABLE, codemirror_editor, monaco_editor




def _quote_identifier(identifier: str, db_type: str) -> str:
    """Quote SQL identifier for the active database."""
    if db_type == "mysql":
        return f"`{identifier.replace('`', '``')}`"
    return f"\"{identifier.replace('\"', '\"\"')}\""


def _quote_table_reference(table_name: str, db_type: str) -> str:
    """Quote table reference, supporting optional schema prefix."""
    if "." in table_name:
        schema_name, bare_table = table_name.split(".", 1)
        return f"{_quote_identifier(schema_name, db_type)}.{_quote_identifier(bare_table, db_type)}"
    return _quote_identifier(table_name, db_type)


def _build_tables_with_min_records_sql(min_records: int = 10) -> str:
    """Build SQL to list tables with more than N records."""
    db_type = (st.session_state.get("db_type") or "").lower()
    db_manager = st.session_state.get("db_manager")
    tables: List[str] = []
    if db_manager:
        try:
            tables = db_manager.get_tables() or []
        except Exception:
            tables = []

    # Preferred path: exact row counts per discovered table.
    if tables:
        table_count_selects: List[str] = []
        for table_name in tables:
            table_label = str(table_name).replace("'", "''")
            table_ref = _quote_table_reference(str(table_name), db_type)
            table_count_selects.append(
                f"SELECT '{table_label}' AS table_name, COUNT(*) AS record_count FROM {table_ref}"
            )

        union_query = "\nUNION ALL\n".join(table_count_selects)
        return (
            "WITH table_counts AS (\n"
            f"{union_query}\n"
            ")\n"
            "SELECT table_name, record_count\n"
            "FROM table_counts\n"
            f"WHERE record_count > {int(min_records)}\n"
            "ORDER BY record_count DESC, table_name;"
        )

    # Fallback path: still return a deterministic "records" query (never column-count logic).
    # PostgreSQL/MySQL use catalog row-count stats (approximate but semantically correct).
    if db_type == "postgresql":
        return (
            "SELECT schemaname || '.' || relname AS table_name,\n"
            "       n_live_tup::bigint AS record_count\n"
            "FROM pg_stat_user_tables\n"
            f"WHERE n_live_tup > {int(min_records)}\n"
            "ORDER BY record_count DESC, table_name;"
        )

    if db_type == "mysql":
        return (
            "SELECT CONCAT(table_schema, '.', table_name) AS table_name,\n"
            "       table_rows AS record_count\n"
            "FROM information_schema.tables\n"
            "WHERE table_schema = DATABASE()\n"
            "  AND table_type = 'BASE TABLE'\n"
            f"  AND table_rows > {int(min_records)}\n"
            "ORDER BY record_count DESC, table_name;"
        )

    if db_type == "sqlite":
        return (
            "SELECT name AS table_name\n"
            "FROM sqlite_master\n"
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'\n"
            "ORDER BY name;"
        )

    return ""


def _build_default_question_sql(question: str) -> str:
    """Return deterministic SQL for built-in default questions."""
    q = (question or "").strip().lower()
    db_type = (st.session_state.get("db_type") or "").lower()

    if "list of all tables" in q:
        if db_type == "sqlite":
            return (
                "SELECT name AS table_name\n"
                "FROM sqlite_master\n"
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'\n"
                "ORDER BY name;"
            )
        if db_type == "mysql":
            return (
                "SELECT table_name\n"
                "FROM information_schema.tables\n"
                "WHERE table_schema = DATABASE()\n"
                "ORDER BY table_name;"
            )
        return (
            "SELECT table_name\n"
            "FROM information_schema.tables\n"
            "WHERE table_schema NOT IN ('pg_catalog', 'information_schema')\n"
            "ORDER BY table_name;"
        )

    if "tables with more than 10 records" in q:
        return _build_tables_with_min_records_sql(10)

    if "column names and data types for all tables" in q:
        if db_type == "sqlite":
            return (
                "SELECT m.name AS table_name, p.name AS column_name, p.type AS data_type\n"
                "FROM sqlite_master m\n"
                "JOIN pragma_table_info(m.name) p\n"
                "WHERE m.type = 'table' AND m.name NOT LIKE 'sqlite_%'\n"
                "ORDER BY m.name, p.cid;"
            )
        if db_type == "mysql":
            return (
                "SELECT table_name, column_name, data_type\n"
                "FROM information_schema.columns\n"
                "WHERE table_schema = DATABASE()\n"
                "ORDER BY table_name, ordinal_position;"
            )
        return (
            "SELECT table_schema, table_name, column_name, data_type\n"
            "FROM information_schema.columns\n"
            "WHERE table_schema NOT IN ('pg_catalog', 'information_schema')\n"
            "ORDER BY table_schema, table_name, ordinal_position;"
        )

    return ""


def _ensure_chatbot_schema_context(with_spinner: bool = False) -> bool:
    """Ensure schema_info exists and chatbot has current schema context."""
    if not st.session_state.get("connected") or st.session_state.get("db_manager") is None:
        return False

    schema_info = st.session_state.get("schema_info") or {}
    needs_schema_fetch = not schema_info.get("tables")

    def _fetch_schema() -> Dict[str, Any]:
        db_manager = st.session_state.get("db_manager")
        db_type = st.session_state.get("db_type", "unknown")
        tables = db_manager.get_tables() or []
        full_table_schemas: List[Dict[str, Any]] = []
        for table_name in tables:
            try:
                table_schema = db_manager.get_table_schema(table_name)
                if table_schema:
                    full_table_schemas.append(table_schema)
                else:
                    full_table_schemas.append({"table_name": table_name, "columns": []})
            except Exception:
                full_table_schemas.append({"table_name": table_name, "columns": []})
        return {
            "tables": full_table_schemas,
            "db_type": db_type,
            "total_tables": len(tables),
            "database_name": db_manager.config.database if db_manager and db_manager.config else "unknown",
        }

    if needs_schema_fetch:
        try:
            if with_spinner:
                with st.spinner("📊 Loading database schema..."):
                    schema_info = _fetch_schema()
            else:
                schema_info = _fetch_schema()
            st.session_state.schema_info = schema_info
        except Exception:
            return False

    chatbot = st.session_state.get("chatbot")
    if chatbot and schema_info.get("tables"):
        try:
            chatbot.set_schema_context(schema_info)
        except Exception:
            return False

    return bool(schema_info.get("tables"))


def _leading_sql_keyword(sql_text: str) -> str:
    """Return the first SQL keyword after skipping comments/whitespace."""
    if not sql_text:
        return ""

    cleaned = sql_text.strip()
    # Remove leading SQL line comments and block comments.
    cleaned = re.sub(r"^\s*(?:--[^\n]*\n\s*)+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*/\*.*?\*/\s*", "", cleaned, flags=re.DOTALL)

    match = re.search(r"\b([A-Z]+)\b", cleaned.upper())
    return match.group(1) if match else ""


def _looks_like_sql(sql_text: str) -> bool:
    """Heuristic guard to avoid treating plain English as SQL."""
    if not sql_text or not str(sql_text).strip():
        return False

    text = str(sql_text).strip()
    upper_text = text.upper()
    first_keyword = _leading_sql_keyword(text)

    if first_keyword in ("SELECT", "WITH"):
        # WITH should usually drive a SELECT in this app context.
        if first_keyword == "WITH" and re.search(r"\bSELECT\b", upper_text) is None:
            return False
        # Basic signal for query shape. Allow SELECT 1 style probes.
        return (
            re.search(r"\bFROM\b", upper_text) is not None
            or re.search(r"^\s*SELECT\s+\d+\s*;?\s*$", text, flags=re.IGNORECASE) is not None
        )

    if first_keyword == "INSERT":
        return re.search(r"\bINTO\b", upper_text) is not None
    if first_keyword == "UPDATE":
        return re.search(r"\bSET\b", upper_text) is not None
    if first_keyword == "DELETE":
        return re.search(r"\bFROM\b", upper_text) is not None
    if first_keyword in ("CREATE", "DROP", "ALTER", "TRUNCATE"):
        return True

    return False


def _is_safe_select_query(sql_query: str) -> bool:
    """Return True when the SQL can be safely auto-executed."""
    normalized_sql = _normalize_sql_for_execution(sql_query)
    if not normalized_sql:
        return False

    first_keyword = _leading_sql_keyword(normalized_sql)
    is_select = first_keyword in ('SELECT', 'WITH')
    is_not_ddl_dml = first_keyword not in [
        'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'INSERT', 'UPDATE', 'DELETE',
        'GRANT', 'REVOKE', 'COMMENT', 'ANALYZE', 'VACUUM'
    ]
    return is_select and is_not_ddl_dml


def _extract_sql_from_response_payload(response: Dict[str, Any]) -> str:
    """Extract SQL from chatbot response dict with fallbacks."""
    sql_query = response.get('sql_query', response.get('sql', '')) if isinstance(response, dict) else ''
    if sql_query and str(sql_query).strip():
        candidate = str(sql_query).strip()
        return candidate if _looks_like_sql(candidate) else ""

    response_text = response.get('response', '') if isinstance(response, dict) else ''
    if not response_text:
        return ''

    # Prefer fenced sql blocks when present.
    sql_block_match = re.search(r"```sql\s*(.*?)```", response_text, flags=re.IGNORECASE | re.DOTALL)
    if sql_block_match:
        candidate = sql_block_match.group(1).strip()
        return candidate if _looks_like_sql(candidate) else ""

    # Fallback to any fenced block.
    any_block_match = re.search(r"```\s*(.*?)```", response_text, flags=re.DOTALL)
    if any_block_match:
        candidate = any_block_match.group(1).strip()
        return candidate if _looks_like_sql(candidate) else ""

    candidate = response_text.strip()
    return candidate if _looks_like_sql(candidate) else ""


def _normalize_sql_for_execution(sql_query: str) -> str:
    """Normalize SQL text by removing wrappers/fences/explanation prefixes."""
    if not sql_query:
        return ''

    sql_text = str(sql_query).strip()

    # Extract from SQL markdown block if present.
    sql_block_match = re.search(r"```sql\s*(.*?)```", sql_text, flags=re.IGNORECASE | re.DOTALL)
    if sql_block_match:
        sql_text = sql_block_match.group(1).strip()
    else:
        # Extract from generic markdown block if present.
        any_block_match = re.search(r"```\s*(.*?)```", sql_text, flags=re.DOTALL)
        if any_block_match:
            sql_text = any_block_match.group(1).strip()

    # If explanatory text exists before SQL, trim to first SQL keyword.
    keyword_match = re.search(r"\b(SELECT|WITH|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TRUNCATE)\b", sql_text, flags=re.IGNORECASE)
    if keyword_match and keyword_match.start() > 0:
        sql_text = sql_text[keyword_match.start():].strip()

    return sql_text if _looks_like_sql(sql_text) else ''


def _dedupe_sql_query_text(sql_query: str) -> str:
    """Remove duplicate SQL statements while preserving order."""
    normalized = _normalize_sql_for_execution(sql_query)
    if not normalized:
        return normalized
    try:
        statements = split_sql_statements(normalized)
    except Exception:
        statements = [normalized]

    seen = set()
    unique_statements: List[str] = []
    for stmt in statements:
        cleaned = (stmt or "").strip().rstrip(";")
        if not cleaned:
            continue
        key = " ".join(cleaned.split()).lower()
        if key in seen:
            continue
        seen.add(key)
        unique_statements.append(cleaned)

    if not unique_statements:
        return ""
    return ";\n".join(unique_statements) + ";"


def _should_expand_sql(sql_query: str) -> bool:
    """Expand short SQL by default; collapse long SQL for readability."""
    if not sql_query:
        return True
    sql_text = str(sql_query).strip()
    line_count = sql_text.count("\n") + 1
    return len(sql_text) <= 220 and line_count <= 4


def _clean_assistant_content_for_sql(content: str, sql_query: str) -> str:
    """Avoid rendering duplicate SQL in assistant explanation area."""
    # If we already extracted SQL separately, keep explanation concise and non-SQL.
    if sql_query and str(sql_query).strip():
        return "SQL generated successfully."

    content_text = (content or "").strip()
    if not content_text:
        return "SQL generated successfully."

    # Remove markdown SQL code blocks from assistant content.
    content_text = re.sub(r"```sql\s*.*?```", "", content_text, flags=re.IGNORECASE | re.DOTALL).strip()
    content_text = re.sub(r"```\s*.*?```", "", content_text, flags=re.DOTALL).strip()

    normalized_content = " ".join(content_text.split()).strip().lower()
    normalized_sql = " ".join(_normalize_sql_for_execution(sql_query).split()).strip().lower() if sql_query else ""

    if normalized_sql and (
        normalized_content == normalized_sql or
        normalized_sql in normalized_content
    ):
        return "SQL generated successfully."

    return content_text or "SQL generated successfully."


def _auto_execute_chatbot_select_query(sql_query: str, timestamp: str, unique_suffix: str = "chatbot_auto") -> bool:
    """Auto-execute safe SELECT queries and set chatbot result state."""
    normalized_sql = _dedupe_sql_query_text(_normalize_sql_for_execution(sql_query))
    if not _is_safe_select_query(normalized_sql):
        return False

    try:
        with st.spinner("⚡ Auto-executing SELECT query..."):
            st.session_state['chatbot_last_auto_executed_query'] = normalized_sql
            st.session_state['chatbot_auto_executed_timestamp'] = timestamp
            st.session_state['chatbot_auto_execution_error'] = None
            st.session_state.pop('chatbot_multi_query_results', None)
            st.session_state.pop('last_result_df', None)
            st.session_state.pop('last_result', None)

            # Silent execution path for chatbot auto-run:
            # Execute without rendering UI here, then render inline per message order.
            statements = split_sql_statements(normalized_sql)
            multi_results: List[Dict[str, Any]] = []
            last_df = None

            for stmt_idx, stmt in enumerate(statements, 1):
                stmt_clean = (stmt or "").strip()
                if not stmt_clean:
                    continue
                result = execute_single_statement(stmt_clean)
                if not result.get('success'):
                    raise Exception(result.get('error', 'Unknown query execution error'))

                if result.get('type') == 'SELECT':
                    df = result.get('dataframe')
                    if df is not None:
                        last_df = df
                        multi_results.append({
                            'query': stmt_clean,
                            'dataframe': df,
                            'index': stmt_idx
                        })

            if last_df is not None:
                st.session_state['last_result_df'] = last_df
                st.session_state['last_result'] = last_df
            if multi_results:
                st.session_state['chatbot_multi_query_results'] = multi_results

            st.session_state.pop('chatbot_auto_execution_error', None)
            st.session_state.pop('chatbot_auto_execution_error_trace', None)
            st.session_state['chatbot_show_results_for_query'] = normalized_sql
            return True
    except Exception as exec_error:
        print(f"DEBUG: Auto-execution failed: {exec_error}")
        import traceback
        error_trace = traceback.format_exc()
        traceback.print_exc()
        st.session_state['chatbot_auto_execution_error'] = str(exec_error)
        st.session_state['chatbot_auto_execution_error_trace'] = error_trace
        st.error(f"❌ Auto-execution failed: {str(exec_error)}")
        st.code(normalized_sql or sql_query, language='sql')
        return False


def _capture_chatbot_auto_results_snapshot() -> Dict[str, Any]:
    """Capture current auto-execution results so they can render in message order."""
    snapshot: Dict[str, Any] = {}

    multi_results = st.session_state.get('chatbot_multi_query_results', [])
    if multi_results:
        copied_multi_results = []
        for item in multi_results:
            copied_multi_results.append({
                'query': item.get('query', ''),
                'dataframe': item.get('dataframe').copy() if item.get('dataframe') is not None else None,
                'index': item.get('index')
            })
        snapshot['auto_multi_query_results'] = copied_multi_results

    last_df = st.session_state.get('last_result_df')
    if last_df is not None:
        snapshot['auto_result_df'] = last_df.copy()

    return snapshot


def _append_assistant_message(message: Dict[str, Any]) -> None:
    """Append assistant message while preventing immediate duplicate SQL entries."""
    history = st.session_state.get('chat_history', [])
    if history:
        last_msg = history[-1]
        if last_msg.get('role') == 'assistant':
            last_sql = _normalize_sql_for_execution(last_msg.get('sql_query', ''))
            new_sql = _normalize_sql_for_execution(message.get('sql_query', ''))
            last_content = (last_msg.get('content', '') or '').strip()
            new_content = (message.get('content', '') or '').strip()
            if new_sql and last_sql == new_sql and last_content == new_content:
                return
    st.session_state.chat_history.append(message)


def _get_message_result_row_count(msg: Dict[str, Any]) -> int:
    """Return total rows captured in message snapshot results."""
    total_rows = 0
    multi_results = msg.get('auto_multi_query_results', [])
    if multi_results:
        for item in multi_results:
            df = item.get('dataframe')
            if df is not None:
                total_rows += len(df)
        return total_rows

    single_df = msg.get('auto_result_df')
    if single_df is not None:
        return len(single_df)
    return 0


def _render_sql_status_chips(msg: Dict[str, Any]) -> None:
    """Render compact SQL status chips near generated SQL."""
    auto_executed = bool(msg.get('auto_executed', False))
    rows = _get_message_result_row_count(msg)
    result_source = "Auto" if auto_executed else "Manual"

    auto_chip = (
        "<span style='display:inline-block;padding:2px 8px;border-radius:999px;"
        "background:#e7f8ee;color:#137333;font-size:12px;font-weight:600;'>Auto-executed</span>"
        if auto_executed else
        "<span style='display:inline-block;padding:2px 8px;border-radius:999px;"
        "background:#f3f4f6;color:#4b5563;font-size:12px;font-weight:600;'>Not auto-executed</span>"
    )
    rows_chip = (
        f"<span style='display:inline-block;padding:2px 8px;border-radius:999px;"
        f"background:#eef2ff;color:#3730a3;font-size:12px;font-weight:600;'>Rows: {rows:,}</span>"
        if rows > 0 else
        "<span style='display:inline-block;padding:2px 8px;border-radius:999px;"
        "background:#fff7ed;color:#9a3412;font-size:12px;font-weight:600;'>Rows: 0</span>"
    )
    source_chip = (
        "<span style='display:inline-block;padding:2px 8px;border-radius:999px;"
        "background:#f3f4f6;color:#374151;font-size:12px;font-weight:600;'>"
        f"Result source: {result_source}</span>"
    )
    st.markdown(f"{auto_chip}&nbsp;&nbsp;{rows_chip}&nbsp;&nbsp;{source_chip}", unsafe_allow_html=True)


def _render_snapshot_result_block(result_df, block_suffix: str, title: str = "**📋 Query Results**") -> None:
    """Render one result block with action icons above the table."""
    result_col1, result_col2, result_col3, result_col4, result_col5 = st.columns([6.8, 0.4, 0.4, 0.4, 0.4], gap="small")
    with result_col1:
        st.markdown(title, unsafe_allow_html=True)
    with result_col2:
        csv = result_df.to_csv(index=False)
        st.download_button(
            "📥",
            csv,
            "results.csv",
            "text/csv",
            help=f"Download CSV - {len(result_df):,} rows",
            width="stretch",
            key=f"download_snapshot_{block_suffix}"
        )
    with result_col3:
        from utils.helpers import _render_viz_icon_button
        _render_viz_icon_button(f"snapshot_{block_suffix}", result_df)
    with result_col4:
        from utils.helpers import _render_data_explorer_button
        _, explorer_active = _render_data_explorer_button(f"snapshot_{block_suffix}", result_df)
    with result_col5:
        from utils.helpers import _render_sql_editor_button
        _, sql_active = _render_sql_editor_button(f"snapshot_{block_suffix}")

    row_count = len(result_df)
    st.caption(f"Rows: {row_count:,}")
    if row_count == 0:
        st.info(
            "No rows returned. Quick checks: remove/relax filters, verify table has data, "
            "or run a broader query like `SELECT * FROM <table> LIMIT 20;`."
        )
    table_height = 520 if row_count > 15 else None
    if table_height:
        st.caption("Scrollable table enabled for long results (toolbar remains above).")
    try:
        if table_height:
            st.dataframe(result_df, use_container_width=True, height=table_height)
        else:
            st.dataframe(result_df, use_container_width=True)
    except Exception:
        st.write(result_df)

    if explorer_active:
        st.markdown("---")
        st.markdown("**🔍 Data Explorer**")
        try:
            from utils.helpers import display_data_explorer
            display_data_explorer(result_df)
        except Exception as e:
            st.error(f"Error displaying data explorer: {str(e)}")

    # Visualization rendering for the snapshot visualization icon toggle.
    viz_button_key = f"viz_btn_viz_icon_snapshot_{block_suffix}"
    if st.session_state.get(viz_button_key, False):
        st.markdown("---")
        try:
            from utils.helpers import visualize_dataframe
            visualize_dataframe(result_df, unique_suffix=f"snapshot_{block_suffix}")
        except Exception as e:
            st.error(f"Error displaying visualization: {str(e)}")

    if sql_active:
        st.markdown("---")
        st.markdown("**📝 SQL Editor**")
        sql_query_editor = render_sql_editor(
            key=f"sql_editor_snapshot_{block_suffix}",
            height=200,
            placeholder="Enter SQL query here...",
            lightweight=True,
            prefer_smart=True,
            minimal_schema=True,
            guided_sql_assist=True
        )
        if sql_query_editor and sql_query_editor.strip():
            if st.button("Execute SQL", key=f"execute_sql_snapshot_{block_suffix}"):
                execute_query(sql_query_editor, enable_agents=True, unique_suffix=f"sql_editor_snapshot_{block_suffix}")


def _render_inline_snapshot_results(msg: Dict[str, Any], unique_key_base: str) -> bool:
    """Render stored snapshot results for a specific assistant message."""
    stored_multi_results = msg.get('auto_multi_query_results', [])
    stored_single_result = msg.get('auto_result_df')
    has_snapshot = (stored_single_result is not None) or (len(stored_multi_results) > 0)
    if not has_snapshot:
        return False

    st.markdown("---")
    rendered_any = False

    if stored_multi_results and len(stored_multi_results) > 1:
        st.markdown("### 📋 Query Results (Multiple Queries)")
        for result_item in stored_multi_results:
            query_text = result_item.get('query', '')
            result_df = result_item.get('dataframe')
            result_idx = result_item.get('index')
            if result_df is None:
                continue
            if query_text:
                st.markdown(f"**Query {result_idx}:**")
                st.code(query_text, language='sql')
            _render_snapshot_result_block(
                result_df,
                block_suffix=f"{unique_key_base}_{result_idx}",
                title=f"**📋 Results {result_idx}**"
            )
            rendered_any = True
            st.markdown("---")
    else:
        result_df = stored_single_result
        if result_df is None and stored_multi_results:
            result_df = stored_multi_results[0].get('dataframe')
        if result_df is not None:
            _render_snapshot_result_block(
                result_df,
                block_suffix=f"{unique_key_base}",
                title="**📋 Query Results**"
            )
            rendered_any = True

    # Fallback safety: if snapshot flags exist but data object is missing, show last_result_df.
    if not rendered_any and st.session_state.get("last_result_df") is not None:
        fallback_df = st.session_state.get("last_result_df")
        _render_snapshot_result_block(
            fallback_df,
            block_suffix=f"{unique_key_base}_fallback",
            title="**📋 Query Results**"
        )
        rendered_any = True

    return rendered_any


def _is_upload_data_request(user_text: str) -> bool:
    """Detect chat requests asking to upload/import local files into DB tables."""
    text = (user_text or "").strip().lower()
    if not text:
        return False

    upload_terms = ["upload", "import", "load"]
    file_terms = ["file", "csv", "excel", "xlsx", "xls"]
    table_terms = ["table", "database", "db"]
    return (
        any(term in text for term in upload_terms) and
        any(term in text for term in file_terms) and
        any(term in text for term in table_terms)
    )


def _is_copy_from_local_file_sql(sql_query: str) -> bool:
    """Detect server-side COPY FROM '/path/file' SQL that fails on managed PG."""
    sql = (sql_query or "").strip()
    if not sql:
        return False
    if re.match(r"^\s*\\copy\s+", sql, flags=re.IGNORECASE):
        return True
    if not re.match(r"^\s*COPY\s+", sql, flags=re.IGNORECASE):
        return False
    return bool(re.search(r"\bFROM\s+'[^']+'", sql, flags=re.IGNORECASE))


def _extract_copy_target_table(sql_query: str) -> Optional[str]:
    """Extract target table from COPY statement."""
    sql = (sql_query or "").strip()
    match = re.match(r"^\s*(?:COPY|\\copy)\s+([A-Za-z_][\w\.]*)", sql, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def _infer_target_table_from_text(user_text: str) -> Optional[str]:
    """Try to infer target table from user message."""
    text = (user_text or "").strip().lower()
    db_manager = st.session_state.get("db_manager")
    if not text or db_manager is None:
        return None

    try:
        tables = db_manager.get_tables() or []
    except Exception:
        return None

    best_match = None
    best_len = 0
    for table_name in tables:
        table_text = str(table_name).strip().lower()
        if not table_text:
            continue
        pattern = rf"\b{re.escape(table_text)}\b"
        if re.search(pattern, text) and len(table_text) > best_len:
            best_match = str(table_name)
            best_len = len(table_text)
    return best_match


def _read_uploaded_dataframe(uploaded_file) -> pd.DataFrame:
    """Read user-uploaded CSV/TSV/Excel file into a DataFrame."""
    file_name = (uploaded_file.name or "").lower()

    if file_name.endswith((".csv", ".tsv", ".txt")):
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, sep=None, engine="python")
    if file_name.endswith((".xlsx", ".xls")):
        uploaded_file.seek(0)
        return pd.read_excel(uploaded_file)
    raise ValueError("Unsupported file type. Please upload CSV or Excel (.xlsx/.xls).")


def _append_uploaded_dataframe_to_table(df: pd.DataFrame, table_name: str) -> Dict[str, Any]:
    """Append uploaded dataframe rows to an existing database table."""
    db_manager = st.session_state.get("db_manager")
    if db_manager is None:
        raise ValueError("No active database manager found.")

    engine = db_manager.get_engine()
    if engine is None:
        raise ValueError("No active database connection.")

    schema = db_manager.get_table_schema(table_name)
    table_columns = [col.get("name") for col in (schema.get("columns") or []) if col.get("name")]
    if not table_columns:
        raise ValueError(f"Could not fetch columns for table '{table_name}'.")

    # Match uploaded columns case-insensitively to table columns.
    table_lookup = {str(col).strip().lower(): str(col) for col in table_columns}
    rename_map: Dict[str, str] = {}
    unmatched_columns: List[str] = []
    for raw_col in df.columns:
        normalized = str(raw_col).strip().lower()
        if normalized in table_lookup:
            rename_map[raw_col] = table_lookup[normalized]
        else:
            unmatched_columns.append(str(raw_col))

    if unmatched_columns:
        raise ValueError(
            "File has columns that do not exist in target table: "
            + ", ".join(unmatched_columns)
        )

    prepared_df = df.rename(columns=rename_map).copy()
    ordered_columns = [col for col in table_columns if col in prepared_df.columns]
    if not ordered_columns:
        raise ValueError(
            "No matching columns found between uploaded file and target table."
        )

    load_df = prepared_df[ordered_columns]
    if load_df.empty:
        raise ValueError("Uploaded file has no rows to insert.")

    remapped_pk_count = 0
    remapped_pk_column = ""
    skipped_existing_pk_count = 0
    skipped_file_duplicate_pk_count = 0
    primary_keys = [pk for pk in (schema.get("primary_keys") or []) if pk]
    if len(primary_keys) == 1:
        pk_col = str(primary_keys[0])
        if pk_col in load_df.columns:
            numeric_pk = pd.to_numeric(load_df[pk_col], errors="coerce")
            has_non_numeric_values = bool(
                numeric_pk.isna().any() and load_df[pk_col].notna().any()
            )
            if not has_non_numeric_values:
                db_type = (st.session_state.get("db_type") or "").lower()
                pk_ident = _quote_identifier(pk_col, db_type)
                table_ref = _quote_table_reference(table_name, db_type)

                max_df = db_manager.execute_query(
                    f"SELECT COALESCE(MAX({pk_ident}), 0) AS max_id FROM {table_ref}"
                )
                max_existing_id = int(max_df.iloc[0, 0]) if max_df is not None and len(max_df) else 0

                upload_ids = [int(v) for v in numeric_pk.fillna(0).tolist()]
                unique_ids = sorted(set(upload_ids))
                existing_ids: set = set()
                if unique_ids:
                    in_clause = ", ".join(str(v) for v in unique_ids)
                    overlap_df = db_manager.execute_query(
                        f"SELECT {pk_ident} AS id FROM {table_ref} WHERE {pk_ident} IN ({in_clause})"
                    )
                    if overlap_df is not None and len(overlap_df) > 0:
                        existing_ids = {int(v) for v in overlap_df["id"].tolist() if pd.notna(v)}

                seen_ids = set()
                next_id = max_existing_id + 1
                remapped_ids: List[int] = []
                for original_id in upload_ids:
                    if original_id in existing_ids or original_id in seen_ids:
                        while next_id in existing_ids or next_id in seen_ids:
                            next_id += 1
                        remapped_ids.append(next_id)
                        seen_ids.add(next_id)
                        remapped_pk_count += 1
                        next_id += 1
                    else:
                        remapped_ids.append(original_id)
                        seen_ids.add(original_id)

                if remapped_pk_count > 0:
                    load_df[pk_col] = remapped_ids
                    remapped_pk_column = pk_col
            else:
                # For non-numeric single primary keys, skip rows that would conflict.
                db_type = (st.session_state.get("db_type") or "").lower()
                pk_ident = _quote_identifier(pk_col, db_type)
                table_ref = _quote_table_reference(table_name, db_type)

                def _sql_literal(value: Any) -> str:
                    if pd.isna(value):
                        return "NULL"
                    text_value = str(value).replace("'", "''")
                    return f"'{text_value}'"

                pk_values = [v for v in load_df[pk_col].tolist() if not pd.isna(v)]
                unique_pk_values = list(dict.fromkeys(pk_values))
                existing_pk_values: set = set()

                chunk_size = 500
                for start in range(0, len(unique_pk_values), chunk_size):
                    chunk = unique_pk_values[start:start + chunk_size]
                    if not chunk:
                        continue
                    in_clause = ", ".join(_sql_literal(v) for v in chunk)
                    overlap_df = db_manager.execute_query(
                        f"SELECT {pk_ident} AS id FROM {table_ref} WHERE {pk_ident} IN ({in_clause})"
                    )
                    if overlap_df is not None and len(overlap_df) > 0:
                        for val in overlap_df["id"].tolist():
                            if pd.isna(val):
                                continue
                            existing_pk_values.add(str(val))

                pk_as_str = load_df[pk_col].astype(str)
                existing_mask = pk_as_str.isin(existing_pk_values)
                duplicate_mask = pk_as_str.duplicated(keep="first")
                keep_mask = ~(existing_mask | duplicate_mask)

                skipped_existing_pk_count = int(existing_mask.sum())
                skipped_file_duplicate_pk_count = int((~existing_mask & duplicate_mask).sum())
                load_df = load_df.loc[keep_mask].copy()

    if load_df.empty:
        if skipped_existing_pk_count > 0 or skipped_file_duplicate_pk_count > 0:
            raise ValueError(
                "No rows inserted: all uploaded rows had duplicate primary key values "
                "that already exist (or were duplicated in the uploaded file)."
            )
        raise ValueError("Uploaded file has no rows to insert.")

    load_df.to_sql(
        table_name,
        con=engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
    )
    return {
        "inserted_rows": len(load_df),
        "loaded_columns": ordered_columns,
        "remapped_pk_count": remapped_pk_count,
        "remapped_pk_column": remapped_pk_column,
        "skipped_existing_pk_count": skipped_existing_pk_count,
        "skipped_file_duplicate_pk_count": skipped_file_duplicate_pk_count
    }


def _render_chatbot_upload_panel(msg: Dict[str, Any], idx: int, unique_key_base: str) -> None:
    """Render upload UI for chatbot messages requesting file-to-table load."""
    st.markdown("---")
    st.markdown("### 📤 Upload local file to database table")

    if not st.session_state.get("connected") or st.session_state.get("db_manager") is None:
        st.warning("Connect to a database first, then upload a file.")
        return

    try:
        tables = st.session_state.db_manager.get_tables() or []
    except Exception as table_error:
        st.error(f"Unable to fetch tables: {table_error}")
        return

    if not tables:
        st.info("No tables found in the connected database.")
        return

    suggested_table = (msg.get("upload_target_table") or "").strip()
    if suggested_table and suggested_table not in tables and "." in suggested_table:
        suggested_table = suggested_table.split(".")[-1]
    default_index = 0
    if suggested_table and suggested_table in tables:
        default_index = tables.index(suggested_table)

    selected_table = st.selectbox(
        "Target table",
        options=tables,
        index=default_index,
        key=f"upload_table_{unique_key_base}"
    )
    try:
        table_schema = st.session_state.db_manager.get_table_schema(selected_table)
        template_columns = [
            col.get("name")
            for col in (table_schema.get("columns") or [])
            if col.get("name")
        ]
    except Exception:
        template_columns = []

    if template_columns:
        template_df = pd.DataFrame(columns=template_columns)
        st.download_button(
            "Download template CSV",
            template_df.to_csv(index=False),
            file_name=f"{selected_table}_template.csv",
            mime="text/csv",
            key=f"download_upload_template_{unique_key_base}",
            help=f"Download column template for `{selected_table}`"
        )
        st.caption(f"Expected columns for `{selected_table}`: {', '.join(template_columns)}")

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "tsv", "txt", "xlsx", "xls"],
        key=f"upload_file_{unique_key_base}"
    )
    st.caption("Rows are appended to the selected table. Column names are matched case-insensitively.")

    if not uploaded_file:
        return

    try:
        preview_df = _read_uploaded_dataframe(uploaded_file)
    except Exception as read_error:
        st.error(f"Could not read file: {read_error}")
        return

    st.caption(f"File preview: {len(preview_df):,} rows, {len(preview_df.columns):,} columns")
    st.dataframe(preview_df.head(20), use_container_width=True, height=240)

    if st.button("Load file to table", key=f"upload_submit_{unique_key_base}"):
        try:
            with st.spinner("Uploading data to database table..."):
                load_result = _append_uploaded_dataframe_to_table(preview_df, selected_table)
            inserted_rows = int(load_result.get("inserted_rows", 0))
            loaded_columns = load_result.get("loaded_columns", [])
            remapped_pk_count = int(load_result.get("remapped_pk_count", 0))
            remapped_pk_column = str(load_result.get("remapped_pk_column", "") or "")
            skipped_existing_pk_count = int(load_result.get("skipped_existing_pk_count", 0))
            skipped_file_duplicate_pk_count = int(load_result.get("skipped_file_duplicate_pk_count", 0))
            st.success(
                f"Loaded {inserted_rows:,} rows into `{selected_table}` "
                f"using {len(loaded_columns)} matched columns."
            )
            if remapped_pk_count > 0 and remapped_pk_column:
                st.info(
                    f"Auto-adjusted {remapped_pk_count:,} duplicate `{remapped_pk_column}` value(s) "
                    "to the next available IDs."
                )
            if skipped_existing_pk_count > 0 or skipped_file_duplicate_pk_count > 0:
                st.warning(
                    f"Skipped {skipped_existing_pk_count:,} row(s) with PK values already in the table "
                    f"and {skipped_file_duplicate_pk_count:,} duplicate PK row(s) inside the uploaded file."
                )
            st.session_state.chat_history[idx]["upload_completed"] = True
            st.session_state.chat_history[idx]["show_upload_panel"] = False
        except Exception as load_error:
            st.error(f"Upload failed: {load_error}")


def chatbot_compact():
    """Compact chatbot for three column layout"""
    st.markdown("### 💬 AI Assistant")
    
    # Example questions (only show if no chat history)
    if not st.session_state.chat_history and st.session_state.chatbot:
        st.markdown("**💡 Quick Start:**")
        example_questions = [
            ("Show me all tables", "Show me the list of all tables in the database"),
            ("Tables >10 records", "List tables that have more than 10 records"),
            ("Table columns", "What are the column names and data types for all tables?")
        ]
        
        # Use smaller buttons in a row
        cols = st.columns(3)
        for idx, (display_text, full_question) in enumerate(example_questions):
            with cols[idx]:
                if st.button(f"💬 {display_text}", key=f"compact_example_{idx}", use_container_width=True):
                    # Process the question
                    st.session_state.chat_history.append({'role': 'user', 'content': full_question})
                    default_sql = _build_default_question_sql(full_question)
                    if default_sql:
                        response = {
                            "response": "Generated from built-in default question template.",
                            "sql_query": default_sql,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        with st.spinner("🤔 Thinking..."):
                            response = st.session_state.chatbot.chat(full_question, include_sql=True)
                    
                    if 'error' not in response:
                        sql_query = _dedupe_sql_query_text(_normalize_sql_for_execution(_extract_sql_from_response_payload(response)))
                        auto_executed = _auto_execute_chatbot_select_query(
                            sql_query,
                            response.get('timestamp', datetime.now().isoformat()),
                            unique_suffix="chatbot_auto_example_compact"
                        )
                        auto_results_snapshot = _capture_chatbot_auto_results_snapshot() if auto_executed else {}
                        
                        _append_assistant_message({
                            'role': 'assistant',
                            'content': _clean_assistant_content_for_sql(response.get('response', ''), sql_query),
                            'sql_query': sql_query,
                            'timestamp': response['timestamp'],
                            'auto_executed': auto_executed,
                            **auto_results_snapshot
                        })
                    else:
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response.get('response', response.get('error', 'Error occurred')),
                            'timestamp': response.get('timestamp', datetime.now().isoformat())
                        })
                    st.rerun()
        st.markdown("---")
    
    # Add marker before chat messages for compact layout
    st.markdown('<div id="chat-container-start-compact"></div>', unsafe_allow_html=True)
    
    # Display chat history
    if st.session_state.chat_history:
        recent_messages = st.session_state.chat_history[-10:]  # Show last 10 messages (increased from 5)
        for idx, msg in enumerate(recent_messages):
            # Use a unique key based on the original index in the full chat history
            original_idx = len(st.session_state.chat_history) - 10 + idx
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                display_content = _clean_assistant_content_for_sql(msg.get('content', ''), msg.get('sql_query', ''))
                # Show explanation in collapsed expander by default
                with st.expander("💡 View Explanation", expanded=False):
                    st.chat_message("assistant").write(display_content)
                
                # Show SQL query in expanded form by default
                if 'sql_query' in msg and msg['sql_query']:
                    with st.expander("📝 Generated SQL", expanded=_should_expand_sql(msg['sql_query'])):
                        st.code(msg['sql_query'], language='sql')
                if msg.get("show_upload_panel", False):
                    _render_chatbot_upload_panel(msg, original_idx, f"compact_{original_idx}")
    else:
        if not st.session_state.chatbot:
            st.info("💡 AI chatbot requires an API key. Set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable.")
        else:
            st.info("Ask questions about your database")
    
    # Add marker after chat messages and JavaScript to wrap them for compact layout
    st.markdown("""
    <div id="chat-container-end-compact"></div>
    <script>
        (function() {
            function wrapCompactChatMessages() {
                const startMarker = document.getElementById('chat-container-start-compact');
                const endMarker = document.getElementById('chat-container-end-compact');
                if (!startMarker || !endMarker) return;
                
                // Check if wrapper already exists
                if (document.getElementById('chat-messages-scrollable-wrapper-compact')) return;
                
                // Find parent container
                let parent = startMarker.parentElement;
                if (!parent) return;
                
                // Create wrapper div
                const wrapper = document.createElement('div');
                wrapper.id = 'chat-messages-scrollable-wrapper-compact';
                wrapper.style.cssText = `
                    max-height: 50vh;
                    overflow-y: auto;
                    overflow-x: hidden;
                    padding: 0.5rem;
                    margin-bottom: 0.5rem;
                    border: 1px solid rgba(250, 250, 250, 0.2);
                    border-radius: 0.5rem;
                    background-color: rgba(0, 0, 0, 0.02);
                    scroll-behavior: smooth;
                `;
                
                // Collect all nodes between markers
                let node = startMarker.nextSibling;
                const nodesToMove = [];
                while (node && node !== endMarker) {
                    nodesToMove.push(node);
                    node = node.nextSibling;
                }
                
                // Move nodes into wrapper
                nodesToMove.forEach(n => wrapper.appendChild(n));
                
                // Insert wrapper after start marker
                startMarker.parentNode.insertBefore(wrapper, startMarker.nextSibling);
                
                // Auto-scroll to bottom
                wrapper.scrollTop = wrapper.scrollHeight;
            }
            
            // Run immediately and after delays
            wrapCompactChatMessages();
            setTimeout(wrapCompactChatMessages, 100);
            setTimeout(wrapCompactChatMessages, 500);
            
            // Also observe for changes
            const observer = new MutationObserver(function() {
                wrapCompactChatMessages();
                const wrapper = document.getElementById('chat-messages-scrollable-wrapper-compact');
                if (wrapper) {
                    wrapper.scrollTop = wrapper.scrollHeight;
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        })();
    </script>
    """, unsafe_allow_html=True)
    
    # Ensure schema context is ready in compact mode as well.
    if st.session_state.get("connected") and st.session_state.get("chatbot"):
        _ensure_chatbot_schema_context(with_spinner=False)

    # Chat input
    user_input = st.chat_input("Ask about your database...")
    
    if user_input:
        # Check if chatbot is available when user actually tries to use it
        print(f"DEBUG: User input received (chatbot_compact): {user_input}")
        print(f"DEBUG: Chatbot available (chatbot_compact): {st.session_state.chatbot is not None}")
        if not st.session_state.chatbot:
            print(f"DEBUG: Chatbot is None (chatbot_compact), showing error message")
            st.error("❌ AI Chatbot is not available. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable to enable AI features.")
        else:
            if not _ensure_chatbot_schema_context(with_spinner=True):
                st.error("❌ Database schema information is not available yet. Please reconnect or try again.")
                return
            # Add user message to history
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})

            # Handle explicit upload-to-table requests with a guided uploader UI.
            if _is_upload_data_request(user_input):
                target_table = _infer_target_table_from_text(user_input)
                _append_assistant_message({
                    'role': 'assistant',
                    'content': (
                        "Upload mode enabled. Choose a local CSV/Excel file and target table below, "
                        "then click **Load file to table**."
                    ),
                    'timestamp': datetime.now().isoformat(),
                    'show_upload_panel': True,
                    'upload_target_table': target_table or ''
                })
                st.rerun()
            
            # Get AI response
            try:
                print(f"DEBUG: Calling chatbot.chat() (chatbot_compact) with query: {user_input}")
                with st.spinner("🤔 Thinking..."):
                    response = st.session_state.chatbot.chat(user_input, include_sql=True)
                print(f"DEBUG: Chatbot response received (chatbot_compact): {type(response)}, has error: {'error' in response if isinstance(response, dict) else 'N/A'}")
                print(f"DEBUG: Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                if 'error' not in response:
                    # Add assistant response to history
                    try:
                        response_content = response.get('response', response.get('content', str(response)))
                        sql_query = _dedupe_sql_query_text(response.get('sql_query', response.get('sql', None)))
                        cleaned_response_content = _clean_assistant_content_for_sql(response_content, sql_query)
                        timestamp = response.get('timestamp', datetime.now().isoformat())
                        print(f"DEBUG: Adding response to chat history - content length: {len(response_content) if response_content else 0}, has sql: {bool(sql_query)}")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': cleaned_response_content,
                            'sql_query': sql_query,
                            'timestamp': timestamp
                        })
                        st.rerun()
                    except Exception as process_error:
                        print(f"DEBUG: Error processing response: {process_error}")
                        import traceback
                        traceback.print_exc()
                        st.error(f"❌ Error processing chatbot response: {str(process_error)}")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': f"Error processing response: {str(process_error)}",
                            'timestamp': datetime.now().isoformat()
                        })
                        st.rerun()
                else:
                    error_msg = response.get('error', 'Unknown error occurred')
                    print(f"DEBUG: Response contains error: {error_msg}")
                    st.error(f"Error: {error_msg}")
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': f"Error: {error_msg}",
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                error_msg = f"❌ Error processing query: {str(e)}"
                st.error(error_msg)
                print(f"DEBUG: Chatbot error: {e}")
                import traceback
                traceback.print_exc()
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
                st.rerun()




def chatbot_tab():
    """AI Chatbot interface"""
    print(f"DEBUG: chatbot_tab() called - chat_history length: {len(st.session_state.chat_history) if st.session_state.chat_history else 0}")
    
    # Check for agent SQL FIRST, before any other rendering
    # This ensures we catch it immediately after button click
    agent_sql = st.session_state.get("agent_sql_to_run")
    agent_execution_result = st.session_state.get("agent_sql_execution_result")
    print(f"DEBUG: chatbot_tab START - agent_sql exists: {agent_sql is not None}, value: {agent_sql[:100] if agent_sql else 'None'}...")
    
    # Also check for any agent SQL button clicks that might have happened
    # This is a fallback in case the button click handler didn't run
    if not agent_sql:
        agent_button_keys = [k for k in st.session_state.keys() if k.endswith("_run") and "agent_sql" in k]
        for button_key in agent_button_keys:
            # Check if this button was clicked (Streamlit buttons return True on click)
            # But we can't check button state directly, so we check if editor_key exists
            editor_key = button_key.replace("_run", "_editor")
            if editor_key in st.session_state:
                # Button might have been clicked but handler didn't run
                # Try to get SQL from editor
                potential_sql = st.session_state.get(editor_key)
                if potential_sql and potential_sql.strip():
                    print(f"DEBUG: Found potential agent SQL from editor: {editor_key}")
                    st.session_state["agent_sql_to_run"] = potential_sql
                    agent_sql = potential_sql
                    break
    
    st.markdown(
        "<div style='font-size: 1.5rem; font-weight: 700; line-height: 1.3; margin: 0;'>"
        "💬 AI SQL Assistant"
        "</div>",
        unsafe_allow_html=True
    )
    st.markdown("Ask questions in natural language and get SQL queries generated automatically")

    # Debug section for agent SQL execution (DISABLED for performance)
    # with st.expander("🔍 Agent SQL Execution Debug", expanded=False):
    #     agent_sql_debug = st.session_state.get("agent_sql_to_run")
    #     agent_result_debug = st.session_state.get("agent_sql_execution_result")
    #     st.write(f"**agent_sql_to_run exists:** {agent_sql_debug is not None}")
    #     if agent_sql_debug:
    #         st.write(f"**agent_sql value:** {agent_sql_debug[:200]}...")
    #     st.write(f"**agent_sql_execution_result exists:** {agent_result_debug is not None}")
    #     if agent_result_debug:
    #         st.write(f"**Result status:** {agent_result_debug.get('status', 'unknown')}")
    #     st.write(f"**agent_sql_source:** {st.session_state.get('agent_sql_source', 'None')}")
    #     # Show all agent-related keys
    #     agent_keys = [k for k in st.session_state.keys() if 'agent' in k.lower()]
    #     st.write(f"**All agent-related keys:** {agent_keys}")
    
    # Visualization Debug Info (DISABLED for performance)
    # with st.expander("🔍 Visualization Debug Info", expanded=True):
    #     # Find all visualization-related keys
    #     viz_keys = [k for k in st.session_state.keys() if 'viz' in k.lower() or 'visualization' in k.lower()]
    #     st.write(f"**All Viz-related Keys:** `{viz_keys}`")
    #     
    #     # Group keys by instance (extract unique suffix)
    #     instances = {}
    #     for key in viz_keys:
    #         if 'viz_debug' in key:
    #             suffix = key.replace('viz_debug_', '')
    #             if suffix not in instances:
    #                 instances[suffix] = {}
    #             instances[suffix]['debug_key'] = key
    #         elif 'viz_btn' in key:
    #             # Extract suffix from button key (format: viz_btn_viz_icon_<suffix>)
    #             if 'viz_icon_' in key:
    #                 suffix = key.split('viz_icon_', 1)[1]
    #                 if suffix not in instances:
    #                     instances[suffix] = {}
    #                 instances[suffix]['button_key'] = key
    #         elif 'viz_active' in key:
    #             # Extract suffix from state key (format: viz_active_viz_icon_<suffix>)
    #             if 'viz_icon_' in key:
    #                 suffix = key.split('viz_icon_', 1)[1]
    #                 if suffix not in instances:
    #                     instances[suffix] = {}
    #                 instances[suffix]['state_key'] = key
    #     
    #     # Display debug info grouped by instance
    #     for suffix, keys in instances.items():
    #         st.write(f"---")
    #         st.write(f"### Instance: `{suffix}`")
    #         
    #         # Show debug info
    #         if 'debug_key' in keys:
    #             debug_info = st.session_state.get(keys['debug_key'], {})
    #             if isinstance(debug_info, dict):
    #                 st.write(f"**Button Clicked:** `{debug_info.get('button_clicked', False)}`")
    #                 st.write(f"**State Before Click:** `{debug_info.get('state_before', False)}`")
    #                 st.write(f"**State After Click:** `{debug_info.get('state_after', False)}`")
    #                 st.write(f"**Click Count:** `{debug_info.get('click_count', 0)}`")
    #                 st.write(f"**Last Checkbox State:** `{debug_info.get('last_checkbox_state', False)}`")
    #         
    #         # Show checkbox state
    #         if 'button_key' in keys:
    #             checkbox_state = st.session_state.get(keys['button_key'], False)
    #             st.write(f"**Checkbox Key:** `{keys['button_key']}`")
    #             st.write(f"**Checkbox State:** `{checkbox_state}`")
    #         
    #         # Show state key
    #         if 'state_key' in keys:
    #             state_value = st.session_state.get(keys['state_key'], False)
    #             st.write(f"**State Key:** `{keys['state_key']}`")
    #             st.write(f"**State Value:** `{state_value}`")
    #             # Show if states match
    #             if 'button_key' in keys:
    #                 checkbox_state = st.session_state.get(keys['button_key'], False)
    #                 st.write(f"**States Match:** `{checkbox_state == state_value}`")
    #     
    #     if not instances:
    #         st.write("**No visualization instances found**")

    # If an agent (e.g., Debug Agent) requested to run suggested SQL, execute it here
    # Check this FIRST before rendering anything else, so results appear at the top
    # Check if we need to execute agent SQL (persist across reruns)
    
    # Debug logging disabled for performance
    # print(f"DEBUG: chatbot_tab - agent_sql exists: {agent_sql is not None}, agent_execution_result exists: {agent_execution_result is not None}")
    if agent_sql:
        print(f"DEBUG: agent_sql value: {agent_sql[:100] if agent_sql else 'None'}...")
    
    if agent_sql:
        # Store execution info before clearing
        agent_source = st.session_state.get("agent_sql_source", "AI Agent")
        agent_timestamp = st.session_state.get("agent_sql_timestamp", None)
        
        print(f"DEBUG: About to execute agent SQL - source: {agent_source}, execution_result: {agent_execution_result}")
        
        # Execute SQL and store result in session state
        if agent_execution_result is None:
            # First time execution - run the SQL
            print(f"DEBUG: First time execution - displaying info and executing SQL")
            
            # Show visible execution status
            execution_status = st.empty()
            execution_status.info(f"▶ **Executing SQL suggested by {agent_source}...**")
            st.code(agent_sql, language='sql')
            
            try:
                print(f"DEBUG: About to call execute_query with SQL: {agent_sql[:100]}...")
                execution_status.info(f"▶ **Executing SQL...** (This may take a moment)")
                
                # Run without agents to avoid recursive analysis
                # execute_query will display results/success messages automatically
                execute_query(agent_sql, enable_agents=False, unique_suffix="agent_suggested")
                print(f"DEBUG: execute_query returned successfully")
                
                execution_status.success("✅ **SQL execution completed!**")
                
                # Store execution result
                st.session_state["agent_sql_execution_result"] = {
                    "status": "success",
                    "sql": agent_sql,
                    "source": agent_source,
                    "timestamp": agent_timestamp
                }
                
                # For UPDATE/DELETE/INSERT, add extra confirmation message
                sql_upper = agent_sql.strip().upper()
                if any(sql_upper.startswith(cmd) for cmd in ['UPDATE', 'DELETE', 'INSERT']):
                    st.info("💡 **Tip:** Run a SELECT query to verify the changes were applied correctly.")
                
                # After DDL operations (especially CREATE SCHEMA), refresh schema info
                if any(sql_upper.startswith(cmd) for cmd in ['CREATE SCHEMA', 'CREATE TABLE', 'DROP SCHEMA', 'DROP TABLE', 'ALTER']):
                    try:
                        # Refresh schema info to reflect new schema/table
                        if st.session_state.connected and st.session_state.db_manager:
                            tables = st.session_state.db_manager.get_tables()
                            schema_info = st.session_state.db_manager.get_database_info()
                            if schema_info:
                                schema_info['tables'] = tables or []
                                schema_info['total_tables'] = len(tables) if tables else 0
                                st.session_state.schema_info = schema_info
                            else:
                                st.session_state.schema_info = {
                                    'tables': tables or [],
                                    'db_type': st.session_state.get('db_type', 'unknown'),
                                    'total_tables': len(tables) if tables else 0,
                                    'database_name': st.session_state.db_manager.config.database if st.session_state.db_manager.config else 'unknown'
                                }
                            st.success("🔄 Schema information refreshed!")
                            
                            # Also refresh chatbot schema context if available
                            if st.session_state.chatbot:
                                try:
                                    st.session_state.chatbot.set_schema_context(st.session_state.schema_info)
                                except Exception as e:
                                    st.debug(f"Could not update chatbot schema context: {e}")
                    except Exception as e:
                        st.warning(f"⚠️ Schema created but could not refresh schema info: {e}")
                
                # Clear the flag after successful execution (but keep result for display)
                print(f"DEBUG: Clearing agent_sql_to_run flag, keeping execution result")
                st.session_state.pop("agent_sql_to_run", None)
                st.session_state.pop("agent_sql_source", None)
                st.session_state.pop("agent_sql_timestamp", None)
                
                # Don't rerun here - let the messages display
                
            except Exception as e:
                error_msg = f"❌ Failed to execute suggested SQL: {str(e)}"
                execution_status.error(f"❌ **Execution failed!** {error_msg}")
                st.error(error_msg)
                print(f"DEBUG: Agent SQL execution error: {e}")
                import traceback
                error_trace = traceback.format_exc()
                print(error_trace)
                st.exception(e)
                
                # Store error result
                print(f"DEBUG: Storing error result in session state")
                st.session_state["agent_sql_execution_result"] = {
                    "status": "error",
                    "sql": agent_sql,
                    "source": agent_source,
                    "error": str(e),
                    "error_trace": error_trace,
                    "timestamp": agent_timestamp
                }
                
                # Clear the flag after error (but keep result for display)
                st.session_state.pop("agent_sql_to_run", None)
                st.session_state.pop("agent_sql_source", None)
                st.session_state.pop("agent_sql_timestamp", None)
        else:
            # Result already stored - display it
            result = agent_execution_result
            st.info(f"▶ SQL suggested by {result.get('source', 'AI Agent')} - Execution Result")
            st.code(result.get('sql', ''), language='sql')
            
            if result.get('status') == 'success':
                st.success("✅ SQL executed successfully!")
                sql_upper = result.get('sql', '').strip().upper()
                if any(sql_upper.startswith(cmd) for cmd in ['UPDATE', 'DELETE', 'INSERT']):
                    st.info("💡 **Tip:** Run a SELECT query to verify the changes were applied correctly.")
            else:
                st.error(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
            
            # Add button to clear the result
            if st.button("Clear Result", key="clear_agent_result"):
                st.session_state.pop("agent_sql_execution_result", None)
                st.rerun()
    
    # Don't show API key message on page load - only show when user tries to use it
    
    # Example questions section - only show if chatbot is available
    if not st.session_state.chat_history and st.session_state.chatbot:
        #st.markdown("### 💡 Example Questions to Get Started")
        #st.markdown("Click on any question below to get started:")
        
        example_questions = [
            "list of all tables in the database",
            "Tables with more than 10 records",
            "Column names and data types for all tables?"
        ]
        
        cols = st.columns(3)
        for idx, question in enumerate(example_questions):
            with cols[idx]:
                if st.button(question, key=f"example_{idx}", use_container_width=True):
                    # Add the question to chat history and process it
                    st.session_state.chat_history.append({'role': 'user', 'content': question})
                    try:
                        default_sql = _build_default_question_sql(question)
                        if default_sql:
                            response = {
                                "response": "Generated from built-in default question template.",
                                "sql_query": default_sql,
                                "timestamp": datetime.now().isoformat()
                            }
                        else:
                            with st.spinner("🤔 Thinking..."):
                                response = st.session_state.chatbot.chat(question, include_sql=True)
                        
                        if 'error' not in response:
                            sql_query = _dedupe_sql_query_text(_normalize_sql_for_execution(_extract_sql_from_response_payload(response)))
                            auto_executed = _auto_execute_chatbot_select_query(
                                sql_query,
                                response.get('timestamp', datetime.now().isoformat()),
                                unique_suffix="chatbot_auto_example"
                            )
                            auto_results_snapshot = _capture_chatbot_auto_results_snapshot() if auto_executed else {}
                            
                            _append_assistant_message({
                                'role': 'assistant',
                                'content': _clean_assistant_content_for_sql(response.get('response', ''), sql_query),
                                'sql_query': sql_query,
                                'timestamp': response['timestamp'],
                                'auto_executed': auto_executed,
                                **auto_results_snapshot
                            })
                        else:
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': response.get('response', response.get('error', 'Error occurred')),
                                'timestamp': response.get('timestamp', datetime.now().isoformat())
                            })
                    except Exception as e:
                        error_msg = f"❌ Error processing query: {str(e)}"
                        print(f"DEBUG: Chatbot error on example question: {e}")
                        import traceback
                        traceback.print_exc()
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': error_msg,
                            'timestamp': datetime.now().isoformat()
                        })
                    st.rerun()
        
        st.markdown("---")
    
    # Add marker before chat messages
    st.markdown('<div id="chat-container-start"></div>', unsafe_allow_html=True)
    
    # DEBUG: Show debug info in UI (temporary - remove after fixing)
    has_last_result = st.session_state.get('last_result_df') is not None
    has_auto_query = st.session_state.get('chatbot_last_auto_executed_query') is not None
    has_auto_error = st.session_state.get('chatbot_auto_execution_error') is not None
    has_show_results_flag = st.session_state.get('chatbot_show_results_for_query') is not None
    # Debug logging disabled for performance (can be enabled if needed)
    # print(f"DEBUG: Checking for results - has_last_result={has_last_result}, has_auto_query={has_auto_query}, has_auto_error={has_auto_error}, has_show_flag={has_show_results_flag}")
    
    # Debug Info section (DISABLED for performance)
    # with st.expander("🔍 Debug Info (Click to see)", expanded=False):
    #     st.write("**Session State Check:**")
    #     st.write(f"- `last_result_df` exists: {has_last_result}")
    #     st.write(f"- `chatbot_last_auto_executed_query` exists: {has_auto_query}")
    #     st.write(f"- `chatbot_show_results_for_query` exists: {has_show_results_flag}")
    #     st.write(f"- `chatbot_auto_execution_error` exists: {has_auto_error}")
    #     if has_last_result:
    #         st.write(f"- Result rows: {len(st.session_state.last_result_df)}")
    #         st.write(f"- Result columns: {list(st.session_state.last_result_df.columns)[:5]}...")
    #     if has_auto_query:
    #         st.write(f"- Last auto-executed query: {st.session_state.chatbot_last_auto_executed_query[:100]}...")
    #     if has_auto_error:
    #         st.write(f"- Auto-execution error: {st.session_state.chatbot_auto_execution_error[:200]}...")
    #     st.write(f"- Query history length: {len(st.session_state.get('query_history', []))}")
    #     st.write(f"- Chat history length: {len(st.session_state.get('chat_history', []))}")
    
    # Display chat history
    # Debug logging disabled for performance
    # print(f"DEBUG: Displaying chat history - total messages: {len(st.session_state.chat_history) if st.session_state.chat_history else 0}")
    
    # Track if we've shown results for the latest message
    results_shown_for_latest = False
    
    if st.session_state.chat_history:
        total_messages = len(st.session_state.chat_history)
        prev_assistant_sql = ""
        for idx, msg in enumerate(st.session_state.chat_history):
            print(f"DEBUG: Displaying message {idx}: role={msg.get('role')}, has_content={bool(msg.get('content'))}, has_sql={bool(msg.get('sql_query'))}")
            # Generate unique key using index and timestamp if available
            msg_timestamp = msg.get('timestamp', str(idx))
            unique_key_base = f"chatbot_tab_{idx}_{hash(str(msg_timestamp)) % 10000}"
            
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                # Recover SQL if assistant message missed explicit sql_query.
                if not msg.get('sql_query'):
                    recovered_sql = _dedupe_sql_query_text(
                        _normalize_sql_for_execution(
                            _extract_sql_from_response_payload({'response': msg.get('content', '')})
                        )
                    )
                    if recovered_sql:
                        st.session_state.chat_history[idx]['sql_query'] = recovered_sql
                        st.session_state.chat_history[idx]['content'] = _clean_assistant_content_for_sql(
                            st.session_state.chat_history[idx].get('content', ''),
                            recovered_sql
                        )
                        msg = st.session_state.chat_history[idx]

                # Hard guard: if message has SQL, explanation should never reprint SQL text.
                has_sql_in_msg = bool(msg.get('sql_query'))
                display_content = "SQL generated successfully." if has_sql_in_msg else _clean_assistant_content_for_sql(msg.get('content', ''), msg.get('sql_query', ''))
                # Show explanation in collapsed expander by default
                try:
                    with st.expander("💡 View Explanation", expanded=False):
                        st.chat_message("assistant").write(display_content)
                except Exception as e:
                    # Fallback if expander fails
                    st.chat_message("assistant").write(display_content)

                if msg.get("show_upload_panel", False):
                    _render_chatbot_upload_panel(msg, idx, unique_key_base)
                
                # Show SQL query in expanded form by default
                if 'sql_query' in msg and msg['sql_query']:
                    try:
                        raw_sql_query = msg['sql_query']
                        sql_query = _dedupe_sql_query_text(_normalize_sql_for_execution(raw_sql_query) or raw_sql_query)
                        # Update normalized/deduped SQL back into history to avoid future duplicates.
                        st.session_state.chat_history[idx]['sql_query'] = sql_query

                        # Skip immediate duplicate assistant SQL blocks in UI.
                        current_sql_signature = " ".join(sql_query.split()).strip().lower()
                        if current_sql_signature and current_sql_signature == prev_assistant_sql:
                            continue
                        prev_assistant_sql = current_sql_signature
                        is_safe_select = _is_safe_select_query(sql_query)
                        is_copy_local = _is_copy_from_local_file_sql(sql_query)
                        is_last_message = (idx == total_messages - 1)
                        
                        # Show SQL
                        with st.expander("📝 Generated SQL", expanded=_should_expand_sql(sql_query)):
                            st.code(sql_query, language='sql')
                            _render_sql_status_chips(msg)
                            
                            # For SELECT queries, show that it was auto-executed (results appear below)
                            if is_copy_local:
                                st.warning(
                                    "Server-side `COPY ... FROM '/path/file'` cannot access local files here. "
                                    "Use the upload panel to load your CSV/Excel into the table."
                                )
                                if st.button("Open Upload Panel", key=f"open_upload_{unique_key_base}"):
                                    st.session_state.chat_history[idx]["show_upload_panel"] = True
                                    st.session_state.chat_history[idx]["upload_target_table"] = _extract_copy_target_table(sql_query) or ""
                                    st.rerun()
                            elif is_safe_select:
                                # Deterministic auto-run for SELECT: attempt once for any unexecuted SQL message.
                                if not msg.get('auto_executed', False):
                                    retry_key = f"chatbot_auto_retry_{unique_key_base}"
                                    if not st.session_state.get(retry_key, False):
                                        auto_ok = _auto_execute_chatbot_select_query(
                                            sql_query,
                                            msg.get('timestamp', datetime.now().isoformat()),
                                            unique_suffix=f"chatbot_auto_retry_{unique_key_base}"
                                        )
                                        st.session_state[retry_key] = True
                                        if auto_ok:
                                            st.session_state.chat_history[idx]['auto_executed'] = True
                                            st.session_state.chat_history[idx].update(_capture_chatbot_auto_results_snapshot())
                                        st.rerun()
                                if msg.get('auto_executed', False):
                                    st.success("✅ Query executed automatically. Results shown below.")
                                else:
                                    # If not auto-executed yet, execute it now
                                    if st.button(f"Execute Query", key=f"exec_{unique_key_base}"):
                                        execute_generated_query(sql_query)
                            else:
                                # For DDL/DML, always require manual execution
                                if st.button(f"Execute Query", key=f"exec_{unique_key_base}"):
                                    execute_generated_query(sql_query)

                        # Deterministic snapshot render: always show stored results inline for this message.
                        snapshot_rendered = _render_inline_snapshot_results(msg, unique_key_base)
                        if is_safe_select and msg.get('auto_executed', False) and not snapshot_rendered:
                            # Hard fallback: if snapshot flags are set but nothing rendered,
                            # execute once here and render directly so user always sees results.
                            fallback_result = execute_single_statement(sql_query)
                            if fallback_result.get('success') and fallback_result.get('type') == 'SELECT':
                                fallback_df = fallback_result.get('dataframe')
                                if fallback_df is not None:
                                    st.markdown("---")
                                    st.markdown("**📋 Query Results**")
                                    st.caption(f"Rows: {len(fallback_df):,}")
                                    st.dataframe(fallback_df, use_container_width=True, hide_index=True)
                                    st.session_state.chat_history[idx]['auto_result_df'] = fallback_df.copy()
                                    snapshot_rendered = True
                        if snapshot_rendered:
                            results_shown_for_latest = True
                            # Snapshot is already rendered in-order for this message.
                            # Skip legacy global/fallback render branches.
                            continue
                        
                        # Show auto-execution results right after the latest assistant message with SQL
                        # Check if this is the last message and matches the auto-executed query
                        is_last_message = (idx == total_messages - 1)
                        msg_has_sql = 'sql_query' in msg and msg['sql_query']
                        stored_multi_results = msg.get('auto_multi_query_results', [])
                        stored_single_result = msg.get('auto_result_df')
                        has_stored_results = (stored_single_result is not None) or (len(stored_multi_results) > 0)

                        # Ensure every SELECT message binds to its own result snapshot,
                        # not just the latest assistant message.
                        if is_safe_select and not has_stored_results and not msg.get('auto_bind_attempted', False):
                            auto_ok = _auto_execute_chatbot_select_query(
                                sql_query,
                                msg.get('timestamp', datetime.now().isoformat()),
                                unique_suffix=f"chatbot_bind_{unique_key_base}"
                            )
                            st.session_state.chat_history[idx]['auto_bind_attempted'] = True
                            if auto_ok:
                                st.session_state.chat_history[idx]['auto_executed'] = True
                                st.session_state.chat_history[idx].update(_capture_chatbot_auto_results_snapshot())
                            st.rerun()

                        # Mark results as already rendered so fallback section doesn't append them at end.
                        if has_stored_results:
                            results_shown_for_latest = True
                        
                        # More lenient SQL matching - strip and compare
                        auto_executed_sql = _dedupe_sql_query_text(_normalize_sql_for_execution(st.session_state.get('chatbot_last_auto_executed_query', '')))
                        show_results_for = _dedupe_sql_query_text(_normalize_sql_for_execution(st.session_state.get('chatbot_show_results_for_query', '')))
                        msg_sql = _dedupe_sql_query_text(_normalize_sql_for_execution(msg['sql_query'])) if msg_has_sql else ''
                        msg_sql_matches = msg_has_sql and msg_sql == auto_executed_sql
                        msg_should_show = msg_has_sql and msg_sql == show_results_for
                        msg_was_auto_executed = msg.get('auto_executed', False)

                        # Late binding: if this message matches the auto-executed query and has no
                        # stored snapshot yet, attach current result so it renders inline in sequence.
                        if (
                            msg_has_sql and
                            not has_stored_results and
                            (msg_sql_matches or msg_should_show or msg_was_auto_executed) and
                            st.session_state.get('last_result_df') is not None
                        ):
                            st.session_state.chat_history[idx]['auto_result_df'] = st.session_state.last_result_df.copy()
                            stored_single_result = st.session_state.chat_history[idx]['auto_result_df']
                            has_stored_results = True
                            from utils.helpers import display_paginated_dataframe
                            st.markdown("---")
                            st.markdown("**📋 Query Results**")
                            display_paginated_dataframe(
                                stored_single_result,
                                unique_suffix=f"chatbot_msg_latebind_{unique_key_base}"
                            )
                            results_shown_for_latest = True
                        
                        print(f"DEBUG: Message {idx}/{total_messages-1} - is_last={is_last_message}, has_sql={msg_has_sql}")
                        print(f"DEBUG: msg_sql[:50]={msg_sql[:50] if msg_sql else 'None'}")
                        print(f"DEBUG: auto_sql[:50]={auto_executed_sql[:50] if auto_executed_sql else 'None'}")
                        print(f"DEBUG: show_results_for[:50]={show_results_for[:50] if show_results_for else 'None'}")
                        print(f"DEBUG: sql_matches={msg_sql_matches}, should_show={msg_should_show}, auto_executed={msg_was_auto_executed}")
                        print(f"DEBUG: has_last_result={has_last_result}, has_auto_query={has_auto_query}")
                        
                        # Check if we have multiple query results from auto-execution
                        has_multi_results = st.session_state.get('chatbot_multi_query_results') is not None and len(st.session_state.get('chatbot_multi_query_results', [])) > 0
                        
                        # Show results for the matching SQL message (not necessarily the last chat message).
                        should_show_results = (
                            msg_has_sql and 
                            (has_last_result or has_multi_results or has_auto_error) and
                            (msg_sql_matches or msg_should_show or msg_was_auto_executed)
                        )
                        
                        print(f"DEBUG: should_show_results={should_show_results}, has_multi_results={has_multi_results}")
                        
                        if should_show_results and not has_stored_results:
                            # Check if we have results or errors to display
                            if has_auto_error:
                                # Show error
                                st.error(f"❌ Auto-execution failed: {st.session_state.chatbot_auto_execution_error}")
                                st.code(st.session_state.get('chatbot_last_auto_executed_query', ''), language='sql')
                                st.info("💡 The query was generated but failed to execute. Please check the SQL syntax and table/column names.")
                                results_shown_for_latest = True
                            else:
                                # Check if we have multiple query results
                                multi_results = st.session_state.get('chatbot_multi_query_results', [])
                                
                                if has_multi_results and len(multi_results) > 1:
                                    # Display all results from multiple SELECT queries
                                    st.markdown("---")
                                    st.markdown("### 📋 Query Results (Multiple Queries)")
                                    
                                    for result_item in multi_results:
                                        query_text = result_item['query']
                                        result_df = result_item['dataframe']
                                        result_idx = result_item['index']
                                        
                                        st.markdown(f"**Query {result_idx}:**")
                                        st.code(query_text, language='sql')
                                        
                                        # Results header with icons
                                        result_col1, result_col2, result_col3, result_col4, result_col5 = st.columns([6.8, 0.4, 0.4, 0.4, 0.4], gap="small")
                                        with result_col1:
                                            st.markdown(f"**📋 Results {result_idx}**", unsafe_allow_html=True)
                                        with result_col2:
                                            # Download CSV button
                                            csv = result_df.to_csv(index=False)
                                            st.download_button(
                                                "📥",
                                                csv,
                                                f"results_{result_idx}.csv",
                                                "text/csv",
                                                help=f"Download CSV - {len(result_df):,} rows",
                                                width="stretch",
                                                key=f"download_multi_{result_idx}_{unique_key_base}"
                                            )
                                        with result_col3:
                                            # Visualization icon button
                                            from utils.helpers import _render_viz_icon_button
                                            viz_suffix = f"chatbot_multi_{result_idx}_{hash(query_text) % 10000}"
                                            _render_viz_icon_button(viz_suffix, result_df)
                                        with result_col4:
                                            # Data Explorer icon button
                                            from utils.helpers import _render_data_explorer_button
                                            explorer_suffix = f"chatbot_multi_{result_idx}_{hash(query_text) % 10000}"
                                            explorer_button_key, explorer_active = _render_data_explorer_button(explorer_suffix, result_df)
                                        with result_col5:
                                            # SQL Editor icon button
                                            from utils.helpers import _render_sql_editor_button
                                            sql_suffix = f"chatbot_multi_{result_idx}_{hash(query_text) % 10000}"
                                            sql_button_key, sql_active = _render_sql_editor_button(sql_suffix)
                                        
                                        # Display SQL Editor if active
                                        if sql_active:
                                            st.markdown("---")
                                            st.markdown("**📝 SQL Editor**")
                                            from ui.components import render_sql_editor
                                            sql_query_editor = render_sql_editor(
                                                key=f"sql_editor_chatbot_multi_{result_idx}_{sql_suffix}",
                                                height=200,
                                                placeholder="Enter SQL query here...",
                                                lightweight=True,
                                                prefer_smart=True,
                                                minimal_schema=True,
                                                guided_sql_assist=True
                                            )
                                            if sql_query_editor and sql_query_editor.strip():
                                                if st.button("Execute SQL", key=f"execute_sql_chatbot_multi_{result_idx}_{sql_suffix}"):
                                                    execute_query(sql_query_editor, enable_agents=True, unique_suffix=f"sql_editor_chatbot_multi_{result_idx}_{sql_suffix}")
                                        
                                        # Display Data Explorer if active
                                        if explorer_active:
                                            st.markdown("---")
                                            st.markdown("**🔍 Data Explorer**")
                                            try:
                                                from utils.helpers import display_data_explorer
                                                display_data_explorer(result_df)
                                            except Exception as e:
                                                st.error(f"Error displaying data explorer: {str(e)}")
                                        
                                        # Display paginated dataframe
                                        from utils.helpers import display_paginated_dataframe
                                        display_paginated_dataframe(
                                            result_df,
                                            unique_suffix=f"chatbot_multi_{result_idx}_{hash(query_text) % 10000}"
                                        )
                                        
                                        st.markdown("---")
                                    
                                    # Clear multi-results after displaying
                                    st.session_state.pop('chatbot_multi_query_results', None)
                                    # Also clear last_result_df to prevent fallback from showing it again
                                    st.session_state.pop('last_result_df', None)
                                    st.session_state.pop('last_result', None)
                                    results_shown_for_latest = True
                                elif has_last_result:
                                    # Show single result (original behavior)
                                    from utils.helpers import display_paginated_dataframe
                                    print(f"DEBUG: ✅ Displaying results after latest message - rows: {len(st.session_state.last_result_df)}")
                                    st.markdown("---")
                                    # Compact Results header with download, visualization, and data explorer icons
                                    result_col1, result_col2, result_col3, result_col4, result_col5 = st.columns([6.8, 0.4, 0.4, 0.4, 0.4], gap="small")
                                    with result_col1:
                                        st.markdown("**📋 Query Results**", unsafe_allow_html=True)
                                    with result_col2:
                                        # Download CSV button
                                        csv = st.session_state.last_result_df.to_csv(index=False)
                                        st.download_button(
                                            "📥",
                                            csv,
                                            "results.csv",
                                            "text/csv",
                                            help=f"Download CSV - {len(st.session_state.last_result_df):,} rows",
                                            width="stretch",  # New Streamlit API - replaces use_container_width=True
                                            key=f"download_auto_{unique_key_base}"
                                        )
                                    with result_col3:
                                        # Visualization icon button - positioned next to download CSV
                                        from utils.helpers import _render_viz_icon_button
                                        viz_suffix = f"chatbot_auto_result_{hash(st.session_state.chatbot_last_auto_executed_query) % 10000}"
                                        _render_viz_icon_button(viz_suffix, st.session_state.last_result_df)
                                    with result_col4:
                                        # Data Explorer icon button - positioned next to visualization button
                                        from utils.helpers import _render_data_explorer_button
                                        explorer_suffix = f"chatbot_auto_result_{hash(st.session_state.chatbot_last_auto_executed_query) % 10000}"
                                        explorer_button_key, explorer_active = _render_data_explorer_button(explorer_suffix, st.session_state.last_result_df)
                                    with result_col5:
                                        # SQL Editor icon button
                                        from utils.helpers import _render_sql_editor_button
                                        sql_suffix = f"chatbot_auto_result_{hash(st.session_state.chatbot_last_auto_executed_query) % 10000}"
                                        sql_button_key, sql_active = _render_sql_editor_button(sql_suffix)
                                    
                                    # Display SQL Editor if active
                                    if sql_active:
                                        st.markdown("---")
                                        st.markdown("**📝 SQL Editor**")
                                        from ui.components import render_sql_editor
                                        sql_query_editor = render_sql_editor(
                                            key=f"sql_editor_chatbot_auto_{sql_suffix}",
                                            height=200,
                                            placeholder="Enter SQL query here...",
                                            lightweight=True,
                                            prefer_smart=True,
                                            minimal_schema=True,
                                            guided_sql_assist=True
                                        )
                                        if sql_query_editor and sql_query_editor.strip():
                                            if st.button("Execute SQL", key=f"execute_sql_chatbot_auto_{sql_suffix}"):
                                                execute_query(sql_query_editor, enable_agents=True, unique_suffix=f"sql_editor_chatbot_auto_{sql_suffix}")
                                    
                                    # Display Data Explorer if active
                                    if explorer_active:
                                        st.markdown("---")
                                        st.markdown("**🔍 Data Explorer**")
                                        try:
                                            # Show basic statistics
                                            st.markdown("**Data Overview:**")
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("Rows", f"{len(st.session_state.last_result_df):,}")
                                            with col2:
                                                st.metric("Columns", len(st.session_state.last_result_df.columns))
                                            with col3:
                                                numeric_cols = st.session_state.last_result_df.select_dtypes(include=['number']).columns
                                                st.metric("Numeric Columns", len(numeric_cols))
                                            
                                            # Show column info
                                            st.markdown("**Column Information:**")
                                            col_info = pd.DataFrame({
                                                'Column': st.session_state.last_result_df.columns,
                                                'Data Type': [str(dtype) for dtype in st.session_state.last_result_df.dtypes],
                                                'Non-Null Count': [st.session_state.last_result_df[col].notna().sum() for col in st.session_state.last_result_df.columns],
                                                'Null Count': [st.session_state.last_result_df[col].isna().sum() for col in st.session_state.last_result_df.columns]
                                            })
                                            st.dataframe(col_info, use_container_width=True, hide_index=True)
                                            
                                            # Show basic statistics for numeric columns
                                            if len(numeric_cols) > 0:
                                                st.markdown("**Numeric Column Statistics:**")
                                                st.dataframe(st.session_state.last_result_df[numeric_cols].describe(), use_container_width=True)
                                            
                                            # Show sample data
                                            st.markdown("**Sample Data:**")
                                            st.dataframe(st.session_state.last_result_df.head(10), use_container_width=True, hide_index=True)
                                        except Exception as e:
                                            st.error(f"Error displaying data explorer: {str(e)}")
                                    
                                    # Search and visualization are now handled inside display_paginated_dataframe
                                    display_df = st.session_state.last_result_df.copy()
                                    st.session_state.current_page = 1
                                    display_paginated_dataframe(
                                        display_df,
                                        unique_suffix=f"chatbot_auto_result_{hash(st.session_state.chatbot_last_auto_executed_query) % 10000}"
                                    )
                                    results_shown_for_latest = True
                        else:
                            print(f"DEBUG: ❌ Not showing results - is_last={is_last_message}, has_sql={msg_has_sql}, has_result={has_last_result}, has_query={has_auto_query}")

                    except Exception as e:
                        # Render-safe fallback: if auto-executed snapshot exists, show it instead of manual button.
                        print(f"DEBUG: Render fallback triggered: {str(e)}")
                        has_snapshot = (
                            msg.get('auto_result_df') is not None or
                            (msg.get('auto_multi_query_results') is not None and len(msg.get('auto_multi_query_results', [])) > 0)
                        )
                        if msg.get('auto_executed', False) and has_snapshot:
                            rendered = _render_inline_snapshot_results(msg, f"{unique_key_base}_except")
                            if rendered:
                                results_shown_for_latest = True
                        else:
                            st.code(msg['sql_query'], language='sql')
                            if st.button(f"Execute Query", key=f"exec_fallback_{unique_key_base}"):
                                execute_generated_query(msg['sql_query'])
    
    # Fallback: If we have results but didn't show them in the loop, show them after chat history
    # Also check if there's an error that should be shown
    if has_auto_error and has_auto_query and not results_shown_for_latest:
        print(f"DEBUG: 🔄 Fallback - showing error after chat history loop")
        st.error(f"❌ Auto-execution failed: {st.session_state.chatbot_auto_execution_error}")
        st.code(st.session_state.get('chatbot_last_auto_executed_query', ''), language='sql')
        st.info("💡 The query was generated but failed to execute. Please check the SQL syntax and table/column names.")
        results_shown_for_latest = True
    
    # Check for multi-query results in fallback (only if results weren't already shown)
    # Re-check has_last_result in case it was cleared in main loop
    has_last_result_fallback = st.session_state.get('last_result_df') is not None
    has_multi_results_fallback = st.session_state.get('chatbot_multi_query_results') is not None and len(st.session_state.get('chatbot_multi_query_results', [])) > 0
    has_inline_result_messages = any(
        m.get('role') == 'assistant' and (
            m.get('auto_result_df') is not None or
            (m.get('auto_multi_query_results') is not None and len(m.get('auto_multi_query_results', [])) > 0)
        )
        for m in st.session_state.get('chat_history', [])
    )
    has_any_auto_executed_message = any(
        m.get('role') == 'assistant' and bool(m.get('auto_executed', False))
        for m in st.session_state.get('chat_history', [])
    )
    
    if (
        False and
        not results_shown_for_latest and
        (has_last_result_fallback or has_multi_results_fallback) and
        has_auto_query and
        not has_auto_error and
        not has_inline_result_messages and
        not has_any_auto_executed_message
    ):
        print(f"DEBUG: 🔄 Fallback - showing results after chat history loop")
        
        # Check if we have multiple query results
        multi_results = st.session_state.get('chatbot_multi_query_results', [])
        
        if has_multi_results_fallback and len(multi_results) > 1:
            # Display all results from multiple SELECT queries
            st.markdown("---")
            st.markdown("### 📋 Query Results (Multiple Queries)")
            
            for result_item in multi_results:
                query_text = result_item['query']
                result_df = result_item['dataframe']
                result_idx = result_item['index']
                
                st.markdown(f"**Query {result_idx}:**")
                st.code(query_text, language='sql')
                
                # Results header with icons
                result_col1, result_col2, result_col3, result_col4, result_col5 = st.columns([6.8, 0.4, 0.4, 0.4, 0.4], gap="small")
                with result_col1:
                    st.markdown(f"**📋 Results {result_idx}**", unsafe_allow_html=True)
                with result_col2:
                    # Download CSV button
                    csv = result_df.to_csv(index=False)
                    st.download_button(
                        "📥",
                        csv,
                        f"results_{result_idx}.csv",
                        "text/csv",
                        help=f"Download CSV - {len(result_df):,} rows",
                        width="stretch",
                        key=f"download_fallback_multi_{result_idx}"
                    )
                with result_col3:
                    # Visualization icon button
                    from utils.helpers import _render_viz_icon_button
                    viz_suffix = f"chatbot_fallback_multi_{result_idx}_{hash(query_text) % 10000}"
                    _render_viz_icon_button(viz_suffix, result_df)
                with result_col4:
                    # Data Explorer icon button
                    from utils.helpers import _render_data_explorer_button
                    explorer_suffix = f"chatbot_fallback_multi_{result_idx}_{hash(query_text) % 10000}"
                    explorer_button_key, explorer_active = _render_data_explorer_button(explorer_suffix, result_df)
                with result_col5:
                    # SQL Editor icon button
                    from utils.helpers import _render_sql_editor_button
                    sql_suffix = f"chatbot_fallback_multi_{result_idx}_{hash(query_text) % 10000}"
                    sql_button_key, sql_active = _render_sql_editor_button(sql_suffix)
                
                # Display SQL Editor if active
                if sql_active:
                    st.markdown("---")
                    st.markdown("**📝 SQL Editor**")
                    from ui.components import render_sql_editor
                    sql_query_editor = render_sql_editor(
                        key=f"sql_editor_chatbot_fallback_multi_{result_idx}_{sql_suffix}",
                        height=200,
                        placeholder="Enter SQL query here...",
                        lightweight=True,
                        prefer_smart=True,
                        minimal_schema=True,
                        guided_sql_assist=True
                    )
                    if sql_query_editor and sql_query_editor.strip():
                        if st.button("Execute SQL", key=f"execute_sql_chatbot_fallback_multi_{result_idx}_{sql_suffix}"):
                            execute_query(sql_query_editor, enable_agents=True, unique_suffix=f"sql_editor_chatbot_fallback_multi_{result_idx}_{sql_suffix}")
                
                # Display Data Explorer if active
                if explorer_active:
                    st.markdown("---")
                    st.markdown("**🔍 Data Explorer**")
                    try:
                        from utils.helpers import display_data_explorer
                        display_data_explorer(result_df)
                    except Exception as e:
                        st.error(f"Error displaying data explorer: {str(e)}")
                
                # Display paginated dataframe
                from utils.helpers import display_paginated_dataframe
                display_paginated_dataframe(
                    result_df,
                    unique_suffix=f"chatbot_fallback_multi_{result_idx}_{hash(query_text) % 10000}"
                )
                
                st.markdown("---")
            
            # Clear multi-results after displaying
            st.session_state.pop('chatbot_multi_query_results', None)
            # Also clear last_result_df to prevent duplicate display
            st.session_state.pop('last_result_df', None)
            st.session_state.pop('last_result', None)
        elif has_last_result_fallback and st.session_state.get('last_result_df') is not None:
            # Show single result (original fallback behavior) - only if last_result_df still exists
            from utils.helpers import display_paginated_dataframe
            st.markdown("---")
            # Compact Results header with download, visualization, data explorer, and SQL editor icons
            result_col1, result_col2, result_col3, result_col4, result_col5 = st.columns([6.8, 0.4, 0.4, 0.4, 0.4], gap="small")
            with result_col1:
                st.markdown("**📋 Query Results**", unsafe_allow_html=True)
            with result_col2:
                # Download CSV button
                csv = st.session_state.last_result_df.to_csv(index=False)
                st.download_button(
                    "📥",
                    csv,
                    "results.csv",
                    "text/csv",
                    help=f"Download CSV - {len(st.session_state.last_result_df):,} rows",
                    width="stretch",  # New Streamlit API - replaces use_container_width=True
                    key="download_auto_fallback"
                )
            with result_col3:
                # Visualization icon button - positioned next to download CSV
                from utils.helpers import _render_viz_icon_button
                viz_suffix = f"chatbot_auto_result_fallback_{hash(st.session_state.chatbot_last_auto_executed_query) % 10000}"
                _render_viz_icon_button(viz_suffix, st.session_state.last_result_df)
            with result_col4:
                # Data Explorer icon button - positioned next to visualization button
                from utils.helpers import _render_data_explorer_button
                explorer_suffix = f"chatbot_auto_result_fallback_{hash(st.session_state.chatbot_last_auto_executed_query) % 10000}"
                explorer_button_key, explorer_active = _render_data_explorer_button(explorer_suffix, st.session_state.last_result_df)
            with result_col5:
                # SQL Editor icon button
                from utils.helpers import _render_sql_editor_button
                sql_suffix = f"chatbot_auto_result_fallback_{hash(st.session_state.chatbot_last_auto_executed_query) % 10000}"
                sql_button_key, sql_active = _render_sql_editor_button(sql_suffix)
            
            # Display SQL Editor if active
            if sql_active:
                st.markdown("---")
                st.markdown("**📝 SQL Editor**")
                from ui.components import render_sql_editor
                sql_query_editor = render_sql_editor(
                    key=f"sql_editor_chatbot_fallback_{sql_suffix}",
                    height=200,
                    placeholder="Enter SQL query here...",
                    lightweight=True,
                    prefer_smart=True,
                    minimal_schema=True,
                    guided_sql_assist=True
                )
                if sql_query_editor and sql_query_editor.strip():
                    if st.button("Execute SQL", key=f"execute_sql_chatbot_fallback_{sql_suffix}"):
                        execute_query(sql_query_editor, enable_agents=True, unique_suffix=f"sql_editor_chatbot_fallback_{sql_suffix}")
            
            # Display Data Explorer if active
            if explorer_active:
                st.markdown("---")
                st.markdown("**🔍 Data Explorer**")
                try:
                    # Show basic statistics
                    st.markdown("**Data Overview:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Rows", f"{len(st.session_state.last_result_df):,}")
                    with col2:
                        st.metric("Columns", len(st.session_state.last_result_df.columns))
                    with col3:
                        numeric_cols = st.session_state.last_result_df.select_dtypes(include=['number']).columns
                        st.metric("Numeric Columns", len(numeric_cols))
                    
                    # Show column info
                    st.markdown("**Column Information:**")
                    col_info = pd.DataFrame({
                        'Column': st.session_state.last_result_df.columns,
                        'Data Type': [str(dtype) for dtype in st.session_state.last_result_df.dtypes],
                        'Non-Null Count': [st.session_state.last_result_df[col].notna().sum() for col in st.session_state.last_result_df.columns],
                        'Null Count': [st.session_state.last_result_df[col].isna().sum() for col in st.session_state.last_result_df.columns]
                    })
                    st.dataframe(col_info, use_container_width=True, hide_index=True)
                    
                    # Show basic statistics for numeric columns
                    if len(numeric_cols) > 0:
                        st.markdown("**Numeric Column Statistics:**")
                        st.dataframe(st.session_state.last_result_df[numeric_cols].describe(), use_container_width=True)
                    
                    # Show sample data
                    st.markdown("**Sample Data:**")
                    st.dataframe(st.session_state.last_result_df.head(10), use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"Error displaying data explorer: {str(e)}")
            
            # Search and visualization are now handled inside display_paginated_dataframe
            display_df = st.session_state.last_result_df.copy()
            st.session_state.current_page = 1
            display_paginated_dataframe(
                display_df,
                unique_suffix=f"chatbot_auto_result_fallback_{hash(st.session_state.chatbot_last_auto_executed_query) % 10000}"
            )

    # else:
    #     st.info("💬 Start chatting by typing a message below!")
    
    # Add marker after chat messages and JavaScript to wrap them
    st.markdown("""
    <div id="chat-container-end"></div>
    <script>
        (function() {
            function wrapChatMessages() {
                const startMarker = document.getElementById('chat-container-start');
                const endMarker = document.getElementById('chat-container-end');
                if (!startMarker || !endMarker) return;
                
                // Check if wrapper already exists
                if (document.getElementById('chat-messages-scrollable-wrapper')) return;
                
                // Find parent container
                let parent = startMarker.parentElement;
                if (!parent) return;
                
                // Create wrapper div
                const wrapper = document.createElement('div');
                wrapper.id = 'chat-messages-scrollable-wrapper';
                wrapper.style.cssText = `
                    max-height: 60vh;
                    overflow-y: auto;
                    overflow-x: hidden;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    border: 1px solid rgba(250, 250, 250, 0.2);
                    border-radius: 0.5rem;
                    background-color: rgba(0, 0, 0, 0.02);
                    scroll-behavior: smooth;
                `;
                
                // Collect all nodes between markers
                let node = startMarker.nextSibling;
                const nodesToMove = [];
                while (node && node !== endMarker) {
                    nodesToMove.push(node);
                    node = node.nextSibling;
                }
                
                // Move nodes into wrapper
                nodesToMove.forEach(n => wrapper.appendChild(n));
                
                // Insert wrapper after start marker
                startMarker.parentNode.insertBefore(wrapper, startMarker.nextSibling);
                
                // Auto-scroll to bottom
                wrapper.scrollTop = wrapper.scrollHeight;
            }
            
            // Run immediately and after delays
            wrapChatMessages();
            setTimeout(wrapChatMessages, 100);
            setTimeout(wrapChatMessages, 500);
            
            // Also observe for changes
            const observer = new MutationObserver(function() {
                wrapChatMessages();
                const wrapper = document.getElementById('chat-messages-scrollable-wrapper');
                if (wrapper) {
                    wrapper.scrollTop = wrapper.scrollHeight;
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        })();
    </script>
    """, unsafe_allow_html=True)
    
    # Ensure schema context is refreshed when chatbot page loads.
    if st.session_state.get("connected") and st.session_state.get("chatbot"):
        _ensure_chatbot_schema_context(with_spinner=False)
    
    # Chat input (outside scrollable container, stays at bottom)
    user_input = st.chat_input("Ask me anything about your database...")
    
    if user_input:
        # Check if chatbot is available when user actually tries to use it
        print(f"DEBUG: User input received (chatbot_tab): {user_input}")
        print(f"DEBUG: Chatbot available (chatbot_tab): {st.session_state.chatbot is not None}")
        if not st.session_state.chatbot:
            print(f"DEBUG: Chatbot is None (chatbot_tab), showing error message")
            st.error("❌ AI Chatbot is not available. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable to enable AI features.")
        else:
            # Ensure chatbot has latest schema context before generating SQL
            schema_info = st.session_state.get('schema_info')
            if st.session_state.chatbot:
                if schema_info and schema_info.get('tables'):
                    try:
                        st.session_state.chatbot.set_schema_context(schema_info)
                        print(f"DEBUG: Schema context set - tables: {len(schema_info.get('tables', []))}")
                        # Debug: Check if tables have column details
                        tables = schema_info.get('tables', [])
                        if tables:
                            first_table = tables[0]
                            if isinstance(first_table, dict):
                                cols = first_table.get('columns', [])
                                print(f"DEBUG: First table '{first_table.get('table_name', 'unknown')}' has {len(cols)} columns")
                            else:
                                print(f"DEBUG: WARNING - First table is not a dict, it's: {type(first_table)}")
                    except Exception as e:
                        print(f"DEBUG: Could not refresh chatbot schema: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"DEBUG: WARNING - schema_info is None or empty")
                    # Try to rebuild schema_info if connected
                    if st.session_state.connected and st.session_state.db_manager:
                        try:
                            with st.spinner("📊 Loading database schema..."):
                                tables = st.session_state.db_manager.get_tables()
                                full_table_schemas = []
                                for table_name in (tables or []):
                                    try:
                                        table_schema = st.session_state.db_manager.get_table_schema(table_name)
                                        if table_schema:
                                            full_table_schemas.append(table_schema)
                                    except Exception as e:
                                        full_table_schemas.append({'table_name': table_name, 'columns': []})
                                
                                schema_info = {
                                    'tables': full_table_schemas,
                                    'db_type': st.session_state.get('db_type', 'unknown'),
                                    'total_tables': len(tables) if tables else 0,
                                    'database_name': st.session_state.db_manager.config.database if st.session_state.db_manager.config else 'unknown'
                                }
                                st.session_state.schema_info = schema_info
                                st.session_state.chatbot.set_schema_context(schema_info)
                                print(f"DEBUG: Rebuilt schema_info - {len(full_table_schemas)} tables with schemas")
                        except Exception as e:
                            print(f"DEBUG: Could not rebuild schema_info: {e}")
                            import traceback
                            traceback.print_exc()
            
            # Add user message to history
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})

            # If user asks to upload/import a local file, show guided upload UI.
            if _is_upload_data_request(user_input):
                target_table = _infer_target_table_from_text(user_input)
                _append_assistant_message({
                    'role': 'assistant',
                    'content': (
                        "Upload mode enabled. Choose a local CSV/Excel file and target table below, "
                        "then click **Load file to table**."
                    ),
                    'timestamp': datetime.now().isoformat(),
                    'show_upload_panel': True,
                    'upload_target_table': target_table or ''
                })
                st.rerun()
            
            # Check if this is an INSERT/UPDATE/DELETE request - if so, use SchemaDataAgent first
            user_upper = user_input.upper()
            is_dml_request = any(keyword in user_upper for keyword in [
                'INSERT', 'UPDATE', 'DELETE', 'POPULATE', 'ADD RECORDS', 
                'CREATE RECORDS', 'ADD DATA', 'TEST RECORDS', 'MODIFY', 'CHANGE', 'REMOVE'
            ])
            
            schema_data_queries = []
            schema_data_analysis = None
            existing_data_summary = {}  # Initialize here to ensure it's always defined
            if is_dml_request and st.session_state.get('schema_info') and st.session_state.get('connected'):
                try:
                    from ai_db_tool.ai import AgentOrchestrator
                    # Initialize orchestrator if not exists
                    if 'agent_orchestrator' not in st.session_state or st.session_state.get('agent_orchestrator') is None:
                        api_key = get_api_key()
                        provider = "openai"  # Default provider
                        orchestrator = AgentOrchestrator(api_key=api_key, provider=provider)
                        st.session_state['agent_orchestrator'] = orchestrator
                    else:
                        orchestrator = st.session_state.get('agent_orchestrator')
                    
                    # Call SchemaDataAgent to determine what data needs to be queried
                    schema_data_response = orchestrator.analyze_schema_data(
                        user_query=user_input,
                        schema_info=st.session_state.get('schema_info', {}),
                        db_type=st.session_state.get('db_type', 'postgresql')
                    )
                    schema_data_analysis = schema_data_response.analysis
                    schema_data_queries = schema_data_response.suggestions
                    
                    print(f"DEBUG: SchemaDataAgent analysis: {schema_data_analysis[:200] if schema_data_analysis else 'None'}...")
                    print(f"DEBUG: SchemaDataAgent suggested queries: {schema_data_queries}")
                    
                    # ALWAYS query primary key values for INSERT operations to avoid UniqueViolation errors
                    # This should run regardless of what SchemaDataAgent returns
                    if 'insert' in user_upper:
                        print(f"DEBUG: INSERT operation detected, ensuring primary key and foreign key queries...")
                        schema_info = st.session_state.get('schema_info', {})
                        tables = schema_info.get('tables', [])
                        
                        # Find the target table from user input
                        target_table_name = None
                        user_lower = user_input.lower()
                        # Try to match table names from schema
                        for table in tables:
                            if isinstance(table, dict):
                                table_name = table.get('table_name', '').lower()
                                # Check if table name appears in user input
                                if table_name in user_lower or any(word in table_name for word in user_lower.split() if len(word) > 3):
                                    target_table_name = table.get('table_name')
                                    break
                            elif isinstance(table, str):
                                if table.lower() in user_lower:
                                    target_table_name = table
                                    break
                        
                        if target_table_name:
                            print(f"DEBUG: Found target table: {target_table_name}")
                            # Find the table schema
                            target_table_schema = None
                            for table in tables:
                                if isinstance(table, dict) and table.get('table_name') == target_table_name:
                                    target_table_schema = table
                                    break
                            
                            if target_table_schema:
                                # 1. Query PRIMARY KEY values from target table (CRITICAL for INSERT)
                                columns = target_table_schema.get('columns', [])
                                primary_keys = target_table_schema.get('primary_keys', [])
                                
                                # If no explicit primary_keys list, find columns marked as primary_key
                                if not primary_keys:
                                    for col in columns:
                                        if isinstance(col, dict) and col.get('primary_key', False):
                                            primary_keys.append(col.get('name', ''))
                                
                                # Query primary key values - ALWAYS add this query for INSERT operations
                                if primary_keys:
                                    pk_col = primary_keys[0]  # Use first primary key column
                                    pk_query = f"SELECT {pk_col} FROM {target_table_name} ORDER BY {pk_col};"
                                    # Check if this query already exists (case-insensitive, ignoring whitespace)
                                    pk_query_normalized = pk_query.upper().strip().replace(' ', '')
                                    pk_query_exists = any(
                                        q.upper().strip().replace(' ', '') == pk_query_normalized 
                                        for q in schema_data_queries
                                    )
                                    if not pk_query_exists:
                                        # Insert at the beginning so primary key query runs first
                                        schema_data_queries.insert(0, pk_query)
                                        print(f"DEBUG: Added primary key query (first): {pk_query}")
                                    else:
                                        print(f"DEBUG: Primary key query already exists in schema_data_queries")
                                else:
                                    print(f"DEBUG: WARNING - No primary key found for table {target_table_name}")
                                
                                # 2. Find foreign keys for this table and query parent table values
                                foreign_keys = target_table_schema.get('foreign_keys', [])
                                if foreign_keys:
                                    for fk in foreign_keys:
                                        if isinstance(fk, dict):
                                            referred_table = fk.get('referred_table', '')
                                            referred_columns = fk.get('referred_columns', [])
                                            if referred_table and referred_columns:
                                                # Generate SELECT query for foreign key values
                                                fk_col = referred_columns[0] if referred_columns else 'id'
                                                fk_query = f"SELECT {fk_col} FROM {referred_table};"
                                                if fk_query not in schema_data_queries:
                                                    schema_data_queries.append(fk_query)
                                                    print(f"DEBUG: Added foreign key query: {fk_query}")
                        else:
                            print(f"DEBUG: Could not determine target table from user input: {user_input}")
                    
                    # Execute the SELECT queries suggested by SchemaDataAgent
                    if schema_data_queries:
                        print(f"DEBUG: SchemaDataAgent suggested {len(schema_data_queries)} queries to check existing data")
                        for query in schema_data_queries:
                            try:
                                # Execute query to get existing data
                                result = st.session_state.db_manager.execute_query(query)
                                if result is not None and len(result) > 0:
                                    # Store the results to be used by chatbot
                                    query_key = f"schema_data_{hash(query) % 10000}"
                                    st.session_state[query_key] = result
                                    
                                    # Extract table and column from query for summary
                                    query_upper = query.upper().strip()
                                    table_name = None
                                    column_name = None
                                    
                                    # Parse SELECT column FROM table
                                    if 'SELECT' in query_upper and 'FROM' in query_upper:
                                        # Get column name
                                        select_part = query_upper.split('SELECT')[1].split('FROM')[0].strip()
                                        # Remove DISTINCT, etc.
                                        select_part = select_part.replace('DISTINCT', '').strip()
                                        column_name = select_part.split(',')[0].strip() if ',' in select_part else select_part.strip()
                                        
                                        # Get table name
                                        from_part = query_upper.split('FROM')[1].strip()
                                        # Handle schema.table format and WHERE clauses
                                        table_name = from_part.split()[0].strip(';').strip()
                                        # Remove schema prefix if present (e.g., "dfu.department" -> "department")
                                        if '.' in table_name:
                                            table_name = table_name.split('.')[-1]
                                    
                                    # Extract values from DataFrame
                                    if table_name and column_name and hasattr(result, 'columns'):
                                        # Get the actual column name from DataFrame (might be different due to case sensitivity)
                                        df_columns = list(result.columns)
                                        actual_col = column_name
                                        # Try to find matching column (case-insensitive)
                                        for col in df_columns:
                                            if col.upper() == column_name.upper():
                                                actual_col = col
                                                break
                                        
                                        if actual_col in df_columns:
                                            # Get unique values from the column
                                            values = result[actual_col].dropna().unique().tolist()
                                            # Convert to strings and filter out empty values
                                            values = [str(v) for v in values if v is not None and str(v).strip()]
                                            
                                            if values:
                                                key = f"{table_name}.{column_name}"
                                                existing_data_summary[key] = values
                                                print(f"DEBUG: Extracted {len(values)} unique values for {key}: {values[:10]}")
                                    
                                    print(f"DEBUG: Executed schema data query, got {len(result)} rows: {list(result.columns) if hasattr(result, 'columns') else 'N/A'}")
                                    if hasattr(result, 'head'):
                                        print(f"DEBUG: Sample values: {result.head(5).to_dict('records')}")
                            except Exception as e:
                                print(f"DEBUG: Could not execute schema data query: {e}")
                                import traceback
                                traceback.print_exc()
                except Exception as e:
                    print(f"DEBUG: SchemaDataAgent error: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Get AI response
            try:
                print(f"DEBUG: Calling chatbot.chat() (chatbot_tab) with query: {user_input}")
                print(f"DEBUG: Schema context available: {st.session_state.chatbot.schema_context is not None if st.session_state.chatbot else False}")
                if st.session_state.chatbot and st.session_state.chatbot.schema_context:
                    tables = st.session_state.chatbot.schema_context.get('tables', [])
                    print(f"DEBUG: Schema tables count: {len(tables)}")
                    if tables:
                        first_table = tables[0]
                        if isinstance(first_table, dict):
                            print(f"DEBUG: First table in context: {first_table.get('table_name', 'unknown')} with {len(first_table.get('columns', []))} columns")
                        else:
                            print(f"DEBUG: First table type: {type(first_table)}, value: {first_table}")
                else:
                    print(f"DEBUG: WARNING - No schema context in chatbot!")
                print(f"DEBUG: Schema tables count: {len(st.session_state.get('schema_info', {}).get('tables', [])) if st.session_state.get('schema_info') else 0}")
                
                # Enhance schema context with existing data if available
                enhanced_schema_context = None
                # Build enhanced context if we have queries executed OR existing data summary
                # This ensures primary key values are always included even if SchemaDataAgent didn't return analysis
                if schema_data_queries or existing_data_summary:
                    enhanced_schema_context = f"\n\n=== EXISTING DATA ANALYSIS ===\n"
                    if schema_data_analysis:
                        enhanced_schema_context += f"{schema_data_analysis}\n"
                    else:
                        enhanced_schema_context += f"Queries were executed to check existing data in the database.\n"
                    
                    if schema_data_queries:
                        enhanced_schema_context += f"\nQueries executed to check existing data:\n"
                        for q in schema_data_queries:
                            enhanced_schema_context += f"- {q}\n"
                    
                    # Add actual existing values to context (CRITICAL - this contains primary key values)
                    if existing_data_summary:
                        print(f"DEBUG: Building enhanced_schema_context with {len(existing_data_summary)} data summaries")
                        enhanced_schema_context += f"\n=== EXISTING VALUES (YOU MUST USE ONLY THESE VALUES) ===\n"
                        for key, values in existing_data_summary.items():
                            # Values are already a list of strings from extraction
                            if values:
                                # Show first 20 values
                                values_str = ', '.join(values[:20])
                                if len(values) > 20:
                                    values_str += f" (and {len(values) - 20} more)"
                                column_name = key.split('.')[1] if '.' in key else key
                                table_name = key.split('.')[0] if '.' in key else 'unknown'
                                
                                # Check if this is a primary key column
                                # A primary key query is: SELECT pk_col FROM table_name
                                # So if the table_name in the key matches a table in schema_info and the column is a primary key, it's a PK query
                                is_primary_key = False
                                schema_info = st.session_state.get('schema_info', {})
                                tables = schema_info.get('tables', [])
                                
                                # Find the matching table
                                matching_table = None
                                for table in tables:
                                    if isinstance(table, dict):
                                        table_name_from_schema = table.get('table_name', '').lower()
                                        if table_name_from_schema == table_name.lower():
                                            matching_table = table
                                            break
                                
                                if matching_table:
                                    # Get primary keys from the table
                                    primary_keys = matching_table.get('primary_keys', [])
                                    if not primary_keys:
                                        # Try to find from columns
                                        columns = matching_table.get('columns', [])
                                        for col in columns:
                                            if isinstance(col, dict) and col.get('primary_key', False):
                                                primary_keys.append(col.get('name', ''))
                                    
                                    # Check if column_name matches any primary key (case-insensitive)
                                    if any(pk_col.lower() == column_name.lower() for pk_col in primary_keys):
                                        is_primary_key = True
                                        print(f"DEBUG: Detected primary key: {table_name}.{column_name} (PKs: {primary_keys})")
                                    else:
                                        print(f"DEBUG: Column {table_name}.{column_name} is NOT a primary key (PKs: {primary_keys})")
                                else:
                                    print(f"DEBUG: Could not find table '{table_name}' in schema_info for primary key check")
                                
                                if is_primary_key:
                                    # Primary key values - must use NEXT available ID
                                    try:
                                        numeric_values = [int(v) for v in values if str(v).strip().isdigit()]
                                        if numeric_values:
                                            max_id = max(numeric_values)
                                            next_id = max_id + 1
                                            enhanced_schema_context += f"🚨 CRITICAL - PRIMARY KEY VALUES for {table_name}.{column_name}:\n"
                                            enhanced_schema_context += f"   Existing IDs: {values_str}\n"
                                            enhanced_schema_context += f"   MAX ID: {max_id}\n"
                                            enhanced_schema_context += f"   NEXT AVAILABLE ID: {next_id}\n"
                                            enhanced_schema_context += f"   ⚠️ YOU MUST USE IDs GREATER THAN {max_id} (e.g., {next_id}, {next_id + 1}, etc.)\n"
                                            enhanced_schema_context += f"   ⚠️ NEVER use IDs that already exist: {', '.join(values[:10])}{'...' if len(values) > 10 else ''}\n"
                                        else:
                                            enhanced_schema_context += f"🚨 CRITICAL - PRIMARY KEY VALUES for {table_name}.{column_name}:\n"
                                            enhanced_schema_context += f"   Existing values: {values_str}\n"
                                            enhanced_schema_context += f"   ⚠️ YOU MUST USE VALUES THAT DO NOT EXIST IN THE LIST ABOVE\n"
                                    except (ValueError, TypeError):
                                        enhanced_schema_context += f"🚨 CRITICAL - PRIMARY KEY VALUES for {table_name}.{column_name}:\n"
                                        enhanced_schema_context += f"   Existing values: {values_str}\n"
                                        enhanced_schema_context += f"   ⚠️ YOU MUST USE VALUES THAT DO NOT EXIST IN THE LIST ABOVE\n"
                                else:
                                    # Foreign key values - must use only existing values
                                    enhanced_schema_context += f"🚨 CRITICAL: For foreign key column '{column_name}' in table '{table_name}', you MUST use ONLY these values: {', '.join(values[:20])}\n"
                                    enhanced_schema_context += f"   - NEVER use values like 1, 2, 3 unless they appear in the list above\n"
                                    enhanced_schema_context += f"   - If the list above shows [10, 20, 30], use ONLY 10, 20, or 30 - nothing else\n"
                        enhanced_schema_context += "\n=== END EXISTING VALUES ===\n"
                    
                    enhanced_schema_context += "\n=== END EXISTING DATA ANALYSIS ===\n"
                
                # Ensure schema context is up-to-date before generating SQL
                if st.session_state.chatbot and st.session_state.connected and st.session_state.db_manager:
                    try:
                        # Refresh schema context to ensure it has latest table and column information
                        if not st.session_state.chatbot.schema_context or not st.session_state.chatbot.schema_context.get('tables'):
                            print(f"DEBUG: Schema context missing, refreshing...")
                            # Rebuild schema_info
                            tables = st.session_state.db_manager.get_tables()
                            full_table_schemas = []
                            for table_name in (tables or []):
                                try:
                                    table_schema = st.session_state.db_manager.get_table_schema(table_name)
                                    if table_schema:
                                        full_table_schemas.append(table_schema)
                                except Exception as e:
                                    print(f"DEBUG: Could not get schema for {table_name}: {e}")
                                    full_table_schemas.append({'table_name': table_name, 'columns': []})
                            
                            schema_info = {
                                'tables': full_table_schemas,
                                'db_type': st.session_state.get('db_type', 'postgresql'),
                                'total_tables': len(tables) if tables else 0,
                                'database_name': st.session_state.db_manager.config.database if st.session_state.db_manager.config else 'unknown'
                            }
                            st.session_state.schema_info = schema_info
                            st.session_state.chatbot.set_schema_context(schema_info)
                            print(f"DEBUG: Refreshed schema context - {len(full_table_schemas)} tables")
                    except Exception as e:
                        print(f"DEBUG: Could not refresh schema context: {e}")
                        import traceback
                        traceback.print_exc()
                
                with st.spinner("🤔 Thinking..."):
                    # Temporarily enhance chatbot's schema context if we have data analysis
                    original_context = None
                    if enhanced_schema_context and st.session_state.chatbot:
                        # Store original context
                        original_context = st.session_state.chatbot.schema_context
                        # Add data analysis to context
                        if original_context:
                            enhanced_context = original_context.copy()
                            enhanced_context['data_analysis'] = enhanced_schema_context
                            st.session_state.chatbot.set_schema_context(enhanced_context)
                    
                    response = st.session_state.chatbot.chat(user_input, include_sql=True)
                    
                    # Restore original context
                    if original_context and st.session_state.chatbot:
                        st.session_state.chatbot.set_schema_context(original_context)
                print(f"DEBUG: Chatbot response received (chatbot_tab): {type(response)}, has error: {'error' in response if isinstance(response, dict) else 'N/A'}")
                print(f"DEBUG: Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                if 'error' not in response:
                    # Add assistant response to history
                    try:
                        response_content = response.get('response', response.get('content', str(response)))
                        sql_query = _dedupe_sql_query_text(response.get('sql_query', response.get('sql', None)))
                        cleaned_response_content = _clean_assistant_content_for_sql(response_content, sql_query)
                        timestamp = response.get('timestamp', datetime.now().isoformat())
                        print(f"DEBUG: Adding response to chat history - content length: {len(response_content) if response_content else 0}, has sql: {bool(sql_query)}")
                        
                        # Check if SQL is a SELECT query (data retrieval) - auto-execute it
                        auto_executed = False
                        if sql_query:
                            print(f"DEBUG: Extracted SQL query: {sql_query[:200]}...")
                            auto_executed = _auto_execute_chatbot_select_query(
                                sql_query,
                                timestamp,
                                unique_suffix="chatbot_auto"
                            )
                        else:
                            print(f"DEBUG: No SQL query extracted from response")
                        
                        _append_assistant_message({
                            'role': 'assistant',
                            'content': cleaned_response_content,
                            'sql_query': sql_query,
                            'timestamp': timestamp,
                            'auto_executed': auto_executed,  # Track if query was auto-executed
                            **(_capture_chatbot_auto_results_snapshot() if auto_executed else {})
                        })
                        
                        # If we auto-executed, results are already displayed and stored in session state
                        # We still need to rerun to show the chat message, but results will be re-displayed
                        st.rerun()
                    except Exception as process_error:
                        print(f"DEBUG: Error processing response: {process_error}")
                        import traceback
                        traceback.print_exc()
                        st.error(f"❌ Error processing chatbot response: {str(process_error)}")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': f"Error processing response: {str(process_error)}",
                            'timestamp': datetime.now().isoformat()
                        })
                        st.rerun()
                else:
                    error_msg = response.get('error', 'Unknown error occurred')
                    print(f"DEBUG: Response contains error: {error_msg}")
                    st.error(f"Error: {error_msg}")
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': f"Error: {error_msg}",
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                error_msg = f"❌ Error processing query: {str(e)}"
                st.error(error_msg)
                print(f"DEBUG: Chatbot error: {e}")
                import traceback
                traceback.print_exc()
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
                st.rerun()


