from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Empresa


class EmpresaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, empresa_id: str) -> Empresa | None:
        return self.db.get(Empresa, empresa_id)

    def list_all(self) -> list[Empresa]:
        return list(self.db.scalars(select(Empresa)))

    def count(self) -> int:
        return self.db.query(Empresa).count()

    def create(self, empresa: Empresa) -> Empresa:
        self.db.add(empresa)
        self.db.commit()
        self.db.refresh(empresa)
        return empresa

    def update(self, empresa: Empresa) -> Empresa:
        self.db.commit()
        self.db.refresh(empresa)
        return empresa
