"""Supabase client singleton."""
from supabase import create_client, Client
from src.utils.config import settings
from typing import Optional


class SupabaseClient:
    """
    Singleton Supabase client.
    
    This ensures we only create one connection to Supabase
    throughout the application, which is more efficient.
    """
    
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create Supabase client.
        
        Returns:
            Client: Supabase client instance
            
        Raises:
            ValueError: If Supabase credentials are not configured
        """
        if cls._instance is None:
            # Get credentials from settings
            url = settings.supabase_url
            key = settings.supabase_service_key
            
            # Validate credentials
            if not url or not key:
                raise ValueError(
                    "Supabase credentials not configured. "
                    "Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env file"
                )
            
            # Create client
            cls._instance = create_client(url, key)
            print(f"[OK] Connected to Supabase: {url}")
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset the client instance (useful for testing)."""
        cls._instance = None


# Convenience function
def get_supabase() -> Client:
    """
    Get Supabase client instance.
    
    This is the main function you'll use throughout the app.
    
    Example:
        db = get_supabase()
        result = db.table('documents').select('*').execute()
    """
    return SupabaseClient.get_client()
