-- Add Full-Text Search (FTS) support to document_chunks table
-- This enables keyword-based retrieval for hybrid search

-- Add tsvector column for full-text search if not exists
ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Create GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS document_chunks_search_vector_idx 
ON document_chunks USING GIN (search_vector);

-- Create trigger to automatically update search_vector on insert/update
CREATE OR REPLACE FUNCTION document_chunks_search_vector_update() 
RETURNS trigger AS $$
BEGIN
  NEW.search_vector := 
    setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'A');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

-- Drop trigger if exists (for re-running migration)
DROP TRIGGER IF EXISTS document_chunks_search_vector_trigger ON document_chunks;

-- Create trigger
CREATE TRIGGER document_chunks_search_vector_trigger
BEFORE INSERT OR UPDATE ON document_chunks
FOR EACH ROW EXECUTE FUNCTION document_chunks_search_vector_update();

-- Backfill search_vector for existing rows
UPDATE document_chunks 
SET search_vector = to_tsvector('english', COALESCE(content, ''))
WHERE search_vector IS NULL;

-- Create RPC function for keyword search
CREATE OR REPLACE FUNCTION keyword_search_chunks(
  search_query TEXT,
  match_count INT DEFAULT 10,
  doc_ids UUID[] DEFAULT NULL,
  min_rank_threshold FLOAT DEFAULT 0.0
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  metadata JSONB,
  document_id UUID,
  chunk_index INT,
  rank FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    dc.id,
    dc.content,
    dc.metadata,
    dc.document_id,
    dc.chunk_index,
    ts_rank(dc.search_vector, websearch_to_tsquery('english', search_query))::double precision as rank
  FROM document_chunks dc
  WHERE 
    dc.search_vector @@ websearch_to_tsquery('english', search_query)
    AND (doc_ids IS NULL OR dc.document_id = ANY(doc_ids))
    AND ts_rank(dc.search_vector, websearch_to_tsquery('english', search_query)) >= min_rank_threshold
  ORDER BY rank DESC
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission on the function (adjust role as needed)
GRANT EXECUTE ON FUNCTION keyword_search_chunks TO authenticated;
GRANT EXECUTE ON FUNCTION keyword_search_chunks TO anon;

-- Verify setup
SELECT 
  'FTS setup complete. Search vector index created.' as status,
  COUNT(*) as total_chunks,
  COUNT(search_vector) as indexed_chunks
FROM document_chunks;
