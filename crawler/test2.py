import requests

# ReviewNote API
url = "https://www.reviewnote.co.kr/api/v2/campaigns?s=popular&limit=1&page=0"
res = requests.get(url).json()
print("ReviewNote keys:", res['objects'][0].keys())
print("ReviewNote obj:", res['objects'][0])

