import requests
from bs4 import BeautifulSoup

def run():
    url = "https://www.seoulouba.co.kr/campaign/?cat=377" # 방문형
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    items = soup.select(".campaign_content")
    if items:
        for idx, item in enumerate(items[:2]):
            print(f"-- Item {idx} HTML --")
            print(item.prettify())

if __name__ == "__main__":
    run()
