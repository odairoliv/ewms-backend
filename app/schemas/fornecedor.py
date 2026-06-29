from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr


class FornecedorBase(BaseModel):
    razao_social: str
    nome_fantasia: str | None = None
    cnpj: str
    segmento: str | None = None
    cidade: str | None = None
    uf: str | None = None
    status: str = "Ativo"
    contato: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    custom01: date | None = None
    custom02: str | None = None
    custom03: str | None = None
    custom04: Decimal | None = None


class FornecedorCreate(FornecedorBase):
    empresa_id: str | None = None  # SuperUsuario pode informar; demais usam a própria empresa


class FornecedorUpdate(BaseModel):
    razao_social: str | None = None
    nome_fantasia: str | None = None
    segmento: str | None = None
    cidade: str | None = None
    uf: str | None = None
    status: str | None = None
    contato: str | None = None
    telefone: str | None = None
    email: EmailStr | None = None
    custom01: date | None = None
    custom02: str | None = None
    custom03: str | None = None
    custom04: Decimal | None = None


class FornecedorOut(FornecedorBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    empresa_id: str
    empresa: str | None = None
    criado_em: datetime
    atualizado_em: datetime
