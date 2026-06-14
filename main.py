import streamlit as st
import requests
import urllib.parse

targetUrl = urllib.parse.quote("http://websmt.ca/player_api.php?username=concmus03&password=3a3b3c3d")
url = "http://api.scrape.do/?url=http%3A%2F%2Fwebsmt.ca%2Fplayer_api.php%3Fusername%3Dconcmus03%26password%3D3a3b3c3d&token=3a23ea3810a04b16bccfac96a2c3b1af73c97a98ef5&super=true&geoCode=BR".format(targetUrl)
headers = {
}


response = requests.request("get", url)

print(response.text)
