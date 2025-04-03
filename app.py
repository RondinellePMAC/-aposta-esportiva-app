import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import requests
from datetime import date
import altair as alt

API_KEY = "a5b1c48c433202056145dd194ad64571"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

continentes = {
    "Europa": ["UEFA Champions League", "Premier League", "La Liga", "Serie A", "Bundesliga"],
    "América do Sul": ["Copa Libertadores", "Campeonato Brasileiro Série A", "Liga Profesional Argentina"]
}

ligas_disponiveis = {
    "UEFA Champions League": 2,
    "Premier League": 39,
    "La Liga": 140,
    "Serie A": 135,
    "Bundesliga": 78,
    "Copa Libertadores": 13,
    "Campeonato Brasileiro Série A": 71,
    "Liga Profesional Argentina": 128
}

def listar_jogos_hoje_por_liga(league_id):
    hoje = date.today().strftime("%Y-%m-%d")
    response = requests.get(f"{BASE_URL}/fixtures", headers=HEADERS, params={"date": hoje, "league": league_id})
    if response.status_code == 200:
        return response.json()['response']
    return []

def buscar_estatisticas_time(team_id, league_id, season):
    response = requests.get(
        f"{BASE_URL}/teams/statistics",
        headers=HEADERS,
        params={"team": team_id, "league": league_id, "season": season}
    )
    if response.status_code == 200:
        return response.json()['response']
    return {
        'goals': {'for': {'average': {'total': 0}}, 'against': {'average': {'total': 0}}},
        'fixtures': {'played': {'total': 1}, 'wins': {'total': 0}, 'draws': {'total': 0}}
    }

def extrair_media(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0

def analisar_jogo_completo(jogo):
    time_casa = jogo['teams']['home']
    time_fora = jogo['teams']['away']
    league_id = jogo['league']['id']
    season = jogo['league']['season']
    id_casa = time_casa['id']
    id_fora = time_fora['id']

    stats_casa = buscar_estatisticas_time(id_casa, league_id, season)
    stats_fora = buscar_estatisticas_time(id_fora, league_id, season)

    gols_casa = extrair_media(stats_casa['goals']['for']['average']['total'])
    gols_fora = extrair_media(stats_fora['goals']['for']['average']['total'])
    media_gols = gols_casa + gols_fora
    ambas_marcam = gols_casa > 0.9 and gols_fora > 0.9
    mais_25 = media_gols > 2.5

    jogos_casa = stats_casa['fixtures']['played']['total'] or 1
    jogos_fora = stats_fora['fixtures']['played']['total'] or 1

    vitorias_casa = stats_casa['fixtures']['wins']['total'] / jogos_casa * 100
    empates = stats_casa['fixtures']['draws']['total'] / jogos_casa * 100
    vitorias_fora = stats_fora['fixtures']['wins']['total'] / jogos_fora * 100

    confianca_casa = vitorias_casa + (gols_casa * 10)
    confianca_fora = vitorias_fora + (gols_fora * 10)

    confianca = 0
    if media_gols > 2.5:
        confianca += 30
    if ambas_marcam:
        confianca += 20
    if max(vitorias_casa, vitorias_fora) > 60:
        confianca += 30
    if empates < 20:
        confianca += 20

    return {
        "Jogo": f"{time_casa['name']} vs {time_fora['name']}",
        "Média de Gols": round(media_gols, 2),
        "Ambas Marcam": "Sim" if ambas_marcam else "Não",
        "+2.5 Gols": "Sim" if mais_25 else "Não",
        "Vitória Mandante (%)": round(vitorias_casa, 1),
        "Empate (%)": round(empates, 1),
        "Vitória Visitante (%)": round(vitorias_fora, 1),
        "Confiabilidade": f"{confianca}%",
        "Confiança Mandante": round(confianca_casa, 1),
        "Confiança Visitante": round(confianca_fora, 1),
        "Mandante": time_casa['name'],
        "Visitante": time_fora['name']
    }

def gerar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Jogos")
    return output.getvalue()

st.set_page_config(page_title="Probabilidades por Continente", layout="wide")
st.title("🌍 Selecione Jogos por Continente e Liga")

continente = st.selectbox("🌎 Escolha um continente:", list(continentes.keys()))
liga_nome = st.selectbox("🏆 Escolha uma liga:", continentes[continente])
liga_id = ligas_disponiveis[liga_nome]

jogos_hoje = listar_jogos_hoje_por_liga(liga_id)
resultados = []

with st.spinner(f"🔍 Analisando partidas de hoje na {liga_nome}..."):
    for jogo in jogos_hoje:
        resultado = analisar_jogo_completo(jogo)
        if resultado:
            resultados.append(resultado)

if resultados:
    df_resultados = pd.DataFrame(resultados)
    st.dataframe(df_resultados, use_container_width=True)
    st.success(f"{len(resultados)} jogos analisados na {liga_nome}.")

    for r in resultados:
        st.markdown(f"### {r['Jogo']}")
        st.markdown(f"- 🔵 **Mandante**: {r['Mandante']} - Confiança: **{r['Confiança Mandante']}%**")
        st.markdown(f"- 🔴 **Visitante**: {r['Visitante']} - Confiança: **{r['Confiança Visitante']}%**")
        st.markdown(f"- 🧠 Probabilidades: Vitória Mandante: {r['Vitória Mandante (%)']}% | Empate: {r['Empate (%)']}% | Vitória Visitante: {r['Vitória Visitante (%)']}%")

        chart_data = pd.DataFrame({
            "Resultado": ["Vitória Mandante", "Empate", "Vitória Visitante"],
            "Probabilidade": [r['Vitória Mandante (%)'], r['Empate (%)'], r['Vitória Visitante (%)']]
        })

        chart = alt.Chart(chart_data).mark_bar().encode(
            x=alt.X("Resultado", sort=None),
            y="Probabilidade",
            color="Resultado"
        ).properties(width=400, height=300)

        st.altair_chart(chart, use_container_width=True)
        st.divider()

    st.markdown("### 📥 Exportar para Excel")
    excel_data = gerar_excel(df_resultados)
    st.download_button(
        label="📥 Baixar Análise",
        data=excel_data,
        file_name=f"analise_{liga_nome.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning(f"Nenhum jogo com estatísticas disponíveis hoje na {liga_nome}.")

st.caption("Desenvolvido com dados da API-Football. Use com responsabilidade.")
