import streamlit as st
import requests
import json
from urllib.parse import quote

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Streamlit Cloud API Debugger (Estabilização Antibloqueio)")

# URL padrão
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"
url = st.text_input("URL da API para Debug:", value=url_padrao)
token = st.text_input("Scrape.do Token:", value="3a23ea3810a04b16bccfac96a2c3b1af73c97a98ef5", type="password")

# Configurações otimizadas ativadas por padrão para evitar o erro 406 intermitente
col1, col2 = st.columns(2)
with col1:
    usar_super = st.checkbox("Ativar Super Proxy (Residencial)", value=True, help="Obrigatório para burlar o bloqueio de IP da AWS.")
with col2:
    render_js = st.checkbox("Forçar Renderização de Navegador (Evita Erro 406)", value=True, help="Faz o Scrape.do usar um navegador real, eliminando rejeições do Nginx.")

if st.button("Buscar Dados via Scrape.do", type="primary"):
    with st.spinner("Conectando através de navegador residencial remoto (Sem quedas)..."):
        try:
            url_codificada = quote(url)
            scrape_url = f"https://api.scrape.do/?token={token}&url={url_codificada}"
            
            headers = {}
            
            # Se a renderização JS estiver ativa, o Scrape.do gerencia os cabeçalhos perfeitamente.
            # Caso contrário, injetamos um cabeçalho completo de navegador moderno.
            if render_js:
                scrape_url += "&render=true"
            else:
                scrape_url += "&customHeaders=true"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    "Accept": "*/*",
                    "Accept-Language": "pt-BR,pt;q=0.9",
                    "Connection": "keep-alive"
                }
                
            if usar_super:
                scrape_url += "&super=true"
                
            resposta = requests.get(scrape_url, headers=headers, timeout=60)
            
            st.subheader("Status da Requisição")
            st.write(f"**Status Code:** {resposta.status_code}")
            
            st.subheader("Dados do JSON")
            
            # Limpeza de possíveis wrappers HTML/Pre do painel
            texto_limpo = resposta.text
            if "<pre>" in texto_limpo and "</pre>" in texto_limpo:
                texto_limpo = texto_limpo.split("<pre>")[1].split("</pre>")[0]
            elif "<body>" in texto_limpo and "</body>" in texto_limpo:
                # Caso o navegador retorne a estrutura básica do DOM
                try:
                    texto_limpo = texto_limpo.split("<body>")[1].split("</body>")[0]
                    if "<pre" in texto_limpo:
                        texto_limpo = texto_limpo.split(">")[1].split("</pre>")[0]
                except IndexError:
                    pass

            texto_limpo = texto_limpo.strip()

            try:
                dados_json = json.loads(texto_limpo)
                st.success("Sucesso estável! JSON extraído corretamente.")
                st.json(dados_json)
            except ValueError:
                st.error("O servidor respondeu, mas o conteúdo não pôde ser convertido diretamente.")
                st.text_area("Conteúdo bruto retornado:", value=resposta.text, height=350)
                    
        except Exception as e:
            st.error(f"Erro na conexão: {e}")
