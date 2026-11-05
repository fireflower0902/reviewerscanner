"""포블로그 크롤러 (브라우저 불필요 — 목록 API 직접 호출)

포블로그는 Cloudflare 봇 방어가 있어 GitHub Actions(데이터센터 IP)에서는 첫 30건 이후의
'더 불러오기' 요청(loadMoreDataCategoryV2)이 403으로 거부된다. 한국 가정용 IP인 기기(Mac 등)에서
run_local_sources.py로 실행하고, 결과는 R2의 부분 파일로 올려 GitHub의 aggregator가 합친다.
"""
import sys
import os
import re
import html
import asyncio
from typing import List, Dict
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward
from region_mapper import RegionMapper
from category_mapper import extract_category_by_keyword

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://4blog.net"
API_URL = f"{BASE_URL}/loadMoreDataCategoryV2"
IMG_BASE = "https://d3oxv6xcx9d0j1.cloudfront.net/public/pr"
CATEGORIES = "coupon,blog,instar21,reels,youtube21,shorts,tiktok,threads,ncafe,naverclip,danggeun,xtwitter,etc"
PAGE_SIZE = 30
MAX_OFFSET = 6000          # 안전 상한 (정상 종료는 빈 응답)
REQUEST_TIMEOUT = 20
MAX_CONSECUTIVE_ERRORS = 3

# API의 CATEGORY 값 → 표준 채널명
_CHANNEL_MAP = {
    "blog": "네이버 블로그",
    "instar21": "인스타그램 피드",
    "reels": "인스타그램 릴스",
    "youtube21": "유튜브 동영상",
    "shorts": "유튜브 숏츠",
    "naverclip": "네이버 클립",
}


class Unreachable(Exception):
    """사이트가 이 네트워크에서 연속으로 거부/무응답일 때(차단 추정)"""


def _dday_text(remain) -> str:
    if remain is None:
        return ""
    try:
        n = int(remain)
    except (TypeError, ValueError):
        return ""
    return "오늘마감" if n <= 0 else f"{n}일 남음"


def _clean(text: str, limit: int = 150) -> str:
    """API 문구 정리: HTML 문자(&gt; 등) 변환, 줄바꿈/연속 공백을 한 칸으로, 너무 길면 자르기"""
    text = html.unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def parse_item(it: Dict) -> Dict:
    location = _clean(it.get("LOCATION_NM"))      # 예: "[시흥시/배곧동]"
    name = _clean(it.get("CAMPAIGN_NM"), limit=200)
    title = f"{location} {name}".strip()
    if not title:
        return {}

    region_match = re.search(r"\[(.*?)\]", location) or re.match(r"^\[(.*?)\]", name)
    raw_region = region_match.group(1) if region_match else title[:5]
    region_data = RegionMapper.normalize(raw_region)

    offer = _clean(it.get("REVIEWER_BENEFIT")) or "상세페이지 참조"
    reward_value = normalize_reward(offer) or normalize_reward(title)

    img = ""
    if it.get("PRID") and it.get("IMGKEY"):
        img = f"{IMG_BASE}/{it['PRID']}/thumbnail/{it['IMGKEY']}"

    return {
        "platform": "포블로그", "title": title, "url": f"{BASE_URL}/campaign/{it['CID']}/",
        "region": region_data, "category": extract_category_by_keyword(title, offer[:80]),  # 긴 문구의 잡다한 단어가 분류를 흐리지 않게 앞부분만
        "reward": {"text": offer, "value": reward_value},
        "meta": {"type": _CHANNEL_MAP.get(it.get("CATEGORY"), "기타"), "dday": _dday_text(it.get("REMAINDATE"))},
        "image_url": img,
        # 추정 매핑: REVIEWER_REQ_CNT=신청자 수, REVIEWER_CNT=모집 인원 (화면과 직접 대조하지는 못함)
        "stats": {"applicants": int(it.get("REVIEWER_REQ_CNT") or 0), "quota": int(it.get("REVIEWER_CNT") or 0)},
    }


def collect() -> List[Dict]:
    """포블로그 방문형 전체 수집 (동기). 연속 실패하면 Unreachable을 던진다."""
    session = requests.Session()
    session.headers.update({"User-Agent": _UA, "Referer": f"{BASE_URL}/list/{CATEGORIES}/local"})

    results: List[Dict] = []
    seen = set()
    errors = 0
    offset = 0
    while offset <= MAX_OFFSET:
        params = {"offset": offset, "limit": PAGE_SIZE, "category": CATEGORIES, "sort": "recommend", "category1": "local"}
        try:
            resp = session.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                raise requests.HTTPError(f"HTTP {resp.status_code}")
            page = resp.json()
            errors = 0
        except (requests.RequestException, ValueError) as e:
            errors += 1
            print(f"  [4Blog] Error offset={offset}: {type(e).__name__} {e}")
            if errors >= MAX_CONSECUTIVE_ERRORS:
                raise Unreachable(f"연속 {errors}회 요청 실패 — 이 네트워크에서는 목록 API를 받을 수 없습니다")
            continue

        if not page:
            break
        for it in page:
            try:
                parsed = parse_item(it)
            except Exception:
                continue
            if parsed and parsed["url"] not in seen:
                seen.add(parsed["url"])
                results.append(parsed)
        offset += PAGE_SIZE

    print(f"[4Blog] Collected {len(results)} items")
    return results


async def run() -> List[Dict]:
    return await asyncio.to_thread(collect)
