#!/bin/bash
# install_kangnam_job.sh 로 등록한 작업을 제거한다. (R2 설정 파일은 남겨 둔다)
LABEL="com.reviewerscanner.kangnam"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
rm -rf "$HOME/.reviewerscanner"
echo "제거 완료. (R2 설정 파일은 그대로: ~/.config/reviewerscanner/r2.env — 필요 없으면 직접 삭제하세요)"
