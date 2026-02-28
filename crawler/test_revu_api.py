import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    print("=== 레뷰(Revu) API 응답 분석 테스트 ===")
    
    apis = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # 네트워크 응답 가로채기
        async def handle_response(response):
            if "campaign" in response.url.lower() and "api" in response.url.lower():
                try:
                    if response.ok:
                        data = await response.json()
                        apis.append({"url": response.url, "data": data})
                except:
                    pass
        
        page.on("response", handle_response)
        
        try:
            print("[1] 로그인 폼 진입")
            await page.goto("https://www.revu.net/login", wait_until="networkidle")
            
            print("[2] 로그인 수행")
            await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
            await page.fill('input[name="password"]', 'Dkssuddy1!')
            submit_btn = await page.query_selector('button[type="submit"]')
            if submit_btn:
                await submit_btn.click()
            else:
                await page.get_by_text("로그인", exact=True).click()
                
            await page.wait_for_timeout(4000)
            
            print("[3] 방문형 캠페인 (맛집) 페이지로드 대기")
            await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
            await page.wait_for_timeout(5000)
            
            print(f"[4] 감지된 API 응답 개수: {len(apis)}")
            for i, api in enumerate(apis[:2]):
                print(f"\n--- API {i} URL: {api['url']} ---")
                
                # Payload preview
                dump = json.dumps(api['data'], ensure_ascii=False)
                print(f"Preview: {dump[:1000]}")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
