import streamlit as st
import requests
import urllib3
from urllib.parse import urlparse, parse_qs

# Desabilitar avisos de segurança SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Debugger Avançado IPTV v3", layout="wide")
st.title("🕵️‍♂️ Debugger IPTV - Quebrando Bloqueio Estrutural")
st.write("Testando emulação total de navegador, interceptação de rota e requisições via POST.")

URLS_TESTE = [
    "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"
]

if st.button("⚡ Executar Varredura Avançada"):
    for url in URLS_TESTE:
        st.markdown(f"### 🌐 Alvo: `{url}`")
        
        # Decompõe a URL para extrair o Host e os dados de login dinamicamente
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        queries = parse_qs(parsed_url.query)
        username = queries.get('username', [''])[0]
        password = queries.get('password', [''])[0]
        base_api = f"{parsed_url.scheme}://{host}/player_api.php"

        # Novos cenários cirúrgicos para burlar a regra do Nginx
        CENARIOS = {
            "1. Strict JSON Client": {
                "method": "GET",
                "url": url,
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept": "application/json, text/javascript, */*; q=0.01"
                },
                "allow_redirects": True
            },
            "2. Chrome Real Completo": {
                "method": "GET",
                "url": url,
                "headers": {
                    "Host": host,
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-User": "?1",
                    "Sec-Fetch-Dest": "document",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"
                },
                "allow_redirects": True
            },
            "3. Travar Redirecionamento": {
                "method": "GET",
                "url": url,
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept": "*/*"
                },
                "allow_redirects": False
            },
            "4. Método POST (URL)": {
                "method": "POST",
                "url": url,
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept": "*/*"
                },
                "allow_redirects": True
            },
            "5. Método POST (Form Data)": {
                "method": "POST_DATA",
                "url": base_api,
                "data": {"username": username, "password": password},
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Accept": "application/json, */*"
                },
                "allow_redirects": True
            }
        }

        cols = st.columns(len(CENARIOS))
        
        for idx, (nome_cenario, conf) in enumerate(CENARIOS.items()):
            with cols[idx]:
                st.info(nome_cenario)
                try:
                    # Executa a requisição conforme a estratégia configurada
                    if conf["method"] == "GET":
                        r = requests.get(conf["url"], headers=conf["headers"], verify=False, timeout=8, allow_redirects=conf["allow_redirects"])
                    elif conf["method"] == "POST":
                        r = requests.post(conf["url"], headers=conf["headers"], verify=False, timeout=8, allow_redirects=conf["allow_redirects"])
                    elif conf["method"] == "POST_DATA":
                        r = requests.post(conf["url"], data=conf["data"], headers=conf["headers"], verify=False, timeout=8, allow_redirects=conf["allow_redirects"])
                    
                    status = r.status_code
                    sucesso = "user_info" in r.text
                    
                    if sucesso:
                        st.success(f"🟢 SUCESSO ({status})")
                        st.balloons()
                    elif status == 406:
                        st.warning(f"🟡 Bloqueio 406")
                    elif status == 403:
                        st.error(f"🔴 Bloqueio 403")
                    else:
                        st.error(f"⚠️ Status: {status}")
                        
                    st.text(f"URL Final: {r.url}")
                    st.write(f"Contém 'user_info'?: **{sucesso}**")
                    
                    with st.expander("Ver Cabeçalhos de Resposta"):
                        st.json(dict(r.headers))
                    with st.expander("Ver Resposta Bruta"):
                        st.code(r.text[:250], language="html" if "html" in r.text else "json")
                        
                except Exception as e:
                    st.error(f"💥 Erro: {type(e).__name__}")
                    st.caption(str(e))
        st.markdown("---")
