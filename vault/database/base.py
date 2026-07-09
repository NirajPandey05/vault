"""Abstract database provider interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID


class DatabaseProvider(ABC):
    """
    Abstract base class for database providers.
    
    All database backends (Supabase, PostgreSQL, SQLite) must implement
    this interface to ensure consistent behavior across providers.
    """

    # ========== Memory Operations ==========

    @abstractmethod
    def add_memory(self, data: dict) -> dict:
        """
        Insert a new memory into the database.

        Args:
            data: Memory data (content, type, source, project_id, tags, metadata)

        Returns:
            Created memory record as dict with all fields including id
        """
        pass

    @abstractmethod
    def get_memory(self, memory_id: UUID) -> Optional[dict]:
        """
        Retrieve a specific memory by ID.

        Args:
            memory_id: UUID of the memory

        Returns:
            Memory record as dict, or None if not found
        """
        pass

    @abstractmethod
    def recent_memories(self, limit: int, type: Optional[str] = None) -> List[dict]:
        """
        Get recent memories ordered by created_at DESC.

        Args:
            limit: Maximum number of memories to return
            type: Optional filter by memory type

        Returns:
            List of memory records as dicts
        """
        pass

    @abstractmethod
    def update_memory(self, memory_id: UUID, updates: dict) -> dict:
        """
        Update an existing memory.

        Args:
            memory_id: UUID of the memory
            updates: Fields to update

        Returns:
            Updated memory record as dict
        """
        pass

    @abstractmethod
    def delete_memory(self, memory_id: UUID) -> bool:
        """
        Delete a memory and its embeddings.

        Args:
            memory_id: UUID of the memory

        Returns:
            True if deleted, False if not found
        """
        pass

    # ========== Embedding Operations ==========

    @abstractmethod
    def add_embedding(self, data: dict) -> dict:
        """
        Insert a new embedding for a memory.

        Args:
            data: Embedding data (memory_id, vector, model_name, is_active)

        Returns:
            Created embedding record as dict
        """
        pass

    @abstractmethod
    def deactivate_embeddings(self, memory_id: UUID, model_name: str) -> int:
        """
        Mark embeddings as inactive for a specific memory and model.

        Args:
            memory_id: UUID of the memory
            model_name: Model name to deactivate

        Returns:
            Number of embeddings updated
        """
        pass

    @abstractmethod
    def search_memories(
        self, query_vector: List[float], model_name: str, limit: int
    ) -> List[dict]:
        """
        Semantic search using vector similarity.

        Args:
            query_vector: Query embedding vector
            model_name: Model name to search within
            limit: Maximum results to return

        Returns:
            List of dicts with memory data + similarity score
        """
        pass

    @abstractmethod
    def get_embeddings_by_model(self, model_name: str) -> List[dict]:
        """
        Get all active embeddings for a specific model.

        Args:
            model_name: Model name to filter by

        Returns:
            List of embedding records with memory content
        """
        pass

    # ========== Project Operations ==========

    @abstractmethod
    def create_project(self, data: dict) -> dict:
        """
        Create a new project.

        Args:
            data: Project data (name, description, status, metadata)

        Returns:
            Created project record as dict
        """
        pass

    @abstractmethod
    def get_project(self, project_id: UUID) -> Optional[dict]:
        """
        Get a specific project by ID.

        Args:
            project_id: UUID of the project

        Returns:
            Project record as dict, or None if not found
        """
        pass

    @abstractmethod
    def get_project_by_name(self, name: str) -> Optional[dict]:
        """
        Get a project by name.

        Args:
            name: Project name

        Returns:
            Project record as dict, or None if not found
        """
        pass

    @abstractmethod
    def list_projects(self, status: Optional[str] = None) -> List[dict]:
        """
        List all projects, optionally filtered by status.

        Args:
            status: Optional status filter (active, paused, completed, archived)

        Returns:
            List of project records as dicts
        """
        pass

    @abstractmethod
    def get_project_memories(self, project_id: UUID) -> List[dict]:
        """
        Get all memories associated with a project.

        Args:
            project_id: UUID of the project

        Returns:
            List of memory records as dicts
        """
        pass

    @abstractmethod
    def update_project(self, project_id: UUID, updates: dict) -> dict:
        """
        Update a project.

        Args:
            project_id: UUID of the project
            updates: Fields to update

        Returns:
            Updated project record as dict
        """
        pass

    # ========== Memory Link Operations ==========

    @abstractmethod
    def add_memory_link(self, data: dict) -> dict:
        """
        Create a relationship between two memories.

        Args:
            data: Link data (from_memory_id, to_memory_id, relation_type)

        Returns:
            Created memory link record as dict
        """
        pass

    # ========== Migration Operations ==========

    @abstractmethod
    def get_all_memories_for_migration(self) -> List[dict]:
        """
        Get all memories (id + content) for bulk embedding migration.

        Returns:
            List of dicts with id and content fields
        """
        pass

    @abstractmethod
    def get_embedding_stats(self) -> dict:
        """
        Get statistics about embeddings by model.

        Returns:
            Dict with model_name -> count mapping
        """
        pass

    # ========== Connection Management ==========

    @abstractmethod
    def close(self):
        """Close database connection(s)."""
        pass

    @abstractmethod
    def ping(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection is healthy
        """
        pass
