from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import CustomField
from app.repositories.custom_field_repository import CustomFieldRepository
from app.schemas.custom_field import OBJETOS_VALIDOS, TIPOS_VALIDOS, CustomFieldUpsert


class CustomFieldService:
    def __init__(self, db: Session):
        self.repo = CustomFieldRepository(db)

    def list_for_user(self, current_user: dict, empresa_id: str | None, id_objeto: str | None) -> list[CustomField]:
        # SuperUsuario pode consultar a configuração de qualquer empresa; demais perfis só a própria.
        alvo = empresa_id if current_user.get("perfil") == "SuperUsuario" and empresa_id else current_user.get("empresa_id")
        if id_objeto:
            return self.repo.list_by_empresa_objeto(alvo, id_objeto)
        return self.repo.list_by_empresa(alvo)

    def upsert(self, payload: CustomFieldUpsert) -> CustomField:
        if payload.id_objeto not in OBJETOS_VALIDOS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "id_objeto inválido")
        if payload.tipo not in TIPOS_VALIDOS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "tipo inválido")

        existente = self.repo.get_by_chave(payload.empresa_id, payload.id_objeto, payload.nome_coluna)
        if existente:
            for campo, valor in payload.model_dump().items():
                setattr(existente, campo, valor)
            return self.repo.update(existente)

        novo = CustomField(**payload.model_dump())
        return self.repo.create(novo)

    def resetar(self, custom_id: int) -> None:
        """Remove a customização — o campo volta a usar o padrão global no front."""
        campo = self.repo.get_by_id(custom_id)
        if not campo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Configuração não encontrada")
        self.repo.delete(campo)

    def validar_obrigatorios(self, empresa_id: str | None, id_objeto: str, dados: dict) -> None:
        """Garante no backend que campos marcados como obrigatórios em tb_custom para esta
        empresa (padrão ou Custom01-04) vieram preenchidos — a obrigatoriedade varia por
        empresa, então essa checagem não pode depender só da validação do frontend."""
        if not empresa_id:
            return
        campos = self.repo.list_by_empresa_objeto(empresa_id, id_objeto)
        faltantes = [
            c.nome for c in campos
            if c.obrigatorio and not dados.get(c.nome_coluna)
        ]
        if faltantes:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Campo(s) obrigatório(s) não preenchido(s): {', '.join(faltantes)}",
            )
