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




def smart_email_agent():
    """Smart Email Agent - placeholder page for future implementation"""
    # Hide sidebar on smart email agent page
    st.markdown("""
    <style>
    /* Hide sidebar on smart email agent page */
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
    }
    
    /* Hide sidebar toggle button on smart email agent page */
    button[data-testid="baseButton-header"],
    button[kind="header"][data-testid*="header"],
    #custom-sidebar-toggle,
    button[aria-label*="sidebar" i],
    button[aria-label*="Close" i],
    button[aria-label*="open" i] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Adjust main content width when sidebar is hidden */
    section[data-testid="stMain"] {
        margin-left: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Home icon button at top left
    home_col1, home_col2 = st.columns([1, 20])
    with home_col1:
        if st.button("🏠", key="home_nav_button_email", help="Go to Home Dashboard"):
            st.session_state.active_section = 'home'
            # Update query param to persist across refreshes
            st.query_params['section'] = 'home'
            st.rerun()
    
    # Style the home button
    st.markdown("""
    <style>
    button[data-testid*="home_nav_button_email"] {
        background-color: #0d7377 !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 45px !important;
        height: 45px !important;
        font-size: 1.5rem !important;
        padding: 0 !important;
        min-width: 45px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        transition: background-color 0.2s, transform 0.2s !important;
    }
    button[data-testid*="home_nav_button_email"]:hover {
        background-color: #14a085 !important;
        transform: scale(1.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.header("📧 Smart Email Agent")
    st.info("Smart Email Agent features will be added here soon.")


