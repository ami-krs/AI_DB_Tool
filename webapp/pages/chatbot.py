"""Page modules for different sections of the application"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime

from utils.query_execution import (
    execute_query, execute_generated_query, show_table_details, 
    show_common_queries, generate_sql_query, optimize_query, 
    debug_query, save_query_to_history
)
from ui.components import render_sql_editor
from shared import CODEMIRROR_AVAILABLE, MONACO_EDITOR_AVAILABLE, codemirror_editor, monaco_editor




def chatbot_compact():
    """Compact chatbot for three column layout"""
    st.markdown("### 💬 AI Assistant")
    
    # Example questions (only show if no chat history)
    if not st.session_state.chat_history and st.session_state.chatbot:
        st.markdown("**💡 Quick Start:**")
        example_questions = [
            ("Show me all tables", "Show me the list of all tables in the database"),
            ("Tables >10 records", "List tables that have more than 10 records"),
            ("Table columns", "What are the column names and data types for all tables?")
        ]
        
        # Use smaller buttons in a row
        cols = st.columns(3)
        for idx, (display_text, full_question) in enumerate(example_questions):
            with cols[idx]:
                if st.button(f"💬 {display_text}", key=f"compact_example_{idx}", use_container_width=True):
                    # Process the question
                    st.session_state.chat_history.append({'role': 'user', 'content': full_question})
                    with st.spinner("🤔 Thinking..."):
                        response = st.session_state.chatbot.chat(full_question, include_sql=True)
                    
                    if 'error' not in response:
                        sql_query = response.get('sql_query')
                        auto_executed = False
                        
                        # Auto-execute SELECT queries for example questions too
                        if sql_query:
                            sql_upper = sql_query.strip().upper()
                            is_select = sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')
                            is_not_ddl_dml = not any(sql_upper.startswith(cmd) for cmd in [
                                'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'INSERT', 'UPDATE', 'DELETE',
                                'GRANT', 'REVOKE', 'COMMENT', 'ANALYZE', 'VACUUM'
                            ])
                            
                            if is_select and is_not_ddl_dml:
                                try:
                                    execute_query(sql_query, enable_agents=False)
                                    auto_executed = True
                                except Exception as exec_error:
                                    print(f"DEBUG: Auto-execution failed: {exec_error}")
                        
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response['response'],
                            'sql_query': sql_query,
                            'timestamp': response['timestamp'],
                            'auto_executed': auto_executed
                        })
                    else:
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response.get('response', response.get('error', 'Error occurred')),
                            'timestamp': response.get('timestamp', datetime.now().isoformat())
                        })
                    st.rerun()
        st.markdown("---")
    
    # Add marker before chat messages for compact layout
    st.markdown('<div id="chat-container-start-compact"></div>', unsafe_allow_html=True)
    
    # Display chat history
    if st.session_state.chat_history:
        recent_messages = st.session_state.chat_history[-10:]  # Show last 10 messages (increased from 5)
        for idx, msg in enumerate(recent_messages):
            # Use a unique key based on the original index in the full chat history
            original_idx = len(st.session_state.chat_history) - 10 + idx
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                # Show explanation in collapsed expander by default
                with st.expander("💡 View Explanation", expanded=False, key=f"compact_explanation_{original_idx}"):
                    st.chat_message("assistant").write(msg['content'])
                
                # Show SQL query in expanded form by default
                if 'sql_query' in msg and msg['sql_query']:
                    with st.expander("📝 Generated SQL", expanded=True, key=f"compact_sql_{original_idx}"):
                        st.code(msg['sql_query'], language='sql')
    else:
        if not st.session_state.chatbot:
            st.info("💡 AI chatbot requires an API key. Set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable.")
        else:
            st.info("Ask questions about your database")
    
    # Add marker after chat messages and JavaScript to wrap them for compact layout
    st.markdown("""
    <div id="chat-container-end-compact"></div>
    <script>
        (function() {
            function wrapCompactChatMessages() {
                const startMarker = document.getElementById('chat-container-start-compact');
                const endMarker = document.getElementById('chat-container-end-compact');
                if (!startMarker || !endMarker) return;
                
                // Check if wrapper already exists
                if (document.getElementById('chat-messages-scrollable-wrapper-compact')) return;
                
                // Find parent container
                let parent = startMarker.parentElement;
                if (!parent) return;
                
                // Create wrapper div
                const wrapper = document.createElement('div');
                wrapper.id = 'chat-messages-scrollable-wrapper-compact';
                wrapper.style.cssText = `
                    max-height: 50vh;
                    overflow-y: auto;
                    overflow-x: hidden;
                    padding: 0.5rem;
                    margin-bottom: 0.5rem;
                    border: 1px solid rgba(250, 250, 250, 0.2);
                    border-radius: 0.5rem;
                    background-color: rgba(0, 0, 0, 0.02);
                    scroll-behavior: smooth;
                `;
                
                // Collect all nodes between markers
                let node = startMarker.nextSibling;
                const nodesToMove = [];
                while (node && node !== endMarker) {
                    nodesToMove.push(node);
                    node = node.nextSibling;
                }
                
                // Move nodes into wrapper
                nodesToMove.forEach(n => wrapper.appendChild(n));
                
                // Insert wrapper after start marker
                startMarker.parentNode.insertBefore(wrapper, startMarker.nextSibling);
                
                // Auto-scroll to bottom
                wrapper.scrollTop = wrapper.scrollHeight;
            }
            
            // Run immediately and after delays
            wrapCompactChatMessages();
            setTimeout(wrapCompactChatMessages, 100);
            setTimeout(wrapCompactChatMessages, 500);
            
            // Also observe for changes
            const observer = new MutationObserver(function() {
                wrapCompactChatMessages();
                const wrapper = document.getElementById('chat-messages-scrollable-wrapper-compact');
                if (wrapper) {
                    wrapper.scrollTop = wrapper.scrollHeight;
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        })();
    </script>
    """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Ask about your database...")
    
    if user_input:
        # Check if chatbot is available when user actually tries to use it
        print(f"DEBUG: User input received (chatbot_compact): {user_input}")
        print(f"DEBUG: Chatbot available (chatbot_compact): {st.session_state.chatbot is not None}")
        if not st.session_state.chatbot:
            print(f"DEBUG: Chatbot is None (chatbot_compact), showing error message")
            st.error("❌ AI Chatbot is not available. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable to enable AI features.")
        else:
            # Add user message to history
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            # Get AI response
            try:
                print(f"DEBUG: Calling chatbot.chat() (chatbot_compact) with query: {user_input}")
                with st.spinner("🤔 Thinking..."):
                    response = st.session_state.chatbot.chat(user_input, include_sql=True)
                print(f"DEBUG: Chatbot response received (chatbot_compact): {type(response)}, has error: {'error' in response if isinstance(response, dict) else 'N/A'}")
                print(f"DEBUG: Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                if 'error' not in response:
                    # Add assistant response to history
                    try:
                        response_content = response.get('response', response.get('content', str(response)))
                        sql_query = response.get('sql_query', response.get('sql', None))
                        timestamp = response.get('timestamp', datetime.now().isoformat())
                        print(f"DEBUG: Adding response to chat history - content length: {len(response_content) if response_content else 0}, has sql: {bool(sql_query)}")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response_content,
                            'sql_query': sql_query,
                            'timestamp': timestamp
                        })
                        st.rerun()
                    except Exception as process_error:
                        print(f"DEBUG: Error processing response: {process_error}")
                        import traceback
                        traceback.print_exc()
                        st.error(f"❌ Error processing chatbot response: {str(process_error)}")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': f"Error processing response: {str(process_error)}",
                            'timestamp': datetime.now().isoformat()
                        })
                        st.rerun()
                else:
                    error_msg = response.get('error', 'Unknown error occurred')
                    print(f"DEBUG: Response contains error: {error_msg}")
                    st.error(f"Error: {error_msg}")
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': f"Error: {error_msg}",
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                error_msg = f"❌ Error processing query: {str(e)}"
                st.error(error_msg)
                print(f"DEBUG: Chatbot error: {e}")
                import traceback
                traceback.print_exc()
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
                st.rerun()




def chatbot_tab():
    """AI Chatbot interface"""
    print(f"DEBUG: chatbot_tab() called - chat_history length: {len(st.session_state.chat_history) if st.session_state.chat_history else 0}")
    
    # Check for agent SQL FIRST, before any other rendering
    # This ensures we catch it immediately after button click
    agent_sql = st.session_state.get("agent_sql_to_run")
    agent_execution_result = st.session_state.get("agent_sql_execution_result")
    print(f"DEBUG: chatbot_tab START - agent_sql exists: {agent_sql is not None}, value: {agent_sql[:100] if agent_sql else 'None'}...")
    
    # Also check for any agent SQL button clicks that might have happened
    # This is a fallback in case the button click handler didn't run
    if not agent_sql:
        agent_button_keys = [k for k in st.session_state.keys() if k.endswith("_run") and "agent_sql" in k]
        for button_key in agent_button_keys:
            # Check if this button was clicked (Streamlit buttons return True on click)
            # But we can't check button state directly, so we check if editor_key exists
            editor_key = button_key.replace("_run", "_editor")
            if editor_key in st.session_state:
                # Button might have been clicked but handler didn't run
                # Try to get SQL from editor
                potential_sql = st.session_state.get(editor_key)
                if potential_sql and potential_sql.strip():
                    print(f"DEBUG: Found potential agent SQL from editor: {editor_key}")
                    st.session_state["agent_sql_to_run"] = potential_sql
                    agent_sql = potential_sql
                    break
    
    st.header("💬 AI SQL Assistant")
    st.markdown("Ask questions in natural language and get SQL queries generated automatically")

    # Debug section for agent SQL execution (visible on page)
    with st.expander("🔍 Agent SQL Execution Debug", expanded=False):
        agent_sql_debug = st.session_state.get("agent_sql_to_run")
        agent_result_debug = st.session_state.get("agent_sql_execution_result")
        st.write(f"**agent_sql_to_run exists:** {agent_sql_debug is not None}")
        if agent_sql_debug:
            st.write(f"**agent_sql value:** {agent_sql_debug[:200]}...")
        st.write(f"**agent_sql_execution_result exists:** {agent_result_debug is not None}")
        if agent_result_debug:
            st.write(f"**Result status:** {agent_result_debug.get('status', 'unknown')}")
        st.write(f"**agent_sql_source:** {st.session_state.get('agent_sql_source', 'None')}")
        # Show all agent-related keys
        agent_keys = [k for k in st.session_state.keys() if 'agent' in k.lower()]
        st.write(f"**All agent-related keys:** {agent_keys}")

    # If an agent (e.g., Debug Agent) requested to run suggested SQL, execute it here
    # Check this FIRST before rendering anything else, so results appear at the top
    # Check if we need to execute agent SQL (persist across reruns)
    
    print(f"DEBUG: chatbot_tab - agent_sql exists: {agent_sql is not None}, agent_execution_result exists: {agent_execution_result is not None}")
    if agent_sql:
        print(f"DEBUG: agent_sql value: {agent_sql[:100] if agent_sql else 'None'}...")
    
    if agent_sql:
        # Store execution info before clearing
        agent_source = st.session_state.get("agent_sql_source", "AI Agent")
        agent_timestamp = st.session_state.get("agent_sql_timestamp", None)
        
        print(f"DEBUG: About to execute agent SQL - source: {agent_source}, execution_result: {agent_execution_result}")
        
        # Execute SQL and store result in session state
        if agent_execution_result is None:
            # First time execution - run the SQL
            print(f"DEBUG: First time execution - displaying info and executing SQL")
            
            # Show visible execution status
            execution_status = st.empty()
            execution_status.info(f"▶ **Executing SQL suggested by {agent_source}...**")
            st.code(agent_sql, language='sql')
            
            try:
                print(f"DEBUG: About to call execute_query with SQL: {agent_sql[:100]}...")
                execution_status.info(f"▶ **Executing SQL...** (This may take a moment)")
                
                # Run without agents to avoid recursive analysis
                # execute_query will display results/success messages automatically
                execute_query(agent_sql, enable_agents=False, unique_suffix="agent_suggested")
                print(f"DEBUG: execute_query returned successfully")
                
                execution_status.success("✅ **SQL execution completed!**")
                
                # Store execution result
                st.session_state["agent_sql_execution_result"] = {
                    "status": "success",
                    "sql": agent_sql,
                    "source": agent_source,
                    "timestamp": agent_timestamp
                }
                
                # For UPDATE/DELETE/INSERT, add extra confirmation message
                sql_upper = agent_sql.strip().upper()
                if any(sql_upper.startswith(cmd) for cmd in ['UPDATE', 'DELETE', 'INSERT']):
                    st.info("💡 **Tip:** Run a SELECT query to verify the changes were applied correctly.")
                
                # After DDL operations (especially CREATE SCHEMA), refresh schema info
                if any(sql_upper.startswith(cmd) for cmd in ['CREATE SCHEMA', 'CREATE TABLE', 'DROP SCHEMA', 'DROP TABLE', 'ALTER']):
                    try:
                        # Refresh schema info to reflect new schema/table
                        if st.session_state.connected and st.session_state.db_manager:
                            tables = st.session_state.db_manager.get_tables()
                            schema_info = st.session_state.db_manager.get_database_info()
                            if schema_info:
                                schema_info['tables'] = tables or []
                                schema_info['total_tables'] = len(tables) if tables else 0
                                st.session_state.schema_info = schema_info
                            else:
                                st.session_state.schema_info = {
                                    'tables': tables or [],
                                    'db_type': st.session_state.get('db_type', 'unknown'),
                                    'total_tables': len(tables) if tables else 0,
                                    'database_name': st.session_state.db_manager.config.database if st.session_state.db_manager.config else 'unknown'
                                }
                            st.success("🔄 Schema information refreshed!")
                            
                            # Also refresh chatbot schema context if available
                            if st.session_state.chatbot:
                                try:
                                    st.session_state.chatbot.set_schema_context(st.session_state.schema_info)
                                except Exception as e:
                                    st.debug(f"Could not update chatbot schema context: {e}")
                    except Exception as e:
                        st.warning(f"⚠️ Schema created but could not refresh schema info: {e}")
                
                # Clear the flag after successful execution (but keep result for display)
                print(f"DEBUG: Clearing agent_sql_to_run flag, keeping execution result")
                st.session_state.pop("agent_sql_to_run", None)
                st.session_state.pop("agent_sql_source", None)
                st.session_state.pop("agent_sql_timestamp", None)
                
                # Don't rerun here - let the messages display
                
            except Exception as e:
                error_msg = f"❌ Failed to execute suggested SQL: {str(e)}"
                execution_status.error(f"❌ **Execution failed!** {error_msg}")
                st.error(error_msg)
                print(f"DEBUG: Agent SQL execution error: {e}")
                import traceback
                error_trace = traceback.format_exc()
                print(error_trace)
                st.exception(e)
                
                # Store error result
                print(f"DEBUG: Storing error result in session state")
                st.session_state["agent_sql_execution_result"] = {
                    "status": "error",
                    "sql": agent_sql,
                    "source": agent_source,
                    "error": str(e),
                    "error_trace": error_trace,
                    "timestamp": agent_timestamp
                }
                
                # Clear the flag after error (but keep result for display)
                st.session_state.pop("agent_sql_to_run", None)
                st.session_state.pop("agent_sql_source", None)
                st.session_state.pop("agent_sql_timestamp", None)
        else:
            # Result already stored - display it
            result = agent_execution_result
            st.info(f"▶ SQL suggested by {result.get('source', 'AI Agent')} - Execution Result")
            st.code(result.get('sql', ''), language='sql')
            
            if result.get('status') == 'success':
                st.success("✅ SQL executed successfully!")
                sql_upper = result.get('sql', '').strip().upper()
                if any(sql_upper.startswith(cmd) for cmd in ['UPDATE', 'DELETE', 'INSERT']):
                    st.info("💡 **Tip:** Run a SELECT query to verify the changes were applied correctly.")
            else:
                st.error(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
            
            # Add button to clear the result
            if st.button("Clear Result", key="clear_agent_result"):
                st.session_state.pop("agent_sql_execution_result", None)
                st.rerun()
    
    # Don't show API key message on page load - only show when user tries to use it
    
    # Example questions section - only show if chatbot is available
    if not st.session_state.chat_history and st.session_state.chatbot:
        #st.markdown("### 💡 Example Questions to Get Started")
        #st.markdown("Click on any question below to get started:")
        
        example_questions = [
            "list of all tables in the database",
            "Tables with more than 10 records",
            "Column names and data types for all tables?"
        ]
        
        cols = st.columns(3)
        for idx, question in enumerate(example_questions):
            with cols[idx]:
                if st.button(f"❓ {question}", key=f"example_{idx}", use_container_width=True):
                    # Add the question to chat history and process it
                    st.session_state.chat_history.append({'role': 'user', 'content': question})
                    try:
                        with st.spinner("🤔 Thinking..."):
                            response = st.session_state.chatbot.chat(question, include_sql=True)
                        
                        if 'error' not in response:
                            sql_query = response.get('sql_query')
                            auto_executed = False
                            
                            # Auto-execute SELECT queries for example questions
                            if sql_query:
                                sql_upper = sql_query.strip().upper()
                                is_select = sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')
                                is_not_ddl_dml = not any(sql_upper.startswith(cmd) for cmd in [
                                    'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'INSERT', 'UPDATE', 'DELETE',
                                    'GRANT', 'REVOKE', 'COMMENT', 'ANALYZE', 'VACUUM'
                                ])
                                
                                if is_select and is_not_ddl_dml:
                                    try:
                                        execute_query(sql_query, enable_agents=False)
                                        auto_executed = True
                                    except Exception as exec_error:
                                        print(f"DEBUG: Auto-execution failed: {exec_error}")
                            
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': response['response'],
                                'sql_query': sql_query,
                                'timestamp': response['timestamp'],
                                'auto_executed': auto_executed
                            })
                        else:
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': response.get('response', response.get('error', 'Error occurred')),
                                'timestamp': response.get('timestamp', datetime.now().isoformat())
                            })
                    except Exception as e:
                        error_msg = f"❌ Error processing query: {str(e)}"
                        print(f"DEBUG: Chatbot error on example question: {e}")
                        import traceback
                        traceback.print_exc()
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': error_msg,
                            'timestamp': datetime.now().isoformat()
                        })
                    st.rerun()
        
        st.markdown("---")
    
    # Add marker before chat messages
    st.markdown('<div id="chat-container-start"></div>', unsafe_allow_html=True)
    
    # DEBUG: Show debug info in UI (temporary - remove after fixing)
    has_last_result = st.session_state.get('last_result_df') is not None
    has_auto_query = st.session_state.get('chatbot_last_auto_executed_query') is not None
    has_auto_error = st.session_state.get('chatbot_auto_execution_error') is not None
    has_show_results_flag = st.session_state.get('chatbot_show_results_for_query') is not None
    print(f"DEBUG: Checking for results - has_last_result={has_last_result}, has_auto_query={has_auto_query}, has_auto_error={has_auto_error}, has_show_flag={has_show_results_flag}")
    
    with st.expander("🔍 Debug Info (Click to see)", expanded=False):
        st.write("**Session State Check:**")
        st.write(f"- `last_result_df` exists: {has_last_result}")
        st.write(f"- `chatbot_last_auto_executed_query` exists: {has_auto_query}")
        st.write(f"- `chatbot_show_results_for_query` exists: {has_show_results_flag}")
        st.write(f"- `chatbot_auto_execution_error` exists: {has_auto_error}")
        if has_last_result:
            st.write(f"- Result rows: {len(st.session_state.last_result_df)}")
            st.write(f"- Result columns: {list(st.session_state.last_result_df.columns)[:5]}...")
        if has_auto_query:
            st.write(f"- Last auto-executed query: {st.session_state.chatbot_last_auto_executed_query[:100]}...")
        if has_auto_error:
            st.write(f"- Auto-execution error: {st.session_state.chatbot_auto_execution_error[:200]}...")
        st.write(f"- Query history length: {len(st.session_state.get('query_history', []))}")
        st.write(f"- Chat history length: {len(st.session_state.get('chat_history', []))}")
    
    # Display chat history
    print(f"DEBUG: Displaying chat history - total messages: {len(st.session_state.chat_history) if st.session_state.chat_history else 0}")
    
    # Track if we've shown results for the latest message
    results_shown_for_latest = False
    
    if st.session_state.chat_history:
        total_messages = len(st.session_state.chat_history)
        for idx, msg in enumerate(st.session_state.chat_history):
            print(f"DEBUG: Displaying message {idx}: role={msg.get('role')}, has_content={bool(msg.get('content'))}, has_sql={bool(msg.get('sql_query'))}")
            # Generate unique key using index and timestamp if available
            msg_timestamp = msg.get('timestamp', str(idx))
            unique_key_base = f"chatbot_tab_{idx}_{hash(str(msg_timestamp)) % 10000}"
            
            if msg['role'] == 'user':
                st.chat_message("user").write(msg['content'])
            else:
                # Show explanation in collapsed expander by default
                try:
                    with st.expander("💡 View Explanation", expanded=False, key=f"explanation_{unique_key_base}"):
                        st.chat_message("assistant").write(msg['content'])
                except Exception as e:
                    # Fallback if expander fails
                    st.chat_message("assistant").write(msg['content'])
                
                # Show SQL query in expanded form by default
                if 'sql_query' in msg and msg['sql_query']:
                    try:
                        sql_query = msg['sql_query']
                        sql_upper = sql_query.strip().upper()
                        
                        # Check if it's a SELECT query (data retrieval)
                        is_select = sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')
                        # Check if it's NOT DDL or DML (for safety)
                        is_not_ddl_dml = not any(sql_upper.startswith(cmd) for cmd in [
                            'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'INSERT', 'UPDATE', 'DELETE',
                            'GRANT', 'REVOKE', 'COMMENT', 'ANALYZE', 'VACUUM'
                        ])
                        
                        # Show SQL
                        with st.expander("📝 Generated SQL", expanded=True, key=f"sql_{unique_key_base}"):
                            st.code(sql_query, language='sql')
                            
                            # For SELECT queries, show that it was auto-executed (results appear below)
                            if is_select and is_not_ddl_dml:
                                if msg.get('auto_executed', False):
                                    st.success("✅ Query executed automatically. Results shown below.")
                                else:
                                    # If not auto-executed yet, execute it now
                                    if st.button(f"Execute Query", key=f"exec_{unique_key_base}"):
                                        execute_generated_query(sql_query)
                            else:
                                # For DDL/DML, always require manual execution
                                if st.button(f"Execute Query", key=f"exec_{unique_key_base}"):
                                    execute_generated_query(sql_query)
                        
                        # Show auto-execution results right after the latest assistant message with SQL
                        # Check if this is the last message and matches the auto-executed query
                        is_last_message = (idx == total_messages - 1)
                        msg_has_sql = 'sql_query' in msg and msg['sql_query']
                        
                        # More lenient SQL matching - strip and compare
                        auto_executed_sql = st.session_state.get('chatbot_last_auto_executed_query', '').strip()
                        show_results_for = st.session_state.get('chatbot_show_results_for_query', '').strip()
                        msg_sql = msg['sql_query'].strip() if msg_has_sql else ''
                        msg_sql_matches = msg_has_sql and msg_sql == auto_executed_sql
                        msg_should_show = msg_has_sql and msg_sql == show_results_for
                        msg_was_auto_executed = msg.get('auto_executed', False)
                        
                        print(f"DEBUG: Message {idx}/{total_messages-1} - is_last={is_last_message}, has_sql={msg_has_sql}")
                        print(f"DEBUG: msg_sql[:50]={msg_sql[:50] if msg_sql else 'None'}")
                        print(f"DEBUG: auto_sql[:50]={auto_executed_sql[:50] if auto_executed_sql else 'None'}")
                        print(f"DEBUG: show_results_for[:50]={show_results_for[:50] if show_results_for else 'None'}")
                        print(f"DEBUG: sql_matches={msg_sql_matches}, should_show={msg_should_show}, auto_executed={msg_was_auto_executed}")
                        print(f"DEBUG: has_last_result={has_last_result}, has_auto_query={has_auto_query}")
                        
                        # Show results if: (1) it's the last message AND (2) has SQL AND (3) we have results available
                        # Simplified condition - if it's the last message with SQL and results exist, show them
                        should_show_results = (
                            is_last_message and 
                            msg_has_sql and 
                            has_last_result and 
                            has_auto_query
                            # Removed strict matching - if results exist and it's the last message, show them
                        )
                        
                        print(f"DEBUG: should_show_results={should_show_results}")
                        
                        if should_show_results:
                            # Check if we have results or errors to display
                            if has_auto_error:
                                # Show error
                                st.error(f"❌ Auto-execution failed: {st.session_state.chatbot_auto_execution_error}")
                                st.code(st.session_state.get('chatbot_last_auto_executed_query', ''), language='sql')
                                st.info("💡 The query was generated but failed to execute. Please check the SQL syntax and table/column names.")
                                results_shown_for_latest = True
                            else:
                                # Show results
                                from utils.helpers import display_paginated_dataframe
                                print(f"DEBUG: ✅ Displaying results after latest message - rows: {len(st.session_state.last_result_df)}")
                                st.markdown("---")
                                # Compact Results header with download icon
                                result_col1, result_col2 = st.columns([9, 0.4], gap="small")
                                with result_col1:
                                    st.markdown("**📊 Query Results**", unsafe_allow_html=True)
                                with result_col2:
                                    # Download CSV button
                                    csv = st.session_state.last_result_df.to_csv(index=False)
                                    st.download_button(
                                        "📥",
                                        csv,
                                        "results.csv",
                                        "text/csv",
                                        help=f"Download CSV - {len(st.session_state.last_result_df):,} rows",
                                        use_container_width=True,
                                        key=f"download_auto_{unique_key_base}"
                                    )
                                
                                # Search and visualization are now handled inside display_paginated_dataframe
                                display_df = st.session_state.last_result_df.copy()
                                st.session_state.current_page = 1
                                display_paginated_dataframe(
                                    display_df, 
                                    unique_suffix=f"chatbot_auto_result_{hash(st.session_state.chatbot_last_auto_executed_query) % 10000}"
                                )
                                results_shown_for_latest = True
                        else:
                            print(f"DEBUG: ❌ Not showing results - is_last={is_last_message}, has_sql={msg_has_sql}, has_result={has_last_result}, has_query={has_auto_query}")
                    except Exception as e:
                        # Fallback if expander fails
                        st.code(msg['sql_query'], language='sql')
                        if st.button(f"Execute Query", key=f"exec_fallback_{unique_key_base}"):
                            execute_generated_query(msg['sql_query'])
    
    # Fallback: If we have results but didn't show them in the loop, show them after chat history
    # Also check if there's an error that should be shown
    if has_auto_error and has_auto_query and not results_shown_for_latest:
        print(f"DEBUG: 🔄 Fallback - showing error after chat history loop")
        st.error(f"❌ Auto-execution failed: {st.session_state.chatbot_auto_execution_error}")
        st.code(st.session_state.get('chatbot_last_auto_executed_query', ''), language='sql')
        st.info("💡 The query was generated but failed to execute. Please check the SQL syntax and table/column names.")
        results_shown_for_latest = True
    
    if not results_shown_for_latest and has_last_result and has_auto_query and not has_auto_error:
        print(f"DEBUG: 🔄 Fallback - showing results after chat history loop")
        from utils.helpers import display_paginated_dataframe
        st.markdown("---")
        # Compact Results header with download icon
        result_col1, result_col2 = st.columns([9, 0.4], gap="small")
        with result_col1:
            st.markdown("**📊 Query Results**", unsafe_allow_html=True)
        with result_col2:
            # Download CSV button
            csv = st.session_state.last_result_df.to_csv(index=False)
            st.download_button(
                "📥",
                csv,
                "results.csv",
                "text/csv",
                help=f"Download CSV - {len(st.session_state.last_result_df):,} rows",
                use_container_width=True,
                key="download_auto_fallback"
            )
        
        # Search and visualization are now handled inside display_paginated_dataframe
        display_df = st.session_state.last_result_df.copy()
        st.session_state.current_page = 1
        display_paginated_dataframe(
            display_df, 
            unique_suffix=f"chatbot_auto_result_fallback_{hash(st.session_state.chatbot_last_auto_executed_query) % 10000}"
        )
    
    # else:
    #     st.info("💬 Start chatting by typing a message below!")
    
    # Add marker after chat messages and JavaScript to wrap them
    st.markdown("""
    <div id="chat-container-end"></div>
    <script>
        (function() {
            function wrapChatMessages() {
                const startMarker = document.getElementById('chat-container-start');
                const endMarker = document.getElementById('chat-container-end');
                if (!startMarker || !endMarker) return;
                
                // Check if wrapper already exists
                if (document.getElementById('chat-messages-scrollable-wrapper')) return;
                
                // Find parent container
                let parent = startMarker.parentElement;
                if (!parent) return;
                
                // Create wrapper div
                const wrapper = document.createElement('div');
                wrapper.id = 'chat-messages-scrollable-wrapper';
                wrapper.style.cssText = `
                    max-height: 60vh;
                    overflow-y: auto;
                    overflow-x: hidden;
                    padding: 1rem;
                    margin-bottom: 1rem;
                    border: 1px solid rgba(250, 250, 250, 0.2);
                    border-radius: 0.5rem;
                    background-color: rgba(0, 0, 0, 0.02);
                    scroll-behavior: smooth;
                `;
                
                // Collect all nodes between markers
                let node = startMarker.nextSibling;
                const nodesToMove = [];
                while (node && node !== endMarker) {
                    nodesToMove.push(node);
                    node = node.nextSibling;
                }
                
                // Move nodes into wrapper
                nodesToMove.forEach(n => wrapper.appendChild(n));
                
                // Insert wrapper after start marker
                startMarker.parentNode.insertBefore(wrapper, startMarker.nextSibling);
                
                // Auto-scroll to bottom
                wrapper.scrollTop = wrapper.scrollHeight;
            }
            
            // Run immediately and after delays
            wrapChatMessages();
            setTimeout(wrapChatMessages, 100);
            setTimeout(wrapChatMessages, 500);
            
            // Also observe for changes
            const observer = new MutationObserver(function() {
                wrapChatMessages();
                const wrapper = document.getElementById('chat-messages-scrollable-wrapper');
                if (wrapper) {
                    wrapper.scrollTop = wrapper.scrollHeight;
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        })();
    </script>
    """, unsafe_allow_html=True)
    
    # Chat input (outside scrollable container, stays at bottom)
    user_input = st.chat_input("Ask me anything about your database...")
    
    if user_input:
        # Check if chatbot is available when user actually tries to use it
        print(f"DEBUG: User input received (chatbot_tab): {user_input}")
        print(f"DEBUG: Chatbot available (chatbot_tab): {st.session_state.chatbot is not None}")
        if not st.session_state.chatbot:
            print(f"DEBUG: Chatbot is None (chatbot_tab), showing error message")
            st.error("❌ AI Chatbot is not available. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable to enable AI features.")
        else:
            # Ensure chatbot has latest schema context before generating SQL
            schema_info = st.session_state.get('schema_info')
            if st.session_state.chatbot:
                if schema_info:
                    try:
                        st.session_state.chatbot.set_schema_context(schema_info)
                        print(f"DEBUG: Schema context set - tables: {len(schema_info.get('tables', []))}")
                        # Debug: Check if tables have column details
                        tables = schema_info.get('tables', [])
                        if tables:
                            first_table = tables[0]
                            if isinstance(first_table, dict):
                                cols = first_table.get('columns', [])
                                print(f"DEBUG: First table '{first_table.get('table_name', 'unknown')}' has {len(cols)} columns")
                            else:
                                print(f"DEBUG: WARNING - First table is not a dict, it's: {type(first_table)}")
                    except Exception as e:
                        print(f"DEBUG: Could not refresh chatbot schema: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"DEBUG: WARNING - schema_info is None or not set in session state")
                    # Try to rebuild schema_info if connected
                    if st.session_state.connected and st.session_state.db_manager:
                        try:
                            tables = st.session_state.db_manager.get_tables()
                            full_table_schemas = []
                            for table_name in (tables or []):
                                try:
                                    table_schema = st.session_state.db_manager.get_table_schema(table_name)
                                    if table_schema:
                                        full_table_schemas.append(table_schema)
                                except Exception as e:
                                    full_table_schemas.append({'table_name': table_name, 'columns': []})
                            
                            schema_info = {
                                'tables': full_table_schemas,
                                'db_type': st.session_state.get('db_type', 'unknown'),
                                'total_tables': len(tables) if tables else 0,
                                'database_name': st.session_state.db_manager.config.database if st.session_state.db_manager.config else 'unknown'
                            }
                            st.session_state.schema_info = schema_info
                            st.session_state.chatbot.set_schema_context(schema_info)
                            print(f"DEBUG: Rebuilt schema_info - {len(full_table_schemas)} tables with schemas")
                        except Exception as e:
                            print(f"DEBUG: Could not rebuild schema_info: {e}")
                            import traceback
                            traceback.print_exc()
            
            # Add user message to history
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            # Get AI response
            try:
                print(f"DEBUG: Calling chatbot.chat() (chatbot_tab) with query: {user_input}")
                print(f"DEBUG: Schema context available: {st.session_state.chatbot.schema_context is not None if st.session_state.chatbot else False}")
                if st.session_state.chatbot and st.session_state.chatbot.schema_context:
                    tables = st.session_state.chatbot.schema_context.get('tables', [])
                    print(f"DEBUG: Schema tables count: {len(tables)}")
                    if tables:
                        first_table = tables[0]
                        if isinstance(first_table, dict):
                            print(f"DEBUG: First table in context: {first_table.get('table_name', 'unknown')} with {len(first_table.get('columns', []))} columns")
                        else:
                            print(f"DEBUG: First table type: {type(first_table)}, value: {first_table}")
                else:
                    print(f"DEBUG: WARNING - No schema context in chatbot!")
                print(f"DEBUG: Schema tables count: {len(st.session_state.get('schema_info', {}).get('tables', [])) if st.session_state.get('schema_info') else 0}")
                with st.spinner("🤔 Thinking..."):
                    response = st.session_state.chatbot.chat(user_input, include_sql=True)
                print(f"DEBUG: Chatbot response received (chatbot_tab): {type(response)}, has error: {'error' in response if isinstance(response, dict) else 'N/A'}")
                print(f"DEBUG: Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
                if 'error' not in response:
                    # Add assistant response to history
                    try:
                        response_content = response.get('response', response.get('content', str(response)))
                        sql_query = response.get('sql_query', response.get('sql', None))
                        timestamp = response.get('timestamp', datetime.now().isoformat())
                        print(f"DEBUG: Adding response to chat history - content length: {len(response_content) if response_content else 0}, has sql: {bool(sql_query)}")
                        
                        # Check if SQL is a SELECT query (data retrieval) - auto-execute it
                        auto_executed = False
                        if sql_query:
                            sql_upper = sql_query.strip().upper()
                            print(f"DEBUG: Extracted SQL query: {sql_query[:200]}...")
                            print(f"DEBUG: SQL query upper: {sql_upper[:200]}...")
                            # Check if it's a SELECT query (data retrieval)
                            is_select = sql_upper.startswith('SELECT') or sql_upper.startswith('WITH')
                            # Check if it's NOT DDL or DML (for safety)
                            is_not_ddl_dml = not any(sql_upper.startswith(cmd) for cmd in [
                                'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'INSERT', 'UPDATE', 'DELETE',
                                'GRANT', 'REVOKE', 'COMMENT', 'ANALYZE', 'VACUUM'
                            ])
                            
                            print(f"DEBUG: is_select={is_select}, is_not_ddl_dml={is_not_ddl_dml}")
                            
                            if is_select and is_not_ddl_dml:
                                # Auto-execute SELECT queries
                                try:
                                    print(f"DEBUG: Auto-executing SELECT query: {sql_query[:100]}...")
                                    # Store the query BEFORE execution so it's available after rerun
                                    st.session_state['chatbot_last_auto_executed_query'] = sql_query
                                    st.session_state['chatbot_auto_executed_timestamp'] = timestamp
                                    st.session_state['chatbot_auto_execution_error'] = None  # Clear any previous error
                                    print(f"DEBUG: Flag set before execute_query")
                                    execute_query(sql_query, enable_agents=False, unique_suffix="chatbot_auto")
                                    # Verify results were stored
                                    has_results = st.session_state.get('last_result_df') is not None
                                    print(f"DEBUG: After execute_query - has_results={has_results}, last_result_df type: {type(st.session_state.get('last_result_df'))}")
                                    # Clear any previous error on success
                                    st.session_state.pop('chatbot_auto_execution_error', None)
                                    st.session_state.pop('chatbot_auto_execution_error_trace', None)
                                    # Set flag to indicate results should be shown for this query
                                    st.session_state['chatbot_show_results_for_query'] = sql_query
                                    auto_executed = True
                                    print(f"DEBUG: Auto-execution successful, auto_executed={auto_executed}, show_results_flag set")
                                except Exception as exec_error:
                                    print(f"DEBUG: Auto-execution failed: {exec_error}")
                                    import traceback
                                    error_trace = traceback.format_exc()
                                    traceback.print_exc()
                                    # Store error in session state so it can be displayed after rerun
                                    st.session_state['chatbot_auto_execution_error'] = str(exec_error)
                                    st.session_state['chatbot_auto_execution_error_trace'] = error_trace
                                    # Keep the query flag so we can show the error with context
                                    # Don't clear chatbot_last_auto_executed_query - we need it to show error
                                    auto_executed = False
                                    # Show error immediately (before rerun)
                                    st.error(f"❌ Auto-execution failed: {str(exec_error)}")
                                    st.code(sql_query, language='sql')
                                    print(f"DEBUG: Error stored in session state for display after rerun")
                        else:
                            print(f"DEBUG: No SQL query extracted from response")
                        
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': response_content,
                            'sql_query': sql_query,
                            'timestamp': timestamp,
                            'auto_executed': auto_executed  # Track if query was auto-executed
                        })
                        
                        # If we auto-executed, results are already displayed and stored in session state
                        # We still need to rerun to show the chat message, but results will be re-displayed
                        st.rerun()
                    except Exception as process_error:
                        print(f"DEBUG: Error processing response: {process_error}")
                        import traceback
                        traceback.print_exc()
                        st.error(f"❌ Error processing chatbot response: {str(process_error)}")
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': f"Error processing response: {str(process_error)}",
                            'timestamp': datetime.now().isoformat()
                        })
                        st.rerun()
                else:
                    error_msg = response.get('error', 'Unknown error occurred')
                    print(f"DEBUG: Response contains error: {error_msg}")
                    st.error(f"Error: {error_msg}")
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': f"Error: {error_msg}",
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                error_msg = f"❌ Error processing query: {str(e)}"
                st.error(error_msg)
                print(f"DEBUG: Chatbot error: {e}")
                import traceback
                traceback.print_exc()
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
                st.rerun()


