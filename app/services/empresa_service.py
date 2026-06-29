import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Empresa
from app.repositories.empresa_repository import EmpresaRepository
from app.schemas.empresa import EmpresaAprovar, EmpresaCreate, EmpresaUpdate
from app.services.audit_service import AuditService
from app.services.custom_field_service import CustomFieldService
from app.services.id_generator import next_id

ACOES_APROVACAO = {"Aprovado", "Recusado"}
CAMPOS_EMPRESA = ["nome", "cnpj", "telefone", "email_contato", "endereco", "custom01", "custom02", "custom03", "custom04"]


class EmpresaService:
    def __init__(self, db: Session):
        self.repo = EmpresaRepository(db)
        self.audit_service = AuditService(db)
        self.custom_field_service = CustomFieldService(db)

    def list_all(self) -> list[Empresa]:
        return self.repo.list_all()

    def get(self, empresa_id: str) -> Empresa:
        empresa = self.repo.get_by_id(empresa_id)
        if not empresa:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa não encontrada")
        return empresa

    def create(self, payload: EmpresaCreate) -> Empresa:
        novo_id = next_id("EMP", self.repo.count())
        empresa = Empresa(id=novo_id, **payload.model_dump())
        return self.repo.create(empresa)

    def update(self, empresa_id: str, payload: EmpresaUpdate, current_user: dict) -> Empresa:
        empresa = self.get(empresa_id)
        perfil = current_user.get("perfil")

        if perfil == "Administrador" and current_user.get("empresa_id") != empresa_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Você só pode editar os dados da sua própria empresa"
            )

        mudancas = payload.model_dump(exclude_unset=True)
        if not mudancas:
            return empresa

        dados_finais = {campo: getattr(empresa, campo) for campo in CAMPOS_EMPRESA}
        dados_finais.update(mudancas)
        self.custom_field_service.validar_obrigatorios(empresa_id, "empresa", dados_finais)

        if perfil == "SuperUsuario":
            # SuperUsuario aplica direto, sem necessidade de aprovação.
            for campo, valor in mudancas.items():
                setattr(empresa, campo, valor)
            empresa.status_aprovacao = "Aprovado"
            empresa.dados_pendentes = None
            empresa.solicitado_por = None
            empresa.solicitado_em = None
            empresa.justificativa_rejeicao = None
            empresa = self.repo.update(empresa)
            self.audit_service.registrar(
                usuario=current_user,
                modulo="Central de Cadastros",
                tipo_acao="Edição",
                nivel="Administrativo",
                entidade="Empresa",
                entidade_id=empresa.id,
                campo_alterado=",".join(mudancas.keys()),
                valor_depois=json.dumps(mudancas, ensure_ascii=False),
            )
            return empresa

        # Administrador: fica pendente de aprovação do SuperUsuario.
        empresa.dados_pendentes = json.dumps(mudancas, ensure_ascii=False)
        empresa.status_aprovacao = "Pendente"
        empresa.solicitado_por = current_user.get("email")
        empresa.solicitado_em = datetime.now(timezone.utc)
        empresa.justificativa_rejeicao = None
        empresa = self.repo.update(empresa)

        self.audit_service.registrar(
            usuario=current_user,
            modulo="Central de Cadastros",
            tipo_acao="Solicitação de edição",
            nivel="Administrativo",
            entidade="Empresa",
            entidade_id=empresa.id,
            campo_alterado=",".join(mudancas.keys()),
            valor_depois=json.dumps(mudancas, ensure_ascii=False),
            justificativa="Aguardando aprovação do SuperUsuario",
        )
        return empresa

    def aprovar(self, empresa_id: str, payload: EmpresaAprovar, current_user: dict) -> Empresa:
        if payload.acao not in ACOES_APROVACAO:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ação inválida")

        empresa = self.get(empresa_id)
        if empresa.status_aprovacao != "Pendente":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Esta empresa não possui edição pendente de aprovação"
            )

        mudancas = json.loads(empresa.dados_pendentes) if empresa.dados_pendentes else {}

        if payload.acao == "Aprovado":
            for campo, valor in mudancas.items():
                setattr(empresa, campo, valor)
            empresa.status_aprovacao = "Aprovado"
            empresa.justificativa_rejeicao = None
        else:
            empresa.status_aprovacao = "Recusado"
            empresa.justificativa_rejeicao = payload.justificativa

        empresa.dados_pendentes = None
        empresa.solicitado_por = None
        empresa.solicitado_em = None
        empresa = self.repo.update(empresa)

        self.audit_service.registrar(
            usuario=current_user,
            modulo="Central de Cadastros",
            tipo_acao=payload.acao,
            nivel="Crítico" if payload.acao == "Recusado" else "Administrativo",
            entidade="Empresa",
            entidade_id=empresa.id,
            campo_alterado=",".join(mudancas.keys()),
            valor_depois=json.dumps(mudancas, ensure_ascii=False),
            justificativa=payload.justificativa,
        )
        return empresa
