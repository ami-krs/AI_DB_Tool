"""Page modules for different sections of the application"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

from utils.query_execution import (
    execute_query, execute_generated_query, show_table_details, 
    show_common_queries, generate_sql_query, optimize_query, 
    debug_query, save_query_to_history
)
from shared import CODEMIRROR_AVAILABLE, MONACO_EDITOR_AVAILABLE, codemirror_editor, monaco_editor
from ui.components import render_sql_editor




def sql_editor_compact():
    """Compact SQL editor for three column layout"""
    st.markdown("### 📝 SQL Editor")
    
    # Keyboard shortcuts help
    with st.expander("⌨️ Keyboard Shortcuts", expanded=False):
        st.markdown("""
        - **Ctrl+Enter** (or **Cmd+Enter** on Mac): Execute query
        - **Ctrl+/** (or **Cmd+/** on Mac): Toggle comment on selected lines
        - **Ctrl+S** (or **Cmd+S** on Mac): Save query to history
        - **Ctrl+L** (or **Cmd+L** on Mac): Clear editor
        """)
    
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
    
    query = render_sql_editor(
        key="sql_editor",
        height=250,
        placeholder="SELECT * FROM table_name LIMIT 10;"
    )
    
    # Action buttons - Execute and Generate SQL icon-only on left, others on right
    action_col1, action_col2, action_col3, action_col4, action_col5 = st.columns([1, 1, 2, 2, 2])
    with action_col1:
        if st.button("▶️", type="primary", width="stretch", key="run_btn_compact", help="Execute Query"):
            execute_query(query or st.session_state.get("sql_editor", ""))
    with action_col2:
        if st.button("🤖", width="stretch", help="Generate SQL"):
            generate_sql_query()
    with action_col3:
        if st.button("🚀 AI Opt", width="stretch"):
            optimize_query(query)
    with action_col4:
        if st.button("🔧 Fix", width="stretch"):
            debug_query(query)
    with action_col5:
        if st.button("💾 Save", width="stretch"):
            save_query_to_history(query)
    
    # Query history
    if st.session_state.query_history:
        with st.expander("📚 Query History"):
            for i, q in enumerate(reversed(st.session_state.query_history[-10:])):
                st.code(q, language='sql')
                if st.button("📋 Copy", key=f"copy_compact_{i}"):
                    st.session_state.sql_editor = q
                    st.rerun()




def sql_editor_tab():
    """SQL Editor interface"""
    st.header("📝 Smart SQL Editor")
    
    # Keyboard shortcuts help
    with st.expander("⌨️ Keyboard Shortcuts", expanded=False):
        st.markdown("""
        - **Ctrl+Enter** (or **Cmd+Enter** on Mac): Execute query
        - **Ctrl+/** (or **Cmd+/** on Mac): Toggle comment on selected lines
        - **Ctrl+S** (or **Cmd+S** on Mac): Save query to history
        - **Ctrl+L** (or **Cmd+L** on Mac): Clear editor
        """)
    
    # Quick insert buttons for tables
    if st.session_state.connected:
        tables = st.session_state.db_manager.get_tables()
        if tables:
            st.markdown("**📋 Quick Insert:**")
            cols = st.columns(min(6, len(tables) + 1))
            with cols[0]:
                if st.button("📋 Table List", width="stretch"):
                    st.session_state.show_table_list = not st.session_state.get('show_table_list', False)
            for i, table in enumerate(tables[:5], 1):
                with cols[i % len(cols)]:
                    if st.button(f"📊 {table}", key=f"insert_{table}", width="stretch"):
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
                    if st.button(f"📋 {table}", key=f"table_btn_{i}", width="stretch"):
                        st.session_state.sql_editor = st.session_state.get('sql_editor', '') + f"{table}"
                        st.session_state.show_table_list = False
                        st.rerun()
        
        # Update sql_editor if fixed_query exists
        if st.session_state.fixed_query:
            st.session_state.sql_editor = st.session_state.fixed_query
            st.session_state.fixed_query = None
        
        query = render_sql_editor(
            key="sql_editor",
            height=300,
            placeholder="SELECT * FROM table_name LIMIT 10;"
        )
        
    with col2:
        st.markdown("### Actions")
        
        # Compact buttons: Execute Query and Generate SQL on same line, icon-only with hover tooltips
        action_col1, action_col2, action_col3 = st.columns([1, 1, 10])
        with action_col1:
            if st.button("▶️", type="primary", width="stretch", key="run_btn_tab", help="Execute Query"):
                execute_query(query or st.session_state.get("sql_editor", ""))
        with action_col2:
            if st.button("🤖", width="stretch", help="Generate SQL"):
                generate_sql_query()
        
        if st.button("🔧 AI Optimize", width="stretch"):
            optimize_query(query)
        
        if st.button("🐛 AI Debug", width="stretch"):
            debug_query(query)
        
        if st.button("💾 Save to History", width="stretch"):
            save_query_to_history(query)
        
        # Smart suggestions
        if st.session_state.connected:
            st.markdown("---")
            st.markdown("### 💡 Smart Help")
            if st.button("📋 Show Tables", width="stretch"):
                show_table_details()
            if st.button("❓ Common Queries", width="stretch"):
                show_common_queries()
    
    # Query history
    if st.session_state.query_history:
        with st.expander("📚 Query History"):
            for i, q in enumerate(reversed(st.session_state.query_history[-10:])):
                st.code(q, language='sql')
                if st.button("📋 Copy", key=f"copy_{i}"):
                    st.code(q, language='sql')
                st.markdown("---")


