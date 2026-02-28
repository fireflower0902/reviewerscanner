import asyncio
from playwright.async_api import async_playwright

async def test_ohmyblog_dynamic():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()

        # 1. Fetch Regions
        region_map = {}
        try:
            res_region = await context.request.get("https://www.ohmyblog.co.kr/api/web/region?action=list")
            if res_region.ok:
                region_data = await res_region.json()
                for country in region_data.get("data", []):
                    province_name = country.get("name", "")
                    for area in country.get("areas", []):
                        g_seq = str(area.get("country_groupSeq", ""))
                        a_name = area.get("area", "")
                        region_map[g_seq] = f"{province_name} {a_name}".strip()
            print(f"Loaded {len(region_map)} region mappings.")
            if region_map:
                print(f"Example Region 2: {region_map.get('2')}")
        except Exception as e:
            print(f"Region fetch error: {e}")

        # 2. Category Array
        categories = [
            ("A", "음식점"),
            ("B", "뷰티"),
            ("C", "여행"),
            ("D", "문화"),
            ("E", "생활"),
            ("F", "생활"),
        ]
        
        # 3. Fetch Campaigns for Category 'A' (Food)
        try:
            cat_code, ct_name = categories[0]
            url = f"https://www.ohmyblog.co.kr/api/web/campaign/active?page=1&limit=2&app_type=A&app_cate_detail={cat_code}"
            res = await context.request.get(url)
            if res.ok:
                data = await res.json()
                campaigns = data.get('data', {}).get('campaigns', [])
                print(f"\\nFound campaigns for category {ct_name}:")
                for c in campaigns:
                    title = c.get('app_title', '')
                    g_seq = str(c.get('country_groupSeq', ''))
                    mapped_region = region_map.get(g_seq, "기타")
                    print(f"  Title: {title}")
                    print(f"  Region seq '{g_seq}' -> {mapped_region}")
        except Exception as e:
            print(f"Error fetching campaigns: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_ohmyblog_dynamic())
