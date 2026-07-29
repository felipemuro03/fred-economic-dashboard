import pandas as pd
import requests

_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"


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


def url_serie(codigo) -> str:
    """Link para os dados brutos da série (a BCB não tem uma página de série
    tão amigável quanto o FRED; este link sempre funciona, para qualquer código)."""
    return f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/24?formato=json"
