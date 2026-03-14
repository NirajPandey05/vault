"""Quick start guide and examples for Vault."""

# ============================================================
# VAULT - QUICK START EXAMPLES
# ============================================================

# 1. Installation
"""
cd vault
pip install -e .
"""

# 2. Basic Memory Operations
"""
# Add memories
vault add "Started learning about vector databases"
vault add "Idea: combine semantic search with tags" --type idea
vault add "Completed database schema design" --type progress

# With tags
vault add "Python best practices for async code" --tags "python,async,learning"

# Search memories
vault search "vector database"
vault search "python async"

# Recent memories
vault recent
vault recent 20
vault recent --type progress
"""

# 3. Projects
"""
# Create project
vault project create "Second Brain" --description "Personal knowledge system"

# List projects
vault project list
vault project list --status active

# Get project context (after adding memories with project_id)
vault project context <project-id>
"""

# 4. Configuration
"""
# View current config
vault config show

# Change embedding provider (requires migration)
vault config set-embedding openai-small --migrate
"""

# 5. Migration
"""
# Check what migration would cost
vault migrate run openai-small --dry-run

# Run migration
vault migrate run openai-small --batch-size 100

# Check migration status
vault migrate status
"""

# 6. Python API Usage
"""
from vault.db import VaultDB
from vault.config import get_config

# Initialize
db = VaultDB()

# Add memory
memory = db.add_memory(
    content="Learning about embeddings",
    type="thought",
    tags=["ai", "learning"]
)

# Search
results = db.search_memories("embeddings", limit=5)
for result in results:
    print(f"{result.similarity:.2f} - {result.memory.content}")

# Recent memories
recent = db.recent_memories(limit=10, type="idea")
"""

# 7. Advanced: Manual Embedding Control
"""
from vault.embeddings.factory import get_embedding_provider

# Get current provider
provider = get_embedding_provider()

# Generate embedding
vector = provider.embed("Some text")

# Batch embeddings
texts = ["text 1", "text 2", "text 3"]
vectors = provider.embed_batch(texts)

# Use specific provider
bedrock = get_embedding_provider("bedrock-titan")
openai = get_embedding_provider("openai-small")
"""

# 8. Real-World Workflow
"""
# Morning: Add thoughts
vault add "Need to research RAG architectures" --type question
vault add "Meeting with team about API design" --type progress

# During day: Capture ideas
vault add "Could use webhook for real-time sync" --type idea --tags "architecture,api"

# Evening: Review
vault recent 20
vault search "API"

# Weekly: Organize by projects
vault project create "API Redesign"
# Then add --project flag to future memories
"""
