"""서울오빠(seoulouba.co.kr) 수집 → R2 부분 파일(v1/parts/seouloppa.json.gz) 업로드 — Mac 전용, 1시간마다

- GitHub Actions(데이터센터 IP)에서는 간헐적으로 차단되어, 한국 가정용 IP인 Mac에서 수집한다.
- 정상 수집은 30~50초. 실패하거나 건수가 비정상적으로 적으면 업로드하지 않는다
  → 직전 부분 파일(36시간 이내)이 그대로 쓰인다.
"""
import asyncio
import os
import sys
import time

ENV_FILE = os.environ.get("R2_ENV_FILE") or os.path.expanduser("~/.config/reviewerscanner/r2.env")
MIN_ITEMS = int(os.environ.get("SEOULOPPA_MIN_ITEMS", "800"))   # 이보다 적으면 비정상으로 보고 업로드하지 않음 (정상 약 1,700건)


def load_env_file(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main() -> int:
    started = time.time()
    load_env_file(ENV_FILE)
    import r2_client
    if not r2_client.is_configured():
        print(f"[SeoulOppa] R2 설정이 없습니다. {ENV_FILE} 를 확인하세요.")
        return 2

    from crawlers import seouloppa
    try:
        items = asyncio.run(asyncio.wait_for(seouloppa.run(), timeout=600))
    except asyncio.TimeoutError:
        print("[SeoulOppa] ✗ 제한 시간 초과 — 업로드하지 않습니다.")
        return 1
    except Exception as e:
        print(f"[SeoulOppa] ✗ {type(e).__name__}: {e} — 업로드하지 않습니다.")
        return 1

    if len(items) < MIN_ITEMS:
        print(f"[SeoulOppa] ✗ 수집 건수 {len(items)}가 최소 기준 {MIN_ITEMS}보다 적어 업로드하지 않습니다.")
        return 1
    r2_client.upload_part("seouloppa", "서울오빠", items)
    print(f"[SeoulOppa] ✓ 완료 ({time.time() - started:.0f}초, {len(items)}건)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
