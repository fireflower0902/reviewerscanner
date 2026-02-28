import asyncio
from playwright.async_api import async_playwright
import aggregator

async def run():
    print("=== 서울오빠 카테고리 매핑 수정 테스트 ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            so_res = await aggregator.crawl_seouloppa(context)
            
            # 카테고리별로 몇개씩 수집되었는지 요약
            cat_counts = {}
            for item in so_res:
                cat = item.get('category')
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
                
            print(f"\n[Summary] Total collected: {len(so_res)}")
            for k, v in cat_counts.items():
                print(f"- {k}: {v}개")
                
            # 샘플 출력
            print("\n[샘플 5개]")
            for item in so_res[:5]:
                print(f"[{item.get('category')}] {item.get('title')}")
                
        except Exception as e: print("SO Error:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
