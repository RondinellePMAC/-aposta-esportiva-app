import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import requests

API_KEY = "a5b1c48c433202056145dd194ad64571"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

def buscar_time_por_nome(nome_time):
    response = requests.get(
        f"{BASE_URL}/teams",
        headers=HEADERS,
        params={"search": nome_time}
    )
    if response.status_code == 200:
        data = response.json()
        if data['results'] > 0:
            return data['response'][0]['team']['id']
    return None

def buscar_estatisticas_time(team_id, league_id=71, season=2023):
    response = requests.get(
        f"{BASE_URL}/teams/statistics",
        headers=HEADERS,
        params={
            "team": team_id,
            "league": league_id,
            "season": season
        }
    )
    if response.status_code == 200:
        return response.json()['response']
    return None

def extrair_media(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 1.0

st.set_page_config(page_title="Análise de Partidas", layout="wide")
st.title("⚽ Análise Automática de Jogo com API")

with st.form("form_api"):
    st.markdown("### 🔍 Buscar Estatísticas dos Times")
    time_casa_nome = st.text_input("Nome do Time Mandante")
    time_fora_nome = st.text_input("Nome do Time Visitante")
    buscar = st.form_submit_button("Buscar Estatísticas e Analisar")

if buscar and time_casa_nome and time_fora_nome:
    id_casa = buscar_time_por_nome(time_casa_nome)
    id_fora = buscar_time_por_nome(time_fora_nome)

    if id_casa and id_fora:
        stats_casa = buscar_estatisticas_time(id_casa)
        stats_fora = buscar_estatisticas_time(id_fora)

        if stats_casa and stats_fora:
            gols_casa = extrair_media(stats_casa['goals']['for']['average']['total'])
            sofre_casa = extrair_media(stats_casa['goals']['against']['average']['total'])
            gols_fora = extrair_media(stats_fora['goals']['for']['average']['total'])
            sofre_fora = extrair_media(stats_fora['goals']['against']['average']['total'])

            jogos_casa = stats_casa['fixtures']['played']['total'] or 1
            jogos_fora = stats_fora['fixtures']['played']['total'] or 1

            vitorias_casa = stats_casa['fixtures']['wins']['total'] / jogos_casa * 100
            empates = stats_casa['fixtures']['draws']['total'] / jogos_casa * 100
            vitorias_fora = stats_fora['fixtures']['wins']['total'] / jogos_fora * 100
            odds = 1.90

            media_gols = gols_casa + gols_fora
            ambas_marcam = gols_casa > 0.9 and gols_fora > 0.9
            mais_25 = media_gols > 2.5

            prob_casa = round(vitorias_casa, 1)
            prob_empate = round(empates, 1)
            prob_fora = round(vitorias_fora, 1)

            if prob_fora > 50:
                melhor = "Vitória Visitante"
            elif prob_casa > 50:
                melhor = "Vitória Mandante"
            elif mais_25:
                melhor = "+2.5 Gols"
            elif ambas_marcam:
                melhor = "Ambas Marcam"
            else:
                melhor = "Dupla Chance (Empate ou Visitante)"

            df = pd.DataFrame([{
                "Jogo": f"{time_casa_nome} vs {time_fora_nome}",
                "Média de Gols": round(media_gols, 2),
                "+2.5 Gols": "Sim" if mais_25 else "Não",
                "Ambas Marcam": "Sim" if ambas_marcam else "Não",
                "Vitória Mandante (%)": prob_casa,
                "Empate (%)": prob_empate,
                "Vitória Visitante (%)": prob_fora,
                "Melhor Aposta": melhor,
                "Odd Simulada": odds
            }])

            st.markdown("### 📊 Resultado da Análise")
            st.dataframe(df, use_container_width=True)

            st.markdown("### 📁 Exportar Palpite")
            def to_excel(df):
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                df.to_excel(writer, index=False, sheet_name='Palpite')
                writer.save()
                return output.getvalue()

            excel_data = to_excel(df)
            st.download_button(
                label="📥 Baixar Palpite (Excel)",
                data=excel_data,
                file_name="palpite_jogo.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.success(f"🎯 Melhor aposta sugerida: {melhor}")

            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🔵 Gols Marcados (Mandante)", f"{gols_casa:.2f}")
                st.metric("🔴 Gols Sofridos (Mandante)", f"{sofre_casa:.2f}")
                st.metric("✅ Vitória Mandante (%)", f"{prob_casa:.1f}%")
            with col2:
                st.metric("🔵 Gols Marcados (Visitante)", f"{gols_fora:.2f}")
                st.metric("🔴 Gols Sofridos (Visitante)", f"{sofre_fora:.2f}")
                st.metric("✅ Vitória Visitante (%)", f"{prob_fora:.1f}%")
        else:
            st.error("Erro ao obter estatísticas dos times.")
    else:
        st.error("Time(s) não encontrados. Verifique os nomes e tente novamente.")

st.markdown("---")
st.caption("⚠️ Esta ferramenta é apenas uma estimativa baseada nos dados fornecidos pela API-Football. Aposte com responsabilidade.")
