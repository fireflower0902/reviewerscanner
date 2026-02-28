import json
from collections import Counter

output_file = "public/campaigns.json"

try:
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    platforms = ["강남맛집", "리뷰플레이스"]
    
    for p in platforms:
        print(f"\n--- {p} Types ---")
        types = [item.get('meta', {}).get('type', 'Unknown') for item in data if item.get('platform') == p]
        counts = Counter(types)
        for t, c in counts.most_common():
            print(f"{t}: {c}")

except Exception as e:
    print(f"Error: {e}")
