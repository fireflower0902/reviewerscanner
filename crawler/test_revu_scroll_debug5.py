import asyncio
import json
import re
from playwright.async_api import async_playwright
import urllib.parse

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("Goto Revu local food...")
        await page.goto("https://www.revu.net/campaign/local/food/all", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        html = await page.content()
        
        # 1. Inspect __NUXT__ or apolloState
        nuxt_match = re.search(r'window\.__NUXT__\s*=\s*(.*?);', html)
        if nuxt_match:
             print("Found __NUXT__ Object!")
             with open("revu_nuxt.txt", "w", encoding="utf-8") as f:
                 f.write(nuxt_match.group(1))
        
        apollo_match = re.search(r'window\.__APOLLO_STATE__\s*=\s*(.*?);</script>', html)
        if apollo_match:
             print("Found __APOLLO_STATE__ Object!")
             with open("revu_apollo.json", "w", encoding="utf-8") as f:
                  f.write(apollo_match.group(1))

        # 2. Or if data is embedded in a script block?
        script_matches = re.finditer(r'<script id="__NEXT_DATA__".*?>(.*?)</script>', html)
        for idx, m in enumerate(script_matches):
            with open(f"revu_next_{idx}.json", "w", encoding="utf-8") as f:
                f.write(m.group(1))
            print("Found __NEXT_DATA__ Object!")
                
        print(f"Total HTML size: {len(html)} bytes")
        with open("revu_raw_source.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        await browser.close()
        
if __name__ == "__main__":
    asyncio.run(run())
