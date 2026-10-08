"""Dashboard — Consumo de Energia Elétrica no Brasil (2015–2024)
Projeto G1 · Linguagem de Programação — Análise e Visualização de Dados com Python
Tecnologias: Python, Pandas, NumPy, Plotly, Matplotlib, Seaborn, Streamlit.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st

st.set_page_config(page_title="Consumo de Energia no Brasil", page_icon="⚡", layout="wide")

DATA_PATH = Path(__file__).parent / "dados" / "simulacao_consumo_energia_brasil.csv"
ORDEM_NIVEL = ["Baixo", "Médio", "Alto", "Crítico"]
MESES = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
         7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

# Coordenadas aproximadas (centro) dos 20 estados presentes na base — usadas no mapa interativo
UF_COORDS = {
    "AM": (-3.4, -65.0), "PA": (-3.8, -52.0), "RO": (-10.9, -62.8), "TO": (-10.2, -48.3),
    "BA": (-12.5, -41.7), "PE": (-8.4, -37.9), "CE": (-5.2, -39.3), "MA": (-5.0, -45.3),
    "PB": (-7.1, -36.8), "DF": (-15.8, -47.9), "GO": (-15.9, -49.8), "MT": (-12.6, -55.4),
    "MS": (-20.5, -54.5), "ES": (-19.6, -40.7), "MG": (-18.5, -44.5), "RJ": (-22.2, -42.6),
    "SP": (-22.2, -48.8), "PR": (-24.6, -51.6), "RS": (-29.7, -53.5), "SC": (-27.3, -50.6),
}


# ----------------------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------------------
@st.cache_data
def carregar_dados(origem) -> pd.DataFrame:
    """Lê o CSV, faz limpeza/tipagem e cria atributos derivados."""
    df = pd.read_csv(origem)
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    df = df.drop_duplicates().dropna(subset=["data", "consumo_mwh"])
    df["nivel_demanda"] = pd.Categorical(df["nivel_demanda"], categories=ORDEM_NIVEL, ordered=True)
    # engenharia de atributos
    df["mes_nome"] = df["mes"].map(MESES)
    df["consumo_per_capita"] = df["consumo_mwh"] / df["populacao"]
    df["custo_estimado"] = df["consumo_mwh"] * df["tarifa_media"]
    return df


def fmt(n: float, sufixo: str = "") -> str:
    """Formata números grandes no padrão brasileiro (1.234,5 / 1,2 mi)."""
    for lim, nome in ((1e9, " bi"), (1e6, " mi"), (1e3, " mil")):
        if abs(n) >= lim:
            return f"{n / lim:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + nome + sufixo
    return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + sufixo


def forca_correlacao(r: float) -> str:
    a = abs(r)
    if a < 0.1:
        return "praticamente nula"
    if a < 0.3:
        return "fraca"
    if a < 0.5:
        return "moderada"
    return "forte"


# ----------------------------------------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------------------------------------
st.title("⚡ Consumo de Energia Elétrica no Brasil (2015–2024)")
st.markdown(
    "**Problema:** o consumo de energia reflete atividade econômica, crescimento urbano e eficiência. "
    "Monitorar padrões de demanda, sazonalidade e picos ajuda a antecipar riscos de sobrecarga no sistema elétrico. "
    "Este dashboard investiga **quais estados e setores mais consomem, como o consumo evolui no tempo, "
    "se há sazonalidade e se a temperatura se relaciona com o consumo**."
)
st.caption("Base: dataset **simulado** fornecido pelo professor (4.440 registros · 20 estados · 5 setores · 2015–2024).")

# ----------------------------------------------------------------------------------------
# Carga (com upload opcional de outro CSV com as mesmas colunas)
# ----------------------------------------------------------------------------------------
st.sidebar.header("🎛️ Filtros")
arquivo = st.sidebar.file_uploader("Opcional: enviar outro CSV (mesmas colunas)", type="csv")
try:
    df = carregar_dados(arquivo if arquivo is not None else DATA_PATH)
except Exception as erro:  # arquivo enviado fora do padrão
    st.sidebar.error(f"Não foi possível ler o arquivo: {erro}")
    df = carregar_dados(DATA_PATH)

anos = sorted(df["ano"].unique())
sel_anos = st.sidebar.multiselect("Ano", anos, default=anos)
sel_meses = st.sidebar.multiselect("Mês", list(MESES), default=list(MESES), format_func=MESES.get)
regioes = sorted(df["regiao"].unique())
sel_regioes = st.sidebar.multiselect("Região", regioes, default=regioes)
ufs_disp = sorted(df.loc[df["regiao"].isin(sel_regioes), "uf"].unique())
sel_ufs = st.sidebar.multiselect("Estado (UF)", ufs_disp, default=ufs_disp)
setores = sorted(df["setor_consumo"].unique())
sel_setores = st.sidebar.multiselect("Setor de consumo", setores, default=setores)
sel_niveis = st.sidebar.multiselect("Nível de demanda", ORDEM_NIVEL, default=ORDEM_NIVEL)

f = df[
    df["ano"].isin(sel_anos)
    & df["mes"].isin(sel_meses)
    & df["regiao"].isin(sel_regioes)
    & df["uf"].isin(sel_ufs)
    & df["setor_consumo"].isin(sel_setores)
    & df["nivel_demanda"].isin(sel_niveis)
]
st.sidebar.metric("Registros após filtros", f"{len(f):,}".replace(",", "."))

if f.empty:
    st.warning("Nenhum registro com esses filtros. Ajuste a seleção na barra lateral.")
    st.stop()

# ----------------------------------------------------------------------------------------
# KPIs dinâmicos
# ----------------------------------------------------------------------------------------
por_uf = f.groupby("uf")["consumo_mwh"].sum().sort_values(ascending=False)
por_setor = f.groupby("setor_consumo")["consumo_mwh"].sum().sort_values(ascending=False)

st.subheader("📌 Indicadores-chave")
c1, c2, c3 = st.columns(3)
c1.metric("Consumo total", fmt(f["consumo_mwh"].sum(), " MWh"))
c2.metric("Estado com maior consumo", por_uf.index[0], fmt(por_uf.iloc[0], " MWh"), delta_color="off")
c3.metric("Setor mais consumidor", por_setor.index[0], fmt(por_setor.iloc[0], " MWh"), delta_color="off")
c4, c5, c6 = st.columns(3)
c4.metric("Demanda de pico média", fmt(f["demanda_pico"].mean(), " MW"))
c5.metric("Tarifa média", f"R$ {f['tarifa_media'].mean():.2f}/kWh".replace(".", ","))
c6.metric("Emissão total de CO₂", fmt(f["emissao_co2"].sum(), " t"))

st.divider()

# ----------------------------------------------------------------------------------------
# Seções (abas)
# ----------------------------------------------------------------------------------------
abas = st.tabs(["📈 Evolução temporal", "🗺️ Regiões e estados", "🏭 Setores",
                "🌦️ Sazonalidade", "🌡️ Temperatura e correlação", "🔌 Demanda e eficiência", "🧮 Tabela dinâmica"])

# ---- 1. Temporal -----------------------------------------------------------------------
with abas[0]:
    st.header("Evolução temporal do consumo")
    mensal = f.groupby("data", as_index=False)["consumo_mwh"].sum().sort_values("data")
    mensal["media_movel_12m"] = mensal["consumo_mwh"].rolling(12, min_periods=12).mean()
    fig = go.Figure()
    fig.add_scatter(x=mensal["data"], y=mensal["consumo_mwh"], mode="lines", name="Consumo mensal")
    if mensal["media_movel_12m"].notna().any():
        fig.add_scatter(x=mensal["data"], y=mensal["media_movel_12m"], mode="lines",
                        name="Média móvel 12 meses", line=dict(width=4, color="crimson"))
    fig.update_layout(yaxis_title="Consumo (MWh)", xaxis_title="", hovermode="x unified", height=420)
    st.plotly_chart(fig, width="stretch")

    anual = f.groupby("ano", as_index=False)["consumo_mwh"].sum()
    anual["variacao_pct"] = anual["consumo_mwh"].pct_change() * 100
    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(anual, x="ano", y="consumo_mwh", text_auto=".3s", title="Consumo total por ano",
                     labels={"consumo_mwh": "MWh", "ano": "Ano"})
        st.plotly_chart(fig, width="stretch")
    with col_b:
        fig = px.bar(anual.dropna(), x="ano", y="variacao_pct", title="Variação anual (%)",
                     labels={"variacao_pct": "% vs. ano anterior", "ano": "Ano"},
                     color="variacao_pct", color_continuous_scale="RdYlGn", color_continuous_midpoint=0)
        st.plotly_chart(fig, width="stretch")

    if len(anual) >= 2:
        ini, fim = anual.iloc[0], anual.iloc[-1]
        cresc = (fim["consumo_mwh"] / ini["consumo_mwh"] - 1) * 100
        pico = anual.loc[anual["consumo_mwh"].idxmax()]
        st.info(
            f"**Interpretação:** entre {int(ini['ano'])} e {int(fim['ano'])} o consumo anual variou "
            f"**{cresc:+.1f}%**. O maior consumo anual foi em **{int(pico['ano'])}** ({fmt(pico['consumo_mwh'], ' MWh')}). "
            "A trajetória não é monotônica: há quedas e recuperações ao longo da série."
        )

# ---- 2. Regiões e estados ---------------------------------------------------------------
with abas[1]:
    st.header("Comparação regional e ranking de estados")
    col_a, col_b = st.columns(2)
    with col_a:
        if len(por_uf) > 3:
            top_n = st.slider("Quantidade de estados no ranking", 3, len(por_uf), min(10, len(por_uf)))
        else:
            top_n = len(por_uf)
        metrica = st.radio("Métrica do ranking", ["Consumo total", "Média por registro"], horizontal=True)
        if metrica == "Consumo total":
            serie = por_uf
        else:
            serie = f.groupby("uf")["consumo_mwh"].mean().sort_values(ascending=False)
        rk = serie.head(top_n).reset_index()
        fig = px.bar(rk.sort_values("consumo_mwh"), x="consumo_mwh", y="uf", orientation="h",
                     text_auto=".3s", title=f"Ranking de estados — {metrica.lower()}",
                     labels={"consumo_mwh": "MWh", "uf": "UF"})
        st.plotly_chart(fig, width="stretch")
        st.caption("⚠️ Na base, alguns estados (ex.: RJ) têm mais registros que outros; "
                   "por isso o total favorece quem tem mais linhas. A média por registro compara em pé de igualdade.")
    with col_b:
        reg = f.groupby("regiao", as_index=False)["consumo_mwh"].sum()
        fig = px.pie(reg, names="regiao", values="consumo_mwh", hole=0.45, title="Participação por região")
        st.plotly_chart(fig, width="stretch")

    reg_ano = f.groupby(["ano", "regiao"], as_index=False)["consumo_mwh"].sum()
    fig = px.line(reg_ano, x="ano", y="consumo_mwh", color="regiao", markers=True,
                  title="Evolução do consumo por região", labels={"consumo_mwh": "MWh", "ano": "Ano"})
    st.plotly_chart(fig, width="stretch")

    # crescimento por região (primeiro vs último ano do filtro)
    piv = reg_ano.pivot(index="regiao", columns="ano", values="consumo_mwh")
    if piv.shape[1] >= 2:
        cresc_reg = ((piv.iloc[:, -1] / piv.iloc[:, 0] - 1) * 100).sort_values(ascending=False)
        st.subheader(f"Crescimento por região ({piv.columns[0]} → {piv.columns[-1]})")
        fig = px.bar(cresc_reg.reset_index(name="crescimento_pct"), x="regiao", y="crescimento_pct",
                     text_auto=".1f", labels={"crescimento_pct": "%", "regiao": "Região"},
                     color="crescimento_pct", color_continuous_scale="RdYlGn", color_continuous_midpoint=0)
        st.plotly_chart(fig, width="stretch")
        st.info(
            f"**Interpretação:** **{por_uf.index[0]}** lidera o consumo total nos filtros atuais "
            f"(parte disso vem de ter mais registros na base — veja a média por registro). "
            f"A região com maior crescimento no período foi **{cresc_reg.index[0]}** ({cresc_reg.iloc[0]:+.1f}%) "
            f"e a de menor, **{cresc_reg.index[-1]}** ({cresc_reg.iloc[-1]:+.1f}%)."
        )

    st.subheader("Mapa interativo — consumo por estado")
    mapa = f.groupby("uf", as_index=False).agg(consumo=("consumo_mwh", "sum"), emissao=("emissao_co2", "sum"))
    mapa["lat"] = mapa["uf"].map(lambda u: UF_COORDS[u][0])
    mapa["lon"] = mapa["uf"].map(lambda u: UF_COORDS[u][1])
    fig = px.scatter_map(mapa, lat="lat", lon="lon", size="consumo", color="consumo", hover_name="uf",
                         hover_data={"consumo": ":,.0f", "emissao": ":,.0f", "lat": False, "lon": False},
                         size_max=45, zoom=3, center={"lat": -15, "lon": -52},
                         color_continuous_scale="YlOrRd", map_style="open-street-map", height=520)
    st.plotly_chart(fig, width="stretch")

# ---- 3. Setores -------------------------------------------------------------------------
with abas[2]:
    st.header("Análise por setor de consumo")
    col_a, col_b = st.columns(2)
    with col_a:
        s = por_setor.reset_index()
        fig = px.bar(s, x="setor_consumo", y="consumo_mwh", text_auto=".3s", color="setor_consumo",
                     title="Consumo total por setor", labels={"consumo_mwh": "MWh", "setor_consumo": "Setor"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")
    with col_b:
        fig = px.box(f, x="setor_consumo", y="consumo_mwh", log_y=True, color="setor_consumo",
                     title="Distribuição do consumo por registro (escala log)",
                     labels={"consumo_mwh": "MWh", "setor_consumo": "Setor"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")

    setor_reg = f.groupby(["regiao", "setor_consumo"], as_index=False)["consumo_mwh"].sum()
    fig = px.bar(setor_reg, x="regiao", y="consumo_mwh", color="setor_consumo", barmode="group",
                 title="Setor × região", labels={"consumo_mwh": "MWh", "regiao": "Região"})
    st.plotly_chart(fig, width="stretch")

    dif = (por_setor.iloc[0] / por_setor.iloc[-1] - 1) * 100
    st.info(
        f"**Interpretação:** **{por_setor.index[0]}** é o setor mais consumidor e **{por_setor.index[-1]}** o menos; "
        f"a diferença entre eles é de apenas **{dif:.1f}%**, ou seja, o consumo está distribuído de forma bastante equilibrada entre os setores."
    )

# ---- 4. Sazonalidade --------------------------------------------------------------------
with abas[3]:
    st.header("Sazonalidade do consumo")
    heat = f.pivot_table(index="ano", columns="mes", values="consumo_mwh", aggfunc="sum")
    heat.columns = [MESES[m] for m in heat.columns]
    fig = px.imshow(heat, aspect="auto", color_continuous_scale="YlOrRd", text_auto=".2s",
                    labels=dict(x="Mês", y="Ano", color="MWh"), title="Heatmap mensal do consumo (ano × mês)")
    st.plotly_chart(fig, width="stretch")

    med_mes = f.groupby("mes")["consumo_mwh"].mean().reset_index()
    med_mes["mes_nome"] = med_mes["mes"].map(MESES)
    fig = px.line(med_mes, x="mes_nome", y="consumo_mwh", markers=True, title="Consumo médio por mês do ano",
                  labels={"consumo_mwh": "MWh (média por registro)", "mes_nome": "Mês"})
    st.plotly_chart(fig, width="stretch")

    idx = med_mes["consumo_mwh"] / med_mes["consumo_mwh"].mean()
    amplitude = (idx.max() - idx.min()) * 100
    mes_pico = med_mes.loc[med_mes["consumo_mwh"].idxmax(), "mes_nome"]
    mes_vale = med_mes.loc[med_mes["consumo_mwh"].idxmin(), "mes_nome"]
    st.info(
        f"**Interpretação:** o mês de maior consumo médio é **{mes_pico}** e o de menor é **{mes_vale}**. "
        f"A diferença entre eles é de **{amplitude:.0f} p.p.** sobre a média, e sem um padrão que se repita todos os anos no heatmap. "
        "Como a base é simulada, não há uma sazonalidade bem definida (ex.: verão × inverno)."
    )

# ---- 5. Temperatura e correlação --------------------------------------------------------
with abas[4]:
    st.header("Relação entre temperatura e consumo")
    r_p = f["temperatura_media"].corr(f["consumo_mwh"])
    r_s = f["temperatura_media"].corr(f["consumo_mwh"], method="spearman")
    k1, k2 = st.columns(2)
    k1.metric("Correlação de Pearson", f"{r_p:.3f}".replace(".", ","))
    k2.metric("Correlação de Spearman", f"{r_s:.3f}".replace(".", ","))

    amostra = f if len(f) <= 3000 else f.sample(3000, random_state=42)
    fig = px.scatter(amostra, x="temperatura_media", y="consumo_mwh", color="setor_consumo", opacity=0.6, log_y=True,
                     hover_data=["uf", "ano", "mes"], title="Temperatura × consumo (escala log no eixo Y)",
                     labels={"temperatura_media": "Temperatura média (°C)", "consumo_mwh": "Consumo (MWh)"})
    if f["temperatura_media"].nunique() > 1:
        a, b = np.polyfit(f["temperatura_media"], np.log10(f["consumo_mwh"]), 1)
        xs = np.linspace(f["temperatura_media"].min(), f["temperatura_media"].max(), 50)
        fig.add_scatter(x=xs, y=10 ** (a * xs + b), mode="lines", name="Tendência linear",
                        line=dict(color="black", width=3, dash="dash"))
    st.plotly_chart(fig, width="stretch")

    st.subheader("Matriz de correlação (Seaborn)")
    cols = ["consumo_mwh", "demanda_pico", "temperatura_media", "tarifa_media",
            "populacao", "eficiencia_energetica", "emissao_co2"]
    fig_sns, ax = plt.subplots(figsize=(8, 5))
    sns.heatmap(f[cols].corr(), annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    ax.set_title("Correlação de Pearson entre variáveis numéricas")
    st.pyplot(fig_sns)

    st.info(
        f"**Interpretação:** a correlação entre temperatura e consumo é **{forca_correlacao(r_p)}** "
        f"(Pearson = {r_p:.3f}). Isso indica que, nesta base, a temperatura **não** explica o consumo — "
        "esperado em dados simulados, onde as variáveis foram geradas de forma independente. "
        "Em dados reais seria esperado um aumento de consumo em períodos mais quentes (ar-condicionado)."
    )

# ---- 6. Demanda e eficiência ------------------------------------------------------------
with abas[5]:
    st.header("Demanda de pico e eficiência energética")
    col_a, col_b = st.columns(2)
    with col_a:
        niv = f["nivel_demanda"].value_counts().reindex(ORDEM_NIVEL).reset_index()
        niv.columns = ["nivel_demanda", "registros"]
        fig = px.bar(niv, x="nivel_demanda", y="registros", text_auto=True, color="nivel_demanda",
                     color_discrete_map={"Baixo": "#2ca02c", "Médio": "#f2c14e", "Alto": "#ff7f0e", "Crítico": "#d62728"},
                     title="Registros por nível de demanda", labels={"nivel_demanda": "Nível", "registros": "Registros"})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")
    with col_b:
        pico_mensal = f.groupby("data", as_index=False)["demanda_pico"].max()
        fig = px.line(pico_mensal, x="data", y="demanda_pico", title="Maior demanda de pico registrada por mês",
                      labels={"demanda_pico": "MW", "data": ""})
        st.plotly_chart(fig, width="stretch")

    efic = f.groupby("ano", as_index=False)["eficiencia_energetica"].mean()
    fig = px.line(efic, x="ano", y="eficiencia_energetica", markers=True,
                  title="Evolução da eficiência energética média", labels={"eficiencia_energetica": "Índice médio", "ano": "Ano"})
    st.plotly_chart(fig, width="stretch")

    top_picos = f.nlargest(10, "demanda_pico")[["data", "uf", "setor_consumo", "demanda_pico", "nivel_demanda"]]
    st.subheader("Top 10 picos de demanda")
    st.dataframe(top_picos.assign(data=top_picos["data"].dt.strftime("%Y-%m")), width="stretch", hide_index=True)

    crit = (f["nivel_demanda"] == "Crítico").mean() * 100
    st.info(
        f"**Interpretação:** **{crit:.1f}%** dos registros estão em nível de demanda *Crítico*. "
        f"A eficiência média no período filtrado é **{f['eficiencia_energetica'].mean():.1f}** pontos, "
        "sem uma tendência clara de melhora ou piora ao longo dos anos."
    )

# ---- 7. Tabela dinâmica -----------------------------------------------------------------
with abas[6]:
    st.header("Tabela dinâmica")
    t1, t2, t3, t4 = st.columns(4)
    linhas = t1.selectbox("Linhas", ["uf", "regiao", "setor_consumo", "ano", "mes_nome", "nivel_demanda"], index=0)
    colunas = t2.selectbox("Colunas", ["setor_consumo", "regiao", "ano", "nivel_demanda", "(nenhuma)"], index=0)
    valor = t3.selectbox("Valor", ["consumo_mwh", "demanda_pico", "emissao_co2", "tarifa_media",
                                   "eficiencia_energetica", "custo_estimado"], index=0)
    func = t4.selectbox("Agregação", ["sum", "mean", "max", "min", "count"], index=0)
    pv = pd.pivot_table(f, index=linhas, columns=None if colunas == "(nenhuma)" else colunas,
                        values=valor, aggfunc=func, observed=True)
    st.dataframe(pv.style.format("{:,.1f}"), width="stretch")
    st.download_button("⬇️ Baixar dados filtrados (CSV)", f.to_csv(index=False).encode("utf-8"),
                       "consumo_energia_filtrado.csv", "text/csv")
    with st.expander("Ver dados brutos filtrados"):
        st.dataframe(f.drop(columns=["mes_nome"]), width="stretch")

# ----------------------------------------------------------------------------------------
# Conclusão executiva
# ----------------------------------------------------------------------------------------
crit_por_uf = (f["nivel_demanda"] == "Crítico").groupby(f["uf"]).mean().sort_values(ascending=False) * 100
crit_uf_txt = (
    f"O estado com maior proporção de registros críticos é **{crit_por_uf.index[0]}** ({crit_por_uf.iloc[0]:.1f}%), "
    f"contra {crit_por_uf.iloc[-1]:.1f}% em **{crit_por_uf.index[-1]}** (diferença de "
    f"{crit_por_uf.iloc[0] - crit_por_uf.iloc[-1]:.1f} p.p.). Em dados simulados, essa variação pode ser apenas aleatória."
    if len(crit_por_uf) > 1 else ""
)
st.divider()
st.header("📝 Conclusão executiva")
st.markdown(
    f"""
- **Quem consome mais:** com os filtros atuais, **{por_uf.index[0]}** é o estado com maior consumo total (em parte por ter mais registros na base) e **{por_setor.index[0]}** o setor mais consumidor; a diferença entre setores é pequena.
- **Evolução:** o consumo anual oscila (não é crescimento contínuo), com queda em 2020 e recuperação nos anos seguintes na base completa.
- **Sazonalidade e temperatura:** não há padrão sazonal nem relação relevante entre temperatura e consumo (correlação de Pearson = {r_p:.3f}).
- **Risco de demanda:** {crit:.1f}% dos registros estão em nível *Crítico*. {crit_uf_txt}
- **Impacto ambiental:** as emissões somam **{fmt(f['emissao_co2'].sum(), ' t de CO₂')}** no recorte selecionado.
- **Limitação:** a base é **simulada**; ausência de correlações é um resultado esperado e não deve ser extrapolada para o sistema elétrico real.
"""
)
st.caption("Projeto G1 · Análise e Visualização de Dados com Python · Streamlit + Pandas + Plotly + Seaborn")
