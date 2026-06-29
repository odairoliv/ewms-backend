from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Empresa(Base):
    __tablename__ = "tb_empresas"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Ativo")
    cnpj: Mapped[str | None] = mapped_column(String(18), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email_contato: Mapped[str | None] = mapped_column(String(150), nullable=True)
    endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Fluxo de aprovação: Administrador edita os dados da própria empresa, mas a mudança
    # só é aplicada de fato quando o SuperUsuario aprova (ver EmpresaService.solicitar_edicao/aprovar).
    status_aprovacao: Mapped[str] = mapped_column(String(20), nullable=False, default="Aprovado")
    dados_pendentes: Mapped[str | None] = mapped_column(Text, nullable=True)
    solicitado_por: Mapped[str | None] = mapped_column(String(150), nullable=True)
    solicitado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    justificativa_rejeicao: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Campos customizáveis: o que aparece em cada um (nome, visibilidade, obrigatoriedade)
    # é configurado por empresa em tb_custom (ver CustomFieldService) — aqui só os tipos fixos.
    custom01: Mapped[date | None] = mapped_column(Date, nullable=True)
    custom02: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom03: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom04: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    usuarios = relationship("Usuario", back_populates="empresa")
    fornecedores = relationship("Fornecedor", back_populates="empresa")
