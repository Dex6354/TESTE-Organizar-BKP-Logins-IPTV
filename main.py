import streamlit as st
import requests

st.set_page_config(page_title="Scrape.do Integration", layout="centered")

st.title("Scrape.do Integration")
st.write("Requisição utilizando Proxies Residenciais/Móveis e Geo-Targeting Brasil.")

# Campo dinâmico para o Token (deixe em branco para testar sem token)
token_input = st.text_input("Token do Scrape.do (Deixe vazio para testar sem token)", type="password")

API_URL = "http://api.scrape.do/"
TARGET_URL = "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

# Parâmetros base da requisição
params = {
    "url": TARGET_URL,
    "super": "true",
    "geoCode": "BR"
}

# Inclui o token nos parâmetros apenas se ele for digitado
if token_input:
    params["token"] = token_input

if st.button("Executar Requisição", type="primary"):
    with st.spinner("Aguardando resposta do scrape.do..."):
        try:
            response = requests.get(API_URL, params=params)
            
            # Exibe metadados úteis dos Headers do scrape.do
            st.subheader("Informações da Requisição")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status Code", response.status_code)
                st.metric("Créditos Restantes", response.headers.get("scrape.do-remaining-credits", "N/A"))
            with col2:
                st.metric("Custo da Requisição", response.headers.get("scrape.do-request-cost", "N/A"))
                st.metric("Status Inicial", response.headers.get("scrape.do-initial-status-code", "N/A"))

            # Exibe o conteúdo retornado (erro ou sucesso)
            st.subheader("Conteúdo da Resposta")
            try:
                st.json(response.json())
            except ValueError:
                st.text(response.text)

        except Exception as e:
            st.error(f"Erro ao conectar com a API: {e}")
