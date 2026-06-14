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

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# ─── helpers ──────────────────────────────────────────────────────────────────

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

def run_curl_cmd(cmd_list, timeout=20):
    """Executa um comando curl e retorna (status, body, final_url, stderr)."""
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout + 5)
        out = result.stdout
        if "___STATUS:" in out:
            parts = out.rsplit("___STATUS:", 1)
            body = parts[0]
            meta = parts[1]
            status_str = meta.split("___URL:")[0]
            final_url  = meta.split("___URL:")[1] if "___URL:" in meta else url
            try:
                status = int(status_str)
            except Exception:
                status = 0
        else:
            body = out
            status = 0
            final_url = url
        return status, body, final_url, result.stderr or None
    except subprocess.TimeoutExpired:
        return None, "", url, "Timeout"
    except Exception as e:
        return None, "", url, str(e)

def build_curl_base(target_url, extra_args=None, timeout=15):
    cmd = [
        CURL_BIN, "-s",
        "-w", "\n___STATUS:%{http_code}___URL:%{url_effective}",
        "-A", UA,
        "-H", "Accept: */*",
        "-H", "Accept-Language: pt-BR,pt;q=0.9,en;q=0.8",
        "--max-time", str(timeout),
        "--compressed", "-k",
    ]
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(target_url)
    return cmd

