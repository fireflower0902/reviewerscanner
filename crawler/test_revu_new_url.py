import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        print("Goto Revu Login...")
        await page.goto("https://www.revu.net/login", wait_until="networkidle")
        await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
        await page.fill('input[name="password"]', 'Dkssuddy1!')
        await page.get_by_text("로그인", exact=True).click()
        await page.wait_for_timeout(3000)
            
        print("Goto Revu '지역 > 맛집' using new URL format...")
        try:
            await page.goto("https://www.revu.net/category/%EC%A7%80%EC%97%AD/%EB%A7%9B%EC%A7%91", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Goto Exception: {e}")
            
        req_count = 0
        async def handle_response(response):
            nonlocal req_count
            if response.request.resource_type in ["xhr", "fetch"] and "campaign" in response.url:
                req_count += 1
        page.on("response", handle_response)
        
        print("Scrolling...")
        for i in range(5):
            await page.mouse.wheel(delta_x=0, delta_y=800)
            await page.wait_for_timeout(1000)
            
        items = await page.query_selector_all(".campaign-list-item, article, [class*='campaign']")
        print(f"Items found: {len(items)}")
        print(f"API requests: {req_count}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
