from datetime import datetime, timedelta, UTC
from uuid import UUID
from app.core.config import settings


import jwt


SECRET_KEY = settings.secret_key
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.token_expiry


def create_access_token(user_id: UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])