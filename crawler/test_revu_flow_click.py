import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        req_count = 0
        async def handle_response(response):
            nonlocal req_count
            if response.request.resource_type in ["xhr", "fetch"] and "campaign" in response.url:
                req_count += 1

        page.on("response", handle_response)
        
        print("Goto Revu Login...")
        try:
            await page.goto("https://www.revu.net/login", wait_until="networkidle")
            await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
            await page.fill('input[name="password"]', 'Dkssuddy1!')
            await page.get_by_text("로그인", exact=True).click()
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Login Exception: {e}")
            
        print("Goto Revu Main to click '지역'...")
        try:
            await page.goto("https://www.revu.net/", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Goto Exception: {e}")
            
        print("Clicking '지역' menu...")
        try:
            # 보통 헤더 GNB나 Nav에 '지역' 텍스트가 있습니다
            local_btn = page.locator("text='지역'").first
            await local_btn.click()
            await page.wait_for_timeout(5000)
            print(f"Current URL after click: {page.url}")
        except Exception as e:
            print(f"Failed to click 지역: {e}")
            
        print("Emulating human wheel scroll on Local Tab...")
        for i in range(15):
            await page.mouse.wheel(delta_x=0, delta_y=800)
            await page.wait_for_timeout(1500)
            
        # 요소 몇 개 있는지 검사 (카드 개수)
        items = await page.query_selector_all(".campaign-list-item, article, [class*='campaign']")
        print(f"Total campaign APIs: {req_count}")
        print(f"DOM Card items counted (heuristic): {len(items)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
