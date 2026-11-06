---
name: mobile-env-setup
description: "Dựng và kiểm tra môi trường để tự chạy test case cho mobile app Android: kiểm tra JDK/adb/emulator/Maestro, lập kế hoạch cài đặt đầy đủ theo từng bước (kèm lệnh cụ thể cho máy này) cho người dùng mới chưa có công cụ hay simulator nào, cài phần thiếu khi người dùng đồng ý, chọn hoặc tạo AVD riêng cho QA, khởi động emulator, cài bản build test của app, đưa app về trạng thái sạch. Dùng khi yêu cầu/bộ test nhắm tới app mobile (Android) và người dùng muốn chạy thử tự động, khi người dùng dùng harness lần đầu và máy chưa đủ công cụ, hoặc khi cần cài đặt/dựng lại/kiểm tra lại môi trường mobile (emulator không lên, Maestro báo lỗi, đổi build)."
---

# Dựng môi trường test mobile (Android + Maestro + emulator)

Trước khi làm, đọc `.claude/skills/qa-security-policy/SKILL.md` (mục 5 về thiết bị di động). Skill này do **orchestrator** thực hiện ở phiên chính, không giao cho `mobile-tester`: việc cài phần mềm, chọn AVD, chọn bản build là quyết định của người dùng, và `mobile-tester` chỉ nên chạy test trên môi trường đã được xác nhận.

Phạm vi hiện tại: **Android emulator + Maestro**. iOS Simulator và thiết bị thật chưa hỗ trợ; TC thuộc các nền tảng đó giữ `mobile_testable = N` để người dùng chạy tay.

## Bước 1: Kiểm tra hiện trạng (chỉ đọc)

```
bash .claude/skills/mobile-env-setup/scripts/check_mobile_env.sh
```

Script dò hệ điều hành, chip (Intel/Apple Silicon), Homebrew, JDK, Android Studio, Android SDK, system image, AVD và Maestro, rồi **in sẵn kế hoạch cài đặt theo thứ tự cho đúng phần còn thiếu của máy này**. Dòng cuối là `MISSING_ITEMS=<id,id,...|none>` để đọc máy được. Ghi tóm tắt (OK/THIẾU, không kèm đường dẫn chứa tên người dùng nếu họ không muốn) vào `_workspace/mobile/env.md`.

Người dùng mới lần đầu thường thiếu gần hết: đừng hỏi từng món một. Trình bày **cả kế hoạch một lượt** (Bước 2), để họ thấy trọn việc cần làm và thời gian/dung lượng tải (vài GB).

Hai bẫy script đã xử lý, cần nhớ khi tự kiểm tra thêm:
- `/usr/bin/java` trên macOS chỉ là stub, không phải JDK. Script tự tìm JDK thật (`JAVA_HOME`, `java_home`, JDK đi kèm Android Studio).
- Tên ngắn `maestro` trong Homebrew (`brew install maestro`) là **một phần mềm khác** ("AI agent command center"). Maestro test mobile chỉ cài bằng `mobile-dev-inc/tap/maestro`. Đừng coi "có lệnh maestro" là đủ; script đã kiểm bằng cách chạy thử lệnh.

## Bước 2: Cài phần thiếu (kế hoạch cho người dùng mới)

Cài phần mềm là thay đổi trên máy người dùng, nên không tự cài mà không hỏi.

**2.1. Xác minh lệnh bằng công cụ cục bộ trước khi gợi ý.** Harness không tra web (WebSearch/WebFetch bị chặn theo chính sách bảo mật), nên tên gói trong script có thể lỗi thời theo thời gian. Kiểm lại bằng lệnh chỉ đọc, và nếu tên đổi thì tự tìm tên mới bằng cùng công cụ thay vì đoán:

