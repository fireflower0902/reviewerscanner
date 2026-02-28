import requests
from bs4 import BeautifulSoup

def run():
    url = "https://www.seoulouba.co.kr/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 방문형 메뉴 찾기
    menus = soup.find_all('a')
    for m in menus:
        if m.text and '방문' in m.text:
            print(f"방문형 메뉴: {m.text.strip()} -> {m.get('href')}")
            
    # 방문형 페이지 접근해서 캠페인 카드에 카테고리 정보 있는지 확인
    visit_url = "https://www.seoulouba.co.kr/campaign/?cp_type=1" # 추측
    print(f"\nTrying to fetch {visit_url}...")
    res2 = requests.get(visit_url, headers=headers)
    res2.encoding = 'utf-8'
    soup2 = BeautifulSoup(res2.text, 'html.parser')
    items = soup2.select(".campaign_content")
    if items:
        print("First item HTML snippet:")
        print(items[0].prettify()[:1000])
        
if __name__ == "__main__":
    run()
