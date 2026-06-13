import streamlit as st
import json
import re
import os
import pandas as pd
import requests
import urllib3
import ssl
import urllib.request
from urllib.parse import quote, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

# Desabilitar avisos de segurança SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Tenta importar curl_cffi para TLS fingerprint impersonation
try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

# Configurações de cabeçalhos realistas
HEADERS_BROWSER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive"
}

HEADERS_VLC = {
    "User-Agent": "VLC/3.0.18 LibVLC/3.0.18",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

class LegacySslAdapter(requests.adapters.HTTPAdapter):
    """Adaptador SSL para compatibilidade com cifras antigas e servidores legados."""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.set_ciphers('ALL:@SECLEVEL=0')
        except:
            pass
        try:
            ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        except:
            pass
        kwargs['ssl_context'] = ctx
        return super(LegacySslAdapter, self).init_poolmanager(*args, **kwargs)

def check_content(content):
    """Verifica o conteúdo da resposta e retorna 'active', 'offline' ou None."""
    if "user_info" not in content:
        return None
    content_clean = content.replace(" ", "")
    if '"status":"Expired"' in content_clean or '"status":"expired"' in content_clean:
        return "offline"
    return "active"

def test_single_user(user):
    """Testa o status do usuário com fallbacks para servidores modernos, legados e redirecionamentos."""
    name = user.get('name', '')
    url = user.get('url', '')

    # Remove emoji de status antigo (✅ ou ❌) se já existir no início do nome
    name = re.sub(r'^[✅❌]\s*', '', name)

    # 1. Extrai ou obtém o usuário
    username = user.get('username') or user.get('user', '')
    if not username:
        user_match = re.search(r"username=([^&]+)", url, re.IGNORECASE)
        username = unquote(user_match.group(1)) if user_match else ""
    else:
        username = unquote(str(username))

    # 2. Extrai ou obtém a senha
    password = user.get('password') or user.get('pass', '')
    if not password:
        pass_match = re.search(r"password=([^&]+)", url, re.IGNORECASE)
        password = unquote(pass_match.group(1)) if pass_match else ""
    else:
        password = unquote(str(password))

    # 3. Higieniza a URL base
    base_match = re.search(r"(https?://[^/]+)", url)
    base = base_match.group(1) if base_match else url
    if base:
        base = base.rstrip('/')
        if not base.startswith(('http://', 'https://')):
            base = 'http://' + base

    status = "offline"

    if username and password and base:
        api_url = f"{base}/player_api.php?username={quote(username)}&password={quote(password)}"
        
        # Gera variações de protocolo para cobrir redirecionamentos estritos de portas
        urls_to_test = [api_url]
        if api_url.startswith("https://"):
            urls_to_test.append(api_url.replace("https://", "http://", 1))
        elif api_url.startswith("http://"):
            urls_to_test.append(api_url.replace("http://", "https://", 1))

        found_active = False

        for target_url in urls_to_test:
            if found_active:
                break

            # ESTRATÉGIA 1: curl_cffi — TLS Fingerprint Impersonation (Resolve websmt.ca e similares)
            if CURL_CFFI_AVAILABLE:
                for impersonate in ["chrome120", "chrome110", "safari17_0"]:
                    try:
                        resp = curl_requests.get(
                            target_url,
                            impersonate=impersonate,
                            timeout=8,
                            allow_redirects=True,
                            verify=False
                        )
                        result = check_content(resp.text)
                        if result is not None:
                            status = result
                            found_active = True
                            break
                    except Exception:
                        continue
                if found_active:
                    break

            # ESTRATÉGIA 2: Conexão Moderna (Padrão do navegador)
            for headers in [HEADERS_BROWSER, HEADERS_VLC]:
                try:
                    resp = requests.get(target_url, headers=headers, verify=False, timeout=8, allow_redirects=True)
                    result = check_content(resp.text)
                    if result is not None:
                        status = result
                        found_active = True
                        break
                except Exception:
                    continue

            if found_active:
                break

            # ESTRATÉGIA 3: Conexão Legada (Força SECLEVEL=0 — Resolve odira.sbs)
            try:
                with requests.Session() as session:
                    session.mount("https://", LegacySslAdapter())
                    for headers in [HEADERS_BROWSER, HEADERS_VLC]:
                        try:
                            resp = session.get(target_url, headers=headers, verify=False, timeout=8, allow_redirects=True)
                            result = check_content(resp.text)
                            if result is not None:
                                status = result
                                found_active = True
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            if found_active:
                break

            # ESTRATÉGIA 4: Fallback Nativo do Sistema (urllib)
            for headers in [HEADERS_BROWSER, HEADERS_VLC]:
                try:
                    ssl_ctx = ssl._create_unverified_context()
                    req = urllib.request.Request(target_url, headers=headers)
                    with urllib.request.urlopen(req, context=ssl_ctx, timeout=8) as response:
                        content = response.read().decode('utf-8', errors='ignore')
                        result = check_content(content)
                        if result is not None:
                            status = result
                            found_active = True
                            break
                except Exception:
                    continue

    # Define o novo emoji com base no status atualizado
    user['name'] = f"✅ {name}" if status == "active" else f"❌ {name}"
    
    # Monta a URL JSON final para a tabela clicável
    if username and password and base:
        user['json_link'] = f"{base}/player_api.php?username={quote(username)}&password={quote(password)}"
    else:
        user['json_link'] = ""
        
    return user

def sort_users(users_list):
    """Organiza a lista de usuários com base na hierarquia estipulada."""
    def get_sort_key(user):
        name = user.get('name', '')
        
        if '✅' in name: r1 = 0
        elif '❌' in name: r1 = 1
        else: r1 = 2
            
        if '🔥' in name: r2 = 0
        elif '💧' in name: r2 = 1
        else: r2 = 2
            
        if '🟢' in name: r3 = 0
        elif '🔞' in name: r3 = 1
        else: r3 = 2
            
        if '📺' in name: r4 = 0
        elif '📱' in name: r4 = 1
        else: r4 = 2
            
        r5 = name.lower()
        return (r1, r2, r3, r4, r5)

    return sorted(users_list, key=get_sort_key)


st.set_page_config(page_title="Organizador de Logins", layout="centered")
st.subheader("Organizador de Logins .dev")

if not CURL_CFFI_AVAILABLE:
    st.warning("⚠️ `curl_cffi` não instalado. Alguns servidores com TLS fingerprinting (ex: websmt.ca) podem falhar. Instale com: `pip install curl_cffi`")

uploaded_file = st.file_uploader("Escolha um arquivo .dev", type="dev")

if uploaded_file is not None:
    try:
        file_content = uploaded_file.getvalue().decode("utf-8")
        data = json.loads(file_content)

        if "multi_users" in data:
            original_users = data["multi_users"]

            with st.spinner("⚡ Testando status dos servidores de IPTV..."):
                tested_users = []
                with ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(test_single_user, user) for user in original_users]
                    for future in as_completed(futures):
                        tested_users.append(future.result())

            st.success("Análise de status concluída com sucesso!")
            organized_users = sort_users(tested_users)

            st.subheader("Lista de Usuários Organizada")

            df_users = pd.DataFrame(organized_users)
            
            cols = list(df_users.columns)
            for c in ['name', 'url', 'json_link']:
                if c in cols:
                    cols.remove(c)
            
            ordered_cols = []
            if 'name' in df_users.columns:
                ordered_cols.append('name')
            if 'url' in df_users.columns:
                ordered_cols.append('url')
                
            ordered_cols.extend(cols)
            
            if 'json_link' in df_users.columns:
                ordered_cols.append('json_link')
                
            df_users = df_users[ordered_cols]

            edited_df = st.data_editor(
                df_users, 
                num_rows="dynamic", 
                use_container_width=True,
                column_config={
                    "userid": None,
                    "type": None,
                    "json_link": st.column_config.LinkColumn("Link JSON", help="URL gerada para a API do Player")
                },
                disabled=["json_link"]
            )

            edited_users = edited_df.to_dict(orient="records")
            for user in edited_users:
                user.pop('json_link', None)

            new_data = {"multi_users": edited_users}
            organized_content = json.dumps(new_data, indent=2, ensure_ascii=False)

            original_file_name, file_extension = os.path.splitext(uploaded_file.name)
            download_file_name = f"{original_file_name}_organized{file_extension}"

            st.download_button(
                label="Clique para Baixar o Arquivo Organizado",
                data=organized_content,
                file_name=download_file_name,
                mime="application/octet-stream"
            )

        else:
            st.error("O arquivo `.dev` não contém a chave 'multi_users'.")

    except json.JSONDecodeError:
        st.error("Erro ao decodificar o arquivo JSON. Certifique-se de que é um arquivo JSON válido.")
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")
