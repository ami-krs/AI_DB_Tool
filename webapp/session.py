"""Session state initialization and management"""
import streamlit as st
from ai_db_tool.connectors import DatabaseManager
from ai_db_tool.ai import AIQueryBuilder, SQLChatbot
from config.database_config import load_db_config
from utils.helpers import get_api_key

def initialize_session_state():
    """Initialize all session state variables"""
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

    # Auto-load saved database connection on startup
    if not st.session_state.connected:
        saved_config = load_db_config()
        if saved_config:
            try:
                if st.session_state.db_manager.connect(saved_config):
                    st.session_state.connected = True
                    st.session_state.db_type = saved_config.db_type
                    # Load schema info
                    try:
                        tables = st.session_state.db_manager.get_tables()
                        try:
                            schema_info = st.session_state.db_manager.get_database_info()
                            if schema_info:
                                if tables and isinstance(tables[0] if tables else None, str):
                                    schema_info['tables'] = tables
                                elif schema_info.get('tables') and isinstance(schema_info['tables'][0] if schema_info['tables'] else None, dict):
                                    schema_info['tables'] = [t['table_name'] if isinstance(t, dict) and 'table_name' in t else str(t) for t in schema_info['tables']]
                                else:
                                    schema_info['tables'] = tables or []
                                schema_info['db_type'] = saved_config.db_type
                                schema_info['total_tables'] = len(tables) if tables else 0
                                st.session_state.schema_info = schema_info
                            else:
                                st.session_state.schema_info = {
                                    'tables': tables or [],
                                    'db_type': saved_config.db_type,
                                    'total_tables': len(tables) if tables else 0,
                                    'database_name': saved_config.database
                                }
                        except:
                            st.session_state.schema_info = {
                                'tables': tables or [],
                                'db_type': saved_config.db_type,
                                'total_tables': len(tables) if tables else 0,
                                'database_name': saved_config.database
                            }
                    except Exception as schema_error:
                        st.session_state.schema_info = {
                            'tables': [],
                            'db_type': saved_config.db_type,
                            'total_tables': 0,
                            'database_name': saved_config.database
                        }
                    st.session_state.auto_connected = True
            except Exception as e:
                pass

    # Ensure schema_info exists if connected
    if st.session_state.connected and 'schema_info' not in st.session_state:
        try:
            tables = st.session_state.db_manager.get_tables()
            try:
                schema_info = st.session_state.db_manager.get_database_info()
                if schema_info:
                    if tables and isinstance(tables[0] if tables else None, str):
                        schema_info['tables'] = tables
                    elif schema_info.get('tables') and isinstance(schema_info['tables'][0] if schema_info['tables'] else None, dict):
                        schema_info['tables'] = [t['table_name'] if isinstance(t, dict) and 'table_name' in t else str(t) for t in schema_info['tables']]
                    else:
                        schema_info['tables'] = tables or []
                    schema_info['db_type'] = st.session_state.db_type
                    schema_info['total_tables'] = len(tables) if tables else 0
                    st.session_state.schema_info = schema_info
                else:
                    st.session_state.schema_info = {
                        'tables': tables or [],
                        'db_type': st.session_state.db_type,
                        'total_tables': len(tables) if tables else 0
                    }
            except:
                st.session_state.schema_info = {
                    'tables': tables or [],
                    'db_type': st.session_state.db_type,
                    'total_tables': len(tables) if tables else 0
                }
        except:
            st.session_state.schema_info = {
                'tables': [],
                'db_type': st.session_state.db_type,
                'total_tables': 0
            }

    # Refresh schema_info if connected
    if st.session_state.connected and st.session_state.db_manager:
        try:
            tables = st.session_state.db_manager.get_tables()
            if st.session_state.get('schema_info'):
                st.session_state.schema_info['tables'] = tables or []
                st.session_state.schema_info['total_tables'] = len(tables) if tables else 0
            else:
                st.session_state.schema_info = {
                    'tables': tables or [],
                    'db_type': st.session_state.db_type,
                    'total_tables': len(tables) if tables else 0
                }
        except Exception as e:
            if not st.session_state.get('schema_info'):
                st.session_state.schema_info = {
                    'tables': [],
                    'db_type': st.session_state.db_type,
                    'total_tables': 0
                }

    # Initialize chatbot if connected
    if st.session_state.connected and (st.session_state.chatbot is None or st.session_state.query_builder is None):
        try:
            openai_key = get_api_key("OPENAI_API_KEY")
            anthropic_key = get_api_key("ANTHROPIC_API_KEY")
            api_key = openai_key or anthropic_key
            
            if api_key and st.session_state.get('schema_info'):
                provider = "openai" if openai_key else "anthropic" if anthropic_key else "openai"
                if st.session_state.chatbot is None:
                    st.session_state.chatbot = SQLChatbot(api_key=api_key, provider=provider)
                if st.session_state.query_builder is None:
                    st.session_state.query_builder = AIQueryBuilder(api_key=api_key, provider=provider)
                
                if st.session_state.chatbot and st.session_state.get('schema_info'):
                    try:
                        st.session_state.chatbot.set_schema_context(st.session_state.schema_info)
                    except Exception:
                        pass
        except Exception as e:
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
    
    # Initialize active_section from query params
    if 'active_section' not in st.session_state:
        section_from_query = None
        try:
            if hasattr(st, 'query_params') and st.query_params:
                query_params = st.query_params
                if 'section' in query_params:
                    section = query_params.get('section')
                    if isinstance(section, list):
                        section = section[0] if section else None
                    elif isinstance(section, str):
                        section = section.strip()
                    section_from_query = section
        except Exception:
            pass
        
        if section_from_query and section_from_query in ['home', 'chatbot', 'sql_editor', 'data_explorer', 'visualizations', 'smart_email_agent']:
            st.session_state.active_section = section_from_query
        else:
            st.session_state.active_section = 'home'
    
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
