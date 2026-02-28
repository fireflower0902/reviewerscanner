import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        async def handle_request(request):
            if request.resource_type in ["xhr", "fetch"]:
                print(f"[Req] {request.method} {request.url}")

        page.on("request", handle_request)
        
        # 1. 로그인
        print("[Revu] Logging in...")
        await page.goto("https://www.revu.net/login", wait_until="networkidle")
        await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
        await page.fill('input[name="password"]', 'Dkssuddy1!')
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
             await submit_btn.click()
        else:
             await page.get_by_text("로그인", exact=True).click()
        await page.wait_for_timeout(3000)
        
        print("Visiting local food...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        # 2. 스크롤하면서 감시
        print("Scrolling...")
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)
            
        # 3. 버튼 클릭 시도 (강제)
        btns = await page.query_selector_all("button")
        for b in btns:
            text = await b.inner_text()
            if text and "더보기" in text:
                print("Force clicking 더보기...")
                await page.evaluate("arguments[0].click();", b)
                await page.wait_for_timeout(3000)
                break

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
