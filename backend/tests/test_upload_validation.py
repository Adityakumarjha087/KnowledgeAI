from fastapi.testclient import TestClient

from app.core.config import settings


def _auth_headers(client: TestClient, email: str) -> dict:
    client.post("/api/auth/register", json={"email": email, "password": "mysecretpassword"})
    token = client.post(
        "/api/auth/login", data={"username": email, "password": "mysecretpassword"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_requires_authentication(client: TestClient):
    response = client.post(
        "/api/documents/upload", files={"file": ("notes.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 401


def test_upload_rejects_unsupported_extension(client: TestClient):
    headers = _auth_headers(client, "upload-ext@test.com")
    response = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("payload.exe", b"MZ", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file format '.exe'" in response.json()["detail"]


def test_upload_rejects_file_without_extension(client: TestClient):
    headers = _auth_headers(client, "upload-noext@test.com")
    response = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("README", b"plain", "text/plain")},
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_upload_rejects_oversized_file(client: TestClient, monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)
    headers = _auth_headers(client, "upload-big@test.com")
    response = client.post(
        "/api/documents/upload",
        headers=headers,
        files={"file": ("big.txt", b"x" * 2048, "text/plain")},
    )
    assert response.status_code == 400
    assert "exceeds maximum limit" in response.json()["detail"]
