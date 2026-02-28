import asyncio
from playwright.async_api import async_playwright
import aggregator

async def run():
    print("=== 서울오빠 채널 파싱 수정 테스트 ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            so_res = await aggregator.crawl_seouloppa(context)
            
            # 채널별 개수 요약
            type_counts = {}
            for item in so_res:
                ctype = item.get('meta', {}).get('type', '기타')
                type_counts[ctype] = type_counts.get(ctype, 0) + 1
                
            print(f"\n[Summary] Total collected: {len(so_res)}")
            for k, v in type_counts.items():
                print(f"- {k}: {v}개")
                
            # 샘플 출력
            print("\n[샘플 5개]")
            for item in so_res[:5]:
                print(f"[{item.get('meta', {}).get('type')}] {item.get('title')}")
                
        except Exception as e: print("SO Error:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
