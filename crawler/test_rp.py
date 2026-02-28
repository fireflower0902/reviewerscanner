from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD")
        html = page.evaluate("""async () => {
            const response = await fetch('https://www.reviewplace.co.kr/theme/rp/_ajax_cmp_list_tpl.php?ct1=%EC%A7%80%EC%97%AD&ct2=%EB%A7%9B%EC%A7%91&rpage=1&device=pc');
            return await response.text();
        }""")
        print(html[:2000])
        browser.close()

if __name__ == "__main__":
    run()
