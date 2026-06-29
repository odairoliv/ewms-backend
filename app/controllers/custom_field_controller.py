from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.schemas.custom_field import CustomFieldOut, CustomFieldUpsert
from app.services.custom_field_service import CustomFieldService

router = APIRouter(prefix="/custom-fields", tags=["custom-fields"])


@router.get("", response_model=list[CustomFieldOut])
def listar(
    empresa_id: str | None = None,
    id_objeto: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return CustomFieldService(db).list_for_user(current_user, empresa_id, id_objeto)


@router.post("", response_model=CustomFieldOut, status_code=201)
def upsert(
    payload: CustomFieldUpsert,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("SuperUsuario")),
):
    return CustomFieldService(db).upsert(payload)


@router.delete("/{custom_id}", status_code=204)
def resetar(
    custom_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("SuperUsuario")),
):
    CustomFieldService(db).resetar(custom_id)
