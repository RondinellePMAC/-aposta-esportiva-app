import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Análise de Partidas", layout="wide")
st.title("⚽ Análise Rápida de Jogo com Visual")

st.markdown("Digite os nomes dos times e forneça os dados estimados para gerar a análise preditiva.")

with st.form("form_analise"):
    col1, col2 = st.columns(2)
    with col1:
        time_casa = st.text_input("🏠 Nome do Time Mandante", value="Time A")
        gols_casa = st.number_input("Média de Gols do Mandante", value=1.0, step=0.1)
        sofre_casa = st.number_input("Média de Gols Sofridos pelo Mandante", value=1.0, step=0.1)
        vitorias_casa = st.number_input("Probabilidade de Vitória Mandante (%)", value=30.0, step=1.0)
    with col2:
        time_fora = st.text_input("🚌 Nome do Time Visitante", value="Time B")
        gols_fora = st.number_input("Média de Gols do Visitante", value=1.0, step=0.1)
        sofre_fora = st.number_input("Média de Gols Sofridos pelo Visitante", value=1.0, step=0.1)
        vitorias_fora = st.number_input("Probabilidade de Vitória Visitante (%)", value=40.0, step=1.0)

    empates = st.slider("Probabilidade de Empate (%)", 0.0, 100.0, 30.0, step=1.0)
    odds = st.number_input("Odd Média para o Palpite", value=1.90, step=0.05)
    enviar = st.form_submit_button("🔍 Analisar Jogo")

if enviar:
    jogo_nome = f"{time_casa} vs {time_fora}"
    media_gols = gols_casa + gols_fora
    ambas_marcam = gols_casa > 0.9 and gols_fora > 0.9
    mais_25 = media_gols > 2.5

    total = vitorias_casa + empates + vitorias_fora
    prob_casa = round(vitorias_casa / total * 100, 1)
    prob_empate = round(empates / total * 100, 1)
    prob_fora = round(vitorias_fora / total * 100, 1)

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
        "Jogo": jogo_nome,
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
    st.markdown(f"### 📌 Visão Geral do Confronto: **{time_casa} vs {time_fora}**")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🔵 Gols Marcados (Mandante)", f"{gols_casa:.2f}")
        st.metric("🔴 Gols Sofridos (Mandante)", f"{sofre_casa:.2f}")
        st.metric("✅ Vitória Mandante (%)", f"{prob_casa:.1f}%")
    with col2:
        st.metric("🔵 Gols Marcados (Visitante)", f"{gols_fora:.2f}")
        st.metric("🔴 Gols Sofridos (Visitante)", f"{sofre_fora:.2f}")
        st.metric("✅ Vitória Visitante (%)", f"{prob_fora:.1f}%")

st.markdown("---")
st.caption("⚠️ Esta ferramenta é apenas uma estimativa baseada nos dados fornecidos. Aposte com responsabilidade.")
