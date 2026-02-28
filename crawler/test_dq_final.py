import asyncio
from playwright.async_api import async_playwright
import aggregator

async def run():
    print("=== 디너의여왕 데이터 파싱 검증 ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        try:
            res = await aggregator.crawl_dinnerqueen(context)
            print(f"Total collected: {len(res)}\n")
            
            for idx, item in enumerate(res[:5]):
                print(f"[{item.get('category')}] {item.get('title')}")
                print(f"   Reward: {item.get('reward')}")
                print(f"   Stats: {item.get('stats')}")
                print("---")
        except Exception as e:
            print("Error:", e)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
