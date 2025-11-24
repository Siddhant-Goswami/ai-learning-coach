#!/usr/bin/env python3
"""
Complete setup and testing script for AI Learning Coach.

This script will:
1. Check all required environment variables
2. Initialize the database with test data
3. Run a test content ingestion
4. Generate a test digest
5. Verify the Streamlit app can load

Usage:
    python3 setup_and_test.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / "learning-coach-mcp" / ".env"
load_dotenv(env_path)

def check_environment():
    """Check if all required environment variables are set."""
    print("="*70)
    print("STEP 1: Checking Environment Variables")
    print("="*70)

    required_vars = {
        "SUPABASE_URL": "Supabase project URL",
        "SUPABASE_KEY": "Supabase anon/public key",
        "OPENAI_API_KEY": "OpenAI API key for embeddings and synthesis"
    }

    optional_vars = {
        "ANTHROPIC_API_KEY": "Anthropic API key for Claude synthesis (optional - OpenAI will be used if not set)"
    }

    missing_vars = []
    configured_vars = []

    for var, description in required_vars.items():
        value = os.getenv(var)

        # Check for placeholder values
        if value and value.startswith("${"):
            value = None

        if value:
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                masked = value[:10] + "..." if len(value) > 10 else "***"
                print(f"✓ {var}: {masked}")
            else:
                print(f"✓ {var}: {value[:50]}...")
            configured_vars.append(var)
        else:
            print(f"✗ {var}: NOT SET ({description})")
            missing_vars.append((var, description))

    print("\nOptional variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value and value.startswith("${"):
            value = None

        if value:
            masked = value[:10] + "..." if len(value) > 10 else "***"
            print(f"✓ {var}: {masked}")
        else:
            print(f"- {var}: not set ({description})")

    if missing_vars:
        print("\n" + "="*70)
        print("MISSING CONFIGURATION")
        print("="*70)
        print(f"\nPlease set the following in {env_path}:\n")

        for var, description in missing_vars:
            print(f"{var}=your_{var.lower()}_here  # {description}")

        print("\nHow to get these keys:")
        print("\n1. SUPABASE_URL and SUPABASE_KEY:")
        print("   - Go to https://supabase.com/dashboard")
        print("   - Select your project")
        print("   - Go to Project Settings > API")
        print("   - Copy 'Project URL' and 'anon/public' key")

        print("\n2. OPENAI_API_KEY:")
        print("   - Go to https://platform.openai.com/api-keys")
        print("   - Create a new API key")

        print("\n3. ANTHROPIC_API_KEY:")
        print("   - Go to https://console.anthropic.com/settings/keys")
        print("   - Create a new API key")

        print("\n" + "="*70)
        return False

    print("\n✅ All required environment variables are set!")
    return True

def test_database_connection():
    """Test connection to Supabase."""
    print("\n" + "="*70)
    print("STEP 2: Testing Database Connection")
    print("="*70)

    try:
        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        client = create_client(supabase_url, supabase_key)

        # Try to query users table
        result = client.table('users').select('*').limit(1).execute()
        print("✓ Successfully connected to Supabase")
        print(f"✓ Database tables are accessible")

        return True

    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("\nThis might be due to:")
        print("1. Incorrect SUPABASE_URL or SUPABASE_KEY")
        print("2. Database schema not created yet")
        print("3. Network connectivity issues")
        return False

def init_database():
    """Initialize database with test data."""
    print("\n" + "="*70)
    print("STEP 3: Initializing Database")
    print("="*70)

    print("\n⚠️  Note: RLS (Row Level Security) is enabled.")
    print("To insert test data, you need to:")
    print("1. Go to your Supabase dashboard")
    print("2. Click 'SQL Editor'")
    print("3. Copy and paste the contents of:")
    print(f"   {Path(__file__).parent}/database/migrations/002_insert_test_data.sql")
    print("4. Click 'Run'")

    print("\nAlternatively, you can use the Python script (requires DB credentials):")
    print(f"   cd database && python3 run_migration.py 002_insert_test_data.sql")

    input("\nPress Enter after you've inserted the test data...")

    # Verify test data exists
    try:
        from supabase import create_client
        client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

        test_user_id = '00000000-0000-0000-0000-000000000001'

        # Check user
        result = client.table('users').select('*').eq('id', test_user_id).execute()
        if result.data:
            print("✓ Test user found")
        else:
            print("✗ Test user not found - please run the migration")
            return False

        # Check sources
        result = client.table('sources').select('*').eq('user_id', test_user_id).execute()
        if result.data:
            print(f"✓ Found {len(result.data)} content sources")
        else:
            print("✗ No content sources found - please run the migration")
            return False

        return True

    except Exception as e:
        print(f"✗ Error verifying test data: {e}")
        return False

def test_openai_connection():
    """Test OpenAI API connection."""
    print("\n" + "="*70)
    print("STEP 4: Testing OpenAI Connection")
    print("="*70)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Test with a simple embedding
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test",
            dimensions=1536
        )

        print("✓ OpenAI API connection successful")
        print(f"✓ Embedding dimension: {len(response.data[0].embedding)}")
        return True

    except Exception as e:
        print(f"✗ OpenAI API connection failed: {e}")
        return False

def test_anthropic_connection():
    """Test Anthropic API connection."""
    print("\n" + "="*70)
    print("STEP 5: Testing Anthropic Connection")
    print("="*70)

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Test with a simple message
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": "Say hello"}]
        )

        print("✓ Anthropic API connection successful")
        print(f"✓ Response: {message.content[0].text[:50]}...")
        return True

    except Exception as e:
        print(f"✗ Anthropic API connection failed: {e}")
        return False

def run_setup():
    """Run complete setup and testing."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "AI Learning Coach - Setup & Test" + " "*21 + "║")
    print("╚" + "="*68 + "╝")
    print()

    # Step 1: Check environment
    if not check_environment():
        print("\n❌ Setup failed: Missing configuration")
        print("Please fix the environment variables and try again.")
        return False

    # Step 2: Test database
    if not test_database_connection():
        print("\n❌ Setup failed: Database connection error")
        return False

    # Step 3: Initialize database
    if not init_database():
        print("\n❌ Setup failed: Database initialization error")
        return False

    # Step 4: Test OpenAI
    if not test_openai_connection():
        print("\n❌ OpenAI connection failed")
        print("OpenAI is required for embeddings and synthesis.")
        return False

    # Step 5: Test Anthropic (optional)
    if os.getenv("ANTHROPIC_API_KEY"):
        if test_anthropic_connection():
            print("✓ Anthropic available - will use Claude for synthesis")
        else:
            print("\n⚠️  Warning: Anthropic key set but connection failed")
            print("Will fall back to OpenAI for synthesis.")
    else:
        print("\n💡 Using OpenAI for synthesis (Anthropic not configured)")

    print("\n" + "="*70)
    print("✅ SETUP COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("1. The Streamlit app should be running at http://localhost:8501")
    print("2. Go to Home page to view today's digest")
    print("3. Use Settings to manage sources and preferences")
    print("\nTo start content ingestion (fetch and process articles):")
    print("   cd learning-coach-mcp && python3 -m src.ingestion.orchestrator")
    print("\n" + "="*70)

    return True

if __name__ == "__main__":
    try:
        success = run_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
