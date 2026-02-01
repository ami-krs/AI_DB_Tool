"""UI component rendering functions"""
import streamlit as st
from typing import Dict, List
from pathlib import Path

from config.database_config import get_persistent_sqlite_path, CONFIG_FILE, save_db_config
from utils.helpers import get_api_key
from shared import CODEMIRROR_AVAILABLE, MONACO_EDITOR_AVAILABLE, codemirror_editor, monaco_editor
from ui.navigation import handle_connection

from ai_db_tool.connectors import DatabaseConfig
from ai_db_tool.ai import AIQueryBuilder, SQLChatbot


def render_db_details():
    """Render connected database details by default in top-left"""
    if st.session_state.connected and st.session_state.db_manager:
        try:
            schema_info = st.session_state.get('schema_info', {})
            db_type = st.session_state.db_type or 'unknown'
            
            # Get actual database path from config
            db_path = None
            if st.session_state.db_manager.config:
                db_path = st.session_state.db_manager.config.database
            
            # For SQLite, show the full path for debugging
            if db_type == 'sqlite' and db_path:
                # Get expected path from secrets/default
                expected_path = get_persistent_sqlite_path()
                db_name = db_path.split('/')[-1] if '/' in db_path else db_path
                
                total_tables = schema_info.get('total_tables', 0)
                
                # Display path info
                st.info(f"🔌 **{db_type.upper()}** | {db_name} | {total_tables} tables")
                # Show full path in expandable section for debugging
                with st.expander("📁 Database Path Info", expanded=False):
                    st.code(f"Current path: {db_path}")
                    st.code(f"Expected path: {expected_path}")
                    if db_path != expected_path:
                        st.warning(f"⚠️ Path mismatch! Current: `{db_path}` vs Expected: `{expected_path}`")
                    else:
                        st.success("✅ Path matches expected location")
            else:
                db_name = schema_info.get('database_name', 'unknown')
                if db_type == 'sqlite' and '/' in str(db_name):
                    db_name = str(db_name).split('/')[-1]
                total_tables = schema_info.get('total_tables', 0)
                st.info(f"🔌 **{db_type.upper()}** | {db_name} | {total_tables} tables")
        except Exception as e:
            st.info(f"🔌 **Connected** (Error: {e})")
    else:
        st.info("🔌 **Not Connected**")




def render_settings_dropdown():
    """Render settings dropdown (Smart Editor, Layout, Theme) using Streamlit selectbox"""
    
    # Use a selectbox styled as a dropdown button for settings
    settings_options = {
        "⚙️ Settings": None,
        "⚡ Smart Editor": "editor",
        "📐 Layout": "layout",
        "🎨 Theme": "theme",
        "🤖 AI Agents": "agents"
    }
    
    option_labels = list(settings_options.keys())
    
    # Initialize active_setting if not exists
    if 'active_setting' not in st.session_state:
        st.session_state.active_setting = None
    
    # Clear active_setting if it's "connection" (no longer in settings dropdown)
    if st.session_state.active_setting == 'connection':
        st.session_state.active_setting = None
    
    # Determine current index (0 if no active setting)
    try:
        current_setting_label = next(k for k, v in settings_options.items() if v == st.session_state.active_setting)
        current_index = option_labels.index(current_setting_label)
    except (StopIteration, ValueError):
        current_index = 0
    
    selected_label = st.selectbox(
        "Settings",
        options=option_labels,
        index=current_index,
        key="settings_dropdown_selectbox",
        label_visibility="collapsed"
    )
    
    selected_setting = settings_options.get(selected_label)
    
    # If "⚙️ Settings" (None) is selected, close the active setting
    if selected_setting is None:
        if st.session_state.active_setting is not None:
            st.session_state.active_setting = None
            st.rerun()
    # If a setting is selected, update active_setting
    elif selected_setting and selected_setting != st.session_state.active_setting:
        st.session_state.active_setting = selected_setting
        st.rerun()
    
    # Render the active setting in an expander
    if st.session_state.active_setting:
        setting_labels = {
            "editor": "⚡ Smart Editor",
            "layout": "📐 Layout",
            "theme": "🎨 Theme",
            "agents": "🤖 AI Agents"
        }
        setting_label = setting_labels.get(st.session_state.active_setting, "Settings")
        with st.expander(setting_label, expanded=True):
            render_setting_content(st.session_state.active_setting)
    
    # Style the selectbox to look like a button
    st.markdown("""
    <style>
    div[data-testid="stSelectbox"]:has(> label[for*="settings_dropdown"]) > div > div {
        background-color: #0d7377 !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem 1rem !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        cursor: pointer !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: background-color 0.2s !important;
        min-width: fit-content !important;
        width: max-content !important;
    }
    div[data-testid="stSelectbox"]:has(> label[for*="settings_dropdown"]) > div > div:hover {
        background-color: #14a085 !important;
    }
    div[data-testid="stSelectbox"]:has(> label[for*="settings_dropdown"]) > div > div > div {
        color: white !important;
    }
    div[data-testid="stSelectbox"]:has(> label[for*="settings_dropdown"]) > div > div > div > svg {
        fill: white !important;
    }
    </style>
    <script>
    (function() {
        function styleSettingsSelectbox() {
            const selectboxes = document.querySelectorAll('div[data-testid="stSelectbox"]');
            selectboxes.forEach(function(selectbox) {
                const label = selectbox.querySelector('label');
                if (label && label.getAttribute('for') && label.getAttribute('for').includes('settings_dropdown')) {
                    selectbox.classList.add('settings-selectbox-styled');
                }
            });
        }
        styleSettingsSelectbox();
        setTimeout(styleSettingsSelectbox, 100);
        setTimeout(styleSettingsSelectbox, 500);
        const observer = new MutationObserver(styleSettingsSelectbox);
        observer.observe(document.body, { childList: true, subtree: true });
    })();
    </script>
    """, unsafe_allow_html=True)




