# AI Learning Coach - MVP Implementation Plan
## 7-Day Sprint to Functional Product

**Version:** 1.0
**Created:** Nov 23, 2024
**Target User:** Sowmya (100xEngineers AI Bootcamp, Week 7/24)
**Goal:** Personalized learning assistant that saves 15+ hours/week on content curation

---

## Executive Summary

### What We're Building
A personalized AI learning coach that uses:
- **Claude Memory** for automatic context tracking (no manual updates)
- **MCP (Model Context Protocol)** for dual-interface delivery (chat + dashboard)
- **Vector RAG** for intelligent content retrieval and synthesis
- **RAGAS evaluation** for quality assurance

### Key Innovation
Unlike traditional RAG systems requiring constant manual updates, this system:
1. Automatically learns from 100xEngineers bootcamp progress
2. Adapts to user feedback patterns
3. Delivers through multiple interfaces (Claude.ai chat, Streamlit dashboard)
4. Ensures quality with automated evaluation

### Success Metrics (MVP)
- ✅ Generate daily digest with 5-7 relevant insights
- ✅ RAGAS scores average > 0.70 (faithfulness, relevancy, recall)
- ✅ User can provide feedback that improves future digests
- ✅ Memory correctly tracks learning context
- ✅ Works in both Claude.ai and standalone dashboard
- ✅ Operates under $10/day cost

---

## Technical Architecture

### Technology Stack Decision Matrix

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **MCP Server** | FastMCP 2.0 (Python) | Production-ready, enterprise auth support, comprehensive tooling |
| **Database** | Supabase (PostgreSQL + pgvector) | Managed vector search, RLS for security, generous free tier |
| **Embeddings** | OpenAI text-embedding-3-small | Cost-effective ($0.02/1M tokens), 1536 dims, good quality |
| **LLM (Synthesis)** | Claude Sonnet 4.5 | Best reasoning, memory support, educational explanations |
| **Quality Eval** | RAGAS (latest) | Industry-standard RAG evaluation, multiple metrics |
| **Dashboard** | Streamlit | Rapid development, Python-native, easy deployment |
| **Memory** | @modelcontextprotocol/server-memory | Official MCP memory implementation, cross-session persistence |
| **Background Jobs** | APScheduler | Simple Python scheduling, no external dependencies |
| **Vector Index** | HNSW (pgvector) | Better recall than IVFFlat, faster queries |

### System Architecture

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

### Key Technical Decisions

#### 1. Why FastMCP over basic MCP SDK?
- **Production-ready**: Enterprise auth, server composition, testing utilities
- **Developer Experience**: Better error handling, built-in development server
- **Future-proof**: Supports advanced patterns (proxying, OpenAPI generation)

#### 2. Why Supabase over self-hosted PostgreSQL?
- **Time savings**: Managed service eliminates DevOps overhead (critical for 7-day sprint)
- **pgvector built-in**: Enable extension with one click
- **Row-Level Security**: Built-in multi-tenancy for future scaling
- **Cost**: Free tier sufficient for MVP (500MB database, 50k monthly active users)

#### 3. Why HNSW index over IVFFlat?
- **Better recall**: More accurate similarity search results
- **Faster queries**: P95 latency < 100ms vs 200-300ms with IVFFlat
- **Simpler**: No need to tune 'lists' parameter
- **Trade-off**: Slower indexing, but we index async (acceptable)

#### 4. Why NOT build custom memory system?
- **Memory is complex**: Cross-session persistence, conflict resolution, version control
- **Official implementation**: @modelcontextprotocol/server-memory is battle-tested
- **Integration**: Works seamlessly with Claude.ai and other MCP clients
- **Focus**: Spend time on RAG quality, not infrastructure

#### 5. Why Streamlit over Next.js/React?
- **Speed**: Build entire dashboard in 1-2 days vs 5-7 days
- **Python-native**: Same language as MCP server, no context switching
- **Components**: Built-in charts, forms, data displays
- **Deployment**: Streamlit Cloud (free tier) or single-command Docker deploy
- **Trade-off**: Less customizable, but sufficient for MVP

---

## Phase-by-Phase Implementation Plan

### Phase 1: Foundation (Days 1-2)

**Objective:** Set up infrastructure, verify all integrations work end-to-end

#### Day 1: Database & MCP Skeleton

**Morning (4 hours):**
1. **Supabase Project Setup**
   - Create project: `ai-learning-coach-mvp`
   - Enable pgvector extension
   - Create initial schema:
     - `users` (id, email, created_at, metadata)
     - `sources` (id, user_id, type, identifier, priority, active, health_score)
     - `content` (id, source_id, title, author, published_at, url, content_hash, raw_text)
     - `embeddings` (id, content_id, chunk_sequence, chunk_text, embedding halfvec(1536))
     - `feedback` (id, user_id, insight_id, content_id, type, reason)
     - `generated_digests` (id, user_id, digest_date, insights jsonb, ragas_scores jsonb)
   - Create indexes:
     ```sql
     CREATE INDEX ON embeddings USING hnsw (embedding halfvec_cosine_ops);
     CREATE INDEX idx_content_published ON content(published_at DESC);
     CREATE INDEX idx_sources_user ON sources(user_id, active);
     CREATE INDEX idx_feedback_user ON feedback(user_id, created_at DESC);
     ```
   - Set up Row Level Security (RLS) policies

   **Reasoning:**
   - Use `halfvec` instead of `vector` → saves 50% storage with minimal accuracy loss
   - HNSW index for best recall and query speed
   - RLS from day 1 → easier to scale to multiple users later

2. **MCP Server Initialization**
   - Create Python project structure:
     ```
     learning-coach-mcp/
     ├── pyproject.toml
     ├── src/
     │   ├── __init__.py
     │   ├── server.py          # Main MCP server
     │   ├── tools/              # 9 MCP tools
     │   ├── ui/                 # 3 UI resources
     │   ├── rag/                # RAG pipeline
     │   ├── ingestion/          # Content fetchers
     │   └── utils/              # Helpers
     └── tests/
     ```
   - Install dependencies:
     ```bash
     uv init learning-coach-mcp
     cd learning-coach-mcp
     uv add fastmcp supabase-py openai ragas apscheduler httpx beautifulsoup4 feedparser
     ```
   - Create basic FastMCP server:
     ```python
     from fastmcp import FastMCP

     mcp = FastMCP("learning-coach")

     @mcp.tool()
     async def generate_daily_digest(date: str = "today") -> dict:
         """Generate personalized learning digest."""
         return {"status": "stub", "message": "Not implemented yet"}

     if __name__ == "__main__":
         mcp.run()
     ```
   - Test with MCP Inspector:
     ```bash
     mcp dev src/server.py
     ```

**Afternoon (4 hours):**
3. **Memory Server Setup**
   - Install official memory MCP server:
     ```bash
     npm install -g @modelcontextprotocol/server-memory
     ```
   - Configure Claude Desktop (`claude_desktop_config.json`):
     ```json
     {
       "mcpServers": {
         "memory": {
           "command": "npx",
           "args": ["-y", "@modelcontextprotocol/server-memory"]
         },
         "learning-coach": {
           "command": "uv",
           "args": ["run", "python", "/path/to/src/server.py"]
         }
       }
     }
     ```
   - Restart Claude Desktop, verify both servers load

   **Reasoning:** Using official memory server instead of building custom:
   - Saves 2-3 days of development time
   - Cross-session persistence handled automatically
   - Works with Claude.ai's memory UI

4. **100xEngineers API Integration**
   - Mock API for MVP (real integration post-launch):
     ```python
     # src/integrations/bootcamp.py
     async def get_user_progress(user_id: str) -> dict:
         """Mock bootcamp progress - replace with real API later."""
         return {
             "current_week": 7,
             "current_topics": ["Attention Mechanisms", "Transformers", "Multi-Head Attention"],
             "difficulty_level": "intermediate",
             "learning_goal": "Build chatbot with RAG"
         }
     ```
   - Create tool to update memory:
     ```python
     @mcp.tool()
     async def sync_bootcamp_progress() -> str:
         """Sync learning context from bootcamp."""
         # Get progress from bootcamp API
         # Update memory via memory MCP server
         # Return status
     ```

