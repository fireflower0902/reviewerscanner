import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        data = {}

        # 1. Gangnam Matjib
        print("Fetching Gangnam Matjib...")
        try:
            await page.goto("https://xn--939au0g4vj8sq.net/cp/?ca=20", wait_until="domcontentloaded")
            resp = await page.request.post("https://xn--939au0g4vj8sq.net/theme/go/_list_cmp_tpl.php", 
                                           data={"ca": "20", "loca_prt": "서울", "local_1": "전체", "local_2": "서울", "rpage": "1", "row_num": "20"})
            html = await resp.text()
            data['gangnam'] = html[:2000] # Just to see the structure of a few items
        except Exception as e:
            print("Gangnam error:", e)

        # 2. Review Place
        print("Fetching Review Place...")
        try:
            await page.goto("https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD", wait_until="domcontentloaded")
            js_code = """async () => {
                const response = await fetch('https://www.reviewplace.co.kr/theme/rp/_ajax_cmp_list_tpl.php?ct1=지역&rpage=1&device=pc', {
                    method: 'GET',
                    headers: { 'Referer': 'https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD' }
                });
                return await response.text();
            }"""
            html = await page.evaluate(js_code)
            data['reviewplace'] = html[:2000]
        except Exception as e:
            print("Review Place error:", e)

        # 3. Review Note
        print("Fetching Review Note...")
        try:
            resp = await context.request.get("https://www.reviewnote.co.kr/api/v2/campaigns?s=popular&limit=5&page=0")
            data['reviewnote'] = await resp.json()
        except Exception as e:
            print("Review Note error:", e)

        with open("sample_for_category.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        await browser.close()
        print("Saved to sample_for_category.json")

if __name__ == "__main__":
    asyncio.run(run())