def parse_curl_command(curl_str):
    """
    Extrai URL, headers e cookies de um comando curl copiado do DevTools.
    Retorna dict com: url, headers, cookies.
    """
    curl_str = curl_str.strip()
    if curl_str.startswith("curl "):
        curl_str = curl_str[5:]

    result = {"url": None, "headers": {}, "cookies": {}}

    # Remove line continuations
    curl_str = re.sub(r"\\\s*\n", " ", curl_str)

    # Extrai URL (primeiro argumento sem flag)
    url_match = re.search(r"'([^']+)'|\"([^\"]+)\"", curl_str)
    if url_match:
        result["url"] = url_match.group(1) or url_match.group(2)

    # Extrai -H headers
    headers_raw = re.findall(r"-H\s+'([^']+)'|-H\s+\"([^\"]+)\"", curl_str)
    for h1, h2 in headers_raw:
        h = h1 or h2
        if ": " in h:
            k, v = h.split(": ", 1)
            if k.lower() == "cookie":
                # Parseia cookies
                for part in v.split("; "):
                    if "=" in part:
                        ck, cv = part.split("=", 1)
                        result["cookies"][ck.strip()] = cv.strip()
            else:
                result["headers"][k] = v

    # Extrai --cookie ou -b
    cookie_match = re.search(r"(?:--cookie|-b)\s+'([^']+)'|(?:--cookie|-b)\s+\"([^\"]+)\"", curl_str)
    if cookie_match:
        cookie_str = cookie_match.group(1) or cookie_match.group(2)
        for part in cookie_str.split("; "):
            if "=" in part:
                ck, cv = part.split("=", 1)
                result["cookies"][ck.strip()] = cv.strip()

    return result

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab_curl_paste, tab_cookies, tab_auto, tab_manual = st.tabs([
    "📋 Colar cURL do Browser",
    "🍪 Cookies Manual",
    "🤖 Auto Diagnose",
    "🔧 Manual",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — COLAR cURL DO BROWSER (SOLUÇÃO PRINCIPAL)
# ═══════════════════════════════════════════════════════════════════════════════
with tab_curl_paste:
    st.markdown("""
    ### Como obter o cURL do browser:
    1. Abra **F12** → aba **Network**
    2. Acesse a URL da API no browser (ela deve funcionar)
    3. Clique na requisição na lista
    4. Botão direito → **Copy** → **Copy as cURL (bash)**
    5. Cole abaixo 👇
    """)

    curl_pasted = st.text_area(
        "Cole o comando cURL aqui:",
        height=150,
        placeholder="curl 'https://websmt.ca/player_api.php?username=...' \\\n  -H 'cookie: session=abc123...' \\\n  -H 'user-agent: Mozilla/5.0...' ...",
    )

    col1, col2 = st.columns(2)
    with col1:
        run_exact = st.button("▶️ Executar cURL EXATO (via terminal)", use_container_width=True)
    with col2:
        run_python = st.button("🐍 Executar via Python (com cookies extraídos)", use_container_width=True)

    if curl_pasted.strip():
        parsed_curl = parse_curl_command(curl_pasted)

        with st.expander("🔍 Dados extraídos do cURL"):
            st.write(f"**URL:** `{parsed_curl['url']}`")
            st.write(f"**Headers ({len(parsed_curl['headers'])}):**")
            st.json(parsed_curl["headers"])
            if parsed_curl["cookies"]:
                st.write(f"**Cookies ({len(parsed_curl['cookies'])}):**")
                st.json(parsed_curl["cookies"])
            else:
                st.warning("⚠️ Nenhum cookie encontrado no cURL — isso pode ser a causa do 406.")

        if run_exact and CURL_BIN:
            # Executa o curl exato do browser, apenas adicionando o -w para capturar status
            lines = curl_pasted.strip()
            # Injeta -w antes da URL final
            lines = re.sub(r"\\\s*\n", " ", lines)  # colapsa line continuations
            # Adiciona -s e -w ao comando original
            cmd_str = lines.replace("curl ", f"curl -s -w '\\n___STATUS:%{{http_code}}___URL:%{{url_effective}}' ", 1)
            with st.spinner("Executando cURL exato do browser..."):
                t0 = time.time()
                try:
                    result = subprocess.run(
                        cmd_str, shell=True, capture_output=True, text=True, timeout=25
                    )
                    elapsed = time.time() - t0
                    out = result.stdout
                    if "___STATUS:" in out:
                        parts = out.rsplit("___STATUS:", 1)
                        body = parts[0]
                        meta = parts[1]
                        status = int(meta.split("___URL:")[0])
                        final_url = meta.split("___URL:")[1] if "___URL:" in meta else ""
                    else:
                        body = out
                        status = 0
                        final_url = ""

                    color = "🟢" if 200 <= status < 300 else "🔴"
                    st.metric("Status", f"{color} {status}")
                    st.caption(f"Tempo: {elapsed:.2f}s | URL Final: {final_url}")

                    parsed = try_parse_json(body)
                    if parsed:
                        st.success("✅ JSON válido! O cURL do browser funcionou.")
                        st.json(parsed)
                        st.download_button("⬇️ Baixar JSON",
                            json.dumps(parsed, indent=2, ensure_ascii=False),
                            "response.json", "application/json", key="dl_exact")
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
                        st.error("❌ Ainda não retornou JSON.")
                        st.code(body[:2000], language="html" if "<html" in body.lower() else "text")
                    if result.stderr:
                        with st.expander("stderr"):
                            st.code(result.stderr)
                except Exception as e:
                    st.error(f"💥 {e}")

        if run_python:
            target = parsed_curl["url"] or url
            headers = {k: v for k, v in parsed_curl["headers"].items()
                       if k.lower() not in ("host",)}
            cookies = parsed_curl["cookies"]

            if not headers.get("User-Agent") and not headers.get("user-agent"):
                headers["User-Agent"] = UA

            with st.spinner("Executando via Python com cookies do browser..."):
                t0 = time.time()
                try:
                    s = std_requests.Session()
                    r = s.get(target, headers=headers, cookies=cookies,
                              verify=False, timeout=15, allow_redirects=True)
                    elapsed = time.time() - t0

                    color = "🟢" if 200 <= r.status_code < 300 else "🔴"
                    st.metric("Status", f"{color} {r.status_code}")
                    st.caption(f"Tempo: {elapsed:.2f}s")

                    parsed = try_parse_json(r.text)
                    if parsed:
                        st.success("✅ JSON válido via Python!")
                        st.json(parsed)
                        st.download_button("⬇️ Baixar JSON",
                            json.dumps(parsed, indent=2, ensure_ascii=False),
                            "response.json", "application/json", key="dl_py_curl")
                    else:
                        st.error("❌ Ainda não retornou JSON.")
                        st.code(r.text[:2000], language="html" if "<html" in r.text.lower() else "text")
                except Exception as e:
                    st.error(f"💥 {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — COOKIES MANUAL
# ═══════════════════════════════════════════════════════════════════════════════
with tab_cookies:
    st.markdown("""
    ### Copie os cookies do browser manualmente
    **F12 → Application → Cookies → `websmt.ca`**  
    Copie o valor completo do campo Cookie (ou da coluna Value de cada cookie).
    """)

    cookie_str = st.text_area(
        "Cole o Cookie header completo (ex: `session=abc; token=xyz`):",
        height=80,
        placeholder="session=abc123; PHPSESSID=xyz...",
    )

    extra_h = st.text_area("Headers extras (JSON)", "{}", height=60, key="ch_extra")

    if st.button("🚀 Testar com Cookies", use_container_width=True):
        try:
            extra = json.loads(extra_h)
        except Exception:
            extra = {}

        headers = {
            "User-Agent": UA,
            "Accept": "*/*",
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
        }
        headers.update(extra)

        cookies = {}
        if cookie_str.strip():
            for part in cookie_str.split(";"):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    cookies[k.strip()] = v.strip()

        with st.spinner("Testando..."):
            t0 = time.time()
            try:
                s = std_requests.Session()
                r = s.get(url, headers=headers, cookies=cookies,
                          verify=False, timeout=15, allow_redirects=True)
                elapsed = time.time() - t0

                color = "🟢" if 200 <= r.status_code < 300 else "🔴"
                c1, c2, c3 = st.columns(3)
                c1.metric("Status", f"{color} {r.status_code}")
                c2.metric("Tempo", f"{elapsed:.2f}s")
                c3.metric("Cookies enviados", len(cookies))

                with st.expander("📋 Headers da Resposta"):
                    st.json(dict(r.headers))

                parsed = try_parse_json(r.text)
                if parsed:
                    st.success("✅ JSON válido!")
                    st.json(parsed)
                    st.download_button("⬇️ Baixar JSON",
                        json.dumps(parsed, indent=2, ensure_ascii=False),
                        "response.json", "application/json", key="dl_cookies")
                else:
                    st.error("❌ Não retornou JSON.")
                    st.code(r.text[:2000], language="html" if "<html" in r.text.lower() else "text")
            except Exception as e:
                st.error(f"💥 {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AUTO DIAGNOSE
# ═══════════════════════════════════════════════════════════════════════════════
with tab_auto:
    st.info("Testa estratégias Python + curl do sistema (sem cookies). Se todas falharem, use a aba **📋 Colar cURL do Browser**.")

    STRATEGIES = [
        {"label": "① curl_cffi Chrome120 · HTTPS · sem redirect",
         "url_fn": lambda u: u, "engine": "cffi:chrome120", "redir": False},
        {"label": "② curl_cffi Chrome120 · HTTP",
         "url_fn": lambda u: u.replace("https://","http://"), "engine": "cffi:chrome120", "redir": False},
        {"label": "③ curl_cffi Chrome120 · HTTPS · COM redirect",
         "url_fn": lambda u: u, "engine": "cffi:chrome120", "redir": True},
        {"label": "④ requests · HTTPS",
         "url_fn": lambda u: u, "engine": "requests", "redir": False},
        {"label": "⑤ requests · HTTP",
         "url_fn": lambda u: u.replace("https://","http://"), "engine": "requests", "redir": False},
    ]
    CURL_STRATEGIES = [
        {"label": "⑥ curl sistema · HTTPS", "url_fn": lambda u: u, "args": []},
        {"label": "⑦ curl sistema · HTTP", "url_fn": lambda u: u.replace("https://","http://"), "args": []},
        {"label": "⑧ curl sistema · HTTP/1.1", "url_fn": lambda u: u, "args": ["--http1.1"]},
        {"label": "⑨ curl sistema · HTTP/2",   "url_fn": lambda u: u, "args": ["--http2"]},
    ]

    if st.button("🚀 Testar Estratégias (sem cookies)", use_container_width=True):
        found = False
        for s in STRATEGIES:
            target = s["url_fn"](url)
            headers = {"User-Agent": UA, "Accept": "*/*"}
            t0 = time.time()
            status, resp_h, text, fu, err = do_request(
                target, headers, s["engine"], False, s["redir"], 10)
            elapsed = time.time() - t0
            if err:
                st.error(f"**{s['label']}** → 💥 `{err}`")
                continue
            color = "🟢" if 200 <= status < 300 else ("🟡" if status < 400 else "🔴")
            parsed = try_parse_json(text)
            if parsed:
                st.success(f"✅ **{s['label']}** → {color} {status} | {elapsed:.2f}s | JSON OK!")
                st.json(parsed)
                found = True
            else:
                preview = text[:120].replace("\n"," ")
                st.warning(f"**{s['label']}** → {color} {status} | {elapsed:.2f}s | `{preview}`")

        st.markdown("**── curl do sistema ──**")
        for s in CURL_STRATEGIES:
            if not CURL_BIN:
                st.error(f"**{s['label']}** → curl não disponível")
                continue
            target = s["url_fn"](url)
            cmd = build_curl_base(target, s["args"])
            t0 = time.time()
            status, text, fu, err = run_curl_cmd(cmd)
            elapsed = time.time() - t0
            if err and status is None:
                st.error(f"**{s['label']}** → 💥 `{err}`")
                continue
            color = "🟢" if status and 200 <= status < 300 else "🔴"
            parsed = try_parse_json(text)
            if parsed:
                st.success(f"✅ **{s['label']}** → {color} {status} | {elapsed:.2f}s | JSON OK!")
                st.json(parsed)
                found = True
            else:
                preview = text[:120].replace("\n"," ")
                st.warning(f"**{s['label']}** → {color} {status} | {elapsed:.2f}s | `{preview}`")

        if not found:
            st.error("❌ Todas falharam. Use a aba **📋 Colar cURL do Browser** — o servidor exige cookies de sessão.")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MANUAL
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
            if CURL_CFFI_AVAILABLE:
                em = st.selectbox("Engine", [
                    "curl_cffi (Chrome120)","curl_cffi (Chrome110)","requests (padrão)"
                ], key="em")
            else:
                em = "requests (padrão)"
        uam = st.text_input("User-Agent", UA, key="uam")
        acm = st.text_input("Accept", "*/*", key="acm")
        exm = st.text_area("Headers extras (JSON)", "{}", 60, key="exm")
        ckm = st.text_area("Cookies (formato: key=val; key2=val2)", "", 60, key="ckm")

    if st.button("🚀 Executar", use_container_width=True, key="run_m"):
        try: extra = json.loads(exm)
        except: extra = {}
        cookies_m = {}
        if ckm.strip():
            for part in ckm.split(";"):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    cookies_m[k.strip()] = v.strip()

        eng_key = "cffi:chrome120"
        if "Chrome110" in em: eng_key = "cffi:chrome110"
        elif "requests" in em: eng_key = "requests"

        headers = {"User-Agent": uam, "Accept": acm}
        headers.update(extra)

        t0 = time.time()
        try:
            if eng_key.startswith("cffi") and CURL_CFFI_AVAILABLE:
                imp = eng_key.split(":")[1]
                r = cffi_requests.request(mm, url, headers=headers, cookies=cookies_m,
                    timeout=tm, verify=vm, allow_redirects=rm, impersonate=imp)
            else:
                s = std_requests.Session()
                r = s.request(mm, url, headers=headers, cookies=cookies_m,
                    timeout=tm, verify=vm, allow_redirects=rm)
            elapsed = time.time() - t0
            status = r.status_code
            color = "🟢" if 200 <= status < 300 else "🔴"
            c1,c2,c3 = st.columns(3)
            c1.metric("Status", f"{color} {status}")
            c2.metric("Tempo", f"{elapsed:.3f}s")
            c3.metric("Tamanho", f"{len(r.content)/1024:.2f} KB")
            with st.expander("📋 Headers da Resposta"):
                st.json(dict(r.headers))
            parsed = try_parse_json(r.text)
            st.markdown("---")
            if parsed:
                st.success("✅ JSON válido!")
                st.json(parsed)
                st.download_button("⬇️ Baixar", json.dumps(parsed,indent=2,ensure_ascii=False),
                    "response.json","application/json",key="dl_m")
            else:
                st.error("❌ Não é JSON")
                preview = r.text[:3000]
                st.code(preview, language="html" if "<html" in preview.lower() else "text")
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
st.sidebar.markdown("## 💡 Por que 406?")
st.sidebar.info(
    "O nginx está exigindo **cookies de sessão** do browser.\n\n"
    "**Solução:** Aba **📋 Colar cURL do Browser**\n\n"
    "F12 → Network → requisição → botão direito → **Copy as cURL**"
)
