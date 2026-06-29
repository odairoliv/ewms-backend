from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    empresa_id: str
    arquivo: str
    periodo: str
    data_upload: datetime
    linhas: int
    processadas: int
    rejeitadas: int
    status: str
    erro_detalhe: str | None = None


class ColunaTemplateOut(BaseModel):
    nome_coluna: str
    nome: str
    obrigatorio: bool
    tipo: str
