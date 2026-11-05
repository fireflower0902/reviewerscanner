#!/bin/bash
# 강남맛집 수집을 Mac에서 1시간마다 실행하도록 등록한다 (launchd).
# 사용법: bash scripts/mac/install_kangnam_job.sh
#  - 처음 실행하면 R2 설정 파일(~/.config/reviewerscanner/r2.env) 템플릿만 만들고 종료한다.
#    값을 채운 뒤 다시 실행하면 등록된다.
#  - 코드를 수정한 뒤에는 이 스크립트를 다시 실행해야 반영된다.
set -euo pipefail

SRC="$(cd "$(dirname "$0")/../.." && pwd)"
HOME_DIR="$HOME/.reviewerscanner"            # ~/Documents 는 launchd가 접근하지 못할 수 있어 별도 위치에 복사해서 실행
ENV_DIR="$HOME/.config/reviewerscanner"
ENV_FILE="$ENV_DIR/r2.env"
LABEL="com.reviewerscanner.kangnam"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/reviewerscanner-kangnam.log"

mkdir -p "$ENV_DIR" && chmod 700 "$ENV_DIR"
if [ ! -f "$ENV_FILE" ]; then
  cat > "$ENV_FILE" <<'EOT'
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=
R2_BUCKET=
EOT
  chmod 600 "$ENV_FILE"
  echo "1) $ENV_FILE 파일을 열어 4개 값을 채워 주세요 (Cloudflare R2 토큰)."
  echo "2) 그 다음 이 스크립트를 다시 실행하세요."
  exit 0
fi
if grep -q '=$' "$ENV_FILE"; then
  echo "$ENV_FILE 에 비어 있는 값이 있습니다. 4개 값을 모두 채운 뒤 다시 실행하세요."
  exit 1
fi

echo "→ 실행 환경 준비: $HOME_DIR"
mkdir -p "$HOME_DIR"
rsync -a --delete --exclude '__pycache__' --exclude 'serviceAccountKey.json' --exclude 'test_*' --exclude 'debug_*' "$SRC/crawler/" "$HOME_DIR/crawler/"
if [ ! -x "$HOME_DIR/venv/bin/python" ]; then
  python3 -m venv "$HOME_DIR/venv"
fi
"$HOME_DIR/venv/bin/pip" install -q --upgrade pip
"$HOME_DIR/venv/bin/pip" install -q requests beautifulsoup4 lxml boto3

echo "→ launchd 등록: $LABEL (1시간마다 + 로그인/깨어날 때)"
mkdir -p "$HOME/Library/LaunchAgents" "$(dirname "$LOG")"
cat > "$PLIST" <<EOT
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$HOME_DIR/venv/bin/python</string>
    <string>$HOME_DIR/crawler/run_kangnam.py</string>
  </array>
  <key>WorkingDirectory</key><string>$HOME_DIR/crawler</string>
  <key>StartInterval</key><integer>3600</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$LOG</string>
  <key>StandardErrorPath</key><string>$LOG</string>
</dict>
</plist>
EOT

launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo
echo "✓ 등록 완료. 지금 한 번 실행 중입니다. 로그 확인:  tail -f $LOG"
echo
echo "(선택) 매일 아침 노트북을 자동으로 깨우려면 아래 명령을 직접 실행하세요 (관리자 권한 필요):"
echo "  sudo pmset repeat wakeorpoweron MTWRFSU 07:55:00"
echo "해제:  sudo pmset repeat cancel"
echo "제거:  bash scripts/mac/uninstall_kangnam_job.sh"
