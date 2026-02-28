import asyncio
from playwright.async_api import async_playwright
import json
import sys
import os

# Add parent directory to path to allow 'crawler.aggregator' import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.aggregator import crawl_4blog

async def test_single_crawler():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        print("Testing 4blog crawler module...")
        results = await crawl_4blog(context)
        print(f"\nFinal Collected: {len(results)} items")
        print(json.dumps(results[:2], ensure_ascii=False, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_single_crawler())
