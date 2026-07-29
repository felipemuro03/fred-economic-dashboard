import pandas as pd
import requests

_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
_BUSCA_URL = "https://dadosabertos.bcb.gov.br/api/3/action/package_search"


def buscar_serie(codigo, inicio=None, fim=None) -> pd.Series:
    """Retorna uma pandas Series com o histórico de uma série do SGS/BCB.

    A API do Banco Central é pública e não exige chave de acesso.
    """
    params = {"formato": "json"}
    if inicio:
        params["dataInicial"] = inicio.strftime("%d/%m/%Y")
    if fim:
        params["dataFinal"] = fim.strftime("%d/%m/%Y")

    resposta = requests.get(_BASE_URL.format(codigo=codigo), params=params, timeout=20)
    resposta.raise_for_status()
    dados = resposta.json()
    if not dados:
        return pd.Series(dtype=float)

    df = pd.DataFrame(dados)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = df["valor"].astype(float)
    return df.set_index("data")["valor"]


def pesquisar_series(termo: str, limite: int = 20) -> list:
    """Pesquisa séries do SGS por palavra-chave, via o portal de dados abertos do BCB.

    Retorna uma lista de dicts {"id": codigo_sgs (int), "titulo": str, "unidade": str}.
    Datasets do portal que não correspondem a uma série numérica simples do SGS
    (sem "codigo_sgs" nos metadados) são descartados.
    """
    resposta = requests.get(
        _BUSCA_URL, params={"q": termo, "rows": limite}, timeout=20
    )
    resposta.raise_for_status()
    corpo = resposta.json()
    if not corpo.get("success"):
        return []

    resultados = []
    for item in corpo["result"]["results"]:
        codigo_sgs = item.get("codigo_sgs")
        if not codigo_sgs:
            continue
        try:
            codigo = int(codigo_sgs)
        except ValueError:
            continue
        resultados.append(
            {
                "id": codigo,
                "titulo": item.get("title", f"Série {codigo}"),
                "unidade": item.get("unidade_medida", ""),
            }
        )
    return resultados


def url_serie(codigo) -> str:
    """Link para os dados brutos da série (a BCB não tem uma página de série
    tão amigável quanto o FRED; este link sempre funciona, para qualquer código)."""
    return f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/24?formato=json"
