import asyncio
import sys
from playwright.async_api import async_playwright

async def debug_scroll():
    print("Starting script...", flush=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://xn--939au0g4vj8sq.net/cp/?ca=20"
        print(f"Navigating to {url}", flush=True)
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Navigation failed: {e}", flush=True)
            return

        # Initial count
        try:
            items = await page.locator("li.list_item").count()
            print(f"Initial items: {items}", flush=True)
            
            # Scroll down
            for i in range(3):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                print(f"Scrolled {i+1}", flush=True)
                await asyncio.sleep(3)
                new_count = await page.locator("li.list_item").count()
                print(f"Items after scroll {i+1}: {new_count}", flush=True)
                
        except Exception as e:
            print(f"Error during interaction: {e}", flush=True)
            
        await browser.close()
        print("Browser closed.", flush=True)

if __name__ == "__main__":
    asyncio.run(debug_scroll())
