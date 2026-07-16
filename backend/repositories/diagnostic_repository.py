import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from backend.database.models import DiagnosticModel, UserModel


class DiagnosticRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, diag_id: int, include_deleted: bool = False) -> Optional[DiagnosticModel]:
        q = self.db.query(DiagnosticModel).filter(DiagnosticModel.id == diag_id)
        if not include_deleted:
            q = q.filter(DiagnosticModel.deleted_at.is_(None))
        return q.first()

    def create(
        self,
        user_id: int,
        filename: str,
        result: str,
        confidence: float,
        model_used: str,
        probabilities: dict,
        inference_time_ms: float,
        image_path: Optional[str] = None,
        analysis_type: str = "single",
        is_demo: bool = False,
    ) -> int:
        diag = DiagnosticModel(
            user_id=user_id,
            filename=filename,
            image_path=image_path,
            result=result,
            confidence=confidence,
            model_used=model_used,
            probabilities=json.dumps(probabilities) if probabilities else None,
            inference_time_ms=inference_time_ms,
            analysis_type=analysis_type,
            status="completed",
            is_demo=1 if is_demo else 0,
        )
        self.db.add(diag)
        self.db.commit()
        self.db.refresh(diag)
        return diag.id

    def list_by_user(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        class_code: Optional[str] = None,
        model_key: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        is_demo: Optional[bool] = None,
    ) -> list[dict]:
        q = (
            self.db.query(
                DiagnosticModel.id,
                DiagnosticModel.timestamp,
                DiagnosticModel.filename,
                DiagnosticModel.image_path,
                DiagnosticModel.result,
                DiagnosticModel.confidence,
                DiagnosticModel.model_used,
                DiagnosticModel.inference_time_ms,
                DiagnosticModel.status,
                DiagnosticModel.is_demo,
            )
            .filter(
                DiagnosticModel.user_id == user_id,
                DiagnosticModel.deleted_at.is_(None),
            )
        )
        q = self._apply_filters(q, search, class_code, model_key, date_from, date_to, is_demo)
        rows = (
            q.order_by(DiagnosticModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [dict(r._mapping) for r in rows]

    def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
        class_code: Optional[str] = None,
        model_key: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        is_demo: Optional[bool] = None,
    ) -> list[dict]:
        q = (
            self.db.query(
                DiagnosticModel.id,
                DiagnosticModel.timestamp,
                DiagnosticModel.filename,
                DiagnosticModel.image_path,
                DiagnosticModel.result,
                DiagnosticModel.confidence,
                DiagnosticModel.model_used,
                DiagnosticModel.inference_time_ms,
                DiagnosticModel.status,
                DiagnosticModel.is_demo,
                UserModel.name.label("user_name"),
                UserModel.username,
            )
            .join(UserModel, DiagnosticModel.user_id == UserModel.id)
            .filter(DiagnosticModel.deleted_at.is_(None))
        )
        q = self._apply_filters(q, search, class_code, model_key, date_from, date_to, is_demo)
        rows = (
            q.order_by(DiagnosticModel.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [dict(r._mapping) for r in rows]

    def _apply_filters(self, query, search, class_code, model_key, date_from, date_to, is_demo):
        if search:
            like = f"%{search}%"
            query = query.filter(
                or_(
                    DiagnosticModel.filename.ilike(like),
                    DiagnosticModel.result.ilike(like),
                )
            )
        if class_code:
            query = query.filter(DiagnosticModel.result == class_code)
        if model_key:
            query = query.filter(DiagnosticModel.model_used.ilike(f"%{model_key}%"))
        if date_from:
            try:
                dt = datetime.fromisoformat(date_from)
                query = query.filter(DiagnosticModel.timestamp >= dt)
            except (ValueError, TypeError):
                pass
        if date_to:
            try:
                dt = datetime.fromisoformat(date_to)
                query = query.filter(DiagnosticModel.timestamp <= dt)
            except (ValueError, TypeError):
                pass
        if is_demo is not None:
            query = query.filter(DiagnosticModel.is_demo == (1 if is_demo else 0))
        return query

    def soft_delete(self, diag_id: int, user_id: Optional[int] = None, deleted_by: Optional[int] = None):
        q = self.db.query(DiagnosticModel).filter(
            DiagnosticModel.id == diag_id,
            DiagnosticModel.deleted_at.is_(None),
        )
        if user_id is not None:
            q = q.filter(DiagnosticModel.user_id == user_id)
        q.update({
            "deleted_at": datetime.now(timezone.utc),
            "deleted_by": deleted_by,
            "status": "deleted",
        })
        self.db.commit()

    def count(self, exclude_demo: bool = False) -> int:
        q = self.db.query(DiagnosticModel).filter(DiagnosticModel.deleted_at.is_(None))
        if exclude_demo:
            q = q.filter(DiagnosticModel.is_demo == 0)
        return q.count()

    def count_by_user(self, user_id: int, exclude_demo: bool = False) -> int:
        q = self.db.query(DiagnosticModel).filter(
            DiagnosticModel.user_id == user_id,
            DiagnosticModel.deleted_at.is_(None),
        )
        if exclude_demo:
            q = q.filter(DiagnosticModel.is_demo == 0)
        return q.count()

    def count_filtered(
        self,
        user_id: Optional[int] = None,
        search: Optional[str] = None,
        class_code: Optional[str] = None,
        model_key: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        is_demo: Optional[bool] = None,
    ) -> int:
        q = self.db.query(DiagnosticModel).filter(DiagnosticModel.deleted_at.is_(None))
        if user_id is not None:
            q = q.filter(DiagnosticModel.user_id == user_id)
        q = self._apply_filters(q, search, class_code, model_key, date_from, date_to, is_demo)
        return q.count()

    def count_today(self) -> int:
        today = datetime.now(timezone.utc).date()
        return (
            self.db.query(DiagnosticModel)
            .filter(
                func.date(DiagnosticModel.timestamp) == today,
                DiagnosticModel.deleted_at.is_(None),
            )
            .count()
        )

    def count_healthy(self, exclude_demo: bool = False) -> int:
        q = self.db.query(DiagnosticModel).filter(
            DiagnosticModel.result == "Healthy",
            DiagnosticModel.deleted_at.is_(None),
        )
        if exclude_demo:
            q = q.filter(DiagnosticModel.is_demo == 0)
        return q.count()

    def get_disease_distribution(self, exclude_demo: bool = False) -> dict:
        q = (
            self.db.query(DiagnosticModel.result, func.count().label("c"))
            .filter(DiagnosticModel.deleted_at.is_(None))
        )
        if exclude_demo:
            q = q.filter(DiagnosticModel.is_demo == 0)
        rows = (
            q.group_by(DiagnosticModel.result)
            .order_by(func.count().desc())
            .all()
        )
        return {r.result: r.c for r in rows}

    def get_diagnostics_by_date(self, days: int = 30, exclude_demo: bool = False) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        q = (
            self.db.query(func.date(DiagnosticModel.timestamp).label("date"), func.count().label("count"))
            .filter(DiagnosticModel.timestamp >= since, DiagnosticModel.deleted_at.is_(None))
        )
        if exclude_demo:
            q = q.filter(DiagnosticModel.is_demo == 0)
        rows = (
            q.group_by(func.date(DiagnosticModel.timestamp))
            .order_by(func.date(DiagnosticModel.timestamp))
            .all()
        )
        return [{"date": r.date, "count": r.count} for r in rows]

    def get_user_stats(self, user_id: int) -> dict:
        total = self.count_by_user(user_id)
        healthy = (
            self.db.query(DiagnosticModel)
            .filter(
                DiagnosticModel.user_id == user_id,
                DiagnosticModel.result == "Healthy",
                DiagnosticModel.deleted_at.is_(None),
            )
            .count()
        )
        today = (
            self.db.query(DiagnosticModel)
            .filter(
                DiagnosticModel.user_id == user_id,
                func.date(DiagnosticModel.timestamp) == datetime.now(timezone.utc).date(),
                DiagnosticModel.deleted_at.is_(None),
            )
            .count()
        )
        last = (
            self.db.query(DiagnosticModel.result, DiagnosticModel.confidence, DiagnosticModel.timestamp)
            .filter(DiagnosticModel.user_id == user_id, DiagnosticModel.deleted_at.is_(None))
            .order_by(DiagnosticModel.timestamp.desc())
            .first()
        )
        return {
            "total": total,
            "healthy": healthy,
            "diseased": total - healthy,
            "today": today,
            "last_diagnosis": {"result": last.result, "confidence": last.confidence, "timestamp": last.timestamp.isoformat() if last.timestamp else None} if last else None,
        }

    def get_admin_stats(self, exclude_demo: bool = True) -> dict:
        total = self.count(exclude_demo=exclude_demo)
        today = self.count_today()
        healthy = self.count_healthy(exclude_demo=exclude_demo)
        from backend.repositories.user_repository import UserRepository
        users = UserRepository(self.db).count()
        return {
            "total_diagnostics": total,
            "today_diagnostics": today,
            "healthy_pct": (healthy / total * 100) if total else 0,
            "diseased_pct": ((total - healthy) / total * 100) if total else 0,
            "total_users": users,
        }
