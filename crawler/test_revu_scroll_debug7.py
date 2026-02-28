import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        # headless=False 로 실제 브라우저를 띄워서 스크롤 렌더링을 유도
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        # Capture API
        req_count = 0
        async def handle_response(response):
            nonlocal req_count
            if response.request.resource_type in ["xhr", "fetch"] and "campaign" in response.url:
                req_count += 1
                print(f"[API] {response.url}")

        page.on("response", handle_response)
        
        print("Goto Revu local food...")
        try:
            await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000) # Give it 5 secs to load components
        except Exception as e:
            print(f"Goto Exception: {e}")
        
        print("Emulating human wheel scroll...")
        for i in range(15):
            # 마우스 휠 이벤트 발생 (단순 scrollTo가 아닌 실제 델타)
            await page.mouse.wheel(delta_x=0, delta_y=600)
            await page.wait_for_timeout(1000)
            
        print(f"Total campaign APIs: {req_count}")
        # wait a bit for observation
        await page.wait_for_timeout(3000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
