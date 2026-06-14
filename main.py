import requests
from urllib.parse import quote

url = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

scrape_url = (
    f"https://api.scrape.do/"
    f"?token=SEU_TOKEN"
    f"&url={quote(url)}"
    f"&super=true"
)

r = requests.get(scrape_url, timeout=60)

print("Status:", r.status_code)
print(r.text[:500])
