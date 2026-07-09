# Vault Tagging Scheme

This document defines compact, consistent tags for memories stored in Vault so coding agents can retrieve useful context with predictable queries.

## Goal

Use tags to improve recall, not to duplicate full content. Keep tag vocabulary small, stable, and machine-friendly.

## Principles

- Use 3 to 6 tags per memory.
- Always include `repo:` and `kind:` tags.
- Usually include one `area:` tag.
- Prefer singular canonical names.
- Use lowercase only.
- Use `:`-prefixed namespaces instead of freeform labels.
- Put status in `state:`, not mixed into note text.
- Keep note text meaningful even without tags.

## Tag Buckets

Use these buckets in most memories:

- `repo:` codebase or product
- `area:` subsystem or feature area
- `kind:` what type of durable knowledge this is
- `state:` lifecycle or confidence

Optional when needed:

- `tech:` language, framework, database, or tool

## Recommended Vocabulary

### `repo:`

- `repo:vault`
- `repo:agent-tutorial`
- `repo:rtmp-product`

### `area:`

- `area:auth`
- `area:cli`
- `area:db`
- `area:deploy`
- `area:embeddings`
- `area:mcp`
- `area:search`
- `area:setup`
- `area:test`
- `area:ui`
- `area:workflow`

Add more only when a new area appears often enough to justify standardization.

### `kind:`

- `kind:decision`
- `kind:bugfix`
- `kind:workflow`
- `kind:reference`
- `kind:setup`
- `kind:gotcha`
- `kind:adr`
- `kind:investigation`

### `state:`

- `state:active`
- `state:done`
- `state:blocked`
- `state:superseded`
- `state:verified`
- `state:unverified`

### `tech:`

- `tech:python`
- `tech:pytest`
- `tech:fastapi`
- `tech:sqlite`
- `tech:postgres`
- `tech:supabase`
- `tech:openai`
- `tech:aws`

## Tag Rules

### 1. `type` and `kind` are different

Vault memory `type` already exists in data model and should continue to describe broad memory intent:

- `thought`
- `idea`
- `progress`
- `decision`
- `question`
- `workflow`
- `reference`

Use `kind:` tags for retrieval precision across similar memories.

Example:

- Vault `type`: `decision`
- Tags: `repo:vault,area:db,kind:decision,state:verified,tech:sqlite`

### 2. Pick one canonical form

Bad:

- `area:database`
- `area:db`
- `database`

Good:

- `area:db`

### 3. Avoid noisy tags

Do not add tags like:

- `important`
- `stuff`
- `misc`
- `todo` when `state:active` or `state:blocked` says more
- long sentence fragments

### 4. Prefer stable categories over temporary wording

Bad:

- `fix-for-weird-auth-bug`

Good:

- `area:auth`
- `kind:bugfix`
- `state:verified`

Put detail in memory content, not in tags.

## Standard Patterns

### Architecture decision

- `repo:vault`
- `area:db`
- `kind:decision`
- `state:verified`
- `tech:sqlite`

### Durable bug fix

- `repo:vault`
- `area:cli`
- `kind:bugfix`
- `state:verified`

### Setup note

- `repo:vault`
- `area:setup`
- `kind:setup`
- `state:verified`

### Reusable workflow

- `repo:vault`
- `area:workflow`
- `kind:workflow`
- `state:verified`

### Open investigation

- `repo:vault`
- `area:search`
- `kind:investigation`
- `state:active`

## Examples

### Decision

```powershell
vault add "SQLite provider fine for local dev and small memory sets; use Postgres or Supabase for larger semantic search workloads." --type decision --tags "repo:vault,area:db,kind:decision,state:verified,tech:sqlite"
```

### Bug fix

```powershell
vault add "`vault add --file` only accepts UTF-8 text. Convert legacy files before import or import will fail." --type decision --tags "repo:vault,area:cli,kind:bugfix,state:verified"
```

### Workflow

```powershell
vault add "Before changing database provider, run schema setup, then smoke-test `vault search` and `vault recent`." --type workflow --tags "repo:vault,area:workflow,area:db,kind:workflow,state:verified"
```

### Reference note

```powershell
vault add -f .\docs\adr-db-provider.md --type reference --tags "repo:vault,area:db,kind:adr,state:verified"
```

## Agent Retrieval Guidance

Agents should search using both content terms and canonical tags.

### Query pattern

Start broad:

```text
<repo> <area> <feature> <error>
```

Then narrow with canonical tag words inside query text:

```text
repo:vault area:db kind:decision sqlite embeddings
```

### Good agent queries

- `vault search "repo:vault area:db sqlite vector similarity"`
- `vault search "repo:vault area:cli add --file utf-8 import failure"`
- `vault search "repo:vault area:workflow database provider migration"`

### Retrieval order

1. Search by repo + area + problem.
2. If too broad, add `kind:` and `tech:` terms.
3. If task is ongoing, check recent memories too.

## What To Save

Good candidates for tagged memories:

- architectural decisions
- reusable workflows
- non-obvious bug fixes
- setup gotchas
- investigation summaries
- commands that solved repeated problems

Do not save:

- trivial progress noise
- raw temporary logs
- duplicated documentation
- secrets
- long copied stack traces without summary

## Minimal Default Scheme

If unsure, use this default set:

- `repo:<repo-name>`
- `area:<subsystem>`
- `kind:<decision|bugfix|workflow|reference|setup>`
- `state:<verified|active|blocked>`

Example:

```text
repo:vault,area:db,kind:decision,state:verified
```

This is enough structure for agents to retrieve well without over-tagging.