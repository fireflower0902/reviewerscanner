import asyncio
import re
import json
from playwright.async_api import async_playwright, Page, BrowserContext
from typing import List, Dict
from bs4 import BeautifulSoup
try:
    from crawler.region_mapper import RegionMapper
    from crawler.category_mapper import GANGNAM_CATEGORY_MAP, REVIEWPLACE_CATEGORY_MAP, REVIEWNOTE_CATEGORY_MAP, DINNERQUEEN_CATEGORY_MAP, SEOULOPPA_CATEGORY_MAP, extract_category_by_keyword
except ImportError:
    from region_mapper import RegionMapper
    from category_mapper import GANGNAM_CATEGORY_MAP, REVIEWPLACE_CATEGORY_MAP, REVIEWNOTE_CATEGORY_MAP, DINNERQUEEN_CATEGORY_MAP, SEOULOPPA_CATEGORY_MAP, extract_category_by_keyword

# ==============================================================================
# [Configuration]
# ==============================================================================
OUTPUT_FILE = "public/campaigns.json"
MAX_CONCURRENT_PAGES = 5  # 너무 많이 띄우면 차단될 수 있음

# ==============================================================================
# [Helper] Common Utilities
# ==============================================================================
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
    """기존 채널 문자열과 제목을 받아 6종 채널 포맷으로 정규화하는 함수"""
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
        # 기본적으로 숏폼이 특정 플랫폼과 명시 안되어있으면 우선 확인 (클립은 네이버 숏폼)
        return "네이버 클립"
        
    return "기타"

def parse_region_from_title(title: str) -> dict:
    """[클립][강남] 처럼 다중 괄호가 있을 때 올바른 지역을 추출하기 위한 헬퍼"""
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

# ==============================================================================
# [Crawler 1] 강남맛집 (Gangnam Matjib)
# ==============================================================================
async def scroll_to_bottom(page: Page, max_scrolls: int = 50):
    """Common infinite scroll helper"""
    previous_height = await page.evaluate("document.body.scrollHeight")
    
    for i in range(max_scrolls):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2) # Wait for load
        
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            # Try once more to be sure
            await asyncio.sleep(2)
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                print(f"  [Scroll] Reached bottom at scroll {i+1}")
                break
        
        previous_height = new_height
        if (i+1) % 10 == 0:
            print(f"  [Scroll] {i+1} times...")

async def crawl_kangnam(context: BrowserContext) -> List[Dict]:
    """강남맛집 크롤링 (API-based Infinite Scroll)"""
    # Define regions to crawl (Top-level regions)
    # Using internal API: https://xn--939au0g4vj8sq.net/theme/go/_list_cmp_tpl.php
    # Params: ca=20, loca_prt=..., local_1=..., local_2=..., rpage=N
    
    regions = [
        {"name": "서울", "loca_prt": "서울", "local_1": "전체", "local_2": "서울"},
        {"name": "경기/인천", "loca_prt": "경기-인천", "local_1": "전체", "local_2": "경기|인천"},
        {"name": "대전/충청", "loca_prt": "대전-세종-충청", "local_1": "전체", "local_2": "대전|세종|충청"},
        {"name": "부산/경남", "loca_prt": "부산-경남", "local_1": "전체", "local_2": "부산|경남"},
        {"name": "대구/경북", "loca_prt": "대구-경북", "local_1": "전체", "local_2": "대구|경북"},
        {"name": "광주/전라", "loca_prt": "광주-전라", "local_1": "전체", "local_2": "광주|전라"},
        {"name": "강원", "loca_prt": "강원", "local_1": "전체", "local_2": "강원"},
        {"name": "제주", "loca_prt": "제주", "local_1": "전체", "local_2": "제주"}
    ]
    
    # 외부 모듈 GANGNAM_CATEGORY_MAP 사용
    all_results = []
    api_url = "https://xn--939au0g4vj8sq.net/theme/go/_list_cmp_tpl.php"
    
    # Create a page in context to ensure headers/cookies are managed, 
    # though context.request is also fine. We'll use page.request for simplicity with headers.
    page = await context.new_page()
    
    # Pre-visit main page to set session/cookies
    try:
        await page.goto("https://xn--939au0g4vj8sq.net/cp/?ca=20", wait_until="domcontentloaded")
    except: pass

    try:
        for ca_code, mapped_category in GANGNAM_CATEGORY_MAP.items():
            for region in regions:
                print(f"[Gangnam] Crawling {mapped_category} (Region: {region['name']})...")
                
                # Pagination loop
                # Try up to 50 pages (approx 1000 items per region max)
                for page_num in range(1, 61): 
                    # Construct form data
                    form_data = {
                        "ca": ca_code,
                        "loca_prt": region['loca_prt'],
                        "local_1": region['local_1'],
                        "local_2": region['local_2'],
                        "rpage": str(page_num),
                        "row_num": "20" # Request 20 items (default seems to be 20)
                    }
                    
                    try:
                        response = await page.request.post(api_url, form=form_data)
                        
                        if not response.ok:
                            print(f"  [Gangnam] API Status {response.status} at {region['name']} p{page_num}")
                            break
                            
                        html_fragment = await response.text()
                        
                        if not html_fragment or len(html_fragment) < 50:
                            # Empty response means end of list
                            # print(f"  [Gangnam] End of list for {region['name']} at page {page_num}")
                            break
                            
                        soup = BeautifulSoup(html_fragment, 'html.parser')
                        soup_items = soup.select("li.list_item")
                        
                        if not soup_items: 
                            break

                        for item in soup_items:
                            try:
                                title_node = item.select_one("dt.tit a")
                                if not title_node: continue
                                title = title_node.get_text(strip=True)
                                link_href = title_node.get('href')
                                if not link_href.startswith('http'): link = "https://xn--939au0g4vj8sq.net" + link_href
                                else: link = link_href
                                
                                # Region Logic
                                raw_region_match = re.match(r'^\[(.*?)\]', title)
                                raw_region = raw_region_match.group(1) if raw_region_match else title[:5]
                                region_data = RegionMapper.normalize(raw_region)
                                
                                # Reward
                                sub_tit = item.select_one("dd.sub_tit")
                                reward_text = sub_tit.get_text(strip=True) if sub_tit else ""
                                reward_value = normalize_reward(reward_text)
                                
                                # Meta
                                dday_node = item.select_one("span.dday")
                                dday = dday_node.get_text(strip=True) if dday_node else ""
                                
                                # Channel
                                label_node = item.select_one("span.label")
                                raw_type = ""
                                if label_node:
                                    if label_node.select_one("em.blog"): raw_type = "블로그"
                                    elif label_node.select_one("em.insta"): raw_type = "인스타그램"
                                    elif label_node.select_one("em.youtube") or label_node.select_one("em.yt"): raw_type = "유튜브"
                                    elif label_node.select_one("em.clip"): raw_type = "클립"
                                    else:
                                        raw_type = label_node.get_text(strip=True)
                                
                                type_ = map_channel(raw_type, title)
                                
                                # Use exact category from source! (Fallback to extract_category if needed, but not needed here)
                                category = mapped_category

                                img_node = item.select_one("img.thumb_img")
                                img = img_node.get('src') if img_node else ""
                                if img and img.startswith('//'): img = "https:" + img

                                # 7. Stats (Applicants / Quota)
                                applicants = 0
                                quota = 0
                                info_node = item.select_one("p.item_info span.numb")
                                if info_node:
                                    info_text = info_node.get_text(strip=True) # e.g. "신청 54 / 모집 20"
                                    stats_match = re.search(r'신청\s*(\d+).*?모집\s*(\d+)', info_text)
                                    if stats_match:
                                        applicants = int(stats_match.group(1))
                                        quota = int(stats_match.group(2))

                                all_results.append({
                                    "platform": "강남맛집",
                                    "title": title,
                                    "url": link,
                                    "region": region_data,
                                    "category": category,
                                    "reward": {"text": reward_text, "value": reward_value},
                                    "meta": {"type": type_, "dday": dday},
                                    "image_url": img,
                                    "stats": {"applicants": applicants, "quota": quota}
                                })
                            except Exception: continue
                        
                    except Exception as e:
                        print(f"  [Gangnam] Error page {page_num}: {e}")
                        break
        
    except Exception as e:
        print(f"[Gangnam] Critical Error: {e}")
    finally:
        await page.close()
        
    print(f"[Gangnam] Collected {len(all_results)} items")
    return all_results

