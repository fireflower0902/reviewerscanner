import requests
from bs4 import BeautifulSoup

def run():
    url = "https://www.seoulouba.co.kr/campaign"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    items = soup.select(".campaign_content")
    print(f"Total .campaign_content items: {len(items)}")
    if items:
        # Print inner HTML of first item
        print("First item contents:")
        print(items[0].prettify()[:2000])

if __name__ == "__main__":
    run()
