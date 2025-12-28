"""
Streamlit Web UI for AI Database Tool
Provides interactive interface for database management and AI-powered SQL queries
"""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any, List
import os
import json
from pathlib import Path
from datetime import datetime

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

# Configuration file path for persistent storage
# Use project directory for SQLite DB to ensure consistency
PROJECT_ROOT = Path(__file__).parent.parent
DB_DIR = PROJECT_ROOT / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)  # Ensure data directory exists

# Config directory - use home directory for user-specific config
CONFIG_DIR = Path.home() / ".ai_db_tool"
CONFIG_FILE = CONFIG_DIR / "db_config.json"

def ensure_config_dir():
    """Ensure config directory exists"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def get_persistent_sqlite_path():
    """Get persistent SQLite database path in project directory"""
    return DB_DIR / "database.sqlite"

def save_db_config(config: DatabaseConfig):
    """Save database configuration to persistent storage"""
    try:
        ensure_config_dir()
        config_dict = {
            'db_type': config.db_type,
            'host': config.host,
            'port': config.port,
            'database': config.database,
            'username': config.username,
            'password': config.password,  # Note: In production, use encryption
            'extra_params': config.extra_params or {}
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_dict, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Failed to save connection config: {e}")
        return False

def load_db_config() -> Optional[DatabaseConfig]:
    """Load database configuration from persistent storage"""
    try:
        if not CONFIG_FILE.exists():
            return None
        
        with open(CONFIG_FILE, 'r') as f:
            config_dict = json.load(f)
        
        db_type = config_dict.get('db_type', 'postgresql')
        database = config_dict.get('database', '')
        
        # For SQLite, always use persistent path (migrate old configs if needed)
        if db_type == 'sqlite':
            persistent_path = get_persistent_sqlite_path()
            persistent_path_abs = str(Path(persistent_path).absolute())
            # If saved config uses a different path (like /tmp/), migrate to persistent path
            if database != persistent_path and database != persistent_path_abs:
                database = persistent_path_abs
                # Update the config file to use persistent path
                config_dict['database'] = database
                try:
                    with open(CONFIG_FILE, 'w') as f:
                        json.dump(config_dict, f, indent=2)
                except:
                    pass  # If we can't update, continue with persistent path
        
        return DatabaseConfig(
            db_type=db_type,
            host=config_dict.get('host', ''),
            port=config_dict.get('port', 5432),
            database=database,
            username=config_dict.get('username', ''),
            password=config_dict.get('password', ''),
            extra_params=config_dict.get('extra_params', {})
        )
    except Exception as e:
        st.warning(f"Could not load saved connection: {e}")
        return None

def get_persistent_sqlite_path() -> str:
    """Get a persistent path for SQLite database (not in /tmp)"""
    ensure_config_dir()
    return str(CONFIG_DIR / "database.sqlite")

# Helper function to get API key from Streamlit secrets or environment variables
def get_api_key(key_name: str) -> Optional[str]:
    """
    Get API key from Streamlit secrets (for Streamlit Cloud) or environment variables (for local)
    
    Args:
        key_name: Name of the API key (e.g., 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY')
        
    Returns:
        API key string or None if not found
    """
    # Try Streamlit secrets first (for Streamlit Cloud)
    try:
        if hasattr(st, 'secrets'):
            # Try to access the key - it will raise KeyError if not found
            try:
                value = st.secrets[key_name]
                if value and str(value).strip():  # Make sure it's not empty
                    return str(value).strip()
            except (KeyError, AttributeError, TypeError):
                # Key not found in secrets, continue to environment variables
                pass
    except Exception:
        # If anything goes wrong with secrets access, fall through to env vars
        pass
    
    # Fallback to environment variables (for local development)
    env_value = os.getenv(key_name)
    if env_value and str(env_value).strip():
        return str(env_value).strip()
    
    return None

# Try to import CodeMirror editor component
try:
    from components.codemirror_editor import codemirror_editor
    CODEMIRROR_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import path
        import sys
        import os
        components_path = os.path.join(os.path.dirname(__file__), 'components')
        if components_path not in sys.path:
            sys.path.insert(0, components_path)
        from codemirror_editor import codemirror_editor
        CODEMIRROR_AVAILABLE = True
    except ImportError:
        CODEMIRROR_AVAILABLE = False
        codemirror_editor = None

# Try to import Monaco editor component
try:
    from components.monaco_editor import monaco_editor
    MONACO_EDITOR_AVAILABLE = True
except ImportError:
    try:
        import sys
        import os
        components_path = os.path.join(os.path.dirname(__file__), 'components')
        if components_path not in sys.path:
            sys.path.insert(0, components_path)
        from monaco_editor import monaco_editor
        MONACO_EDITOR_AVAILABLE = True
    except ImportError:
        MONACO_EDITOR_AVAILABLE = False
        monaco_editor = None


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
    /* Completely remove top padding/margin for the main container */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 2rem !important;
        margin-top: 0 !important;
    }
    
    /* Remove all space above title */
    h1 {
        margin-top: 0 !important;
        padding-top: 0 !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.2 !important;
    }
    
    /* Minimize Streamlit header to absolute minimum */
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        visibility: hidden !important;
        overflow: hidden !important;
        position: absolute !important;
    }
    
    /* Remove padding in the app header area */
    .stApp > header {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        visibility: hidden !important;
        overflow: hidden !important;
    }
    
    /* Hide Streamlit menu button if present, but allow sidebar toggle */
    button[kind="header"]:not([aria-label*="sidebar"]):not([aria-label*="Sidebar"]):not([data-testid*="sidebar"]):not([data-testid*="Collapse"]) {
        display: none !important;
    }
    
    /* Remove any top margin from header content */
    header[data-testid="stHeader"] > div {
        display: none !important;
        padding: 0 !important;
        margin: 0 !important;
        height: 0 !important;
    }
    
    /* Remove top margin from first element in main content */
    .main .block-container > div:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Remove any top spacing from the main app container */
    .stApp {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove spacing from the main content area */
    section[data-testid="stMain"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Target the first vertical block to remove top spacing */
    div[data-testid="stVerticalBlock"]:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Target all vertical blocks in main area */
    .main div[data-testid="stVerticalBlock"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove spacing from element containers */
    .element-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Target the container that holds the title specifically */
    .main .block-container > div > div[data-testid="stVerticalBlock"]:first-child > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove any gap/padding from Streamlit's layout containers */
    .stApp > div[data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Target the view container */
    div[data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove spacing from sidebar that might affect layout */
    section[data-testid="stSidebar"] {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* Hide sidebar on home page */
    body:has([data-testid="stAppViewContainer"]:has-text("🏠 Agentic Apps Dashboard")) section[data-testid="stSidebar"],
    section[data-testid="stSidebar"]:has(+ *:has-text("🏠 Agentic Apps Dashboard")) {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Make sidebar title more compact */
    section[data-testid="stSidebar"] h1 {
        margin-top: 0 !important;
        margin-bottom: 0.75rem !important;
        padding-bottom: 0 !important;
        font-size: 1.5rem !important;
        line-height: 1.3 !important;
    }
    
    /* Reduce spacing between sidebar elements */
    section[data-testid="stSidebar"] .element-container {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
    }
    
    /* Reduce divider spacing (hr elements created by ---) */
    section[data-testid="stSidebar"] hr {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        border: none !important;
        border-top: 1px solid rgba(250, 250, 250, 0.2) !important;
    }
    
    /* Reduce spacing around sidebar expanders */
    section[data-testid="stSidebar"] .streamlit-expanderHeader {
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
        margin-bottom: 0.1rem !important;
        margin-top: 0.1rem !important;
    }
    
    /* Reduce spacing inside expanders - minimal padding */
    section[data-testid="stSidebar"] .streamlit-expanderContent {
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
    }
    
    /* Reduce spacing for toggle switches in sidebar */
    section[data-testid="stSidebar"] .stToggle {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }
    
    /* Reduce spacing for selectbox in sidebar */
    section[data-testid="stSidebar"] .stSelectbox {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
    }
    
    /* Remove info box spacing in settings */
    section[data-testid="stSidebar"] .streamlit-expanderContent .stInfo {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding: 0.25rem 0.5rem !important;
    }
    
    /* Reduce spacing in sidebar info boxes */
    section[data-testid="stSidebar"] .stInfo {
        margin-top: 0.25rem !important;
        margin-bottom: 0.25rem !important;
        padding: 0.5rem !important;
    }
    
    /* Ensure sidebar collapse/expand button is always visible */
    button[data-testid="baseButton-header"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: fixed !important;
        top: 0.5rem !important;
        left: 0 !important;
        z-index: 999 !important;
        background-color: #0d7377 !important;
        color: white !important;
        border: none !important;
        border-radius: 0 0.5rem 0.5rem 0 !important;
        padding: 0.5rem !important;
        cursor: pointer !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        transition: background-color 0.2s !important;
    }
    
    button[data-testid="baseButton-header"]:hover {
        background-color: #14a085 !important;
    }
    
    /* Alternative selector for sidebar toggle */
    button[kind="header"][data-testid*="header"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: fixed !important;
        top: 0.5rem !important;
        left: 0 !important;
        z-index: 999 !important;
        background-color: #0d7377 !important;
        color: white !important;
        border: none !important;
        border-radius: 0 0.5rem 0.5rem 0 !important;
        padding: 0.5rem !important;
        cursor: pointer !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
    }
    
    button[kind="header"][data-testid*="header"]:hover {
        background-color: #14a085 !important;
    }
    
    /* Streamlit's sidebar collapse button */
    .stApp > button {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: fixed !important;
        top: 0.5rem !important;
        left: 0 !important;
        z-index: 999 !important;
        background-color: #0d7377 !important;
        color: white !important;
        border: none !important;
        border-radius: 0 0.5rem 0.5rem 0 !important;
        padding: 0.5rem !important;
        cursor: pointer !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
    }
    
    /* Ensure sidebar toggle arrow is visible */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] button,
    button[aria-label*="Close"],
    button[aria-label*="open"] {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Ensure custom sidebar toggle button is always visible */
    #custom-sidebar-toggle {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
        position: fixed !important;
        top: 0.5rem !important;
        left: 0 !important;
        z-index: 99999 !important;
        background-color: #0d7377 !important;
        color: white !important;
        border: none !important;
        border-radius: 0 0.5rem 0.5rem 0 !important;
        padding: 0.5rem !important;
        cursor: pointer !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
        min-width: 40px !important;
        min-height: 40px !important;
        font-size: 1.2rem !important;
    }
    
    #custom-sidebar-toggle:hover {
        background-color: #14a085 !important;
    }
    
    /* Negative margin hack if needed - use with caution */
    .main .block-container > div:first-child > div:first-child {
        margin-top: -1rem !important;
    }
    
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
    
    /* Scrollable chat container - targets container with chat messages */
    #chat-history-scrollable {
        max-height: 60vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
        border: 1px solid rgba(250, 250, 250, 0.2) !important;
        border-radius: 0.5rem !important;
        background-color: rgba(0, 0, 0, 0.02) !important;
        scroll-behavior: smooth !important;
    }
    
    /* Compact chat container for sidebar */
    #chat-history-scrollable-compact {
        max-height: 50vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        border: 1px solid rgba(250, 250, 250, 0.2) !important;
        border-radius: 0.5rem !important;
        background-color: rgba(0, 0, 0, 0.02) !important;
        scroll-behavior: smooth !important;
    }
    
    /* Custom scrollbar styling */
    #chat-history-scrollable::-webkit-scrollbar,
    #chat-history-scrollable-compact::-webkit-scrollbar,
    #chat-messages-scrollable-wrapper::-webkit-scrollbar,
    #chat-messages-scrollable-wrapper-compact::-webkit-scrollbar {
        width: 8px;
    }
    
    #chat-history-scrollable::-webkit-scrollbar-track,
    #chat-history-scrollable-compact::-webkit-scrollbar-track,
    #chat-messages-scrollable-wrapper::-webkit-scrollbar-track,
    #chat-messages-scrollable-wrapper-compact::-webkit-scrollbar-track {
        background: rgba(0, 0, 0, 0.05);
        border-radius: 4px;
    }
    
    #chat-history-scrollable::-webkit-scrollbar-thumb,
    #chat-history-scrollable-compact::-webkit-scrollbar-thumb,
    #chat-messages-scrollable-wrapper::-webkit-scrollbar-thumb,
    #chat-messages-scrollable-wrapper-compact::-webkit-scrollbar-thumb {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 4px;
    }
    
    #chat-history-scrollable::-webkit-scrollbar-thumb:hover,
    #chat-history-scrollable-compact::-webkit-scrollbar-thumb:hover,
    #chat-messages-scrollable-wrapper::-webkit-scrollbar-thumb:hover,
    #chat-messages-scrollable-wrapper-compact::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 0, 0, 0.3);
    }
    
    /* Alternative approach: Target the vertical block container that holds chat messages */
    div[data-testid="stVerticalBlock"]:has(> div[data-testid="stChatMessage"]) {
        max-height: 60vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
        scroll-behavior: smooth !important;
    }
    
    /* Hide navigation buttons completely */
    button[data-testid*="nav_btn_"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        position: absolute !important;
        left: -9999px !important;
        opacity: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }
    /* Hide parent containers of navigation buttons */
    div:has(> button[data-testid*="nav_btn_"]) {
        display: none !important;
        height: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        visibility: hidden !important;
    }
    
    /* Compact Results header */
    div[data-testid="stVerticalBlock"]:has(> div > div > p:has-text("📊 Results")) p,
    div[data-testid="stVerticalBlock"]:has(> div > div > p:has-text("📊 Last Query Results")) p {
        font-size: 1rem !important;
        margin-bottom: 0.25rem !important;
        margin-top: 0.25rem !important;
        font-weight: 600 !important;
    }
    
    /* Compact download button - icon only */
    div[data-testid="stDownloadButton"] button {
        font-size: 1.2rem !important;
        padding: 0.2rem 0.4rem !important;
        height: auto !important;
        min-height: 1.5rem !important;
        max-height: 1.5rem !important;
        line-height: 1 !important;
        width: auto !important;
        min-width: 2rem !important;
    }
    
    /* Remove text spacing in icon-only button */
    div[data-testid="stDownloadButton"] button > div {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Compact icon-only action buttons - Execute and Generate SQL */
    button[data-testid*="run_btn"]:has-text("▶️"),
    button:has-text("▶️"):not([data-testid*="download"]),
    button:has-text("🤖"):not([data-testid*="download"]) {
        font-size: 1.3rem !important;
        padding: 0.3rem 0.5rem !important;
        height: auto !important;
        min-height: 2rem !important;
        max-height: 2rem !important;
        width: auto !important;
        min-width: 2.5rem !important;
        line-height: 1 !important;
    }
    
    /* Remove text spacing in icon-only buttons */
    button:has-text("▶️") > div:not([data-testid*="download"]),
    button:has-text("🤖") > div:not([data-testid*="download"]) {
        padding: 0 !important;
        margin: 0 !important;
    }
</style>
<script>
    // TEST: This should appear in console immediately
    console.log('=== SIDEBAR TOGGLE SCRIPT STARTING ===');
    console.error('TEST ERROR MESSAGE - IF YOU SEE THIS, SCRIPT IS RUNNING');
    
    // Aggressively remove all top spacing
    function removeTopSpacing() {
        // Hide header completely
        const header = document.querySelector('header[data-testid="stHeader"]');
        if (header) {
            header.style.display = 'none';
            header.style.height = '0';
            header.style.visibility = 'hidden';
        }
        
        // Remove padding from main container
        const blockContainer = document.querySelector('.main .block-container');
        if (blockContainer) {
            blockContainer.style.paddingTop = '0';
            blockContainer.style.marginTop = '0';
        }
        
        // Remove padding from main section
        const mainSection = document.querySelector('section[data-testid="stMain"]');
        if (mainSection) {
            mainSection.style.paddingTop = '0';
            mainSection.style.marginTop = '0';
        }
        
        // Remove spacing from first vertical block
        const firstVerticalBlock = document.querySelector('.main div[data-testid="stVerticalBlock"]:first-child');
        if (firstVerticalBlock) {
            firstVerticalBlock.style.paddingTop = '0';
            firstVerticalBlock.style.marginTop = '0';
        }
        
        // Target the title directly
        const title = document.querySelector('.main h1');
        if (title) {
            title.style.marginTop = '0';
            title.style.paddingTop = '0';
            // Also target parent containers
            let parent = title.parentElement;
            for (let i = 0; i < 5 && parent; i++) {
                if (parent.classList && parent.classList.contains('block-container')) break;
                parent.style.paddingTop = '0';
                parent.style.marginTop = '0';
                parent = parent.parentElement;
            }
        }
        
        // Remove spacing from app view container
        const appView = document.querySelector('div[data-testid="stAppViewContainer"]');
        if (appView) {
            appView.style.paddingTop = '0';
            appView.style.marginTop = '0';
        }
    }
    
    // Run on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', removeTopSpacing);
    } else {
        removeTopSpacing();
    }
    
    // Run after delays to catch dynamically loaded content
    setTimeout(removeTopSpacing, 100);
    setTimeout(removeTopSpacing, 500);
    setTimeout(removeTopSpacing, 1000);
    
    // Also observe for changes
    const observer = new MutationObserver(removeTopSpacing);
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Test if script is running
    console.log('=== SIDEBAR TOGGLE SCRIPT LOADED ===');
    
    // Ensure sidebar toggle button is always visible
    function ensureSidebarToggleVisible() {
        // Find all buttons first
        const allButtons = document.querySelectorAll('button');
        let sidebarToggleButton = null;
        
        // Try to find the sidebar toggle button using various methods
        for (let button of allButtons) {
            const ariaLabel = (button.getAttribute('aria-label') || '').toLowerCase();
            const testId = (button.getAttribute('data-testid') || '').toLowerCase();
            const kind = button.getAttribute('kind') || '';
            const className = button.className || '';
            
            // Check multiple conditions to identify sidebar toggle
            const isSidebarToggle = 
                ariaLabel.includes('sidebar') ||
                ariaLabel.includes('menu') ||
                testId.includes('sidebar') ||
                testId.includes('collapse') ||
                (kind === 'header' && (ariaLabel.includes('sidebar') || testId.includes('header'))) ||
                (testId.includes('basebutton') && testId.includes('header')) ||
                // Check if button is positioned where sidebar toggle would be
                (button.style && (
                    button.style.left === '0px' ||
                    button.style.position === 'fixed'
                ) && button.offsetLeft < 100);
            
            if (isSidebarToggle) {
                sidebarToggleButton = button;
                break;
            }
        }
        
        // Also check for Streamlit's specific sidebar toggle elements
        if (!sidebarToggleButton) {
            // Try Streamlit's specific selectors
            const collapseButton = document.querySelector('[data-testid="stSidebarCollapseButton"]');
            if (collapseButton) {
                sidebarToggleButton = collapseButton.querySelector('button') || collapseButton;
            }
        }
        
        // If still not found, look for buttons with specific SVG icons (chevron/arrow)
        if (!sidebarToggleButton) {
            for (let button of allButtons) {
                const svg = button.querySelector('svg');
                if (svg) {
                    const svgPath = svg.innerHTML || '';
                    // Sidebar toggle typically has chevron/arrow icons
                    if (svgPath.includes('chevron') || 
                        svgPath.includes('arrow') ||
                        svgPath.includes('M9') || // Common path for chevrons
                        svgPath.includes('path d=')) {
                        // Check if it's positioned near the left edge
                        const rect = button.getBoundingClientRect();
                        if (rect.left < 100 && rect.top < 100) {
                            sidebarToggleButton = button;
                            break;
                        }
                    }
                }
            }
        }
        
        // Style the found button
        if (sidebarToggleButton) {
            sidebarToggleButton.style.display = 'flex';
            sidebarToggleButton.style.visibility = 'visible';
            sidebarToggleButton.style.opacity = '1';
            sidebarToggleButton.style.position = 'fixed';
            sidebarToggleButton.style.top = '0.5rem';
            sidebarToggleButton.style.left = '0';
            sidebarToggleButton.style.zIndex = '9999';
            sidebarToggleButton.style.backgroundColor = '#0d7377';
            sidebarToggleButton.style.color = 'white';
            sidebarToggleButton.style.border = 'none';
            sidebarToggleButton.style.borderRadius = '0 0.5rem 0.5rem 0';
            sidebarToggleButton.style.padding = '0.5rem';
            sidebarToggleButton.style.cursor = 'pointer';
            sidebarToggleButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
            sidebarToggleButton.style.transition = 'background-color 0.2s';
            sidebarToggleButton.style.minWidth = '40px';
            sidebarToggleButton.style.minHeight = '40px';
            
            // Ensure SVG icons inside are white
            const svgIcons = sidebarToggleButton.querySelectorAll('svg');
            svgIcons.forEach(svg => {
                svg.style.fill = 'white';
                svg.style.color = 'white';
            });
            
            // Remove existing listeners to avoid duplicates, then add hover effect
            const newButton = sidebarToggleButton.cloneNode(true);
            sidebarToggleButton.parentNode.replaceChild(newButton, sidebarToggleButton);
            sidebarToggleButton = newButton;
            
            sidebarToggleButton.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#14a085';
            });
            sidebarToggleButton.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '#0d7377';
            });
        }
    }
    
    // Run immediately and after delays
    ensureSidebarToggleVisible();
    setTimeout(ensureSidebarToggleVisible, 100);
    setTimeout(ensureSidebarToggleVisible, 500);
    setTimeout(ensureSidebarToggleVisible, 1000);
    
        // Also observe for dynamically added buttons
        const sidebarToggleObserver = new MutationObserver(ensureSidebarToggleVisible);
        sidebarToggleObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class', 'aria-label', 'data-testid']
        });
        
        // Always create a custom toggle button that's guaranteed to be visible
        function createCustomSidebarToggle() {
            console.log('=== Creating custom sidebar toggle button ===');
            
            // Remove existing custom button if present
            const existing = document.getElementById('custom-sidebar-toggle');
            if (existing) {
                console.log('Removing existing custom button');
                existing.remove();
            }
            
            // Create custom toggle button - always visible, don't wait for sidebar
            const toggleButton = document.createElement('button');
            toggleButton.id = 'custom-sidebar-toggle';
            toggleButton.innerHTML = '☰';
            toggleButton.setAttribute('aria-label', 'Toggle sidebar');
            toggleButton.setAttribute('type', 'button');
            toggleButton.setAttribute('title', 'Toggle Sidebar');
            
            // Style the button with inline styles to ensure they're applied
            toggleButton.style.position = 'fixed';
            toggleButton.style.top = '0.5rem';
            toggleButton.style.left = '0';
            toggleButton.style.zIndex = '99999';
            toggleButton.style.backgroundColor = '#0d7377';
            toggleButton.style.color = 'white';
            toggleButton.style.border = 'none';
            toggleButton.style.borderRadius = '0 0.5rem 0.5rem 0';
            toggleButton.style.padding = '0.5rem';
            toggleButton.style.cursor = 'pointer';
            toggleButton.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
            toggleButton.style.transition = 'background-color 0.2s';
            toggleButton.style.minWidth = '40px';
            toggleButton.style.minHeight = '40px';
            toggleButton.style.fontSize = '1.2rem';
            toggleButton.style.display = 'flex';
            toggleButton.style.alignItems = 'center';
            toggleButton.style.justifyContent = 'center';
            toggleButton.style.visibility = 'visible';
            toggleButton.style.opacity = '1';
            toggleButton.style.pointerEvents = 'auto';
            
            // Hover effects
            toggleButton.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#14a085';
            });
            
            toggleButton.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '#0d7377';
            });
            
            // Click handler - try multiple methods to toggle sidebar
            toggleButton.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Method 1: Try to find and click Streamlit's native toggle button
                const selectors = [
                    'button[aria-label*="close sidebar" i]',
                    'button[aria-label*="open sidebar" i]',
                    'button[aria-label*="Close sidebar" i]',
                    'button[aria-label*="Open sidebar" i]',
                    '[data-testid*="stSidebarCollapse"] button',
                    '[data-testid*="stSidebarCollapseButton"]',
                    'button[kind="header"]'
                ];
                
                let clicked = false;
                for (let selector of selectors) {
                    const btn = document.querySelector(selector);
                    if (btn && btn.offsetParent !== null) { // Check if visible
                        btn.click();
                        clicked = true;
                        break;
                    }
                }
                
                // Method 2: If native button not found, try to toggle sidebar directly via Streamlit's API
                if (!clicked) {
                    // Send message to Streamlit to toggle sidebar
                    if (window.parent && window.parent.postMessage) {
                        window.parent.postMessage({
                            type: 'streamlit:setComponentValue',
                            key: 'sidebar',
                            value: 'toggle'
                        }, '*');
                    }
                    
                    // Fallback: Try to manipulate sidebar CSS directly
                    const sidebarEl = document.querySelector('[data-testid="stSidebar"]');
                    if (sidebarEl) {
                        const computedStyle = window.getComputedStyle(sidebarEl);
                        const isVisible = computedStyle.display !== 'none' && 
                                         computedStyle.visibility !== 'hidden' &&
                                         sidebarEl.offsetWidth > 0;
                        
                        // Try to trigger Streamlit's sidebar toggle by dispatching events
                        const event = new CustomEvent('sidebar-toggle', { bubbles: true });
                        document.dispatchEvent(event);
                        
                        // As last resort, try CSS manipulation (this may not work with Streamlit's state)
                        // But we'll try it anyway
                        if (!isVisible) {
                            sidebarEl.style.display = '';
                            sidebarEl.style.visibility = '';
                        }
                    }
                }
            });
            
            // Always append to body or main container
            const targetContainer = document.body || document.documentElement;
            targetContainer.appendChild(toggleButton);
            console.log('Custom sidebar toggle button created and appended');
            
            // Verify it's visible
            setTimeout(function() {
                const btn = document.getElementById('custom-sidebar-toggle');
                if (btn) {
                    const rect = btn.getBoundingClientRect();
                    console.log('Button position:', rect.left, rect.top, 'Visible:', rect.width > 0 && rect.height > 0);
                } else {
                    console.error('Button was not found after creation!');
                }
            }, 100);
        }
        
        // Create toggle button immediately when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                createCustomSidebarToggle();
            });
        } else {
            createCustomSidebarToggle();
        }
        
        // Also retry multiple times to ensure it's created
        setTimeout(createCustomSidebarToggle, 100);
        setTimeout(createCustomSidebarToggle, 300);
        setTimeout(createCustomSidebarToggle, 500);
        setTimeout(createCustomSidebarToggle, 1000);
        setTimeout(createCustomSidebarToggle, 2000);
        setTimeout(createCustomSidebarToggle, 3000);
        
        // Observe for sidebar changes and ensure button is always visible
        const sidebarObserver = new MutationObserver(function(mutations) {
            // Check if custom button exists
            let customButton = document.getElementById('custom-sidebar-toggle');
            if (!customButton) {
                console.log('Custom button missing, recreating...');
                createCustomSidebarToggle();
            } else {
                // Ensure it's still visible
                const rect = customButton.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) {
                    console.log('Button exists but not visible, fixing...');
                    customButton.style.display = 'flex';
                    customButton.style.visibility = 'visible';
                    customButton.style.opacity = '1';
                }
            }
            // Also try to style native button
            ensureSidebarToggleVisible();
        });
        
        sidebarObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class', 'data-testid']
        });
        
        // Also watch for sidebar specifically
        function watchSidebar() {
            const sidebarElement = document.querySelector('[data-testid="stSidebar"]');
            if (sidebarElement) {
                const sidebarMutationObserver = new MutationObserver(function() {
                    if (!document.getElementById('custom-sidebar-toggle')) {
                        createCustomSidebarToggle();
                    }
                });
                sidebarMutationObserver.observe(sidebarElement, {
                    attributes: true,
                    attributeFilter: ['style', 'class']
                });
            } else {
                // Retry if sidebar not found yet
                setTimeout(watchSidebar, 500);
            }
        }
        watchSidebar();
</script>
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

    # Auto-load saved database connection on startup
if not st.session_state.connected:
    saved_config = load_db_config()
    if saved_config:
        try:
            if st.session_state.db_manager.connect(saved_config):
                st.session_state.connected = True
                st.session_state.db_type = saved_config.db_type
                # Load schema info to ensure tables are displayed
                # This is critical - refresh schema info after auto-connect
                try:
                    # Get table names directly first (this is more reliable)
                    tables = st.session_state.db_manager.get_tables()
                    
                    # Then get full database info if available
                    try:
                        schema_info = st.session_state.db_manager.get_database_info()
                        if schema_info:
                            # Ensure 'tables' contains table names (strings), not schema objects
                            # get_database_info() returns schema objects, but we need names
                            if tables and isinstance(tables[0] if tables else None, str):
                                # If we have table names, use them directly
                                schema_info['tables'] = tables
                            elif schema_info.get('tables') and isinstance(schema_info['tables'][0] if schema_info['tables'] else None, dict):
                                # If it's schema objects, extract table names
                                schema_info['tables'] = [t['table_name'] if isinstance(t, dict) and 'table_name' in t else str(t) for t in schema_info['tables']]
                            else:
                                schema_info['tables'] = tables or []
                            
                            schema_info['db_type'] = saved_config.db_type
                            schema_info['total_tables'] = len(tables) if tables else 0
                            st.session_state.schema_info = schema_info
                        else:
                            # If get_database_info returns None, use table names directly
                            st.session_state.schema_info = {
                                'tables': tables or [],
                                'db_type': saved_config.db_type,
                                'total_tables': len(tables) if tables else 0,
                                'database_name': saved_config.database
                            }
                    except:
                        # If get_database_info fails, use table names directly
                        st.session_state.schema_info = {
                            'tables': tables or [],
                            'db_type': saved_config.db_type,
                            'total_tables': len(tables) if tables else 0,
                            'database_name': saved_config.database
                        }
                except Exception as schema_error:
                    # If even get_tables fails, create empty schema info
                    st.session_state.schema_info = {
                        'tables': [],
                        'db_type': saved_config.db_type,
                        'total_tables': 0,
                        'database_name': saved_config.database
                    }
                # Show info in sidebar (non-intrusive)
                st.session_state.auto_connected = True
        except Exception as e:
            # Silently fail - user can reconnect manually
            pass

# Ensure schema_info exists if connected but schema_info is missing
if st.session_state.connected and 'schema_info' not in st.session_state:
    try:
        # Get table names directly (more reliable)
        tables = st.session_state.db_manager.get_tables()
        
        # Try to get full database info
        try:
            schema_info = st.session_state.db_manager.get_database_info()
            if schema_info:
                # Ensure 'tables' contains table names (strings), not schema objects
                if tables and isinstance(tables[0] if tables else None, str):
                    schema_info['tables'] = tables
                elif schema_info.get('tables') and isinstance(schema_info['tables'][0] if schema_info['tables'] else None, dict):
                    # Extract table names from schema objects
                    schema_info['tables'] = [t['table_name'] if isinstance(t, dict) and 'table_name' in t else str(t) for t in schema_info['tables']]
                else:
                    schema_info['tables'] = tables or []
                
                schema_info['db_type'] = st.session_state.db_type
                schema_info['total_tables'] = len(tables) if tables else 0
                st.session_state.schema_info = schema_info
            else:
                # Use table names directly
                st.session_state.schema_info = {
                    'tables': tables or [],
                    'db_type': st.session_state.db_type,
                    'total_tables': len(tables) if tables else 0
                }
        except:
            # If get_database_info fails, use table names directly
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

# Force refresh schema_info if connected - ensure tables are always loaded
if st.session_state.connected and st.session_state.db_manager:
    try:
        # Always refresh tables list from database to ensure we have the latest
        tables = st.session_state.db_manager.get_tables()
        
        # Update schema_info with fresh table list
        if st.session_state.get('schema_info'):
            st.session_state.schema_info['tables'] = tables or []
            st.session_state.schema_info['total_tables'] = len(tables) if tables else 0
        else:
            # Create schema_info if it doesn't exist
            st.session_state.schema_info = {
                'tables': tables or [],
                'db_type': st.session_state.db_type,
                'total_tables': len(tables) if tables else 0
            }
    except Exception as e:
        # If refresh fails, try to preserve existing schema_info
        if not st.session_state.get('schema_info'):
            st.session_state.schema_info = {
                'tables': [],
                'db_type': st.session_state.db_type,
                'total_tables': 0
            }

# Initialize chatbot if connected but chatbot is None and API keys are available
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
            
            # Set schema context for chatbot
            if st.session_state.chatbot and st.session_state.get('schema_info'):
                try:
                    st.session_state.chatbot.set_schema_context(st.session_state.schema_info)
                except:
                    pass  # Schema context setting failed, but chatbot is still usable
    except Exception as e:
        # Silently fail - chatbot will remain None if initialization fails
        pass

if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'fixed_query' not in st.session_state:
    st.session_state.fixed_query = None
if 'layout_mode' not in st.session_state:
    st.session_state.layout_mode = 'tabs'  # Default: Tabs (Classic) layout
if 'last_quick_select' not in st.session_state:
    st.session_state.last_quick_select = "-- Select --"
if 'show_db_info' not in st.session_state:
    st.session_state.show_db_info = False  # Minimize by default
if 'show_chatbot' not in st.session_state:
    st.session_state.show_chatbot = True  # Show chatbot by default
if 'show_connection' not in st.session_state:
    st.session_state.show_connection = True  # Show connection section by default
# Check query params first to preserve section across refreshes
if 'active_section' not in st.session_state:
    # Check if there's a section in query params first
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
    
    # Use section from query params if available, otherwise default to home
    if section_from_query and section_from_query in ['home', 'chatbot', 'sql_editor', 'data_explorer', 'visualizations', 'smart_email_agent']:
        st.session_state.active_section = section_from_query
    else:
        st.session_state.active_section = 'home'  # Default to Home Dashboard
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False  # Light mode by default
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
    st.session_state.api_server_url = "http://localhost:8000"  # Default API URL


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
    
    # Rows per page selector - use unique key based on dataframe ID
    rows_per_page_key = f"rows_per_page_select_{id(df)}"
    rows_per_page_options = [50, 100, 250, 500, 1000]
    new_rows_per_page = st.selectbox(
        "Rows per page:",
        options=rows_per_page_options,
        index=rows_per_page_options.index(st.session_state.rows_per_page) if st.session_state.rows_per_page in rows_per_page_options else 1,
        key=rows_per_page_key
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


def inject_keyboard_shortcuts():
    """Inject JavaScript for keyboard shortcuts in SQL editor"""
    st.markdown("""
    <script>
    (function() {
        let shortcutsAttached = new Set();
        
        function attachShortcutsToTextarea(textarea) {
            // Skip if already attached
            if (shortcutsAttached.has(textarea)) return;
            
            // Mark as attached
            shortcutsAttached.add(textarea);
            
            // Add keyboard event listener with capture phase
            textarea.addEventListener('keydown', function(e) {
                // Helper: Check if Ctrl (Windows/Linux) or Cmd (Mac) is pressed
                const isModifierPressed = e.ctrlKey || e.metaKey;
                
                // Ctrl+Enter or Cmd+Enter: Execute query
                if (isModifierPressed && (e.key === 'Enter' || e.keyCode === 13)) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    // Small delay to ensure Streamlit has processed the input
                    setTimeout(function() {
                        // Try multiple methods to find and click the Run button
                        const allButtons = Array.from(document.querySelectorAll('button'));
                        let runButton = null;
                        
                        // Method 1: Try to find hidden execute button first (most reliable)
                        // Streamlit buttons have data-testid that includes the key
                        runButton = allButtons.find(btn => {
                            const testId = btn.getAttribute('data-testid') || '';
                            return testId.includes('hidden_execute_btn');
                        });
                        
                        // Also try finding by text content "Execute"
                        if (!runButton) {
                            runButton = allButtons.find(btn => {
                                const text = (btn.textContent || btn.innerText || '').trim();
                                const testId = btn.getAttribute('data-testid') || '';
                                return text === 'Execute' && testId.includes('hidden_execute');
                            });
                        }
                        
                        // Method 2: Find by text content (Run button)
                        if (!runButton) {
                            runButton = allButtons.find(btn => {
                                const text = (btn.textContent || btn.innerText || '').trim();
                                return text.includes('Run') || text.includes('▶') || text.includes('▶️') || text.includes('Execute');
                            });
                        }
                        
                        // Method 3: Find primary button
                        if (!runButton) {
                            runButton = allButtons.find(btn => {
                                return btn.classList.contains('primary') || 
                                       btn.getAttribute('data-baseweb') === 'button' ||
                                       (btn.type === 'button' && btn.getAttribute('data-testid')?.includes('baseButton'));
                            });
                        }
                        
                        if (runButton && !runButton.disabled) {
                            // Try multiple click methods
                            console.log('Found button, clicking...', runButton);
                            runButton.focus();
                            
                            // Try native click first
                            runButton.click();
                            
                            // Also try dispatching events
                            const clickEvent = new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                detail: 1
                            });
                            runButton.dispatchEvent(clickEvent);
                            
                            // Also try mousedown/mouseup
                            runButton.dispatchEvent(new MouseEvent('mousedown', { 
                                bubbles: true, 
                                cancelable: true,
                                view: window,
                                detail: 1
                            }));
                            runButton.dispatchEvent(new MouseEvent('mouseup', { 
                                bubbles: true, 
                                cancelable: true,
                                view: window,
                                detail: 1
                            }));
                            
                            // Also try focus and Enter key
                            runButton.focus();
                            runButton.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
                            runButton.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
                        } else {
                            console.log('Button not found. Total buttons:', allButtons.length);
                        }
                    }, 100);
                    return false;
                }
                
                // Ctrl+/ or Cmd+/: Toggle comment
                if (isModifierPressed && e.key === '/') {
                    e.preventDefault();
                    e.stopPropagation();
                    const start = textarea.selectionStart;
                    const end = textarea.selectionEnd;
                    const text = textarea.value;
                    const lines = text.split('\\n');
                    
                    // Find which lines are selected
                    let startLine = 0;
                    let endLine = 0;
                    let charCount = 0;
                    
                    // If no selection, use current line
                    if (start === end) {
                        for (let i = 0; i < lines.length; i++) {
                            if (charCount <= start && charCount + lines[i].length >= start) {
                                startLine = i;
                                endLine = i;
                                break;
                            }
                            charCount += lines[i].length + 1; // +1 for newline
                        }
                    } else {
                        // Find lines for selection
                        for (let i = 0; i < lines.length; i++) {
                            if (charCount <= start && charCount + lines[i].length >= start) {
                                startLine = i;
                            }
                            if (charCount <= end && charCount + lines[i].length >= end) {
                                endLine = i;
                                break;
                            }
                            charCount += lines[i].length + 1; // +1 for newline
                        }
                    }
                    
                    // Toggle comments on selected lines
                    let allCommented = true;
                    let hasNonEmptyLines = false;
                    for (let i = startLine; i <= endLine; i++) {
                        if (lines[i].trim()) {
                            hasNonEmptyLines = true;
                            if (!lines[i].trim().startsWith('--')) {
                                allCommented = false;
                                break;
                            }
                        }
                    }
                    
                    // Apply comment toggle
                    if (hasNonEmptyLines) {
                        for (let i = startLine; i <= endLine; i++) {
                            if (lines[i].trim()) {
                                if (allCommented) {
                                    // Remove comment (handle both '--' and '-- ')
                                    lines[i] = lines[i].replace(/^\\s*--\\s?/, '');
                                } else {
                                    // Add comment
                                    lines[i] = '-- ' + lines[i];
                                }
                            }
                        }
                    }
                    
                    const newText = lines.join('\\n');
                    textarea.value = newText;
                    
                    // Restore selection
                    textarea.setSelectionRange(start, end);
                    
                    // Trigger input event to update Streamlit
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    return false;
                }
                
                // Ctrl+S or Cmd+S: Save to history
                if (isModifierPressed && (e.key === 's' || e.keyCode === 83)) {
                    e.preventDefault();
                    e.stopPropagation();
                    // Find and click the Save button
                    setTimeout(function() {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const saveButton = buttons.find(btn => {
                            const text = (btn.textContent || btn.innerText || '').trim();
                            return text.includes('Save') || text.includes('💾');
                        });
                        if (saveButton && !saveButton.disabled) {
                            saveButton.click();
                        }
                    }, 50);
                    return false;
                }
                
                // Ctrl+L or Cmd+L: Clear editor
                if (isModifierPressed && (e.key === 'l' || e.keyCode === 76)) {
                    e.preventDefault();
                    e.stopPropagation();
                    textarea.value = '';
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    return false;
                }
            }, true); // Use capture phase for better event handling
        }
        
        function setupKeyboardShortcuts() {
            // Find all textareas
            const textareas = document.querySelectorAll('textarea');
            
            // Try to find SQL editor textarea
            let sqlEditor = null;
            for (let textarea of textareas) {
                // Check if it's the SQL editor by looking at the label
                const container = textarea.closest('[data-testid*="stTextArea"]') || 
                                 textarea.closest('.stTextArea') ||
                                 textarea.parentElement;
                if (container) {
                    const label = container.querySelector('label');
                    if (label && (label.textContent.includes('SQL') || label.textContent.includes('Query') || 
                        label.textContent.includes('Enter SQL'))) {
                        sqlEditor = textarea;
                        break;
                    }
                }
            }
            
            // Fallback: use the first textarea if we can't find the SQL editor
            if (!sqlEditor && textareas.length > 0) {
                sqlEditor = textareas[0];
            }
            
            // Attach shortcuts to found textarea
            if (sqlEditor) {
                attachShortcutsToTextarea(sqlEditor);
            }
        }
        
        // Use MutationObserver to watch for dynamically added textareas
        const observer = new MutationObserver(function(mutations) {
            setupKeyboardShortcuts();
        });
        
        // Start observing
        if (document.body) {
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
        
        // Initialize when page loads
        function init() {
            setupKeyboardShortcuts();
            // Also try multiple times to catch dynamically loaded content
            setTimeout(setupKeyboardShortcuts, 100);
            setTimeout(setupKeyboardShortcuts, 500);
            setTimeout(setupKeyboardShortcuts, 1000);
            setTimeout(setupKeyboardShortcuts, 2000);
        }
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
        
        // Also listen for Streamlit events
        if (window.parent) {
            window.parent.addEventListener('load', init);
        }
        
        // Document-level event listener as fallback (catches events even if textarea not found)
        document.addEventListener('keydown', function(e) {
            // Only handle if focus is on a textarea
            if (e.target && e.target.tagName === 'TEXTAREA') {
                const isModifierPressed = e.ctrlKey || e.metaKey;
                
                // Cmd+Enter or Ctrl+Enter: Execute query
                if (isModifierPressed && (e.key === 'Enter' || e.keyCode === 13)) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    // Try multiple methods to find and click the Run button
                    setTimeout(function() {
                        // Method 1: Try to find hidden execute button first (most reliable)
                        let runButton = null;
                        const allButtons = Array.from(document.querySelectorAll('button'));
                        
                        // Look for Run button by its Streamlit key attribute
                        // Streamlit buttons have data-testid that includes the key
                        runButton = allButtons.find(btn => {
                            const testId = btn.getAttribute('data-testid') || '';
                            return testId.includes('run_btn_tab') || testId.includes('run_btn_compact');
                        });
                        
                        // Also try finding by text content "Run"
                        if (!runButton) {
                            runButton = allButtons.find(btn => {
                                const text = (btn.textContent || btn.innerText || '').trim();
                                return text.includes('Run') || text.includes('▶') || text.includes('▶️');
                            });
                        }
                        
                        // Method 2: Find by text content (Run button)
                        if (!runButton) {
                            runButton = allButtons.find(btn => {
                                const text = (btn.textContent || btn.innerText || '').trim();
                                return text.includes('Run') || text.includes('▶') || text.includes('▶️') || text.includes('Execute');
                            });
                        }
                        
                        // Method 3: Find primary button (Run button is usually primary)
                        if (!runButton) {
                            runButton = allButtons.find(btn => {
                                return btn.classList.contains('primary') || 
                                       btn.getAttribute('data-baseweb') === 'button' ||
                                       (btn.type === 'button' && btn.getAttribute('data-testid')?.includes('baseButton'));
                            });
                        }
                        
                        // Method 4: Find first button in the action buttons row
                        if (!runButton && allButtons.length > 0) {
                            // Find the textarea first
                            const textarea = e.target;
                            const textareaContainer = textarea.closest('[data-testid*="stTextArea"]') || 
                                                      textarea.closest('.stTextArea') ||
                                                      textarea.parentElement;
                            if (textareaContainer) {
                                // Find the next sibling container with buttons
                                let nextSibling = textareaContainer.nextElementSibling;
                                while (nextSibling && !runButton) {
                                    const btn = nextSibling.querySelector('button[type="button"]');
                                    if (btn) {
                                        runButton = btn;
                                        break;
                                    }
                                    nextSibling = nextSibling.nextElementSibling;
                                }
                            }
                        }
                        
                        if (runButton && !runButton.disabled) {
                            // Try multiple click methods
                            console.log('Found button (document-level), clicking...', runButton);
                            runButton.focus();
                            
                            // Try native click first
                            runButton.click();
                            
                            // Also try dispatching events
                            const clickEvent = new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                view: window,
                                detail: 1
                            });
                            runButton.dispatchEvent(clickEvent);
                            
                            // Also try mousedown/mouseup
                            runButton.dispatchEvent(new MouseEvent('mousedown', { 
                                bubbles: true, 
                                cancelable: true,
                                view: window,
                                detail: 1
                            }));
                            runButton.dispatchEvent(new MouseEvent('mouseup', { 
                                bubbles: true, 
                                cancelable: true,
                                view: window,
                                detail: 1
                            }));
                            
                            // Also try focus and Enter key
                            runButton.focus();
                            runButton.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
                            runButton.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
                        } else {
                            console.log('Button not found (document-level). Total buttons:', allButtons.length);
                        }
                    }, 100);
                    return false;
                }
            }
        }, true); // Use capture phase
    })();
    </script>
    """, unsafe_allow_html=True)


def main():
    """Main application"""
    
    # Add autocomplete attributes to form fields via JavaScript
    st.markdown("""
    <script>
    (function() {
        function setAutocompleteAttributes() {
            // Find password inputs and set autocomplete
            const passwordInputs = document.querySelectorAll('input[type="password"]');
            passwordInputs.forEach(input => {
                if (!input.getAttribute('autocomplete')) {
                    input.setAttribute('autocomplete', 'current-password');
                }
            });
            
            // Find text inputs and set appropriate autocomplete based on label
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
        
        // Run on load and after delays
        setAutocompleteAttributes();
        setTimeout(setAutocompleteAttributes, 100);
        setTimeout(setAutocompleteAttributes, 500);
        setTimeout(setAutocompleteAttributes, 1000);
        
        // Also observe for dynamically added inputs
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
            // Find all input fields
            const inputs = document.querySelectorAll('input[type="text"], input[type="password"], input[type="number"], input[type="email"], input[type="url"], textarea');
            
            inputs.forEach(function(input, index) {
                // Skip if already has id
                if (input.id) return;
                
                // Get label to determine appropriate id/name
                const container = input.closest('[data-testid*="stTextInput"], [data-testid*="stTextArea"], [data-testid*="stNumberInput"]');
                let fieldName = 'field_' + index;
                
                if (container) {
                    const label = container.querySelector('label');
                    if (label && label.textContent) {
                        // Create id from label text
                        fieldName = label.textContent.toLowerCase()
                            .replace(/[^a-z0-9]+/g, '_')
                            .replace(/^_+|_+$/g, '')
                            .substring(0, 50) || 'field_' + index;
                    }
                }
                
                // Set id and name attributes
                const uniqueId = fieldName + '_' + Date.now() + '_' + index;
                input.id = uniqueId;
                input.name = fieldName;
            });
        }
        
        // Run on load and after delays
        setFormFieldAttributes();
        setTimeout(setFormFieldAttributes, 100);
        setTimeout(setFormFieldAttributes, 500);
        setTimeout(setFormFieldAttributes, 1000);
        
        // Also observe for dynamically added inputs
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
                // Skip if already has listener attached (check for data attribute)
                if (item.hasAttribute('data-listener-attached')) {
                    return;
                }
                
                console.log('Attaching listener to menu item', index, item);
                item.setAttribute('data-listener-attached', 'true');
                
                // Attach click listener directly
                item.addEventListener('click', function(e) {
                    console.log('Menu item clicked!', e);
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    const section = this.getAttribute('data-section');
                    console.log('Section:', section);
                    
                    if (section) {
                        const baseUrl = window.location.origin + window.location.pathname;
                        // Preserve any existing query params
                        const currentParams = new URLSearchParams(window.location.search);
                        currentParams.set('section', section);
                        const newUrl = baseUrl + '?' + currentParams.toString();
                        console.log('Navigating to:', newUrl);
                        // Use window.location.replace to avoid adding to history
                        window.location.replace(newUrl);
                    }
                }, false);
                
                // Ensure clicks work
                item.style.cursor = 'pointer';
                item.style.pointerEvents = 'auto';
            });
        }
        
        // Try multiple times to catch the elements
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', attachNavListeners);
        } else {
            attachNavListeners();
        }
        
        // Retry with delays
        setTimeout(attachNavListeners, 100);
        setTimeout(attachNavListeners, 500);
        setTimeout(attachNavListeners, 1000);
        setTimeout(attachNavListeners, 2000);
        
        // Use MutationObserver to catch dynamically added elements
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
    
    # Handle navigation via query parameters at the top level (most reliable)
    section_labels = {
        'home': '🏠 Home',
        'chatbot': '💬 AI SQL Assistant',
        'sql_editor': '📝 Smart SQL Editor',
        'data_explorer': '🔍 Data Explorer',
        'visualizations': '📊 Data Visualizations',
        'smart_email_agent': '📧 Smart Email Agent'
    }
    
    # Check query parameters first, before anything else
    try:
        if hasattr(st, 'query_params'):
            query_params = st.query_params
            if query_params and 'section' in query_params:
                section = query_params.get('section')
                # Handle both string and list formats
                if isinstance(section, list):
                    section = section[0] if section else None
                elif isinstance(section, str):
                    section = section.strip()
                
                if section and section in section_labels:
                    # Update active section if different
                    if st.session_state.active_section != section:
                        st.session_state.active_section = section
                        # Keep query param to persist across refreshes (don't clear it)
                        st.rerun()
    except Exception as e:
        # Continue if query params don't work
        pass
    
    # Inject dark mode CSS (must be called early)
    inject_dark_mode_css()
    
    # Inject keyboard shortcuts (must be called early)
    inject_keyboard_shortcuts()
    
    # Show auto-connection notification if applicable
    if st.session_state.get('auto_connected', False):
        st.session_state.auto_connected = False  # Only show once
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
            
            # Minimal divider - reduced spacing
            st.markdown("<hr style='margin: 0.25rem 0; border: none; border-top: 1px solid rgba(250, 250, 250, 0.2);'>", unsafe_allow_html=True)
            
            # Database Connection (standalone)
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
                # Update query param to persist across refreshes
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
            # Minimized header for three column layout when connected
            st.markdown("#### 🤖 AI Database Tool")
        else:
            # Header with title
            st.markdown("#### 🤖 AI Database Tool")
            st.markdown("Intelligent database management with AI-powered SQL generation")
            
            # Navigation dropdown below subtitle on the left
            if st.session_state.connected:
                nav_col1, nav_col2 = st.columns([1, 3])
                with nav_col1:
                    render_navigation_bar()
    
    # Render active section - Home and Smart Email Agent are always available, others require connection
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
            # Classic layout - render active section based on selection
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


