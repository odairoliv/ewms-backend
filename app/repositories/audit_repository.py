from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, audit_id: str) -> AuditLog | None:
        return self.db.get(AuditLog, audit_id)

    def list_all(self) -> list[AuditLog]:
        return list(self.db.scalars(select(AuditLog).order_by(AuditLog.data_hora.desc())))

    def list_by_empresa(self, empresa_id: str) -> list[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.empresa_id == empresa_id)
            .order_by(AuditLog.data_hora.desc())
        )
        return list(self.db.scalars(stmt))

    def list_all_filtrado(self, empresa_id: str | None) -> list[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.data_hora.desc())
        if empresa_id:
            stmt = stmt.where(AuditLog.empresa_id == empresa_id)
        return list(self.db.scalars(stmt))

    def count(self) -> int:
        return self.db.query(AuditLog).count()

    def create(self, log: AuditLog) -> AuditLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def update(self, log: AuditLog) -> AuditLog:
        self.db.commit()
        self.db.refresh(log)
        return log
