#!/usr/bin/env python3
"""
Interactive demo of AI Database Tool
Shows how to connect to databases, generate SQL with AI, and query data
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


def create_sample_database():
    """Create a sample SQLite database with realistic data"""
    import sqlite3
    
    db_path = "/tmp/demo_database.sqlite"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            department TEXT,
            salary REAL,
            hire_date DATE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            budget REAL,
            manager_id INTEGER,
            FOREIGN KEY (manager_id) REFERENCES employees(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY,
            name TEXT,
            department_id INTEGER,
            status TEXT,
            budget REAL,
            start_date DATE,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    """)
    
    # Insert sample data
    employees_data = [
        ('John Smith', 'john.smith@company.com', 'Engineering', 95000, '2020-01-15'),
        ('Alice Johnson', 'alice.j@company.com', 'Engineering', 105000, '2019-03-10'),
        ('Bob Miller', 'bob.miller@company.com', 'Sales', 85000, '2021-06-01'),
        ('Carol White', 'carol.white@company.com', 'Sales', 88000, '2020-11-20'),
        ('David Brown', 'david.brown@company.com', 'Marketing', 92000, '2018-08-05'),
        ('Eva Davis', 'eva.davis@company.com', 'Marketing', 87000, '2022-02-14'),
    ]
    
    cursor.executemany("""
        INSERT INTO employees (name, email, department, salary, hire_date)
        VALUES (?, ?, ?, ?, ?)
    """, employees_data)
    
    departments_data = [
        ('Engineering', 500000, 2),
        ('Sales', 300000, 4),
        ('Marketing', 250000, 5),
    ]
    
    cursor.executemany("""
        INSERT INTO departments (name, budget, manager_id)
        VALUES (?, ?, ?)
    """, departments_data)
    
    projects_data = [
        ('Website Redesign', 1, 'In Progress', 150000, '2024-01-01'),
        ('Mobile App', 1, 'Planning', 200000, '2024-03-01'),
        ('Q1 Sales Campaign', 2, 'Completed', 75000, '2024-01-01'),
        ('Brand Awareness', 3, 'In Progress', 100000, '2024-02-01'),
    ]
    
    cursor.executemany("""
        INSERT INTO projects (name, department_id, status, budget, start_date)
        VALUES (?, ?, ?, ?, ?)
    """, projects_data)
    
    conn.commit()
    conn.close()
    
    print("✅ Sample database created successfully!")
    return db_path


def demo_database_operations():
    """Demonstrate database operations"""
    print("\n" + "="*60)
    print("DATABASE OPERATIONS DEMO")
    print("="*60)
    
    # Create sample database
    db_path = create_sample_database()
    
    # Connect to database
    db_manager = DatabaseManager()
    config = DatabaseConfig(
        db_type="sqlite",
        host="",
        port=0,
        database=db_path,
        username="",
        password=""
    )
    
    print("\n🔄 Connecting to database...")
    if db_manager.connect(config):
        print("✅ Connected!")
        
        # Show tables
        tables = db_manager.get_tables()
        print(f"\n📊 Available tables: {', '.join(tables)}")
        
        # Get database info
        print("\n🔄 Fetching database schema...")
        schema_info = db_manager.get_database_info()
        print(f"✅ Retrieved schema for {len(schema_info['tables'])} tables")
        
        # Execute a query
        print("\n🔄 Executing sample query...")
        query = """
        SELECT 
            e.name, 
            e.department, 
            e.salary,
            d.name as dept_name,
            d.budget
        FROM employees e
        LEFT JOIN departments d ON e.department = d.name
        ORDER BY e.salary DESC
        LIMIT 5
        """
        
        df = db_manager.execute_query(query)
        print(f"\n📈 Query Results ({len(df)} rows):")
        print(df.to_string(index=False))
        
        return db_manager, schema_info
    else:
        print("❌ Connection failed!")
        return None, None


def demo_ai_query_generation(schema_info):
    """Demonstrate AI-powered query generation"""
    print("\n" + "="*60)
    print("AI QUERY GENERATION DEMO")
    print("="*60)
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("\n⚠️  OpenAI API key not found in environment.")
        print("   To test AI features, set OPENAI_API_KEY in .env file")
        print("   For now, showing mock examples:")
        return
    
    try:
        print("\n🔄 Initializing AI Query Builder...")
        query_builder = AIQueryBuilder(model="gpt-4o-mini", provider="openai")
        print("✅ AI Query Builder ready!")
        
        # Generate queries
        questions = [
            "Show me the top 3 employees by salary",
            "What are all the departments and their budgets?",
            "Which projects are currently in progress?",
        ]
        
        for question in questions:
            print(f"\n💬 Question: {question}")
            
            try:
                sql_query = query_builder.generate_query(question, schema_info, db_type="sqlite")
                print(f"✅ Generated SQL:")
                print(sql_query)
                
                # Explain the query
                explanation = query_builder.explain_query(sql_query)
                print(f"\n📝 Explanation:")
                print(explanation)
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    except Exception as e:
        print(f"❌ AI Query Builder failed: {e}")


def demo_chatbot(schema_info):
    """Demonstrate conversational SQL chatbot"""
    print("\n" + "="*60)
    print("AI CHATBOT DEMO")
    print("="*60)
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("\n⚠️  OpenAI API key not found. Skipping chatbot demo.")
        return
    
    try:
        print("\n🔄 Initializing AI Chatbot...")
        chatbot = SQLChatbot(model="gpt-4o-mini", provider="openai")
        chatbot.set_schema_context(schema_info)
        print("✅ Chatbot ready!")
        
        # Simulate conversation
        questions = [
            "What tables are in this database?",
            "Can you show me employees in the Engineering department?",
        ]
        
        for question in questions:
            print(f"\n👤 User: {question}")
            
            try:
                response = chatbot.chat(question, include_sql=True)
                
                if 'error' not in response:
                    print(f"\n🤖 Assistant: {response['response']}")
                    
                    if response.get('sql_query'):
                        print(f"\nGenerated SQL:")
                        print(response['sql_query'])
                else:
                    print(f"❌ Error: {response['error']}")
            
            except Exception as e:
                print(f"❌ Chat failed: {e}")
    
    except Exception as e:
        print(f"❌ Chatbot failed: {e}")


def main():
    """Run complete demo"""
    print("\n" + "="*60)
    print("AI DATABASE TOOL - INTERACTIVE DEMO")
    print("="*60)
    
    # Step 1: Database operations
    db_manager, schema_info = demo_database_operations()
    
    if db_manager and schema_info:
        # Step 2: AI query generation
        demo_ai_query_generation(schema_info)
        
        # Step 3: Chatbot
        demo_chatbot(schema_info)
        
        # Cleanup
        db_manager.disconnect()
        
    print("\n" + "="*60)
    print("DEMO COMPLETED!")
    print("="*60)
    print("\n✅ Core features demonstrated successfully!")
    print("\n📚 Next steps:")
    print("   1. Set up your API key in .env file for AI features")
    print("   2. Connect to your own database")
    print("   3. Try the web UI: streamlit run webapp/app.py")
    print("\n🚀 Happy querying!")


if __name__ == "__main__":
    main()


