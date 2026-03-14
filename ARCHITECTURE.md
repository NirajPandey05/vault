# Vault Architecture

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI / API                           │
│                      (vault add/search)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   VaultDB    │  │  Embeddings  │  │    Config    │     │
│  │   (db.py)    │  │  (factory)   │  │  (config.py) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Model-Agnostic Embedding Layer                 │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ BedrockTitan     │  │  OpenAI          │               │
│  │ Provider         │  │  Provider        │               │
│  └──────────────────┘  └──────────────────┘               │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Supabase Postgres + pgvector               │  │
│  │                                                      │  │
│  │  memories │ embeddings │ projects │ memory_links    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 📊 Data Model

### Core Tables

#### memories
- **Purpose**: Store all thoughts, ideas, progress logs
- **Key Fields**: content, type, tags, project_id, metadata
- **Relationships**: → projects, → embeddings

#### embeddings
- **Purpose**: Vector representations for semantic search
- **Key Fields**: vector(1536), model_name, is_active
- **Unique Feature**: Multiple embeddings per memory (migration support)

#### projects
- **Purpose**: Organize memories by project/context
- **Key Fields**: name, status, description

#### memory_links
- **Purpose**: Relationships between memories
- **Key Fields**: from_memory_id, to_memory_id, relation_type

## 🔄 Backward-Compatible Migration Strategy

### Problem
Different embedding models produce incompatible vector spaces:
- Bedrock Titan: 1536 dimensions, AWS space
- OpenAI Small: 1536 dimensions, OpenAI space
- Cannot compare across models even with same dimensions

### Solution
1. **Store Multiple Embeddings**: Each memory can have embeddings from different models
2. **Track Active Model**: `is_active` flag marks current primary embedding
3. **Model-Specific Search**: Always search within same model's vector space
4. **Safe Migration**: Generate new embeddings, keep old ones for rollback

### Migration Flow
```
1. User initiates: vault migrate run openai-small
2. Fetch all memories
3. Batch process: Generate OpenAI embeddings
4. Store as NEW embeddings (model_name='openai-small')
5. Mark as active
6. Keep old Bedrock embeddings (is_active=false)
7. Optional cleanup after confidence period
```

### Cost Control
- Dry run estimates cost before migrating
- Batch processing reduces API calls
- Configurable batch sizes
- Track model costs in config

## 🔌 Model-Agnostic Architecture

### Abstract Interface
```python
class EmbeddingProvider(ABC):
    def embed(text: str) -> List[float]
    def embed_batch(texts: List[str]) -> List[List[float]]
    def normalize_vector(vector: List[float]) -> List[float]
```

### Provider Implementations
- **BedrockTitanProvider**: AWS Bedrock Titan Embed v2
- **OpenAIProvider**: OpenAI text-embedding-3-small/large
- **Extensible**: Easy to add Voyage, Cohere, local models

### Factory Pattern
```python
provider = get_embedding_provider("bedrock-titan")
vector = provider.embed("Some text")
```

Change providers without code changes—just config update.

## 🎯 Key Features

### 1. Semantic Search
```sql
SELECT * FROM search_memories(
    query_embedding := [0.1, 0.2, ...],
    model_filter := 'bedrock-titan',
    limit_count := 10
)
```

### 2. Multi-Device Sync
- Cloud-first via Supabase
- Real-time updates across devices
- Offline cache (Phase 2)

### 3. Tag + Semantic Hybrid
- Full-text search on content
- GIN index on tags array
- Vector similarity search
- Combine for precision

### 4. Project Context
Get all memories for a project:
```python
memories = db.get_project_memories(project_id)
```

## 💰 Cost Breakdown

### Storage (Supabase Free Tier)
- 500 MB database
- 10,000 rows per table
- ≈ 5,000-10,000 memories
- **Cost: $0/month**

### Embeddings
| Model | Dimension | Cost per 1K tokens | 10K memories |
|-------|-----------|-------------------|--------------|
| Bedrock Titan | 1536 | $0.0002 | ~$0.20 |
| OpenAI Small | 1536 | $0.00002 | ~$0.02 |
| OpenAI Large | 3072 | $0.00013 | ~$0.13 |

**Typical Usage: < $0.50/month**

## 🚀 Usage Patterns

### Daily Capture
```bash
vault add "Thought about X"
vault add "Idea for Y" --type idea
vault add "Completed Z" --type progress
```

### Search & Recall
```bash
vault search "authentication"
vault recent 10
vault recent --type progress
```

### Project Organization
```bash
vault project create "Second Brain"
vault add "Progress update" --project <id>
vault project context <id>
```

### Model Migration
```bash
# Estimate cost
vault migrate run openai-small --dry-run

# Execute migration
vault migrate run openai-small
```

## 🔐 Security

- **No hardcoded credentials**: Use .env only
- **Supabase RLS**: Row-level security (future)
- **AWS IAM**: Standard AWS credential chain
- **Environment isolation**: .env never committed

## 📈 Scalability

### Current Limits (Free Tier)
- 10,000 memories
- 500 MB storage
- Shared Postgres instance

### Upgrade Path
- Supabase Pro: $25/mo → 8GB + 100K rows
- Better pgvector performance
- Dedicated resources
- Point-in-time recovery

### Performance Optimizations
- IVFFlat index for vector search
- B-tree indexes on common queries
- Batch embedding generation
- Connection pooling

## 🎯 Future Enhancements

### Phase 2
- [ ] Local SQLite cache for offline
- [ ] MCP server for AI agent access
- [ ] Web UI for browsing
- [ ] Auto-linking related memories

### Phase 3
- [ ] Voice memo transcription (Whisper)
- [ ] File drop ingestion
- [ ] Obsidian/Notion sync
- [ ] Browser extension for web clipping

### Phase 4
- [ ] Multi-user support
- [ ] Shared projects
- [ ] Real-time collaboration
- [ ] API webhooks
