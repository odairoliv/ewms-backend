from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import AuditLog
from app.repositories.audit_repository import AuditRepository
from app.services.id_generator import next_id


class AuditService:
    def __init__(self, db: Session):
        self.repo = AuditRepository(db)

    def list_for_user(self, current_user: dict, empresa_id: str | None = None) -> list[AuditLog]:
        if current_user.get("perfil") == "SuperUsuario":
            return self.repo.list_all_filtrado(empresa_id)
        return self.repo.list_by_empresa(current_user.get("empresa_id"))

    def revisar(self, audit_id: str, acao: str, justificativa: str | None) -> AuditLog:
        log = self.repo.get_by_id(audit_id)
        if not log:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Log de auditoria não encontrado")
        log.tipo_acao = acao
        log.justificativa = justificativa
        return self.repo.update(log)

    def registrar(
        self,
        usuario: dict,
        modulo: str,
        tipo_acao: str,
        nivel: str,
        entidade: str | None = None,
        entidade_id: str | None = None,
        campo_alterado: str | None = None,
        valor_antes: str | None = None,
        valor_depois: str | None = None,
        justificativa: str | None = None,
        ip: str | None = None,
    ) -> AuditLog:
        novo_id = next_id("AUD", self.repo.count())
        log = AuditLog(
            id=novo_id,
            empresa_id=usuario.get("empresa_id"),
            usuario=usuario.get("nome", usuario.get("email", "desconhecido")),
            email_usuario=usuario.get("email", "desconhecido"),
            modulo=modulo,
            tipo_acao=tipo_acao,
            ip=ip,
            nivel=nivel,
            entidade=entidade,
            entidade_id=entidade_id,
            campo_alterado=campo_alterado,
            valor_antes=valor_antes,
            valor_depois=valor_depois,
            justificativa=justificativa,
        )
        return self.repo.create(log)
