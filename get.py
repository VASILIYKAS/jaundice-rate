import requests

urls = [
    "https://inosmi.ru/politic/20190629/245376799.html",
    "https://inosmi.ru/politic/20190629/245379332.html",
    "https://inosmi.ru/20260202/khromaya_utka-276910274.html"
]
url_param = ','.join(urls)
response = requests.get(f"http://127.0.0.1:8080/?urls={url_param}")
print(response.json())