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


