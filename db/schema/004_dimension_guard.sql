-- Migration 004: Embedding Dimension Guard and Migration Helper
--
-- Different embedding models produce different vector dimensions:
--   - Ollama (nomic-embed-text): 768
--   - Cohere (embed-english-v3.0): 1024
--   - OpenAI (text-embedding-3-small): 1536
--   - HuggingFace (all-MiniLM-L6-v2): 384
--
-- This migration provides:
-- 1. A metadata registry tracking the configured embedding dimension.
-- 2. A migration function `set_embedding_dimension(new_dim INT)` that
--    safely resizes the vector column and rebuilds the vector index.

CREATE TABLE IF NOT EXISTS schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seed initial dimension if not already set
INSERT INTO schema_metadata (key, value)
VALUES ('embedding_dimension', '1536')
ON CONFLICT (key) DO NOTHING;

-- Migration helper to safely resize chunks.embedding
CREATE OR REPLACE FUNCTION set_embedding_dimension(new_dim INT)
RETURNS void AS $$
BEGIN
    IF new_dim <= 0 OR new_dim > 4000 THEN
        RAISE EXCEPTION 'Invalid vector dimension: %. Must be between 1 and 4000.', new_dim;
    END IF;

    -- 1. Drop the existing vector index before altering column type
    DROP INDEX IF EXISTS idx_chunks_embedding;

    -- 2. Alter column type to the new dimension
    EXECUTE format('ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(%s)', new_dim);

    -- 3. Rebuild IVFFlat index on the resized vector column
    -- Note: IVFFlat requires at least some rows to build optimal centroids;
    -- if empty, index creation still succeeds.
    EXECUTE 'CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)';

    -- 4. Update the schema metadata tracking table
    INSERT INTO schema_metadata (key, value, updated_at)
    VALUES ('embedding_dimension', new_dim::text, NOW())
    ON CONFLICT (key)
    DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();

    RAISE NOTICE 'Successfully updated chunks.embedding dimension to % and rebuilt index.', new_dim;
END;
$$ LANGUAGE plpgsql;
