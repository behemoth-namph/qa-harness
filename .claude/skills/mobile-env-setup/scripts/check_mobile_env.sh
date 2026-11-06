#!/usr/bin/env bash
# Kiểm tra môi trường test mobile Android và IN KẾ HOẠCH CÀI ĐẶT cho phần còn thiếu.
# CHỈ ĐỌC: không cài, không khởi động, không sửa file nào, không đụng ~/.zshrc.
#
# Chạy: bash .claude/skills/mobile-env-setup/scripts/check_mobile_env.sh
# Thoát 0 nếu đủ điều kiện chạy test; 1 nếu còn thiếu. Dòng cuối cùng luôn là
#   MISSING_ITEMS=<danh sách id cách nhau bởi dấu phẩy, hoặc none>
# để orchestrator đọc máy được. Id có thể là: homebrew, jdk, sdk, cmdline-tools, platform-tools,
# emulator, system-image, avd, maestro.
#
# Script dò: hệ điều hành, chip (Intel/Apple Silicon), Homebrew, JDK, Android Studio, Android SDK,
# system image đã tải, AVD, Maestro (có kiểm tra đúng là Maestro của mobile.dev, xem ghi chú bên dưới).
# Không in biến môi trường, tài khoản hay dữ liệu trên thiết bị.
#
# Ghi chú quan trọng: tên ngắn `maestro` trong Homebrew (brew install maestro) là MỘT PHẦN MỀM KHÁC
# ("AI agent command center"). Maestro test mobile phải cài bằng tên đầy đủ mobile-dev-inc/tap/maestro.

OS="$(uname -s)"
ARCH="$(uname -m)"
case "$ARCH" in arm64|aarch64) ABI="arm64-v8a" ;; *) ABI="x86_64" ;; esac
API_LEVEL="34"          # bản Android mặc định gợi ý cho system image mới (ổn định, phổ biến)
AVD_NAME="qa_test"      # tên AVD riêng cho QA
MISSING=""
add_missing() { MISSING="${MISSING:+$MISSING,}$1"; }
has_missing() { case ",$MISSING," in *",$1,"*) return 0 ;; *) return 1 ;; esac; }

ok()   { printf 'OK     %s\n' "$1"; }
miss() { printf 'THIẾU  %s\n' "$1"; add_missing "$2"; }
info() { printf '       %s\n' "$1"; }

echo "Hệ điều hành: $OS $ARCH"

# ---------------- Homebrew (macOS/Linux) ----------------
BREW=""
for c in "$(command -v brew 2>/dev/null)" /opt/homebrew/bin/brew /usr/local/bin/brew /home/linuxbrew/.linuxbrew/bin/brew; do
  [ -n "$c" ] && [ -x "$c" ] && BREW="$c" && break
done
if [ -n "$BREW" ]; then
  BREW_PREFIX="$("$BREW" --prefix 2>/dev/null)"
  ok "Homebrew ($BREW)"
else
  BREW_PREFIX=""
  miss "Homebrew (trình quản lý gói; dùng để cài JDK, Android SDK, Maestro)" homebrew
fi

# ---------------- JDK (Maestro và sdkmanager cần JDK 17 trở lên) ----------------
# /usr/bin/java trên macOS chỉ là stub nên không tin nó: tìm JDK thật.
JAVA_BIN=""
for cand in "${JAVA_HOME:+$JAVA_HOME/bin/java}" \
            "$(/usr/libexec/java_home -v 17+ 2>/dev/null)/bin/java" \
            "/Applications/Android Studio.app/Contents/jbr/Contents/Home/bin/java" \
            "/usr/lib/jvm/default-java/bin/java"; do
  [ -n "$cand" ] && [ -x "$cand" ] && JAVA_BIN="$cand" && break
