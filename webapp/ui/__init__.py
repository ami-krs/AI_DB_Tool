"""UI components module"""
from .styling import inject_dark_mode_css, inject_keyboard_shortcuts, inject_base_css
from .components import (
    render_db_details,
    render_settings_dropdown,
    render_setting_content,
    render_smart_editor_setting,
    render_layout_setting,
    render_theme_setting,
    render_connection_setting,
    render_sql_editor,
    handle_connection
)
from .navigation import render_navigation_bar

__all__ = [
    'inject_dark_mode_css',
    'inject_keyboard_shortcuts',
    'inject_base_css',
    'render_db_details',
    'render_settings_dropdown',
    'render_setting_content',
    'render_smart_editor_setting',
    'render_layout_setting',
    'render_theme_setting',
    'render_connection_setting',
    'render_sql_editor',
    'handle_connection',
    'render_navigation_bar'
]
