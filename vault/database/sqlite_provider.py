"""SQLite database provider implementation (local/offline support)."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID, uuid4

try:
    import numpy as np
except ImportError:
    np = None

from .base import DatabaseProvider


class SQLiteProvider(DatabaseProvider):
    """
    SQLite database provider for local/offline usage.
    
    Note: Vector search is less efficient than PostgreSQL pgvector.
    Uses simple cosine similarity with numpy for MVP.
    For production, consider sqlite-vss or sqlite-vec extensions.
    """

    def __init__(self, db_path: str):
        """
        Initialize SQLite provider.

        Args:
            db_path: Path to SQLite database file
        """
        if np is None:
            raise ImportError("numpy required for vector ops. Install: pip install numpy")

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Initialize SQLite schema if not exists."""
        cursor = self.conn.cursor()

        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                description TEXT,
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Memories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                type TEXT DEFAULT 'thought',
                source TEXT DEFAULT 'cli',
                project_id TEXT,
                tags TEXT DEFAULT '[]',
                metadata TEXT DEFAULT '{}',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
            )
        """)

        # Embeddings table (vector stored as JSON blob)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                vector TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE,
                UNIQUE(memory_id, model_name)
            )
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_memory ON embeddings(memory_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model_name)")

        self.conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """Convert SQLite Row to dict with JSON parsing."""
        if row is None:
            return None

        data = dict(row)

        # Parse JSON fields
        if "tags" in data and isinstance(data["tags"], str):
            data["tags"] = json.loads(data["tags"])
        if "metadata" in data and isinstance(data["metadata"], str):
            data["metadata"] = json.loads(data["metadata"])
        if "vector" in data and isinstance(data["vector"], str):
            data["vector"] = json.loads(data["vector"])
        if "is_active" in data:
            data["is_active"] = bool(data["is_active"])

        return data

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a = np.array(vec1)
        b = np.array(vec2)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

    # ========== Memory Operations ==========

    def add_memory(self, data: dict) -> dict:
        """Insert a new memory."""
        memory_id = str(uuid4())
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO memories (id, content, type, source, project_id, tags, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id,
                data["content"],
                data.get("type", "thought"),
                data.get("source", "cli"),
                data.get("project_id"),
                json.dumps(data.get("tags", [])),
                json.dumps(data.get("metadata", {})),
            ),
        )
        self.conn.commit()

        # Fetch and return created record
        cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        return self._row_to_dict(cursor.fetchone())

    def get_memory(self, memory_id: UUID) -> Optional[dict]:
        """Retrieve a specific memory by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE id = ?", (str(memory_id),))
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def recent_memories(self, limit: int, type: Optional[str] = None) -> List[dict]:
        """Get recent memories."""
        cursor = self.conn.cursor()

        if type:
            cursor.execute(
                "SELECT * FROM memories WHERE type = ? ORDER BY created_at DESC LIMIT ?",
                (type, limit),
            )
        else:
            cursor.execute(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?", (limit,)
            )

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def update_memory(self, memory_id: UUID, updates: dict) -> dict:
        """Update an existing memory."""
        set_clauses = []
        params = []

        for key, value in updates.items():
            if key in ["tags", "metadata"] and isinstance(value, (list, dict)):
                value = json.dumps(value)
            set_clauses.append(f"{key} = ?")
            params.append(value)

        params.append(str(memory_id))

        cursor = self.conn.cursor()
        cursor.execute(
            f"""
            UPDATE memories
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            params,
        )
        self.conn.commit()

        # Return updated record
        cursor.execute("SELECT * FROM memories WHERE id = ?", (str(memory_id),))
        return self._row_to_dict(cursor.fetchone())

    def delete_memory(self, memory_id: UUID) -> bool:
        """Delete a memory (cascade deletes embeddings)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (str(memory_id),))
        self.conn.commit()
        return cursor.rowcount > 0

    # ========== Embedding Operations ==========

    def add_embedding(self, data: dict) -> dict:
        """Insert a new embedding."""
        embedding_id = str(uuid4())
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO embeddings (id, memory_id, vector, model_name, model_version, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                embedding_id,
                str(data["memory_id"]),
                json.dumps(data["vector"]),
                data["model_name"],
                data.get("model_version"),
                int(data.get("is_active", True)),
            ),
        )
        self.conn.commit()

        cursor.execute("SELECT * FROM embeddings WHERE id = ?", (embedding_id,))
        return self._row_to_dict(cursor.fetchone())

    def deactivate_embeddings(self, memory_id: UUID, model_name: str) -> int:
        """Mark embeddings as inactive."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE embeddings
            SET is_active = 0
            WHERE memory_id = ? AND model_name = ?
            """,
            (str(memory_id), model_name),
        )
        self.conn.commit()
        return cursor.rowcount

    def search_memories(
        self, query_vector: List[float], model_name: str, limit: int
    ) -> List[dict]:
        """Semantic search using cosine similarity (slower than pgvector)."""
        cursor = self.conn.cursor()

        # Fetch all active embeddings for the model
        cursor.execute(
            """
            SELECT e.vector, e.memory_id, m.content, m.type, m.tags, m.created_at
            FROM embeddings e
            JOIN memories m ON e.memory_id = m.id
            WHERE e.model_name = ? AND e.is_active = 1
            """,
            (model_name,),
        )

        # Calculate similarities
        results = []
        for row in cursor.fetchall():
            row_dict = self._row_to_dict(row)
            stored_vector = row_dict["vector"]
            similarity = self._cosine_similarity(query_vector, stored_vector)

            results.append(
                {
                    "memory_id": row_dict["memory_id"],
                    "content": row_dict["content"],
                    "type": row_dict["type"],
                    "tags": row_dict["tags"],
                    "similarity": similarity,
                    "created_at": row_dict["created_at"],
                }
            )

        # Sort by similarity and return top N
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def get_embeddings_by_model(self, model_name: str) -> List[dict]:
        """Get all active embeddings for a specific model."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT e.*, m.content
            FROM embeddings e
            JOIN memories m ON e.memory_id = m.id
            WHERE e.model_name = ? AND e.is_active = 1
            """,
            (model_name,),
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    # ========== Project Operations ==========

    def create_project(self, data: dict) -> dict:
        """Create a new project."""
        project_id = str(uuid4())
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT INTO projects (id, name, description, status, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                project_id,
                data["name"],
                data.get("description"),
                data.get("status", "active"),
                json.dumps(data.get("metadata", {})),
            ),
        )
        self.conn.commit()

        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        return self._row_to_dict(cursor.fetchone())

    def get_project(self, project_id: UUID) -> Optional[dict]:
        """Get a specific project by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (str(project_id),))
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def get_project_by_name(self, name: str) -> Optional[dict]:
        """Get a project by name."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
        row = cursor.fetchone()
        return self._row_to_dict(row) if row else None

    def list_projects(self, status: Optional[str] = None) -> List[dict]:
        """List all projects, optionally filtered by status."""
        cursor = self.conn.cursor()

        if status:
            cursor.execute(
                "SELECT * FROM projects WHERE status = ? ORDER BY created_at DESC",
                (status,),
            )
        else:
            cursor.execute("SELECT * FROM projects ORDER BY created_at DESC")

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_project_memories(self, project_id: UUID) -> List[dict]:
        """Get all memories associated with a project."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM memories WHERE project_id = ? ORDER BY created_at DESC",
            (str(project_id),),
        )
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def update_project(self, project_id: UUID, updates: dict) -> dict:
        """Update a project."""
        set_clauses = []
        params = []

        for key, value in updates.items():
            if key == "metadata" and isinstance(value, dict):
                value = json.dumps(value)
            set_clauses.append(f"{key} = ?")
            params.append(value)

        params.append(str(project_id))

        cursor = self.conn.cursor()
        cursor.execute(
            f"""
            UPDATE projects
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            params,
        )
        self.conn.commit()

        cursor.execute("SELECT * FROM projects WHERE id = ?", (str(project_id),))
        return self._row_to_dict(cursor.fetchone())

    # ========== Memory Link Operations ==========

    def add_memory_link(self, data: dict) -> dict:
        """Create a relationship between two memories."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO memory_links (from_memory_id, to_memory_id, relation_type)
            VALUES (?, ?, ?)
            """,
            (
                str(data["from_memory_id"]),
                str(data["to_memory_id"]),
                data.get("relation_type", "extends"),
            ),
        )
        self.conn.commit()
        cursor.execute(
            """
            SELECT * FROM memory_links
            WHERE from_memory_id = ? AND to_memory_id = ? AND relation_type = ?
            """,
            (
                str(data["from_memory_id"]),
                str(data["to_memory_id"]),
                data.get("relation_type", "extends"),
            ),
        )
        return self._row_to_dict(cursor.fetchone())

    # ========== Migration Operations ==========

    def get_all_memories_for_migration(self) -> List[dict]:
        """Get all memories for bulk embedding migration."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, content FROM memories ORDER BY created_at")
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_embedding_stats(self) -> dict:
        """Get statistics about embeddings by model."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT model_name, COUNT(*) as count
            FROM embeddings
            WHERE is_active = 1
            GROUP BY model_name
            """
        )
        return {row["model_name"]: row["count"] for row in cursor.fetchall()}

    # ========== Connection Management ==========

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def ping(self) -> bool:
        """Test database connection."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
