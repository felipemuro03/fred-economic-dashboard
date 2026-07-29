import sys
from pathlib import Path
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

RAIZ_PROJETO = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ_PROJETO))

from fred_lib import client, excel_export, html_export
from fred_lib.series_catalog import CATALOGO, listar_destaques, url_serie

st.set_page_config(page_title="Cenário Econômico EUA", layout="wide", page_icon="📊")

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

try:
    client.obter_cliente()
except RuntimeError as e:
    st.error(str(e))
    st.stop()

if "selecionadas" not in st.session_state:
    st.session_state.selecionadas = {}


@st.cache_data(ttl=3600, show_spinner="Buscando dados no FRED...")
def _buscar_serie_cache(series_id, inicio, fim, unidades=None):
    return client.buscar_serie(series_id, inicio=inicio, fim=fim, unidades=unidades)


@st.cache_data(ttl=3600, show_spinner="Pesquisando séries...")
def _pesquisar_cache(termo):
    return client.pesquisar_series(termo)


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
    st.title("Cenário Econômico dos EUA")
    st.caption("Dados oficiais via FRED (Federal Reserve Economic Data)")

with st.sidebar:
    st.header("Período")
    anos_atras = st.slider("Anos de histórico", 1, 30, 10)
    inicio = date.today() - timedelta(days=365 * anos_atras)
    st.caption(f"Desde {inicio.strftime('%d/%m/%Y')}")

    if st.button("🔄 Limpar cache e buscar dados novos"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.header(f"Selecionados para exportar ({len(st.session_state.selecionadas)})")
    for sid, dados in list(st.session_state.selecionadas.items()):
        col1, col2 = st.columns([4, 1])
        col1.write(dados["nome"])
        if col2.button("✖", key=f"remover_{sid}"):
            del st.session_state.selecionadas[sid]
            st.rerun()

aba_overview, aba_explorador, aba_exportar = st.tabs(
    ["Visão Geral", "Explorador", "Exportar"]
)

with aba_overview:
    st.subheader("Resumo — principais indicadores")
    linhas_resumo = []
    for s in listar_destaques():
        e_indice = s.get("tipo") == "indice"
        try:
            serie = _buscar_serie_cache(
                s["id"], inicio, None, "pc1" if e_indice else None
            ).dropna()
        except Exception:
            continue
        if serie.empty:
            continue
        sufixo = "%" if e_indice else ""
        ultimo = serie.iloc[-1]
        anterior = serie.iloc[-2] if len(serie) > 1 else ultimo
        linhas_resumo.append(
            {
                "Indicador": s["nome"],
                "Categoria": s["categoria"],
                "Valor": f"{ultimo:,.2f}{sufixo}",
                "Variação": ultimo - anterior,
            }
        )

    if linhas_resumo:
        df_resumo = pd.DataFrame(linhas_resumo)
        estilo = df_resumo.style.format({"Variação": "{:+,.2f}"}).map(
            lambda v: f"color: {'#1E7D32' if v >= 0 else '#C62828'}; font-weight: 600",
            subset=["Variação"],
        )
        st.dataframe(estilo, use_container_width=True, hide_index=True)

    st.divider()

    for categoria, series in CATALOGO.items():
        st.subheader(categoria)
        cols = st.columns(len(series))
        for col, s in zip(cols, series):
            with col:
                e_indice = s.get("tipo") == "indice"
                try:
                    serie_exibida = _buscar_serie_cache(
                        s["id"], inicio, None, "pc1" if e_indice else None
                    ).dropna()
                except Exception as e:
                    st.error(f"Erro ao buscar {s['id']}: {e}")
                    continue
                if serie_exibida.empty:
                    st.warning(f"Sem dados para {s['id']}")
                    continue

                sufixo = "%" if e_indice else ""
                legenda = (
                    "Variação % vs. 12 meses atrás (units=pc1, cálculo oficial do FRED)"
                    if e_indice
                    else s["nota"]
                )

                st.markdown(f"**{s['nome']}**")
                ultimo = serie_exibida.iloc[-1]
                anterior = serie_exibida.iloc[-2] if len(serie_exibida) > 1 else ultimo
                st.metric(
                    label="",
                    value=f"{ultimo:,.2f}{sufixo}",
                    delta=f"{ultimo - anterior:,.2f}",
                    label_visibility="collapsed",
                )
                st.plotly_chart(
                    _grafico_linha(serie_exibida),
                    use_container_width=True,
                    key=f"chart_{s['id']}",
                )
                st.caption(legenda)
                st.caption(f"[Ver no FRED ↗]({url_serie(s['id'])})")
                if st.button("➕ Adicionar à exportação", key=f"add_{s['id']}"):
                    st.session_state.selecionadas[s["id"]] = {
                        "nome": s["nome"],
                        "serie": serie_exibida,
                        "nota": legenda,
                        "url": url_serie(s["id"]),
                    }
                    st.rerun()

with aba_explorador:
    st.subheader("Pesquisar qualquer série do FRED")
    termo = st.text_input(
        "Palavra-chave (ex: 'unemployment', 'oil price', 'housing')"
    )
    if termo:
        try:
            resultados = _pesquisar_cache(termo)
        except Exception as e:
            st.error(f"Erro na busca: {e}")
            resultados = None

        if resultados is None or resultados.empty:
            st.info("Nenhuma série encontrada.")
        else:
            for series_id, linha in resultados.iterrows():
                titulo = linha.get("title", series_id)
                with st.expander(f"{titulo} ({series_id})"):
                    st.caption(
                        f"Frequência: {linha.get('frequency', '-')} | "
                        f"Unidade: {linha.get('units', '-')}"
                    )
                    st.caption(f"[Ver no FRED ↗]({url_serie(series_id)})")
                    if st.button("Ver gráfico e adicionar", key=f"explorar_{series_id}"):
                        try:
                            serie = _buscar_serie_cache(series_id, inicio, None).dropna()
                        except Exception as e:
                            st.error(f"Erro: {e}")
                            serie = None
                        if serie is not None and not serie.empty:
                            st.plotly_chart(
                                _grafico_linha(serie),
                                use_container_width=True,
                                key=f"explorar_chart_{series_id}",
                            )
                            st.session_state.selecionadas[series_id] = {
                                "nome": titulo,
                                "serie": serie,
                                "nota": linha.get("units", ""),
                                "url": url_serie(series_id),
                            }
                            st.success("Adicionado à exportação.")

with aba_exportar:
    st.subheader("Relatório completo (HTML)")
    st.caption(
        "Traz todos os indicadores do catálogo, organizados por categoria — "
        "ideal para compartilhar o cenário inteiro com a equipe."
    )
    if st.button("Gerar Relatório HTML Completo"):
        todas_series = {}
        with st.spinner("Buscando todos os indicadores no FRED..."):
            for categoria, series in CATALOGO.items():
                for s in series:
                    e_indice = s.get("tipo") == "indice"
                    try:
                        serie = _buscar_serie_cache(
                            s["id"], inicio, None, "pc1" if e_indice else None
                        ).dropna()
                    except Exception:
                        continue
                    if serie.empty:
                        continue
                    legenda = (
                        "Variação % vs. 12 meses atrás (units=pc1, cálculo oficial do FRED)"
                        if e_indice
                        else s["nota"]
                    )
                    todas_series[s["id"]] = {
                        "nome": s["nome"],
                        "serie": serie,
                        "nota": legenda,
                        "url": url_serie(s["id"]),
                        "categoria": categoria,
                    }

        caminho = RAIZ_PROJETO / "cenario_economico_eua.html"
        gerado_em = date.today().strftime("%d/%m/%Y")
        html_export.exportar_html(todas_series, str(caminho), gerado_em)
        with open(caminho, "rb") as f:
            st.download_button(
                "⬇️ Baixar HTML (envie por e-mail/Teams)",
                f,
                file_name="cenario_economico_eua.html",
                mime="text/html",
            )

    st.divider()

    st.subheader("Excel com indicadores selecionados")
    if not st.session_state.selecionadas:
        st.info(
            "Nenhuma série selecionada ainda. Adicione pela Visão Geral ou pelo Explorador."
        )
    else:
        st.write(f"{len(st.session_state.selecionadas)} série(s) selecionada(s):")
        for sid, dados in st.session_state.selecionadas.items():
            st.write(f"- {dados['nome']} ({sid})")

        if st.button("Gerar Excel"):
            caminho = RAIZ_PROJETO / "cenario_economico_eua.xlsx"
            excel_export.exportar_excel(
                st.session_state.selecionadas, str(caminho), rotulo_codigo="Série (FRED)"
            )
            with open(caminho, "rb") as f:
                st.download_button(
                    "⬇️ Baixar Excel", f, file_name="cenario_economico_eua.xlsx"
                )
