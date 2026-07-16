from typing import Optional

from sqlalchemy.orm import Session

from backend.database.models import UserModel
from backend.core.security import hash_password


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.username == username).first()

    def create(self, name: str, username: str, password: str, role: str = "client") -> UserModel:
        user = UserModel(
            name=name,
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_last_login(self, user_id: int):
        from datetime import datetime, timezone
        self.db.query(UserModel).filter(UserModel.id == user_id).update(
            {"last_login": datetime.now(timezone.utc)}
        )
        self.db.commit()

    def list_all(self) -> list[UserModel]:
        return self.db.query(UserModel).all()

    def count(self) -> int:
        return self.db.query(UserModel).count()