**End of Day 1 Deliverables:**
- ✅ Supabase database with schema and indexes
- ✅ MCP server running with stub tools
- ✅ Memory server integrated with Claude Desktop
- ✅ Mock bootcamp integration

#### Day 2: Content Ingestion Pipeline

**Morning (4 hours):**
1. **RSS Feed Fetcher**
   ```python
   # src/ingestion/rss_fetcher.py
   import feedparser
   from datetime import datetime, timedelta

   async def fetch_rss_feed(feed_url: str, since: datetime) -> list[dict]:
       """Fetch new articles from RSS feed since given timestamp."""
       feed = feedparser.parse(feed_url)
       articles = []

       for entry in feed.entries:
           published = datetime(*entry.published_parsed[:6])
           if published > since:
               articles.append({
                   "title": entry.title,
                   "url": entry.link,
                   "content": entry.get("summary", ""),
                   "published_at": published,
                   "author": entry.get("author", "Unknown")
               })

       return articles
   ```

2. **Content Chunking**
   ```python
   # src/ingestion/chunker.py
   from typing import List

   def chunk_text(text: str, chunk_size: int = 750, overlap: int = 100) -> List[str]:
       """
       Chunk text into overlapping segments.
       Respects sentence boundaries.
       """
       sentences = text.split('. ')
       chunks = []
       current_chunk = []
       current_tokens = 0

       for sentence in sentences:
           tokens = len(sentence.split())

           if current_tokens + tokens > chunk_size and current_chunk:
               chunks.append('. '.join(current_chunk) + '.')
               # Keep last few sentences for overlap
               overlap_sentences = []
               overlap_tokens = 0
               for s in reversed(current_chunk):
                   overlap_tokens += len(s.split())
                   if overlap_tokens > overlap:
                       break
                   overlap_sentences.insert(0, s)

               current_chunk = overlap_sentences
               current_tokens = overlap_tokens

           current_chunk.append(sentence)
           current_tokens += tokens

       if current_chunk:
           chunks.append('. '.join(current_chunk) + '.')

       return chunks
   ```

   **Reasoning:**
   - 750 tokens target (between 500-1000 range) → balances context vs precision
   - 100-token overlap → prevents losing context at boundaries
   - Sentence-aware chunking → cleaner semantic units

**Afternoon (4 hours):**
3. **Embedding Generation**
   ```python
   # src/ingestion/embedder.py
   from openai import AsyncOpenAI

   client = AsyncOpenAI()

   async def generate_embeddings(texts: List[str]) -> List[List[float]]:
       """Generate embeddings using OpenAI text-embedding-3-small."""
       response = await client.embeddings.create(
           model="text-embedding-3-small",
           input=texts,
           dimensions=1536  # Match halfvec(1536) in database
       )
       return [item.embedding for item in response.data]
   ```

4. **Ingestion Orchestrator**
   ```python
   # src/ingestion/orchestrator.py
   from apscheduler.schedulers.asyncio import AsyncIOScheduler
   from supabase import create_client
   import hashlib

   class IngestionOrchestrator:
       def __init__(self, supabase_url: str, supabase_key: str):
           self.db = create_client(supabase_url, supabase_key)
           self.scheduler = AsyncIOScheduler()

       async def ingest_content(self, source_id: str):
           """Fetch, chunk, embed, and store content from a source."""
           # 1. Get source details
           source = self.db.table("sources").select("*").eq("id", source_id).single().execute()

           # 2. Fetch new articles based on source type
           if source.data["type"] == "rss":
               articles = await fetch_rss_feed(source.data["identifier"], since=...)

           # 3. Deduplicate (check content_hash)
           for article in articles:
               content_hash = hashlib.md5(article["content"].encode()).hexdigest()
               existing = self.db.table("content").select("id").eq("content_hash", content_hash).execute()
               if existing.data:
                   continue  # Skip duplicate

               # 4. Store article
               content_result = self.db.table("content").insert({
                   "source_id": source_id,
                   "title": article["title"],
                   "url": article["url"],
                   "content_hash": content_hash,
                   "raw_text": article["content"],
                   "published_at": article["published_at"]
               }).execute()

               # 5. Chunk content
               chunks = chunk_text(article["content"])

               # 6. Generate embeddings (batch for efficiency)
               embeddings = await generate_embeddings(chunks)

               # 7. Store chunks with embeddings
               for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                   self.db.table("embeddings").insert({
                       "content_id": content_result.data[0]["id"],
                       "chunk_sequence": idx,
                       "chunk_text": chunk,
                       "embedding": embedding
                   }).execute()

       def start_scheduled_ingestion(self):
           """Run ingestion every 6 hours."""
           self.scheduler.add_job(
               self.ingest_all_sources,
               'interval',
               hours=6,
               id='content_ingestion'
           )
           self.scheduler.start()
   ```

   **Reasoning:**
   - Batch embedding generation → reduces API calls, saves cost
   - Content hash for deduplication → prevents processing same article twice
   - Scheduled every 6 hours → balances freshness vs cost

**End of Day 2 Deliverables:**
- ✅ RSS feed fetcher working
- ✅ Chunking algorithm with sentence-awareness
- ✅ Embedding pipeline with OpenAI integration
- ✅ Background job scheduler set up
- ✅ End-to-end: RSS → chunks → embeddings → database

---

### Phase 2: Core RAG Pipeline (Days 3-4)

**Objective:** Build the heart of the system - retrieve relevant content and synthesize insights

#### Day 3: Retrieval & Memory Integration

**Morning (4 hours):**
1. **Query Construction from Memory**
   ```python
   # src/rag/query_builder.py
   async def build_query_from_memory(user_id: str) -> str:
       """
       Construct semantic search query from user's learning context.
       Uses Claude Memory for context awareness.
       """
       # In MCP environment, memory is automatically available to Claude
       # For direct API calls, we query the memory server

       # Mock for MVP - will be replaced with actual memory retrieval
       learning_context = {
           "current_week": 7,
           "topics": ["Attention Mechanisms", "Transformers", "Multi-Head Attention"],
           "difficulty": "intermediate",
           "goal": "Build chatbot with RAG"
       }

       query = f"""
       User is in Week {learning_context['current_week']} of AI bootcamp learning about
       {', '.join(learning_context['topics'])}.
       {learning_context['difficulty'].capitalize()} level.
       Goal: {learning_context['goal']}.

       Find recent articles explaining these topics with practical examples and
       implementation details. Prefer technical depth over high-level overviews.
       """

       return query.strip()
   ```

2. **Vector Similarity Search**
   ```python
   # src/rag/retriever.py
   from supabase import create_client
   from openai import AsyncOpenAI

   class VectorRetriever:
       def __init__(self, supabase_url: str, supabase_key: str):
           self.db = create_client(supabase_url, supabase_key)
           self.embeddings_client = AsyncOpenAI()

       async def retrieve(self, query: str, top_k: int = 15, similarity_threshold: float = 0.70) -> list[dict]:
           """
           Retrieve most relevant chunks using vector similarity.
           """
           # 1. Generate query embedding
           query_embedding = await self.embeddings_client.embeddings.create(
               model="text-embedding-3-small",
               input=query,
               dimensions=1536
           )

           # 2. Vector similarity search with filters
           # Using Supabase RPC function for complex query
           results = self.db.rpc(
               'match_embeddings',
               {
                   'query_embedding': query_embedding.data[0].embedding,
                   'match_threshold': similarity_threshold,
                   'match_count': top_k
               }
           ).execute()

           # 3. Enrich with source metadata
           enriched_results = []
           for result in results.data:
               # Get full content metadata
               content = self.db.table("content").select("*").eq("id", result["content_id"]).single().execute()
               source = self.db.table("sources").select("*").eq("id", content.data["source_id"]).single().execute()

               enriched_results.append({
                   "chunk_text": result["chunk_text"],
                   "similarity": result["similarity"],
                   "content_title": content.data["title"],
                   "content_url": content.data["url"],
                   "published_at": content.data["published_at"],
                   "source_name": source.data["identifier"],
                   "source_priority": source.data["priority"]
               })

           # 4. Re-rank by combined score (similarity + recency + priority)
           for result in enriched_results:
               # Recency factor (0-1, higher for newer content)
               days_old = (datetime.now() - result["published_at"]).days
               recency_factor = max(0, 1 - (days_old / 30))

               # Priority factor (0-1, normalized from 1-5 scale)
               priority_factor = result["source_priority"] / 5.0

               # Combined score
               result["final_score"] = (
                   0.6 * result["similarity"] +
                   0.3 * recency_factor +
                   0.1 * priority_factor
               )

           # Sort by final score
           enriched_results.sort(key=lambda x: x["final_score"], reverse=True)

           return enriched_results[:top_k]
   ```

