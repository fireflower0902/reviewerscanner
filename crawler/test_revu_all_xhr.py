import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        async def handle_request(request):
            if request.resource_type in ["xhr", "fetch"] and "google" not in request.url and "analytics" not in request.url:
                print(f"[Req] {request.method} {request.url}")

        page.on("request", handle_request)
        
        print("[Revu] Logging in...")
        await page.goto("https://www.revu.net/login", wait_until="networkidle")
        await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
        await page.fill('input[name="password"]', 'Dkssuddy1!')
        btn = await page.query_selector("button[type='submit']")
        if btn: await btn.click()
        else: await page.get_by_text("로그인", exact=True).click()
        await page.wait_for_timeout(3000)

        print("[Revu] Visiting local food...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        print("Scrolling...")
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
