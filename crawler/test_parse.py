import asyncio
from playwright.async_api import async_playwright
import aggregator

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()

        try:
            print("=== 리뷰플레이스 테스트 ===")
            aggregator.REVIEWPLACE_CATEGORY_MAP = {"맛집": "음식점"} # 최소한으로 단건
            rp_res = await aggregator.crawl_reviewplace(context)
            for item in rp_res[:3]:
                print(item.get('title'), item.get('stats'))
        except Exception as e: print("RP Error:", e)

        try:
            print("\n=== 강남맛집 테스트 ===")
            aggregator.GANGNAM_CATEGORY_MAP = {"2005": "음식점"} 
            gm_res = await aggregator.crawl_kangnam(context)
            for item in gm_res[:3]:
                print(item.get('title'), item.get('stats'))
        except Exception as e: print("GM Error:", e)

        try:
            print("\n=== 리뷰노트 테스트 ===")
            rn_res = await aggregator.crawl_reviewnote(context)
            for item in rn_res[:3]:
                print(item.get('title'), item.get('stats'))
        except Exception as e: print("RN Error:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
