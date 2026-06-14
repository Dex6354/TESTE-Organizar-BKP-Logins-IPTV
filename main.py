import streamlit as st
import cloudscraper
import json

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Python Streamlit API Debugger (Cloudflare Bypass)")

# URL completa fornecida
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

# Input para a URL
url = st.text_input("URL da API para Debug:", value=url_padrao)

if st.button("Buscar Dados / Enviar Requisição", type="primary"):
    with st.spinner("Burlando proteção do Cloudflare..."):
        try:
            # Cria um cliente scraper que imita perfeitamente um navegador contra o Cloudflare
            scraper = cloudscraper.create_scraper()
            resposta = scraper.get(url, timeout=15)
            
            # Exibe o Status Code
            st.subheader("Status da Requisição")
            if resposta.status_code == 200:
                st.success(f"Sucesso! Status Code: {resposta.status_code}")
            else:
                st.warning(f"Aviso! Status Code: {resposta.status_code}")
            
            # Tenta parsear e exibir o JSON direto
            st.subheader("Dados do JSON")
            try:
                dados_json = resposta.json()
                st.json(dados_json)
            except ValueError:
                try:
                    # Segunda tentativa caso venha como string pura
                    dados_json = json.loads(resposta.text)
                    st.json(dados_json)
                except ValueError:
                    st.error("A resposta recebida não é um JSON válido.")
                    st.text_area("Resposta bruta (Texto):", value=resposta.text, height=300)
                
        except Exception as e:
            st.error(f"Erro de conexão ao tentar acessar a API: {e}")