# ==============================================================================
# [Crawler 2] 리뷰플레이스 (Review Place)
# ==============================================================================
async def crawl_reviewplace(context: BrowserContext) -> List[Dict]:
    """리뷰플레이스 크롤링 (API Pagination)"""
    # API Direct Call using playwright request context (or just page.request)
    # Since we are already in playwright async context.
    
    results = []
    base_url = "https://www.reviewplace.co.kr/theme/rp/_ajax_cmp_list_tpl.php"
    
    # 외부 모듈 REVIEWPLACE_CATEGORY_MAP 사용
    try:
        page = await context.new_page()
        await page.goto("https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD", wait_until="domcontentloaded")
        
        print(f"[ReviewPlace] Starting API Crawl by Category...")
        
        for ct2_val, mapped_category in REVIEWPLACE_CATEGORY_MAP.items():
            print(f"[ReviewPlace] Crawling {mapped_category} (ct2: {ct2_val})...")
            
            import urllib.parse
            encoded_ct2 = urllib.parse.quote(ct2_val)
            
            page_num = 0
            max_pages = 30 # 지역+카테고리별 최대 30페이지 정도면 충분 (30*30 = 900개)
            
            while page_num < max_pages:
                page_num += 1
                
                try:
                    js_code = f"""async () => {{
                        const response = await fetch('{base_url}?ct1=%EC%A7%80%EC%97%AD&ct2={encoded_ct2}&rpage={page_num}&device=pc', {{
                            method: 'GET',
                            headers: {{ 'Referer': 'https://www.reviewplace.co.kr/pr/?ct1=%EC%A7%80%EC%97%AD' }}
                        }});
                        return await response.text();
                    }}"""
                    
                    html_content = await page.evaluate(js_code)
                
                    if not html_content or len(html_content) < 100:
                        # Empty or too short
                        print(f"[ReviewPlace] Empty response at page {page_num}. Stopping.")
                        break
                        
                    soup = BeautifulSoup(html_content, 'html.parser')
                    items = soup.select(".item")
                    
                    if not items:
                        print(f"[ReviewPlace] No items at page {page_num}. Stopping.")
                        break
                    
                    for item in items:
                        try:
                            # 1. Title & URL
                            title_node = item.select_one(".tit")
                            if not title_node: continue
                            title = title_node.get_text(strip=True)
                            
                            link_node = item.select_one("a")
                            link = link_node.get('href') if link_node else ""
                            if link and not link.startswith('http'): 
                                link = f"https://www.reviewplace.co.kr{link}"

                            # 2. Region Logic
                            region_match = re.match(r'^\[(.*?)\]', title)
                            if region_match:
                                raw_region = region_match.group(1)
                                region_data = RegionMapper.normalize(raw_region)
                            else:
                                region_data = RegionMapper.normalize(title[:5])

                            # 3. Reward
                            reward_node = item.select_one(".txt")
                            reward_text = reward_node.get_text(strip=True) if reward_node else ""
                            reward_value = normalize_reward(reward_text)

                            # 4. Meta & Channel Detection
                            raw_type = ""
                            icon_nodes = item.select("div[class*='icon'], span[class*='icon'], i[class*='icon']")
                            for node in icon_nodes:
                                cls = " ".join(node.get("class", []))
                                if "blog" in cls: raw_type = "블로그"; break
                                if "insta" in cls: raw_type = "인스타그램"; break
                                if "youtube" in cls: raw_type = "유튜브"; break 
                                
                            type_ = map_channel(raw_type, title)
                            
                            # Use exact mapped category
                            category = mapped_category

                            dday_node = item.select_one(".date_wrap .date")
                            dday_text = dday_node.get_text(strip=True) if dday_node else ""
                            dday = dday_text.replace(" ", "") if dday_text else ""

                            # 5. Image
                            img_node = item.select_one("img.thumbimg")
                            img = img_node.get('src') if img_node else ""
                            if img and not img.startswith('http'):
                                 img = f"https{img}" if img.startswith('//') else f"https://www.reviewplace.co.kr{img}"

                            # 6. Stats (Applicants / Quota)
                            applicants = 0
                            quota = 0
                            info_node = item.select_one(".item_info")
                            if info_node:
                                info_text = info_node.get_text(strip=True) # e.g. "신청 0 / 10명"
                                stats_match = re.search(r'신청\s*(\d+).*?(\d+)\s*명', info_text)
                                if stats_match:
                                    applicants = int(stats_match.group(1))
                                    quota = int(stats_match.group(2))

                            results.append({
                                "platform": "리뷰플레이스",
                                "title": title,
                                "url": link,
                                "region": region_data,
                                "category": category,
                                "reward": {"text": reward_text, "value": reward_value},
                                "meta": {"type": type_, "dday": dday},
                                "image_url": img,
                                "stats": {"applicants": applicants, "quota": quota}
                            })
                        except: continue
                        
                except Exception as e:
                    print(f"[ReviewPlace] Page {page_num} Error: {e}")
                    break
                
        await page.close()

    except Exception as e:
        print(f"[ReviewPlace] Critical Error: {e}")

    print(f"[ReviewPlace] Collected {len(results)} items")
    return results

