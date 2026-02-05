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
- Ask clarifying questions ONLY when absolutely necessary (e.g., missing critical information)
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
                # If no SQL block found but response contains SQL-like text, try to extract it
                elif any(keyword in response_text.upper() for keyword in ['INSERT INTO', 'SELECT', 'UPDATE', 'DELETE FROM', 'CREATE TABLE']):
                    # Try to find SQL statements even without code blocks
                    import re
                    sql_pattern = r'(INSERT\s+INTO[^;]+(?:;[^;]+)*)'
                    matches = re.findall(sql_pattern, response_text, re.IGNORECASE | re.DOTALL)
                    if matches:
                        sql_query = '; '.join(matches)
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
                        else:
                            prompt += f"\nTable: {str(table)}\n"
                prompt += "\n=== END OF SCHEMA ===\n\n"
                prompt += "🚨 CRITICAL RULES FOR SQL GENERATION (VIOLATION WILL CAUSE ERRORS):\n"
                prompt += "1. You MUST ONLY use table names from the list above: " + ', '.join(all_table_names[:10]) + (f" and {len(all_table_names) - 10} more" if len(all_table_names) > 10 else "") + "\n"
                prompt += "2. You MUST ONLY use column names that appear in the column lists above for each table.\n"
                prompt += "3. When user asks to insert records in 'all tables', generate INSERT statements for EACH table in the list above.\n"
                prompt += "4. NEVER use placeholder names like 'example_table', 'test_table', 'table1', 'table2', 'table_name', 'column1', 'column2', 'column3' - these DO NOT EXIST in this database.\n"
                prompt += "5. NEVER use 'table_name' as a literal string in SQL (e.g., 'FROM dfu.table_name') - replace it with actual table names from the list.\n"
                prompt += "6. If user asks for 'records from DFU table' or 'records from schema X', they likely mean tables IN that schema. Generate SELECT statements for each table in that schema, or ask which specific table they want.\n"
                prompt += "7. NEVER generate 'SELECT * FROM schema_name' - you cannot SELECT from a schema directly. Use 'SELECT * FROM schema_name.table_name' instead.\n"
                prompt += "8. Generate actual SQL statements directly - do NOT provide explanations, examples, or 'here's how you can' text.\n"
                prompt += "9. If you cannot see the table names above, DO NOT generate SQL - return an error instead.\n\n"
        
        prompt += f"User Question: {user_message}\n"
        
        if include_sql:
            # For INSERT/UPDATE/DELETE operations, emphasize generating actual SQL, not explanations
            user_upper = user_message.upper()
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

