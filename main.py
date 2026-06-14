import streamlit as st
import requests
from urllib.parse import quote

st.set_page_config(
    page_title="Xtream Login Validator",
    layout="centered"
)

st.title("📺 Xtream Login Validator")

usuario = st.text_input(
    "Usuário",
    value="concmus03"
)

senha = st.text_input(
    "Senha",
    value="3a3b3c3d",
    type="password"
)

token = st.text_input(
    "Token Scrape.do",
    type="password"
)

@st.cache_data(ttl=300)
def consultar_xtream(usuario, senha, token):

    url_alvo = (
        f"http://websmt.ca/player_api.php"
        f"?username={usuario}"
        f"&password={senha}"
    )

    scrape_url = (
        "https://api.scrape.do/"
        f"?token={token}"
        f"&url={quote(url_alvo, safe='')}"
        "&super=true"
        "&geoCode=BR"
    )

    resposta = requests.get(
        scrape_url,
        timeout=60
    )

    return {
        "status_code": resposta.status_code,
        "headers": dict(resposta.headers),
        "texto": resposta.text
    }

if st.button("🔍 Validar Login", type="primary"):

    if not token:
        st.error("Informe o token do Scrape.do")
        st.stop()

    try:

        resultado = consultar_xtream(
            usuario,
            senha,
            token
        )

        st.write("### Status")

        st.code(resultado["status_code"])

        st.write("### Créditos Restantes")

        st.code(
            resultado["headers"].get(
                "scrape.do-remaining-credits",
                "N/A"
            )
        )

        st.write("### Custo da Requisição")

        st.code(
            resultado["headers"].get(
                "scrape.do-request-cost",
                "N/A"
            )
        )

        try:

            dados = requests.models.complexjson.loads(
                resultado["texto"]
            )

            st.success("✅ JSON recebido com sucesso")

            st.json(dados)

            user_info = dados.get("user_info", {})

            auth = user_info.get("auth")
            status = user_info.get("status")
            exp_date = user_info.get("exp_date")

            st.write("### Resumo")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Auth", auth)

            with col2:
                st.metric("Status", status)

            with col3:
                st.metric("Exp Date", exp_date)

        except Exception:

            st.error("A resposta não é JSON")

            st.text_area(
                "Resposta recebida",
                resultado["texto"],
                height=300
            )

    except Exception as e:

        st.exception(e)
