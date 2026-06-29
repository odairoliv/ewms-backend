from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ConsultorCreate(BaseModel):
    usuario_id: int
    cargo: str | None = None
    departamento: str | None = None
    valor_hora: Decimal
    horas_previstas_semana: Decimal = Decimal("0")
    id_fornecedor: str
    lideranca_id: int | None = None
    status: str = "Ativo"
    data_inicio: date | None = None
    data_fim: date | None = None
    custom01: date | None = None
    custom02: str | None = None
    custom03: str | None = None
    custom04: Decimal | None = None


class ConsultorUpdate(BaseModel):
    cargo: str | None = None
    departamento: str | None = None
    valor_hora: Decimal | None = None
    horas_previstas_semana: Decimal | None = None
    id_fornecedor: str | None = None
    lideranca_id: int | None = None
    status: str | None = None
    data_inicio: date | None = None
    data_fim: date | None = None
    custom01: date | None = None
    custom02: str | None = None
    custom03: str | None = None
    custom04: Decimal | None = None


class ConsultorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    usuario_id: int
    nome: str
    cpf: str | None = None
    email: str | None = None
    cargo: str | None = None
    departamento: str | None = None
    valor_hora: float
    horas_previstas_semana: float
    id_fornecedor: str
    fornecedor: str | None = None
    lideranca_id: int | None = None
    lideranca: str | None = None
    status: str
    data_inicio: date | None = None
    data_fim: date | None = None
    ativo: bool
    revisao: int
    custom01: date | None = None
    custom02: str | None = None
    custom03: str | None = None
    custom04: Decimal | None = None
    criado_em: datetime
    atualizado_em: datetime
