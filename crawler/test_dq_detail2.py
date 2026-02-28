import asyncio
from playwright.async_api import async_playwright
import aggregator
from bs4 import BeautifulSoup
import re

def parse_dq_offer(text):
    text = text.replace('\n', '')
    match = re.search(r'제공\s*내역\s*(.*?)(?:참여\s*전\s*필수|◈|★)', text)
    if match:
        offer = match.group(1).strip()
        if offer: return offer
    return "상세페이지 참조"

async def run():
    print("=== 디너의여왕 상세페이지 제공량 파싱 테스트 2 ===")
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
            
            items = soup.select(".qz-dq-card")[:5]
            for idx, item in enumerate(items):
                link_node = item.select_one("a.qz-dq-card__link")
                link = link_node.get('href', '') if link_node else ""
                if link and not link.startswith('http'): link = f"https://dinnerqueen.net{link}"
                title = link_node.get('title', '').replace(' 신청하기', '') if link_node else "N/A"
                print(f"--- {title} ---")
                
                if link:
                    detail_page = await context.new_page()
                    await detail_page.goto(link, wait_until="domcontentloaded")
                    await detail_page.wait_for_timeout(500)
                    detail_html = await detail_page.content()
                    d_soup = BeautifulSoup(detail_html, 'html.parser')
                    
                    full_text = d_soup.get_text(separator=' ', strip=True)
                    # "제공 내역" 근처 텍스트 추출 시도
                    offer = parse_dq_offer(full_text)
                    print(f"Parsed Offer: {offer}")
                             
                    await detail_page.close()
                    
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
