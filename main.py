import streamlit as st
import json
import time
import subprocess
import shutil
import re

try:
    from curl_cffi import requests as cffi_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

import requests as std_requests

CURL_BIN = shutil.which("curl")

st.set_page_config(page_title="🛠️ API Debugger", layout="wide")
st.title("🛠️ Python Streamlit API Debugger")

url = st.text_input(
    "URL da API para Debug:",
    value="https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
)

# Headers exatos capturados do browser Brave/Chromium
BROWSER_HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "pt-BR,pt;q=0.6",
    "cache-control": "max-age=0",
    "priority": "u=0, i",
    "sec-ch-ua": '"Brave";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
}

def try_parse_json(text):
    try:
        return json.loads(text)
    except Exception:
        t = text.strip()
        if t.startswith("{") or t.startswith("["):
            try:
                return json.loads(t)
            except Exception:
                pass
    return None

def show_json_result(parsed, key_suffix=""):
    st.success("✅ JSON válido recebido!")
    st.json(parsed)
    st.download_button(
        "⬇️ Baixar JSON",
        json.dumps(parsed, indent=2, ensure_ascii=False),
        "response.json", "application/json",
        key=f"dl_{key_suffix}",
    )
    if "user_info" in parsed or "server_info" in parsed:
        st.markdown("---")
        st.subheader("🎯 Xtream Codes API")
        c1, c2 = st.columns(2)
        if "user_info" in parsed:
            with c1:
                st.markdown("**👤 user_info**")
                for k, v in parsed["user_info"].items():
                    st.write(f"• **{k}**: `{v}`")
        if "server_info" in parsed:
            with c2:
                st.markdown("**🖥️ server_info**")
                for k, v in parsed["server_info"].items():
                    st.write(f"• **{k}**: `{v}`")

