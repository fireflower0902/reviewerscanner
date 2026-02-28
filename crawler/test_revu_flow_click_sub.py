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
            
        print("Goto Revu Main to click '지역'...")
        await page.goto("https://www.revu.net/", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # '지역' 메뉴 클릭
        try:
            local_btn = page.locator("text='지역'").first
            await local_btn.click()
            await page.wait_for_timeout(3000)
            print(f"[Success] Clicked 지역. Current URL: {page.url}")
        except Exception as e:
            print(f"[Error] Failed to click 지역: {e}")
            
        # 서브 카테고리 테스트 (뷰티)
        try:
            beauty_btn = page.locator("text='뷰티'").first
            await beauty_btn.click()
            await page.wait_for_timeout(3000)
            print(f"[Success] Clicked 뷰티. Current URL: {page.url}")
        except Exception as e:
            print(f"[Error] Failed to click 뷰티: {e}")
            
        print("Scrolling...")
        for i in range(5):
            await page.mouse.wheel(delta_x=0, delta_y=800)
            await page.wait_for_timeout(1000)
            
        items = await page.query_selector_all(".campaign-list-item, article, [class*='campaign']")
        print(f"Items found for 뷰티: {len(items)}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
