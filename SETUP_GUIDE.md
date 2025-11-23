# AI Learning Coach - Complete Setup Guide

This guide will walk you through setting up the AI Learning Coach from scratch.

## Prerequisites Checklist

- [ ] Python 3.11 or higher installed
- [ ] Node.js and npm installed (for memory MCP server)
- [ ] Claude Desktop app installed
- [ ] Supabase account created
- [ ] OpenAI API account with credits
- [ ] Anthropic API account with credits

## Step 1: Set Up Supabase Database

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign in or create account
3. Click "New Project"
4. Fill in:
   - **Name**: `ai-learning-coach`
   - **Database Password**: (save this securely)
   - **Region**: Choose closest to you
5. Click "Create new project"
6. Wait for project to be ready (~2 minutes)

### 1.2 Run Database Migration

1. In Supabase dashboard, click "SQL Editor" in left sidebar
2. Click "New Query"
3. Open the file: `database/migrations/001_initial_schema.sql`
4. Copy entire contents
5. Paste into SQL Editor
6. Click "Run"
7. Verify success message appears

### 1.3 Get Supabase Credentials

1. In Supabase dashboard, go to "Project Settings" (gear icon)
2. Click "API" in left menu
3. Copy and save:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **Anon key**: `eyJhb...` (under "Project API keys")
   - **Service Role key**: `eyJhb...` (keep this secret!)

## Step 2: Get API Keys

### 2.1 OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign in or create account
3. Click your profile → "View API keys"
4. Click "Create new secret key"
5. Name it "AI Learning Coach"
6. Copy and save the key (starts with `sk-`)
7. Add credits if needed (minimum $10 recommended)

### 2.2 Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create account
3. Click "API Keys" in left menu
4. Click "Create Key"
5. Name it "AI Learning Coach"
6. Copy and save the key (starts with `sk-ant-`)
7. Add credits if needed (minimum $20 recommended)

## Step 3: Install MCP Server

### 3.1 Clone and Install

```bash
# Navigate to project directory
cd ai-learning-coach/learning-coach-mcp

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Or using pip
pip install -e .
```

### 3.2 Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

Fill in the following in `.env`:

```bash
# Supabase (from Step 1.3)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# OpenAI (from Step 2.1)
OPENAI_API_KEY=sk-your-openai-key

# Anthropic (from Step 2.2)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Keep defaults for everything else
```

### 3.3 Verify Installation

```bash
# Test that server can start
uv run python src/server.py --help

# Should see MCP server info (then Ctrl+C to stop)
```

## Step 4: Install Memory MCP Server

### 4.1 Install Official Memory Server

```bash
# Install globally
npm install -g @modelcontextprotocol/server-memory

# Verify installation
npx @modelcontextprotocol/server-memory --version
```

## Step 5: Configure Claude Desktop

### 5.1 Find Config File Location

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### 5.2 Edit Configuration

