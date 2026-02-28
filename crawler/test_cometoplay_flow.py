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
        
        print("Goto ComeToPlay Main...")
        await page.goto("https://www.cometoplay.kr/", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        
        print("Clicking '지역' menu at the top...")
        # '지역' 메뉴 클릭
        try:
            # gnb_menu 안에 있는 지역 링크 클릭
            local_menu = page.locator(".gnb_menu a:has-text('지역')").first
            await local_menu.click()
            await page.wait_for_timeout(3000)
        except Exception as e:
            print(f"Failed to click 지역: {e}")
            
        # 서브 카테고리 순회할 수도 있고, Region(001) 전체보기에서 page=1~50까지 전부 돌 수도 있음.
        total_items = 0
        
        for page_num in range(1, 41): # 40페이지 = 800개 정도
            paginated_url = f"https://www.cometoplay.kr/item_list.php?category_id=001012&sst=it_datetime&sod=desc&page={page_num}"
            await page.goto(paginated_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select(".item_box_list li")
            
            if not items:
                print(f"Page {page_num} is empty. Stop crawling.")
                break
                
            print(f"Page {page_num} (001012): Found {len(items)} items")
            total_items += len(items)

        print(f"Total collected from '지역' tab: {total_items}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
