import streamlit as st
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Streamlit Cloud API Debugger (Navegador Linux)")

# URL completa fornecida
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"
url = st.text_input("URL da API para Debug:", value=url_padrao)

if st.button("Buscar Dados / Enviar Requisição", type="primary"):
    with st.spinner("Disparando Chromium headless no servidor do Streamlit..."):
        driver = None
        try:
            # Configurações obrigatórias para rodar Linux/Streamlit Cloud
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Caminhos binários padrão do ambiente Linux do Streamlit Cloud
            chrome_options.binary_location = "/usr/bin/chromium"
            servico = Service("/usr/bin/chromedriver")

            # Inicializa o navegador do servidor
            driver = webdriver.Chrome(service=servico, options=chrome_options)
            
            # Acessa a API
            driver.get(url)
            time.sleep(5)  # 5 segundos para o Cloudflare processar a entrada
            
            # Captura o texto gerado
            conteudo_bruto = driver.find_element("xpath", "//body").text
            driver.quit()
            
            # Processa o JSON recebido
            st.subheader("Dados do JSON")
            try:
                dados_json = json.loads(conteudo_bruto)
                st.success("Sucesso! O Cloudflare aceitou o navegador do Streamlit Cloud.")
                st.json(dados_json)
            except ValueError:
                st.error("O navegador abriu, mas o servidor bloqueou o IP da Nuvem (AWS/Streamlit Cloud).")
                st.text_area("Resposta do Servidor:", value=conteudo_bruto, height=300)
                
        except Exception as e:
            if driver:
                driver.quit()
            st.error(f"Erro ao executar o Chromium na Nuvem: {e}")
            st.info("Confirme se os arquivos 'packages.txt' e 'requirements.txt' estão na raiz do seu GitHub.")
