import asyncio
from playwright.async_api import async_playwright
import aggregator
from bs4 import BeautifulSoup

async def run():
    print("=== 디너의여왕 상세페이지 제공량 파싱 테스트 ===")
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
            
            items = soup.select(".qz-dq-card")[:3]
            for idx, item in enumerate(items):
                link_node = item.select_one("a.qz-dq-card__link")
                link = link_node.get('href', '') if link_node else ""
                if link and not link.startswith('http'): link = f"https://dinnerqueen.net{link}"
                
                print(f"--- Item {idx} ---")
                print(f"URL: {link}")
                
                if link:
                    # 상세페이지 이동
                    detail_page = await context.new_page()
                    await detail_page.goto(link, wait_until="domcontentloaded")
                    await detail_page.wait_for_timeout(1000)
                    detail_html = await detail_page.content()
                    d_soup = BeautifulSoup(detail_html, 'html.parser')
                    
                    # 제공내역 후보 탐색
                    offer_node = d_soup.select_one(".offer-content, .info-offer .text, .camp-offer")
                    if offer_node:
                         print(f"Offer: {offer_node.get_text(strip=True)}")
                    else:
                         # 다른 패턴 찾아보기
                         titles = d_soup.find_all(text=lambda t: '제공' in t if t else False)
                         for t in titles:
                             parent = t.parent
                             print(f"Maybe Offer: {parent.get_text(strip=True)[:100]}")
                             
                    await detail_page.close()
                    
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
