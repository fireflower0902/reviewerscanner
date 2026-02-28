import asyncio
from playwright.async_api import async_playwright
import json

async def check_next_data():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.reviewnote.co.kr/campaigns?s=popular"
        print(f"Goto {url}...")
        await page.goto(url, wait_until="networkidle")
        
        # 1. Check __NEXT_DATA__
        next_data = await page.query_selector("#__NEXT_DATA__")
        if next_data:
            print("Found #__NEXT_DATA__!")
            content = await next_data.inner_text()
            try:
                data = json.loads(content)
                print("Successfully parsed JSON.")
                
                # Try to find campaign list in the props
                # Usually in props -> pageProps -> campaigns or dehydratedState
                print(f"Keys: {data.keys()}")
                if 'props' in data:
                    print(f"Props keys: {data['props'].keys()}")
                    if 'pageProps' in data['props']:
                        page_props = data['props']['pageProps']
                        print(f"PageProps keys: {page_props.keys()}")
                        
                        if 'data' in page_props:
                            # data might be the list or contain the list
                            d = page_props['data']
                            print(f"Data type: {type(d)}")
                            if isinstance(d, dict):
                                print(f"Data keys: {d.keys()}")
                                if 'objects' in d:
                                    objs = d['objects']
                                    print(f"Objects length: {len(objs)}")
                                    if len(objs) > 0:
                                        print(f"First object: {objs[0]}")

            except Exception as e:
                print(f"JSON Parse Error: {e}")
        else:
            print("No #__NEXT_DATA__ found.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_next_data())
