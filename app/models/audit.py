from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "tb_audit"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    empresa_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("tb_empresas.id"), nullable=False
    )
    data_hora: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    usuario: Mapped[str] = mapped_column(String(150), nullable=False)
    email_usuario: Mapped[str] = mapped_column(String(150), nullable=False)
    modulo: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo_acao: Mapped[str] = mapped_column(String(30), nullable=False)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    nivel: Mapped[str] = mapped_column(String(30), nullable=False)
    entidade: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entidade_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    campo_alterado: Mapped[str | None] = mapped_column(String(100), nullable=True)
    valor_antes: Mapped[str | None] = mapped_column(Text, nullable=True)
    valor_depois: Mapped[str | None] = mapped_column(Text, nullable=True)
    justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)
