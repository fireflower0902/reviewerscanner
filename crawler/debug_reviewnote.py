import asyncio
from playwright.async_api import async_playwright

async def debug_reviewnote():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.reviewnote.co.kr/campaigns?s=popular"
        print(f"Accessing: {url}")
        await page.goto(url, wait_until="networkidle")
        
        # Scroll down a bit to ensure items are loaded
        await page.evaluate("window.scrollBy(0, 1000)")
        await asyncio.sleep(2)
        
        # Save HTML
        content = await page.content()
        with open("debug_reviewnote.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Saved debug_reviewnote.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_reviewnote())
