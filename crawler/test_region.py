import sys
sys.path.append('.')
from region_mapper import RegionMapper

titles = [
    "[클립][서초] OOO 식당",
    "[인스타방문형][광주] 전라도추어탕",
    "[배송형][서울] OOO 제품",
    "[마곡] 몸바로체형교정센터"
]

for t in titles:
    print(f"Title: {t}")
    print(f" -> Result: {RegionMapper.normalize(t)}")
    
# 기존 로직 (문제재현)
import re
print("\n--- 기존 로직 결과 ---")
for t in titles:
    raw_region_match = re.search(r'\[([^\]]+)\]', t)
    raw_region = raw_region_match.group(1) if raw_region_match else t[:5]
    print(f"Title: {t}")
    print(f" -> Extracted: {raw_region} / Result: {RegionMapper.normalize(raw_region)}")
