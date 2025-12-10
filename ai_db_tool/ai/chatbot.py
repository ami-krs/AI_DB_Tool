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

IMPORTANT RULES:
- ONLY generate SQL queries (SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, etc.) - NEVER shell commands or CLI syntax
- Generate ONLY the SQL statement, nothing else
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

Examples:
- CORRECT: SELECT * FROM employees WHERE salary > 50000
- CORRECT: INSERT INTO employees (name, salary) VALUES ('John', 60000)
- CORRECT: CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT)
- WRONG: sqlite3 database.db "SELECT * FROM employees" or .tables

Guidelines:
- Be helpful, accurate, and concise
- Always provide pure SQL only
- Ask clarifying questions when needed
- Provide explanations along with queries
- Never execute destructive operations unless explicitly requested
- Remember context from previous messages in the conversation
- Support complete database management capabilities
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
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
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
            if include_sql and "```sql" in response_text:
                sql_start = response_text.find("```sql")
                sql_end = response_text.find("```", sql_start + 6)
                if sql_end != -1:
                    sql_query = response_text[sql_start + 6:sql_end].strip()
                    response_text = response_text[:sql_start] + response_text[sql_end + 3:].strip()
            
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
            prompt += "Database Schema:\n"
            for table in self.schema_context.get('tables', [])[:10]:
                table_name = table.get('table_name', 'unknown')
                columns = ', '.join([col['name'] for col in table.get('columns', [])])
                prompt += f"- {table_name}: {columns}\n"
            prompt += "\n"
        
        prompt += f"User Question: {user_message}\n"
        
        if include_sql:
            prompt += "\nIf the question requires SQL, provide both an explanation and the SQL query in a code block."
        
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

