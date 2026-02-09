"""
Multi-Agent System for Database Query Analysis and Optimization
Implements specialized AI agents for query analysis, results review, debugging, and suggestions
"""

from __future__ import annotations
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


def _get_api_key(key_name: str) -> Optional[str]:
    """Get API key from environment or Streamlit secrets"""
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    return os.getenv(key_name)


@dataclass
class AgentResponse:
    """Response from an AI agent"""
    agent_name: str
    analysis: str
    suggestions: List[str]
    confidence: float  # 0.0 to 1.0
    metadata: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_name': self.agent_name,
            'analysis': self.analysis,
            'suggestions': self.suggestions,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, name: str, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4o"):
        self.name = name
        self.provider = provider
        self.model = model
        
        if not api_key:
            api_key = _get_api_key("OPENAI_API_KEY") if provider == "openai" else _get_api_key("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError(f"API key required for {name} agent")
        
        if provider == "openai" and OpenAI:
            self.client = OpenAI(api_key=api_key)
        elif provider == "anthropic" and Anthropic:
            self.client = Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Provider {provider} not available")
    
    @abstractmethod
    def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Perform analysis and return response"""
        pass
    
    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM with given prompts"""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                return response.choices[0].message.content
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return response.content[0].text
        except Exception as e:
            return f"Error calling LLM: {str(e)}"


class QueryAnalyzerAgent(BaseAgent):
    """Agent that analyzes SQL queries before execution"""
    
    SYSTEM_PROMPT = """You are an expert SQL query analyzer. Provide BRIEF analysis (2-3 sentences max).

Analyze queries for:
- Critical errors or security issues
- Destructive operations (DROP, DELETE without WHERE)
- Major performance problems

Format: One sentence assessment, then 1-2 key suggestions if needed. Be concise."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4o"):
        super().__init__("Query Analyzer", api_key, provider, model)
    
    def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze a SQL query before execution"""
        query = context.get('query', '')
        schema_info = context.get('schema_info', {})
        db_type = context.get('db_type', 'unknown')
        
        user_prompt = f"""Briefly analyze this SQL query (2-3 sentences max):

Database: {db_type} ({schema_info.get('total_tables', 0)} tables)
Query: ```sql
{query}
```

Provide: 1) Quick assessment, 2) Critical issues only (if any), 3) One key suggestion if needed. Be very brief."""
        
        analysis_text = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        
        # Extract suggestions (simple parsing - can be improved)
        suggestions = self._extract_suggestions(analysis_text)
        confidence = self._extract_confidence(analysis_text)
        
        return AgentResponse(
            agent_name=self.name,
            analysis=analysis_text,
            suggestions=suggestions,
            confidence=confidence,
            metadata={'query': query, 'db_type': db_type},
            timestamp=datetime.now()
        )
    
    def _extract_suggestions(self, text: str) -> List[str]:
        """Extract suggestions from analysis text"""
        suggestions = []
        lines = text.split('\n')
        for line in lines:
            if any(marker in line.lower() for marker in ['suggest', 'recommend', 'consider', 'should', 'could']):
                if line.strip() and not line.strip().startswith('#'):
                    suggestions.append(line.strip())
        return suggestions[:5]  # Limit to 5 suggestions
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level from analysis text"""
        import re
        # Look for confidence patterns like "confidence: 0.8" or "80% confident"
        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', text.lower())
        if confidence_match:
            try:
                return float(confidence_match.group(1))
            except:
                pass
        
        # Default confidence based on text content
        if any(word in text.lower() for word in ['error', 'issue', 'problem', 'warning']):
            return 0.7
        return 0.9


class ResultsAnalyzerAgent(BaseAgent):
    """Agent that analyzes query results and suggests solutions for errors/issues"""
    
    SYSTEM_PROMPT = """You are an expert database results analyzer. Provide BRIEF analysis (2-3 sentences max).

Focus on:
- Critical errors or anomalies
- Data quality issues
- One key follow-up action if needed

Be very concise. Only mention important issues."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4o"):
        super().__init__("Results Analyzer", api_key, provider, model)
    
    def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze query execution results"""
        query = context.get('query', '')
        result = context.get('result', {})
        error = context.get('error')
        rows_retrieved = context.get('rows_retrieved', 0)
        execution_time = context.get('execution_time', 0)
        
        user_prompt = f"""Briefly analyze this query result (2-3 sentences max):

