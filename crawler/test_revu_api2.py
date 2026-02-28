import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    print("=== 레뷰(Revu) API 심층 분석 ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        async def handle_response(response):
            # campaigns 관련 API 수집
            if "weble.net" in response.url and "campaigns" in response.url.lower():
                try:
                    if response.ok:
                        data = await response.json()
                        print(f"\n[Captured API] {response.url}")
                        
                        # 아이템 구조체 확인
                        if "items" in data and len(data["items"]) > 0:
                            item = data["items"][0]
                            print(" - [Title]:", item.get("title") or item.get("item"))
                            print(" - [Category]:", item.get("category"))
                            print(" - [Sido]:", item.get("sido"))
                            print(" - [Area]:", item.get("area"))
                            print(" - [Media]:", item.get("media"))
                            print(" - [Offer]:", item.get("offer"))
                            print(" - [Applicants]:", item.get("requestCount"))
                            print(" - [Quota]:", item.get("reviewerLimit"))
                            print(" - [Status]:", item.get("status"))
                            print(" - [Thumb]:", item.get("thumbnail"))
                            print(" - [KeySet]:", list(item.keys()))
                except Exception as e:
                    pass
        
        page.on("response", handle_response)
        
        try:
            print("[1] 로그인 폼 진입")
            await page.goto("https://www.revu.net/login", wait_until="networkidle")
            
            await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
            await page.fill('input[name="password"]', 'Dkssuddy1!')
            submit_btn = await page.query_selector('button[type="submit"]')
            if submit_btn:
                await submit_btn.click()
            else:
                await page.get_by_text("로그인", exact=True).click()
                
            await page.wait_for_timeout(3000)
            
            print("[2] 맛집 페이지 로드")
            await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            # 페이지네이션 2 페이지도 눌러봄
            print("[3] 2페이지 이동 시도")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
