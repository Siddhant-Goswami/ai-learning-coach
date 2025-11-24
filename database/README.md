# Database Setup Guide

This guide explains how to set up the AI Learning Coach database in Supabase.

## Option 1: Using Supabase MCP (Recommended for AI-assisted setup)

Supabase MCP allows AI assistants to interact directly with your Supabase project. To set it up:

### Setup Steps:

1. **Get your Supabase Personal Access Token:**
   - Go to https://supabase.com/dashboard/account/tokens
   - Click "Generate new token"
   - Copy the token (you'll need it for MCP configuration)

2. **Configure Supabase MCP in Cursor:**
   - The MCP server can be configured to run via npx
   - Add to your Cursor MCP configuration:
   ```json
   {
     "mcpServers": {
       "supabase": {
         "command": "npx",
         "args": [
           "-y",
           "@supabase/mcp-server-supabase@latest",
           "--access-token",
           "<your-personal-access-token>"
         ]
       }
     }
   }
   ```

3. **Once configured, you can use Supabase MCP tools to:**
   - Create projects
   - Execute SQL migrations
   - Manage database schema
   - Query data

## Option 2: Using Migration Script (Direct PostgreSQL Connection)

If you prefer to run the migration directly:

### Prerequisites:
- Python 3.11+
- psycopg2-binary (will be installed automatically if missing)
- Supabase database credentials

### Steps:

1. **Get your Supabase database connection string:**
   - Go to https://supabase.com/dashboard
   - Select your project
   - Go to **Project Settings** > **Database**
   - Scroll to **Connection string** section
   - Copy the **URI** connection string (or use Connection pooling > Session mode)
   - It should look like: `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres`

2. **Set up environment variables:**
   
   Create or update `learning-coach-mcp/.env`:
   ```bash
   # Option A: Full connection string
   SUPABASE_DB_URL=postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres
   
   # Option B: Individual components
   SUPABASE_DB_HOST=db.xxxxx.supabase.co
   SUPABASE_DB_PORT=5432
   SUPABASE_DB_NAME=postgres
   SUPABASE_DB_USER=postgres
   SUPABASE_DB_PASSWORD=your_password_here
   ```

3. **Run the migration:**
   ```bash
   cd database
   python run_migration.py
   ```

## Option 3: Using Supabase SQL Editor (Manual)

1. Go to your Supabase project dashboard
2. Click **SQL Editor** in the left sidebar
3. Click **New Query**
4. Open `database/migrations/001_initial_schema.sql`
5. Copy the entire contents
6. Paste into the SQL Editor
7. Click **Run**

## What Gets Created

The migration creates:

- **Tables:**
  - `users` - User profiles
  - `sources` - Content sources (RSS, Twitter, etc.)
  - `content` - Raw content items
  - `embeddings` - Vector embeddings for RAG
  - `feedback` - User feedback on insights
  - `generated_digests` - Cached daily digests
  - `learning_progress` - Learning state backup

- **Indexes:**
  - HNSW vector index for similarity search
  - B-tree indexes for common queries
  - GIN indexes for JSONB metadata

- **Security:**
  - Row Level Security (RLS) enabled on all tables
  - RLS policies for multi-tenant isolation

- **Functions:**
  - `match_embeddings()` - Vector similarity search
  - `update_source_health()` - Source health tracking

- **Test Data:**
  - Default test user (ID: `00000000-0000-0000-0000-000000000001`)
  - Sample learning progress

## Verification

After running the migration, verify it worked:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check pgvector extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check test user
SELECT * FROM users WHERE email = 'test@example.com';
```

## Troubleshooting

### "Extension vector does not exist"
- Enable the pgvector extension in Supabase:
  - Go to SQL Editor
  - Run: `CREATE EXTENSION IF NOT EXISTS vector;`

### Connection errors
- Verify your connection string is correct
- Check that your IP is allowed (Supabase allows all IPs by default)
- Ensure your database password is correct

### Permission errors
- Make sure you're using the correct database user (usually `postgres`)
- For production, consider using connection pooling