Query: ```sql
{query}
```
Result: Success={result.get('success', False)}, Rows={rows_retrieved}, Time={execution_time:.3f}s
Error: {error if error else 'None'}

Provide: 1) Quick assessment, 2) Critical issues only, 3) One suggestion if needed. Be very brief."""
        
        analysis_text = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        
        suggestions = self._extract_suggestions(analysis_text)
        confidence = self._extract_confidence(analysis_text)
        
        return AgentResponse(
            agent_name=self.name,
            analysis=analysis_text,
            suggestions=suggestions,
            confidence=confidence,
            metadata={'query': query, 'rows_retrieved': rows_retrieved, 'has_error': bool(error)},
            timestamp=datetime.now()
        )
    
    def _extract_suggestions(self, text: str) -> List[str]:
        """Extract suggestions from analysis text"""
        suggestions = []
        lines = text.split('\n')
        for line in lines:
            if any(marker in line.lower() for marker in ['suggest', 'recommend', 'consider', 'try', 'should', 'could']):
                if line.strip() and not line.strip().startswith('#'):
                    suggestions.append(line.strip())
        return suggestions[:5]
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level from analysis text"""
        import re
        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', text.lower())
        if confidence_match:
            try:
                return float(confidence_match.group(1))
            except:
                pass
        return 0.8


