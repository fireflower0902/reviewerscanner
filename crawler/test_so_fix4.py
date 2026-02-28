import requests
from bs4 import BeautifulSoup
import re

def run():
    url = "https://www.seoulouba.co.kr/campaign/?cat=377" # 방문형
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 카테고리 네비게이션
    print("[방문형 서브 카테고리 네비게이션]")
    navs = soup.select(".sub_cate li a")
    if not navs:
        navs = soup.find_all('a', href=re.compile(r'\?cat=\d+$'))
        
    for n in navs:
        if n.text.strip():
            print(f"- {n.text.strip()}: {n.get('href')}")
            
if __name__ == "__main__":
    run()
