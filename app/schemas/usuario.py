from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, ConfigDict


class UsuarioBase(BaseModel):
    nome: str
    email: EmailStr
    perfil: str
    cpf: str | None = None
    telefone: str | None = None
    departamento: str | None = None
    cargo: str | None = None
    status: str = "Ativo"
    id_fornecedor: str | None = None
    custom01: date | None = None
    custom02: str | None = None
    custom03: str | None = None
    custom04: Decimal | None = None


class UsuarioCreate(UsuarioBase):
    senha: str
    empresa_id: str | None = None  # obrigatório só para SuperUsuario; demais usam a própria empresa


class UsuarioUpdate(BaseModel):
    nome: str | None = None
    telefone: str | None = None
    departamento: str | None = None
    cargo: str | None = None
    status: str | None = None
    id_fornecedor: str | None = None
    senha: str | None = None
    custom01: date | None = None
    custom02: str | None = None
    custom03: str | None = None
    custom04: Decimal | None = None


class UsuarioAprovarEdicao(BaseModel):
    acao: str  # "Aprovado" | "Recusado"
    justificativa: str | None = None


class UsuarioOut(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: str
    empresa: str | None = None
    edicao_status: str
    dados_pendentes: str | None = None
    solicitado_em: datetime | None = None
    justificativa_edicao: str | None = None
    criado_em: datetime
    atualizado_em: datetime
