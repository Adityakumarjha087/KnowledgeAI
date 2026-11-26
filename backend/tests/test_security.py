from datetime import timedelta

import pytest
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password


def test_password_hash_roundtrip():
    hashed = get_password_hash("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("wrong-pass", hashed)


def test_password_hashes_are_salted():
    assert get_password_hash("same-password") != get_password_hash("same-password")


def test_verify_password_rejects_malformed_hash():
    # A corrupt or non-bcrypt stored value must fail closed, not raise.
    assert verify_password("anything", "not-a-bcrypt-hash") is False


def test_access_token_carries_subject_and_expiry():
    token = create_access_token(42)
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == "42"
    assert "exp" in payload


def test_expired_access_token_is_rejected():
    token = create_access_token("user@example.com", expires_delta=timedelta(seconds=-5))
    with pytest.raises(JWTError):
        jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def test_access_token_with_wrong_secret_is_rejected():
    token = create_access_token("user@example.com")
    with pytest.raises(JWTError):
        jwt.decode(token, "a-different-secret-key-of-32-chars!!", algorithms=[settings.JWT_ALGORITHM])
