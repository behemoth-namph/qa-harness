# Viết flow Maestro từ bước test case

Mục lục: 1. Cấu trúc flow · 2. Dịch bước → lệnh · 3. Chọn phần tử · 4. Điều kiện tiên quyết và trạng thái · 5. TC mobile thường gặp · 6. Việc không làm được

## 1. Cấu trúc flow

Mỗi TC một file `_workspace/mobile/flows/<TC_ID>.yaml`, độc lập với TC khác (giống nguyên tắc độc lập của test case).

```yaml
appId: ${APP_ID}
name: TC-AUTH-001 Mật khẩu 7 ký tự bị từ chối
---
- launchApp            # không clearState sau khi người dùng đã đăng nhập (xem mục 4)
- tapOn: "Đăng ký"
- tapOn:
    id: "email_input"
- inputText: "qa.${RUN_ID}@example.com"
- assertVisible: "Mật khẩu tối thiểu 8 ký tự"
```

Giá trị đi vào qua `-e KEY=value` (`APP_ID`, `RUN_ID`, dữ liệu giả...). Không viết giá trị nhạy cảm vào file YAML. Flow chỉ chứa dữ liệu giả hoặc biến.

## 2. Dịch bước → lệnh Maestro

| Bước trong TC | Lệnh |
|---|---|
| Mở app | `launchApp` |
| Chạm nút/nhãn | `tapOn: "Văn bản"` hoặc `tapOn: {id: "..."}` |
| Nhập vào ô (không phải mật khẩu) | `tapOn` ô rồi `inputText` |
| Cuộn tới phần tử | `scrollUntilVisible: {element: "..."}` |
| Vuốt | `swipe: {direction: UP}` |
| Nút Back / Home | `pressKey: Back` / `pressKey: Home` |
| Đợi nội dung | `extendedWaitUntil: {visible: "...", timeout: 10000}` |
| Kỳ vọng hiển thị | `assertVisible: "văn bản nguyên văn từ spec"` |
| Kỳ vọng không hiển thị | `assertNotVisible: "..."` |
| Kỳ vọng nút bị vô hiệu | `assertVisible: {text: "...", enabled: false}` |
| Đóng bàn phím | `hideKeyboard` |
| Tắt/bật máy bay | `setAirplaneMode: enabled` / `disabled` (khôi phục sau TC) |
| Ngắt tiến trình app | `stopApp` |

Kiểm tên lệnh theo phiên bản Maestro đã cài (`maestro --version`); lệnh mới có thể chưa có ở bản cũ. Lệnh không có thì dùng `adb` trong danh sách cho phép ở SKILL.md.

## 3. Chọn phần tử

Thứ tự ưu tiên: `id` (resource-id/accessibility id) → văn bản hiển thị → vị trí tương đối (`below`, `rightOf`). Tránh tọa độ tuyệt đối vì vỡ khi đổi kích thước màn hình. Muốn biết phần tử có `id` gì: `maestro --device <serial> hierarchy` in cây giao diện dạng chữ (không cần ảnh). Chỉ trích các nhãn/ID cần thiết vào flow, không chép cả cây vào kết quả (có thể chứa dữ liệu người dùng).

Văn bản thông báo trong `assertVisible` lấy nguyên văn từ cột "Kết quả mong đợi"; Maestro dùng regex nên thoát ký tự đặc biệt (`.`, `?`, `(`, `)`) bằng `\\`.

## 4. Điều kiện tiên quyết và trạng thái

- **Chưa cần đăng nhập** (màn hình đăng ký, đăng nhập, onboarding): đầu flow dùng `launchApp: {clearState: true}` để sạch.
- **Cần đã đăng nhập**: người dùng đăng nhập một lần ở đầu phiên (`NEEDS_USER_LOGIN`). Các flow sau chỉ `launchApp` (không `clearState`), và tự đưa app về màn hình xuất phát bằng thao tác điều hướng. Mất phiên đăng nhập thì báo lại, không cố tự đăng nhập.
- **Dữ liệu cần tồn tại** (ví dụ một bản ghi có sẵn) mà app không tạo được qua giao diện: `Blocked`, nêu điều kiện thiếu. Không chèn dữ liệu bằng cách sửa file/DB trên thiết bị.
- Giá trị giả sinh theo quy tắc ở sheet Test Data, ví dụ `qa.<số ngẫu nhiên>@example.com`.

## 5. TC đặc thù mobile thường gặp

| Nhóm | Cách kiểm trên emulator |
|---|---|
| Vòng đời | `pressKey: Home` rồi `launchApp` (không clear) → kiểm trạng thái còn giữ; `stopApp` + `launchApp` → kiểm khôi phục |
| Xoay màn hình | `adb ... settings put system user_rotation 1`, kiểm bố cục/dữ liệu còn, trả về 0 sau TC |
| Quyền | Không `pm grant` trước; để hộp thoại quyền hiện, chọn Cho phép/Từ chối bằng `tapOn`, kiểm hành vi app ở cả hai nhánh |
| Mất mạng | `setAirplaneMode: enabled`, thao tác, kiểm thông báo lỗi/offline; **bật lại** cuối TC dù pass hay fail |
| Nút Back | `pressKey: Back` tại từng màn hình, kiểm điều hướng/xác nhận thoát |
| Bàn phím/nhập liệu | `hideKeyboard`, kiểm ô bị che, kiểu bàn phím không kiểm được qua Maestro → ghi vào `note` |
| Kích thước màn hình | Chạy trên AVD khác do người dùng cung cấp; một flow, nhiều thiết bị |

## 6. Việc không làm được bằng emulator + Maestro (đánh `mobile_testable = N`)

Push notification thật, camera/quét mã, vân tay/Face ID, SMS/OTP thật, cuộc gọi đến, GPS thật, Bluetooth/NFC, thanh toán trong app, hiệu năng/pin trên máy thật, hành vi riêng của nhà sản xuất máy. Những TC này vẫn nằm trong Excel để người dùng chạy tay trên thiết bị thật.
