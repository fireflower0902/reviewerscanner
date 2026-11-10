"""
리뷰어스캐너 크롤러 오케스트레이터
- 7개 사이트별 모듈이 각자 독립 브라우저로 동시 실행
- 서울오빠(간헐 차단)·강남맛집·포블로그·미블은 Mac이 수집(run_*.py)한다. 강남맛집·포블로그는 GitHub Actions(데이터센터 IP)에서 차단되어 한국 IP 기기가 수집(run_local_sources.py)하고, 여기서는 R2의 부분 파일을 합친다
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

from helpers import normalize_dday, shift_dday

from crawlers import reviewplace, reviewnote, dinnerqueen
from crawlers import cometoplay, revu, ohmyblog

# 크롤러 하나가 이 시간(초) 넘게 응답하지 않으면 그 사이트만 포기하고 나머지는 계속 진행한다
CRAWLER_TIMEOUT = int(os.environ.get("CRAWLER_TIMEOUT", "900"))   # 사이트당 최대 15분 (정상은 5분 안팎, 레뷰·리뷰노트가 가장 오래 걸림)
MIN_ITEMS_TO_UPLOAD = int(os.environ.get("MIN_ITEMS_TO_UPLOAD", "5000"))

# 한국 IP 기기가 별도로 수집해서 R2에 올리는 사이트(부분 파일 이름)
LOCAL_PARTS = ["kangnam", "fourblog", "mrblog", "seouloppa"]

_CRAWLERS = [
    ("리뷰플레이스", reviewplace.run),
    ("리뷰노트",    reviewnote.run),
    ("디너의여왕",  dinnerqueen.run),
    ("놀러와체험단", cometoplay.run),
    ("레뷰",       revu.run),
    ("오마이블로그", ohmyblog.run),
]


def carry_over_missing(new_items, prev_items, prev_generated_at, now=None,
                       min_prev=50, ratio=0.5, max_age_hours=36):
    """수집에 실패해 건수가 크게 줄어든 사이트는 직전 데이터를 그대로 유지한다.

    플랫폼별로 (직전 건수 >= min_prev) 이고 (이번 건수 < 직전 건수 * ratio) 이면 그 사이트의 직전 항목을 가져온다.
    직전 데이터가 max_age_hours보다 오래됐으면 쓰지 않는다. 마감 표기는 지난 날짜만큼 보정하고 마감 지난 항목은 뺀다.
    반환: (가져온 항목 목록, {플랫폼: (이번 건수, 직전 건수, 유지한 건수)})"""
    from collections import Counter
    if not prev_items or not prev_generated_at:
        return [], {}
    now = now or datetime.datetime.now(datetime.timezone.utc)
    prev_dt = datetime.datetime.fromisoformat(prev_generated_at)
    if (now - prev_dt).total_seconds() / 3600 > max_age_hours:
        return [], {}
    kst = datetime.timezone(datetime.timedelta(hours=9))
    days_passed = (now.astimezone(kst).date() - prev_dt.astimezone(kst).date()).days

    new_counts = Counter(c["platform"] for c in new_items)
    prev_counts = Counter(c["platform"] for c in prev_items)
    targets = {p for p, pc in prev_counts.items() if pc >= min_prev and new_counts.get(p, 0) < pc * ratio}

    carried, info = [], {}
    for p in targets:
        kept = 0
        for it in prev_items:
            if it["platform"] != p:
                continue
            dday = shift_dday(it["meta"].get("dday", ""), days_passed)
            if dday is None:
                continue
            carried.append({**it, "meta": {**it["meta"], "dday": dday}})
            kept += 1
        info[p] = (new_counts.get(p, 0), prev_counts[p], kept)
    return carried, info


async def run_aggregator():
    # 마감 표기(N일 남음)는 수집 시점 기준이므로 시작 시각을 기록해 R2 메타데이터로 전달한다
    generated_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    run_started = time.time()

    # 동시 실행 수 (기본 9 = 전부 동시). Chromium ~700MB/개 × 9 ≈ 6GB — 공개 저장소용 GitHub 러너(16GB) 기준
    sem = asyncio.Semaphore(int(os.environ.get("CRAWLER_CONCURRENCY", "9")))

    outcomes: List[Dict] = []   # 사이트별 결과 기록(→ run_report.json)

    async def run_with_sem(name: str, run_func) -> List[Dict]:
        async with sem:
            print(f"\n[System] ▶ Starting: {name}")
            started = time.time()
            try:
                results = await asyncio.wait_for(run_func(), timeout=CRAWLER_TIMEOUT)
                print(f"[System] ✓ Done: {name} — {len(results)} items ({time.time() - started:.0f}s)")
                outcomes.append({"name": name, "status": "ok", "count": len(results), "seconds": round(time.time() - started)})
                return results
            except asyncio.TimeoutError:
                print(f"[System] ✗ Timeout: {name} — {CRAWLER_TIMEOUT}초 안에 끝나지 않아 건너뜁니다")
                outcomes.append({"name": name, "status": "timeout", "count": 0, "seconds": round(time.time() - started)})
                return []
            except Exception as e:
                print(f"[System] ✗ Failed: {name} — {e} ({time.time() - started:.0f}s)")
                outcomes.append({"name": name, "status": "failed", "count": 0, "seconds": round(time.time() - started),
                                 "error": f"{type(e).__name__}: {str(e)[:200]}"})
                return []

    tasks = [run_with_sem(name, func) for name, func in _CRAWLERS]
    results_list = await asyncio.gather(*tasks)

    all_campaigns: List[Dict] = [item for sublist in results_list for item in sublist]
    # 한국 IP 기기가 별도로 수집해 R2에 올린 부분 파일(강남맛집) 합치기
    import r2_client
    if r2_client.is_configured():
        max_age = float(os.environ.get("PART_MAX_AGE_HOURS", os.environ.get("KANGNAM_MAX_AGE_HOURS", "36")))
        for part_name in LOCAL_PARTS:
            all_campaigns.extend(r2_client.load_part(part_name, max_age_hours=max_age))

    # 일부 사이트가 실패해 건수가 절반 아래로 줄었으면 그 사이트는 직전 데이터를 유지한다(목록에서 통째로 사라지는 것 방지)
    carry_info: Dict = {}
    if r2_client.is_configured():
        prev_items, prev_generated_at = r2_client.load_previous()
        carried, info = carry_over_missing(all_campaigns, prev_items, prev_generated_at)
        carry_info = {p: {"this_run": n, "previous": pv, "kept": k} for p, (n, pv, k) in info.items()}
        if info:
            all_campaigns = [c for c in all_campaigns if c["platform"] not in info] + carried
            for plat, (new_n, prev_n, kept) in info.items():
                print(f"[System] ⚠ {plat}: 이번 수집 {new_n}건(직전 {prev_n}건)으로 줄어 직전 데이터 {kept}건을 유지합니다")

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

    # 실행 보고서(원인 추적용): 업로드 성공 여부와 무관하게 먼저 남긴다. 실패해도 본 작업에는 영향 없음
    try:
        r2_client.upload_report({
            "generated_at": generated_at,
            "finished_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "duration_seconds": round(time.time() - run_started),
            "crawler_timeout_seconds": CRAWLER_TIMEOUT,
            "total": len(all_campaigns),
            "platform_counts": dict(counts),
            "crawlers": sorted(outcomes, key=lambda o: o["name"]),
            "carried_over": carry_info,
        })
    except Exception as e:
        print(f"[R2] 실행 보고서 업로드 실패(무시): {e}")

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
