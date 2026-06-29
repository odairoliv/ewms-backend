from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CustomField


class CustomFieldRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, custom_id: int) -> CustomField | None:
        return self.db.get(CustomField, custom_id)

    def get_by_chave(self, empresa_id: str, id_objeto: str, nome_coluna: str) -> CustomField | None:
        stmt = select(CustomField).where(
            CustomField.empresa_id == empresa_id,
            CustomField.id_objeto == id_objeto,
            CustomField.nome_coluna == nome_coluna,
        )
        return self.db.scalar(stmt)

    def list_by_empresa_objeto(self, empresa_id: str, id_objeto: str) -> list[CustomField]:
        stmt = (
            select(CustomField)
            .where(CustomField.empresa_id == empresa_id, CustomField.id_objeto == id_objeto)
            .order_by(CustomField.ordem)
        )
        return list(self.db.scalars(stmt))

    def list_by_empresa(self, empresa_id: str) -> list[CustomField]:
        stmt = select(CustomField).where(CustomField.empresa_id == empresa_id).order_by(
            CustomField.id_objeto, CustomField.ordem
        )
        return list(self.db.scalars(stmt))

    def create(self, campo: CustomField) -> CustomField:
        self.db.add(campo)
        self.db.commit()
        self.db.refresh(campo)
        return campo

    def update(self, campo: CustomField) -> CustomField:
        self.db.commit()
        self.db.refresh(campo)
        return campo

    def delete(self, campo: CustomField) -> None:
        self.db.delete(campo)
        self.db.commit()
