from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Fornecedor(Base):
    __tablename__ = "tb_fornecedores"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    empresa_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("tb_empresas.id"), nullable=False
    )
    razao_social: Mapped[str] = mapped_column(String(150), nullable=False)
    nome_fantasia: Mapped[str | None] = mapped_column(String(150), nullable=True)
    cnpj: Mapped[str] = mapped_column(String(18), nullable=False, unique=True)
    segmento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cidade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    uf: Mapped[str | None] = mapped_column(String(2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Ativo")
    contato: Mapped[str | None] = mapped_column(String(150), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)

    custom01: Mapped[date | None] = mapped_column(Date, nullable=True)
    custom02: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom03: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom04: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    empresa = relationship("Empresa", back_populates="fornecedores")
    usuarios = relationship("Usuario", back_populates="fornecedor")
    consultores = relationship("Consultor", back_populates="fornecedor")
