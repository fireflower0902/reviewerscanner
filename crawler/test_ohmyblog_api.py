import asyncio
import json
from playwright.async_api import async_playwright

async def test_ohmyblog_api():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        
        # app_type=A,B,C,D,F? Let's check what is returned when app_type=A
        # Actually in the intercept we saw: app_type=A%2CC -> A,C
        url = "https://www.ohmyblog.co.kr/api/web/campaign/active?page=1&limit=20&app_type=A"
        print(f"Fetching {url}")
        res = await context.request.get(url)
        data = await res.json()
        
        campaigns = data.get('data', {}).get('campaigns', [])
        print(f"Found {len(campaigns)} campaigns.")
        if campaigns:
            print(json.dumps(campaigns[0], ensure_ascii=False, indent=2))
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_ohmyblog_api())
