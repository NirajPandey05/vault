# Vault Quick Reference Card

Fast reference for Vault commands and workflows.

---

## Installation

```bash
# Local (SQLite)
pip install -e .

# Cloud (Supabase)
pip install -e ".[supabase]"

# Self-hosted (PostgreSQL)
pip install -e ".[postgres]"

# All features
pip install -e ".[all]"
```

---

## Configuration

```bash
# Copy example
cp .env.example .env

# Edit config
nano .env  # or notepad .env on Windows

# Required variables
DATABASE_PROVIDER=supabase|postgres|sqlite
EMBEDDING_PROVIDER=bedrock-titan|openai-small|openai-large
```

---

## Basic Commands

### Adding Memories

```bash
# Simple note
vault add "Your thought here"

# With type
vault add "Great idea!" --type idea
vault add "Completed task X" --type progress
vault add "Useful link" --type reference
vault add "Open question?" --type question
vault add "Decision made" --type decision

# With tags
vault add "Python is amazing" --tags "python,programming"

# Combined
vault add "Idea for new feature" --type idea --tags "features,roadmap"
```

### Searching

```bash
# Semantic search
vault search "machine learning"
vault search "database performance"

# Limited results
vault search "python" --limit 10

# By type
vault search "ideas" --type idea
```

### Recent Memories

```bash
# Last 10
vault recent

# Last 20
vault recent 20

# By type
vault recent --type idea
vault recent --type progress
```

---

## Projects

```bash
# Create
vault project create "Project Name" --description "Description"

# List all
vault project list

# Get context (all memories for project)
vault project context <project-id>
```

---

## Configuration

```bash
# Show current config
vault config show

# Test connection
vault config test
```

---

## Migration

```bash
# Switch embedding model
vault migrate run openai-small

# Dry run (see what would happen)
vault migrate run openai-small --dry-run

# Check status
vault migrate status

# Batch size control
vault migrate run bedrock-titan --batch-size 50
```

---

## Common Workflows

### Morning Routine
```bash
vault recent 20                      # Review yesterday
vault add "Today's focus: ..."       # Set intentions
```

### Throughout Day
```bash
vault add "Quick thought"            # Instant capture
vault search "that thing"            # Find context
```

### Evening Review
```bash
vault recent 15                      # Today's captures
vault search "open questions"        # Check status
```

### Weekly Review
```bash
vault recent 100                     # Week overview
vault recent --type idea             # All ideas
vault recent --type progress         # All progress
vault project list                   # Project status
```

---

## Memory Types

| Type | Use For | Example |
|------|---------|---------|
| `note` | General thoughts | "Meeting notes from standup" |
| `idea` | Creative thoughts | "What if we used serverless?" |
| `progress` | Status updates | "Completed auth module" |
| `decision` | Choices made | "Decided to use PostgreSQL" |
| `question` | Open items | "How does X work?" |
| `reference` | External links | "Great article: https://..." |

---

## Tag Strategies

### By Topic
```bash
--tags "python,programming"
--tags "databases,scaling"
--tags "ai,ml"
```

### By Status
```bash
--tags "todo"
--tags "done"
--tags "blocked"
```

### By Source
```bash
--tags "meeting,work"
--tags "reading,book"
--tags "experiment,personal"
```

### By Priority
```bash
--tags "high-priority"
--tags "someday-maybe"
```

---

## Keyboard-Friendly Aliases

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# Quick adds
alias va='vault add'
alias vs='vault search'
alias vr='vault recent'

# Type-specific adds
alias vi='vault add --type idea'
alias vp='vault add --type progress'
alias vd='vault add --type decision'
alias vq='vault add --type question'

# Common searches
alias vst='vault search --type'
alias vsi='vault search --type idea'
alias vsp='vault search --type progress'
```

Usage:
```bash
va "Quick note"
vi "Great idea!" --tags "features"
vs "search term"
vr 20
```

---

## Database Providers

| Provider | Best For | Cost | Setup Time |
|----------|----------|------|------------|
| **SQLite** | Local, testing, offline | Free | 5 min |
| **Supabase** | Cloud sync, multi-device | Free tier | 15 min |
| **PostgreSQL** | Self-hosted, full control | Server cost | 30 min |

---

## Embedding Providers

| Provider | Model | Dimensions | Cost/1M tokens |
|----------|-------|------------|----------------|
| **Bedrock** | Titan v2 | 1536 | ~$0.20 |
| **OpenAI** | text-embedding-3-small | 1536 | ~$0.02 |
| **OpenAI** | text-embedding-3-large | 3072 | ~$0.13 |

---

## Troubleshooting

### Command not found
```bash
# Activate venv
source venv/bin/activate  # Mac/Linux
.\venv\Scripts\Activate.ps1  # Windows

# Reinstall
pip install -e .
```

### Connection failed
```bash
# Check config
cat .env

# Test database
vault config test

# Check AWS credentials (for Bedrock)
aws sts get-caller-identity
```

### Slow search
```bash
# Use faster embedding model
# Edit .env:
EMBEDDING_PROVIDER=openai-small

# Re-embed
vault migrate run openai-small
```

---

## Python API Quick Reference

```python
from vault.db import VaultDB
from vault.models import MemoryType

# Initialize
vault = VaultDB()

# Add
memory = vault.add_memory(
    content="Text",
    memory_type=MemoryType.IDEA,
    tags=["tag1", "tag2"],
    metadata={"key": "value"}
)

# Search
results = vault.search_memories("query", limit=10)
for r in results:
    print(f"{r.similarity:.3f}: {r.memory.content}")

# Recent
recent = vault.recent_memories(limit=20)

# Projects
project = vault.create_project("Name", "Description")
projects = vault.list_projects()
```

---

## Environment Variables

```bash
# Database
DATABASE_PROVIDER=supabase|postgres|sqlite
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx...
POSTGRES_CONNECTION_STRING=postgresql://...
SQLITE_DB_PATH=~/.vault/vault.db

# Embeddings
EMBEDDING_PROVIDER=bedrock-titan|openai-small|openai-large
AWS_REGION=us-east-1
AWS_PROFILE=default
OPENAI_API_KEY=sk-xxx...

# App
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
```

---

## File Locations

```
~/.vault/                    # Vault home directory
├── vault.db                 # SQLite database (if using SQLite)
├── journals/                # Daily markdown journals
│   └── YYYY/MM/            
│       └── YYYY-MM-DD.md   
└── assets/                  # Images and attachments

~/.aws/credentials           # AWS credentials (for Bedrock)

vault/.env                   # Configuration (in project dir)
```

---

## Common Patterns

### 1. Quick Capture
```bash
alias capture='vault add'
capture "Thought at $(date)"
```

### 2. Daily Log
```bash
vault add "Daily log: $(date)" --type progress | tee -a daily.log
```

### 3. Search + Add Related
```bash
vault search "topic" && \
vault add "New thought related to topic" --tags "topic"
```

### 4. Export Search Results
```bash
vault search "project" > project-notes.txt
```

### 5. Count Memories
```bash
vault recent 10000 | wc -l
```

---

## Performance Tips

1. **Use batch operations** for multiple adds
2. **Index frequently** (automatic with PostgreSQL)
3. **Limit search results** for faster queries
4. **Use SQLite for offline** work
5. **Sync to cloud** when back online

---

## Links

- [README.md](README.md) - Overview and features
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full setup guide
- [WORKFLOW.md](WORKFLOW.md) - Daily usage patterns
- [EXAMPLES.md](EXAMPLES.md) - Code examples
- [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md) - Migration guide

---

**Print this card and keep it handy!** 📋