# ==============================================================================
# [Crawler 3] 리뷰노트 (Review Note)
# ==============================================================================
async def crawl_reviewnote(context):
    print("[ReviewNote] Accessing API...")
    results = []
    
    # Create a page to visit the site once (initialize session/cookies)
    page = await context.new_page()
    try:
        await page.goto("https://www.reviewnote.co.kr", wait_until="domcontentloaded")
    except Exception as e:
        print(f"[ReviewNote] Init Page Error: {e}")
    
    # API Loop
    page_idx = 0
    limit = 20
    max_items = 4000 # Safety cap
    base_img_url = "https://firebasestorage.googleapis.com/v0/b/reviewnote-e92d9.appspot.com/o/"

    while len(results) < max_items:
        api_url = f"https://www.reviewnote.co.kr/api/v2/campaigns?s=popular&limit={limit}&page={page_idx}"
        try:
            response_obj = await context.request.get(api_url)
            if not response_obj.ok:
                print(f"[ReviewNote] API Error {response_obj.status} at page {page_idx}")
                break
                
            data = await response_obj.json()
            items = data.get('objects', [])
            
            if not items:
                print("[ReviewNote] No more items.")
                break
                
            print(f"[ReviewNote] Page {page_idx}: Found {len(items)} items")
            
            for item in items:
                try:
                    # 1. Title & URL
                    title = item.get('title', '').strip()
                    campaign_id = item.get('id')
                    link = f"https://www.reviewnote.co.kr/campaigns/{campaign_id}"
                    
                    # 2. Region / Filtering
                    sido_name = item.get('sido', {}).get('name', '')
                    city_name = item.get('city', '')
                    
                    if sido_name in ['재택', '배송'] or city_name in ['재택', '배송']:
                        continue  # 방문형 캠페인만 수집
                    
                    raw_region = f"{sido_name} {city_name}".strip()
                    region_data = RegionMapper.normalize(raw_region)
                        
                    # 3. Reward
                    offer = item.get('offer', '').strip()
                    reward_value = normalize_reward(offer)
                    
                    # 4. Type (Channel)
                    channel = item.get('channel', '')
                    type_ = map_channel(channel, title)
                    
                    # Category
                    raw_cat = item.get('category', {}).get('title', '')
                    if raw_cat in REVIEWNOTE_CATEGORY_MAP:
                        category = REVIEWNOTE_CATEGORY_MAP[raw_cat]
                    else:
                        category = extract_category_by_keyword(title, offer)
                    
                    # 5. D-Day
                    dday = ""
                    end_at = item.get('applyEndAt')
                    if end_at:
                        import datetime
                        try:
                             dt_str = end_at.split('.')[0]
                             target = datetime.datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")
                             now = datetime.datetime.now()
                             diff = target - now
                             if diff.days >= 0:
                                 dday = f"{diff.days}일 남음"
                             else:
                                 dday = "마감"
                        except: pass

                    # 6. Image
                    img_key = item.get('imageKey')
                    img_url = ""
                    if img_key:
                        import urllib.parse
                        encoded_key = urllib.parse.quote(img_key, safe='')
                        img_url = f"{base_img_url}{encoded_key}?alt=media"
                    
                    # 7. Stats (Applicants / Quota)
                    applicants = int(item.get('applicantCount', 0))
                    try:
                        quota = int(item.get('infNum', 0))
                    except:
                        quota = 0

                    results.append({
                        "platform": "리뷰노트",
                        "title": title,
                        "url": link,
                        "region": region_data,
                        "category": category,
                        "reward": {"text": offer, "value": reward_value},
                        "meta": {"type": type_, "dday": dday},
                        "image_url": img_url,
                        "stats": {"applicants": applicants, "quota": quota}
                    })
                    
                except Exception as e:
                    continue
            
            page_idx += 1
            
        except Exception as e:
            print(f"[ReviewNote] Page Loop Error: {e}")
            break
            
    await page.close()
    print(f"[ReviewNote] Collected {len(results)} items")
    return results

