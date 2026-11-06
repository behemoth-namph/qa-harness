# QA Harness

Bộ agent và skill cho [Claude Code](https://claude.com/claude-code) giúp QA:

1. Nhận yêu cầu / user story / bug.
2. Đối chiếu với spec của dự án trong `specs/` và phân loại điểm khớp, mâu thuẫn, thiếu, mơ hồ.
3. Hỏi lại người đưa yêu cầu về các điểm sai/thiếu.
4. Thiết kế test case đầy đủ, được một agent khác rà soát, rồi xuất file Excel vào `output/`.
5. Nếu bạn đồng ý, chạy thử các test case trên môi trường test và ghi kết quả vào cùng file Excel: web bằng Claude in Chrome, mobile app Android bằng Maestro trên emulator.

Harness chỉ chứa quy trình, không chứa spec hay dữ liệu của dự án nào. Mỗi dự án dùng một bản clone riêng.

## Yêu cầu

- Claude Code (CLI hoặc extension VS Code)
- Python 3.9 trở lên
- Chỉ khi chạy thử trên trình duyệt: extension Claude in Chrome
- Chỉ khi chạy thử mobile app Android: Android SDK (adb, emulator, một AVD riêng cho QA), JDK 17+ (dùng được JDK đi kèm Android Studio) và [Maestro](https://maestro.mobile.dev). Máy chưa có gì cũng được: harness tự dò máy và in kế hoạch cài đặt từng bước (xem bên dưới)
- Tùy chọn: `pdftotext` (poppler) để đọc spec PDF tốt hơn, không có thì dùng `pypdf`

## Cài đặt

```bash
git clone <URL-repo> qa-harness
cd qa-harness
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Cách dùng

1. Đặt tài liệu spec của dự án vào `specs/` (hỗ trợ `.md`, `.txt`, `.csv`, `.docx`, `.pdf`, `.xlsx`; có thể chia thư mục con).
2. Mở Claude Code tại thư mục `qa-harness` và đưa yêu cầu bằng ngôn ngữ tự nhiên, ví dụ:
   - "Viết test case cho tính năng đăng nhập: mật khẩu tối thiểu 8 ký tự, khóa sau 5 lần sai"
   - "Đối chiếu user story này với spec"
   - "Bổ sung test case phân quyền vào bộ test hiện tại"
   - "Chạy lại pretest cho các TC Fail"
3. Trả lời các câu hỏi xác nhận về điểm lệch giữa yêu cầu và spec.
4. Nhận file Excel tại `output/TestCases_<tên>_<YYYYMMDD>.xlsx`. Các tài liệu văn bản (đề xuất cập nhật spec, ghi chú thiếu sót/bảo mật) là file Word `.docx` cũng nằm trong `output/`; harness không giao file `.md` cho người đọc.
5. Khi được hỏi có chạy thử bằng Chrome không: chọn Có thì **tự cung cấp link môi trường test** (không phải production) và **tự đăng nhập trực tiếp trên Chrome**.
6. Test mobile app: nói rõ là app Android (ví dụ "viết và chạy test cho màn hình đăng ký của app Android"). Khi chạy thử, harness dựng emulator, bạn **tự đưa file APK bản test và package id**, xác nhận bản build trỏ backend test, và **tự đăng nhập app trên cửa sổ emulator**. iOS: harness vẫn thiết kế test case nhưng chưa tự chạy, bạn chạy tay.

### Lần đầu dùng: máy chưa có công cụ mobile

Khi bạn chọn chạy thử mobile (hoặc chạy tay `bash .claude/skills/mobile-env-setup/scripts/check_mobile_env.sh`, lệnh này chỉ đọc), harness dò máy rồi in kế hoạch cài đặt theo thứ tự, đúng với hệ điều hành và chip của bạn (Homebrew, JDK 17, Android command-line tools, system image, AVD riêng cho QA `qa_test`, Maestro). Mỗi bước ghi rõ ai chạy:

- **Bạn tự chạy** trong Terminal: cài Homebrew, các lệnh `brew install --cask ...` (có thể hỏi mật khẩu máy) và chấp nhận điều khoản Android SDK. Harness không xử lý mật khẩu và không đồng ý điều khoản thay bạn.
- **Harness chạy giúp** nếu bạn đồng ý: tải gói SDK, tạo AVD, cài Maestro.

Chạy lại script để xác nhận cho tới khi báo `MISSING_ITEMS=none`. Lưu ý: dùng `mobile-dev-inc/tap/maestro` để cài Maestro; `brew install maestro` cài phần mềm khác. Homebrew bản mới sẽ hỏi bạn có tin cậy tap `mobile-dev-inc/tap` không (`brew trust`, quyết định của bạn) và có thể đòi cập nhật Command Line Tools của macOS; nếu bạn không muốn cập nhật, harness có cách tải bản phát hành Maestro và đối chiếu mã băm SHA-256. Kế hoạch đầy đủ hiện có cho macOS; Linux có hướng dẫn một phần, Windows chưa hỗ trợ.

### Phạm vi chạy tự động trên mobile

- Làm được: chạm, nhập chữ, vuốt, kiểm văn bản trên màn hình, vòng đời app, xoay màn hình, hộp thoại quyền, mất/khôi phục mạng, nút Back.
- Không làm được (TC vẫn nằm trong Excel để bạn chạy tay): push thật, camera, vân tay, SMS/OTP thật, GPS thật, Bluetooth/NFC, thanh toán, hiệu năng trên máy thật, và các TC phải gõ mật khẩu.
- Cột `Nền tảng` và `Chạy được bằng Mobile (Maestro)` trong Excel cho biết TC nào chạy tự động được.

## Cấu trúc

```
.claude/
  agents/     spec-analyst, testcase-designer, testcase-reviewer, browser-tester, mobile-tester
  skills/
    qa-orchestrator/       điều phối toàn bộ quy trình
    spec-mapping/          đối chiếu yêu cầu với spec
    testcase-design/       thiết kế test case, xuất và ghi kết quả vào Excel
    browser-pretest/       chạy thử bằng Chrome
    mobile-env-setup/      dựng môi trường mobile (Android SDK, Maestro, emulator, bản build test)
    mobile-pretest/        chạy thử mobile app bằng Maestro trên emulator
    qa-security-policy/    quy tắc bảo mật bắt buộc cho mọi bước
  settings.json            các tool bị chặn (đọc mật khẩu/cookie/network, tải file lên...)
CLAUDE.md                  điều kiện gọi harness
specs/                     spec của dự án (không đưa lên git)
output/                    file Excel test case và tài liệu Word (không đưa lên git)
_workspace/                file trung gian, tự sinh khi chạy (không đưa lên git)
```

## Bảo mật

Chi tiết ở `.claude/skills/qa-security-policy/SKILL.md`. Tóm tắt:

- Spec và yêu cầu không được gửi ra dịch vụ ngoài máy. `WebFetch` và `WebSearch` bị chặn trong `.claude/settings.json`.
- Agent không xử lý mật khẩu, OTP, token. Bạn tự đăng nhập trên Chrome hoặc trên cửa sổ emulator.
- `javascript_tool`, `read_network_requests`, `gif_creator`... bị chặn để agent không đọc cookie, storage hay header xác thực.
- Test case chỉ dùng placeholder hoặc dữ liệu giả. Script xuất Excel quét mật khẩu, token, thẻ, CCCD, số điện thoại, email thật và dừng nếu phát hiện.
- Mobile: chỉ emulator (không thiết bị thật), AVD không chứa tài khoản cá nhân, build trỏ backend test, không `maestro cloud/studio/record`, không lưu ảnh chụp màn hình. `.claude/settings.json` chặn thêm các lệnh `adb pull/backup/run-as/screencap`... làm lớp phụ; quy tắc chính nằm ở `qa-security-policy` mục 5.
- Chỉ chạy trên môi trường test đã xác nhận, không làm thao tác không thể hoàn tác (xóa hàng loạt, thanh toán, gửi email/SMS thật).

`specs/*`, `output/*` và `_workspace/` chứa thông tin nội bộ của dự án và đã nằm trong `.gitignore`. Không dùng `git add -f` cho các thư mục này, và không sửa `.claude/settings.json` để nới các quy tắc chặn.

## Tùy chỉnh

- Cả 5 agent đang dùng model `sonnet`. Đổi trong phần frontmatter của `.claude/agents/*.md` nếu cần.
- Khi sửa agent hoặc skill, ghi lại thay đổi vào bảng "Biến động" trong `CLAUDE.md`.
