import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

async def test_4blog_paging():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # We need to intersect network requests to see if an API is used for scrolling
        api_requests = []
        page.on("request", lambda req: api_requests.append(req.url) if 'api' in req.url or 'ajax' in req.url or 'list' in req.url else None)
        
        print("Scraping 4blog.net 방문(local) campaigns and scrolling...")
        url = "https://4blog.net/list/all/local"
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # Scroll 5 times
        for i in range(5):
            print(f"Scrolling {i+1}...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        items = soup.select("a[href*='/campaign/']")
        print(f"Found {len(items)} possible items after scrolling.")
        
        print("\nCaptured possible API/list requests:")
        for req in set(api_requests):
            if '4blog.net' in req and ('api' in req or 'list' in req):
                print(req)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_4blog_paging())
