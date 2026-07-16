from typing import Optional

from sqlalchemy.orm import Session

from backend.database.models import ModelModel


class ModelRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self) -> list[ModelModel]:
        return self.db.query(ModelModel).order_by(ModelModel.id).all()

    def get_by_name(self, name: str) -> Optional[ModelModel]:
        return self.db.query(ModelModel).filter(ModelModel.name == name).first()

    def count(self) -> int:
        return self.db.query(ModelModel).count()

    def upsert(self, name: str, type_: str, accuracy: float = None, precision: float = None,
               recall: float = None, f1_score: float = None, status: str = "available") -> ModelModel:
        existing = self.get_by_name(name)
        if existing:
            existing.accuracy = accuracy
            existing.precision = precision
            existing.recall = recall
            existing.f1_score = f1_score
            existing.status = status
        else:
            existing = ModelModel(
                name=name, type=type_, accuracy=accuracy,
                precision=precision, recall=recall, f1_score=f1_score, status=status,
            )
            self.db.add(existing)
        self.db.commit()
        self.db.refresh(existing)
        return existing
