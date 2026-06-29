from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.schemas.audit import AuditLogOut, AuditRevisaoRequest
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auditoria", tags=["auditoria"])


@router.get("", response_model=list[AuditLogOut])
def listar(
    empresa_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    return AuditService(db).list_for_user(current_user, empresa_id)


@router.post("/{audit_id}/revisar", response_model=AuditLogOut)
def revisar(
    audit_id: str,
    payload: AuditRevisaoRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    return AuditService(db).revisar(audit_id, payload.acao, payload.justificativa)
