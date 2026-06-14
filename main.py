import streamlit as st
import json

try:
    from curl_cffi import requests
except ImportError:
    st.error("Instale a biblioteca executando no terminal: pip install curl_cffi")
    st.stop()

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Python Streamlit API Debugger")

# URL fornecida pelo usuário
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

# Input para a URL
url = st.text_input("URL da API para Debug:", value=url_padrao)

if st.button("Buscar Dados / Enviar Requisição", type="primary"):
    with st.spinner("Simulando navegação real (Bypassing Nginx WAF)..."):
        try:
            # Cabeçalhos idênticos aos que o Chrome envia ao acessar a URL diretamente
            headers = {
                "Upgrade-Insecure-Requests": "1",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User": "?1",
                "Sec-Fetch-Dest": "document",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
            }
            
            # Executa clonando o comportamento e TLS do Chrome
            resposta = requests.get(url, headers=headers, impersonate="chrome", timeout=15)
            
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
                try:
                    dados_json = json.loads(resposta.text)
                    st.json(dados_json)
                except ValueError:
                    st.error("A resposta recebida não é um JSON válido.")
                    st.text_area("Resposta bruta (Texto):", value=resposta.text, height=300)
                
        except Exception as e:
            st.error(f"Erro de conexão: {e}")
