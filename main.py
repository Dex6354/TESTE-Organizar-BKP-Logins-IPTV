import streamlit as st
import requests

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Python Streamlit API Debugger")

# URL fornecida pelo usuário
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

# Input para a URL
url = st.text_input("URL da API para Debug:", value=url_padrao)

if st.button("Buscar Dados / Enviar Requisição", type="primary"):
    with st.spinner("Conectando à API..."):
        try:
            # Cabeçalhos para simular um navegador real e evitar o erro 403
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*"
            }
            
            # Faz a requisição HTTP GET com os headers
            resposta = requests.get(url, headers=headers, timeout=15)
            
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
            except ValueError:
                st.error("A resposta recebida não é um JSON válido.")
                st.text_area("Resposta bruta (Texto):", value=resposta.text, height=300)
                
        except requests.exceptions.RequestException as e:
            st.error(f"Erro de conexão ao tentar acessar a API: {e}")
