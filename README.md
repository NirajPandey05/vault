# Vault - Your Second Brain 🧠

A self-managed, AI-native memory system that stores thoughts, ideas, progress logs, and workflows with semantic search capabilities. Now with **daily markdown journals**, **multimodal content support**, and **MCP server** for IDE integration.

## 📚 Documentation

**New to Vault? Start here:**

- **[⚡ QUICKREF.md](QUICKREF.md)** - Quick reference card for all commands
- **[📖 DEPLOYMENT.md](DEPLOYMENT.md)** - Complete step-by-step setup guide (5-30 minutes)
- **[📝 WORKFLOW.md](WORKFLOW.md)** - Daily usage patterns and best practices
- **[💻 EXAMPLES.md](EXAMPLES.md)** - Code examples and integrations
- **[🔄 DATABASE_MIGRATION.md](DATABASE_MIGRATION.md)** - How to switch databases
- **[🏗️ DATABASE_ABSTRACTION_COMPLETE.md](DATABASE_ABSTRACTION_COMPLETE.md)** - Technical architecture

## Features

- **Model-Agnostic Embeddings**: Switch between Bedrock Titan, OpenAI, or other providers without breaking existing data
- **Semantic Search**: Find memories by meaning, not just keywords
- **Multi-Device Sync**: Cloud-synced via Supabase
- **CLI-First**: Fast, scriptable interface
- **Daily Journals**: Store daily knowledge as versioned `.md` files
- **Multimodal Content**: Add text, images, tables, and links to your journals
- **MCP Server**: Connect from any IDE (VS Code, Claude Code, Windsurf, Cursor)
- **Backward Compatible**: Safe embedding model migrations with automatic re-embedding

## Quick Start

### 1. Install

```bash
cd vault

# Option A: Install with Supabase support (default)
pip install -e ".[supabase]"

# Option B: Install with PostgreSQL support
pip install -e ".[postgres]"

# Option C: Install with SQLite only (built-in)
pip install -e .

# Option D: Install all features
pip install -e ".[all]"
```

### 2. Choose Your Database

**Option A: Supabase (Recommended for cloud sync)**

