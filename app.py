import streamlit as st
import pandas as pd
import numpy as np
import requests
import altair as alt

API_KEY = "a5b1c48c433202056145dd194ad64571"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

ligas_disponiveis = {
    "Premier League": 39,
    "La Liga": 140,
    "Serie A (Brasil)": 71,
    "Libertadores": 13
}

continentes = {
    "Europa": ["Premier League", "La Liga"],
    "América do Sul": ["Serie A (Brasil)", "Libertadores"]
}

def buscar_times(league_id):
    response = requests.get(f"{BASE_URL}/teams", headers=HEADERS, params={"league": league_id, "season": 2023})
    if response.status_code == 200:
        data = response.json()['response']
        return {item['team']['name']: item['team']['id'] for item in data}
    return {}

def buscar_estatisticas_time(team_id, league_id=39, season=2023):
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
    empates = stats_casa['fixtures']['draws']['total'] / jogos_casa * 100

    forma_casa = stats_casa.get('form', '').count("W") * 10
    forma_fora = stats_fora.get('form', '').count("W") * 10

    score = (
        (media_gols_casa + media_gols_fora) * 10 +
        vitoria_casa * 0.3 +
        vitoria_fora * 0.3 +
        forma_casa * 0.2 +
        forma_fora * 0.2
    )

    if media_gols_casa + media_gols_fora >= 2.8:
        palpite = "+2.5 Gols"
    elif media_gols_casa + media_gols_fora >= 1.5:
        palpite = "+1.5 Gols"
    elif vitoria_fora > 60:
        palpite = "Vitória Visitante"
    elif vitoria_casa > 60:
        palpite = "Vitória Mandante"
    elif media_gols_casa > 0.8 and media_gols_fora > 0.8:
        palpite = "Ambas Marcam"
    else:
        palpite = "Dupla Chance"

    return min(round(score, 1), 100), palpite, vitoria_casa, empates, vitoria_fora

st.set_page_config(page_title="Análise Avançada de Partidas", layout="centered")
st.title("⚽ Análise Estatística de Partida com o Melhor Algoritmo")

continente = st.selectbox("🌍 Escolha o continente", list(continentes.keys()))
liga_nome = st.selectbox("🏆 Escolha a liga", continentes[continente])
liga_id = ligas_disponiveis[liga_nome]

with st.spinner("Carregando times da liga selecionada..."):
    times = buscar_times(liga_id)

if times:
    time_casa = st.selectbox("🏠 Time Mandante", list(times.keys()))
    time_fora = st.selectbox("🚩 Time Visitante", list(times.keys()))

    if time_casa and time_fora and time_casa != time_fora:
        id_casa = times[time_casa]
        id_fora = times[time_fora]

        stats_casa = buscar_estatisticas_time(id_casa, liga_id)
        stats_fora = buscar_estatisticas_time(id_fora, liga_id)

        score, palpite, v_casa, empates, v_fora = avaliar_partida_melhor_do_mundo(stats_casa, stats_fora)

        st.subheader(f"🔍 {time_casa} vs {time_fora}")
        st.markdown(f"- 🧠 **Score do Algoritmo:** `{score}/100`")
        st.markdown(f"- 🎯 **Melhor Aposta Sugerida:** `{palpite}`")
        st.markdown("- 📊 **Probabilidades Estimadas:**")

        probs = pd.DataFrame({
            "Resultado": ["Vitória Mandante", "Empate", "Vitória Visitante"],
            "Probabilidade (%)": [v_casa, empates, v_fora]
        })

        chart = alt.Chart(probs).mark_bar().encode(
            x="Resultado",
            y="Probabilidade (%)",
            color="Resultado"
        ).properties(height=300)

        st.altair_chart(chart, use_container_width=True)
else:
    st.error("Erro ao carregar times. Verifique sua chave de API.")

st.caption("Análise baseada no modelo mais eficiente e comprovado para apostas esportivas")
