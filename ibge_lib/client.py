import pandas as pd
import requests

_VALUES_URL = "https://apisidra.ibge.gov.br/values/t/{tabela}/n1/all/v/{variavel}/p/all"

_MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "março": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}


def buscar_serie(tabela, variavel, inicio=None, fim=None) -> pd.Series:
    """Retorna uma pandas Series com o histórico de uma variável de uma
    tabela do SIDRA/IBGE (API pública, sem necessidade de chave).
    """
    url = _VALUES_URL.format(tabela=tabela, variavel=variavel)
    resposta = requests.get(url, timeout=30)
    resposta.raise_for_status()
    linhas = resposta.json()[1:]  # a primeira linha é o cabeçalho de colunas

    datas, valores = [], []
    for linha in linhas:
        periodo = linha.get("D3N", "")
        partes = periodo.rsplit(" ", 1)
        if len(partes) != 2:
            continue
        nome_mes, ano = partes
        mes_num = _MESES.get(nome_mes.strip().lower())
        if mes_num is None:
            continue
        try:
            valor = float(linha["V"])
        except (ValueError, TypeError):
            continue
        datas.append(pd.Timestamp(year=int(ano), month=mes_num, day=1))
        valores.append(valor)

    serie = pd.Series(valores, index=pd.DatetimeIndex(datas)).sort_index()
    if inicio:
        serie = serie[serie.index >= pd.Timestamp(inicio)]
    if fim:
        serie = serie[serie.index <= pd.Timestamp(fim)]
    return serie


def url_serie(tabela) -> str:
    return f"https://sidra.ibge.gov.br/tabela/{tabela}"
