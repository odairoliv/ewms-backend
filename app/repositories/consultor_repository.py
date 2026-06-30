from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Consultor, Fornecedor

# Relacionamentos sempre lidos em _enrich (ConsultorService) — carregados de uma vez via
# selectinload (3 queries extras no total, fixas) em vez de lazy-load por linha (N+1).
_EAGER = (
    selectinload(Consultor.usuario),
    selectinload(Consultor.fornecedor),
    selectinload(Consultor.lideranca),
)


class ConsultorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, consultor_id: str) -> Consultor | None:
        return self.db.scalar(
            select(Consultor).where(Consultor.id == consultor_id).options(*_EAGER)
        )

    def get_by_usuario_id(self, usuario_id: int) -> Consultor | None:
        return self.db.scalar(
            select(Consultor).where(Consultor.usuario_id == usuario_id, Consultor.ativo.is_(True))
        )

    def list_all(self) -> list[Consultor]:
        stmt = select(Consultor).where(Consultor.ativo.is_(True)).options(*_EAGER)
        return list(self.db.scalars(stmt))

    def list_by_empresa(self, empresa_id: str) -> list[Consultor]:
        stmt = (
            select(Consultor)
            .join(Fornecedor, Fornecedor.id == Consultor.id_fornecedor)
            .where(Fornecedor.empresa_id == empresa_id, Consultor.ativo.is_(True))
            .options(*_EAGER)
        )
        return list(self.db.scalars(stmt))

    def list_by_fornecedor(self, id_fornecedor: str) -> list[Consultor]:
        stmt = (
            select(Consultor)
            .where(Consultor.id_fornecedor == id_fornecedor, Consultor.ativo.is_(True))
            .options(*_EAGER)
        )
        return list(self.db.scalars(stmt))

    def list_by_lideranca(self, lideranca_id: int) -> list[Consultor]:
        stmt = (
            select(Consultor)
            .where(Consultor.lideranca_id == lideranca_id, Consultor.ativo.is_(True))
            .options(*_EAGER)
        )
        return list(self.db.scalars(stmt))

    def liderancas_ids(self) -> set[int]:
        """IDs de usuário que são líder de algum consultor ativo, numa única query —
        usado para resolver o perfil "Liderança" de uma lista inteira de usuários sem
        repetir existe_lideranca() (1 query por usuário) para cada um."""
        stmt = (
            select(Consultor.lideranca_id)
            .where(Consultor.lideranca_id.is_not(None), Consultor.ativo.is_(True))
            .distinct()
        )
        return set(self.db.scalars(stmt))

    def existe_lideranca(self, usuario_id: int) -> bool:
        """True se este usuário está referenciado como líder em algum consultor ativo —
        é isso que faz o perfil "Liderança" ser atribuído automaticamente."""
        return (
            self.db.scalar(
                select(Consultor.id).where(
                    Consultor.lideranca_id == usuario_id, Consultor.ativo.is_(True)
                ).limit(1)
            )
            is not None
        )

    def count(self) -> int:
        return self.db.query(Consultor).count()

    def create(self, consultor: Consultor) -> Consultor:
        self.db.add(consultor)
        self.db.commit()
        self.db.refresh(consultor)
        return consultor

    def update(self, consultor: Consultor) -> Consultor:
        self.db.commit()
        self.db.refresh(consultor)
        return consultor

    def delete(self, consultor: Consultor) -> None:
        self.db.delete(consultor)
        self.db.commit()
