import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        print("\n=== 디너의여왕 (Dinner Queen) ===")
        page1 = await context.new_page()
        try:
            await page1.goto("https://dinnerqueen.net/taste", wait_until="networkidle")
            await page1.wait_for_timeout(2000)
            html = await page1.content()
            soup = BeautifulSoup(html, 'html.parser')
            # The class mentioned earlier: 'qz-dq-card'
            items = soup.select(".qz-dq-card")
            if items:
                print(f"Found {len(items)} items using .qz-dq-card")
                print("First item HTML:\n", items[0].prettify())
        except Exception as e: print("DQ Error:", e)

        print("\n=== 서울오빠 (Seoul Oppa) ===")
        page2 = await context.new_page()
        try:
            await page2.goto("https://www.seoulouba.co.kr/campaign", wait_until="networkidle")
            await page2.wait_for_timeout(2000)
            html = await page2.content()
            soup = BeautifulSoup(html, 'html.parser')
            # The class mentioned earlier: 'load_campaign' or 'campaign_content'
            items = soup.select(".load_campaign")
            if items:
                print(f"Found {len(items)} items using .load_campaign")
                print("First item HTML:\n", items[0].prettify())
        except Exception as e: print("SO Error:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