class DebugAgent(BaseAgent):
    """Agent specialized in debugging SQL queries and database issues"""
    
    SYSTEM_PROMPT = """You are an expert SQL debugger. Provide BRIEF debugging (2-3 sentences max) AND a corrected SQL query.

CRITICAL REQUIREMENTS:
1. You MUST provide a corrected SQL query in a ```sql code block
2. Use ONLY actual column names from the provided schema - NEVER use generic names like 'id' unless that column actually exists
3. For JOIN queries: Use actual foreign key column names from the schema (e.g., 'department_id', 'employee_id')
4. For UPDATE/DELETE: Use actual primary key column names from the schema
5. Check the schema carefully before suggesting column names
6. For MULTIPLE UPDATE statements with foreign key constraints:
   - When updating PRIMARY KEYS that are referenced by FOREIGN KEYS in PostgreSQL:
     * IMPORTANT: Most PostgreSQL foreign key constraints are NOT DEFERRABLE by default
     * SET CONSTRAINTS ALL DEFERRED only works if constraints are explicitly created as DEFERRABLE
     * 
     * IMPORTANT: System triggers (RI_ConstraintTrigger) for foreign keys cannot be disabled
     * DISABLE TRIGGER ALL will fail with "permission denied: is a system trigger"
     * 
     * Option 1 (if foreign key column allows NULL):
       BEGIN;
       -- Step 1: Set foreign key to NULL temporarily (breaks constraint temporarily)
       UPDATE employee SET department_id = NULL;
       -- Step 2: Update parent table to new values
       UPDATE department SET department_id = department_id + 1000;
       -- Step 3: Update child to match parent using reverse mapping
       WITH parent_mapping AS (
         SELECT department_id AS new_id, department_id - 1000 AS old_id 
         FROM department
       )
       UPDATE employee 
       SET department_id = (SELECT new_id FROM parent_mapping 
                             WHERE parent_mapping.old_id = employee.department_id)
       WHERE employee.department_id IS NULL;
       COMMIT;
       Note: Only works if the foreign key column allows NULL values.
     
     * Option 2 (requires DBA/superuser): Drop and recreate constraint:
       BEGIN;
       ALTER TABLE employee DROP CONSTRAINT employee_department_id_fkey;
       UPDATE employee SET department_id = department_id + 1000;
       UPDATE department SET department_id = department_id + 1000;
       ALTER TABLE employee ADD CONSTRAINT employee_department_id_fkey 
         FOREIGN KEY (department_id) REFERENCES department(department_id);
       COMMIT;
       Note: This requires DROP/ADD CONSTRAINT permissions. Not recommended for production.
     
     * Option 3 (only if constraint is DEFERRABLE): Use SET CONSTRAINTS:
       BEGIN;
       SET CONSTRAINTS employee_department_id_fkey DEFERRED;
       UPDATE employee SET department_id = department_id + 1000;
       UPDATE department SET department_id = department_id + 1000;
       COMMIT;
       Note: Only works if constraint was created as DEFERRABLE.
     
     * Option 4: Ask a DBA to make the constraint DEFERRABLE:
       ALTER TABLE employee ALTER CONSTRAINT employee_department_id_fkey DEFERRABLE INITIALLY DEFERRED;
       Then use Option 3.
   - For PostgreSQL, try Option 1 (NULL approach) first if column allows NULL, otherwise you may need DBA help

Focus on:
- Root cause (one sentence)
- One specific fix suggestion with corrected SQL
- Use actual column names from schema
- Use three-step approach for updating referenced primary keys

Be very concise. Provide corrected SQL using actual schema column names."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4o"):
        super().__init__("Debug Agent", api_key, provider, model)
    
    def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Debug a query error or issue"""
        query = context.get('query', '')
        error = context.get('error', '')
        error_message = context.get('error_message', '')
        schema_info = context.get('schema_info', {})
        db_type = context.get('db_type', 'unknown')
        
        # Build schema context for the prompt
        schema_context = ""
        if schema_info and schema_info.get('tables'):
            tables = schema_info.get('tables', [])
            schema_context = f"\n\n=== DATABASE SCHEMA (USE ONLY THESE COLUMN NAMES) ===\n"
            schema_context += f"Database Type: {db_type}\n"
            schema_context += f"Total Tables: {schema_info.get('total_tables', len(tables))}\n\n"
            
            # Add table and column information
            for table in tables[:10]:  # Limit to first 10 tables
                if isinstance(table, dict):
                    table_name = table.get('table_name', 'unknown')
                    columns_list = table.get('columns', [])
                    if columns_list:
                        if isinstance(columns_list[0], dict):
                            col_names = [col.get('name', str(col)) for col in columns_list]
                        else:
                            col_names = [str(col) for col in columns_list]
                        schema_context += f"Table: {table_name}\n  Columns: {', '.join(col_names[:20])}\n"
                    else:
                        schema_context += f"Table: {table_name} (no column info)\n"
                elif isinstance(table, str):
                    schema_context += f"Table: {table}\n"
            
            schema_context += "\n=== END SCHEMA ===\n"
            schema_context += "\nCRITICAL: Use ONLY the column names listed above. NEVER use generic names like 'id' unless that exact column exists in the table's column list.\n"
        
        user_prompt = f"""Debug this SQL error and provide a corrected query:

Database: {db_type} ({schema_info.get('total_tables', 0)} tables)
{schema_context}
Query: ```sql
{query}
```
Error: {error} - {error_message}

REQUIRED:
1. Root cause (one sentence)
2. Provide a CORRECTED SQL query in a ```sql code block using ONLY actual column names from the schema above
3. Replace any generic column names (like 'id') with actual column names from the schema
4. For JOIN queries: Use actual foreign key columns from the schema (e.g., 'department_id', 'employee_id')
5. For INSERT statements with foreign key violations:
   - If error mentions "foreign key constraint" or "Key (column_name)=(value) is not present in table":
     * The foreign key value does not exist in the referenced table
     * Solution 1 (RECOMMENDED): First query existing values from the parent table, then use those values
       Example: If inserting into 'employee' with 'department_id', first run:
       SELECT department_id FROM department;
       Then use only those existing department_id values in your INSERT statements
     * Solution 2: Generate INSERT statements for the parent table first (if it's empty)
       Example: If 'department' table is empty, first insert departments:
       INSERT INTO department (department_id, department_name) VALUES (101, 'Sales');
       INSERT INTO department (department_id, department_name) VALUES (102, 'Marketing');
       Then insert employees using those department_id values
     * Solution 3: Use NULL if the foreign key column allows NULL values
       Example: INSERT INTO employee (employee_id, employee_name, department_id, salary) VALUES (1, 'John', NULL, 50000);
     * NEVER suggest using non-existent foreign key values
6. For MULTIPLE UPDATE statements with foreign key relationships:
   - If error mentions "foreign key constraint" or "referential integrity":
     * Identify which table is the PARENT (referenced) and which is the CHILD (referencing)
     * IMPORTANT: Most PostgreSQL foreign key constraints are NOT DEFERRABLE by default
     * SET CONSTRAINTS ALL DEFERRED will NOT work for non-deferrable constraints
     * 
     * For PostgreSQL, when updating PRIMARY KEYS referenced by FOREIGN KEYS:
       IMPORTANT: System triggers (RI_ConstraintTrigger) for foreign keys cannot be disabled.
       DISABLE TRIGGER ALL will fail with "permission denied: is a system trigger".
       
       Option 1 (if foreign key column allows NULL):
       BEGIN;
       -- Step 1: Set foreign key to NULL temporarily
       UPDATE child_table SET foreign_key_col = NULL;
       -- Step 2: Update parent table
       UPDATE parent_table SET primary_key_col = primary_key_col + 1000;
       -- Step 3: Update child to match parent using reverse mapping
       WITH parent_mapping AS (
         SELECT primary_key_col AS new_id, primary_key_col - 1000 AS old_id 
         FROM parent_table
       )
       UPDATE child_table 
       SET foreign_key_col = (SELECT new_id FROM parent_mapping 
                               WHERE parent_mapping.old_id = child_table.foreign_key_col)
       WHERE child_table.foreign_key_col IS NULL;
       COMMIT;
       Note: Only works if the foreign key column allows NULL values.
       
       Option 2 (requires DBA/superuser - not recommended for production):
       BEGIN;
       ALTER TABLE child_table DROP CONSTRAINT child_table_foreign_key_fkey;
       UPDATE child_table SET foreign_key_col = foreign_key_col + 1000;
       UPDATE parent_table SET primary_key_col = primary_key_col + 1000;
       ALTER TABLE child_table ADD CONSTRAINT child_table_foreign_key_fkey 
         FOREIGN KEY (foreign_key_col) REFERENCES parent_table(primary_key_col);
       COMMIT;
       
       Option 3 (only if constraint is DEFERRABLE):
       BEGIN;
       SET CONSTRAINTS child_table_foreign_key_fkey DEFERRED;
       UPDATE child_table SET foreign_key_col = foreign_key_col + 1000;
       UPDATE parent_table SET primary_key_col = primary_key_col + 1000;
       COMMIT;
       
       Option 4: Ask DBA to make constraint DEFERRABLE:
       ALTER TABLE child_table ALTER CONSTRAINT child_table_foreign_key_fkey DEFERRABLE INITIALLY DEFERRED;
       Then use Option 3.
     * Try Option 1 (NULL approach) first if column allows NULL, otherwise you may need DBA help

Be brief but provide the corrected SQL query with proper UPDATE ordering."""
        
        analysis_text = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        
        suggestions = self._extract_suggestions(analysis_text)
        confidence = self._extract_confidence(analysis_text)
        
        return AgentResponse(
            agent_name=self.name,
            analysis=analysis_text,
            suggestions=suggestions,
            confidence=confidence,
            metadata={'query': query, 'error': error, 'db_type': db_type},
            timestamp=datetime.now()
        )
    
    def _extract_suggestions(self, text: str) -> List[str]:
        """Extract debugging suggestions"""
        suggestions = []
        lines = text.split('\n')
        for line in lines:
            if any(marker in line.lower() for marker in ['fix', 'try', 'check', 'verify', 'ensure', 'change']):
                if line.strip() and not line.strip().startswith('#'):
                    suggestions.append(line.strip())
        return suggestions[:5]
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level"""
        import re
        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', text.lower())
        if confidence_match:
            try:
                return float(confidence_match.group(1))
            except:
                pass
        return 0.85


class SchemaDataAgent(BaseAgent):
    """Agent specialized in reading schema data and existing records before generating INSERT/UPDATE/DELETE statements"""
    
    SYSTEM_PROMPT = """You are an expert database schema and data analyzer. Your role is to analyze user requests for INSERT/UPDATE/DELETE operations and determine what data needs to be queried from the database before generating SQL statements.

