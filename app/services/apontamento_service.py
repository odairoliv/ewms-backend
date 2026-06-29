from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Apontamento
from app.repositories.apontamento_repository import ApontamentoRepository
from app.schemas.apontamento import (
    ApontamentoAprovarHoras,
    ApontamentoCreate,
    ApontamentoEditarHoras,
    ApontamentoStatusUpdate,
)
from app.services.audit_service import AuditService
from app.services.id_generator import next_id
from app.services.periodo_utils import calcular_semana, data_para_periodo, periodo_para_data

STATUS_VALIDOS = {"Em Análise", "Aprovado", "Recusado"}
ACOES_APROVACAO_HORAS = {"Aprovado", "Recusado"}
PERFIS_QUE_EDITAM_AUTO = {"Administrador", "SuperUsuario"}


class ApontamentoService:
    def __init__(self, db: Session):
        self.repo = ApontamentoRepository(db)
        self.audit_service = AuditService(db)

    def _enrich(self, apontamento: Apontamento) -> dict:
        consultor = apontamento.consultor
        usuario = consultor.usuario if consultor else None
        lideranca_nome = consultor.lideranca.nome if consultor and consultor.lideranca else None
        return {
            "id": apontamento.id,
            "id_consultor": apontamento.id_consultor,
            "nome_consultor": usuario.nome if usuario else None,
            "id_fornecedor": apontamento.id_fornecedor,
            "fornecedor": (
                consultor.fornecedor.razao_social if consultor and consultor.fornecedor else None
            ),
            "lideranca": lideranca_nome,
            "id_projeto": apontamento.id_projeto,
            "nome_projeto": apontamento.nome_projeto,
            "data_reporte": apontamento.data_reporte,
            "semana": apontamento.semana,
            "periodo": data_para_periodo(apontamento.data_reporte),
            "horas_trabalhadas": apontamento.horas_trabalhadas,
            "valor_hora": apontamento.valor_hora,
            "valor_total": apontamento.valor_total,
            "status": apontamento.status,
            "justificativa": apontamento.justificativa,
            "edicao_status": apontamento.edicao_status,
            "horas_pendentes": apontamento.horas_pendentes,
            "solicitado_por": apontamento.solicitado_por,
            "solicitado_em": apontamento.solicitado_em,
            "justificativa_edicao": apontamento.justificativa_edicao,
            "ativo": apontamento.ativo,
            "custom01": apontamento.custom01,
            "custom02": apontamento.custom02,
            "custom03": apontamento.custom03,
            "custom04": apontamento.custom04,
            "criado_em": apontamento.criado_em,
            "atualizado_em": apontamento.atualizado_em,
        }

    def list_for_user(self, current_user: dict, periodo: str | None = None) -> list[dict]:
        perfil = current_user.get("perfil")
        if perfil == "SuperUsuario":
            apontamentos = self.repo.list_all(periodo)
        elif perfil == "Fornecedor":
            apontamentos = self.repo.list_by_fornecedor(current_user.get("id_fornecedor"), periodo)
        elif perfil == "Liderança":
            apontamentos = self.repo.list_by_lideranca(current_user.get("id"), periodo)
        else:
            apontamentos = self.repo.list_by_empresa(current_user.get("empresa_id"), periodo)
        return [self._enrich(a) for a in apontamentos]

    def get(self, apontamento_id: str) -> Apontamento:
        apontamento = self.repo.get_by_id(apontamento_id)
        if not apontamento:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Apontamento não encontrado")
        return apontamento

    def create(self, payload: ApontamentoCreate) -> dict:
        valor_total = (payload.horas_trabalhadas * payload.valor_hora).quantize(Decimal("0.01"))
        novo_id = next_id("APO", self.repo.count())
        data_reporte = periodo_para_data(payload.periodo)
        dados = payload.model_dump(exclude={"periodo"})
        apontamento = Apontamento(
            id=novo_id,
            **dados,
            data_reporte=data_reporte,
            semana=calcular_semana(data_reporte),
            valor_total=valor_total,
        )
        return self._enrich(self.repo.create(apontamento))

    def atualizar_status(
        self, apontamento_id: str, payload: ApontamentoStatusUpdate, current_user: dict
    ) -> dict:
        if payload.status not in STATUS_VALIDOS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Status inválido")
        if payload.status == "Recusado" and not payload.justificativa:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Justificativa é obrigatória para recusar"
            )

        apontamento = self.get(apontamento_id)
        status_anterior = apontamento.status
        apontamento.status = payload.status
        apontamento.justificativa = payload.justificativa
        apontamento = self.repo.update(apontamento)

        self.audit_service.registrar(
            usuario=current_user,
            modulo="Fechamento de Horas",
            tipo_acao=payload.status,
            nivel="Crítico" if payload.status == "Recusado" else "Administrativo",
            entidade="Apontamento",
            entidade_id=apontamento.id,
            campo_alterado="status",
            valor_antes=status_anterior,
            valor_depois=payload.status,
            justificativa=payload.justificativa,
        )
        return self._enrich(apontamento)

    def delete(self, apontamento_id: str, current_user: dict) -> None:
        # Soft delete: nunca remove a linha do banco — apenas marca ativo=False,
        # o que já é suficiente para o registro deixar de aparecer nas listagens do frontend.
        apontamento = self.get(apontamento_id)
        apontamento.ativo = False
        self.repo.update(apontamento)
        self.audit_service.registrar(
            usuario=current_user,
            modulo="Fechamento de Horas",
            tipo_acao="Exclusão",
            nivel="Crítico",
            entidade="Apontamento",
            entidade_id=apontamento.id,
            justificativa="Registro inativado (soft delete) — dado preservado no banco",
        )

    def editar_horas(
        self, apontamento_id: str, payload: ApontamentoEditarHoras, current_user: dict
    ) -> dict:
        apontamento = self.get(apontamento_id)
        perfil = current_user.get("perfil")
        horas_anteriores = apontamento.horas_trabalhadas

        if perfil in PERFIS_QUE_EDITAM_AUTO:
            # Administrador/SuperUsuario: aplica direto, sem aprovação (auto-aprovado).
            apontamento.horas_trabalhadas = payload.horas_trabalhadas
            apontamento.valor_total = (payload.horas_trabalhadas * apontamento.valor_hora).quantize(
                Decimal("0.01")
            )
            apontamento.edicao_status = "Nenhuma"
            apontamento.horas_pendentes = None
            apontamento.solicitado_por = None
            apontamento.solicitado_em = None
            apontamento.justificativa_edicao = None
            apontamento = self.repo.update(apontamento)

            self.audit_service.registrar(
                usuario=current_user,
                modulo="Fechamento de Horas",
                tipo_acao="Edição auto-aprovada",
                nivel="Administrativo",
                entidade="Apontamento",
                entidade_id=apontamento.id,
                campo_alterado="horas_trabalhadas",
                valor_antes=str(horas_anteriores),
                valor_depois=str(payload.horas_trabalhadas),
                justificativa=payload.justificativa,
            )
            return self._enrich(apontamento)

        if perfil != "Liderança":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Seu perfil não pode editar horas de apontamentos"
            )

        # Liderança: fica pendente de aprovação do Administrador/SuperUsuario.
        apontamento.horas_pendentes = payload.horas_trabalhadas
        apontamento.edicao_status = "Pendente"
        apontamento.solicitado_por = current_user.get("email")
        apontamento.solicitado_em = datetime.now(timezone.utc)
        apontamento.justificativa_edicao = None
        apontamento = self.repo.update(apontamento)

        self.audit_service.registrar(
            usuario=current_user,
            modulo="Fechamento de Horas",
            tipo_acao="Solicitação edição horas",
            nivel="Administrativo",
            entidade="Apontamento",
            entidade_id=apontamento.id,
            campo_alterado="horas_trabalhadas",
            valor_antes=str(horas_anteriores),
            valor_depois=str(payload.horas_trabalhadas),
            justificativa="Aguardando aprovação do Administrador",
        )
        return self._enrich(apontamento)

    def aprovar_horas(
        self, apontamento_id: str, payload: ApontamentoAprovarHoras, current_user: dict
    ) -> dict:
        if payload.acao not in ACOES_APROVACAO_HORAS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ação inválida")
        if current_user.get("perfil") not in PERFIS_QUE_EDITAM_AUTO:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Apenas Administrador ou SuperUsuario podem aprovar edições de horas",
            )

        apontamento = self.get(apontamento_id)
        if apontamento.edicao_status != "Pendente":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Este apontamento não possui edição pendente"
            )

        horas_anteriores = apontamento.horas_trabalhadas
        horas_propostas = apontamento.horas_pendentes

        if payload.acao == "Aprovado":
            apontamento.horas_trabalhadas = horas_propostas
            apontamento.valor_total = (horas_propostas * apontamento.valor_hora).quantize(
                Decimal("0.01")
            )
            apontamento.edicao_status = "Nenhuma"
            apontamento.justificativa_edicao = None
        else:
            apontamento.edicao_status = "Recusada"
            apontamento.justificativa_edicao = payload.justificativa

        apontamento.horas_pendentes = None
        apontamento.solicitado_por = None
        apontamento.solicitado_em = None
        apontamento = self.repo.update(apontamento)

        self.audit_service.registrar(
            usuario=current_user,
            modulo="Fechamento de Horas",
            tipo_acao=f"{payload.acao} (edição de horas)",
            nivel="Crítico" if payload.acao == "Recusado" else "Administrativo",
            entidade="Apontamento",
            entidade_id=apontamento.id,
            campo_alterado="horas_trabalhadas",
            valor_antes=str(horas_anteriores),
            valor_depois=str(horas_propostas),
            justificativa=payload.justificativa,
        )
        return self._enrich(apontamento)
