-- AI Learning Coach Database Schema
-- Run this in your Supabase SQL Editor

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Content sources table
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('rss', 'twitter', 'reddit', 'custom_url', 'youtube')),
    identifier TEXT NOT NULL, -- URL, handle, subreddit name
    priority INTEGER DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    active BOOLEAN DEFAULT true,
    health_score FLOAT DEFAULT 1.0 CHECK (health_score BETWEEN 0.0 AND 1.0),
    last_fetched TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(user_id, identifier)
);

-- Raw content table
CREATE TABLE content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES sources(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    author TEXT,
    published_at TIMESTAMPTZ,
    url TEXT UNIQUE NOT NULL,
    content_hash TEXT UNIQUE NOT NULL, -- MD5 hash for deduplication
    raw_text TEXT NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Embeddings table (chunks with vectors)
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content_id UUID REFERENCES content(id) ON DELETE CASCADE,
    chunk_sequence INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding halfvec(1536), -- Using halfvec for 50% space savings
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(content_id, chunk_sequence)
);

-- Feedback table
CREATE TABLE feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    insight_id UUID NOT NULL, -- Reference to generated insight
    content_id UUID REFERENCES content(id) ON DELETE SET NULL,
    type TEXT NOT NULL CHECK (type IN ('helpful', 'not_relevant', 'incorrect', 'too_basic', 'too_advanced')),
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generated digests table (cache + history)
CREATE TABLE generated_digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    digest_date DATE NOT NULL,
    insights JSONB NOT NULL, -- Array of insight objects
    ragas_scores JSONB, -- Quality metrics
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    cache_expires_at TIMESTAMPTZ, -- For 6-hour caching
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(user_id, digest_date)
);

-- Learning progress table (backup for memory)
CREATE TABLE learning_progress (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current_week INTEGER CHECK (current_week BETWEEN 1 AND 24),
    current_topics TEXT[], -- Array of topic strings
    completed_weeks INTEGER[],
    difficulty_level TEXT CHECK (difficulty_level IN ('beginner', 'intermediate', 'advanced')),
    learning_goals TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance

-- HNSW index for vector similarity search (best recall and speed)
CREATE INDEX embeddings_vector_idx ON embeddings
USING hnsw (embedding halfvec_cosine_ops);

-- B-tree indexes for common queries
CREATE INDEX idx_content_published ON content(published_at DESC);
CREATE INDEX idx_content_source ON content(source_id);
CREATE INDEX idx_sources_user_active ON sources(user_id, active);
CREATE INDEX idx_feedback_user ON feedback(user_id, created_at DESC);
CREATE INDEX idx_digests_user_date ON generated_digests(user_id, digest_date DESC);
CREATE INDEX idx_embeddings_content ON embeddings(content_id);

-- GIN index for JSONB metadata searching
CREATE INDEX idx_content_metadata ON content USING GIN (metadata);
CREATE INDEX idx_sources_metadata ON sources USING GIN (metadata);

-- Enable Row Level Security (RLS) for multi-tenant isolation
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE content ENABLE ROW LEVEL SECURITY;
ALTER TABLE embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE generated_digests ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_progress ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only access their own data)

-- Users can read their own profile
CREATE POLICY "Users can view own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

-- Users can manage their own sources
CREATE POLICY "Users can manage own sources"
    ON sources FOR ALL
    USING (auth.uid() = user_id);

-- Users can only see content from their sources
CREATE POLICY "Users can view own content"
    ON content FOR SELECT
    USING (
        source_id IN (
            SELECT id FROM sources WHERE user_id = auth.uid()
        )
    );

-- Users can only see embeddings from their content
CREATE POLICY "Users can view own embeddings"
    ON embeddings FOR SELECT
    USING (
        content_id IN (
            SELECT c.id FROM content c
            JOIN sources s ON c.source_id = s.id
            WHERE s.user_id = auth.uid()
        )
    );

-- Users can manage their own feedback
CREATE POLICY "Users can manage own feedback"
    ON feedback FOR ALL
    USING (auth.uid() = user_id);

-- Users can manage their own digests
CREATE POLICY "Users can manage own digests"
    ON generated_digests FOR ALL
    USING (auth.uid() = user_id);

-- Users can manage their own learning progress
CREATE POLICY "Users can manage own progress"
    ON learning_progress FOR ALL
    USING (auth.uid() = user_id);

-- Create RPC function for vector similarity search
CREATE OR REPLACE FUNCTION match_embeddings(
    query_embedding halfvec(1536),
    match_threshold float DEFAULT 0.70,
    match_count int DEFAULT 15,
    filter_user_id uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    content_id uuid,
    chunk_text text,
    chunk_sequence int,
    similarity float,
    content_title text,
    content_url text,
    content_author text,
    published_at timestamptz,
    source_id uuid,
    source_priority int
)
LANGUAGE sql STABLE
AS $$
    SELECT
        e.id,
        e.content_id,
        e.chunk_text,
        e.chunk_sequence,
        1 - (e.embedding <=> query_embedding) AS similarity,
        c.title AS content_title,
        c.url AS content_url,
        c.author AS content_author,
        c.published_at,
        c.source_id,
        s.priority AS source_priority
    FROM embeddings e
    JOIN content c ON e.content_id = c.id
    JOIN sources s ON c.source_id = s.id
    WHERE
        1 - (e.embedding <=> query_embedding) > match_threshold
        AND s.active = true
        AND (filter_user_id IS NULL OR s.user_id = filter_user_id)
    ORDER BY e.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Create function to update source health score
CREATE OR REPLACE FUNCTION update_source_health(
    source_id_param uuid,
    success boolean
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE sources
    SET
        health_score = CASE
            WHEN success THEN LEAST(health_score + 0.1, 1.0)
            ELSE GREATEST(health_score - 0.2, 0.0)
        END,
        last_fetched = NOW()
    WHERE id = source_id_param;
END;
$$;

-- Insert default test user (for development)
INSERT INTO users (id, email, metadata) VALUES
    ('00000000-0000-0000-0000-000000000001', 'test@example.com', '{"role": "test_user"}')
ON CONFLICT (email) DO NOTHING;

-- Insert default learning progress for test user
INSERT INTO learning_progress (user_id, current_week, current_topics, difficulty_level, learning_goals) VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        7,
        ARRAY['Attention Mechanisms', 'Transformers', 'Multi-Head Attention'],
        'intermediate',
        'Build chatbot with RAG'
    )
ON CONFLICT (user_id) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'AI Learning Coach database schema created successfully!';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Enable pgvector extension if not already enabled';
    RAISE NOTICE '2. Test vector search with: SELECT match_embeddings(...)';
    RAISE NOTICE '3. Configure RLS policies for production';
END $$;
