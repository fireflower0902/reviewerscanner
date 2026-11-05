import re
import sys
import os
import datetime
from typing import List, Dict
from playwright.async_api import async_playwright, BrowserContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward, map_channel
from region_mapper import RegionMapper
from category_mapper import OHMYBLOG_CATEGORY_MAP, extract_category_by_keyword

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def crawl(context: BrowserContext) -> List[Dict]:
    """오마이블로그 크롤링 (API 2단계 페이지네이션)"""
    print("[OhMyBlog] Starting crawl...")
    results = []

    # 1. 지역 동적 조회
    region_map = {}
    try:
        res_region = await context.request.get("https://www.ohmyblog.co.kr/api/web/region?action=list")
        if res_region.ok:
            region_data = await res_region.json()
            for country in region_data.get("data", []):
                province_name = country.get("name", "")
                for area in country.get("areas", []):
                    g_seq = str(area.get("country_groupSeq", ""))
                    a_name = area.get("area", "")
                    region_map[g_seq] = f"{province_name} {a_name}".strip()
    except Exception as e:
        print(f"[OhMyBlog] Region fetch error: {e}")

    # 2. 카테고리별 app_seq → category 매핑 사전 빌드
    native_category_lookup = {}
    for cat_code, mapped_category in OHMYBLOG_CATEGORY_MAP.items():
        page_idx = 1
        try:
            while True:
                url = f"https://www.ohmyblog.co.kr/api/web/campaign/active?page={page_idx}&limit=100&app_type=A&app_cate_detail={cat_code}"
                res = await context.request.get(url)
                if not res.ok: break
                data = await res.json()
                campaigns = data.get('data', {}).get('campaigns', [])
                if not campaigns: break
                for item in campaigns:
                    app_seq = str(item.get('app_seq', ''))
                    native_category_lookup[app_seq] = mapped_category
                page_idx += 1
        except Exception:
            pass

    # 3. 전체 방문형 캠페인 조회
    page_idx = 1
    try:
        while True:
            url = f"https://www.ohmyblog.co.kr/api/web/campaign/active?page={page_idx}&limit=20&app_type=A"
            res = await context.request.get(url)
            if not res.ok:
                print(f"  [OhMyBlog] API Error at page {page_idx}")
                break

            data = await res.json()
            campaigns = data.get('data', {}).get('campaigns', [])
            if not campaigns: break
            print(f"  [OhMyBlog] Page {page_idx}: Found {len(campaigns)} items")

            for item in campaigns:
                try:
                    title = item.get('app_title', '')
                    app_seq = str(item.get('app_seq', ''))
                    link = f"https://www.ohmyblog.co.kr/productDetail.apsl?app_seq={app_seq}"
                    offer = item.get('supplyItem', '상세페이지 참조')

                    region_data = {"province": "기타", "city": "기타", "normalized": "기타"}
                    g_seq = str(item.get('country_groupSeq', ''))
                    if g_seq and g_seq in region_map:
                        raw_region = region_map[g_seq]
                        region_data = RegionMapper.normalize(raw_region)
                    else:
                        region_match = re.search(r'^\[(.*?)\]', title)
                        if region_match:
                            raw_region = region_match.group(1)
                            region_data = RegionMapper.normalize(raw_region)

                    if app_seq in native_category_lookup:
                        category = native_category_lookup[app_seq]
                    else:
                        category = extract_category_by_keyword(title, offer)

                    reward_value = normalize_reward(offer)

                    dday = ""
                    end_date = item.get('app_recruitEndDate', '')
                    if end_date:
                        try:
                            target = datetime.datetime.strptime(end_date.split(' ')[0], "%Y-%m-%d")
                            now = datetime.datetime.now()
                            diff = target - now
                            if diff.days >= 0: dday = f"{diff.days}일 남음"
                            else: dday = "마감"
                        except Exception: pass

                    raw_sns = item.get('sns_platforms', '')
                    type_ = map_channel(raw_sns, title)

                    img = item.get('thumbnail', '')
                    if img and not img.startswith('http'):
                        img = f"https://www.ohmyblog.co.kr{img}"

                    applicants = int(item.get('applicant_count', 0))
                    try: quota = int(item.get('app_recruitCount', 0))
                    except ValueError: quota = 0

                    results.append({
                        "platform": "오마이블로그", "title": title, "url": link,
                        "region": region_data, "category": category,
                        "reward": {"text": offer, "value": reward_value},
                        "meta": {"type": type_, "dday": dday},
                        "image_url": img,
                        "stats": {"applicants": applicants, "quota": quota}
                    })
                except Exception:
                    pass
            page_idx += 1

    except Exception as e:
        print(f"[OhMyBlog] Critical Error: {e}")

    print(f"[OhMyBlog] Collected {len(results)} items")
    return results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
