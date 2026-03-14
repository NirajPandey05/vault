# Database Migration Guide

## Switching Between Database Providers

Vault supports three database backends. Switching is straightforward:

### Supported Backends

| Provider | Use Case | Cost | Setup Difficulty |
|----------|----------|------|------------------|
| **Supabase** | Cloud sync, multi-device | $0 (free tier) | Easy |
| **PostgreSQL** | Self-hosted, Neon, Railway | Varies | Medium |
| **SQLite** | Local/offline, single device | $0 | Very Easy |

---

## Quick Switch Guide

### 1. Supabase → PostgreSQL

**Scenario:** Moving from Supabase to self-hosted PostgreSQL

```bash
# 1. Export data from Supabase
pg_dump "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres" > backup.sql

# 2. Update .env
DATABASE_PROVIDER=postgres
POSTGRES_CONNECTION_STRING=postgresql://user:pass@localhost:5432/vault

# 3. Install dependencies
pip install psycopg2-binary pgvector

# 4. Set up new database
createdb vault
psql vault < scripts/schema.sql

# 5. Import data
psql vault < backup.sql

# 6. Test connection
vault config show
```

**Downtime:** ~15 minutes

---

### 2. Supabase → SQLite

**Scenario:** Going offline-first or local-only

```bash
# 1. Export memories from Supabase
# (Use Python script to fetch and save)

# 2. Update .env
DATABASE_PROVIDER=sqlite
SQLITE_DB_PATH=~/.vault/vault.db

# 3. Vault automatically creates SQLite schema on first run
vault add "Test memory"

# 4. Import old data
python scripts/import_from_supabase.py

# 5. Re-generate embeddings
vault migrate run bedrock-titan
```

**Downtime:** ~30 minutes + embedding regeneration time

---

### 3. SQLite → PostgreSQL

**Scenario:** Scaling up or enabling multi-device sync

```bash
# 1. Your SQLite data is in ~/.vault/vault.db

# 2. Set up PostgreSQL
createdb vault
psql vault < scripts/schema.sql

# 3. Update .env
DATABASE_PROVIDER=postgres
POSTGRES_CONNECTION_STRING=postgresql://user:pass@host:5432/vault

# 4. Install dependencies
pip install psycopg2-binary pgvector

# 5. Export and import
python scripts/export_sqlite.py > data.json
python scripts/import_to_postgres.py data.json

# 6. Verify
vault recent 10
```

**Downtime:** ~20 minutes

---

## Zero-Downtime Migration

For production use with no downtime:

### Dual-Write Strategy

```python
from vault.database import get_database_provider

# Temporarily write to both databases
old_db = get_database_provider("supabase")
new_db = get_database_provider("postgres")

def add_memory_with_replication(content, **kwargs):
    # Write to new DB
    memory = new_db.add_memory({
        "content": content,
        **kwargs
    })
    
    # Replicate to old DB (fire-and-forget)
    try:
        old_db.add_memory({
            "content": content,
            **kwargs
        })
    except:
        log.warning("Old DB replication failed")
    
    return memory
```

**Steps:**
1. Deploy dual-write code
2. Backfill historical data  to new DB
3. Verify both DBs in sync
4. Switch `DATABASE_PROVIDER` in config
5. Remove dual-write code

**Downtime:** None

---

## Data Export/Import Scripts

### Export from any provider

```python
# scripts/export_data.py
from vault.db import VaultDB
import json

db = VaultDB()

# Export memories
memories = db.recent_memories(limit=999999)
projects = db.list_projects()

data = {
    "memories": [m.dict() for m in memories],
    "projects": [p.dict() for p in projects],
}

with open("vault_export.json", "w") as f:
    json.dump(data, f, indent=2, default=str)
```

### Import to any provider

```python
# scripts/import_data.py
from vault.db import VaultDB
from vault.database import get_database_provider
import json

# Load data
with open("vault_export.json") as f:
    data = json.load(f)

# Initialize new provider
db = VaultDB(provider=get_database_provider("postgres"))

# Import projects
for proj in data["projects"]:
    db.create_project(proj["name"], proj.get("description"))

# Import memories
for mem in data["memories"]:
    db.add_memory(
        content=mem["content"],
        type=mem["type"],
        tags=mem.get("tags", []),
        auto_embed=False  # Re-embed after
    )

# Re-generate embeddings
# vault migrate run bedrock-titan
```

---

## Performance Comparison

| Operation | Supabase | PostgreSQL | SQLite |
|-----------|----------|------------|--------|
| Add memory | 50-100ms | 10-30ms | 2-5ms |
| Search (100 memories) | 80-150ms | 30-80ms | 50-200ms |
| Search (10,000 memories) | 100-200ms | 50-150ms | 500-2000ms |
| Batch import (1000) | 15-25s | 8-15s | 3-8s |

**Notes:**
- Supabase: Network latency included
- PostgreSQL: Local network (self-hosted) or managed (Neon)
- SQLite: Uses numpy cosine similarity (no pgvector)

---

## Best Practice: Multi-Environment Setup

### Development: SQLite

```bash
# .env.dev
DATABASE_PROVIDER=sqlite
SQLITE_DB_PATH=./dev_vault.db
```

### Staging: Neon PostgreSQL

```bash
# .env.staging
DATABASE_PROVIDER=postgres
POSTGRES_CONNECTION_STRING=postgresql://user:pass@neon.tech/vault_staging
```

### Production: Supabase

```bash
# .env.production
DATABASE_PROVIDER=supabase
SUPABASE_URL=https://prod.supabase.co
SUPABASE_KEY=prod_key
```

---

## Troubleshooting

### "Provider X requires Y to be installed"

```bash
# Install missing dependencies
pip install -e ".[supabase]"  # For Supabase
pip install -e ".[postgres]"  # For PostgreSQL
# SQLite is built-in
```

### "Connection failed"

```bash
# Test connection
python -c "from vault.database import get_database_provider; \
    db = get_database_provider(); \
    print('✓ Connected' if db.ping() else '✗ Failed')"
```

### "Embeddings not found after migration"

```bash
# Re-generate embeddings for all memories
vault migrate run bedrock-titan --batch-size 500
```

---

## FAQ

**Q: Can I run multiple providers simultaneously?**

A: Not directly, but you can instantiate multiple `VaultDB` instances with different providers for data migration.

**Q: Which provider is fastest?**

A: SQLite for writes, PostgreSQL for vector search (with pgvector IVFFlat index).

**Q: Which provider is cheapest?**

A: SQLite ($0) → Supabase Free ($0) → PostgreSQL (varies)

**Q: Can I sync SQLite to cloud later?**

A: Yes! Use the export/import scripts to move data to Supabase or PostgreSQL when ready.
