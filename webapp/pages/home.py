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




def home_dashboard():
    """Home/Dashboard page with links to agentic apps"""
    st.markdown("""
    <style>
    /* Hide sidebar on home page */
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
    }
    
    /* Hide sidebar toggle button on home page */
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
    
    .app-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
        border: 2px solid transparent;
    }
    .app-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        border-color: #14a085;
    }
    .app-card-content {
        color: white;
        text-align: center;
    }
    .app-icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .app-title {
        font-size: 1.3rem;
        font-weight: 600;
        margin-bottom: 0.25rem;
    }
    .app-description {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("## 🏠 Agentic Apps Dashboard")
    st.markdown("Welcome to your AI-powered applications hub. Select an app to get started.")
    st.markdown("---")
    
    # Define agentic apps
    apps = [
        {
            'icon': '🤖',
            'title': 'AI Database Tool',
            'description': 'Intelligent database management with AI-powered SQL generation',
            'section': 'chatbot'  # Navigate to chatbot section
        },
        {
            'icon': '📧',
            'title': 'Smart Email Agent',
            'description': 'AI-powered email management and automation',
            'section': 'smart_email_agent'  # Navigate to smart email agent section
        },
        # Add more apps here in the future
        # {
        #     'icon': '📊',
        #     'title': 'Data Analytics App',
        #     'description': 'Advanced analytics and insights',
        #     'url': 'https://example.com/analytics'
        # },
    ]
    
    # Display apps in a grid (2 columns)
    cols = st.columns(2)
    for idx, app in enumerate(apps):
        with cols[idx % 2]:
            if 'section' in app:
                # Internal navigation - use button with styled content
                button_text = f"{app['icon']}\n\n**{app['title']}**\n\n{app['description']}"
                if st.button(
                    button_text,
                    key=f"app_card_{idx}",
                    use_container_width=True
                ):
                    st.session_state.active_section = app['section']
                    # Set query param to persist section across refreshes
                    st.query_params['section'] = app['section']
                    st.rerun()
            else:
                # External link (for future apps)
                st.markdown(f"""
                <a href="{app.get('url', '#')}" target="_blank" style="text-decoration: none;">
                    <div class="app-card">
                        <div class="app-card-content">
                            <div class="app-icon">{app['icon']}</div>
                            <div class="app-title">{app['title']}</div>
                            <div class="app-description">{app['description']}</div>
                        </div>
                    </div>
                </a>
                """, unsafe_allow_html=True)
    
    # Add CSS for better card styling
    st.markdown("""
    <style>
    button[data-testid*="app_card"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: 2px solid transparent !important;
        border-radius: 12px !important;
        padding: 2rem 1rem !important;
        color: white !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        min-height: 180px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-align: center !important;
        line-height: 1.6 !important;
    }
    button[data-testid*="app_card"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
        border-color: #14a085 !important;
    }
    button[data-testid*="app_card"] > div {
        color: white !important;
        font-size: 1rem !important;
    }
    button[data-testid*="app_card"] strong {
        color: white !important;
        font-size: 1.2rem !important;
        display: block !important;
        margin: 0.5rem 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)


