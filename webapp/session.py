"""Session state initialization and management"""
import streamlit as st
from ai_db_tool.connectors import DatabaseManager
from ai_db_tool.ai import AIQueryBuilder, SQLChatbot
from config.database_config import load_db_config
from utils.helpers import get_api_key
import importlib.util


DB_SECTIONS = {"chatbot", "sql_editor", "data_explorer", "visualizations"}
AI_SECTIONS = {"chatbot", "sql_editor"}


def _anthropic_pkg_available() -> bool:
    """Return True if the optional `anthropic` package is installed."""
    try:
        return importlib.util.find_spec("anthropic") is not None
    except Exception:
        return False


def _get_active_section() -> str:
    """Get active section from session state / query params without doing heavy work."""
    # If already set (e.g., user clicked a button), keep it.
    section = st.session_state.get("active_section")
    if isinstance(section, str) and section.strip():
        return section.strip()

    # Otherwise, initialize from query params (if present)
    section_from_query = None
    try:
        # Safely check for query_params (available in Streamlit 1.28+)
        if hasattr(st, "query_params"):
            query_params = st.query_params
            if query_params and "section" in query_params:
                section_val = query_params.get("section")
                if isinstance(section_val, list):
                    section_val = section_val[0] if section_val else None
                elif isinstance(section_val, str):
                    section_val = section_val.strip()
                if isinstance(section_val, str) and section_val:
                    section_from_query = section_val
    except (AttributeError, TypeError, KeyError, Exception):
        # If query_params doesn't exist or fails, just use default
        section_from_query = None

    if section_from_query and section_from_query in ["home", "chatbot", "sql_editor", "data_explorer", "visualizations", "smart_email_agent"]:
        return section_from_query
    return "home"

def initialize_session_state():
    """Initialize all session state variables"""
    # Determine active section EARLY so we can defer heavy work on Home.
    # (This runs on every rerun; keep it lightweight.)
    if "active_section" not in st.session_state:
        st.session_state.active_section = _get_active_section()

    # Core database manager
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = None
    if 'query_builder' not in st.session_state:
        st.session_state.query_builder = None
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'db_type' not in st.session_state:
        st.session_state.db_type = None

    # Defer auto-connecting + schema fetching until user opens DB-relevant sections.
    # This makes Home load much faster after boot.
    active_section = st.session_state.get("active_section", "home")
    should_autoconnect_now = active_section in DB_SECTIONS

    if "auto_connect_attempted" not in st.session_state:
        st.session_state.auto_connect_attempted = False

    # Auto-load saved database connection (DEFERRED)
    if should_autoconnect_now and (not st.session_state.connected) and (not st.session_state.auto_connect_attempted):
        st.session_state.auto_connect_attempted = True
        saved_config = load_db_config()
        if saved_config:
            try:
                if st.session_state.db_manager.connect(saved_config):
                    st.session_state.connected = True
                    st.session_state.db_type = saved_config.db_type
                    st.session_state.auto_connected = True
                    # Do NOT fetch schema here. Schema can be heavy; pages will fetch on-demand.
                    if "schema_info" not in st.session_state:
                        st.session_state.schema_info = {
                            "tables": [],
                            "db_type": saved_config.db_type,
                            "total_tables": 0,
                            "database_name": saved_config.database,
                        }
            except Exception:
                # Silent failure; user can still manually connect via UI
                pass

    # Ensure schema_info exists if connected (lightweight placeholder only)
    if st.session_state.connected and "schema_info" not in st.session_state:
        st.session_state.schema_info = {
            "tables": [],
            "db_type": st.session_state.db_type,
            "total_tables": 0,
        }

    # Defer AI client initialization until user opens AI-relevant sections.
    should_init_ai_now = active_section in AI_SECTIONS
    if should_init_ai_now and st.session_state.connected and (st.session_state.chatbot is None or st.session_state.query_builder is None):
        try:
            openai_key = get_api_key("OPENAI_API_KEY")
            anthropic_key = get_api_key("ANTHROPIC_API_KEY")
            api_key = openai_key or anthropic_key

            if api_key:
                # Prefer OpenAI when available. Only use Anthropic if package is installed.
                if openai_key:
                    provider = "openai"
                elif anthropic_key and _anthropic_pkg_available():
                    provider = "anthropic"
                else:
                    provider = "openai"

                if st.session_state.chatbot is None:
                    st.session_state.chatbot = SQLChatbot(api_key=api_key, provider=provider)
                if st.session_state.query_builder is None:
                    st.session_state.query_builder = AIQueryBuilder(api_key=api_key, provider=provider)

                # Schema context will be built/expanded on-demand in the pages (Chatbot does this already).
                if st.session_state.chatbot and st.session_state.get("schema_info"):
                    try:
                        st.session_state.chatbot.set_schema_context(st.session_state.schema_info)
                    except Exception:
                        pass
        except Exception:
            # Silent failure; DB features remain usable
            pass

    # Initialize other session state variables
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'fixed_query' not in st.session_state:
        st.session_state.fixed_query = None
    if 'layout_mode' not in st.session_state:
        st.session_state.layout_mode = 'tabs'
    if 'last_quick_select' not in st.session_state:
        st.session_state.last_quick_select = "-- Select --"
    if 'show_db_info' not in st.session_state:
        st.session_state.show_db_info = False
    if 'show_chatbot' not in st.session_state:
        st.session_state.show_chatbot = True
    if 'show_connection' not in st.session_state:
        st.session_state.show_connection = True
    
    # active_section is initialized early now (before heavy work)
    
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'rows_per_page' not in st.session_state:
        st.session_state.rows_per_page = 100
    if 'editor_mode' not in st.session_state:
        legacy_flag = st.session_state.get('use_codemirror_editor', False)
        st.session_state.editor_mode = 'codemirror' if legacy_flag else 'textarea'
    if 'use_codemirror_editor' not in st.session_state:
        st.session_state.use_codemirror_editor = st.session_state.editor_mode != 'textarea'
    if 'api_server_url' not in st.session_state:
        st.session_state.api_server_url = "http://localhost:8000"
    if 'enable_ai_agents' not in st.session_state:
        st.session_state.enable_ai_agents = True  # Enable agents by default