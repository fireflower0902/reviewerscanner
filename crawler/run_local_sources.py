"""한국 가정용 IP 기기(Mac 등)에서 수집하는 사이트들 → R2 부분 파일 업로드

GitHub Actions(데이터센터 IP)에서는 아래 사이트가 막힌다.
  - 강남맛집: 연결 자체가 안 맺어짐(해외 IP 차단 추정)
  - 포블로그: Cloudflare 봇 방어가 '더 불러오기' 요청을 403으로 거부
이 스크립트를 주기적으로 실행하면 결과가 R2의 v1/parts/<이름>.json.gz 로 올라가고,
GitHub의 aggregator가 합친다. 사이트 하나가 실패해도 나머지는 계속 진행한다.

R2 자격증명: 환경변수 또는 ~/.config/reviewerscanner/r2.env (KEY=VALUE 형식, 권한 600)
"""
import os
import sys
import time

ENV_FILE = os.environ.get("R2_ENV_FILE") or os.path.expanduser("~/.config/reviewerscanner/r2.env")


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
        print(f"[Local] R2 설정이 없습니다. {ENV_FILE} 를 확인하세요.")
        return 2

    from crawlers import kangnam, fourblog
    # (부분 파일 이름, 플랫폼 표시명, 수집 함수, 비정상 판단 최소 건수, 접속 불가 예외)
    sources = [
        ("kangnam", "강남맛집", kangnam.collect, int(os.environ.get("KANGNAM_MIN_ITEMS", "1500")), kangnam.Unreachable),
        ("fourblog", "포블로그", fourblog.collect, int(os.environ.get("FOURBLOG_MIN_ITEMS", "200")), fourblog.Unreachable),
    ]

    failed = 0
    for name, platform, collect, min_items, unreachable in sources:
        t = time.time()
        try:
            items = collect()
        except unreachable as e:
            print(f"[Local] ✗ {platform}: {e} — VPN이 켜져 있거나 해외 네트워크일 수 있습니다. 업로드하지 않습니다.")
            failed += 1
            continue
        except Exception as e:
            print(f"[Local] ✗ {platform}: 예상치 못한 오류 {type(e).__name__}: {e}")
            failed += 1
            continue
        if len(items) < min_items:
            print(f"[Local] ✗ {platform}: 수집 건수 {len(items)}가 최소 기준 {min_items}보다 적어 업로드하지 않습니다.")
            failed += 1
            continue
        r2_client.upload_part(name, platform, items)
        print(f"[Local] ✓ {platform} 완료 ({time.time() - t:.0f}초)")

    print(f"[Local] 전체 종료 ({time.time() - started:.0f}초, 실패 {failed}건)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
