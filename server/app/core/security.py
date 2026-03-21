from __future__ import annotations
from dataclasses import dataclass

from datetime import datetime, timedelta, UTC
from hashlib import sha256
import secrets
from pwdlib import PasswordHash

from app.core.config import settings


@dataclass(frozen=True, slots=True)
class SessionSecrets:
    session_token: str
    session_token_hash: str
    csrf_token: str
    csrf_token_hash: str
    expires_at: datetime
    
class Security:
    PASSWORD_HASHER = PasswordHash.recommended()
    
    SESSION_TOKEN_NBYTES = 48
    CSRF_TOKEN_NBYTES = 32
    MIN_TOKEN_NBYTES = 16
    MAX_TOKEN_NBYTES = 128
    SHA256_HEX_LEN = 64
    MAX_SESSION_MINUTES = 60 * 24 * 30
    
    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
    
    
    @classmethod
    def hash_password(cls, password: str) -> str:
        return cls.PASSWORD_HASHER.hash(password)
    
    @classmethod
    def verify_password(cls, password: str, hashed_password: str) -> bool:
        return cls.PASSWORD_HASHER.verify(password, hashed_password)
    
    @classmethod 
    def verify_and_maybe_rehash(cls, password: str, hashed_password: str) -> tuple[bool, str | None]:
        return cls.PASSWORD_HASHER.verify_and_update(password, hashed_password)
    
    
    @classmethod
    def _validate_token_nbytes(cls, nbytes: int) -> int:
        if not isinstance(nbytes, int):
            raise TypeError("Token size must be an int")
        if nbytes < cls.MIN_TOKEN_NBYTES or nbytes > cls.MAX_TOKEN_NBYTES:
            raise ValueError(
                f"Token size must be between {cls.MIN_TOKEN_NBYTES} and {cls.MAX_TOKEN_NBYTES} bytes"
            )
        return nbytes
    
    @classmethod
    def generate_token(cls, nbytes: int = SESSION_TOKEN_NBYTES) -> str:
        size = cls._validate_token_nbytes(nbytes)
        return secrets.token_urlsafe(size)
    
    @staticmethod
    def hash_token(raw_token: str) -> str:
        if not isinstance(raw_token, str):
            raise TypeError("Token must be a string")
        if not raw_token:
            raise ValueError("Token cannot be empty")
        return sha256(raw_token.encode("utf-8")).hexdigest()
    
    @classmethod
    def verify_csrf(cls, raw_csrf_token: str, csrf_token_hash: str) -> bool:
        if not isinstance(raw_csrf_token, str) or not isinstance(csrf_token_hash, str):
            return False
        if not raw_csrf_token or len(csrf_token_hash) != cls.SHA256_HEX_LEN:
            return False
       
        try:
            computed = cls.hash_token(raw_csrf_token)
            expected = csrf_token_hash.lower()
            return secrets.compare_digest(computed, expected)
        except Exception:
            return False
    
    @classmethod
    def session_expires_at(cls) -> datetime:
        minutes = int(settings.token_expiry)
        if minutes <= 0 or minutes > cls.MAX_SESSION_MINUTES:
            raise ValueError("token_expiry must be a positive number of minutes within safety limits")
        return cls._utcnow() + timedelta(minutes=minutes)
    
    @classmethod
    def is_expired(cls, expires_at: datetime, now: datetime | None =None) -> bool:
        if expires_at.tzinfo is None:
            raise ValueError("expires_at must be time-zone aware")
        current = now or cls._utcnow()
        if current.tzinfo is None:
            raise ValueError("now must be time-zone aware")
        return expires_at <= current
    
    @classmethod
    def issue_session_secrets(cls) -> SessionSecrets:
        session_token = cls.generate_token(cls.SESSION_TOKEN_NBYTES)
        csrf_token = cls.generate_token(cls.CSRF_TOKEN_NBYTES)
        return SessionSecrets(
            session_token=session_token,
            session_token_hash=cls.hash_token(session_token),
            csrf_token=csrf_token,
            csrf_token_hash=cls.hash_token(csrf_token),
            expires_at=cls.session_expires_at(),
        )
    
    