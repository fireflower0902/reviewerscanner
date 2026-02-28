import asyncio
from playwright.async_api import async_playwright

async def debug_api():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a real browser context to get default headers/cookies if acts like a user
        page = await browser.new_page()
        
        # Go to home first to set cookies/session if needed
        await page.goto("https://www.reviewnote.co.kr")
        
        # Call API
        api_url = "https://www.reviewnote.co.kr/api/v2/campaigns?s=popular&limit=16&page=0"
        print(f"Fetching {api_url}...")
        
        response = await page.evaluate(f"""async () => {{
            const res = await fetch("{api_url}");
            return await res.json();
        }}""")
        
        print("Response received.")
        if 'objects' in response:
            print(f"Objects count: {len(response['objects'])}")
            if len(response['objects']) > 0:
                item = response['objects'][0]
                print(f"First item: {item}")
        else:
            print(f"Unexpected response keys: {response.keys()}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_api())
