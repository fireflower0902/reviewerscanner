from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://xn--939au0g4vj8sq.net/cp/?ca=20")
        
        # Try waiting for body first
        page.wait_for_selector("body", timeout=10000)
        
        # Try a more generic selector or just print body if list not found
        try:
            page.wait_for_selector("div.item_list", timeout=5000)
            items = page.locator("div.item_list a.item").all()
        except:
            print("Item list not found. Dumping body start...", flush=True)
            print(page.content()[:1000], flush=True)
            items = []

        print(f"Items found: {len(items)}", flush=True)
        
        for i, item in enumerate(items[:3]):
            print(f"\n--- Item {i} ---", flush=True)
            try:
                html = item.inner_html()
                print(html, flush=True)
            except Exception as e:
                print(f"Error extracting HTML: {e}", flush=True)
            
        browser.close()

if __name__ == "__main__":
    run()
