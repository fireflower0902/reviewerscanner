import asyncio
import json
from playwright.async_api import async_playwright

REVU_CATEGORY_URLS = {
    "음식점": "food",
    "뷰티": "beauty",
    "숙박": "stay",
    "문화": "culture",
    "기타": "life"
}

# 레뷰의 경우 지역정보는 API 응답의 sido, area 로 들어옴 (예: 서울, 강남구)

async def crawl_revu(context):
    print("[Revu] Starting crawl...")
    results = []
    
    page = await context.new_page()
    
    # 1. 로그인
    try:
        print("[Revu] Logging in...")
        await page.goto("https://www.revu.net/login", wait_until="networkidle")
        await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
        await page.fill('input[name="password"]', 'Dkssuddy1!')
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
            await submit_btn.click()
        else:
            await page.get_by_text("로그인", exact=True).click()
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[Revu] Login Error: {e}")
        await page.close()
        return results

    # 2. JSON 응답 수집기 설정
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
                                
                                # Category 매핑
                                raw_cat = item.get("category", [])
                                category = "기타"
                                
                                sido = item.get("sido") or "기타"
                                area = item.get("area") or "기타"
                                
                                # 1. 제목에서 파싱 시도
                                try:
                                    from aggregator import parse_region_from_title
                                    import sys
                                    if 'RegionMapper' not in sys.modules:
                                        from region_mapper import RegionMapper
                                    
                                    parsed = parse_region_from_title(str(title))
                                    prov = parsed["province"]
                                    city = parsed["city"]
                                    
                                    # 제목 파싱에서 city를 못 찾았을 경우, 레뷰 API의 sido/area를 사용해 다시 정규화
                                    if city == "기타":
                                        revu_region_str = f"{sido} {area}".strip()
                                        fallback_parsed = RegionMapper.normalize(revu_region_str)
                                        # fallback에서 찾은 prov/city가 있다면 그것을 사용. 없다면 sido/area 원본이나 기타 유지
                                        prov = fallback_parsed["province"] if fallback_parsed["province"] != "기타" else sido
                                        city = fallback_parsed["city"] if fallback_parsed["city"] != "기타" else area
                                        
                                except ImportError:
                                    prov = sido
                                    city = area
                                
                                region_data = {
                                    "province": prov,
                                    "city": city,
                                    "normalized": city if city != "기타" else prov
                                }
                                
                                media = item.get("media", "")
                                ch_map = {
                                    "blog": "네이버 블로그",
                                    "instagram": "인스타그램 피드",
                                    "youtube": "유튜브 동영상",
                                    "reels": "인스타그램 릴스",
                                    "shorts": "유튜브 숏츠",
                                    "clip": "네이버 클립"
                                }
                                type_ = ch_map.get(media, "기타")
                                
                                offer = item.get("offer", "상세페이지 참조")
                                
                                stats = item.get("campaignStats", {})
                                applicants = stats.get("requestCount", 0)
                                quota = item.get("reviewerLimit", 0)
                                
                                thumb = item.get("thumbnail", "")
                                
                                campaign_id = item.get("id")
                                link = f"https://www.revu.net/campaign/detail/{campaign_id}" if campaign_id else "https://www.revu.net/"
                                
                                res = {
                                    "platform": "레뷰",
                                    "title": title,
                                    "url": link,
                                    "region": region_data,
                                    "category": "추론중", # URL 순회 루프에서 할당
                                    "reward": {"text": offer, "value": 0},
                                    "meta": {"type": type_, "dday": ""}, # dday는 남은 일자 계산 필요
                                    "image_url": thumb,
                                    "stats": {"applicants": applicants, "quota": quota}
                                }
                                # 중복 방지 (여러 API 덤프 시 겹칠 수 있음)
                                if not any(r['url'] == res['url'] for r in results):
                                    results.append(res)
                            except Exception as parse_e:
                                print(f"[Revu] Parse Item Error: {parse_e}")
            except Exception as e:
                pass

    page.on("response", handle_response)
    
    # 3. 각 카테고리 순회하며 네트워크 응답 받기
    for cat_name, revu_path in REVU_CATEGORY_URLS.items():
        print(f"[Revu] Crawling {cat_name} ({revu_path})...")
        try:
            start_count = len(results)
            await page.goto(f"https://www.revu.net/campaign/local/{revu_path}/all", wait_until="networkidle")
            await page.wait_for_timeout(2000)
            
            # 스크롤 2번 정도 해서 추가 데이터 불려오기 유도
            for _ in range(2):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
            
            # 방금 추가된 애들에게 카테고리 일괄 부여
            for r in results[start_count:]:
                r["category"] = cat_name
                
        except Exception as e:
            print(f"[Revu] Navigation Error on {cat_name}: {e}")
            
    await page.close()
    print(f"[Revu] Total Collected: {len(results)}")
    return results

async def test_run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        res = await crawl_revu(context)
        print("Sample 3 Items:")
        for r in res[:3]:
             print(json.dumps(r, ensure_ascii=False, indent=2))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_run())
