"""Supabase storage operations for documents."""


class DocumentStorage:
    """Handle document storage in Supabase."""
    
    async def upload_file(self, file_path: str, filename: str) -> str:
        """Upload file to Supabase Storage."""
        # To be implemented
        return "storage_path"
    
    async def download_file(self, storage_path: str, local_path: str):
        """Download file from Supabase Storage."""
        # To be implemented
        pass
    
    async def delete_file(self, storage_path: str):
        """Delete file from Supabase Storage."""
        # To be implemented
        pass
