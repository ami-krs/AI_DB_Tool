"""UI components for displaying AI agent analysis and suggestions"""
import streamlit as st
from typing import List, Dict, Any
from datetime import datetime
import re

from ai_db_tool.ai.agents import AgentResponse


def _extract_first_sql_block(text: str) -> str | None:
    """Extract first ```sql ...``` fenced block from text, if present."""
    if not text:
        return None
    match = re.search(r"```sql\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    if not match:
        return None
    sql = match.group(1).strip()
    return sql or None


def display_agent_response(response: AgentResponse, expanded: bool = False):
    """Display a single agent response"""
    if not response:
        return
    
    # Determine icon and color based on agent type
    agent_icons = {
        "Query Analyzer": "🔍",
        "Results Analyzer": "📊",
        "Debug Agent": "🐛",
        "Review Agent": "✨"
    }
    
    agent_colors = {
        "Query Analyzer": "🔵",
        "Results Analyzer": "🟢",
        "Debug Agent": "🔴",
        "Review Agent": "🟡"
    }
    
    icon = agent_icons.get(response.agent_name, "🤖")
    color_indicator = agent_colors.get(response.agent_name, "⚪")
    
    # Confidence indicator
    confidence_color = "🟢" if response.confidence >= 0.8 else "🟡" if response.confidence >= 0.6 else "🔴"
    
    with st.expander(
        f"{icon} **{response.agent_name}** {color_indicator} (Confidence: {confidence_color} {response.confidence:.0%})",
        expanded=expanded
    ):
        # Display analysis
        st.markdown("#### 📝 Analysis")
        analysis_text = response.analysis or ""

        # For Results Analyzer, force very brief display (first 2 sentences or ~250 chars)
        if response.agent_name == "Results Analyzer":
            # Split on sentence boundaries (very simple heuristic)
            parts = re.split(r'(?<=[.!?])\s+', analysis_text.strip())
            brief = " ".join(parts[:2]).strip()
            if len(brief) > 250:
                brief = brief[:247].rstrip() + "..."
            st.markdown(brief)
        else:
            st.markdown(analysis_text)
        
        # Display suggestions if available
        if response.suggestions:
            st.markdown("#### 💡 Suggestions")
            for idx, suggestion in enumerate(response.suggestions, 1):
                st.markdown(f"{idx}. {suggestion}")

        # Optional: runnable SQL snippet (when agent suggests SQL)
        suggested_sql = _extract_first_sql_block(response.analysis or "")
        if suggested_sql:
            st.markdown("#### ▶ Run suggested SQL")
            st.caption("Edit and run the suggested SQL. This runs **once** in the main results area (agents disabled).")

            key_base = f"agent_sql_{response.agent_name}_{int(response.timestamp.timestamp())}"
            # Get current value from session state if it exists, otherwise use suggested SQL
            editor_key = f"{key_base}_editor"
            initial_value = st.session_state.get(editor_key, suggested_sql)
            
            sql_to_run = st.text_area(
                "Suggested SQL",
                value=initial_value,
                height=120,
                key=editor_key,
            )
            
            run_cols = st.columns([1, 4])
            with run_cols[0]:
                run_button_clicked = st.button("Run", key=f"{key_base}_run", type="primary")
            
            # Handle button click - check both button state and session state flag
            button_key = f"{key_base}_run"
            # Also check if button was clicked in previous run (stored in session state)
            was_clicked = st.session_state.get(f"{button_key}_clicked", False)
            
            if run_button_clicked or was_clicked:
                # Mark that button was clicked
                st.session_state[f"{button_key}_clicked"] = True
                
                # Get the current SQL value from session state (text_area updates session state automatically)
                current_sql = st.session_state.get(editor_key, sql_to_run)
                
                # Final fallback to suggested_sql
                if not current_sql or not current_sql.strip():
                    current_sql = suggested_sql
                
                print(f"DEBUG: Run button clicked (run_button_clicked={run_button_clicked}, was_clicked={was_clicked})")
                print(f"DEBUG: editor_key: {editor_key}")
                print(f"DEBUG: sql_to_run (from text_area return): {sql_to_run[:100] if sql_to_run else 'None'}...")
                print(f"DEBUG: session_state[{editor_key}]: {st.session_state.get(editor_key, 'NOT FOUND')[:100] if st.session_state.get(editor_key) else 'NOT FOUND'}...")
                print(f"DEBUG: suggested_sql (original): {suggested_sql[:100] if suggested_sql else 'None'}...")
                print(f"DEBUG: current_sql (final): {current_sql[:100] if current_sql else 'None'}...")
                
                # Store SQL in session state - use direct assignment
                st.session_state["agent_sql_to_run"] = current_sql
                st.session_state["agent_sql_source"] = response.agent_name
                st.session_state["agent_sql_timestamp"] = response.timestamp.isoformat()
                # Clear any previous execution result
                if "agent_sql_execution_result" in st.session_state:
                    del st.session_state["agent_sql_execution_result"]
                
                # Clear the clicked flag
                if f"{button_key}_clicked" in st.session_state:
                    del st.session_state[f"{button_key}_clicked"]
                
                # Verify it was stored immediately
                stored_value = st.session_state.get("agent_sql_to_run")
                print(f"DEBUG: Verification - agent_sql_to_run in session_state: {stored_value is not None}")
                if stored_value:
                    print(f"DEBUG:   Stored value: {stored_value[:100]}...")
                    # Show visible confirmation
                    st.success(f"✅ SQL queued for execution! ({len(stored_value)} characters)")
                else:
                    print(f"DEBUG:   ERROR - Value was NOT stored!")
                    st.error("❌ Error: Failed to store SQL in session state. Please try again.")
                    st.stop()
                
                print(f"DEBUG: Stored in session state:")
                print(f"DEBUG:   agent_sql_to_run = {stored_value[:100] if stored_value else 'NOT SET'}...")
                print(f"DEBUG:   agent_sql_source = {st.session_state.get('agent_sql_source', 'NOT SET')}")
                print(f"DEBUG: Triggering rerun...")
                st.rerun()
        
        # Display metadata
        if response.metadata:
            with st.expander("🔧 Technical Details", expanded=False):
                st.json(response.metadata)
        
        # Timestamp
        st.caption(f"Generated at: {response.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


def display_agent_suggestions(responses: List[AgentResponse], title: str = "🤖 AI Agent Analysis"):
    """Display multiple agent responses in a organized way"""
    if not responses:
        return
    
    st.markdown(f"### {title}")
    st.markdown("---")
    
    # Group by agent type
    agent_groups = {}
    for response in responses:
        agent_type = response.agent_name
        if agent_type not in agent_groups:
            agent_groups[agent_type] = []
        agent_groups[agent_type].append(response)
    
    # Display each agent group
    for agent_type, agent_responses in agent_groups.items():
        # Show most recent response for each agent type
        latest_response = max(agent_responses, key=lambda r: r.timestamp)
        display_agent_response(latest_response, expanded=(agent_type == "Debug Agent"))
    
    st.markdown("---")


def display_agent_summary(responses: List[AgentResponse]):
    """Display a quick summary of agent responses"""
    if not responses:
        return
    
    # Count by agent type
    agent_counts = {}
    for response in responses:
        agent_type = response.agent_name
        agent_counts[agent_type] = agent_counts.get(agent_type, 0) + 1
    
    # Display summary
    cols = st.columns(len(agent_counts))
    for idx, (agent_type, count) in enumerate(agent_counts.items()):
        with cols[idx]:
            st.metric(agent_type, count)


def display_agent_insights(responses: List[AgentResponse], max_insights: int = 5):
    """Extract and display key insights from agent responses"""
    if not responses:
        return
    
    insights = []
    for response in responses:
        # Extract key insights from suggestions
        for suggestion in response.suggestions[:2]:  # Top 2 suggestions per agent
            insights.append({
                'agent': response.agent_name,
                'insight': suggestion,
                'confidence': response.confidence
            })
    
    # Sort by confidence
    insights.sort(key=lambda x: x['confidence'], reverse=True)
    
    if insights:
        st.markdown("#### 🎯 Key Insights")
        for insight in insights[:max_insights]:
            st.info(f"**{insight['agent']}**: {insight['insight']}")
