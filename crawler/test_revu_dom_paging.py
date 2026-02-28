import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        # 1. 로그인
        print("[Revu] Logging in...")
        await page.goto("https://www.revu.net/login", wait_until="networkidle")
        await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
        await page.fill('input[name="password"]', 'Dkssuddy1!')
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
             await submit_btn.click()
        else:
             await page.get_by_text("로그인", exact=True).click()
        await page.wait_for_timeout(3000)
        
        print("Visiting local food...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 2. 더보기 계속 누르기
        for i in range(5): # 5번 눌러보기
            more_btn = await page.query_selector('button.btn-more') # 클래스는 추측
            if not more_btn:
                # 텍스트로 찾기
                more_btn = await page.get_by_text("더보기", exact=True).element_handle()
                
            if more_btn:
                print(f"Clicking more button... {i+1}")
                await more_btn.click()
                await page.wait_for_timeout(2000)
            else:
                print("No more button found.")
                break

        # 3. DOM 분석
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # 레뷰 캠페인 카드는 보통 .campaign-list 안의 .campaign-card 또는 li 요소임
        items = soup.select('ul.campaign-list > li, div.campaign-list .campaign-card, .list-campaign li, .campaign-card')
        
        print(f"Total HTML items found: {len(items)}")
        
        if items:
            for i, item in enumerate(items[:3]):
                title = item.select_one('.title, .tit')
                print(f"Item {i} title: {title.get_text(strip=True) if title else 'No title'}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
