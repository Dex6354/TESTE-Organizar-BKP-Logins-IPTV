import streamlit as st
import requests
import urllib3
import ssl
import urllib.request

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

HEADERS_BROWSER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

HEADERS_VLC = {
    "User-Agent": "VLC/3.0.18 LibVLC/3.0.18",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

class LegacySslAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.set_ciphers('ALL:@SECLEVEL=0')
        except:
            pass
        try:
            ctx.options |= 0x4
        except:
            pass
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

def render_result(label, resp_text=None, status_code=None, error=None, final_url=None):
    if error:
        st.error(f"**{label}** → ❌ `{error}`")
    else:
        has_user_info = "user_info" in resp_text
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"**{label}** → HTTP `{status_code}`")
        with col2:
            st.write("✅ `user_info`" if has_user_info else "❌ sem `user_info`")
        if final_url:
            st.caption(f"🔀 Redirect final: `{final_url}`")
        if has_user_info:
            idx = resp_text.find("user_info")
            snippet = resp_text[max(0, idx - 10):idx + 200]
            st.code(snippet, language="json")
        else:
            st.code(resp_text[:400], language="text")


st.set_page_config(page_title="IPTV Debugger", layout="wide")
st.title("🔍 IPTV Debugger")

st.info("cole uma URL por linha no formato: `http://servidor.com/player_api.php?username=X&password=Y`")

default_urls = """http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d
http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d
https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"""

urls_input = st.text_area("URLs para testar", value=default_urls, height=120)

if not CURL_CFFI_AVAILABLE:
    st.warning("⚠️ `curl_cffi` não instalado — Estratégia 1 será pulada. Instale com: `pip install curl_cffi`")

if st.button("▶️ Rodar Debug", type="primary"):
    urls = [u.strip() for u in urls_input.strip().splitlines() if u.strip()]

    for url in urls:
        st.markdown(f"---\n## 🌐 `{url}`")

        # ── 5. Redirect manual (sem follow) ─────────────────────────────────
        st.markdown("### 🔀 Redirect manual (`allow_redirects=False`)")
        try:
            r = requests.get(url, headers=HEADERS_BROWSER, verify=False, timeout=10, allow_redirects=False)
            location = r.headers.get("Location", "—")
            st.info(f"HTTP `{r.status_code}` → Location: `{location}`")
        except Exception as e:
            st.error(f"Erro: {e}")

        # ── 1. curl_cffi ─────────────────────────────────────────────────────
        st.markdown("### 1️⃣ curl_cffi (TLS Impersonation)")
        if CURL_CFFI_AVAILABLE:
            for imp in ["chrome120", "chrome110", "safari17_0", "chrome107"]:
                try:
                    r = curl_requests.get(url, impersonate=imp, timeout=10, allow_redirects=True, verify=False)
                    render_result(f"curl_cffi / {imp}", r.text, r.status_code, final_url=r.url)
                except Exception as e:
                    render_result(f"curl_cffi / {imp}", error=str(e))
        else:
            st.warning("Pulado — curl_cffi não instalado")

        # ── 2. requests padrão ───────────────────────────────────────────────
        st.markdown("### 2️⃣ requests padrão")
        for label, headers in [("Browser UA", HEADERS_BROWSER), ("VLC UA", HEADERS_VLC)]:
            try:
                r = requests.get(url, headers=headers, verify=False, timeout=10, allow_redirects=True)
                render_result(f"requests / {label}", r.text, r.status_code, final_url=r.url)
            except Exception as e:
                render_result(f"requests / {label}", error=str(e))

        # ── 3. SSL Legado ────────────────────────────────────────────────────
        st.markdown("### 3️⃣ SSL Legado (SECLEVEL=0)")
        for label, headers in [("Browser UA", HEADERS_BROWSER), ("VLC UA", HEADERS_VLC)]:
            try:
                with requests.Session() as s:
                    s.mount("https://", LegacySslAdapter())
                    r = s.get(url, headers=headers, verify=False, timeout=10, allow_redirects=True)
                    render_result(f"ssl-legado / {label}", r.text, r.status_code, final_url=r.url)
            except Exception as e:
                render_result(f"ssl-legado / {label}", error=str(e))

        # ── 4. urllib nativo ─────────────────────────────────────────────────
        st.markdown("### 4️⃣ urllib nativo")
        for label, headers in [("Browser UA", HEADERS_BROWSER), ("VLC UA", HEADERS_VLC)]:
            try:
                ssl_ctx = ssl._create_unverified_context()
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
                    content = resp.read().decode("utf-8", errors="ignore")
                    render_result(f"urllib / {label}", content, resp.status, final_url=resp.url)
            except Exception as e:
                render_result(f"urllib / {label}", error=str(e))

    st.markdown("---")
    st.success("✅ Debug completo!")
