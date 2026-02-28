import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        print("\n=== 서울오빠 (Seoul Oppa) ===")
        page2 = await context.new_page()
        
        apis = []
        async def on_response(response):
            if "api" in response.url or "campaign" in response.url or "list" in response.url:
                if response.request.resource_type in ["fetch", "xhr"]:
                    try:
                        text = await response.text()
                        if text and len(text) > 200:
                            print(f"[SO] Found API: {response.url[:100]}")
                            apis.append(response.url)
                    except: pass
        page2.on("response", on_response)
        
        try:
            await page2.goto("https://www.seoulouba.co.kr/campaign", wait_until="networkidle")
            await page2.wait_for_timeout(3000)
            
            # Print page title
            title = await page2.title()
            print("Title:", title)
            
            # Check for any items in the DOM
            html = await page2.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select("li, .item, .campaign-item")
            print(f"Found {len(items)} generic li/items.")
            
            # Find class names looking like campaigns
            classes = [c for item in soup.find_all(class_=True) for c in item['class']]
            from collections import Counter
            common = Counter(classes).most_common(10)
            print("Most common classes:", common)
            
        except Exception as e: print("SO Error:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
