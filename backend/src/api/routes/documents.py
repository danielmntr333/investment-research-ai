"""Document management endpoints."""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import tempfile
import uuid
from datetime import datetime
import traceback

from src.db.supabase import get_supabase
from src.document_processing.parser import DocumentParser
from src.rag.chunking import FinancialDocumentChunker
from src.rag.embeddings import EmbeddingService

router = APIRouter(prefix="/api/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    """Document response model."""
    id: str
    filename: str
    file_type: str
    file_size: int
    uploaded_at: str
    processed: bool
    processing_error: Optional[str] = None
    metadata: dict = {}


class DocumentListResponse(BaseModel):
    """Document list response."""
    documents: List[DocumentResponse]
    total: int


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None)
):
    """
    Upload and process a document.
    
    Steps:
    1. Save uploaded file to temp location
    2. Parse document (extract text)
    3. Chunk document (smart chunking)
    4. Generate embeddings
    5. Store in database
    6. Return document metadata
    """
    db = get_supabase()
    doc_id = str(uuid.uuid4())
    
    # Validate file type
    allowed_types = ['application/pdf', 'pdf']
    file_type = file.content_type or 'application/pdf'
    
    if not any(t in file_type.lower() for t in allowed_types):
        # Try to infer from filename
        if file.filename and not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Only PDF files are currently supported."
            )
    
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            # Read and save uploaded file
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        file_size = len(content)
        
        # Insert document record (processing=false initially)
        doc_data = {
            'id': doc_id,
            'filename': file.filename,
            'file_type': file_type,
            'file_size': file_size,
            'storage_path': f"documents/{doc_id}/{file.filename}",
            'metadata': {},
            'uploaded_at': datetime.utcnow().isoformat(),
            'processed': False,
            'processing_error': None
        }
        
        # Only add user_id if it's a valid UUID
        if user_id:
            try:
                uuid.UUID(user_id)  # Validate UUID format
                doc_data['user_id'] = user_id
            except (ValueError, AttributeError):
                # Invalid UUID format, skip it
                print(f"⚠️ Warning: Invalid UUID format for user_id: {user_id}")
        
        result = db.table('documents').insert(doc_data).execute()
        
        # Process document
        try:
            # 1. Parse document
            parser = DocumentParser()
            parsed_doc = parser.parse(tmp_path, 'pdf')
            
            # 2. Chunk document
            chunker = FinancialDocumentChunker()
            chunks = chunker.chunk_document(
                text=parsed_doc.full_text,
                document_id=doc_id,
                metadata={'page_count': len(parsed_doc.pages)}
            )
            
            if not chunks:
                raise ValueError("No content extracted from document")
            
            # 3. Generate embeddings
            try:
                embedder = EmbeddingService()
                chunks_with_embeddings = embedder.embed_chunks(chunks)
            except ValueError as ve:
                # API key not configured
                raise ValueError(
                    "OpenAI API key not configured. Please set OPENAI_API_KEY in your backend/.env file. "
                    "Get your API key from https://platform.openai.com/api-keys"
                )
            
            # 4. Store chunks in database
            chunk_records = []
            for i, chunk in enumerate(chunks_with_embeddings):
                # Merge chunk metadata with document filename for better source attribution
                chunk_metadata = chunk.get('metadata', {})
                chunk_metadata['document_name'] = file.filename  # Add filename to chunk metadata
                chunk_metadata['file_type'] = file_type
                
                chunk_record = {
                    'id': str(uuid.uuid4()),
                    'document_id': doc_id,
                    'content': chunk['content'],
                    'embedding': chunk['embedding'],
                    'chunk_index': i,
                    'metadata': chunk_metadata,
                    'created_at': datetime.utcnow().isoformat()
                }
                chunk_records.append(chunk_record)
            
            # Batch insert chunks
            db.table('document_chunks').insert(chunk_records).execute()
            
            # Update document as processed
            db.table('documents').update({
                'processed': True,
                'metadata': {
                    'page_count': len(parsed_doc.pages),
                    'chunk_count': len(chunks),
                    'total_chars': len(parsed_doc.full_text)
                }
            }).eq('id', doc_id).execute()
            
            doc_data['processed'] = True
            doc_data['metadata'] = {
                'page_count': len(parsed_doc.pages),
                'chunk_count': len(chunks),
                'total_chars': len(parsed_doc.full_text)
            }
            
        except Exception as e:
            # Update document with error
            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"❌ Document processing error: {error_msg}")
            print(f"Stack trace: {error_trace}")
            
            db.table('documents').update({
                'processing_error': error_msg
            }).eq('id', doc_id).execute()
            
            doc_data['processing_error'] = error_msg
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process document: {error_msg}"
            )
        
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        return DocumentResponse(**doc_data)
    
    except HTTPException:
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"❌ Upload failed: {str(e)}")
        print(f"Stack trace: {error_trace}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """List all documents for the current user."""
    try:
        db = get_supabase()
        
        # Query documents
        result = db.table('documents').select('*').order('uploaded_at', desc=True).execute()
        
        documents = [DocumentResponse(**doc) for doc in result.data]
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get document metadata."""
    try:
        db = get_supabase()
        
        result = db.table('documents').select('*').eq('id', doc_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document: {str(e)}"
        )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and all its chunks."""
    try:
        db = get_supabase()
        
        # Check if document exists
        result = db.table('documents').select('id').eq('id', doc_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Delete chunks (cascade should handle this, but explicit is better)
        db.table('document_chunks').delete().eq('document_id', doc_id).execute()
        
        # Delete document
        db.table('documents').delete().eq('id', doc_id).execute()
        
        return {"message": "Document deleted successfully", "id": doc_id}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
