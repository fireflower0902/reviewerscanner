import asyncio
from playwright.async_api import async_playwright

async def run():
    print("=== 레뷰(Revu) 로그인 및 접근 테스트 2 ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("[1] 로그인 페이지 접근")
            await page.goto("https://www.revu.net/login", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            print("[2] 로그인 폼 분석 및 값 입력")
            await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
            await page.fill('input[name="password"]', 'Dkssuddy1!')
            
            submit_btn = await page.query_selector('button[type="submit"]')
            if submit_btn:
                await submit_btn.click()
            else:
                await page.get_by_text("로그인", exact=True).click()
                
            print("[3] 로그인 처리 대기 중...")
            await page.wait_for_timeout(4000)
            
            print(f"Post-Login URL: {page.url}")
            
            print("[4] 로그인 후 방문형 캠페인 페이지(맛집) 접근")
            await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            title = await page.title()
            print(f"Current Page Title: {title}")
            
            # 캠페인 카드 요소 찾기
            cards = await page.query_selector_all('.campaign-list .campaign-item, .card, li.search-list-item, div.campaign-list figure, .campaign-card-list li')
            print(f"Items found (approx): {len(cards)}")
            if cards:
                html = await cards[0].inner_html()
                print("First card HTML:")
                print(html[:1000])
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
