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
            # Cabeçalhos completos de um navegador real para evitar o bloqueio 406 do Nginx
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            # Usando uma sessão para gerenciar cookies automaticamente se o servidor exigir
            session = requests.Session()
            resposta = session.get(url, headers=headers, timeout=15)
            
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