1. Create account at [supabase.com](https://supabase.com)
2. Create new project
3. Copy `.env.example` to `.env`:
   ```bash
   DATABASE_PROVIDER=supabase
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-anon-key-here
   ```
4. Run schema setup:
   ```bash
   python scripts/setup_supabase.py
   ```

**Option B: PostgreSQL (Self-hosted or Neon/Railway)**

1. Set up PostgreSQL with pgvector extension
2. Configure `.env`:
   ```bash
   DATABASE_PROVIDER=postgres
   POSTGRES_CONNECTION_STRING=postgresql://user:pass@host:5432/dbname
   ```
3. Run schema:
   ```bash
   psql $POSTGRES_CONNECTION_STRING < scripts/schema.sql
   ```

**Option C: SQLite (Local/Offline)**

1. Configure `.env`:
   ```bash
   DATABASE_PROVIDER=sqlite
   SQLITE_DB_PATH=~/.vault/vault.db
   ```
2. That's it! Schema auto-creates on first use.

### 3. Configure AWS (for Bedrock)

Ensure AWS credentials are in `~/.aws/credentials` with Bedrock access.

### 4. Start Using

**`vault add` command reference:**
```
Usage: vault add [OPTIONS] [CONTENT]

  Add a new memory to your vault.

Arguments:
  [CONTENT]  Memory content (required unless --file is used)

Options:
  -f, --file PATH        Path to a .md or .txt file to import as memory content
  --type TEXT            Memory type  [default: thought]
  --project TEXT         Project name
  --tags TEXT            Comma-separated tags
```

```bash
# Add memories
vault add "Started working on Second Brain project"
vault add "Idea: use vector embeddings for semantic search" --type idea
vault add --file notes.md
vault add -f meeting-notes.txt --type reference --tags "imported,meeting"

# Search
vault search "vector search"
vault recent 10

# Projects
vault project create "Second Brain"
vault project list
```

**👉 See [WORKFLOW.md](WORKFLOW.md) for complete daily usage patterns, best practices, and advanced workflows.**

## Daily Journals 📓

Each day's knowledge is stored as a markdown file (`~/.vault/journals/2026/03/2026-03-03.md`).

### Journal Structure

```markdown
# Journal - 2026-03-03

> Date: 2026-03-03
> Tags: project, ideas

## Your Content Here

Text, images, tables, and links are all supported...

---
*Entry ID: uuid*
```

### Adding Content via Python

```python
from vault import add_text, add_table, add_image, add_link, today

# Add text (markdown supported)
add_text("## My Idea\nThis is a **great** concept for...")

# Add a table
add_table(
    headers=["Task", "Status", "Priority"],
    rows=[
        ["Implement MCP", "Done", "High"],
        ["Add multimodal", "In Progress", "Medium"],
    ],
    caption="Project Tasks"
)

# Add an image
add_image("/path/to/screenshot.png", caption="Architecture diagram")

# Add a link
add_link("https://example.com", title="Reference", description="Useful documentation")

# Get today's journal
journal = today()
print(journal.to_markdown())
```

## MCP Server 🔌

The MCP (Model Context Protocol) server allows any compatible IDE to interact with your vault.

### Starting the MCP Server

```bash
vault-mcp
```

### IDE Configuration

#### VS Code / Claude Code

Add to your MCP settings (`settings.json` or `.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "vault": {
      "command": "vault-mcp",
      "args": []
    }
  }
}
```

#### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "vault": {
      "command": "vault-mcp"
    }
  }
}
```

#### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vault": {
      "command": "vault-mcp"
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `vault_add_text` | Add text memory or journal entry |
| `vault_add_table` | Add table to today's journal |
| `vault_add_link` | Add link to today's journal |
| `vault_add_image` | Add image to today's journal |
| `vault_search` | Semantic search across memories |
| `vault_recent` | Get recent memories |
| `vault_journal_today` | Get today's journal content |
| `vault_journal_sync` | Sync journal to database with embeddings |
| `vault_project_list` | List all projects |
| `vault_project_create` | Create a new project |

### MCP Resources

The server also exposes journal entries as resources:
- `vault://journal/today` - Today's journal
- `vault://journal/2026-03-03` - Specific date journals

## Architecture

- **Storage**: Supabase Postgres + pgvector
- **Local Files**: Daily markdown journals in `~/.vault/journals/`
- **Embeddings**: Model-agnostic (Bedrock Titan default, OpenAI ready)
- **CLI**: Python + Typer
- **MCP**: stdio-based server for IDE integration
- **Multi-Model**: Multiple embeddings per memory for safe migrations

## Multimodal Content Types

| Type | Support | Storage |
|------|---------|---------|
| **Text** | Full | Inline + DB |
| **Images** | Reference | Path in MD, file in assets |
| **Tables** | Full | Markdown format |
| **Links** | Full | Markdown format |
| **Code** | Full | Fenced code blocks |

## Cost

### Database Storage
- **SQLite**: $0 (local file)
- **Supabase Free**: $0/mo (500MB, 10K rows)
- **Neon Free**: $0/mo (0.5GB, no row limit)
- **Self-hosted PostgreSQL**: Server cost only

### Embeddings
- **Bedrock Titan**: ~$0.30/mo for typical use
- **OpenAI Small**: ~$0.02/mo for typical use

**Total**: **$0-0.50/mo** depending on choices

## Embedding Model Migration

Switch providers without losing data:

```bash
# Switch and re-embed in background
vault config set-embedding openai-small --migrate

# Check migration status
vault migrate status
```

## File Structure

```
~/.vault/
├── journals/
│   └── 2026/
│       └── 03/
│  Switching Databases

See [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md) for detailed migration guides.

**Quick example:**

```bash
# Export from current database
python scripts/export_data.py

# Change DATABASE_PROVIDER in .env
# supabase → postgres → sqlite

# Import to new database
python scripts/import_data.py

# Re-generate embeddings
vault migrate run bedrock-titan
```

Migration typically takes 15-30 minutes.

##          ├── 2026-03-01.md
│           ├── 2026-03-02.md
│           └── 2026-03-03.md
│   └── assets/
│       └── 20260303_screenshot.png
└── local.db
```

## License

MIT
