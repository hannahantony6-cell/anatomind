import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..core.errors import AppError
from ..core.security import hash_password, verify_password
from ..models import RevokedToken, User

_FAIL_WINDOW, _FAIL_LIMIT = 300, 8
_failures: dict[str, deque] = defaultdict(deque)   # in-memory brute-force throttle (per process)


def _throttle_key(email: str, ip: str) -> str:
    return f"{email}|{ip}"


def signup(db: Session, full_name: str, email: str, password: str) -> User:
    if db.scalar(select(User).where(User.email == email)):
        raise AppError(409, "email_taken", "An account with this email already exists.")
    user = User(full_name=full_name, email=email, password_hash=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:           # race: two signups with the same email
        db.rollback()
        raise AppError(409, "email_taken", "An account with this email already exists.")
    return user


def authenticate(db: Session, email: str, password: str, ip: str = "-") -> User:
    key = _throttle_key(email, ip)
    q = _failures[key]
    now = time.monotonic()
    while q and now - q[0] > _FAIL_WINDOW:
        q.popleft()
    if len(q) >= _FAIL_LIMIT:
        raise AppError(429, "too_many_attempts", "Too many failed logins. Please wait a few minutes and try again.")
    user = db.scalar(select(User).where(User.email == email))
    if not verify_password(password, user.password_hash if user else None):
        q.append(now)
        raise AppError(401, "invalid_credentials", "Incorrect email or password.")
    q.clear()
    return user


def revoke_token(db: Session, jti: str, expires_at: datetime) -> None:
    if not db.get(RevokedToken, jti):
        db.add(RevokedToken(jti=jti, expires_at=expires_at))
    # opportunistic cleanup of expired revocations
    db.query(RevokedToken).filter(RevokedToken.expires_at < datetime.now(timezone.utc)).delete()
    db.commit()


def reset_throttle() -> None:
    _failures.clear()
