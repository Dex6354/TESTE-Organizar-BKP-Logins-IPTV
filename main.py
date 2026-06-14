import streamlit as st
import requests

st.set_page_config(page_title="Requisição com Proxy Gratuito", layout="centered")

st.title("Requisição com Proxy Gratuito (Brasil)")
st.write("Buscando proxies públicos do Brasil dinamicamente para evitar o erro 406.")

TARGET_URL = "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

def obter_proxy_brasil():
    """Busca dinamicamente um proxy público do Brasil que esteja ativo."""
    try:
        # API pública que lista proxies gratuitos
        url = "https://proxylist.geonode.com/api/proxy-list?country=BR&limit=5&page=1&sort_by=lastChecked&sort_type=desc"
        response = requests.get(url, timeout=10)
        dados = response.json()
        
        if dados and "data" in dados and len(dados["data"]) > 0:
            for proxy in dados["data"]:
                protocolo = proxy["protocols"][0]
                # Filtra apenas protocolos HTTP/HTTPS simples para o requests
                if protocolo in ["http", "https"]:
                    ip = proxy["ip"]
                    porta = proxy["port"]
                    return {
                        "http": f"http://{ip}:{porta}",
                        "https": f"http://{ip}:{porta}"
                    }
    except Exception:
        pass
    return None

if st.button("Executar Requisição", type="primary"):
    with st.spinner("Buscando proxy gratuito do Brasil na lista pública..."):
        proxies = obter_proxy_brasil()
        
        if proxies:
            st.info(f"Proxy encontrado e aplicado: {proxies['http']}")
        else:
            st.warning("Nenhum proxy gratuito responsivo encontrado no momento. Tentando conexão direta...")

    with st.spinner("Executando requisição..."):
        # Headers completos de navegador para evitar bloqueios adicionais
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        try:
            # Executa com o proxy obtido (se houver)
            response = requests.get(TARGET_URL, headers=headers, proxies=proxies, timeout=20)
            
            st.subheader("Informações da Resposta")
            st.metric("Status Code", response.status_code)

            st.subheader("Conteúdo da Resposta")
            try:
                st.json(response.json())
            except ValueError:
                st.text(response.text)

        except Exception as e:
            st.error(f"Erro ao conectar: {e}. Como proxies gratuitos falham muito, tente clicar novamente para sortear outro IP.")
