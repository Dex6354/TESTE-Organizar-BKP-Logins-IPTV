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

# Variações de headers para testar — do mais simples ao mais completo
HEADER_VARIANTS = {
    "sem headers": {},
    "só User-Agent Chrome": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    },
    "só User-Agent VLC": {
        "User-Agent": "VLC/3.0.18 LibVLC/3.0.18",
    },
    "Accept */* simples": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
    },
    "Accept application/json": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    },
    "sem Accept-Encoding": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Connection": "keep-alive",
    },
    "headers completos com Accept-Encoding": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    },
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
        return
    has_user_info = "user_info" in resp_text
    color = "✅" if has_user_info else ("⚠️" if status_code == 200 else "❌")
    st.write(f"{color} **{label}** → HTTP `{status_code}` | `user_info`: {'**SIM ✅**' if has_user_info else 'NÃO'}")
    if final_url:
        st.caption(f"🔀 URL final: `{final_url}`")
    if has_user_info:
        idx = resp_text.find("user_info")
        snippet = resp_text[max(0, idx - 10):idx + 300]
        st.code(snippet, language="json")
    else:
        st.code(resp_text[:300], language="text")


st.set_page_config(page_title="IPTV Debugger v2", layout="wide")
st.title("🔍 IPTV Debugger v2 — Teste de Headers")

if not CURL_CFFI_AVAILABLE:
    st.warning("⚠️ `curl_cffi` não instalado. Instale com: `pip install curl_cffi`")

default_urls = """http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d
http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d
https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"""

urls_input = st.text_area("URLs para testar", value=default_urls, height=120)

if st.button("▶️ Rodar Debug", type="primary"):
    urls = [u.strip() for u in urls_input.strip().splitlines() if u.strip()]

    for url in urls:
        st.markdown(f"---\n## 🌐 `{url}`")

        # ── Redirect check ───────────────────────────────────────────────────
        st.markdown("#### 🔀 Redirect (`allow_redirects=False`)")
        try:
            r = requests.get(url, verify=False, timeout=10, allow_redirects=False)
            location = r.headers.get("Location", "—")
            st.info(f"HTTP `{r.status_code}` → Location: `{location}`")
            if r.headers:
                with st.expander("Ver todos os response headers"):
                    st.json(dict(r.headers))
        except Exception as e:
            st.error(f"Erro: {e}")

        # ── Teste cada variação de header ────────────────────────────────────
        st.markdown("#### 🧪 Variações de Headers (requests)")
        for variant_name, headers in HEADER_VARIANTS.items():
            try:
                r = requests.get(url, headers=headers, verify=False, timeout=10, allow_redirects=True)
                render_result(variant_name, r.text, r.status_code, final_url=r.url)
            except Exception as e:
                render_result(variant_name, error=str(e))

        # ── SSL Legado com headers mínimos ───────────────────────────────────
        st.markdown("#### 🔒 SSL Legado + sem headers")
        try:
            with requests.Session() as s:
                s.mount("https://", LegacySslAdapter())
                r = s.get(url, headers={}, verify=False, timeout=10, allow_redirects=True)
                render_result("ssl-legado / sem headers", r.text, r.status_code, final_url=r.url)
        except Exception as e:
            render_result("ssl-legado / sem headers", error=str(e))

        # ── curl_cffi sem headers ────────────────────────────────────────────
        if CURL_CFFI_AVAILABLE:
            st.markdown("#### 🦾 curl_cffi")
            for imp in ["chrome120", "chrome110", "safari17_0"]:
                try:
                    r = curl_requests.get(url, impersonate=imp, timeout=10, allow_redirects=True, verify=False)
                    render_result(f"curl_cffi / {imp}", r.text, r.status_code, final_url=r.url)
                except Exception as e:
                    render_result(f"curl_cffi / {imp}", error=str(e))

        # ── urllib sem headers ───────────────────────────────────────────────
        st.markdown("#### 🐍 urllib nativo / sem headers")
        try:
            ssl_ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                render_result("urllib / sem headers", content, resp.status, final_url=resp.url)
        except Exception as e:
            render_result("urllib / sem headers", error=str(e))

    st.markdown("---")
    st.success("✅ Debug completo!")