def render_setting_content(setting_type):
    """Render the content for a specific setting type"""
    if setting_type == 'editor':
        render_smart_editor_setting()
    elif setting_type == 'layout':
        render_layout_setting()
    elif setting_type == 'theme':
        render_theme_setting()
    elif setting_type == 'agents':
        render_agents_setting()




def render_smart_editor_setting():
    """Render Smart Editor selection"""
    editor_options = [("textarea", "Streamlit Text Area (Default)")]
    if CODEMIRROR_AVAILABLE:
        editor_options.append(("codemirror", "CodeMirror (AI Autocomplete)"))
    if MONACO_EDITOR_AVAILABLE:
        editor_options.append(("monaco", "Monaco (VS Code Experience)"))

    valid_modes = [value for value, _ in editor_options]
    if st.session_state.editor_mode not in valid_modes:
        st.session_state.editor_mode = "textarea"

    current_index = valid_modes.index(st.session_state.editor_mode)
    option_labels = [label for _, label in editor_options]

    selected_label = st.selectbox(
        "SQL Editor Mode",
        option_labels,
        index=current_index,
        key="editor_mode_select_popup",
        help="Choose which SQL editor to use in the workspace."
    )

    selected_mode = next(value for value, label in editor_options if label == selected_label)
    if selected_mode != st.session_state.editor_mode:
        st.session_state.editor_mode = selected_mode
        st.session_state.use_codemirror_editor = selected_mode != "textarea"
        st.session_state.active_setting = None
        st.rerun()

    if st.session_state.editor_mode in ("codemirror", "monaco"):
        api_url = st.text_input(
            "API Server URL",
            value=st.session_state.api_server_url,
            autocomplete="url",
            help="Backend API URL for AI autocomplete (default: http://localhost:8000)"
        )
        if api_url != st.session_state.api_server_url:
            st.session_state.api_server_url = api_url
            st.rerun()
        st.info("💡 Start the API server: `python webapp/api_server.py`")
    elif not (CODEMIRROR_AVAILABLE or MONACO_EDITOR_AVAILABLE):
        st.info("Install the optional smart editor components to enable AI autocomplete.")
        



def render_layout_setting():
    """Render Layout selection"""
    layout_mode = st.radio(
        "Choose layout:",
        ["Tabs (Classic)", "Three Column"],
        index=0 if st.session_state.layout_mode == 'tabs' else 1,
        key="layout_radio_popup"
    )
    new_layout_mode = 'tabs' if layout_mode == "Tabs (Classic)" else 'three_column'
    if new_layout_mode != st.session_state.layout_mode:
        st.session_state.layout_mode = new_layout_mode
        st.session_state.active_setting = None
        st.rerun()




