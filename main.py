import streamlit as st
import requests
import json
from urllib.parse import quote

st.set_page_config(
    page_title="Xtream API Debugger",
    layout="wide"
)

st.title("🛠️ Xtream API Debugger")

url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

url = st.text_input(
    "URL da API",
    value=url_padrao
)

token = st.text_input(
    "Token Scrape.do",
    value="",
    type="password"
)

col1, col2, col3 = st.columns(3)

with col1:
    usar_super = st.checkbox(
        "Super Proxy",
        value=True
    )

with col2:
    render_js = st.checkbox(
        "Render JS",
        value=False
    )

with col3:
    tentativas = st.number_input(
        "Tentativas",
        min_value=1,
        max_value=20,
        value=5
    )

if st.button("🚀 Executar Testes", type="primary"):

    if not token:
        st.error("Informe o token do Scrape.do")
        st.stop()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Connection": "keep-alive"
    }

    sucessos = 0
    falhas = 0

    for tentativa in range(1, tentativas + 1):

        st.markdown("---")
        st.subheader(f"🔎 Tentativa {tentativa}")

        try:

            scrape_url = (
                f"https://api.scrape.do/"
                f"?token={token}"
                f"&url={quote(url)}"
            )

            if usar_super:
                scrape_url += "&super=true"

            if render_js:
                scrape_url += "&render=true"

            scrape_url += "&customHeaders=true"

            resposta = requests.get(
                scrape_url,
                headers=headers,
                timeout=60
            )

            st.write("### Status")

            col_a, col_b, col_c = st.columns(3)

            with col_a:
                st.metric("HTTP", resposta.status_code)

            with col_b:
                st.metric(
                    "Tamanho",
                    f"{len(resposta.text):,}"
                )

            with col_c:
                st.metric(
                    "Content-Type",
                    resposta.headers.get(
                        "content-type",
                        "-"
                    )
                )

            st.write("### Headers")

            st.json(dict(resposta.headers))

            st.write("### Informações Cloudflare")

            st.code(
                f"CF-RAY: {resposta.headers.get('cf-ray', 'N/A')}\n"
                f"Server: {resposta.headers.get('server', 'N/A')}"
            )

            texto = resposta.text

            eh_json = False

            try:
                dados = resposta.json()

                if isinstance(dados, dict):
                    eh_json = True

            except Exception:
                pass

            if not eh_json:
                try:
                    dados = json.loads(texto)

                    if isinstance(dados, dict):
                        eh_json = True

                except Exception:
                    pass

            if eh_json:

                sucessos += 1

                st.success("✅ JSON retornado com sucesso")

                st.write("### JSON")

                st.json(dados)

                try:

                    auth = (
                        dados
                        .get("user_info", {})
                        .get("auth")
                    )

                    status = (
                        dados
                        .get("user_info", {})
                        .get("status")
                    )

                    st.write("### Resumo")

                    st.code(
                        f"Auth: {auth}\n"
                        f"Status: {status}"
                    )

                except Exception:
                    pass

            else:

                falhas += 1

                st.error("❌ Não retornou JSON")

                st.write("### Primeiros 1000 caracteres")

                st.text(texto[:1000])

                if "Welcome to nginx" in texto:
                    st.warning(
                        "Detectado: Welcome to nginx "
                        "(possível bloqueio por IP/ASN)"
                    )

                elif "Error..." in texto:
                    st.warning(
                        "Detectado: Error... "
                        "(possível bloqueio Cloudflare)"
                    )

        except Exception as e:

            falhas += 1

            st.exception(e)

    st.markdown("---")

    st.header("📊 Resultado Final")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Sucessos",
            sucessos
        )

    with col2:
        st.metric(
            "Falhas",
            falhas
        )

    with col3:
        percentual = (
            round(
                (sucessos / tentativas) * 100,
                1
            )
            if tentativas
            else 0
        )

        st.metric(
            "Taxa de Sucesso",
            f"{percentual}%"
        )

    if sucessos > 0 and falhas > 0:
        st.warning(
            "O Scrape.do parece estar alternando entre "
            "IPs/proxies diferentes. Algumas tentativas "
            "foram aceitas e outras bloqueadas."
        )

    elif sucessos == 0:
        st.error(
            "Nenhuma tentativa retornou JSON."
        )

    else:
        st.success(
            "Todas as tentativas retornaram JSON."
        )
