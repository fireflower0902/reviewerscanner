import requests
from bs4 import BeautifulSoup

def run():
    url = "https://www.seoulouba.co.kr/campaign/?cat=377" # 방문형
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 카테고리 네비게이션
    print("[방문형 서브 카테고리 네비게이션]")
    navs = soup.select(".cate_list a, .sub_cate a, .swiper-slide a, .category_list a")
    if not navs:
        navs = soup.find_all('a')
        
    for n in navs:
        if n.text and '맛집' in n.text or '뷰티' in n.text:
            print(f"- {n.text.strip()}: {n.get('href')}")
            
if __name__ == "__main__":
    run()
