"""미블(mrblog.net) 로그인 프로필 저장 도구 (Mac에서 한 번 실행)

- 브라우저 창이 열리면 사람이 직접 로그인한다 (네이버 로그인 + 보안 확인 포함).
- 로그인 상태(쿠키 등)는 이 Mac의 전용 프로필 폴더에만 저장된다. 저장소(git)에는 올라가지 않는다.
    프로필 위치: ~/.reviewerscanner/profiles/mrblog   (권한 700)
- 이후 크롤러는 이 프로필을 재사용해 로그인 없이 목록을 읽는다. 세션이 만료되면 이 도구를 다시 실행한다.

사용: crawler 폴더의 venv 파이썬으로 실행
    venv/bin/python scripts/mac/mrblog_login.py          # 로그인 저장
    venv/bin/python scripts/mac/mrblog_login.py --check  # 저장된 로그인이 아직 유효한지 확인(창 없이)
"""
import asyncio
import os
import re
import sys
from playwright.async_api import async_playwright

PROFILE_DIR = os.path.expanduser("~/.reviewerscanner/profiles/mrblog")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0.0.0 Safari/537.36")
WAIT_MINUTES = 15


async def count_campaign_links(page) -> int:
    await page.goto("https://www.mrblog.net/campaigns/region", wait_until="domcontentloaded", timeout=60000)
    await page.wait_for_timeout(4000)
    if "/login" in page.url:
        return -1
    return await page.evaluate(
        "[...new Set([...document.querySelectorAll('a')].map(a => a.getAttribute('href')||'').filter(h => /\\/campaigns\\/\\d+/.test(h)))].length"
    )


async def main(check_only: bool):
    os.makedirs(PROFILE_DIR, exist_ok=True)
    os.chmod(PROFILE_DIR, 0o700)
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            PROFILE_DIR,
            headless=check_only,
            user_agent=UA,
            locale="ko-KR",
            viewport={"width": 1100, "height": 850},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        if check_only:
            n = await count_campaign_links(page)
            print("로그인 유효: 캠페인 링크 %d개" % n if n >= 0 else "로그인 만료 — 다시 저장해 주세요")
            await ctx.close()
            return 0 if n >= 0 else 1

        await page.goto("https://www.mrblog.net/login", wait_until="domcontentloaded", timeout=60000)
        print("브라우저 창에서 미블에 로그인해 주세요 (네이버로 로그인). 최대 %d분 기다립니다." % WAIT_MINUTES, flush=True)
        for _ in range(WAIT_MINUTES * 30):
            await asyncio.sleep(2)
            try:
                url = page.url
            except Exception:
                print("창이 닫혔습니다."); return 1
            if re.match(r"https://(www\.)?mrblog\.net/", url) and "/login" not in url:
                break
        else:
            print("시간 초과 — 로그인이 확인되지 않았습니다."); await ctx.close(); return 1

        n = await count_campaign_links(page)
        print("저장 완료. 로그인 확인: 지역 목록 캠페인 링크 %d개" % n if n >= 0 else "로그인이 확인되지 않았습니다.", flush=True)
        await ctx.close()
        return 0 if n >= 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main("--check" in sys.argv)))
