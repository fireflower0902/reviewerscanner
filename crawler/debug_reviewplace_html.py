from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # ReviewPlace uses AJAX for list, so we go to a category page
        page.goto("https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD")
        
        page.wait_for_selector(".item_list .item", timeout=10000)
        items = page.locator(".item_list .item").all()[:3]
        
        print(f"Items found: {len(items)}", flush=True)
        
        for i, item in enumerate(items):
            print(f"\n--- Item {i} ---", flush=True)
            try:
                html = item.inner_html()
                print(html, flush=True)
            except Exception as e:
                print(f"Error extracting HTML: {e}", flush=True)
            
        browser.close()

if __name__ == "__main__":
    run()
