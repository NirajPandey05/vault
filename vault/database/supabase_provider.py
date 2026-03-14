"""Supabase database provider implementation."""

import json
from typing import List, Optional
from uuid import UUID

from supabase import Client, create_client

from .base import DatabaseProvider


class SupabaseProvider(DatabaseProvider):
    """Supabase (managed PostgreSQL) database provider."""

    def __init__(self, url: str, key: str):
        """
        Initialize Supabase provider.

        Args:
            url: Supabase project URL
            key: Supabase anon/service key
        """
        self.client: Client = create_client(url, key)

    @staticmethod
    def _normalize_embedding_record(record: dict) -> dict:
        """Convert Supabase pgvector responses into Pydantic-friendly Python types."""
        normalized = dict(record)
        vector = normalized.get("vector")
        if isinstance(vector, str):
            normalized["vector"] = json.loads(vector)

        return normalized

    # ========== Memory Operations ==========

    def add_memory(self, data: dict) -> dict:
        """Insert a new memory."""
        response = self.client.table("memories").insert(data).execute()
        return response.data[0]

    def get_memory(self, memory_id: UUID) -> Optional[dict]:
        """Retrieve a specific memory by ID."""
        response = (
            self.client.table("memories").select("*").eq("id", str(memory_id)).execute()
        )
        return response.data[0] if response.data else None

    def recent_memories(self, limit: int, type: Optional[str] = None) -> List[dict]:
        """Get recent memories."""
        query = self.client.table("memories").select("*").order("created_at", desc=True)

        if type:
            query = query.eq("type", type)

        response = query.limit(limit).execute()
        return response.data

    def update_memory(self, memory_id: UUID, updates: dict) -> dict:
        """Update an existing memory."""
        response = (
            self.client.table("memories")
            .update(updates)
            .eq("id", str(memory_id))
            .execute()
        )
        return response.data[0]

    def delete_memory(self, memory_id: UUID) -> bool:
        """Delete a memory (cascade deletes embeddings)."""
        response = self.client.table("memories").delete().eq("id", str(memory_id)).execute()
        return len(response.data) > 0

    # ========== Embedding Operations ==========

    def add_embedding(self, data: dict) -> dict:
        """Insert a new embedding."""
        response = self.client.table("embeddings").insert(data).execute()
        return self._normalize_embedding_record(response.data[0])

    def deactivate_embeddings(self, memory_id: UUID, model_name: str) -> int:
        """Mark embeddings as inactive."""
        response = (
            self.client.table("embeddings")
            .update({"is_active": False})
            .eq("memory_id", str(memory_id))
            .eq("model_name", model_name)
            .execute()
        )
        return len(response.data)

    def search_memories(
        self, query_vector: List[float], model_name: str, limit: int
    ) -> List[dict]:
        """Semantic search using RPC function."""
        response = self.client.rpc(
            "search_memories",
            {
                "query_embedding": query_vector,
                "model_filter": model_name,
                "limit_count": limit,
            },
        ).execute()
        return response.data

    def get_embeddings_by_model(self, model_name: str) -> List[dict]:
        """Get all active embeddings for a specific model."""
        response = (
            self.client.table("embeddings")
            .select("*, memories!inner(content)")
            .eq("model_name", model_name)
            .eq("is_active", True)
            .execute()
        )
        return [self._normalize_embedding_record(item) for item in response.data]

    # ========== Project Operations ==========

    def create_project(self, data: dict) -> dict:
        """Create a new project."""
        response = self.client.table("projects").insert(data).execute()
        return response.data[0]

    def get_project(self, project_id: UUID) -> Optional[dict]:
        """Get a specific project by ID."""
        response = (
            self.client.table("projects").select("*").eq("id", str(project_id)).execute()
        )
        return response.data[0] if response.data else None

    def get_project_by_name(self, name: str) -> Optional[dict]:
        """Get a project by name."""
        response = self.client.table("projects").select("*").eq("name", name).execute()
        return response.data[0] if response.data else None

    def list_projects(self, status: Optional[str] = None) -> List[dict]:
        """List all projects, optionally filtered by status."""
        query = self.client.table("projects").select("*").order("created_at", desc=True)

        if status:
            query = query.eq("status", status)

        response = query.execute()
        return response.data

    def get_project_memories(self, project_id: UUID) -> List[dict]:
        """Get all memories associated with a project."""
        response = (
            self.client.table("memories")
            .select("*")
            .eq("project_id", str(project_id))
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    def update_project(self, project_id: UUID, updates: dict) -> dict:
        """Update a project."""
        response = (
            self.client.table("projects")
            .update(updates)
            .eq("id", str(project_id))
            .execute()
        )
        return response.data[0]

    # ========== Migration Operations ==========

    def get_all_memories_for_migration(self) -> List[dict]:
        """Get all memories for bulk embedding migration."""
        response = (
            self.client.table("memories")
            .select("id, content")
            .order("created_at")
            .execute()
        )
        return response.data

    def get_embedding_stats(self) -> dict:
        """Get statistics about embeddings by model."""
        # Note: Supabase doesn't have native aggregation via Python client
        # This would require a custom RPC function or fetching all and counting
        response = self.client.table("embeddings").select("model_name, is_active").execute()

        stats = {}
        for emb in response.data:
            if emb["is_active"]:
                model = emb["model_name"]
                stats[model] = stats.get(model, 0) + 1

        return stats

    # ========== Connection Management ==========

    def close(self):
        """Close connection (Supabase client handles this automatically)."""
        # Supabase REST client doesn't require explicit closure
        pass

    def ping(self) -> bool:
        """Test database connection."""
        try:
            # Try a simple query
            self.client.table("projects").select("count", count="exact").limit(1).execute()
            return True
        except Exception:
            return False