# ==============================================================================
# [Crawler 4] 디너의여왕 (Dinner Queen)
# ==============================================================================
async def crawl_dinnerqueen(context):
    print("[DinnerQueen] Starting crawl...")
    results = []
    page = await context.new_page()
    
    try:
        await page.goto("https://dinnerqueen.net/taste", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # 스크롤하여 더 많은 데이터 로드 시도 (무한스크롤 대응: 스크롤 후 데이터 변화 없으면 종료)
        prev_count = 0
        for _ in range(20):
             await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
             await page.wait_for_timeout(2000)
             html_check = await page.content()
             cur_count = html_check.count('qz-dq-card')
             if cur_count == prev_count:
                 break  # 더 이상 로드 없음
             prev_count = cur_count
             
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select(".qz-dq-card")
        
        # 1단계: 목록 페이지에서 기본 정보 수집
        raw_list = []
        for item in items:
            try:
                link_node = item.select_one("a.qz-dq-card__link")
                link = link_node.get('href', '') if link_node else ""
                if link and not link.startswith('http'): link = f"https://dinnerqueen.net{link}"
                
                title = link_node.get('title', '').replace(' 신청하기', '') if link_node else ""
                if not title: continue
                
                region_data = parse_region_from_title(title)
                reward_value = normalize_reward(title) 
                
                applicants = 0
                quota = 0
                text_content = item.get_text(separator=' ', strip=True)
                stats_match = re.search(r'신청\s*([\d,]+).*?모집\s*([\d,]+)', text_content)
                if stats_match:
                    applicants = int(stats_match.group(1).replace(',', ''))
                    quota = int(stats_match.group(2).replace(',', ''))
                
                dday_node = item.select_one(".qz-caption-kr--line strong")
                dday = dday_node.get_text(strip=True) if dday_node else ""
                
                type_ = map_channel("", title)
                category = DINNERQUEEN_CATEGORY_MAP.get("taste", "음식점")
                
                img_node = item.select_one(".qz-dq-card__link__img img")
                img = img_node.get('src', '') if img_node else ""
                
                raw_list.append({
                    "platform": "디너의여왕",
                    "title": title,
                    "url": link,
                    "region": region_data,
                    "category": category,
                    "reward": {"text": "상세페이지 참조", "value": reward_value},
                    "meta": {"type": type_, "dday": dday},
                    "image_url": img,
                    "stats": {"applicants": applicants, "quota": quota}
                })
            except Exception as e:
                continue
        
        print(f"[DinnerQueen] List parsed: {len(raw_list)} items. Fetching detail pages...")
        
        # 2단계: 상세 페이지에서 제공 내역 병렬 수집 (세마포어로 동시 5개 제한)
        semaphore = asyncio.Semaphore(5)
        
        async def fetch_offer(item_data):
            link = item_data["url"]
            async with semaphore:
                try:
                    detail_page = await context.new_page()
                    await detail_page.goto(link, wait_until="domcontentloaded", timeout=10000)
                    detail_html = await detail_page.content()
                    d_soup = BeautifulSoup(detail_html, 'html.parser')
                    full_text = d_soup.get_text(separator=' ', strip=True).replace('\n', '')
                    match = re.search(r'제공\s*내역\s*(.*?)(?:참여\s*전\s*필수|◈|★)', full_text)
                    if match:
                        parsed_offer = match.group(1).strip()
                        if parsed_offer:
                            item_data["reward"]["text"] = parsed_offer
                except Exception:
                    pass
                finally:
                    try:
                        await detail_page.close()
                    except Exception:
                        pass
            return item_data
        
        results = await asyncio.gather(*[fetch_offer(item) for item in raw_list])
        results = list(results)
        
    except Exception as e:
        print(f"[DinnerQueen] Error: {e}")
    finally:
         await page.close()
         
    print(f"[DinnerQueen] Collected {len(results)} items")
    return results


# ==============================================================================
# [Crawler 5] 서울오빠 (Seoul Oppa)
# ==============================================================================
async def crawl_seouloppa(context):
    print("[SeoulOppa] Starting crawl...")
    results = []
    page = await context.new_page()
    
    try:
        from category_mapper import SEOULOPPA_CATEGORY_MAP
        
        for cat_code, mapped_category in SEOULOPPA_CATEGORY_MAP.items():
            print(f"[SeoulOppa] Crawling {mapped_category} (cat: {cat_code})...")
            url = f"https://www.seoulouba.co.kr/campaign/?cat={cat_code}"
            
            try:
                await page.goto(url, wait_until="networkidle")
                await page.wait_for_timeout(2000)
                
                # 더 많은 아이템 로드를 위해 스크롤 다운 (카테고리별로 충분히)
                for _ in range(5):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)
                    
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                items = soup.select(".campaign_content")
                
                for item in items:
                    try:
                        # 1. URL & Title
                        title_node = item.select_one(".t_ttl a")
                        if not title_node: continue
                        title = title_node.get_text(strip=True)
                        link = title_node.get('href', '')
                        if link and not link.startswith('http'): link = f"https://www.seoulouba.co.kr{link}"
                        
                        # 2. Region Logic
                        region_data = parse_region_from_title(title)
                        
                        # 배송형/기자단 등 필터 (안전망)
                        type_node = item.select_one(".com_icon .icon_tag span")
                        if type_node:
                            tt = type_node.get_text(strip=True)
                            if "배송형" in tt or "기자단" in tt or "구매평" in tt:
                                continue
                        
                        # 3. Reward
                        reward_node = item.select_one(".t_basic .basic_blue")
                        reward_text = reward_node.get_text(strip=True) if reward_node else ""
                        reward_value = normalize_reward(reward_text)
                        
                        # 4. Stats
                        applicants = 0
                        quota = 0
                        recruit_node = item.select_one(".recruit span")
                        if recruit_node:
                            recruit_text = recruit_node.get_text(strip=True) # "신청 77 / 모집 2"
                            stats_match = re.search(r'신청\s*(\d+).*?모집\s*(\d+)', recruit_text)
                            if stats_match:
                                applicants = int(stats_match.group(1))
                                quota = int(stats_match.group(2))
                        
                        # 5. Type & Category
                        dday_node = item.select_one(".d_day span")
                        dday = dday_node.get_text(strip=True) if dday_node else ""
                        
                        channel_alt = ""
                        channel_node = item.select_one(".ltop_icon .icon_box img")
                        if channel_node:
                            channel_alt = channel_node.get('alt', '')
                        
                        type_ = map_channel(channel_alt, title)
                        category = mapped_category
                        
                        # 6. Image
                        img_node = item.select_one(".tum_img img")
                        img = img_node.get('src', '') if img_node else ""
                        
                        results.append({
                            "platform": "서울오빠",
                    "title": title,
                    "url": link,
                    "region": region_data,
                    "category": category,
                    "reward": {"text": reward_text, "value": reward_value},
                    "meta": {"type": type_, "dday": dday},
                    "image_url": img,
                    "stats": {"applicants": applicants, "quota": quota}
                        })
                    except Exception as e:
                        print(f"[SeoulOppa] Item Parse Error: {e} -> title: {title}")
                        continue
            except Exception as inner_e:
                print(f"[SeoulOppa] Category {cat_code} Crawl Error: {inner_e}")
                continue
            
    except Exception as e:
        print(f"[SeoulOppa] Error: {e}")
    finally:
        await page.close()
        
    print(f"[SeoulOppa] Collected {len(results)} items")
    return results

