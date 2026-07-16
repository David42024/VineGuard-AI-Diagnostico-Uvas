from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func

from backend.database.base import Base


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="client")
    active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)


class DiagnosticModel(Base):
    __tablename__ = "diagnostics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    filename = Column(String, nullable=True)
    image_path = Column(String, nullable=True)
    result = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    model_used = Column(String, nullable=True)
    probabilities = Column(Text, nullable=True)
    inference_time_ms = Column(Float, nullable=True)
    analysis_type = Column(String, default="single")
    status = Column(String, default="completed")
    is_demo = Column(Integer, default=0)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id"), nullable=True)


class AuditLogModel(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    detail = Column(Text, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())


class ModelModel(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    type = Column(String, nullable=False)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    status = Column(String, default="available")
    created_at = Column(DateTime, server_default=func.now())
