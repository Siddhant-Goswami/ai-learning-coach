"""
AI Learning Coach - Streamlit Dashboard

Simplified dashboard showing daily learning digest.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
learning_coach_path = Path(__file__).parent.parent / "learning-coach-mcp"
src_path = learning_coach_path / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(learning_coach_path))

from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

# Set defaults if not found
if not os.getenv("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://hkwuyxqltunphmbmqpsm.supabase.co"
if not os.getenv("SUPABASE_KEY"):
    os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imhrd3V5eHFsdHVucGhtYm1xcHNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4OTY2NTAsImV4cCI6MjA3OTQ3MjY1MH0.aGQwSmxrqzTd6M30BkIuGSIiGQAnF-Cb46vJbcw2AoA"
if not os.getenv("DEFAULT_USER_ID"):
    os.environ["DEFAULT_USER_ID"] = "00000000-0000-0000-0000-000000000001"

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
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff;
    }

    section[data-testid="stSidebar"] {
        background-color: #1a1a1a;
        border-right: 1px solid #333333;
    }

    .insight-card {
        background: #1a1a1a;
        border: 1px solid #333333;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
    }

    div[data-testid="stMetricValue"] {
        color: #3b82f6;
        font-size: 28px;
    }

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

    h1, h2, h3 {
        color: #ffffff;
    }

    p, span, label {
        color: #a0a0a0;
    }

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

# Sidebar
with st.sidebar:
    st.title("🎓 AI Learning Coach")
    st.markdown("---")

    # Navigation
    page = st.radio(
        "Navigation",
        ["📚 Today's Digest", "⚙️ Settings"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Get progress from database
    try:
        from supabase import create_client
        client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        result = client.table('learning_progress').select('*').eq(
            'user_id', st.session_state.user_id
        ).execute()

        if result.data:
            progress_data = result.data[0]
            week_num = progress_data.get('current_week', 7)
            topics = progress_data.get('current_topics', [])

            st.markdown("### 📈 Your Progress")
            total_weeks = 24
            progress = week_num / total_weeks

            st.metric("Current Week", f"{week_num} / {total_weeks}")
            st.progress(progress)
            st.caption(f"{progress * 100:.1f}% Complete")

            st.markdown("---")
            st.markdown("### 📖 Current Focus")
            for topic in topics[:3]:
                st.caption(f"• {topic}")
        else:
            st.markdown("### 📈 Your Progress")
            st.caption("No progress data available")
    except Exception as e:
        st.markdown("### 📈 Your Progress")
        st.caption("Unable to load progress")

    st.markdown("---")
    st.caption("Powered by OpenAI GPT-4o-mini")

# Main content area
if page == "📚 Today's Digest":
    from views import home
    home.show()

elif page == "⚙️ Settings":
    from views import settings
    settings.show()
