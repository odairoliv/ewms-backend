from fastapi import APIRouter, BackgroundTasks, Depends, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_roles
from app.schemas.upload import ColunaTemplateOut, UploadOut
from app.services.upload_service import UploadService

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("", response_model=list[UploadOut])
def listar(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    return UploadService(db).list_for_user(current_user)


@router.get("/template", response_model=list[ColunaTemplateOut])
def template(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    """Colunas do template de upload para a empresa do usuário logado — nomes e
    obrigatoriedade podem variar por empresa (configurados em Config. de Formulários)."""
    return UploadService(db).template_colunas(current_user.get("empresa_id"))


@router.post("", response_model=UploadOut, status_code=202)
def enviar(
    arquivo: UploadFile,
    background_tasks: BackgroundTasks,
    periodo: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("Administrador")),
):
    """Cria o registro do upload e devolve imediatamente (202) — o processamento
    pesado (validação tudo-ou-nada + importação) roda em background no servidor,
    então o usuário pode navegar para outra tela enquanto isso acontece."""
    conteudo = arquivo.file.read()
    service = UploadService(db)
    upload = service.iniciar_upload(arquivo.filename, periodo, current_user)
    background_tasks.add_task(
        UploadService.processar_em_background, upload.id, conteudo, current_user
    )
    return upload
