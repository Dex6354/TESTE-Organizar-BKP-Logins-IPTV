import streamlit as st
import json
import time

# Tenta curl_cffi primeiro (melhor para anti-bot), fallback para requests
try:
    from curl_cffi import requests as cffi_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

import requests as std_requests

st.set_page_config(page_title="🛠️ API Debugger", layout="wide")
st.title("🛠️ Python Streamlit API Debugger")

# --- URL Input ---
url = st.text_input(
    "URL da API para Debug:",
    value="https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
)

# --- Advanced Options ---
with st.expander("⚙️ Opções Avançadas"):
    col1, col2 = st.columns(2)
    with col1:
        timeout = st.number_input("Timeout (segundos)", min_value=1, max_value=60, value=15)
        verify_ssl = st.checkbox("Verificar SSL", value=False)
        allow_redirects = st.checkbox("Seguir redirecionamentos", value=True)
    with col2:
        method = st.selectbox("Método HTTP", ["GET", "POST", "PUT", "DELETE"])
        if CURL_CFFI_AVAILABLE:
            engine = st.selectbox(
                "Engine HTTP",
                ["curl_cffi (Chrome120)", "curl_cffi (Chrome110)", "curl_cffi (Firefox110)", "requests (padrão)"],
            )
        else:
            engine = "requests (padrão)"
            st.info("💡 Instale `curl_cffi` para bypass de anti-bot:\n```\npip install curl_cffi\n```")

    st.markdown("**Headers Customizados**")
    user_agent = st.text_input(
        "User-Agent",
        value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    )
    accept = st.text_input("Accept", value="*/*")
    extra_headers_raw = st.text_area("Headers extras (formato JSON)", value='{}', height=80)

    body_raw = ""
    if method in ["POST", "PUT"]:
        body_raw = st.text_area("Body (JSON)", value="{}", height=100)

