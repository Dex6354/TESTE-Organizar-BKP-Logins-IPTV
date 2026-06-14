import streamlit as st
import requests
import time

st.set_page_config(page_title="Geonode Integration", layout="centered")

st.title("Geonode Integration")
st.write("Requisição utilizando a configuração personalizada do Geonode (US Proxy).")

# Configurações da API Geonode
API_URL = "https://scraper.geonode.io/v1/extract"
API_KEY = "4c6317bd-c28f-4816-8a92-a3d8f362a6fa"
TARGET_URL = "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Payload atualizado conforme especificações fornecidas
payload = {
    "url": TARGET_URL,
    "formats": ["html", "markdown"],
    "render_js": False,
    "processing_mode": "sync",
    "proxy": {
        "country": "BR",
        "type": "datacenter"
    },
    "headers": {
        "Accept-Language": "en-US"
    }
}

if st.button("Executar Requisição", type="primary"):
    with st.spinner("Aguardando resposta do Geonode..."):
        max_retries = 3
        delay = 3  # Segundos de espera entre as tentativas
        response = None

        for attempt in range(max_retries):
            try:
                response = requests.post(API_URL, json=payload, headers=headers)
                
                # Se persistir o Rate Limit (429), aguarda o backoff e tenta de novo
                if response.status_code == 429:
                    if attempt < max_retries - 1:
                        st.warning(f"Limite de concorrência atingido. Tentativa {attempt + 1}/{max_retries}. Aguardando {delay}s...")
                        time.sleep(delay)
                        delay *= 2
                        continue
                
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                st.error(f"Erro ao conectar com a API: {e}")

        if response is not None:
            # Exibe os metadados
            st.subheader("Informações da Requisição")
            st.metric("Status Code", response.status_code)
            
            # Exibe o conteúdo retornado (JSON ou Texto)
            st.subheader("Conteúdo da Resposta")
            try:
                st.json(response.json())
            except ValueError:
                st.text(response.text)
        else:
            st.error("Falha ao obter resposta após várias tentativas.")
