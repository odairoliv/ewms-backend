from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.schemas.empresa import EmpresaAprovar, EmpresaCreate, EmpresaOut, EmpresaUpdate
from app.services.empresa_service import EmpresaService

router = APIRouter(prefix="/empresas", tags=["empresas"])


@router.get("", response_model=list[EmpresaOut])
def listar(db: Session = Depends(get_db), _: dict = Depends(require_roles("SuperUsuario"))):
    return EmpresaService(db).list_all()


@router.get("/{empresa_id}", response_model=EmpresaOut)
def obter(
    empresa_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    perfil = current_user.get("perfil")
    if perfil not in ("SuperUsuario", "Administrador"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sem permissão")
    # Administrador só pode ver os dados da própria empresa — sem isso, qualquer Administrador
    # conseguiria ler CNPJ/telefone/endereço de QUALQUER outra empresa só trocando o ID na URL.
    if perfil == "Administrador" and current_user.get("empresa_id") != empresa_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa não encontrada")
    return EmpresaService(db).get(empresa_id)


@router.post("", response_model=EmpresaOut, status_code=201)
def criar(
    payload: EmpresaCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles("SuperUsuario")),
):
    return EmpresaService(db).create(payload)


@router.put("/{empresa_id}", response_model=EmpresaOut)
def editar(
    empresa_id: str,
    payload: EmpresaUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    return EmpresaService(db).update(empresa_id, payload, current_user)


@router.post("/{empresa_id}/aprovar", response_model=EmpresaOut)
def aprovar(
    empresa_id: str,
    payload: EmpresaAprovar,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("SuperUsuario")),
):
    return EmpresaService(db).aprovar(empresa_id, payload, current_user)
