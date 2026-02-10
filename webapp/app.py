"""
Streamlit Web UI for AI Database Tool
Provides interactive interface for database management and AI-powered SQL queries

Modularized version - imports from separate modules for better organization
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Load environment variables (optional - Streamlit Cloud uses secrets.toml instead)
# Note: python-dotenv is optional - Streamlit Cloud uses .streamlit/secrets.toml
# Check if dotenv module is available before importing
_dotenv_available = False
try:
    import importlib.util
    spec = importlib.util.find_spec("dotenv")
    if spec is not None:
        from dotenv import load_dotenv
        load_dotenv()
        _dotenv_available = True
except (ImportError, ModuleNotFoundError, AttributeError):
    # python-dotenv not available (e.g., on Streamlit Cloud)
    # Streamlit Cloud uses .streamlit/secrets.toml instead
    pass

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import shared components
from shared import CODEMIRROR_AVAILABLE, MONACO_EDITOR_AVAILABLE

# Import configuration functions
from config.database_config import (
    get_persistent_sqlite_path, CONFIG_FILE, save_db_config, load_db_config
)

# Import utility functions
from utils.helpers import get_api_key

# Import UI modules
from ui.styling import inject_base_css, inject_dark_mode_css, inject_keyboard_shortcuts
from ui.components import (
    render_db_details, render_settings_dropdown, render_connection_setting
)
from ui.navigation import render_navigation_bar, handle_connection

# Import page modules
from pages import (
    home_dashboard, chatbot_tab, sql_editor_tab, data_explorer_tab,
    visualizations_tab, smart_email_agent, three_column_layout
)

# Import session initialization
from session import initialize_session_state

# Page configuration
st.set_page_config(
    page_title="AI Database Tool",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject base CSS (must be called early, before any content)
inject_base_css()

# Initialize session state (with error handling)
try:
    initialize_session_state()
except Exception as e:
    # If initialization fails, set minimal defaults to prevent server crash
    if 'active_section' not in st.session_state:
        st.session_state.active_section = 'home'
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'db_manager' not in st.session_state:
        from ai_db_tool.connectors import DatabaseManager
        st.session_state.db_manager = DatabaseManager()
    # Log error but don't crash
        import traceback
    print(f"ERROR in initialize_session_state: {e}")
        traceback.print_exc()


def main():
    """Main application"""
    
    # Add autocomplete attributes to form fields via JavaScript
    st.markdown("""
    <script>
    (function() {
        function setAutocompleteAttributes() {
            const passwordInputs = document.querySelectorAll('input[type="password"]');
            passwordInputs.forEach(input => {
                if (!input.getAttribute('autocomplete')) {
                    input.setAttribute('autocomplete', 'current-password');
                }
            });
            
            const textInputs = document.querySelectorAll('input[type="text"]');
            textInputs.forEach(input => {
                if (!input.getAttribute('autocomplete')) {
                    const label = input.closest('[data-testid*="stTextInput"]')?.querySelector('label');
                    if (label) {
                        const labelText = label.textContent.toLowerCase();
                        if (labelText.includes('username') || labelText.includes('user')) {
                            input.setAttribute('autocomplete', 'username');
                        } else if (labelText.includes('host') || labelText.includes('url')) {
                            input.setAttribute('autocomplete', 'url');
                        } else if (labelText.includes('email')) {
                            input.setAttribute('autocomplete', 'email');
                        } else {
                            input.setAttribute('autocomplete', 'off');
                        }
                    } else {
                        input.setAttribute('autocomplete', 'off');
                    }
                }
            });
        }
        
        setAutocompleteAttributes();
        setTimeout(setAutocompleteAttributes, 100);
        setTimeout(setAutocompleteAttributes, 500);
        setTimeout(setAutocompleteAttributes, 1000);
        
        const observer = new MutationObserver(setAutocompleteAttributes);
        observer.observe(document.body, { childList: true, subtree: true });
    })();
    </script>
    """, unsafe_allow_html=True)
    
    # Add id and name attributes to form fields
    st.markdown("""
    <script>
    (function() {
        function setFormFieldAttributes() {
            const inputs = document.querySelectorAll('input[type="text"], input[type="password"], input[type="number"], input[type="email"], input[type="url"], textarea');
            
            inputs.forEach(function(input, index) {
                if (input.id) return;
                
                const container = input.closest('[data-testid*="stTextInput"], [data-testid*="stTextArea"], [data-testid*="stNumberInput"]');
                let fieldName = 'field_' + index;
                
                if (container) {
                    const label = container.querySelector('label');
                    if (label && label.textContent) {
                        fieldName = label.textContent.toLowerCase()
                            .replace(/[^a-z0-9]+/g, '_')
                            .replace(/^_+|_+$/g, '')
                            .substring(0, 50) || 'field_' + index;
                    }
                }
                
                const uniqueId = fieldName + '_' + Date.now() + '_' + index;
                input.id = uniqueId;
                input.name = fieldName;
            });
        }
        
        setFormFieldAttributes();
        setTimeout(setFormFieldAttributes, 100);
        setTimeout(setFormFieldAttributes, 500);
        setTimeout(setFormFieldAttributes, 1000);
        
        const observer = new MutationObserver(setFormFieldAttributes);
        observer.observe(document.body, { childList: true, subtree: true });
    })();
    </script>
    """, unsafe_allow_html=True)
    
    # Add navigation dropdown JavaScript
    st.markdown("""
    <script>
    (function() {
        console.log('Navigation script loading...');
        
        function attachNavListeners() {
            console.log('Attempting to attach navigation listeners...');
            const menuItems = document.querySelectorAll('.nav-menu-item[data-section]');
            console.log('Found navigation menu items:', menuItems.length);
            
            menuItems.forEach(function(item, index) {
                if (item.hasAttribute('data-listener-attached')) {
                    return;
                }
                
                console.log('Attaching listener to menu item', index, item);
                item.setAttribute('data-listener-attached', 'true');
                
                item.addEventListener('click', function(e) {
                    console.log('Menu item clicked!', e);
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    const section = this.getAttribute('data-section');
                    console.log('Section:', section);
                    
                    if (section) {
                        const baseUrl = window.location.origin + window.location.pathname;
                        const currentParams = new URLSearchParams(window.location.search);
                        currentParams.set('section', section);
                        const newUrl = baseUrl + '?' + currentParams.toString();
                        console.log('Navigating to:', newUrl);
                        window.location.replace(newUrl);
                    }
                }, false);
                
                item.style.cursor = 'pointer';
                item.style.pointerEvents = 'auto';
            });
        }
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', attachNavListeners);
        } else {
            attachNavListeners();
        }
        
        setTimeout(attachNavListeners, 100);
        setTimeout(attachNavListeners, 500);
        setTimeout(attachNavListeners, 1000);
        setTimeout(attachNavListeners, 2000);
        
        const observer = new MutationObserver(function(mutations) {
            attachNavListeners();
        });
        
        if (document.body) {
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    })();
    </script>
    """, unsafe_allow_html=True)
    
    # Handle navigation via query parameters
    section_labels = {
        'home': '🏠 Home',
        'chatbot': '💬 AI SQL Assistant',
        'sql_editor': '📝 Smart SQL Editor',
        'data_explorer': '🔍 Data Explorer',
        'visualizations': '📊 Data Visualizations',
        'smart_email_agent': '📧 Smart Email Agent'
    }
    
    # Check query parameters first
    try:
        if hasattr(st, 'query_params'):
            query_params = st.query_params
            if query_params and 'section' in query_params:
                section = query_params.get('section')
                if isinstance(section, list):
                    section = section[0] if section else None
                elif isinstance(section, str):
                    section = section.strip()
                
                if section and section in section_labels:
                    if st.session_state.active_section != section:
                        st.session_state.active_section = section
                        st.rerun()
    except Exception as e:
        pass
    
    # Inject dark mode CSS (must be called early)
    inject_dark_mode_css()
    
    # Inject keyboard shortcuts (must be called early)
    inject_keyboard_shortcuts()
    
    # Show auto-connection notification if applicable
    if st.session_state.get('auto_connected', False):
        st.session_state.auto_connected = False
        st.toast("✅ Auto-connected to saved database", icon="🔗")
    
    # Sidebar - only show when not on home page or smart email agent page
    if st.session_state.active_section not in ['home', 'smart_email_agent']:
        with st.sidebar:
            st.title("🤖 AI Database Tool")
            
            # Database details display
            render_db_details()
            
            st.markdown("---")
            
            # Settings dropdown
            render_settings_dropdown()
            
            # Minimal divider
            st.markdown("<hr style='margin: 0.25rem 0; border: none; border-top: 1px solid rgba(250, 250, 250, 0.2);'>", unsafe_allow_html=True)
            
            # Database Connection
            with st.expander("🔌 Database Connection", expanded=not st.session_state.connected):
                render_connection_setting()
    
    # Main content area
    # Header - only show when not on home page or smart email agent page
    if st.session_state.active_section not in ['home', 'smart_email_agent']:
        # Home icon button at top left
        home_col1, home_col2 = st.columns([1, 20])
        with home_col1:
            if st.button("🏠", key="home_nav_button", help="Go to Home Dashboard"):
                st.session_state.active_section = 'home'
                st.query_params['section'] = 'home'
                st.rerun()
        
        # Style the home button
        st.markdown("""
        <style>
        button[data-testid*="home_nav_button"] {
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
        button[data-testid*="home_nav_button"]:hover {
            background-color: #14a085 !important;
            transform: scale(1.1) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        if st.session_state.layout_mode == 'three_column' and st.session_state.connected:
            st.markdown("#### 🤖 AI Database Tool")
        else:
            st.markdown("#### 🤖 AI Database Tool")
            st.markdown("Intelligent database management with AI-powered SQL generation")
            
            # Navigation dropdown
            if st.session_state.connected:
                nav_col1, nav_col2 = st.columns([1, 3])
                with nav_col1:
                    render_navigation_bar()
    
    # Render active section
    if st.session_state.active_section == 'home':
        home_dashboard()
    elif st.session_state.active_section == 'smart_email_agent':
        smart_email_agent()
    elif not st.session_state.connected:
        st.info("👈 Connect to a database using the sidebar to get started")
    else:
        # Choose layout based on user preference
        if st.session_state.layout_mode == 'three_column':
            three_column_layout()
        else:
            # Classic layout
            if st.session_state.active_section == 'chatbot':
                chatbot_tab()
            elif st.session_state.active_section == 'sql_editor':
                sql_editor_tab()
            elif st.session_state.active_section == 'data_explorer':
                data_explorer_tab()
            elif st.session_state.active_section == 'visualizations':
                visualizations_tab()
            elif st.session_state.active_section == 'smart_email_agent':
                smart_email_agent()


if __name__ == "__main__":
    main()
