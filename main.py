import streamlit as st
import json
import time

try:
    from curl_cffi import requests as cffi_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

import requests as std_requests

st.set_page_config(page_title="🛠️ API Debugger", layout="wide")
st.title("🛠️ Python Streamlit API Debugger")

url = st.text_input(
    "URL da API para Debug:",
    value="https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
)

# ─── AUTO DIAGNOSE ────────────────────────────────────────────────────────────
def make_request(url, headers, engine, verify, allow_redirects, timeout, body=None, method="GET"):
    try:
        if engine.startswith("cffi") and CURL_CFFI_AVAILABLE:
            imp = engine.split(":")[1] if ":" in engine else "chrome120"
            r = cffi_requests.request(
                method, url, headers=headers,
                json=body, timeout=timeout, verify=verify,
                allow_redirects=allow_redirects, impersonate=imp,
            )
        else:
            session = std_requests.Session()
            r = session.request(
                method, url, headers=headers,
                json=body, timeout=timeout, verify=verify,
                allow_redirects=allow_redirects,
            )
        return r, None
    except Exception as e:
        return None, str(e)

STRATEGIES = [
    {
        "label": "① HTTPS · curl_cffi Chrome120 · sem redirect · Accept */*",
        "url_fn": lambda u: u,
        "engine": "cffi:chrome120",
        "allow_redirects": False,
        "headers": {"Accept": "*/*"},
    },
    {
        "label": "② HTTP direto · curl_cffi Chrome120 · sem redirect",
        "url_fn": lambda u: u.replace("https://", "http://"),
        "engine": "cffi:chrome120",
        "allow_redirects": False,
        "headers": {"Accept": "*/*"},
    },
    {
        "label": "③ HTTPS · curl_cffi Chrome120 · COM redirect · Accept */*",
        "url_fn": lambda u: u,
        "engine": "cffi:chrome120",
        "allow_redirects": True,
        "headers": {"Accept": "*/*"},
    },
    {
        "label": "④ HTTP direto · curl_cffi Chrome120 · COM redirect",
        "url_fn": lambda u: u.replace("https://", "http://"),
        "engine": "cffi:chrome120",
        "allow_redirects": True,
        "headers": {"Accept": "*/*"},
    },
    {
        "label": "⑤ HTTPS · requests padrão · sem redirect · sem Accept",
        "url_fn": lambda u: u,
        "engine": "requests",
        "allow_redirects": False,
        "headers": {},
    },
    {
        "label": "⑥ HTTP direto · requests padrão · sem redirect",
        "url_fn": lambda u: u.replace("https://", "http://"),
        "engine": "requests",
        "allow_redirects": False,
        "headers": {},
    },
]

# ─── MANUAL MODE ──────────────────────────────────────────────────────────────
tab_auto, tab_manual = st.tabs(["🤖 Auto Diagnose", "🔧 Manual"])

# ── AUTO ──────────────────────────────────────────────────────────────────────
with tab_auto:
    st.info("Testa 6 estratégias automaticamente e mostra qual retorna JSON válido.")
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

    if st.button("🚀 Testar Todas as Estratégias", use_container_width=True):
        for s in STRATEGIES:
            target_url = s["url_fn"](url)
            headers = {"User-Agent": ua, **s["headers"]}
            with st.spinner(f"Testando {s['label']}..."):
                t0 = time.time()
                r, err = make_request(
                    target_url, headers, s["engine"],
                    verify=False, allow_redirects=s["allow_redirects"], timeout=10
                )
                elapsed = time.time() - t0

            if err:
                st.error(f"**{s['label']}** → 💥 Erro: `{err}`")
                continue

            status = r.status_code
            color = "🟢" if 200 <= status < 300 else ("🟡" if status < 400 else "🔴")

            # Tenta parsear JSON
            parsed = None
            try:
                parsed = r.json()
            except Exception:
                try:
                    t = r.text.strip()
                    if t.startswith("{") or t.startswith("["):
                        parsed = json.loads(t)
                except Exception:
                    pass

            if parsed is not None:
                st.success(f"✅ **{s['label']}** → {color} {status} | {elapsed:.2f}s | **JSON OK!**")
                st.json(parsed)
                json_str = json.dumps(parsed, indent=2, ensure_ascii=False)
                st.download_button(
                    f"⬇️ Baixar JSON ({s['label'][:20]})",
                    data=json_str, file_name="response.json", mime="application/json",
                    key=s["label"],
                )
                # Xtream
                if "user_info" in parsed or "server_info" in parsed:
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
            else:
                location = r.headers.get("Location", "")
                redirect_info = f" → `{location}`" if location else ""
                preview = r.text[:200].replace("\n", " ")
                st.warning(
                    f"**{s['label']}** → {color} {status}{redirect_info} | {elapsed:.2f}s\n\n"
                    f"`{preview}`"
                )

