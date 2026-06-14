import streamlit as st
import json
import time
import subprocess
import shutil

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

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# ─── helpers ──────────────────────────────────────────────────────────────────

def try_parse_json(text):
    try:
        return json.loads(text)
    except Exception:
        t = text.strip()
        if t.startswith("{") or t.startswith("["):
            try: return json.loads(t)
            except Exception: pass
    return None

def do_request(url, headers, engine, verify, allow_redirects, timeout, body=None, method="GET"):
    try:
        if engine.startswith("cffi") and CURL_CFFI_AVAILABLE:
            imp = engine.split(":")[1] if ":" in engine else "chrome120"
            r = cffi_requests.request(
                method, url, headers=headers, json=body,
                timeout=timeout, verify=verify,
                allow_redirects=allow_redirects, impersonate=imp,
            )
            return r.status_code, dict(r.headers), r.text, str(r.url), None
        else:
            s = std_requests.Session()
            r = s.request(
                method, url, headers=headers, json=body,
                timeout=timeout, verify=verify,
                allow_redirects=allow_redirects,
            )
            return r.status_code, dict(r.headers), r.text, str(r.url), None
    except Exception as e:
        return None, {}, "", url, str(e)

def do_curl(url, extra_args=None, timeout=15):
    """Chama o curl real do sistema via subprocess."""
    if not CURL_BIN:
        return None, "", "curl não encontrado no sistema"
    cmd = [
        CURL_BIN, "-s", "-w", "\n___STATUS:%{http_code}___URL:%{url_effective}",
        "-A", UA,
        "-H", "Accept: */*",
        "-H", "Accept-Language: pt-BR,pt;q=0.9,en;q=0.8",
        "--max-time", str(timeout),
        "--compressed",
        "-k",  # insecure (ignora SSL)
    ]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(url)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        out = result.stdout
        # Separa body do status
        if "___STATUS:" in out:
            parts = out.rsplit("___STATUS:", 1)
            body = parts[0]
            meta = parts[1]
            status_str = meta.split("___URL:")[0]
            final_url = meta.split("___URL:")[1] if "___URL:" in meta else url
            try: status = int(status_str)
            except: status = 0
        else:
            body = out
            status = 0
            final_url = url
        return status, body, final_url, result.stderr or None
    except subprocess.TimeoutExpired:
        return None, "", url, "Timeout"
    except Exception as e:
        return None, "", url, str(e)

# ─── estratégias ──────────────────────────────────────────────────────────────

STRATEGIES = [
    # curl_cffi variants
    {"label": "① curl_cffi Chrome120 · HTTPS · sem redirect",
     "url_fn": lambda u: u, "engine": "cffi:chrome120", "redir": False},
    {"label": "② curl_cffi Chrome120 · HTTP · sem redirect",
     "url_fn": lambda u: u.replace("https://","http://"), "engine": "cffi:chrome120", "redir": False},
    {"label": "③ curl_cffi Chrome120 · HTTPS · COM redirect",
     "url_fn": lambda u: u, "engine": "cffi:chrome120", "redir": True},
    {"label": "④ curl_cffi Chrome110 · HTTPS · sem redirect",
     "url_fn": lambda u: u, "engine": "cffi:chrome110", "redir": False},
    {"label": "⑤ curl_cffi Firefox110 · HTTPS · sem redirect",
     "url_fn": lambda u: u, "engine": "cffi:ff110", "redir": False},
    # requests
    {"label": "⑥ requests · HTTPS · sem redirect",
     "url_fn": lambda u: u, "engine": "requests", "redir": False},
    {"label": "⑦ requests · HTTP direto",
     "url_fn": lambda u: u.replace("https://","http://"), "engine": "requests", "redir": False},
]

