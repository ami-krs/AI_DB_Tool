"""Page modules for different sections"""
from .home import home_dashboard
from .chatbot import chatbot_tab, chatbot_compact
from .sql_editor import sql_editor_tab, sql_editor_compact
from .data_explorer import data_explorer_tab, data_explorer_compact
from .visualizations import visualizations_tab, visualizations_compact
from .smart_email_agent import smart_email_agent
from .layouts import three_column_layout

__all__ = [
    'home_dashboard',
    'chatbot_tab',
    'chatbot_compact',
    'sql_editor_tab',
    'sql_editor_compact',
    'data_explorer_tab',
    'data_explorer_compact',
    'visualizations_tab',
    'visualizations_compact',
    'smart_email_agent',
    'three_column_layout'
]
