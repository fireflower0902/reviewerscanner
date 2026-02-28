import asyncio
from playwright.async_api import async_playwright

async def dump_ohmyblog():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        url = "https://www.ohmyblog.co.kr/"
        print(f"Going to {url}")
        await page.goto(url, wait_until="networkidle")
        
        # Save main page HTML
        html = await page.content()
        with open("debug_ohmyblog_main.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("Done saving main page HTML.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_ohmyblog())
