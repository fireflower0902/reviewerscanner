import re
import sys
import os
from typing import List, Dict
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, BrowserContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward, map_channel
from region_mapper import RegionMapper
from category_mapper import extract_category_by_keyword

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def crawl(context: BrowserContext) -> List[Dict]:
    """포블로그 크롤링 (무한스크롤)"""
    print("[4Blog] Starting crawl...")
    results = []
    page = await context.new_page()

    try:
        url = "https://4blog.net/list/coupon,blog,instar21,reels,youtube21,shorts,tiktok,threads,ncafe,naverclip,danggeun,xtwitter,etc/local"
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)

        print("[4Blog] Scrolling to load campaigns...")
        # 높이가 아니라 '캠페인 링크 수'가 늘어나는지로 판단하고, 느린 네트워크를 고려해 여러 번 기다린다
        item_selector = "a[href*='/campaign/']"
        prev_count = await page.locator(item_selector).count()
        stagnant = 0
        for i in range(120):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            grew = False
            for _ in range(6):  # 최대 약 9초 동안 증가 여부 확인
                await page.wait_for_timeout(1500)
                cur_count = await page.locator(item_selector).count()
                if cur_count > prev_count:
                    grew = True
                    break
            if grew:
                prev_count = cur_count
                stagnant = 0
            else:
                stagnant += 1
                if stagnant >= 2:
                    print(f"  [4Blog] Reached bottom at scroll {i+1} ({prev_count} links)")
                    break
            if (i+1) % 10 == 0:
                print(f"  [4Blog] Scroll {i+1} times... ({prev_count} links)")

        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select("a[href*='/campaign/']")
        print(f"  [4Blog] Found {len(items)} possible items after scrolling.")

        for item in items:
            try:
                link = item.get('href', '')
                if link and not link.startswith('http'):
                    link = f"https://4blog.net{link}"

                title_node = item.select_one(".camp-name")
                title = title_node.get_text(strip=True) if title_node else ""
                if not title: continue

                region_match = re.search(r'^\[(.*?)\]', title)
                raw_region = region_match.group(1) if region_match else title[:5]
                region_data = RegionMapper.normalize(raw_region)

                reward_node = item.select_one(".emphasize")
                offer = reward_node.get_text(separator=' ', strip=True) if reward_node else "상세페이지 참조"
                reward_value = normalize_reward(offer)
                if reward_value == 0:
                    reward_value = normalize_reward(title)

                dday_node = item.select_one(".remainDate")
                dday = dday_node.get_text(strip=True) if dday_node else ""

                type_node = item.select_one(".label-success")
                raw_type = type_node.get_text(strip=True) if type_node else ""
                type_ = map_channel(raw_type, title)

                img_node = item.select_one("img.lazy")
                img = img_node.get('src', '') if img_node else ""

                category = extract_category_by_keyword(title, offer)

                results.append({
                    "platform": "포블로그", "title": title, "url": link,
                    "region": region_data, "category": category,
                    "reward": {"text": offer, "value": reward_value},
                    "meta": {"type": type_, "dday": dday},
                    "image_url": img,
                    "stats": {"applicants": 0, "quota": 0}
                })
            except Exception:
                pass

    except Exception as e:
        print(f"[4Blog] Critical Error: {e}")
    finally:
        await page.close()

    print(f"[4Blog] Collected {len(results)} items")
    return results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
