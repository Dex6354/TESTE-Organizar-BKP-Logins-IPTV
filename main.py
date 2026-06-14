import streamlit as st
import requests
import json
import time

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
        timeout = st.number_input("Timeout (segundos)", min_value=1, max_value=60, value=10)
        verify_ssl = st.checkbox("Verificar SSL", value=False)
    with col2:
        method = st.selectbox("Método HTTP", ["GET", "POST", "PUT", "DELETE"])

    st.markdown("**Headers Customizados**")
    user_agent = st.text_input(
        "User-Agent",
        value="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    )
    accept = st.text_input(
        "Accept",
        value="text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    )
    extra_headers_raw = st.text_area(
        "Headers extras (formato JSON)",
        value='{}',
        height=80,
    )

    body_raw = ""
    if method in ["POST", "PUT"]:
        body_raw = st.text_area("Body (JSON)", value="{}", height=100)

# --- Build Request ---
if st.button("🚀 Executar Requisição", use_container_width=True):
    headers = {
        "User-Agent": user_agent,
        "Accept": accept,
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    try:
        extra = json.loads(extra_headers_raw)
        headers.update(extra)
    except json.JSONDecodeError:
        st.warning("⚠️ Headers extras inválidos — ignorados.")

    body = None
    if method in ["POST", "PUT"]:
        try:
            body = json.loads(body_raw)
        except json.JSONDecodeError:
            st.warning("⚠️ Body inválido — ignorado.")

    with st.spinner("Aguardando resposta..."):
        start = time.time()
        try:
            session = requests.Session()
            response = session.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body else None,
                timeout=timeout,
                verify=verify_ssl,
                allow_redirects=True,
            )
            elapsed = time.time() - start

            # --- Status ---
            st.markdown("---")
            st.subheader("📡 Status da Requisição")
            col1, col2, col3, col4 = st.columns(4)
            status = response.status_code
            color = "🟢" if 200 <= status < 300 else ("🟡" if status < 500 else "🔴")
            col1.metric("Status Code", f"{color} {status}")
            col2.metric("Tempo de Resposta", f"{elapsed:.3f}s")
            col3.metric("Tamanho", f"{len(response.content) / 1024:.2f} KB")
            col4.metric("URL Final", response.url[:40] + "..." if len(response.url) > 40 else response.url)

            if 200 <= status < 300:
                st.success(f"✅ Sucesso! Status Code: {status}")
            elif status == 403:
                st.error("🚫 Acesso negado (403) — tente mudar o User-Agent.")
            elif status == 406:
                st.error("❌ Not Acceptable (406) — o servidor rejeitou o header Accept. Tente usar `text/html,*/*;q=0.9,*/*;q=0.8`")
            elif status == 404:
                st.error("❌ Não encontrado (404)")
            else:
                st.warning(f"⚠️ Status Code: {status}")

            # --- Histórico de redirecionamentos ---
            if response.history:
                with st.expander(f"🔀 Redirecionamentos ({len(response.history)})"):
                    for r in response.history:
                        st.write(f"→ `{r.status_code}` {r.url}")
                    st.write(f"✅ Final: `{response.status_code}` {response.url}")

            # --- Headers da Resposta ---
            with st.expander("📋 Headers da Resposta"):
                st.json(dict(response.headers))

            # --- Detecta Content-Type ---
            content_type = response.headers.get("Content-Type", "")

            # --- JSON ---
            st.markdown("---")
            st.subheader("📦 Dados do JSON")

            parsed_json = None
            try:
                parsed_json = response.json()
            except Exception:
                # Tenta forçar parse mesmo com content-type errado
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
                st.download_button(
                    "⬇️ Baixar JSON",
                    data=json_str,
                    file_name="response.json",
                    mime="application/json",
                )

                # --- Xtream Codes API ---
                if "user_info" in parsed_json or "server_info" in parsed_json:
                    st.markdown("---")
                    st.subheader("🎯 Dados Interpretados (Xtream Codes API)")
                    col1, col2 = st.columns(2)

                    if "user_info" in parsed_json:
                        with col1:
                            st.markdown("**👤 user_info**")
                            ui = parsed_json["user_info"]
                            for k, v in ui.items():
                                st.write(f"• **{k}**: `{v}`")

                    if "server_info" in parsed_json:
                        with col2:
                            st.markdown("**🖥️ server_info**")
                            si = parsed_json["server_info"]
                            for k, v in si.items():
                                st.write(f"• **{k}**: `{v}`")

            else:
                st.error("❌ A resposta não é um JSON válido.")
                st.markdown(f"**Content-Type recebido:** `{content_type}`")
                st.markdown("**Resposta bruta (Texto):**")
                preview = response.text[:3000]
                st.code(preview, language="html" if "<html" in preview.lower() else "text")

        except requests.exceptions.SSLError as e:
            st.error(f"🔐 Erro SSL: {e}\n\nDesative 'Verificar SSL' nas opções avançadas.")
        except requests.exceptions.ConnectionError as e:
            st.error(f"🔌 Erro de conexão: {e}")
        except requests.exceptions.Timeout:
            st.error(f"⏱️ Timeout após {timeout}s")
        except Exception as e:
            st.error(f"💥 Erro inesperado: {e}")

# --- Request Headers Preview ---
with st.expander("🔍 Ver headers que serão enviados"):
    preview_headers = {
        "User-Agent": user_agent,
        "Accept": accept,
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    try:
        extra = json.loads(extra_headers_raw)
        preview_headers.update(extra)
    except Exception:
        pass
    st.json(preview_headers)
