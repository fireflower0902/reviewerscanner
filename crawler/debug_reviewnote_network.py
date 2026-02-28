import asyncio
from playwright.async_api import async_playwright

async def debug_network():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Log requests
        page.on("request", lambda request: print(f">> {request.method} {request.url}") if "api" in request.url or "json" in request.url else None)
        
        url = "https://www.reviewnote.co.kr/campaigns?s=popular"
        print(f"Goto {url}...")
        await page.goto(url, wait_until="networkidle")
        
        print("Scrolling...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_network())
