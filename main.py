import streamlit as st
import requests
import json
from urllib.parse import quote

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Streamlit Cloud API Debugger (Scrape.do Premium)")

# URL padrão
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"
url = st.text_input("URL da API para Debug:", value=url_padrao)
token = st.text_input("Scrape.do Token:", value="3a23ea3810a04b16bccfac96a2c3b1af73c97a98ef5", type="password")

# Controles para forçar o Bypass do Erro 406 e bloqueios
col1, col2, col3 = st.columns(3)
with col1:
    corrigir_406 = st.checkbox("Forçar Accept */* (Corrige Erro 406)", value=True)
with col2:
    usar_super = st.checkbox("Ativar Super Proxy (Residencial)", value=False)
with col3:
    render_js = st.checkbox("Renderizar JavaScript", value=False)

if st.button("Buscar Dados via Scrape.do", type="primary"):
    with st.spinner("Processando requisição através do Scrape.do..."):
        try:
            url_codificada = quote(url)
            scrape_url = f"https://api.scrape.do/?token={token}&url={url_codificada}"
            
            headers = {}
            
            # Correção do 406: Avisa o Scrape.do para usar nossos cabeçalhos limpos
            if corrigir_406:
                scrape_url += "&customHeaders=true"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept": "*/*",  # Remove a rejeição do Nginx do IPTV
                    "Accept-Language": "*",
                    "Connection": "keep-alive"
                }
                
            if usar_super:
                scrape_url += "&super=true"
            if render_js:
                scrape_url += "&render=true"
                
            # Executa a chamada
            resposta = requests.get(scrape_url, headers=headers, timeout=40)
            
            st.subheader("Status da Requisição")
            st.write(f"**Status Code:** {resposta.status_code}")
            
            st.subheader("Dados do JSON")
            try:
                dados_json = resposta.json()
                st.success("Sucesso! O JSON foi retornado direto.")
                st.json(dados_json)
            except ValueError:
                try:
                    dados_json = json.loads(resposta.text)
                    st.json(dados_json)
                except ValueError:
                    st.error("A resposta recebida não pôde ser convertida em JSON.")
                    st.text_area("Conteúdo bruto retornado:", value=resposta.text, height=350)
                    
        except Exception as e:
            st.error(f"Erro na conexão: {e}")