3. **Create Supabase RPC Function**
   ```sql
   -- Run this in Supabase SQL Editor
   CREATE OR REPLACE FUNCTION match_embeddings(
     query_embedding halfvec(1536),
     match_threshold float,
     match_count int
   )
   RETURNS TABLE (
     id uuid,
     content_id uuid,
     chunk_text text,
     similarity float
   )
   LANGUAGE sql STABLE
   AS $$
     SELECT
       embeddings.id,
       embeddings.content_id,
       embeddings.chunk_text,
       1 - (embeddings.embedding <=> query_embedding) AS similarity
     FROM embeddings
     WHERE 1 - (embeddings.embedding <=> query_embedding) > match_threshold
     ORDER BY embeddings.embedding <=> query_embedding
     LIMIT match_count;
   $$;
   ```

   **Reasoning:**
   - `<=>` operator for cosine distance (best for normalized embeddings)
   - Hybrid scoring (similarity + recency + priority) → prevents stale or low-quality sources dominating
   - Re-ranking after retrieval → more flexible than pure vector search

**Afternoon (4 hours):**
4. **Educational Synthesis Prompt**
   ```python
   # src/rag/synthesizer.py
   from anthropic import AsyncAnthropic

   class InsightSynthesizer:
       def __init__(self, api_key: str):
           self.client = AsyncAnthropic(api_key=api_key)

       async def synthesize_insights(
           self,
           retrieved_chunks: list[dict],
           learning_context: dict,
           num_insights: int = 7
       ) -> dict:
           """
           Synthesize personalized learning insights from retrieved content.
           Uses first-principles thinking and Feynman technique.
           """

           # Build context from chunks
           context = self._build_context(retrieved_chunks)

           # Construct prompt
           system_prompt = """You are an expert AI learning coach with deep expertise in
           educational theory and first-principles thinking. Your role is to help learners
           understand complex AI concepts by:

           1. Breaking down concepts to fundamentals
           2. Using the Feynman technique (explain like teaching someone else)
           3. Providing practical, actionable examples
           4. Connecting new concepts to prior knowledge
           5. Maintaining source attribution and accuracy

           Educational Principles:
           - Start with "why" before "how"
           - Use analogies only when they clarify, not obscure
           - Prefer concrete examples over abstract descriptions
           - Always provide a practical takeaway
           - Cite sources accurately
           """

           user_prompt = f"""
           Learning Context:
           - Current Week: {learning_context['current_week']}
           - Topics: {', '.join(learning_context['topics'])}
           - Level: {learning_context['difficulty']}
           - Goal: {learning_context['goal']}

           Retrieved Content:
           {context}

           Task: Generate {num_insights} personalized learning insights based on this content.

           For each insight, provide:
           1. Title (concise, specific)
           2. Relevance Reason (why this matters for current learning)
           3. Explanation (300-500 words, first-principles approach)
           4. Practical Takeaway (actionable item, 50-100 words)
           5. Source Attribution (title, author, URL)

           Return as JSON array matching this schema:
           {{
             "insights": [
               {{
                 "title": "string",
                 "relevance_reason": "string",
                 "explanation": "string",
                 "practical_takeaway": "string",
                 "source": {{
                   "title": "string",
                   "author": "string",
                   "url": "string",
                   "published_date": "ISO date"
                 }},
                 "metadata": {{
                   "confidence": 0.0-1.0,
                   "estimated_read_time": integer (minutes)
                 }}
               }}
             ]
           }}
           """

           # Call Claude
           response = await self.client.messages.create(
               model="claude-sonnet-4-5-20250929",
               max_tokens=8000,
               temperature=0.3,  # Lower temp for more consistent structure
               system=system_prompt,
               messages=[{"role": "user", "content": user_prompt}]
           )

           # Parse JSON response
           import json
           insights = json.loads(response.content[0].text)

           return insights

       def _build_context(self, chunks: list[dict]) -> str:
           """Format retrieved chunks into context string."""
           context_parts = []
           for i, chunk in enumerate(chunks, 1):
               context_parts.append(f"""
               Source {i}: {chunk['content_title']}
               Author: {chunk.get('author', 'Unknown')}
               URL: {chunk['content_url']}
               Published: {chunk['published_at']}
               Similarity: {chunk['similarity']:.2f}

               Content:
               {chunk['chunk_text']}

               ---
               """)
           return "\n".join(context_parts)
   ```

   **Reasoning:**
   - Claude Sonnet 4.5 for synthesis → best at educational explanations
   - Temperature 0.3 → balance between creativity and consistency
   - Structured JSON output → easier to validate and render
   - First-principles prompting → ensures depth, not just summarization

**End of Day 3 Deliverables:**
- ✅ Query construction from learning context
- ✅ Vector similarity search with hybrid re-ranking
- ✅ Educational synthesis prompt with Claude
- ✅ End-to-end: query → retrieve → synthesize → insights JSON

#### Day 4: Quality Evaluation & MCP Tools

**Morning (4 hours):**
1. **RAGAS Integration**
   ```python
   # src/rag/evaluator.py
   from ragas import evaluate, SingleTurnSample
   from ragas.metrics import Faithfulness, LLMContextPrecisionWithoutReference, NonLLMContextRecall

   class QualityEvaluator:
       def __init__(self):
           self.faithfulness = Faithfulness()
           self.context_precision = LLMContextPrecisionWithoutReference()
           self.context_recall = NonLLMContextRecall()

       async def evaluate_insights(
           self,
           query: str,
           insights: dict,
           retrieved_chunks: list[dict]
       ) -> dict:
           """
           Evaluate quality of generated insights using RAGAS.
           Returns scores for faithfulness, context precision, and context recall.
           """
           # Prepare contexts (retrieved chunk texts)
           contexts = [chunk['chunk_text'] for chunk in retrieved_chunks]

           # Prepare response (concatenated insights)
           response = self._format_insights_for_eval(insights)

           # Create sample
           sample = SingleTurnSample(
               user_input=query,
               response=response,
               retrieved_contexts=contexts
           )

           # Evaluate each metric
           faithfulness_score = await self.faithfulness.single_turn_ascore(sample)
           precision_score = await self.context_precision.single_turn_ascore(sample)
           recall_score = await self.context_recall.single_turn_ascore(sample)

           scores = {
               "faithfulness": faithfulness_score,
               "context_precision": precision_score,
               "context_recall": recall_score,
               "average": (faithfulness_score + precision_score + recall_score) / 3
           }

           return scores

       def _format_insights_for_eval(self, insights: dict) -> str:
           """Format insights into single text for evaluation."""
           texts = []
           for insight in insights['insights']:
               texts.append(f"{insight['title']}: {insight['explanation']}")
           return "\n\n".join(texts)
   ```

