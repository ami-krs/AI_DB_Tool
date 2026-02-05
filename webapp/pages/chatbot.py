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
    st.header("💬 AI SQL Assistant")
    st.markdown("Ask questions in natural language and get SQL queries generated automatically")

    # If an agent (e.g., Debug Agent) requested to run suggested SQL, execute it here
    # Check this FIRST before rendering anything else, so results appear at the top
    agent_sql = st.session_state.get("agent_sql_to_run")
    if agent_sql:
        # Clear the flag immediately to prevent re-execution
        st.session_state.pop("agent_sql_to_run", None)
        agent_source = st.session_state.pop("agent_sql_source", "AI Agent")
        agent_timestamp = st.session_state.pop("agent_sql_timestamp", None)
        
        st.info(f"▶ Running SQL suggested by {agent_source}")
        st.code(agent_sql, language='sql')
        try:
            # Run without agents to avoid recursive analysis
            execute_query(agent_sql, enable_agents=False)
            
            # After DDL operations (especially CREATE SCHEMA), refresh schema info
            sql_upper = agent_sql.strip().upper()
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
        except Exception as e:
            st.error(f"❌ Failed to execute suggested SQL: {e}")
            import traceback
            st.exception(e)
    
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
                            st.session_state.chat_history.append({
                                'role': 'assistant',
                                'content': response['response'],
                                'sql_query': response.get('sql_query'),
                                'timestamp': response['timestamp']
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
    
    # Display chat history
    print(f"DEBUG: Displaying chat history - total messages: {len(st.session_state.chat_history) if st.session_state.chat_history else 0}")
    if st.session_state.chat_history:
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
                            
                            # For SELECT queries, show that it was auto-executed (results appear above)
                            if is_select and is_not_ddl_dml:
                                if msg.get('auto_executed', False):
                                    st.success("✅ Query executed automatically. Results shown above.")
                                else:
                                    # If not auto-executed yet, execute it now
                                    if st.button(f"Execute Query", key=f"exec_{unique_key_base}"):
                                        execute_generated_query(sql_query)
                            else:
                                # For DDL/DML, always require manual execution
                                if st.button(f"Execute Query", key=f"exec_{unique_key_base}"):
                                    execute_generated_query(sql_query)
                    except Exception as e:
                        # Fallback if expander fails
                        st.code(msg['sql_query'], language='sql')
                        if st.button(f"Execute Query", key=f"exec_fallback_{unique_key_base}"):
                            execute_generated_query(msg['sql_query'])
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
            if st.session_state.chatbot and st.session_state.get('schema_info'):
                try:
                    st.session_state.chatbot.set_schema_context(st.session_state.schema_info)
                except Exception as e:
                    st.debug(f"Could not refresh chatbot schema: {e}")
            
            # Add user message to history
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            
            # Get AI response
            try:
                print(f"DEBUG: Calling chatbot.chat() (chatbot_tab) with query: {user_input}")
                print(f"DEBUG: Schema context available: {st.session_state.chatbot.schema_context is not None if st.session_state.chatbot else False}")
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


