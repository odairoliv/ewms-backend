from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Consultor(Base):
    __tablename__ = "tb_consultores"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    # Sem unique=True: cada edição cria uma nova linha (revisão) para o mesmo usuario_id,
    # mantendo a anterior inativa. A unicidade "1 usuário = 1 consultor ATIVO" é validada em
    # ConsultorService, não no banco.
    usuario_id: Mapped[int] = mapped_column(ForeignKey("tb_usuarios.id"), nullable=False)
    cargo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    departamento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    valor_hora: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    horas_previstas_semana: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    id_fornecedor: Mapped[str] = mapped_column(
        String(20), ForeignKey("tb_fornecedores.id"), nullable=False
    )
    # FK para tb_usuarios: o usuário referenciado aqui recebe o perfil "Liderança"
    # automaticamente (ver UsuarioService.resolver_perfil) — não é mais um e-mail solto.
    lideranca_id: Mapped[int | None] = mapped_column(ForeignKey("tb_usuarios.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Ativo")
    data_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_fim: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Soft-delete + histórico de revisões: editar cria uma nova linha (revisao = anterior + 1)
    # e marca a linha anterior como ativo=False; excluir apenas marca ativo=False sem nova linha.
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revisao: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    custom01: Mapped[date | None] = mapped_column(Date, nullable=True)
    custom02: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom03: Mapped[str | None] = mapped_column(String(255), nullable=True)
    custom04: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    lideranca = relationship("Usuario", foreign_keys=[lideranca_id])
    fornecedor = relationship("Fornecedor", back_populates="consultores")
    apontamentos = relationship("Apontamento", back_populates="consultor")
