from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.schemas.consultor import ConsultorCreate, ConsultorOut, ConsultorUpdate
from app.services.consultor_service import ConsultorService

router = APIRouter(prefix="/consultores", tags=["consultores"])


@router.get("", response_model=list[ConsultorOut])
def listar(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return ConsultorService(db).list_for_user(current_user)


@router.get("/{consultor_id}", response_model=ConsultorOut)
def detalhar(consultor_id: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return ConsultorService(db).get_out(consultor_id, current_user)


@router.post("", response_model=ConsultorOut, status_code=201)
def criar(
    payload: ConsultorCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador", "Liderança")),
):
    return ConsultorService(db).create(payload, current_user)


@router.put("/{consultor_id}", response_model=ConsultorOut)
def atualizar(
    consultor_id: str,
    payload: ConsultorUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador", "Liderança", "Usuário")),
):
    return ConsultorService(db).update(consultor_id, payload, current_user)


@router.delete("/{consultor_id}", status_code=204)
def remover(
    consultor_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    ConsultorService(db).delete(consultor_id, current_user)
