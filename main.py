import streamlit as st
import requests

st.set_page_config(page_title="Requisição Direta", layout="centered")

st.title("Requisição Direta (Geo-Targeting Brasil)")
st.write("Testando a conexão direta, simulando localização do Brasil.")

TARGET_URL = "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

if st.button("Executar Requisição", type="primary"):
    with st.spinner("Executando requisição direta..."):
        
        # Define headers simulando origem do Brasil
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        try:
            # Requisição direta sem proxy
            response = requests.get(TARGET_URL, headers=headers, timeout=30)
            
            st.subheader("Informações da Resposta")
            st.metric("Status Code", response.status_code)

            st.subheader("Conteúdo da Resposta")
            try:
                st.json(response.json())
            except ValueError:
                st.text(response.text)

        except Exception as e:
            st.error(f"Erro ao conectar: {e}")
