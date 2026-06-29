from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class EmpresaBase(BaseModel):
    nome: str
    status: str = "Ativo"
    cnpj: str | None = None
    telefone: str | None = None
    email_contato: str | None = None
    endereco: str | None = None
    custom01: date | None = None
    custom02: str | None = None
    custom03: str | None = None
    custom04: Decimal | None = None


class EmpresaCreate(EmpresaBase):
    pass


# Campos que o Administrador da própria empresa (ou o SuperUsuario) pode editar.
# Quando quem edita é Administrador, a alteração fica pendente de aprovação do SuperUsuario.
class EmpresaUpdate(BaseModel):
    nome: str | None = None
    cnpj: str | None = None
    telefone: str | None = None
    email_contato: str | None = None
    endereco: str | None = None
    custom01: date | None = None
    custom02: str | None = None
    custom03: str | None = None
    custom04: Decimal | None = None


class EmpresaAprovar(BaseModel):
    acao: str  # "Aprovado" | "Recusado"
    justificativa: str | None = None


class EmpresaOut(EmpresaBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status_aprovacao: str
    dados_pendentes: str | None = None
    solicitado_por: str | None = None
    solicitado_em: datetime | None = None
    justificativa_rejeicao: str | None = None
    criado_em: datetime
    atualizado_em: datetime
