import streamlit as st
import requests
import urllib3
import ssl
import urllib.request

# Desabilitar avisos de segurança SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Debugger Avançado IPTV", layout="wide")
st.title("🕵️‍♂️ Debugger de Cabeçalhos & Bloqueios Nginx")
st.write("Vamos testar variações de assinaturas (Headers) para quebrar o erro 406.")

URLS_TESTE = [
    "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"
]

# Dicionário de cenários de teste (Variando estritamente os cabeçalhos)
CENARIOS = {
    "Cenário 1: Player IPTV Real (Smarters)": {
        "User-Agent": "IPTVSmarters",
        "Accept": "*/*"
    },
    "Cenário 2: Player VLC Puro": {
        "User-Agent": "VLC/3.0.18 LibVLC/3.0.18",
        "Accept": "*/*"
    },
    "Cenário 3: Totalmente Pelado (Sem Headers)": {},
    "Cenário 4: User-Agent Padrão do Python-Requests": None, # Deixa a biblioteca decidir
    "Cenário 5: Android Mobile Player": {
        "User-Agent": "Mozilla/5.0 (Linux; Android 12; TV) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*"
    }
}

if st.button("⚡ Executar Varredura de Diagnóstico"):
    for url in URLS_TESTE:
        st.markdown(f"### 🌐 Alvo: `{url}`")
        
        # Cria colunas para organizar os resultados visualmente na tela
        cols = st.columns(len(CENARIOS))
        
        for idx, (nome_cenario, headers) in enumerate(CENARIOS.items()):
            with cols[idx]:
                st.info(nome_cenario)
                try:
                    # Executa a requisição baseada no cenário
                    if headers is None:
                        # Deixa o requests usar o header dele padrão (python-requests/x.x)
                        r = requests.get(url, verify=False, timeout=8, allow_redirects=True)
                    else:
                        r = requests.get(url, headers=headers, verify=False, timeout=8, allow_redirects=True)
                    
                    status = r.status_code
                    sucesso = "user_info" in r.text
                    
                    # Estiliza baseado no sucesso da resposta real
                    if sucesso:
                        st.success(f"🟢 SUCESSO (200)")
                        st.balloons()
                    elif status == 406:
                        st.warning(f"🟡 Bloqueio 406")
                    else:
                        st.error(f"🔴 Status: {status}")
                        
                    st.text(f"URL Final: {r.url}")
                    st.write(f"Contém 'user_info'?: **{sucesso}**")
                    
                    with st.expander("Ver Resposta Bruta"):
                        st.code(r.text[:250], language="html")
                        
                except Exception as e:
                    st.error(f"💥 Erro: {type(e).__name__}")
                    st.caption(str(e))
        st.markdown("---")
