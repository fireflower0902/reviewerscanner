import re
import asyncio
import sys
import os
from typing import List, Dict
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, BrowserContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward, map_channel, parse_region_from_title
from category_mapper import DINNERQUEEN_CATEGORY_MAP

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


_LIST_URL = ("https://dinnerqueen.net/taste/taste_list?ct=&area1=%EC%A0%84%EA%B5%AD"
             "&area2=%EC%A0%84%EC%B2%B4&page={page}&ctype=&query=")
_MAX_PAGES = 300          # 안전 상한 (페이지당 30건, has_next로 정상 종료)


# 카드 뱃지 → 표준 카테고리 / 제외 대상
_BADGE_CATEGORY = {"맛집": "음식점", "여가": "레저", "뷰티": "뷰티", "배달": "배달"}
_EXCLUDED_BADGES = {"배송", "기자단"}


def _parse_card(item) -> Dict:
    link_node = item.select_one("a.qz-dq-card__link")
    link = link_node.get('href', '') if link_node else ""
    if link and not link.startswith('http'):
        link = f"https://dinnerqueen.net{link}"
    title = link_node.get('title', '').replace(' 신청하기', '') if link_node else ""
    if not title:
        return {}

    # 카드 상단 뱃지: [채널(릴스/클립)] + 분류(맛집/여가/뷰티/배달/배송/기자단...) + (포인트).
    # 채널 뱃지가 없으면 일반 네이버 블로그 캠페인이다.
    badges = [b.get_text(strip=True) for b in item.select(".qz-dq-card__badge-row strong")]
    if any(b in _EXCLUDED_BADGES for b in badges):
        return {}   # 배송형/기자단은 방문형이 아니라 다른 사이트와 동일하게 제외
    if "릴스" in badges:
        channel = "인스타그램 릴스"
    elif "클립" in badges:
        channel = "네이버 클립"
    else:
        channel = "네이버 블로그" if badges else map_channel("", title)
    category = next((_BADGE_CATEGORY[b] for b in badges if b in _BADGE_CATEGORY), "기타")

    applicants = 0
    quota = 0
    text_content = item.get_text(separator=' ', strip=True)
    stats_match = re.search(r'신청\s*([\d,]+)\s*/\s*([\d,]+)', text_content)
    if stats_match:
        applicants = int(stats_match.group(1).replace(',', ''))
        quota = int(stats_match.group(2).replace(',', ''))

    # 카드 텍스트의 "N 일 남음" / "오늘까지" (strong 태그는 맛집/릴스 같은 라벨이라 사용 불가)
    dday = ""
    dday_match = re.search(r'(\d+)\s*일\s*남음', text_content)
    if dday_match:
        dday = f"{dday_match.group(1)}일 남음"
    elif "오늘까지" in text_content:
        dday = "오늘까지"
    elif "마감" in text_content:
        dday = "마감"
    img_node = item.select_one(".qz-dq-card__link__img img")
    img = img_node.get('src', '') if img_node else ""

    # 제공내역은 카드 서브텍스트에 있음 (상세페이지 '제공 내역'과 동일 — 상세 요청은 서버가 느려 사용하지 않음)
    offer_node = item.select_one("p.qz-caption-kr.color-placeholder")
    offer = offer_node.get_text(strip=True) if offer_node else ""
    reward_value = normalize_reward(offer) or normalize_reward(title)

    return {
        "platform": "디너의여왕", "title": title, "url": link,
        "region": parse_region_from_title(title),
        "category": category,
        "reward": {"text": offer or "상세페이지 참조", "value": reward_value},
        "meta": {"type": channel, "dday": dday},
        "image_url": img,
        "stats": {"applicants": applicants, "quota": quota},
    }


async def crawl(context: BrowserContext) -> List[Dict]:
    """디너의여왕 크롤링 (목록 API 페이지네이션)

    - 목록: POST /taste/taste_list?page=N → {"layout": html, "has_next": bool}
    - 제공내역/D-day/신청수 모두 목록 카드에서 파싱 (상세 요청 불필요)
    """
    print("[DinnerQueen] Starting crawl...")
    results: List[Dict] = []
    seen = set()
    headers = {"X-Requested-With": "XMLHttpRequest", "Referer": "https://dinnerqueen.net/taste"}

    try:
        await context.request.get("https://dinnerqueen.net/taste")  # 쿠키 확보

        for page_no in range(1, _MAX_PAGES + 1):
            data = None
            for _ in range(3):  # 일시 오류 재시도
                try:
                    resp = await context.request.post(_LIST_URL.format(page=page_no), headers=headers, timeout=20000)
                    if resp.ok:
                        data = await resp.json()
                        break
                except Exception:
                    pass
                await asyncio.sleep(1)
            if not data:
                print(f"[DinnerQueen] List page {page_no} failed. Stopping.")
                break

            soup = BeautifulSoup(data.get("layout", ""), 'html.parser')
            for card in soup.select(".qz-dq-card"):
                try:
                    parsed = _parse_card(card)
                except Exception:
                    continue
                if parsed and parsed["url"] not in seen:
                    seen.add(parsed["url"])
                    results.append(parsed)

            if page_no % 10 == 0:
                print(f"  [DinnerQueen] Page {page_no}: {len(results)} items")
            if not data.get("has_next"):
                break

        print(f"[DinnerQueen] List parsed: {len(results)} items")

    except Exception as e:
        print(f"[DinnerQueen] Error: {e}")

    no_offer = sum(1 for r in results if r["reward"]["text"] == "상세페이지 참조")
    print(f"[DinnerQueen] Collected {len(results)} items ({no_offer} without offer text)")
    return results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
