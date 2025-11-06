# Monaco Editor with AI Autocomplete Guide

## Overview

The AI Database Tool now includes **Monaco Editor** (the same editor that powers VS Code) with **AI-powered autocomplete** using GPT-4. This provides a professional SQL editing experience with intelligent code completion, syntax highlighting, and optimization hints.

## Features

### ✨ Monaco Editor Features
- **Syntax Highlighting**: Beautiful SQL syntax highlighting
- **Code Completion**: Intelligent autocomplete for SQL keywords, tables, and columns
- **Multi-cursor Editing**: Support for multiple cursors
- **Find & Replace**: Advanced search and replace functionality
- **Code Folding**: Collapse/expand code blocks
- **Dark Mode Support**: Automatically adapts to your theme preference

### 🤖 AI Autocomplete Features
- **Context-Aware Suggestions**: AI understands your query context
- **Table & Column Suggestions**: Suggests available tables and columns from your database
- **SQL Keyword Completion**: Completes SQL keywords based on context
- **Optimization Hints**: Provides suggestions for query optimization
- **Database-Specific**: Adapts to your database type (PostgreSQL, MySQL, SQLite, etc.)

## Setup

### 1. Start the API Server

The Monaco Editor requires a backend API server for AI autocomplete. Start it using:

```bash
# Option 1: Using the startup script
./start_api_server.sh

# Option 2: Direct Python command
python webapp/api_server.py
```

The API server will run on `http://localhost:8000` by default.

### 2. Enable Monaco Editor in Streamlit

1. Start the Streamlit app:
   ```bash
   streamlit run webapp/app.py
   ```

2. In the sidebar, toggle **"Use Monaco Editor (AI Autocomplete)"** to enable it.

3. (Optional) Configure the API Server URL if your API server is running on a different port or host.

## Usage

### Basic Usage

1. **Enable Monaco Editor**: Toggle the switch in the sidebar
2. **Connect to Database**: Connect to your database as usual
3. **Start Typing**: Begin typing your SQL query
4. **Get Suggestions**: Press `Ctrl+Space` (or `Cmd+Space` on Mac) to trigger autocomplete
5. **Select Suggestion**: Use arrow keys to navigate and Enter to select

### Keyboard Shortcuts

Monaco Editor supports all standard VS Code keyboard shortcuts:

- **Ctrl+Space** / **Cmd+Space**: Trigger autocomplete
- **Ctrl+F** / **Cmd+F**: Find
- **Ctrl+H** / **Cmd+H**: Find and Replace
- **Ctrl+/** / **Cmd+/**: Toggle comment
- **Alt+Up/Down**: Move line up/down
- **Shift+Alt+Up/Down**: Copy line up/down
- **Ctrl+D** / **Cmd+D**: Select next occurrence
- **Ctrl+Shift+L** / **Cmd+Shift+L**: Select all occurrences

### AI Autocomplete

The AI autocomplete provides intelligent suggestions based on:

1. **Current Query Context**: Understands what you're trying to write
2. **Database Schema**: Suggests tables and columns from your connected database
3. **SQL Best Practices**: Recommends optimized SQL patterns
4. **Database Type**: Adapts suggestions to your database (PostgreSQL, MySQL, etc.)

### Example

When you type:
```sql
SELECT * FROM
```

The AI will suggest:
- Available table names from your database
- Common SQL keywords (WHERE, JOIN, etc.)
- Column names if you've selected a table

## API Endpoints

The backend API provides the following endpoints:

### `/api/autocomplete`
**POST** - Get AI-powered autocomplete suggestions

**Request:**
```json
{
  "query": "SELECT * FROM users WHERE",
  "cursor_position": 25,
  "database_type": "postgresql",
  "schema_info": {...},
  "tables": ["users", "orders", "products"]
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "label": "users",
      "kind": "table",
      "insertText": "users",
      "documentation": "Table: users"
    },
    ...
  ],
  "completions": ["users", "orders", "products"],
  "hints": "Consider adding an index on the WHERE clause column"
}
```

### `/api/optimize`
**POST** - Get query optimization suggestions

**Request:**
```json
{
  "query": "SELECT * FROM users",
  "database_type": "postgresql",
  "schema_info": {...}
}
```

**Response:**
```json
{
  "optimized_query": "SELECT id, name, email FROM users",
  "suggestions": [
    "Avoid SELECT *",
    "Add LIMIT clause",
    "Consider adding indexes"
  ],
  "explanation": "Using SELECT * retrieves all columns..."
}
```

## Configuration

### API Server URL

By default, the API server runs on `http://localhost:8000`. You can change this in the Streamlit sidebar when Monaco Editor is enabled.

### Theme

Monaco Editor automatically uses:
- **Light Theme** (`vs`) when dark mode is disabled
- **Dark Theme** (`vs-dark`) when dark mode is enabled

## Troubleshooting

### Monaco Editor Not Loading

1. **Check API Server**: Ensure the API server is running on the configured URL
2. **Check Console**: Open browser console (F12) to see any JavaScript errors
3. **Check Network**: Verify that the API requests are reaching the server

### Autocomplete Not Working

1. **Verify API Connection**: Check that the API server URL is correct
2. **Check OpenAI API Key**: Ensure `OPENAI_API_KEY` is set in your `.env` file
3. **Check Database Connection**: Autocomplete works better when connected to a database

### Fallback to Regular Editor

If Monaco Editor fails to load, the app will automatically fall back to the regular Streamlit text area. You'll see a warning message.

## Architecture

```
┌─────────────────┐
│  Streamlit App  │
│  (Monaco Editor)│
└────────┬────────┘
         │ HTTP Request
         ▼
┌─────────────────┐
│  FastAPI Server │
│  (api_server.py)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   OpenAI GPT-4  │
│  (Autocomplete) │
└─────────────────┘
```

## Development

### Adding Custom Suggestions

To add custom autocomplete suggestions, modify `webapp/api_server.py`:

```python
@app.post("/api/autocomplete")
async def get_autocomplete(request: AutocompleteRequest):
    # Add your custom logic here
    suggestions = []
    # ... your code ...
    return AutocompleteResponse(suggestions=suggestions)
```

### Customizing Monaco Editor

To customize Monaco Editor appearance or behavior, modify `webapp/components/monaco_editor.py`:

```python
editor = monaco.editor.create(..., {
    # Add your custom options here
    'fontSize': 16,
    'wordWrap': 'on',
    # ...
})
```

## Performance

- **Autocomplete Latency**: Typically 200-500ms depending on API response time
- **Caching**: Suggestions are cached per query context
- **Rate Limiting**: Consider implementing rate limiting for production use

## Security

- **API Key**: Never expose your OpenAI API key in client-side code
- **CORS**: Configure CORS properly for production deployments
- **Authentication**: Consider adding authentication for the API server in production

## Future Enhancements

- [ ] Multi-database schema support
- [ ] Query history integration
- [ ] Custom snippet library
- [ ] Real-time collaboration
- [ ] Query validation before execution
- [ ] Performance profiling integration

## Support

For issues or questions:
1. Check the browser console for errors
2. Verify API server is running
3. Check OpenAI API key configuration
4. Review the logs in the API server terminal

