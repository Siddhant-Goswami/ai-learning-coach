-- Add RLS policies to allow anon key access to test user data
-- This is needed for development/testing

-- Allow anyone to view the test user (for development)
CREATE POLICY "Allow anon access to test user"
    ON users FOR SELECT
    USING (id = '00000000-0000-0000-0000-000000000001');

-- Allow anon access to test user's learning progress
CREATE POLICY "Allow anon access to test user progress"
    ON learning_progress FOR ALL
    USING (user_id = '00000000-0000-0000-0000-000000000001');

-- Allow anon access to test user's sources
CREATE POLICY "Allow anon access to test user sources"
    ON sources FOR ALL
    USING (user_id = '00000000-0000-0000-0000-000000000001');

-- Allow anon access to content from test user's sources
CREATE POLICY "Allow anon access to test user content"
    ON content FOR ALL
    USING (
        source_id IN (
            SELECT id FROM sources WHERE user_id = '00000000-0000-0000-0000-000000000001'
        )
    );

-- Allow anon access to embeddings from test user's content
CREATE POLICY "Allow anon access to test user embeddings"
    ON embeddings FOR ALL
    USING (
        content_id IN (
            SELECT c.id FROM content c
            JOIN sources s ON c.source_id = s.id
            WHERE s.user_id = '00000000-0000-0000-0000-000000000001'
        )
    );

-- Allow anon access to test user's feedback
CREATE POLICY "Allow anon access to test user feedback"
    ON feedback FOR ALL
    USING (user_id = '00000000-0000-0000-0000-000000000001');

-- Allow anon access to test user's digests
CREATE POLICY "Allow anon access to test user digests"
    ON generated_digests FOR ALL
    USING (user_id = '00000000-0000-0000-0000-000000000001');

-- Verify policies were created
DO $$
BEGIN
    RAISE NOTICE '✅ Test user RLS policies created successfully!';
    RAISE NOTICE '';
    RAISE NOTICE 'The test user data is now accessible via the anon key.';
    RAISE NOTICE 'This is safe for development as it only affects the test user.';
END $$;
