import requests
from bs4 import BeautifulSoup

def run():
    url = "https://www.seoulouba.co.kr/campaign/?cat=378" # 맛집 방문형
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    items = soup.select(".campaign_content")
    for item in items[:20]:
        title_node = item.select_one(".t_ttl a")
        if title_node:
            print(title_node.get_text(strip=True))

if __name__ == "__main__":
    run()
