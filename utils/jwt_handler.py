from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt

from app.core.config import settings


class JWTHandler:
    """Utility class for encoding and decoding JWT tokens."""

    @staticmethod
    def create_access_token(subject: Dict[str, Any]) -> str:
        expire_minutes = settings.access_token_expire_minutes
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
        payload = {"exp": expire, "iat": datetime.now(timezone.utc), **subject}
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
        return token

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
