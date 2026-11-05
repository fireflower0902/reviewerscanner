import re
import sys
import os
from typing import List, Dict
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, BrowserContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward, map_channel, parse_region_from_title
from region_mapper import RegionMapper
from category_mapper import GANGNAM_CATEGORY_MAP

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def crawl(context: BrowserContext) -> List[Dict]:
    """강남맛집 크롤링 (API-based Pagination)"""
    regions = [
        {"name": "서울", "loca_prt": "서울", "local_1": "전체", "local_2": "서울"},
        {"name": "경기/인천", "loca_prt": "경기-인천", "local_1": "전체", "local_2": "경기|인천"},
        {"name": "대전/충청", "loca_prt": "대전-세종-충청", "local_1": "전체", "local_2": "대전|세종|충청"},
        {"name": "부산/경남", "loca_prt": "부산-경남", "local_1": "전체", "local_2": "부산|경남"},
        {"name": "대구/경북", "loca_prt": "대구-경북", "local_1": "전체", "local_2": "대구|경북"},
        {"name": "광주/전라", "loca_prt": "광주-전라", "local_1": "전체", "local_2": "광주|전라"},
        {"name": "강원", "loca_prt": "강원", "local_1": "전체", "local_2": "강원"},
        {"name": "제주", "loca_prt": "제주", "local_1": "전체", "local_2": "제주"}
    ]

    all_results = []
    api_url = "https://xn--939au0g4vj8sq.net/theme/go/_list_cmp_tpl.php"

    page = await context.new_page()
    try:
        await page.goto("https://xn--939au0g4vj8sq.net/cp/?ca=20", wait_until="domcontentloaded")
    except: pass

    try:
        for ca_code, mapped_category in GANGNAM_CATEGORY_MAP.items():
            for region in regions:
                print(f"[Gangnam] Crawling {mapped_category} (Region: {region['name']})...")
                for page_num in range(1, 61):
                    form_data = {
                        "ca": ca_code,
                        "loca_prt": region['loca_prt'],
                        "local_1": region['local_1'],
                        "local_2": region['local_2'],
                        "rpage": str(page_num),
                        "row_num": "20"
                    }
                    try:
                        response = await page.request.post(api_url, form=form_data)
                        if not response.ok:
                            print(f"  [Gangnam] API Status {response.status} at {region['name']} p{page_num}")
                            break
                        html_fragment = await response.text()
                        if not html_fragment or len(html_fragment) < 50:
                            break
                        soup = BeautifulSoup(html_fragment, 'html.parser')
                        soup_items = soup.select("li.list_item")
                        if not soup_items:
                            break

                        for item in soup_items:
                            try:
                                title_node = item.select_one("dt.tit a")
                                if not title_node: continue
                                title = title_node.get_text(strip=True)
                                link_href = title_node.get('href')
                                if not link_href.startswith('http'): link = "https://xn--939au0g4vj8sq.net" + link_href
                                else: link = link_href

                                raw_region_match = re.match(r'^\[(.*?)\]', title)
                                raw_region = raw_region_match.group(1) if raw_region_match else title[:5]
                                region_data = RegionMapper.normalize(raw_region)

                                sub_tit = item.select_one("dd.sub_tit")
                                reward_text = sub_tit.get_text(strip=True) if sub_tit else ""
                                reward_value = normalize_reward(reward_text)

                                dday_node = item.select_one("span.dday")
                                dday = dday_node.get_text(strip=True) if dday_node else ""

                                label_node = item.select_one("span.label")
                                raw_type = ""
                                if label_node:
                                    if label_node.select_one("em.blog"): raw_type = "블로그"
                                    elif label_node.select_one("em.insta"): raw_type = "인스타그램"
                                    elif label_node.select_one("em.youtube") or label_node.select_one("em.yt"): raw_type = "유튜브"
                                    elif label_node.select_one("em.clip"): raw_type = "클립"
                                    else: raw_type = label_node.get_text(strip=True)
                                type_ = map_channel(raw_type, title)
                                category = mapped_category

                                img_node = item.select_one("img.thumb_img")
                                img = img_node.get('src') if img_node else ""
                                if img and img.startswith('//'): img = "https:" + img

                                applicants = 0
                                quota = 0
                                info_node = item.select_one("p.item_info span.numb")
                                if info_node:
                                    info_text = info_node.get_text(strip=True)
                                    stats_match = re.search(r'신청\s*(\d+).*?모집\s*(\d+)', info_text)
                                    if stats_match:
                                        applicants = int(stats_match.group(1))
                                        quota = int(stats_match.group(2))

                                all_results.append({
                                    "platform": "강남맛집", "title": title, "url": link,
                                    "region": region_data, "category": category,
                                    "reward": {"text": reward_text, "value": reward_value},
                                    "meta": {"type": type_, "dday": dday},
                                    "image_url": img,
                                    "stats": {"applicants": applicants, "quota": quota}
                                })
                            except Exception: continue
                    except Exception as e:
                        print(f"  [Gangnam] Error page {page_num}: {e}")
                        break
    except Exception as e:
        print(f"[Gangnam] Critical Error: {e}")
    finally:
        await page.close()

    print(f"[Gangnam] Collected {len(all_results)} items")
    return all_results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
