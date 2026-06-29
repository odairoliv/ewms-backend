from datetime import date

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
MESES_PT_INDEX = {nome.lower(): i + 1 for i, nome in enumerate(MESES_PT)}


def periodo_atual() -> str:
    hoje = date.today()
    return f"{MESES_PT[hoje.month - 1]}/{hoje.year}"


def periodo_para_data(periodo: str) -> date:
    """Converte 'Maio/2026' ou '05/2026' no primeiro dia daquele mês (data_reporte)."""
    try:
        parte_mes, ano = periodo.split("/")
        parte_mes = parte_mes.strip()
        mes = int(parte_mes) if parte_mes.isdigit() else MESES_PT_INDEX[parte_mes.lower()]
        return date(int(ano), mes, 1)
    except (ValueError, KeyError, AttributeError):
        raise ValueError(
            f"Período inválido: {periodo!r}. Use o formato 'Mês/Ano' ou 'MM/AAAA', ex: 'Maio/2026' ou '05/2026'."
        )


def data_para_periodo(data_reporte: date) -> str:
    return f"{MESES_PT[data_reporte.month - 1]}/{data_reporte.year}"


def calcular_semana(data_reporte: date) -> str:
    """Formato S{semana ISO com 2 dígitos}{ano ISO}, ex: S252026."""
    ano_iso, semana_iso, _ = data_reporte.isocalendar()
    return f"S{semana_iso:02d}{ano_iso}"
