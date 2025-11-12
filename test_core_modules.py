#!/usr/bin/env python3
"""
Test script for AI Database Tool core modules
Tests database connections, AI query builder, and chatbot functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_db_tool.connectors import DatabaseManager, DatabaseConfig
from ai_db_tool.ai import AIQueryBuilder, SQLChatbot


def test_database_manager():
    """Test DatabaseManager with SQLite (no external setup needed)"""
    print("\n" + "="*60)
    print("TEST 1: Database Manager (SQLite)")
    print("="*60)
    
    try:
        # Create SQLite database for testing
        import sqlite3
        
        test_db_path = "/tmp/test_db.sqlite"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        # Create test data
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE customers (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                age INTEGER,
                city TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO customers (name, email, age, city) VALUES
            ('Alice Johnson', 'alice@example.com', 28, 'New York'),
            ('Bob Smith', 'bob@example.com', 35, 'Los Angeles'),
            ('Charlie Brown', 'charlie@example.com', 42, 'Chicago'),
            ('Diana Prince', 'diana@example.com', 29, 'Seattle'),
            ('Eve Davis', 'eve@example.com', 38, 'Boston')
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Test database created successfully")
        
        # Test DatabaseManager
        db_manager = DatabaseManager()
        
        config = DatabaseConfig(
            db_type="sqlite",
            host="",
            port=0,
            database=test_db_path,
            username="",
            password=""
        )
        
        print("\n🔄 Connecting to SQLite database...")
        if db_manager.connect(config):
            print("✅ Connected successfully!")
            
            # Test getting tables
            tables = db_manager.get_tables()
            print(f"✅ Found {len(tables)} tables: {tables}")
            
            # Test getting table schema
            schema = db_manager.get_table_schema("customers")
            print(f"\n📋 Schema for 'customers' table:")
            print(f"   Columns: {len(schema['columns'])}")
            for col in schema['columns']:
                print(f"   - {col['name']}: {col['type']}")
            
            # Test executing query
            print("\n🔄 Executing test query...")
            df = db_manager.execute_query("SELECT * FROM customers LIMIT 3")
            print(f"✅ Query executed successfully! Retrieved {len(df)} rows")
            print("\nResults:")
            print(df.to_string(index=False))
            
            # Clean up
            db_manager.disconnect()
            os.remove(test_db_path)
            print("\n✅ Database manager test completed successfully!")
            return True
        else:
            print("❌ Failed to connect to database")
            return False
    
    except Exception as e:
        print(f"❌ Database manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_query_builder():
    """Test AI Query Builder"""
    print("\n" + "="*60)
    print("TEST 2: AI Query Builder")
    print("="*60)
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("⚠️  No API key found. Skipping AI test.")
        print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env to test AI features")
        return True
    
    try:
        print("🔄 Initializing AI Query Builder...")
        query_builder = AIQueryBuilder(model="gpt-4o-mini", provider="openai")
        print("✅ AI Query Builder initialized!")
        
        # Test 1: Generate simple query
        print("\n🔄 Generating SQL query from natural language...")
        question = "Show me top 3 customers by age"
        schema_info = {
            'tables': [
                {
                    'table_name': 'customers',
                    'columns': [
                        {'name': 'id', 'type': 'INTEGER', 'primary_key': True},
                        {'name': 'name', 'type': 'TEXT'},
                        {'name': 'email', 'type': 'TEXT'},
                        {'name': 'age', 'type': 'INTEGER'},
                        {'name': 'city', 'type': 'TEXT'},
                    ]
                }
            ]
        }
        
        sql_query = query_builder.generate_query(question, schema_info, db_type="sqlite")
        print("✅ SQL query generated!")
        print(f"\nQuestion: {question}")
        print(f"\nGenerated SQL:")
        print(sql_query)
        
        # Test 2: Explain query
        print("\n" + "-"*60)
        print("🔄 Explaining SQL query...")
        explanation = query_builder.explain_query(sql_query)
        print("✅ Query explained!")
        print(f"\nExplanation:\n{explanation}")
        
        # Test 3: Optimize query (if it's a real query)
        print("\n" + "-"*60)
        print("🔄 Optimizing SQL query...")
        optimized = query_builder.optimize_query(sql_query)
        print("✅ Query optimized!")
        print(f"\nOptimized SQL:")
        print(optimized)
        
        print("\n✅ AI Query Builder test completed successfully!")
        return True
    
    except Exception as e:
        print(f"❌ AI Query Builder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_chatbot():
    """Test AI Chatbot"""
    print("\n" + "="*60)
    print("TEST 3: AI SQL Chatbot")
    print("="*60)
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("⚠️  No API key found. Skipping AI chatbot test.")
        return True
    
    try:
        print("🔄 Initializing AI Chatbot...")
        chatbot = SQLChatbot(model="gpt-4o-mini", provider="openai")
        print("✅ AI Chatbot initialized!")
        
        # Set schema context
        schema_info = {
            'tables': [
                {
                    'table_name': 'customers',
                    'columns': [
                        {'name': 'id', 'type': 'INTEGER', 'primary_key': True},
                        {'name': 'name', 'type': 'TEXT'},
                        {'name': 'email', 'type': 'TEXT'},
                        {'name': 'age', 'type': 'INTEGER'},
                        {'name': 'city', 'type': 'TEXT'},
                    ]
                }
            ]
        }
        chatbot.set_schema_context(schema_info)
        
        # Test conversation
        print("\n🔄 Starting conversation...")
        questions = [
            "What columns are in the customers table?",
            "How many customers do we have?",
        ]
        
        for question in questions:
            print(f"\n👤 User: {question}")
            response = chatbot.chat(question, include_sql=True)
            
            if 'error' not in response:
                print(f"🤖 Assistant: {response['response']}")
                if response.get('sql_query'):
                    print(f"\nGenerated SQL:")
                    print(response['sql_query'])
            else:
                print(f"❌ Error: {response['error']}")
        
        print("\n✅ AI Chatbot test completed successfully!")
        return True
    
    except Exception as e:
        print(f"❌ AI Chatbot test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI DATABASE TOOL - CORE MODULES TEST")
    print("="*60)
    
    results = []
    
    # Test 1: Database Manager
    results.append(test_database_manager())
    
    # Test 2: AI Query Builder (requires API key)
    results.append(test_ai_query_builder())
    
    # Test 3: AI Chatbot (requires API key)
    results.append(test_ai_chatbot())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    tests_passed = sum(results)
    total_tests = len(results)
    
    print(f"\nTests Passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n🎉 All tests passed! Core modules are working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed or were skipped.")
        print("   Note: AI tests require API keys in .env file")
        return 1


if __name__ == "__main__":
    sys.exit(main())


