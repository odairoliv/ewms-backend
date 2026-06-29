from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Consultor
from app.repositories.consultor_repository import ConsultorRepository
from app.repositories.fornecedor_repository import FornecedorRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.consultor import ConsultorCreate, ConsultorUpdate
from app.services.audit_service import AuditService
from app.services.custom_field_service import CustomFieldService
from app.services.id_generator import next_id

CAMPOS_REVISIONAVEIS = [
    "cargo", "departamento", "valor_hora", "horas_previstas_semana",
    "id_fornecedor", "lideranca_id", "status", "data_inicio", "data_fim",
    "custom01", "custom02", "custom03", "custom04",
]


class ConsultorService:
    def __init__(self, db: Session):
        self.repo = ConsultorRepository(db)
        self.usuario_repo = UsuarioRepository(db)
        self.fornecedor_repo = FornecedorRepository(db)
        self.audit_service = AuditService(db)
        self.custom_field_service = CustomFieldService(db)

    def _enrich(self, consultor: Consultor) -> dict:
        usuario = consultor.usuario
        return {
            "id": consultor.id,
            "usuario_id": consultor.usuario_id,
            "nome": usuario.nome if usuario else None,
            "cpf": usuario.cpf if usuario else None,
            "email": usuario.email if usuario else None,
            "cargo": consultor.cargo,
            "departamento": consultor.departamento,
            "valor_hora": consultor.valor_hora,
            "horas_previstas_semana": consultor.horas_previstas_semana,
            "id_fornecedor": consultor.id_fornecedor,
            "fornecedor": consultor.fornecedor.razao_social if consultor.fornecedor else None,
            "lideranca_id": consultor.lideranca_id,
            "lideranca": consultor.lideranca.nome if consultor.lideranca else None,
            "status": consultor.status,
            "data_inicio": consultor.data_inicio,
            "data_fim": consultor.data_fim,
            "ativo": consultor.ativo,
            "revisao": consultor.revisao,
            "custom01": consultor.custom01,
            "custom02": consultor.custom02,
            "custom03": consultor.custom03,
            "custom04": consultor.custom04,
            "criado_em": consultor.criado_em,
            "atualizado_em": consultor.atualizado_em,
        }

    def list_for_user(self, current_user: dict) -> list[dict]:
        perfil = current_user.get("perfil")
        if perfil == "SuperUsuario":
            consultores = self.repo.list_all()
        elif perfil in ("Administrador", "Usuário"):
            consultores = self.repo.list_by_empresa(current_user.get("empresa_id"))
        elif perfil == "Fornecedor":
            consultores = self.repo.list_by_fornecedor(current_user.get("id_fornecedor"))
        elif perfil == "Liderança":
            consultores = self.repo.list_by_lideranca(current_user.get("id"))
        else:
            consultores = []
        return [self._enrich(c) for c in consultores]

    def get(self, consultor_id: str) -> Consultor:
        consultor = self.repo.get_by_id(consultor_id)
        if not consultor:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultor não encontrado")
        return consultor

    def _get_escopado(self, consultor_id: str, current_user: dict) -> Consultor:
        """Garante que o consultor pertence ao escopo de quem está pedindo — sem isso,
        qualquer usuário autenticado poderia ler/editar dados financeiros (valor_hora) e
        pessoais (CPF) de consultores de OUTRAS empresas só sabendo o ID (IDOR)."""
        consultor = self.get(consultor_id)
        perfil = current_user.get("perfil")
        if perfil == "SuperUsuario":
            return consultor
        if perfil == "Fornecedor":
            if consultor.id_fornecedor != current_user.get("id_fornecedor"):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultor não encontrado")
            return consultor
        if perfil == "Liderança":
            if consultor.lideranca_id != current_user.get("id"):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultor não encontrado")
            return consultor
        if perfil == "Usuário":
            # Usuário comum só acessa o PRÓPRIO registro de consultor, nunca o de outra pessoa.
            if consultor.usuario_id != current_user.get("id"):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultor não encontrado")
            return consultor
        # Administrador: precisa pertencer à mesma empresa (via fornecedor vinculado).
        empresa_consultor = consultor.fornecedor.empresa_id if consultor.fornecedor else None
        if empresa_consultor != current_user.get("empresa_id"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Consultor não encontrado")
        return consultor

    def get_out(self, consultor_id: str, current_user: dict) -> dict:
        return self._enrich(self._get_escopado(consultor_id, current_user))

    def _validar_usuario_e_fornecedor(self, payload: ConsultorCreate, current_user: dict) -> None:
        usuario = self.usuario_repo.get_by_id(payload.usuario_id)
        if not usuario:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
        if usuario.id_fornecedor:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Usuários vinculados a um fornecedor não podem ser cadastrados como consultor/terceiro",
            )
        if self.repo.get_by_usuario_id(usuario.id):
            raise HTTPException(status.HTTP_409_CONFLICT, "Este usuário já está vinculado a um consultor")

        if current_user.get("perfil") != "SuperUsuario":
            empresa_id = current_user.get("empresa_id")
            if usuario.empresa_id != empresa_id:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, "Usuário não pertence à sua empresa"
                )
            fornecedor = self.fornecedor_repo.get_by_id(payload.id_fornecedor)
            if not fornecedor or fornecedor.empresa_id != empresa_id:
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, "Fornecedor não pertence à sua empresa"
                )

    def create(self, payload: ConsultorCreate, current_user: dict) -> dict:
        self._validar_usuario_e_fornecedor(payload, current_user)
        dados = payload.model_dump()
        fornecedor = self.fornecedor_repo.get_by_id(dados["id_fornecedor"])
        self.custom_field_service.validar_obrigatorios(
            fornecedor.empresa_id if fornecedor else None, "consultor", dados
        )
        novo_id = next_id("CON", self.repo.count())
        consultor = Consultor(id=novo_id, **dados)
        return self._enrich(self.repo.create(consultor))

    def update(self, consultor_id: str, payload: ConsultorUpdate, current_user: dict) -> dict:
        """Edição não sobrescreve a linha: inativa a atual e cria uma nova revisão
        (revisao = anterior + 1), preservando o histórico completo do cadastro."""
        anterior = self._get_escopado(consultor_id, current_user)
        mudancas = payload.model_dump(exclude_unset=True)

        dados_novos = {campo: getattr(anterior, campo) for campo in CAMPOS_REVISIONAVEIS}
        dados_novos.update(mudancas)

        fornecedor = self.fornecedor_repo.get_by_id(dados_novos["id_fornecedor"])
        self.custom_field_service.validar_obrigatorios(
            fornecedor.empresa_id if fornecedor else None, "consultor", dados_novos
        )

        anterior.ativo = False
        self.repo.update(anterior)

        novo_id = next_id("CON", self.repo.count())
        novo = Consultor(
            id=novo_id,
            usuario_id=anterior.usuario_id,
            revisao=anterior.revisao + 1,
            ativo=True,
            **dados_novos,
        )
        novo = self.repo.create(novo)

        self.audit_service.registrar(
            usuario=current_user,
            modulo="Central de Cadastros",
            tipo_acao="Edição",
            nivel="Administrativo",
            entidade="Consultor",
            entidade_id=novo.id,
            campo_alterado=",".join(mudancas.keys()) or None,
            valor_antes=anterior.id,
            valor_depois=novo.id,
            justificativa=f"Revisão {novo.revisao} (anterior: {anterior.id})",
        )
        return self._enrich(novo)

    def delete(self, consultor_id: str, current_user: dict) -> None:
        consultor = self._get_escopado(consultor_id, current_user)
        consultor.ativo = False
        self.repo.update(consultor)
        self.audit_service.registrar(
            usuario=current_user,
            modulo="Central de Cadastros",
            tipo_acao="Exclusão",
            nivel="Crítico",
            entidade="Consultor",
            entidade_id=consultor.id,
            justificativa="Registro inativado (soft delete) — dado preservado no banco",
        )
