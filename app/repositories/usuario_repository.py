from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Usuario

# `empresa` é lido em UsuarioService._enrich e no login (AuthService); `fornecedor` em
# alguns fluxos de validação. Eager load evita 1 query extra por usuário (N+1).
_EAGER = (selectinload(Usuario.empresa), selectinload(Usuario.fornecedor))


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(Usuario.id == usuario_id).options(*_EAGER))

    def get_by_email(self, email: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(Usuario.email == email).options(*_EAGER))

    def list_all(self) -> list[Usuario]:
        return list(self.db.scalars(select(Usuario).options(*_EAGER)))

    def list_by_empresa(self, empresa_id: str) -> list[Usuario]:
        stmt = select(Usuario).where(Usuario.empresa_id == empresa_id).options(*_EAGER)
        return list(self.db.scalars(stmt))

    def create(self, usuario: Usuario) -> Usuario:
        self.db.add(usuario)
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def update(self, usuario: Usuario) -> Usuario:
        self.db.commit()
        self.db.refresh(usuario)
        return usuario

    def delete(self, usuario: Usuario) -> None:
        self.db.delete(usuario)
        self.db.commit()
