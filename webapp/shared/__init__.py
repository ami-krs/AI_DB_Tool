"""Shared components and constants"""
import os
import sys

# Try to import CodeMirror editor component
try:
    from components.codemirror_editor import codemirror_editor
    CODEMIRROR_AVAILABLE = True
except ImportError:
    try:
        components_path = os.path.join(os.path.dirname(__file__), '..', 'components')
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
        components_path = os.path.join(os.path.dirname(__file__), '..', 'components')
        if components_path not in sys.path:
            sys.path.insert(0, components_path)
        from monaco_editor import monaco_editor
        MONACO_EDITOR_AVAILABLE = True
    except ImportError:
        MONACO_EDITOR_AVAILABLE = False
        monaco_editor = None

__all__ = [
    'CODEMIRROR_AVAILABLE',
    'MONACO_EDITOR_AVAILABLE',
    'codemirror_editor',
    'monaco_editor'
]
