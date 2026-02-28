import asyncio
from playwright.async_api import async_playwright

async def debug_reviewplace():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 지역 카테고리 (방문형 위주)
        url = "https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD"
        print(f"Accessing: {url}")
        
        try:
            response = await page.goto(url, wait_until="networkidle", timeout=30000)
            print(f"Status Code: {response.status}")
            
            if response.status == 200:
                await page.screenshot(path="debug_reviewplace_list.png")
                content = await page.content()
                with open("debug_reviewplace_list.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print("Saved screenshot and HTML dump of List Page.")
                
            else:
                print("Failed to load page properly.")
                
        except Exception as e:
            print(f"Error: {e}")
                
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_reviewplace())
