import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import json

async def debug_api_mapping():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a real browser context to get default headers/cookies if acts like a user
        context = await browser.new_context()
        page = await context.new_page()
        
        # Go to home first to set cookies/session if needed
        await page.goto("https://www.reviewnote.co.kr")
        
        # Call API using APIRequestContext
        api_url = "https://www.reviewnote.co.kr/api/v2/campaigns?s=popular&limit=20&page=0"
        print(f"Fetching {api_url}...")
        
        # Use context request
        response_obj = await context.request.get(api_url)
        
        if not response_obj.ok:
            print(f"Request failed: {response_obj.status} {response_obj.status_text}")
            await browser.close()
            return
            
        print("Response received.")
        response = await response_obj.json()
        
        items = response.get('objects', [])
        print(f"Items: {len(items)}")
        
        for item in items[:5]:
            print(f"\n--- Item {item['id']} ---")
            print(f"Title: {item['title']}")
            print(f"Channel: {item['channel']}")
            print(f"Sido: {item.get('sido', {}).get('name')}")
            print(f"City: {item.get('city')}")
            
            # Construct Image URL
            img_key = item.get('imageKey', '')
            if img_key:
                # Need to handle slash coding if any
                encoded_key = urllib.parse.quote(img_key, safe='')
                img_url = f"https://firebasestorage.googleapis.com/v0/b/reviewnote-e92d9.appspot.com/o/{encoded_key}?alt=media"
                print(f"Constructed Img: {img_url}")
            
            # D-Day Logic
            # applyEndAt (e.g. 2026-02-27T14:59:59.999Z)
            print(f"ApplyEndAt: {item.get('applyEndAt')}")
            
            # Reward
            print(f"Offer: {item.get('offer')}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_api_mapping())
