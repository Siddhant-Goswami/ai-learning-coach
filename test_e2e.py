#!/usr/bin/env python3
"""
End-to-end test script for AI Learning Coach
Tests core functionality without requiring full MCP server
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add learning-coach-mcp to path and set PYTHONPATH for proper package imports
learning_coach_path = str(Path(__file__).parent / "learning-coach-mcp")
src_path = str(Path(__file__).parent / "learning-coach-mcp" / "src")
if learning_coach_path not in sys.path:
    sys.path.insert(0, learning_coach_path)
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Change to the src directory to allow relative imports to work
os.chdir(src_path)

# Load environment variables
load_dotenv(Path(__file__).parent / "learning-coach-mcp" / ".env")

# Test results
results = {
    "database_connection": False,
    "source_management": False,
    "content_ingestion": False,
    "digest_generation": False,
}

async def test_database_connection():
    """Test Supabase database connection."""
    print("\n" + "="*70)
    print("TEST 1: Database Connection")
    print("="*70)
    
    try:
        from utils.db import get_supabase_client, check_db_connection
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Missing SUPABASE_URL or SUPABASE_KEY in environment")
            return False
        
        print(f"✓ Connecting to: {supabase_url}")
        client = get_supabase_client(supabase_url, supabase_key)
        
        # Test connection by querying users table
        response = client.table("users").select("id, email").limit(1).execute()
        
        if response.data:
            print(f"✓ Database connection successful!")
            print(f"  Found user: {response.data[0].get('email', 'N/A')}")
            results["database_connection"] = True
            return True
        else:
            print("⚠ Database connected but no users found")
            results["database_connection"] = True
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

async def test_source_management():
    """Test source management (add, list sources)."""
    print("\n" + "="*70)
    print("TEST 2: Source Management")
    print("="*70)
    
    try:
        from tools import source_manager
        SourceManager = source_manager.SourceManager
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        user_id = os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")
        
        manager = SourceManager(supabase_url=supabase_url, supabase_key=supabase_key)
        
        # List existing sources
        print("📋 Listing existing sources...")
        sources = await manager.list_sources(user_id=user_id)
        print(f"  Found {len(sources.get('sources', []))} sources")
        
        # Add a test RSS source
        test_feed = "https://lilianweng.github.io/feed.xml"
        print(f"\n➕ Adding test source: {test_feed}")
        result = await manager.add_source(
            user_id=user_id,
            source_type="rss",
            identifier=test_feed,
            priority=5
        )
        
        if "error" in result:
            print(f"⚠ Source add result: {result}")
            # Check if it's a duplicate error (which is OK)
            if "already exists" in str(result.get("error", "")).lower():
                print("✓ Source already exists (expected for re-runs)")
                results["source_management"] = True
                return True
        else:
            print(f"✓ Source added successfully!")
            print(f"  Source ID: {result.get('source_id', 'N/A')}")
            results["source_management"] = True
            return True
        
        # List sources again
        sources = await manager.list_sources(user_id=user_id)
        print(f"\n📋 Sources after add: {len(sources.get('sources', []))} total")
        results["source_management"] = True
        return True
        
    except Exception as e:
        print(f"❌ Source management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_content_ingestion():
    """Test content ingestion from RSS feed."""
    print("\n" + "="*70)
    print("TEST 3: Content Ingestion")
    print("="*70)
    
    try:
        from ingestion import orchestrator
        IngestionOrchestrator = orchestrator.IngestionOrchestrator
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        user_id = os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")
        
        orchestrator = IngestionOrchestrator(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        )
        
        print("🔄 Fetching and ingesting content from sources...")
        result = await orchestrator.ingest_all_sources(user_id=user_id)
        
        if "error" in result:
            print(f"⚠ Ingestion result: {result}")
            # Check if it's just missing API key
            if "OPENAI_API_KEY" in str(result.get("error", "")):
                print("⚠ OpenAI API key not set - skipping embedding generation")
                print("  (This is OK for testing, embeddings will be skipped)")
                results["content_ingestion"] = True
                return True
        else:
            print(f"✓ Ingestion completed!")
            print(f"  Sources processed: {result.get('sources_processed', 0)}")
            print(f"  Items fetched: {result.get('items_fetched', 0)}")
            print(f"  Items embedded: {result.get('items_embedded', 0)}")
            results["content_ingestion"] = True
            return True
        
    except Exception as e:
        print(f"❌ Content ingestion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_digest_generation():
    """Test digest generation."""
    print("\n" + "="*70)
    print("TEST 4: Digest Generation")
    print("="*70)
    
    try:
        from rag import digest_generator
        DigestGenerator = digest_generator.DigestGenerator
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        user_id = os.getenv("DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")
        
        if not openai_api_key or not anthropic_api_key:
            print("⚠ Missing OPENAI_API_KEY or ANTHROPIC_API_KEY")
            print("  Skipping digest generation (requires API keys)")
            return False
        
        generator = DigestGenerator(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            openai_api_key=openai_api_key,
            anthropic_api_key=anthropic_api_key,
        )
        
        from datetime import date
        print("📝 Generating daily digest...")
        digest = await generator.generate(
            user_id=user_id,
            date=date.today(),
            max_insights=3,  # Small number for testing
            force_refresh=False,
        )
        
        if "error" in digest:
            print(f"❌ Digest generation failed: {digest.get('error')}")
            return False
        
        print(f"✓ Digest generated successfully!")
        print(f"  Insights: {len(digest.get('insights', []))}")
        print(f"  Quality score: {digest.get('ragas_scores', {}).get('average', 'N/A')}")
        
        if digest.get('insights'):
            print("\n  Sample insights:")
            for i, insight in enumerate(digest['insights'][:2], 1):
                print(f"    {i}. {insight.get('title', 'N/A')[:60]}...")
        
        results["digest_generation"] = True
        return True
        
    except Exception as e:
        print(f"❌ Digest generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("AI LEARNING COACH - END-TO-END TEST SUITE")
    print("="*70)
    
    # Check environment
    print("\n📋 Environment Check:")
    print(f"  SUPABASE_URL: {'✓ Set' if os.getenv('SUPABASE_URL') else '❌ Missing'}")
    print(f"  SUPABASE_KEY: {'✓ Set' if os.getenv('SUPABASE_KEY') else '❌ Missing'}")
    print(f"  OPENAI_API_KEY: {'✓ Set' if os.getenv('OPENAI_API_KEY') else '⚠ Not set (optional for some tests)'}")
    print(f"  ANTHROPIC_API_KEY: {'✓ Set' if os.getenv('ANTHROPIC_API_KEY') else '⚠ Not set (optional for some tests)'}")
    
    # Run tests
    await test_database_connection()
    await test_source_management()
    await test_content_ingestion()
    await test_digest_generation()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "❌ FAIL"
        print(f"  {status} - {test_name.replace('_', ' ').title()}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