CURL_STRATEGIES = [
    {"label": "⑧ curl sistema · HTTPS",
     "url_fn": lambda u: u, "args": []},
    {"label": "⑨ curl sistema · HTTP direto",
     "url_fn": lambda u: u.replace("https://","http://"), "args": []},
    {"label": "⑩ curl sistema · HTTPS · sem redirect (-L off)",
     "url_fn": lambda u: u, "args": ["--max-redirs", "0"]},
    {"label": "⑪ curl sistema · HTTPS · HTTP/1.1 forçado",
     "url_fn": lambda u: u, "args": ["--http1.1"]},
    {"label": "⑫ curl sistema · HTTPS · HTTP/2 forçado",
     "url_fn": lambda u: u, "args": ["--http2"]},
]

# ─── tabs ─────────────────────────────────────────────────────────────────────
tab_auto, tab_manual = st.tabs(["🤖 Auto Diagnose (12 estratégias)", "🔧 Manual"])

with tab_auto:
    col_info, col_curl = st.columns(2)
    with col_info:
        st.info("Testa 12 estratégias: Python (curl_cffi + requests) + curl real do sistema.")
    with col_curl:
        if CURL_BIN:
            st.success(f"✅ curl encontrado: `{CURL_BIN}`")
        else:
            st.warning("⚠️ curl não encontrado no PATH")

    if st.button("🚀 Testar Todas as 12 Estratégias", use_container_width=True):

        found = False

        # Python strategies
        for s in STRATEGIES:
            target = s["url_fn"](url)
            headers = {"User-Agent": UA, "Accept": "*/*"}
            t0 = time.time()
            status, resp_headers, text, final_url, err = do_request(
                target, headers, s["engine"], verify=False,
                allow_redirects=s["redir"], timeout=10
            )
            elapsed = time.time() - t0

            if err:
                st.error(f"**{s['label']}** → 💥 `{err}`")
                continue

            color = "🟢" if 200 <= status < 300 else ("🟡" if status < 400 else "🔴")
            parsed = try_parse_json(text)

            if parsed is not None:
                st.success(f"✅ **{s['label']}** → {color} {status} | {elapsed:.2f}s | **JSON OK!**")
                st.json(parsed)
                st.download_button("⬇️ Baixar JSON", json.dumps(parsed, indent=2, ensure_ascii=False),
                    "response.json", "application/json", key=f"dl_{s['label']}")
                found = True
            else:
                loc = resp_headers.get("Location", "")
                extra = f" → `{loc}`" if loc else ""
                preview = text[:120].replace("\n"," ")
                st.warning(f"**{s['label']}** → {color} {status}{extra} | {elapsed:.2f}s | `{preview}`")

        # curl strategies
        st.markdown("**── curl do sistema ──**")
        for s in CURL_STRATEGIES:
            if not CURL_BIN:
                st.error(f"**{s['label']}** → ⚠️ curl não disponível")
                continue
            target = s["url_fn"](url)
            t0 = time.time()
            status, text, final_url, err = do_curl(target, extra_args=s["args"], timeout=10)
            elapsed = time.time() - t0

            if err and status is None:
                st.error(f"**{s['label']}** → 💥 `{err}`")
                continue

            color = "🟢" if status and 200 <= status < 300 else ("🟡" if status and status < 400 else "🔴")
            parsed = try_parse_json(text)

            if parsed is not None:
                st.success(f"✅ **{s['label']}** → {color} {status} | {elapsed:.2f}s | **JSON OK!**")
                st.json(parsed)
                st.download_button("⬇️ Baixar JSON", json.dumps(parsed, indent=2, ensure_ascii=False),
                    "response.json", "application/json", key=f"dl_curl_{s['label']}")
                found = True
            else:
                preview = text[:120].replace("\n"," ")
                st.warning(f"**{s['label']}** → {color} {status} | {elapsed:.2f}s | `{preview}`")

        if not found:
            st.error(
                "❌ Nenhuma estratégia retornou JSON.\n\n"
                "**Possíveis causas:**\n"
                "- Bloqueio por IP/ASN do servidor\n"
                "- A API requer sessão autenticada via cookie (login no site primeiro)\n"
                "- O servidor só responde para IPs específicos (geo-block)\n\n"
                "**Próximo passo:** copie a requisição do DevTools do navegador "
                "(F12 → Network → clique na requisição → *Copy as cURL*) e cole aqui."
            )

