import sys
from pathlib import Path
from datetime import timedelta

from fastapi import APIRouter, HTTPException, status, Depends, Response, Request
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.security import (
    create_access_token,
    verify_token,
    get_current_user,
    TokenData,
)
from backend.schemas.auth import LoginRequest, TokenResponse, UserInfo
from backend.database.session import get_db
from backend.repositories.user_repository import UserRepository
from backend.repositories.audit_repository import AuditRepository

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.repository import authenticate

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

COOKIE_MAX_AGE = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def _set_token_cookie(response: Response, token: str):
    response.set_cookie(
        key="token",
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
        path="/",
    )


def _clear_token_cookie(response: Response):
    response.set_cookie(
        key="token",
        value="",
        max_age=0,
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.cookie_secure,
        path="/",
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, response: Response):
    user = authenticate(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    _set_token_cookie(response, access_token)

    return TokenResponse(
        user=UserInfo(
            id=user["id"],
            username=user["username"],
            name=user["name"],
            role=user["role"],
            active=bool(user["active"]),
        ),
    )


@router.post("/logout")
def logout(current_user: TokenData = Depends(get_current_user), response: Response = None):
    if response is not None:
        _clear_token_cookie(response)
    return {"message": "Sesión cerrada exitosamente"}


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
    response: Response = None,
):
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(current_user.sub)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    new_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    _set_token_cookie(response, new_token)

    return TokenResponse(
        user=UserInfo(
            id=user.id,
            username=user.username,
            name=user.name,
            role=user.role,
            active=bool(user.active),
        ),
    )


@router.get("/me", response_model=UserInfo)
def me(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    user_repo = UserRepository(db)
    user = user_repo.get_by_username(current_user.sub)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UserInfo(
        id=user.id,
        username=user.username,
        name=user.name,
        role=user.role,
        active=bool(user.active),
    )
