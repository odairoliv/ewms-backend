from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Apontamento(Base):
    __tablename__ = "tb_apontamentos"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    id_consultor: Mapped[str] = mapped_column(
        String(20), ForeignKey("tb_consultores.id"), nullable=False
    )
    id_fornecedor: Mapped[str] = mapped_column(
        String(20), ForeignKey("tb_fornecedores.id"), nullable=False
    )
    id_projeto: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nome_projeto: Mapped[str | None] = mapped_column(String(150), nullable=True)
    data_reporte: Mapped[date] = mapped_column(Date, nullable=False)
    semana: Mapped[str] = mapped_column(String(8), nullable=False)
    horas_trabalhadas: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    valor_hora: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Em Análise")
    justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Edição de horas: Administrador edita direto (auto-aprovado); Liderança edita e fica
    # pendente até o Administrador (ou SuperUsuario) aprovar — ver ApontamentoService.editar_horas/aprovar_horas.
    edicao_status: Mapped[str] = mapped_column(String(20), nullable=False, default="Nenhuma")
    horas_pendentes: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    solicitado_por: Mapped[str | None] = mapped_column(String(150), nullable=True)
    solicitado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    justificativa_edicao: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft-delete: excluir só marca ativo=False (nunca remove a linha); listas filtram ativo=True.
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    custom01: Mapped[date | None] = mapped_column(Date, nullable=True)
    custom02: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom03: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom04: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    consultor = relationship("Consultor", back_populates="apontamentos")
