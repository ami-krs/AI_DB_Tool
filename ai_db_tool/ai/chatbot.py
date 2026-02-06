"""
SQL Chatbot - Conversational interface for database interactions
Allows users to ask questions, explore data, and get SQL assistance
"""

from __future__ import annotations
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from openai import OpenAI

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

# Helper to get API key from Streamlit secrets or environment variables
def _get_api_key_from_secrets(key_name: str) -> Optional[str]:
    """Get API key from Streamlit secrets (for Streamlit Cloud) or environment variables"""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name)


@dataclass
class ChatMessage:
    """Represents a chat message"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat()
        }


SYSTEM_PROMPT_CHATBOT = """
You are an intelligent SQL assistant chatbot. You help users:
1. Understand their databases and tables
2. Generate SQL queries from natural language questions
3. Debug SQL errors
4. Explain database concepts and query optimization
5. Explore data relationships
6. Create, modify, and manage database objects (tables, indexes, views)
7. Insert, update, and delete data

CRITICAL - RESPONSE FORMAT:
- When user asks for SQL (INSERT, SELECT, UPDATE, DELETE, etc.), you MUST respond with ONLY the SQL code in a ```sql code block
- DO NOT provide explanations, instructions, or "here's how you can" text BEFORE the SQL
- DO NOT say "you'll need to" or "first ensure you have" - just generate the SQL directly
- Start your response with the SQL code block immediately
- Brief explanations can come AFTER the SQL code block, but the SQL must come first

IMPORTANT RULES:
- ONLY generate SQL queries (SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, etc.) - NEVER shell commands or CLI syntax
- Generate ONLY the SQL statement(s), nothing else
- Support ALL SQL operations:
  * SELECT queries for reading data
  * INSERT/UPDATE/DELETE for modifying data
  * CREATE/DROP/ALTER for managing database objects (tables, indexes, views, etc.)
- Use SQLite-specific syntax when database type is SQLite
- Use PostgreSQL-specific syntax when database type is PostgreSQL
- Use MySQL-specific syntax when database type is MySQL
- For SQLite: Use sqlite_master instead of information_schema
- For PostgreSQL: Use information_schema
- For MySQL: Use information_schema

CRITICAL - USE REAL SCHEMA ONLY (NO PLACEHOLDERS):
- For SELECT/INSERT/UPDATE/DELETE operations: You MUST ONLY use table names and column names that appear in the provided "Database Schema".
- For CREATE TABLE operations: You can create NEW tables based on the user's description. Use appropriate column names, data types, and relationships as described by the user.
- NEVER invent table names like example_table/sample_table/test_table or columns like column1/column2 for SELECT/INSERT/UPDATE/DELETE operations (unless those exact names exist in the schema).
- If the user requests inserts "in all tables" and there are many tables, LIMIT to the first 10 tables and note in SQL comments which tables were included.
- For each table, generate INSERT statements that match the real columns. Prefer inserting into a minimal set of non-null, non-generated columns.

CRITICAL - MULTIPLE OPERATIONS:
- When the user requests operations on MULTIPLE tables (e.g., "populate records in three tables", "insert data into table1, table2, and table3"), you MUST generate SQL statements for ALL mentioned tables
- Separate multiple SQL statements using semicolons (;)
- Generate complete, separate INSERT/UPDATE/DELETE/CREATE statements for each table mentioned
- Do NOT skip any tables - handle ALL tables mentioned in the user's request
- If the user says "populate records in three tables" or "insert into multiple tables", generate INSERT statements for ALL three/multiple tables
- Example for multiple tables:
  ```sql
  INSERT INTO table1 (col1, col2) VALUES ('value1', 'value2');
  INSERT INTO table2 (col1, col2) VALUES ('value1', 'value2');
  INSERT INTO table3 (col1, col2) VALUES ('value1', 'value2');
  ```

Examples:
- CORRECT: SELECT * FROM employees WHERE salary > 50000
- CORRECT: INSERT INTO employees (name, salary) VALUES ('John', 60000)
- CORRECT: CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT)
- CORRECT (multiple tables): INSERT INTO table1 (name) VALUES ('A'); INSERT INTO table2 (name) VALUES ('B'); INSERT INTO table3 (name) VALUES ('C');
- WRONG: sqlite3 database.db "SELECT * FROM employees" or .tables
- WRONG: Only generating SQL for the first table when multiple tables are requested
- WRONG: INSERT INTO example_table (column1, column2) ...  (placeholders that don't exist)

Guidelines:
- Be helpful, accurate, and concise
- ALWAYS generate actual SQL statements - do NOT provide generic explanations or examples
- When user asks to insert/populate records, generate the actual INSERT statements for their specific tables
- Do NOT say "here's how you can" or "assuming you have" - just generate the SQL directly
- For "insert records in all tables" requests, generate INSERT statements for each table listed in the schema
- For JOIN queries: ALWAYS generate SQL even if column details are incomplete. Use common column naming patterns (id, name, key, etc.) or table prefixes to create reasonable JOIN conditions.
- NEVER refuse to generate JOIN queries due to missing column details - always make reasonable assumptions and generate the SQL.
- For UPDATE/DELETE queries: You MUST use ONLY column names that exist in the schema. NEVER assume a table has an 'id' column - check the column list first and use the actual primary key or identifier column name.
- Ask clarifying questions ONLY when absolutely necessary (e.g., missing critical information that cannot be reasonably inferred)
- Provide brief explanations ONLY when the SQL is complex or needs context
- Never execute destructive operations unless explicitly requested
- Remember context from previous messages in the conversation
- Support complete database management capabilities
- When multiple tables/operations are requested, generate SQL for ALL of them, not just the first one
- NEVER use placeholder table names like "table_name", "example_table", "sample_table" - use ONLY real table names from the schema
"""


class SQLChatbot:
    """Conversational AI chatbot for SQL assistance"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        provider: str = "openai"
    ):
        """
        Initialize SQL Chatbot
        
        Args:
            api_key: API key for OpenAI or Anthropic
            model: Model to use
            provider: AI provider ("openai" or "anthropic")
        """
        self.api_key = api_key or _get_api_key_from_secrets("OPENAI_API_KEY") or _get_api_key_from_secrets("ANTHROPIC_API_KEY")
        self.model = model
        self.provider = provider
        
        # Check if API key is available
        if not self.api_key:
            self.client = None
            self.api_key_available = False
        else:
            self.api_key_available = True
            try:
                if provider.lower() == "openai":
                    self.client = OpenAI(api_key=self.api_key)
                elif provider.lower() == "anthropic":
                    if Anthropic is None:
                        raise ImportError("anthropic package not installed. Install with: pip install anthropic")
                    self.client = Anthropic(api_key=self.api_key)
                else:
                    raise ValueError(f"Unsupported provider: {provider}")
            except Exception as e:
                self.client = None
                self.api_key_available = False
                import warnings
                warnings.warn(f"Failed to initialize AI client: {e}")
        
        self.conversation_history: List[ChatMessage] = []
        self.schema_context: Optional[Dict[str, Any]] = None
    
    def set_schema_context(self, schema_info: Dict[str, Any]):
        """Set database schema context for the chatbot"""
        self.schema_context = schema_info
    
    def chat(
        self,
        user_message: str,
        include_sql: bool = True
    ) -> Dict[str, Any]:
        """
        Process user message and generate response
        
        Args:
            user_message: User's question or request
            include_sql: Whether to generate SQL in response
            
        Returns:
            Dictionary with assistant response and optional SQL query
        """
        # Check if AI client is available
        if not self.client or not self.api_key_available:
            return {
                'error': 'AI features are not available. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.',
                'response': 'AI chatbot requires an API key to function. Please configure your API key in the environment variables.',
                'timestamp': datetime.now().isoformat()
            }
        
        # Check user request type - CREATE TABLE requests don't need existing schema
        user_upper = user_message.upper()
        is_create_request = any(keyword in user_upper for keyword in [
            'CREATE TABLE', 'CREATE TABLES', 'CREATE SCHEMA', 'CREATE DATABASE',
            'DESIGN TABLE', 'DESIGN TABLES', 'BUILD TABLE', 'BUILD TABLES',
            'MAKE TABLE', 'MAKE TABLES', 'NEW TABLE', 'NEW TABLES'
        ])
        
        # For CREATE TABLE requests, schema context is optional (we're creating new tables)
        # For other requests (INSERT, SELECT, etc.), schema context is required
        if not is_create_request:
            # Check if schema context is available - critical for generating accurate SQL
            if not self.schema_context or not self.schema_context.get('tables'):
                return {
                    'error': 'Database schema not available',
                    'response': '❌ Database schema information is not available. Please reconnect to your database to refresh the schema context.',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Validate that we have actual table names (not empty)
            tables = self.schema_context.get('tables', [])
            if not tables or len(tables) == 0:
                return {
                    'error': 'No tables found in schema',
                    'response': '❌ No tables found in your database schema. Please ensure your database has tables and reconnect.',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Log schema info for debugging
            print(f"DEBUG: Chatbot schema context - {len(tables)} tables available")
            if tables and isinstance(tables[0], dict):
                table_names = [t.get('table_name', 'unknown') for t in tables[:5]]
                print(f"DEBUG: First 5 tables: {table_names}")
            elif tables:
                print(f"DEBUG: First 5 table names: {tables[:5]}")
        else:
            # For CREATE TABLE requests, log that we're creating new tables
            print(f"DEBUG: CREATE TABLE request detected - schema context not required")
        
        # Add user message to history
        self.conversation_history.append(
            ChatMessage("user", user_message, datetime.now())
        )
        
        # Build prompt with context
        prompt = self._build_prompt(user_message, include_sql)
        
        try:
            if self.provider == "openai":
                messages = self._build_openai_messages()
                messages.append({"role": "user", "content": prompt})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.2,
                )
                response_text = response.choices[0].message.content.strip()
            
            elif self.provider == "anthropic":
                messages = self._build_anthropic_messages()
                
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=SYSTEM_PROMPT_CHATBOT,
                    messages=messages + [{"role": "user", "content": prompt}],
                )
                response_text = response.content[0].text.strip()
            
            # Extract SQL from response if present
            sql_query = None
            if include_sql:
                # Look for SQL code block
                if "```sql" in response_text:
                    sql_start = response_text.find("```sql")
                    sql_end = response_text.find("```", sql_start + 6)
                    if sql_end != -1:
                        sql_query = response_text[sql_start + 6:sql_end].strip()
                        # For INSERT requests, prioritize SQL - remove explanations before SQL
                        user_upper = user_message.upper()
                        if any(keyword in user_upper for keyword in ['INSERT', 'POPULATE', 'ADD RECORDS', 'CREATE RECORDS', 'ADD DATA', 'TEST RECORDS']):
                            # Keep only SQL and anything after it, remove text before SQL
                            response_text = response_text[sql_start:]  # Keep SQL code block and anything after
                        else:
                            response_text = response_text[:sql_start] + response_text[sql_end + 3:].strip()
                else:
                    # If no SQL block found but response contains SQL-like text, try to extract it
                    if any(keyword in response_text.upper() for keyword in ['INSERT INTO', 'SELECT', 'UPDATE', 'DELETE FROM', 'CREATE TABLE']):
                        # Try to find SQL statements even without code blocks
                        import re
                        # Pattern for SELECT statements (most common for auto-execution)
                        select_pattern = r'(SELECT\s+[^;]+(?:;[^;]+)*)'
                        # Pattern for INSERT statements
                        insert_pattern = r'(INSERT\s+INTO[^;]+(?:;[^;]+)*)'
                        # Pattern for other DML/DDL
                        other_pattern = r'((?:UPDATE|DELETE\s+FROM|CREATE\s+TABLE|DROP\s+TABLE|ALTER\s+TABLE)\s+[^;]+(?:;[^;]+)*)'
                        
                        # Try SELECT first (most common for data retrieval)
                        matches = re.findall(select_pattern, response_text, re.IGNORECASE | re.DOTALL)
                        if not matches:
                            # Try INSERT
                            matches = re.findall(insert_pattern, response_text, re.IGNORECASE | re.DOTALL)
                        if not matches:
                            # Try other DML/DDL
                            matches = re.findall(other_pattern, response_text, re.IGNORECASE | re.DOTALL)
                        
                        if matches:
                            sql_query = '; '.join(matches)
                            # Clean up SQL query (remove extra whitespace, newlines)
                            sql_query = ' '.join(sql_query.split())
                            # Remove the SQL from response text
                            for match in matches:
                                response_text = response_text.replace(match, '').strip()
            
            # Add assistant response to history
            self.conversation_history.append(
                ChatMessage("assistant", response_text, datetime.now())
            )
            
            return {
                "response": response_text,
                "sql_query": sql_query,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "error": f"Chatbot error: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_prompt(self, user_message: str, include_sql: bool) -> str:
        """Build prompt with schema context"""
        prompt = ""
        
        # Add database type if available
        db_type = self.schema_context.get('db_type', 'unknown') if self.schema_context else 'unknown'
        if db_type != 'unknown':
            prompt += f"Database Type: {db_type}\n\n"
        
        if self.schema_context:
            prompt += "=== DATABASE SCHEMA (YOU MUST USE ONLY THESE TABLES AND COLUMNS - NO PLACEHOLDERS) ===\n"
            tables = self.schema_context.get('tables', [])
            
            if not tables:
                prompt += "⚠️ ERROR: No tables found in schema. Cannot generate SQL without table information.\n\n"
            else:
                # List all table names at the top for visibility
                if isinstance(tables[0], dict):
                    all_table_names = [t.get('table_name', 'unknown') for t in tables]
                else:
                    all_table_names = [str(t) for t in tables]
                prompt += f"AVAILABLE TABLES ({len(all_table_names)} total): {', '.join(all_table_names[:20])}\n"
                if len(all_table_names) > 20:
                    prompt += f"(... and {len(all_table_names) - 20} more tables)\n"
                prompt += "\n"
                # If tables are just strings, try to get full schema from db_manager
                if isinstance(tables[0], str):
                    # Tables are just names - we need to fetch full schema
                    prompt += f"Available Tables ({len(tables)} tables found):\n"
                    for table_name in tables[:20]:  # Show up to 20 tables
                        prompt += f"- {table_name}\n"
                    prompt += "\n⚠️ WARNING: Column details not available. Please ensure schema context includes column information.\n\n"
                else:
                    # Tables have full schema info
                    prompt += f"Tables with full schema ({len(tables)} tables):\n"
                    for table in tables[:20]:  # Show up to 20 tables
                        if isinstance(table, dict):
                            # If table is a dict with schema info, extract table_name and columns
                            table_name = table.get('table_name', 'unknown')
                            columns_list = table.get('columns', [])
                            if columns_list:
                                # Handle columns as list of dicts or list of strings
                                if isinstance(columns_list[0], dict):
                                    # Format: column_name (type) [nullable/not null] [primary key]
                                    col_details = []
                                    for col in columns_list:
                                        col_name = col.get('name', str(col))
                                        col_type = col.get('type', '')
                                        nullable = 'NULL' if col.get('nullable', True) else 'NOT NULL'
                                        pk = 'PRIMARY KEY' if col.get('primary_key', False) else ''
                                        col_str = f"{col_name} ({col_type}) {nullable}"
                                        if pk:
                                            col_str += f" {pk}"
                                        col_details.append(col_str)
                                    columns = ', '.join(col_details)
                                else:
                                    columns = ', '.join([str(col) for col in columns_list])
                                prompt += f"\nTable: {table_name}\n  Columns: {columns}\n"
                            else:
                                prompt += f"\nTable: {table_name} (no column info available)\n"
                        elif isinstance(table, str):
                            prompt += f"\nTable: {table} (no column info available)\n"
                prompt += "\n=== END OF SCHEMA ===\n\n"
                prompt += "🚨 CRITICAL RULES FOR SQL GENERATION (VIOLATION WILL CAUSE ERRORS):\n"
                prompt += "1. You MUST ONLY use table names from the list above: " + ', '.join(all_table_names[:10]) + (f" and {len(all_table_names) - 10} more" if len(all_table_names) > 10 else "") + "\n"
                prompt += "\n"
                prompt += "🚫 ABSOLUTE PROHIBITION - YOU MUST NEVER:\n"
                prompt += "- Refuse to generate SQL queries\n"
                prompt += "- Say 'I cannot generate' or 'I'm unable to generate'\n"
                prompt += "- Ask for column details that are already provided in the schema above\n"
                prompt += "- Say 'column details are not available' when they ARE in the schema above\n"
                prompt += "- Refuse UPDATE/DELETE/INSERT/CREATE VIEW queries if the table name appears in the schema above\n"
                prompt += "- Say 'column details for the tables are not available' - the schema above shows the column information\n"
                prompt += "- For CREATE VIEW: Even if column details seem incomplete, use the columns that ARE shown in the schema\n"
                prompt += "\n"
                prompt += "✅ YOU MUST ALWAYS:\n"
                prompt += "- Generate SQL queries using the table and column information from the schema above\n"
                prompt += "- If a table name appears in the schema above, you HAVE the information needed to generate SQL for it\n"
                prompt += "- For UPDATE queries: Use the column names from the schema. If you see 'department_id' in the schema, use it. If you see 'id', use 'id'. Use whatever column names are actually listed.\n"
                prompt += "- For tables in the schema: Even if some column details seem incomplete, generate the SQL using the information available and reasonable assumptions based on common patterns\n"
                prompt += "\n"
                prompt += "⚠️ CRITICAL: The schema above shows table information. For CREATE VIEW requests:\n"
                prompt += "- If column details ARE shown in the 'Columns:' line, use ONLY those exact columns\n"
                prompt += "- If column details are NOT shown (table shows 'no column info available'), you MUST still generate SQL using:\n"
                prompt += "  * The join column (usually purchase_order_id, order_id, or similar foreign key)\n"
                prompt += "  * Primary key columns (usually table_name_id or id)\n"
                prompt += "  * Common column patterns (order_date, created_at, status) ONLY if you can reasonably infer them\n"
                prompt += "- DO NOT refuse to generate SQL - always generate the CREATE VIEW statement\n"
                prompt += "- DO NOT say 'column details are not available' - use what you can see in the schema\n"
                prompt += "2. For JOIN queries: You MUST use ACTUAL column names from the schema above, NOT generic names like 'id' or 'name'.\n"
                prompt += "   - Look at the column lists for each table in the schema above\n"
                prompt += "   - Use the EXACT column names that appear in those lists for JOIN conditions\n"
                prompt += "   - For foreign key relationships, identify which TABLE contains the foreign key column\n"
                prompt += "   - CRITICAL: Foreign key columns (like 'department_id', 'division_id') are typically in the CHILD table, NOT the parent table\n"
                prompt += "   - Example: If 'employee' table has 'department_id' column, then JOIN should be: 'employee.department_id = department.department_id' (assuming department has 'department_id' as primary key)\n"
                prompt += "   - Example: If 'employee' table has 'division_id' column, then JOIN should be: 'employee.division_id = division.division_id' (NOT 'department.division_id')\n"
                prompt += "   - ALWAYS check which table actually HAS the foreign key column before using it in JOIN conditions\n"
                prompt += "   - NEVER assume a table has a foreign key column - check the column list for that specific table first\n"
                prompt += "   - If you see columns like 'employee_id', 'department_id', 'division_id', etc., check which table they belong to in the schema\n"
                prompt += "   - NEVER use generic 'id = id' or assume foreign keys exist in parent tables\n"
                prompt += "   - If a table does NOT have an 'id' column, find the actual primary key column name from the schema (might be 'department_id', 'dept_id', etc.)\n"
                prompt += "   - CRITICAL: Use table aliases in SELECT clause to avoid duplicate column names (e.g., 'SELECT e.employee_id, e.name, d.department_id AS dept_id, d.name AS dept_name')\n"
                prompt += "   - When selecting columns from multiple tables, prefix column names with table aliases to prevent duplicate column name errors\n"
                prompt += "   - For CREATE VIEW with JOIN: NEVER use `SELECT table1.*, table2.*` - this causes duplicate column errors\n"
                prompt += "   - Instead, explicitly list columns with aliases: `SELECT t1.col1, t1.col2, t2.col3, t2.col4`\n"
                prompt += "   - CRITICAL: Use ONLY column names that actually exist in the schema for each table\n"
                prompt += "   - Check the schema above - find each table's column list and use ONLY those columns\n"
                prompt += "   - NEVER invent column names - if schema shows 'procurement' has columns 'id', 'purchase_order_id', 'status', use ONLY those\n"
                prompt += "   - If join column exists in both tables, select it only once: `SELECT t1.join_col, t1.other_col, t2.other_col`\n"
                prompt += "   - Example: `CREATE VIEW my_view AS SELECT po.purchase_order_id, po.order_date, pr.procurement_id, pr.status FROM purchase_order po JOIN procurement pr ON po.purchase_order_id = pr.purchase_order_id`\n"
                prompt += "   - But ONLY if 'order_date', 'procurement_id', 'status' actually exist in the schema for those tables\n"
                prompt += "3. For INSERT/UPDATE/DELETE: You MUST ONLY use column names that appear in the column lists above for each table.\n"
                prompt += "   - For UPDATE queries: Check the column list for the table you're updating and use ONLY those exact column names\n"
                prompt += "   - CRITICAL: When user says 'department id' or 'employee id', you MUST:\n"
                prompt += "     * Look at the actual column names in the schema for that table\n"
                prompt += "     * Find the column that matches (might be 'department_id', 'id', 'dept_id', etc.)\n"
                prompt += "     * Use the EXACT column name from the schema, NOT a guessed name\n"
                prompt += "   - For WHERE clauses in UPDATE/DELETE: Use ONLY column names that exist in the table's column list\n"
                prompt += "   - NEVER assume a table has an 'id' column - check the column list first\n"
                prompt += "   - NEVER use generic 'id' unless the schema explicitly shows a column named 'id'\n"
                prompt += "   - If the table has a primary key, it might be named differently (e.g., 'employee_id', 'customer_id', 'product_id', 'department_id')\n"
                prompt += "   - Look at the column list for the table to find the correct primary key or identifier column name\n"
                prompt += "   - Example: If user says 'update department id', check department table columns:\n"
                prompt += "     * If schema shows 'department_id INTEGER PRIMARY KEY', use 'department_id'\n"
                prompt += "     * If schema shows 'id INTEGER PRIMARY KEY', use 'id'\n"
                prompt += "     * DO NOT guess - use what's actually in the schema\n"
                prompt += "4. When user asks to insert records in 'all tables', generate INSERT statements for EACH table in the list above.\n"
                prompt += "5. NEVER use placeholder names like 'example_table', 'test_table', 'table1', 'table2', 'table_name', 'column1', 'column2', 'column3' - these DO NOT EXIST in this database.\n"
                prompt += "6. NEVER use 'table_name' as a literal string in SQL (e.g., 'FROM dfu.table_name') - replace it with actual table names from the list.\n"
                prompt += "7. If user asks for 'records from DFU table' or 'records from schema X', they likely mean tables IN that schema. Generate SELECT statements for each table in that schema, or ask which specific table they want.\n"
                prompt += "8. NEVER generate 'SELECT * FROM schema_name' - you cannot SELECT from a schema directly. Use 'SELECT * FROM schema_name.table_name' instead.\n"
                prompt += "9. Generate actual SQL statements directly - do NOT provide explanations, examples, or 'here's how you can' text.\n"
                prompt += "10. For JOIN queries, ALWAYS use the actual column names from the schema above - check the column lists carefully before generating JOIN conditions.\n"
                prompt += "11. If you cannot see the table names above, DO NOT generate SQL - return an error instead.\n\n"
        
        prompt += f"User Question: {user_message}\n"
        
        if include_sql:
            # For INSERT/UPDATE/DELETE operations, emphasize generating actual SQL, not explanations
            user_upper = user_message.upper()
            
            # For UPDATE/DELETE operations, add explicit instructions
            if any(keyword in user_upper for keyword in ['UPDATE', 'MODIFY', 'CHANGE', 'SET', 'EDIT']):
                prompt += "\n\n=== CRITICAL INSTRUCTIONS FOR UPDATE/DELETE ===\n"
                prompt += "The user wants to UPDATE or MODIFY data in a table.\n"
                prompt += "1. Look at the schema above - find the table name mentioned by the user (e.g., 'department')\n"
                prompt += "2. Find that table's column list in the schema above - it will show something like:\n"
                prompt += "   Table: department\n"
                prompt += "     Columns: department_id (INTEGER) NOT NULL PRIMARY KEY, name (VARCHAR) NOT NULL, ...\n"
                prompt += "3. Use the EXACT column names from that table's column list - DO NOT guess or assume column names\n"
                prompt += "4. If the user says 'department id' or 'department_id', look for the ACTUAL column name in the schema:\n"
                prompt += "   - It might be 'department_id', 'id', 'dept_id', or something else\n"
                prompt += "   - Check the column list for the department table in the schema above\n"
                prompt += "   - Use whatever column name is ACTUALLY listed in the schema\n"
                prompt += "5. NEVER assume a column is named 'id' - check the schema first\n"
                prompt += "6. If the user says 'division_id = division_id + 9000' or 'update column = column + value':\n"
                prompt += "   - This means: UPDATE the column to be ITSELF plus a value (increment operation)\n"
                prompt += "   - Use the SAME column name on BOTH sides of the assignment\n"
                prompt += "   - Example: 'update division_id = division_id + 9000' means: UPDATE division SET division_id = division_id + 9000\n"
                prompt += "   - Example: 'update department_id = department_id + 1000' means: UPDATE department SET department_id = department_id + 1000\n"
                prompt += "   - CRITICAL: Check the schema - find the table mentioned (e.g., 'division')\n"
                prompt += "   - Use the EXACT column name from that table's column list\n"
                prompt += "   - If the user says 'division_id', check if 'division_id' exists in the 'division' table's columns\n"
                prompt += "   - If the user says 'department_id', check if 'department_id' exists in the 'department' table's columns\n"
                prompt += "   - NEVER use a column name from a DIFFERENT table - use columns from the table you're updating\n"
                prompt += "   - WRONG: UPDATE division SET division_id = department_id + 9000 (department_id doesn't exist in division table!)\n"
                prompt += "   - CORRECT: UPDATE division SET division_id = division_id + 9000 (using division_id from division table)\n"
                prompt += "7. Generate the UPDATE statement using the EXACT column names from the schema for the table being updated\n"
                prompt += "8. DO NOT refuse - if the table is in the schema, you have all the information needed\n"
                prompt += "9. Start your response IMMEDIATELY with ```sql\n"
                prompt += "10. DO NOT say 'I cannot generate' or 'column details not available' - just generate the SQL\n"
                prompt += "=== END CRITICAL INSTRUCTIONS ===\n"
            
            if any(keyword in user_upper for keyword in ['INSERT', 'POPULATE', 'ADD RECORDS', 'CREATE RECORDS', 'ADD DATA', 'TEST RECORDS']):
                prompt += "\n\n=== CRITICAL INSTRUCTIONS ===\n"
                prompt += "The user wants ACTUAL SQL INSERT statements for their specific database tables.\n"
                prompt += "1. Start your response IMMEDIATELY with ```sql\n"
                prompt += "2. Generate INSERT statements for EACH table listed in the schema above\n"
                prompt += "3. Use the EXACT table names and column names from the schema\n"
                prompt += "4. Generate 5 INSERT statements per table (as requested)\n"
                prompt += "5. DO NOT write explanations before the SQL - the SQL code block must be the FIRST thing in your response\n"
                prompt += "6. DO NOT use placeholder names like 'table_name', 'example_table', 'column1', 'column2'\n"
                prompt += "7. DO NOT say 'you'll need to' or 'first ensure' - just generate the SQL\n"
                prompt += "8. If you cannot generate SQL, return an error message explaining why\n"
                prompt += "=== END CRITICAL INSTRUCTIONS ===\n"
            elif any(keyword in user_upper for keyword in ['CREATE VIEW', 'VIEW', 'CREATE.*VIEW']):
                prompt += "\n\n=== CRITICAL INSTRUCTIONS FOR CREATE VIEW ===\n"
                prompt += "The user wants to CREATE a VIEW (virtual table).\n"
                prompt += "🚨 YOU MUST GENERATE SQL - DO NOT REFUSE:\n"
                prompt += "- The schema above contains the table information you need\n"
                prompt += "- Even if column details seem incomplete, use what IS shown in the schema\n"
                prompt += "- DO NOT say 'column details are not available' - check the schema above\n"
                prompt += "- DO NOT refuse to generate SQL - the tables are in the schema\n"
                prompt += "\n"
                prompt += "1. Start your response IMMEDIATELY with ```sql\n"
                prompt += "2. For VIEWs with JOIN: NEVER use `SELECT table1.*, table2.*` - this causes duplicate column errors\n"
                prompt += "3. ABSOLUTE REQUIREMENT - STEP BY STEP PROCESS:\n"
                prompt += "   STEP 1: Find the table names in the schema above (e.g., 'purchase_order', 'procurement')\n"
                prompt += "   STEP 2: For EACH table, find the line that says 'Table: table_name' followed by 'Columns: ...'\n"
                prompt += "   STEP 3: Extract ONLY the column names from the 'Columns:' line\n"
                prompt += "   STEP 4: Write down the EXACT column names as they appear (e.g., 'procurement_id', 'purchase_order_id')\n"
                prompt += "   STEP 5: Use ONLY those exact column names in your SQL - nothing else\n"
                prompt += "   STEP 6: If a table shows '(no column info available)', use the join column and assume a primary key column exists\n"
                prompt += "4. CRITICAL EXAMPLES:\n"
                prompt += "   - If schema shows: 'Table: procurement\\n  Columns: procurement_id (INTEGER), purchase_order_id (INTEGER)'\n"
                prompt += "     Then you can ONLY use: 'procurement_id' and 'purchase_order_id'\n"
                prompt += "     You CANNOT use: 'item_name', 'status', 'procurement_date', or ANY other column name\n"
                prompt += "   - If schema shows: 'Table: purchase_order\\n  Columns: purchase_order_id (INTEGER), order_date (DATE), supplier_id (INTEGER)'\n"
                prompt += "     Then you can ONLY use: 'purchase_order_id', 'order_date', 'supplier_id'\n"
                prompt += "     You CANNOT use: 'total_amount', 'status', or ANY other column name not in that list\n"
                prompt += "5. ZERO TOLERANCE RULE:\n"
                prompt += "   - If a column name is NOT explicitly shown in the 'Columns:' line for that table, DO NOT use it\n"
                prompt += "   - DO NOT assume common column names like 'name', 'status', 'date', 'item_name' exist\n"
                prompt += "   - DO NOT guess column names based on table name or context\n"
                prompt += "   - ONLY use column names that are ACTUALLY listed in the schema\n"
                prompt += "6. If the schema shows limited columns, use ONLY those columns - do not add more\n"
                prompt += "7. Explicitly list ALL columns with table aliases using ONLY schema-defined columns:\n"
                prompt += "   - Example: `CREATE VIEW my_view AS SELECT t1.col1, t1.col2, t2.col3 FROM table1 t1 JOIN table2 t2 ON t1.id = t2.id`\n"
                prompt += "   - But ONLY if col1, col2, col3 are ACTUALLY listed in the schema for those tables\n"
                prompt += "8. If a join column exists in both tables, select it only ONCE from one table\n"
                prompt += "9. Use table aliases (e.g., `po`, `pr`) and prefix all column names with the alias\n"
                prompt += "10. List columns explicitly: `SELECT po.column1, po.column2, pr.column3`\n"
                prompt += "    - But ONLY use column1, column2, column3 if they are ACTUALLY in the schema column list\n"
                prompt += "11. DO NOT use `SELECT po.*, pr.*` - this will cause duplicate column errors\n"
                prompt += "12. DO NOT invent column names - if a column is not in the schema column list, DO NOT use it\n"
                prompt += "13. Generate the CREATE VIEW statement with explicit column list using ONLY schema-defined columns\n"
                prompt += "14. REMEMBER: The schema shows columns in format 'Table: name\\n  Columns: col1, col2, col3' - use ONLY those columns\n"
                prompt += "15. FINAL CHECK: Before generating SQL, verify each column name appears in the 'Columns:' line for its table\n"
                prompt += "16. DO NOT REFUSE - Generate the SQL using the columns shown in the schema above\n"
                prompt += "=== END CRITICAL INSTRUCTIONS ===\n"
            elif any(keyword in user_upper for keyword in ['UPDATE', 'SET', 'MODIFY', 'CHANGE', 'EDIT']):
                prompt += "\n\n=== CRITICAL INSTRUCTIONS FOR UPDATE ===\n"
                prompt += "The user wants to UPDATE records in their database.\n"
                prompt += "1. Start your response IMMEDIATELY with ```sql\n"
                prompt += "2. Check the column list for the table you're updating - use ONLY those exact column names\n"
                prompt += "3. For WHERE clauses: Use ONLY column names that exist in the table's column list\n"
                prompt += "4. NEVER assume a table has an 'id' column - check the column list first\n"
                prompt += "5. Look for the actual primary key or identifier column (might be 'employee_id', 'customer_id', etc.)\n"
                prompt += "6. Use the EXACT table name and column names from the schema above\n"
                prompt += "7. DO NOT use generic column names like 'id', 'name', 'value' unless they actually exist in the column list\n"
                prompt += "8. CRITICAL: When user says 'update column_name = column_name + value':\n"
                prompt += "   - This means increment the column by the value\n"
                prompt += "   - Use the SAME column name on BOTH sides: UPDATE table SET column_name = column_name + value\n"
                prompt += "   - Check the schema - find the table and verify the column exists in THAT table\n"
                prompt += "   - NEVER use a column name from a different table\n"
                prompt += "   - Example: 'update division_id = division_id + 9000' → UPDATE division SET division_id = division_id + 9000\n"
                prompt += "   - WRONG: UPDATE division SET division_id = department_id + 9000 (department_id is from a different table!)\n"
                prompt += "=== END CRITICAL INSTRUCTIONS ===\n"
            elif any(keyword in user_upper for keyword in ['DELETE', 'REMOVE', 'DROP RECORDS']):
                prompt += "\n\n=== CRITICAL INSTRUCTIONS FOR DELETE ===\n"
                prompt += "The user wants to DELETE records from their database.\n"
                prompt += "1. Start your response IMMEDIATELY with ```sql\n"
                prompt += "2. For WHERE clauses: Use ONLY column names that exist in the table's column list\n"
                prompt += "3. NEVER assume a table has an 'id' column - check the column list first\n"
                prompt += "4. Look for the actual primary key or identifier column (might be 'employee_id', 'customer_id', etc.)\n"
                prompt += "5. Use the EXACT table name and column names from the schema above\n"
                prompt += "6. DO NOT use generic column names like 'id', 'name', 'value' unless they actually exist in the column list\n"
                prompt += "=== END CRITICAL INSTRUCTIONS ===\n"
            elif any(keyword in user_upper for keyword in ['CREATE TABLE', 'CREATE TABLES', 'DESIGN TABLE', 'BUILD TABLE', 'MAKE TABLE', 'NEW TABLE']):
                prompt += "\n\n=== CRITICAL INSTRUCTIONS FOR CREATE TABLE ===\n"
                prompt += "The user wants you to CREATE NEW tables based on their description.\n"
                prompt += "1. Start your response IMMEDIATELY with ```sql\n"
                prompt += "2. Generate CREATE TABLE statements based on the user's description\n"
                prompt += "3. Use appropriate column names, data types, and constraints\n"
                prompt += "4. Include PRIMARY KEYs, FOREIGN KEYs, and relationships as described\n"
                prompt += "5. Use PostgreSQL syntax (since database type is PostgreSQL)\n"
                prompt += "6. DO NOT say 'I cannot' or 'details not provided' - generate the SQL based on best practices for the described tables\n"
                prompt += "7. For purchase order tables, typical tables include: purchase_orders, purchase_order_items, suppliers, products, etc.\n"
                prompt += "8. Include relationships (FOREIGN KEYs) between related tables\n"
                prompt += "=== END CRITICAL INSTRUCTIONS ===\n"
            else:
                prompt += "\nIf the question requires SQL, provide the SQL query in a code block. Keep explanations brief and focus on the actual SQL."
        
        return prompt
    
    def _build_openai_messages(self) -> List[Dict[str, str]]:
        """Build messages array for OpenAI API"""
        messages = [{"role": "system", "content": SYSTEM_PROMPT_CHATBOT}]
        
        # Add recent history (last 10 messages)
        for msg in self.conversation_history[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        return messages
    
    def _build_anthropic_messages(self) -> List[Dict[str, str]]:
        """Build messages array for Anthropic API"""
        messages = []
        
        # Add recent history (last 10 messages)
        for msg in self.conversation_history[-10:]:
            messages.append({"role": msg.role, "content": msg.content})
        
        return messages
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        return [msg.to_dict() for msg in self.conversation_history]

