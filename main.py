import streamlit as st
import requests
import httpx
import socket
import json

URL = "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"

st.set_page_config(page_title="IPTV Debugger")

st.title("🔍 IPTV Debugger")

try:
    st.subheader("DNS")

    infos = socket.getaddrinfo("websmt.ca", 443)

    ips = sorted(list(set(i[4][0] for i in infos)))

    st.json({
        "ips_encontrados": ips
    })

except Exception as e:
    st.exception(e)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    "Referer": "https://websmt.ca/",
    "Origin": "https://websmt.ca"
}

st.subheader("Requests")

try:

    r = requests.get(
        URL,
        headers=headers,
        timeout=30,
        verify=True,
        allow_redirects=True
    )

    st.write("Status:", r.status_code)

    st.write("URL Final:")
    st.code(r.url)

    st.write("Headers:")
    st.json(dict(r.headers))

    st.write("Primeiros 2000 caracteres:")
    st.text(r.text[:2000])

    try:
        st.write("JSON:")
        st.json(r.json())
    except:
        st.warning("Resposta não é JSON")

except Exception as e:
    st.exception(e)

st.divider()

st.subheader("HTTPX HTTP/2")

try:

    with httpx.Client(
        http2=True,
        follow_redirects=True,
        timeout=30
    ) as client:

        r = client.get(
            URL,
            headers=headers
        )

        st.write("Status:", r.status_code)

        st.write("URL Final:")
        st.code(str(r.url))

        st.write("Headers:")
        st.json(dict(r.headers))

        st.write("Primeiros 2000 caracteres:")
        st.text(r.text[:2000])

        try:
            st.write("JSON:")
            st.json(r.json())
        except:
            st.warning("Resposta não é JSON")

except Exception as e:
    st.exception(e)

st.divider()

st.subheader("Resultado")

st.info(
    "Se Requests e HTTPX retornarem 'Welcome to nginx' ou 406, "
    "o problema não é Python nem header. O servidor está tratando "
    "o IP do Streamlit Cloud de forma diferente do IP da sua máquina."
)
