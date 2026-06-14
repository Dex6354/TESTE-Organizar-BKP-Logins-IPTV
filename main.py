import streamlit as st
import httpx
import json

# Trava de segurança para garantir que o HTTP/2 está disponível
try:
    import h2
except ImportError:
    st.error("⚠️ Falta o suporte para HTTP/2 no seu ambiente!")
    st.warning("Pare a aplicação e execute no terminal:\n\n`pip install \"httpx[http2]\"`")
    st.stop()

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Debugger Avançado (HTTP/2 & Headers)")

# URL fornecida pelo usuário
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

url = st.text_input("URL da API:", value=url_padrao)
usar_http2 = st.checkbox("Forçar protocolo HTTP/2 (Evita bloqueios Nginx)", value=True)

if st.button("Executar Debug Profundo", type="primary"):
    with st.spinner("Analisando tráfego e forçando conexão..."):
        try:
            # Headers básicos e limpos
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            }

            # Usando httpx para suporte a HTTP/2
            with httpx.Client(http2=usar_http2, verify=False) as client:
                resposta = client.get(url, headers=headers, timeout=15, follow_redirects=True)

            # --- DEBUGGER VISUAL ---
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📡 Requisição (Enviado)")
                st.write(f"**Versão HTTP:** {resposta.http_version}")
                st.json(dict(resposta.request.headers))

            with col2:
                st.subheader("📥 Resposta (Recebido)")
                st.write(f"**Status Code:** {resposta.status_code}")
                st.json(dict(resposta.headers))

            # --- RESULTADO FINAL ---
            st.divider()
            st.subheader("📦 Dados Retornados")
            
            if resposta.status_code == 200:
                try:
                    dados_json = resposta.json()
                    st.success("JSON processado com sucesso!")
                    st.json(dados_json)
                except json.JSONDecodeError:
                    st.error("O servidor retornou Status 200, mas o conteúdo não é JSON.")
                    st.code(resposta.text, language="html")
            else:
                st.warning(f"O servidor ainda rejeitou a conexão. Código: {resposta.status_code}")
                st.code(resposta.text, language="html")

        except Exception as e:
            st.error(f"Erro fatal de conexão: {e}")

st.info("💡 **Dica Diagnóstica:** Se o Status 406 continuar mesmo com HTTP/2 ativado, **o bloqueio é 100% no seu IP**. Você precisará rodar este código localmente na sua máquina (`localhost`), pois IPs de hospedagem em nuvem estão na blacklist do servidor.")
