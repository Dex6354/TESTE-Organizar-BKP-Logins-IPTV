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

# Cabeçalhos minimalistas para evitar o erro 406 Not Acceptable do Nginx
LISTA_HEADERS = [
    {"User-Agent": "VLC/3.0.18 LibVLC/3.0.18"}, # Simula player real
    {"User-Agent": "Mozilla/5.0"},               # Agente genérico minimalista
    {}                                           # Totalmente limpo (vazio)
]

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

def test_single_user(user):
    """Testa o status do usuário com cabeçalhos limpos para evitar bloqueios 406."""
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
        
        # Gera variações de protocolo (HTTP/HTTPS)
        urls_to_test = [api_url]
        if api_url.startswith("https://"):
            urls_to_test.append(api_url.replace("https://", "http://", 1))
        elif api_url.startswith("http://"):
            urls_to_test.append(api_url.replace("http://", "https://", 1))

        found_active = False

        for target_url in urls_to_test:
            if found_active:
                break

            # Tenta as combinações de cabeçalhos limpos
            for headers in LISTA_HEADERS:
                # ESTRATÉGIA 1: Conexão Direta/Moderna
                try:
                    resp = requests.get(target_url, headers=headers, verify=False, timeout=8, allow_redirects=True)
                    content = resp.text
                    if "user_info" in content:
                        if '"status":"Expired"' in content.replace(" ", "") or '"status":"expired"' in content.replace(" ", ""):
                            status = "offline"
                        else:
                            status = "active"
                        found_active = True
                        break
                except:
                    pass

                # ESTRATÉGIA 2: Modo Legado (SECLEVEL=0)
                if not found_active:
                    try:
                        with requests.Session() as session:
                            session.mount("https://", LegacySslAdapter())
                            resp = session.get(target_url, headers=headers, verify=False, timeout=8, allow_redirects=True)
                            content = resp.text
                            if "user_info" in content:
                                if '"status":"Expired"' in content.replace(" ", "") or '"status":"expired"' in content.replace(" ", ""):
                                    status = "offline"
                                else:
                                    status = "active"
                                found_active = True
                                break
                    except:
                        pass

                # ESTRATÉGIA 3: Fallback Nativo (urllib)
                if not found_active:
                    try:
                        ssl_ctx = ssl._create_unverified_context()
                        try:
                            ssl_ctx.set_ciphers('ALL:@SECLEVEL=0')
                        except:
                            pass
                        req = urllib.request.Request(target_url, headers=headers)
                        with urllib.request.urlopen(req, context=ssl_ctx, timeout=8) as response:
                            content = response.read().decode('utf-8', errors='ignore')
                            if "user_info" in content:
                                if '"status":"Expired"' in content.replace(" ", "") or '"status":"expired"' in content.replace(" ", ""):
                                    status = "offline"
                                else:
                                    status = "active"
                                found_active = True
                                break
                    except:
                        pass

            if found_active:
                break

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
