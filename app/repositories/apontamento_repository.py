from sqlalchemy import extract, select
from sqlalchemy.orm import Session, selectinload

from app.models import Apontamento, Consultor, Fornecedor
from app.services.periodo_utils import periodo_para_data

# Relacionamentos sempre lidos em _enrich (ApontamentoService): consultor -> usuario/
# fornecedor/lideranca. selectinload carrega tudo em poucas queries extras fixas, em vez
# de uma query por apontamento por relacionamento (N+1, agravado pela latência de rede
# entre o backend e o banco).
_EAGER = (
    selectinload(Apontamento.consultor).selectinload(Consultor.usuario),
    selectinload(Apontamento.consultor).selectinload(Consultor.fornecedor),
    selectinload(Apontamento.consultor).selectinload(Consultor.lideranca),
)


def _filtrar_por_periodo(stmt, periodo: str | None):
    if not periodo:
        return stmt
    data_ref = periodo_para_data(periodo)
    return stmt.where(
        extract("year", Apontamento.data_reporte) == data_ref.year,
        extract("month", Apontamento.data_reporte) == data_ref.month,
    )


class ApontamentoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, apontamento_id: str) -> Apontamento | None:
        stmt = select(Apontamento).where(Apontamento.id == apontamento_id).options(*_EAGER)
        return self.db.scalar(stmt)

    def list_all(self, periodo: str | None = None) -> list[Apontamento]:
        stmt = select(Apontamento).where(Apontamento.ativo.is_(True)).options(*_EAGER)
        stmt = _filtrar_por_periodo(stmt, periodo)
        return list(self.db.scalars(stmt))

    def list_by_empresa(self, empresa_id: str, periodo: str | None = None) -> list[Apontamento]:
        stmt = (
            select(Apontamento)
            .join(Fornecedor, Fornecedor.id == Apontamento.id_fornecedor)
            .where(Fornecedor.empresa_id == empresa_id, Apontamento.ativo.is_(True))
            .options(*_EAGER)
        )
        stmt = _filtrar_por_periodo(stmt, periodo)
        return list(self.db.scalars(stmt))

    def list_by_fornecedor(self, id_fornecedor: str, periodo: str | None = None) -> list[Apontamento]:
        stmt = (
            select(Apontamento)
            .where(Apontamento.id_fornecedor == id_fornecedor, Apontamento.ativo.is_(True))
            .options(*_EAGER)
        )
        stmt = _filtrar_por_periodo(stmt, periodo)
        return list(self.db.scalars(stmt))

    def list_by_consultor(self, id_consultor: str, periodo: str | None = None) -> list[Apontamento]:
        stmt = (
            select(Apontamento)
            .where(Apontamento.id_consultor == id_consultor, Apontamento.ativo.is_(True))
            .options(*_EAGER)
        )
        stmt = _filtrar_por_periodo(stmt, periodo)
        return list(self.db.scalars(stmt))

    def list_by_lideranca(self, lideranca_id: int, periodo: str | None = None) -> list[Apontamento]:
        stmt = (
            select(Apontamento)
            .join(Consultor, Consultor.id == Apontamento.id_consultor)
            .where(Consultor.lideranca_id == lideranca_id, Apontamento.ativo.is_(True))
            .options(*_EAGER)
        )
        stmt = _filtrar_por_periodo(stmt, periodo)
        return list(self.db.scalars(stmt))

    def count(self) -> int:
        return self.db.query(Apontamento).count()

    def create(self, apontamento: Apontamento) -> Apontamento:
        self.db.add(apontamento)
        self.db.commit()
        self.db.refresh(apontamento)
        return apontamento

    def update(self, apontamento: Apontamento) -> Apontamento:
        self.db.commit()
        self.db.refresh(apontamento)
        return apontamento
