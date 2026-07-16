"""Backward-compatible re-exports from the new database layer."""
from backend.database.base import Base
from backend.database.session import engine, SessionLocal, get_db
from backend.database.models import UserModel, DiagnosticModel, AuditLogModel, ModelModel


def init_db():
    Base.metadata.create_all(bind=engine)
