from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import verify_password


def test_register_user(client: TestClient, db_session: Session):
    # 1. Successful registration
    response = client.post(
        "/api/auth/register",
        json={"email": "register@test.com", "password": "securepassword"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "register@test.com"
    assert "id" in data

    # Verify db record password is hashed
    user = db_session.query(User).filter(User.email == "register@test.com").first()
    assert user is not None
    assert user.hashed_password != "securepassword"
    assert verify_password("securepassword", user.hashed_password) is True

    # 2. Reject duplicate email registration
    dup_response = client.post(
        "/api/auth/register",
        json={"email": "register@test.com", "password": "otherpassword"},
    )
    assert dup_response.status_code == 400
    assert "exists" in dup_response.json()["detail"]


def test_login_user(client: TestClient, db_session: Session):
    # 1. Register a user
    client.post(
        "/api/auth/register",
        json={"email": "login@test.com", "password": "mysecretpassword"},
    )

    # 2. Successful login
    login_response = client.post(
        "/api/auth/login",
        data={"username": "login@test.com", "password": "mysecretpassword"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert token_data["token_type"] == "bearer"
    assert "access_token" in token_data

    # 3. Failed login: wrong password
    bad_pwd_response = client.post(
        "/api/auth/login",
        data={"username": "login@test.com", "password": "wrongpassword"},
    )
    assert bad_pwd_response.status_code == 400
    assert "Incorrect" in bad_pwd_response.json()["detail"]

    # 4. Failed login: non-existent email
    bad_email_response = client.post(
        "/api/auth/login",
        data={"username": "fake@test.com", "password": "password123"},
    )
    assert bad_email_response.status_code == 400
    assert "Incorrect" in bad_email_response.json()["detail"]


def test_read_profile(client: TestClient):
    # 1. Register and login to get token
    client.post(
        "/api/auth/register",
        json={"email": "profile@test.com", "password": "mypassword123"},
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "profile@test.com", "password": "mypassword123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Successful profile access
    me_response = client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    profile = me_response.json()
    assert profile["email"] == "profile@test.com"

    # 3. Unauthorized: No token
    no_token_response = client.get("/api/auth/me")
    assert no_token_response.status_code == 401

    # 4. Unauthorized: Invalid token
    bad_token_headers = {"Authorization": "Bearer badtokenvalue123"}
    bad_token_response = client.get("/api/auth/me", headers=bad_token_headers)
    assert bad_token_response.status_code == 401
