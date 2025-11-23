"""
AI Learning Coach - Streamlit Dashboard

Main dashboard application providing web interface for:
- Daily digest viewing
- Past insights search
- Learning analytics
- Settings and preferences
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "learning-coach-mcp"))

from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Learning Coach",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark theme
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #1a1a1a;
        border-right: 1px solid #333333;
    }

    /* Cards */
    .insight-card {
        background: #1a1a1a;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }

    /* Metrics */
    div[data-testid="stMetricValue"] {
        color: #3b82f6;
        font-size: 32px;
    }

    /* Buttons */
    .stButton>button {
        background-color: #3b82f6;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 16px;
        font-weight: 500;
    }

    .stButton>button:hover {
        background-color: #2563eb;
    }

    /* Headers */
    h1, h2, h3 {
        color: #ffffff;
    }

    /* Text */
    p, span, label {
        color: #a0a0a0;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1a1a;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")

if 'current_digest' not in st.session_state:
    st.session_state.current_digest = None

if 'learning_context' not in st.session_state:
    st.session_state.learning_context = None

# Sidebar navigation
with st.sidebar:
    st.title("🎓 AI Learning Coach")
    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        ["🏠 Today's Digest", "🔍 Search", "📊 Analytics", "⚙️ Settings"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Current progress (mock data for now)
    st.markdown("### 📈 Your Progress")
    week_num = 7
    total_weeks = 24
    progress = week_num / total_weeks

    st.metric("Current Week", f"{week_num} / {total_weeks}")
    st.progress(progress)
    st.caption(f"{progress * 100:.1f}% Complete")

    st.markdown("---")

    # Quick stats
    st.markdown("### 📊 Quick Stats")
    st.metric("This Week", "42 insights", delta="+7")
    st.metric("Helpful Rate", "85%", delta="+3%")

    st.markdown("---")
    st.caption("Built with ❤️ using Claude & MCP")

# Main content area
if page == "🏠 Today's Digest":
    from pages import home
    home.show()

elif page == "🔍 Search":
    from pages import search
    search.show()

elif page == "📊 Analytics":
    from pages import analytics
    analytics.show()

elif page == "⚙️ Settings":
    from pages import settings
    settings.show()
