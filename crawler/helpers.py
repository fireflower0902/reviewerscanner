import re
import asyncio
from typing import Dict

try:
    from crawler.region_mapper import RegionMapper
except ImportError:
    from region_mapper import RegionMapper


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
    m = re.match(r'^D\s*-\s*(\d+)$', t, re.IGNORECASE)
    if m:
        n = int(m.group(1))
        return "오늘까지" if n == 0 else f"{n}일 남음"
    if t.upper().replace(" ", "") in ("D-DAY", "DDAY"):
        return "오늘까지"
    return t
