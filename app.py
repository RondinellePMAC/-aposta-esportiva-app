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

# A função avaliar_partida_melhor_do_mundo será integrada no loop que mostra os jogos:
# Após st.altair_chart(chart, use_container_width=True), insira:
        stats_casa = buscar_estatisticas_time(jogo['teams']['home']['id'], jogo['league']['id'], jogo['league']['season'])
        stats_fora = buscar_estatisticas_time(jogo['teams']['away']['id'], jogo['league']['id'], jogo['league']['season'])
        score_melhor, palpite = avaliar_partida_melhor_do_mundo(stats_casa, stats_fora)
        st.success(f"🏅 Score Melhor do Mundo: {score_melhor}/100 | Palpite: {palpite}")
