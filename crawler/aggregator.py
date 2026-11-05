"""
리뷰어스캐너 크롤러 오케스트레이터
- 8개 사이트별 모듈이 각자 독립 브라우저로 동시 실행
- 강남맛집은 해외 IP(GitHub Actions)에서 접속이 차단되어 별도 기기가 수집(run_kangnam.py)하고, 여기서는 R2의 부분 파일을 합친다
- asyncio.Semaphore(CRAWLER_CONCURRENCY, 기본 9)로 동시 실행 수 제한 (GitHub Actions 메모리 보호)
- 각 모듈 위치: crawler/crawlers/{사이트명}.py
"""
import asyncio
import datetime
import json
import os
import random
import time
from typing import List, Dict

from helpers import normalize_dday

from crawlers import reviewplace, reviewnote, dinnerqueen
from crawlers import seouloppa, cometoplay, revu, fourblog, ohmyblog

MIN_ITEMS_TO_UPLOAD = int(os.environ.get("MIN_ITEMS_TO_UPLOAD", "5000"))

_CRAWLERS = [
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
    # 마감 표기(N일 남음)는 수집 시점 기준이므로 시작 시각을 기록해 R2 메타데이터로 전달한다
    generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # 동시 실행 수 (기본 9 = 전부 동시). Chromium ~700MB/개 × 9 ≈ 6GB — 공개 저장소용 GitHub 러너(16GB) 기준
    sem = asyncio.Semaphore(int(os.environ.get("CRAWLER_CONCURRENCY", "9")))

    async def run_with_sem(name: str, run_func) -> List[Dict]:
        async with sem:
            print(f"\n[System] ▶ Starting: {name}")
            started = time.time()
            try:
                results = await run_func()
                print(f"[System] ✓ Done: {name} — {len(results)} items ({time.time() - started:.0f}s)")
                return results
            except Exception as e:
                print(f"[System] ✗ Failed: {name} — {e} ({time.time() - started:.0f}s)")
                return []

    tasks = [run_with_sem(name, func) for name, func in _CRAWLERS]
    results_list = await asyncio.gather(*tasks)

    all_campaigns: List[Dict] = [item for sublist in results_list for item in sublist]
    # 한국 IP 기기가 별도로 수집해 R2에 올린 부분 파일(강남맛집) 합치기
    import r2_client
    if r2_client.is_configured():
        max_age = float(os.environ.get("KANGNAM_MAX_AGE_HOURS", "36"))
        all_campaigns.extend(r2_client.load_part("kangnam", max_age_hours=max_age))

    for c in all_campaigns:
        c["meta"]["dday"] = normalize_dday(c["meta"].get("dday", ""))
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
        r2_client.upload_campaigns(all_campaigns, generated_at=generated_at)
    except Exception as e:
        print(f"[R2] ❌ FAILED: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_aggregator())