CRITICAL REQUIREMENTS:
1. For INSERT operations with foreign keys: Identify which parent tables need to be queried to get existing foreign key values
2. For UPDATE/DELETE operations: Identify which tables need to be queried to check existing primary key values
3. Generate SELECT queries to retrieve necessary data (foreign key values, primary key values, etc.)
4. Provide brief analysis (2-3 sentences max) explaining what data needs to be checked
5. Always provide the SELECT queries in a ```sql code block

Focus on:
- Foreign key relationships: If inserting into a child table, query parent table for existing foreign key values
- Primary key constraints: If updating/deleting, check what primary key values exist
- Data dependencies: Identify any data that must exist before the operation can succeed

Be very concise. Provide SELECT queries that will help generate correct INSERT/UPDATE/DELETE statements."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4o"):
        super().__init__("Schema Data Agent", api_key, provider, model)
    
    def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze user request and determine what data needs to be queried"""
        user_query = context.get('user_query', '')
        schema_info = context.get('schema_info', {})
        db_type = context.get('db_type', 'unknown')
        
        # Build schema context for the prompt
        schema_context = ""
        if schema_info and schema_info.get('tables'):
            tables = schema_info.get('tables', [])
            schema_context = f"\n\n=== DATABASE SCHEMA ===\n"
            schema_context += f"Database Type: {db_type}\n"
            schema_context += f"Total Tables: {schema_info.get('total_tables', len(tables))}\n\n"
            
            # Add table and column information with foreign key hints
            # First, identify foreign key relationships
            fk_relationships = {}  # {child_table: [(fk_column, parent_table, parent_pk_column)]}
            for table in tables[:15]:  # Show more tables for better context
                if isinstance(table, dict):
                    table_name = table.get('table_name', 'unknown')
                    columns_list = table.get('columns', [])
                    foreign_keys = table.get('foreign_keys', [])
                    
                    # Extract foreign key relationships
                    if foreign_keys:
                        for fk in foreign_keys:
                            if isinstance(fk, dict):
                                fk_col = fk.get('constrained_columns', [])
                                referred_table = fk.get('referred_table', '')
                                referred_columns = fk.get('referred_columns', [])
                                if fk_col and referred_table:
                                    if table_name not in fk_relationships:
                                        fk_relationships[table_name] = []
                                    fk_relationships[table_name].append((
                                        fk_col[0] if fk_col else 'unknown',
                                        referred_table,
                                        referred_columns[0] if referred_columns else 'unknown'
                                    ))
                    
                    if columns_list:
                        if isinstance(columns_list[0], dict):
                            col_details = []
                            for col in columns_list:
                                col_name = col.get('name', str(col))
                                col_type = col.get('type', '')
                                is_pk = col.get('primary_key', False)
                                
                                col_str = f"{col_name} ({col_type})"
                                if is_pk:
                                    col_str += " PRIMARY KEY"
                                
                                # Check if this column is a foreign key
                                if table_name in fk_relationships:
                                    for fk_col, parent_table, parent_pk in fk_relationships[table_name]:
                                        if col_name == fk_col:
                                            col_str += f" -> REFERENCES {parent_table}({parent_pk})"
                                            break
                                
                                col_details.append(col_str)
                            schema_context += f"Table: {table_name}\n  Columns: {', '.join(col_details[:15])}\n"
                        else:
                            schema_context += f"Table: {table_name}\n  Columns: {', '.join([str(col) for col in columns_list[:15]])}\n"
                    else:
                        schema_context += f"Table: {table_name} (no column info)\n"
                elif isinstance(table, str):
                    schema_context += f"Table: {table}\n"
            
            # Add foreign key relationship summary
            if fk_relationships:
                schema_context += "\n=== FOREIGN KEY RELATIONSHIPS ===\n"
                for child_table, fks in fk_relationships.items():
                    for fk_col, parent_table, parent_pk in fks:
                        schema_context += f"{child_table}.{fk_col} -> {parent_table}.{parent_pk}\n"
                schema_context += "=== END FOREIGN KEY RELATIONSHIPS ===\n"
            
            schema_context += "\n=== END SCHEMA ===\n"
        
        user_prompt = f"""Analyze this user request and determine what data needs to be queried from the database:

User Request: {user_query}

{schema_context}

CRITICAL REQUIREMENTS:
1. If the user wants to INSERT into a table, identify ALL foreign key columns in that table
2. For EACH foreign key column, generate a SELECT query to get existing values from the referenced parent table
3. Example: If inserting into 'employee' table and 'employee' has 'department_id' -> REFERENCES 'department.department_id':
   - Generate: SELECT department_id FROM department;
4. Generate queries in a ```sql code block - ONE query per foreign key relationship
5. Explain briefly (1-2 sentences) why these queries are needed

