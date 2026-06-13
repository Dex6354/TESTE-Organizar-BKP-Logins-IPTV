import streamlit as st
import subprocess
import sys
import requests
import urllib3

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
            st.success("✅ Instalado com sucesso! Recarregue a página (F5).")
            st.code(result.stdout)
        else:
            st.error("❌ Erro na instalação:")
            st.code(result.stderr)
    st.stop()

# ── Configurações ───────────────────────────────────────────────────────────
default_urls = """https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d
http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d
http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d
https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"""

urls_input = st.text_area("URLs para testar", value=default_urls, height=150)

IMPERSONATIONS = ["chrome", "chrome120", "chrome110", "chrome107"]

# Headers mais completos e realistas (muito importante para Cloudflare)
HEADERS_FULL = {
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
    "Referer": "https://websmt.ca/",
    "Origin": "https://websmt.ca",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "DNT": "1",
}

def render(label, text=None, code=None, url=None, error=None, headers=None):
    if error:
        st.error(f"**{label}** ❌ `{error}`")
        return False
    
    has_user_info = "user_info" in text if text else False
    if has_user_info:
        st.success(f"**{label}** → HTTP `{code}` ✅ **user_info ENCONTRADO!**")
        if url:
            st.caption(f"🔀 URL final: `{url}`")
        idx = text.find("user_info")
        st.code(text[max(0, idx-10):idx+600], language="json")
        return True
    else:
        st.warning(f"**{label}** → HTTP `{code}` ❌ sem user_info")
        if url:
            st.caption(f"🔀 URL final: `{url}`")
        if headers:
            with st.expander("Ver Response Headers"):
                st.json(dict(headers))
        st.code(text[:500] if text else "Sem conteúdo", language="text")
        return False


if st.button("▶️ Rodar Debug", type="primary"):
    urls = [u.strip() for u in urls_input.strip().splitlines() if u.strip()]

    for url in urls:
        st.markdown(f"---\n## 🌐 `{url}`")
        found = False

        # ── 1. curl_cffi com Session (melhor para Cloudflare) ─────────────────
        st.markdown("### 🦾 curl_cffi + Session (Recomendado)")
        try:
            session = curl_requests.Session()
            for imp in IMPERSONATIONS:
                if found:
                    break
                try:
                    r = session.get(
                        url,
                        impersonate=imp,
                        headers=HEADERS_FULL,
                        timeout=15,
                        allow_redirects=True,
                        verify=False
                    )
                    found = render(
                        f"curl_cffi Session / {imp}",
                        r.text, r.status_code, r.url, headers=r.headers
                    )
                except Exception as e:
                    render(f"curl_cffi Session / {imp}", error=str(e))
        except Exception as e:
            st.error(f"Erro ao criar session: {e}")

        # ── 2. curl_cffi sem session ────────────────────────────────────────
        if not found:
            st.markdown("### 🦾 curl_cffi (sem Session)")
            for imp in IMPERSONATIONS:
                if found:
                    break
                try:
                    r = curl_requests.get(
                        url,
                        impersonate=imp,
                        headers=HEADERS_FULL,
                        timeout=15,
                        allow_redirects=True,
                        verify=False
                    )
                    found = render(f"curl_cffi / {imp}", r.text, r.status_code, r.url, headers=r.headers)
                except Exception as e:
                    render(f"curl_cffi / {imp}", error=str(e))

        # ── 3. requests padrão ──────────────────────────────────────────────
        if not found:
            st.markdown("### 🌐 requests + Headers")
            try:
                r = requests.get(
                    url, 
                    headers=HEADERS_FULL, 
                    verify=False, 
                    timeout=15, 
                    allow_redirects=True
                )
                found = render("requests + Full Headers", r.text, r.status_code, r.url, headers=r.headers)
            except Exception as e:
                render("requests + Full Headers", error=str(e))

        # ── 4. requests básico (último recurso) ─────────────────────────────
        if not found:
            st.markdown("### 🔓 requests básico (sem headers)")
            try:
                r = requests.get(url, verify=False, timeout=12, allow_redirects=True)
                found = render("requests básico", r.text, r.status_code, r.url, headers=r.headers)
            except Exception as e:
                render("requests básico", error=str(e))

        if found:
            st.balloons()
            st.success("🎉 Sucesso nesta URL!")
        else:
            st.error("⛔ Nenhuma estratégia funcionou para esta URL.")

    st.markdown("---")
    st.success("✅ Debug completo!")

st.caption("Dica: Use sempre a primeira opção (curl_cffi + Session) — é a mais eficaz contra Cloudflare.")