2. **Quality Gate Logic**
   ```python
   # src/rag/quality_gate.py
   class QualityGate:
       def __init__(self, min_score: float = 0.70, max_retries: int = 2):
           self.min_score = min_score
           self.max_retries = max_retries

       async def apply_gate(
           self,
           scores: dict,
           synthesize_fn,
           retry_count: int = 0
       ) -> tuple[dict, dict, bool]:
           """
           Apply quality gate. Retry with stricter prompt if scores too low.
           Returns: (insights, final_scores, passed)
           """
           # Check if all scores meet threshold
           if all(score >= self.min_score for score in [
               scores['faithfulness'],
               scores['context_precision'],
               scores['context_recall']
           ]):
               return None, scores, True  # Passed

           # If faithfulness too low and retries available, retry
           if scores['faithfulness'] < self.min_score and retry_count < self.max_retries:
               # Retry with stricter prompt
               stricter_insights = await synthesize_fn(stricter=True)
               new_scores = await evaluator.evaluate_insights(...)
               return await self.apply_gate(new_scores, synthesize_fn, retry_count + 1)

           # Failed quality gate
           return None, scores, False
   ```

**Afternoon (4 hours):**
3. **Implement Core MCP Tools**
   ```python
   # src/server.py (updated)
   from fastmcp import FastMCP
   from datetime import datetime

   mcp = FastMCP("learning-coach")

   @mcp.tool()
   async def generate_daily_digest(
       date: str = "today",
       max_insights: int = 7,
       force_refresh: bool = False
   ) -> dict:
       """
       Generate personalized learning digest for specified date.

       Args:
           date: ISO date string or "today" (default: "today")
           max_insights: Number of insights to generate (3-10, default: 7)
           force_refresh: Skip cache and regenerate (default: False)

       Returns:
           JSON with insights array, sources, and RAGAS scores
       """
       # 1. Check cache (if not force_refresh)
       if not force_refresh:
           cached = await get_cached_digest(user_id, date)
           if cached:
               return cached

       # 2. Build query from memory/context
       query = await build_query_from_memory(user_id)

       # 3. Retrieve relevant chunks
       retriever = VectorRetriever(supabase_url, supabase_key)
       chunks = await retriever.retrieve(query, top_k=15)

       # 4. Synthesize insights
       synthesizer = InsightSynthesizer(anthropic_api_key)
       learning_context = await get_learning_context(user_id)
       insights = await synthesizer.synthesize_insights(chunks, learning_context, max_insights)

       # 5. Evaluate quality
       evaluator = QualityEvaluator()
       scores = await evaluator.evaluate_insights(query, insights, chunks)

       # 6. Apply quality gate
       gate = QualityGate()
       final_insights, final_scores, passed = await gate.apply_gate(scores, ...)

       # 7. Store digest (with cache)
       digest = {
           "date": date,
           "insights": insights['insights'],
           "ragas_scores": final_scores,
           "quality_badge": "✨" if final_scores['average'] > 0.85 else "✓" if passed else "⚠️",
           "generated_at": datetime.now().isoformat()
       }

       await store_digest(user_id, digest)

       return digest

   @mcp.tool()
   async def manage_sources(
       action: str,
       source_type: str = None,
       source_identifier: str = None,
       priority: int = 3
   ) -> dict:
       """
       Manage content sources (add, remove, update, list).

       Args:
           action: "add", "remove", "update", or "list"
           source_type: "rss", "twitter", "reddit", "custom_url"
           source_identifier: URL, handle, or subreddit name
           priority: 1-5 (default: 3)
       """
       if action == "add":
           # Validate source
           valid = await validate_source(source_type, source_identifier)
           if not valid:
               return {"error": "Invalid source or unreachable"}

           # Add to database
           result = db.table("sources").insert({
               "user_id": user_id,
               "type": source_type,
               "identifier": source_identifier,
               "priority": priority,
               "active": True
           }).execute()

           return {"success": True, "message": f"Added {source_identifier}", "source_id": result.data[0]["id"]}

       elif action == "list":
           sources = db.table("sources").select("*").eq("user_id", user_id).execute()
           return {"sources": sources.data}

       # ... implement remove, update

   @mcp.tool()
   async def provide_feedback(
       insight_id: str,
       feedback_type: str,
       reason: str = None
   ) -> str:
       """
       Capture user feedback on an insight.

       Args:
           insight_id: UUID of the insight
           feedback_type: "helpful", "not_relevant", "incorrect", "too_basic", "too_advanced"
           reason: Optional free text explanation (max 500 chars)
       """
       # Store feedback
       db.table("feedback").insert({
           "user_id": user_id,
           "insight_id": insight_id,
           "type": feedback_type,
           "reason": reason,
           "created_at": datetime.now()
       }).execute()

       # Update source priority (async)
       await update_source_priority_from_feedback(insight_id, feedback_type)

       # Update memory with preference signals
       await update_memory_preferences(user_id, feedback_type, reason)

       return "✓ Feedback recorded. Your preferences will influence future digests."

   @mcp.tool()
   async def sync_bootcamp_progress() -> str:
       """Manually sync learning context from 100xEngineers platform."""
       progress = await get_user_progress(user_id)

       # Update memory (via memory MCP server or direct storage)
       await update_learning_context(user_id, progress)

       return f"✓ Synced: Week {progress['current_week']}, Topics: {', '.join(progress['current_topics'])}"

   @mcp.tool()
   async def search_past_insights(
       query: str,
       date_range: dict = None,
       min_feedback_score: int = None
   ) -> dict:
       """
       Search through previously delivered digests.

       Args:
           query: Semantic search query
           date_range: {"start_date": "ISO", "end_date": "ISO"}
           min_feedback_score: Filter by helpful feedback only
       """
       # Generate query embedding
       # Search through generated_digests table (insights are jsonb)
       # Return matching insights with context
       pass
   ```

**End of Day 4 Deliverables:**
- ✅ RAGAS evaluation integrated
- ✅ Quality gate with retry logic
- ✅ 5 core MCP tools implemented (generate_daily_digest, manage_sources, provide_feedback, sync_bootcamp_progress, search_past_insights)
- ✅ End-to-end working: MCP tool call → digest generation → quality evaluation → return

---

### Phase 3: User Interfaces (Days 5-6)

**Objective:** Build interactive UIs for both Claude.ai (MCP Apps) and standalone dashboard (Streamlit)

#### Day 5: MCP UI Resources

