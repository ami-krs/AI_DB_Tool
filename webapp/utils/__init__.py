"""Utility functions for the application"""
from .helpers import get_api_key, display_paginated_dataframe
from .query_execution import (
    split_sql_statements,
    execute_single_statement,
    execute_query,
    execute_generated_query,
    show_table_details,
    show_common_queries,
    generate_sql_query,
    optimize_query,
    debug_query,
    save_query_to_history
)

__all__ = [
    'get_api_key',
    'display_paginated_dataframe',
    'split_sql_statements',
    'execute_single_statement',
    'execute_query',
    'execute_generated_query',
    'show_table_details',
    'show_common_queries',
    'generate_sql_query',
    'optimize_query',
    'debug_query',
    'save_query_to_history'
]