def render_theme_setting():
    """Render Theme settings"""
    # Dark mode toggle with hover tooltip
    dark_mode_toggle = st.toggle(
        "🌙 Dark Mode",
        value=st.session_state.dark_mode,
        key="dark_mode_toggle_settings",
        help="Toggle between light and dark theme. Dark mode uses a dark color scheme for better visibility in low-light environments. Light mode uses a light color scheme for better visibility in bright environments."
    )
    
    if dark_mode_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode_toggle
        st.rerun()

def render_agents_setting():
    """Render AI Agents settings"""
    st.info("🤖 Multi-Agent AI System")
    st.markdown("""
    Enable specialized AI agents to analyze queries, review results, debug errors, and suggest improvements.
    
    **Available Agents:**
    - 🔍 **Query Analyzer**: Analyzes queries before execution
    - 📊 **Results Analyzer**: Reviews results and suggests solutions
    - 🐛 **Debug Agent**: Debugs errors and issues
    - ✨ **Review Agent**: Reviews results and suggests optimizations
    """)
    
    enable_agents = st.toggle(
        "Enable AI Agents", 
        value=st.session_state.get('enable_ai_agents', True),
        key="enable_ai_agents_toggle",
        help="Enable multi-agent AI analysis for queries and results"
    )
    if enable_agents != st.session_state.get('enable_ai_agents', True):
        st.session_state.enable_ai_agents = enable_agents
        st.rerun()
    
    if enable_agents:
        st.success("✅ AI Agents are enabled. They will analyze your queries and results automatically.")
    else:
        st.info("ℹ️ AI Agents are disabled. Enable them to get AI-powered analysis and suggestions.")
        



