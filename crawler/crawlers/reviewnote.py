import asyncio
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


PAGE_SIZE = 16               # 서버가 limit 값을 무시하고 항상 16개씩 준다
MAX_PAGES = 100              # 2026-11 이후 한 조건(지역/카테고리)당 100페이지(1,600건)까지만 내려준다
PACE_MS = 150                # 요청 사이 간격
CONCURRENCY = 1             # 동시에 여러 개 요청하면 403(봇 차단)이 난다 — 한 번에 하나씩
MAX_FAILED_UNITS = 3         # 재시도 후에도 실패한 조각이 이 개수를 넘으면 이번 수집은 버린다
_CATEGORIES = ["맛집", "뷰티", "식품", "여행", "디지털", "반려동물", "기타"]


def parse_item(item: Dict):
    """API 항목 하나 → 표준 캠페인 dict. 제외 대상(재택·배송)이면 None"""
    title = item.get('title', '').strip()
    campaign_id = item.get('id')
    link = f"https://www.reviewnote.co.kr/campaigns/{campaign_id}"

    sido_name = item.get('sido', {}).get('name', '')
    city_name = item.get('city', '')
    if sido_name in ['재택', '배송'] or city_name in ['재택', '배송']:
        return None

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
            diff = target - datetime.datetime.now()
            dday = f"{diff.days}일 남음" if diff.days >= 0 else "마감"
        except Exception:
            pass

    img_key = item.get('imageKey')
    img_url = ""
    if img_key:
        img_url = f"{_BASE_IMG_URL}{urllib.parse.quote(img_key, safe='')}?alt=media"

    applicants = int(item.get('applicantCount', 0))
    try:
        quota = int(item.get('infNum', 0))
    except Exception:
        quota = 0

    return {
        "platform": "리뷰노트", "title": title, "url": link,
        "region": region_data, "category": category,
        "reward": {"text": offer, "value": reward_value},
        "meta": {"type": type_, "dday": dday},
        "image_url": img_url,
        "stats": {"applicants": applicants, "quota": quota},
    }


async def _fetch(page, url: str):
    """페이지 컨텍스트 안에서 fetch(직접 요청은 403). 일시 오류·403·429는 쉬었다가 6번까지 재시도. 끝내 실패하면 None"""
    for attempt in range(6):
        try:
            status, data = await page.evaluate(_FETCH_JS, url)
            if status == 200 and data is not None:
                await page.wait_for_timeout(PACE_MS)
                return data
            print(f"[ReviewNote] HTTP {status} ({url[-80:]}) 시도 {attempt + 1}/6")
            await page.wait_for_timeout(min(10000 * (attempt + 1), 45000) if status in (403, 429) else 1500)
        except Exception as e:
            print(f"[ReviewNote] fetch 실패 (시도 {attempt + 1}/6): {str(e).splitlines()[0][:120]}")
            await page.wait_for_timeout(1500)
    return None


async def _collect_unit(page, params: str):
    """한 조건(지역[+카테고리])의 모든 페이지를 받는다. 반환: (항목 목록, 상한 도달 여부, 성공 여부)"""
    objs = []
    for idx in range(MAX_PAGES):
        data = await _fetch(page, f"https://www.reviewnote.co.kr/api/v2/campaigns?{params}&s=default&limit={PAGE_SIZE}&page={idx}")
        if data is None:
            return objs, False, False
        items = data.get('objects', [])
        objs.extend(items)
        if not items or not data.get('has_more'):
            return objs, False, True
    return objs, True, True      # 100페이지를 다 채움 = 더 있을 수 있음


async def crawl(context: BrowserContext) -> List[Dict]:
    """리뷰노트 크롤링: 구·군 단위로 나눠 받는다(조건당 1,600건 상한 우회)"""
    print("[ReviewNote] Accessing API...")
    page = await context.new_page()
    try:
        await page.goto("https://www.reviewnote.co.kr/campaigns", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[ReviewNote] Init Page Error: {e}")

    sidos = await _fetch(page, "https://www.reviewnote.co.kr/api/v2/sidos")
    if not sidos:
        raise RuntimeError("리뷰노트 지역 목록(/api/v2/sidos)을 받지 못했습니다")

    # 시·도 단위로 한 번에 받고, 1,600건 상한에 닿은 곳(서울·경기 등)만 구·군 → 카테고리 순으로 더 쪼갠다
    # 재택·배송은 어차피 제외하므로 요청하지 않는다
    units = [(sido["name"], sido, f"city={urllib.parse.quote(sido['name'])}")
             for sido in sidos if sido["name"] not in ("재택", "배송")]
    print(f"[ReviewNote] 시·도 {len(units)}곳")

    sem = asyncio.Semaphore(CONCURRENCY)
    all_objs: List[Dict] = []
    failed: List[str] = []

    async def get_unit(label: str, params: str):
        async with sem:
            return await _collect_unit(page, params)

    async def by_category(label: str, params: str):
        out = []
        for cat in _CATEGORIES:
            sub, capped, ok = await get_unit(label, f"{params}&category={urllib.parse.quote(cat)}")
            if not ok:
                failed.append(f"{label}/{cat}")
            if capped:
                print(f"[ReviewNote] ⚠ {label}/{cat}도 상한({MAX_PAGES * PAGE_SIZE}건)에 닿았습니다 — 일부 누락 가능")
            out.extend(sub)
        return out

    async def worker(label: str, sido: Dict, params: str):
        objs, capped, ok = await get_unit(label, params)
        if not ok:
            failed.append(label)
            return
        if capped:
            print(f"[ReviewNote] {label}: 상한 도달 → 구·군별로 다시 수집")
            objs = []
            for g in sido.get("guguns", []):
                gl, gp = f"{label} {g['name']}", f"{params}&gugunSelected={g['id']}"
                sub, g_capped, g_ok = await get_unit(gl, gp)
                if not g_ok:
                    failed.append(gl)
                    continue
                if g_capped:
                    print(f"[ReviewNote] {gl}: 상한 도달 → 카테고리별로 다시 수집")
                    sub = await by_category(gl, gp)
                objs.extend(sub)
        all_objs.extend(objs)

    await asyncio.gather(*(worker(l, sd, q) for l, sd, q in units))
    await page.close()

    if len(failed) > MAX_FAILED_UNITS:
        raise RuntimeError(f"리뷰노트 {len(failed)}개 조각 수집 실패 {failed[:5]} — 이번 결과는 사용하지 않습니다")
    if failed:
        print(f"[ReviewNote] ⚠ 일부 조각 실패(이번 회차 누락): {failed}")

    results, seen_ids = [], set()
    for item in all_objs:
        cid = item.get('id')
        if cid in seen_ids:
            continue
        seen_ids.add(cid)
        try:
            parsed = parse_item(item)
        except Exception:
            continue
        if parsed:
            results.append(parsed)

    print(f"[ReviewNote] Collected {len(results)} items (시·도 {len(units)}곳, 원본 {len(all_objs)}건, 중복 제거 후 {len(seen_ids)}건)")
    return results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
