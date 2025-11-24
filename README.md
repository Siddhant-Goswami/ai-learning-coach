# AI Learning Coach

A personalized AI learning assistant using Claude Memory, Model Context Protocol (MCP), and RAG to deliver daily learning insights tailored to your bootcamp progress.

## 🎯 Features

- **Daily Learning Digest**: AI-generated insights from curated content sources
- **MCP Integration**: Use as an MCP server with Claude Desktop
- **RAG Pipeline**: Vector search with OpenAI embeddings and GPT-4o-mini synthesis
- **Learning Context Tracking**: Automatically tracks your week, topics, and progress
- **Streamlit Dashboard**: Web interface to view insights and manage settings
- **Quality Metrics**: RAGAS evaluation scores for each digest

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Setup](#setup)
- [Using as MCP Server](#using-as-mcp-server)
- [Using the Dashboard](#using-the-dashboard)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Supabase account (free tier works)
- OpenAI API key
- Claude Desktop (for MCP integration)

### Installation

```bash
# 1. Clone the repository
cd ai-learning-coach

# 2. Set up the MCP server
cd learning-coach-mcp
pip install -e .

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your credentials

# 4. Initialize database
cd ../database
# Run the SQL migrations in Supabase SQL Editor (see below)
```

---

## ⚙️ Setup

### 1. Supabase Database Setup

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** in your Supabase dashboard
3. Run the following migration files in order:

**File: `database/migrations/001_initial_schema.sql`**
- Creates all tables (users, sources, content, embeddings, etc.)
- Sets up vector search with HNSW index
- Enables Row Level Security (RLS)

**File: `database/migrations/003_insert_test_data_with_rls_bypass.sql`**
- Inserts test user and learning progress
- Adds 3 default RSS content sources
- Creates your initial learning context

**File: `database/migrations/004_add_test_user_rls_policies.sql`**
- Adds RLS policies to allow test user access
- Required for the app to read/write data

### 2. Environment Configuration

Edit `learning-coach-mcp/.env`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-key-here

# Anthropic (Optional - OpenAI used by default)
# ANTHROPIC_API_KEY=sk-ant-your-key-here

# User Configuration
DEFAULT_USER_ID=00000000-0000-0000-0000-000000000001
```

**Getting your Supabase credentials:**
1. Go to your Supabase project
2. Click **Settings** → **API**
3. Copy **Project URL** → Use as `SUPABASE_URL`
4. Copy **anon/public** key → Use as `SUPABASE_KEY`

---

## 🔌 Using as MCP Server

### What is MCP?

Model Context Protocol (MCP) allows Claude Desktop to connect to external data sources and tools. Your AI Learning Coach becomes available as a set of tools Claude can use to help you learn.

### Configure Claude Desktop

1. **Open Claude Desktop Configuration**

```bash
# macOS
code ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Windows
code %APPDATA%\Claude\claude_desktop_config.json

# Linux
code ~/.config/Claude/claude_desktop_config.json
```

2. **Add the MCP Server Configuration**

```json
{
  "mcpServers": {
    "learning-coach": {
      "command": "/Users/path/miniconda3/bin/python3",
      "args": ["-m", "src.server"],
      "cwd": "/absolute/path/to/ai-learning-coach/learning-coach-mcp",
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_KEY": "your-anon-key",
        "OPENAI_API_KEY": "sk-proj-your-key",
        "DEFAULT_USER_ID": "00000000-0000-0000-0000-000000000001"
      }
    }
  }
}
```

**Important:** Replace `/absolute/path/to/ai-learning-coach` with the actual path on your system.

3. **Restart Claude Desktop**

Close and reopen Claude Desktop. You should see the learning-coach server connected in the bottom-right corner.

### Available MCP Tools

Once connected, Claude Desktop can use these tools:

#### 1. `generate_daily_digest`
Generate your personalized daily learning digest.

**Example prompt:**
```
Generate my daily learning digest
```

**What it does:**
- Fetches your learning context (week, topics)
- Retrieves relevant content from your sources
- Generates 7 educational insights using AI
- Returns quality metrics (faithfulness, precision, recall)

#### 2. `search_past_insights`
Search through previously generated insights.

**Example prompt:**
```
Search my past insights for "attention mechanisms"
```

**Parameters:**
- `query`: What to search for
- `limit`: Number of results (default: 10)
- `date_range`: Optional date filtering

#### 3. `manage_sources`
Add, remove, or update content sources.

**Example prompts:**
```
Add RSS feed: https://blog.example.com/feed.xml with priority 5

List my content sources

Deactivate the source with URL: https://old-blog.com/feed.xml
```

**Parameters:**
- `action`: "add", "remove", "list", or "update"
- `source_type`: "rss", "twitter", "reddit", etc.
- `identifier`: URL or handle
- `priority`: 1-5 (higher = more important)

#### 4. `provide_feedback`
Submit feedback on insights to improve future recommendations.

**Example prompts:**
```
Mark insight abc123 as helpful

This insight xyz789 is too advanced for me
```

**Feedback types:**
- `helpful`: Great insight
- `not_relevant`: Not related to my learning
- `too_basic`: Already know this
- `too_advanced`: Over my head
- `incorrect`: Wrong information

#### 5. `sync_bootcamp_progress`
Update your current week and learning topics.

**Example prompts:**
```
I'm now in week 8 learning about CNNs and Computer Vision

Update my topics to: Deep Learning, Neural Networks
```

### Example Usage in Claude Desktop

**Scenario 1: Morning Learning Routine**
```
You: Good morning! Generate my daily learning digest for today.

Claude: [Uses generate_daily_digest tool]
Here are your 7 personalized insights for Week 7:

1. Understanding Multi-Head Attention (Intermediate)
   Why this matters: Core concept for transformers...
   [Full insight with explanation and takeaway]

2. Positional Encoding in Transformers (Advanced)
   ...

Quality Scores:
- Faithfulness: 0.87
- Context Precision: 0.82
- Context Recall: 0.78
```

**Scenario 2: Managing Content Sources**
```
You: Add Andrej Karpathy's blog as a high priority source

Claude: [Uses manage_sources tool]
✓ Added RSS feed: Andrej Karpathy's Blog
Priority: 5
Status: Active

I'll start including insights from this source in your future digests.
```

**Scenario 3: Searching Past Learning**
```
You: What did I learn about backpropagation last week?

Claude: [Uses search_past_insights tool]
I found 3 insights about backpropagation from your digests:

1. From Nov 18: "Chain Rule in Backpropagation"
   You learned how gradients flow backward through layers...

2. From Nov 20: "Vanishing Gradients Problem"
   ...
```

---

## 🖥️ Using the Dashboard

The Streamlit dashboard provides a web interface to view and manage your learning.

### Start the Dashboard

```bash
cd dashboard
streamlit run app.py
```

Opens at: http://localhost:8501

### Dashboard Features

#### 📚 Today's Digest Page

- **View Today's Insights**: See AI-generated learning insights
- **Quality Metrics**: Faithfulness, Precision, Recall scores
- **Source Attribution**: See where each insight came from
- **Feedback Buttons**: Rate insights (👍 👎 📉 📈)
- **Refresh Digest**: Generate new insights

#### ⚙️ Settings Page

**Learning Context Tab:**
- Edit current week (1-24)
- Change difficulty level (beginner/intermediate/advanced)
- Update learning topics
- Set learning goals
- Save changes to database

**Sources Tab:**
- View all RSS feeds
- Toggle sources active/inactive
- See priority and status
- Add new RSS sources

**System Tab:**
- Database connection status
- API configuration status
- Database statistics (articles, embeddings, digests)
- Clear digest cache
- Refresh data

### Workflow Example

1. **Morning:** Open dashboard to view today's digest
2. **Read:** Go through insights, expand explanations
3. **Feedback:** Click 👍 on helpful insights, 👎 on irrelevant ones
4. **Update:** Go to Settings → Learning Context to update your progress
5. **Customize:** Add new RSS sources in Settings → Sources

---

## 🏗️ Architecture

### System Components

```
┌─────────────────────────────────────────────┐
│           Claude Desktop (MCP)              │
│  - generate_daily_digest                    │
│  - search_past_insights                     │
│  - manage_sources                           │
│  - provide_feedback                         │
│  - sync_bootcamp_progress                   │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│        Learning Coach MCP Server            │
│  - FastMCP Framework                        │
│  - Tool Handlers                            │
│  - Claude Memory Integration                │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│            RAG Pipeline                     │
│  - Query Builder                            │
│  - Vector Retriever (HNSW)                  │
│  - OpenAI GPT-4o-mini Synthesis             │
│  - Quality Gate (RAGAS)                     │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Supabase Database                   │
│  - PostgreSQL + pgvector                    │
│  - 7 tables (users, sources, content, etc.) │
│  - HNSW vector index (halfvec)              │
│  - Row Level Security (RLS)                 │
└─────────────────────────────────────────────┘
```

### Tech Stack

**Backend:**
- **FastMCP**: MCP server framework
- **OpenAI**: text-embedding-3-small (embeddings), gpt-4o-mini (synthesis)
- **Supabase**: PostgreSQL + pgvector + RLS
- **Python**: 3.10+

**Frontend:**
- **Streamlit**: Dashboard UI
- **Plotly**: Not used in simplified version

**Data Flow:**
1. RSS feeds → Content ingestion → Database
2. Content → Chunking → Embeddings (OpenAI) → Vector DB
3. User query → Vector search → Relevant chunks
4. Chunks + Context → GPT-4o-mini → Insights
5. Insights + RAGAS → Quality scores → Storage

---

## 🔧 Troubleshooting

### MCP Server Not Connecting

**Problem:** Claude Desktop doesn't show the learning-coach server or shows "spawn python ENOENT" error

**Solutions:**
1. **Fix "spawn python ENOENT" error**: Use the full path to Python instead of just `python`
   ```bash
   # Find your Python path
   which python3
   # Use this path in claude_desktop_config.json
   # Example: "/Users/yourname/miniconda3/bin/python3"
   ```
2. Check Claude Desktop config path is correct:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
3. Verify absolute path to `learning-coach-mcp` directory (no relative paths)
4. Ensure environment variables are set in config (SUPABASE_URL, OPENAI_API_KEY, etc.)
5. Restart Claude Desktop completely (quit and reopen)
6. Check logs in Claude Desktop developer console for specific errors

### Database Connection Errors

**Problem:** "Could not connect to database" or RLS errors

**Solutions:**
1. Verify SUPABASE_URL and SUPABASE_KEY in `.env`
2. Run all 3 migration files in Supabase SQL Editor:
   - `001_initial_schema.sql`
   - `003_insert_test_data_with_rls_bypass.sql`
   - `004_add_test_user_rls_policies.sql`
3. Check RLS policies allow test user access
4. Try using Supabase service role key for testing

### No Insights Generated

**Problem:** "No digest available for today"

**Solutions:**
1. Check OpenAI API key is valid
2. Ensure you have content sources in database
3. Run content ingestion: `python3 quick_test_ingestion.py`
4. Check database has embeddings: Go to Settings → System tab
5. Try "Generate Today's Digest" button on home page

### JSON Generation Errors

**Problem:** "JSON could not be generated" errors

**Solutions:**
1. Already fixed in current version with fallback handling
2. Check OpenAI API key has credits
3. Verify internet connection
4. Try refreshing the page

### Extra Navigation Showing

**Problem:** "app", "home", "settings" navigation appearing

**Solutions:**
1. Already fixed - `pages/` directory renamed to `views/`
2. Hard refresh browser: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
3. Clear browser cache
4. Restart Streamlit: `pkill -f streamlit && streamlit run app.py`

---

## 📚 Additional Resources

### Quick Commands

```bash
# Start dashboard
cd dashboard && streamlit run app.py

# Run test ingestion
python3 quick_test_ingestion.py

# Setup and test
python3 setup_and_test.py

# Install MCP server
cd learning-coach-mcp && pip install -e .
```

### File Structure

```
ai-learning-coach/
├── README.md                          # This file
├── learning-coach-mcp/               # MCP Server
│   ├── src/
│   │   ├── server.py                 # MCP tools
│   │   ├── rag/                      # RAG pipeline
│   │   ├── ingestion/                # Content fetching
│   │   └── tools/                    # Source & feedback management
│   ├── .env                          # Configuration
│   └── pyproject.toml                # Python dependencies
├── dashboard/                         # Streamlit UI
│   ├── app.py                        # Main dashboard
│   ├── views/
│   │   ├── home.py                   # Today's digest page
│   │   └── settings.py               # Settings page
│   └── digest_api.py                 # API wrapper
├── database/                          # Database setup
│   └── migrations/
│       ├── 001_initial_schema.sql    # Main schema
│       ├── 003_insert_test_data...   # Test data
│       └── 004_add_test_user_rls...  # RLS policies
└── docs/                              # Documentation
    ├── QUICK_START.md
    ├── TEST_REPORT.md
    └── VERIFICATION_COMPLETE.md
```

---

## 🤝 Contributing

This is a personal learning project built for the 100xEngineers AI bootcamp. Feel free to fork and adapt for your own learning journey!

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Built with [Claude](https://claude.ai) and [MCP](https://modelcontextprotocol.io)
- Inspired by the need for personalized, context-aware learning
- Uses [OpenAI](https://openai.com) for embeddings and synthesis
- Powered by [Supabase](https://supabase.com) for vector storage

---

**Happy Learning! 📚🚀**

For questions or issues, see the [Troubleshooting](#troubleshooting) section above.
