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
                    temperature=0.3
                )
                return response.choices[0].message.content
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return response.content[0].text
        except Exception as e:
            return f"Error calling LLM: {str(e)}"


class QueryAnalyzerAgent(BaseAgent):
    """Agent that analyzes SQL queries before execution"""
    
    SYSTEM_PROMPT = """You are an expert SQL query analyzer. Your role is to:
1. Analyze SQL queries for potential issues BEFORE execution
2. Identify syntax errors, logical errors, and performance issues
3. Check for security concerns (SQL injection risks, dangerous operations)
4. Suggest optimizations and improvements
5. Warn about potentially destructive operations (DROP, DELETE without WHERE, etc.)

Provide your analysis in a clear, structured format with:
- Overall assessment
- Specific issues found (if any)
- Suggestions for improvement
- Confidence level (0.0 to 1.0) in your analysis

Be thorough but concise. Focus on actionable insights."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4o"):
        super().__init__("Query Analyzer", api_key, provider, model)
    
    def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze a SQL query before execution"""
        query = context.get('query', '')
        schema_info = context.get('schema_info', {})
        db_type = context.get('db_type', 'unknown')
        
        user_prompt = f"""Analyze this SQL query:

Database Type: {db_type}
Schema Information: {schema_info.get('total_tables', 0)} tables available

Query to analyze:
```sql
{query}
```

Please provide:
1. Overall assessment (is this query safe and well-formed?)
2. Any syntax or logical errors you can spot
3. Performance concerns
4. Security concerns
5. Suggestions for improvement
6. Confidence level (0.0-1.0) in your analysis

Format your response clearly with sections."""
        
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
    
    SYSTEM_PROMPT = """You are an expert database results analyzer. Your role is to:
1. Analyze query execution results
2. Identify errors, anomalies, or unexpected results
3. Suggest solutions when issues are detected
4. Provide insights about data quality and patterns
5. Recommend follow-up queries or actions

When analyzing results, consider:
- Error messages and their meanings
- Empty result sets (might indicate query issues)
- Unexpected data patterns
- Performance implications
- Data quality issues

Provide clear, actionable suggestions."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4o"):
        super().__init__("Results Analyzer", api_key, provider, model)
    
    def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Analyze query execution results"""
        query = context.get('query', '')
        result = context.get('result', {})
        error = context.get('error')
        rows_retrieved = context.get('rows_retrieved', 0)
        execution_time = context.get('execution_time', 0)
        
        user_prompt = f"""Analyze this query execution result:

Query executed:
```sql
{query}
```

Execution Result:
- Success: {result.get('success', False)}
- Rows retrieved: {rows_retrieved}
- Execution time: {execution_time:.3f}s
- Error: {error if error else 'None'}

Result details:
{result.get('message', 'No additional details')}

Please analyze:
1. Is the result expected?
2. Are there any issues or anomalies?
3. What suggestions do you have?
4. Should the user take any follow-up actions?
5. Confidence level (0.0-1.0) in your analysis"""
        
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
    
    SYSTEM_PROMPT = """You are an expert SQL debugger. Your role is to:
1. Debug SQL query errors and issues
2. Identify root causes of problems
3. Provide step-by-step debugging guidance
4. Suggest fixes and workarounds
5. Explain error messages in user-friendly terms

When debugging, consider:
- Syntax errors
- Type mismatches
- Missing tables/columns
- Permission issues
- Logic errors
- Database-specific quirks

Provide clear, actionable debugging steps."""
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "openai", model: str = "gpt-4o"):
        super().__init__("Debug Agent", api_key, provider, model)
    
    def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """Debug a query error or issue"""
        query = context.get('query', '')
        error = context.get('error', '')
        error_message = context.get('error_message', '')
        schema_info = context.get('schema_info', {})
        db_type = context.get('db_type', 'unknown')
        
        user_prompt = f"""Debug this SQL query error:

Database Type: {db_type}
Schema: {schema_info.get('total_tables', 0)} tables available

Query that failed:
```sql
{query}
```

Error information:
- Error type: {error}
- Error message: {error_message}

Please provide:
1. Root cause analysis
2. Step-by-step debugging approach
3. Specific fix suggestions
4. Alternative approaches if the fix doesn't work
5. Confidence level (0.0-1.0) in your diagnosis"""
        
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


class ReviewAgent(BaseAgent):
    """Agent that reviews results and suggests optimizations and improvements"""
    
    SYSTEM_PROMPT = """You are an expert database query reviewer. Your role is to:
1. Review query results for quality and completeness
2. Suggest optimizations and improvements
3. Identify data quality issues
4. Recommend best practices
5. Suggest follow-up queries or analyses

When reviewing, consider:
- Query efficiency and performance
- Result completeness
- Data patterns and insights
- Opportunities for optimization
- Best practices adherence

Provide constructive, actionable feedback."""
    
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
        
        user_prompt = f"""Review this query and its results:

Query:
```sql
{query}
```

Execution Summary:
- Rows retrieved: {rows_retrieved}
- Execution time: {execution_time:.3f}s
- Success: {result.get('success', False)}

Data Summary:
{data_summary}

Please provide:
1. Overall review of query quality
2. Optimization suggestions
3. Data quality observations
4. Best practice recommendations
5. Suggested follow-up queries or analyses
6. Confidence level (0.0-1.0) in your review"""
        
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
    
    def get_all_responses(self) -> List[AgentResponse]:
        """Get all agent responses"""
        return self.agent_responses
    
    def clear_responses(self):
        """Clear stored responses"""
        self.agent_responses = []
