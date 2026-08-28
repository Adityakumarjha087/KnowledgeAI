import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.services.memory import rewrite_query


def test_query_rewriter():
    # 1. Test empty history (returns original query)
    assert rewrite_query("What is sick leave?", []) == "What is sick leave?"

    # 2. Test history parsing (mock-llm will yield standalone response)
    history = [
        {"role": "user", "content": "What is the annual leave policy?"},
        {"role": "assistant", "content": "It is 20 days per year."}
    ]
    standalone = rewrite_query("What about sick leave?", history)
    # The mock LLM yields standard mock content, which we verify runs without error
    assert len(standalone) > 0


def test_chat_generation_stream(client: TestClient, db_session: Session):
    # Setup auth and token
    response = client.post(
        "/api/auth/register",
        json={"email": "chatstream@test.com", "password": "mypassword123"},
    )
    user_id = response.json()["id"]
    login_response = client.post(
        "/api/auth/login",
        data={"username": "chatstream@test.com", "password": "mypassword123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Call streaming chat API
    chat_response = client.post(
        "/api/chat",
        json={"message": "What is the holiday calendar?"},
        headers=headers,
    )
    assert chat_response.status_code == 200
    assert "text/event-stream" in chat_response.headers["content-type"]

    # Read streaming chunks
    stream_content = chat_response.text
    assert "sources" in stream_content
    assert "token" in stream_content
    assert "done" in stream_content

    # Verify conversation and message were created in DB
    conv = db_session.query(Conversation).filter(Conversation.user_id == user_id).first()
    assert conv is not None
    assert conv.title.startswith("What is the holiday")
    
    messages = db_session.query(Message).filter(Message.conversation_id == conv.id).all()
    assert len(messages) == 2  # User message + Assistant message
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"
    assert messages[1].sources is not None


def test_feedback_submission(client: TestClient, db_session: Session):
    # Setup auth
    client.post(
        "/api/auth/register",
        json={"email": "feedback@test.com", "password": "mypassword123"},
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "feedback@test.com", "password": "mypassword123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Generate message through chat
    client.post(
        "/api/chat",
        json={"message": "Test query for feedback"},
        headers=headers,
    )

    # Get assistant message ID
    assistant_msg = db_session.query(Message).filter(Message.role == "assistant").first()
    assert assistant_msg is not None

    # Submit feedback
    fb_response = client.post(
        "/api/feedback",
        json={
            "message_id": assistant_msg.id,
            "rating": 1,
            "feedback": "Perfect answer!"
        },
        headers=headers,
    )
    assert fb_response.status_code == 201
    fb_data = fb_response.json()
    assert fb_data["rating"] == 1
    assert fb_data["feedback"] == "Perfect answer!"


def test_metrics_and_evaluation(client: TestClient):
    # Setup auth
    client.post(
        "/api/auth/register",
        json={"email": "admin@test.com", "password": "mypassword123"},
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "admin@test.com", "password": "mypassword123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Access metrics
    m_response = client.get("/api/metrics", headers=headers)
    assert m_response.status_code == 200
    metrics = m_response.json()
    assert "total_users" in metrics
    assert "total_questions" in metrics
    assert "total_estimated_cost_usd" in metrics

    # Run evaluation
    eval_response = client.get("/api/evaluation", headers=headers)
    assert eval_response.status_code == 200
    report = eval_response.json()
    assert report["status"] == "success"
    assert "metrics" in report
    assert "faithfulness" in report["metrics"]
