import streamlit as st
import requests

st.set_page_config(page_title="Proxy Request Integration", layout="centered")

st.title("Proxy Request Integration")
st.write("Requisição utilizando um Proxy Público Gratuito do Brasil.")

# URL final de destino
TARGET_URL = "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

# IP e Porta de um proxy público brasileiro de exemplo
# Substitua por outro caso este fique offline
PROXY_BR = "191.40.5.0:8888" 

proxies = {
    "http": f"http://{PROXY_BR}",
    "https": f"http://{PROXY_BR}"
}

if st.button("Executar Requisição", type="primary"):
    with st.spinner("Aguardando resposta através do proxy brasileiro..."):
        try:
            # Realiza a requisição passando o dicionário de proxies e um timeout menor
            response = requests.get(TARGET_URL, proxies=proxies, timeout=10)
            
            # Exibe metadados da requisição
            st.subheader("Informações da Requisição")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Status Code", response.status_code)
            with col2:
                st.metric("Proxy Utilizado", PROXY_BR)

            # Exibe o conteúdo retornado
            st.subheader("Conteúdo da Resposta")
            try:
                st.json(response.json())
            except ValueError:
                st.text(response.text)

        except requests.exceptions.ProxyError:
            st.error("Erro de Proxy: O IP configurado recusou a conexão ou está offline.")
        except requests.exceptions.Timeout:
            st.error("Erro de Timeout: O proxy demorou muito para responder.")
        except Exception as e:
            st.error(f"Erro ao conectar: {e}")
