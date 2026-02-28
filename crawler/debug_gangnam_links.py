import asyncio
from playwright.async_api import async_playwright

async def debug_links():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating...")
        await page.goto("https://xn--939au0g4vj8sq.net/", wait_until="domcontentloaded")
        
        # Get all links
        links = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.innerText.trim(),
                href: a.href
            }));
        }""")
        
        print(f"Found {len(links)} links.")
        for i, l in enumerate(links):
            if i < 50: # Print first 50
                print(f"{i}: {l['text']} -> {l['href']}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_links())
