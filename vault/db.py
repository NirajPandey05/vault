"""High-level database operations for Vault."""

from uuid import UUID

from .config import get_config
from .database import get_database_provider
from .database.base import DatabaseProvider
from .embeddings.factory import get_embedding_provider
from .models import Embedding, Memory, Project, SearchResult


class VaultDB:
    """Provider-agnostic database facade used by the CLI, journal manager, and MCP server."""

    def __init__(self, provider: DatabaseProvider | None = None):
        self.db: DatabaseProvider = provider or get_database_provider()
        self.config = get_config()

    # ========== Memory Operations ==========

    def add_memory(
        self,
        content: str,
        type: str = "thought",
        source: str = "cli",
        project_id: UUID | None = None,
        tags: list[str] | None = None,
        auto_embed: bool = True,
    ) -> Memory:
        """Add a new memory and optionally generate an embedding."""
        memory_data = {
            "content": content,
            "type": type,
            "source": source,
            "project_id": str(project_id) if project_id else None,
            "tags": tags or [],
            "metadata": {},
        }

        memory = Memory(**self.db.add_memory(memory_data))

        if auto_embed:
            self._generate_embedding(memory.id, content)

        return memory

    def get_memory(self, memory_id: UUID) -> Memory | None:
        """Retrieve a specific memory by ID."""
        memory_dict = self.db.get_memory(memory_id)
        return Memory(**memory_dict) if memory_dict else None

    def recent_memories(self, limit: int = 10, type: str | None = None) -> list[Memory]:
        """Get recent memories, optionally filtered by type."""
        return [Memory(**item) for item in self.db.recent_memories(limit=limit, type=type)]

    # ========== Embedding Operations ==========

    def _generate_embedding(self, memory_id: UUID, content: str) -> Embedding:
        """Generate and store an embedding for a memory."""
        provider = get_embedding_provider()
        vector = provider.embed(content)

        self.db.deactivate_embeddings(memory_id, provider.model_name)

        embedding_data = {
            "memory_id": str(memory_id),
            "vector": vector,
            "model_name": provider.model_name,
            "model_version": None,
            "is_active": True,
        }
        return Embedding(**self.db.add_embedding(embedding_data))

    def search_memories(
        self,
        query: str,
        limit: int = 10,
        model_name: str | None = None,
    ) -> list[SearchResult]:
        """Search memories by semantic similarity."""
        provider = get_embedding_provider(model_name)
        query_vector = provider.embed(query)
        active_model = model_name or provider.model_name

        results: list[SearchResult] = []
        for item in self.db.search_memories(query_vector, active_model, limit):
            memory = Memory(
                id=item["memory_id"],
                content=item["content"],
                type=item["type"],
                tags=item.get("tags", []),
                created_at=item["created_at"],
                source="cli",
            )
            results.append(
                SearchResult(
                    memory=memory,
                    similarity=item["similarity"],
                    embedding_model=active_model,
                )
            )

        return results

    # ========== Project Operations ==========

    def create_project(self, name: str, description: str | None = None) -> Project:
        """Create a new project."""
        project_data = {
            "name": name,
            "description": description,
            "status": "active",
            "metadata": {},
        }
        return Project(**self.db.create_project(project_data))

    def list_projects(self, status: str | None = None) -> list[Project]:
        """List all projects, optionally filtered by status."""
        return [Project(**item) for item in self.db.list_projects(status=status)]

    def get_project_memories(self, project_id: UUID) -> list[Memory]:
        """Get all memories associated with a project."""
        return [Memory(**item) for item in self.db.get_project_memories(project_id)]

    # ========== Migration Operations ==========

    def migrate_embeddings(
        self,
        from_model: str,
        to_model: str,
        batch_size: int = 100,
        dry_run: bool = False,
    ) -> dict:
        """Migrate active embeddings from one model to another."""
        memories = self.db.get_all_memories_for_migration()
        total = len(memories)

        if dry_run:
            return {
                "total_memories": total,
                "estimated_cost_usd": self._estimate_embedding_cost(total, to_model),
                "dry_run": True,
            }

        provider = get_embedding_provider(to_model)
        migrated = 0

        for start in range(0, total, batch_size):
            batch = memories[start : start + batch_size]
            contents = [item["content"] for item in batch]
            vectors = provider.embed_batch(contents)

            for memory, vector in zip(batch, vectors):
                memory_id = UUID(str(memory["id"]))
                self.db.deactivate_embeddings(memory_id, from_model)
                self.db.deactivate_embeddings(memory_id, to_model)
                self.db.add_embedding(
                    {
                        "memory_id": str(memory_id),
                        "vector": vector,
                        "model_name": to_model,
                        "model_version": None,
                        "is_active": True,
                    }
                )
                migrated += 1

        return {
            "from_model": from_model,
            "to_model": to_model,
            "migrated": migrated,
            "total_memories": total,
            "dry_run": False,
        }

    def get_embedding_stats(self) -> dict:
        """Return active embedding counts by model."""
        return self.db.get_embedding_stats()

    def _estimate_embedding_cost(self, memory_count: int, model_name: str) -> float:
        """Estimate migration cost using a rough 100-tokens-per-memory heuristic."""
        model_config = self.config.get_model_config(model_name)
        tokens = memory_count * 100
        return (tokens / 1000) * model_config["cost_per_1k_tokens"]

    # ========== Connection Management ==========

    def ping(self) -> bool:
        """Test provider connectivity."""
        return self.db.ping()

    def close(self):
        """Close the underlying provider connection."""
        self.db.close()
