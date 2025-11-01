"""
AI-Powered Universal Database Tool
A comprehensive database management and query tool with AI capabilities
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .connectors import DatabaseManager
from .ai import AIQueryBuilder, SQLChatbot

# SmartSQLEditor will be implemented later
# from .editor import SmartSQLEditor

__all__ = [
    "__version__",
    "DatabaseManager",
    "AIQueryBuilder",
    "SQLChatbot",
    # "SmartSQLEditor",
]

