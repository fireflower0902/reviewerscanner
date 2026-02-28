import asyncio
import random
import re
import json
from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from typing import List, Dict

# ==============================================================================
# [Skill 1] 봇 탐지 우회
# ==============================================================================
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

async def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
    """사람처럼 보이게 하기 위한 랜덤 딜레이"""
    delay = random.uniform(min_seconds, max_seconds)
    # print(f"[Delay] {delay:.2f}s...") # 로그 과다 방지
    await asyncio.sleep(delay)

async def get_page_content(url: str, page: Page) -> str:
    try:
        await page.set_extra_http_headers({"User-Agent": random.choice(USER_AGENTS)})
        print(f"[Crawling] Connecting to: {url}")
        
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        
        # 스크롤하여 Lazy Loading 이미지만 데이터 로딩 유도
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(0.5)
            
        return await page.content()
    except Exception as e:
        print(f"[Error] Crawling failed: {e}")
        return ""

# ==============================================================================
# [Skill 2] 데이터 정규화 (Data Normalization)
# ==============================================================================
def normalize_region(raw_region: str) -> str:
    """
    제목 등에서 추출한 원본 지역명을 표준 행정구역명으로 변환
    Mapping Table 기반 (화성시, 서울 강남구 등)
    """
    target = raw_region.replace('[', '').replace(']', '').strip()
    
    # 매핑 테이블 (Geo-Tagging)
    MAPPING = {
        # 화성시 관련
        "동탄": "화성시", "병점": "화성시", "봉담": "화성시", "2동탄": "화성시", "화성": "화성시",
        # 서울 강남권
        "서울 강남": "서울 강남구", "강남": "서울 강남구", "역삼": "서울 강남구", "논현": "서울 강남구",
        "삼성": "서울 강남구", "청담": "서울 강남구", "신사": "서울 강남구", "압구정": "서울 강남구",
        "도곡": "서울 강남구", "대치": "서울 강남구", "개포": "서울 강남구",
        # 서울 마포권
        "홍대": "서울 마포구", "연남": "서울 마포구", "합정": "서울 마포구", "망원": "서울 마포구",
        # 기타 (지역명이 명확하면 그대로 사용하되, 시/군/구 단위로 통일 권장)
    }
    
    for key, val in MAPPING.items():
        if key in target:
            return val
            
    return target

def normalize_reward(reward_text: str) -> int:
    """
    '3만원 체험권', '50,000 포인트' -> 30000 (int)
    """
    if not reward_text: return 0
    
    txt = reward_text.replace(',', '').replace('원', '')
    nums = re.findall(r'\d+', txt)
    
    if not nums: return 0
    
    val = int(nums[0])
    if '만' in reward_text:
        val *= 10000
        
    return val

def parse_campaigns(html: str) -> List[Dict]:
    """
    HTML 파싱 및 데이터 구조화
    Target: 강남맛집 (li.list_item)
    """
    soup = BeautifulSoup(html, 'html.parser')
    campaigns = []
    
    items = soup.select("li.list_item")
    print(f"\n[Parsing] Found {len(items)} items raw.")
    
    for item in items:
        try:
            # 1. Title & URL
            title_node = item.select_one("dt.tit a")
            if not title_node: continue
            
            title = title_node.get_text(strip=True)
            link = title_node.get('href')
            if link and not link.startswith('http'):
                link = f"https://xn--939au0g4vj8sq.net{link}"
                
            # 2. Region (Extraction from Title "[Region]")
            region_match = re.match(r'^\[(.*?)\]', title)
            raw_region = region_match.group(1) if region_match else "기타"
            norm_region = normalize_region(raw_region)
            
            # 3. Reward (Sub Title)
            sub_tit_node = item.select_one("dd.sub_tit")
            reward_text = sub_tit_node.get_text(strip=True) if sub_tit_node else ""
            reward_value = normalize_reward(reward_text)
            
            # 4. Meta Info (Type, D-Day)
            type_node = item.select_one("span.label em.type")
            campaign_type = type_node.get_text(strip=True) if type_node else "기타"
            
            dday_node = item.select_one("span.dday em.day_c")
            dday = dday_node.get_text(strip=True) if dday_node else ""
            
            # 5. Image
            img_node = item.select_one("img.thumb_img")
            img_url = img_node.get('src') if img_node else ""
            if img_url and img_url.startswith('//'):
                img_url = "https:" + img_url

            # 6. Build Data Object
            campaign = {
                "platform": "강남맛집",
                "title": title,
                "url": link,
                "region": {
                    "raw": raw_region,
                    "normalized": norm_region
                },
                "reward": {
                    "text": reward_text,
                    "value": reward_value
                },
                "meta": {
                    "type": campaign_type,
                    "dday": dday
                },
                "image_url": img_url
            }
            campaigns.append(campaign)
            
        except Exception as e:
            continue
            
    return campaigns

# ==============================================================================
# [Main Logic]
# ==============================================================================
async def run_crawler():
    async with async_playwright() as p:
        # Debugging: Show browser
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("[System] Start Crawling: 강남맛집 (xn--939au0g4vj8sq.net)")
        
        # 1. Main List Page
        target_url = "https://xn--939au0g4vj8sq.net/"
        html = await get_page_content(target_url, page)
        
        if not html:
            print("[Error] Failed to get content")
            await browser.close()
            return

        # 2. Parse Data
        data = parse_campaigns(html)
        
        print(f"\n[Result] Successfully parsed {len(data)} campaigns.\n")
        
        # 3. Save Data (JSON)
        # 프론트엔드에서 사용할 수 있도록 JSON 파일로 저장
        output_file = "public/campaigns.json"
        
        # public 폴더가 없으면 생성 (Next.js 정적 파일 경로)
        import os
        os.makedirs("public", exist_ok=True)
            
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"\n[System] Data saved to {output_file} (Count: {len(data)})")
        
        # 4. Filter Test (Optional)
        filter_region = "서울 강남구"
        filtered_data = [d for d in data if d['region']['normalized'] == filter_region]
        
        print(f"--- [Filter Test] Region: '{filter_region}' (Count: {len(filtered_data)}) ---")
        for idx, item in enumerate(filtered_data[:5]):
            print(f"[{idx+1}] {item['title']}")
            print(f"    - Reward: {item['reward']['value']}원 ({item['reward']['text']})")
            print(f"    - URL: {item['url']}")
            
        print(f"\n--- [Sample Data (JSON)] ---")
        print(json.dumps(data[:2], indent=2, ensure_ascii=False))

        await browser.close()
        print("\n[System] Crawling Finished.")

if __name__ == "__main__":
    asyncio.run(run_crawler())
