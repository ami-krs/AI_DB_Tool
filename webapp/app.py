"""
Streamlit Web UI for AI Database Tool
Provides interactive interface for database management and AI-powered SQL queries
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List
import os

# Try to import sqlparse, fallback to simple split if not available
try:
    import sqlparse
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_db_tool.connectors import DatabaseManager, DatabaseConfig
from ai_db_tool.ai import AIQueryBuilder, SQLChatbot


# Page configuration
st.set_page_config(
    page_title="AI Database Tool",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better table display
st.markdown("""
<style>
    /* Force better column display in dataframes */
    div[data-testid="stDataFrame"] {
        width: 100% !important;
    }
    
    /* Ensure table takes full width */
    div[data-testid="stDataFrame"] table {
        width: 100% !important;
        table-layout: auto !important;
    }
    
    /* Set minimum column width */
    div[data-testid="stDataFrame"] th {
        min-width: 120px !important;
        max-width: none !important;
    }
    
    div[data-testid="stDataFrame"] td {
        min-width: 120px !important;
        max-width: none !important;
    }
    
    /* Improve horizontal scrolling */
    div[data-testid="stDataFrame"] > div {
        overflow-x: auto !important;
    }
    
    /* Better container width */
    .element-container {
        width: 100% !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
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
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'fixed_query' not in st.session_state:
    st.session_state.fixed_query = None
if 'layout_mode' not in st.session_state:
    st.session_state.layout_mode = 'three_column'  # or 'tabs'
if 'last_quick_select' not in st.session_state:
    st.session_state.last_quick_select = "-- Select --"
if 'show_db_info' not in st.session_state:
    st.session_state.show_db_info = False  # Minimize by default
if 'show_chatbot' not in st.session_state:
    st.session_state.show_chatbot = True  # Show chatbot by default
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False  # Light mode by default
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1
if 'rows_per_page' not in st.session_state:
    st.session_state.rows_per_page = 100


def display_paginated_dataframe(df):
    """Display dataframe with pagination controls"""
    if df is None or len(df) == 0:
        st.info("No data to display")
        return
    
    total_rows = len(df)
    total_pages = (total_rows - 1) // st.session_state.rows_per_page + 1
    
    # Ensure current_page is valid
    if st.session_state.current_page > total_pages:
        st.session_state.current_page = 1
    if st.session_state.current_page < 1:
        st.session_state.current_page = 1
    
    # Calculate pagination
    start_idx = (st.session_state.current_page - 1) * st.session_state.rows_per_page
    end_idx = min(start_idx + st.session_state.rows_per_page, total_rows)
    
    # Display pagination info (using markdown to avoid column nesting issues)
    st.markdown(f"**Total Rows:** {total_rows:,} | **Page:** {st.session_state.current_page} of {total_pages} | **Showing:** {start_idx + 1:,} - {end_idx:,}")
    
    # Rows per page selector
    rows_per_page_options = [50, 100, 250, 500, 1000]
    new_rows_per_page = st.selectbox(
        "Rows per page:",
        options=rows_per_page_options,
        index=rows_per_page_options.index(st.session_state.rows_per_page) if st.session_state.rows_per_page in rows_per_page_options else 1,
        key="rows_per_page_select"
    )
    if new_rows_per_page != st.session_state.rows_per_page:
        st.session_state.rows_per_page = new_rows_per_page
        st.session_state.current_page = 1  # Reset to first page
        st.rerun()
    
    # Pagination controls (NO COLUMNS to prevent nesting issues when called from within columns)
    if total_pages > 1:
        # Create unique keys for each button to avoid conflicts
        button_key_prefix = f"pagination_{id(df)}"
        
        st.markdown("**Navigation:**")
        
        # Use HTML/CSS for horizontal button layout to avoid column nesting
        st.markdown("""
        <style>
            .pagination-buttons {
                display: flex;
                gap: 10px;
                align-items: center;
                margin: 10px 0;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Navigation buttons in a simple row (no columns)
        button_container = st.container()
        with button_container:
            # Use a simple approach: buttons in a row without columns
            # We'll use st.button with custom layout via CSS or just vertical layout
            nav_buttons = []
            
            if st.button("⏮️ First", disabled=(st.session_state.current_page == 1), key=f"{button_key_prefix}_first"):
                st.session_state.current_page = 1
                st.rerun()
            
            if st.button("◀️ Prev", disabled=(st.session_state.current_page == 1), key=f"{button_key_prefix}_prev"):
                st.session_state.current_page -= 1
                st.rerun()
            
            # Page number input
            page_input = st.number_input(
                "Go to page:",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.current_page,
                key=f"{button_key_prefix}_input"
            )
            if page_input != st.session_state.current_page:
                st.session_state.current_page = int(page_input)
                st.rerun()
            
            if st.button("Next ▶️", disabled=(st.session_state.current_page == total_pages), key=f"{button_key_prefix}_next"):
                st.session_state.current_page += 1
                st.rerun()
            
            if st.button("Last ⏭️", disabled=(st.session_state.current_page == total_pages), key=f"{button_key_prefix}_last"):
                st.session_state.current_page = total_pages
                st.rerun()
    
    # Display paginated data
    paginated_df = df.iloc[start_idx:end_idx]
    st.dataframe(paginated_df, hide_index=True, use_container_width=True)
    
    # Show info if paginated
    if total_pages > 1:
        st.caption(f"📄 Displaying page {st.session_state.current_page} of {total_pages} ({len(paginated_df):,} rows)")


def inject_dark_mode_css():
    """Inject dark mode CSS"""
    if st.session_state.dark_mode:
        st.markdown("""
        <style>
            /* Dark mode styles */
            .stApp {
                background-color: #0E1117;
                color: #FAFAFA;
            }
            
            /* Sidebar dark mode */
            [data-testid="stSidebar"] {
                background-color: #1E1E1E;
            }
            
            /* Text colors */
            h1, h2, h3, h4, h5, h6, p, label, span {
                color: #FAFAFA !important;
            }
            
            /* Input fields */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > select {
                background-color: #262730;
                color: #FAFAFA;
                border-color: #3E3E3E;
            }
            
            /* Buttons */
            .stButton > button {
                background-color: #262730;
                color: #FAFAFA;
                border-color: #3E3E3E;
            }
            
            .stButton > button:hover {
                background-color: #3E3E3E;
                border-color: #4E4E4E;
            }
            
            /* Dataframes */
            .dataframe {
                background-color: #1E1E1E;
                color: #FAFAFA;
            }
            
            .dataframe th {
                background-color: #262730;
                color: #FAFAFA;
            }
            
            .dataframe td {
                background-color: #1E1E1E;
                color: #FAFAFA;
            }
            
            /* Code blocks */
            .stCodeBlock {
                background-color: #1E1E1E;
            }
            
            /* Expanders */
            .streamlit-expanderHeader {
                background-color: #262730;
                color: #FAFAFA;
            }
            
            /* Info boxes */
            .stInfo {
                background-color: #1E3A5F;
                color: #FAFAFA;
            }
            
            .stSuccess {
                background-color: #1E5F3A;
                color: #FAFAFA;
            }
            
            .stWarning {
                background-color: #5F3A1E;
                color: #FAFAFA;
            }
            
            .stError {
                background-color: #5F1E1E;
                color: #FAFAFA;
            }
            
            /* Chat messages */
            [data-testid="stChatMessage"] {
                background-color: #262730;
            }
            
            /* Selectbox dropdown */
            .stSelectbox > div > div > select {
                background-color: #262730;
                color: #FAFAFA;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light mode - minimal override to ensure clean light theme
        st.markdown("""
        <style>
            /* Light mode - use Streamlit defaults */
            .stApp {
                background-color: #FFFFFF;
            }
        </style>
        """, unsafe_allow_html=True)


def main():
    """Main application"""
    
    # Inject dark mode CSS (must be called early)
    inject_dark_mode_css()
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 AI Database Tool")
        
        # Dark mode toggle
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**Theme:**")
        with col2:
            dark_mode_toggle = st.toggle(
                "🌙",
                value=st.session_state.dark_mode,
                key="dark_mode_toggle",
                help="Toggle dark mode"
            )
            if dark_mode_toggle != st.session_state.dark_mode:
                st.session_state.dark_mode = dark_mode_toggle
                st.rerun()
        
        st.markdown("---")
        
        # Layout toggle
        st.header("📐 Layout")
        layout_mode = st.radio(
            "Choose layout:",
            ["Three Column (Default)", "Tabs (Classic)"],
            index=0 if st.session_state.layout_mode == 'three_column' else 1,
            key="layout_radio"
        )
        st.session_state.layout_mode = 'three_column' if layout_mode == "Three Column (Default)" else 'tabs'
        st.markdown("---")
        
        # Connection section
        st.header("🔌 Database Connection")
        
        db_type = st.selectbox(
            "Database Type",
            ["postgresql", "mysql", "sqlserver", "oracle", "sqlite"]
        )
        
        with st.form("connection_form"):
            host = st.text_input("Host", value="localhost")
            port = st.number_input("Port", value=5432 if db_type == "postgresql" else 3306)
            database = st.text_input("Database Name")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            connect_button = st.form_submit_button("Connect", type="primary")
        
        if connect_button:
            config = DatabaseConfig(
                db_type=db_type,
                host=host,
                port=int(port),
                database=database,
                username=username,
                password=password,
            )
            
            if st.session_state.db_manager.connect(config):
                st.success("✅ Connected successfully!")
                st.session_state.connected = True
                
                # Store database type
                st.session_state.db_type = config.db_type
                
                # Initialize AI components
                st.session_state.chatbot = SQLChatbot()
                st.session_state.query_builder = AIQueryBuilder()
                
                # Set schema context for chatbot with db_type awareness
                schema_info = st.session_state.db_manager.get_database_info()
                schema_info['db_type'] = config.db_type
                st.session_state.chatbot.set_schema_context(schema_info)
                
                # Store schema for later use
                st.session_state.schema_info = schema_info
            else:
                st.error("❌ Connection failed!")
                st.session_state.connected = False
        
        if st.session_state.connected:
            if st.button("Disconnect"):
                st.session_state.db_manager.disconnect()
                st.session_state.connected = False
                st.session_state.chatbot = None
                st.session_state.query_builder = None
                st.success("Disconnected")
                st.rerun()
        
        st.markdown("---")
    
    # Main content area
    if st.session_state.layout_mode == 'three_column' and st.session_state.connected:
        # Minimized header for three column layout when connected
        col1, col2, col3 = st.columns([1, 8, 1])
        with col2:
            st.markdown("#### 🤖 AI Database Tool")
    else:
        st.title("🤖 AI Database Tool")
        st.markdown("Intelligent database management with AI-powered SQL generation")
    
    if not st.session_state.connected:
        st.info("👈 Connect to a database using the sidebar to get started")
    else:
        # Choose layout based on user preference
        if st.session_state.layout_mode == 'three_column':
            three_column_layout()
        else:
            # Classic tabs layout
            tab1, tab2, tab3, tab4 = st.tabs([
                "💬 AI Chatbot",
                "📝 SQL Editor",
                "🔍 Data Explorer",
                "📊 Visualizations"
            ])
            
            with tab1:
                chatbot_tab()
            
            with tab2:
                sql_editor_tab()
            
            with tab3:
                data_explorer_tab()
            
            with tab4:
                visualizations_tab()


def three_column_layout():
    """Three column layout: Left=Info, Middle=Editor, Right=Chatbot"""
    # Adjust column widths based on what's visible
    if st.session_state.show_db_info and st.session_state.show_chatbot:
        col_left, col_mid, col_right = st.columns([1, 3, 1.5])
    elif st.session_state.show_db_info:
        col_left, col_mid, col_right = st.columns([1, 3, 1.5])
    elif st.session_state.show_chatbot:
        col_left, col_mid, col_right = st.columns([1, 3, 1.5])
    else:
        col_left, col_mid, col_right = st.columns([1, 3, 1.5])
    
    # Left Column: Database Info & Tools (toggleable)
    if col_left:
        with col_left:
            # Smart Help at the top
            if st.session_state.connected:
                st.markdown("**💡 Smart Help**")
                if st.button("📋 Show Tables", use_container_width=True):
                    show_table_details()
                if st.button("❓ Common Queries", use_container_width=True):
                    show_common_queries()
                st.markdown("---")
            
            # Toggle button
            if st.button("🗄️" if not st.session_state.show_db_info else "🗄️ ▼"):
                st.session_state.show_db_info = not st.session_state.show_db_info
                st.rerun()
            
            # Collapsible Database Info (optional, can be removed entirely if not needed)
            if st.session_state.show_db_info:
                if st.session_state.connected:
                    st.info("🗄️ Database connected")
                else:
                    st.info("Connect to a database")
            
            # Always-visible Tools section
            st.markdown("**🔧 Tools**")
            with st.expander("🔍 Data Explorer"):
                data_explorer_compact()
            with st.expander("📊 Quick Charts"):
                visualizations_compact()
    
    # Middle Column: SQL Editor
    with col_mid:
        sql_editor_compact()
    
    # Right Column: AI Chatbot (toggleable)
    if col_right:
        with col_right:
            # Toggle button
            if st.button("💬" if not st.session_state.show_chatbot else "💬 ▼"):
                st.session_state.show_chatbot = not st.session_state.show_chatbot
                st.rerun()
            
            if st.session_state.show_chatbot:
                chatbot_compact()
            else:
                st.info("Click 💬 to show AI Assistant")


def chatbot_compact():
    """Compact chatbot for three column layout"""
    st.markdown("### 💬 AI Assistant")
    
    # Display chat history
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history[-5:]:  # Show last 5 messages
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                st.chat_message("assistant").write(msg['content'])
                if 'sql_query' in msg and msg['sql_query']:
                    st.code(msg['sql_query'], language='sql')
    else:
        st.info("Ask questions about your database")
    
    # Chat input
    user_input = st.chat_input("Ask about your database...")
    
    if user_input and st.session_state.chatbot:
        # Add user message to history
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        # Get AI response
        with st.spinner("🤔 Thinking..."):
            response = st.session_state.chatbot.chat(user_input, include_sql=True)
        
        if 'error' not in response:
            # Add assistant response to history
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response['response'],
                'sql_query': response.get('sql_query'),
                'timestamp': response['timestamp']
            })
            st.rerun()
        else:
            st.error(response['error'])


def sql_editor_compact():
    """Compact SQL editor for three column layout"""
    st.markdown("### 📝 SQL Editor")
    
    # Quick insert buttons for tables
    if st.session_state.connected:
        tables = st.session_state.db_manager.get_tables()
        if tables:
            selected_table = st.selectbox(
                "📋 Quick Insert Table", 
                ["-- Select --"] + tables[:10], 
                key="quick_select",
                index=0
            )
            
            # Check if selection changed
            if selected_table != st.session_state.last_quick_select:
                if selected_table and selected_table != "-- Select --":
                    current_query = st.session_state.get('sql_editor', '')
                    st.session_state.sql_editor = current_query + f" {selected_table} "
                st.session_state.last_quick_select = selected_table
                st.rerun()
    
    # Update sql_editor if fixed_query exists
    if st.session_state.fixed_query:
        st.session_state.sql_editor = st.session_state.fixed_query
        st.session_state.fixed_query = None
    
    query = st.text_area(
        "Enter SQL Query",
        height=250,
        placeholder="SELECT * FROM table_name LIMIT 10;",
        key="sql_editor",
        help="💡 Use sidebar to insert table names"
    )
    
    # Action buttons in row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("▶️ Run", type="primary", use_container_width=True):
            execute_query(query)
    with col2:
        if st.button("🤖 AI Gen", use_container_width=True):
            generate_sql_query()
    with col3:
        if st.button("🚀 AI Opt", use_container_width=True):
            optimize_query(query)
    with col4:
        if st.button("🔧 Fix", use_container_width=True):
            debug_query(query)
    with col5:
        if st.button("💾 Save", use_container_width=True):
            save_query_to_history(query)
    
    # Query history
    if st.session_state.query_history:
        with st.expander("📚 Query History"):
            for i, q in enumerate(reversed(st.session_state.query_history[-10:])):
                st.code(q, language='sql')
                if st.button("📋 Copy", key=f"copy_compact_{i}"):
                    st.session_state.sql_editor = q
                    st.rerun()


def data_explorer_compact():
    """Compact data explorer"""
    try:
        tables = st.session_state.db_manager.get_tables()
        if tables:
            selected_table = st.selectbox("Select table", tables, key="explorer_table")
            
            if selected_table:
                # Quick preview
                preview_query = f"SELECT * FROM {selected_table} LIMIT 100"
                
                if st.button("📊 Load Preview", use_container_width=True):
                    try:
                        df = st.session_state.db_manager.execute_query(preview_query)
                        st.dataframe(df, use_container_width=True)
                        st.session_state.last_result = df
                    except Exception as e:
                        st.error(f"Error: {e}")
    except Exception as e:
        st.error(f"Error: {e}")


def visualizations_compact():
    """Compact visualizations"""
    if st.session_state.get('last_result') is not None:
        df = st.session_state.last_result
        
        if len(df.columns) >= 2:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                selected_col = st.selectbox("Column", numeric_cols, key="viz_col")
                st.bar_chart(df[selected_col].head(20))
    else:
        st.info("Execute a query to see charts")


def chatbot_tab():
    """AI Chatbot interface"""
    st.header("💬 AI SQL Assistant")
    st.markdown("Ask questions in natural language and get SQL queries generated automatically")
    
    # Display chat history
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            st.chat_message("user").write(msg['content'])
        else:
            st.chat_message("assistant").write(msg['content'])
            if 'sql_query' in msg and msg['sql_query']:
                with st.expander("View Generated SQL"):
                    st.code(msg['sql_query'], language='sql')
                    if st.button(f"Execute Query", key=f"exec_{msg['timestamp']}"):
                        execute_generated_query(msg['sql_query'])
    
    # Chat input
    user_input = st.chat_input("Ask me anything about your database...")
    
    if user_input and st.session_state.chatbot:
        # Add user message to history
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        
        # Get AI response
        with st.spinner("🤔 Thinking..."):
            response = st.session_state.chatbot.chat(user_input, include_sql=True)
        
        if 'error' not in response:
            # Add assistant response to history
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response['response'],
                'sql_query': response.get('sql_query'),
                'timestamp': response['timestamp']
            })
            st.rerun()
        else:
            st.error(response['error'])


