#!/usr/bin/env python3
"""Run database migration using Supabase connection."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Try to import psycopg2, install if missing
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("psycopg2-binary is required. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

def get_connection_string():
    """Get PostgreSQL connection string from Supabase credentials."""
    # Try to get connection string directly
    db_url = os.getenv("SUPABASE_DB_URL")
    if db_url:
        # Ensure it starts with postgresql://
        if not db_url.startswith("postgresql://"):
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql://", 1)
            else:
                db_url = f"postgresql://{db_url}"
        return db_url
    
    # Build connection string from individual components
    db_host = os.getenv("SUPABASE_DB_HOST")
    db_port = os.getenv("SUPABASE_DB_PORT", "5432")
    db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
    db_user = os.getenv("SUPABASE_DB_USER", "postgres")
    db_password = os.getenv("SUPABASE_DB_PASSWORD")
    
    if not db_host or not db_password:
        print("\n" + "="*70)
        print("ERROR: Missing database credentials")
        print("="*70)
        print("\nTo get your Supabase database connection string:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to Project Settings > Database")
        print("4. Scroll to 'Connection string' section")
        print("5. Copy the 'URI' or 'Connection pooling' > 'Session mode' connection string")
        print("\nThen set one of these environment variables:")
        print("  - SUPABASE_DB_URL (full connection string)")
        print("  OR set these individually:")
        print("  - SUPABASE_DB_HOST (e.g., db.xxxxx.supabase.co)")
        print("  - SUPABASE_DB_PASSWORD (your database password)")
        print("  - SUPABASE_DB_USER (usually 'postgres')")
        print("  - SUPABASE_DB_NAME (usually 'postgres')")
        print("  - SUPABASE_DB_PORT (usually '5432')")
        print("\nYou can add these to your .env file in learning-coach-mcp/.env")
        print("="*70 + "\n")
        raise ValueError("Missing database credentials")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def run_migration(migration_name="001_initial_schema.sql"):
    """Execute the migration SQL file."""
    # Get the migration file path
    script_dir = Path(__file__).parent
    migration_file = script_dir / "migrations" / migration_name

    if not migration_file.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_file}")

    # Read the SQL file
    with open(migration_file, "r") as f:
        sql_content = f.read()
    
    # Get connection string
    try:
        conn_string = get_connection_string()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Connect to database
    try:
        print("Connecting to Supabase database...")
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("Executing migration...")
        # Execute the SQL (split by semicolons for better error handling)
        # But first, let's execute it as a whole to preserve DO blocks
        cursor.execute(sql_content)
        
        print("Migration completed successfully!")
        print("\nDatabase schema created with:")
        print("  - Tables: users, sources, content, embeddings, feedback, generated_digests, learning_progress")
        print("  - Indexes: Vector similarity search, B-tree, and GIN indexes")
        print("  - RLS policies: Row-level security enabled")
        print("  - Functions: match_embeddings, update_source_health")
        print("  - Test data: Default test user and learning progress")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument(
        "migration",
        nargs="?",
        default="001_initial_schema.sql",
        help="Migration file name (default: 001_initial_schema.sql)"
    )

    args = parser.parse_args()
    run_migration(args.migration)