STEP-BY-STEP PROCESS:
1. Identify the target table from user request (e.g., 'employee')
2. Find that table in the schema above
3. Look for foreign key relationships (columns with -> REFERENCES)
4. For EACH foreign key, generate: SELECT [parent_pk_column] FROM [parent_table];
5. If no foreign keys found, you may not need to generate queries (but still check)

Focus on:
- For INSERT: ALWAYS query parent tables for existing foreign key values - this is CRITICAL
- For UPDATE/DELETE: Query tables for existing primary key values
- Generate at least ONE SELECT query if foreign keys exist

Example output format:
```sql
SELECT department_id FROM department;
```"""
        
        analysis_text = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        
        # Extract SELECT queries from the response
        suggestions = self._extract_select_queries(analysis_text)
        confidence = self._extract_confidence(analysis_text)
        
        return AgentResponse(
            agent_name=self.name,
            analysis=analysis_text,
            suggestions=suggestions,
            confidence=confidence,
            metadata={'user_query': user_query, 'db_type': db_type},
            timestamp=datetime.now()
        )
    
    def _extract_select_queries(self, text: str) -> List[str]:
        """Extract SELECT queries from analysis text"""
        import re
        queries = []
        
        # Look for SQL code blocks
        sql_block_pattern = r'```sql\s*(.*?)\s*```'
        matches = re.findall(sql_block_pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            # Extract individual SELECT statements
            select_pattern = r'(SELECT\s+[^;]+(?:;[^;]+)*)'
            select_matches = re.findall(select_pattern, match, re.IGNORECASE | re.DOTALL)
            queries.extend(select_matches)
        
        # Also look for SELECT statements outside code blocks
        if not queries:
            select_pattern = r'(SELECT\s+[^;]+(?:;[^;]+)*)'
            select_matches = re.findall(select_pattern, text, re.IGNORECASE | re.DOTALL)
            queries.extend(select_matches)
        
        return queries[:5]  # Limit to 5 queries
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level"""
        import re
        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', text.lower())
        if confidence_match:
            try:
                return float(confidence_match.group(1))
            except:
                pass
        return 0.85


