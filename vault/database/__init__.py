"""Database abstraction layer for Vault.

Provides a common interface for multiple database backends:
- Supabase (PostgreSQL + managed API)
- PostgreSQL (direct connection)
- SQLite (local, with vector support)
"""

from .base import DatabaseProvider
from .factory import get_database_provider

__all__ = ["DatabaseProvider", "get_database_provider"]
