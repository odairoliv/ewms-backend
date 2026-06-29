from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class UsuarioLogado(BaseModel):
    id: int
    nome: str
    email: str
    perfil: str
    id_fornecedor: str | None = None
    empresa_id: str | None = None
    empresa: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioLogado
