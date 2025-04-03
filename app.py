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
        'fixtures': {'played': {'total': 1}, 'wins': {'total': 0}, 'draws': {'total': 0}},
        'form': ""
    }

def avaliar_partida_melhor_do_mundo(stats_casa, stats_fora):
    media_gols_casa = float(stats_casa['goals']['for']['average']['total'] or 0)
    media_gols_fora = float(stats_fora['goals']['for']['average']['total'] or 0)

    jogos_casa = stats_casa['fixtures']['played']['total'] or 1
    jogos_fora = stats_fora['fixtures']['played']['total'] or 1

    vitoria_casa = stats_casa['fixtures']['wins']['total'] / jogos_casa * 100
    vitoria_fora = stats_fora['fixtures']['wins']['total'] / jogos_fora * 100

    forma_casa = stats_casa.get('form', '').count("W") * 10
    forma_fora = stats_fora.get('form', '').count("W") * 10

    score = (
        (media_gols_casa + media_gols_fora) * 10 +
        vitoria_casa * 0.3 +
        vitoria_fora * 0.3 +
        forma_casa * 0.2 +
        forma_fora * 0.2
    )

    if media_gols_casa + media_gols_fora >= 2.5:
        palpite = "+2.5 Gols"
    elif vitoria_fora > 60:
        palpite = "Vitória Visitante"
    elif vitoria_casa > 60:
        palpite = "Vitória Mandante"
    else:
        palpite = "Dupla Chance"

    return min(round(score, 1), 100), palpite

def listar_jogos_hoje_por_liga(league_id):
    hoje = date.today().strftime("%Y-%m-%d")
    response = requests.get(f"{BASE_URL}/fixtures", headers=HEADERS, params={"date": hoje, "league": league_id})
    if response.status_code == 200:
        return response.json()['response']
    return []

st.set_page_config(page_title="Melhor do Mundo - Apostas", layout="wide")
st.title("🔍 Análise de Partidas - Estilo Melhor do Mundo")

continente = st.selectbox("🌎 Selecione o continente", list(continentes.keys()))
liga_nome = st.selectbox("🏆 Escolha a liga", continentes[continente])
liga_id = ligas_disponiveis[liga_nome]

jogos_hoje = listar_jogos_hoje_por_liga(liga_id)

if not jogos_hoje:
    st.warning("Nenhum jogo encontrado para hoje nesta liga.")
else:
    for jogo in jogos_hoje:
        time_casa = jogo['teams']['home']['name']
        time_fora = jogo['teams']['away']['name']
        st.markdown(f"### ⚽ {time_casa} vs {time_fora}")

        stats_casa = buscar_estatisticas_time(jogo['teams']['home']['id'], jogo['league']['id'], jogo['league']['season'])
        stats_fora = buscar_estatisticas_time(jogo['teams']['away']['id'], jogo['league']['id'], jogo['league']['season'])

        score, palpite = avaliar_partida_melhor_do_mundo(stats_casa, stats_fora)

        st.info(f"🏅 Score: {score}/100")
        st.success(f"🎯 Palpite sugerido: {palpite}")

        chart_data = pd.DataFrame({
            "Equipe": ["Mandante", "Visitante"],
            "Confiança": [score if palpite == "Vitória Mandante" else score / 2,
                          score if palpite == "Vitória Visitante" else score / 2]
        })

        chart = alt.Chart(chart_data).mark_bar().encode(
            x="Equipe",
            y="Confiança",
            color="Equipe"
        ).properties(height=200)

        st.altair_chart(chart, use_container_width=True)
        st.divider()

st.caption("Desenvolvido com inteligência para análise preditiva de apostas esportivas")
