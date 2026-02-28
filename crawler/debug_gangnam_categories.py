from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Test candidate URLs for regions
        # ca=20 (Current)
        # ca=1 ? (Seoul)
        # ca=2 ? (Gyeonggi)
        
        candidates = [20, 1, 2, 3]
        
        for cat_id in candidates:
            url = f"https://xn--939au0g4vj8sq.net/cp/?ca={cat_id}"
            print(f"\nAccessing: {url}...", flush=True)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=10000)
                page.wait_for_selector("li.list_item", timeout=5000)
                
                # Check active tab or breadcrumb if possible, or just first few titles
                items = page.locator("li.list_item dt.tit a").all()[:5]
                print(f"  Found {len(items)} items. First few titles:", flush=True)
                for item in items:
                    print(f"    - {item.inner_text()}", flush=True)
                    
            except Exception as e:
                print(f"  Error: {e}", flush=True)
        
        browser.close()

if __name__ == "__main__":
    run()
