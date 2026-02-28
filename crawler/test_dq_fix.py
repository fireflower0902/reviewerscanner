import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run():
    print("=== 디너의여왕 데이터 분석 시작 ===")
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
                print(f"Total items found: {len(items)}\n")
                # 앞의 3개 아이템 분석
                for idx, item in enumerate(items[:3]):
                    print(f"--- Item {idx} ---")
                    # 그대로 HTML 덤프 찍어보기
                    print(item.prettify()[:1000])
                    
                    # title 노드 탐색
                    title_node = item.select_one(".qz-title, .title, strong, h3, .title-box")
                    print(f"Title Node: {title_node.get_text(strip=True) if title_node else 'N/A'}")
                    print("모든 텍스트:")
                    print(item.get_text(separator=' | ', strip=True))
                    print("\n")
            else:
                print("No .qz-dq-card items found!")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
