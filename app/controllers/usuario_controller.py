from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.schemas.usuario import UsuarioAprovarEdicao, UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioOut])
def listar(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador", "Liderança")),
):
    return UsuarioService(db).list_for_user(current_user)


@router.get("/{usuario_id}", response_model=UsuarioOut)
def detalhar(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador", "Liderança", "Usuário")),
):
    return UsuarioService(db).get_out(usuario_id, current_user)


@router.post("", response_model=UsuarioOut, status_code=201)
def criar(
    payload: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    return UsuarioService(db).create(payload, current_user)


@router.put("/{usuario_id}", response_model=UsuarioOut)
def atualizar(
    usuario_id: int,
    payload: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador", "Liderança", "Usuário")),
):
    return UsuarioService(db).update(usuario_id, payload, current_user)


@router.post("/{usuario_id}/aprovar-edicao", response_model=UsuarioOut)
def aprovar_edicao(
    usuario_id: int,
    payload: UsuarioAprovarEdicao,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    return UsuarioService(db).aprovar_edicao(usuario_id, payload, current_user)


@router.delete("/{usuario_id}", status_code=204)
def remover(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    UsuarioService(db).delete(usuario_id, current_user)
