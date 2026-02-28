import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        async def handle_request(request):
            if "api.weble.net/v1/campaigns" in request.url:
                print(f"API Request URL: {request.url}")

        page.on("request", handle_request)
        
        await page.goto("https://www.revu.net/campaign/local/food/all")
        await page.wait_for_timeout(3000)
        
        # 스크롤 동작 후 새로운 URL이 요청되는지 확인
        print("Scrolling...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)
        
        print("Scrolling again...")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)
        
        # '더보기' 버튼 류가 있는지 확인
        buttons = await page.query_selector_all("button")
        for b in buttons:
            try:
                text = await b.inner_text()
                if text and ("더보기" in text or "more" in text.lower()):
                    print(f"Found 'more' button: {text}")
            except: pass
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
