import asyncio
import json
from playwright.async_api import async_playwright

async def test_ohmyblog_search():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        api_responses = []
        async def handle_response(response):
            if "api" in response.url or "search" in response.url or "list" in response.url:
                try:
                    if "json" in response.headers.get("content-type", ""):
                        data = await response.json()
                        api_responses.append({"url": response.url, "data": data})
                except Exception as e:
                    pass
        
        page.on("response", handle_response)
        
        url = "https://www.ohmyblog.co.kr/user/search?app_cate_detail=A" # 맛집
        print(f"Fetching {url}")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        if api_responses:
            for r in api_responses:
                print(f"Found API URL: {r['url']}")
            with open("debug_ohmyblog_search_api.json", "w", encoding="utf-8") as f:
                json.dump(api_responses, f, ensure_ascii=False, indent=2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_ohmyblog_search())