# --- Executar ---
if st.button("🚀 Executar Requisição", use_container_width=True):

    try:
        extra = json.loads(extra_headers_raw)
    except json.JSONDecodeError:
        extra = {}
        st.warning("⚠️ Headers extras inválidos — ignorados.")

    body = None
    if method in ["POST", "PUT"]:
        try:
            body = json.loads(body_raw)
        except json.JSONDecodeError:
            st.warning("⚠️ Body inválido — ignorado.")

    with st.spinner("Aguardando resposta..."):
        start = time.time()
        response = None
        error_msg = None

        try:
            # --- curl_cffi engine ---
            if "curl_cffi" in engine and CURL_CFFI_AVAILABLE:
                impersonate_map = {
                    "curl_cffi (Chrome120)": "chrome120",
                    "curl_cffi (Chrome110)": "chrome110",
                    "curl_cffi (Firefox110)": "firefox110",
                }
                imp = impersonate_map.get(engine, "chrome120")

                headers = {"User-Agent": user_agent, "Accept": accept}
                headers.update(extra)

                response = cffi_requests.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body else None,
                    timeout=timeout,
                    verify=verify_ssl,
                    allow_redirects=allow_redirects,
                    impersonate=imp,
                )

            # --- requests padrão ---
            else:
                headers = {
                    "User-Agent": user_agent,
                    "Accept": accept,
                    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                }
                headers.update(extra)

                session = std_requests.Session()
                response = session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=body if body else None,
                    timeout=timeout,
                    verify=verify_ssl,
                    allow_redirects=allow_redirects,
                )

        except Exception as e:
            error_msg = str(e)

        elapsed = time.time() - start

        if error_msg:
            st.error(f"💥 Erro: {error_msg}")
        elif response is not None:
            # --- Status ---
            st.markdown("---")
            st.subheader("📡 Status da Requisição")
            status = response.status_code
            color = "🟢" if 200 <= status < 300 else ("🟡" if status < 500 else "🔴")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Status Code", f"{color} {status}")
            c2.metric("Tempo de Resposta", f"{elapsed:.3f}s")
            c3.metric("Tamanho", f"{len(response.content) / 1024:.2f} KB")
            final_url = str(response.url)
            c4.metric("URL Final", final_url[:35] + "..." if len(final_url) > 35 else final_url)

            status_msgs = {
                200: ("success", "✅ Sucesso!"),
                403: ("error", "🚫 403 — Acesso negado. Tente curl_cffi."),
                406: ("error", "❌ 406 — Servidor rejeitou o Accept header ou TLS fingerprint. Use curl_cffi Chrome120."),
                404: ("error", "❌ 404 — Endpoint não encontrado."),
                301: ("warning", "🔀 301 — Redirecionamento permanente."),
                302: ("warning", "🔀 302 — Redirecionamento temporário."),
            }
            if status in status_msgs:
                kind, msg = status_msgs[status]
                getattr(st, kind)(msg)
            elif not (200 <= status < 300):
                st.warning(f"⚠️ Status Code: {status}")

            # Redirecionamentos
            if hasattr(response, "history") and response.history:
                with st.expander(f"🔀 Redirecionamentos ({len(response.history)})"):
                    for r in response.history:
                        st.write(f"→ `{r.status_code}` {r.url}")
                    st.write(f"✅ Final: `{status}` {response.url}")

            # Headers resposta
            with st.expander("📋 Headers da Resposta"):
                st.json(dict(response.headers))

            # --- JSON ---
            st.markdown("---")
            st.subheader("📦 Dados do JSON")

            parsed_json = None
            try:
                parsed_json = response.json()
            except Exception:
                try:
                    text = response.text.strip()
                    if text.startswith("{") or text.startswith("["):
                        parsed_json = json.loads(text)
                except Exception:
                    pass

            if parsed_json is not None:
                st.success("✅ JSON válido recebido!")
                st.json(parsed_json)

                json_str = json.dumps(parsed_json, indent=2, ensure_ascii=False)
                st.download_button("⬇️ Baixar JSON", data=json_str, file_name="response.json", mime="application/json")

                # Xtream Codes
                if "user_info" in parsed_json or "server_info" in parsed_json:
                    st.markdown("---")
                    st.subheader("🎯 Xtream Codes API")
                    col1, col2 = st.columns(2)
                    if "user_info" in parsed_json:
                        with col1:
                            st.markdown("**👤 user_info**")
                            for k, v in parsed_json["user_info"].items():
                                st.write(f"• **{k}**: `{v}`")
                    if "server_info" in parsed_json:
                        with col2:
                            st.markdown("**🖥️ server_info**")
                            for k, v in parsed_json["server_info"].items():
                                st.write(f"• **{k}**: `{v}`")
            else:
                content_type = response.headers.get("Content-Type", "")
                st.error("❌ A resposta não é um JSON válido.")
                st.markdown(f"**Content-Type:** `{content_type}`")
                preview = response.text[:3000]
                lang = "html" if "<html" in preview.lower() else "text"
                st.code(preview, language=lang)

# --- Preview headers ---
with st.expander("🔍 Ver headers que serão enviados"):
    preview_h = {"User-Agent": user_agent, "Accept": accept}
    try:
        preview_h.update(json.loads(extra_headers_raw))
    except Exception:
        pass
    if "curl_cffi" in (engine if CURL_CFFI_AVAILABLE else ""):
        st.info("ℹ️ curl_cffi adiciona automaticamente headers TLS/HTTP2 do Chrome — não visíveis aqui.")
    st.json(preview_h)

# --- Status da engine ---
st.sidebar.markdown("## 🔧 Engine Status")
if CURL_CFFI_AVAILABLE:
    st.sidebar.success("✅ curl_cffi disponível")
else:
    st.sidebar.warning("⚠️ curl_cffi não instalado\n\n`pip install curl_cffi`")
st.sidebar.info("curl_cffi faz impersonação real do TLS do Chrome, resolvendo 403/406 em servidores com anti-bot.")
