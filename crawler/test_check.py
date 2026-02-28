import json
from collections import Counter

data = json.load(open("../public/campaigns.json"))
ohmyblog = [d for d in data if d.get("platform") == "오마이블로그"]

print(f"Total OhMyBlog: {len(ohmyblog)}")
cats = Counter(d['category'] for d in ohmyblog)
print(f"Categories: {dict(cats)}")

regs = Counter(d['region']['province'] for d in ohmyblog)
print(f"Provinces: {dict(regs)}")
