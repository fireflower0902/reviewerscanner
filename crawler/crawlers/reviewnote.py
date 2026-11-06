import re
import sys
import os
import datetime
import urllib.parse
from typing import List, Dict
from playwright.async_api import async_playwright, BrowserContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward, map_channel
from region_mapper import RegionMapper
from category_mapper import REVIEWNOTE_CATEGORY_MAP, extract_category_by_keyword

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
_BASE_IMG_URL = "https://firebasestorage.googleapis.com/v0/b/reviewnote-e92d9.appspot.com/o/"


_FETCH_JS = """async (u) => {
    const c = new AbortController();
    const t = setTimeout(() => c.abort(), 30000);
    try {
        const r = await fetch(u, { signal: c.signal });
        return [r.status, r.ok ? await r.json() : null];
    } finally { clearTimeout(t); }
}"""


async def crawl(context: BrowserContext) -> List[Dict]:
    """리뷰노트 크롤링 (API Pagination)"""
    print("[ReviewNote] Accessing API...")
    results = []

    page = await context.new_page()
    try:
        await page.goto("https://www.reviewnote.co.kr/campaigns", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[ReviewNote] Init Page Error: {e}")

    page_idx = 0
    limit = 20
    max_pages = 2000  # 안전 상한. 정상 종료는 API의 has_more=False
    seen_ids = set()

    while page_idx < max_pages:
        api_url = f"https://www.reviewnote.co.kr/api/v2/campaigns?s=popular&limit={limit}&page={page_idx}"
        try:
            # 직접 요청은 403(봇 차단)이라 페이지 컨텍스트 안에서 fetch (Referer/Sec-Fetch 헤더 자동 포함)
            # fetch에 30초 제한을 둔다(없으면 응답 하나가 멈출 때 크롤러 전체가 영원히 대기), 일시 오류는 2번 더 재시도
            fetched = None
            for attempt in range(3):
                try:
                    fetched = await page.evaluate(_FETCH_JS, api_url)
                    break
                except Exception as fetch_err:
                    print(f"[ReviewNote] fetch 실패 page {page_idx} (시도 {attempt + 1}/3): {str(fetch_err).splitlines()[0][:120]}")
                    await page.wait_for_timeout(1500)
            if fetched is None:
                print(f"[ReviewNote] page {page_idx}에서 3번 연속 실패 — 지금까지 수집한 {len(results)}건으로 마무리합니다")
                break
            status, data = fetched
            if status != 200 or data is None:
                print(f"[ReviewNote] API Error {status} at page {page_idx}")
                break

            items = data.get('objects', [])
            if not items:
                print("[ReviewNote] No more items.")
                break

            print(f"[ReviewNote] Page {page_idx}: Found {len(items)} items")

            for item in items:
                try:
                    title = item.get('title', '').strip()
                    campaign_id = item.get('id')
                    if campaign_id in seen_ids:
                        continue
                    seen_ids.add(campaign_id)
                    link = f"https://www.reviewnote.co.kr/campaigns/{campaign_id}"

                    sido_name = item.get('sido', {}).get('name', '')
                    city_name = item.get('city', '')
                    if sido_name in ['재택', '배송'] or city_name in ['재택', '배송']:
                        continue

                    raw_region = f"{sido_name} {city_name}".strip()
                    region_data = RegionMapper.normalize(raw_region)

                    offer = item.get('offer', '').strip()
                    reward_value = normalize_reward(offer)

                    channel = item.get('channel', '')
                    type_ = map_channel(channel, title)

                    raw_cat = item.get('category', {}).get('title', '')
                    if raw_cat in REVIEWNOTE_CATEGORY_MAP:
                        category = REVIEWNOTE_CATEGORY_MAP[raw_cat]
                    else:
                        category = extract_category_by_keyword(title, offer)

                    dday = ""
                    end_at = item.get('applyEndAt')
                    if end_at:
                        try:
                            dt_str = end_at.split('.')[0]
                            target = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                            now = datetime.datetime.now()
                            diff = target - now
                            if diff.days >= 0:
                                dday = f"{diff.days}일 남음"
                            else:
                                dday = "마감"
                        except: pass

                    img_key = item.get('imageKey')
                    img_url = ""
                    if img_key:
                        encoded_key = urllib.parse.quote(img_key, safe='')
                        img_url = f"{_BASE_IMG_URL}{encoded_key}?alt=media"

                    applicants = int(item.get('applicantCount', 0))
                    try:
                        quota = int(item.get('infNum', 0))
                    except:
                        quota = 0

                    results.append({
                        "platform": "리뷰노트", "title": title, "url": link,
                        "region": region_data, "category": category,
                        "reward": {"text": offer, "value": reward_value},
                        "meta": {"type": type_, "dday": dday},
                        "image_url": img_url,
                        "stats": {"applicants": applicants, "quota": quota}
                    })
                except Exception:
                    continue

            if page_idx % 100 == 0:
                print(f"  [ReviewNote] Page {page_idx}: {len(results)} items so far")
            if not data.get('has_more'):
                break
            page_idx += 1

        except Exception as e:
            print(f"[ReviewNote] Page Loop Error: {e}")
            break

    await page.close()
    print(f"[ReviewNote] Collected {len(results)} items")
    return results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
