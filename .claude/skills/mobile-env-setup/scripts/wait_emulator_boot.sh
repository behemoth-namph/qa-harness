#!/usr/bin/env bash
# Đợi emulator khởi động xong (sys.boot_completed = 1).
# Chạy: bash wait_emulator_boot.sh <serial emulator-XXXX> [timeout_giay=240]
# Từ chối serial không bắt đầu bằng "emulator-" để không vô tình thao tác lên thiết bị thật.

SERIAL="$1"
TIMEOUT="${2:-240}"
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}"
ADB="$SDK/platform-tools/adb"

case "$SERIAL" in
  emulator-*) ;;
  *) echo "Từ chối: serial '$SERIAL' không phải emulator-*." >&2; exit 2 ;;
esac

start=$(date +%s)
"$ADB" -s "$SERIAL" wait-for-device 2>/dev/null
while true; do
  b=$("$ADB" -s "$SERIAL" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')
  [ "$b" = "1" ] && { echo "Emulator $SERIAL đã sẵn sàng."; exit 0; }
  now=$(date +%s)
  if [ $((now - start)) -ge "$TIMEOUT" ]; then
    echo "Quá $TIMEOUT giây mà emulator $SERIAL chưa khởi động xong." >&2
    exit 1
  fi
  sleep 3
done
