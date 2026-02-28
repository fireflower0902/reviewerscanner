import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto('https://www.revu.net/category/%EC%A7%80%EC%97%AD', wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        
        items = await page.query_selector_all('a')
        for i in items:
            t = await i.text_content()
            h = await i.get_attribute('href')
            if t and h and ('category' in h or 'local' in h):
                print(f"{t.strip()}: {h}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
