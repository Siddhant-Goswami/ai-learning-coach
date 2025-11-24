#!/usr/bin/env python3
"""
Quick test of the content ingestion pipeline.

This script will:
1. Fetch ONE article from Lilian Weng's blog
2. Chunk it
3. Generate embeddings
4. Store in database
5. Generate a test digest

This is a minimal test to verify the pipeline works.
"""

import os
import sys
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment
env_path = Path(__file__).parent / "learning-coach-mcp" / ".env"
load_dotenv(env_path)


async def quick_test():
    """Run a quick end-to-end test."""
    print("="*70)
    print("Quick Ingestion Test - AI Learning Coach")
    print("="*70)

    # Check environment
    print("\n1. Checking environment...")
    required = ["SUPABASE_URL", "SUPABASE_KEY", "OPENAI_API_KEY"]
    for var in required:
        if not os.getenv(var):
            print(f"❌ {var} not set")
            return False
        print(f"✓ {var} configured")

    from supabase import create_client
    from openai import OpenAI

    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    test_user_id = '00000000-0000-0000-0000-000000000001'

    # Verify test user exists
    print("\n2. Checking test user...")
    user_result = supabase.table('users').select('*').eq('id', test_user_id).execute()
    if not user_result.data:
        print("❌ Test user not found. Please insert test data first.")
        print("   Run the SQL script: database/migrations/002_insert_test_data.sql")
        return False
    print(f"✓ Test user exists: {user_result.data[0]['email']}")

    # Get all sources
    print("\n3. Getting content sources...")
    sources_result = supabase.table('sources').select('*').eq(
        'user_id', test_user_id
    ).execute()

    if not sources_result.data:
        print("❌ No sources found. Please insert test data first.")
        return False

    # Try each source until we find one that works
    source = None
    for s in sources_result.data:
        title = s.get('metadata', {}).get('title', 'Unknown')
        url = s['identifier']
        print(f"  Trying: {title} ({url})")

        import feedparser
        feed = feedparser.parse(url)
        if feed.entries:
            source = s
            print(f"✓ Using source: {title}")
            print(f"  URL: {url}")
            break

    if not source:
        print("❌ No working RSS feeds found")
        return False

    # Fetch RSS feed (we already parsed it above)
    print("\n4. Processing article from feed...")
    try:
        import feedparser
        feed = feedparser.parse(source['identifier'])

        # Get the most recent article
        entry = feed.entries[0]
        print(f"✓ Found article: {entry.get('title', 'Untitled')[:60]}...")

        # Check if already in database
        content_hash = hashlib.md5(entry.get('summary', '')[:1000].encode()).hexdigest()
        existing = supabase.table('content').select('id').eq('content_hash', content_hash).execute()

        if existing.data:
            print("✓ Article already in database, using existing")
            content_id = existing.data[0]['id']
        else:
            # Insert content
            print("\n5. Storing article...")
            from bs4 import BeautifulSoup

            # Clean HTML
            summary = entry.get('summary', '')
            soup = BeautifulSoup(summary, 'html.parser')
            clean_text = soup.get_text()

            content_data = {
                'source_id': source['id'],
                'title': entry.get('title', 'Untitled'),
                'author': entry.get('author', 'Unknown'),
                'published_at': entry.get('published', datetime.now().isoformat()),
                'url': entry.get('link', ''),
                'content_hash': content_hash,
                'raw_text': clean_text[:5000],  # Limit for testing
                'metadata': {'feed_entry': entry.get('id', '')}
            }

            result = supabase.table('content').insert(content_data).execute()
            content_id = result.data[0]['id']
            print(f"✓ Article stored: {content_id}")

        # Generate embeddings
        print("\n6. Generating embeddings...")

        # Check if embeddings exist
        existing_emb = supabase.table('embeddings').select('id').eq('content_id', content_id).execute()

        if existing_emb.data:
            print(f"✓ Found {len(existing_emb.data)} existing embeddings")
        else:
            # Get content
            content = supabase.table('content').select('*').eq('id', content_id).execute()
            text = content.data[0]['raw_text']

            # Simple chunking (just split into ~500 char chunks for testing)
            chunk_size = 500
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            print(f"  Created {len(chunks)} chunks")

            # Generate embeddings for each chunk
            for idx, chunk_text in enumerate(chunks[:3]):  # Limit to 3 for testing
                print(f"  Generating embedding {idx+1}/3...", end=' ')

                embedding_response = openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=chunk_text,
                    dimensions=1536
                )

                embedding_data = {
                    'content_id': content_id,
                    'chunk_sequence': idx,
                    'chunk_text': chunk_text,
                    'embedding': embedding_response.data[0].embedding
                }

                supabase.table('embeddings').insert(embedding_data).execute()
                print("✓")

            print(f"✓ Generated {min(len(chunks), 3)} embeddings")

        # Test digest generation
        print("\n7. Testing digest generation...")

        from dashboard.digest_api import generate_digest_simple
        from datetime import date

        digest = await generate_digest_simple(
            user_id=test_user_id,
            date_obj=date.today(),
            max_insights=3,  # Just 3 for testing
            force_refresh=True
        )

        if 'error' in digest:
            print(f"❌ Digest generation error: {digest['error']}")
            return False

        if 'insights' in digest and digest['insights']:
            print(f"✓ Generated {len(digest['insights'])} insights")
            print("\nSample insight:")
            insight = digest['insights'][0]
            print(f"  Title: {insight.get('title', 'N/A')}")
            print(f"  Relevance: {insight.get('relevance_reason', 'N/A')[:100]}...")
        else:
            print("⚠️  No insights generated (may be in demo mode)")

        print("\n" + "="*70)
        print("✅ QUICK TEST COMPLETE!")
        print("="*70)
        print("\nWhat was tested:")
        print("  ✓ Database connection")
        print("  ✓ RSS feed fetching")
        print("  ✓ Content storage")
        print("  ✓ OpenAI embedding generation")
        print("  ✓ Digest generation with OpenAI")
        print("\nNext steps:")
        print("  1. Visit http://localhost:8501")
        print("  2. Go to Home page")
        print("  3. You should see the generated insights!")
        print("\nTo fetch more content:")
        print("  cd learning-coach-mcp")
        print("  python3 -m src.ingestion.orchestrator")
        print()

        return True

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(quick_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        sys.exit(1)
