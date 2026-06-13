import requests
import urllib3
import ssl
import urllib.request
from urllib.parse import quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
    print("✅ curl_cffi disponível")
except ImportError:
    CURL_CFFI_AVAILABLE = False
    print("❌ curl_cffi NÃO instalado")

# ── URLs para testar ────────────────────────────────────────────────────────
TEST_URLS = [
    "http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "http://cdn.club8.ca/player_api.php?username=concmus03&password=3a3b3c3d",
    "https://websmt.ca/player_api.php?username=mgerminia&password=iptv2022",
]

HEADERS_BROWSER = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

HEADERS_VLC = {
    "User-Agent": "VLC/3.0.18 LibVLC/3.0.18",
    "Accept": "*/*",
    "Connection": "keep-alive",
}

class LegacySslAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            ctx.set_ciphers('ALL:@SECLEVEL=0')
        except:
            pass
        try:
            ctx.options |= 0x4
        except:
            pass
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


def divider(label):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print('='*60)

def show_result(label, resp_text=None, status_code=None, error=None, final_url=None):
    if error:
        print(f"  [{label}] ❌ ERRO: {error}")
    else:
        print(f"  [{label}] ✅ HTTP {status_code}")
        if final_url:
            print(f"  → Redirect final: {final_url}")
        print(f"  → Contém 'user_info': {'SIM ✅' if 'user_info' in resp_text else 'NÃO ❌'}")
        print(f"  → Contém 'status':    {'SIM' if 'status' in resp_text else 'NÃO'}")
        if 'user_info' in resp_text:
            # Mostra o trecho relevante
            idx = resp_text.find('user_info')
            snippet = resp_text[max(0, idx-10):idx+120]
            print(f"  → Trecho: {snippet!r}")
        else:
            print(f"  → Resposta (primeiros 300): {resp_text[:300]!r}")


for url in TEST_URLS:
    divider(f"URL: {url}")

    # ── 1. curl_cffi ────────────────────────────────────────────────────────
    if CURL_CFFI_AVAILABLE:
        for imp in ["chrome120", "chrome110", "safari17_0", "chrome107"]:
            try:
                r = curl_requests.get(url, impersonate=imp, timeout=10, allow_redirects=True, verify=False)
                show_result(f"curl_cffi/{imp}", r.text, r.status_code, final_url=r.url)
            except Exception as e:
                show_result(f"curl_cffi/{imp}", error=str(e))
    else:
        print("  [curl_cffi] PULADO — não instalado")

    # ── 2. requests padrão ──────────────────────────────────────────────────
    for label, headers in [("requests/browser", HEADERS_BROWSER), ("requests/vlc", HEADERS_VLC)]:
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=10, allow_redirects=True)
            show_result(label, r.text, r.status_code, final_url=r.url)
        except Exception as e:
            show_result(label, error=str(e))

    # ── 3. requests + SSL legado ─────────────────────────────────────────────
    for label, headers in [("ssl-legacy/browser", HEADERS_BROWSER), ("ssl-legacy/vlc", HEADERS_VLC)]:
        try:
            with requests.Session() as s:
                s.mount("https://", LegacySslAdapter())
                r = s.get(url, headers=headers, verify=False, timeout=10, allow_redirects=True)
                show_result(label, r.text, r.status_code, final_url=r.url)
        except Exception as e:
            show_result(label, error=str(e))

    # ── 4. urllib nativo ─────────────────────────────────────────────────────
    for label, headers in [("urllib/browser", HEADERS_BROWSER), ("urllib/vlc", HEADERS_VLC)]:
        try:
            ssl_ctx = ssl._create_unverified_context()
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ssl_ctx, timeout=10) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                show_result(label, content, resp.status, final_url=resp.url)
        except Exception as e:
            show_result(label, error=str(e))

    # ── 5. requests SEM follow redirect (ver redirect manual) ────────────────
    print("\n  --- Redirect manual (allow_redirects=False) ---")
    try:
        r = requests.get(url, headers=HEADERS_BROWSER, verify=False, timeout=10, allow_redirects=False)
        print(f"  HTTP {r.status_code} → Location: {r.headers.get('Location', 'N/A')}")
    except Exception as e:
        print(f"  ERRO: {e}")

print("\n\nDEBUG COMPLETO.")
