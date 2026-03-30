import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.utils.errors import AppError

security = HTTPBearer(auto_error=False)


async def get_jwt_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    settings = get_settings()

    if settings.allow_anonymous_requests:
        return {"sub": "anonymous"}

    if not credentials:
        raise AppError(code="UNAUTHORIZED", message="Missing bearer token", status_code=401)

    token = credentials.credentials
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise AppError(code="UNAUTHORIZED", message="Invalid token", status_code=401) from exc
