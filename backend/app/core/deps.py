from datetime import datetime, timezone

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import RevokedToken, User
from .errors import AppError
from .security import decode_token


def _extract_token(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return request.cookies.get(get_settings().cookie_name)


def get_token_claims(request: Request) -> dict:
    token = _extract_token(request)
    claims = decode_token(token) if token else None
    if not claims:
        raise AppError(401, "not_authenticated", "Please log in to continue.")
    return claims


def get_current_user(claims: dict = Depends(get_token_claims), db: Session = Depends(get_db)) -> User:
    """The ONLY source of user identity. Client-supplied user ids are never trusted."""
    if db.get(RevokedToken, claims["jti"]):
        raise AppError(401, "session_revoked", "Your session has ended. Please log in again.")
    user = db.get(User, int(claims["sub"]))
    if not user:
        raise AppError(401, "not_authenticated", "Please log in to continue.")
    return user
