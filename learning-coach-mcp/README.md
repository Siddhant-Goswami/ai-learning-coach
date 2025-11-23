# AI Learning Coach MCP Server

A personalized AI learning assistant that uses Claude Memory, Model Context Protocol (MCP), and RAG to deliver contextually relevant learning content.

## Features

- **Automatic Context Tracking**: Uses Claude Memory to track learning progress without manual updates
- **Intelligent Content Retrieval**: Vector-based RAG with hybrid ranking (similarity + recency + priority)
- **Quality Assurance**: RAGAS evaluation ensures high-quality insights
- **Dual Interface**: Works in Claude.ai chat and standalone Streamlit dashboard
- **Feedback Loop**: Learns from user feedback to improve future recommendations

## Quick Start

### Prerequisites

- Python 3.11+
- Supabase account (free tier works)
- OpenAI API key
- Anthropic API key
- Claude Desktop app (for MCP integration)

### Installation

1. **Clone the repository**
   ```bash
   cd learning-coach-mcp
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync

   # Or using pip
   pip install -e .
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and fill in your API keys
   ```

4. **Set up Supabase database**
   - Create a new Supabase project
   - Run the migration script in SQL Editor:
     ```bash
     # Copy contents of database/migrations/001_initial_schema.sql
     # Paste and run in Supabase SQL Editor
     ```

5. **Configure Claude Desktop**

   Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "learning-coach": {
         "command": "uv",
         "args": ["run", "python", "/absolute/path/to/learning-coach-mcp/src/server.py"],
         "env": {
           "SUPABASE_URL": "your-supabase-url",
           "SUPABASE_KEY": "your-supabase-key",
           "OPENAI_API_KEY": "your-openai-key",
           "ANTHROPIC_API_KEY": "your-anthropic-key"
         }
       }
     }
   }
   ```

6. **Restart Claude Desktop**

   Completely quit and relaunch Claude Desktop to load the MCP server.

### First Use

In Claude.ai chat:

1. Add your first source:
   ```
   Add https://lilianweng.github.io/feed.xml as a learning source with priority 5
   ```

2. Generate your first digest:
   ```
   Generate my daily learning digest
   ```

3. Provide feedback:
   ```
   I found that insight helpful! [Use thumbs up in the UI]
   ```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Development Server

```bash
# Run with MCP Inspector for debugging
mcp dev src/server.py
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

## Architecture

```
┌─────────────────────────────────────────────┐
│ ACCESS LAYER                                │
│ ├─ Claude.ai (Chat + MCP Apps rendering)   │
│ └─ Streamlit Dashboard (Direct access)     │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ MCP SERVER: learning-coach                  │
│ ├─ Tools (9 core functions)                │
│ ├─ UI Resources (3 HTML templates)         │
│ └─ Integration Layer                        │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ INTELLIGENCE LAYER                          │
│ ├─ Claude Memory (auto-context)            │
│ ├─ RAG Pipeline (retrieve → synthesize)    │
│ └─ RAGAS Evaluation (quality gate)         │
└─────────────────┬───────────────────────────┘
                  ↓
┌─────────────────────────────────────────────┐
│ DATA LAYER                                  │
│ ├─ Supabase (pgvector + metadata)         │
│ ├─ Content Ingestion Workers              │
│ └─ 100xEngineers API Integration           │
└─────────────────────────────────────────────┘
```

## MCP Tools

### `generate_daily_digest`
Generate personalized learning digest for specified date.

**Parameters:**
- `date`: ISO date or "today" (default: "today")
- `max_insights`: Number of insights (3-10, default: 7)
- `force_refresh`: Skip cache (default: false)

**Returns:** Digest with insights, sources, and quality scores

### `manage_sources`
Manage content sources (add, remove, update, list).

**Parameters:**
- `action`: "add", "remove", "update", or "list"
- `source_type`: "rss", "twitter", "reddit", "custom_url"
- `source_identifier`: URL, handle, or subreddit
- `priority`: 1-5 (default: 3)

### `provide_feedback`
Capture user feedback on insights.

**Parameters:**
- `insight_id`: UUID of insight
- `feedback_type`: "helpful", "not_relevant", "incorrect", "too_basic", "too_advanced"
- `reason`: Optional explanation

### `sync_bootcamp_progress`
Sync learning context from 100xEngineers platform.

**Returns:** Current week and topics

### `search_past_insights`
Search previously delivered digests.

**Parameters:**
- `query`: Semantic search query
- `date_range`: Optional date filter
- `min_feedback_score`: Optional quality filter

## Configuration

See `.env.example` for all available configuration options.

Key settings:
- `TOP_K_RETRIEVAL`: Number of chunks to retrieve (default: 15)
- `SIMILARITY_THRESHOLD`: Minimum similarity score (default: 0.70)
- `RAGAS_MIN_SCORE`: Quality gate threshold (default: 0.70)
- `DIGEST_CACHE_HOURS`: Cache duration (default: 6)

## Cost Estimation

For typical usage (1 user, daily digest):
- OpenAI Embeddings: ~$10/month
- Claude Sonnet 4.5: ~$120/month
- Supabase: Free tier
- **Total: ~$130/month (~$4.30/day)**

## Troubleshooting

### MCP Server Not Loading

1. Check Claude Desktop config path is correct
2. Verify all environment variables are set
3. Check logs: `tail -f ~/Library/Logs/Claude/mcp*.log`

### Database Connection Failed

1. Verify Supabase URL and key in `.env`
2. Check Supabase project is active
3. Test connection: `python -c "from src.utils.db import get_supabase_client; get_supabase_client('url', 'key')"`

### Poor Digest Quality

1. Check RAGAS scores in digest output
2. Add more high-quality sources
3. Provide feedback (helps system learn)
4. Lower `SIMILARITY_THRESHOLD` if no results

## Contributing

This is currently a single-user MVP. Post-launch, we'll open for contributions.

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
- GitHub Issues: [your-repo-url]
- Email: [your-email]

## Roadmap

### MVP (Current)
- [x] Supabase database with vector search
- [x] MCP server with 5 core tools
- [x] Content ingestion (RSS)
- [ ] RAG pipeline
- [ ] RAGAS evaluation
- [ ] Streamlit dashboard

### Post-MVP
- [ ] Email delivery
- [ ] Twitter/Reddit fetchers
- [ ] Export to Notion/Obsidian
- [ ] Learning patterns analysis
- [ ] Multi-user support

---

**Built with ❤️ using Claude, MCP, and Supabase**