def sql_editor_tab():
    """SQL Editor interface"""
    st.header("📝 Smart SQL Editor")
    
    # Quick insert buttons for tables
    if st.session_state.connected:
        tables = st.session_state.db_manager.get_tables()
        if tables:
            st.markdown("**📋 Quick Insert:**")
            cols = st.columns(min(6, len(tables) + 1))
            with cols[0]:
                if st.button("📋 Table List", use_container_width=True):
                    st.session_state.show_table_list = not st.session_state.get('show_table_list', False)
            for i, table in enumerate(tables[:5], 1):
                with cols[i % len(cols)]:
                    if st.button(f"📊 {table}", key=f"insert_{table}", use_container_width=True):
                        # Insert table name at cursor position
                        current_query = st.session_state.get('sql_editor', '')
                        st.session_state.sql_editor = current_query + f" {table} "
                        st.rerun()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Show table list if requested
        if st.session_state.get('show_table_list', False) and st.session_state.connected:
            with st.expander("📊 Available Tables", expanded=True):
                tables = st.session_state.db_manager.get_tables()
                for i, table in enumerate(tables):
                    if st.button(f"📋 {table}", key=f"table_btn_{i}", use_container_width=True):
                        st.session_state.sql_editor = st.session_state.get('sql_editor', '') + f"{table}"
                        st.session_state.show_table_list = False
                        st.rerun()
        
        # Update sql_editor if fixed_query exists
        if st.session_state.fixed_query:
            st.session_state.sql_editor = st.session_state.fixed_query
            st.session_state.fixed_query = None
        
        query = st.text_area(
            "Enter SQL Query",
            height=300,
            placeholder="SELECT * FROM table_name LIMIT 10;",
            key="sql_editor",
            help="💡 Tip: Use the Quick Insert buttons above to insert table names"
        )
    
    with col2:
        st.markdown("### Actions")
        
        if st.button("▶️ Execute", type="primary", use_container_width=True):
            execute_query(query)
        
        if st.button("🤖 AI Generate", use_container_width=True):
            generate_sql_query()
        
        if st.button("🔧 AI Optimize", use_container_width=True):
            optimize_query(query)
        
        if st.button("🐛 AI Debug", use_container_width=True):
            debug_query(query)
        
        if st.button("💾 Save to History", use_container_width=True):
            save_query_to_history(query)
        
        # Smart suggestions
        if st.session_state.connected:
            st.markdown("---")
            st.markdown("### 💡 Smart Help")
            if st.button("📋 Show Tables", use_container_width=True):
                show_table_details()
            if st.button("❓ Common Queries", use_container_width=True):
                show_common_queries()
    
    # Query history
    if st.session_state.query_history:
        with st.expander("📚 Query History"):
            for i, q in enumerate(reversed(st.session_state.query_history[-10:])):
                st.code(q, language='sql')
                if st.button("📋 Copy", key=f"copy_{i}"):
                    st.code(q, language='sql')
                st.markdown("---")


