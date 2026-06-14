import requests
import streamlit as st

urls = [
    "https://websmt.ca",
    "https://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d"
]

for url in urls:

    st.write("###", url)

    try:
        r = requests.get(
            url,
            timeout=30,
            allow_redirects=True
        )

        st.write("Status:", r.status_code)

        st.write("Server:", r.headers.get("Server"))

        st.text(r.text[:500])

    except Exception as e:
        st.exception(e)
