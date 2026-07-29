"""Catálogo de indicadores econômicos do Brasil (API SGS do Banco Central).

Códigos verificados diretamente na API (api.bcb.gov.br) antes de entrar aqui.

"unidade" descreve como formatar valor/variação (ver fred_lib/formatos.py) e
qual selo de unidade mostrar (ex: "%", "US$ milhões").
"""

_PCT = {"badge": "%", "tipo": "percentual"}
_PCT_PIB = {"badge": "% do PIB", "tipo": "percentual"}
_USD_MI = {"badge": "US$ milhões", "tipo": "moeda", "simbolo": "US$"}

CATALOGO = {
    "Juros": [
        {"id": 432, "nome": "Meta Selic definida pelo Copom", "nota": "% a.a.", "destaque": True, "unidade": _PCT},
    ],
    "Inflação": [
        {"id": "ipca_mensal_ibge", "fonte": "ibge", "tabela": 1737, "variavel": 63, "nome": "IPCA - Variação Mensal", "nota": "Fonte: IBGE (oficial)", "unidade": _PCT},
        {"id": "ipca_12m_ibge", "fonte": "ibge", "tabela": 1737, "variavel": 2265, "nome": "IPCA - Acumulado 12 Meses", "nota": "Fonte: IBGE (oficial)", "destaque": True, "unidade": _PCT},
        {"id": "ipca15_mensal_ibge", "fonte": "ibge", "tabela": 3065, "variavel": 355, "nome": "IPCA-15 - Variação Mensal (prévia)", "nota": "Fonte: IBGE (oficial) — prévia do IPCA, sai ~10 dias antes", "destaque": True, "unidade": _PCT},
        {"id": "ipca15_12m_ibge", "fonte": "ibge", "tabela": 3065, "variavel": 1120, "nome": "IPCA-15 - Acumulado 12 Meses (prévia)", "nota": "Fonte: IBGE (oficial) — prévia do IPCA", "unidade": _PCT},
        {"id": 189, "nome": "IGP-M - variação mensal", "nota": "% no mês", "unidade": _PCT},
        {"id": 7478, "nome": "INPC - variação mensal", "nota": "% no mês", "unidade": _PCT},
    ],
    "Atividade": [
        {"id": 24364, "nome": "IBC-Br (Índice de Atividade Econômica do BC)", "nota": "Dessazonalizado", "destaque": True, "unidade": {"badge": "Índice", "tipo": "numero"}},
    ],
    "Emprego": [
        {"id": 24369, "nome": "Taxa de Desocupação (PNAD Contínua)", "nota": "Trimestre móvel", "destaque": True, "unidade": _PCT},
    ],
    "Endividamento": [
        {"id": 13762, "nome": "Dívida Bruta do Governo Geral", "nota": "Metodologia atual (desde 2008)", "destaque": True, "unidade": _PCT_PIB},
        {"id": 4536, "nome": "Dívida Líquida do Governo Geral", "nota": "", "unidade": _PCT_PIB},
        {"id": 5793, "nome": "Resultado Primário - Setor Público Consolidado", "nota": "Acumulado 12 meses", "destaque": True, "unidade": _PCT_PIB},
        {"id": 20622, "nome": "Saldo da Carteira de Crédito em Relação ao PIB", "nota": "", "unidade": _PCT_PIB},
        {"id": 21082, "nome": "Inadimplência da Carteira de Crédito - Total", "nota": "Atraso acima de 90 dias", "unidade": _PCT},
        {"id": 29034, "nome": "Comprometimento de Renda das Famílias com Serviço da Dívida", "nota": "Com ajuste sazonal", "unidade": _PCT},
        {"id": 4177, "nome": "Dívida Mobiliária Federal - Participação Over/Selic", "nota": "% da dívida em carteira, por indexador", "destaque": True, "unidade": _PCT},
        {"id": 4178, "nome": "Dívida Mobiliária Federal - Participação Prefixado", "nota": "% da dívida em carteira, por indexador", "destaque": True, "unidade": _PCT},
        {"id": "ntnb_ipca_pct", "nome": "Dívida Mobiliária Federal - Participação IPCA (NTN-B)", "nota": "Calculado: saldo NTN-B (10642) ÷ saldo total em mercado (4154) — o BCB não publica um % pronto para esse indexador na série de participação", "formula": (10642, 4154), "destaque": True, "unidade": _PCT},
    ],
    "Externo": [
        {"id": 13621, "nome": "Reservas Internacionais", "nota": "Conceito caixa", "unidade": _USD_MI},
        {"id": 22701, "nome": "Transações Correntes", "nota": "Saldo mensal", "unidade": _USD_MI},
        {"id": 22707, "nome": "Balança Comercial", "nota": "Saldo mensal (Balanço de Pagamentos)", "unidade": _USD_MI},
    ],
}


def url_serie(codigo) -> str:
    return f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/24?formato=json"


def listar_todas_series():
    """Retorna lista achatada de todas as séries do catálogo, com categoria."""
    achatado = []
    for categoria, series in CATALOGO.items():
        for s in series:
            achatado.append({**s, "categoria": categoria})
    return achatado


def listar_destaques():
    """Retorna as séries marcadas como "destaque": True (resumo dos principais)."""
    return [s for s in listar_todas_series() if s.get("destaque")]