# ==============================================================================
# [Crawler 6] 놀러와체험단 (Come To Play)
# ==============================================================================
async def crawl_cometoplay(context):
    print("[ComeToPlay] Starting crawl...")
    results = []
    page = await context.new_page()
    
    try:
        from crawler.category_mapper import COMETOPLAY_CATEGORY_MAP
    except ImportError:
        from category_mapper import COMETOPLAY_CATEGORY_MAP
        
    # 초기 지역 메뉴 클릭 (사용자 피드백 반영: 상단 지역 버튼 누르고 크롤링)
    try:
        print("[ComeToPlay] Accessing main page to click '지역'...")
        await page.goto("https://www.cometoplay.kr/", wait_until="domcontentloaded", timeout=60000)
        local_menu = page.locator(".gnb_menu a:has-text('지역')").first
        await local_menu.click()
        await page.wait_for_timeout(2000)
    except Exception as e:
        print(f"[ComeToPlay] Click '지역' Error: {e}")

    try:
        for ct_id, mapped_category in COMETOPLAY_CATEGORY_MAP.items():
            print(f"[ComeToPlay] Crawling {mapped_category} (cat: {ct_id})...")
            url = f"https://www.cometoplay.kr/item_list.php?category_id={ct_id}&sst=it_datetime&sod=desc"
            
            try:
                # Iterate through page 1 to 20
                for page_num in range(1, 100):  # 충분히 큰 값으로 전체 페이지 수집
                    paginated_url = f"{url}&page={page_num}"
                    try:
                        await page.goto(paginated_url, wait_until="networkidle")
                        await page.wait_for_timeout(1000)
                    except Exception as goto_e:
                         print(f"[ComeToPlay] Page {page_num} Goto Error: {goto_e}")
                         break
                         
                    html = await page.content()
                    soup = BeautifulSoup(html, 'html.parser')
                    items = soup.select(".item_box_list li")
                    
                    if not items:
                        break # No more items
                    
                    print(f"  -> Page {page_num}: Found {len(items)} items")
                
                    for item in items:
                        try:
                            # 1. URL & Title
                            link_node = item.select_one("a")
                            if not link_node: continue
                            link = link_node.get('href', '')
                            if link and not link.startswith('http'): link = f"https://www.cometoplay.kr/{link.lstrip('/')}"
                            
                            title_node = item.select_one(".it_name")
                            title = title_node.get_text(strip=True) if title_node else ""
                            if not title: continue
                            
                            # 2. Region Logic
                            region_match = re.search(r'\[(.*?)\]', title)
                            raw_region = region_match.group(1) if region_match else title[:5]
                            region_data = RegionMapper.normalize(raw_region)
                            
                            # 3. Reward
                            reward_node = item.select_one(".it_description")
                            offer = reward_node.get_text(strip=True) if reward_node else "상세페이지 참조"
                            reward_value = normalize_reward(title)
                            
                            # 4. Meta & Channel
                            dday_node = item.select_one(".option_re .txt_num")
                            dday = dday_node.get_text(strip=True) if dday_node else ""
                            if dday.startswith("D-day"): dday = dday.replace("D-day", "").strip() + "일 남음"
                            
                            raw_type = ""
                            if item.select_one(".blog"): raw_type = "블로그"
                            elif item.select_one(".insta"): raw_type = "인스타그램"
                            type_ = map_channel(raw_type, title)
                            
                            category = mapped_category
                            
                            # 5. Stats
                            applicants = 0
                            quota = 0
                            peo_cnt = item.select_one(".peo_cnt")
                            if peo_cnt:
                                peo_text = peo_cnt.get_text(strip=True) # "신청 0 명 / 모집 10 명"
                                stats_match = re.search(r'신청\s*(\d+).*?모집\s*(\d+)', peo_text)
                                if stats_match:
                                    applicants = int(stats_match.group(1))
                                    quota = int(stats_match.group(2))
                            
                            # 6. Image
                            img_node = item.select_one(".it_img")
                            img_src = img_node.get('src', '') if img_node else ""
                            img = ""
                            if img_src:
                                if img_src.startswith('http'):
                                    img = img_src
                                else:
                                    # ./data/... 또는 /data/... 형태를 모두 처리
                                    import urllib.parse
                                    img = urllib.parse.urljoin("https://www.cometoplay.kr/", img_src)
                            
                            results.append({
                                "platform": "놀러와체험단",
                                "title": title,
                                "url": link,
                                "region": region_data,
                                "category": category,
                                "reward": {"text": offer, "value": reward_value},
                                "meta": {"type": type_, "dday": dday},
                                "image_url": img,
                                "stats": {"applicants": applicants, "quota": quota}
                            })
                        except Exception as e:
                            continue
            except Exception as inner_e:
                 print(f"[ComeToPlay] Category {ct_id} Crawl Error: {inner_e}")
                 continue
                 
    except Exception as e:
        print(f"[ComeToPlay] Error: {e}")
    finally:
        await page.close()
        
    print(f"[ComeToPlay] Collected {len(results)} items")
    return results

