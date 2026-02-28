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
            if "api.weble.net" in response.url and response.request.method in ["GET", "POST"]:
                print(f"\n[API {response.request.method}] {response.url}")
                if "campaign" in response.url.lower():
                    try:
                        data = await response.json()
                        items = data.get('items', [])
                        print(f"  --> Returns {len(items)} items")
                    except Exception as e:
                        print("  --> Error parsing JSON")

        page.on("response", handle_response)
        
        print("Goto Revu local food...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        print("\nPressing '더보기(More)' button if exists...")
        # 레뷰 모바일뷰/PC뷰에서 무한스크롤 대신 '더보기' 버튼이 있을 수도 있으므로 클릭 시도
        try:
            more_btn = await page.query_selector("button:has-text('더보기'), button:has-text('more'), .btn-more")
            if more_btn:
                print("Found MORE button, clicking...")
                await more_btn.click()
                await page.wait_for_timeout(2000)
            else:
                print("No MORE button found. Trying explicit scroll...")
                for i in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
