import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        print("=== 디너의여왕 (Dinner Queen) API Capture ===")
        page1 = await context.new_page()
        dq_apis = []
        async def on_response_dq(response):
            try:
                if "api" in response.url or "list" in response.url or "campaign" in response.url:
                    if response.request.resource_type in ["fetch", "xhr"]:
                        text = await response.text()
                        if text and len(text) > 500:
                            print(f"[DQ] API Found: {response.url}")
                            print(f"[DQ] Response Snippet: {text[:300]}")
                            dq_apis.append(response.url)
            except: pass
        page1.on("response", on_response_dq)
        try:
            await page1.goto("https://dinnerqueen.net/taste", wait_until="networkidle")
            await page1.wait_for_timeout(2000)
            
            # Scroll down to trigger pagination
            await page1.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page1.wait_for_timeout(2000)
        except Exception as e: print("DQ Error:", e)

        print("\n=== 서울오빠 (Seoul Oppa) API Capture ===")
        page2 = await context.new_page()
        so_apis = []
        async def on_response_so(response):
            try:
                if "api" in response.url or "list" in response.url or "campaign" in response.url:
                    if response.request.resource_type in ["fetch", "xhr"]:
                        text = await response.text()
                        if text and len(text) > 500:
                            print(f"[SO] API Found: {response.url}")
                            print(f"[SO] Response Snippet: {text[:300]}")
                            so_apis.append(response.url)
            except: pass
        page2.on("response", on_response_so)
        try:
            await page2.goto("https://www.seoulouba.co.kr/", wait_until="networkidle")
            await page2.wait_for_timeout(2000)
            await page2.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page2.wait_for_timeout(2000)
        except Exception as e: print("SO Error:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
