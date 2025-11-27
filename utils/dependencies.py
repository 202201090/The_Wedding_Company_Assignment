from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.utils.jwt_handler import JWTHandler

security_scheme = HTTPBearer(auto_error=False)


def get_current_admin(credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme)) -> dict:
    """Extract and validate JWT token, returning admin_email and organization_name."""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization header")

    token = credentials.credentials

    try:
        payload = JWTHandler.decode_token(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc

    if "admin_email" not in payload or "organization_name" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing required claims (admin_email, organization_name)"
        )

    return payload
