import streamlit as st
import requests
import urllib3
import ssl
import urllib.request
from urllib.parse import unquote

# Desabilitar avisos de segurança SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Debugger de Domínios IPTV", layout="wide")
st.title("🔍 Debugger de Conexão IPTV")
st.write("Testando os domínios problemáticos diretamente na página:")

# URLs exatas informadas com problema
URLS_TESTE = [
    "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive"
}

class LegacySslAdapter(requests.adapters.HTTPAdapter):
    """Força SSL antigo/legado"""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try: ctx.set_ciphers('ALL:@SECLEVEL=0')
        except: pass
        kwargs['ssl_context'] = ctx
        return super(LegacySslAdapter, self).init_poolmanager(*args, **kwargs)

# Botão para iniciar o teste manual na página
if st.button("⚡ Executar Testes de Conexão"):
    for url in URLS_TESTE:
        st.subheader(f"🌐 Alvo: `{url}`")
        
        # -------------------------------------------------------------
        # MÉTODO 1: Requests Moderno
        # -------------------------------------------------------------
        with st.expander("Camada 1: Requests Moderno (Padrão Navegador)", expanded=True):
            try:
                r = requests.get(url, headers=HEADERS, verify=False, timeout=10, allow_redirects=True)
                st.metric("Status Code", r.status_code)
                st.text(f"URL Final: {r.url}")
                st.write(f"Contém 'user_info'?: **{ 'user_info' in r.text }**")
                st.code(r.text[:300], language="json")
            except Exception as e:
                st.error(f"Falha: {type(e).__name__} -> {e}")

        # -------------------------------------------------------------
        # MÉTODO 2: Requests Criptografia Legada (SECLEVEL=0)
        # -------------------------------------------------------------
        with st.expander("Camada 2: Requests Legado (SECLEVEL=0)", expanded=False):
            try:
                with requests.Session() as session:
                    session.mount("https://", LegacySslAdapter())
                    r = session.get(url, headers=HEADERS, verify=False, timeout=10, allow_redirects=True)
                    st.metric("Status Code", r.status_code)
                    st.text(f"URL Final: {r.url}")
                    st.write(f"Contém 'user_info'?: **{ 'user_info' in r.text }**")
                    st.code(r.text[:300], language="json")
            except Exception as e:
                st.error(f"Falha: {type(e).__name__} -> {e}")

        # -------------------------------------------------------------
        # MÉTODO 3: Urllib Nativo do Python
        # -------------------------------------------------------------
        with st.expander("Camada 3: Urllib Nativo (Ignora travas)", expanded=False):
            try:
                ssl_ctx = ssl._create_unverified_context()
                req = urllib.request.Request(url, headers=HEADERS)
                with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                    st.text(f"URL Final: {response.geturl()}")
                    st.write(f"Contém 'user_info'?: **{ 'user_info' in content }**")
                    st.code(content[:300], language="json")
            except Exception as e:
                st.error(f"Falha: {type(e).__name__} -> {e}")
                
        st.markdown("---")
