import json

def run():
    try:
        with open("public/campaigns.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        gangnam_items = [d for d in data if d.get('platform') == '강남맛집']
        print(f"Total Gangnam Items: {len(gangnam_items)}")
        
        hanam_items = []
        for item in gangnam_items:
            title = item.get('title', '')
            region = item.get('region', {})
            # Check normalized region or title
            if "하남" in title or "하남" in region.get('city', ''):
                hanam_items.append(item['title'])
                
        print(f"Gangnam Hanam Items: {len(hanam_items)}")
        if len(hanam_items) > 0:
            print("Examples:")
            for t in hanam_items[:10]:
                print(f" - {t}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
