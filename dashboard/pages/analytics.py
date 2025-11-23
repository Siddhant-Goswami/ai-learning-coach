"""
Analytics Page - Learning Progress & Stats

Visualize learning progress, feedback trends, and source performance.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
import os


def show():
    """Render the analytics page."""
    st.title("📊 Learning Analytics")

    # Key metrics (top row)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Insights", "142", delta="+7 this week")

    with col2:
        st.metric("Helpful Rate", "85%", delta="+3%")

    with col3:
        st.metric("Time Saved", "18 hours", delta="+3 hours")

    with col4:
        st.metric("Current Week", "7 / 24", delta="29%")

    st.markdown("---")

    # Charts in tabs
    tab1, tab2, tab3 = st.tabs(["📈 Progress", "💬 Feedback", "📚 Sources"])

    with tab1:
        show_progress_charts()

    with tab2:
        show_feedback_charts()

    with tab3:
        show_source_charts()


def show_progress_charts():
    """Show learning progress charts."""
    st.subheader("Learning Progress Over Time")

    # Mock data for progress
    weeks = list(range(1, 8))
    topics_covered = [3, 4, 5, 6, 7, 8, 9]
    expected = [3, 5, 7, 9, 11, 13, 15]

    df = pd.DataFrame({
        "Week": weeks,
        "Topics Covered": topics_covered,
        "Expected": expected,
    })

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Week"],
        y=df["Topics Covered"],
        mode="lines+markers",
        name="Actual Progress",
        line=dict(color="#3b82f6", width=3),
        marker=dict(size=8),
    ))

    fig.add_trace(go.Scatter(
        x=df["Week"],
        y=df["Expected"],
        mode="lines",
        name="Expected Progress",
        line=dict(color="#a0a0a0", width=2, dash="dash"),
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#1a1a1a",
        font=dict(color="#ffffff"),
        height=400,
        xaxis_title="Week",
        yaxis_title="Topics Covered",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # Topic engagement heatmap
    st.subheader("Topic Engagement")

    topics = ["Transformers", "Attention", "Multi-Head", "Self-Attention", "Positional Encoding"]
    engagement = [95, 88, 72, 65, 58]

    df_topics = pd.DataFrame({
        "Topic": topics,
        "Engagement %": engagement,
    })

    fig_topics = px.bar(
        df_topics,
        x="Engagement %",
        y="Topic",
        orientation="h",
        color="Engagement %",
        color_continuous_scale="Blues",
    )

    fig_topics.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#1a1a1a",
        font=dict(color="#ffffff"),
        height=300,
        showlegend=False,
    )

    st.plotly_chart(fig_topics, use_container_width=True)


def show_feedback_charts():
    """Show feedback analytics."""
    st.subheader("Feedback Trends")

    # Mock feedback data
    dates = pd.date_range(end=datetime.now(), periods=14, freq="D")
    helpful = [5, 6, 7, 8, 6, 9, 10, 8, 9, 11, 10, 12, 11, 13]
    not_relevant = [1, 2, 1, 0, 2, 1, 1, 2, 1, 1, 0, 1, 2, 1]

    df_feedback = pd.DataFrame({
        "Date": dates,
        "Helpful": helpful,
        "Not Relevant": not_relevant,
    })

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_feedback["Date"],
        y=df_feedback["Helpful"],
        name="Helpful",
        marker_color="#10b981",
    ))

    fig.add_trace(go.Bar(
        x=df_feedback["Date"],
        y=df_feedback["Not Relevant"],
        name="Not Relevant",
        marker_color="#ef4444",
    ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#1a1a1a",
        font=dict(color="#ffffff"),
        height=350,
        barmode="stack",
        xaxis_title="Date",
        yaxis_title="Feedback Count",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Feedback breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Feedback Breakdown")

        feedback_types = ["Helpful", "Not Relevant", "Too Basic", "Too Advanced", "Incorrect"]
        counts = [125, 10, 3, 3, 1]

        df_breakdown = pd.DataFrame({
            "Type": feedback_types,
            "Count": counts,
        })

        fig_pie = px.pie(
            df_breakdown,
            values="Count",
            names="Type",
            color_discrete_sequence=["#10b981", "#ef4444", "#f59e0b", "#f59e0b", "#ef4444"],
        )

        fig_pie.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0a0a0a",
            font=dict(color="#ffffff"),
            height=300,
        )

        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("Insights")

        st.success("✅ **Most Engaged Topics**\nTransformers, Attention Mechanisms, RAG Systems")
        st.warning("⚠️ **Topics Needing Review**\nBackpropagation Math, Gradient Descent")
        st.info("💡 **Recommended Next**\nMulti-Modal Learning, Vision Transformers")


def show_source_charts():
    """Show source performance analytics."""
    st.subheader("Source Performance")

    # Mock source data
    sources = [
        "Lilian Weng's Blog",
        "Distill.pub",
        "Papers with Code",
        "ArXiv ML",
        "Hugging Face Blog",
    ]
    insights_count = [45, 32, 28, 22, 15]
    helpful_rate = [92, 88, 85, 78, 90]

    df_sources = pd.DataFrame({
        "Source": sources,
        "Insights": insights_count,
        "Helpful Rate %": helpful_rate,
    })

    # Insights per source
    fig_sources = px.bar(
        df_sources,
        x="Insights",
        y="Source",
        orientation="h",
        color="Helpful Rate %",
        color_continuous_scale="RdYlGn",
        text="Insights",
    )

    fig_sources.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#1a1a1a",
        font=dict(color="#ffffff"),
        height=350,
    )

    fig_sources.update_traces(textposition="outside")

    st.plotly_chart(fig_sources, use_container_width=True)

    # Source table
    st.subheader("Detailed Source Stats")

    df_sources["Priority"] = [5, 5, 4, 4, 5]
    df_sources["Active"] = [True, True, True, True, True]

    st.dataframe(
        df_sources,
        use_container_width=True,
        hide_index=True,
    )
