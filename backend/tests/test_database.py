from sqlalchemy.orm import Session
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.models.conversation import Conversation, Message
from app.models.feedback import Feedback
from app.models.observability import QueryLog


def test_user_creation(db_session: Session):
    # 1. Create a user
    user = User(
        email="test@enterprise.com",
        hashed_password="hashed_secure_password_123",
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@enterprise.com"
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.created_at is not None
    assert user.updated_at is not None


def test_document_and_chunks(db_session: Session):
    # 1. Setup parent user
    user = User(email="author@doc.com", hashed_password="pwd")
    db_session.add(user)
    db_session.commit()

    # 2. Create document
    doc = Document(
        user_id=user.id,
        filename="test_policy.pdf",
        file_type="pdf",
        file_size=2048,
        processing_status="PROCESSING",
        page_count=5,
        chunk_count=0,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    assert doc.id is not None
    assert doc.user_id == user.id
    assert doc.processing_status == "PROCESSING"

    # 3. Create document chunk (testing SafeVector list storage)
    mock_vector = [0.12, -0.43, 0.88, 0.01] + [0.0] * 1532  # 1536 dims
    chunk = DocumentChunk(
        document_id=doc.id,
        user_id=user.id,
        chunk_index=0,
        page_number=1,
        section="Introduction",
        text="This is a test document text content.",
        embedding=mock_vector,
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)

    assert chunk.id is not None
    assert chunk.document_id == doc.id
    assert chunk.user_id == user.id
    # Test vector deserialization
    assert len(chunk.embedding) == 1536
    assert chunk.embedding[0] == 0.12
    assert chunk.embedding[1] == -0.43
    assert chunk.embedding[2] == 0.88

    # 4. Verify relations back-populating
    db_session.refresh(doc)
    assert len(doc.chunks) == 1
    assert doc.chunks[0].text == "This is a test document text content."


def test_conversations_and_messages_with_feedback(db_session: Session):
    user = User(email="chat@doc.com", hashed_password="pwd")
    db_session.add(user)
    db_session.commit()

    # Create Conversation
    conv = Conversation(user_id=user.id, title="Test Chat Session")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    assert conv.id is not None
    assert conv.title == "Test Chat Session"

    # Create Message with structured Sources
    sources_data = [
        {"document_id": 1, "filename": "policy.pdf", "page_number": 3, "text": "leave policy"}
    ]
    msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content="According to the policy, leave must be approved.",
        sources=sources_data,
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)

    assert msg.id is not None
    assert msg.role == "assistant"
    assert msg.sources == sources_data

    # Add Feedback
    fb = Feedback(
        message_id=msg.id,
        user_id=user.id,
        rating=1,
        feedback="Extremely helpful answer!",
    )
    db_session.add(fb)
    db_session.commit()
    db_session.refresh(fb)

    assert fb.id is not None
    assert fb.rating == 1
    assert fb.feedback == "Extremely helpful answer!"
    assert fb.message_id == msg.id


def test_observability_query_logs(db_session: Session):
    user = User(email="metrics@doc.com", hashed_password="pwd")
    db_session.add(user)
    db_session.commit()

    # Log an AI search transaction
    log = QueryLog(
        user_id=user.id,
        question="How many leave days do we get?",
        retrieved_chunks=[{"chunk_id": 12, "document_id": 3, "score": 0.89}],
        retrieval_latency=0.15,
        llm_latency=1.23,
        total_latency=1.38,
        tokens_used=1200,
        estimated_cost=0.0024,
        model_used="gpt-4o-mini",
        errors=None,
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)

    assert log.id is not None
    assert log.user_id == user.id
    assert log.tokens_used == 1200
    assert log.estimated_cost == 0.0024
    assert log.total_latency == 1.38
