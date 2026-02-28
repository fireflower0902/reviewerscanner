import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

async def scrape_ohmyblog_visit():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        url = "https://www.ohmyblog.co.kr/user/visit"
        print(f"Going to {url}")
        
        # We can intercept API requests or just parse the DOM
        # Let's intercept to see if there's a JSON API
        api_responses = []
        async def handle_response(response):
            if "api" in response.url or "list" in response.url or "search" in response.url:
                if response.request.method == "GET" or response.request.method == "POST":
                    try:
                        if "json" in response.headers.get("content-type", ""):
                            data = await response.json()
                            api_responses.append({"url": response.url, "data": data})
                    except Exception as e:
                        pass
        
        page.on("response", handle_response)
        
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # Save page HTML
        html = await page.content()
        with open("debug_ohmyblog_visit.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("Done saving visit page HTML.")
        
        if api_responses:
            print(f"Found {len(api_responses)} potential API responses")
            # save the first one
            with open("debug_ohmyblog_api.json", "w", encoding="utf-8") as f:
                json.dump(api_responses, f, ensure_ascii=False, indent=2)
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_ohmyblog_visit())
