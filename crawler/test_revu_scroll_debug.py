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
            if "api.weble.net/v1/campaigns" in response.url and response.request.method == "GET":
                req_count += 1
                print(f"[API Call {req_count}] URL: {response.url}")
                try:
                    data = await response.json()
                    print(f"  -> Returned items: {len(data.get('items', []))}")
                except:
                    print("  -> Failed to parse JSON")

        page.on("response", handle_response)
        
        print("Goto Revu local food...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        print("Scrolling...")
        for i in range(10):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
        print(f"Total API calls: {req_count}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
