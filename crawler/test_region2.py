import re
import sys
sys.path.append('.')
from region_mapper import RegionMapper

def parse_region(title):
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

titles = [
    "[클립][서초] OOO 식당",
    "[인스타방문형][광주] 전라도추어탕",
    "[배송형][서울] OOO 제품",
    "[마곡] 몸바로체형교정센터",
    "[동탄] 앤슬 (aensl)",
    "괄호없는제목 식당"
]

for t in titles:
    print(f"Title: {t}")
    print(f" -> {parse_region(t)}")