**Morning (4 hours):**
1. **Daily Digest Interactive View**
   ```python
   # src/ui/daily_digest.py
   from fastmcp import FastMCP

   @mcp.resource("ui://learning-coach/daily-digest")
   async def daily_digest_ui(digest_data: dict) -> str:
       """
       Interactive daily digest UI (HTML).
       Rendered in Claude.ai via MCP Apps.
       """
       html = f"""
       <!DOCTYPE html>
       <html>
       <head>
           <meta charset="UTF-8">
           <meta name="viewport" content="width=device-width, initial-scale=1.0">
           <style>
               :root {{
                   --bg-primary: #0a0a0a;
                   --bg-secondary: #1a1a1a;
                   --text-primary: #ffffff;
                   --text-secondary: #a0a0a0;
                   --accent: #3b82f6;
                   --success: #10b981;
                   --warning: #f59e0b;
               }}

               body {{
                   background: var(--bg-primary);
                   color: var(--text-primary);
                   font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                   margin: 0;
                   padding: 20px;
                   line-height: 1.6;
               }}

               .digest-header {{
                   border-bottom: 1px solid var(--bg-secondary);
                   padding-bottom: 20px;
                   margin-bottom: 30px;
               }}

               .quality-badge {{
                   display: inline-block;
                   padding: 4px 12px;
                   border-radius: 12px;
                   background: var(--bg-secondary);
                   font-size: 14px;
               }}

               .insight-card {{
                   background: var(--bg-secondary);
                   border-radius: 12px;
                   padding: 24px;
                   margin-bottom: 20px;
                   transition: all 0.2s ease;
               }}

               .insight-card:hover {{
                   transform: translateY(-2px);
                   box-shadow: 0 8px 16px rgba(0,0,0,0.3);
               }}

               .insight-title {{
                   font-size: 20px;
                   font-weight: 600;
                   margin-bottom: 12px;
                   color: var(--accent);
               }}

               .relevance-badge {{
                   background: var(--accent);
                   color: white;
                   padding: 2px 8px;
                   border-radius: 4px;
                   font-size: 12px;
                   margin-left: 8px;
               }}

               .explanation {{
                   color: var(--text-secondary);
                   margin: 16px 0;
                   line-height: 1.8;
               }}

               .explanation.collapsed {{
                   max-height: 150px;
                   overflow: hidden;
                   position: relative;
               }}

               .explanation.collapsed::after {{
                   content: '';
                   position: absolute;
                   bottom: 0;
                   left: 0;
                   right: 0;
                   height: 50px;
                   background: linear-gradient(transparent, var(--bg-secondary));
               }}

               .read-more {{
                   color: var(--accent);
                   cursor: pointer;
                   font-size: 14px;
                   margin-top: 8px;
               }}

               .takeaway {{
                   background: var(--bg-primary);
                   border-left: 3px solid var(--success);
                   padding: 12px 16px;
                   margin: 16px 0;
                   border-radius: 4px;
               }}

               .takeaway-label {{
                   font-weight: 600;
                   color: var(--success);
                   margin-bottom: 8px;
               }}

               .source {{
                   margin-top: 16px;
                   padding-top: 16px;
                   border-top: 1px solid var(--bg-primary);
                   font-size: 14px;
                   color: var(--text-secondary);
               }}

               .source-link {{
                   color: var(--accent);
                   text-decoration: none;
               }}

               .source-link:hover {{
                   text-decoration: underline;
               }}

               .feedback-buttons {{
                   display: flex;
                   gap: 12px;
                   margin-top: 16px;
               }}

               .feedback-btn {{
                   background: var(--bg-primary);
                   border: 1px solid var(--text-secondary);
                   color: var(--text-primary);
                   padding: 8px 16px;
                   border-radius: 8px;
                   cursor: pointer;
                   font-size: 14px;
                   transition: all 0.2s;
               }}

               .feedback-btn:hover {{
                   background: var(--accent);
                   border-color: var(--accent);
               }}

               .feedback-btn.active {{
                   background: var(--success);
                   border-color: var(--success);
               }}
           </style>
       </head>
       <body>
           <div class="digest-header">
               <h1>Your Learning Digest - {digest_data['date']}</h1>
               <span class="quality-badge">{digest_data['quality_badge']} Quality Score: {digest_data['ragas_scores']['average']:.2f}</span>
           </div>

           <div class="insights-container">
               {self._render_insights(digest_data['insights'])}
           </div>

           <script>
               // Expand/collapse functionality
               document.querySelectorAll('.read-more').forEach(btn => {{
                   btn.addEventListener('click', (e) => {{
                       const explanation = e.target.previousElementSibling;
                       explanation.classList.toggle('collapsed');
                       e.target.textContent = explanation.classList.contains('collapsed') ? 'Read more' : 'Read less';
                   }});
               }});

               // Feedback handling
               document.querySelectorAll('.feedback-btn').forEach(btn => {{
                   btn.addEventListener('click', async (e) => {{
                       const insightId = e.target.dataset.insightId;
                       const feedbackType = e.target.dataset.feedbackType;

                       // Send message to MCP server
                       window.parent.postMessage({{
                           type: 'mcp-tool-call',
                           tool: 'provide_feedback',
                           params: {{
                               insight_id: insightId,
                               feedback_type: feedbackType
                           }}
                       }}, '*');

                       // Visual feedback
                       e.target.classList.add('active');
                       e.target.textContent = '✓ ' + e.target.textContent;
                   }});
               }});
           </script>
       </body>
       </html>
       """
       return html

   def _render_insights(self, insights: list) -> str:
       """Render individual insight cards."""
       cards = []
       for insight in insights:
           card = f"""
           <div class="insight-card">
               <div class="insight-title">
                   {insight['title']}
                   <span class="relevance-badge">Relevant</span>
               </div>

               <div class="explanation collapsed">
                   {insight['explanation']}
               </div>
               <div class="read-more">Read more</div>

               <div class="takeaway">
                   <div class="takeaway-label">💡 Practical Takeaway</div>
                   {insight['practical_takeaway']}
               </div>

               <div class="source">
                   <strong>Source:</strong> {insight['source']['title']} by {insight['source']['author']}<br>
                   <a href="{insight['source']['url']}" target="_blank" class="source-link">Read full article →</a>
               </div>

               <div class="feedback-buttons">
                   <button class="feedback-btn" data-insight-id="{insight.get('id', '')}" data-feedback-type="helpful">
                       👍 Helpful
                   </button>
                   <button class="feedback-btn" data-insight-id="{insight.get('id', '')}" data-feedback-type="not_relevant">
                       👎 Not Relevant
                   </button>
               </div>
           </div>
           """
           cards.append(card)

       return "\n".join(cards)
   ```

   **Reasoning:**
   - Dark theme (black background) → easier on eyes for daily reading
   - Collapsible explanations → prevents overwhelming with text
   - Inline feedback → frictionless user feedback loop
   - Sandboxed iframe → security built-in via MCP Apps spec

**Afternoon (4 hours):**
2. **Weekly Summary Dashboard UI**
   ```python
   # src/ui/weekly_summary.py

   @mcp.resource("ui://learning-coach/weekly-summary")
   async def weekly_summary_ui(summary_data: dict) -> str:
       """Interactive weekly summary with visualizations."""
       # Similar structure to daily digest but with:
       # - Progress charts (topics covered vs expected)
       # - Top 10 insights grid
       # - Learning analytics
       # - Upcoming topics preview
       # Uses Chart.js for visualizations
       pass
   ```

3. **Source Manager UI**
   ```python
   # src/ui/source_manager.py

   @mcp.resource("ui://learning-coach/sources")
   async def source_manager_ui(sources_data: dict) -> str:
       """Interactive source management interface."""
       # Features:
       # - List all sources with priority sliders
       # - Toggle active/inactive
       # - Add new source form
       # - Source statistics (articles fetched, feedback)
       pass
   ```

**End of Day 5 Deliverables:**
- ✅ Daily digest interactive UI (HTML + CSS + JS)
- ✅ Weekly summary UI template
- ✅ Source manager UI template
- ✅ MCP Apps postMessage communication working
- ✅ UIs render correctly in Claude.ai

#### Day 6: Streamlit Dashboard

**All Day (8 hours):**
1. **Dashboard Structure**
   ```python
   # dashboard/app.py
   import streamlit as st
   from datetime import datetime, timedelta
   import pandas as pd
   import plotly.express as px

   # Page config
   st.set_page_config(
       page_title="AI Learning Coach",
       page_icon="🎓",
       layout="wide",
       initial_sidebar_state="expanded"
   )

   # Custom CSS
   st.markdown("""
   <style>
       .main { background-color: #0a0a0a; color: #ffffff; }
       .stButton>button { background-color: #3b82f6; color: white; }
       .insight-card { background: #1a1a1a; padding: 20px; border-radius: 12px; margin: 10px 0; }
   </style>
   """, unsafe_allow_html=True)

   # Sidebar navigation
   page = st.sidebar.radio(
       "Navigation",
       ["🏠 Today's Digest", "🔍 Search", "📊 Analytics", "⚙️ Settings"]
   )

   # Current week indicator
   st.sidebar.markdown("---")
   st.sidebar.markdown("### Current Progress")
   st.sidebar.metric("Week", "7 / 24")
   st.sidebar.progress(7/24)

   if page == "🏠 Today's Digest":
       show_daily_digest()
   elif page == "🔍 Search":
       show_search_page()
   elif page == "📊 Analytics":
       show_analytics_page()
   elif page == "⚙️ Settings":
       show_settings_page()
   ```

