import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import requests
from datetime import date

API_KEY = "a5b1c48c433202056145dd194ad64571"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

def listar_jogos_hoje():
    hoje = date.today().strftime("%Y-%m-%d")
    response = requests.get(f"{BASE_URL}/fixtures", headers=HEADERS, params={"date": hoje})
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
    return None

def extrair_media(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 1.0

def analisar_jogo_completo(jogo):
    time_casa = jogo['teams']['home']
    time_fora = jogo['teams']['away']
    league_id = jogo['league']['id']
    season = jogo['league']['season']
    id_casa = time_casa['id']
    id_fora = time_fora['id']

    stats_casa = buscar_estatisticas_time(id_casa, league_id, season)
    stats_fora = buscar_estatisticas_time(id_fora, league_id, season)

    if not stats_casa or not stats_fora:
        return None

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
        "Confiabilidade": f"{confianca}%"
    }

st.set_page_config(page_title="Probabilidades Diárias de Jogos", layout="wide")
st.title("📊 Probabilidades de Todos os Jogos de Hoje")

jogos_hoje = listar_jogos_hoje()
resultados = []

with st.spinner("Analisando todas as partidas de hoje..."):
    for jogo in jogos_hoje:
        resultado = analisar_jogo_completo(jogo)
        if resultado:
            resultados.append(resultado)

if resultados:
    df_resultados = pd.DataFrame(resultados)
    st.dataframe(df_resultados, use_container_width=True)
    st.success(f"{len(resultados)} jogos analisados com sucesso.")
else:
    st.warning("Nenhuma estatística disponível para os jogos de hoje.")

st.caption("Desenvolvido com dados da API-Football. Use as informações com responsabilidade.")
