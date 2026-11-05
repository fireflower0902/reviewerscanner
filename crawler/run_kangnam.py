"""강남맛집 단독 수집 → R2 부분 파일 업로드 (한국 IP 기기에서 실행)

GitHub Actions(해외 IP)는 강남맛집에 접속할 수 없어서, 한국에 있는 Mac 등에서 이 스크립트를
주기적으로 실행한다. 결과는 R2의 v1/parts/kangnam.json.gz 로 올라가고, GitHub의 aggregator가 합친다.

R2 자격증명: 환경변수 또는 ~/.config/reviewerscanner/r2.env (KEY=VALUE 형식, 권한 600)
"""
import os
import sys
import time

MIN_ITEMS = int(os.environ.get("KANGNAM_MIN_ITEMS", "1500"))  # 이보다 적으면 비정상으로 보고 업로드하지 않음
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
        print(f"[Kangnam] R2 설정이 없습니다. {ENV_FILE} 를 확인하세요.")
        return 2

    from crawlers import kangnam
    try:
        items = kangnam.collect()
    except kangnam.Unreachable as e:
        print(f"[Kangnam] ✗ {e} — VPN이 켜져 있거나 해외 네트워크일 수 있습니다. 업로드하지 않습니다.")
        return 1

    if len(items) < MIN_ITEMS:
        print(f"[Kangnam] ✗ 수집 건수 {len(items)}가 최소 기준 {MIN_ITEMS}보다 적어 업로드하지 않습니다.")
        return 1

    r2_client.upload_part("kangnam", "강남맛집", items)
    print(f"[Kangnam] ✓ 완료 ({time.time() - started:.0f}초)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
