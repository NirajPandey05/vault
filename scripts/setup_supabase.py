"""Setup script for Supabase database."""

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()


def setup_database():
    """Initialize Supabase database with schema."""
    
    # Get Supabase credentials
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        print("   Copy .env.example to .env and fill in your credentials")
        return False
    
    print(f"🔗 Connecting to: {url}")
    
    try:
        client: Client = create_client(url, key)
        
        # Read schema file
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, "r") as f:
            schema_sql = f.read()
        
        print("📝 Loading schema...")
        
        # Note: Supabase Python client doesn't directly support raw SQL execution
        # You'll need to run the schema.sql file manually in the Supabase SQL Editor
        # Or use the Supabase CLI
        
        print("✅ Schema file ready at:", schema_path)
        print("\n⚠️  Manual Step Required:")
        print("   1. Open your Supabase project dashboard")
        print("   2. Go to SQL Editor")
        print(f"   3. Copy and paste contents from: {schema_path}")
        print("   4. Run the SQL")
        print("\nAlternatively, use Supabase CLI:")
        print(f"   supabase db push")
        
        # Verify connection by checking tables
        print("\n🔍 Verifying connection...")
        response = client.table("projects").select("count", count="exact").execute()
        print(f"✅ Connection successful!")
        print(f"   Projects table exists")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify SUPABASE_URL and SUPABASE_KEY in .env")
        print("2. Ensure you have created a Supabase project")
        print("3. Check your internet connection")
        return False


def enable_pgvector():
    """Instructions for enabling pgvector."""
    print("\n📦 Enable pgvector Extension:")
    print("   1. Go to Database → Extensions in Supabase dashboard")
    print("   2. Search for 'vector'")
    print("   3. Enable 'pgvector'")
    print("   4. Wait for extension to activate")


def main():
    """Main setup function."""
    print("=" * 70)
    print("🧠 Vault - Database Setup")
    print("=" * 70)
    print()
    
    # Check for .env file
    if not Path(".env").exists():
        print("❌ .env file not found")
        print("   Copy .env.example to .env and fill in your credentials:")
        print("   cp .env.example .env")
        return
    
    # Setup database
    success = setup_database()
    
    if success:
        print("\n" + "=" * 70)
        print("🎉 Setup Instructions")
        print("=" * 70)
        enable_pgvector()
        print("\n✅ Once pgvector is enabled, run schema.sql in SQL Editor")
        print("\n🚀 Then you're ready to use Vault:")
        print("   vault add 'My first thought'")
        print("   vault search 'first'")
        print("   vault recent")


if __name__ == "__main__":
    main()
