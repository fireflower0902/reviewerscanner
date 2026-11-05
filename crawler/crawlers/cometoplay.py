import re
import sys
import os
import urllib.parse
from typing import List, Dict
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, BrowserContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward, map_channel
from region_mapper import RegionMapper
from category_mapper import COMETOPLAY_CATEGORY_MAP

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def crawl(context: BrowserContext) -> List[Dict]:
    """놀러와체험단 크롤링 (페이지네이션)"""
    print("[ComeToPlay] Starting crawl...")
    results = []
    page = await context.new_page()

    try:
        print("[ComeToPlay] Accessing main page to click '지역'...")
        await page.goto("https://www.cometoplay.kr/", wait_until="domcontentloaded", timeout=60000)
        local_menu = page.locator(".gnb_menu a:has-text('지역')").first
        await local_menu.click()
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"[ComeToPlay] Click '지역' Error: {e}")

    try:
        for ct_id, mapped_category in COMETOPLAY_CATEGORY_MAP.items():
            print(f"[ComeToPlay] Crawling {mapped_category} (cat: {ct_id})...")
            url = f"https://www.cometoplay.kr/item_list.php?category_id={ct_id}&sst=it_datetime&sod=desc"

            try:
                for page_num in range(1, 100):
                    paginated_url = f"{url}&page={page_num}"
                    try:
                        await page.goto(paginated_url, wait_until="networkidle")
                        await page.wait_for_timeout(1000)
                    except Exception as goto_e:
                        print(f"[ComeToPlay] Page {page_num} Goto Error: {goto_e}")
                        break

                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    items = soup.select(".item_box_list li")

                    if not items:
                        break

                    print(f"  -> Page {page_num}: Found {len(items)} items")

                    for item in items:
                        try:
                            link_node = item.select_one("a")
                            if not link_node: continue
                            link = link_node.get('href', '')
                            if link and not link.startswith('http'): link = f"https://www.cometoplay.kr/{link.lstrip('/')}"

                            title_node = item.select_one(".it_name")
                            title = title_node.get_text(strip=True) if title_node else ""
                            if not title: continue

                            region_match = re.search(r'\[(.*?)\]', title)
                            raw_region = region_match.group(1) if region_match else title[:5]
                            region_data = RegionMapper.normalize(raw_region)

                            reward_node = item.select_one(".it_description")
                            offer = reward_node.get_text(strip=True) if reward_node else "상세페이지 참조"
                            reward_value = normalize_reward(title)

                            dday_node = item.select_one(".option_re .txt_num")
                            dday = dday_node.get_text(strip=True) if dday_node else ""
                            if dday.startswith("D-day"): dday = dday.replace("D-day", "").strip() + "일 남음"

                            raw_type = ""
                            if item.select_one(".blog"): raw_type = "블로그"
                            elif item.select_one(".insta"): raw_type = "인스타그램"
                            type_ = map_channel(raw_type, title)
                            category = mapped_category

                            applicants = 0
                            quota = 0
                            peo_cnt = item.select_one(".peo_cnt")
                            if peo_cnt:
                                peo_text = peo_cnt.get_text(strip=True)
                                stats_match = re.search(r'신청\s*(\d+).*?모집\s*(\d+)', peo_text)
                                if stats_match:
                                    applicants = int(stats_match.group(1))
                                    quota = int(stats_match.group(2))

                            img_node = item.select_one(".it_img")
                            img_src = img_node.get('src', '') if img_node else ""
                            img = ""
                            if img_src:
                                if img_src.startswith('http'):
                                    img = img_src
                                else:
                                    img = urllib.parse.urljoin("https://www.cometoplay.kr/", img_src)

                            results.append({
                                "platform": "놀러와체험단", "title": title, "url": link,
                                "region": region_data, "category": category,
                                "reward": {"text": offer, "value": reward_value},
                                "meta": {"type": type_, "dday": dday},
                                "image_url": img,
                                "stats": {"applicants": applicants, "quota": quota}
                            })
                        except Exception:
                            continue
            except Exception as inner_e:
                print(f"[ComeToPlay] Category {ct_id} Crawl Error: {inner_e}")
                continue

    except Exception as e:
        print(f"[ComeToPlay] Error: {e}")
    finally:
        await page.close()

    print(f"[ComeToPlay] Collected {len(results)} items")
    return results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
