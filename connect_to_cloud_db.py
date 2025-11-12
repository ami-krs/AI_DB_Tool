#!/usr/bin/env python3
"""
Helper script to connect to free cloud databases
Supports Neon, Supabase, PlanetScale, and more
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_db_tool.connectors import DatabaseManager, DatabaseConfig


def connect_neon():
    """
    Connect to Neon PostgreSQL
    Get connection details from: https://neon.tech/
    """
    print("\n" + "="*60)
    print("CONNECTING TO NEON (PostgreSQL)")
    print("="*60)
    
    print("\n📝 Please enter your Neon connection details:")
    print("   Get them from: https://console.neon.tech")
    
    host = input("\nHost (e.g., ep-xxx.us-east-2.aws.neon.tech): ").strip()
    database = input("Database name (e.g., neondb): ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    config = DatabaseConfig(
        db_type="postgresql",
        host=host,
        port=5432,
        database=database,
        username=username,
        password=password
    )
    
    return config


def connect_supabase():
    """
    Connect to Supabase PostgreSQL
    Get connection details from: https://supabase.com/dashboard
    """
    print("\n" + "="*60)
    print("CONNECTING TO SUPABASE (PostgreSQL)")
    print("="*60)
    
    print("\n📝 Please enter your Supabase connection details:")
    print("   Get them from: https://supabase.com/dashboard > Project Settings > Database")
    
    host = input("\nHost (e.g., db.xxx.supabase.co): ").strip()
    database = input("Database name (usually: postgres): ").strip() or "postgres"
    username = input("Username (usually: postgres): ").strip() or "postgres"
    password = input("Database password: ").strip()
    
    config = DatabaseConfig(
        db_type="postgresql",
        host=host,
        port=5432,
        database=database,
        username=username,
        password=password
    )
    
    return config


def connect_planetscale():
    """
    Connect to PlanetScale MySQL
    Get connection details from: https://console.planetscale.com
    """
    print("\n" + "="*60)
    print("CONNECTING TO PLANETSCALE (MySQL)")
    print("="*60)
    
    print("\n📝 Please enter your PlanetScale connection details:")
    print("   Get them from: https://console.planetscale.com > Database > Connect")
    
    host = input("\nHost (e.g., aws.connect.psdb.cloud): ").strip()
    database = input("Database name: ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    config = DatabaseConfig(
        db_type="mysql",
        host=host,
        port=3306,
        database=database,
        username=username,
        password=password
    )
    
    return config


def connect_custom():
    """Connect to any custom database"""
    print("\n" + "="*60)
    print("CUSTOM DATABASE CONNECTION")
    print("="*60)
    
    db_type = input("\nDatabase type (postgresql/mysql/sqlserver/oracle/sqlite): ").strip().lower()
    host = input("Host: ").strip()
    port = int(input("Port (default from db type): ").strip() or "5432" if db_type == "postgresql" else "3306")
    database = input("Database name: ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    config = DatabaseConfig(
        db_type=db_type,
        host=host,
        port=port,
        database=database,
        username=username,
        password=password
    )
    
    return config


def test_connection(config: DatabaseConfig):
    """Test database connection"""
    print("\n🔄 Testing connection...")
    
    db_manager = DatabaseManager()
    
    if db_manager.connect(config):
        print("✅ Connected successfully!")
        
        # Get database info
        tables = db_manager.get_tables()
        print(f"\n📊 Found {len(tables)} tables: {', '.join(tables) if tables else 'None'}")
        
        if tables:
            print("\nWould you like to create sample data? (y/n)")
            create_data = input().strip().lower()
            
            if create_data == 'y':
                create_sample_data(db_manager, config.db_type)
        
        return db_manager
    else:
        print("❌ Connection failed!")
        return None


def create_sample_data(db_manager: DatabaseManager, db_type: str):
    """Create sample tables and data"""
    print("\n🔄 Creating sample data...")
    
    if db_type == "sqlite":
        create_sql = """
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER,
            city TEXT
        );
        
        INSERT OR IGNORE INTO customers (name, email, age, city) VALUES
        ('Alice Johnson', 'alice@example.com', 28, 'New York'),
        ('Bob Smith', 'bob@example.com', 35, 'Los Angeles'),
        ('Charlie Brown', 'charlie@example.com', 42, 'Chicago'),
        ('Diana Prince', 'diana@example.com', 29, 'Seattle'),
        ('Eve Davis', 'eve@example.com', 38, 'Boston');
        """
    else:
        create_sql = """
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE,
            age INTEGER,
            city VARCHAR(100)
        );
        
        INSERT INTO customers (name, email, age, city) VALUES
        ('Alice Johnson', 'alice@example.com', 28, 'New York'),
        ('Bob Smith', 'bob@example.com', 35, 'Los Angeles'),
        ('Charlie Brown', 'charlie@example.com', 42, 'Chicago'),
        ('Diana Prince', 'diana@example.com', 29, 'Seattle'),
        ('Eve Davis', 'eve@example.com', 38, 'Boston')
        ON CONFLICT (email) DO NOTHING;
        """
    
    try:
        db_manager.execute_non_query(create_sql)
        print("✅ Sample data created!")
        
        # Query to verify
        df = db_manager.execute_query("SELECT * FROM customers LIMIT 5")
        print(f"\n📋 Sample data ({len(df)} rows):")
        print(df.to_string(index=False))
        
    except Exception as e:
        print(f"⚠️  Could not create sample data: {e}")


def main():
    """Main menu"""
    print("\n" + "="*60)
    print("CLOUD DATABASE CONNECTION HELPER")
    print("="*60)
    print("\nChoose your database:")
    print("1. Neon (PostgreSQL) - Recommended")
    print("2. Supabase (PostgreSQL)")
    print("3. PlanetScale (MySQL)")
    print("4. Custom Database")
    print("5. SQLite (Local, no setup needed)")
    print("6. Exit")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    config = None
    
    if choice == "1":
        config = connect_neon()
    elif choice == "2":
        config = connect_supabase()
    elif choice == "3":
        config = connect_planetscale()
    elif choice == "4":
        config = connect_custom()
    elif choice == "5":
        # SQLite
        db_path = input("\nEnter SQLite database path (or press Enter for /tmp/test_db.sqlite): ").strip()
        if not db_path:
            db_path = "/tmp/test_db.sqlite"
        
        config = DatabaseConfig(
            db_type="sqlite",
            host="",
            port=0,
            database=db_path,
            username="",
            password=""
        )
    elif choice == "6":
        print("\n👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice!")
        return
    
    db_manager = test_connection(config)
    
    if db_manager:
        print("\n" + "="*60)
        print("✅ CONNECTION SUCCESSFUL!")
        print("="*60)
        print("\nYou can now use this database with your AI Database Tool!")
        print("\nExample usage:")
        print("```python")
        print("from ai_db_tool.connectors import DatabaseManager, DatabaseConfig")
        print("config = DatabaseConfig(...)")
        print("db_manager = DatabaseManager()")
        print("db_manager.connect(config)")
        print("df = db_manager.execute_query('SELECT * FROM customers')")
        print("```")
        
        # Ask if they want to test AI features
        print("\n🤖 Would you like to test AI features now? (y/n)")
        test_ai = input().strip().lower()
        
        if test_ai == 'y':
            from ai_db_tool.ai import AIQueryBuilder
            
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                print("\n🔄 Testing AI query generation...")
                query_builder = AIQueryBuilder()
                schema_info = db_manager.get_database_info()
                
                question = input("\n💬 Ask a question about your data (e.g., 'Show me top 3 customers by age'): ")
                
                try:
                    sql = query_builder.generate_query(question, schema_info, db_type=config.db_type)
                    print(f"\n✅ Generated SQL:")
                    print(sql)
                    
                    execute = input("\n▶️  Execute this query? (y/n): ").strip().lower()
                    if execute == 'y':
                        df = db_manager.execute_query(sql)
                        print(f"\n📊 Results ({len(df)} rows):")
                        print(df.to_string(index=False))
                except Exception as e:
                    print(f"❌ Error: {e}")
            else:
                print("⚠️  No OpenAI API key found. Set OPENAI_API_KEY in .env")


if __name__ == "__main__":
    main()


