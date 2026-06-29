from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models import Usuario
from app.repositories.fornecedor_repository import FornecedorRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import LoginRequest, LoginResponse, UsuarioLogado
from app.services.audit_service import AuditService
from app.services.usuario_service import UsuarioService

# Camada 2 de proteção contra força bruta (a 1ª é o limite por IP em /auth/login):
# bloqueio por CONTA — persiste mesmo se o atacante trocar de IP ou o servidor reiniciar.
MAX_TENTATIVAS_LOGIN = 5
BLOQUEIO_MINUTOS = 15


class AuthService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)
        self.fornecedor_repo = FornecedorRepository(db)
        self.audit_service = AuditService(db)
        self.usuario_service = UsuarioService(db)

    def _emitir_login_response(self, usuario: Usuario, impersonado_por: dict | None = None) -> LoginResponse:
        # O perfil que vai no token/sessão é o EFETIVO (Fornecedor/Liderança são automáticos
        # com base em id_fornecedor / tb_consultores — ver UsuarioService.resolver_perfil).
        perfil_efetivo = self.usuario_service.resolver_perfil(usuario)
        token_payload = {
            "sub": str(usuario.id),
            "id": usuario.id,
            "email": usuario.email,
            "perfil": perfil_efetivo,
            "id_fornecedor": usuario.id_fornecedor,
            "empresa_id": usuario.empresa_id,
        }
        if impersonado_por:
            token_payload["impersonado_por"] = impersonado_por.get("email")
        access_token = create_access_token(token_payload)

        if usuario.id_fornecedor:
            fornecedor = self.fornecedor_repo.get_by_id(usuario.id_fornecedor)
            empresa_nome = fornecedor.razao_social if fornecedor else None
        else:
            empresa_nome = usuario.empresa.nome if usuario.empresa else None

        return LoginResponse(
            access_token=access_token,
            usuario=UsuarioLogado(
                id=usuario.id,
                nome=usuario.nome,
                email=usuario.email,
                perfil=perfil_efetivo,
                id_fornecedor=usuario.id_fornecedor,
                empresa_id=usuario.empresa_id,
                empresa=empresa_nome,
            ),
        )

    def login(self, payload: LoginRequest) -> LoginResponse:
        usuario = self.repo.get_by_email(payload.email)

        if usuario and usuario.bloqueado_until:
            agora = datetime.now(timezone.utc)
            bloqueado_until = usuario.bloqueado_until
            if bloqueado_until.tzinfo is None:
                bloqueado_until = bloqueado_until.replace(tzinfo=timezone.utc)
            if bloqueado_until > agora:
                minutos_restantes = max(1, int((bloqueado_until - agora).total_seconds() // 60) + 1)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Conta temporariamente bloqueada por excesso de tentativas. "
                    f"Tente novamente em {minutos_restantes} minuto(s).",
                )
            # Bloqueio expirou — libera e zera o contador antes de seguir com a validação normal.
            usuario.bloqueado_until = None
            usuario.tentativas_login_falhas = 0
            self.repo.update(usuario)

        if not usuario or not verify_password(payload.senha, usuario.senha_hash):
            if usuario:
                usuario.tentativas_login_falhas += 1
                if usuario.tentativas_login_falhas >= MAX_TENTATIVAS_LOGIN:
                    usuario.bloqueado_until = datetime.now(timezone.utc) + timedelta(minutes=BLOQUEIO_MINUTOS)
                    usuario.tentativas_login_falhas = 0
                    self.repo.update(usuario)
                    self.audit_service.registrar(
                        usuario={"nome": usuario.nome, "email": usuario.email, "empresa_id": usuario.empresa_id},
                        modulo="Segurança",
                        tipo_acao="Bloqueio de conta",
                        nivel="Crítico",
                        entidade="Usuario",
                        entidade_id=str(usuario.id),
                        justificativa=f"{MAX_TENTATIVAS_LOGIN} tentativas de login com senha incorreta",
                    )
                else:
                    self.repo.update(usuario)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha inválidos",
            )

        if usuario.tentativas_login_falhas > 0:
            usuario.tentativas_login_falhas = 0
            self.repo.update(usuario)

        if usuario.status != "Ativo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo",
            )
        return self._emitir_login_response(usuario)

    def impersonar(self, usuario_id: int, current_user: dict) -> LoginResponse:
        usuario = self.repo.get_by_id(usuario_id)
        if not usuario:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")
        if usuario.perfil == "SuperUsuario":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Não é possível simular outro SuperUsuario"
            )
        if usuario.status != "Ativo":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Usuário inativo")

        self.audit_service.registrar(
            usuario=current_user,
            modulo="Segurança",
            tipo_acao="Impersonação",
            nivel="Crítico",
            entidade="Usuario",
            entidade_id=str(usuario.id),
            justificativa=f"SuperUsuario acessou o sistema como {usuario.email}",
        )
        return self._emitir_login_response(usuario, impersonado_por=current_user)