# ── MANUAL ────────────────────────────────────────────────────────────────────
with tab_manual:
    with st.expander("⚙️ Opções", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            timeout_m = st.number_input("Timeout", 1, 60, 15, key="t_manual")
            verify_m  = st.checkbox("Verificar SSL", False, key="v_manual")
            redir_m   = st.checkbox("Seguir redirects", False, key="r_manual")
        with c2:
            method_m  = st.selectbox("Método", ["GET","POST","PUT","DELETE"], key="m_manual")
            if CURL_CFFI_AVAILABLE:
                engine_m = st.selectbox("Engine", [
                    "curl_cffi (Chrome120)", "curl_cffi (Chrome110)",
                    "curl_cffi (Firefox110)", "requests (padrão)"
                ], key="e_manual")
            else:
                engine_m = "requests (padrão)"

        ua_m      = st.text_input("User-Agent", ua, key="ua_manual")
        accept_m  = st.text_input("Accept", "*/*", key="ac_manual")
        extra_m   = st.text_area("Headers extras (JSON)", "{}", height=60, key="ex_manual")
        body_m_raw = ""
        if method_m in ["POST","PUT"]:
            body_m_raw = st.text_area("Body (JSON)", "{}", height=80, key="b_manual")

    if st.button("🚀 Executar", use_container_width=True, key="run_manual"):
        try:
            extra = json.loads(extra_m)
        except Exception:
            extra = {}
        body = None
        if method_m in ["POST","PUT"]:
            try: body = json.loads(body_m_raw)
            except Exception: pass

        eng_key = "cffi:chrome120"
        if "Chrome110" in engine_m: eng_key = "cffi:chrome110"
        elif "Firefox" in engine_m: eng_key = "cffi:firefox110"
        elif "requests" in engine_m: eng_key = "requests"

        headers = {"User-Agent": ua_m, "Accept": accept_m}
        headers.update(extra)

        with st.spinner("Aguardando..."):
            t0 = time.time()
            r, err = make_request(url, headers, eng_key, verify_m, redir_m, timeout_m, body, method_m)
            elapsed = time.time() - t0

        if err:
            st.error(f"💥 {err}")
        else:
            status = r.status_code
            color = "🟢" if 200 <= status < 300 else ("🟡" if status < 400 else "🔴")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Status", f"{color} {status}")
            c2.metric("Tempo", f"{elapsed:.3f}s")
            c3.metric("Tamanho", f"{len(r.content)/1024:.2f} KB")
            fu = str(r.url)
            c4.metric("URL Final", fu[:35]+"..." if len(fu)>35 else fu)

            if 300 <= status < 400:
                loc = r.headers.get("Location","?")
                st.warning(f"🔀 Redirect {status} → `{loc}`\n\nTente desmarcar 'Seguir redirects' ou acesse a URL HTTP diretamente.")
            elif 200 <= status < 300:
                st.success(f"✅ Sucesso!")
            else:
                st.error(f"❌ Status {status}")

            with st.expander("📋 Headers da Resposta"):
                st.json(dict(r.headers))

            parsed = None
            try: parsed = r.json()
            except Exception:
                try:
                    t = r.text.strip()
                    if t.startswith("{") or t.startswith("["):
                        parsed = json.loads(t)
                except Exception: pass

            st.markdown("---")
            if parsed is not None:
                st.success("✅ JSON válido!")
                st.json(parsed)
                st.download_button("⬇️ Baixar JSON",
                    data=json.dumps(parsed, indent=2, ensure_ascii=False),
                    file_name="response.json", mime="application/json", key="dl_manual")
            else:
                ct = r.headers.get("Content-Type","")
                st.error("❌ Não é JSON válido")
                st.markdown(f"**Content-Type:** `{ct}`")
                preview = r.text[:3000]
                st.code(preview, language="html" if "<html" in preview.lower() else "text")

# Sidebar
st.sidebar.markdown("## 🔧 Engine")
if CURL_CFFI_AVAILABLE:
    st.sidebar.success("✅ curl_cffi disponível")
else:
    st.sidebar.warning("⚠️ `pip install curl_cffi`")

st.sidebar.markdown("---")
st.sidebar.markdown("## 💡 Use a aba Auto Diagnose")
st.sidebar.info("Testa 6 combinações (HTTP/HTTPS × redirect on/off × engines) e mostra qual retorna JSON.")
