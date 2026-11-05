import re
import sys
import os
from typing import List, Dict
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, BrowserContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward, map_channel, parse_region_from_title
from category_mapper import SEOULOPPA_CATEGORY_MAP

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def crawl(context: BrowserContext) -> List[Dict]:
    """서울오빠 크롤링 (DOM + 동적 스크롤)"""
    print("[SeoulOppa] Starting crawl...")
    results = []
    page = await context.new_page()

    try:
        for cat_code, mapped_category in SEOULOPPA_CATEGORY_MAP.items():
            print(f"[SeoulOppa] Crawling {mapped_category} (cat: {cat_code})...")
            url = f"https://www.seoulouba.co.kr/campaign/?cat={cat_code}"

            try:
                await page.goto(url, wait_until="networkidle")
                await page.wait_for_timeout(2000)

                # 높이 변화 없을 때까지 동적 스크롤
                prev_height = await page.evaluate("document.body.scrollHeight")
                for _ in range(30):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(2000)
                    new_height = await page.evaluate("document.body.scrollHeight")
                    if new_height == prev_height:
                        break
                    prev_height = new_height

                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.select(".campaign_content")

                for item in items:
                    try:
                        title_node = item.select_one(".t_ttl a")
                        if not title_node: continue
                        title = title_node.get_text(strip=True)
                        link = title_node.get('href', '')
                        if link and not link.startswith('http'): link = f"https://www.seoulouba.co.kr{link}"

                        region_data = parse_region_from_title(title)

                        type_node = item.select_one(".com_icon .icon_tag span")
                        if type_node:
                            tt = type_node.get_text(strip=True)
                            if "배송형" in tt or "기자단" in tt or "구매평" in tt:
                                continue

                        reward_node = item.select_one(".t_basic .basic_blue")
                        reward_text = reward_node.get_text(strip=True) if reward_node else ""
                        reward_value = normalize_reward(reward_text)

                        applicants = 0
                        quota = 0
                        recruit_node = item.select_one(".recruit span")
                        if recruit_node:
                            recruit_text = recruit_node.get_text(strip=True)
                            stats_match = re.search(r'신청\s*(\d+).*?모집\s*(\d+)', recruit_text)
                            if stats_match:
                                applicants = int(stats_match.group(1))
                                quota = int(stats_match.group(2))

                        dday_node = item.select_one(".d_day span")
                        dday = dday_node.get_text(strip=True) if dday_node else ""

                        channel_alt = ""
                        channel_node = item.select_one(".ltop_icon .icon_box img")
                        if channel_node:
                            channel_alt = channel_node.get('alt', '')
                        type_ = map_channel(channel_alt, title)
                        category = mapped_category

                        img_node = item.select_one(".tum_img img")
                        img = img_node.get('src', '') if img_node else ""

                        results.append({
                            "platform": "서울오빠", "title": title, "url": link,
                            "region": region_data, "category": category,
                            "reward": {"text": reward_text, "value": reward_value},
                            "meta": {"type": type_, "dday": dday},
                            "image_url": img,
                            "stats": {"applicants": applicants, "quota": quota}
                        })
                    except Exception as e:
                        print(f"[SeoulOppa] Item Parse Error: {e} -> title: {title}")
                        continue
            except Exception as inner_e:
                print(f"[SeoulOppa] Category {cat_code} Crawl Error: {inner_e}")
                continue

    except Exception as e:
        print(f"[SeoulOppa] Error: {e}")
    finally:
        await page.close()

    print(f"[SeoulOppa] Collected {len(results)} items")
    return results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
