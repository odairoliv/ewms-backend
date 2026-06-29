from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import require_roles
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    return AuthService(db).login(payload)


@router.post("/impersonar/{usuario_id}", response_model=LoginResponse)
def impersonar(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("SuperUsuario")),
):
    return AuthService(db).impersonar(usuario_id, current_user)