2. **Home Page (Today's Digest)**
   ```python
   def show_daily_digest():
       st.title("📚 Today's Learning Digest")

       col1, col2, col3 = st.columns([2, 1, 1])
       with col1:
           st.markdown(f"### {datetime.now().strftime('%B %d, %Y')}")
       with col2:
           if st.button("🔄 Refresh Digest"):
               with st.spinner("Generating fresh insights..."):
                   digest = generate_daily_digest(force_refresh=True)
                   st.session_state['digest'] = digest
       with col3:
           week_topics = "Transformers, Attention"
           st.markdown(f"**Focus:** {week_topics}")

       # Load or generate digest
       if 'digest' not in st.session_state:
           with st.spinner("Loading today's digest..."):
               digest = generate_daily_digest()
               st.session_state['digest'] = digest
       else:
           digest = st.session_state['digest']

       # Quality badge
       quality_badge = digest['quality_badge']
       avg_score = digest['ragas_scores']['average']
       st.markdown(f"**Quality:** {quality_badge} {avg_score:.2f}")

       # Render insights
       for idx, insight in enumerate(digest['insights']):
           render_insight_card(insight, idx)

   def render_insight_card(insight, idx):
       with st.container():
           st.markdown(f"""
           <div class="insight-card">
               <h3>{insight['title']}</h3>
               <span style="background: #3b82f6; padding: 2px 8px; border-radius: 4px; font-size: 12px;">
                   Relevant to Week 7
               </span>
           </div>
           """, unsafe_allow_html=True)

           # Expandable explanation
           with st.expander("📖 Read Explanation"):
               st.write(insight['explanation'])

           # Practical takeaway (always visible)
           st.info(f"💡 **Takeaway:** {insight['practical_takeaway']}")

           # Source
           st.markdown(f"""
           **Source:** [{insight['source']['title']}]({insight['source']['url']}) by {insight['source']['author']}
           Published: {insight['source']['published_date']}
           """)

           # Feedback buttons
           col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
           with col1:
               if st.button("👍 Helpful", key=f"helpful_{idx}"):
                   provide_feedback(insight['id'], "helpful")
                   st.success("Feedback recorded!")
           with col2:
               if st.button("👎 Not Relevant", key=f"not_relevant_{idx}"):
                   provide_feedback(insight['id'], "not_relevant")
                   st.info("Feedback recorded!")

           st.markdown("---")
   ```

3. **Search Page**
   ```python
   def show_search_page():
       st.title("🔍 Search Past Insights")

       # Search interface
       query = st.text_input("Search for topics, concepts, or questions...")

       col1, col2 = st.columns(2)
       with col1:
           date_range = st.date_input(
               "Date Range",
               value=(datetime.now() - timedelta(days=30), datetime.now())
           )
       with col2:
           feedback_filter = st.selectbox(
               "Filter by Feedback",
               ["All", "Helpful Only", "Not Reviewed"]
           )

       if st.button("Search"):
           with st.spinner("Searching..."):
               results = search_past_insights(
                   query=query,
                   date_range=date_range,
                   feedback_filter=feedback_filter
               )

               st.write(f"Found {len(results)} insights")

               for result in results:
                   render_search_result(result)
   ```

4. **Analytics Page**
   ```python
   def show_analytics_page():
       st.title("📊 Learning Analytics")

       # Key metrics (top row)
       col1, col2, col3, col4 = st.columns(4)
       with col1:
           st.metric("Total Insights", "142", "+7 this week")
       with col2:
           st.metric("Helpful Rate", "85%", "+3%")
       with col3:
           st.metric("Time Saved", "18 hours", "+3 hours")
       with col4:
           st.metric("Current Week", "7 / 24", "29%")

       # Progress chart
       st.subheader("Learning Progress Over Time")
       progress_data = get_learning_progress_data()
       fig = px.line(
           progress_data,
           x='week',
           y='topics_covered',
           title='Topics Covered per Week'
       )
       st.plotly_chart(fig, use_container_width=True)

       # Topic engagement heatmap
       col1, col2 = st.columns(2)
       with col1:
           st.subheader("Topic Engagement")
           topic_data = get_topic_engagement_data()
           fig = px.bar(topic_data, x='topic', y='engagement_score')
           st.plotly_chart(fig)

       with col2:
           st.subheader("Source Contribution")
           source_data = get_source_contribution_data()
           fig = px.pie(source_data, values='insights_count', names='source_name')
           st.plotly_chart(fig)

       # Insights
       st.subheader("📈 Key Insights")
       st.success("✅ **Most Engaged Topics:** Transformers, Attention Mechanisms, RAG Systems")
       st.warning("⚠️ **Topics Needing Review:** Backpropagation Math, Gradient Descent")
       st.info("💡 **Recommended Next:** Multi-Modal Learning, Vision Transformers")
   ```

5. **Settings Page**
   ```python
   def show_settings_page():
       st.title("⚙️ Settings")

       # Learning Context (read-only, managed by memory)
       st.subheader("Learning Context")
       st.info("Your learning context is automatically synced from 100xEngineers bootcamp.")

       col1, col2 = st.columns(2)
       with col1:
           st.text_input("Current Week", value="7", disabled=True)
           st.text_area("Current Topics", value="Transformers\nAttention Mechanisms", disabled=True)
       with col2:
           difficulty = st.selectbox("Difficulty Level", ["Beginner", "Intermediate", "Advanced"], index=1)
           st.text_area("Learning Goal", value="Build chatbot with RAG")

       if st.button("Save Preferences"):
           st.success("Preferences saved!")

       # Digest Preferences
       st.subheader("Digest Preferences")
       col1, col2 = st.columns(2)
       with col1:
           max_insights = st.slider("Max Insights per Digest", 3, 10, 7)
           explanation_style = st.selectbox(
               "Explanation Style",
               ["Technical (detailed)", "ELI5 (simple)", "Visual (diagrams)"]
           )
       with col2:
           response_length = st.selectbox("Response Length", ["Concise", "Detailed"])
           enable_email = st.checkbox("Email Daily Digest")

       # Source Management
       st.subheader("Content Sources")
       st.markdown("Manage your content sources")

       if st.button("Go to Source Manager"):
           st.info("Opening source manager...")

       # Privacy
       st.subheader("Privacy & Data")
       if st.button("View Memory Contents"):
           memory = get_memory_contents()
           st.json(memory)

       if st.button("Clear All Memories", type="secondary"):
           if st.confirm("Are you sure? This cannot be undone."):
               clear_all_memories()
               st.success("Memories cleared")

       if st.button("Export All Data"):
           data = export_all_user_data()
           st.download_button("Download Data", data, "learning_coach_data.json")
   ```

**End of Day 6 Deliverables:**
- ✅ Streamlit dashboard with 4 pages
- ✅ Interactive charts with Plotly
- ✅ Source management interface
- ✅ Settings page with preferences
- ✅ Responsive design (works on mobile)
- ✅ Deployed to Streamlit Cloud or local Docker

---

### Phase 4: Testing & Polish (Day 7)

**Objective:** Comprehensive testing, documentation, deployment, and first user onboarding

#### Day 7: Testing, Documentation & Launch

**Morning (4 hours): Testing**

1. **End-to-End Testing**
   ```python
   # tests/test_e2e.py
   import pytest
   from datetime import datetime

   @pytest.mark.asyncio
   async def test_full_digest_generation():
       """Test complete flow from MCP tool call to digest delivery."""
       # 1. Add test sources
       result = await manage_sources(
           action="add",
           source_type="rss",
           source_identifier="https://lilianweng.github.io/feed.xml",
           priority=5
       )
       assert result['success']

       # 2. Trigger ingestion (simulate or run actual)
       await orchestrator.ingest_content(result['source_id'])

       # 3. Generate digest
       digest = await generate_daily_digest(date="today", max_insights=7)

       # 4. Verify structure
       assert 'insights' in digest
       assert len(digest['insights']) <= 7
       assert all('title' in insight for insight in digest['insights'])
       assert all('explanation' in insight for insight in digest['insights'])

       # 5. Verify RAGAS scores
       assert 'ragas_scores' in digest
       assert digest['ragas_scores']['faithfulness'] > 0.0
       assert digest['ragas_scores']['average'] > 0.0

   @pytest.mark.asyncio
   async def test_feedback_loop():
       """Test feedback processing and source priority adjustment."""
       # Generate digest
       digest = await generate_daily_digest()
       insight_id = digest['insights'][0]['id']

       # Provide positive feedback
       await provide_feedback(insight_id, "helpful")

       # Verify feedback stored
       feedback = db.table("feedback").select("*").eq("insight_id", insight_id).execute()
       assert len(feedback.data) > 0

       # Verify source priority adjusted (check source table)
       # ... implementation

   @pytest.mark.asyncio
   async def test_quality_gate():
       """Test RAGAS evaluation and quality gate logic."""
       # Create low-quality synthetic response
       bad_insights = {
           "insights": [{
               "title": "Random content",
               "explanation": "This is completely unrelated.",
               "practical_takeaway": "Nothing useful",
               "source": {"title": "Test", "url": "http://example.com"}
           }]
       }

       # Evaluate
       scores = await evaluator.evaluate_insights(
           query="Explain transformers",
           insights=bad_insights,
           retrieved_chunks=[...]
       )

       # Should fail quality gate
       assert scores['faithfulness'] < 0.70 or scores['average'] < 0.70
   ```

2. **Performance Testing**
   ```python
   # tests/test_performance.py
   import time

   @pytest.mark.asyncio
   async def test_digest_generation_latency():
       """Ensure digest generation completes within 15 seconds."""
       start = time.time()
       digest = await generate_daily_digest()
       elapsed = time.time() - start

       assert elapsed < 15.0, f"Digest generation took {elapsed}s (target: <15s)"

   @pytest.mark.asyncio
   async def test_vector_search_latency():
       """Ensure vector search completes within 2 seconds."""
       retriever = VectorRetriever(...)

       start = time.time()
       results = await retriever.retrieve("test query", top_k=15)
       elapsed = time.time() - start

       assert elapsed < 2.0, f"Vector search took {elapsed}s (target: <2s)"
   ```

3. **Security Testing**
   - Verify RLS policies in Supabase
   - Test input validation for source URLs
   - Check for SQL injection vulnerabilities
   - Verify iframe sandboxing in MCP Apps

**Afternoon (4 hours): Documentation & Deployment**

4. **User Documentation**
   ```markdown
   # AI Learning Coach - Quick Start Guide

   ## Installation (5 minutes)

   ### Step 1: Install MCP Server
   1. Clone repository: `git clone https://github.com/your-org/learning-coach-mcp.git`
   2. Install dependencies: `cd learning-coach-mcp && uv install`
   3. Set environment variables:
      ```bash
      export SUPABASE_URL="your-project-url"
      export SUPABASE_KEY="your-api-key"
      export OPENAI_API_KEY="your-openai-key"
      export ANTHROPIC_API_KEY="your-anthropic-key"
      ```

   ### Step 2: Configure Claude Desktop
   Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "learning-coach": {
         "command": "uv",
         "args": ["run", "python", "/path/to/learning-coach-mcp/src/server.py"],
         "env": {
           "SUPABASE_URL": "your-url",
           "SUPABASE_KEY": "your-key"
         }
       }
     }
   }
   ```

   ### Step 3: Restart Claude Desktop
   Quit Claude Desktop completely and relaunch.

   ### Step 4: First Digest
   In Claude.ai chat:
   - "Add my favorite AI blogs as sources" (guides you through adding sources)
   - "Generate my first daily digest"

   ## Using the Dashboard
   Run Streamlit dashboard:
   ```bash
   cd dashboard
   streamlit run app.py
   ```

   Open browser to http://localhost:8501

   ## FAQ

   **Q: Why is my digest not relevant?**
   A: Provide feedback! Use thumbs down on irrelevant insights. The system learns from your feedback.

   **Q: How does memory work?**
   A: Claude automatically remembers your learning context (week, topics, preferences) across sessions.

   **Q: Can I use custom sources?**
   A: Yes! Use "Add source" in Settings → Sources. Supports RSS, Twitter, custom URLs.
   ```

