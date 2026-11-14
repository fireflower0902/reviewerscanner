import asyncio
import time as _time
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
PACE_MS = 350                # 요청 사이 간격 (너무 빠르면 403)
REQUEST_BUDGET = int(os.environ.get("REVIEWNOTE_REQUEST_BUDGET", "1100"))   # 한 회차에 보내는 요청 수 상한
TIME_BUDGET_SEC = int(os.environ.get("REVIEWNOTE_TIME_BUDGET", "660"))
STATE_NAME = "reviewnote"
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


class Blocked(Exception):
    """리뷰노트가 일정 시간 요청을 막고 있다(403/429). 이번 회차는 여기서 멈추고 다음 회차에 이어서 한다."""


_requests_sent = 0


async def _fetch(page, url: str):
    """페이지 컨텍스트 안에서 fetch(직접 요청은 403). 일시 오류는 재시도, 403·429가 이어지면 Blocked"""
    global _requests_sent
    blocked = 0
    for attempt in range(4):
        try:
            _requests_sent += 1
            status, data = await page.evaluate(_FETCH_JS, url)
            if status == 200 and data is not None:
                await page.wait_for_timeout(PACE_MS)
                return data
            print(f"[ReviewNote] HTTP {status} ({url[-70:]}) 시도 {attempt + 1}/4")
            if status in (403, 429):
                blocked += 1
                if blocked >= 3:
                    raise Blocked(f"HTTP {status}")
                await page.wait_for_timeout(15000 * blocked)
            else:
                await page.wait_for_timeout(1500)
        except Blocked:
            raise
        except Exception as e:
            print(f"[ReviewNote] fetch 실패 (시도 {attempt + 1}/4): {str(e).splitlines()[0][:120]}")
            await page.wait_for_timeout(1500)
    return None


def _api(params: str, idx: int) -> str:
    return f"https://www.reviewnote.co.kr/api/v2/campaigns?{params}&s=default&limit={PAGE_SIZE}&page={idx}"


async def _pages(page, params: str):
    """한 조건의 모든 페이지. 반환: (항목 목록, 상한에 닿았는지). 중간에 실패하면 예외."""
    objs = []
    for idx in range(MAX_PAGES):
        data = await _fetch(page, _api(params, idx))
        if data is None:
            raise RuntimeError(f"리뷰노트 응답 실패: {params} page {idx}")
        items = data.get('objects', [])
        objs.extend(items)
        if not items or not data.get('has_more'):
            return objs, False
    return objs, True


async def _is_capped(page, params: str) -> bool:
    """마지막(100번째) 페이지에 내용이 있으면 이 조건은 1,600건 상한을 넘는다"""
    data = await _fetch(page, _api(params, MAX_PAGES - 1))
    if data is None:
        raise RuntimeError(f"리뷰노트 응답 실패: {params} probe")
    return bool(data.get('objects'))


async def _plan(page, sidos):
    """수집 조각 목록: 시·도 단위, 1,600건을 넘는 시·도(서울·경기 등)는 구·군 단위. 재택·배송은 제외"""
    units = []
    for sido in sidos:
        if sido["name"] in ("재택", "배송"):
            continue
        params = f"city={urllib.parse.quote(sido['name'])}"
        if await _is_capped(page, params):
            for g in sido.get("guguns", []):
                units.append((f"{sido['name']} {g['name']}", f"{params}&gugunSelected={g['id']}"))
        else:
            units.append((sido["name"], params))
    return units


async def _collect_unit(page, label: str, params: str):
    """조각 하나 수집. 구·군 하나가 상한을 넘으면 카테고리로 더 쪼갠다"""
    objs, capped = await _pages(page, params)
    if not capped:
        return objs
    print(f"[ReviewNote] {label}: 상한 도달 → 카테고리별로 다시 수집")
    objs = []
    for cat in _CATEGORIES:
        sub, sub_capped = await _pages(page, f"{params}&category={urllib.parse.quote(cat)}")
        if sub_capped:
            print(f"[ReviewNote] ⚠ {label}/{cat}도 상한에 닿았습니다 — 일부 누락 가능")
        objs.extend(sub)
    return objs


