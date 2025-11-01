"""
Base database connector and universal database manager
Supports PostgreSQL, MySQL, SQL Server, Oracle, SQLite, and more
"""

from __future__ import annotations
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from sqlalchemy import create_engine, text, MetaData, inspect
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
import pandas as pd

import keyring


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    db_type: str  # postgresql, mysql, sqlserver, oracle, sqlite
    host: str
    port: int
    database: str
    username: str
    password: str
    extra_params: Optional[Dict[str, Any]] = None


class BaseConnector(ABC):
    """Abstract base class for database connectors"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish database connection"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close database connection"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        pass
    
    @abstractmethod
    def execute_non_query(self, query: str) -> int:
        """Execute non-query SQL (INSERT, UPDATE, DELETE) and return rows affected"""
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        pass


class DatabaseManager:
    """Universal database manager supporting multiple database types"""
    
    SUPPORTED_DB_TYPES = {
        'postgresql': 'postgresql+psycopg2://',
        'mysql': 'mysql+mysqlconnector://',
        'sqlserver': 'mssql+pymssql://',
        'oracle': 'oracle+cx_oracle://',
        'sqlite': 'sqlite:///',
    }
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.config: Optional[DatabaseConfig] = None
        self.connections: Dict[str, Engine] = {}
    
    def _build_connection_string(self, config: DatabaseConfig) -> str:
        """Build SQLAlchemy connection string"""
        db_type = config.db_type.lower()
        
        if db_type not in self.SUPPORTED_DB_TYPES:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        dialect = self.SUPPORTED_DB_TYPES[db_type]
        
        if db_type == 'sqlite':
            return f"{dialect}{config.database}"
        
        # Build URL for other database types
        url = f"{dialect}{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
        
        # Add extra parameters if provided
        if config.extra_params:
            params = '&'.join([f"{k}={v}" for k, v in config.extra_params.items()])
            url = f"{url}?{params}"
        
        return url
    
    def connect(self, config: Optional[DatabaseConfig] = None, connection_id: str = "default") -> bool:
        """
        Connect to database
        
        Args:
            config: Database configuration
            connection_id: Unique identifier for this connection
            
        Returns:
            True if connected successfully
        """
        if config:
            self.config = config
        elif not self.config:
            raise ValueError("No configuration provided")
        
        try:
            conn_string = self._build_connection_string(self.config)
            self.engine = create_engine(conn_string, pool_pre_ping=True)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.connections[connection_id] = self.engine
            return True
            
        except SQLAlchemyError as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def get_engine(self, connection_id: str = "default") -> Optional[Engine]:
        """Get SQLAlchemy engine for a connection"""
        return self.connections.get(connection_id)
    
    def execute_query(self, query: str, connection_id: str = "default") -> pd.DataFrame:
        """
        Execute SELECT query and return results as DataFrame
        
        Args:
            query: SQL query string
            connection_id: Connection identifier
            
        Returns:
            DataFrame with query results
        """
        engine = self.get_engine(connection_id)
        if not engine:
            raise ValueError("No active connection")
        
        try:
            return pd.read_sql(query, engine)
        except SQLAlchemyError as e:
            raise ValueError(f"Query execution failed: {e}")
    
    def execute_non_query(self, query: str, connection_id: str = "default") -> int:
        """
        Execute non-query SQL (INSERT, UPDATE, DELETE, DDL)
        
        Args:
            query: SQL statement
            connection_id: Connection identifier
            
        Returns:
            Number of rows affected
        """
        engine = self.get_engine(connection_id)
        if not engine:
            raise ValueError("No active connection")
        
        try:
            with engine.begin() as conn:
                result = conn.execute(text(query))
                return result.rowcount
        except SQLAlchemyError as e:
            raise ValueError(f"Query execution failed: {e}")
    
    def get_tables(self, connection_id: str = "default") -> List[str]:
        """Get list of all tables in the database"""
        engine = self.get_engine(connection_id)
        if not engine:
            raise ValueError("No active connection")
        
        inspector = inspect(engine)
        return inspector.get_table_names()
    
    def get_table_schema(self, table_name: str, connection_id: str = "default") -> Dict[str, Any]:
        """Get schema information for a specific table"""
        engine = self.get_engine(connection_id)
        if not engine:
            raise ValueError("No active connection")
        
        inspector = inspect(engine)
        
        columns = []
        for col in inspector.get_columns(table_name):
            columns.append({
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': col.get('default'),
                'primary_key': col.get('primary_key', False),
            })
        
        # Get primary keys
        pk_constraint = inspector.get_pk_constraint(table_name)
        primary_keys = pk_constraint.get('constrained_columns', [])
        
        # Get foreign keys
        foreign_keys = inspector.get_foreign_keys(table_name)
        
        return {
            'table_name': table_name,
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys,
        }
    
    def get_database_info(self, connection_id: str = "default") -> Dict[str, Any]:
        """Get comprehensive database information"""
        engine = self.get_engine(connection_id)
        if not engine:
            raise ValueError("No active connection")
        
        tables = self.get_tables(connection_id)
        
        info = {
            'database_type': self.config.db_type if self.config else 'unknown',
            'database_name': self.config.database if self.config else 'unknown',
            'total_tables': len(tables),
            'tables': [],
        }
        
        for table in tables[:20]:  # Limit to first 20 tables for performance
            schema = self.get_table_schema(table, connection_id)
            info['tables'].append(schema)
        
        return info
    
    def disconnect(self, connection_id: str = "default"):
        """Close database connection"""
        engine = self.connections.get(connection_id)
        if engine:
            engine.dispose()
            del self.connections[connection_id]
    
    @staticmethod
    def save_connection_config(config: DatabaseConfig, name: str):
        """Save connection configuration securely using keyring"""
        try:
            keyring.set_password("ai_db_tool", f"{name}_host", config.host)
            keyring.set_password("ai_db_tool", f"{name}_port", str(config.port))
            keyring.set_password("ai_db_tool", f"{name}_database", config.database)
            keyring.set_password("ai_db_tool", f"{name}_username", config.username)
            keyring.set_password("ai_db_tool", f"{name}_password", config.password)
            return True
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
            return False
    
    @staticmethod
    def load_connection_config(name: str) -> Optional[DatabaseConfig]:
        """Load connection configuration from keyring"""
        try:
            host = keyring.get_password("ai_db_tool", f"{name}_host")
            port = keyring.get_password("ai_db_tool", f"{name}_port")
            database = keyring.get_password("ai_db_tool", f"{name}_database")
            username = keyring.get_password("ai_db_tool", f"{name}_username")
            password = keyring.get_password("ai_db_tool", f"{name}_password")
            
            if all([host, port, database, username, password]):
                return DatabaseConfig(
                    db_type="postgresql",  # Default, should be stored separately
                    host=host,
                    port=int(port),
                    database=database,
                    username=username,
                    password=password,
                )
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
        
        return None

