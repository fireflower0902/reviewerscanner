"""미블(mrblog.net) 크롤러 — 로그인 필요, Mac 전용

- 미블은 네이버 로그인(캡차)이 필요해 자동 로그인이 불가능하다.
  사람이 한 번 로그인해 둔 브라우저 프로필(scripts/mac/mrblog_login.py)을 재사용한다.
- 목록: GET /xhr/campaigns?type=region&page=N&category=<이름> → {"count", "html"} (페이지당 24개)
  로그인된 페이지 안에서 CSRF 토큰(meta csrf-token)과 함께 요청해야 한다 (밖에서 직접 요청하면 403).
- 카테고리는 카드에 없어서 사이트의 카테고리별 목록을 따로 읽어 분류한다.
- 세션이 만료되면 LoginRequired 를 던진다 → 호출한 쪽은 이전 데이터를 유지해야 한다.
"""
import asyncio
import json
import os
import re
import sys
from typing import Dict, List

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from region_mapper import RegionMapper
from helpers import normalize_reward, region_from_station
from category_mapper import extract_category_by_keyword

PROFILE_DIR = os.path.expanduser(os.environ.get("MRBLOG_PROFILE", "~/.reviewerscanner/profiles/mrblog"))
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
       "Chrome/130.0.0.0 Safari/537.36")

# 미블 카테고리 → 서비스 카테고리 (이후 프론트에서 식품→음식점, 여행→여행/숙박, 레저→문화/레저로 합쳐 보여줌)
CATEGORY_MAP = {
    "맛집": "음식점",
    "식품": "식품",
    "뷰티": "뷰티",
    "패션": "뷰티",        # 서울오빠의 '뷰티/패션' 처리와 같은 기준
    "생활": "생활",
    "여행/체험": "여행",
    "취미/레저": "레저",
}
MAX_PAGES = 120          # 안전 상한 (정상은 카테고리당 최대 50페이지 안팎)
MAX_CONSECUTIVE_ERRORS = 3


class LoginRequired(Exception):
    pass


_FETCH_JS = """async (u) => {
    const token = document.querySelector('meta[name="csrf-token"]')?.content || '';
    const c = new AbortController();
    const t = setTimeout(() => c.abort(), 30000);
    try {
        const r = await fetch(u, {headers: {'X-CSRF-TOKEN': token, 'X-Requested-With': 'XMLHttpRequest'},
                                  credentials: 'include', signal: c.signal});
        return [r.status, await r.text()];
    } finally { clearTimeout(t); }
}"""


def _channel(item) -> str:
    """카드의 채널 표시(sns_icon 클래스, 릴스 배지) → 표준 채널명"""
    icon = item.select_one(".sns_icon")
    classes = " ".join(icon.get("class", [])) if icon else ""
    text = item.get_text(" ", strip=True)
    if "릴스" in text and ("insta" in classes or item.select_one(".reels")):
        return "인스타그램 릴스"
    if "insta" in classes:
        return "인스타그램 피드"
    if "youtube" in classes:
        return "유튜브 동영상"
    if "clip" in classes:
        return "네이버 클립"
    return "네이버 블로그"


def _dday(text: str) -> str:
    t = re.sub(r"\s+", "", text or "")
    if not t:
        return ""
    if "마감" in t and "일" not in t:
        return "마감"
    m = re.search(r"(\d+)일남음", t)
    if m:
        return f"{int(m.group(1))}일 남음"
    m = re.search(r"D-?(\d+)", t, re.I)
    if m:
        return f"{int(m.group(1))}일 남음"
    return t


def parse_card(li, category: str):
    a = li.select_one("a.campaign_item")
    if not a:
        return None
    m = re.search(r"/campaigns/(\d+)", a.get("href", ""))
    if not m:
        return None
    cid = m.group(1)
    title = (a.select_one(".subject").get_text(strip=True) if a.select_one(".subject") else "").strip()
    if not title:
        return None
    area_node = a.select_one(".area")
    area = re.sub(r"\s+", " ", area_node.get_text(" ", strip=True)) if area_node else ""
    area = re.sub(r"^(릴스|인스타(그램)?)\s+", "", area)      # 지역 앞에 붙는 채널 배지 글자 제거 ("릴스 구파발역")
    if area in ("배송", "재택", "배송형"):
        return None                                           # 방문형이 아닌 캠페인은 수집하지 않는다
    region = RegionMapper.normalize(area)
    # 지역이 역 이름뿐("사당역")이거나 구/시까지 모를 때, 서울·경기 역 표로 보정한다
    if region["province"] == "기타" or (region["city"] == "기타" and region["province"] in ("서울", "경기")):
        hint = "" if region["province"] == "기타" else region["province"]
        station = region_from_station(area, hint)
        if station:
            region = RegionMapper.normalize(f"{station[0]} {station[1]}")
    desc_node = a.select_one(".desc")
    reward = re.sub(r"\s+", " ", (desc_node.get_text(" ", strip=True) if desc_node else "").replace("\xa0", " ")).strip()
    img = a.select_one(".thumb img")
    image_url = (img.get("src") or "") if img else ""
    if image_url.startswith("http://"):
        image_url = "https://" + image_url[len("http://"):]
    status = a.select_one(".status")
    dday = _dday(status.select_one(".d_day").get_text(" ", strip=True)) if status and status.select_one(".d_day") else ""
    applicants = quota = 0
    count = status.select_one(".count") if status else None
    if count:
        ctext = count.get_text(" ", strip=True)
        am = re.search(r"신청\s*(\d+)", ctext)
        qm = re.search(r"모집\s*(\d+)", ctext)
        applicants = int(am.group(1)) if am else 0
        quota = int(qm.group(1)) if qm else 0
    return {
        "platform": "미블", "title": title, "url": f"https://www.mrblog.net/campaigns/{cid}",
        "region": region, "category": category or extract_category_by_keyword(title, reward),
        "reward": {"text": reward[:100], "value": normalize_reward(reward)},
        "meta": {"type": _channel(a), "dday": dday},
        "image_url": image_url,
        "stats": {"applicants": applicants, "quota": quota},
    }


