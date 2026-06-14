import streamlit as st
import json

# Usamos curl_cffi em vez do requests padrão para clonar o TLS do Chrome
try:
    from curl_cffi import requests
except ImportError:
    st.error("Instale a biblioteca necessária executando: pip install curl_cffi")
    st.stop()

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Python Streamlit API Debugger")

# URL fornecida pelo usuário
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

# Input para a URL
url = st.text_input("URL da API para Debug:", value=url_padrao)

if st.button("Buscar Dados / Enviar Requisição", type="primary"):
    with st.spinner("Conectando à API mascarando o TLS..."):
        try:
            # O parâmetro impersonate="chrome" faz a mágica de fingir ser o Chrome real no nível de rede
            resposta = requests.get(url, impersonate="chrome", timeout=15)
            
            # Exibe o Status Code
            st.subheader("Status da Requisição")
            if resposta.status_code == 200:
                st.success(f"Sucesso! Status Code: {resposta.status_code}")
            else:
                st.warning(f"Aviso! Status Code: {resposta.status_code}")
            
            # Tenta parsear e exibir o JSON
            st.subheader("Dados do JSON")
            try:
                dados_json = resposta.json()
                st.json(dados_json)
            except Exception:
                # Caso venha string misturada, tenta forçar um decode
                try:
                    dados_json = json.loads(resposta.text)
                    st.json(dados_json)
                except ValueError:
                    st.error("A resposta recebida não é um JSON válido.")
                    st.text_area("Resposta bruta (Texto):", value=resposta.text, height=300)
                
        except Exception as e:
            st.error(f"Erro de conexão ao tentar acessar a API: {e}")
