import streamlit as st
import requests
import json
from pprint import pprint

URL = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

st.title("Debugger IPTV")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.6",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1"
}

try:

    st.write("### Fazendo request...")

    r = requests.get(
        URL,
        headers=headers,
        timeout=30,
        allow_redirects=True
    )

    st.write("### Status")
    st.code(r.status_code)

    st.write("### URL Final")
    st.code(r.url)

    st.write("### Headers da Resposta")
    st.json(dict(r.headers))

    st.write("### Content-Type")
    st.code(r.headers.get("content-type"))

    st.write("### Primeiros 3000 caracteres")
    st.text(r.text[:3000])

    st.write("### JSON")

    try:
        st.json(r.json())
    except Exception as e:
        st.error(f"Erro JSON: {e}")

except Exception as e:
    st.exception(e)
