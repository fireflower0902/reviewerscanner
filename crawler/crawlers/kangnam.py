"""강남맛집 크롤러 (브라우저 불필요 — requests만 사용)

강남맛집은 GitHub Actions(해외 IP)에서 접속이 차단된다(연결 자체가 안 맺어짐).
그래서 한국 IP 기기(Mac 등)에서 run_kangnam.py로 실행하고, 결과는 R2의 부분 파일로 올려
GitHub Actions의 aggregator가 합친다.
"""
import re
import sys
import os
import asyncio
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward, map_channel
from region_mapper import RegionMapper
from category_mapper import GANGNAM_CATEGORY_MAP

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "https://xn--939au0g4vj8sq.net"
API_URL = f"{BASE_URL}/theme/go/_list_cmp_tpl.php"
REQUEST_TIMEOUT = 20          # 초
MAX_CONSECUTIVE_ERRORS = 3    # 연속 실패 시 접속 불가로 판단하고 중단
MAX_PAGES = 60

REGIONS = [
    {"name": "서울", "loca_prt": "서울", "local_1": "전체", "local_2": "서울"},
    {"name": "경기/인천", "loca_prt": "경기-인천", "local_1": "전체", "local_2": "경기|인천"},
    {"name": "대전/충청", "loca_prt": "대전-세종-충청", "local_1": "전체", "local_2": "대전|세종|충청"},
    {"name": "부산/경남", "loca_prt": "부산-경남", "local_1": "전체", "local_2": "부산|경남"},
    {"name": "대구/경북", "loca_prt": "대구-경북", "local_1": "전체", "local_2": "대구|경북"},
    {"name": "광주/전라", "loca_prt": "광주-전라", "local_1": "전체", "local_2": "광주|전라"},
    {"name": "강원", "loca_prt": "강원", "local_1": "전체", "local_2": "강원"},
    {"name": "제주", "loca_prt": "제주", "local_1": "전체", "local_2": "제주"},
]


class Unreachable(Exception):
    """사이트에 연속으로 접속하지 못할 때(차단/장애)"""


def parse_items(html_fragment: str, mapped_category: str) -> List[Dict]:
    """목록 API 응답(HTML 조각)에서 캠페인 목록을 추출"""
    soup = BeautifulSoup(html_fragment, "html.parser")
    results = []
    for item in soup.select("li.list_item"):
        try:
            title_node = item.select_one("dt.tit a")
            if not title_node:
                continue
            title = title_node.get_text(strip=True)
            link_href = title_node.get("href")
            link = link_href if link_href.startswith("http") else BASE_URL + link_href

            raw_region_match = re.match(r"^\[(.*?)\]", title)
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
                if label_node.select_one("em.blog"):
                    raw_type = "블로그"
                elif label_node.select_one("em.insta"):
                    raw_type = "인스타그램"
                elif label_node.select_one("em.youtube") or label_node.select_one("em.yt"):
                    raw_type = "유튜브"
                elif label_node.select_one("em.clip"):
                    raw_type = "클립"
                else:
                    raw_type = label_node.get_text(strip=True)
            type_ = map_channel(raw_type, title)

            img_node = item.select_one("img.thumb_img")
            img = img_node.get("src") if img_node else ""
            if img and img.startswith("//"):
                img = "https:" + img

            applicants = 0
            quota = 0
            info_node = item.select_one("p.item_info span.numb")
            if info_node:
                stats_match = re.search(r"신청\s*(\d+).*?모집\s*(\d+)", info_node.get_text(strip=True))
                if stats_match:
                    applicants = int(stats_match.group(1))
                    quota = int(stats_match.group(2))

            results.append({
                "platform": "강남맛집", "title": title, "url": link,
                "region": region_data, "category": mapped_category,
                "reward": {"text": reward_text, "value": reward_value},
                "meta": {"type": type_, "dday": dday},
                "image_url": img,
                "stats": {"applicants": applicants, "quota": quota},
            })
        except Exception:
            continue
    return results


def _post_list(session: requests.Session, form: Dict) -> Optional[str]:
    """목록 API 호출. 일시 오류는 1회 재시도하고, 그래도 실패하면 예외를 던진다."""
    last_error = None
    for _ in range(2):
        try:
            resp = session.post(API_URL, data=form, timeout=REQUEST_TIMEOUT)
            if resp.status_code != 200:
                print(f"  [Gangnam] API Status {resp.status_code}")
                return None
            return resp.text
        except requests.RequestException as e:
            last_error = e
    raise last_error


def collect() -> List[Dict]:
    """강남맛집 전체 수집 (동기). 접속 불가가 반복되면 Unreachable을 던진다."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": _UA,
        "Referer": f"{BASE_URL}/cp/?ca=20",
        "Origin": BASE_URL,
        "X-Requested-With": "XMLHttpRequest",
    })

    results: List[Dict] = []
    seen_urls = set()
    consecutive_errors = 0

    for ca_code, mapped_category in GANGNAM_CATEGORY_MAP.items():
        for region in REGIONS:
            print(f"[Gangnam] Crawling {mapped_category} (Region: {region['name']})...")
            for page_num in range(1, MAX_PAGES + 1):
                form = {
                    "ca": ca_code,
                    "loca_prt": region["loca_prt"],
                    "local_1": region["local_1"],
                    "local_2": region["local_2"],
                    "rpage": str(page_num),
                    "row_num": "20",
                }
                try:
                    html_fragment = _post_list(session, form)
                    consecutive_errors = 0
                except requests.RequestException as e:
                    consecutive_errors += 1
                    print(f"  [Gangnam] Error page {page_num}: {type(e).__name__}")
                    if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                        raise Unreachable(f"연속 {consecutive_errors}회 접속 실패 — 이 네트워크에서는 접속할 수 없습니다")
                    break

                if not html_fragment or len(html_fragment) < 50:
                    break
                items = parse_items(html_fragment, mapped_category)
                if not items:
                    break
                for it in items:
                    if it["url"] not in seen_urls:
                        seen_urls.add(it["url"])
                        results.append(it)

    print(f"[Gangnam] Collected {len(results)} items")
    return results


async def run() -> List[Dict]:
    return await asyncio.to_thread(collect)