def data_explorer_tab():
    """Data explorer interface"""
    st.header("🔍 Data Explorer")
    
    if st.session_state.connected:
        try:
            tables = st.session_state.db_manager.get_tables()
            
            selected_table = st.selectbox("Select a table", tables)
            
            if selected_table:
                # Show schema
                schema = st.session_state.db_manager.get_table_schema(selected_table)
                
                st.subheader(f"Schema: {selected_table}")
                
                # Display columns
                col_df = pd.DataFrame(schema['columns'])
                st.dataframe(col_df, use_container_width=True)
                
                # Quick query
                st.subheader("Quick Preview")
                preview_query = f"SELECT * FROM {selected_table} LIMIT 100"
                
                if st.button("Load Preview"):
                    with st.spinner("Loading data..."):
                        try:
                            df = st.session_state.db_manager.execute_query(preview_query)
                            st.dataframe(df, use_container_width=True)
                            
                            # Statistics
                            st.subheader("Statistics")
                            st.dataframe(df.describe(), use_container_width=True)
                        except Exception as e:
                            st.error(f"Error loading data: {e}")
        except Exception as e:
            st.error(f"Error: {e}")


def visualizations_tab():
    """Data visualization interface"""
    st.header("📊 Data Visualizations")
    
    # This will be populated with results from executed queries
    if 'last_result_df' in st.session_state:
        df = st.session_state.last_result_df
        
        st.subheader("Data Preview")
        st.dataframe(df.head(20), use_container_width=True)
        
        # Basic visualizations
        if len(df.columns) >= 2:
            col1, col2 = st.columns(2)
            
            with col1:
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    selected_col = st.selectbox("Select column for chart", numeric_cols)
                    st.bar_chart(df[selected_col].head(20))
            
            with col2:
                if len(df.columns) >= 2:
                    x_col = st.selectbox("X-axis", df.columns)
                    y_col = st.selectbox("Y-axis", df.columns)
                    st.line_chart(df[[x_col, y_col]].head(20))
    else:
        st.info("👆 Execute a query in the SQL Editor to visualize results here")


