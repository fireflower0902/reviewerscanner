import asyncio
from playwright.async_api import async_playwright
import aggregator

async def run():
    print("Test started")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        try:
            res = await aggregator.crawl_dinnerqueen(context)
            print(f"Result count: {len(res)}")
        except Exception as e:
            print("Error:", e)
        await browser.close()
    print("Test ended")

if __name__ == "__main__":
    asyncio.run(run())
