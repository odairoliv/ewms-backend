from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    empresa_id: str
    data_hora: datetime
    usuario: str
    email_usuario: str
    modulo: str
    tipo_acao: str
    ip: str | None = None
    nivel: str
    entidade: str | None = None
    entidade_id: str | None = None
    campo_alterado: str | None = None
    valor_antes: str | None = None
    valor_depois: str | None = None
    justificativa: str | None = None


class AuditRevisaoRequest(BaseModel):
    acao: str
    justificativa: str | None = None
