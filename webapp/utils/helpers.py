"""Helper utility functions"""
import streamlit as st
import os
import pandas as pd
from typing import Optional, Dict, Any
import plotly.express as px
import plotly.graph_objects as go

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
    
    # Display paginated data with small visualization icon positioned with hover icons
    paginated_df = df.iloc[start_idx:end_idx]
    
    # Add small visualization icon button positioned with Streamlit's built-in hover icons
    viz_icon_key = f"viz_icon_{unique_suffix}"
    viz_state_key = f"viz_active_{viz_icon_key}"
    if viz_state_key not in st.session_state:
        st.session_state[viz_state_key] = False
    
    # DEBUG: Add debug info for visualization icon
    debug_key = f"viz_debug_{unique_suffix}"
    if debug_key not in st.session_state:
        st.session_state[debug_key] = {
            'button_clicked': False,
            'state_before': False,
            'state_after': False,
            'click_count': 0
        }
    
    # Create a container with relative positioning to overlay the icon
    st.markdown("""
    <style>
        /* Style for visualization icon overlay - positioned like Streamlit's hover icons */
        .dataframe-viz-wrapper {
            position: relative;
            display: inline-block;
            width: 100%;
        }
        .viz-icon-floating {
            position: absolute;
            top: 8px;
            right: 8px;
            z-index: 1000;
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
            cursor: pointer;
        }
        .viz-icon-floating:hover {
            background: rgba(240, 240, 240, 0.98);
            box-shadow: 0 2px 4px rgba(0,0,0,0.15);
            transform: scale(1.05);
        }
        /* Ensure dataframe container is relative */
        div[data-testid="stDataFrame"] {
            position: relative;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Display dataframe first
    st.dataframe(paginated_df, hide_index=True, use_container_width=True)
    
    # Add visualization toggle checkbox right after dataframe
    button_key = f"viz_btn_{viz_icon_key}"
    
    # Initialize debug info if needed
    if debug_key not in st.session_state:
        st.session_state[debug_key] = {
            'button_clicked': False,
            'state_before': False,
            'state_after': False,
            'click_count': 0
        }
    
    debug_info = st.session_state[debug_key]
    current_state = st.session_state.get(viz_state_key, False)
    
    # Initialize checkbox state in session state if not exists
    if button_key not in st.session_state:
        st.session_state[button_key] = current_state
    
    # Use checkbox for more reliable toggle behavior
    # Position it in a small column on the right side
    toggle_col1, toggle_col2 = st.columns([0.97, 0.03])
    with toggle_col1:
        st.empty()  # Spacer to align with dataframe
    with toggle_col2:
        # Checkbox - value is automatically stored in st.session_state[button_key]
        checkbox_value = st.checkbox(
            "📊",
            value=st.session_state.get(button_key, current_state),
            help="Toggle Data Visualization",
            key=button_key,
            label_visibility="collapsed"
        )
        
        # Read the actual value from session state (checkbox updates it automatically)
        actual_state = st.session_state.get(button_key, False)
        
        # Update our state key if checkbox value changed
        if actual_state != current_state:
            old_state = current_state
            debug_info['button_clicked'] = True
            debug_info['state_before'] = old_state
            debug_info['click_count'] = debug_info.get('click_count', 0) + 1
            st.session_state[viz_state_key] = actual_state
            debug_info['state_after'] = actual_state
            print(f"DEBUG: Visualization toggle changed - key: {button_key}, state: {old_state} -> {actual_state}")
            st.session_state[debug_key] = debug_info
        else:
            # Sync state if they're out of sync
            if st.session_state.get(viz_state_key, False) != actual_state:
                st.session_state[viz_state_key] = actual_state
    
    # DEBUG: Show debug info in expander (always visible for debugging)
    with st.expander("🔍 Visualization Debug Info", expanded=True):
        debug_info = st.session_state.get(debug_key, {})
        current_state = st.session_state.get(viz_state_key, False)
        button_key_display = f"viz_btn_{viz_icon_key}"
        
        st.write(f"**Button Key:** `{button_key_display}`")
        st.write(f"**State Key:** `{viz_state_key}`")
        st.write(f"**Current State:** `{current_state}`")
        st.write(f"**Button Clicked (Last):** `{debug_info.get('button_clicked', False)}`")
        st.write(f"**State Before Click:** `{debug_info.get('state_before', False)}`")
        st.write(f"**State After Click:** `{debug_info.get('state_after', False)}`")
        st.write(f"**Click Count:** `{debug_info.get('click_count', 0)}`")
        st.write(f"**DataFrame Rows:** `{len(df)}`")
        st.write(f"**Paginated Rows:** `{len(paginated_df)}`")
        st.write(f"**Unique Suffix:** `{unique_suffix}`")
        
        # Show all session state keys related to visualization
        viz_keys = [k for k in st.session_state.keys() if 'viz' in k.lower() or 'visualization' in k.lower()]
        st.write(f"**All Viz-related Keys:** `{viz_keys}`")
        
        # Test button to manually toggle state
        if st.button("🔧 Test Toggle State", key=f"test_toggle_{unique_suffix}"):
            old_state = st.session_state.get(viz_state_key, False)
            st.session_state[viz_state_key] = not old_state
            st.rerun()
    
    # Display visualization if active (right after dataframe and toggle)
    # Get the current state after checkbox update
    viz_active = st.session_state.get(viz_state_key, False)
    if viz_active:
        print(f"DEBUG: Visualization is active, calling visualize_dataframe with suffix: viz_{unique_suffix}")
        st.markdown("---")  # Separator before visualization
        try:
            visualize_dataframe(df, unique_suffix=f"viz_{unique_suffix}")
        except Exception as e:
            st.error(f"Error displaying visualization: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            print(f"DEBUG: Visualization error: {e}")
            print(traceback.format_exc())
    
    # Show info if paginated
    if total_pages > 1:
        st.caption(f"📄 Displaying page {st.session_state.current_page} of {total_pages} ({len(paginated_df):,} rows)")


def search_dataframe(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
    """
    Search/filter dataframe based on search term across all columns
    
    Args:
        df: DataFrame to search
        search_term: Search term to filter by
        
    Returns:
        Filtered DataFrame
    """
    if not search_term or search_term.strip() == "":
        return df
    
    search_term = search_term.strip().lower()
    
    # Create a mask for rows that match the search term in any column
    mask = pd.Series([False] * len(df))
    
    for col in df.columns:
        # Convert column to string and search (case-insensitive)
        col_str = df[col].astype(str).str.lower()
        mask |= col_str.str.contains(search_term, na=False, regex=False)
    
    return df[mask].reset_index(drop=True)


def visualize_dataframe(df: pd.DataFrame, unique_suffix: str = None):
    """
    Display interactive data visualization options for the dataframe
    
    Args:
        df: DataFrame to visualize
        unique_suffix: Optional unique suffix for session state keys
    """
    if df is None or len(df) == 0:
        st.warning("No data to visualize")
        return
    
    if unique_suffix is None:
        import time
        unique_suffix = f"{id(df)}_{int(time.time() * 1000000) % 1000000}"
    
    # Don't use expander - display directly to avoid hiding issues
    st.markdown("### 📊 Data Visualization")
    # Get numeric columns for charts
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    if len(numeric_cols) == 0 and len(categorical_cols) == 0:
        st.info("No numeric or categorical columns available for visualization")
        return
    
    # Visualization type selector
    viz_type_key = f"viz_type_{unique_suffix}"
    viz_type = st.selectbox(
        "Chart Type:",
        options=["Bar Chart", "Line Chart", "Scatter Plot", "Histogram", "Box Plot", "Pie Chart"],
        key=viz_type_key
    )
    
    # Chart configuration based on type
    if viz_type == "Bar Chart":
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            x_col_key = f"bar_x_{unique_suffix}"
            y_col_key = f"bar_y_{unique_suffix}"
            x_col = st.selectbox("X-axis (Category):", categorical_cols, key=x_col_key)
            y_col = st.selectbox("Y-axis (Value):", numeric_cols, key=y_col_key)
            
            # Aggregate if needed (handle duplicates)
            if df[x_col].duplicated().any():
                agg_df = df.groupby(x_col)[y_col].sum().reset_index()
                fig = px.bar(agg_df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
            else:
                fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Bar chart requires at least one categorical and one numeric column")
    
    elif viz_type == "Line Chart":
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            x_col_key = f"line_x_{unique_suffix}"
            y_col_key = f"line_y_{unique_suffix}"
            x_col = st.selectbox("X-axis:", categorical_cols + numeric_cols, key=x_col_key)
            y_col = st.selectbox("Y-axis:", numeric_cols, key=y_col_key)
            
            # Sort by x-axis for line chart
            if x_col in numeric_cols:
                sorted_df = df.sort_values(x_col)
            else:
                sorted_df = df.sort_values(x_col)
            fig = px.line(sorted_df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Line chart requires at least one categorical/numeric and one numeric column")
    
    elif viz_type == "Scatter Plot":
        if len(numeric_cols) >= 2:
            x_col_key = f"scatter_x_{unique_suffix}"
            y_col_key = f"scatter_y_{unique_suffix}"
            color_col_key = f"scatter_color_{unique_suffix}"
            x_col = st.selectbox("X-axis:", numeric_cols, key=x_col_key)
            y_col = st.selectbox("Y-axis:", numeric_cols, key=y_col_key)
            color_col = st.selectbox("Color by (optional):", [None] + categorical_cols, key=color_col_key)
            
            if color_col:
                fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=f"{y_col} vs {x_col}")
            else:
                fig = px.scatter(df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Scatter plot requires at least two numeric columns")
    
    elif viz_type == "Histogram":
        if len(numeric_cols) > 0:
            col_key = f"hist_col_{unique_suffix}"
            col = st.selectbox("Column:", numeric_cols, key=col_key)
            bins_key = f"hist_bins_{unique_suffix}"
            bins = st.slider("Number of bins:", 10, 100, 30, key=bins_key)
            fig = px.histogram(df, x=col, nbins=bins, title=f"Distribution of {col}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Histogram requires at least one numeric column")
    
    elif viz_type == "Box Plot":
        if len(numeric_cols) > 0:
            y_col_key = f"box_y_{unique_suffix}"
            x_col_key = f"box_x_{unique_suffix}"
            y_col = st.selectbox("Y-axis (Value):", numeric_cols, key=y_col_key)
            x_col = st.selectbox("X-axis (Category, optional):", [None] + categorical_cols, key=x_col_key)
            
            if x_col:
                fig = px.box(df, x=x_col, y=y_col, title=f"Box Plot: {y_col} by {x_col}")
            else:
                fig = px.box(df, y=y_col, title=f"Box Plot: {y_col}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Box plot requires at least one numeric column")
    
    elif viz_type == "Pie Chart":
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            label_col_key = f"pie_label_{unique_suffix}"
            value_col_key = f"pie_value_{unique_suffix}"
            label_col = st.selectbox("Category:", categorical_cols, key=label_col_key)
            value_col = st.selectbox("Value:", numeric_cols, key=value_col_key)
            
            # Aggregate if needed
            if df[label_col].duplicated().any():
                agg_df = df.groupby(label_col)[value_col].sum().reset_index()
                fig = px.pie(agg_df, names=label_col, values=value_col, title=f"{value_col} by {label_col}")
            else:
                fig = px.pie(df, names=label_col, values=value_col, title=f"{value_col} by {label_col}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Pie chart requires at least one categorical and one numeric column")
