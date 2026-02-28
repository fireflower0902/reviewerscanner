import asyncio
from playwright.async_api import async_playwright

async def debug_reviewnote():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.reviewnote.co.kr/campaigns?s=popular"
        print(f"Goto {url}...")
        await page.goto(url, wait_until="networkidle")
        
        # Select items
        items = await page.query_selector_all("div.infinite-scroll-component > div.relative")
        print(f"Found {len(items)} items.")
        
        missing_count = 0
        for i, item in enumerate(items):
            # Get Title/URL for context
            title_node = await item.query_selector("a.text-16m")
            title = await title_node.inner_text() if title_node else "No Title"
            link = await title_node.get_attribute("href") if title_node else ""
            
            # Check for img[alt='campaign']
            img = await item.query_selector("img[alt='campaign']")
            if not img:
                print(f"Item {i} [{title}]: Missing img[alt='campaign']")
                html = await item.inner_html()
                print(f"HTML: {html[:200]}...")
                missing_count += 1
            else:
                img_src = await img.get_attribute("src")
                
                # Logic from aggregator.py (simplified for debug)
                
                # Try scrolling to item if it's a placeholder
                if not img_src or "data:image" in img_src:
                     await item.scroll_into_view_if_needed()
                     await page.wait_for_timeout(500) # Wait for load
                     img_src = await img.get_attribute("src")
                     srcset = await img.get_attribute("srcset")
                
                final_img = img_src
                if not img_src or "data:image" in img_src:
                    if srcset:
                        candidates = srcset.split(',')
                        if candidates:
                            best_candidate = candidates[-1].strip().split(' ')[0]
                            if best_candidate:
                                final_img = best_candidate
                
                print(f"Item {i} [{title}]:")
                print(f"  - Original Src: {img_src[:50]}...")
                print(f"  - Extracted: {final_img}")
                
                if not final_img or "data:image" in final_img:
                     print(f"  - STILL BAD!")
                     missing_count += 1

        
        print(f"Total missing/bad images: {missing_count}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_reviewnote())
