"""
Monaco Editor Component for Streamlit
Integrates Monaco Editor (VS Code editor) with AI autocomplete
"""

import streamlit.components.v1 as components
import json
from typing import Optional, Dict, Any, List

# Monaco Editor HTML template with AI autocomplete
MONACO_EDITOR_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs/loader.js"></script>
    <style>
        #monaco-container {
            width: 100%;
            height: {height}px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div id="monaco-container"></div>
    
    <script>
        require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
        
        let editor = null;
        let autocompleteProvider = null;
        const API_URL = '{api_url}';
        
        require(['vs/editor/editor.main'], function() {
            // Create editor
            editor = monaco.editor.create(document.getElementById('monaco-container'), {{
                value: `{initial_value}`,
                language: 'sql',
                theme: '{theme}',
                automaticLayout: true,
                minimap: {{ enabled: false }},
                fontSize: 14,
                lineNumbers: 'on',
                roundedSelection: false,
                scrollBeyondLastLine: false,
                readOnly: false,
                cursorStyle: 'line',
                wordWrap: 'on',
                suggestOnTriggerCharacters: true,
                quickSuggestions: true,
                suggestSelection: 'first',
                tabCompletion: 'on',
                wordBasedSuggestions: 'matchingDocuments',
                suggest: {{
                    showKeywords: true,
                    showSnippets: true,
                    showClasses: true,
                    showFunctions: true,
                    showVariables: true,
                    showFields: true,
                    showMethods: true,
                    showProperties: true,
                    showValues: true,
                    showConstants: true,
                    showEnums: true,
                    showStructs: true,
                    showInterfaces: true,
                    showModules: true,
                    showOperators: true,
                    showEvents: true,
                    showColors: true,
                    showFiles: true,
                    showReferences: true,
                    showFolders: true,
                    showTypeParameters: true,
                    showIssues: true,
                    showUsers: true,
                    showText: true
                }}
            }});
            
            // Register SQL language
            monaco.languages.register({{ id: 'sql' }});
            
            // Register completion item provider with AI autocomplete
            monaco.languages.registerCompletionItemProvider('sql', {{
                provideCompletionItems: async function(model, position) {{
                    const textUntilPosition = model.getValueInRange({{
                        startLineNumber: 1,
                        startColumn: 1,
                        endLineNumber: position.lineNumber,
                        endColumn: position.column
                    }});
                    
                    const textAfterPosition = model.getValueInRange({{
                        startLineNumber: position.lineNumber,
                        startColumn: position.column,
                        endLineNumber: model.getLineCount(),
                        endColumn: model.getLineMaxColumn(model.getLineCount())
                    }});
                    
                    const fullText = model.getValue();
                    const cursorPosition = model.getOffsetAt(position);
                    
                    // Call AI autocomplete API
                    try {{
                        const response = await fetch(API_URL + '/api/autocomplete', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify({{
                                query: fullText,
                                cursor_position: cursorPosition,
                                database_type: '{database_type}',
                                schema_info: {schema_info},
                                tables: {tables}
                            }})
                        }});
                        
                        const data = await response.json();
                        
                        // Convert suggestions to Monaco completion items
                        const suggestions = data.suggestions || [];
                        const items = suggestions.map(suggestion => ({{
                            label: suggestion.label || suggestion.insertText,
                            kind: monaco.languages.CompletionItemKind[suggestion.kind?.toUpperCase()] || 
                                  monaco.languages.CompletionItemKind.Text,
                            insertText: suggestion.insertText || suggestion.label,
                            documentation: suggestion.documentation || '',
                            detail: suggestion.detail || '',
                            range: {{
                                startLineNumber: position.lineNumber,
                                startColumn: position.column,
                                endLineNumber: position.lineNumber,
                                endColumn: position.column
                            }}
                        }}));
                        
                        // Add default SQL keywords if no AI suggestions
                        if (items.length === 0) {{
                            const sqlKeywords = [
                                'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN',
                                'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT', 'OFFSET',
                                'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE',
                                'CREATE', 'TABLE', 'INDEX', 'VIEW', 'ALTER', 'DROP',
                                'AND', 'OR', 'NOT', 'IN', 'LIKE', 'BETWEEN', 'IS NULL', 'IS NOT NULL',
                                'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'DISTINCT', 'AS'
                            ];
                            
                            sqlKeywords.forEach(keyword => {{
                                items.push({{
                                    label: keyword,
                                    kind: monaco.languages.CompletionItemKind.Keyword,
                                    insertText: keyword,
                                    documentation: 'SQL keyword: ' + keyword
                                }});
                            }});
                        }}
                        
                        return {{ suggestions: items }};
                    }} catch (error) {{
                        console.error('Autocomplete error:', error);
                        return {{ suggestions: [] }};
                    }}
                }},
                triggerCharacters: ['.', ' ', '(', ',', '=']
            }});
            
            // Listen for changes and send to Streamlit
            editor.onDidChangeModelContent(function() {{
                const value = editor.getValue();
                window.parent.postMessage({{
                    type: 'monaco-editor-change',
                    value: value
                }}, '*');
            }});
            
            // Listen for cursor position changes
            editor.onDidChangeCursorPosition(function(e) {{
                const value = editor.getValue();
                const position = editor.getPosition();
                window.parent.postMessage({{
                    type: 'monaco-editor-cursor',
                    value: value,
                    line: position.lineNumber,
                    column: position.column
                }}, '*');
            }});
            
            // Expose editor to window for external access
            window.monacoEditor = editor;
        }});
        
        // Listen for messages from Streamlit
        window.addEventListener('message', function(event) {{
            if (event.data.type === 'set-value' && editor) {{
                editor.setValue(event.data.value);
            }}
            if (event.data.type === 'set-theme' && editor) {{
                monaco.editor.setTheme(event.data.theme);
            }}
        }});
    </script>
</body>
</html>
"""


def monaco_editor(
    value: str = "",
    height: int = 300,
    language: str = "sql",
    theme: str = "vs",
    api_url: str = "http://localhost:8000",
    database_type: Optional[str] = None,
    schema_info: Optional[Dict[str, Any]] = None,
    tables: Optional[List[str]] = None,
    key: Optional[str] = None
) -> str:
    """
    Monaco Editor component with AI autocomplete
    
    Parameters:
    -----------
    value : str
        Initial SQL query value
    height : int
        Editor height in pixels
    language : str
        Programming language (default: 'sql')
    theme : str
        Editor theme ('vs', 'vs-dark', 'hc-black')
    api_url : str
        Backend API URL for autocomplete
    database_type : str
        Database type (postgresql, mysql, sqlite, etc.)
    schema_info : dict
        Database schema information
    tables : list
        List of available table names
    key : str
        Unique key for the component
    
    Returns:
    --------
    str
        Current editor value (updated via JavaScript)
    """
    # Prepare data for JavaScript
    schema_info_json = json.dumps(schema_info) if schema_info else "null"
    tables_json = json.dumps(tables) if tables else "[]"
    
    # Escape value for JavaScript
    escaped_value = value.replace("`", "\\`").replace("$", "\\$")
    
    # Format HTML
    html = MONACO_EDITOR_HTML.format(
        height=height,
        initial_value=escaped_value,
        theme=theme,
        api_url=api_url,
        database_type=database_type or "",
        schema_info=schema_info_json,
        tables=tables_json
    )
    
    # Render component
    component_value = components.html(
        html,
        height=height + 50,
        key=key
    )
    
    return component_value or value