def render_connection_setting():
    """Render Database Connection form"""
    # Add CSS to make Connect/Disconnect buttons compact and fit in one line
    st.markdown("""
    <style>
    /* Target buttons in connection form columns - wider but shorter height */
    div[data-testid="stForm"]:has(form) div[data-testid="column"] button {
        font-size: 0.7rem !important;
        padding: 0.15rem 0.8rem !important;
        line-height: 1.2 !important;
        height: 1.8rem !important;
        min-height: 1.8rem !important;
        max-height: 1.8rem !important;
        margin: 0 !important;
    }
    /* Reduce padding around form fields */
    div[data-testid="stForm"]:has(form) {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    /* Reduce spacing between form elements */
    div[data-testid="stForm"]:has(form) > div {
        gap: 0.5rem !important;
    }
    div[data-testid="stForm"]:has(form) .stTextInput,
    div[data-testid="stForm"]:has(form) .stSelectbox,
    div[data-testid="stForm"]:has(form) .stNumberInput {
        margin-bottom: 0.5rem !important;
    }
    /* Make button text more compact */
    div[data-testid="stForm"]:has(form) div[data-testid="column"] button > div {
        padding: 0 !important;
        margin: 0 !important;
        line-height: 1.2 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    db_type = st.selectbox(
        "Database Type",
        ["postgresql", "mysql", "sqlserver", "oracle", "sqlite"],
        index=4,  # Default to sqlite
        key="db_type_popup"
    )
    
    with st.form("connection_form_popup", clear_on_submit=False):
        if db_type == "sqlite":
            # Always use persistent path for SQLite to ensure data persistence
            persistent_path = get_persistent_sqlite_path()
            # Always use the persistent path - show it as read-only or inform user
            st.info(f"💾 SQLite database location: `{persistent_path}` (persistent - data will be preserved)")
            database = persistent_path  # Always use persistent path
            # Hidden input to satisfy form requirements
            st.text_input(
                "Database File Path", 
                value=persistent_path, 
                help="SQLite database is always stored in a persistent location to ensure data is preserved across restarts", 
                disabled=True,  # Make it read-only so user can't change it
                key="db_file_popup_display"
            )
            # Store the persistent path
            st.session_state['db_file_path_sqlite'] = persistent_path
            host = ""
            port = 0
            username = ""
            password = ""
        else:
            host = st.text_input("Host", value="localhost", autocomplete="url", key="host_popup")
            port = st.number_input("Port", value=5432 if db_type == "postgresql" else 3306, key="port_popup")
            database = st.text_input("Database Name", autocomplete="off", key="database_popup")
            username = st.text_input("Username", autocomplete="username", key="username_popup")
            password = st.text_input("Password", type="password", autocomplete="current-password", key="password_popup")
        
        col1, col2 = st.columns(2)
        with col1:
            connect_button = st.form_submit_button("Connect", type="primary", use_container_width=True)
        with col2:
            if st.session_state.connected:
                disconnect_button = st.form_submit_button("Disconnect", use_container_width=True)
            else:
                disconnect_button = False
        
        # Handle form submission inside the form context
        if connect_button:
            try:
                # For SQLite, always use persistent path
                if db_type == "sqlite":
                    database = get_persistent_sqlite_path()
                handle_connection(db_type, host, port, database, username, password)
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
                import traceback
                st.exception(e)
        
        if disconnect_button and st.session_state.connected:
            st.session_state.db_manager.disconnect()
            st.session_state.connected = False
            st.session_state.chatbot = None
            st.session_state.query_builder = None
            
            # Optionally clear saved config (user can choose to keep it)
            if CONFIG_FILE.exists():
                try:
                    CONFIG_FILE.unlink()
                except:
                    pass
            
            st.success("Disconnected")
            st.rerun()




def render_sql_editor(key: str, height: int = 250, placeholder: str = "SELECT * FROM table_name LIMIT 10;"):
    """
    Render SQL editor (Monaco, CodeMirror, or regular text area)
    
    Parameters:
    -----------
    key : str
        Unique key for the editor
    height : int
        Editor height in pixels
    placeholder : str
        Placeholder text
    
    Returns:
    --------
    str
        Current SQL query value
    """
    # Get current query value
    current_query = st.session_state.get('sql_editor', '')
    
    # Get schema info if connected
    schema_info = None
    tables = None
    table_columns: Dict[str, List[str]] = {}
    if st.session_state.connected and st.session_state.db_manager:
        try:
            tables = st.session_state.db_manager.get_tables()
            if tables:
                for table_name in tables[:20]:
                    try:
                        schema = st.session_state.db_manager.get_table_schema(table_name)
                        columns = [col['name'] for col in schema.get('columns', [])]
                        if columns:
                            table_columns[table_name] = columns
                    except Exception:
                        continue
                if tables:
                    schema_info = st.session_state.db_manager.get_table_schema(tables[0])
        except Exception:
            pass

    if not table_columns and tables:
        table_columns = {table: [] for table in tables[:10]}

    sql_hint_config = {
        "language": "sql",
        "theme": "darcula",
        "autoCloseBrackets": True,
        "lineNumbers": True,
        "sql": {
            "tables": table_columns
            or {
                "employees": ["id", "name", "salary"],
                "departments": ["dept_id", "dept_name"],
            }
        },
    }

    editor_mode = st.session_state.get('editor_mode', 'textarea')
    st.session_state.use_codemirror_editor = editor_mode != 'textarea'

    # Use Monaco Editor if selected and available
    if editor_mode == 'monaco' and MONACO_EDITOR_AVAILABLE and monaco_editor:
        try:
            theme = "vs-dark" if st.session_state.dark_mode else "vs"

            editor_value = monaco_editor(
                value=current_query,
                height=height,
                language="sql",
                theme=theme,
                api_url=st.session_state.api_server_url,
                database_type=st.session_state.db_type,
                schema_info=schema_info,
                tables=tables,
                config=sql_hint_config,
                key=f"monaco_{key}"
            )

            if editor_value != current_query:
                st.session_state.sql_editor = editor_value
            return editor_value
        except Exception as e:
            st.warning(f"Monaco editor error: {e}. Falling back to regular editor.")
            st.session_state.editor_mode = 'textarea'
            st.session_state.use_codemirror_editor = False

    # Use CodeMirror Editor if selected and available
    if editor_mode == 'codemirror' and CODEMIRROR_AVAILABLE and codemirror_editor:
        try:
            theme = "vs-dark" if st.session_state.dark_mode else "vs"

            editor_value = codemirror_editor(
                value=current_query,
                height=height,
                language="sql",
                theme=theme,
                api_url=st.session_state.api_server_url,
                database_type=st.session_state.db_type,
                schema_info=schema_info,
                tables=tables,
                config=sql_hint_config,
                key=f"codemirror_{key}"
            )

            if editor_value != current_query:
                st.session_state.sql_editor = editor_value
            return editor_value
        except Exception as e:
            st.warning(f"CodeMirror editor error: {e}. Falling back to regular editor.")
            st.session_state.editor_mode = 'textarea'
            st.session_state.use_codemirror_editor = False

    # Regular text area (fallback or default)
    query = st.text_area(
        "Enter SQL Query",
        height=height,
        placeholder=placeholder,
        key=key,
        help="💡 Use sidebar to insert table names"
    )
    return query



