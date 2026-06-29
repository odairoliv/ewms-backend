from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.schemas.apontamento import (
    ApontamentoAprovarHoras,
    ApontamentoCreate,
    ApontamentoEditarHoras,
    ApontamentoOut,
    ApontamentoStatusUpdate,
)
from app.services.apontamento_service import ApontamentoService

router = APIRouter(prefix="/apontamentos", tags=["apontamentos"])


@router.get("", response_model=list[ApontamentoOut])
def listar(
    periodo: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApontamentoService(db).list_for_user(current_user, periodo)


@router.post("", response_model=ApontamentoOut, status_code=201)
def criar(
    payload: ApontamentoCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("Administrador")),
):
    return ApontamentoService(db).create(payload)


@router.put("/{apontamento_id}", response_model=ApontamentoOut)
def atualizar_status(
    apontamento_id: str,
    payload: ApontamentoStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_roles("Administrador", "Liderança", "Fornecedor", "Usuário")
    ),
):
    return ApontamentoService(db).atualizar_status(apontamento_id, payload, current_user)


@router.delete("/{apontamento_id}", status_code=204)
def remover(
    apontamento_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    ApontamentoService(db).delete(apontamento_id, current_user)


@router.put("/{apontamento_id}/horas", response_model=ApontamentoOut)
def editar_horas(
    apontamento_id: str,
    payload: ApontamentoEditarHoras,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador", "Liderança")),
):
    return ApontamentoService(db).editar_horas(apontamento_id, payload, current_user)


@router.post("/{apontamento_id}/aprovar-horas", response_model=ApontamentoOut)
def aprovar_horas(
    apontamento_id: str,
    payload: ApontamentoAprovarHoras,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    return ApontamentoService(db).aprovar_horas(apontamento_id, payload, current_user)
