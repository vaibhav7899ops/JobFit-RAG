from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_hash_password_is_not_plaintext():
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"


def test_verify_password_correct():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("mysecret")
    assert verify_password("wrongpassword", hashed) is False


def test_access_token_round_trip():
    token = create_access_token({"sub": "user@example.com"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user@example.com"


def test_decode_tampered_token_returns_none():
    token = create_access_token({"sub": "user@example.com"})
    assert decode_access_token(token + "tampered") is None


def test_decode_garbage_token_returns_none():
    assert decode_access_token("not-a-real-token") is None
