from datetime import datetime

from pydantic import BaseModel, ConfigDict

# Objetos (formulários/tabelas) que suportam configuração de campos
OBJETOS_VALIDOS = {"empresa", "fornecedor", "consultor", "apontamento", "usuario"}
TIPOS_VALIDOS = {"padrao", "date", "texto", "float"}


class CustomFieldUpsert(BaseModel):
    empresa_id: str
    id_objeto: str
    nome_coluna: str
    nome: str
    tipo: str = "padrao"
    visivel: bool = True
    obrigatorio: bool = False
    ordem: int = 0


class CustomFieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    empresa_id: str
    id_objeto: str
    nome_coluna: str
    nome: str
    tipo: str
    visivel: bool
    obrigatorio: bool
    ordem: int
    criado_em: datetime
    atualizado_em: datetime
