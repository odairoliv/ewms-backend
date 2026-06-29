import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Usuario
from app.repositories.consultor_repository import ConsultorRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioAprovarEdicao, UsuarioCreate, UsuarioUpdate
from app.services.audit_service import AuditService
from app.services.custom_field_service import CustomFieldService

# Únicos valores que podem ficar "gravados" como perfil de um usuário — Fornecedor e
# Liderança nunca são armazenados: são sempre derivados de id_fornecedor / tb_consultores.
PERFIS_ARMAZENAVEIS = {"Administrador", "SuperUsuario", "Usuário"}

# Campos "não sensíveis" que um usuário comum pode propor alterar no próprio cadastro —
# e-mail, senha (tratada à parte), status, perfil, empresa e fornecedor vinculado ficam de fora.
CAMPOS_AUTOEDITAVEIS = {
    "nome", "telefone", "departamento", "cargo",
    "custom01", "custom02", "custom03", "custom04",
}
ACOES_APROVACAO_EDICAO = {"Aprovado", "Recusado"}


class UsuarioService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)
        self.consultor_repo = ConsultorRepository(db)
        self.custom_field_service = CustomFieldService(db)
        self.audit_service = AuditService(db)

    def resolver_perfil(self, usuario: Usuario) -> str:
        """O perfil efetivo de um usuário: Administrador/SuperUsuario continuam sendo
        atribuídos manualmente; todo o resto é automático — Fornecedor se houver
        id_fornecedor vinculado, Liderança se ele for o líder de algum consultor ativo,
        senão Usuário comum."""
        if usuario.perfil in ("Administrador", "SuperUsuario"):
            return usuario.perfil
        if usuario.id_fornecedor:
            return "Fornecedor"
        if self.consultor_repo.existe_lideranca(usuario.id):
            return "Liderança"
        return "Usuário"

    def _enrich(self, usuario: Usuario) -> dict:
        return {
            "id": usuario.id,
            "nome": usuario.nome,
            "email": usuario.email,
            "perfil": self.resolver_perfil(usuario),
            "cpf": usuario.cpf,
            "telefone": usuario.telefone,
            "departamento": usuario.departamento,
            "cargo": usuario.cargo,
            "status": usuario.status,
            "empresa_id": usuario.empresa_id,
            "empresa": usuario.empresa.nome if usuario.empresa else None,
            "id_fornecedor": usuario.id_fornecedor,
            "custom01": usuario.custom01,
            "custom02": usuario.custom02,
            "custom03": usuario.custom03,
            "custom04": usuario.custom04,
            "edicao_status": usuario.edicao_status,
            "dados_pendentes": usuario.dados_pendentes,
            "solicitado_em": usuario.solicitado_em,
            "justificativa_edicao": usuario.justificativa_edicao,
            "criado_em": usuario.criado_em,
            "atualizado_em": usuario.atualizado_em,
        }

    def list_for_user(self, current_user: dict) -> list[dict]:
        if current_user.get("perfil") == "SuperUsuario":
            usuarios = self.repo.list_all()
        else:
            usuarios = self.repo.list_by_empresa(current_user.get("empresa_id"))
        return [self._enrich(u) for u in usuarios]

    def get(self, usuario_id: int) -> Usuario:
        usuario = self.repo.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
        return usuario

    def _get_escopado(self, usuario_id: int, current_user: dict) -> Usuario:
        """Sem essa checagem, qualquer usuário autenticado conseguiria ler/editar o cadastro
        (CPF, telefone etc.) de QUALQUER outra pessoa — inclusive de outra empresa — só
        incrementando o ID na URL (IDOR). Administrador/Liderança ficam restritos à própria
        empresa; os demais perfis só podem acessar o próprio cadastro."""
        usuario = self.get(usuario_id)
        perfil = current_user.get("perfil")
        if perfil == "SuperUsuario":
            return usuario
        if perfil in ("Administrador", "Liderança"):
            if usuario.empresa_id != current_user.get("empresa_id"):
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
            return usuario
        if usuario.id != current_user.get("id"):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
        return usuario

    def get_out(self, usuario_id: int, current_user: dict) -> dict:
        return self._enrich(self._get_escopado(usuario_id, current_user))

    def create(self, payload: UsuarioCreate, current_user: dict) -> dict:
        if self.repo.get_by_email(payload.email):
            raise HTTPException(status.HTTP_409_CONFLICT, "Email já cadastrado")
        dados = payload.model_dump(exclude={"senha"})
        if not dados.get("id_fornecedor"):
            dados["id_fornecedor"] = None
        # Fornecedor/Liderança nunca são gravados — são sempre derivados (ver resolver_perfil).
        if dados.get("perfil") not in PERFIS_ARMAZENAVEIS:
            dados["perfil"] = "Usuário"
        if current_user.get("perfil") == "SuperUsuario":
            if not dados.get("empresa_id"):
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, "Informe a empresa do novo usuário"
                )
        else:
            dados["empresa_id"] = current_user.get("empresa_id")
        self.custom_field_service.validar_obrigatorios(dados["empresa_id"], "usuario", dados)
        usuario = Usuario(**dados, senha_hash=hash_password(payload.senha))
        return self._enrich(self.repo.create(usuario))

    def update(self, usuario_id: int, payload: UsuarioUpdate, current_user: dict) -> dict:
        usuario = self._get_escopado(usuario_id, current_user)
        data = payload.model_dump(exclude_unset=True, exclude={"senha"})
        # Fornecedor/Liderança nunca são gravados — são sempre derivados (ver resolver_perfil).
        if "perfil" in data and data["perfil"] not in PERFIS_ARMAZENAVEIS:
            data["perfil"] = "Usuário"

        eh_autoedicao = (
            current_user.get("id") == usuario.id
            and self.resolver_perfil(usuario) not in ("Administrador", "SuperUsuario")
        )

        # A senha é sempre auto-aplicada (só o próprio usuário a conhece/decide trocar) —
        # nunca passa pela fila de aprovação, mesmo numa autoedição.
        if payload.senha:
            usuario.senha_hash = hash_password(payload.senha)
            self.repo.update(usuario)

        if not eh_autoedicao:
            dados_finais = {**self._enrich(usuario), **data}
            self.custom_field_service.validar_obrigatorios(usuario.empresa_id, "usuario", dados_finais)
            for field, value in data.items():
                setattr(usuario, field, value)
            return self._enrich(self.repo.update(usuario))

        if not data:
            return self._enrich(usuario)

        campos_nao_permitidos = set(data.keys()) - CAMPOS_AUTOEDITAVEIS
        if campos_nao_permitidos:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Você só pode editar campos não sensíveis do próprio cadastro. "
                f"Não permitido: {', '.join(sorted(campos_nao_permitidos))}",
            )

        dados_finais = {**self._enrich(usuario), **data}
        self.custom_field_service.validar_obrigatorios(usuario.empresa_id, "usuario", dados_finais)

        usuario.dados_pendentes = json.dumps(data, ensure_ascii=False, default=str)
        usuario.edicao_status = "Pendente"
        usuario.solicitado_em = datetime.now(timezone.utc)
        usuario.justificativa_edicao = None
        usuario = self.repo.update(usuario)

        self.audit_service.registrar(
            usuario=current_user,
            modulo="Central de Cadastros",
            tipo_acao="Solicitação de edição",
            nivel="Administrativo",
            entidade="Usuario",
            entidade_id=str(usuario.id),
            campo_alterado=",".join(data.keys()),
            valor_depois=json.dumps(data, ensure_ascii=False, default=str),
            justificativa="Aguardando aprovação do Administrador",
        )
        return self._enrich(usuario)

    def aprovar_edicao(self, usuario_id: int, payload: UsuarioAprovarEdicao, current_user: dict) -> dict:
        if payload.acao not in ACOES_APROVACAO_EDICAO:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ação inválida")

        usuario = self.get(usuario_id)
        if current_user.get("perfil") != "SuperUsuario" and usuario.empresa_id != current_user.get("empresa_id"):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Este usuário não pertence à sua empresa")
        if usuario.edicao_status != "Pendente":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este usuário não possui edição pendente")

        mudancas = json.loads(usuario.dados_pendentes) if usuario.dados_pendentes else {}

        if payload.acao == "Aprovado":
            for campo, valor in mudancas.items():
                setattr(usuario, campo, valor)
            usuario.edicao_status = "Nenhuma"
            usuario.justificativa_edicao = None
        else:
            usuario.edicao_status = "Recusada"
            usuario.justificativa_edicao = payload.justificativa

        usuario.dados_pendentes = None
        usuario.solicitado_em = None
        usuario = self.repo.update(usuario)

        self.audit_service.registrar(
            usuario=current_user,
            modulo="Central de Cadastros",
            tipo_acao=payload.acao,
            nivel="Crítico" if payload.acao == "Recusado" else "Administrativo",
            entidade="Usuario",
            entidade_id=str(usuario.id),
            campo_alterado=",".join(mudancas.keys()),
            valor_depois=json.dumps(mudancas, ensure_ascii=False),
            justificativa=payload.justificativa,
        )
        return self._enrich(usuario)

    def delete(self, usuario_id: int, current_user: dict) -> None:
        usuario = self._get_escopado(usuario_id, current_user)
        self.repo.delete(usuario)
