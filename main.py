import streamlit as st
import requests

st.set_page_config(page_title="Proxy Direto Integration", layout="centered")

st.title("Requisição Direta via Proxy")
st.write("Testando a conexão sem scrape.do, configurando Proxy Residencial e Geo-Targeting Brasil manualmente.")

# Campos para inserir as credenciais do seu provedor de Proxy Residencial
proxy_host = st.text_input("Proxy Host / Gateway", placeholder="ex: pr.oxylabs.io ou br.smartproxy.com")
proxy_port = st.text_input("Proxy Port", placeholder="ex: 7777 ou 10000")
proxy_user = st.text_input("Proxy Username")
proxy_pass = st.text_input("Proxy Password", type="password")

TARGET_URL = "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

if st.button("Executar Requisição", type="primary"):
    if not all([proxy_host, proxy_port, proxy_user, proxy_pass]):
        st.error("Por favor, preencha todos os campos do seu provedor de proxy.")
    else:
        with st.spinner("Executando requisição via proxy residencial..."):
            
            # Força o Geo-Targeting Brasil adicionando o parâmetro no formato padrão dos provedores
            if "country" not in proxy_user.lower():
                user_with_geo = f"{proxy_user}-country-BR"
            else:
                user_with_geo = proxy_user

            # Monta a string de conexão do proxy
            proxy_url = f"http://{user_with_geo}:{proxy_pass}@{proxy_host}:{proxy_port}"
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }

            try:
                # Requisição direta passando o dicionário de proxies
                response = requests.get(TARGET_URL, proxies=proxies, timeout=30)
                
                st.subheader("Informações da Resposta")
                st.metric("Status Code", response.status_code)

                st.subheader("Conteúdo da Resposta")
                try:
                    st.json(response.json())
                except ValueError:
                    st.text(response.text)

            except Exception as e:
                st.error(f"Erro ao conectar através do proxy: {e}")
