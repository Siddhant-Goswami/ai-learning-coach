"""
Settings Page - Simplified version with better error handling
"""

import streamlit as st
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent.parent.parent / "learning-coach-mcp" / ".env"
load_dotenv(env_path)


def show():
    """Render the settings page."""
    st.title("⚙️ Settings")

    tab1, tab2, tab3 = st.tabs(["📖 Learning Context", "📚 Sources", "🔧 System"])

    with tab1:
        show_learning_context()

    with tab2:
        show_sources()

    with tab3:
        show_system_info()


def show_learning_context():
    """Show and edit learning context."""
    st.markdown("### Your Learning Context")

    from supabase import create_client

    try:
        client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        # Get learning progress
        progress_data = None
        try:
            result = client.table('learning_progress').select(
                'current_week, difficulty_level, current_topics, learning_goals'
            ).eq('user_id', st.session_state.user_id).limit(1).execute()

            if result.data and len(result.data) > 0:
                progress_data = result.data[0]
        except Exception as e:
            st.warning(f"Could not load existing data: {str(e)}")

        # Current Week
        st.markdown("#### 📅 Current Week")
        current_week = st.number_input(
            "Week Number",
            min_value=1,
            max_value=24,
            value=progress_data.get('current_week', 7) if progress_data else 7,
            help="Your current week in the bootcamp (1-24)"
        )

        # Difficulty Level
        st.markdown("#### 📊 Difficulty Level")
        difficulty_options = ['beginner', 'intermediate', 'advanced']
        current_diff = progress_data.get('difficulty_level', 'intermediate') if progress_data else 'intermediate'

        try:
            diff_index = difficulty_options.index(current_diff)
        except ValueError:
            diff_index = 1

        difficulty = st.selectbox(
            "Select your learning level",
            options=difficulty_options,
            index=diff_index
        )

        # Current Topics
        st.markdown("#### 📝 Current Topics")
        current_topics = progress_data.get('current_topics', []) if progress_data else []

        topics_text = st.text_area(
            "Topics (one per line)",
            value="\n".join(current_topics) if current_topics else "Attention Mechanisms\nTransformers\nMulti-Head Attention",
            height=150,
            help="Enter each topic on a new line"
        )

        # Learning Goals
        st.markdown("#### 🎯 Learning Goals")
        current_goals = progress_data.get('learning_goals', '') if progress_data else ''

        learning_goals = st.text_area(
            "What do you want to build or achieve?",
            value=current_goals if current_goals else "Build a chatbot with RAG",
            height=100
        )

        # Save button
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            topics_list = [t.strip() for t in topics_text.split('\n') if t.strip()]

            try:
                # Try update first
                update_data = {
                    'current_week': current_week,
                    'difficulty_level': difficulty,
                    'current_topics': topics_list,
                    'learning_goals': learning_goals,
                }

                result = client.table('learning_progress').update(update_data).eq(
                    'user_id', st.session_state.user_id
                ).execute()

                if result.data:
                    st.success("✓ Learning context saved!")
                    st.balloons()
                else:
                    # Try insert if update didn't work
                    insert_data = update_data.copy()
                    insert_data['user_id'] = st.session_state.user_id

                    client.table('learning_progress').insert(insert_data).execute()
                    st.success("✓ Learning context created!")
                    st.balloons()

                # Wait a moment then rerun
                import time
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"Error saving: {str(e)}")
                st.info("💡 Try refreshing the page and trying again")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.info("💡 Check your database connection in the System tab")


def show_sources():
    """Show content sources."""
    st.markdown("### 📚 Content Sources")

    from supabase import create_client

    try:
        client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        result = client.table('sources').select('*').eq(
            'user_id', st.session_state.user_id
        ).execute()

        if result.data and len(result.data) > 0:
            st.markdown(f"**{len(result.data)} sources configured**")
            st.markdown("---")

            for idx, source in enumerate(result.data):
                metadata = source.get('metadata', {})
                title = metadata.get('title', 'Unknown Source')
                url = source['identifier']
                priority = source.get('priority', 3)
                active = source.get('active', True)
                source_type = source.get('type', 'rss')

                with st.expander(f"{'✅' if active else '⏸️'} {title}"):
                    st.text(f"URL: {url}")
                    st.text(f"Type: {source_type}")
                    st.text(f"Priority: {priority}/5")
                    st.text(f"Status: {'Active' if active else 'Inactive'}")

                    if st.button(f"Toggle Active/Inactive", key=f"toggle_{idx}"):
                        try:
                            client.table('sources').update({
                                'active': not active
                            }).eq('id', source['id']).execute()
                            st.success("✓ Updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
        else:
            st.info("No content sources found")

    except Exception as e:
        st.error(f"Error loading sources: {str(e)}")


def show_system_info():
    """Show system information."""
    st.markdown("### 🔧 System Status")

    # API Configuration
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Database**")
        supabase_url = os.getenv("SUPABASE_URL", "Not set")
        st.code(supabase_url[:50] + "..." if len(supabase_url) > 50 else supabase_url)

    with col2:
        st.markdown("**OpenAI API**")
        openai_key = os.getenv("OPENAI_API_KEY", "")
        st.code("✓ Configured" if openai_key else "✗ Not set")

    st.markdown("---")

    # Database Stats
    st.markdown("### 📊 Database Statistics")

    try:
        from supabase import create_client
        client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        col1, col2, col3 = st.columns(3)

        with col1:
            try:
                count = len(client.table('content').select('id').execute().data)
                st.metric("Articles", count)
            except:
                st.metric("Articles", "?")

        with col2:
            try:
                count = len(client.table('embeddings').select('id').execute().data)
                st.metric("Embeddings", count)
            except:
                st.metric("Embeddings", "?")

        with col3:
            try:
                count = len(client.table('generated_digests').select('id').eq(
                    'user_id', st.session_state.user_id
                ).execute().data)
                st.metric("Digests", count)
            except:
                st.metric("Digests", "?")

    except Exception as e:
        st.error(f"Error loading stats: {e}")

    st.markdown("---")

    # Actions
    st.markdown("### 🔄 Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Today's Digest", use_container_width=True):
            try:
                from datetime import date
                from supabase import create_client

                client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
                today = date.today().isoformat()

                client.table('generated_digests').delete().eq(
                    'user_id', st.session_state.user_id
                ).eq('digest_date', today).execute()

                st.success("✓ Cleared! Go to Home to generate new digest.")
            except Exception as e:
                st.error(f"Error: {e}")

    with col2:
        if st.button("🔄 Refresh This Page", use_container_width=True):
            st.rerun()

    st.markdown("---")
    st.markdown("**AI Learning Coach** v1.0 • Powered by OpenAI GPT-4o-mini")
