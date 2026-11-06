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
from category_mapper import REVIEWPLACE_CATEGORY_MAP

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def crawl(context: BrowserContext) -> List[Dict]:
    """리뷰플레이스 크롤링 (API Pagination)"""
    results = []
    base_url = "https://www.reviewplace.co.kr/theme/rp/_ajax_cmp_list_tpl.php"

    try:
        page = await context.new_page()
        await page.goto("https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD", wait_until="domcontentloaded")

        print(f"[ReviewPlace] Starting API Crawl by Category...")

        for ct2_val, mapped_category in REVIEWPLACE_CATEGORY_MAP.items():
            print(f"[ReviewPlace] Crawling {mapped_category} (ct2: {ct2_val})...")
            encoded_ct2 = urllib.parse.quote(ct2_val)
            page_num = 0
            max_pages = 30

            while page_num < max_pages:
                page_num += 1
                try:
                    # fetch에 30초 제한(없으면 응답 하나가 멈출 때 영원히 대기)
                    js_code = f"""async () => {{
                        const c = new AbortController();
                        const t = setTimeout(() => c.abort(), 30000);
                        try {{
                            const response = await fetch('{base_url}?ct1=%EC%A7%80%EC%97%AD&ct2={encoded_ct2}&rpage={page_num}&device=pc', {{
                                method: 'GET',
                                headers: {{ 'Referer': 'https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD' }},
                                signal: c.signal
                            }});
                            return await response.text();
                        }} finally {{ clearTimeout(t); }}
                    }}"""
                    html_content = await page.evaluate(js_code)

                    if not html_content or len(html_content) < 100:
                        print(f"[ReviewPlace] Empty response at page {page_num}. Stopping.")
                        break

                    soup = BeautifulSoup(html_content, 'html.parser')
                    items = soup.select(".item")

                    if not items:
                        print(f"[ReviewPlace] No items at page {page_num}. Stopping.")
                        break

                    for item in items:
                        try:
                            title_node = item.select_one(".tit")
                            if not title_node: continue
                            title = title_node.get_text(strip=True)

                            link_node = item.select_one("a")
                            link = link_node.get('href') if link_node else ""
                            if link and not link.startswith('http'):
                                link = f"https://www.reviewplace.co.kr{link}"

                            region_match = re.match(r'^\[(.*?)\]', title)
                            if region_match:
                                raw_region = region_match.group(1)
                                region_data = RegionMapper.normalize(raw_region)
                            else:
                                region_data = RegionMapper.normalize(title[:5])

                            reward_node = item.select_one(".txt")
                            reward_text = reward_node.get_text(strip=True) if reward_node else ""
                            reward_value = normalize_reward(reward_text)

                            raw_type = ""
                            icon_nodes = item.select("div[class*='icon'], span[class*='icon'], i[class*='icon']")
                            for node in icon_nodes:
                                cls = " ".join(node.get("class", []))
                                if "blog" in cls: raw_type = "블로그"; break
                                if "insta" in cls: raw_type = "인스타그램"; break
                                if "youtube" in cls: raw_type = "유튜브"; break
                            type_ = map_channel(raw_type, title)
                            category = mapped_category

                            dday_node = item.select_one(".date_wrap .date")
                            dday_text = dday_node.get_text(strip=True) if dday_node else ""
                            dday = dday_text.replace(" ", "") if dday_text else ""

                            img_node = item.select_one("img.thumbimg")
                            img = img_node.get('src') if img_node else ""
                            if img and not img.startswith('http'):
                                img = f"https{img}" if img.startswith('//') else f"https://www.reviewplace.co.kr{img}"

                            applicants = 0
                            quota = 0
                            info_node = item.select_one(".item_info")
                            if info_node:
                                info_text = info_node.get_text(strip=True)
                                stats_match = re.search(r'신청\s*(\d+).*?(\d+)\s*명', info_text)
                                if stats_match:
                                    applicants = int(stats_match.group(1))
                                    quota = int(stats_match.group(2))

                            results.append({
                                "platform": "리뷰플레이스", "title": title, "url": link,
                                "region": region_data, "category": category,
                                "reward": {"text": reward_text, "value": reward_value},
                                "meta": {"type": type_, "dday": dday},
                                "image_url": img,
                                "stats": {"applicants": applicants, "quota": quota}
                            })
                        except: continue

                except Exception as e:
                    print(f"[ReviewPlace] Page {page_num} Error: {e}")
                    break

        await page.close()

    except Exception as e:
        print(f"[ReviewPlace] Critical Error: {e}")

    print(f"[ReviewPlace] Collected {len(results)} items")
    return results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
