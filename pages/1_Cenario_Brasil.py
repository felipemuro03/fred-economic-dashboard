import sys
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ_PROJETO))

from bcb_lib import client, series_catalog
from fred_lib import excel_export, formatos, html_export
from ibge_lib import client as ibge_client

st.set_page_config(page_title="Cenário Econômico Brasil", layout="wide", page_icon="🇧🇷")

NAVY = "#102134"
GOLD = "#BAA377"
GOLD_ESCURO = "#896F3D"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Montserrat', Arial, sans-serif;
    }}
    h1, h2, h3 {{
        font-weight: 600 !important;
        color: {NAVY};
    }}
    [data-testid="stMetricLabel"] {{
        font-weight: 600;
        color: {NAVY};
    }}
    [data-testid="stMetricValue"] {{
        color: {NAVY};
    }}
    [data-testid="stSidebar"] {{
        background-color: {NAVY};
    }}
    [data-testid="stSidebar"] * {{
        color: #FFFFFF !important;
    }}
    .stButton > button, .stDownloadButton > button {{
        background-color: {GOLD};
        color: {NAVY};
        border: none;
        font-weight: 600;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        background-color: {GOLD_ESCURO};
        color: #FFFFFF;
    }}
    .stTabs [aria-selected="true"] {{
        color: {GOLD_ESCURO};
        border-bottom-color: {GOLD_ESCURO} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

if "selecionadas_br" not in st.session_state:
    st.session_state.selecionadas_br = {}


@st.cache_data(ttl=3600, show_spinner="Buscando dados no Banco Central...")
def _buscar_serie_cache(codigo, inicio, fim):
    return client.buscar_serie(codigo, inicio=inicio, fim=fim)


@st.cache_data(ttl=3600, show_spinner="Buscando dados no IBGE...")
def _buscar_ibge_cache(tabela, variavel, inicio, fim):
    return ibge_client.buscar_serie(tabela, variavel, inicio=inicio, fim=fim)


def _buscar_indicador(s, inicio):
    """Busca a série de um indicador do catálogo: direta (id, BCB) ou via IBGE (fonte="ibge")."""
    if s.get("fonte") == "ibge":
        return _buscar_ibge_cache(s["tabela"], s["variavel"], inicio, None)
    return _buscar_serie_cache(s["id"], inicio, None)


def _url_indicador(s):
    if s.get("fonte") == "ibge":
        return ibge_client.url_serie(s["tabela"])
    return series_catalog.url_serie(s["id"])


@st.cache_data(ttl=3600, show_spinner="Pesquisando séries...")
def _pesquisar_cache(termo):
    return client.pesquisar_series(termo)


def _inferir_unidade(texto_unidade: str) -> dict:
    """Melhor esforço pra séries achadas pelo Explorador, fora do catálogo curado."""
    texto = (texto_unidade or "").lower()
    if "percentual" in texto or texto.strip() == "%":
        return {"badge": texto_unidade or "%", "tipo": "percentual"}
    if "real" in texto or "r$" in texto:
        return {"badge": texto_unidade, "tipo": "moeda", "simbolo": "R$"}
    if "dólar" in texto or "dolar" in texto or "us$" in texto:
        return {"badge": texto_unidade, "tipo": "moeda", "simbolo": "US$"}
    return {"badge": texto_unidade or "Número", "tipo": "numero"}


def _grafico_linha(serie, altura=150):
    fig = go.Figure(
        go.Scatter(x=serie.index, y=serie.values, mode="lines", line=dict(color=GOLD_ESCURO, width=2))
    )
    fig.update_layout(
        height=altura,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    caminho_logo = RAIZ_PROJETO / "assets" / "logo_swm.png"
    if caminho_logo.exists():
        st.image(str(caminho_logo), width=90)
with col_titulo:
    st.title("Cenário Econômico do Brasil")
    st.caption("Dados oficiais via Banco Central do Brasil (SGS)")

with st.sidebar:
    st.header("Período")
    anos_atras = st.slider("Anos de histórico", 1, 30, 10, key="anos_br")
    inicio = date.today() - timedelta(days=365 * anos_atras)
    st.caption(f"Desde {inicio.strftime('%d/%m/%Y')}")

    if st.button("🔄 Limpar cache e buscar dados novos", key="limpar_cache_br"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.header(f"Selecionados para exportar ({len(st.session_state.selecionadas_br)})")
    for sid, dados in list(st.session_state.selecionadas_br.items()):
        col1, col2 = st.columns([4, 1])
        col1.write(dados["nome"])
        if col2.button("✖", key=f"remover_br_{sid}"):
            del st.session_state.selecionadas_br[sid]
            st.rerun()

aba_overview, aba_explorador, aba_exportar = st.tabs(
    ["Visão Geral", "Explorador", "Exportar"]
)

with aba_overview:
    st.subheader("Resumo — principais indicadores")
    linhas_resumo = []
    for s in series_catalog.listar_destaques():
        try:
            serie = _buscar_indicador(s, inicio).dropna()
        except Exception:
            continue
        if serie.empty:
            continue
        unidade = s.get("unidade", {})
        ultimo = serie.iloc[-1]
        anterior = serie.iloc[-2] if len(serie) > 1 else ultimo
        linhas_resumo.append(
            {
                "Indicador": s["nome"],
                "Categoria": s["categoria"],
                "Unidade": formatos.badge_unidade(unidade),
                "Valor": formatos.formatar_valor(ultimo, unidade),
                "Variação": formatos.formatar_delta(ultimo - anterior, unidade),
                "Dado de": serie.index[-1].strftime("%d/%m/%Y"),
            }
        )

    if linhas_resumo:
        df_resumo = pd.DataFrame(linhas_resumo)
        estilo = df_resumo.style.map(
            lambda v: f"color: {'#1E7D32' if not str(v).startswith('-') else '#C62828'}; font-weight: 600",
            subset=["Variação"],
        )
        st.dataframe(estilo, use_container_width=True, hide_index=True)

    st.divider()

    COLUNAS_POR_LINHA = 3
    for categoria, series in series_catalog.CATALOGO.items():
        st.subheader(categoria)
        linhas = [
            series[i : i + COLUNAS_POR_LINHA]
            for i in range(0, len(series), COLUNAS_POR_LINHA)
        ]
        for linha in linhas:
            cols = st.columns(COLUNAS_POR_LINHA)
            for col, s in zip(cols, linha):
                with col:
                    try:
                        serie = _buscar_indicador(s, inicio).dropna()
                    except Exception as e:
                        st.error(f"Erro ao buscar {s['id']}: {e}")
                        continue
                    if serie.empty:
                        st.warning(f"Sem dados para {s['id']}")
                        continue

                    unidade = s.get("unidade", {})
                    st.markdown(f"**{s['nome']}**")
                    ultimo = serie.iloc[-1]
                    anterior = serie.iloc[-2] if len(serie) > 1 else ultimo
                    st.metric(
                        label="",
                        value=formatos.formatar_valor(ultimo, unidade),
                        delta=formatos.formatar_delta(ultimo - anterior, unidade),
                        label_visibility="collapsed",
                    )
                    st.caption(f"📅 Dado de: {serie.index[-1].strftime('%d/%m/%Y')}")
                    st.plotly_chart(
                        _grafico_linha(serie, altura=220),
                        use_container_width=True,
                        key=f"chart_br_{s['id']}",
                    )
                    nota_texto = f"{s['nota']} · " if s["nota"] else ""
                    st.caption(f"{nota_texto}Unidade: {formatos.badge_unidade(unidade)}")
                    st.caption(f"[Ver dados brutos ↗]({_url_indicador(s)})")
                    if st.button("➕ Adicionar à exportação", key=f"add_br_{s['id']}"):
                        st.session_state.selecionadas_br[str(s["id"])] = {
                            "nome": s["nome"],
                            "serie": serie,
                            "nota": s["nota"],
                            "url": _url_indicador(s),
                            "categoria": categoria,
                            "unidade": unidade,
                        }
                        st.rerun()
        st.divider()

with aba_explorador:
    st.subheader("Pesquisar qualquer série do Banco Central")
    termo = st.text_input(
        "Palavra-chave (ex: 'dívida', 'crédito', 'inadimplência', 'salário')",
        key="termo_busca_br",
    )
    if termo:
        try:
            resultados = _pesquisar_cache(termo)
        except Exception as e:
            st.error(f"Erro na busca: {e}")
            resultados = []

        if not resultados:
            st.info("Nenhuma série encontrada.")
        else:
            for r in resultados:
                with st.expander(f"{r['titulo']} ({r['id']})"):
                    st.caption(f"Unidade: {r['unidade'] or '-'}")
                    st.caption(f"[Ver dados brutos ↗]({series_catalog.url_serie(r['id'])})")
                    if st.button("Ver gráfico e adicionar", key=f"explorar_br_{r['id']}"):
                        try:
                            serie = _buscar_serie_cache(r["id"], inicio, None).dropna()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                            serie = None
                        if serie is not None and not serie.empty:
                            st.plotly_chart(
                                _grafico_linha(serie),
                                use_container_width=True,
                                key=f"explorar_br_chart_{r['id']}",
                            )
                            st.session_state.selecionadas_br[str(r["id"])] = {
                                "nome": r["titulo"],
                                "serie": serie,
                                "nota": "",
                                "url": series_catalog.url_serie(r["id"]),
                                "unidade": _inferir_unidade(r["unidade"]),
                            }
                            st.success("Adicionado à exportação.")

    st.divider()
    st.subheader("Ou digite o código SGS diretamente")
    codigo_input = st.text_input("Código SGS", key="codigo_sgs_input")
    if codigo_input:
        try:
            codigo = int(codigo_input)
        except ValueError:
            st.error("Digite apenas o número do código.")
            codigo = None

        if codigo is not None:
            try:
                serie = _buscar_serie_cache(codigo, inicio, None).dropna()
            except Exception as e:
                st.error(f"Erro ao buscar a série {codigo}: {e}")
                serie = None

            if serie is not None and serie.empty:
                st.warning("Código válido, mas sem dados retornados nesse período.")
            elif serie is not None:
                st.plotly_chart(
                    _grafico_linha(serie, altura=300),
                    use_container_width=True,
                    key=f"consulta_chart_{codigo}",
                )
                st.caption(f"[Ver dados brutos ↗]({series_catalog.url_serie(codigo)})")
                nome_manual = st.text_input(
                    "Nome para exibir na exportação", value=f"Série SGS {codigo}"
                )
                if st.button("➕ Adicionar à exportação", key=f"add_consulta_{codigo}"):
                    st.session_state.selecionadas_br[str(codigo)] = {
                        "nome": nome_manual,
                        "serie": serie,
                        "nota": "",
                        "url": series_catalog.url_serie(codigo),
                    }
                    st.success("Adicionado à exportação.")

with aba_exportar:
    st.subheader("Relatório completo (HTML)")
    st.caption(
        "Traz todos os indicadores do catálogo brasileiro, organizados por "
        "categoria — ideal para compartilhar o cenário inteiro com a equipe."
    )
    if st.button("Gerar Relatório HTML Completo", key="gerar_html_br"):
        todas_series = {}
        with st.spinner("Buscando todos os indicadores no Banco Central..."):
            for categoria, series in series_catalog.CATALOGO.items():
                for s in series:
                    try:
                        serie = _buscar_indicador(s, inicio).dropna()
                    except Exception:
                        continue
                    if serie.empty:
                        continue
                    todas_series[str(s["id"])] = {
                        "nome": s["nome"],
                        "serie": serie,
                        "nota": s["nota"],
                        "url": _url_indicador(s),
                        "categoria": categoria,
                        "unidade": s.get("unidade", {}),
                    }

        caminho = RAIZ_PROJETO / "cenario_economico_brasil.html"
        gerado_em = date.today().strftime("%d/%m/%Y")
        html_export.exportar_html(
            todas_series,
            str(caminho),
            gerado_em,
            titulo="Cenário Econômico do Brasil",
            fonte="Banco Central do Brasil (SGS)",
        )
        with open(caminho, "rb") as f:
            st.download_button(
                "⬇️ Baixar HTML (envie por e-mail/Teams)",
                f,
                file_name="cenario_economico_brasil.html",
                mime="text/html",
                key="download_html_br",
            )

    st.divider()

    st.subheader("Excel com indicadores selecionados")
    if not st.session_state.selecionadas_br:
        st.info(
            "Nenhuma série selecionada ainda. Adicione pela Visão Geral ou pelo Explorador."
        )
    else:
        st.write(f"{len(st.session_state.selecionadas_br)} série(s) selecionada(s):")
        for sid, dados in st.session_state.selecionadas_br.items():
            st.write(f"- {dados['nome']} ({sid})")

        if st.button("Gerar Excel", key="gerar_excel_br"):
            caminho = RAIZ_PROJETO / "cenario_economico_brasil.xlsx"
            excel_export.exportar_excel(
                st.session_state.selecionadas_br, str(caminho), rotulo_codigo="Código SGS"
            )
            with open(caminho, "rb") as f:
                st.download_button(
                    "⬇️ Baixar Excel",
                    f,
                    file_name="cenario_economico_brasil.xlsx",
                    key="download_excel_br",
                )
