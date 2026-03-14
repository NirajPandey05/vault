# Vault Code Examples

Programming examples for interacting with Vault programmatically.

---

## Table of Contents

1. [Python API Usage](#python-api-usage)
2. [Batch Operations](#batch-operations)
3. [Custom Integrations](#custom-integrations)
4. [MCP Server Integration](#mcp-server-integration)
5. [Advanced Patterns](#advanced-patterns)

---

## Python API Usage

### Basic Operations

```python
from vault.db import VaultDB
from vault.models import MemoryType

# Initialize Vault
vault = VaultDB()

# Add a simple memory
memory = vault.add_memory(
    content="Learning about vector embeddings",
    memory_type=MemoryType.NOTE
)
print(f"Created memory: {memory.id}")

# Add with metadata
idea = vault.add_memory(
    content="Build an AI-powered search engine",
    memory_type=MemoryType.IDEA,
    tags=["ai", "search", "startup"],
    metadata={"priority": "high", "status": "brainstorming"}
)

# Search semantically
results = vault.search_memories("machine learning", limit=5)
for result in results:
    print(f"[{result.similarity:.3f}] {result.memory.content}")

# Get recent memories
recent = vault.recent_memories(limit=10, memory_type=MemoryType.IDEA)
for mem in recent:
    print(f"{mem.created_at}: {mem.content}")
```

### Project Management

```python
# Create a project
project = vault.create_project(
    name="Second Brain Implementation",
    description="Building my personal knowledge system",
    status="active"
)

# List all projects
projects = vault.list_projects()
for p in projects:
    print(f"{p.name} - {p.status}")

# Get project context (all related memories)
context = vault.get_project_context(project.id)
print(f"Project has {len(context)} memories")
```

---

## Batch Operations

### Bulk Import

```python
from vault.db import VaultDB
from vault.models import MemoryType

vault = VaultDB()

# Import from notes
notes = [
    "Read 'Designing Data-Intensive Applications' chapter 3",
    "Meeting notes: Q1 planning session",
    "Idea: Use embeddings for similar document detection",
    "TIL: Python's asyncio can speed up I/O operations",
]

for note in notes:
    vault.add_memory(content=note, memory_type=MemoryType.NOTE)
    print(f"✓ Imported: {note[:50]}...")

print(f"\nImported {len(notes)} memories")
```

### Export All Memories

```python
import json
from datetime import datetime

vault = VaultDB()

# Get all memories (use pagination for large datasets)
all_memories = []
offset = 0
batch_size = 100

while True:
    batch = vault.recent_memories(limit=batch_size, offset=offset)
    if not batch:
        break
    all_memories.extend(batch)
    offset += batch_size

# Export to JSON
export_data = {
    "exported_at": datetime.utcnow().isoformat(),
    "count": len(all_memories),
    "memories": [
        {
            "id": str(m.id),
            "content": m.content,
            "type": m.type,
            "tags": m.tags,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in all_memories
    ]
}

with open("vault_export.json", "w") as f:
    json.dump(export_data, f, indent=2)

print(f"Exported {len(all_memories)} memories to vault_export.json")
```

---

## Custom Integrations

### Slack Integration

```python
# Example: Import Slack messages to Vault
from slack_sdk import WebClient
from vault.db import VaultDB
from vault.models import MemoryType

slack_client = WebClient(token="xoxb-your-token")
vault = VaultDB()

# Get messages from a channel
response = slack_client.conversations_history(channel="C1234567890")
messages = response["messages"]

for msg in messages:
    # Skip bot messages
    if msg.get("bot_id"):
        continue
    
    # Import to Vault
    vault.add_memory(
        content=msg["text"],
        memory_type=MemoryType.NOTE,
        tags=["slack", "imported"],
        metadata={
            "slack_ts": msg["ts"],
            "slack_user": msg.get("user"),
            "slack_channel": "general"
        }
    )

print(f"Imported {len(messages)} Slack messages")
```

### Browser Bookmarks Import

```python
# Example: Import browser bookmarks
import json
from vault.db import VaultDB
from vault.models import MemoryType

vault = VaultDB()

# Load Chrome bookmarks (example path)
with open("path/to/Bookmarks", "r") as f:
    bookmarks_data = json.load(f)

def extract_bookmarks(node, folder_path=""):
    """Recursively extract bookmarks"""
    if node.get("type") == "url":
        return [{
            "title": node.get("name"),
            "url": node.get("url"),
            "folder": folder_path
        }]
    
    bookmarks = []
    if "children" in node:
        current_path = f"{folder_path}/{node.get('name', '')}" if folder_path else node.get('name', '')
        for child in node["children"]:
            bookmarks.extend(extract_bookmarks(child, current_path))
    
    return bookmarks

# Extract all bookmarks
all_bookmarks = extract_bookmarks(bookmarks_data["roots"]["bookmark_bar"])

# Import to Vault
for bm in all_bookmarks:
    content = f"[{bm['title']}]({bm['url']})"
    vault.add_memory(
        content=content,
        memory_type=MemoryType.REFERENCE,
        tags=["bookmark", "imported", bm['folder'].lower()],
        metadata={"source": "chrome", "url": bm['url']}
    )

print(f"Imported {len(all_bookmarks)} bookmarks")
```

### GitHub Issues Import

```python
# Example: Import GitHub issues as memories
import requests
from vault.db import VaultDB
from vault.models import MemoryType

vault = VaultDB()

# GitHub API
repo = "owner/repo"
url = f"https://api.github.com/repos/{repo}/issues"
headers = {"Authorization": "token YOUR_GITHUB_TOKEN"}

response = requests.get(url, headers=headers)
issues = response.json()

for issue in issues:
    content = f"Issue #{issue['number']}: {issue['title']}\n\n{issue['body']}"
    
    vault.add_memory(
        content=content,
        memory_type=MemoryType.REFERENCE,
        tags=["github", "issue", repo.split('/')[1]],
        metadata={
            "github_issue": issue["number"],
            "github_url": issue["html_url"],
            "github_state": issue["state"]
        }
    )

print(f"Imported {len(issues)} GitHub issues")
```

---

## MCP Server Integration

### Using in Claude Desktop

```json
// ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "vault": {
      "command": "vault-mcp"
    }
  }
}
```

Then in Claude:
```
You: Search my vault for "machine learning"
Claude: [Uses vault_search tool] Here's what I found in your vault...

You: Add this to my journal: "Meeting with Sarah about Q2 roadmap"
Claude: [Uses vault_add_text tool] I've added that to your journal.

You: What did I work on today?
Claude: [Uses vault_journal_today tool] Here's your journal for today...
```

### Custom MCP Client

```python
# Example: Custom script that uses MCP tools
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_vault_mcp():
    # Start MCP server
    server_params = StdioServerParameters(
        command="vault-mcp",
        args=[]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # Call vault_search
            result = await session.call_tool(
                "vault_search",
                {"query": "machine learning", "limit": 5}
            )
            
            print("Search results:")
            print(result.content[0].text)
            
            # Add a memory
            result = await session.call_tool(
                "vault_add_text",
                {"content": "Explored MCP integration with Vault"}
            )
            
            print(f"Added: {result.content[0].text}")

# Run
asyncio.run(use_vault_mcp())
```

---

## Advanced Patterns

### Zettelkasten-Style Linking

```python
from vault.db import VaultDB
from vault.models import MemoryType

vault = VaultDB()

# Create atomic notes with unique IDs
note1 = vault.add_memory(
    content="Zettelkasten is a personal knowledge management system",
    memory_type=MemoryType.NOTE,
    tags=["zettelkasten", "pkm"]
)

note2 = vault.add_memory(
    content="Atomic notes contain one idea each",
    memory_type=MemoryType.NOTE,
    tags=["zettelkasten", "atomic"]
)

# Create index note that references others
index = vault.add_memory(
    content=f"Index: Zettelkasten Method - See notes {note1.id}, {note2.id}",
    memory_type=MemoryType.NOTE,
    tags=["index", "zettelkasten"]
)

# Find related notes via search
related = vault.search_memories("zettelkasten method", limit=10)
print(f"Found {len(related)} related notes")
```

### Daily Standup Automation

```python
from vault.db import VaultDB
from vault.models import MemoryType
from datetime import datetime, timedelta

vault = VaultDB()

def generate_standup():
    """Generate standup report from yesterday's memories"""
    yesterday = datetime.now() - timedelta(days=1)
    
    # Get yesterday's progress
    recent = vault.recent_memories(limit=50)
    yesterday_memories = [
        m for m in recent 
        if m.created_at and m.created_at.date() == yesterday.date()
    ]
    
    # Categorize
    progress = [m for m in yesterday_memories if "done" in m.content.lower() or "completed" in m.content.lower()]
    blockers = [m for m in yesterday_memories if "blocked" in m.content.lower() or "issue" in m.content.lower()]
    
    # Generate report
    report = f"""
## Standup - {datetime.now().strftime('%Y-%m-%d')}

### Yesterday:
{chr(10).join(f"- {p.content}" for p in progress[:5])}

### Blockers:
{chr(10).join(f"- {b.content}" for b in blockers) if blockers else "- None"}

### Today:
- Continue implementation
"""
    
    # Save as memory
    vault.add_memory(
        content=report,
        memory_type=MemoryType.NOTE,
        tags=["standup", "daily"]
    )
    
    return report

# Run daily via cron
print(generate_standup())
```

### Knowledge Graph Export

```python
from vault.db import VaultDB
import networkx as nx
import matplotlib.pyplot as plt

vault = VaultDB()

def build_knowledge_graph():
    """Build graph of memory connections via tags"""
    G = nx.Graph()
    
    # Get all memories
    memories = vault.recent_memories(limit=1000)
    
    # Add nodes
    for mem in memories:
        G.add_node(str(mem.id), content=mem.content[:50], tags=mem.tags)
    
    # Add edges based on shared tags
    for i, mem1 in enumerate(memories):
        for mem2 in memories[i+1:]:
            shared_tags = set(mem1.tags or []) & set(mem2.tags or [])
            if shared_tags:
                G.add_edge(str(mem1.id), str(mem2.id), weight=len(shared_tags))
    
    # Visualize
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=False, node_size=50, alpha=0.8)
    plt.title("Vault Knowledge Graph")
    plt.savefig("knowledge_graph.png")
    print(f"Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")

build_knowledge_graph()
```

### Context-Aware AI Assistant

```python
from vault.db import VaultDB
import openai

vault = VaultDB()
openai.api_key = "your-key"

def answer_with_context(question: str) -> str:
    """Answer questions using Vault context"""
    
    # Search Vault for relevant memories
    memories = vault.search_memories(question, limit=5)
    
    # Build context
    context = "\n\n".join([
        f"Memory {i+1}: {m.memory.content}"
        for i, m in enumerate(memories)
    ])
    
    # Ask OpenAI with context
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Answer using the provided context from the user's vault."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
        ]
    )
    
    return response.choices[0].message.content

# Example usage
answer = answer_with_context("What have I learned about databases?")
print(answer)
```

---

## Error Handling

```python
from vault.db import VaultDB
from vault.exceptions import VaultException

vault = VaultDB()

try:
    # Attempt operation
    result = vault.search_memories("test query")
    
except VaultException as e:
    print(f"Vault error: {e}")
    # Handle gracefully
    
except Exception as e:
    print(f"Unexpected error: {e}")
    # Log and report
```

---

## Testing

```python
import pytest
from vault.db import VaultDB
from vault.models import MemoryType

@pytest.fixture
def vault():
    """Create test vault instance"""
    return VaultDB()

def test_add_memory(vault):
    """Test adding a memory"""
    memory = vault.add_memory(
        content="Test memory",
        memory_type=MemoryType.NOTE
    )
    assert memory.id is not None
    assert memory.content == "Test memory"

def test_search(vault):
    """Test semantic search"""
    # Add test data
    vault.add_memory("Python programming", memory_type=MemoryType.NOTE)
    vault.add_memory("Java programming", memory_type=MemoryType.NOTE)
    
    # Search
    results = vault.search_memories("Python code")
    assert len(results) > 0
    assert "Python" in results[0].memory.content
```

---

## Performance Optimization

```python
from vault.db import VaultDB
from vault.embeddings import get_embedding_provider
import time

vault = VaultDB()
embedder = get_embedding_provider()

# Batch embedding generation
texts = ["Text 1", "Text 2", "Text 3", "...100 more"]

# ❌ Slow: Individual calls
start = time.time()
for text in texts:
    embedder.embed(text)
print(f"Individual: {time.time() - start:.2f}s")

# ✅ Fast: Batch call
start = time.time()
embedder.embed_batch(texts)
print(f"Batch: {time.time() - start:.2f}s")
```

---

## Monitoring

```python
from vault.db import VaultDB
from vault.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

vault = VaultDB()

# Log operations
def monitored_add(content: str):
    start = time.time()
    try:
        memory = vault.add_memory(content=content)
        duration = time.time() - start
        logger.info(f"Added memory {memory.id} in {duration:.2f}s")
        return memory
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        raise

monitored_add("Test memory with monitoring")
```

---

For more examples, see:
- [WORKFLOW.md](WORKFLOW.md) - Daily usage patterns
- [DEPLOYMENT.md](DEPLOYMENT.md) - Setup examples
- [tests/](tests/) - Unit test examples

**Happy coding!** 🚀
