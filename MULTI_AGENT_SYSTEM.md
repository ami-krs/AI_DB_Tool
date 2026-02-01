# Multi-Agent AI System Documentation

## Overview

The AI Database Tool now includes a sophisticated multi-agent system that provides intelligent analysis, debugging, and optimization suggestions for SQL queries and results.

## Architecture

### Agent Types

1. **🔍 Query Analyzer Agent**
   - **Role**: Analyzes SQL queries BEFORE execution
   - **Capabilities**:
     - Identifies syntax and logical errors
     - Detects security concerns (SQL injection risks)
     - Warns about destructive operations (DROP, DELETE without WHERE)
     - Suggests optimizations and improvements
   - **When Active**: Before query execution

2. **📊 Results Analyzer Agent**
   - **Role**: Analyzes query execution results
   - **Capabilities**:
     - Identifies errors, anomalies, or unexpected results
     - Suggests solutions when issues are detected
     - Provides insights about data quality and patterns
     - Recommends follow-up queries or actions
   - **When Active**: After successful query execution

3. **🐛 Debug Agent**
   - **Role**: Specialized in debugging SQL errors
   - **Capabilities**:
     - Analyzes error messages and root causes
     - Provides step-by-step debugging guidance
     - Suggests fixes and workarounds
     - Explains errors in user-friendly terms
   - **When Active**: When query execution fails

4. **✨ Review Agent**
   - **Role**: Reviews results and suggests optimizations
   - **Capabilities**:
     - Reviews query efficiency and performance
     - Identifies data quality issues
     - Recommends best practices
     - Suggests follow-up queries or analyses
   - **When Active**: After successful query execution

### Agent Orchestrator

The `AgentOrchestrator` coordinates all agents and manages their responses. It:
- Initializes all agents with proper API keys
- Routes queries to appropriate agents based on context
- Collects and manages agent responses
- Provides a unified interface for agent interactions

## Workflow

### Query Execution Flow with Agents

1. **Pre-Execution** (Query Analyzer)
   ```
   User enters query → Query Analyzer analyzes → Shows analysis → Execute query
   ```

2. **Execution**
   ```
   Execute query → Get result (success or error)
   ```

3. **Post-Execution** (Results Analyzer + Review Agent)
   ```
   If success → Results Analyzer + Review Agent analyze → Show suggestions
   ```

4. **Error Handling** (Debug Agent)
   ```
   If error → Debug Agent analyzes error → Shows debugging suggestions
   ```

## Usage

### Enabling/Disabling Agents

1. Go to **Settings** → **🤖 AI Agents**
2. Toggle "Enable AI Agents" on/off
3. Agents are enabled by default

### Viewing Agent Analysis

Agent analysis appears automatically:
- **Before execution**: Query Analyzer suggestions
- **After execution**: Results Analyzer and Review Agent insights
- **On errors**: Debug Agent troubleshooting steps

Each agent response shows:
- Analysis summary
- Specific suggestions
- Confidence level
- Technical details (expandable)

## File Structure

```
ai_db_tool/ai/
├── agents.py              # Agent classes and orchestrator
├── chatbot.py             # Existing chatbot
└── query_builder.py       # Existing query builder

webapp/
├── ui/
│   └── agent_display.py   # UI components for displaying agent responses
├── utils/
│   └── query_execution.py # Integrated agent calls
└── session.py             # Session state (enable_ai_agents flag)
```

## Configuration

### API Keys

Agents use the same API keys as the chatbot:
- `OPENAI_API_KEY` (for OpenAI models)
- `ANTHROPIC_API_KEY` (for Anthropic models)

Set in:
- Streamlit Cloud: Secrets
- Local: Environment variables or `.env` file

### Default Settings

- **Agents Enabled**: `True` (default)
- **Provider**: OpenAI (if key available), else Anthropic
- **Model**: `gpt-4o` (OpenAI) or `claude-3-5-sonnet-20241022` (Anthropic)

## Example Agent Responses

### Query Analyzer Example
```
🔍 Query Analyzer 🔵 (Confidence: 🟢 90%)

Analysis:
This query looks well-formed and safe. However, I notice:
- The query uses SELECT * which may impact performance
- Consider adding a LIMIT clause for large tables

Suggestions:
1. Consider specifying columns instead of SELECT *
2. Add LIMIT clause for better performance
3. Consider adding indexes if querying frequently
```

### Debug Agent Example
```
🐛 Debug Agent 🔴 (Confidence: 🟢 85%)

Analysis:
The error "table does not exist" indicates the table name is incorrect.

Root Cause:
- Table name might be case-sensitive
- Table might not exist in the current schema
- Database connection might be pointing to wrong database

Suggestions:
1. Check table name spelling and case
2. Verify table exists: SELECT * FROM information_schema.tables
3. Check current database/schema connection
```

## Benefits

1. **Proactive Error Prevention**: Query Analyzer catches issues before execution
2. **Intelligent Debugging**: Debug Agent provides actionable error resolution
3. **Performance Optimization**: Review Agent suggests improvements
4. **Data Quality Insights**: Results Analyzer identifies anomalies
5. **Learning Tool**: Helps users understand SQL best practices

## Performance Considerations

- Agents run asynchronously and don't block query execution
- Analysis appears after results are displayed
- Can be disabled if API costs are a concern
- Each agent call uses ~500-2000 tokens

## Future Enhancements

Potential improvements:
- Agent collaboration (agents discussing with each other)
- Learning from user feedback
- Custom agent prompts
- Agent response caching
- Multi-model agent comparison

## Troubleshooting

### Agents Not Working

1. **Check API Keys**: Ensure `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set
2. **Check Settings**: Verify "Enable AI Agents" is toggled on
3. **Check Logs**: Look for import errors or API errors in Streamlit Cloud logs

### Agents Too Slow

- Agents run in background and don't block execution
- Consider disabling for very simple queries
- API rate limits may affect response time

### Agent Suggestions Not Helpful

- Agents improve with better context (schema info, query history)
- Ensure database connection is active for better suggestions
- Provide feedback through the UI (future feature)

---

**Status**: ✅ Implemented and Deployed
**Version**: 1.0
**Last Updated**: February 1, 2025