def split_sql_statements(query: str) -> List[str]:
    """Split SQL query into individual statements, handling semicolons in strings/comments"""
    if not query.strip():
        return []
    
    # Use sqlparse if available for proper statement splitting
    if SQLPARSE_AVAILABLE:
        try:
            parsed = sqlparse.split(query)
            # Filter out empty statements and strip whitespace
            statements = [stmt.strip() for stmt in parsed if stmt.strip()]
            return statements
        except Exception:
            # Fallback to simple split if sqlparse fails
            pass
    
    # Fallback: simple split by semicolon (handles most cases)
    # Note: This may not handle semicolons inside strings/comments perfectly
    statements = [stmt.strip() for stmt in query.split(';') if stmt.strip()]
    return statements


def execute_single_statement(statement: str) -> Dict[str, Any]:
    """Execute a single SQL statement and return result info"""
    result = {
        'success': False,
        'statement': statement,
        'type': None,
        'rows_affected': 0,
        'rows_retrieved': 0,
        'dataframe': None,
        'error': None
    }
    
    if not statement.strip():
        return result
    
    statement_upper = statement.strip().upper()
    
    # Determine query type
    is_ddl = any(statement_upper.startswith(cmd) for cmd in [
        'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 
        'GRANT', 'REVOKE', 'COMMENT', 'ANALYZE', 'VACUUM'
    ])
    
    is_dml = any(statement_upper.startswith(cmd) for cmd in ['INSERT', 'UPDATE', 'DELETE'])
    is_select = statement_upper.startswith('SELECT')
    
    try:
        if is_ddl or is_dml:
            # Execute non-query operations
            affected_rows = st.session_state.db_manager.execute_non_query(statement)
            result['success'] = True
            result['type'] = 'DDL' if is_ddl else 'DML'
            result['rows_affected'] = affected_rows if affected_rows >= 0 else 0
            return result
        
        elif is_select:
            # Execute SELECT query
            df = st.session_state.db_manager.execute_query(statement)
            result['success'] = True
            result['type'] = 'SELECT'
            result['rows_retrieved'] = len(df)
            result['dataframe'] = df
            return result
        
        else:
            # Unknown query type - try SELECT first, then non-query
            try:
                df = st.session_state.db_manager.execute_query(statement)
                result['success'] = True
                result['type'] = 'SELECT'
                result['rows_retrieved'] = len(df)
                result['dataframe'] = df
                return result
            except:
                # Fallback to non-query execution
                affected_rows = st.session_state.db_manager.execute_non_query(statement)
                result['success'] = True
                result['type'] = 'DML'
                result['rows_affected'] = affected_rows if affected_rows >= 0 else 0
                return result
    
    except Exception as e:
        result['error'] = str(e)
        return result


