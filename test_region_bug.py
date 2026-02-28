from crawler.region_mapper import RegionMapper

def parse_region_from_title(title: str) -> dict:
    import re
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

title = "[울산] 트레비어 언양점"
parsed = parse_region_from_title(title)
prov = parsed["province"]
city = parsed["city"]

# Legacy Buggy Logic
if city == "기타":
    revu_sido = "기타"
    revu_area = "기타"
    revu_region_str = f"{revu_sido} {revu_area}".strip()
    fallback_parsed = RegionMapper.normalize(revu_region_str)
    prov = fallback_parsed["province"] if fallback_parsed["province"] != "기타" else revu_sido
    city = fallback_parsed["city"] if fallback_parsed["city"] != "기타" else revu_area

print(f"Legacy logic output: prov={prov}, city={city}")

# Corrected Logic
parsed2 = parse_region_from_title(title)
prov2 = parsed2["province"]
city2 = parsed2["city"]

if prov2 == "기타" and city2 == "기타":
    revu_sido = "기타" # api fallback
    revu_area = "기타"
    revu_region_str = f"{revu_sido} {revu_area}".strip()
    if revu_region_str != "기타 기타":
        fallback_parsed = RegionMapper.normalize(revu_region_str)
        if fallback_parsed["province"] != "기타": prov2 = fallback_parsed["province"]
        if fallback_parsed["city"] != "기타": city2 = fallback_parsed["city"]

print(f"Correct logic output: prov={prov2}, city={city2}")
