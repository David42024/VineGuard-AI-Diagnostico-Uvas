from sqlalchemy.orm import Session

from backend.database.models import AuditLogModel


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, user_id: int, action: str, detail: str = ""):
        entry = AuditLogModel(user_id=user_id, action=action, detail=detail)
        self.db.add(entry)
        self.db.commit()

    def list_recent(self, limit: int = 100) -> list[AuditLogModel]:
        return (
            self.db.query(AuditLogModel)
            .order_by(AuditLogModel.timestamp.desc())
            .limit(limit)
            .all()
        )