def execute_query(query: str):
    """Execute SQL query and display results (supports multiple statements, SELECT, INSERT, UPDATE, DELETE, DDL)"""
    if not query.strip():
        st.warning("Please enter a query")
        return
    
    # Split into multiple statements
    statements = split_sql_statements(query)
    
    if not statements:
        st.warning("No valid SQL statements found")
        return
    
    # If single statement, use original behavior for backward compatibility
    if len(statements) == 1:
        single_statement = statements[0]
        result = execute_single_statement(single_statement)
        
        if not result['success']:
            st.error(f"❌ Query execution failed: {result['error']}")
            st.code(single_statement, language='sql')
            return
        
        # Handle single statement results (original behavior)
        if result['type'] == 'SELECT':
            st.subheader("📊 Results")
            st.session_state.current_page = 1
            display_paginated_dataframe(result['dataframe'])
            st.session_state.last_result_df = result['dataframe']
            st.session_state.last_result = result['dataframe']
            
            csv = result['dataframe'].to_csv(index=False)
            st.download_button(
                "📥 Download Full CSV",
                csv,
                "results.csv",
                "text/csv",
                help=f"Download all {len(result['dataframe']):,} rows"
            )
            st.success(f"✅ Query executed successfully! Retrieved {result['rows_retrieved']:,} rows.")
        
        elif result['type'] == 'DDL':
            st.success(f"✅ Database object operation completed successfully!")
            if any(single_statement.strip().upper().startswith(cmd) for cmd in ['CREATE', 'DROP', 'ALTER']):
                st.info("💡 Refresh the page to see updated schema")
        
        else:  # DML
            if result['rows_affected'] >= 0:
                st.success(f"✅ Query executed successfully! {result['rows_affected']} row(s) affected.")
            else:
                st.success(f"✅ Query executed successfully!")
        
        return
    
    # Multiple statements - execute each and show summary
    st.subheader(f"📋 Executing {len(statements)} Statement(s)")
    
    results = []
    success_count = 0
    error_count = 0
    
    for idx, statement in enumerate(statements, 1):
        with st.expander(f"Statement {idx}/{len(statements)}", expanded=(idx == 1)):
            st.code(statement, language='sql')
            
            result = execute_single_statement(statement)
            results.append(result)
            
            if result['success']:
                success_count += 1
                
                if result['type'] == 'SELECT':
                    st.success(f"✅ Statement {idx} executed: Retrieved {result['rows_retrieved']:,} rows")
                    if result['dataframe'] is not None and len(result['dataframe']) > 0:
                        st.session_state.current_page = 1
                        display_paginated_dataframe(result['dataframe'])
                        
                        # Store last result for visualization
                        st.session_state.last_result_df = result['dataframe']
                        st.session_state.last_result = result['dataframe']
                
                elif result['type'] == 'DDL':
                    st.success(f"✅ Statement {idx} executed: DDL operation completed")
                
                else:  # DML
                    st.success(f"✅ Statement {idx} executed: {result['rows_affected']} row(s) affected")
            else:
                error_count += 1
                st.error(f"❌ Statement {idx} failed: {result['error']}")
    
    # Summary
    st.markdown("---")
    st.subheader("📊 Execution Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Statements", len(statements))
    with col2:
        st.metric("✅ Successful", success_count, delta=None)
    with col3:
        st.metric("❌ Failed", error_count, delta=None, delta_color="inverse")
    
    if success_count == len(statements):
        st.success(f"🎉 All {len(statements)} statement(s) executed successfully!")
    elif success_count > 0:
        st.warning(f"⚠️ {success_count} statement(s) succeeded, {error_count} statement(s) failed")
    else:
        st.error(f"❌ All statements failed to execute")
    
    # Show last SELECT result if available
    last_select_result = None
    for result in reversed(results):
        if result['success'] and result['type'] == 'SELECT' and result['dataframe'] is not None:
            last_select_result = result['dataframe']
            break
    
    if last_select_result is not None:
        st.markdown("---")
        st.subheader("📊 Last Query Results")
        st.session_state.current_page = 1
        display_paginated_dataframe(last_select_result)
        
        csv = last_select_result.to_csv(index=False)
        st.download_button(
            "📥 Download Full CSV",
            csv,
            "results.csv",
            "text/csv",
            help=f"Download all {len(last_select_result):,} rows"
        )


