# Quick Start Guide

## Setup Steps

### 1. Database Initialization

The database has Row Level Security (RLS) enabled. To insert test data, you need to run the SQL directly in Supabase:

1. Go to https://supabase.com/dashboard
2. Select your project: `hkwuyxqltunphmbmqpsm`
3. Click "SQL Editor" in the left sidebar
4. Click "New Query"
5. Copy and paste the contents of `database/migrations/002_insert_test_data.sql`
6. Click "Run" (or press Cmd/Ctrl + Enter)

You should see: "Test data inserted successfully!"

### 2. Verify Configuration

Run the setup script:

```bash
python3 setup_and_test.py
```

This will:
- Check all environment variables
- Test database connection
- Test OpenAI connection
- Guide you through any missing setup

### 3. Start the Dashboard

The dashboard should already be running at:
```
http://localhost:8501
```

If not, start it with:
```bash
cd dashboard
streamlit run app.py
```

### 4. Test the App

1. **Home Page**: Should show "No content in database yet" initially
2. **Settings Page**: Check that all API keys are configured
3. **Analytics Page**: Will show mock data initially

### 5. Add Real Content (Optional)

To fetch real content from RSS feeds:

```bash
cd learning-coach-mcp
python3 -m pip install -e .
python3 -m src.ingestion.orchestrator
```

This will:
- Fetch articles from the 3 configured RSS sources
- Process and chunk the content
- Generate embeddings
- Store in the database

After ingestion completes, refresh the Home page to see real insights!

## Troubleshooting

### "Row Level Security policy violated"

This means you're trying to insert data using the anon key. Solutions:

1. **Recommended**: Run the SQL in Supabase SQL Editor (bypasses RLS)
2. **Alternative**: Temporarily disable RLS:
   ```sql
   ALTER TABLE users DISABLE ROW LEVEL SECURITY;
   ALTER TABLE learning_progress DISABLE ROW LEVEL SECURITY;
   ALTER TABLE sources DISABLE ROW LEVEL SECURITY;
   ```
   Then re-enable after inserting test data.

### "ANTHROPIC_API_KEY not set"

This is fine! The system will use OpenAI for synthesis instead. If you want to use Claude:

1. Get an API key from https://console.anthropic.com/settings/keys
2. Add to `learning-coach-mcp/.env`:
   ```
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

### App shows "Demo Mode"

This means either:
- No content in database yet → Run ingestion (step 5 above)
- Test data not inserted → Follow step 1 above

## Current Status

✅ Database schema created
✅ Streamlit dashboard running
✅ OpenAI configured for embeddings & synthesis
⏳ Waiting for test data insertion
⏳ Waiting for content ingestion

## Next Steps

1. **Insert test data** (Step 1 above) - 2 minutes
2. **Run ingestion** (Step 5 above) - 5-10 minutes
3. **Generate first digest** - Refresh home page

After these steps, you'll have a fully functioning AI Learning Coach!
