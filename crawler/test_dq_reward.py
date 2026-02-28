import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run():
    print("=== 디너의여왕 제공량 분석 시작 ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            await page.goto("https://dinnerqueen.net/taste", wait_until="networkidle")
            await page.wait_for_timeout(3000)
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            items = soup.select(".qz-dq-card")
            if items:
                for idx, item in enumerate(items[:5]):
                    print(f"--- Item {idx} ---")
                    
                    link_node = item.select_one("a.qz-dq-card__link")
                    title = link_node.get('title', '').replace(' 신청하기', '') if link_node else ""
                    print(f"Title: {title}")
                    
                    # 텍스트 구조 파악
                    info_area = item.select_one(".qz-dq-card__text")
                    if info_area:
                        print("Text area HTML:")
                        print(info_area.prettify()[:500])
                    
                    # p 태그 텍스트 모두 출력
                    print("\nAll P tags:")
                    for p in item.select("p"):
                        print(f" - {p.get_text(strip=True)}")
                    
            else:
                print("No .qz-dq-card items found!")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
