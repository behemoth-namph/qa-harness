# Định dạng JSON

## `_workspace/03_testcases.json`

```json
{
  "meta": {
    "title": "Đăng nhập - bộ test v1",
    "input_summary": "Tóm tắt yêu cầu đầu vào",
    "spec_files": ["specs/auth/login.md"],
    "created": "2026-10-19",
    "env_note": "Chưa xác định (điền khi chạy thử)",
    "assumptions": "Các giả định người dùng đã chọn, mỗi giả định một dòng"
  },
  "requirements": [
    {
      "id": "REQ-01", "text": "Mật khẩu tối thiểu 8 ký tự", "spec_ref": "specs/auth/login.md#2.1",
      "mapping_status": "MATCH | CONFLICT | MISSING_IN_SPEC | AMBIGUOUS | SPEC_ONLY",
      "discrepancy": "(chỉ khi khác MATCH)", "spec_quote": "trích dẫn", "question": "câu đã hỏi", "resolution": "quyết định của người dùng"
    }
  ],
  "test_cases": [
    {
      "tc_id": "TC-AUTH-001",
      "module": "Xác thực",
      "feature": "Đăng nhập",
      "req_ids": ["REQ-01"],
      "spec_ref": "specs/auth/login.md#2.1",
      "title": "Mật khẩu 7 ký tự bị từ chối kèm thông báo độ dài tối thiểu",
      "type": "Functional | UI | Validation | Boundary | Negative | Permission | Security | Integration | Compatibility | Performance",
      "priority": "P0 | P1 | P2 | P3",
      "technique": "Phân tích giá trị biên",
      "preconditions": "Đang ở trang đăng ký; chưa đăng nhập",
      "test_data": "Mật khẩu: <PWD_7_CHARS> (7 ký tự, gồm chữ và số)",
      "steps": ["Mở trang đăng ký", "Nhập mật khẩu <PWD_7_CHARS> vào ô Mật khẩu", "Bấm nút Đăng ký"],
      "expected": "Không tạo tài khoản; hiển thị thông báo \"Mật khẩu tối thiểu 8 ký tự\" dưới ô Mật khẩu",
      "chrome_testable": "Y",
      "notes": ""
    }
  ],
  "test_data": [
    {"name": "PWD_7_CHARS", "description": "Mật khẩu 7 ký tự", "value": "Sinh khi chạy: 7 ký tự gồm chữ hoa, chữ thường, số"}
  ]
}
```

Các trường `status`, `actual`, `executed_at`, `executed_by` để trống khi thiết kế (mặc định `Not Run`).
`steps` và `expected` có thể là chuỗi hoặc mảng chuỗi (mảng được tự đánh số).

## `_workspace/05_pretest_results.json`

```json
{
  "run_label": "Chạy thử lần 1",
  "executed_by": "Claude in Chrome",
  "env": "Tên môi trường test (không ghi URL có token)",
  "results": [
    {"tc_id": "TC-AUTH-001", "status": "Pass | Fail | Blocked | Skipped", "actual": "Mô tả kết quả thực tế bằng chữ, đã che dữ liệu nhạy cảm", "note": "Với Fail: bước lệch, hành vi thấy được; với Blocked/Skipped: lý do"}
  ]
}
```