# ==============================================================================
# [Crawler 7] 레뷰 (Revu)
# ==============================================================================
async def crawl_revu(context):
    print("[Revu] Starting crawl...")
    results = []
    
    page = await context.new_page()
    
    # 1. 로그인
    login_ok = False
    try:
        print("[Revu] Logging in...")
        # domcontentloaded 후 JS가 폼을 렌더링할 때까지 명시적 대기
        await page.goto("https://www.revu.net/login", wait_until="domcontentloaded", timeout=60000)
        # 로그인 폼(이메일 입력란)이 나타날 때까지 최대 20초 대기
        await page.wait_for_selector('input[name="email"]', timeout=20000)
        await page.fill('input[name="email"]', 'reviewhyun@gmail.com')
        await page.fill('input[name="password"]', 'Dkssuddy1!')
        submit_btn = await page.query_selector('button[type="submit"]')
        if submit_btn:
             await submit_btn.click()
        else:
             await page.get_by_text("로그인", exact=True).click()
        await page.wait_for_timeout(4000)
        login_ok = True
        print("[Revu] Login success")
    except Exception as e:
        print(f"[Revu] Login Error: {e}")
        await page.close()
        return results

    # 초기 지역 메뉴 클릭 (사용자 피드백 반영: 상단 지역 버튼 누르고 크롤링)
    try:
        print("[Revu] Accessing main page to click '지역'...")
        await page.goto("https://www.revu.net/", wait_until="domcontentloaded", timeout=60000)
        local_menu = page.locator("nav a, .navigation a, header a").filter(has_text="지역").first
        await local_menu.click()
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[Revu] Click '지역' Error: {e}")

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
                                
                                # 사용자의 요청: '지역' 메뉴만 포함 (제품, 기자단, 저금통 전부 제외)
                                # 레뷰 응답의 category 배열에 '방문형' 태그가 있는지 체크
                                cats = item.get("category", [])
                                if "방문형" not in cats:
                                    continue
                                
                                # 1. 제목에서 파싱 시도
                                try:
                                    parsed = parse_region_from_title(str(title))
                                    prov = parsed["province"]
                                    city = parsed["city"]
                                    
                                    # 제목 파싱에서 province와 city를 모두 못 찾았을 때만 레뷰 API의 sido/area를 사용해 다시 정규화
                                    if prov == "기타" and city == "기타":
                                        revu_sido = item.get("sido") or "기타"
                                        revu_area = item.get("area") or "기타"
                                        revu_region_str = f"{revu_sido} {revu_area}".strip()
                                        if revu_region_str != "기타 기타":
                                            fallback_parsed = RegionMapper.normalize(revu_region_str)
                                            # fallback에서 찾은 prov/city가 있다면 그것을 사용.
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
                                ch_map = {
                                    "blog": "네이버 블로그",
                                    "instagram": "인스타그램 피드",
                                    "youtube": "유튜브 동영상",
                                    "reels": "인스타그램 릴스",
                                    "shorts": "유튜브 숏츠",
                                    "clip": "네이버 클립"
                                }
                                type_ = ch_map.get(media, "기타")
                                
                                # 보상 내역 파싱: 'campaignData' 내의 'reward' 필드에 상세 내역 탑재
                                campaign_data = item.get("campaignData", {})
                                offer = campaign_data.get("reward") or item.get("offer", "상세페이지 참조")
                                
                                stats = item.get("campaignStats", {})
                                applicants = stats.get("requestCount", 0)
                                quota = item.get("reviewerLimit", 0)
                                reward_value = normalize_reward(offer) if offer != "상세페이지 참조" else normalize_reward(title)
                                
                                thumb = item.get("thumbnail", "")
                                
                                campaign_id = item.get("id")
                                link = f"https://www.revu.net/campaign/{campaign_id}" if campaign_id else "https://www.revu.net/"
                                
                                # D-day 계산: byDeadline 필드 우선, 없으면 requestEndedOn으로 직접 계산
                                by_deadline = item.get("byDeadline")
                                request_ended_on = item.get("requestEndedOn", "")
                                if by_deadline is not None:
                                    dday = f"{by_deadline}일 남음"
                                elif request_ended_on:
                                    try:
                                        from datetime import datetime, timezone, timedelta
                                        KST = timezone(timedelta(hours=9))
                                        today = datetime.now(KST).date()
                                        end_date = datetime.strptime(request_ended_on, "%Y-%m-%d").date()
                                        diff = (end_date - today).days
                                        dday = f"{diff}일 남음" if diff >= 0 else "마감"
                                    except Exception:
                                        dday = ""
                                else:
                                    dday = ""

                                res = {
                                    "platform": "레뷰",
                                    "title": str(title),
                                    "url": str(link),
                                    "region": region_data,
                                    "category": "추론중", 
                                    "reward": {"text": str(offer)[:100], "value": reward_value},
                                    "meta": {"type": type_, "dday": dday},
                                    "image_url": str(thumb),
                                    "stats": {"applicants": int(applicants), "quota": int(quota)}
                                }
                                if not any(r['url'] == res['url'] for r in results):
                                    results.append(res)
                            except Exception as parse_e:
                                print(f"[Revu] Parse Item Error: {parse_e}")
            except Exception as e:
                pass

    page.on("response", handle_response)
    
    # 3. 신규 URL 체계에 맞춘 카테고리 순회
    # 새로운 레뷰 URL 라우팅 체계 반영: /category/지역/맛집
    revu_url_map = {"음식점": "맛집", "뷰티": "뷰티", "숙박": "숙박", "문화": "문화", "기타": "기타"}
    
    for cat_name, revu_path in revu_url_map.items():
        print(f"[Revu] Crawling {cat_name} ({revu_path})...")
        try:
            start_count = len(results)
            # DOMContentLoaded로 대기하여 타임아웃 방지, 실제 마우스 휠 이벤트 발생
            try:
                await page.goto(f"https://www.revu.net/category/지역/{revu_path}", wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"[Revu] Goto ({revu_path}) Exception: {e}")
                
            for _ in range(30):
                await page.mouse.wheel(delta_x=0, delta_y=800)
                await page.wait_for_timeout(1500)
            
            for r in results[start_count:]:
                r["category"] = cat_name
                
        except Exception as e:
            print(f"[Revu] Navigation Error on {cat_name}: {e}")
            
    await page.close()
    print(f"[Revu] Collected {len(results)} items")
    return results

