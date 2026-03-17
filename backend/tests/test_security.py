import pytest

pytest.importorskip('jose')
pytest.importorskip('passlib')

from app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_verify() -> None:
    password = 'StrongPass123'
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_jwt_encode_decode() -> None:
    token = create_access_token(subject='1', role='admin', expires_minutes=5)
    payload = decode_access_token(token)
    assert payload['sub'] == '1'
    assert payload['role'] == 'admin'
