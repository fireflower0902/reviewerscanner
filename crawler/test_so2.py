import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        try:
            await page.goto("https://www.seoulouba.co.kr/campaign", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            # Extract .campaign_content or other possible parents
            items = soup.select("li.m_mb15")
            if not items:
                items = soup.find_all("li")
            for item in items:
                text = item.get_text(strip=True)
                if '모집' in text or '신청' in text or '명' in text:
                    print(item.prettify()[:1500])
                    break
        except Exception as e: print("SO Error:", e)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