def _load_known():
    """지금까지 모은 리뷰노트 항목과 다음에 할 조각. 상태 파일이 없으면 직전에 게시한 데이터에서 시작한다.
    남은 일수 표기는 시간이 지난 만큼 보정하고, 마감이 지난 항목은 뺀다."""
    import datetime as _dt
    import r2_client
    from helpers import shift_dday
    if not r2_client.is_configured():
        return {}, None
    now = _dt.datetime.now(_dt.timezone.utc)
    state = r2_client.load_state(STATE_NAME)
    if state:
        items, saved_at, next_label = state.get("items", []), state.get("saved_at"), state.get("next_label")
    else:
        prev, saved_at = r2_client.load_previous()
        items, next_label = [c for c in prev if c.get("platform") == "리뷰노트"], saved_at
        print(f"[ReviewNote] 상태 파일 없음 → 직전 게시 데이터 {len(items)}건에서 시작")
    days_passed = 0
    if saved_at:
        kst = _dt.timezone(_dt.timedelta(hours=9))
        days_passed = (now.astimezone(kst).date() - _dt.datetime.fromisoformat(saved_at).astimezone(kst).date()).days
    known = {}
    for it in items:
        dday = shift_dday(it["meta"].get("dday", ""), days_passed)
        if dday is None or dday == "마감":
            continue
        it["meta"]["dday"] = dday
        known[it["url"]] = it
    return known, next_label


def _save_known(known: Dict, next_label):
    import datetime as _dt
    import r2_client
    if not r2_client.is_configured():
        return
    r2_client.save_state(STATE_NAME, {
        "saved_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "next_label": next_label,
        "items": list(known.values()),
    })


async def crawl(context: BrowserContext) -> List[Dict]:
    """리뷰노트 크롤링.

    서버가 조건당 1,600건까지만 주고 요청이 몰리면 403으로 막아서, 전체를 한 번에 받지 않는다.
    한 회차에 일부 조각(시·도/구·군)만 받아서 R2 상태 파일에 합치고, 다음 회차가 이어서 받는다.
    (전체를 한 바퀴 도는 데 약 2~3회차, 1~1.5시간) 반환값은 지금까지 모은 전체 항목이다."""
    print("[ReviewNote] Accessing API...")
    known, next_label = _load_known()
    page = await context.new_page()
    try:
        await page.goto("https://www.reviewnote.co.kr/campaigns", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[ReviewNote] Init Page Error: {e}")

    started = _time.time()
    done_units, blocked_msg = 0, None
    units = []
    try:
        sidos = await _fetch(page, "https://www.reviewnote.co.kr/api/v2/sidos")
        if not sidos:
            raise RuntimeError("리뷰노트 지역 목록(/api/v2/sidos)을 받지 못했습니다")
        units = await _plan(page, sidos)
        labels = [l for l, _ in units]
        start = labels.index(next_label) if next_label in labels else 0
        order = units[start:] + units[:start]
        print(f"[ReviewNote] 조각 {len(units)}개, {labels[start]} 부터 시작 (이미 보유 {len(known)}건)")
        for label, params in order:
            if _requests_sent >= REQUEST_BUDGET or _time.time() - started > TIME_BUDGET_SEC:
                break
            objs = await _collect_unit(page, label, params)
            for item in objs:
                try:
                    parsed = parse_item(item)
                except Exception:
                    continue
                if parsed and parsed["meta"]["dday"] != "마감":
                    known[parsed["url"]] = parsed
            done_units += 1
            next_label = order[done_units][0] if done_units < len(order) else order[0][0]
    except Blocked as e:
        blocked_msg = str(e)
        print(f"[ReviewNote] 요청이 막혔습니다({e}) — 여기까지 받은 것을 저장하고 다음 회차에 이어서 합니다")
    finally:
        await page.close()

    if not known:
        raise RuntimeError("리뷰노트 수집 결과가 없습니다")
    _save_known(known, next_label)
    print(f"[ReviewNote] Collected {len(known)} items (이번 회차 조각 {done_units}/{len(units)}개, 요청 {_requests_sent}번, "
          f"{_time.time() - started:.0f}초{', 막힘' if blocked_msg else ''}, 다음: {next_label})")
    return list(known.values())


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
