from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Usuario


class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)

    def get_by_email(self, email: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(Usuario.email == email))

    def list_all(self) -> list[Usuario]:
        return list(self.db.scalars(select(Usuario)))

    def list_by_empresa(self, empresa_id: str) -> list[Usuario]:
        return list(self.db.scalars(select(Usuario).where(Usuario.empresa_id == empresa_id)))

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
