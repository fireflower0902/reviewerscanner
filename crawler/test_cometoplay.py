import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        print("Goto cometoplay...")
        await page.goto("https://www.cometoplay.kr/item_list.php?category_id=001", wait_until="networkidle")
        
        # 스크롤 3회 (페이지네이션 방식 확인 위해)
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)
            
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        items = soup.select(".item_wrap") # 가상의 셀렉터 (우선 전체 HTML을 뽑거나 item 리스트를 추정)
        print(f"Items wrap count: {len(items)}")
        
        # 만약 찾기 어렵다면 html 일부를 저장
        with open("cometoplay_dump.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
            
        await browser.close()
        print("Done. Saved to cometoplay_dump.html (check the file for class names).")

if __name__ == "__main__":
    asyncio.run(run())