done
if [ -n "$JAVA_BIN" ]; then
  jv="$("$JAVA_BIN" -version 2>&1 | head -1 | sed -E 's/.*"([0-9]+)[.".].*/\1/')"
  JAVA_HOME_FOUND="$(dirname "$(dirname "$JAVA_BIN")")"
  if [ -n "$jv" ] && [ "$jv" -ge 17 ] 2>/dev/null; then
    ok "JDK $jv ($JAVA_HOME_FOUND)"
  else
    miss "JDK phiên bản $jv (cần >= 17)" jdk; JAVA_HOME_FOUND=""
  fi
else
  JAVA_HOME_FOUND=""
  miss "JDK thật (chỉ có stub /usr/bin/java hoặc chưa cài)" jdk
fi

# ---------------- Android SDK ----------------
ANDROID_STUDIO=""
[ -d "/Applications/Android Studio.app" ] && ANDROID_STUDIO="yes"

SDK=""
for c in "$ANDROID_HOME" "$ANDROID_SDK_ROOT" "$HOME/Library/Android/sdk" "$HOME/Android/Sdk" \
         "${BREW_PREFIX:+$BREW_PREFIX/share/android-commandlinetools}"; do
  [ -n "$c" ] && [ -d "$c" ] && SDK="$c" && break
done
# Nơi sẽ cài SDK mới nếu chưa có (gói command-line tools của Homebrew tự đặt ở đây)
# Chưa có Homebrew thì đoán prefix theo chip: Apple Silicon /opt/homebrew, Intel /usr/local.
if [ -n "$BREW_PREFIX" ]; then GUESS_PREFIX="$BREW_PREFIX"
elif [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then GUESS_PREFIX="/opt/homebrew"
elif [ "$OS" = "Darwin" ]; then GUESS_PREFIX="/usr/local"
else GUESS_PREFIX=""; fi
SDK_NEW="${GUESS_PREFIX:+$GUESS_PREFIX/share/android-commandlinetools}"
SDK_NEW="${SDK_NEW:-$HOME/Android/Sdk}"

if [ -n "$SDK" ]; then ok "Android SDK ($SDK)"; else miss "Android SDK (chưa có thư mục SDK)" sdk; fi
SDKROOT="${SDK:-$SDK_NEW}"

ADB="$SDKROOT/platform-tools/adb"
EMU="$SDKROOT/emulator/emulator"
# sdkmanager/avdmanager phải nằm TRONG SDK đang dùng: avdmanager chỉ nhìn SDK nơi chính nó được cài
# (bỏ qua ANDROID_HOME và cờ --sdk_root), nên bản của Homebrew không thấy image trong SDK của Android Studio.
SDKMGR=""; AVDMGR=""
for c in "$SDKROOT"/cmdline-tools/latest/bin "$SDKROOT"/cmdline-tools/*/bin; do
  [ -x "$c/sdkmanager" ] && SDKMGR="$c/sdkmanager" && AVDMGR="$c/avdmanager" && break
done
ANY_SDKMGR="$(command -v sdkmanager 2>/dev/null)"   # bản bất kỳ trên PATH (ví dụ của Homebrew)

[ -x "$ADB" ] && ok "adb ($ADB)" || miss "adb (Android Platform-Tools)" platform-tools
[ -x "$EMU" ] && ok "emulator" || miss "Android Emulator" emulator
if [ -n "$SDKMGR" ]; then
  ok "cmdline-tools trong SDK (sdkmanager, avdmanager)"
elif [ -n "$ANY_SDKMGR" ] && [ -n "$SDK" ]; then
  miss "cmdline-tools chưa nằm trong SDK đang dùng ($SDKROOT); bản trên PATH ($ANY_SDKMGR) không tạo được AVD cho SDK này" cmdline-tools
else
  miss "Android SDK Command-line Tools (sdkmanager/avdmanager, để tải image và tạo AVD bằng lệnh)" cmdline-tools
fi

# System image đã tải đúng chip (image khác chip sẽ không chạy nhanh/không chạy được)
IMG_PKG=""
for d in "$SDKROOT"/system-images/*/*/"$ABI"; do
  if [ -d "$d" ]; then
    api="$(basename "$(dirname "$(dirname "$d")")")"; tag="$(basename "$(dirname "$d")")"
    IMG_PKG="system-images;$api;$tag;$ABI"; break
  fi
done
if [ -n "$IMG_PKG" ]; then ok "System image đã tải ($IMG_PKG)"; else miss "System image cho chip $ARCH ($ABI)" system-image; fi

# AVD hiện có (chỉ tên)
AVDS=""
if [ -x "$EMU" ]; then AVDS="$("$EMU" -list-avds 2>/dev/null)"; fi
if [ -z "$AVDS" ] && [ -d "$HOME/.android/avd" ]; then AVDS="$(ls "$HOME/.android/avd" 2>/dev/null | sed -n 's/\.ini$//p')"; fi
if [ -n "$AVDS" ]; then
  ok "AVD hiện có:"; echo "$AVDS" | sed 's/^/         - /'
  echo "$AVDS" | grep -qx "$AVD_NAME" || info "chưa có AVD riêng '$AVD_NAME' cho QA (khuyến nghị tạo; AVD cũ có thể chứa tài khoản/dữ liệu cá nhân)"
else
  miss "AVD (máy ảo Android)" avd
fi

# ---------------- Maestro (kiểm tra đúng sản phẩm) ----------------
MAESTRO_BIN="$(command -v maestro 2>/dev/null)"
[ -z "$MAESTRO_BIN" ] && [ -x "$HOME/.maestro/bin/maestro" ] && MAESTRO_BIN="$HOME/.maestro/bin/maestro"
if [ -n "$MAESTRO_BIN" ]; then
  if JAVA_HOME="${JAVA_HOME_FOUND:-$JAVA_HOME}" "$MAESTRO_BIN" --help 2>&1 | grep -qiE "hierarchy|studio"; then
    ok "Maestro ($MAESTRO_BIN)"
  else
    miss "lệnh 'maestro' có tồn tại ($MAESTRO_BIN) nhưng không phải Maestro test mobile, hoặc không chạy được (thiếu JDK?)" maestro
  fi
else
  miss "Maestro (công cụ chạy test mobile)" maestro
fi

# ---------------- Thiết bị đang chạy ----------------
echo "--- Thiết bị đang chạy ---"
if [ -x "$ADB" ]; then
  devs="$("$ADB" devices 2>/dev/null | sed '1d' | awk 'NF{print $1" "$2}')"
  if [ -n "$devs" ]; then
    echo "$devs" | sed 's/^/       /'
    echo "$devs" | grep -qv '^emulator-' && echo "CẢNH BÁO: có thiết bị KHÔNG phải emulator đang kết nối; harness chỉ dùng serial emulator-*."
  else
    echo "       (chưa có thiết bị nào chạy)"
  fi
else
  echo "       (chưa có adb)"
fi

# ---------------- Kế hoạch cài đặt ----------------
if [ -n "$MISSING" ]; then
  echo
  echo "=================== KẾ HOẠCH CÀI ĐẶT (theo thứ tự) ==================="
  echo "Quy ước: [TỰ CHẠY] = bạn chạy trong Terminal của bạn (có thể hỏi mật khẩu máy hoặc cần bạn đọc/đồng ý điều khoản)."
  echo "         [HARNESS CHẠY ĐƯỢC] = lệnh không cần mật khẩu; harness chạy giúp nếu bạn đồng ý."
  n=0
  step() { n=$((n+1)); echo; echo "Bước $n. $1"; }

  case "$OS" in
  Darwin|Linux)
    if has_missing homebrew; then
      step "Cài Homebrew [TỰ CHẠY]. Mở https://brew.sh, sao chép đúng lệnh cài đặt chính thức ở đầu trang rồi chạy trong Terminal."
      info "Harness không chạy lệnh tải-và-chạy-ngay (curl | bash) và không xử lý mật khẩu. Xong thì mở Terminal mới (hoặc làm theo dòng 'Next steps' Homebrew in ra để brew vào PATH) rồi chạy lại script này."
    fi
    if has_missing jdk; then
      step "Cài JDK 17 [TỰ CHẠY, thường hỏi mật khẩu máy]."
      if [ "$OS" = "Darwin" ]; then
        info "brew install --cask temurin@17"
        [ -n "$ANDROID_STUDIO" ] && info "(Thay thế không cần cài: JDK đi kèm Android Studio, script đã tự nhận nếu có.)"
      else
        info "sudo apt install openjdk-17-jdk      # Debian/Ubuntu; distro khác dùng gói tương đương"
      fi
    fi
    if has_missing cmdline-tools || has_missing sdk; then
      if [ -z "$ANY_SDKMGR" ]; then
        if [ "$OS" = "Darwin" ]; then
          step "Cài Android SDK Command-line Tools [TỰ CHẠY, thường hỏi mật khẩu máy]. Cách nhẹ nhất, không cần mở Android Studio; lệnh sdkmanager được đưa vào PATH."
          info "brew install --cask android-commandlinetools"
          has_missing sdk && info "Sau khi cài, SDK nằm ở: $SDK_NEW"
          [ -n "$ANDROID_STUDIO" ] && info "Máy đã có Android Studio: cách khác là Android Studio > Settings > Languages & Frameworks > Android SDK > SDK Tools, tick 'Android SDK Command-line Tools (latest)', Apply."
        else
          step "Cài Android SDK Command-line Tools [TỰ CHẠY]. Tải gói 'Command line tools only' từ https://developer.android.com/studio#command-line-tools-only, giải nén thành \$ANDROID_HOME/cmdline-tools/latest."
        fi
        info "Nếu brew báo 'Your Command Line Tools are too outdated': cập nhật Command Line Tools trong System Settings > Software Update (hoặc làm theo lệnh sudo brew in ra), rồi chạy lại."
      fi
      # SDK đã có (ví dụ của Android Studio) nhưng chưa có cmdline-tools bên trong: cài vào đúng SDK đó
      if ! has_missing sdk && [ -z "$SDKMGR" ]; then
        step "Cài cmdline-tools vào SDK đang dùng [HARNESS CHẠY ĐƯỢC]. Cần để avdmanager nhìn thấy system image của SDK này (~170 MB)."
        info "${ANY_SDKMGR:-sdkmanager} --sdk_root=\"$SDKROOT\" \"cmdline-tools;latest\""
      fi
    fi
    SDKMGR_HINT="${SDKMGR:-${ANY_SDKMGR:-sdkmanager}}"
    AVDMGR_HINT="$SDKROOT/cmdline-tools/latest/bin/avdmanager"

    step "Đặt biến môi trường cho phiên Terminal hiện tại (không ghi vào ~/.zshrc; muốn dùng lâu dài thì tự thêm)."
    if [ -n "$JAVA_HOME_FOUND" ]; then info "export JAVA_HOME=\"$JAVA_HOME_FOUND\""
    elif [ "$OS" = "Darwin" ]; then info "export JAVA_HOME=\"\$(/usr/libexec/java_home -v 17)\"   # chạy sau khi đã cài JDK"; fi
    info "export ANDROID_HOME=\"$SDKROOT\""
    info "export PATH=\"\$ANDROID_HOME/platform-tools:\$ANDROID_HOME/emulator:\$PATH\""

    # Tải thành phần SDK / system image chỉ khi thật sự thiếu (vài GB nên không tải thừa)
    if has_missing sdk || has_missing platform-tools || has_missing emulator || has_missing system-image; then
      pk=""
      if has_missing sdk || has_missing platform-tools; then pk="$pk \"platform-tools\""; fi
      if has_missing sdk || has_missing emulator; then pk="$pk \"emulator\""; fi
      if has_missing sdk || has_missing system-image; then pk="$pk \"platforms;android-$API_LEVEL\" \"system-images;android-$API_LEVEL;google_apis;$ABI\""; IMG_PKG="system-images;android-$API_LEVEL;google_apis;$ABI"; fi
      step "Chấp nhận điều khoản Android SDK [TỰ CHẠY, bạn đọc và đồng ý]. Harness không tự trả lời 'y' thay bạn."
      info "$SDKMGR_HINT --sdk_root=\"\$ANDROID_HOME\" --licenses"
      step "Tải thành phần SDK còn thiếu [HARNESS CHẠY ĐƯỢC sau khi bạn đã chấp nhận điều khoản; có thể vài GB]."
      info "$SDKMGR_HINT --sdk_root=\"\$ANDROID_HOME\"$pk"
      info "(Image 'google_apis' không có Google Play nên không cần đăng nhập Google. Báo không tìm thấy gói thì xem danh sách: $SDKMGR_HINT --sdk_root=\"\$ANDROID_HOME\" --list | grep system-images)"
    fi

    if has_missing avd || ! echo "$AVDS" | grep -qx "$AVD_NAME"; then
      step "Tạo AVD riêng cho QA tên '$AVD_NAME' [HARNESS CHẠY ĐƯỢC]. AVD riêng để không dính tài khoản/dữ liệu cá nhân trên AVD cũ."
      info "echo no | \"$AVDMGR_HINT\" create avd -n $AVD_NAME -k \"$IMG_PKG\" -d pixel_6    # 'no' = không tạo hardware profile tùy chỉnh"
      [ -n "$ANDROID_STUDIO" ] && info "(Hoặc Android Studio > Device Manager > Create Device nếu bạn quen giao diện. Dùng lại image đã tải ở trên, không tải thêm.)"
    fi
    if has_missing maestro; then
      step "Cài Maestro [HARNESS CHẠY ĐƯỢC]. PHẢI dùng đúng tên đầy đủ dưới đây."
      info "brew tap mobile-dev-inc/tap"
      info "brew install mobile-dev-inc/tap/maestro"
      info "CẢNH BÁO: KHÔNG chạy 'brew install maestro' (tên ngắn) vì đó là phần mềm khác ('AI agent command center')."
      info "Nếu brew báo 'untrusted tap': đây là quyết định tin cậy của BẠN. Sau khi tự xem formula, chạy: brew trust --formula mobile-dev-inc/tap/maestro (hẹp hơn 'brew trust mobile-dev-inc/tap')."
      info "Nếu brew báo 'Command Line Tools are too outdated': cập nhật Command Line Tools, hoặc dùng cách tải bản phát hành có kiểm mã băm ở skill mobile-env-setup (mục 'Cài Maestro khi brew không cài được')."
      info "Kiểm tra sau khi cài: brew info mobile-dev-inc/tap/maestro  (trang chủ phải là maestro.mobile.dev), rồi maestro --version"
    fi
    ;;
  *)
    echo
    echo "Hệ điều hành '$OS' chưa có kế hoạch tự động. Làm theo tài liệu chính thức:"
    ;;
  esac
  echo
  echo "Sau khi cài xong: chạy lại script này để xác nhận. Tài liệu chính thức khi cần đối chiếu:"
  echo "  Homebrew: https://brew.sh   Android SDK: https://developer.android.com/studio#command-line-tools-only   Maestro: https://maestro.mobile.dev"
fi

echo "---"
if [ -z "$MISSING" ]; then
  echo "Môi trường đủ điều kiện."
  echo "MISSING_ITEMS=none"
  exit 0
else
  echo "Còn thiếu mục ở trên."
  echo "MISSING_ITEMS=$MISSING"
  exit 1
fi
