"""PostgreSQL database provider implementation (direct connection)."""

import json
from typing import List, Optional
from uuid import UUID

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from pgvector.psycopg2 import register_vector
except ImportError:
    psycopg2 = None

from .base import DatabaseProvider


class PostgresProvider(DatabaseProvider):
    """Direct PostgreSQL connection provider (for self-hosted, Neon, Railway, etc.)."""

    def __init__(self, connection_string: str):
        """
        Initialize PostgreSQL provider.

        Args:
            connection_string: PostgreSQL connection string
                Example: "postgresql://user:pass@host:5432/dbname"
        """
        if psycopg2 is None:
            raise ImportError("psycopg2 required. Install: pip install psycopg2-binary pgvector")

        self.conn = psycopg2.connect(connection_string)
        self.conn.autocommit = False
        register_vector(self.conn)

    def _execute_query(self, query: str, params: tuple = (), fetch: str = "all") -> List[dict] | dict | None:
        """Execute a query and return results as dict(s)."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)

            if fetch == "all":
                result = cur.fetchall()
                return [dict(row) for row in result] if result else []
            elif fetch == "one":
                result = cur.fetchone()
                return dict(result) if result else None
            else:  # no fetch
                self.conn.commit()
                return None

    # ========== Memory Operations ==========

    def add_memory(self, data: dict) -> dict:
        """Insert a new memory."""
        query = """
            INSERT INTO memories (content, type, source, project_id, tags, metadata, doc_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id, content, type, source, project_id, tags, metadata, doc_path, created_at, updated_at
        """
        params = (
            data["content"],
            data.get("type", "thought"),
            data.get("source", "cli"),
            data.get("project_id"),
            data.get("tags", []),
            json.dumps(data.get("metadata", {})),
            data.get("doc_path"),
        )
        result = self._execute_query(query, params, fetch="one")
        self.conn.commit()
        return result

    def get_memory(self, memory_id: UUID) -> Optional[dict]:
        """Retrieve a specific memory by ID."""
        query = "SELECT * FROM memories WHERE id = %s"
        return self._execute_query(query, (str(memory_id),), fetch="one")

    def recent_memories(self, limit: int, type: Optional[str] = None) -> List[dict]:
        """Get recent memories."""
        if type:
            query = """
                SELECT * FROM memories
                WHERE type = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            params = (type, limit)
        else:
            query = "SELECT * FROM memories ORDER BY created_at DESC LIMIT %s"
            params = (limit,)

        return self._execute_query(query, params, fetch="all")

    def update_memory(self, memory_id: UUID, updates: dict) -> dict:
        """Update an existing memory."""
        set_clauses = []
        params = []

        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            params.append(value)

        params.append(str(memory_id))

        query = f"""
            UPDATE memories
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """
        result = self._execute_query(query, tuple(params), fetch="one")
        self.conn.commit()
        return result

    def delete_memory(self, memory_id: UUID) -> bool:
        """Delete a memory (cascade deletes embeddings)."""
        query = "DELETE FROM memories WHERE id = %s RETURNING id"
        result = self._execute_query(query, (str(memory_id),), fetch="one")
        self.conn.commit()
        return result is not None

    # ========== Embedding Operations ==========

    def add_embedding(self, data: dict) -> dict:
        """Insert a new embedding."""
        query = """
            INSERT INTO embeddings (memory_id, vector, model_name, model_version, is_active)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, memory_id, vector, model_name, model_version, is_active, created_at
        """
        params = (
            str(data["memory_id"]),
            data["vector"],
            data["model_name"],
            data.get("model_version"),
            data.get("is_active", True),
        )
        result = self._execute_query(query, params, fetch="one")
        self.conn.commit()
        # Convert vector to list for consistency
        if result and "vector" in result:
            result["vector"] = list(result["vector"])
        return result

    def deactivate_embeddings(self, memory_id: UUID, model_name: str) -> int:
        """Mark embeddings as inactive."""
        query = """
            UPDATE embeddings
            SET is_active = FALSE
            WHERE memory_id = %s AND model_name = %s
            RETURNING id
        """
        result = self._execute_query(query, (str(memory_id), model_name), fetch="all")
        self.conn.commit()
        return len(result)

    def search_memories(
        self, query_vector: List[float], model_name: str, limit: int
    ) -> List[dict]:
        """Semantic search using vector similarity."""
        query = """
            SELECT 
                m.id as memory_id,
                m.content,
                m.type,
                m.tags,
                m.doc_path,
                1 - (e.vector <=> %s::vector) AS similarity,
                m.created_at
            FROM embeddings e
            JOIN memories m ON e.memory_id = m.id
            WHERE e.model_name = %s AND e.is_active = true
            ORDER BY e.vector <=> %s::vector
            LIMIT %s
        """
        return self._execute_query(
            query, (query_vector, model_name, query_vector, limit), fetch="all"
        )

    def get_embeddings_by_model(self, model_name: str) -> List[dict]:
        """Get all active embeddings for a specific model."""
        query = """
            SELECT e.*, m.content
            FROM embeddings e
            JOIN memories m ON e.memory_id = m.id
            WHERE e.model_name = %s AND e.is_active = true
        """
        return self._execute_query(query, (model_name,), fetch="all")

    # ========== Project Operations ==========

    def create_project(self, data: dict) -> dict:
        """Create a new project."""
        query = """
            INSERT INTO projects (name, description, status, metadata)
            VALUES (%s, %s, %s, %s)
            RETURNING id, name, description, status, metadata, created_at, updated_at
        """
        params = (
            data["name"],
            data.get("description"),
            data.get("status", "active"),
            json.dumps(data.get("metadata", {})),
        )
        result = self._execute_query(query, params, fetch="one")
        self.conn.commit()
        return result

    def get_project(self, project_id: UUID) -> Optional[dict]:
        """Get a specific project by ID."""
        query = "SELECT * FROM projects WHERE id = %s"
        return self._execute_query(query, (str(project_id),), fetch="one")

    def get_project_by_name(self, name: str) -> Optional[dict]:
        """Get a project by name."""
        query = "SELECT * FROM projects WHERE name = %s"
        return self._execute_query(query, (name,), fetch="one")

    def list_projects(self, status: Optional[str] = None) -> List[dict]:
        """List all projects, optionally filtered by status."""
        if status:
            query = "SELECT * FROM projects WHERE status = %s ORDER BY created_at DESC"
            params = (status,)
        else:
            query = "SELECT * FROM projects ORDER BY created_at DESC"
            params = ()

        return self._execute_query(query, params, fetch="all")

    def get_project_memories(self, project_id: UUID) -> List[dict]:
        """Get all memories associated with a project."""
        query = """
            SELECT * FROM memories
            WHERE project_id = %s
            ORDER BY created_at DESC
        """
        return self._execute_query(query, (str(project_id),), fetch="all")

    def update_project(self, project_id: UUID, updates: dict) -> dict:
        """Update a project."""
        set_clauses = []
        params = []

        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            params.append(value)

        params.append(str(project_id))

        query = f"""
            UPDATE projects
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE id = %s
            RETURNING *
        """
        result = self._execute_query(query, tuple(params), fetch="one")
        self.conn.commit()
        return result

    # ========== Memory Link Operations ==========

    def add_memory_link(self, data: dict) -> dict:
        """Create a relationship between two memories."""
        query = """
            INSERT INTO memory_links (from_memory_id, to_memory_id, relation_type)
            VALUES (%s, %s, %s)
            ON CONFLICT (from_memory_id, to_memory_id, relation_type) DO UPDATE
            SET relation_type = EXCLUDED.relation_type
            RETURNING id, from_memory_id, to_memory_id, relation_type, created_at
        """
        params = (
            str(data["from_memory_id"]),
            str(data["to_memory_id"]),
            data.get("relation_type", "extends"),
        )
        result = self._execute_query(query, params, fetch="one")
        self.conn.commit()
        return result

    # ========== Migration Operations ==========

    def get_all_memories_for_migration(self) -> List[dict]:
        """Get all memories for bulk embedding migration."""
        query = "SELECT id, content FROM memories ORDER BY created_at"
        return self._execute_query(query, fetch="all")

    def get_embedding_stats(self) -> dict:
        """Get statistics about embeddings by model."""
        query = """
            SELECT model_name, COUNT(*) as count
            FROM embeddings
            WHERE is_active = true
            GROUP BY model_name
        """
        results = self._execute_query(query, fetch="all")
        return {row["model_name"]: row["count"] for row in results}

    # ========== Connection Management ==========

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def ping(self) -> bool:
        """Test database connection."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception:
            return False
