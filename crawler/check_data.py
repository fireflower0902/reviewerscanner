import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        
        # 1. ReviewPlace
        print("=== ReviewPlace ===")
        await page.goto("https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD")
        rp_html = await page.evaluate("""async () => {
            const res = await fetch('https://www.reviewplace.co.kr/theme/rp/_ajax_cmp_list_tpl.php?ct1=%EC%A7%80%EC%97%AD&ct2=%EB%A7%9B%EC%A7%91&rpage=1&device=pc');
            return await res.text();
        }""")
        soup = BeautifulSoup(rp_html, 'html.parser')
        item = soup.select_one('.item')
        if item:
            print("RP HTML Text:", item.text[:500].replace('\\n', ' '))
            
        print("\n=== ReviewNote ===")
        # 2. ReviewNote
        api_url = "https://www.reviewnote.co.kr/api/v2/campaigns?s=popular&limit=1&page=0"
        rn_res = await context.request.get(api_url)
        data = await rn_res.json()
        if data.get('objects'):
            obj = data['objects'][0]
            print("keys:", obj.keys())
            print("apply_cnt:", obj.get('apply_cnt', obj.get('apply_count', obj.get('applicant', 'Not Found'))))
            print("recruit_cnt:", obj.get('recruit_cnt', obj.get('recruit_count', obj.get('quota', 'Not Found'))))
            # Just print all key-values looking like numbers
            for k, v in obj.items():
                if isinstance(v, int):
                    print(f"RN int field {k}: {v}")
                    
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
