import requests
from bs4 import BeautifulSoup

def run():
    url = "https://www.seoulouba.co.kr/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 방문형 메뉴 체계 확인
    print("메뉴 링크 분석:")
    for a in soup.find_all('a', href=True):
        if '방문' in a.text or '캠페인' in a.text:
            print(f"- {a.text.strip()}: {a['href']}")
            
    # 특정 캠페인 페이지 하나 가져와보기
    # campaign/?c= 카테고리?
    print("\n[태그 / 카테고리 분석]")
    c_url = "https://www.seoulouba.co.kr/campaign"
    c_res = requests.get(c_url, headers=headers)
    c_res.encoding = 'utf-8'
    c_soup = BeautifulSoup(c_res.text, 'html.parser')
    
    # 카테고리 네비게이션
    navs = c_soup.select(".swiper-slide a, .sub_cate a, .category_list a")
    for n in navs:
        print(f"Cat Nav: {n.text.strip()} -> {n.get('href')}")
        
    items = c_soup.select(".campaign_content")
    if items:
        # 두세개 아이템 HTML 덤프
        for idx, item in enumerate(items[:3]):
            print(f"\nItem {idx} text:")
            print(item.get_text(separator=' | ', strip=True))

if __name__ == "__main__":
    run()
