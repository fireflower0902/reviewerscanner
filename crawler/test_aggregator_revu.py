import asyncio
import json
from playwright.async_api import async_playwright
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from aggregator import crawl_revu

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        print("Running crawl_revu from aggregator.py...")
        results = await crawl_revu(context)
        print(f"Aggregator Revu collected: {len(results)} items")
        if results:
            print("Sample 1:")
            print(json.dumps(results[0], indent=2, ensure_ascii=False))
            print("Sample 2:")
            print(json.dumps(results[-1], indent=2, ensure_ascii=False))
            
        with open("revu_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        await browser.close()
        
if __name__ == "__main__":
    asyncio.run(run())
