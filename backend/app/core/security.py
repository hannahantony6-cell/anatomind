import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from ..config import get_settings

_hasher = PasswordHasher()   # Argon2id with library-default (OWASP-aligned) parameters
_DUMMY_HASH = _hasher.hash("anatomind-dummy-password")  # equalises timing for unknown emails


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: int) -> tuple[str, str, datetime]:
    s = get_settings()
    jti = uuid.uuid4().hex
    exp = datetime.now(timezone.utc) + timedelta(minutes=s.access_token_minutes)
    token = jwt.encode({"sub": str(user_id), "jti": jti, "exp": exp}, s.secret_key, algorithm="HS256")
    return token, jti, exp


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, get_settings().secret_key, algorithms=["HS256"],
                          options={"require": ["exp", "sub", "jti"]})
    except jwt.PyJWTError:
        return None
