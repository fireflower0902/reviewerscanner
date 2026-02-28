import asyncio
from playwright.async_api import async_playwright
import aggregator

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            print("=== 디너의여왕 테스트 ===")
            dq_res = await aggregator.crawl_dinnerqueen(context)
            for item in dq_res[:3]:
                print(item.get('title'), item.get('stats'))
        except Exception as e: print("DQ Error:", e)

        try:
            print("\n=== 서울오빠 테스트 ===")
            so_res = await aggregator.crawl_seouloppa(context)
            for item in so_res[:3]:
                print(item.get('title'), item.get('stats'))
        except Exception as e: print("SO Error:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
