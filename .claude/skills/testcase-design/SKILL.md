---
name: testcase-design
description: "Thiết kế bộ test case đầy đủ và chi tiết từ yêu cầu đã được đối chiếu và xác nhận với spec (functional, validation, biên, negative, phân quyền, trạng thái, UI, bảo mật cơ bản, tích hợp), rồi xuất file Excel vào thư mục output/ và ghi kết quả chạy thử vào cùng file. Dùng khi tạo, bổ sung, rà soát test case hoặc xuất/cập nhật file Excel test case."
---

# Thiết kế test case và xuất Excel

Trước khi làm, đọc `.claude/skills/qa-security-policy/SKILL.md`.

## Đầu vào

- `_workspace/01_requirements.json` (danh sách REQ)
- `_workspace/02_mapping_*.json` đã gộp + `_workspace/02_clarifications.json` (quyết định của người dùng)

Dùng `effective_text` của quyết định làm yêu cầu hiệu lực. Điểm người dùng chọn "giả định" thì viết test case theo giả định và ghi rõ vào `notes` cũng như `meta.assumptions`.

## Thế nào là "đầy đủ và chi tiết nhất"

Với mỗi REQ và mỗi quy tắc `SPEC_ONLY`, xét lần lượt các chiều dưới đây và chỉ bỏ chiều nào thật sự không áp dụng (ghi lý do trong lúc nghĩ, không cần ghi ra file):

| Chiều | Câu hỏi để sinh test case |
|---|---|
| Luồng chính | Đường đi hợp lệ chuẩn chạy đúng không? |
| Luồng thay thế | Có nhánh khác, tùy chọn khác, thao tác lặp lại, quay lại, hủy không? |
| Validation | Mỗi trường: bắt buộc, kiểu, độ dài, định dạng, ký tự đặc biệt, khoảng trắng đầu/cuối, Unicode/tiếng Việt có dấu |
| Biên | Phân vùng tương đương + giá trị biên: min-1, min, min+1, max-1, max, max+1 |
| Negative | Dữ liệu sai, thiếu, trùng, quá lớn, thao tác sai thứ tự, hết phiên |
| Quy tắc nghiệp vụ | Bảng quyết định cho tổ hợp điều kiện; công thức tính toán |
| Trạng thái | Mỗi chuyển trạng thái hợp lệ và các chuyển bị cấm |
| Phân quyền | Từng vai trò: được làm, không được làm; truy cập trực tiếp bằng URL |
| Thông báo & UI | Văn bản thông báo đúng spec, nhãn, thứ tự tab, trạng thái nút, responsive, trạng thái rỗng/đang tải/lỗi |
| Tích hợp & dữ liệu | Dữ liệu lưu đúng, hiển thị đúng ở màn hình liên quan, đồng thời nhiều người dùng |
| Bảo mật cơ bản | Escape ký tự đặc biệt, không lộ thông tin nhạy cảm trong thông báo lỗi, khóa tài khoản, kiểm soát truy cập |
| Phi chức năng (khi spec nêu) | Hiệu năng, tương thích trình duyệt, khả năng truy cập |

## Chất lượng một test case

- **Tiêu đề** nêu điều kiện và kết quả, ví dụ "Mật khẩu 7 ký tự bị từ chối kèm thông báo độ dài tối thiểu", không viết "Kiểm tra mật khẩu".
- **Các bước** là hành động cụ thể, đánh số, một thao tác một bước, người khác làm theo được mà không phải đoán. Nêu rõ trường, nút, giá trị (dạng placeholder).
- **Kết quả mong đợi** kiểm chứng được và lấy từ spec/quyết định: văn bản thông báo nguyên văn nếu spec có, trạng thái nút, dữ liệu sau khi lưu. Không viết "hoạt động đúng".
- **Độc lập**: mỗi TC tự nêu điều kiện tiên quyết; không phụ thuộc kết quả TC khác.
- **Không trùng**: hai TC không cùng kiểm một điều. Muốn nhiều giá trị cho cùng một quy tắc thì mỗi giá trị biên là một TC riêng chỉ khi kỳ vọng khác nhau.
- **Truy vết**: `req_ids` liệt kê REQ-xx hoặc SPEC-xx; `spec_ref` ghi file#mục. Mỗi REQ phải có ít nhất một TC (script từ chối nếu thiếu).
- **Ưu tiên**: P0 = chặn luồng chính/bảo mật/mất dữ liệu; P1 = chức năng quan trọng; P2 = biên, validation phụ; P3 = giao diện, thẩm mỹ.
- **Dữ liệu**: chỉ placeholder hoặc dữ liệu giả (theo chính sách bảo mật). Mô tả quy tắc sinh giá trị ở sheet Test Data.
- **Cờ `chrome_testable`**: "Y" chỉ khi thực hiện được qua giao diện web trên môi trường test, không cần OTP/email/SMS thật, không thanh toán thật, không phá hủy dữ liệu thật. Các TC khác là "N" (người dùng chạy thủ công).

Mã TC: `TC-<MODULE ngắn>-<số 3 chữ số>`, ví dụ `TC-AUTH-001`.

## Định dạng JSON trung gian

Ghi `_workspace/03_testcases.json` theo `references/testcase-format.md`. Sau khi reviewer rà soát và bổ sung xong, xuất Excel:

```
.venv/bin/python -I .claude/skills/testcase-design/scripts/build_xlsx.py \
  --input _workspace/03_testcases.json --output output/TestCases_<tên-ngắn>_<YYYYMMDD>.xlsx
```

Script kiểm tra cấu trúc, độ phủ REQ→TC và quét dữ liệu nhạy cảm. Lỗi cấu trúc (mã 2) hoặc dữ liệu nhạy cảm (mã 3) thì sửa JSON rồi chạy lại; không sửa script để qua mặt.

Sheet tạo ra: Tổng quan (thống kê tự cập nhật theo trạng thái), Test Cases, Traceability, Spec Mapping (điểm lệch và quyết định), Test Data, Pretest Log.

## Ghi kết quả chạy thử vào cùng file

Sau khi `browser-tester` ghi `_workspace/05_pretest_results.json` (định dạng ở `references/testcase-format.md`):

```
.venv/bin/python -I .claude/skills/testcase-design/scripts/write_results.py \
  --xlsx output/TestCases_<...>.xlsx --results _workspace/05_pretest_results.json
```

Script chỉ cập nhật các cột kết quả của đúng dòng TC ID, thêm dòng vào Pretest Log, và không đụng tới phần thiết kế test case.
