import streamlit as st
import subprocess
import requests
import urllib3
import json
import re

# Desabilitar avisos de segurança SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="Debugger Nativo IPTV v4", layout="wide")
st.title("🕵️‍♂️ Debugger de Infraestrutura - Camada do Sistema Operacional")
st.write("Burlado o bloqueio de TLS/Handshake usando o motor de rede nativo do sistema (Curl).")

URLS_TESTE = [
    "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"
]

def executar_curl_nativo(url):
    """Executa a requisição usando o executável curl do próprio sistema operacional."""
    cmd = [
        "curl",
        "-s",                # Silencioso (sem barra de progresso)
        "-i",                # Inclui cabeçalhos de resposta no output
        "-k",                # Ignora erros de certificado SSL
        "-L",                # Segue redirecionamentos (essencial para o status 302)
        "-m", "10",          # Timeout de 10 segundos
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        url
    ]
    
    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
        output = resultado.stdout
        
        # Separa os cabeçalhos do corpo do JSON
        partes = output.split("\r\n\r\n")
        corpo = partes[-1] if partes else ""
        headers_brutos = "\n".join(partes[:-1]) if len(partes) > 1 else output
        
        # Captura o último Status Code da resposta
        status_match = re.findall(r"HTTP\/[\d\.]+\s+(\d+)", headers_brutos)
        status = int(status_match[-1]) if status_match else 0
        
        return status, corpo, headers_brutos
    except Exception as e:
        return 999, f"Erro ao executar subprocesso curl: {e}", ""

if st.button("⚡ Executar Varredura via Motor Nativo"):
    for url in URLS_TESTE:
        st.markdown(f"### 🌐 Alvo: `{url}`")
        
        col1, col2 = st.columns(2)
        
        # -------------------------------------------------------------
        # ESTRATÉGIA 1: Motor Nativo do Sistema (Bypass de TLS/JA3)
        # -------------------------------------------------------------
        with col1:
            st.info("Estratégia 1: Subprocesso Curl (Sistema Nativo)")
            status, corpo, headers = executar_curl_nativo(url)
            sucesso = "user_info" in corpo
            
            if sucesso:
                st.success(f"🟢 SUCESSO ({status})")
                st.balloons()
            elif status == 406:
                st.warning("🟡 Bloqueio 406 persistente")
            else:
                st.error(f"🔴 Status do Curl: {status}")
                
            st.write(f"Contém 'user_info'?: **{sucesso}**")
            with st.expander("Ver Resposta Bruta do Sistema"):
                st.code(corpo[:400], language="json" if sucesso else "html")
                
        # -------------------------------------------------------------
        # ESTRATÉGIA 2: Rastreamento do Redirecionamento (Análise do 302)
        # -------------------------------------------------------------
        with col2:
            st.info("Estratégia 2: Rastreamento de Rota (Requests Sem Seguir)")
            try:
                # Teste sem seguir o redirect para ver para onde o cdn.club8.ca aponta
                r = requests.get(url, verify=False, timeout=6, allow_redirects=False)
                st.write(f"Status Base: **{r.status_code}**")
                st.write(f"Location Header: `{r.headers.get('Location', 'Nenhum')}`")
                
                with st.expander("Ver Cabeçalhos HTTP do Servidor"):
                    st.json(dict(r.headers))
            except Exception as e:
                st.error(f"💥 Falha na rota: {type(e).__name__}")
        
        st.markdown("---")