def execute_generated_query(query: str):
    """Execute AI-generated query"""
    execute_query(query)


def show_table_details():
    """Show detailed table information"""
    if not st.session_state.connected:
        st.warning("Please connect to a database first")
        return
    
    tables = st.session_state.db_manager.get_tables()
    if not tables:
        st.info("No tables found in the database")
        return
    
    selected_table = st.selectbox("Select a table to view details", tables)
    
    if selected_table:
        schema = st.session_state.db_manager.get_table_schema(selected_table)
        
        st.markdown(f"### 📊 Schema: `{selected_table}`")
        
        # Display columns
        df_cols = pd.DataFrame(schema['columns'])
        st.dataframe(df_cols, use_container_width=True)
        
        # Show primary keys
        if schema.get('primary_keys'):
            st.markdown(f"**Primary Keys:** {', '.join(schema['primary_keys'])}")
        
        # Show foreign keys
        if schema.get('foreign_keys'):
            st.markdown("**Foreign Keys:**")
            for fk in schema['foreign_keys']:
                st.markdown(f"- {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")


def show_common_queries():
    """Show common query templates"""
    if not st.session_state.connected:
        st.warning("Please connect to a database first")
        return
    
    db_type = st.session_state.get('db_type', 'sqlite')
    tables = st.session_state.db_manager.get_tables()
    
    if not tables:
        st.info("No tables found")
        return
    
    selected_table = st.selectbox("Select a table", tables)
    
    # Get schema to provide accurate examples
    try:
        schema = st.session_state.db_manager.get_table_schema(selected_table)
        columns = [col['name'] for col in schema.get('columns', [])[:5]]  # First 5 columns
        columns_str = ', '.join(columns)
    except:
        columns_str = "column1, column2, column3"
    
    common_queries = [
        ("📊 SELECT - View All Rows", f"SELECT * FROM {selected_table} LIMIT 100;"),
        ("📊 SELECT - Count Rows", f"SELECT COUNT(*) FROM {selected_table};"),
        ("📊 SELECT - Top 10", f"SELECT * FROM {selected_table} LIMIT 10;"),
        ("➕ INSERT - Add New Row", f"INSERT INTO {selected_table} ({columns_str}) VALUES ('value1', 'value2', 'value3');"),
        ("✏️ UPDATE - Modify Data", f"UPDATE {selected_table} SET {columns[0] if columns else 'column1'} = 'new_value' WHERE condition;"),
        ("🗑️ DELETE - Remove Rows", f"DELETE FROM {selected_table} WHERE condition;"),
    ]
    
    # Add DDL examples
    st.markdown("---")
    st.markdown("**📊 Common Query Patterns:**")
    for name, query in common_queries:
        with st.expander(f"📝 {name}"):
            st.code(query, language='sql')
            if st.button(f"📋 Use This Query", key=f"common_{name}_{selected_table}"):
                st.session_state.sql_editor = query
                st.rerun()
    
    st.markdown("---")
    st.markdown("**🏗️ Database Management (DDL):**")
    
    # Get column details for CREATE TABLE example
    try:
        if schema and schema.get('columns'):
            col_defs = []
            for col in schema['columns'][:3]:  # First 3 columns
                col_name = col['name']
                col_type = col['type']
                if 'INTEGER' in str(col_type).upper():
                    col_type = 'INTEGER'
                elif 'TEXT' in str(col_type).upper() or 'VARCHAR' in str(col_type).upper():
                    col_type = 'TEXT'
                else:
                    col_type = 'TEXT'
                col_defs.append(f"{col_name} {col_type}")
            sample_cols = ', '.join(col_defs[:2])  # First 2 columns for example
        else:
            sample_cols = "id INTEGER, name TEXT"
    except:
        sample_cols = "id INTEGER PRIMARY KEY, name TEXT"
    
    ddl_queries = [
        ("🏗️ CREATE - New Table", f"CREATE TABLE new_table ({sample_cols});"),
        ("🏗️ CREATE - Index", f"CREATE INDEX idx_name ON {selected_table} (column_name);"),
        ("🏗️ CREATE - View", f"CREATE VIEW my_view AS SELECT * FROM {selected_table} WHERE condition;"),
        ("🗑️ DROP - Delete Table", f"DROP TABLE table_name;"),
        ("🔧 ALTER - Add Column", f"ALTER TABLE {selected_table} ADD COLUMN new_column TEXT;"),
    ]
    
    for name, query in ddl_queries:
        with st.expander(f"🏗️ {name}"):
            st.code(query, language='sql')
            if st.button(f"📋 Use This Query", key=f"ddl_{name}"):
                st.session_state.sql_editor = query
                st.rerun()


