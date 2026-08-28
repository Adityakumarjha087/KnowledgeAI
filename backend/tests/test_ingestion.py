import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.ingestion.parsers import parse_document
from app.ingestion.splitter import split_text
from app.services.ingestion import ingest_document_task
from app.rag.retrieval import hybrid_retrieval


def test_parsers():
    # Test plain text and markdown parsing
    text_content = b"This is a sample document content.\nSecond paragraph here."
    text, pages = parse_document(text_content, "txt")
    assert "sample" in text
    assert pages == 1

    # Mock PdfReader to bypass actual PDF binary stream validation
    with patch("app.ingestion.parsers.PdfReader") as mock_pdf_class:
        mock_reader = MagicMock()
        page_1 = MagicMock()
        page_1.extract_text.return_value = "Intro content"
        page_2 = MagicMock()
        page_2.extract_text.return_value = "Chapter content"
        
        mock_reader.pages = [page_1, page_2]
        mock_pdf_class.return_value = mock_reader
        
        parsed, pages = parse_document(b"mock_pdf_bytes", "pdf")
        assert "Intro" in parsed
        assert "Chapter" in parsed
        assert pages == 2


def test_splitter():
    text = "[PAGE_1]\nParagraph 1 is long enough to exceed the size limit.\n\n[PAGE_2]\nParagraph 2 is also long and will trigger split."
    # Set chunk_size very small (30 chars) to guarantee multiple chunks are generated
    chunks = split_text(text, chunk_size=30, chunk_overlap=5)
    
    assert len(chunks) >= 2
    assert chunks[0]["page_number"] == 1
    assert chunks[-1]["page_number"] == 2
    assert len(chunks[0]["text"]) > 0


def test_ingestion_end_to_end(db_session: Session):
    # Setup users
    user_a = User(email="usera@rag.com", hashed_password="pwd")
    user_b = User(email="userb@rag.com", hashed_password="pwd")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    # Create document for User A
    doc = Document(
        user_id=user_a.id,
        filename="company_policy.txt",
        file_type="txt",
        file_size=1024,
        processing_status="UPLOADED",
    )
    db_session.add(doc)
    db_session.commit()

    # Execute ingestion task
    file_bytes = b"Company holiday calendar: Christmas on Dec 25. Thanksgiving in November."
    ingest_document_task(db_session, doc.id, file_bytes)

    # Verify status and chunk count
    db_session.refresh(doc)
    assert doc.processing_status == "COMPLETED"
    assert doc.chunk_count > 0

    # Verify chunks database entries
    chunk = db_session.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).first()
    assert chunk is not None
    assert chunk.user_id == user_a.id
    assert "holiday" in chunk.text
    assert chunk.embedding is not None

    # Test Hybrid Retrieval for User A
    results_a = hybrid_retrieval(db_session, "holiday calendar", user_a.id, limit=5)
    assert len(results_a) > 0
    assert "holiday" in results_a[0]["chunk"].text
    assert results_a[0]["filename"] == "company_policy.txt"

    # Test Tenant Isolation: User B runs the query and must get ZERO results!
    results_b = hybrid_retrieval(db_session, "holiday calendar", user_b.id, limit=5)
    assert len(results_b) == 0
