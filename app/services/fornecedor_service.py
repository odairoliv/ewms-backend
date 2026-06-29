from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Fornecedor
from app.repositories.fornecedor_repository import FornecedorRepository
from app.schemas.fornecedor import FornecedorCreate, FornecedorUpdate
from app.services.audit_service import AuditService
from app.services.custom_field_service import CustomFieldService
from app.services.id_generator import next_id


class FornecedorService:
    def __init__(self, db: Session):
        self.repo = FornecedorRepository(db)
        self.audit_service = AuditService(db)
        self.custom_field_service = CustomFieldService(db)

    def _enrich(self, fornecedor: Fornecedor) -> dict:
        return {
            "id": fornecedor.id,
            "empresa_id": fornecedor.empresa_id,
            "empresa": fornecedor.empresa.nome if fornecedor.empresa else None,
            "razao_social": fornecedor.razao_social,
            "nome_fantasia": fornecedor.nome_fantasia,
            "cnpj": fornecedor.cnpj,
            "segmento": fornecedor.segmento,
            "cidade": fornecedor.cidade,
            "uf": fornecedor.uf,
            "status": fornecedor.status,
            "contato": fornecedor.contato,
            "telefone": fornecedor.telefone,
            "email": fornecedor.email,
            "custom01": fornecedor.custom01,
            "custom02": fornecedor.custom02,
            "custom03": fornecedor.custom03,
            "custom04": fornecedor.custom04,
            "criado_em": fornecedor.criado_em,
            "atualizado_em": fornecedor.atualizado_em,
        }

    def list_for_user(self, current_user: dict) -> list[dict]:
        if current_user.get("perfil") == "SuperUsuario":
            fornecedores = self.repo.list_all()
        else:
            fornecedores = self.repo.list_by_empresa(current_user.get("empresa_id"))
        return [self._enrich(f) for f in fornecedores]

    def get(self, fornecedor_id: str) -> Fornecedor:
        fornecedor = self.repo.get_by_id(fornecedor_id)
        if not fornecedor:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Fornecedor não encontrado")
        return fornecedor

    def _get_escopado(self, fornecedor_id: str, current_user: dict) -> Fornecedor:
        """Busca um fornecedor garantindo que ele pertence à empresa de quem está pedindo —
        sem isso, qualquer Administrador autenticado poderia ler/editar dados (inclusive
        financeiros) de fornecedores de OUTRAS empresas só sabendo o ID (IDOR)."""
        fornecedor = self.get(fornecedor_id)
        if current_user.get("perfil") != "SuperUsuario" and fornecedor.empresa_id != current_user.get("empresa_id"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Fornecedor não encontrado")
        return fornecedor

    def get_out(self, fornecedor_id: str, current_user: dict) -> dict:
        return self._enrich(self._get_escopado(fornecedor_id, current_user))

    def create(self, payload: FornecedorCreate, current_user: dict) -> dict:
        novo_id = next_id("FOR", self.repo.count())
        dados = payload.model_dump()
        if current_user.get("perfil") != "SuperUsuario" or not dados.get("empresa_id"):
            dados["empresa_id"] = current_user.get("empresa_id")
        self.custom_field_service.validar_obrigatorios(dados["empresa_id"], "fornecedor", dados)
        fornecedor = Fornecedor(id=novo_id, **dados)
        return self._enrich(self.repo.create(fornecedor))

    def update(self, fornecedor_id: str, payload: FornecedorUpdate, current_user: dict) -> dict:
        fornecedor = self._get_escopado(fornecedor_id, current_user)
        mudancas = payload.model_dump(exclude_unset=True)
        dados_finais = {**self._enrich(fornecedor), **mudancas}
        self.custom_field_service.validar_obrigatorios(fornecedor.empresa_id, "fornecedor", dados_finais)
        for field, value in mudancas.items():
            setattr(fornecedor, field, value)
        return self._enrich(self.repo.update(fornecedor))

    def delete(self, fornecedor_id: str, current_user: dict) -> None:
        # Soft delete: o fornecedor permanece visível (status Inativo) para que
        # Administrador/SuperUsuario possam reativá-lo depois — nunca é removido do banco.
        fornecedor = self._get_escopado(fornecedor_id, current_user)
        fornecedor.status = "Inativo"
        self.repo.update(fornecedor)
        self.audit_service.registrar(
            usuario=current_user,
            modulo="Central de Cadastros",
            tipo_acao="Exclusão",
            nivel="Crítico",
            entidade="Fornecedor",
            entidade_id=fornecedor.id,
            justificativa="Registro inativado (soft delete) — dado preservado no banco",
        )

    def reativar(self, fornecedor_id: str, current_user: dict) -> dict:
        fornecedor = self._get_escopado(fornecedor_id, current_user)
        fornecedor.status = "Ativo"
        fornecedor = self.repo.update(fornecedor)
        self.audit_service.registrar(
            usuario=current_user,
            modulo="Central de Cadastros",
            tipo_acao="Reativação",
            nivel="Administrativo",
            entidade="Fornecedor",
            entidade_id=fornecedor.id,
        )
        return self._enrich(fornecedor)