5. **Developer Documentation**
   - Architecture diagram
   - API reference for all 9 tools
   - Database schema documentation
   - Deployment guide (Heroku, Docker, Railway)

6. **Deploy to Production**
   ```bash
   # Option 1: Heroku
   heroku create learning-coach-api
   git push heroku main

   # Option 2: Docker
   docker build -t learning-coach-mcp .
   docker run -p 8000:8000 --env-file .env learning-coach-mcp

   # Option 3: Railway
   railway init
   railway up
   ```

7. **First User Onboarding (Sowmya)**
   - Schedule 30-minute onboarding call
   - Walk through:
     1. Installation verification
     2. Adding 3-5 trusted sources
     3. Generating first digest
     4. Providing feedback
     5. Exploring dashboard
   - Gather qualitative feedback
   - Set up daily check-in for first 3 days

**End of Day 7 Deliverables:**
- ✅ Comprehensive test suite (E2E, performance, security)
- ✅ User documentation (Quick Start, FAQ, Troubleshooting)
- ✅ Developer documentation (Architecture, API, Deployment)
- ✅ Production deployment (MCP server + Streamlit dashboard)
- ✅ First user onboarded (Sowmya)
- ✅ Monitoring and alerts configured

---

## Implementation Priorities (MVP vs Nice-to-Have)

### Must-Have for MVP (Blocking Launch)
- [x] Supabase database with vector search
- [x] MCP server with 5 core tools:
  - `generate_daily_digest`
  - `manage_sources`
  - `provide_feedback`
  - `sync_bootcamp_progress`
  - `search_past_insights`
- [x] Content ingestion (RSS + custom URLs)
- [x] RAG pipeline (retrieve + synthesize)
- [x] RAGAS evaluation (faithfulness, precision, recall)
- [x] Daily digest MCP App UI
- [x] Streamlit dashboard (Home, Analytics, Settings pages)
- [x] Memory integration for context tracking
- [x] Feedback loop (feedback → source priority adjustment)

### Should-Have (Launch with Caveats)
- [ ] Twitter/X content fetcher
- [ ] Reddit content fetcher
- [ ] Weekly summary generation
- [ ] Email delivery
- [ ] Source manager UI (can use Settings page for MVP)
- [ ] Search page in dashboard

### Nice-to-Have (Post-MVP)
- [ ] Export to Notion/Obsidian
- [ ] Fresh content search (web search for breaking news)
- [ ] Learning patterns analysis tool
- [ ] Knowledge gap detection
- [ ] Spaced repetition reminders
- [ ] Collaborative features

---

## Risk Mitigation Strategies

### Technical Risks

**RISK: RAGAS scores consistently low**
- **Mitigation Plan:**
  - Pre-launch: Test with 20+ diverse queries, manually review quality
  - If scores < 0.70: Iterate on synthesis prompt, add more context to retrieval
  - Fallback: Launch with lower threshold (0.60) but show warning badge to user

**RISK: Vector search returns irrelevant results**
- **Mitigation Plan:**
  - A/B test similarity thresholds (0.65, 0.70, 0.75)
  - Implement diversity boosting (ensure ≥3 different sources in top-k)
  - Add metadata filtering (date range, source priority)
  - User feedback loop: "not relevant" directly retrains ranking

**RISK: Memory system doesn't track context accurately**
- **Mitigation Plan:**
  - Implement fallback: Manual context update tool
  - Cache memory state in database (redundancy)
  - Weekly verification: Ask user "Is this context correct?"
  - If memory fails: Use database-stored learning_progress table

**RISK: API rate limits hit**
- **Mitigation Plan:**
  - Monitor usage daily (set up alerts at 80% of limits)
  - Implement aggressive caching (6-hour digest cache)
  - Batch embedding generation (reduce API calls)
  - Budget allocated for API tier upgrades if needed

### User Experience Risks

**RISK: Insights not actually relevant to user's learning**
- **Mitigation Plan:**
  - Daily check-ins with Sowmya (first 3 days)
  - Gather qualitative feedback: "Which insights were most helpful?"
  - Quick iteration on synthesis prompt based on feedback
  - A/B test different prompt approaches
  - Success metric: 80%+ helpful rate within 2 weeks

