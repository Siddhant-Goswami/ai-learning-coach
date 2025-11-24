-- Insert test data for development
-- Run this in Supabase SQL Editor to bypass RLS

-- Insert test user
INSERT INTO users (id, email, metadata) VALUES
    ('00000000-0000-0000-0000-000000000001', 'test@example.com', '{"role": "test_user"}'::jsonb)
ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    metadata = EXCLUDED.metadata;

-- Insert learning progress for test user
INSERT INTO learning_progress (user_id, current_week, current_topics, difficulty_level, learning_goals) VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        7,
        ARRAY['Attention Mechanisms', 'Transformers', 'Multi-Head Attention'],
        'intermediate',
        'Build chatbot with RAG'
    )
ON CONFLICT (user_id) DO UPDATE SET
    current_week = EXCLUDED.current_week,
    current_topics = EXCLUDED.current_topics,
    difficulty_level = EXCLUDED.difficulty_level,
    learning_goals = EXCLUDED.learning_goals,
    updated_at = NOW();

-- Insert test content sources
INSERT INTO sources (user_id, type, identifier, priority, active, metadata) VALUES
    (
        '00000000-0000-0000-0000-000000000001',
        'rss',
        'https://lilianweng.github.io/index.xml',
        5,
        true,
        '{"title": "Lilian Weng''s Blog", "description": "ML research and insights"}'::jsonb
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'rss',
        'https://distill.pub/rss.xml',
        5,
        true,
        '{"title": "Distill.pub", "description": "Clear explanations of ML concepts"}'::jsonb
    ),
    (
        '00000000-0000-0000-0000-000000000001',
        'rss',
        'https://huggingface.co/blog/feed.xml',
        4,
        true,
        '{"title": "Hugging Face Blog", "description": "Latest in NLP and transformers"}'::jsonb
    )
ON CONFLICT (user_id, identifier) DO UPDATE SET
    priority = EXCLUDED.priority,
    active = EXCLUDED.active,
    metadata = EXCLUDED.metadata;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Test data inserted successfully!';
    RAISE NOTICE 'Test User ID: 00000000-0000-0000-0000-000000000001';
    RAISE NOTICE 'Sources created: 3';
END $$;
