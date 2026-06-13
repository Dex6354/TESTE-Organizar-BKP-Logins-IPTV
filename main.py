import streamlit as st
import subprocess
import sys
import requests
import urllib3
import ssl

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="IPTV Debugger v3", layout="wide")
st.title("🔍 IPTV Debugger v3 — Diagnóstico Cloudflare")

# ── Instalar curl_cffi ───────────────────────────────────────────────────────
st.markdown("### 📦 Status do curl_cffi")

try:
    from curl_cffi import requests as curl_requests
    st.success("✅ curl_cffi já instalado!")
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False
    st.error("❌ curl_cffi não instalado.")
    if st.button("⬇️ Instalar curl_cffi agora"):
        with st.spinner("Instalando curl_cffi..."):
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "curl_cffi"],
                capture_output=True, text=True
            )
        if result.returncode == 0:
            st.success("✅ Instalado com sucesso! Recarregue a página (F5) e rode o debug novamente.")
            st.code(result.stdout)
        else:
            st.error("❌ Erro na instalação:")
            st.code(result.stderr)
    st.stop()

# ── URLs de teste ────────────────────────────────────────────────────────────
default_urls = """https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d
http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d
http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d
https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"""

urls_input = st.text_area("URLs para testar", value=default_urls, height=130)

IMPERSONATIONS = ["chrome120", "chrome110", "chrome107", "safari17_0", "safari15_5", "firefox117"]

# Headers extras com Sec-Fetch (idênticos ao Chrome real)
HEADERS_CHROME_FULL = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Connection": "keep-alive",
}

def render(label, text=None, code=None, url=None, error=None, headers=None):
    if error:
        st.error(f"**{label}** ❌ `{error}`")
        return False
    has = "user_info" in text
    if has:
        st.success(f"**{label}** → HTTP `{code}` ✅ **user_info ENCONTRADO!**")
        if url:
            st.caption(f"🔀 URL final: `{url}`")
        idx = text.find("user_info")
        st.code(text[max(0, idx-5):idx+400], language="json")
    else:
        st.warning(f"**{label}** → HTTP `{code}` ❌ sem user_info")
        if url:
            st.caption(f"🔀 URL final: `{url}`")
        if headers:
            with st.expander("Ver response headers"):
                st.json(dict(headers))
        st.code(text[:300], language="text")
    return has

if st.button("▶️ Rodar Debug", type="primary"):
    urls = [u.strip() for u in urls_input.strip().splitlines() if u.strip()]

    for url in urls:
        st.markdown(f"---\n## 🌐 `{url}`")
        found = False

        # ── curl_cffi — prioridade máxima ────────────────────────────────────
        st.markdown("### 🦾 curl_cffi (TLS Fingerprint)")
        for imp in IMPERSONATIONS:
            if found:
                break
            try:
                r = curl_requests.get(url, impersonate=imp, timeout=12, allow_redirects=True, verify=False)
                found = render(f"curl_cffi / {imp}", r.text, r.status_code, r.url, headers=r.headers)
            except Exception as e:
                render(f"curl_cffi / {imp}", error=str(e))

        # ── curl_cffi + headers Sec-Fetch ────────────────────────────────────
        if not found:
            st.markdown("### 🦾 curl_cffi + headers Sec-Fetch")
            for imp in ["chrome120", "chrome110"]:
                if found:
                    break
                try:
                    r = curl_requests.get(
                        url, impersonate=imp, headers=HEADERS_CHROME_FULL,
                        timeout=12, allow_redirects=True, verify=False
                    )
                    found = render(f"curl_cffi+Sec-Fetch / {imp}", r.text, r.status_code, r.url, headers=r.headers)
                except Exception as e:
                    render(f"curl_cffi+Sec-Fetch / {imp}", error=str(e))

        # ── requests padrão + Sec-Fetch headers ─────────────────────────────
        if not found:
            st.markdown("### 🌐 requests + Sec-Fetch headers")
            try:
                r = requests.get(url, headers=HEADERS_CHROME_FULL, verify=False, timeout=12, allow_redirects=True)
                found = render("requests + Sec-Fetch", r.text, r.status_code, r.url, headers=r.headers)
            except Exception as e:
                render("requests + Sec-Fetch", error=str(e))

        # ── Sem SSL verify + sem headers ─────────────────────────────────────
        if not found:
            st.markdown("### 🔓 requests sem verify, sem headers")
            try:
                r = requests.get(url, verify=False, timeout=12, allow_redirects=True)
                found = render("requests / sem headers", r.text, r.status_code, r.url, headers=r.headers)
            except Exception as e:
                render("requests / sem headers", error=str(e))

        if found:
            st.balloons()
        else:
            st.error("⛔ Nenhuma estratégia funcionou para esta URL.")

    st.markdown("---")
    st.success("✅ Debug completo!")
