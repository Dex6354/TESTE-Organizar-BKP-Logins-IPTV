import streamlit as st
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

st.set_page_config(page_title="Xtream API Debugger", layout="wide")

st.title("🛠️ Python Streamlit API Debugger (Navegador Real)")

# URL completa fornecida
url_padrao = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

url = st.text_input("URL da API para Debug:", value=url_padrao)

if st.button("Buscar Dados / Enviar Requisição", type="primary"):
    with st.spinner("Abrindo Chrome em segundo plano para burlar o bloqueio..."):
        driver = None
        try:
            # Configurações para o Chrome rodar oculto e parecer um usuário real
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Roda sem abrir a janela do navegador
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            # Inicializa o navegador real
            servico = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=servico, options=chrome_options)
            
            # Acessa a URL inteira
            driver.get(url)
            time.sleep(3)  # Aguarda 3 segundos para o Nginx/Cloudflare liberar o JSON
            
            # Captura o texto que aparece na tela (o JSON)
            conteudo_bruto = driver.find_element("xpath", "//body").text
            
            # Fecha o navegador
            driver.quit()
            
            # Exibe e processa o resultado
            st.subheader("Dados do JSON")
            try:
                dados_json = json.loads(conteudo_bruto)
                st.success("Sucesso! JSON retornado direto do navegador.")
                st.json(dados_json)
            except ValueError:
                st.error("O navegador abriu a página, mas o conteúdo não é um JSON válido.")
                st.text_area("Conteúdo da página:", value=conteudo_bruto, height=300)
                
        except Exception as e:
            if driver:
                driver.quit()
            st.error(f"Erro ao simular o navegador: {e}")
