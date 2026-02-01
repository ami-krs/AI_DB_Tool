"""Database configuration management"""
import streamlit as st
import json
from pathlib import Path
from typing import Optional

from ai_db_tool.connectors import DatabaseConfig

# Configuration file path for persistent storage
# Use project directory for SQLite DB to ensure consistency
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_DIR = PROJECT_ROOT / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)  # Ensure data directory exists

# Config directory - use home directory for user-specific config
CONFIG_DIR = Path.home() / ".ai_db_tool"
CONFIG_FILE = CONFIG_DIR / "db_config.json"

def ensure_config_dir():
    """Ensure config directory exists"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def get_persistent_sqlite_path():
    """
    Get persistent SQLite database path (returns absolute path as string)
    Priority:
    1. Streamlit secrets (if available)
    2. Project directory: {project_root}/data/database.sqlite
    """
    # Try to get path from Streamlit secrets first
    secret_path_used = None
    try:
        if hasattr(st, 'secrets') and st.secrets:
            # Check for SQLite database path in secrets
            if 'database' in st.secrets:
                db_secrets = st.secrets.database
                if isinstance(db_secrets, dict) and 'sqlite_path' in db_secrets:
                    secret_path = db_secrets.sqlite_path
                    if secret_path:
                        # Ensure it's an absolute path
                        secret_path_used = str(Path(secret_path).absolute())
                        print(f"DEBUG: Using database path from secrets [database.sqlite_path]: {secret_path_used}")
                        return secret_path_used
            # Alternative: direct key in secrets
            if 'SQLITE_DB_PATH' in st.secrets:
                secret_path = st.secrets.SQLITE_DB_PATH
                if secret_path:
                    secret_path_used = str(Path(secret_path).absolute())
                    print(f"DEBUG: Using database path from secrets [SQLITE_DB_PATH]: {secret_path_used}")
                    return secret_path_used
    except Exception as e:
        # If secrets access fails, fall through to default
        print(f"DEBUG: Error reading secrets: {e}")
    
    # Default: Use project directory
    default_path = DB_DIR / "database.sqlite"
    default_path_str = str(default_path.absolute())
    print(f"DEBUG: Using default database path (project directory): {default_path_str}")
    return default_path_str

def save_db_config(config: DatabaseConfig):
    """Save database configuration to persistent storage"""
    try:
        ensure_config_dir()
        config_dict = {
            'db_type': config.db_type,
            'host': config.host,
            'port': config.port,
            'database': config.database,
            'username': config.username,
            'password': config.password,  # Note: In production, use encryption
            'extra_params': config.extra_params or {}
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_dict, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Failed to save connection config: {e}")
        return False

def load_db_config() -> Optional[DatabaseConfig]:
    """Load database configuration from persistent storage"""
    try:
        if not CONFIG_FILE.exists():
            return None
        
        with open(CONFIG_FILE, 'r') as f:
            config_dict = json.load(f)
        
        db_type = config_dict.get('db_type', 'postgresql')
        database = config_dict.get('database', '')
        
        # For SQLite, always use persistent path in project directory
        if db_type == 'sqlite':
            persistent_path = get_persistent_sqlite_path()
            # Always use the project directory path, regardless of what's saved
            database = persistent_path
            
            # If saved path is different, update config file to use project directory path
            old_db_path = config_dict.get('database', '')
            if old_db_path and Path(old_db_path).resolve() != Path(persistent_path).resolve():
                config_dict['database'] = database
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config_dict, f, indent=2)
        
        return DatabaseConfig(
            db_type=db_type,
            host=config_dict.get('host', ''),
            port=config_dict.get('port', 5432),
            database=database,
            username=config_dict.get('username', ''),
            password=config_dict.get('password', ''),
            extra_params=config_dict.get('extra_params', {})
        )
    except Exception as e:
        st.warning(f"Could not load saved connection: {e}")
        return None
