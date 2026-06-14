import streamlit as st
import requests
import json
from urllib.parse import quote

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Streamlit Cloud API Debugger (Scrape.do API)")

# URL completa fornecida
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"
url = st.text_input("URL da API para Debug:", value=url_padrao)

# Token fornecido inserido como padrão
token = st.text_input("Scrape.do Token:", value="3a23ea3810a04b16bccfac96a2c3b1af73c97a98ef5", type="password")

# Opção para ativar renderização de JavaScript se o Cloudflare for muito agressivo
render_js = st.checkbox("Ativar Renderização de JavaScript (Render=True)", value=False)

if st.button("Buscar Dados via Scrape.do", type="primary"):
    with st.spinner("Solicitando dados através dos proxies do Scrape.do..."):
        try:
            # Codifica a URL de destino para o formato da API
            url_codificada = quote(url)
            
            # Monta a URL de requisição do Scrape.do
            scrape_url = f"https://api.scrape.do/?token={token}&url={url_codificada}"
            
            if render_js:
                scrape_url += "&render=true"
                
            # Faz a requisição HTTP simples (o Scrape.do resolve o IP e o Cloudflare)
            resposta = requests.get(scrape_url, timeout=30)
            
            # Exibe o Status da Resposta do Scrape.do
            st.subheader("Status da Requisição")
            if resposta.status_code == 200:
                st.success(f"Sucesso! Status Code: {resposta.status_code}")
            else:
                st.warning(f"Aviso! Gateway Status Code: {resposta.status_code}")
            
            # Processa e exibe o JSON direto
            st.subheader("Dados do JSON")
            try:
                dados_json = resposta.json()
                st.json(dados_json)
            except ValueError:
                try:
                    dados_json = json.loads(resposta.text)
                    st.json(dados_json)
                except ValueError:
                    st.error("A resposta recebida ainda não é um JSON válido.")
                    st.text_area("Resposta bruta recebida:", value=resposta.text, height=300)
                    
        except requests.exceptions.RequestException as e:
            st.error(f"Erro ao conectar na API do Scrape.do: {e}")
