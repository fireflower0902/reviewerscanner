"""수도권(서울·경기·인천) 철도·지하철 역 이름 → 시/도·시/군/구 표 만들기

데이터 출처: OpenStreetMap (© OpenStreetMap contributors, ODbL) — Overpass API.
결과: crawler/data/capital_stations.json   {"사당": ["서울", "동작구"], ...}  (이름은 '역' 글자를 뺀 형태)

사용:
    python tools/build_capital_stations.py            # Overpass 에서 새로 받아 만들기 (약 3분)
    python tools/build_capital_stations.py raw.json   # 이미 받아 둔 응답 파일로 만들기
"""
import json
import os
import re
import sys
import time

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "capital_stations.json")
SIDO = {"서울특별시": "서울", "경기도": "경기", "인천광역시": "인천"}
PRIORITY = {"서울": 0, "경기": 1, "인천": 2}      # 같은 이름이 여럿이면 서울 > 경기 > 인천 순

QUERY = """
[out:json][timeout:600];
(area["ISO3166-2"="KR-11"];area["ISO3166-2"="KR-41"];area["ISO3166-2"="KR-28"];)->.sido;
(
  node[railway=station](area.sido);
  node[railway=halt](area.sido);
  node[station=subway](area.sido);
  node[public_transport=station][subway=yes](area.sido);
)->.st;
foreach.st->.s(
  .s out tags;
  .s is_in->.a;
  area.a[boundary=administrative][admin_level~"^(4|6)$"];
  out tags;
);
"""


def fetch():
    import requests
    r = requests.post("https://overpass-api.de/api/interpreter", data={"data": QUERY},
                      headers={"User-Agent": "reviewerscanner-data-build/1.0"}, timeout=650)
    r.raise_for_status()
    return r.json()["elements"]


def clean(name: str) -> str:
    n = re.sub(r"\(.*?\)", "", name or "").strip()      # "신촌(경의중앙선)" -> "신촌"
    n = re.sub(r"역$", "", n).strip()
    return n


def build(elements):
    table = {}
    stations = 0
    cur = None
    for el in elements:
        if el["type"] == "node":
            cur = {"names": set(), "sido": None, "city": None}
            tags = el.get("tags", {})
            for key in ("name", "name:ko", "alt_name", "alt_name:ko", "official_name"):
                for part in re.split(r"[;,]", tags.get(key, "")):
                    c = clean(part)
                    if len(c) >= 2 and re.search(r"[가-힣]", c) and not re.search(r"정류장|\d{3}", c):
                        cur["names"].add(c)
            stations += 1
            cur["done"] = False
            cur_list.append(cur)
        elif el["type"] == "area" and cur is not None:
            level = el.get("tags", {}).get("admin_level")
            name = el.get("tags", {}).get("name", "")
            if level == "4" and name in SIDO:
                cur["sido"] = SIDO[name]
            elif level == "6":
                cur["city"] = name
    for st in cur_list:
        if not (st["sido"] and st["city"]):
            continue
        for n in st["names"]:
            prev = table.get(n)
            cand = [st["sido"], st["city"]]
            if prev is None or PRIORITY[cand[0]] < PRIORITY[prev[0]]:
                table[n] = cand
    return table, stations


cur_list = []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        elements = json.load(open(sys.argv[1], encoding="utf-8"))
    else:
        t = time.time()
        elements = fetch()
        print(f"받기 완료 ({time.time() - t:.0f}초)")
    table, stations = build(elements)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(dict(sorted(table.items())), f, ensure_ascii=False, indent=0)
    print(f"역 노드 {stations}개 → 이름 {len(table)}개 저장: {OUT}")
