from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from ..config import get_settings
from ..core.deps import get_current_user, get_token_claims
from ..core.security import create_access_token
from ..database import get_db
from ..models import User
from ..schemas.auth import LoginRequest, LoginResponse, SignupRequest, UserOut
from ..services import authentication

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=201)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    return authentication.signup(db, body.full_name, body.email, body.password)


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "-"
    user = authentication.authenticate(db, body.email, body.password, ip)
    s = get_settings()
    token, _, _ = create_access_token(user.id)
    response.set_cookie(s.cookie_name, token, max_age=s.access_token_minutes * 60, httponly=True,
                        secure=s.cookie_secure, samesite="lax", path="/")
    return LoginResponse(user=UserOut.model_validate(user), expires_in_seconds=s.access_token_minutes * 60)


@router.post("/logout", status_code=204)
def logout(response: Response, claims: dict = Depends(get_token_claims), db: Session = Depends(get_db)):
    authentication.revoke_token(db, claims["jti"], datetime.fromtimestamp(claims["exp"], timezone.utc))
    response.delete_cookie(get_settings().cookie_name, path="/")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
