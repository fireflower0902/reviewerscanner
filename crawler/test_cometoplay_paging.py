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
        
        print("Goto ComeToPlay...")
        await page.goto("https://www.cometoplay.kr/item_list.php?category_id=001", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # 하단 페이징 영역(pg) 확인
        pagination = soup.select(".pg_wrap a, .paging a, .pagination a, [class*='page'] a")
        print("\n[Pagination Links]")
        for a in pagination:
            print(f"Text: {a.text.strip()}, Href: {a.get('href')}")
            
        items = soup.select(".item_box_list li")
        print(f"\nItems on first page: {len(items)}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
