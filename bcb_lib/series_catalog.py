"""Catálogo de indicadores econômicos do Brasil (API SGS do Banco Central).

Códigos verificados diretamente na API (api.bcb.gov.br) antes de entrar aqui.
"""

CATALOGO = {
    "Juros": [
        {"id": 432, "nome": "Meta Selic definida pelo Copom", "nota": "% a.a.", "destaque": True},
    ],
    "Inflação": [
        {"id": 433, "nome": "IPCA - variação mensal", "nota": "% no mês"},
        {"id": 13522, "nome": "IPCA - acumulado 12 meses", "nota": "%", "destaque": True},
        {"id": 189, "nome": "IGP-M - variação mensal", "nota": "% no mês"},
        {"id": 7478, "nome": "INPC - variação mensal", "nota": "% no mês"},
    ],
    "Atividade": [
        {"id": 24364, "nome": "IBC-Br (Índice de Atividade Econômica do BC)", "nota": "Índice, dessazonalizado", "destaque": True},
    ],
    "Emprego": [
        {"id": 24369, "nome": "Taxa de Desocupação (PNAD Contínua)", "nota": "%, trimestre móvel", "destaque": True},
    ],
    "Endividamento": [
        {"id": 13762, "nome": "Dívida Bruta do Governo Geral", "nota": "% do PIB", "destaque": True},
        {"id": 4536, "nome": "Dívida Líquida do Governo Geral", "nota": "% do PIB"},
        {"id": 5793, "nome": "Resultado Primário - Setor Público Consolidado", "nota": "% do PIB, acumulado 12 meses", "destaque": True},
        {"id": 20622, "nome": "Saldo da Carteira de Crédito em Relação ao PIB", "nota": "%"},
        {"id": 21082, "nome": "Inadimplência da Carteira de Crédito - Total", "nota": "%, atraso acima de 90 dias"},
        {"id": 29034, "nome": "Comprometimento de Renda das Famílias com Serviço da Dívida", "nota": "%, com ajuste sazonal"},
    ],
    "Externo": [
        {"id": 13621, "nome": "Reservas Internacionais", "nota": "US$ milhões"},
        {"id": 22701, "nome": "Transações Correntes", "nota": "US$ milhões, saldo mensal"},
        {"id": 22707, "nome": "Balança Comercial", "nota": "US$ milhões, saldo mensal (Balanço de Pagamentos)"},
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
