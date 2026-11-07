import re
import sys
import os
from typing import List, Dict
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, BrowserContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward, map_channel, parse_region_from_title
from category_mapper import SEOULOPPA_CATEGORY_MAP

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


BASE = "https://www.seoulouba.co.kr"
MAX_MORE_PAGES = 60          # "더보기" 요청 상한 (정상은 카테고리당 10회 안팎)

# "더보기" 버튼이 호출하는 주소: 36개씩 이어서 내려준다 (첫 화면은 192개만 보여줌)
_MORE_JS = """async ([cat, page, more]) => {
    const body = new URLSearchParams({cat, qq: '', q: '', q1: '', q2: '', ar1: '', ar2: '', sort: '', pt: '', page, more, rows: 36});
    const c = new AbortController();
    const t = setTimeout(() => c.abort(), 20000);
    try {
        const res = await fetch('/campaign/ajax/list.ajax.php', {
            method: 'POST',
            headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest'},
            body, signal: c.signal
        });
        return await res.text();
    } finally { clearTimeout(t); }
}"""


def _parse_item(item, mapped_category: str):
    """목록 항목 하나를 캠페인 dict 로 변환. 대상이 아니면 None"""
    title_node = item.select_one(".t_ttl a")
    if not title_node:
        return None
    title = title_node.get_text(strip=True)
    link = title_node.get('href', '')
    if link and not link.startswith('http'):
        link = f"{BASE}{link}"

    region_data = parse_region_from_title(title)

    type_node = item.select_one(".com_icon .icon_tag span")
    if type_node:
        tt = type_node.get_text(strip=True)
        if "배송형" in tt or "기자단" in tt or "구매평" in tt:
            return None

    reward_node = item.select_one(".t_basic .basic_blue")
    reward_text = reward_node.get_text(strip=True) if reward_node else ""
    reward_value = normalize_reward(reward_text)

    applicants = 0
    quota = 0
    recruit_node = item.select_one(".recruit span")
    if recruit_node:
        stats_match = re.search(r'신청\s*(\d+).*?모집\s*(\d+)', recruit_node.get_text(strip=True))
        if stats_match:
            applicants = int(stats_match.group(1))
            quota = int(stats_match.group(2))

    dday_node = item.select_one(".d_day span")
    dday = dday_node.get_text(strip=True) if dday_node else ""

    channel_alt = ""
    channel_node = item.select_one(".ltop_icon .icon_box img")
    if channel_node:
        channel_alt = channel_node.get('alt', '')
    type_ = map_channel(channel_alt, title)

    img_node = item.select_one(".tum_img img")
    img = img_node.get('src', '') if img_node else ""

    return {
        "platform": "서울오빠", "title": title, "url": link,
        "region": region_data, "category": mapped_category,
        "reward": {"text": reward_text, "value": reward_value},
        "meta": {"type": type_, "dday": dday},
        "image_url": img,
        "stats": {"applicants": applicants, "quota": quota}
    }


def _dday_of(item) -> str:
    node = item.select_one(".d_day span")
    return node.get_text(strip=True) if node else ""


async def crawl(context: BrowserContext) -> List[Dict]:
    """서울오빠 크롤링: 첫 화면(192개) + "더보기" 요청으로 이어 받기.
    목록은 진행 중 캠페인이 앞에, 마감된 캠페인이 뒤에 오므로 '전부 마감'인 페이지가 나오면 멈춘다."""
    print("[SeoulOppa] Starting crawl...")
    results: List[Dict] = []
    seen_urls = set()
    page = await context.new_page()

    def add(items, mapped_category: str) -> int:
        """항목들을 결과에 추가하고, 이 묶음에서 마감되지 않은 항목 수를 돌려준다"""
        active = 0
        for item in items:
            try:
                if _dday_of(item) != "마감":
                    active += 1
                parsed = _parse_item(item, mapped_category)
                if parsed and parsed["url"] not in seen_urls:
                    seen_urls.add(parsed["url"])
                    results.append(parsed)
            except Exception as e:
                print(f"[SeoulOppa] Item Parse Error: {e}")
        return active

    try:
        for cat_code, mapped_category in SEOULOPPA_CATEGORY_MAP.items():
            print(f"[SeoulOppa] Crawling {mapped_category} (cat: {cat_code})...")
            url = f"{BASE}/campaign/?cat={cat_code}"
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_selector(".campaign_content", timeout=30000)

                soup = BeautifulSoup(await page.content(), 'html.parser')
                first_items = soup.select(".campaign_content")
                add(first_items, mapped_category)
                loaded = len(first_items)
                more_pages = 0

                # 첫 화면이 가득 차 있을 때만 이어 받는다 (가득 차지 않았으면 이게 전부)
                if loaded >= 192:
                    for page_no in range(2, 2 + MAX_MORE_PAGES):
                        html = await page.evaluate(_MORE_JS, [cat_code, page_no, loaded])
                        items = BeautifulSoup(html, 'html.parser').select(".campaign_content")
                        if not items:
                            break
                        more_pages += 1
                        loaded += len(items)
                        if add(items, mapped_category) == 0:
                            break   # 이 묶음이 전부 마감 → 이후는 모두 마감
                print(f"[SeoulOppa] {mapped_category}: 화면 {len(first_items)}개 + 더보기 {more_pages}회 → 누적 {len(results)}건")
            except Exception as inner_e:
                print(f"[SeoulOppa] Category {cat_code} Crawl Error: {inner_e}")
                continue

    except Exception as e:
        print(f"[SeoulOppa] Error: {e}")
    finally:
        await page.close()

    print(f"[SeoulOppa] Collected {len(results)} items")
    return results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
