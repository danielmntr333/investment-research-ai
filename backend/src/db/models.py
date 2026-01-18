"""Pydantic models for database entities."""
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID


class User(BaseModel):
    """User model."""
    id: UUID
    email: str
    api_key: str
    created_at: datetime
    usage_quota: int
    usage_count: int


class Document(BaseModel):
    """Document model."""
    id: UUID
    user_id: UUID
    filename: str
    file_type: str
    file_size: int
    storage_path: str
    metadata: Dict = {}
    uploaded_at: datetime
    processed: bool = False
    processing_error: Optional[str] = None


class DocumentChunk(BaseModel):
    """Document chunk model."""
    id: UUID
    document_id: UUID
    content: str
    embedding: Optional[List[float]] = None
    chunk_index: int
    metadata: Dict = {}
    created_at: datetime


class Message(BaseModel):
    """Message model."""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    metadata: Dict = {}
    created_at: datetime


class Citation(BaseModel):
    """Citation model."""
    id: UUID
    message_id: UUID
    chunk_id: UUID
    relevance_score: float
    created_at: datetime
