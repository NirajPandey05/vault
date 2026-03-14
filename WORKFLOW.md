# Vault Workflow Guide

How to use Vault in your daily knowledge management workflow.

---

## Table of Contents

1. [Daily Capture Workflow](#daily-capture-workflow)
2. [Weekly Review](#weekly-review)
3. [Project-Based Organization](#project-based-organization)
4. [Search and Recall](#search-and-recall)
5. [Knowledge Synthesis](#knowledge-synthesis)
6. [Common Patterns](#common-patterns)
7. [Advanced Workflows](#advanced-workflows)

---

## Daily Capture Workflow

### Morning Routine (5 minutes)

**Review yesterday's thoughts:**
```bash
# See what you captured yesterday
vault recent 20

# Search for unresolved items
vault search "TODO" 
vault search "question"
```

**Set intentions:**
```bash
# Capture today's priorities
vault add "Today's focus: Implement authentication module" --type progress --tags "daily,work"

# Log important meetings
vault add "Meeting notes: Product roadmap discussion at 2pm" --type reference --tags "meetings"
```

### Throughout the Day

**`vault add` accepts either inline text or a file (`--file/-f`):**
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

**Capture thoughts immediately:**
```bash
# Quick captures (< 30 seconds)
vault add "Interesting pattern: Using event sourcing for audit logs"

# Ideas as they come
vault add "Idea: Add voice memo support to Vault" --type idea --tags "vault,enhancement"

# Questions to explore later
vault add "How does pgvector indexing work under the hood?" --type question --tags "learning,databases"
```

**Progress tracking:**
```bash
# After completing tasks
vault add "Completed user authentication flow" --type progress --tags "work,milestone"

# When blocked
vault add "Blocked: Need design approval before proceeding" --type decision --tags "work,blocked"
```

**Learning captures:**
```bash
# Interesting articles/docs
vault add "Great article on database sharding: https://example.com/sharding" --type reference --tags "databases,scaling"

# Code snippets or techniques
vault add "TIL: Python's walrus operator := is great for list comprehensions" --tags "python,til"
```

### Evening Reflection (5 minutes)

**Review and tag:**
```bash
# See today's captures
vault recent 15

# Search and organize
vault search "today"

# Make connections
vault search "similar concept" --limit 5
```

---

## Weekly Review

Every Sunday, spend 20-30 minutes organizing your Second Brain.

### Step 1: Audit Last Week

```bash
# Review all captures from last week
vault recent 100

# Group by type
vault recent --type idea
vault recent --type progress
vault recent --type question
```

### Step 2: Answer Open Questions

```bash
# Find questions
vault search "how does" --type question
vault search "why" --type question

# Add answers as new memories
vault add "Answer: pgvector uses IVFFlat indexing for approximate nearest neighbor search" --tags "databases,answers"
```

### Step 3: Surface Insights

```bash
# Look for patterns
vault search "productivity"
vault search "learning"

# Document insights
vault add "Pattern noticed: Most productive in early morning sessions" --type idea --tags "productivity,insight"
```

### Step 4: Update Projects

```bash
# Review project status
vault project list

# Add weekly summaries
vault add "Week summary: Completed auth module, started on API design" --type progress --tags "work,weekly"
```

---

## Project-Based Organization

### Creating Projects

```bash
# Work projects
vault project create "Customer Portal Redesign" --description "Q1 2026 redesign initiative"

# Learning projects
vault project create "Machine Learning Study" --description "Learning ML fundamentals"

# Personal projects
vault project create "Second Brain Setup" --description "Building personal knowledge system"
```

### Linking Memories to Projects

*(Note: Project linking via CLI coming soon. For now, use tags)*

```bash
# Use project name as tag
vault add "API design decision: RESTful vs GraphQL" --tags "customer-portal,architecture"

# Search by project
vault search "customer portal"
```

### Project Context

```bash
# Get all context for a project
vault project context <project-id>

# Export project memories
vault search "project-name" > project-notes.txt
```

---

## Search and Recall

### Semantic Search (The Magic ✨)

```bash
# Search by meaning, not exact words
vault search "authentication"
# Returns: "user login", "auth flow", "OAuth setup", etc.

vault search "database performance"
# Returns: "slow queries", "indexing strategy", "query optimization", etc.

vault search "best practices"
# Returns: relevant advice across all topics
```

### Finding Specific Types

```bash
# All your ideas
vault search "innovation" --type idea

# Recent decisions
vault recent --type decision

# Progress across projects
vault recent --type progress
```

### Temporal Search

```bash
# Recent captures
vault recent 5    # Last 5 memories
vault recent 50   # Last 50 memories

# Use search + recency
vault search "architecture" | head -10
```

### Combining Searches

```bash
# Search + filter by type
vault search "python" --type reference

# Multiple tags (use search)
vault search "python api"
```

---

## Knowledge Synthesis

### Making Connections

When you search and find related memories:

```bash
# Find related concepts
vault search "vector embeddings"

# Document the connection
vault add "Connection: Vector embeddings relate to semantic search and recommendation systems" --type idea --tags "connections"
```

### Creating Knowledge Hierarchies

```bash
# Parent concept
vault add "Topic: Database Scaling Strategies" --type reference --tags "databases,index"

# Sub-concepts
vault add "Horizontal scaling: sharding, replication" --tags "databases,scaling"
vault add "Vertical scaling: hardware upgrades" --tags "databases,scaling"
vault add "Read replicas for query distribution" --tags "databases,scaling"

# Later search "scaling" to see all related
vault search "scaling"
```

### Periodic Synthesis

Monthly, create summary memories:

```bash
# Review month's learning
vault search "databases" | grep "March"

# Create synthesis
vault add "March Learning Summary: Focused on database internals, learned about indexing, query optimization, and replication strategies" --type idea --tags "monthly-review,databases"
```

---

## Common Patterns

### Pattern 1: Meeting Notes

**Before meeting:**
```bash
vault add "Meeting prep: Questions for Product team - roadmap timeline, resource allocation" --type reference --tags "meetings,prep"
```

**During meeting:**
```bash
vault add "Decision: Launch MVP by April 15th" --type decision --tags "meetings,product"
vault add "Action item: Schedule design review by March 10th" --tags "meetings,action"
```

**After meeting:**
```bash
vault search "product meeting" --limit 10
```

### Pattern 2: Reading and Research

**While reading:**
```bash
vault add "Key insight from 'Designing Data-Intensive Applications': Event sourcing provides audit trail" --type reference --tags "reading,databases"

vault add "Quote: 'Premature optimization is the root of all evil' - Knuth" --tags "reading,quotes"
```

**After finishing:**
```bash
vault add "Book summary: DDIA covers distributed systems, replication, partitioning, transactions" --type reference --tags "reading,summary"
```

### Pattern 3: Troubleshooting

**When encountering error:**
```bash
vault add "Error: PostgreSQL connection timeout with pgvector queries" --tags "troubleshooting,databases"
```

**During investigation:**
```bash
vault add "Hypothesis: IVFFlat index needs more lists for dataset size" --tags "troubleshooting,databases"
```

**After resolution:**
```bash
vault add "Solution: Increased IVFFlat lists from 100 to 500, queries now fast" --type reference --tags "troubleshooting,databases,solved"
```

### Pattern 4: Learning New Technology

**Day 1 - Overview:**
```bash
vault add "Starting to learn React: JavaScript library for building UIs" --tags "react,learning"
vault add "React uses component-based architecture" --tags "react,concepts"
```

**Day 7 - Practical:**
```bash
vault add "React hooks useEffect example: runs after every render" --type reference --tags "react,code"
```

**Day 30 - Synthesis:**
```bash
vault search "react"
vault add "React learning complete: comfortable with components, hooks, state management" --type progress --tags "react,milestone"
```

---

## Advanced Workflows

### Workflow 1: Zettelkasten Method

Use Vault for Zettelkasten-style note-taking:

```bash
# Atomic notes (one idea per memory)
vault add "Spaced repetition improves long-term retention" --tags "learning,memory"

# Connect ideas through search
vault search "learning" 
vault search "memory retention"

# Create index notes
vault add "Index: Learning Techniques - spaced repetition, active recall, interleaving" --type reference --tags "index,learning"
```

### Workflow 2: Research Projects

```bash
# Research question
vault add "Research question: What makes vector databases fast?" --type question --tags "research,databases"

# Hypothesis
vault add "Hypothesis: Approximate nearest neighbor search sacrifices accuracy for speed" --tags "research,databases"

# Evidence gathering
vault add "Paper finding: HNSW provides 10-100x speedup over exact search" --type reference --tags "research,databases"

# Conclusion
vault add "Conclusion: Vector databases use approximate algorithms (HNSW, IVFFlat) to balance speed and accuracy" --type idea --tags "research,databases"
```

### Workflow 3: Writing Projects

```bash
# Brainstorm
vault add "Blog post idea: How I built a Second Brain for $0.30/mo" --type idea --tags "writing,blog"

# Outline
vault add "Outline: 1. Problem 2. Architecture 3. Implementation 4. Results" --tags "writing,blog"

# Research
vault search "second brain"
vault search "personal knowledge"

# Drafting (use search results as reference)
# Write in your editor, then:
vault add "Blog post drafted, ready for review" --type progress --tags "writing,blog"
```

### Workflow 4: Decision Making

```bash
# Decision needed
vault add "Decision needed: Which database for Vault - Supabase, Postgres, or SQLite?" --type question --tags "decisions,vault"

# Gather options
vault add "Option 1: Supabase - easy setup, free tier, managed" --tags "decisions,vault"
vault add "Option 2: Postgres - full control, self-hosted" --tags "decisions,vault"
vault add "Option 3: SQLite - local, offline-first" --tags "decisions,vault"

# Analysis
vault search "decisions vault"

# Decision
vault add "Decision: Support all three via abstraction layer for maximum flexibility" --type decision --tags "decisions,vault"

# Outcome
vault add "Result: Abstraction layer successful, migration is easy" --type progress --tags "decisions,vault,result"
```

---

## Tips and Best Practices

### ✅ Do's

- **Capture immediately** - Don't wait, thoughts are fleeting
- **Use descriptive content** - Make it searchable
- **Tag consistently** - Develop your own tagging system
- **Review regularly** - Weekly reviews prevent information overload
- **Trust semantic search** - It finds related ideas you forgot about
- **One idea per memory** - Keep it atomic
- **Link through search** - Use search to find connections

### ❌ Don'ts

- **Don't over-organize** - Tags and search are enough
- **Don't edit obsessively** - Capture > perfect formatting
- **Don't worry about duplicates** - Search finds all instances
- **Don't create complex hierarchies** - Stay flat, use tags
- **Don't force connections** - Let them emerge naturally
- **Don't skip the capture** - "I'll remember" = you won't

---

## Integration with Other Tools

### With Obsidian/Notion

```bash
# Export for Obsidian
vault search "topic" > topic-notes.md

# Import from Obsidian
vault add --file obsidian-note.md --tags "imported,obsidian"
```

### With Calendar/Tasks

```bash
# Daily standup notes
vault add "Standup: Yesterday - auth flow, Today - API design, Blockers - none" --tags "daily,standup"

# Weekly planning
vault add "Week goals: Complete MVP, Write documentation, Deploy staging" --tags "weekly,planning"
```

### With Code Editor

```bash
# Document code decisions
vault add "Code decision: Used Factory pattern for database providers to support multiple backends" --type decision --tags "code,patterns"

# Save useful snippets
vault add "Useful regex for email validation: ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$" --type reference --tags "code,regex"
```

---

## Measuring Success

After 30 days of use:

```bash
# Total captures
vault recent 1000 | wc -l

# Most common tags
vault search "" | grep -o '#\w*' | sort | uniq -c | sort -rn

# Knowledge growth
vault search "learned" --type progress
vault search "insight" --type idea

# Decision tracking
vault recent --type decision
```

---

## Your Second Brain Journey

**Week 1:** Capture everything, don't worry about organization
**Week 2-4:** Develop tagging habits, start weekly reviews  
**Month 2:** Notice patterns emerging, solidify workflow  
**Month 3+:** Your Second Brain becomes invaluable, can't live without it

**The goal:** Offload memory to Vault, free your mind for thinking, not remembering.

---

## Questions?

Check out:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Setup guide
- [EXAMPLES.py](EXAMPLES.py) - Code examples
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design

**Happy knowledge building!** 🧠✨
