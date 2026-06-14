import streamlit as st
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Streamlit Cloud API Debugger (Bypass IP AWS)")

# URL completa fornecida
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"
url = st.text_input("URL da API para Debug:", value=url_padrao)

# Campo para injetar um Proxy e burlar o bloqueio de Datacenter da AWS
proxy = st.text_input(
    "Proxy IP:Porta (Opcional - Ex: 198.23.239.231:80)", 
    help="Insira um proxy HTTP/SOCKS válido para camuflar o IP do Streamlit Cloud."
)

if st.button("Buscar Dados / Enviar Requisição", type="primary"):
    with st.spinner("Disparando Chromium headless no servidor do Streamlit..."):
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Injeta o proxy se ele for digitado pelo usuário
            if proxy:
                chrome_options.add_argument(f"--proxy-server={proxy}")
            
            # Caminhos padrão do Streamlit Cloud Linux
            chrome_options.binary_location = "/usr/bin/chromium"
            servico = Service("/usr/bin/chromedriver")

            # Inicializa o navegador
            driver = webdriver.Chrome(service=servico, options=chrome_options)
            driver.get(url)
            time.sleep(5)  # Tempo para resposta do servidor
            
            conteudo_bruto = driver.find_element("xpath", "//body").text
            driver.quit()
            
            # Processa o JSON recebido
            st.subheader("Dados do JSON")
            try:
                dados_json = json.loads(conteudo_bruto)
                st.success("Sucesso! O servidor aceitou a conexão e entregou o JSON.")
                st.json(dados_json)
            except ValueError:
                st.error("O servidor barrou a requisição (Retornou a página do Nginx).")
                st.text_area("Resposta do Servidor:", value=conteudo_bruto, height=300)
                if not proxy:
                    st.info("💡 **O que fazer:** Como você está na nuvem, use sites de proxies gratuitos (como *sslproxies.org* ou *geonode.com*) e insira um IP:Porta válido no campo acima para contornar o bloqueio de ASN da AWS.")
                
        except Exception as e:
            if driver:
                driver.quit()
            st.error(f"Erro ao executar o Chromium na Nuvem: {e}")
