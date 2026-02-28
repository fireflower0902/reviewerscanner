import asyncio
from playwright.async_api import async_playwright
import re

async def run():
    print("=== 레뷰(Revu) DOM 스크래핑 테스트 ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("[1] 로그인 폼 진입")
            await page.goto("https://www.revu.net/login", wait_until="networkidle")
            
            await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
            await page.fill('input[name="password"]', 'Dkssuddy1!')
            submit_btn = await page.query_selector('button[type="submit"]')
            if submit_btn:
                await submit_btn.click()
            else:
                await page.get_by_text("로그인", exact=True).click()
                
            await page.wait_for_timeout(4000)
            
            cats = ['food', 'beauty', 'travel', 'culture', 'stay']
            print(f"[2] 카테고리 로드: {cats[0]}")
            await page.goto(f"https://www.revu.net/campaign/local/{cats[0]}/all", wait_until="networkidle")
            
            # 충분히 스크롤해서 아이템 렌더링
            for _ in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
                
            # 카드 노드
            cards = await page.query_selector_all('.campaign-list .campaign-item')
            print(f"Cards found: {len(cards)}")
            
            for idx, c in enumerate(cards[:3]):
                print(f"--- Item {idx} ---")
                
                # Title
                title_node = await c.query_selector('.tit')
                title = await title_node.inner_text() if title_node else ""
                
                # Image
                img_node = await c.query_selector('.campaign-thumb .img')
                # lazy-src or background-image
                # 레뷰는 img 태그인지 div의 background-image인지 확인
                img_html = await c.query_selector('.campaign-thumb')
                html_content = await img_html.inner_html() if img_html else ""
                
                # Channel & Platform
                sns_node = await c.query_selector('ui-sns i.ico')
                # ico-blog, ico-instagram, etc
                sns_cls = await sns_node.get_attribute('class') if sns_node else ""
                
                # Reward (Text)
                desc_node = await c.query_selector('.desc')
                desc = await desc_node.inner_text() if desc_node else ""
                
                # Stats (Applicants)
                stat_node = await c.query_selector('.stat .txt-point')
                applicants = await stat_node.inner_text() if stat_node else "0"
                
                # Link
                a_node = await c.query_selector('a')
                link = await a_node.get_attribute('href') if a_node else ""
                
                # full text
                full_text = await c.inner_text()
                
                print(f"Title: {title}")
                print(f"Desc: {desc}")
                print(f"SNS: {sns_cls}")
                print(f"Stats: {applicants}")
                print(f"Link: {link}")
                print(f"Thumb HTML: {html_content[:200]}")
                print(f"Full text: {full_text.replace(chr(10), ' | ')}")
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