async def crawl(context) -> List[Dict]:
    print("[MrBlog] Starting crawl...")
    results: List[Dict] = []
    seen = set()
    page = context.pages[0] if context.pages else await context.new_page()
    await page.goto("https://www.mrblog.net/campaigns/region", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(2500)
    if "/login" in page.url:
        raise LoginRequired("미블 로그인이 만료되었습니다 — scripts/mac/mrblog_login.py 를 다시 실행해 로그인해 주세요")

    from urllib.parse import quote
    total_requests = 0
    for cat_name, mapped in CATEGORY_MAP.items():
        before = len(results)
        pages = 0
        errors = 0
        for page_no in range(1, MAX_PAGES + 1):
            url = (f"/xhr/campaigns?type=region&page={page_no}&category={quote(cat_name)}&order_by=1"
                   f"&is_instagram%5B0%5D=0&is_instagram%5B1%5D=1&category_seq=")
            try:
                status, body = await page.evaluate(_FETCH_JS, url)
            except Exception as e:
                errors += 1
                print(f"  [MrBlog] {cat_name} p{page_no} 요청 실패: {type(e).__name__}")
                if errors >= MAX_CONSECUTIVE_ERRORS:
                    break
                continue
            total_requests += 1
            if status in (401, 403, 419):
                if "csrf" in body.lower() or status in (401, 419):
                    raise LoginRequired(f"미블 요청이 거부되었습니다 (HTTP {status}) — 로그인 만료 가능성")
                errors += 1
                if errors >= MAX_CONSECUTIVE_ERRORS:
                    break
                continue
            if status != 200:
                errors += 1
                if errors >= MAX_CONSECUTIVE_ERRORS:
                    break
                continue
            errors = 0
            try:
                items = BeautifulSoup(json.loads(body).get("html", ""), "html.parser").select("li")
            except Exception:
                break
            cards = [c for c in items if c.select_one("a.campaign_item")]
            if not cards:
                break
            pages += 1
            for li in cards:
                try:
                    parsed = parse_card(li, mapped)
                except Exception as e:
                    print(f"  [MrBlog] 카드 파싱 오류: {e}")
                    continue
                if parsed and parsed["url"] not in seen:
                    seen.add(parsed["url"])
                    results.append(parsed)
        print(f"[MrBlog] {cat_name} → {mapped}: {len(results) - before}건 ({pages}페이지)")

    # 카테고리 목록에 없는 캠페인(카테고리 미지정)을 전체 목록에서 보충 — 제목·제공 내역 키워드로 분류
    before = len(results)
    errors = 0
    for page_no in range(1, MAX_PAGES + 1):
        url = (f"/xhr/campaigns?type=region&page={page_no}&category=&order_by=1"
               f"&is_instagram%5B0%5D=0&is_instagram%5B1%5D=1&category_seq=")
        try:
            status, body = await page.evaluate(_FETCH_JS, url)
        except Exception:
            errors += 1
            if errors >= MAX_CONSECUTIVE_ERRORS:
                break
            continue
        total_requests += 1
        if status != 200:
            errors += 1
            if errors >= MAX_CONSECUTIVE_ERRORS:
                break
            continue
        errors = 0
        cards = [c for c in BeautifulSoup(json.loads(body).get("html", ""), "html.parser").select("li") if c.select_one("a.campaign_item")]
        if not cards:
            break
        for li in cards:
            try:
                parsed = parse_card(li, None)
            except Exception:
                continue
            if parsed and parsed["url"] not in seen:
                seen.add(parsed["url"])
                results.append(parsed)
    print(f"[MrBlog] 카테고리 미지정 보충: {len(results) - before}건")
    print(f"[MrBlog] Collected {len(results)} items (요청 {total_requests}회)")
    return results


async def run() -> List[Dict]:
    os.makedirs(PROFILE_DIR, exist_ok=True)
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            PROFILE_DIR, headless=True, user_agent=_UA, locale="ko-KR",
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            return await crawl(context)
        finally:
            await context.close()