class ReviewAgent(BaseAgent):
    """Agent that reviews results and suggests optimizations and improvements"""
    
    SYSTEM_PROMPT = """You are an expert database query reviewer. Provide BRIEF review (2-3 sentences max).

Focus on:
- One key optimization if significant
- One data quality insight if notable
- One follow-up query suggestion if valuable

Be very concise. Only mention important improvements."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4o"):
        super().__init__("Review Agent", api_key, provider, model)
    
    def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Review query results and suggest improvements"""
        query = context.get('query', '')
        result = context.get('result', {})
        rows_retrieved = context.get('rows_retrieved', 0)
        execution_time = context.get('execution_time', 0)
        dataframe = context.get('dataframe')
        
        # Sample data info
        data_summary = "No data"
        if dataframe is not None and len(dataframe) > 0:
            data_summary = f"""
- Rows: {len(dataframe)}
- Columns: {list(dataframe.columns)[:10]}
- Sample data types: {dict(dataframe.dtypes.head(5))}
"""
        
        user_prompt = f"""Briefly review this query (2-3 sentences max):

Query: ```sql
{query}
```
Rows: {rows_retrieved}, Time: {execution_time:.3f}s
Data: {data_summary[:200] if len(data_summary) > 200 else data_summary}

Provide: 1) One key optimization if significant, 2) One insight if notable. Be very brief."""
        
        analysis_text = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        
        suggestions = self._extract_suggestions(analysis_text)
        confidence = self._extract_confidence(analysis_text)
        
        return AgentResponse(
            agent_name=self.name,
            analysis=analysis_text,
            suggestions=suggestions,
            confidence=confidence,
            metadata={'query': query, 'rows_retrieved': rows_retrieved, 'execution_time': execution_time},
            timestamp=datetime.now()
        )
    
    def _extract_suggestions(self, text: str) -> List[str]:
        """Extract review suggestions"""
        suggestions = []
        lines = text.split('\n')
        for line in lines:
            if any(marker in line.lower() for marker in ['suggest', 'recommend', 'consider', 'optimize', 'improve']):
                if line.strip() and not line.strip().startswith('#'):
                    suggestions.append(line.strip())
        return suggestions[:5]
    
    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level"""
        import re
        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', text.lower())
        if confidence_match:
            try:
                return float(confidence_match.group(1))
            except:
                pass
        return 0.8


class AgentOrchestrator:
    """Orchestrates multiple agents to work together"""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4o"):
        self.query_analyzer = QueryAnalyzerAgent(api_key, provider, model)
        self.results_analyzer = ResultsAnalyzerAgent(api_key, provider, model)
        self.debug_agent = DebugAgent(api_key, provider, model)
        self.review_agent = ReviewAgent(api_key, provider, model)
        self.agent_responses = []
    
    def analyze_query(self, query: str, schema_info: Dict[str, Any], db_type: str) -> AgentResponse:
        """Analyze query before execution"""
        context = {
            'query': query,
            'schema_info': schema_info,
            'db_type': db_type
        }
        response = self.query_analyzer.analyze(context)
        self.agent_responses.append(response)
        return response
    
    def analyze_results(self, query: str, result: Dict[str, Any], error: Optional[str] = None, 
                       rows_retrieved: int = 0, execution_time: float = 0, dataframe=None) -> AgentResponse:
        """Analyze query results"""
        context = {
            'query': query,
            'result': result,
            'error': error,
            'rows_retrieved': rows_retrieved,
            'execution_time': execution_time,
            'dataframe': dataframe
        }
        response = self.results_analyzer.analyze(context)
        self.agent_responses.append(response)
        return response
    
    def debug_error(self, query: str, error: str, error_message: str, 
                   schema_info: Dict[str, Any], db_type: str) -> AgentResponse:
        """Debug a query error"""
        context = {
            'query': query,
            'error': error,
            'error_message': error_message,
            'schema_info': schema_info,
            'db_type': db_type
        }
        response = self.debug_agent.analyze(context)
        self.agent_responses.append(response)
        return response
    
    def review_results(self, query: str, result: Dict[str, Any], rows_retrieved: int = 0, 
                      execution_time: float = 0, dataframe=None) -> AgentResponse:
        """Review query results and suggest improvements"""
        context = {
            'query': query,
            'result': result,
            'rows_retrieved': rows_retrieved,
            'execution_time': execution_time,
            'dataframe': dataframe
        }
        response = self.review_agent.analyze(context)
        self.agent_responses.append(response)
        return response
    
    def analyze_schema_data(self, user_query: str, schema_info: Dict[str, Any], db_type: str) -> AgentResponse:
        """Analyze what schema data needs to be queried before generating INSERT/UPDATE/DELETE statements"""
        context = {
            'user_query': user_query,
            'schema_info': schema_info,
            'db_type': db_type
        }
        response = self.schema_data_agent.analyze(context)
        self.agent_responses.append(response)
        return response
    
    def get_all_responses(self) -> List[AgentResponse]:
        """Get all agent responses"""
        return self.agent_responses
    
    def clear_responses(self):
        """Clear stored responses"""
        self.agent_responses = []
