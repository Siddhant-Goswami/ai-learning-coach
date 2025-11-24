#!/usr/bin/env python3
"""
Initialize test data in the database.

This script needs to be run with the SERVICE_ROLE_KEY (not anon key) to bypass RLS.
Get your service role key from: Supabase Dashboard > Settings > API > service_role key

Usage:
    SUPABASE_SERVICE_KEY=your_service_role_key python3 init_test_data.py
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../learning-coach-mcp/.env")

def init_database():
    """Initialize database with test data."""
    try:
        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL")
        # Try service key first, fall back to regular key
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set")
            return False

        # Check if we're using service key
        if not os.getenv("SUPABASE_SERVICE_KEY"):
            print("⚠️  Warning: Using anon key. May encounter RLS errors.")
            print("   For full access, set SUPABASE_SERVICE_KEY environment variable")
            print()

        client = create_client(supabase_url, supabase_key)

        test_user_id = '00000000-0000-0000-0000-000000000001'

        # Check if user already exists
        print("Checking for existing test user...")
        result = client.table('users').select('*').eq('id', test_user_id).execute()

        if result.data:
            print(f"✓ Test user already exists: {result.data[0]['email']}")
        else:
            # Create test user
            print("Creating test user...")
            try:
                result = client.table('users').insert({
                    'id': test_user_id,
                    'email': 'test@example.com',
                    'metadata': {'role': 'test_user'}
                }).execute()
                print('✓ Test user created')
            except Exception as e:
                if 'row-level security' in str(e).lower():
                    print(f"❌ RLS Error: {e}")
                    print("\n💡 Solution: You need to use the SERVICE_ROLE_KEY")
                    print("   Get it from: Supabase Dashboard > Settings > API")
                    print("   Run: SUPABASE_SERVICE_KEY=your_key python3 init_test_data.py")
                    return False
                else:
                    print(f"❌ Error creating user: {e}")
                    return False

        # Create learning progress
        print("Creating learning progress...")
        try:
            # Check if exists
            result = client.table('learning_progress').select('*').eq('user_id', test_user_id).execute()
            if result.data:
                print('✓ Learning progress already exists')
            else:
                result = client.table('learning_progress').insert({
                    'user_id': test_user_id,
                    'current_week': 7,
                    'current_topics': ['Attention Mechanisms', 'Transformers', 'Multi-Head Attention'],
                    'difficulty_level': 'intermediate',
                    'learning_goals': 'Build chatbot with RAG'
                }).execute()
                print('✓ Learning progress created')
        except Exception as e:
            print(f"Error with learning progress: {e}")

        # Add test content sources
        print("\nCreating test sources...")
        test_sources = [
            {
                'user_id': test_user_id,
                'type': 'rss',
                'identifier': 'https://lilianweng.github.io/index.xml',
                'priority': 5,
                'active': True,
                'metadata': {'title': 'Lilian Weng\'s Blog', 'description': 'ML research and insights'}
            },
            {
                'user_id': test_user_id,
                'type': 'rss',
                'identifier': 'https://distill.pub/rss.xml',
                'priority': 5,
                'active': True,
                'metadata': {'title': 'Distill.pub', 'description': 'Clear explanations of ML concepts'}
            },
            {
                'user_id': test_user_id,
                'type': 'rss',
                'identifier': 'https://huggingface.co/blog/feed.xml',
                'priority': 4,
                'active': True,
                'metadata': {'title': 'Hugging Face Blog', 'description': 'Latest in NLP and transformers'}
            }
        ]

        for source in test_sources:
            try:
                # Check if exists
                result = client.table('sources').select('*').eq(
                    'user_id', test_user_id
                ).eq('identifier', source['identifier']).execute()

                if result.data:
                    print(f'✓ Source already exists: {source["metadata"]["title"]}')
                else:
                    result = client.table('sources').insert(source).execute()
                    print(f'✓ Created source: {source["metadata"]["title"]}')
            except Exception as e:
                print(f'❌ Error creating source {source["metadata"]["title"]}: {e}')

        print("\n" + "="*50)
        print("✅ Database initialization complete!")
        print("="*50)
        print(f"\nTest User ID: {test_user_id}")
        print("Next steps:")
        print("1. Run content ingestion to fetch and process articles")
        print("2. Generate embeddings for the content")
        print("3. Test the digest generation in the Streamlit app")

        return True

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
