import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.reviewplace.co.kr/")
        html = await page.evaluate("""async () => {
            const response = await fetch('https://www.reviewplace.co.kr/theme/rp/_ajax_cmp_list_tpl.php?ct1=%EC%A7%80%EC%97%AD&ct2=%EB%A7%9B%EC%A7%91&rpage=1&device=pc');
            return await response.text();
        }""")
        print(html[:2000])
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