def show_error(text, status):
    st.error(f"❌ Status {status} — resposta não é JSON válido.")
    preview = text[:3000]
    st.code(preview, language="html" if "<html" in preview.lower() else "text")

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab_main, tab_curl, tab_manual = st.tabs([
    "🚀 Requisição Principal",
    "📋 Colar cURL do Browser",
    "🔧 Manual / Debug",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — REQUISIÇÃO PRINCIPAL (com headers do browser)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_main:
    st.info("Usa os headers exatos capturados do seu browser Brave/Chrome que retornou 200 OK.")

    with st.expander("📋 Headers configurados (do seu browser)"):
        st.json(BROWSER_HEADERS)

    col1, col2 = st.columns(2)
    with col1:
        engine_main = st.selectbox(
            "Engine",
            ["curl_cffi (Chrome149)" if CURL_CFFI_AVAILABLE else "requests (padrão)",
             "requests (padrão)",
             "curl sistema"],
            key="eng_main",
        )
    with col2:
        redir_main = st.checkbox("Seguir redirects", True, key="redir_main")

    if st.button("🚀 Executar com Headers do Browser", use_container_width=True):
        with st.spinner("Requisitando..."):
            t0 = time.time()
            parsed = None
            status = None
            text = ""
            err = None

            try:
                if "curl_cffi" in engine_main and CURL_CFFI_AVAILABLE:
                    r = cffi_requests.get(
                        url,
                        headers=BROWSER_HEADERS,
                        timeout=15,
                        verify=False,
                        allow_redirects=redir_main,
                        impersonate="chrome110",  # mais próximo do Brave 149
                    )
                    status, text = r.status_code, r.text

                elif "curl sistema" in engine_main and CURL_BIN:
                    cmd = [CURL_BIN, "-s",
                           "-w", "\n___STATUS:%{http_code}",
                           "--compressed", "-k",
                           "--max-time", "15"]
                    for k, v in BROWSER_HEADERS.items():
                        cmd += ["-H", f"{k}: {v}"]
                    if not redir_main:
                        cmd += ["--max-redirs", "0"]
                    cmd.append(url)
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                    out = result.stdout
                    if "___STATUS:" in out:
                        parts = out.rsplit("___STATUS:", 1)
                        text = parts[0]
                        status = int(parts[1].strip())
                    else:
                        text = out
                        status = 0

                else:
                    s = std_requests.Session()
                    r = s.get(url, headers=BROWSER_HEADERS, timeout=15,
                              verify=False, allow_redirects=redir_main)
                    status, text = r.status_code, r.text

            except Exception as e:
                err = str(e)

            elapsed = time.time() - t0

        if err:
            st.error(f"💥 {err}")
        else:
            color = "🟢" if 200 <= status < 300 else "🔴"
            c1, c2, c3 = st.columns(3)
            c1.metric("Status Code", f"{color} {status}")
            c2.metric("Tempo", f"{elapsed:.3f}s")
            c3.metric("Tamanho", f"{len(text)/1024:.2f} KB")
            st.markdown("---")
            parsed = try_parse_json(text)
            if parsed:
                show_json_result(parsed, "main")
            else:
                show_error(text, status)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — COLAR cURL DO BROWSER
# ═══════════════════════════════════════════════════════════════════════════════
with tab_curl:
    st.markdown("""
    **F12 → Network → requisição → botão direito → Copy as cURL (bash)** → cole abaixo:
    """)

    curl_pasted = st.text_area("Cole o cURL aqui:", height=150,
        placeholder="curl 'https://websmt.ca/player_api.php?...' -H 'sec-ch-ua: ...' ...")

    if curl_pasted.strip():
        if st.button("▶️ Executar cURL Exato", use_container_width=True) and CURL_BIN:
            clean = re.sub(r"\\\s*\n", " ", curl_pasted.strip())
            cmd_str = clean.replace("curl ", f"curl -s -w '\\n___STATUS:%{{http_code}}' ", 1)
            with st.spinner("Executando..."):
                t0 = time.time()
                try:
                    res = subprocess.run(cmd_str, shell=True, capture_output=True, text=True, timeout=25)
                    elapsed = time.time() - t0
                    out = res.stdout
                    if "___STATUS:" in out:
                        parts = out.rsplit("___STATUS:", 1)
                        body = parts[0]
                        status = int(parts[1].strip())
                    else:
                        body, status = out, 0
                    color = "🟢" if 200 <= status < 300 else "🔴"
                    c1, c2 = st.columns(2)
                    c1.metric("Status", f"{color} {status}")
                    c2.metric("Tempo", f"{elapsed:.2f}s")
                    parsed = try_parse_json(body)
                    if parsed:
                        show_json_result(parsed, "curl_exact")
                    else:
                        show_error(body, status)
                except Exception as e:
                    st.error(f"💥 {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — MANUAL
# ═══════════════════════════════════════════════════════════════════════════════
with tab_manual:
    with st.expander("⚙️ Opções", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            tm = st.number_input("Timeout", 1, 60, 15, key="tm")
            vm = st.checkbox("Verificar SSL", False, key="vm")
            rm = st.checkbox("Seguir redirects", True, key="rm")
        with c2:
            mm = st.selectbox("Método", ["GET","POST","PUT","DELETE"], key="mm")
            engines = ["curl_cffi (Chrome110)", "requests (padrão)"]
            if CURL_BIN:
                engines.append("curl sistema")
            em = st.selectbox("Engine", engines, key="em")

        use_browser_h = st.checkbox("Usar headers do browser (recomendado)", True, key="ubh")
        exm = st.text_area("Headers extras ou substituição (JSON)", "{}", 80, key="exm")
        ckm = st.text_area("Cookies (key=val; key2=val2)", "", 50, key="ckm")

    if st.button("🚀 Executar", use_container_width=True, key="run_m"):
        try:
            extra = json.loads(exm)
        except Exception:
            extra = {}

        headers = dict(BROWSER_HEADERS) if use_browser_h else {}
        headers.update(extra)

        cookies = {}
        for part in ckm.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookies[k.strip()] = v.strip()

        t0 = time.time()
        try:
            if "curl_cffi" in em and CURL_CFFI_AVAILABLE:
                r = cffi_requests.request(mm, url, headers=headers, cookies=cookies,
                    timeout=tm, verify=vm, allow_redirects=rm, impersonate="chrome110")
                status, text = r.status_code, r.text
            elif "curl sistema" in em and CURL_BIN:
                cmd = [CURL_BIN, "-s", "-w", "\n___STATUS:%{http_code}",
                       "--compressed", "-k", "--max-time", str(tm)]
                for k, v in headers.items():
                    cmd += ["-H", f"{k}: {v}"]
                for k, v in cookies.items():
                    cmd += ["-b", f"{k}={v}"]
                cmd.append(url)
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=tm+5)
                out = res.stdout
                if "___STATUS:" in out:
                    parts = out.rsplit("___STATUS:", 1)
                    text = parts[0]
                    status = int(parts[1].strip())
                else:
                    text, status = out, 0
            else:
                s = std_requests.Session()
                r = s.request(mm, url, headers=headers, cookies=cookies,
                    timeout=tm, verify=vm, allow_redirects=rm)
                status, text = r.status_code, r.text
            elapsed = time.time() - t0

            color = "🟢" if 200 <= status < 300 else "🔴"
            c1, c2, c3 = st.columns(3)
            c1.metric("Status", f"{color} {status}")
            c2.metric("Tempo", f"{elapsed:.3f}s")
            c3.metric("Tamanho", f"{len(text)/1024:.2f} KB")
            parsed = try_parse_json(text)
            st.markdown("---")
            if parsed:
                show_json_result(parsed, "manual")
            else:
                show_error(text, status)
        except Exception as e:
            st.error(f"💥 {e}")

# Sidebar
st.sidebar.markdown("## 🔧 Status")
if CURL_CFFI_AVAILABLE:
    st.sidebar.success("✅ curl_cffi")
else:
    st.sidebar.warning("⚠️ pip install curl_cffi")
if CURL_BIN:
    st.sidebar.success(f"✅ curl: {CURL_BIN}")
else:
    st.sidebar.warning("⚠️ curl não encontrado")
st.sidebar.markdown("---")
st.sidebar.markdown("## ℹ️ Por que funcionou no browser?")
st.sidebar.info(
    "O Cloudflare verificava os headers:\n\n"
    "- `sec-ch-ua` (fingerprint do browser)\n"
    "- `sec-fetch-*` (contexto de navegação)\n"
    "- `sec-gpc` (Global Privacy Control)\n\n"
    "Sem eles, retornava 406. Agora estão incluídos."
)