**RISK: User doesn't trust memory-based automation**
- **Mitigation Plan:**
  - Transparency: Settings page shows full memory contents
  - Control: Manual override always available
  - Clear explanation during onboarding: "Memory tracks X, Y, Z"
  - Easy memory editing/deletion
  - Opt-out option: User can disable memory, use manual context

### Deployment Risks

**RISK: Infrastructure costs exceed budget**
- **Mitigation Plan:**
  - Use free tiers where possible:
    - Supabase: Free tier (500MB, 50k MAU)
    - Streamlit Cloud: Free tier (1 app)
  - Monitor costs daily via dashboard
  - Optimize:
    - Use halfvec (saves 50% storage)
    - Cache embeddings (don't re-embed same content)
    - Batch API calls
  - Alert at $8/day (target: <$10/day)

---

## Success Criteria for MVP

### Quantitative Metrics
- ✅ RAGAS scores average > 0.70 across 10 test digests
- ✅ User helpful rate > 80% (after 2 weeks)
- ✅ Digest generation time < 15 seconds (P95)
- ✅ Vector search latency < 2 seconds (P95)
- ✅ Zero critical bugs in core flow
- ✅ Operate within $10/day cost

### Qualitative Metrics
- ✅ Sowmya reports time saved ≥ 10 hours/week
- ✅ User finds insights "highly relevant" (survey)
- ✅ User uses product 5+ days/week
- ✅ User recommends to fellow bootcamp students

### Technical Validation
- ✅ All 5 core MCP tools working end-to-end
- ✅ Memory correctly tracks learning context
- ✅ Feedback loop demonstrably improves future digests
- ✅ Both access methods work (Claude.ai + dashboard)
- ✅ Content ingestion pipeline runs without errors

---

## Post-Launch Plan (Week 2)

### Daily Monitoring (Days 8-14)
- **Metrics to Watch:**
  - RAGAS scores (should maintain > 0.70)
  - User feedback rate (5-10 events/day expected)
  - System errors (monitor Sentry)
  - API usage (ensure under limits)

- **User Check-ins:**
  - Daily Slack message with Sowmya (Days 8-10)
  - Ask: "Which insights were most helpful today?"
  - Gather: Pain points, confusion, feature requests

- **Expected Adjustments:**
  - Tune retrieval parameters (similarity threshold, top-k)
  - Refine synthesis prompt based on feedback
  - Adjust source priorities
  - Fix any UX issues

### Week 2 Retrospective
- Review all metrics vs targets
- Analyze feedback patterns
- Prioritize "nice-to-have" features for next sprint
- Plan wider rollout (if metrics meet targets)

---

## Task Checklist

### Pre-Development Setup
- [ ] Set up Supabase project
- [ ] Obtain API keys (OpenAI, Anthropic, 100xEngineers)
- [ ] Create GitHub repository
- [ ] Set up development environment

### Day 1: Foundation
- [ ] Create database schema with all 6 tables
- [ ] Enable pgvector extension
- [ ] Create HNSW index on embeddings
- [ ] Set up RLS policies
- [ ] Initialize MCP server project
- [ ] Install all dependencies
- [ ] Create basic MCP server with stub tools
- [ ] Set up memory MCP server
- [ ] Configure Claude Desktop
- [ ] Mock bootcamp API integration
- [ ] Test: MCP server loads in Claude Desktop

### Day 2: Ingestion
- [ ] Build RSS feed fetcher
- [ ] Implement chunking algorithm
- [ ] Create embedding generation pipeline
- [ ] Build ingestion orchestrator
- [ ] Set up APScheduler for background jobs
- [ ] Test: RSS → chunks → embeddings → database
- [ ] Verify: Embeddings stored correctly in Supabase

### Day 3: RAG Pipeline
- [ ] Implement query builder from memory
- [ ] Create Supabase RPC function (match_embeddings)
- [ ] Build vector retriever with hybrid ranking
- [ ] Develop educational synthesis prompt
- [ ] Integrate Claude Sonnet 4.5
- [ ] Test: Query → retrieve → synthesize → insights
- [ ] Verify: Insights have proper structure

### Day 4: Quality & Tools
- [ ] Install RAGAS
- [ ] Implement faithfulness evaluation
- [ ] Implement context precision evaluation
- [ ] Implement context recall evaluation
- [ ] Create quality gate logic
- [ ] Implement generate_daily_digest tool
- [ ] Implement manage_sources tool
- [ ] Implement provide_feedback tool
- [ ] Implement sync_bootcamp_progress tool
- [ ] Implement search_past_insights tool
- [ ] Test: End-to-end MCP tool call → digest with RAGAS scores

### Day 5: MCP UIs
- [ ] Create daily digest HTML template
- [ ] Style with dark theme CSS
- [ ] Add interactive elements (expand/collapse, feedback buttons)
- [ ] Implement postMessage communication
- [ ] Create weekly summary UI template
- [ ] Create source manager UI template
- [ ] Test: UIs render in Claude.ai
- [ ] Verify: Feedback buttons work

### Day 6: Streamlit Dashboard
- [ ] Set up Streamlit project
- [ ] Create navigation structure
- [ ] Build Home page (Today's Digest)
- [ ] Build Search page
- [ ] Build Analytics page with charts
- [ ] Build Settings page
- [ ] Add custom CSS styling
- [ ] Test: All pages work locally
- [ ] Deploy to Streamlit Cloud
- [ ] Verify: Dashboard accessible online

### Day 7: Testing & Launch
- [ ] Write E2E tests
- [ ] Write performance tests
- [ ] Run security audit
- [ ] Write Quick Start Guide
- [ ] Write FAQ
- [ ] Create architecture diagram
- [ ] Document all API tools
- [ ] Deploy MCP server to production
- [ ] Configure monitoring (Sentry)
- [ ] Set up cost alerts
- [ ] Onboard Sowmya (first user)
- [ ] Gather initial feedback
- [ ] Create post-launch monitoring dashboard

---

## Cost Estimate (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| OpenAI Embeddings | ~500k tokens/day | ~$10/month |
| Claude Sonnet 4.5 | ~50 digests/day, 8k tokens/digest | ~$120/month |
| Supabase | 500MB database, 50k MAU | Free tier |
| Streamlit Cloud | 1 app | Free tier |
| Monitoring (Sentry) | <10k events/month | Free tier |
| **Total** | | **~$130/month** ($4.30/day) |

**Well under $10/day target** ✅

---

## Appendix: Key Commands

### Development
```bash
# Start MCP server in dev mode
mcp dev src/server.py

# Run Streamlit dashboard
cd dashboard && streamlit run app.py

# Run tests
pytest tests/ -v

# Run background ingestion worker
python -m src.ingestion.worker
```

### Deployment
```bash
# Build Docker image
docker build -t learning-coach-mcp .

# Run with Docker
docker run -p 8000:8000 --env-file .env learning-coach-mcp

# Deploy to Heroku
git push heroku main

# Deploy Streamlit
cd dashboard && streamlit deploy app.py
```

### Database
```bash
# Run migrations
python -m src.db.migrate

# Seed test data
python -m src.db.seed

# Backup database
supabase db dump > backup.sql
```

---

## Contact & Support

**Developer:** [Your Name]
**User (MVP):** Sowmya
**Repository:** https://github.com/your-org/learning-coach-mcp
**Documentation:** https://docs.learning-coach.ai

---

## Next Steps After Plan Approval

Once you approve this plan:

1. **I will ask clarifying questions** about:
   - 100xEngineers API access (real vs mock for MVP)
   - Preferred deployment platform (Heroku, Railway, Docker)
   - Any specific design preferences for dashboard

2. **I will create task tracking** using TodoWrite tool

3. **We'll begin Day 1** implementation immediately

Please review this plan and let me know:
- ✅ Approve as-is and start implementation
- 🔄 Request changes or clarifications
- ❓ Ask questions about specific technical decisions

---

**Ready to build? Let's create an amazing learning coach! 🚀**