| Cần xác minh | Lệnh chỉ đọc |
|---|---|
| Gói JDK còn tồn tại | `brew info --cask temurin@17` |
| Gói Android command-line tools | `brew info --cask android-commandlinetools` (xem mục Artifacts và Caveats: nơi đặt SDK, sdkmanager/avdmanager có vào PATH không) |
| Tên gói system image | `sdkmanager --sdk_root="$ANDROID_HOME" --list \| grep system-images` (sau khi đã có sdkmanager) |
| Maestro đúng sản phẩm | sau `brew tap mobile-dev-inc/tap`: `brew info mobile-dev-inc/tap/maestro`, trang chủ phải là `maestro.mobile.dev` |

Vẫn không xác minh được thì nói thẳng với người dùng và chỉ họ tới tài liệu chính thức (Homebrew: https://brew.sh · Android: https://developer.android.com/studio#command-line-tools-only · Maestro: https://maestro.mobile.dev), không bịa lệnh.

**2.2. Trình bày kế hoạch và phân loại ai chạy.** Chép kế hoạch từ script vào câu trả lời (lệnh để trong khối mã, sao chép được). Mỗi bước script đã gắn nhãn:

| Nhãn | Ý nghĩa | Lý do |
|---|---|---|
| `[TỰ CHẠY]` | Người dùng chạy trong Terminal của họ | Cài Homebrew, `brew install --cask ...` thường hỏi **mật khẩu máy**; chấp nhận điều khoản Android SDK là việc người dùng đồng ý bằng chính họ. Agent không xử lý mật khẩu và không trả lời "y" thay họ |
| `[HARNESS CHẠY ĐƯỢC]` | Lệnh không cần mật khẩu (tải gói SDK, tạo AVD, `brew install` công thức thường, Maestro) | Chỉ chạy sau khi người dùng đồng ý bằng `AskUserQuestion` |

Không bao giờ: chạy lệnh dạng `curl ... | bash` (Homebrew thì để người dùng tự lấy lệnh chính thức ở https://brew.sh), `sudo`, hay `yes | sdkmanager --licenses`.

**2.3. Hỏi cách tiến hành** (`AskUserQuestion`): (a) "Tôi tự chạy phần [TỰ CHẠY], bạn chạy giúp phần còn lại" (khuyến nghị) / (b) "Tôi tự chạy toàn bộ" / (c) "Để sau". Chọn (c) thì dừng, giữ `mobile_testable = Y` trong Excel.

**2.4. Xác nhận bằng cách chạy lại script.** Người dùng báo đã làm xong phần của họ → chạy phần `[HARNESS CHẠY ĐƯỢC]` theo thứ tự trong kế hoạch (mỗi lệnh một lần Bash, kiểm kết quả từng lệnh) → chạy lại script. Lặp đến khi `MISSING_ITEMS=none`. Lệnh nào lỗi thì đọc thông báo lỗi, không thử lặp quá một lần; báo người dùng nguyên văn lỗi (che đường dẫn cá nhân nếu có).

Sau khi cài Maestro, đặt các biến để Maestro không gửi số liệu hay tự kiểm tra cập nhật ra ngoài (lý do: chính sách "dữ liệu không rời khỏi máy"):

```
export MAESTRO_CLI_NO_ANALYTICS=1 MAESTRO_DISABLE_UPDATE_CHECK=true
```

Chạy `maestro --version` rồi `maestro test --help` để xác nhận tên cờ theo đúng phiên bản đã cài (cờ có thể đổi giữa các phiên bản). Đã xác nhận ở Maestro 2.12.1: `--device`, `-e`, `--test-output-dir`, `--format`, `--output` đều có.

**Kiểm số liệu Maestro gửi đi.** Tác dụng của hai biến môi trường trên chưa kiểm chứng được (mã Maestro đã nén nên không dò được tên biến), vì vậy đừng chỉ tin biến. Kiểm tệp cấu hình thật trước mỗi lượt chạy, trường `enabled` trong `~/.maestro/analytics.json` phải là `false`. Đọc tệp bằng công cụ Read; `true` thì dừng, báo người dùng, không chạy test cho tới khi họ xử lý. Maestro 2.12.1 còn có cờ `--analyze` ("AI Insights", gửi kết quả cho dịch vụ đám mây) và lệnh `maestro mcp`: không dùng.

### Cài Maestro khi brew không cài được

Hai lỗi Homebrew với Maestro đã xảy ra thật:

| Thông báo | Nghĩa | Xử lý |
|---|---|---|
| `Refusing to load formula ... from untrusted tap` | Homebrew bản mới chặn tap bên thứ ba cho tới khi người dùng tin cậy | Đọc formula bằng Read (`$(brew --prefix)/Library/Taps/mobile-dev-inc/homebrew-tap/Formula/maestro.rb`): trang chủ phải là `maestro.mobile.dev`, `url` phải nằm trên `github.com/mobile-dev-inc/maestro/releases`, có `sha256`. Trình bày cho người dùng, **hỏi** rồi mới chạy `brew trust --formula mobile-dev-inc/tap/maestro` (hẹp hơn trust cả tap). Tin cậy mã bên thứ ba là quyết định của họ |
| `Your Command Line Tools are too outdated` | Command Line Tools của macOS cũ; sửa cần `sudo` hoặc System Settings | Người dùng tự cập nhật (nhãn [TỰ CHẠY]). Nếu họ không muốn, dùng cách tải bản phát hành bên dưới |

**Tải bản phát hành có kiểm mã băm** (không cần Homebrew, không `sudo`; khác kế hoạch ban đầu nên hỏi người dùng đồng ý trước):
1. Lấy `url` và `sha256` từ file formula đã đọc ở trên, không lấy từ nơi khác.
2. Tải vào một thư mục **mới, trống**, mỗi lệnh `curl -fsSL -o <thư mục>/maestro.zip "<url>"` chạy riêng, không nối pipe với lệnh khác.
3. Tính SHA-256 bằng Python (`hashlib`) và so với `sha256` của formula. **Không khớp → xóa file và dừng**, báo người dùng.
4. Giải nén vào thư mục tạm, xem cấu trúc, rồi chuyển thư mục `maestro` thành `~/.maestro` (đã tồn tại thì hỏi, không ghi đè) và `chmod +x ~/.maestro/bin/maestro`.
5. `JAVA_HOME=<JDK> ~/.maestro/bin/maestro --version`. Script kiểm tra tự nhận `~/.maestro/bin/maestro` dù chưa nằm trong PATH; ghi đường dẫn đó vào `maestro_bin` của `env.json`.

Phạm vi hệ điều hành: kế hoạch đầy đủ cho macOS (đã kiểm tên gói trên Apple Silicon). Linux có JDK và hướng dẫn SDK; Windows chưa có kế hoạch tự động, chỉ trỏ tài liệu chính thức.

## Bước 3: Chọn emulator (AVD)

AVD có sẵn trên máy có thể đang chứa tài khoản Google, ảnh, tin nhắn của người dùng. Vì vậy:

1. Liệt kê tên AVD từ Bước 1 và hỏi người dùng dùng AVD nào. Khuyến nghị một AVD **riêng cho QA** (tên gợi ý `qa_test`) chưa đăng nhập tài khoản cá nhân. Nếu người dùng muốn dùng AVD cũ, hỏi xác nhận rõ ràng là AVD đó không chứa dữ liệu cá nhân hoặc cho phép wipe.
2. Cần tạo AVD mới: hướng dẫn tạo bằng Android Studio Device Manager (chọn image không cần Google Play nếu app không cần). Tự tạo bằng `avdmanager` chỉ khi có `cmdline-tools` và người dùng đồng ý.
3. Wipe dữ liệu (`-wipe-data`) chỉ khi người dùng đồng ý, vì không hoàn tác được.

## Bước 4: Khởi động emulator

Khởi động **có cửa sổ** (không `-no-window`) để người dùng tự đăng nhập app trên đó khi cần. Chạy nền bằng Bash `run_in_background`:

```
"$ANDROID_HOME/emulator/emulator" -avd <TÊN_AVD> -no-audio -no-boot-anim -no-snapshot-save
```

`ANDROID_HOME` là đường dẫn SDK script đã dò ở Bước 1 (đặt biến trong lệnh, không phụ thuộc cấu hình shell của người dùng). Rồi đợi sẵn sàng và lấy serial:

```
bash .claude/skills/mobile-env-setup/scripts/wait_emulator_boot.sh emulator-5554 240
"$ANDROID_HOME/platform-tools/adb" devices
```

Chỉ dùng serial bắt đầu bằng `emulator-`. Có thiết bị thật đang cắm USB thì mọi lệnh `adb` phải kèm `-s emulator-XXXX` để không chạm vào máy thật; nhắc người dùng rút thiết bị thật nếu muốn yên tâm.

## Bước 5: Cài bản build test của app

1. Người dùng **tự đưa** đường dẫn file APK bản test (hoặc xác nhận app đã cài sẵn) và **package id**. Không đoán, không tải APK từ internet, không đọc nội dung APK.
2. Hỏi xác nhận bản build này **trỏ tới backend test/staging, không phải production** (lý do: emulator sẽ gọi API thật của bản build; bản trỏ production có thể tạo/sửa dữ liệu thật).
3. Cài: `adb -s emulator-XXXX install -r <đường dẫn APK>`.
4. Cấp quyền cần thiết cho TC bằng `adb -s emulator-XXXX shell pm grant <package> <permission>` chỉ khi TC yêu cầu; các TC kiểm tra hộp thoại quyền thì không cấp trước.
5. Trạng thái sạch: `adb -s emulator-XXXX shell pm clear <package>` trước mỗi lượt chạy (xóa dữ liệu của chính app test trên emulator).

## Bước 6: Ghi cấu hình cho mobile-tester

Ghi `_workspace/mobile/env.json` (không chứa mật khẩu/token/đường dẫn nhạy cảm):

```json
{
  "platform": "Android",
  "serial": "emulator-5554",
  "package_id": "<PACKAGE_ID người dùng đưa>",
  "avd": "qa_test",
  "backend_confirmed_test": true,
  "maestro_env": {"MAESTRO_CLI_NO_ANALYTICS": "1", "MAESTRO_DISABLE_UPDATE_CHECK": "true"},
  "java_home": "đường dẫn JDK đã chọn",
  "android_home": "đường dẫn Android SDK đã dùng",
  "maestro_bin": "đường dẫn tới lệnh maestro (có thể là ~/.maestro/bin/maestro)"
}
```

`backend_confirmed_test` chỉ là `true` khi người dùng đã xác nhận ở Bước 5. Thiếu hoặc `false` thì `mobile-tester` không được chạy.

## Khi gặp lỗi

| Tình huống | Cách xử lý |
|---|---|
| Emulator không lên sau 240 giây | Báo người dùng, gợi ý kiểm tra hardware acceleration và dung lượng đĩa; không thử khởi động lặp |
| `adb devices` hiện `offline`/`unauthorized` | Đợi thêm một lần; vẫn vậy thì báo người dùng, không chạy `adb kill-server` hàng loạt |
| Maestro không tìm thấy thiết bị | Kiểm tra serial emulator và `JAVA_HOME`, chạy lại một lần |
| `avdmanager`: `Package path is not valid ... null`, hoặc `avdmanager list target` trả rỗng | `avdmanager` chỉ nhìn SDK nơi chính nó nằm (bỏ qua `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `--sdk_root`). Bản của Homebrew nhìn SDK của Homebrew nên không thấy image trong SDK của Android Studio. Cài cmdline-tools vào đúng SDK: `sdkmanager --sdk_root="$SDK" "cmdline-tools;latest"`, rồi dùng `$SDK/cmdline-tools/latest/bin/avdmanager` |
| `maestro` có trong PATH nhưng `--help` không có lệnh `hierarchy` | Có thể là phần mềm khác (`brew install maestro` tên ngắn). Hỏi người dùng rồi gỡ bản sai và cài đúng `mobile-dev-inc/tap/maestro` |
| Người dùng không muốn cài Maestro | Dừng ở đây; giữ `mobile_testable = Y` trong Excel để chạy sau, hoặc người dùng chạy tay |
