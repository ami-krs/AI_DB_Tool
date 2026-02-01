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
from ui.components import render_sql_editor
from shared import CODEMIRROR_AVAILABLE, MONACO_EDITOR_AVAILABLE, codemirror_editor, monaco_editor




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


