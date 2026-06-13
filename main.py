import requests
import urllib3
import ssl
import urllib.request
from urllib.parse import unquote

# Desabilitar avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# URLs exatas informadas com problema
URLS_TESTE = [
    "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive"
}

class LegacySslAdapter(requests.adapters.HTTPAdapter):
    """Força SSL antigo/legado"""
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try: ctx.set_ciphers('ALL:@SECLEVEL=0')
        except: pass
        kwargs['ssl_context'] = ctx
        return super(LegacySslAdapter, self).init_poolmanager(*args, **kwargs)

print("=" * 60)
print("             INICIANDO DEBUGGER IPTV DOMÍNIOS          ")
print("=" * 60)

for url in URLS_TESTE:
    print(f"\n\n[ALVO]: {url}")
    print("-" * 60)

    # -------------------------------------------------------------
    # MÉTODO 1: Requests Moderno / Padrão
    # -------------------------------------------------------------
    print("\n-> [MÉTODO 1] Requests Moderno (Navegador Padrão):")
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=10, allow_redirects=True)
        print(f"   Status Code: {r.status_code}")
        print(f"   URL Final Redirecionada: {r.url}")
        print(f"   Contém 'user_info'?: {'user_info' in r.text}")
        print(f"   Resposta Bruta (150 chars): {r.text[:150].strip()}")
    except Exception as e:
        print(f"   ❌ FALHA: {type(e).__name__} -> {e}")

    # -------------------------------------------------------------
    # MÉTODO 2: Requests Criptografia Legada (SECLEVEL=0)
    # -------------------------------------------------------------
    print("\n-> [MÉTODO 2] Requests Legado (SECLEVEL=0):")
    try:
        with requests.Session() as session:
            session.mount("https://", LegacySslAdapter())
            r = session.get(url, headers=HEADERS, verify=False, timeout=10, allow_redirects=True)
            print(f"   Status Code: {r.status_code}")
            print(f"   URL Final Redirecionada: {r.url}")
            print(f"   Contém 'user_info'?: {'user_info' in r.text}")
            print(f"   Resposta Bruta (150 chars): {r.text[:150].strip()}")
    except Exception as e:
        print(f"   ❌ FALHA: {type(e).__name__} -> {e}")

    # -------------------------------------------------------------
    # MÉTODO 3: Urllib Nativo do Python
    # -------------------------------------------------------------
    print("\n-> [MÉTODO 3] Urllib Nativo (Ignora travas de Ciphers):")
    try:
        ssl_ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as response:
            content = response.read().decode('utf-8', errors='ignore')
            print(f"   URL Final Redirecionada: {response.geturl()}")
            print(f"   Contém 'user_info'?: {'user_info' in content}")
            print(f"   Resposta Bruta (150 chars): {content[:150].strip()}")
    except Exception as e:
        print(f"   ❌ FALHA: {type(e).__name__} -> {e}")

print("\n" + "=" * 60)
print("             FIM DOS TESTES DO DEBUGGER               ")
print("=" * 60)
