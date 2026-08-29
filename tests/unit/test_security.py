import uuid
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hashing_and_verification():
    plain_password = "SuperSecretPassword123!"
    hashed = hash_password(plain_password)

    assert hashed != plain_password
    assert verify_password(plain_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_generation_and_decoding():
    user_id = uuid.uuid4()
    token = create_access_token(user_id=user_id)

    assert isinstance(token, str)
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] - payload["iat"] == 3600
