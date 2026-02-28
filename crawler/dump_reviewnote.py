import asyncio
from playwright.async_api import async_playwright

async def dump_reviewnote():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 리뷰노트 메인 페이지 (또는 지역 필터링된 리스트 URL)
        url = "https://www.reviewnote.co.kr/"
        print(f"[System] 리뷰노트 접속 중: {url}")
        
        await page.goto(url, wait_until="networkidle")
        
        # 스크롤을 통해 데이터 로딩 유도
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(1)

        content = await page.content()
        with open("crawler/debug_reviewnote.html", "w", encoding="utf-8") as f:
            f.write(content)
            
        print("[System] HTML 덤프 완료: crawler/debug_reviewnote.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_reviewnote())
