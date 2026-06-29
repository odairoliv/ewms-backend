from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Usuario(Base):
    __tablename__ = "tb_usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[str] = mapped_column(String(30), nullable=False)
    cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    departamento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cargo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Ativo")
    empresa_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("tb_empresas.id"), nullable=False
    )
    id_fornecedor: Mapped[str | None] = mapped_column(
        String(20), ForeignKey("tb_fornecedores.id"), nullable=True
    )

    custom01: Mapped[date | None] = mapped_column(Date, nullable=True)
    custom02: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom03: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom04: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    # Autoedição: um usuário comum pode editar seus próprios campos não sensíveis, mas a
    # alteração só é aplicada depois que o Administrador da empresa aprova (ver
    # UsuarioService.update/aprovar_edicao). Administrador/SuperUsuario continuam editando
    # qualquer cadastro direto, sem essa fila.
    edicao_status: Mapped[str] = mapped_column(String(20), nullable=False, default="Nenhuma")
    dados_pendentes: Mapped[str | None] = mapped_column(Text, nullable=True)
    solicitado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    justificativa_edicao: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Camada 2 de proteção contra força bruta (a 1ª é o limite por IP em /auth/login):
    # bloqueio por CONTA, que persiste mesmo se o atacante trocar de IP. Nunca exposto em
    # UsuarioOut — é detalhe interno de autenticação, não dado de cadastro.
    tentativas_login_falhas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bloqueado_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    empresa = relationship("Empresa", back_populates="usuarios")
    fornecedor = relationship("Fornecedor", back_populates="usuarios")
