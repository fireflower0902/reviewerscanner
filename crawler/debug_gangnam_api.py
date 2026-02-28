from playwright.sync_api import sync_playwright
import urllib.parse

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # We need a context to manage cookies/session if needed
        context = browser.new_context()
        page = context.new_page()
        
        # 1. Visit main page first to get cookies (just in case)
        page.goto("https://xn--939au0g4vj8sq.net/cp/?ca=20", wait_until="domcontentloaded")
        
        # 2. Test API Call for Gyeonggi Region, Page 2
        # Endpoint: https://xn--939au0g4vj8sq.net/theme/go/_list_cmp_tpl.php
        api_url = "https://xn--939au0g4vj8sq.net/theme/go/_list_cmp_tpl.php"
        
        # Params observed: ca=20, loca_prt=..., rpage=2
        # Let's try to fetch Page 2 of Gyeonggi
        params = {
            "ca": "20",
            "loca_prt": "경기-인천",
            "local_1": "전체",
            "local_2": "경기|인천",
            "rpage": "2",  # Requesting Page 2
            "row_num": "20" # Items per page?
        }
        
        # Playwright request
        print(f"Calling API with rpage=2...", flush=True)
        response = page.request.post(api_url, form=params)
        
        if response.ok:
            text = response.text()
            print(f"Response Length: {len(text)}", flush=True)
            if len(text) < 100:
                print("Response too short, might be empty or error.", flush=True)
                print(text)
            else:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(text, 'html.parser')
                items = soup.select("li.list_item")
                print(f"Found {len(items)} items in API response.", flush=True)
                for item in items[:3]:
                    title_node = item.select_one("dt.tit a")
                    print(f" - {title_node.get_text(strip=True) if title_node else 'No Title'}", flush=True)
        else:
            print(f"API Request Failed: {response.status}", flush=True)
            
        browser.close()

if __name__ == "__main__":
    run()
