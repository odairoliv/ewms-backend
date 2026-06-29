from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ApontamentoCreate(BaseModel):
    id_consultor: str
    id_fornecedor: str
    id_projeto: str | None = None
    nome_projeto: str | None = None
    periodo: str  # "Mês/Ano", ex: "Maio/2026" — a API converte para data_reporte
    horas_trabalhadas: Decimal
    valor_hora: Decimal


class ApontamentoStatusUpdate(BaseModel):
    status: str
    justificativa: str | None = None


class ApontamentoEditarHoras(BaseModel):
    horas_trabalhadas: Decimal
    justificativa: str | None = None


class ApontamentoAprovarHoras(BaseModel):
    acao: str  # "Aprovado" | "Recusado"
    justificativa: str | None = None


class ApontamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    id_consultor: str
    nome_consultor: str | None = None
    id_fornecedor: str
    fornecedor: str | None = None
    lideranca: str | None = None
    id_projeto: str | None = None
    nome_projeto: str | None = None
    data_reporte: date
    semana: str
    periodo: str
    horas_trabalhadas: float
    valor_hora: float
    valor_total: float
    status: str
    justificativa: str | None = None
    edicao_status: str
    horas_pendentes: float | None = None
    solicitado_por: str | None = None
    solicitado_em: datetime | None = None
    justificativa_edicao: str | None = None
    ativo: bool
    custom01: date | None = None
    custom02: str | None = None
    custom03: str | None = None
    custom04: Decimal | None = None
    criado_em: datetime
    atualizado_em: datetime
