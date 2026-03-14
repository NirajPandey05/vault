-- Vault Database Schema
-- Migration-safe architecture for embedding model changes

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',  -- active, paused, completed, archived
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Memories table (core storage)
CREATE TABLE IF NOT EXISTS memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'thought',  -- thought, idea, progress, decision, question, workflow, reference
    source VARCHAR(50) DEFAULT 'cli',    -- cli, api, file, voice, web
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Embeddings table (supports multiple models per memory)
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_id UUID REFERENCES memories(id) ON DELETE CASCADE,
    vector VECTOR(1536),                 -- Standard 1536 dimensions (OpenAI compatible)
    model_name VARCHAR(100) NOT NULL,    -- 'bedrock-titan-v2', 'openai-small', etc.
    model_version VARCHAR(50),           -- Model version for tracking
    is_active BOOLEAN DEFAULT true,      -- Current primary embedding for this memory
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(memory_id, model_name)        -- One embedding per model per memory
);

-- Memory links (relationships between memories)
CREATE TABLE IF NOT EXISTS memory_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_memory_id UUID REFERENCES memories(id) ON DELETE CASCADE,
    to_memory_id UUID REFERENCES memories(id) ON DELETE CASCADE,
    relation_type VARCHAR(50),           -- related, references, contradicts, extends
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(from_memory_id, to_memory_id, relation_type)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id);
CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_memories_content_search ON memories USING GIN(to_tsvector('english', content));

-- Embeddings indexes
CREATE INDEX IF NOT EXISTS idx_embeddings_memory ON embeddings(memory_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_name);
CREATE INDEX IF NOT EXISTS idx_embeddings_active ON embeddings(memory_id, is_active) WHERE is_active = true;

-- Vector similarity index (IVFFlat for fast approximate search)
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);

-- Projects indexes
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_name ON projects(name);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- View: Active embeddings (latest per memory)
CREATE OR REPLACE VIEW active_embeddings AS
SELECT 
    e.id,
    e.memory_id,
    e.vector,
    e.model_name,
    e.model_version,
    e.created_at,
    m.content,
    m.type,
    m.project_id,
    m.tags
FROM embeddings e
JOIN memories m ON e.memory_id = m.id
WHERE e.is_active = true;

-- Helper function: Search by similarity
CREATE OR REPLACE FUNCTION search_memories(
    query_embedding VECTOR(1536),
    model_filter VARCHAR(100),
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    memory_id UUID,
    content TEXT,
    type VARCHAR(50),
    tags TEXT[],
    similarity DOUBLE PRECISION,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.id,
        m.content,
        m.type,
        m.tags,
        1 - (e.vector <=> query_embedding) AS similarity,
        m.created_at
    FROM embeddings e
    JOIN memories m ON e.memory_id = m.id
    WHERE e.model_name = model_filter AND e.is_active = true
    ORDER BY e.vector <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Sample data for testing (optional)
-- INSERT INTO projects (name, description) VALUES 
--     ('Second Brain', 'Building a personal knowledge management system'),
--     ('Learning AI', 'Notes and progress on AI/ML learning');
