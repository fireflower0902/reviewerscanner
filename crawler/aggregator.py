"""
리뷰어스캐너 크롤러 오케스트레이터
- 9개 사이트별 모듈이 각자 독립 브라우저로 동시 실행
- asyncio.Semaphore(5)로 최대 5개 동시 실행 제한 (GitHub Actions 메모리 보호)
- 각 모듈 위치: crawler/crawlers/{사이트명}.py
"""
import asyncio
import json
import os
import random
from typing import List, Dict

from crawlers import kangnam, reviewplace, reviewnote, dinnerqueen
from crawlers import seouloppa, cometoplay, revu, fourblog, ohmyblog

MIN_ITEMS_TO_UPLOAD = int(os.environ.get("MIN_ITEMS_TO_UPLOAD", "5000"))

_CRAWLERS = [
    ("강남맛집",    kangnam.run),
    ("리뷰플레이스", reviewplace.run),
    ("리뷰노트",    reviewnote.run),
    ("디너의여왕",  dinnerqueen.run),
    ("서울오빠",    seouloppa.run),
    ("놀러와체험단", cometoplay.run),
    ("레뷰",       revu.run),
    ("포블로그",    fourblog.run),
    ("오마이블로그", ohmyblog.run),
]


async def run_aggregator():
    # 최대 5개 크롤러 동시 실행 (Chromium 메모리 ~700MB/개 × 5 = 3.5GB, GitHub Actions 7GB 이내)
    sem = asyncio.Semaphore(5)

    async def run_with_sem(name: str, run_func) -> List[Dict]:
        async with sem:
            print(f"\n[System] ▶ Starting: {name}")
            try:
                results = await run_func()
                print(f"[System] ✓ Done: {name} — {len(results)} items")
                return results
            except Exception as e:
                print(f"[System] ✗ Failed: {name} — {e}")
                return []

    tasks = [run_with_sem(name, func) for name, func in _CRAWLERS]
    results_list = await asyncio.gather(*tasks)

    all_campaigns: List[Dict] = [item for sublist in results_list for item in sublist]
    random.shuffle(all_campaigns)

    # 플랫폼별 수집 수 출력
    print(f"\n[Summary] Total: {len(all_campaigns)} items")
    from collections import Counter
    counts = Counter(c["platform"] for c in all_campaigns)
    for platform, count in sorted(counts.items()):
        print(f"  - {platform}: {count}")

    # JSON 저장 (프로젝트 루트/public/campaigns.json)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    public_dir = os.path.join(project_root, "public")
    os.makedirs(public_dir, exist_ok=True)
    output_path = os.path.join(public_dir, "campaigns.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_campaigns, f, indent=2, ensure_ascii=False)
    print(f"\n[System] Saved → {output_path}")

    # R2 업로드 (사이트가 읽는 데이터 파일)
    import r2_client
    if not r2_client.is_configured():
        print("[R2] R2_* 환경변수가 없어 업로드를 건너뜁니다 (로컬 실행)")
        return

    # 크롤러 대량 실패로 데이터가 크게 줄었을 때 기존 파일을 덮어쓰지 않는 안전장치
    if len(all_campaigns) < MIN_ITEMS_TO_UPLOAD:
        raise RuntimeError(
            f"수집 건수({len(all_campaigns)})가 최소 기준({MIN_ITEMS_TO_UPLOAD}) 미만이라 업로드하지 않습니다"
        )
    try:
        r2_client.upload_campaigns(all_campaigns)
    except Exception as e:
        print(f"[R2] ❌ FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_aggregator())
