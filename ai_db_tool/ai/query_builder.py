"""
AI-Powered SQL Query Builder
Converts natural language questions into optimized SQL queries
"""

from __future__ import annotations
import os
from typing import Optional, Dict, Any, List
from openai import OpenAI

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


SYSTEM_PROMPT_QUERY_BUILDER = """
You are an expert SQL query generator. Your task is to convert natural language questions into optimized SQL queries.

Guidelines:
1. Generate only valid SQL that follows the database's syntax (PostgreSQL, MySQL, SQL Server, Oracle, SQLite)
2. Use appropriate JOINs, WHERE clauses, and aggregations
3. Optimize queries for performance (use indexes, avoid SELECT *, use LIMIT when appropriate)
4. Handle NULL values appropriately
5. Use parameterized queries or explain which values need to be substituted
6. Always include comments explaining the query logic
7. If the question is ambiguous, ask for clarification
8. Support ALL SQL operations including:
   - SELECT (queries)
   - INSERT (add new data)
   - UPDATE (modify existing data)
   - DELETE (remove data)
   - DDL (CREATE, DROP, ALTER tables/indexes/views/etc.)
9. Use database-specific syntax based on the database type provided
10. Never include destructive operations unless explicitly requested

Return ONLY the SQL query, no explanations.
"""


class AIQueryBuilder:
    """Generate SQL queries from natural language using AI"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        provider: str = "openai"
    ):
        """
        Initialize AI Query Builder
        
        Args:
            api_key: API key for OpenAI or Anthropic
            model: Model to use (gpt-4o, gpt-4o-mini, claude-3-5-sonnet)
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
    
    def generate_query(
        self,
        question: str,
        schema_info: Optional[Dict[str, Any]] = None,
        db_type: str = "postgresql"
    ) -> str:
        """
        Generate SQL query from natural language question
        
        Args:
            question: Natural language question (e.g., "Show me top 10 customers by sales")
            schema_info: Database schema information (tables, columns)
            db_type: Database type (postgresql, mysql, sqlserver, oracle, sqlite)
            
        Returns:
            Generated SQL query string
        """
        # Check if AI client is available
        if not self.client or not self.api_key_available:
            return "-- AI Query Generation requires an API key. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
        
        # Build context with schema information
        context = f"Database Type: {db_type}\n\n"
        
        if schema_info:
            context += "Available Tables and Columns:\n"
            for table in schema_info.get('tables', [])[:20]:  # Limit to first 20 tables
                table_name = table.get('table_name', 'unknown')
                columns = ', '.join([col['name'] for col in table.get('columns', [])])
                context += f"- {table_name}: {columns}\n"
        
        user_prompt = f"{context}\n\nQuestion: {question}\n\nGenerate the SQL query:"
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_QUERY_BUILDER},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=SYSTEM_PROMPT_QUERY_BUILDER,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                )
                return response.content[0].text.strip()
        
        except Exception as e:
            raise ValueError(f"Failed to generate SQL query: {e}")
    
    def explain_query(self, sql_query: str) -> str:
        """
        Explain SQL query in natural language
        
        Args:
            sql_query: SQL query to explain
            
        Returns:
            Natural language explanation
        """
        prompt = f"""
        Explain the following SQL query in simple, natural language:
        
        ```sql
        {sql_query}
        ```
        
        Provide a clear explanation of what this query does, including:
        1. What data it retrieves
        2. What conditions/filters are applied
        3. What joins or relationships are used
        4. Any aggregations or calculations performed
        """
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                )
                return response.content[0].text.strip()
        
        except Exception as e:
            raise ValueError(f"Failed to explain query: {e}")
    
    def optimize_query(self, sql_query: str, execution_plan: Optional[str] = None) -> str:
        """
        Optimize SQL query for better performance
        
        Args:
            sql_query: SQL query to optimize
            execution_plan: Query execution plan (if available)
            
        Returns:
            Optimized SQL query
        """
        # Check if AI client is available
        if not self.client or not self.api_key_available:
            return "-- AI Query Optimization requires an API key. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
        
        context = f"Query to optimize:\n```sql\n{sql_query}\n```\n"
        
        if execution_plan:
            context += f"Current Execution Plan:\n{execution_plan}\n"
        
        prompt = f"""
        {context}
        
        Provide an optimized version of this SQL query. Consider:
        1. Using appropriate indexes
        2. Reducing full table scans
        3. Optimizing JOINs
        4. Limiting result sets
        5. Using appropriate WHERE clause conditions
        
        Return ONLY the optimized SQL query.
        """
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                )
                return response.content[0].text.strip()
        
        except Exception as e:
            raise ValueError(f"Failed to optimize query: {e}")
    
    def debug_query(self, sql_query: str, error_message: str, schema_context: str = "") -> str:
        """
        Debug SQL query error and suggest fixes
        
        Args:
            sql_query: SQL query with error
            error_message: Error message from database
            schema_context: Optional schema context for better debugging
            
        Returns:
            Fixed SQL query or debugging suggestions
        """
        # Check if AI client is available
        if not self.client or not self.api_key_available:
            return "AI Query Debugging requires an API key. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable."
        
        context = ""
        if schema_context:
            context = f"\n{schema_context}\n"
        
        prompt = f"""
        Fix the following SQL query that has an error:{context}
        
        Query:
        ```sql
        {sql_query}
        ```
        
        Error:
        {error_message}
        
        IMPORTANT: Use ONLY the tables and columns from the schema provided above. Generate the corrected SQL query using the correct table names and column names. Do NOT make up table or column names.
        
        Provide the corrected SQL query and briefly explain what was wrong.
        """
        
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                )
                return response.choices[0].message.content.strip()
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                )
                return response.content[0].text.strip()
        
        except Exception as e:
            raise ValueError(f"Failed to debug query: {e}")

