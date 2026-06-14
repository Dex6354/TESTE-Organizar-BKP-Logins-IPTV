import streamlit as st
import requests
import json
import time
from urllib.parse import quote

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🚀 Solução Definitiva: Conexão Estabilizada 100% (Status 200)")

# URL padrão
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"
url = st.text_input("URL da API para Debug:", value=url_padrao)
token = st.text_input("Scrape.do Token:", value="3a23ea3810a04b16bccfac96a2c3b1af73c97a98ef5", type="password")

if st.button("Buscar Dados (Forçar Status 200)", type="primary"):
    # Parâmetros de estabilização
    max_tentativas = 5
    sucesso = False
    resposta = None
    
    status_progresso = st.empty()
    
    for tentativa in range(1, max_tentativas + 1):
        status_progresso.info(f"🔄 Tentativa {tentativa}/{max_tentativas}: Solicitando IP limpo ao Scrape.do...")
        
        try:
            url_codificada = quote(url)
            # Desativamos o 'render' (pesado) e usamos o super proxy com cabeçalhos customizados
            scrape_url = f"https://api.scrape.do/?token={token}&url={url_codificada}&super=true&customHeaders=true"
            
            # Personificação exata de um aplicativo de IPTV (Evita o bloqueio do Nginx/Cloudflare)
            headers = {
                "User-Agent": "IPTVSmarters",
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive"
            }
            
            resposta = requests.get(scrape_url, headers=headers, timeout=20)
            
            if resposta.status_code == 200:
                sucesso = True
                status_progresso.success(f"🟢 Sucesso na Tentativa {tentativa}! Conexão estabelecida.")
                break
            else:
                st.warning(f"⚠️ IP da tentativa {tentativa} retornou {resposta.status_code}. Rotacionando proxy...")
                time.sleep(1) # Pequena pausa antes de rotacionar o IP
                
        except Exception as e:
            st.error(f"Erro na tentativa {tentativa}: {e}")
            time.sleep(1)

    # --- PROCESSAMENTO DO RESULTADO ---
    if sucesso and resposta:
        st.subheader("Dados do JSON")
        
        texto_limpo = resposta.text
        # Limpa qualquer resíduo de HTML que o painel envie
        if "<pre>" in texto_limpo and "</pre>" in texto_limpo:
            texto_limpo = texto_limpo.split("<pre>")[1].split("</pre>")[0]
        elif "<body>" in texto_limpo and "</body>" in texto_limpo:
            try:
                texto_limpo = texto_limpo.split("<body>")[1].split("</body>")[0]
                if "<pre" in texto_limpo:
                    texto_limpo = texto_limpo.split(">")[1].split("</pre>")[0]
            except IndexError:
                pass
        
        texto_limpo = texto_limpo.strip()
        
        try:
            dados_json = json.loads(texto_limpo)
            st.json(dados_json)
        except ValueError:
            st.error("O servidor respondeu com 200, mas o formato não é um JSON puro.")
            st.text_area("Conteúdo bruto:", value=resposta.text, height=250)
    else:
        st.error("❌ Não foi possível obter Status 200 após as 5 tentativas. Tente novamente para forçar uma nova rota de IPs.")
