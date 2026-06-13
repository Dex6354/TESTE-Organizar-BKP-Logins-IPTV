import streamlit as st
import requests
import urllib3
import ssl
import urllib.request

# Desabilitar avisos de segurança SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Debugger Avançado IPTV v2", layout="wide")
st.title("🕵️‍♂️ Debugger de Cabeçalhos - Quebrando o Nginx 406")
st.write("Testando assinaturas profundas de motores de comunicação para contornar o bloqueio do painel.")

URLS_TESTE = [
    "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"
]

# Cenários ultra-específicos focados em ignorar assinaturas manjadas de scanners
CENARIOS = {
    "Cenário 1: Motor Android (okhttp)": {
        "headers": {
            "User-Agent": "okhttp/4.9.3",
            "Accept-Encoding": "gzip"
        },
        "remover_accept": True
    },
    "Cenário 2: Motor FFmpeg Nativo (Lavf)": {
        "headers": {
            "User-Agent": "Lavf/59.27.100",
            "Accept": "*/*"
        },
        "remover_accept": False
    },
    "Cenário 3: Player TiviMate Premium": {
        "headers": {
            "User-Agent": "TiviMate/4.7.0 (Linux; Android 11)",
            "Accept": "*/*"
        },
        "remover_accept": False
    },
    "Cenário 4: Sem cabeçalho 'Accept' (Clean Mozilla)": {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "remover_accept": True  # Remove o Accept padrão do Requests que gera o 406
    },
    "Cenário 5: Urllib Nativo sem metadados": {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        },
        "use_urllib": True
    }
}

if st.button("⚡ Executar Nova Varredura de Diagnóstico"):
    for url in URLS_TESTE:
        st.markdown(f"### 🌐 Alvo: `{url}`")
        
        cols = st.columns(len(CENARIOS))
        
        for idx, (nome_cenario, config) in enumerate(CENARIOS.items()):
            with cols[idx]:
                st.info(nome_cenario)
                try:
                    # Implementação via URLLIB Nativo (Cenário 5)
                    if config.get("use_urllib"):
                        ssl_ctx = ssl._create_unverified_context()
                        req = urllib.request.Request(url, headers=config["headers"])
                        # O urllib nativo não injeta o cabeçalho 'Accept' automaticamente
                        with urllib.request.urlopen(req, context=ssl_ctx, timeout=8) as response:
                            content = response.read().decode('utf-8', errors='ignore')
                            status = response.status
                            url_final = response.geturl()
                            sucesso = "user_info" in content
                            response_text = content
                    
                    # Implementação via Requests Controlado (Cenários 1, 2, 3, 4)
                    else:
                        session = requests.Session()
                        req = requests.Request('GET', url, headers=config["headers"])
                        prepared = session.prepare_request(req)
                        
                        # Removemos o 'Accept' padrão do requests caso configurado para evitar o 406
                        if config.get("remover_accept") and 'Accept' in prepared.headers:
                            del prepared.headers['Accept']
                            
                        r = session.send(prepared, verify=False, timeout=8, allow_redirects=True)
                        status = r.status_code
                        url_final = r.url
                        sucesso = "user_info" in r.text
                        response_text = r.text
                    
                    # Exibição dos resultados na interface
                    if sucesso:
                        st.success(f"🟢 SUCESSO ({status})")
                        st.balloons()
                    elif status == 406:
                        st.warning(f"🟡 Bloqueio 406")
                    elif status == 403:
                        st.error(f"🔴 Bloqueio 403")
                    else:
                        st.error(f"⚠️ Status: {status}")
                        
                    st.text(f"URL Final: {url_final}")
                    st.write(f"Contém 'user_info'?: **{sucesso}**")
                    
                    with st.expander("Ver Resposta Bruta"):
                        st.code(response_text[:250], language="html" if "html" in response_text else "json")
                        
                except Exception as e:
                    st.error(f"💥 Erro: {type(e).__name__}")
                    st.caption(str(e))
        st.markdown("---")