# ==============================================================================
# [Crawler 8] 포블로그 (4blog.net)
# ==============================================================================
async def crawl_4blog(context):
    print("[4Blog] Starting crawl...")
    results = []
    page = await context.new_page()
    
    try:
        url = "https://4blog.net/list/all/local"
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        # 무한 스크롤 다운을 통해 항목 로드 (포블로그의 경우 최대 50회 정도면 대부분 수집 가능할 것으로 예상)
        print("[4Blog] Scrolling to load campaigns...")
        previous_height = await page.evaluate("document.body.scrollHeight")
        for i in range(50):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                # Retry once
                await page.wait_for_timeout(2000)
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == previous_height:
                    print(f"  [4Blog] Reached bottom at scroll {i+1}")
                    break
            previous_height = new_height
            if (i+1) % 10 == 0:
                print(f"  [4Blog] Scroll {i+1} times...")
                
        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        items = soup.select("a[href*='/campaign/']")
        print(f"  [4Blog] Found {len(items)} possible items after scrolling.")
        
        for item in items:
            try:
                # 1. URL
                link = item.get('href', '')
                if link and not link.startswith('http'):
                    link = f"https://4blog.net{link}"
                
                # 2. Title & Region
                title_node = item.select_one(".camp-name")
                title = title_node.get_text(strip=True) if title_node else ""
                if not title: continue
                
                region_match = re.search(r'^\[(.*?)\]', title)
                raw_region = region_match.group(1) if region_match else title[:5]
                region_data = RegionMapper.normalize(raw_region)
                
                # 3. Reward
                reward_node = item.select_one(".emphasize")
                offer = reward_node.get_text(separator=' ', strip=True) if reward_node else "상세페이지 참조"
                reward_value = normalize_reward(offer)
                if reward_value == 0:
                    reward_value = normalize_reward(title)
                
                # 4. Meta & Channel
                dday_node = item.select_one(".remainDate")
                dday = dday_node.get_text(strip=True) if dday_node else ""
                
                type_node = item.select_one(".label-success")
                raw_type = type_node.get_text(strip=True) if type_node else ""
                type_ = map_channel(raw_type, title)
                
                # 5. Image
                img_node = item.select_one("img.lazy")
                img = img_node.get('src', '') if img_node else ""
                
                # 6. Stats (Not visible in list view usually, but lets default 0)
                applicants = 0
                quota = 0
                
                # 7. Category (포블로그 방문형은 세부 카테고리가 확인되지 않아 제목과 리워드로 추론)
                category = extract_category_by_keyword(title, offer)
                
                results.append({
                    "platform": "포블로그",
                    "title": title,
                    "url": link,
                    "region": region_data,
                    "category": category,
                    "reward": {"text": offer, "value": reward_value},
                    "meta": {"type": type_, "dday": dday},
                    "image_url": img,
                    "stats": {"applicants": applicants, "quota": quota}
                })
            except Exception as e:
                pass
                
    except Exception as e:
        print(f"[4Blog] Critical Error: {e}")
    finally:
        await page.close()
        
    print(f"[4Blog] Collected {len(results)} items")
    return results

