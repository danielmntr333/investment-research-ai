"""
Test script to verify Supabase connection.

Run this after setting up your .env file to make sure everything works!

Usage:
    python test_connection.py
"""
import sys
import io

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.db.supabase import get_supabase
from src.utils.config import settings


def test_connection():
    """Test connection to Supabase."""
    
    print("🔍 Testing Supabase Connection...")
    print(f"   Environment: {settings.environment}")
    print(f"   Supabase URL: {settings.supabase_url}")
    print()
    
    try:
        # Get client
        db = get_supabase()
        
        # Test query - count documents
        result = db.table('documents').select('*', count='exact').execute()
        
        print("✅ Connection successful!")
        print(f"   Documents in database: {result.count}")
        
        # Test query - count users
        users_result = db.table('users').select('*', count='exact').execute()
        print(f"   Users in database: {users_result.count}")
        
        # List all tables (verify schema)
        print("\n📊 Available tables:")
        tables = [
            'users', 'documents', 'document_chunks', 
            'conversations', 'messages', 'citations',
            'evaluations', 'prompt_versions'
        ]
        for table in tables:
            try:
                result = db.table(table).select('*', count='exact').limit(0).execute()
                print(f"   ✓ {table} ({result.count} rows)")
            except Exception as e:
                print(f"   ✗ {table} - Error: {str(e)}")
        
        print("\n🎉 All systems go! Your database is ready.")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Next steps:")
        print("   1. Create a .env file in backend/ folder")
        print("   2. Add your Supabase credentials:")
        print("      SUPABASE_URL=https://your-project.supabase.co")
        print("      SUPABASE_SERVICE_KEY=your-key-here")
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        print("\n💡 Check:")
        print("   1. Your .env file has correct credentials")
        print("   2. You ran setup_supabase.sql in Supabase SQL Editor")
        print("   3. Your Supabase project is active")


if __name__ == "__main__":
    test_connection()
