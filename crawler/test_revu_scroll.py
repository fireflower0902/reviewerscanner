import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
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

        # 2. JSON 응답 수집
        collected_items = []
        async def handle_response(response):
            if "api.weble.net/v1/campaigns" in response.url and response.request.method == "GET":
                try:
                    if response.ok:
                        data = await response.json()
                        if "items" in data and len(data["items"]) > 0:
                            for item in data["items"]:
                                cats = item.get("category", [])
                                if "방문형" in cats:
                                    collected_items.append(item)
                except Exception:
                    pass
        
        page.on("response", handle_response)
        
        # 3. 방문형 맛집 진입 및 지속적 스크롤
        print("[Revu] Fetching local food (음식점)...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        # 무한 스크롤 시뮬레이션
        last_height = await page.evaluate("document.body.scrollHeight")
        scroll_count = 0
        while scroll_count < 20: # 최대 20번 스크롤
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000) # API 응답 대기
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                print(f"Reached bottom after {scroll_count} scrolls.")
                break
            last_height = new_height
            scroll_count += 1
            print(f"Scroll {scroll_count}, Collected valid items so far: {len(collected_items)}")
            
        print(f"Total collected local food items: {len(collected_items)}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
