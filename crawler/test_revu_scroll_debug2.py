import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        req_count = 0
        async def handle_response(response):
            nonlocal req_count
            # Observe ALL API calls to revu or weble
            if ("api" in response.url or "graphql" in response.url or "campaign" in response.url) and response.request.resource_type in ["xhr", "fetch"]:
                req_count += 1
                print(f"[API] {response.request.method} {response.url}")

        page.on("response", handle_response)
        
        print("Goto Revu local food...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        print("Scrolling 5 times...")
        for i in range(5):
            print(f" Scroll {i+1}")
            # 스크롤 최하단 이동 후 약간 위로 올리는 보정 (가끔 바닥에 닿아야 트리거됨)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(500)
            await page.evaluate("window.scrollBy(0, -200)")
            await page.wait_for_timeout(500)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
        print(f"Total mapped XHR/Fetch calls: {req_count}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
