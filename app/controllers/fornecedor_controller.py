from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.schemas.fornecedor import FornecedorCreate, FornecedorOut, FornecedorUpdate
from app.services.fornecedor_service import FornecedorService

router = APIRouter(prefix="/fornecedores", tags=["fornecedores"])


@router.get("", response_model=list[FornecedorOut])
def listar(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador", "Liderança")),
):
    return FornecedorService(db).list_for_user(current_user)


@router.get("/{fornecedor_id}", response_model=FornecedorOut)
def detalhar(
    fornecedor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    return FornecedorService(db).get_out(fornecedor_id, current_user)


@router.post("", response_model=FornecedorOut, status_code=201)
def criar(
    payload: FornecedorCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    return FornecedorService(db).create(payload, current_user)


@router.put("/{fornecedor_id}", response_model=FornecedorOut)
def atualizar(
    fornecedor_id: str,
    payload: FornecedorUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    return FornecedorService(db).update(fornecedor_id, payload, current_user)


@router.delete("/{fornecedor_id}", status_code=204)
def remover(
    fornecedor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    FornecedorService(db).delete(fornecedor_id, current_user)


@router.post("/{fornecedor_id}/reativar", response_model=FornecedorOut)
def reativar(
    fornecedor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    return FornecedorService(db).reativar(fornecedor_id, current_user)
