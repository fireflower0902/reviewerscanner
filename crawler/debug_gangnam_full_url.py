from playwright.sync_api import sync_playwright
import urllib.parse

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Construct proper URL
        base = "https://xn--939au0g4vj8sq.net/cp/?ca=20"
        params = {
            "loca_prt": "경기-인천",
            "local_1": "전체",
            "local_2": "경기|인천"
        }
        query = urllib.parse.urlencode(params)
        url = f"{base}&{query}"
        
        print(f"Accessing: {url}", flush=True)
        page.goto(url, wait_until="networkidle") # Wait for network idle to ensure scripts run
        
        items = page.locator("li.list_item dt.tit a").all_inner_texts()
        print(f"Found {len(items)} items. Top 5:", flush=True)
        for item in items[:5]:
            print(f" - {item}", flush=True)
            
        browser.close()

if __name__ == "__main__":
    run()
