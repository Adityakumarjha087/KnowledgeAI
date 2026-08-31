from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.core.config import settings
from app.api.deps import get_current_active_user
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.schemas.document import DocumentResponse
from app.services.storage import get_storage_provider
from app.services.ingestion import ingest_document_task

router = APIRouter(prefix="/documents", tags=["documents"])


def background_ingest_runner(document_id: int, file_bytes: bytes) -> None:
    """Wrapper to handle database session lifespan safely inside background threads"""
    db = SessionLocal()
    try:
        ingest_document_task(db, document_id, file_bytes)
    finally:
        db.close()


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Uploads a document. Saves bytes to the storage provider, inserts document 
    record, and triggers background parsing, chunking, and embedding generation.
    """
    # 1. Validate file extension
    filename = file.filename
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Allowed types: {settings.ALLOWED_EXTENSIONS}",
        )

    # 2. Read and validate file size
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    # 3. Save to storage provider
    try:
        storage = get_storage_provider()
        storage_path = storage.upload_file(file_bytes, filename, file.content_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write file to storage: {str(e)}",
        )

    # 4. Insert Document record in status UPLOADED
    doc = Document(
        user_id=current_user.id,
        filename=filename,
        file_type=ext,
        file_size=len(file_bytes),
        processing_status="UPLOADED",
        page_count=0,
        chunk_count=0,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 5. Enqueue background ingestion processing task
    background_tasks.add_task(background_ingest_runner, doc.id, file_bytes)
    
    return doc


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lists all documents uploaded by the authenticated user (Tenant Isolated)"""
    return db.query(Document).filter(Document.user_id == current_user.id).all()


@router.get("/{doc_id}", response_model=DocumentResponse)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Retrieves document metadata by ID, enforcing user ownership"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")
    return doc


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Deletes a document and its vector chunks from database and storage, enforcing user ownership"""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this document")

    # Delete from S3/local storage
    try:
        storage = get_storage_provider()
        storage.delete_file(doc.filename)
    except Exception as e:
        print(f"Failed to delete storage file {doc.filename}: {str(e)}")

    # Explicitly delete all associated document chunks (handles SQLite cascade)
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()

    # Delete Document record
    db.delete(doc)
    db.commit()
    return None
