"""
FastAPI Backend Server for AI Autocomplete
Provides endpoints for Monaco Editor autocomplete and query suggestions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_db_tool.ai.query_builder import AIQueryBuilder

load_dotenv()

app = FastAPI(title="AI Database Tool API", version="1.0.0")

# CORS middleware to allow Streamlit to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Query Builder
query_builder = None

def get_query_builder():
    """Get or initialize the AI Query Builder"""
    global query_builder
    if query_builder is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        query_builder = AIQueryBuilder(api_key=api_key, model="gpt-4o", provider="openai")
    return query_builder


class AutocompleteRequest(BaseModel):
    """Request model for autocomplete"""
    query: str  # Current SQL query
    cursor_position: int  # Cursor position in the query
    database_type: Optional[str] = None  # Database type (postgresql, mysql, sqlite, etc.)
    schema_info: Optional[Dict[str, Any]] = None  # Database schema information
    tables: Optional[List[str]] = None  # Available tables


class AutocompleteResponse(BaseModel):
    """Response model for autocomplete"""
    suggestions: List[Dict[str, Any]]  # List of autocomplete suggestions
    completions: List[str]  # List of completion strings
    hints: Optional[str] = None  # Optimization hints


class QueryOptimizationRequest(BaseModel):
    """Request model for query optimization"""
    query: str
    database_type: Optional[str] = None
    schema_info: Optional[Dict[str, Any]] = None


class QueryOptimizationResponse(BaseModel):
    """Response model for query optimization"""
    optimized_query: str
    suggestions: List[str]
    explanation: str


@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "AI Database Tool API", "version": "1.0.0"}


@app.post("/api/autocomplete", response_model=AutocompleteResponse)
async def get_autocomplete(request: AutocompleteRequest):
    """
    Get AI-powered autocomplete suggestions for SQL query
    
    This endpoint provides intelligent autocomplete suggestions based on:
    - Current query context
    - Database schema
    - Available tables and columns
    - SQL best practices
    """
    try:
        builder = get_query_builder()
        
        # Extract context around cursor
        query = request.query
        cursor_pos = request.cursor_position
        
        # Get text before and after cursor
        before_cursor = query[:cursor_pos]
        after_cursor = query[cursor_pos:]
        
        # Build context for AI
        context = f"""
        Current SQL query (cursor at position {cursor_pos}):
        {query}
        
        Text before cursor: {before_cursor}
        Text after cursor: {after_cursor}
        """
        
        if request.schema_info:
            context += f"\nDatabase schema: {request.schema_info}"
        
        if request.tables:
            context += f"\nAvailable tables: {', '.join(request.tables)}"
        
        # Generate suggestions using AI
        prompt = f"""
        Based on the SQL query context below, provide intelligent autocomplete suggestions.
        Focus on:
        1. Completing the current statement (SELECT, INSERT, UPDATE, DELETE, etc.)
        2. Suggesting table names, column names, and SQL keywords
        3. Providing optimization hints
        
        Context:
        {context}
        
        Provide suggestions in the following format:
        - Completion text (what to insert)
        - Label (description)
        - Kind (keyword, table, column, function, etc.)
        - Documentation (help text)
        
        Return JSON format with suggestions array.
        """
        
        # Call AI for suggestions
        response = builder.client.chat.completions.create(
            model=builder.model,
            messages=[
                {"role": "system", "content": "You are an expert SQL autocomplete assistant. Provide helpful, accurate SQL completions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        # Parse AI response and create suggestions
        suggestions = []
        completions = []
        
        # Extract suggestions from AI response
        # For now, provide basic suggestions based on context
        words = before_cursor.strip().split()
        last_word = words[-1].upper() if words else ""
        
        # Common SQL keywords
        sql_keywords = [
            "SELECT", "FROM", "WHERE", "JOIN", "INNER", "LEFT", "RIGHT", "FULL",
            "ON", "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "OFFSET",
            "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE",
            "CREATE", "TABLE", "INDEX", "VIEW", "ALTER", "DROP",
            "AND", "OR", "NOT", "IN", "LIKE", "BETWEEN", "IS NULL", "IS NOT NULL",
            "COUNT", "SUM", "AVG", "MAX", "MIN", "DISTINCT", "AS"
        ]
        
        # Filter keywords based on context
        if last_word:
            filtered_keywords = [kw for kw in sql_keywords if kw.startswith(last_word)]
        else:
            filtered_keywords = sql_keywords[:10]  # Show first 10
        
        # Add table suggestions
        if request.tables:
            for table in request.tables:
                if not last_word or table.upper().startswith(last_word.upper()):
                    suggestions.append({
                        "label": table,
                        "kind": "table",
                        "insertText": table,
                        "documentation": f"Table: {table}"
                    })
                    completions.append(table)
        
        # Add keyword suggestions
        for keyword in filtered_keywords:
            suggestions.append({
                "label": keyword,
                "kind": "keyword",
                "insertText": keyword,
                "documentation": f"SQL keyword: {keyword}"
            })
            completions.append(keyword)
        
        # Add AI-generated suggestions if available
        if ai_response:
            # Try to extract suggestions from AI response
            # This is a simplified version - you can enhance it
            lines = ai_response.split('\n')
            for line in lines[:5]:  # Take first 5 suggestions
                line = line.strip()
                if line and len(line) < 50:  # Reasonable suggestion length
                    suggestions.append({
                        "label": line,
                        "kind": "snippet",
                        "insertText": line,
                        "documentation": "AI suggestion"
                    })
                    completions.append(line)
        
        return AutocompleteResponse(
            suggestions=suggestions[:20],  # Limit to 20 suggestions
            completions=completions[:20],
            hints=ai_response[:200] if ai_response else None  # First 200 chars as hint
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autocomplete error: {str(e)}")


@app.post("/api/optimize", response_model=QueryOptimizationResponse)
async def optimize_query(request: QueryOptimizationRequest):
    """
    Get query optimization suggestions using AI
    """
    try:
        builder = get_query_builder()
        
        # Use the existing optimize_query method
        result = builder.optimize_query(
            request.query,
            db_type=request.database_type,
            schema_info=request.schema_info
        )
        
        return QueryOptimizationResponse(
            optimized_query=result.get("optimized_query", request.query),
            suggestions=result.get("suggestions", []),
            explanation=result.get("explanation", "")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization error: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

