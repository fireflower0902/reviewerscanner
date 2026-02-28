import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    print("=== 레뷰(Revu) API 심층 분석 3 ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        async def handle_request(request):
            if "weble.net" in request.url and "campaigns" in request.url.lower():
                print(f"[API Request] {request.url}")
                print(f"Headers: {request.headers.get('authorization', 'No Auth Header')}")
                
        async def handle_response(response):
            if "weble.net/v1/campaigns" in response.url.lower() and "?" in response.url:
                try:
                    if response.ok:
                        data = await response.json()
                        if "items" in data and len(data["items"]) > 0:
                            print(f"\n[API Response Data for {response.url}]")
                            item = data["items"][0]
                            print("Item keys:", list(item.keys()))
                            print("Title:", item.get("title"))
                            print("Category:", item.get("category"))
                            print("Applicants:", item.get("campaignStats", {}).get("requestCount"))
                            print("Quota:", item.get("reviewerLimit"))
                            
                            # dump first item fully to a file
                            with open("revu_item_sample.json", "w") as f:
                                json.dump(item, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    pass
        
        page.on("request", handle_request)
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
            await page.wait_for_timeout(4000)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
