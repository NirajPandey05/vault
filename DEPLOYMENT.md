# Vault Deployment Guide

Complete step-by-step guide to deploy and configure Vault from scratch.

---

## Prerequisites

### Required
- Python 3.10 or higher
- Git (for cloning repository)
- Terminal/Command line access

### For Specific Databases
- **Supabase**: Free account at [supabase.com](https://supabase.com)
- **PostgreSQL**: Access to PostgreSQL server (local/Neon/Railway/etc.)
- **SQLite**: Nothing extra needed (built-in)

### For Embeddings
- **AWS Bedrock**: AWS account with Bedrock access configured in `~/.aws/credentials`
- **OpenAI**: API key from [platform.openai.com](https://platform.openai.com)

---

## Deployment Options

Choose your path based on your needs:

| Option | Best For | Cost | Setup Time |
|--------|----------|------|------------|
| **Quick Start (SQLite + Bedrock)** | Testing, local use | $0.30/mo | 5 minutes |
| **Cloud Sync (Supabase + Bedrock)** | Multi-device, free tier | $0.30/mo | 15 minutes |
| **Self-Hosted (Postgres + Bedrock)** | Full control | Server cost | 30 minutes |

---

## Option 1: Quick Start (SQLite + AWS Bedrock) ⚡

**Best for:** Testing, single device, offline usage

### Step 1: Clone and Install

```bash
# Clone the repository
cd e:\agent_tutorial\agent-skills-demo
cd vault

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# Install Vault (SQLite only, no extra dependencies)
pip install -e .
```

### Step 2: Configure AWS Credentials

```bash
# Verify AWS credentials are set up
aws configure list

# If not configured, run:
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter region: us-east-1
```

### Step 3: Configure Vault

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
# Windows: notepad .env
# macOS/Linux: nano .env
```

**Minimal .env for SQLite:**
```bash
DATABASE_PROVIDER=sqlite
SQLITE_DB_PATH=~/.vault/vault.db
EMBEDDING_PROVIDER=bedrock-titan
AWS_REGION=us-east-1
LOG_LEVEL=INFO
```

### Step 4: Test Installation

```bash
# Add your first memory
vault add "Setting up my Second Brain system"

# Verify it worked
vault recent

# Test search
vault search "brain"
```

**Done!** ✅ You now have a working local Vault.

---

## Option 2: Cloud Sync (Supabase + AWS Bedrock) ☁️

**Best for:** Multi-device sync, collaboration, free cloud tier

### Step 1: Set Up Supabase

1. **Create Supabase Account**
   - Go to [supabase.com](https://supabase.com)
   - Sign up (free tier is sufficient)

2. **Create New Project**
   - Click "New Project"
   - Choose name: `vault-secondbrain`
   - Set strong database password (save it!)
   - Choose region closest to you
   - Click "Create new project" (takes ~2 minutes)

3. **Get Project Credentials**
   - Go to Project Settings → API
   - Copy:
     - **Project URL** (e.g., `https://abc123.supabase.co`)
     - **anon/public key** (starts with `eyJ...`)

4. **Enable pgvector Extension**
   - Go to Database → Extensions
   - Search for "vector"
   - Click "Enable" on **pgvector**
   - Wait for activation (~30 seconds)

5. **Run Database Schema**
   - Go to SQL Editor
   - Click "New Query"
   - Copy entire contents of `vault/scripts/schema.sql`
   - Paste and click "Run"
   - You should see "Success" messages

### Step 2: Install Vault with Supabase Support

```bash
cd vault

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Install with Supabase dependencies
pip install -e ".[supabase]"
```

### Step 3: Configure Vault

```bash
# Copy example config
cp .env.example .env
```

**Edit .env:**
```bash
# Database
DATABASE_PROVIDER=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# AWS Bedrock
EMBEDDING_PROVIDER=bedrock-titan
AWS_REGION=us-east-1
AWS_PROFILE=default

# App
LOG_LEVEL=INFO
```

### Step 4: Verify Setup

```bash
# Test database connection
python scripts/setup_supabase.py

# Add first memory
vault add "My Second Brain is now cloud-synced!"

# Check in Supabase Dashboard
# Go to Table Editor → memories
# You should see your entry
```

### Step 5: Set Up on Other Devices

On your second device:

```bash
# Clone and install
git clone <your-repo>
cd vault
pip install -e ".[supabase]"

# Copy same .env file (with same SUPABASE_URL and KEY)
cp .env.example .env
# Add your credentials

# Test - you should see memories from first device!
vault recent
```

**Done!** ✅ You now have multi-device sync.

---

## Option 3: Self-Hosted (PostgreSQL + AWS Bedrock) 🔧

**Best for:** Full control, privacy, scaling

### Step 1: Set Up PostgreSQL

**Option A: Local PostgreSQL**

```bash
# Install PostgreSQL with pgvector
# Ubuntu/Debian:
sudo apt install postgresql postgresql-contrib
sudo apt install postgresql-16-pgvector

# macOS (Homebrew):
brew install postgresql pgvector

# Windows: Download from postgresql.org
```

**Option B: Managed PostgreSQL (Neon)**

1. Go to [neon.tech](https://neon.tech)
2. Sign up (free tier available)
3. Create project
4. Copy connection string

**Option C: Railway/Render**

Similar to Neon - create PostgreSQL instance and get connection string.

### Step 2: Initialize Database

```bash
# Connect to your database
psql postgresql://user:password@host:5432/postgres

# Create vault database
CREATE DATABASE vault;

# Enable pgvector
\c vault
CREATE EXTENSION IF NOT EXISTS vector;

# Run schema
\i scripts/schema.sql

# Exit
\q
```

### Step 3: Install Vault with PostgreSQL Support

```bash
cd vault
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install with PostgreSQL dependencies
pip install -e ".[postgres]"
```

### Step 4: Configure

**Edit .env:**
```bash
# Database
DATABASE_PROVIDER=postgres
POSTGRES_CONNECTION_STRING=postgresql://user:password@host:5432/vault

# AWS Bedrock
EMBEDDING_PROVIDER=bedrock-titan
AWS_REGION=us-east-1

# App
LOG_LEVEL=INFO
```

### Step 5: Test

```bash
vault add "Self-hosted Second Brain is running!"
vault recent
vault search "running"
```

**Done!** ✅ You have full control over your data.

---

## Post-Deployment: First Steps

### 1. Create Your First Project

```bash
vault project create "Personal Knowledge" --description "My learning and ideas"
vault project create "Work" --description "Work-related notes"
vault project list
```

### 2. Add Structured Memories

```bash
# Regular thoughts
vault add "Need to research vector databases"

# Ideas with tags
vault add "Idea: Use embeddings for search" --type idea --tags "ai,search"

# Progress updates
vault add "Completed database abstraction layer" --type progress --tags "vault,milestone"

# Decisions
vault add "Decided to use Supabase for cloud sync" --type decision
```

### 3. Test Search

```bash
# Semantic search
vault search "database"
vault search "ideas about AI"

# Recent items
vault recent 10
vault recent --type idea
```

### 4. Set Up Daily Workflow

See [WORKFLOW.md](WORKFLOW.md) for detailed usage patterns.

---

## Troubleshooting

### "Command 'vault' not found"

```bash
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Verify installation
pip list | grep vault

# If not found, reinstall
pip install -e .
```

### "Supabase connection failed"

```bash
# Verify credentials in .env
cat .env

# Test connection
python -c "from vault.database import get_database_provider; \
    db = get_database_provider(); \
    print('✓ Connected' if db.ping() else '✗ Failed')"
```

### "AWS Bedrock access denied"

```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

### "Embedding generation slow"

```bash
# Switch to faster/cheaper provider
# Edit .env:
EMBEDDING_PROVIDER=openai-small

# Get OpenAI key from platform.openai.com
OPENAI_API_KEY=sk-...

# Migrate embeddings
vault migrate run openai-small
```

### "Database migration needed"

See [DATABASE_MIGRATION.md](DATABASE_MIGRATION.md) for migration guides.

---

## Updating Vault

```bash
# Pull latest changes
git pull origin main

# Reinstall
pip install -e ".[your-provider]"

# Check for schema updates
# Compare scripts/schema.sql with your database
# Run any new migrations
```

---

## Production Deployment

### Docker (Coming Soon)

```dockerfile
# Dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[all]"
CMD ["vault", "add", "Container is running"]
```

### Systemd Service (Linux)

```ini
# /etc/systemd/system/vault.service
[Unit]
Description=Vault Second Brain
After=network.target

[Service]
Type=simple
User=vault
WorkingDirectory=/home/vault/vault
Environment="PATH=/home/vault/vault/venv/bin"
ExecStart=/home/vault/vault/venv/bin/vault add "Daily heartbeat"
Restart=always

[Install]
WantedBy=multi-user.target
```

### Scheduled Backups

```bash
# Cron job for daily backups
0 2 * * * cd /path/to/vault && python scripts/export_data.py
```

---

## Security Best Practices

### 1. Never Commit Credentials

```bash
# .env is in .gitignore by default
# Verify:
git check-ignore .env
```

### 2. Use Strong Database Passwords

```bash
# Generate strong password
openssl rand -base64 32
```

### 3. Rotate API Keys Regularly

```bash
# AWS: Rotate keys every 90 days
# OpenAI: Rotate keys every 6 months
```

### 4. Enable Row-Level Security (Supabase)

In Supabase Dashboard → Authentication → Policies:
```sql
-- Enable RLS on all tables
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
```

---

## Next Steps

1. ✅ Review [WORKFLOW.md](WORKFLOW.md) for daily usage patterns
2. ✅ Check [EXAMPLES.py](EXAMPLES.py) for code examples
3. ✅ Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
4. ✅ Join community (Discord/GitHub Discussions)

**Your Second Brain is ready!** 🧠
