import json
from collections import Counter

def run():
    try:
        with open("public/campaigns.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        gangnam_items = [d for d in data if d.get('platform') == '강남맛집']
        print(f"Total Gangnam Items: {len(gangnam_items)}")
        
        urls = [d['url'] for d in gangnam_items]
        unique_urls = set(urls)
        print(f"Unique Gangnam URLs: {len(unique_urls)}")
        
        if len(gangnam_items) != len(unique_urls):
            print("WARNING: Duplicates found!")
            print(f"Duplicate Count: {len(gangnam_items) - len(unique_urls)}")
            # counts = Counter(urls)
            # print("Top duplicates:", counts.most_common(3))
        else:
            print("SUCCESS: No duplicates.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
