import re
import asyncio
from typing import Dict

try:
    from crawler.region_mapper import RegionMapper
except ImportError:
    from region_mapper import RegionMapper


TODAY_LABEL = "오늘마감"   # 당일 마감 표기(프론트 app/lib/dday.ts 의 TODAY_LABEL과 동일하게 유지)


def normalize_reward(reward_text: str) -> int:
    """'3만원' -> 30000"""
    if not reward_text: return 0
    txt = reward_text.replace(',', '').replace('원', '')
    nums = re.findall(r'\d+', txt)
    if not nums: return 0
    val = int(nums[0])
    if '만' in reward_text: val *= 10000
    return val


def map_channel(type_text: str, title: str) -> str:
    text = (type_text + " " + title).lower()
    if any(k in text for k in ['블로그', 'blog']):
        return "네이버 블로그"
    elif any(k in text for k in ['릴스', 'reels', '숏폼_인스타']):
        return "인스타그램 릴스"
    elif any(k in text for k in ['인스타', 'instagram', '피드']):
        return "인스타그램 피드"
    elif any(k in text for k in ['숏츠', 'shorts', '숏폼_유튜브']):
        return "유튜브 숏츠"
    elif any(k in text for k in ['유튜브', 'youtube', '동영상']):
        return "유튜브 동영상"
    elif any(k in text for k in ['클립', 'clip', '숏폼']):
        return "네이버 클립"
    return "기타"


def parse_region_from_title(title: str) -> Dict:
    region_data = {"province": "기타", "city": "기타", "normalized": "기타"}
    brackets = re.findall(r'\[([^\]]+)\]', title)

    if brackets:
        raw_region_fallback = brackets[-1]
        for b in reversed(brackets):
            res = RegionMapper.normalize(b)
            if res["province"] != "기타" or res["city"] != "기타":
                region_data = res
                break
        else:
            region_data = RegionMapper.normalize(raw_region_fallback)
            if region_data["province"] == "기타":
                region_data["normalized"] = raw_region_fallback
    else:
        region_data = RegionMapper.normalize(title[:5])
        if region_data["province"] == "기타":
            region_data["normalized"] = title[:5]

    return region_data


async def scroll_to_bottom(page, max_scrolls: int = 50):
    previous_height = await page.evaluate("document.body.scrollHeight")
    for i in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            await asyncio.sleep(2)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                print(f"  [Scroll] Reached bottom at scroll {i+1}")
                break
        previous_height = new_height
        if (i+1) % 10 == 0:
            print(f"  [Scroll] {i+1} times...")


def normalize_dday(text: str) -> str:
    """마감 표기를 프론트가 읽는 형식으로 통일: 'D-5' -> '5일 남음', 'D-DAY' -> '오늘까지'"""
    if not text:
        return text
    t = text.strip()
    if re.match(r'^0\s*일\s*남음$', t) or re.match(r'^오늘\s*(까지|마감)$', t):   # 당일 마감 표기 통일
        return TODAY_LABEL
    m = re.match(r'^D\s*-\s*(\d+)$', t, re.IGNORECASE)
    if m:
        n = int(m.group(1))
        return TODAY_LABEL if n == 0 else f"{n}일 남음"
    if t.upper().replace(" ", "") in ("D-DAY", "DDAY"):
        return TODAY_LABEL
    return t


def shift_dday(dday: str, days_passed: int):
    """수집한 지 days_passed일이 지난 데이터의 마감 표기를 보정한다.
    '5일 남음' -> '3일 남음'(2일 경과), 마감일이 지났으면 None(제외)을 반환한다."""
    if days_passed <= 0 or not dday:
        return dday
    m = re.search(r'(\d+)\s*일\s*남음', dday)
    if m:
        remain = int(m.group(1)) - days_passed
        if remain < 0:
            return None
        return TODAY_LABEL if remain == 0 else f"{remain}일 남음"
    if "오늘" in dday:  # '오늘까지', '오늘마감' — 하루라도 지나면 마감
        return None
    return dday


# ---------------------------------------------------------------------------
# 지하철·철도역 이름 → 지역 (서울·경기). 지역 글자가 "사당역" 처럼 역 이름뿐일 때 쓴다.
# 데이터: crawler/data/capital_stations.json (OpenStreetMap 기반, tools/build_capital_stations.py 로 생성)
# ---------------------------------------------------------------------------
import json as _json
import os as _os

_STATION_PROVINCES = ("서울", "경기")      # 요청 범위: 서울·경기 (인천 등은 '기타'로 둔다)
_stations_cache = None


def _stations():
    global _stations_cache
    if _stations_cache is None:
        path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "data", "capital_stations.json")
        try:
            with open(path, encoding="utf-8") as f:
                _stations_cache = _json.load(f)
        except Exception:
            _stations_cache = {}
    return _stations_cache


def region_from_station(text: str, province_hint: str = ""):
    """'사당역', '릴스 구파발역', '고속터미널역(3,7,9호선)' 같은 글자에서 역 이름을 찾아 (시/도, 시/군/구) 를 돌려준다.
    province_hint 가 있으면 같은 시/도의 역만 인정한다. 못 찾으면 None."""
    table = _stations()
    if not table or not text:
        return None
    cleaned = re.sub(r"\(.*?\)", " ", text)                 # 괄호 안(노선 안내 등)은 버린다
    for token in re.split(r"[\s/·,]+", cleaned):
        if not token.endswith("역"):                          # '서울 신당동' 의 '서울' 이 서울역으로 오인되지 않게: 반드시 '…역' 형태만
            continue
        hit = table.get(token[:-1].strip())
        if not hit or hit[0] not in _STATION_PROVINCES:
            continue
        if province_hint and hit[0] != province_hint:
            continue
        return hit[0], hit[1]
    return None
