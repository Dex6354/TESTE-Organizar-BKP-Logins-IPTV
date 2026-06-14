import socket

st.write("### DNS")

try:
    ip = socket.gethostbyname("websmt.ca")
    st.code(ip)
except Exception as e:
    st.exception(e)
