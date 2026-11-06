import re
import sys
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from playwright.async_api import async_playwright, BrowserContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helpers import normalize_reward, parse_region_from_title
from region_mapper import RegionMapper

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
_KST = timezone(timedelta(hours=9))

_CH_MAP = {
    "blog": "네이버 블로그",
    "instagram": "인스타그램 피드",
    "youtube": "유튜브 동영상",
    "reels": "인스타그램 릴스",
    "shorts": "유튜브 숏츠",
    "clip": "네이버 클립"
}

_REVU_URL_MAP = {
    "음식점": "맛집",
    "뷰티": "뷰티",
    "숙박": "숙박",
    "문화": "문화",
    "기타": "기타"
}


async def crawl(context: BrowserContext) -> List[Dict]:
    """레뷰 크롤링 (로그인 + response 인터셉터 + 동적 스크롤)"""
    print("[Revu] Starting crawl...")
    results = []

    # 계정 정보는 환경변수(GitHub Secrets)에서만 읽는다 — 코드에 적지 않음
    email = os.environ.get("REVU_EMAIL", "")
    password = os.environ.get("REVU_PASSWORD", "")
    if not email or not password:
        print("[Revu] REVU_EMAIL / REVU_PASSWORD 환경변수가 없어 레뷰 수집을 건너뜁니다")
        return results

    page = await context.new_page()

    # 1. 로그인
    try:
        print("[Revu] Logging in...")
        await page.goto("https://www.revu.net/login", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_selector('input[name="email"]', timeout=20000)
        await page.fill('input[name="email"]', email)
        await page.fill('input[name="password"]', password)
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
            await submit_btn.click()
        else:
            await page.get_by_text("로그인", exact=True).click()
        await page.wait_for_timeout(4000)
        print("[Revu] Login success")
    except Exception as e:
        print(f"[Revu] Login Error: {e}")
        await page.close()
        return results

    # 지역 메뉴 클릭
    try:
        print("[Revu] Accessing main page to click '지역'...")
        await page.goto("https://www.revu.net/", wait_until="domcontentloaded", timeout=60000)
        local_menu = page.locator("nav a, .navigation a, header a").filter(has_text="지역").first
        await local_menu.click()
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[Revu] Click '지역' Error: {e}")

    # 2. 응답 인터셉터
    async def handle_response(response):
        if "api.weble.net/v1/campaigns" in response.url and response.request.method == "GET":
            try:
                if response.ok:
                    data = await response.json()
                    if "items" in data and len(data["items"]) > 0:
                        for item in data["items"]:
                            try:
                                title = item.get("title") or item.get("item")
                                if not title: continue

                                # '방문형' 태그가 있거나, sido가 실제 지역(배송/재택 아님)이면 포함
                                cats = item.get("category", [])
                                sido = item.get("sido", "")
                                is_visit_type = "방문형" in cats
                                has_real_region = bool(sido) and sido not in ["재택", "배송", "배송형"]
                                if not (is_visit_type or has_real_region):
                                    continue

                                # 지역 파싱
                                try:
                                    parsed = parse_region_from_title(str(title))
                                    prov = parsed["province"]
                                    city = parsed["city"]
                                    if prov == "기타" and city == "기타":
                                        revu_sido = item.get("sido") or "기타"
                                        revu_area = item.get("area") or "기타"
                                        revu_region_str = f"{revu_sido} {revu_area}".strip()
                                        if revu_region_str != "기타 기타":
                                            fallback_parsed = RegionMapper.normalize(revu_region_str)
                                            if fallback_parsed["province"] != "기타": prov = fallback_parsed["province"]
                                            if fallback_parsed["city"] != "기타": city = fallback_parsed["city"]
                                except Exception:
                                    prov = item.get("sido") or "기타"
                                    city = item.get("area") or "기타"

                                region_data = {
                                    "province": prov,
                                    "city": city,
                                    "normalized": city if city != "기타" else prov
                                }

                                media = item.get("media", "")
                                type_ = _CH_MAP.get(media, "기타")

                                campaign_data = item.get("campaignData", {})
                                offer = campaign_data.get("reward") or item.get("offer", "상세페이지 참조")

                                stats = item.get("campaignStats", {})
                                applicants = stats.get("requestCount", 0)
                                quota = item.get("reviewerLimit", 0)
                                reward_value = normalize_reward(offer) if offer != "상세페이지 참조" else normalize_reward(title)

                                thumb = item.get("thumbnail", "")
                                campaign_id = item.get("id")
                                link = f"https://www.revu.net/campaign/{campaign_id}" if campaign_id else "https://www.revu.net/"

                                # D-day 계산
                                by_deadline = item.get("byDeadline")
                                request_ended_on = item.get("requestEndedOn", "")
                                if by_deadline is not None:
                                    dday = f"{by_deadline}일 남음"
                                elif request_ended_on:
                                    try:
                                        today = datetime.now(_KST).date()
                                        end_date = datetime.strptime(request_ended_on, "%Y-%m-%d").date()
                                        diff = (end_date - today).days
                                        dday = f"{diff}일 남음" if diff >= 0 else "마감"
                                    except Exception:
                                        dday = ""
                                else:
                                    dday = ""

                                res = {
                                    "platform": "레뷰", "title": str(title), "url": str(link),
                                    "region": region_data, "category": "추론중",
                                    "reward": {"text": str(offer)[:100], "value": reward_value},
                                    "meta": {"type": type_, "dday": dday},
                                    "image_url": str(thumb),
                                    "stats": {"applicants": int(applicants), "quota": int(quota)}
                                }
                                if not any(r['url'] == res['url'] for r in results):
                                    results.append(res)
                            except Exception as parse_e:
                                print(f"[Revu] Parse Item Error: {parse_e}")
            except Exception:
                pass

    page.on("response", handle_response)

    # 3. 카테고리 순회 + 동적 스크롤
    for cat_name, revu_path in _REVU_URL_MAP.items():
        print(f"[Revu] Crawling {cat_name} ({revu_path})...")
        try:
            start_count = len(results)
            try:
                await page.goto(f"https://www.revu.net/category/지역/{revu_path}", wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"[Revu] Goto ({revu_path}) Exception: {e}")

            prev_height = await page.evaluate("document.body.scrollHeight")
            no_change = 0
            for _ in range(150):
                await page.mouse.wheel(delta_x=0, delta_y=800)
                await page.wait_for_timeout(1500)
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == prev_height:
                    no_change += 1
                    if no_change >= 3:
                        print(f"[Revu] Reached bottom for {revu_path}")
                        break
                else:
                    no_change = 0
                    prev_height = new_height

            for r in results[start_count:]:
                r["category"] = cat_name

        except Exception as e:
            print(f"[Revu] Navigation Error on {cat_name}: {e}")

    await page.close()
    print(f"[Revu] Collected {len(results)} items")
    return results


async def run() -> List[Dict]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=_UA)
        try:
            return await crawl(context)
        finally:
            await browser.close()