def render_db_details():
    """Render connected database details by default in top-left"""
    if st.session_state.connected and st.session_state.db_manager:
        try:
            schema_info = st.session_state.get('schema_info', {})
            db_type = st.session_state.db_type or 'unknown'
            db_name = schema_info.get('database_name', 'unknown')
            
            # Format database name for display
            if db_type == 'sqlite':
                # Show just the filename for SQLite
                if '/' in db_name:
                    db_name = db_name.split('/')[-1]
                display_name = db_name
            else:
                display_name = db_name
            
            total_tables = schema_info.get('total_tables', 0)
            
            # Display in a compact info box
            st.info(f"🔌 **{db_type.upper()}** | {display_name} | {total_tables} tables")
        except Exception:
            st.info("🔌 **Connected**")
    else:
        st.info("🔌 **Not Connected**")


def render_settings_dropdown():
    """Render settings dropdown (Smart Editor, Layout, Theme) using Streamlit selectbox"""
    
    # Use a selectbox styled as a dropdown button for settings
    settings_options = {
        "⚙️ Settings": None,
        "⚡ Smart Editor": "editor",
        "📐 Layout": "layout",
        "🎨 Theme": "theme"
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
            "theme": "🎨 Theme"
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


def handle_connection(db_type, host, port, database, username, password):
    """Handle database connection logic"""
    # Warn if using /tmp/ for SQLite (will be wiped on restart)
    if db_type == "sqlite" and "/tmp/" in database:
        st.warning("⚠️ Using /tmp/ for SQLite database will be wiped on system restart! Use a persistent location like ~/.ai_db_tool/database.sqlite")
    
    if db_type == "sqlite":
        # ALWAYS use persistent path for SQLite to ensure data persistence
        # This prevents data loss from using /tmp/ or other temporary locations
        persistent_path = get_persistent_sqlite_path()
        database = persistent_path  # Force use of persistent path
        
        # Ensure directory exists for SQLite file
        db_path = Path(persistent_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        config = DatabaseConfig(
            db_type=db_type,
            host="",
            port=0,
            database=str(db_path.absolute()),  # Always use absolute persistent path
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
    
    # Example questions (only show if no chat history)
    if not st.session_state.chat_history and st.session_state.chatbot:
        st.markdown("**💡 Quick Start:**")
        example_questions = [
            ("Show me all tables", "Show me the list of all tables in the database"),
            ("Tables >10 records", "List tables that have more than 10 records"),
            ("Table columns", "What are the column names and data types for all tables?")
        ]
        
        # Use smaller buttons in a row
        cols = st.columns(3)
        for idx, (display_text, full_question) in enumerate(example_questions):
            with cols[idx]:
                if st.button(f"💬 {display_text}", key=f"compact_example_{idx}", use_container_width=True):
                    # Process the question
                    st.session_state.chat_history.append({'role': 'user', 'content': full_question})
                    with st.spinner("🤔 Thinking..."):
                        response = st.session_state.chatbot.chat(full_question, include_sql=True)
                    
                    if 'error' not in response:
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response['response'],
                            'sql_query': response.get('sql_query'),
                            'timestamp': response['timestamp']
                        })
                    else:
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response.get('response', response.get('error', 'Error occurred')),
                            'timestamp': response.get('timestamp', datetime.now().isoformat())
                        })
                    st.rerun()
        st.markdown("---")
    
    # Add marker before chat messages for compact layout
    st.markdown('<div id="chat-container-start-compact"></div>', unsafe_allow_html=True)
    
    # Display chat history
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history[-10:]:  # Show last 10 messages (increased from 5)
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                # Show explanation in collapsed expander by default
                with st.expander("💡 View Explanation", expanded=False):
                    st.chat_message("assistant").write(msg['content'])
                
                # Show SQL query in expanded form by default
                if 'sql_query' in msg and msg['sql_query']:
                    with st.expander("📝 Generated SQL", expanded=True):
                        st.code(msg['sql_query'], language='sql')
    else:
        if not st.session_state.chatbot:
            st.info("💡 AI chatbot requires an API key. Set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable.")
        else:
            st.info("Ask questions about your database")
    
    # Add marker after chat messages and JavaScript to wrap them for compact layout
    st.markdown("""
    <div id="chat-container-end-compact"></div>
    <script>
        (function() {
            function wrapCompactChatMessages() {
                const startMarker = document.getElementById('chat-container-start-compact');
                const endMarker = document.getElementById('chat-container-end-compact');
                if (!startMarker || !endMarker) return;
                
                // Check if wrapper already exists
                if (document.getElementById('chat-messages-scrollable-wrapper-compact')) return;
                
                // Find parent container
                let parent = startMarker.parentElement;
                if (!parent) return;
                
                // Create wrapper div
                const wrapper = document.createElement('div');
                wrapper.id = 'chat-messages-scrollable-wrapper-compact';
                wrapper.style.cssText = `
                    max-height: 50vh;
                    overflow-y: auto;
                    overflow-x: hidden;
                    padding: 0.5rem;
                    margin-bottom: 0.5rem;
                    border: 1px solid rgba(250, 250, 250, 0.2);
                    border-radius: 0.5rem;
                    background-color: rgba(0, 0, 0, 0.02);
                    scroll-behavior: smooth;
                `;
                
                // Collect all nodes between markers
                let node = startMarker.nextSibling;
                const nodesToMove = [];
                while (node && node !== endMarker) {
                    nodesToMove.push(node);
                    node = node.nextSibling;
                }
                
                // Move nodes into wrapper
                nodesToMove.forEach(n => wrapper.appendChild(n));
                
                // Insert wrapper after start marker
                startMarker.parentNode.insertBefore(wrapper, startMarker.nextSibling);
                
                // Auto-scroll to bottom
                wrapper.scrollTop = wrapper.scrollHeight;
            }
            
            // Run immediately and after delays
            wrapCompactChatMessages();
            setTimeout(wrapCompactChatMessages, 100);
            setTimeout(wrapCompactChatMessages, 500);
            
            // Also observe for changes
            const observer = new MutationObserver(function() {
                wrapCompactChatMessages();
                const wrapper = document.getElementById('chat-messages-scrollable-wrapper-compact');
                if (wrapper) {
                    wrapper.scrollTop = wrapper.scrollHeight;
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        })();
    </script>
    """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Ask about your database...")
    
    if user_input:
        # Check if chatbot is available when user actually tries to use it
        if not st.session_state.chatbot:
            st.error("❌ AI Chatbot is not available. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable to enable AI features.")
            return
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
        if st.button("▶️", type="primary", use_container_width=True, key="run_btn_compact", help="Execute Query"):
            execute_query(query)
    with action_col2:
        if st.button("🤖", use_container_width=True, help="Generate SQL"):
            generate_sql_query()
    with action_col3:
        if st.button("🚀 AI Opt", use_container_width=True):
            optimize_query(query)
    with action_col4:
        if st.button("🔧 Fix", use_container_width=True):
            debug_query(query)
    with action_col5:
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


def chatbot_tab():
    """AI Chatbot interface"""
    st.header("💬 AI SQL Assistant")
    st.markdown("Ask questions in natural language and get SQL queries generated automatically")
    
    # Don't show API key message on page load - only show when user tries to use it
    
    # Example questions section - only show if chatbot is available
    if not st.session_state.chat_history and st.session_state.chatbot:
        #st.markdown("### 💡 Example Questions to Get Started")
        #st.markdown("Click on any question below to get started:")
        
        example_questions = [
            "list of all tables in the database",
            "Tables with more than 10 records",
            "Column names and data types for all tables?"
        ]
        
        cols = st.columns(3)
        for idx, question in enumerate(example_questions):
            with cols[idx]:
                if st.button(f"❓ {question}", key=f"example_{idx}", use_container_width=True):
                    # Add the question to chat history and process it
                    st.session_state.chat_history.append({'role': 'user', 'content': question})
                    with st.spinner("🤔 Thinking..."):
                        response = st.session_state.chatbot.chat(question, include_sql=True)
                    
                    if 'error' not in response:
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response['response'],
                            'sql_query': response.get('sql_query'),
                            'timestamp': response['timestamp']
                        })
                    else:
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response.get('response', response.get('error', 'Error occurred')),
                            'timestamp': response.get('timestamp', datetime.now().isoformat())
                        })
                    st.rerun()
        
        st.markdown("---")
    
    # Add marker before chat messages
    st.markdown('<div id="chat-container-start"></div>', unsafe_allow_html=True)
    
    # Display chat history
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                # Show explanation in collapsed expander by default
                with st.expander("💡 View Explanation", expanded=False):
                    st.chat_message("assistant").write(msg['content'])
                
                # Show SQL query in expanded form by default
                if 'sql_query' in msg and msg['sql_query']:
                    with st.expander("📝 Generated SQL", expanded=True):
                        st.code(msg['sql_query'], language='sql')
                        if st.button(f"Execute Query", key=f"exec_{msg['timestamp']}"):
                            execute_generated_query(msg['sql_query'])
    # else:
    #     st.info("💬 Start chatting by typing a message below!")
    
    # Add marker after chat messages and JavaScript to wrap them
    st.markdown("""
    <div id="chat-container-end"></div>
    <script>
        (function() {
            function wrapChatMessages() {
                const startMarker = document.getElementById('chat-container-start');
                const endMarker = document.getElementById('chat-container-end');
                if (!startMarker || !endMarker) return;
                
                // Check if wrapper already exists
                if (document.getElementById('chat-messages-scrollable-wrapper')) return;
                
                // Find parent container
                let parent = startMarker.parentElement;
                if (!parent) return;
                
                // Create wrapper div
                const wrapper = document.createElement('div');
                wrapper.id = 'chat-messages-scrollable-wrapper';
                wrapper.style.cssText = `
                    max-height: 60vh;
                    overflow-y: auto;
                    overflow-x: hidden;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    border: 1px solid rgba(250, 250, 250, 0.2);
                    border-radius: 0.5rem;
                    background-color: rgba(0, 0, 0, 0.02);
                    scroll-behavior: smooth;
                `;
                
                // Collect all nodes between markers
                let node = startMarker.nextSibling;
                const nodesToMove = [];
                while (node && node !== endMarker) {
                    nodesToMove.push(node);
                    node = node.nextSibling;
                }
                
                // Move nodes into wrapper
                nodesToMove.forEach(n => wrapper.appendChild(n));
                
                // Insert wrapper after start marker
                startMarker.parentNode.insertBefore(wrapper, startMarker.nextSibling);
                
                // Auto-scroll to bottom
                wrapper.scrollTop = wrapper.scrollHeight;
            }
            
            // Run immediately and after delays
            wrapChatMessages();
            setTimeout(wrapChatMessages, 100);
            setTimeout(wrapChatMessages, 500);
            
            // Also observe for changes
            const observer = new MutationObserver(function() {
                wrapChatMessages();
                const wrapper = document.getElementById('chat-messages-scrollable-wrapper');
                if (wrapper) {
                    wrapper.scrollTop = wrapper.scrollHeight;
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        })();
    </script>
    """, unsafe_allow_html=True)
    
    # Chat input (outside scrollable container, stays at bottom)
    user_input = st.chat_input("Ask me anything about your database...")
    
    if user_input:
        # Check if chatbot is available when user actually tries to use it
        if not st.session_state.chatbot:
            st.error("❌ AI Chatbot is not available. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable to enable AI features.")
            return
        
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
            if st.button("▶️", type="primary", use_container_width=True, key="run_btn_tab", help="Execute Query"):
                execute_query(query)
        with action_col2:
            if st.button("🤖", use_container_width=True, help="Generate SQL"):
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
            # Remove trailing semicolons that sqlparse might leave
            statements = [stmt.rstrip(';').strip() for stmt in statements if stmt.rstrip(';').strip()]
            return statements
        except Exception as e:
            # Fallback to improved split if sqlparse fails
            pass
    
    # Improved fallback: handle semicolons in quotes and comments
    statements = []
    current = []
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = False
    i = 0
    
    while i < len(query):
        char = query[i]
        next_char = query[i + 1] if i + 1 < len(query) else ''
        
        # Handle block comments
        if char == '/' and next_char == '*' and not in_single_quote and not in_double_quote:
            in_block_comment = True
            current.append(char)
            current.append(next_char)
            i += 2
            continue
        
        if in_block_comment:
            current.append(char)
            if char == '*' and next_char == '/':
                in_block_comment = False
                current.append(next_char)
                i += 2
                continue
            i += 1
            continue
        
        # Handle line comments
        if char == '-' and next_char == '-' and not in_single_quote and not in_double_quote:
            in_line_comment = True
            current.append(char)
            current.append(next_char)
            i += 2
            # Continue until newline
            while i < len(query) and query[i] != '\n':
                current.append(query[i])
                i += 1
            if i < len(query):
                current.append(query[i])  # Add the newline
                in_line_comment = False
            i += 1
            continue
        
        if in_line_comment:
            current.append(char)
            i += 1
            continue
        
        # Handle quotes
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(char)
            i += 1
            continue
        
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(char)
            i += 1
            continue
        
        # Handle semicolon (statement separator)
        if char == ';' and not in_single_quote and not in_double_quote and not in_line_comment and not in_block_comment:
            stmt = ''.join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            i += 1
            continue
        
        current.append(char)
        i += 1
    
    # Add remaining statement (if any)
    if current:
        stmt = ''.join(current).strip()
        if stmt:
            statements.append(stmt)
    
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
    try:
        statements = split_sql_statements(query)
    except Exception as e:
        st.error(f"❌ Failed to parse SQL statements: {e}")
        st.info("💡 Tip: Make sure your SQL statements are properly formatted and separated by semicolons (;)")
        return
    
    if not statements:
        st.warning("No valid SQL statements found. Please check your SQL syntax.")
        st.info("💡 Tip: SQL statements should be separated by semicolons (;)")
        return
    
    # Show info for multiple statements
    if len(statements) > 1:
        st.info(f"📋 Detected {len(statements)} SQL statements. They will be executed sequentially.")
    
    # If single statement, use original behavior for backward compatibility
    if len(statements) == 1:
        single_statement = statements[0]
        result = execute_single_statement(single_statement)
        
        if not result['success']:
            st.error(f"❌ Query execution failed: {result['error']}")
            st.code(single_statement, language='sql')
            st.info("💡 Tip: Check your SQL syntax, table/column names, and ensure you're connected to the database.")
            return
        
        # Handle single statement results (original behavior)
        if result['type'] == 'SELECT':
            # Compact Results header with download icon in same line
            result_col1, result_col2 = st.columns([10, 1])
            with result_col1:
                st.markdown("**📊 Results**", unsafe_allow_html=True)
            with result_col2:
                csv = result['dataframe'].to_csv(index=False)
                st.download_button(
                    "📥",
                    csv,
                    "results.csv",
                    "text/csv",
                    help=f"Download CSV - {len(result['dataframe']):,} rows",
                    use_container_width=True
                )
            
            st.session_state.current_page = 1
            display_paginated_dataframe(result['dataframe'])
            st.session_state.last_result_df = result['dataframe']
            st.session_state.last_result = result['dataframe']
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
                st.info("💡 This statement failed, but other statements will continue executing.")
    
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
        # Compact Results header with download icon in same line
        result_col1, result_col2 = st.columns([10, 1])
        with result_col1:
            st.markdown("**📊 Last Query Results**", unsafe_allow_html=True)
        with result_col2:
            csv = last_select_result.to_csv(index=False)
            st.download_button(
                "📥",
                csv,
                "results.csv",
                "text/csv",
                help=f"Download CSV - {len(last_select_result):,} rows",
                use_container_width=True
            )
        
        st.session_state.current_page = 1
        display_paginated_dataframe(last_select_result)


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

