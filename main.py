import streamlit as st
import http.client
import urllib.parse
import requests
import urllib3

# Desabilitar avisos de segurança SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Debugger Baixo Nível IPTV", layout="wide")
st.title("🕵️‍♂️ Debugger de Baixo Nível - Emulação Cirúrgica de Navegador")
st.write("Burlas estruturais via conexões de socket bruto para quebrar o bloqueio Nginx.")

URLS_TESTE = [
    "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"
]

def testar_baixo_nivel(url, cenario):
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc
    path_query = parsed.path + "?" + parsed.query
    is_https = parsed.scheme == "https"
    
    # Abre o socket puro correto baseado no protocolo
    if is_https:
        conn = http.client.HTTPSConnection(host, timeout=10)
    else:
        conn = http.client.HTTPConnection(host, timeout=10)
        
    # skip_host e skip_accept_encoding removem qualquer rastro oculto do Python
    conn.putrequest("GET", path_query, skip_host=True, skip_accept_encoding=True)
    
    # Injeta os cabeçalhos na ordem exata e idêntica à de um navegador real
    if cenario == "chrome_puro":
        conn.putheader("Host", host)
        conn.putheader("Connection", "keep-alive")
        conn.putheader("Upgrade-Insecure-Requests", "1")
        conn.putheader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        conn.putheader("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8")
        conn.putheader("Accept-Encoding", "gzip, deflate")
        conn.putheader("Accept-Language", "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7")
    
    elif cenario == "http_1_0_force":
        # Força o protocolo antigo HTTP/1.0 que costuma ignorar regras de WAF/Firewall modernos
        conn._http_vsn = 10
        conn._http_vsn_str = 'HTTP/1.0'
        conn.putheader("Host", host)
        conn.putheader("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        conn.putheader("Accept", "*/*")
        
    conn.endheaders()
    
    response = conn.getresponse()
    status = response.status
    headers = dict(response.getheaders())
    
    # Lê e decodifica a resposta tratando possíveis compressões de dados
    body = response.read()
    try:
        if headers.get('content-encoding') == 'gzip':
            import gzip
            body = gzip.decompress(body)
        text = body.decode('utf-8', errors='ignore')
    except:
        text = body.decode('latin-1', errors='ignore')
        
    conn.close()
    return status, text, headers

if st.button("⚡ Executar Varredura de Baixo Nível"):
    for url in URLS_TESTE:
        st.markdown(f"### 🌐 Alvo: `{url}`")
        
        col1, col2 = st.columns(2)
        
        # -------------------------------------------------------------
        # ESTRATÉGIA 1: Emulação Avançada Chrome Sem Assinatura Python
        # -------------------------------------------------------------
        with col1:
            st.info("Estratégia 1: Chrome Estrutural (http.client)")
            try:
                status, text, headers = testar_baixo_nivel(url, "chrome_puro")
                sucesso = "user_info" in text
                
                if sucesso:
                    st.success(f"🟢 SUCESSO ({status})")
                    st.balloons()
                elif status == 406:
                    st.warning("🟡 Bloqueio 406")
                else:
                    st.error(f"🔴 Status: {status}")
                    
                st.write(f"Contém 'user_info'?: **{sucesso}**")
                with st.expander("Ver Resposta Bruta"):
                    st.code(text[:300], language="json" if sucesso else "html")
            except Exception as e:
                st.error(f"💥 Erro: {type(e).__name__}")
                st.caption(str(e))
                
        # -------------------------------------------------------------
        # ESTRATÉGIA 2: Forçar Protocolo Legado HTTP/1.0
        # -------------------------------------------------------------
        with col2:
            st.info("Estratégia 2: Bypass via HTTP/1.0 Legado")
            try:
                status, text, headers = testar_baixo_nivel(url, "http_1_0_force")
                sucesso = "user_info" in text
                
                if sucesso:
                    st.success(f"🟢 SUCESSO ({status})")
                    st.balloons()
                elif status == 406:
                    st.warning("🟡 Bloqueio 406")
                else:
                    st.error(f"🔴 Status: {status}")
                    
                st.write(f"Contém 'user_info'?: **{sucesso}**")
                with st.expander("Ver Resposta Bruta"):
                    st.code(text[:300], language="json" if sucesso else "html")
            except Exception as e:
                st.error(f"💥 Erro: {type(e).__name__}")
                st.caption(str(e))
                
        st.markdown("---")