# ==============================================================================
# [Crawler 9] 오마이블로그 (Oh My Blog)
# ==============================================================================
async def crawl_ohmyblog(context):
    print("[OhMyBlog] Starting crawl...")
    results = []
    
    try:
        from crawler.category_mapper import OHMYBLOG_CATEGORY_MAP, extract_category_by_keyword
        from crawler.region_mapper import RegionMapper
    except ImportError:
        from category_mapper import OHMYBLOG_CATEGORY_MAP, extract_category_by_keyword
        from region_mapper import RegionMapper

    # 1. Fetch Regions Dynamically
    region_map = {}
    try:
        res_region = await context.request.get("https://www.ohmyblog.co.kr/api/web/region?action=list")
        if res_region.ok:
            region_data = await res_region.json()
            for country in region_data.get("data", []):
                province_name = country.get("name", "")
                for area in country.get("areas", []):
                    g_seq = str(area.get("country_groupSeq", ""))
                    a_name = area.get("area", "")
                    region_map[g_seq] = f"{province_name} {a_name}".strip()
    except Exception as e:
        print(f"[OhMyBlog] Region fetch error: {e}")

    # 2. Pre-fetch native categories to build app_seq -> category map
    # Since requesting app_type=A directly does not return app_cate_detail, 
    # we build a lookup table so we don't lose the remaining 200+ unstructured campaigns.
    native_category_lookup = {}
    for cat_code, mapped_category in OHMYBLOG_CATEGORY_MAP.items():
        page_idx = 1
        try:
            while True:
                url = f"https://www.ohmyblog.co.kr/api/web/campaign/active?page={page_idx}&limit=100&app_type=A&app_cate_detail={cat_code}"
                res = await context.request.get(url)
                if not res.ok: break
                data = await res.json()
                campaigns = data.get('data', {}).get('campaigns', [])
                if not campaigns: break
                for item in campaigns:
                    app_seq = str(item.get('app_seq', ''))
                    native_category_lookup[app_seq] = mapped_category
                page_idx += 1
        except Exception:
            pass

    # 3. Fetch ALL Visit Campaigns
    page_idx = 1
    try:
        while True:
            # Fetch ALL active campaigns 
            url = f"https://www.ohmyblog.co.kr/api/web/campaign/active?page={page_idx}&limit=20&app_type=A"
            res = await context.request.get(url)
            
            if not res.ok:
                print(f"  [OhMyBlog] API Error at page {page_idx}")
                break
                
            data = await res.json()
            campaigns = data.get('data', {}).get('campaigns', [])
            if not campaigns: break
            print(f"  [OhMyBlog] Page {page_idx}: Found {len(campaigns)} items")
            
            for item in campaigns:
                try:
                    title = item.get('app_title', '')
                    app_seq = str(item.get('app_seq', ''))
                    link = f"https://www.ohmyblog.co.kr/productDetail.apsl?app_seq={app_seq}"
                    offer = item.get('supplyItem', '상세페이지 참조')
                    
                    # Region Lookup
                    region_data = {"province": "기타", "city": "기타", "normalized": "기타"}
                    g_seq = str(item.get('country_groupSeq', ''))
                    if g_seq and g_seq in region_map:
                        raw_region = region_map[g_seq]
                        region_data = RegionMapper.normalize(raw_region)
                    else:
                        # Fallback to Title Regex
                        region_match = re.search(r'^\[(.*?)\]', title)
                        if region_match:
                            raw_region = region_match.group(1)
                            region_data = RegionMapper.normalize(raw_region)
                    
                    # Category Lookup (Native Map -> Keyword Fallback)
                    if app_seq in native_category_lookup:
                        category = native_category_lookup[app_seq]
                    else:
                        category = extract_category_by_keyword(title, offer)
                    
                    # Reward Extraction
                    reward_value = normalize_reward(offer)
                    
                    # Meta
                    dday = ""
                    end_date = item.get('app_recruitEndDate', '')
                    if end_date:
                        import datetime
                        try:
                             target = datetime.datetime.strptime(end_date.split(' ')[0], "%Y-%m-%d")
                             now = datetime.datetime.now()
                             diff = target - now
                             if diff.days >= 0: dday = f"{diff.days}일 남음"
                             else: dday = "마감"
                        except Exception: pass
                        
                    raw_sns = item.get('sns_platforms', '')
                    type_ = map_channel(raw_sns, title)
                    
                    # Image & Stats
                    img = item.get('thumbnail', '')
                    if img and not img.startswith('http'):
                        img = f"https://www.ohmyblog.co.kr{img}"
                        
                    applicants = int(item.get('applicant_count', 0))
                    try: quota = int(item.get('app_recruitCount', 0))
                    except ValueError: quota = 0
                        
                    results.append({
                        "platform": "오마이블로그",
                        "title": title,
                        "url": link,
                        "region": region_data,
                        "category": category,
                        "reward": {"text": offer, "value": reward_value},
                        "meta": {"type": type_, "dday": dday},
                        "image_url": img,
                        "stats": {"applicants": applicants, "quota": quota}
                    })
                except Exception as e:
                    pass
            page_idx += 1
            
    except Exception as e:
        print(f"[OhMyBlog] Critical Error: {e}")
        
    print(f"[OhMyBlog] Collected {len(results)} items")
    return results

# ==============================================================================
# [Main Aggregator]
# ==============================================================================
async def run_aggregator():
    async with async_playwright() as p:
        # Launch Browser (Headless=True)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        print("\n[System] Starting Aggregator for 7 Sites...")
        
        # Gather Results
        concurrent_tasks = [
            crawl_kangnam(context),
            crawl_reviewnote(context),
            crawl_reviewplace(context),
            crawl_dinnerqueen(context),
            crawl_seouloppa(context),
            crawl_cometoplay(context),
            crawl_revu(context),
            crawl_4blog(context),
            crawl_ohmyblog(context)
        ]
        
        results_list = await asyncio.gather(*concurrent_tasks)
        
        # Flatten
        all_campaigns = [item for sublist in results_list for item in sublist]
        
        # Shuffle for better demo (Optional)
        import random
        random.shuffle(all_campaigns)
        
        # Log Summary
        print(f"\n[Summary]")
        print(f"- Total Items: {len(all_campaigns)}")
        
        # Save JSON
        import os
        # Ensure we write to the project root's public folder, not crawler/public
        # implementation: aggregator.py is in crawler/, so ../public
        
        # Get absolute path to project root (parent of crawler)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        public_dir = os.path.join(project_root, "public")
        
        os.makedirs(public_dir, exist_ok=True)
        output_path = os.path.join(public_dir, "campaigns.json")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_campaigns, f, indent=2, ensure_ascii=False)
            
        print(f"[System] Data conversion complete -> {output_path}")

        # Upload to Firebase Firestore (Chunking Architecture)
        try:
            from firebase_chunk_client import upload_to_firestore_chunks
            upload_to_firestore_chunks(all_campaigns)
        except Exception as e:
            print(f"[Firebase Chunking] ❌ FAILED to upload to Firestore: {e}")
            raise  # ← GitHub Actions가 실패(❌)로 표시되도록 오류를 다시 발생시킴

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_aggregator())
