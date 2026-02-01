"""Helper utility functions"""
import streamlit as st
import os
from typing import Optional

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

def display_paginated_dataframe(df, unique_suffix=None):
    """Display dataframe with pagination controls
    
    Args:
        df: DataFrame to display
        unique_suffix: Optional unique suffix for keys to avoid conflicts when called multiple times
    """
    if df is None or len(df) == 0:
        st.info("No data to display")
        return
    
    # Generate unique key suffix to avoid conflicts
    if unique_suffix is None:
        import time
        unique_suffix = f"{id(df)}_{int(time.time() * 1000000) % 1000000}"
    
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
    
    # Rows per page selector - use unique key based on dataframe ID and unique suffix
    rows_per_page_key = f"rows_per_page_select_{unique_suffix}"
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
        button_key_prefix = f"pagination_{unique_suffix}"
        
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
