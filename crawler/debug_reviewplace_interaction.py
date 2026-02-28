import asyncio
from playwright.async_api import async_playwright

async def debug_reviewplace():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        # "강남맛집" 처럼 "전체" 혹은 "지역" 탭의 모든 리스트를 볼 수 있는 URL인지 확인
        url = "https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD" 
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="networkidle")
        
        # Initial item count
        initial_count = await page.locator(".campaign_list .item").count()
        print(f"Initial: {initial_count}")
        
        # Try Scroll
        print("Scorlling...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)
        
        after_scroll = await page.locator(".campaign_list .item").count()
        print(f"After Scroll: {after_scroll}")
        
        # Check for 'Load More' button?
        load_more = await page.locator("text=더보기").count()
        print(f"Load More buttons found: {load_more}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_reviewplace())
