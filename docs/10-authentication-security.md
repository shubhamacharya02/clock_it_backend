# Document 10: Authentication & Security Architecture

## 1. Authentication Scheme
The application uses standard **JWT (JSON Web Token)** bearer authentication via FastAPI.

### Token Specs
- **Algorithm**: `HS256`
- **Expiration Lifetime**: `1 hour` (`3,600 seconds`) (`JWT_EXPIRATION_SECONDS=3600`)
- **Token Payload Claims**:
  ```json
  {
    "sub": "123e4567-e89b-12d3-a456-426614174000",
    "iat": 1787965200,
    "exp": 1787968800
  }
  ```
- **Header Format**: `Authorization: Bearer <token>`

---

## 2. Password Security & Hashing
Passwords are stored as salted hashes using `passlib` with `bcrypt`:

```python
# app/core/security.py
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: uuid.UUID | str) -> str:
    now = datetime.utcnow()
    expire = now + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS) # 3600 seconds (1 hour)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": expire
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
```

---

## 3. Security Dependencies & Resource Authorization

### FastAPI Authentication Dependency & UUID Validation
The authentication dependency decodes the JWT, validates token expiration and signature, and strictly validates that the `sub` claim is a valid UUID format before querying PostgreSQL. Malformed or invalid `sub` claims raise an `HTTP 401 Unauthorized` exception.

```python
# app/core/dependencies.py
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from sqlmodel.ext.asyncio.session import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

security_bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    session: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        
        # Validate sub claim as a valid UUID before querying database
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
    
    user = await session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or missing")
    return user
```

### Resource Ownership & Canonical 404 Isolation
All endpoints operating on user-owned resources (`recipes`, `recipe_ingredients`, `carts`, `cart_items`, `orders`, `order_items`) MUST enforce strict resource ownership.

If an authenticated user attempts to access or modify a resource belonging to another user, the system MUST return `HTTP 404 Not Found` rather than `HTTP 403 Forbidden` to hide resource existence and prevent ID enumeration:

```python
# Canonical Resource Ownership Validation Example
if resource.user_id != current_user.id:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found"
    )
```

> [!NOTE]
> Public catalog resources (`products`, `product_variants`) are non-user-owned and remain accessible based on standard public/authenticated catalog endpoint rules.

---

## 4. General Application Security

1. **SQL Injection Prevention**: All database access utilizes `SQLModel` / `SQLAlchemy` ORM parameterized statements. Raw string interpolation in queries is strictly prohibited.
2. **File Upload Security**: Image processing endpoints validate MIME types against an explicit allowlist (`image/jpeg`, `image/png`, `image/webp`) and enforce a strict 10MB payload body size limit before reading stream data.
3. **Secrets Management**: No API keys or credentials exist in source code. All configuration values are loaded via `pydantic-settings` from environment variables (`.env`).
4. **CORS Policy**: Configured in `main.py` using `CORSMiddleware` with explicit origin controls.
