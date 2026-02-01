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


