import asyncio
import json
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

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

        # 2. JSON 응답 수집기 설정
        sample_items = []
        async def handle_response(response):
            if "api.weble.net/v1/campaigns" in response.url and response.request.method == "GET":
                try:
                    if response.ok:
                        data = await response.json()
                        if "items" in data:
                            for item in data["items"]:
                                sample_items.append(item)
                except Exception as e:
                    pass
        
        page.on("response", handle_response)
        
        # 3. 방문형 맛집 페이지 접속
        print("[Revu] Visiting local food...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        print(f"Captured {len(sample_items)} items from API.")
        
        # 아이템들 전체 구조 파악 (배송형 여부 등)
        for i, item in enumerate(sample_items):
            title = item.get("title") or item.get("item")
            itype = item.get("type")
            cats = item.get("category", [])
            sido = item.get("sido")
            print(f"[{i:02d}] Type: {itype}, Sido: {sido}, Cats: {cats}, Title: {title}")
        
        # 4. 첫 번째 로컬(방문형) 아이템의 상세 페이지 파싱 시도
        local_items = [i for i in sample_items if i.get("type") == "local" or i.get("sido")]
        if local_items:
            first_id = local_items[0].get("id")
            detail_url = f"https://www.revu.net/campaign/detail/{first_id}"
            print(f"\n[Revu] Fetching detail URL: {detail_url}")
            
            detail_page = await context.new_page()
            await detail_page.goto(detail_url, wait_until="networkidle")
            
            html = await detail_page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # CSS Selector 테스트
            # 보통 class에 offer나 box_offer, text_offer 등이 있을 수 있음
            for el in soup.select('.offer, .reward, .camp-info-text, dl.info > dd'):
                 print("Found select element:", el.get_text(separator=' ', strip=True)[:100])
                 
            await detail_page.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
