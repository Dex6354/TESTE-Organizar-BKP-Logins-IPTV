import streamlit as st
import requests

st.set_page_config(page_title="Geonode Integration", layout="centered")

st.title("Geonode Integration")
st.write("Requisição utilizando Proxies e Geo-Targeting Brasil via Geonode.")

# Configurações da API Geonode
API_URL = "https://scraper.geonode.io/v1/extract"
API_KEY = "4c6317bd-c28f-4816-8a92-a3d8f362a6fa"
TARGET_URL = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

payload = {
    "url": TARGET_URL,
    "formats": ["html"],
    "render_js": False,
    "processing_mode": "sync",
    "proxy": {
        "country": "BR",  # Mantido o Geo-Targeting para o Brasil
        "type": "datacenter"
    }
}

if st.button("Executar Requisição", type="primary"):
    with st.spinner("Aguardando resposta do Geonode..."):
        try:
            # Alterado para POST conforme especificação da Geonode
            response = requests.post(API_URL, json=payload, headers=headers)
            
            # Exibe metadados úteis
            st.subheader("Informações da Requisição")
            st.metric("Status Code", response.status_code)
            
            # Exibe o conteúdo retornado
            st.subheader("Conteúdo da Resposta")
            try:
                st.json(response.json())
            except ValueError:
                st.text(response.text)

        except Exception as e:
            st.error(f"Erro ao conectar com a API: {e}")
