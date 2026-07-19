import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from backend.core.security import get_current_user, TokenData, hash_password
from backend.schemas.auth import UserResponse, UserUpdate
from backend.schemas import UserCreate
from backend.database.database import get_db, UserModel

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _require_admin(current_user: TokenData = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return current_user


@router.get("", response_model=list[UserResponse])
def list_users(
    admin: TokenData = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(UserModel).all()
    return [
        UserResponse(
            id=u.id,
            username=u.username,
            name=u.name,
            role=u.role,
            active=bool(u.active),
        )
        for u in users
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    data: UserCreate,
    admin: TokenData = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    existing = db.query(UserModel).filter(UserModel.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    user = UserModel(
        username=data.username,
        name=data.name,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        username=user.username,
        name=user.name,
        role=user.role,
        active=bool(user.active),
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    admin: TokenData = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UserResponse(
        id=user.id,
        username=user.username,
        name=user.name,
        role=user.role,
        active=bool(user.active),
    )


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updates: UserUpdate,
    admin: TokenData = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    update_data = updates.model_dump(exclude_unset=True)
    if "role" in update_data and update_data["role"] not in ("admin", "client"):
        raise HTTPException(status_code=400, detail="Rol inválido")

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        username=user.username,
        name=user.name,
        role=user.role,
        active=bool(user.active),
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    admin: TokenData = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="No se puede eliminar el administrador principal")
    db.delete(user)
    db.commit()