def generate_sql_query():
    """Generate SQL query using AI"""
    st.info("Enter your question in the AI Chatbot tab to generate SQL")


def optimize_query(query: str):
    """Optimize query using AI"""
    if not query.strip() or not st.session_state.query_builder:
        st.warning("Please enter a query first")
        return
    
    try:
        with st.spinner("🤖 Optimizing query..."):
            optimized = st.session_state.query_builder.optimize_query(query)
        st.subheader("Optimized Query")
        st.code(optimized, language='sql')
    except Exception as e:
        st.error(f"Optimization failed: {e}")


def debug_query(query: str):
    """Debug query using AI"""
    if not query.strip():
        st.warning("Please enter a query first")
        return
    
    if not st.session_state.connected:
        st.error("Please connect to a database first")
        return
    
    # Try to execute the query first to get the error
    error_message = None
    try:
        # Try to execute the query
        df = st.session_state.db_manager.execute_query(query)
        # If successful, no debug needed
        st.success("✅ Query is valid and executes successfully!")
        st.info(f"Retrieved {len(df)} rows. No errors to debug.")
        return
    except Exception as e:
        # Got an error - now we can debug it
        error_message = str(e)
        st.error(f"❌ Query Error Detected:\n{error_message}")
    
    # Use AI to debug the error
    if error_message and st.session_state.query_builder:
        with st.spinner("🤖 AI is analyzing the error..."):
            try:
                # Pass schema context for better debugging
                schema_info = st.session_state.get('schema_info', {})
                if schema_info:
                    # Create a context string for AI
                    schema_context = f"Database type: {st.session_state.db_type}\n\nTables:\n"
                    for table in schema_info.get('tables', []):
                        table_name = table.get('table_name', 'unknown')
                        columns = ', '.join([col['name'] for col in table.get('columns', [])])
                        schema_context += f"- {table_name}: {columns}\n"
                    
                    debugged_query = st.session_state.query_builder.debug_query(query, error_message, schema_context)
                else:
                    debugged_query = st.session_state.query_builder.debug_query(query, error_message)
                
                st.markdown("### 🔧 AI Debug Suggestions:")
                
                # Split the response into explanation and fixed query
                if "```sql" in debugged_query:
                    parts = debugged_query.split("```sql")
                    explanation = parts[0].strip()
                    sql_part = parts[1].split("```")[0].strip() if len(parts) > 1 else ""
                    
                    if explanation:
                        st.markdown(explanation)
                    
                    if sql_part:
                        st.markdown("**Suggested Fixed Query:**")
                        st.code(sql_part, language='sql')
                        
                        # Use a form to handle the button properly
                        with st.form(key="use_fixed_query_form"):
                            if st.form_submit_button("📋 Use Fixed Query"):
                                st.session_state.fixed_query = sql_part
                                st.rerun()
                else:
                    st.info(debugged_query)
                    
            except Exception as e:
                st.error(f"Debug failed: {e}")


def save_query_to_history(query: str):
    """Save query to history"""
    if query.strip():
        st.session_state.query_history.append(query)
        st.success("✅ Query saved to history!")


if __name__ == "__main__":
    main()

