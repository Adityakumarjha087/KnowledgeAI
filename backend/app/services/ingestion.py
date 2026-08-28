import traceback
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.ingestion.parsers import parse_document
from app.ingestion.splitter import split_text
from app.ai.embeddings import get_embedding_provider


def ingest_document_task(db_session: Session, document_id: int, file_bytes: bytes) -> None:
    """
    Asynchronous background worker pipeline:
    1. Parse document text content and page counts.
    2. Split into intelligent chunks.
    3. Generate vector embeddings in batch.
    4. Store chunks and embeddings in pgvector.
    5. Update document completion status metrics.
    """
    # Fetch the document in session
    doc = db_session.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return

    try:
        # 1. Update status to PROCESSING
        doc.processing_status = "PROCESSING"
        db_session.commit()
        db_session.refresh(doc)

        # 2. Parse text and page count based on file type
        parsed_text, page_count = parse_document(file_bytes, doc.file_type)
        doc.page_count = page_count
        db_session.commit()

        # 3. Intelligent splitting
        chunks_metadata = split_text(parsed_text)
        if not chunks_metadata:
            raise ValueError("No text content could be extracted from this document.")

        # 4. Generate batch embeddings
        embedding_provider = get_embedding_provider()
        texts = [c["text"] for c in chunks_metadata]
        embeddings = embedding_provider.get_embeddings(texts)

        # 5. Save chunks to Vector DB
        db_chunks = []
        for idx, (chunk_meta, embedding) in enumerate(zip(chunks_metadata, embeddings)):
            db_chunk = DocumentChunk(
                document_id=doc.id,
                user_id=doc.user_id,
                chunk_index=idx,
                page_number=chunk_meta["page_number"],
                section=chunk_meta["section"],
                text=chunk_meta["text"],
                embedding=embedding
            )
            db_chunks.append(db_chunk)
            
        db_session.bulk_save_objects(db_chunks)
        
        # 6. Mark COMPLETED
        doc.chunk_count = len(db_chunks)
        doc.processing_status = "COMPLETED"
        db_session.commit()

    except Exception as e:
        db_session.rollback()
        # Save error message and set FAILED
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Ingestion failed for doc {document_id}: {error_msg}")
        
        # Fetch fresh doc instance to write failure status
        doc = db_session.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.processing_status = "FAILED"
            db_session.commit()
