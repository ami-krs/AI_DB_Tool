"""UI components for displaying AI agent analysis and suggestions"""
import streamlit as st
from typing import List, Dict, Any
from datetime import datetime

from ai_db_tool.ai.agents import AgentResponse


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
        st.markdown(response.analysis)
        
        # Display suggestions if available
        if response.suggestions:
            st.markdown("#### 💡 Suggestions")
            for idx, suggestion in enumerate(response.suggestions, 1):
                st.markdown(f"{idx}. {suggestion}")
        
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
