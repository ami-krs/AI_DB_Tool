"""Navigation and connection handling functions"""
import streamlit as st
from pathlib import Path

from config.database_config import get_persistent_sqlite_path, save_db_config
from utils.helpers import get_api_key

from ai_db_tool.connectors import DatabaseConfig
from ai_db_tool.ai import AIQueryBuilder, SQLChatbot


def handle_connection(db_type, host, port, database, username, password):
    """Handle database connection logic"""
    # Warn if using /tmp/ for SQLite (will be wiped on restart)
    if db_type == "sqlite" and "/tmp/" in database:
        st.warning("⚠️ Using /tmp/ for SQLite database will be wiped on system restart! Use a persistent location like ~/.ai_db_tool/database.sqlite")
    
    if db_type == "sqlite":
        # ALWAYS use persistent path in project directory for SQLite to ensure consistency
        # This prevents connecting to different DB files due to working directory changes
        persistent_path = get_persistent_sqlite_path()  # Returns absolute path string
        database = persistent_path  # Force use of persistent path in project directory
        
        # Ensure directory exists for SQLite file
        db_path = Path(persistent_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Debug: Log the path and file status
        print(f"DEBUG: handle_connection - Using database path: {persistent_path}")
        print(f"DEBUG: handle_connection - Path exists: {db_path.exists()}")
        if db_path.exists():
            try:
                file_size = db_path.stat().st_size
                print(f"DEBUG: handle_connection - File size: {file_size} bytes")
            except Exception as e:
                print(f"DEBUG: handle_connection - Could not get file size: {e}")
        
        config = DatabaseConfig(
            db_type=db_type,
            host="",
            port=0,
            database=persistent_path,  # Already absolute path from get_persistent_sqlite_path()
            username="",
            password="",
            extra_params=None
        )
    else:
        # For NeonDB and other cloud databases, add connection parameters for persistence
        extra_params = {}
        if db_type == "postgresql" and "neon" in host.lower():
            # NeonDB-specific parameters for better persistence
            extra_params = {
                'sslmode': 'require',
                'connect_timeout': '10',
                'application_name': 'ai_db_tool'
            }
        
        config = DatabaseConfig(
            db_type=db_type,
            host=host,
            port=int(port),
            database=database,
            username=username,
            password=password,
            extra_params=extra_params if extra_params else None
        )
        
    try:
        if st.session_state.db_manager.connect(config):
            # Save connection config for persistence
            save_db_config(config)
            
            st.success("✅ Connected successfully! Connection saved for next session.")
            st.session_state.connected = True
            st.session_state.db_type = config.db_type
            
            # Get table names directly first (more reliable)
            tables = st.session_state.db_manager.get_tables()
            
            # Get full database info
            try:
                schema_info = st.session_state.db_manager.get_database_info()
                if schema_info:
                    # Ensure 'tables' contains table names (strings), not schema objects
                    # get_database_info() returns schema objects, but we need names
                    if tables and isinstance(tables[0] if tables else None, str):
                        # Use table names directly if available
                        schema_info['tables'] = tables
                    elif schema_info.get('tables') and isinstance(schema_info['tables'][0] if schema_info['tables'] else None, dict):
                        # Extract table names from schema objects
                        schema_info['tables'] = [t.get('table_name', str(t)) if isinstance(t, dict) else str(t) for t in schema_info['tables']]
                    else:
                        schema_info['tables'] = tables or []
                    
                    schema_info['db_type'] = config.db_type
                    schema_info['total_tables'] = len(tables) if tables else 0
                    st.session_state.schema_info = schema_info
                else:
                    # If get_database_info returns None, use table names directly
                    st.session_state.schema_info = {
                        'tables': tables or [],
                        'db_type': config.db_type,
                        'total_tables': len(tables) if tables else 0,
                        'database_name': config.database
                    }
            except:
                # If get_database_info fails, use table names directly
                st.session_state.schema_info = {
                    'tables': tables or [],
                    'db_type': config.db_type,
                    'total_tables': len(tables) if tables else 0,
                    'database_name': config.database
                }
            
            # Initialize AI components
            try:
                openai_key = get_api_key("OPENAI_API_KEY")
                anthropic_key = get_api_key("ANTHROPIC_API_KEY")
                api_key = openai_key or anthropic_key
                
                if not api_key:
                    st.info("ℹ️ AI features are disabled. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in Streamlit secrets to enable AI chatbot and query generation.")
                    st.session_state.chatbot = None
                    st.session_state.query_builder = None
                else:
                    provider = "openai" if openai_key else "anthropic" if anthropic_key else "openai"
                    st.session_state.chatbot = SQLChatbot(api_key=api_key, provider=provider)
                    st.session_state.query_builder = AIQueryBuilder(api_key=api_key, provider=provider)
                    
                    if (st.session_state.chatbot and 
                        hasattr(st.session_state.chatbot, 'client') and
                        st.session_state.chatbot.client is not None):
                        st.session_state.chatbot.set_schema_context(schema_info)
            except Exception as e:
                st.session_state.chatbot = None
                st.session_state.query_builder = None
                st.warning(f"⚠️ AI features unavailable: {e}. Database operations will still work.")
            
            st.session_state.active_setting = None
            st.rerun()
        else:
            st.error("❌ Connection failed!")
            st.session_state.connected = False
    except Exception as e:
        st.error(f"❌ Connection error: {str(e)}")
        import traceback
        st.exception(e)
        st.session_state.connected = False



def render_navigation_bar():
    """Render dropdown navigation bar using Streamlit selectbox styled as dropdown"""
    
    # Get current section label
    section_labels = {
        'home': '🏠 Home',
        'chatbot': '💬 AI SQL Assistant',
        'sql_editor': '📝 Smart SQL Editor',
        'data_explorer': '🔍 Data Explorer',
        'visualizations': '📊 Data Visualizations',
        'smart_email_agent': '📧 Smart Email Agent'
    }
    
    # Get options and current index
    options = list(section_labels.keys())
    labels = [section_labels[k] for k in options]
    
    try:
        current_index = options.index(st.session_state.active_section)
    except ValueError:
        current_index = 0
    
    # Use Streamlit selectbox - this is reliable and works with Streamlit's state
    selected_label = st.selectbox(
        "Select Section",
        options=labels,
        index=current_index,
        key="nav_dropdown_selectbox",
        label_visibility="collapsed"
    )
    
    # Update active section if selection changed
    selected_section = options[labels.index(selected_label)] if selected_label in labels else options[0]
    if selected_section != st.session_state.active_section:
        st.session_state.active_section = selected_section
        st.rerun()
    
    # Style the selectbox to look like a compact dropdown button
    # Use JavaScript to find and style the selectbox since CSS :has() might not work
    st.markdown("""
    <style>
    /* Style selectbox to look like a navigation dropdown button */
    .nav-selectbox-styled > div > div {
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
    .nav-selectbox-styled > div > div:hover {
        background-color: #14a085 !important;
    }
    .nav-selectbox-styled > div > div > div {
        color: white !important;
    }
    .nav-selectbox-styled > div > div > div > svg {
        fill: white !important;
    }
    </style>
    <script>
    (function() {
        function styleNavSelectbox() {
            const selectboxes = document.querySelectorAll('div[data-testid="stSelectbox"]');
            selectboxes.forEach(function(selectbox) {
                const label = selectbox.querySelector('label');
                if (label && label.getAttribute('for') && label.getAttribute('for').includes('nav_dropdown')) {
                    selectbox.classList.add('nav-selectbox-styled');
                }
            });
        }
        styleNavSelectbox();
        setTimeout(styleNavSelectbox, 100);
        setTimeout(styleNavSelectbox, 500);
        const observer = new MutationObserver(styleNavSelectbox);
        observer.observe(document.body, { childList: true, subtree: true });
    })();
    </script>
    """, unsafe_allow_html=True)


