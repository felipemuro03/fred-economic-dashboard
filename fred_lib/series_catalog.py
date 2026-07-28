"""Catálogo curado dos principais indicadores econômicos dos EUA (FRED).

Nomes seguem o título oficial da série no FRED. Séries com "tipo": "indice"
são índices de base 100 (ex: CPI, PCE) — no dashboard são exibidas como
variação % em 12 meses, não como nível bruto.
"""

CATALOGO = {
    "Crescimento": [
        {"id": "GDPC1", "nome": "Real Gross Domestic Product", "nota": "Trimestral, taxa anualizada"},
        {"id": "INDPRO", "nome": "Industrial Production: Total Index", "nota": "Mensal", "tipo": "indice"},
    ],
    "Inflação": [
        {"id": "CPIAUCSL", "nome": "Consumer Price Index for All Urban Consumers: All Items in U.S. City Average", "nota": "Mensal", "tipo": "indice"},
        {"id": "CPILFESL", "nome": "Consumer Price Index for All Urban Consumers: All Items Less Food and Energy in U.S. City Average", "nota": "Mensal (Core CPI)", "tipo": "indice"},
        {"id": "PCEPI", "nome": "Personal Consumption Expenditures: Chain-type Price Index", "nota": "Mensal, métrica preferida do Fed", "tipo": "indice"},
        {"id": "PCEPILFE", "nome": "Personal Consumption Expenditures Excluding Food and Energy (Chain-Type Price Index)", "nota": "Mensal (Core PCE)", "tipo": "indice"},
    ],
    "Emprego": [
        {"id": "UNRATE", "nome": "Unemployment Rate", "nota": "Mensal, %"},
        {"id": "PAYEMS", "nome": "All Employees, Total Nonfarm", "nota": "Mensal, milhares de vagas"},
        {"id": "ICSA", "nome": "Initial Claims", "nota": "Semanal"},
        {"id": "CIVPART", "nome": "Labor Force Participation Rate", "nota": "Mensal, %"},
    ],
    "Juros": [
        {"id": "FEDFUNDS", "nome": "Federal Funds Effective Rate", "nota": "Mensal, %"},
        {"id": "DGS10", "nome": "Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity", "nota": "Diário, %"},
        {"id": "DGS2", "nome": "Market Yield on U.S. Treasury Securities at 2-Year Constant Maturity", "nota": "Diário, %"},
        {"id": "T10Y2Y", "nome": "10-Year Treasury Constant Maturity Minus 2-Year Treasury Constant Maturity", "nota": "Diário, indicador de curva/recessão"},
    ],
    "Consumo": [
        {"id": "UMCSENT", "nome": "University of Michigan: Consumer Sentiment", "nota": "Mensal, nível do índice"},
        {"id": "RSAFS", "nome": "Advance Retail Sales: Retail Trade and Food Services", "nota": "Mensal, US$"},
        {"id": "PCE", "nome": "Personal Consumption Expenditures", "nota": "Mensal, US$"},
    ],
    "Moradia": [
        {"id": "HOUST", "nome": "New Privately-Owned Housing Units Started: Total Units", "nota": "Mensal, mil unidades anualizadas"},
        {"id": "MORTGAGE30US", "nome": "30-Year Fixed Rate Mortgage Average in the United States", "nota": "Semanal, %"},
        {"id": "CSUSHPISA", "nome": "S&P/Case-Shiller U.S. National Home Price Index", "nota": "Mensal", "tipo": "indice"},
    ],
    "Mercados": [
        {"id": "SP500", "nome": "S&P 500", "nota": "Diário, pontos"},
        {"id": "M2SL", "nome": "M2", "nota": "Mensal, US$ bi"},
        {"id": "DTWEXBGS", "nome": "Nominal Broad U.S. Dollar Index", "nota": "Diário", "tipo": "indice"},
    ],
}


def url_serie(series_id: str) -> str:
    return f"https://fred.stlouisfed.org/series/{series_id}"


def listar_todas_series():
    """Retorna lista achatada de todas as séries do catálogo, com categoria."""
    achatado = []
    for categoria, series in CATALOGO.items():
        for s in series:
            achatado.append({**s, "categoria": categoria})
    return achatado
