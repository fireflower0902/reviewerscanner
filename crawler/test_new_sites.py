import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        print("=== 디너의여왕 (Dinner Queen) ===")
        try:
            page = await context.new_page()
            # 메인이나 방문형 메뉴 접근
            await page.goto("https://dinnerqueen.net/taste", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            # Look for campaign items
            items = soup.select(".dq-grid div, .campaign-list li, .card, li")
            found = False
            for item in items:
                text = item.get_text(strip=True)
                if '모집' in text or '신청' in text:
                    print("Found potential DQ item!")
                    print(item.prettify()[:1000])
                    found = True
                    break
            if not found:
                print("DQ items not parsed well. Printing snippet:")
                print(soup.body.text[:500])
        except Exception as e:
            print("Dinner Queen Error:", e)

        print("\n=== 서울오빠 (Seoul Oppa) ===")
        try:
            page = await context.new_page()
            await page.goto("https://www.seoulouba.co.kr/", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select(".item, .card, .list_item, li, .CampaignList_item__...")
            found = False
            for item in items:
                text = item.get_text(strip=True)
                if '모집' in text or '신청' in text:
                    print("Found potential SeoulOppa item!")
                    print(item.prettify()[:1000])
                    found = True
                    break
            if not found:
                print("SeoulOppa items not parsed well. Printing snippet:")
                print(soup.body.text[:500])
        except Exception as e:
            print("Seoul Oppa Error:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
