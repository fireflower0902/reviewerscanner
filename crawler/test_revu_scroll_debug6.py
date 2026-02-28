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
        
        async def handle_response(response):
            if response.request.resource_type in ["xhr", "fetch"]:
                try:
                    text = await response.text()
                    if "items" in text or "campaign" in text:
                        print(f"[FOUND DATA in {response.request.method} {response.url}]")
                        print(f"  Length: {len(text)} chars")
                        # 캡처를 위해 처음 발견된 큰 데이터만 덤프
                        if len(text) > 1000:
                            filename = response.url.split("/")[-1].split("?")[0] + "_dump.json"
                            with open(filename, "w", encoding="utf-8") as f:
                                f.write(text)
                            print(f"  -> Dumped to {filename}")
                except Exception as e:
                    pass

        page.on("response", handle_response)
        
        print("Goto Revu local food...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        print("Scrolling...")
        for i in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollBy(0, -300)")
            await page.wait_for_timeout(500)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
