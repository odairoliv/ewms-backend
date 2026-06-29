from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CustomField(Base):
    """Mapeia, por empresa, como cada campo (padrão ou Custom01-04) de um objeto
    (formulário/tabela) deve aparecer no front: nome exibido, se é visível e se é obrigatório.

    Quando não existe linha para um campo de uma empresa, o front usa o padrão global
    (nome técnico do campo, visível, não obrigatório).
    """

    __tablename__ = "tb_custom"
    __table_args__ = (
        UniqueConstraint("empresa_id", "id_objeto", "nome_coluna", name="uq_custom_campo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    empresa_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("tb_empresas.id"), nullable=False
    )
    # Identifica o formulário/tabela: "fornecedor" | "consultor" | "apontamento" | "usuario" | "empresa"
    id_objeto: Mapped[str] = mapped_column(String(50), nullable=False)
    # Nome técnico da coluna no banco, ex.: "custom01" ou um campo padrão como "cargo"
    nome_coluna: Mapped[str] = mapped_column(String(50), nullable=False)
    # Nome de exibição definido pelo SuperUsuario para esta empresa
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    # Tipo do dado: "date" | "texto" | "float" | "padrao" (campos padrão mantêm seu tipo original)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="padrao")
    visivel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    obrigatorio: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ordem: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    criado_em: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