# ─── Manual ───────────────────────────────────────────────────────────────────
with tab_manual:
    with st.expander("⚙️ Opções", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            timeout_m = st.number_input("Timeout", 1, 60, 15, key="tm")
            verify_m  = st.checkbox("Verificar SSL", False, key="vm")
            redir_m   = st.checkbox("Seguir redirects", False, key="rm")
            use_curl_m = st.checkbox("Usar curl do sistema", bool(CURL_BIN), key="uc")
        with c2:
            method_m = st.selectbox("Método", ["GET","POST","PUT","DELETE"], key="mm")
            if CURL_CFFI_AVAILABLE:
                engine_m = st.selectbox("Engine Python", [
                    "curl_cffi (Chrome120)","curl_cffi (Chrome110)",
                    "curl_cffi (Firefox110)","requests (padrão)"
                ], key="em")
            else:
                engine_m = "requests (padrão)"
        ua_m = st.text_input("User-Agent", UA, key="uam")
        accept_m = st.text_input("Accept", "*/*", key="acm")
        extra_m  = st.text_area("Headers extras (JSON)", "{}", 60, key="exm")
        curl_args_m = st.text_input("Args extras curl (ex: --http1.1)", "", key="cam")
        body_raw_m = ""
        if method_m in ["POST","PUT"]:
            body_raw_m = st.text_area("Body (JSON)", "{}", 80, key="bm")

    if st.button("🚀 Executar", use_container_width=True, key="run_m"):
        try: extra = json.loads(extra_m)
        except: extra = {}
        body = None
        if method_m in ["POST","PUT"]:
            try: body = json.loads(body_raw_m)
            except: pass

        t0 = time.time()
        if use_curl_m and CURL_BIN:
            extra_args = curl_args_m.split() if curl_args_m.strip() else []
            status, text, final_url, err = do_curl(url, extra_args=extra_args, timeout=timeout_m)
            elapsed = time.time() - t0
            resp_headers = {}
        else:
            eng_key = "cffi:chrome120"
            if "Chrome110" in engine_m: eng_key = "cffi:chrome110"
            elif "Firefox" in engine_m: eng_key = "cffi:ff110"
            elif "requests" in engine_m: eng_key = "requests"
            headers = {"User-Agent": ua_m, "Accept": accept_m}
            headers.update(extra)
            status, resp_headers, text, final_url, err = do_request(
                url, headers, eng_key, verify_m, redir_m, timeout_m, body, method_m)
            elapsed = time.time() - t0

        if err and status is None:
            st.error(f"💥 {err}")
        else:
            color = "🟢" if status and 200 <= status < 300 else ("🟡" if status and status < 400 else "🔴")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Status", f"{color} {status}")
            c2.metric("Tempo", f"{elapsed:.3f}s")
            c3.metric("Tamanho", f"{len(text)/1024:.2f} KB")
            c4.metric("URL Final", (final_url[:32]+"...") if len(final_url)>32 else final_url)
            if resp_headers:
                with st.expander("📋 Headers da Resposta"):
                    st.json(resp_headers)
            parsed = try_parse_json(text)
            st.markdown("---")
            if parsed:
                st.success("✅ JSON válido!")
                st.json(parsed)
                st.download_button("⬇️ Baixar", json.dumps(parsed,indent=2,ensure_ascii=False),
                    "response.json","application/json",key="dl_m")
            else:
                st.error("❌ Não é JSON")
                preview = text[:3000]
                st.code(preview, language="html" if "<html" in preview.lower() else "text")

st.sidebar.markdown("## 🔧 Engine Status")
st.sidebar.success("✅ curl_cffi") if CURL_CFFI_AVAILABLE else st.sidebar.warning("⚠️ pip install curl_cffi")
st.sidebar.success(f"✅ curl: {CURL_BIN}") if CURL_BIN else st.sidebar.warning("⚠️ curl não encontrado")
