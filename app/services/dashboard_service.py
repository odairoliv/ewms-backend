from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Fornecedor
from app.repositories.apontamento_repository import ApontamentoRepository
from app.services.periodo_utils import periodo_para_data

MESES_ABREV = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.apontamento_repo = ApontamentoRepository(db)

    def resumo(self, current_user: dict, empresa: str | None = None, periodo: str | None = None) -> dict:
        perfil = current_user.get("perfil")

        stmt_fornecedores = select(Fornecedor)
        if perfil != "SuperUsuario":
            stmt_fornecedores = stmt_fornecedores.where(
                Fornecedor.empresa_id == current_user.get("empresa_id")
            )
        fornecedores_escopo = list(self.db.scalars(stmt_fornecedores))
        fornecedores = {f.id: f.razao_social for f in fornecedores_escopo}

        # Filtra já no banco pela empresa do usuário (em vez de trazer todos os
        # apontamentos de todas as empresas e descartar em Python): menos dado trafegado
        # pela rede e menos exposição de dados de outros tenants na memória da aplicação.
        if perfil == "SuperUsuario":
            apontamentos = self.apontamento_repo.list_all()
        else:
            apontamentos = self.apontamento_repo.list_by_empresa(current_user.get("empresa_id"))

        if perfil == "Fornecedor":
            apontamentos = [a for a in apontamentos if a.id_fornecedor == current_user.get("id_fornecedor")]
        elif perfil == "Liderança":
            id_lideranca = current_user.get("id")
            apontamentos = [
                a for a in apontamentos if a.consultor and a.consultor.lideranca_id == id_lideranca
            ]
        elif empresa and empresa != "Todas as empresas":
            fornecedor = next((f for f in fornecedores_escopo if f.razao_social == empresa), None)
            if fornecedor:
                apontamentos = [a for a in apontamentos if a.id_fornecedor == fornecedor.id]

        # A evolução mensal sempre mostra o ano completo, independente do filtro de período —
        # por isso é calculada a partir do escopo (empresa/fornecedor/liderança) antes do
        # filtro de período ser aplicado ao restante dos gráficos.
        horas_por_mes = {mes: 0.0 for mes in MESES_ABREV}
        for apontamento in apontamentos:
            horas_por_mes[MESES_ABREV[apontamento.data_reporte.month - 1]] += float(
                apontamento.horas_trabalhadas
            )

        if periodo:
            data_ref = periodo_para_data(periodo)
            apontamentos = [
                a for a in apontamentos
                if a.data_reporte.year == data_ref.year and a.data_reporte.month == data_ref.month
            ]

        horas_por_fornecedor: dict[str, float] = {}
        horas_por_consultor: dict[str, float] = {}
        horas_por_projeto_total: dict[str, float] = {}

        # Para os gráficos de previsto: soma de horas Aprovadas (realizado) e soma das
        # horas previstas/semana de cada consultor, por semana distinta que trabalhou
        # naquele recorte (projeto ou o próprio terceiro)
        realizado_por_projeto: dict[str, float] = {}
        semanas_por_consultor_e_projeto: dict[str, set] = {}
        semanas_por_consultor: dict[str, set] = {}

        for apontamento in apontamentos:
            nome_fornecedor = fornecedores.get(apontamento.id_fornecedor, apontamento.id_fornecedor)
            horas_por_fornecedor[nome_fornecedor] = (
                horas_por_fornecedor.get(nome_fornecedor, 0) + float(apontamento.horas_trabalhadas)
            )

            usuario_consultor = apontamento.consultor.usuario if apontamento.consultor else None
            nome_terceiro = usuario_consultor.nome if usuario_consultor else apontamento.id_consultor
            horas_por_consultor[nome_terceiro] = (
                horas_por_consultor.get(nome_terceiro, 0) + float(apontamento.horas_trabalhadas)
            )
            semanas_por_consultor.setdefault(nome_terceiro, set()).add(
                (apontamento.id_consultor, apontamento.semana)
            )

            projeto = apontamento.nome_projeto or "Sem projeto"
            horas_por_projeto_total[projeto] = (
                horas_por_projeto_total.get(projeto, 0) + float(apontamento.horas_trabalhadas)
            )
            semanas_por_consultor_e_projeto.setdefault(projeto, set()).add(
                (apontamento.id_consultor, apontamento.semana)
            )
            if apontamento.status == "Aprovado":
                realizado_por_projeto[projeto] = (
                    realizado_por_projeto.get(projeto, 0) + float(apontamento.horas_trabalhadas)
                )

        def _somar_previsto(pares_consultor_semana: set) -> float:
            total_previsto = 0.0
            for id_consultor, _semana in pares_consultor_semana:
                consultor = next(
                    (a.consultor for a in apontamentos if a.id_consultor == id_consultor), None
                )
                if consultor:
                    total_previsto += float(consultor.horas_previstas_semana)
            return total_previsto

        previsto_por_projeto = {
            projeto: _somar_previsto(pares) for projeto, pares in semanas_por_consultor_e_projeto.items()
        }
        previsto_por_consultor = {
            nome: _somar_previsto(pares) for nome, pares in semanas_por_consultor.items()
        }

        horas_por_prestador = sorted(
            ({"prestador": nome, "horas": horas} for nome, horas in horas_por_fornecedor.items()),
            key=lambda item: item["horas"],
            reverse=True,
        )
        horas_por_projeto_lista = sorted(
            ({"projeto": nome, "horas": horas} for nome, horas in horas_por_projeto_total.items()),
            key=lambda item: item["horas"],
            reverse=True,
        )
        previsto_vs_realizado = sorted(
            (
                {
                    "projeto": projeto,
                    "previsto": previsto_por_projeto.get(projeto, 0.0),
                    "realizado": realizado_por_projeto.get(projeto, 0.0),
                }
                for projeto in semanas_por_consultor_e_projeto
            ),
            key=lambda item: item["projeto"],
        )

        # Normal = horas reportadas dentro do previsto para o período filtrado;
        # Extra = horas reportadas que excedem o previsto. Por terceiro (consultor).
        horas_por_tipo = sorted(
            (
                {
                    "terceiro": nome,
                    "normal": min(reportadas, previsto_por_consultor.get(nome, 0.0)),
                    "extra": max(reportadas - previsto_por_consultor.get(nome, 0.0), 0.0),
                }
                for nome, reportadas in horas_por_consultor.items()
            ),
            key=lambda item: item["normal"] + item["extra"],
            reverse=True,
        )

        return {
            "horas_por_prestador": horas_por_prestador,
            "horas_por_projeto": horas_por_projeto_lista,
            "previsto_vs_realizado": previsto_vs_realizado,
            "horas_por_tipo": horas_por_tipo,
            "evolucao_mensal": [{"mes": mes, "horas": horas_por_mes[mes]} for mes in MESES_ABREV],
        }
