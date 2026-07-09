"""
Set up local PostgreSQL database for Vault.

Usage:
    python scripts/setup_local_postgres.py

Requires POSTGRES_CONNECTION_STRING in .env (without database name, or pointing to postgres db).
e.g.  POSTGRES_CONNECTION_STRING=postgresql://postgres:yourpassword@localhost:5432/vault
"""

import sys
import os

# Load .env
from pathlib import Path
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

CONN_STR = os.getenv("POSTGRES_CONNECTION_STRING")
if not CONN_STR:
    print("❌ POSTGRES_CONNECTION_STRING not set in .env")
    sys.exit(1)

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# Parse db name out of connection string and connect to 'postgres' db to create 'vault'
# e.g. postgresql://postgres:pass@localhost:5432/vault  →  connect to .../postgres first
def get_admin_conn_str(conn_str: str) -> tuple[str, str]:
    """Return (admin_conn_str_to_postgres_db, target_db_name)."""
    from urllib.parse import urlparse, urlunparse
    p = urlparse(conn_str)
    db_name = p.path.lstrip("/") or "vault"
    admin = urlunparse(p._replace(path="/postgres"))
    return admin, db_name


def run():
    admin_conn_str, db_name = get_admin_conn_str(CONN_STR)

    print(f"Connecting to PostgreSQL (admin db) ...")
    try:
        conn = psycopg2.connect(admin_conn_str)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("   Check POSTGRES_CONNECTION_STRING in .env (user, password, host, port)")
        sys.exit(1)

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    # Create database if it doesn't exist
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    if cur.fetchone():
        print(f"ℹ  Database '{db_name}' already exists — skipping creation")
    else:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        print(f"✓ Created database '{db_name}'")

    cur.close()
    conn.close()

    # Now connect to the vault db and apply schema
    print(f"Applying schema to '{db_name}' ...")
    try:
        vault_conn = psycopg2.connect(CONN_STR)
    except Exception as e:
        print(f"❌ Could not connect to '{db_name}': {e}")
        sys.exit(1)

    vault_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = vault_conn.cursor()

    # Enable pgvector
    try:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✓ pgvector extension enabled")
    except Exception as e:
        print(f"❌ pgvector not available: {e}")
        print("   Install pgvector: https://github.com/pgvector/pgvector#installation")
        vault_conn.close()
        sys.exit(1)

    # Apply schema
    schema_path = Path(__file__).parent / "schema.sql"
    schema_sql = schema_path.read_text(encoding="utf-8")

    try:
        cur.execute(schema_sql)
        print("✓ Schema applied successfully")
    except Exception as e:
        print(f"❌ Schema application failed: {e}")
        vault_conn.close()
        sys.exit(1)

    # Verify tables
    cur.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename
    """)
    tables = [row[0] for row in cur.fetchall()]
    print(f"\n✓ Tables created: {', '.join(tables)}")

    # Verify vector dimension
    cur.execute("""
        SELECT atttypmod FROM pg_attribute
        JOIN pg_class ON pg_class.oid = pg_attribute.attrelid
        WHERE pg_class.relname = 'embeddings' AND pg_attribute.attname = 'vector'
    """)
    row = cur.fetchone()
    if row:
        dims = row[0]  # atttypmod for pgvector equals the dimension directly
        print(f"✓ Vector column dimension: {dims}")

    cur.close()
    vault_conn.close()
    print(f"\n✅ Local Postgres database '{db_name}' is ready!")
    print(f"   Connection: {CONN_STR}")


if __name__ == "__main__":
    run()
