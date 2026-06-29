from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Upload(Base):
    __tablename__ = "tb_uploads"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    empresa_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("tb_empresas.id"), nullable=False
    )
    arquivo: Mapped[str] = mapped_column(String(255), nullable=False)
    periodo: Mapped[str] = mapped_column(String(20), nullable=False)
    data_upload: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    linhas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejeitadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # "Processando" (assíncrono, em andamento no servidor) -> "Processado" (tudo importado)
    # ou "Recusado" (validação tudo-ou-nada falhou — nada foi salvo, ver erro_detalhe).
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Processando")
    erro_detalhe: Mapped[str | None] = mapped_column(Text, nullable=True)
