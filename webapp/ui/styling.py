"""UI styling functions for CSS and JavaScript injection"""
import streamlit as st

def inject_base_css():
    """Inject base CSS for the application"""
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


