import asyncio
from playwright.async_api import async_playwright

async def dump_reviewplace():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 리뷰플레이스 체험단 전체 리스트 페이지
        url = "https://www.reviewplace.co.kr/exp/exp_list.php"
        print(f"[System] 리뷰플레이스 접속 중: {url}")
        
        await page.goto(url, wait_until="networkidle")
        
        # 구조 분석용 HTML 저장
        content = await page.content()
        with open("crawler/debug_reviewplace.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("[System] HTML 덤프 완료: crawler/debug_reviewplace.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_reviewplace())
