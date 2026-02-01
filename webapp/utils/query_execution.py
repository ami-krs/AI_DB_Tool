"""Query execution and SQL-related utility functions"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

# Try to import sqlparse, fallback to simple split if not available
try:
    import sqlparse
    SQLPARSE_AVAILABLE = True
except ImportError:
    SQLPARSE_AVAILABLE = False

from .helpers import display_paginated_dataframe

# Import agents (with fallback if not available)
try:
    from ai_db_tool.ai.agents import AgentOrchestrator
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    AgentOrchestrator = None

def split_sql_statements(query: str) -> List[str]:
    """Split SQL query into individual statements, handling semicolons in strings/comments"""
    if not query.strip():
        return []
    
    # Use sqlparse if available for proper statement splitting
    if SQLPARSE_AVAILABLE:
        try:
            parsed = sqlparse.split(query)
            # Filter out empty statements and strip whitespace
            statements = [stmt.strip() for stmt in parsed if stmt.strip()]
            # Remove trailing semicolons that sqlparse might leave
            statements = [stmt.rstrip(';').strip() for stmt in statements if stmt.rstrip(';').strip()]
            return statements
        except Exception as e:
            # Fallback to improved split if sqlparse fails
            pass
    
    # Improved fallback: handle semicolons in quotes and comments
    statements = []
    current = []
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = False
    i = 0
    
    while i < len(query):
        char = query[i]
        next_char = query[i + 1] if i + 1 < len(query) else ''
        
        # Handle block comments
        if char == '/' and next_char == '*' and not in_single_quote and not in_double_quote:
            in_block_comment = True
            current.append(char)
            current.append(next_char)
            i += 2
            continue
        
        if in_block_comment:
            current.append(char)
            if char == '*' and next_char == '/':
                in_block_comment = False
                current.append(next_char)
                i += 2
                continue
            i += 1
            continue
        
        # Handle line comments
        if char == '-' and next_char == '-' and not in_single_quote and not in_double_quote:
            in_line_comment = True
            current.append(char)
            current.append(next_char)
            i += 2
            # Continue until newline
            while i < len(query) and query[i] != '\n':
                current.append(query[i])
                i += 1
            if i < len(query):
                current.append(query[i])  # Add the newline
                in_line_comment = False
            i += 1
            continue
        
        if in_line_comment:
            current.append(char)
            i += 1
            continue
        
        # Handle quotes
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(char)
            i += 1
            continue
        
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(char)
            i += 1
            continue
        
        # Handle semicolon (statement separator)
        if char == ';' and not in_single_quote and not in_double_quote and not in_line_comment and not in_block_comment:
            stmt = ''.join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            i += 1
            continue
        
        current.append(char)
        i += 1
    
    # Add remaining statement (if any)
    if current:
        stmt = ''.join(current).strip()
        if stmt:
            statements.append(stmt)
    
    return statements

def execute_single_statement(statement: str) -> Dict[str, Any]:
    """Execute a single SQL statement and return result info"""
    result = {
        'success': False,
        'statement': statement,
        'type': None,
        'rows_affected': 0,
        'rows_retrieved': 0,
        'dataframe': None,
        'error': None
    }
    
    if not statement.strip():
        return result
    
    statement_upper = statement.strip().upper()
    
    # Determine query type
    is_ddl = any(statement_upper.startswith(cmd) for cmd in [
        'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 
        'GRANT', 'REVOKE', 'COMMENT', 'ANALYZE', 'VACUUM'
    ])
    
    is_dml = any(statement_upper.startswith(cmd) for cmd in ['INSERT', 'UPDATE', 'DELETE'])
    is_select = statement_upper.startswith('SELECT')
    
    try:
        if is_ddl or is_dml:
            # Execute non-query operations
            affected_rows = st.session_state.db_manager.execute_non_query(statement)
            result['success'] = True
            result['type'] = 'DDL' if is_ddl else 'DML'
            result['rows_affected'] = affected_rows if affected_rows >= 0 else 0
            return result
        
        elif is_select:
            # Execute SELECT query
            df = st.session_state.db_manager.execute_query(statement)
            result['success'] = True
            result['type'] = 'SELECT'
            result['rows_retrieved'] = len(df)
            result['dataframe'] = df
            return result
        
        else:
            # Unknown query type - try SELECT first, then non-query
            try:
                df = st.session_state.db_manager.execute_query(statement)
                result['success'] = True
                result['type'] = 'SELECT'
                result['rows_retrieved'] = len(df)
                result['dataframe'] = df
                return result
            except:
                # Fallback to non-query execution
                affected_rows = st.session_state.db_manager.execute_non_query(statement)
                result['success'] = True
                result['type'] = 'DML'
                result['rows_affected'] = affected_rows if affected_rows >= 0 else 0
                return result
    
    except Exception as e:
        result['error'] = str(e)
        return result

def execute_query(query: str, enable_agents: Optional[bool] = None):
    """Execute SQL query and display results (supports multiple statements, SELECT, INSERT, UPDATE, DELETE, DDL)
    
    Args:
        query: SQL query to execute
        enable_agents: Whether to use AI agents for analysis (default: from session state)
    """
    if not query.strip():
        st.warning("Please enter a query")
        return
    
    # Use session state setting if enable_agents not explicitly provided
    if enable_agents is None:
        enable_agents = st.session_state.get('enable_ai_agents', True)
    
    # Initialize agent orchestrator if available and enabled
    orchestrator = None
    if enable_agents and AGENTS_AVAILABLE:
        try:
            from utils.helpers import get_api_key
            api_key = get_api_key("OPENAI_API_KEY") or get_api_key("ANTHROPIC_API_KEY")
            provider = "openai" if get_api_key("OPENAI_API_KEY") else "anthropic"
            if api_key:
                orchestrator = AgentOrchestrator(api_key=api_key, provider=provider)
            else:
                # Silently skip if no API key - agents are optional
                pass
        except Exception as e:
            # Log error but don't show warning to user (agents are optional)
            import traceback
            print(f"DEBUG: Could not initialize AI agents: {e}")
            print(traceback.format_exc())
            orchestrator = None
    
    # Split into multiple statements
    try:
        statements = split_sql_statements(query)
    except Exception as e:
        st.error(f"❌ Failed to parse SQL statements: {e}")
        st.info("💡 Tip: Make sure your SQL statements are properly formatted and separated by semicolons (;)")
        return
    
    if not statements:
        st.warning("No valid SQL statements found. Please check your SQL syntax.")
        st.info("💡 Tip: SQL statements should be separated by semicolons (;)")
        return
    
    # Show info for multiple statements
    if len(statements) > 1:
        st.info(f"📋 Detected {len(statements)} SQL statements. They will be executed sequentially.")
    
    # If single statement, use original behavior for backward compatibility
    if len(statements) == 1:
        single_statement = statements[0]
        
            # Pre-execution: Query Analyzer Agent
        if orchestrator:
            try:
                from ui.agent_display import display_agent_response
                schema_info = st.session_state.get('schema_info', {})
                db_type = st.session_state.get('db_type', 'unknown')
                with st.spinner("🔍 Analyzing query with AI..."):
                    query_analysis = orchestrator.analyze_query(single_statement, schema_info, db_type)
                    if query_analysis and query_analysis.confidence > 0.5:
                        display_agent_response(query_analysis, expanded=False)
            except Exception as e:
                st.debug(f"Query analysis failed: {e}")
        
        # Execute query
        start_time = time.time()
        result = execute_single_statement(single_statement)
        execution_time = time.time() - start_time
        
        if not result['success']:
            st.error(f"❌ Query execution failed: {result['error']}")
            st.code(single_statement, language='sql')
            
            # Debug Agent: Analyze the error
            if orchestrator:
                try:
                    from ui.agent_display import display_agent_response
                    schema_info = st.session_state.get('schema_info', {})
                    db_type = st.session_state.get('db_type', 'unknown')
                    with st.spinner("🐛 Debugging error with AI..."):
                        debug_response = orchestrator.debug_error(
                            single_statement, 
                            result.get('error', 'Unknown error'),
                            str(result.get('error', '')),
                            schema_info,
                            db_type
                        )
                        if debug_response:
                            display_agent_response(debug_response, expanded=True)
                except Exception as e:
                    st.debug(f"Debug analysis failed: {e}")
            
            st.info("💡 Tip: Check your SQL syntax, table/column names, and ensure you're connected to the database.")
            return
        
        # Handle single statement results (original behavior)
        if result['type'] == 'SELECT':
            # Compact Results header with download icon in same line
            result_col1, result_col2 = st.columns([10, 1])
            with result_col1:
                st.markdown("**📊 Results**", unsafe_allow_html=True)
            with result_col2:
                csv = result['dataframe'].to_csv(index=False)
                st.download_button(
                    "📥",
                    csv,
                    "results.csv",
                    "text/csv",
                    help=f"Download CSV - {len(result['dataframe']):,} rows",
                    use_container_width=True
                )
            
            st.session_state.current_page = 1
            display_paginated_dataframe(result['dataframe'], unique_suffix=f"query_result_{len(st.session_state.query_history)}")
            st.session_state.last_result_df = result['dataframe']
            st.session_state.last_result = result['dataframe']
            st.success(f"✅ Query executed successfully! Retrieved {result['rows_retrieved']:,} rows.")
            
            # Post-execution: Results Analyzer and Review Agent
            if orchestrator:
                try:
                    from ui.agent_display import display_agent_response
                    with st.spinner("📊 Analyzing results with AI..."):
                        # Results Analyzer
                        results_analysis = orchestrator.analyze_results(
                            single_statement,
                            result,
                            error=None,
                            rows_retrieved=result['rows_retrieved'],
                            execution_time=execution_time,
                            dataframe=result['dataframe']
                        )
                        
                        # Review Agent
                        review_response = orchestrator.review_results(
                            single_statement,
                            result,
                            rows_retrieved=result['rows_retrieved'],
                            execution_time=execution_time,
                            dataframe=result['dataframe']
                        )
                        
                        # Display agent responses
                        if results_analysis:
                            display_agent_response(results_analysis, expanded=False)
                        if review_response:
                            display_agent_response(review_response, expanded=False)
                except Exception as e:
                    st.debug(f"Results analysis failed: {e}")
        
        elif result['type'] == 'DDL':
            st.success(f"✅ Database object operation completed successfully!")
            if any(single_statement.strip().upper().startswith(cmd) for cmd in ['CREATE', 'DROP', 'ALTER']):
                st.info("💡 Refresh the page to see updated schema")
        
        else:  # DML
            if result['rows_affected'] >= 0:
                st.success(f"✅ Query executed successfully! {result['rows_affected']} row(s) affected.")
            else:
                st.success(f"✅ Query executed successfully!")
        
        return
    
    # Multiple statements - execute each and show summary
    st.subheader(f"📋 Executing {len(statements)} Statement(s)")
    
    # Pre-execution: Query Analyzer Agent for first statement (or all if enabled)
    if orchestrator and len(statements) > 0:
        try:
            from ui.agent_display import display_agent_response
            schema_info = st.session_state.get('schema_info', {})
            db_type = st.session_state.get('db_type', 'unknown')
            # Analyze the first statement as a preview
            with st.spinner("🔍 Analyzing queries with AI..."):
                query_analysis = orchestrator.analyze_query(statements[0], schema_info, db_type)
                if query_analysis and query_analysis.confidence > 0.5:
                    display_agent_response(query_analysis, expanded=False)
        except Exception as e:
            st.debug(f"Query analysis failed: {e}")
    
    results = []
    success_count = 0
    error_count = 0
    
    for idx, statement in enumerate(statements, 1):
        with st.expander(f"Statement {idx}/{len(statements)}", expanded=(idx == 1)):
            st.code(statement, language='sql')
            
            result = execute_single_statement(statement)
            results.append(result)
            
            if result['success']:
                success_count += 1
                
                if result['type'] == 'SELECT':
                    st.success(f"✅ Statement {idx} executed: Retrieved {result['rows_retrieved']:,} rows")
                    if result['dataframe'] is not None and len(result['dataframe']) > 0:
                        st.session_state.current_page = 1
                        display_paginated_dataframe(result['dataframe'], unique_suffix=f"multi_stmt_{idx}_{len(statements)}")
                        
                        # Store last result for visualization
                        st.session_state.last_result_df = result['dataframe']
                        st.session_state.last_result = result['dataframe']
                
                elif result['type'] == 'DDL':
                    st.success(f"✅ Statement {idx} executed: DDL operation completed")
                
                else:  # DML
                    st.success(f"✅ Statement {idx} executed: {result['rows_affected']} row(s) affected")
            else:
                error_count += 1
                st.error(f"❌ Statement {idx} failed: {result['error']}")
                
                # Debug Agent: Analyze the error for multi-statement queries
                if orchestrator:
                    try:
                        from ui.agent_display import display_agent_response
                        schema_info = st.session_state.get('schema_info', {})
                        db_type = st.session_state.get('db_type', 'unknown')
                        
                        # Extract error information
                        error_obj = result.get('error', 'Unknown error')
                        error_message = str(error_obj) if error_obj else 'Unknown error'
                        
                        # Extract error type
                        error_type = type(error_obj).__name__ if error_obj and hasattr(error_obj, '__class__') else 'Error'
                        
                        with st.spinner("🐛 Debugging error with AI..."):
                            debug_response = orchestrator.debug_error(
                                statement,
                                error_type,
                                error_message,
                                schema_info,
                                db_type
                            )
                            if debug_response:
                                display_agent_response(debug_response, expanded=True)
                    except Exception as e:
                        # Show error in debug mode, but don't break the UI
                        import traceback
                        print(f"DEBUG: Debug Agent failed: {e}")
                        print(traceback.format_exc())
                        st.debug(f"Debug analysis failed: {e}")
                
                st.info("💡 This statement failed, but other statements will continue executing.")
    
    # Summary
    st.markdown("---")
    st.subheader("📊 Execution Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Statements", len(statements))
    with col2:
        st.metric("✅ Successful", success_count, delta=None)
    with col3:
        st.metric("❌ Failed", error_count, delta=None, delta_color="inverse")
    
    if success_count == len(statements):
        st.success(f"🎉 All {len(statements)} statement(s) executed successfully!")
    elif success_count > 0:
        st.warning(f"⚠️ {success_count} statement(s) succeeded, {error_count} statement(s) failed")
    else:
        st.error(f"❌ All statements failed to execute")
    
    # Show last SELECT result if available
    last_select_result = None
    for result in reversed(results):
        if result['success'] and result['type'] == 'SELECT' and result['dataframe'] is not None:
            last_select_result = result['dataframe']
            break
    
    if last_select_result is not None:
        st.markdown("---")
        # Compact Results header with download icon in same line
        result_col1, result_col2 = st.columns([10, 1])
        with result_col1:
            st.markdown("**📊 Last Query Results**", unsafe_allow_html=True)
        with result_col2:
            csv = last_select_result.to_csv(index=False)
            st.download_button(
                "📥",
                csv,
                "results.csv",
                "text/csv",
                help=f"Download CSV - {len(last_select_result):,} rows",
                use_container_width=True
            )
        
        st.session_state.current_page = 1
        display_paginated_dataframe(last_select_result, unique_suffix=f"last_result_{len(st.session_state.query_history)}")

def execute_generated_query(query: str):
    """Execute AI-generated query"""
    execute_query(query)

def show_table_details():
    """Show detailed table information"""
    if not st.session_state.connected:
        st.warning("Please connect to a database first")
        return
    
    tables = st.session_state.db_manager.get_tables()
    if not tables:
        st.info("No tables found in the database")
        return
    
    selected_table = st.selectbox("Select a table to view details", tables)
    
    if selected_table:
        schema = st.session_state.db_manager.get_table_schema(selected_table)
        
        st.markdown(f"### 📊 Schema: `{selected_table}`")
        
        # Display columns
        df_cols = pd.DataFrame(schema['columns'])
        st.dataframe(df_cols, use_container_width=True)
        
        # Show primary keys
        if schema.get('primary_keys'):
            st.markdown(f"**Primary Keys:** {', '.join(schema['primary_keys'])}")
        
        # Show foreign keys
        if schema.get('foreign_keys'):
            st.markdown("**Foreign Keys:**")
            for fk in schema['foreign_keys']:
                st.markdown(f"- {fk['constrained_columns']} → {fk['referred_table']}.{fk['referred_columns']}")

def show_common_queries():
    """Show common query templates"""
    if not st.session_state.connected:
        st.warning("Please connect to a database first")
        return
    
    db_type = st.session_state.get('db_type', 'sqlite')
    tables = st.session_state.db_manager.get_tables()
    
    if not tables:
        st.info("No tables found")
        return
    
    selected_table = st.selectbox("Select a table", tables)
    
    # Get schema to provide accurate examples
    try:
        schema = st.session_state.db_manager.get_table_schema(selected_table)
        columns = [col['name'] for col in schema.get('columns', [])[:5]]  # First 5 columns
        columns_str = ', '.join(columns)
    except:
        columns_str = "column1, column2, column3"
    
    common_queries = [
        ("📊 SELECT - View All Rows", f"SELECT * FROM {selected_table} LIMIT 100;"),
        ("📊 SELECT - Count Rows", f"SELECT COUNT(*) FROM {selected_table};"),
        ("📊 SELECT - Top 10", f"SELECT * FROM {selected_table} LIMIT 10;"),
        ("➕ INSERT - Add New Row", f"INSERT INTO {selected_table} ({columns_str}) VALUES ('value1', 'value2', 'value3');"),
        ("✏️ UPDATE - Modify Data", f"UPDATE {selected_table} SET {columns[0] if columns else 'column1'} = 'new_value' WHERE condition;"),
        ("🗑️ DELETE - Remove Rows", f"DELETE FROM {selected_table} WHERE condition;"),
    ]
    
    # Add DDL examples
    st.markdown("---")
    st.markdown("**📊 Common Query Patterns:**")
    for name, query in common_queries:
        with st.expander(f"📝 {name}"):
            st.code(query, language='sql')
            if st.button(f"📋 Use This Query", key=f"common_{name}_{selected_table}"):
                st.session_state.sql_editor = query
                st.rerun()
    
    st.markdown("---")
    st.markdown("**🏗️ Database Management (DDL):**")
    
    # Get column details for CREATE TABLE example
    try:
        if schema and schema.get('columns'):
            col_defs = []
            for col in schema['columns'][:3]:  # First 3 columns
                col_name = col['name']
                col_type = col['type']
                if 'INTEGER' in str(col_type).upper():
                    col_type = 'INTEGER'
                elif 'TEXT' in str(col_type).upper() or 'VARCHAR' in str(col_type).upper():
                    col_type = 'TEXT'
                else:
                    col_type = 'TEXT'
                col_defs.append(f"{col_name} {col_type}")
            sample_cols = ', '.join(col_defs[:2])  # First 2 columns for example
        else:
            sample_cols = "id INTEGER, name TEXT"
    except:
        sample_cols = "id INTEGER PRIMARY KEY, name TEXT"
    
    ddl_queries = [
        ("🏗️ CREATE - New Table", f"CREATE TABLE new_table ({sample_cols});"),
        ("🏗️ CREATE - Index", f"CREATE INDEX idx_name ON {selected_table} (column_name);"),
        ("🏗️ CREATE - View", f"CREATE VIEW my_view AS SELECT * FROM {selected_table} WHERE condition;"),
        ("🗑️ DROP - Delete Table", f"DROP TABLE table_name;"),
        ("🔧 ALTER - Add Column", f"ALTER TABLE {selected_table} ADD COLUMN new_column TEXT;"),
    ]
    
    for name, query in ddl_queries:
        with st.expander(f"🏗️ {name}"):
            st.code(query, language='sql')
            if st.button(f"📋 Use This Query", key=f"ddl_{name}"):
                st.session_state.sql_editor = query
                st.rerun()

def generate_sql_query():
    """Generate SQL query using AI"""
    st.info("Enter your question in the AI Chatbot tab to generate SQL")

def optimize_query(query: str):
    """Optimize query using AI"""
    if not query.strip() or not st.session_state.query_builder:
        st.warning("Please enter a query first")
        return
    
    try:
        with st.spinner("🤖 Optimizing query..."):
            optimized = st.session_state.query_builder.optimize_query(query)
        st.subheader("Optimized Query")
        st.code(optimized, language='sql')
    except Exception as e:
        st.error(f"Optimization failed: {e}")

def debug_query(query: str):
    """Debug query using AI"""
    if not query.strip():
        st.warning("Please enter a query first")
        return
    
    if not st.session_state.connected:
        st.error("Please connect to a database first")
        return
    
    # Try to execute the query first to get the error
    error_message = None
    try:
        # Try to execute the query
        df = st.session_state.db_manager.execute_query(query)
        # If successful, no debug needed
        st.success("✅ Query is valid and executes successfully!")
        st.info(f"Retrieved {len(df)} rows. No errors to debug.")
        return
    except Exception as e:
        # Got an error - now we can debug it
        error_message = str(e)
        st.error(f"❌ Query Error Detected:\n{error_message}")
    
    # Use AI to debug the error
    if error_message and st.session_state.query_builder:
        with st.spinner("🤖 AI is analyzing the error..."):
            try:
                # Pass schema context for better debugging
                schema_info = st.session_state.get('schema_info', {})
                if schema_info:
                    # Create a context string for AI
                    schema_context = f"Database type: {st.session_state.db_type}\n\nTables:\n"
                    for table in schema_info.get('tables', []):
                        table_name = table.get('table_name', 'unknown')
                        columns = ', '.join([col['name'] for col in table.get('columns', [])])
                        schema_context += f"- {table_name}: {columns}\n"
                    
                    debugged_query = st.session_state.query_builder.debug_query(query, error_message, schema_context)
                else:
                    debugged_query = st.session_state.query_builder.debug_query(query, error_message)
                
                st.markdown("### 🔧 AI Debug Suggestions:")
                
                # Split the response into explanation and fixed query
                if "```sql" in debugged_query:
                    parts = debugged_query.split("```sql")
                    explanation = parts[0].strip()
                    sql_part = parts[1].split("```")[0].strip() if len(parts) > 1 else ""
                    
                    if explanation:
                        st.markdown(explanation)
                    
                    if sql_part:
                        st.markdown("**Suggested Fixed Query:**")
                        st.code(sql_part, language='sql')
                        
                        # Use a form to handle the button properly
                        with st.form(key="use_fixed_query_form"):
                            if st.form_submit_button("📋 Use Fixed Query"):
                                st.session_state.fixed_query = sql_part
                                st.rerun()
                else:
                    st.info(debugged_query)
                    
            except Exception as e:
                st.error(f"Debug failed: {e}")

def save_query_to_history(query: str):
    """Save query to history"""
    if query.strip():
        st.session_state.query_history.append(query)
        st.success("✅ Query saved to history!")
