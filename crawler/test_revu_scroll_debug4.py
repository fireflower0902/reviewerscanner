import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Goto Revu local food...")
        try:
            await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Goto Error: {e}")
            
        print("\nScrolling and counting elements...")
        for i in range(10):
            # 레뷰의 기본 카드 컨테이너 추정 셀렉터 (vue component class 등)
            items = await page.query_selector_all(".campaign-list-item, .campaign-card, article")
            print(f" Scroll {i}: Found {len(items)} items in DOM")
            
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)
            await page.evaluate("window.scrollBy(0, -300)")
            await page.wait_for_timeout(500)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
