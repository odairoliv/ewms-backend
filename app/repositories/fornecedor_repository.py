from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Fornecedor

# `empresa` é lido em FornecedorService._enrich — eager load evita 1 query extra por linha.
_EAGER = (selectinload(Fornecedor.empresa),)


class FornecedorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, fornecedor_id: str) -> Fornecedor | None:
        return self.db.scalar(select(Fornecedor).where(Fornecedor.id == fornecedor_id).options(*_EAGER))

    def list_all(self) -> list[Fornecedor]:
        return list(self.db.scalars(select(Fornecedor).options(*_EAGER)))

    def list_by_empresa(self, empresa_id: str) -> list[Fornecedor]:
        stmt = select(Fornecedor).where(Fornecedor.empresa_id == empresa_id).options(*_EAGER)
        return list(self.db.scalars(stmt))

    def count(self) -> int:
        return self.db.query(Fornecedor).count()

    def create(self, fornecedor: Fornecedor) -> Fornecedor:
        self.db.add(fornecedor)
        self.db.commit()
        self.db.refresh(fornecedor)
        return fornecedor

    def update(self, fornecedor: Fornecedor) -> Fornecedor:
        self.db.commit()
        self.db.refresh(fornecedor)
        return fornecedor

    def delete(self, fornecedor: Fornecedor) -> None:
        self.db.delete(fornecedor)
        self.db.commit()
