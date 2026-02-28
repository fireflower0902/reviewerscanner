from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Check 1: ca=20 page 1 vs page 2
        url1 = "https://xn--939au0g4vj8sq.net/cp/?ca=20&page=1"
        url2 = "https://xn--939au0g4vj8sq.net/cp/?ca=20&page=2"
        
        print(f"Checking {url1}...", flush=True)
        page.goto(url1, wait_until="domcontentloaded")
        page.wait_for_selector("li.list_item")
        
        items1 = page.locator("li.list_item dt.tit a").all_inner_texts()
        print(f"Page 1 First Item: {items1[0] if items1 else 'None'}", flush=True)

        print(f"Checking {url2}...", flush=True)
        page.goto(url2, wait_until="domcontentloaded")
        page.wait_for_selector("li.list_item")
        
        items2 = page.locator("li.list_item dt.tit a").all_inner_texts()
        print(f"Page 2 First Item: {items2[0] if items2 else 'None'}", flush=True)
        
        if items1[0] != items2[0]:
            print("SUCCESS: Pagination works (Content is different).", flush=True)
        else:
            print("FAILURE: Content is identical (Pagination parameter ignored?).", flush=True)
            
        # Check 2: Gyeonggi Region
        url_gyeonggi = "https://xn--939au0g4vj8sq.net/cp/?ca=20&loca_prt=경기-인천&page=1"
        print(f"\nChecking Gyeonggi: {url_gyeonggi}...", flush=True)
        page.goto(url_gyeonggi, wait_until="domcontentloaded")
        items_g = page.locator("li.list_item dt.tit a").all_inner_texts()
        print(f"Gyeonggi Items: {len(items_g)}", flush=True)
        for item in items_g[:5]:
            print(f" - {item}", flush=True)
            
        browser.close()

if __name__ == "__main__":
    run()
