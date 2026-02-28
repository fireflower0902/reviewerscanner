import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        # 1. 로그인
        print("[Revu] Logging in...")
        await page.goto("https://www.revu.net/login", wait_until="networkidle")
        await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
        await page.fill('input[name="password"]', 'Dkssuddy1!')
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
             await submit_btn.click()
        else:
             await page.get_by_text("로그인", exact=True).click()
        await page.wait_for_timeout(3000)
        
        print("[Revu] Visiting local food...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        html = await page.content()
        with open("debug_revu.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 페이지네이션 링크 찾기
        links = soup.select("a[href*='page=']")
        print(f"Found {len(links)} links with 'page='.")
        for l in links:
            print(l.get('href'), l.get_text(strip=True))
            
        # 페이지네이션 영역 클래스 찾기
        pagers = soup.select(".pagination, .pager, .paging")
        for p in pagers:
            print("Found pager block:", p.get('class'))
            
        # 다른 더보기 버튼 후보 찾기
        btns = soup.select("button")
        for b in btns:
            text = b.get_text(strip=True)
            if "더보기" in text or "more" in text.lower():
                 print("Found candidate '더보기' button in HTML:", text)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
