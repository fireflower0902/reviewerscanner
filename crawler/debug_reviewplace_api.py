import requests
from bs4 import BeautifulSoup

def debug_api():
    # Base URL from the script analysis
    # url: '/theme/rp/_ajax_cmp_list_tpl.php?' + add_params + '&rpage='+rpage
    # Main page was /pr/?ct1=지역 so add_params might be ct1=지역 (encoded)
    
    base_url = "https://www.reviewplace.co.kr/theme/rp/_ajax_cmp_list_tpl.php"
    params = {
        "ct1": "지역",
        "rpage": 1,
        "device": "pc"
    }
    
    print(f"Requesting {base_url} with {params}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD"
    }
    
    try:
        res = requests.get(base_url, params=params, headers=headers)
        print(f"Status: {res.status_code}")
        # print(f"Content Preview: {res.text[:500]}")
        
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select(".item")
        print(f"Items found: {len(items)}")
        
        if items:
            print("First item title:", items[0].select_one(".tit").get_text(strip=True))
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_api()
