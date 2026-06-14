import requests
import streamlit as st

ip = requests.get("https://api.ipify.org").text

st.write("IP Público:")
st.code(ip)
