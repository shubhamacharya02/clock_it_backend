import uuid
import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import jwt
from app.core.config import settings

def hash_password(password: str) -> str:
    """Hashes password using bcrypt with 72-byte truncation safety."""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored bcrypt hash."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(pwd_bytes, hashed_bytes)

def create_access_token(user_id: uuid.UUID) -> str:
    """Generates signed 1-hour JWT access token (sub, iat, exp)."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp())
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and verifies JWT access token signature and expiry."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
