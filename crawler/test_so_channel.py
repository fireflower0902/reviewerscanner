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
        for idx, item in enumerate(items[:5]):
            print(f"-- Item {idx} --")
            title_node = item.select_one(".t_ttl a")
            title = title_node.get_text(strip=True) if title_node else "No Title"
            print(f"Title: {title}")
            
            # 모든 텍스트 포함된 구조 확인
            for icon in item.select(".com_icon .icon_tag span"):
                print(f"Icon Tag: {icon.get_text(strip=True)}")
            
            for badge in item.select(".sns_icon img"):
                print(f"SNS Icon: {badge.get('src')} / {badge.get('alt')}")
                
            print(item.get_text(separator=' | ', strip=True))

if __name__ == "__main__":
    run()