Open the config file and add both MCP servers:

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "learning-coach": {
      "command": "uv",
      "args": [
        "run",
        "python",
        "/ABSOLUTE/PATH/TO/ai-learning-coach/learning-coach-mcp/src/server.py"
      ],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_KEY": "your-anon-key",
        "OPENAI_API_KEY": "sk-your-openai-key",
        "ANTHROPIC_API_KEY": "sk-ant-your-anthropic-key"
      }
    }
  }
}
```

**IMPORTANT:**
- Replace `/ABSOLUTE/PATH/TO/` with your actual full path
- Use forward slashes `/` even on Windows
- Don't use `~` for home directory - use full path

### 5.3 Restart Claude Desktop

1. **Completely quit** Claude Desktop (not just close window)
   - macOS: Claude → Quit Claude
   - Windows: Right-click taskbar icon → Exit
2. Relaunch Claude Desktop
3. Wait 5-10 seconds for MCP servers to load

### 5.4 Verify MCP Servers Loaded

In Claude.ai chat, type:
```
What MCP servers do you have access to?
```

You should see:
- `memory` - for persistent context
- `learning-coach` - for personalized learning

## Step 6: Add Your First Source

In Claude.ai chat:

```
Add https://lilianweng.github.io/feed.xml as a learning source with priority 5
```

Claude should respond confirming the source was added.

## Step 7: Generate First Digest

```
Generate my daily learning digest
```

Wait 10-15 seconds. You should receive a personalized digest with 5-7 insights!

## Step 8: Test Feedback Loop

In the digest UI:
1. Click "👍 Helpful" on an insight you like
2. Click "👎 Not Relevant" on one that doesn't fit

This trains the system to learn your preferences.

## Step 9: Sync Bootcamp Progress

```
Sync my bootcamp progress
```

This will update your learning context. (Uses mock data in MVP)

## Troubleshooting

### MCP Server Not Loading

**Problem**: Claude doesn't see the learning-coach server

**Solutions:**
1. Check Claude Desktop logs:
   ```bash
   # macOS
   tail -f ~/Library/Logs/Claude/mcp*.log

   # Look for errors related to learning-coach
   ```

2. Verify path is absolute:
   ```bash
   # Test the command directly
   uv run python /your/absolute/path/src/server.py
   ```

3. Check environment variables are set in config

4. Try removing and re-adding the MCP server config

### Database Connection Error

**Problem**: "Failed to connect to Supabase"

**Solutions:**
1. Verify Supabase project is active (not paused)
2. Check URL and key are correct in `.env`
3. Test connection:
   ```python
   python -c "from supabase import create_client; client = create_client('YOUR_URL', 'YOUR_KEY'); print(client.table('users').select('*').limit(1).execute())"
   ```

### No Insights Generated

**Problem**: Digest returns empty or error

**Solutions:**
1. Make sure you've added at least one source
2. Check that source has recent content (< 30 days)
3. Lower `SIMILARITY_THRESHOLD` in `.env` from 0.70 to 0.60
4. Check OpenAI API key has credits
5. Look at server logs for errors

### Poor Quality Insights

**Problem**: Insights aren't relevant to learning goals

**Solutions:**
1. Provide feedback (thumbs down) on irrelevant insights
2. Add more high-quality sources in your domain
3. Verify your learning context:
   ```
   What do you know about my learning context?
   ```
4. Manually update if needed:
   ```
   I'm learning about [specific topics] at [beginner/intermediate/advanced] level
   ```

### Memory Not Persisting

**Problem**: Claude forgets context between sessions

**Solutions:**
1. Verify memory MCP server is running:
   ```
   What's in my memory?
   ```
2. Check memory server logs
3. Reinstall memory server:
   ```bash
   npm uninstall -g @modelcontextprotocol/server-memory
   npm install -g @modelcontextprotocol/server-memory
   ```

## Next Steps

Now that you're set up:

1. **Add 3-5 trusted sources** in your learning domain
2. **Generate daily digests** for 1 week
3. **Provide feedback** consistently (helps system learn)
4. **Check analytics** (coming in Phase 2)
5. **Explore advanced features**:
   - Search past insights
   - Weekly summaries
   - Learning progress tracking

## Getting Help

If you're still stuck:

1. Check the main README.md for common issues
2. Look at example `.env.example` for configuration hints
3. Review logs:
   - MCP server: `~/Library/Logs/Claude/mcp*.log`
   - Supabase: Dashboard → Logs
4. Create an issue on GitHub with:
   - Error messages
   - Relevant log snippets
   - Steps to reproduce

## Advanced Configuration

### Custom Learning Context

Edit directly in database:

```sql
-- In Supabase SQL Editor
UPDATE learning_progress
SET
  current_week = 10,
  current_topics = ARRAY['Advanced RAG', 'Vector Databases', 'LLM Fine-tuning'],
  difficulty_level = 'advanced',
  learning_goals = 'Build production RAG system'
WHERE user_id = '00000000-0000-0000-0000-000000000001';
```

### Adjust Quality Threshold

In `.env`:
```bash
# Make quality gate more strict
RAGAS_MIN_SCORE=0.80

# Or more lenient
RAGAS_MIN_SCORE=0.60
```

### Increase Insight Count

In `.env`:
```bash
# Default is 7, can go up to 10
MAX_INSIGHTS=10
```

---

**Setup Complete! 🎉**

You now have a fully functional AI Learning Coach. Happy learning!
