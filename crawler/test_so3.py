import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            await page.goto("https://www.seoulouba.co.kr/campaign", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            print("Title:", await page.title())
            items = soup.select(".campaign_content")
            if items:
                print("First item:\n", items[0].prettify()[:1000])
                print("\nText snippet:\n", items[0].get_text(separator=' | ', strip=True))
        except Exception as e: print("SO Error:", e)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
