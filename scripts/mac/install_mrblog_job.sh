#!/bin/bash
# 미블 수집을 Mac에서 1시간마다 실행하도록 등록한다 (launchd). 강남맛집·포블로그 작업과는 별도.
# 사용법: bash scripts/mac/install_mrblog_job.sh
#  - 먼저 로그인 프로필을 만들어야 한다:  venv/bin/python scripts/mac/mrblog_login.py
#  - R2 설정(~/.config/reviewerscanner/r2.env)은 강남맛집 작업과 같은 파일을 쓴다.
#  - 코드를 수정한 뒤에는 이 스크립트를 다시 실행해야 반영된다.
set -euo pipefail

SRC="$(cd "$(dirname "$0")/../.." && pwd)"
HOME_DIR="$HOME/.reviewerscanner"
ENV_FILE="$HOME/.config/reviewerscanner/r2.env"
PROFILE="$HOME_DIR/profiles/mrblog"
LABEL="com.reviewerscanner.mrblog"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG="$HOME/Library/Logs/reviewerscanner-mrblog.log"

[ -f "$ENV_FILE" ] || { echo "$ENV_FILE 가 없습니다. 먼저 scripts/mac/install_kangnam_job.sh 를 실행하세요."; exit 1; }
[ -d "$PROFILE" ] || { echo "로그인 프로필($PROFILE)이 없습니다. 먼저 venv/bin/python scripts/mac/mrblog_login.py 로 로그인하세요."; exit 1; }

echo "→ 실행 환경 준비: $HOME_DIR"
mkdir -p "$HOME_DIR"
rsync -a --delete --exclude '__pycache__' --exclude 'serviceAccountKey.json' --exclude 'test_*' --exclude 'debug_*' "$SRC/crawler/" "$HOME_DIR/crawler/"
if [ ! -x "$HOME_DIR/venv/bin/python" ]; then python3 -m venv "$HOME_DIR/venv"; fi
"$HOME_DIR/venv/bin/pip" install -q --upgrade pip
"$HOME_DIR/venv/bin/pip" install -q requests beautifulsoup4 lxml boto3 playwright
"$HOME_DIR/venv/bin/python" -m playwright install chromium >/dev/null 2>&1 || true

echo "→ launchd 등록: $LABEL (1시간마다)"
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
    <string>$HOME_DIR/crawler/run_mrblog.py</string>
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
echo "✓ 등록 완료. 지금 한 번 실행 중입니다(약 7분). 로그 확인:  tail -f $LOG"
echo "제거:  launchctl bootout gui/\$(id -u) $PLIST && rm $PLIST"
echo "주의: 미블 로그인 프로필은 한 번에 한 프로그램만 열 수 있다. 수집 중에 mrblog_login.py 를 실행하지 마세요."
