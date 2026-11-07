"""미블(mrblog.net) 수집 → R2 부분 파일(v1/parts/mrblog.json.gz) 업로드 — Mac 전용, 1시간마다

- 강남맛집·포블로그(run_local_sources.py)와 따로 돌린다: 미블은 느리고(약 7분) 로그인 프로필이 필요하다.
- 로그인 프로필: ~/.reviewerscanner/profiles/mrblog  (scripts/mac/mrblog_login.py 로 한 번 로그인해 저장)
- 실패하면 업로드하지 않는다 → 직전 부분 파일(36시간 이내)이 그대로 쓰인다.
- 로그인이 만료되면 macOS 알림을 띄운다 (하루 한 번).
"""
import asyncio
import os
import subprocess
import sys
import time

ENV_FILE = os.environ.get("R2_ENV_FILE") or os.path.expanduser("~/.config/reviewerscanner/r2.env")
ALERT_STATE = os.path.expanduser("~/.reviewerscanner/mrblog_login_alert_at")
MIN_ITEMS = int(os.environ.get("MRBLOG_MIN_ITEMS", "500"))     # 이보다 적으면 비정상으로 보고 업로드하지 않음 (정상 약 2,000건)


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


def notify_login_needed(message: str) -> None:
    """로그인 만료 알림 — 하루에 한 번만"""
    try:
        if os.path.exists(ALERT_STATE) and time.time() - os.path.getmtime(ALERT_STATE) < 20 * 3600:
            return
        os.makedirs(os.path.dirname(ALERT_STATE), exist_ok=True)
        open(ALERT_STATE, "w").close()
        subprocess.run(["osascript", "-e",
                        f'display notification "{message}" with title "체험단스캐너 · 미블 로그인 필요" sound name "Glass"'],
                       timeout=10, check=False)
    except Exception:
        pass


def main() -> int:
    started = time.time()
    load_env_file(ENV_FILE)
    import r2_client
    if not r2_client.is_configured():
        print(f"[MrBlog] R2 설정이 없습니다. {ENV_FILE} 를 확인하세요.")
        return 2

    from crawlers import mrblog
    try:
        items = asyncio.run(asyncio.wait_for(mrblog.run(), timeout=int(os.environ.get("MRBLOG_TIMEOUT", "1500"))))
    except mrblog.LoginRequired as e:
        print(f"[MrBlog] ✗ 로그인 필요: {e}")
        notify_login_needed("로그인이 만료됐어요. scripts/mac/mrblog_login.py 를 다시 실행해 주세요.")
        return 3
    except asyncio.TimeoutError:
        print("[MrBlog] ✗ 제한 시간 초과 — 업로드하지 않습니다.")
        return 1
    except Exception as e:
        print(f"[MrBlog] ✗ 예상치 못한 오류 {type(e).__name__}: {e}")
        return 1

    if len(items) < MIN_ITEMS:
        print(f"[MrBlog] ✗ 수집 건수 {len(items)}가 최소 기준 {MIN_ITEMS}보다 적어 업로드하지 않습니다.")
        return 1
    r2_client.upload_part("mrblog", "미블", items)
    print(f"[MrBlog] ✓ 완료 ({time.time() - started:.0f}초, {len(items)}건)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
