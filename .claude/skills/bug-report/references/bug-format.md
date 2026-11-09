# Định dạng JSON log bug

## `_workspace/06_bugs.json`

```json
{
  "meta": {
    "title": "Bug đợt test 09/11",
    "project": "<TÊN_DỰ_ÁN>",
    "source": "Chạy thử lần 1 (Claude in Chrome) | Ghi chú bug của QA",
    "env_note": "Test (<TÊN_MÔI_TRƯỜNG_TEST>)",
    "created": "2026-11-09",
    "reporter": "<TÊN_QA>"
  },
  "bugs": [
    {
      "kind": "functional",
      "title": "[Quản lý chương trình > Tạo chương trình] Ô Ngân sách chấp nhận số âm và lưu thành công",
      "module": "Quản lý chương trình",
      "feature": "Tạo chương trình",
      "bug_type": "Validation",
      "severity": "S3 - Trung bình",
      "priority": 3,
      "platform": "Web",
      "env_name": "Test (<TÊN_MÔI_TRƯỜNG_TEST>)",
      "client": "Chrome <PHIÊN_BẢN>, macOS",
      "build": "<MÃ_BUILD> hoặc \"Không rõ\"",
      "account": "<TEST_ADMIN> (vai trò Quản trị chương trình)",
      "preconditions": "Đã đăng nhập bằng tài khoản test có quyền tạo chương trình",
      "test_data": "Tên chương trình: <TEN_CT_TEST>; Ngân sách: -1000",
      "steps": ["Vào menu Quản lý chương trình > Tạo chương trình", "Nhập Tên chương trình = <TEN_CT_TEST> và các trường bắt buộc khác bằng giá trị hợp lệ", "Nhập Ngân sách = -1000", "Bấm nút Lưu"],
      "actual": "Lưu thành công, không có thông báo lỗi. Mở chi tiết chương trình thấy Ngân sách hiển thị -1.000.",
      "expected": "Không cho lưu; hiện thông báo lỗi dưới ô Ngân sách yêu cầu nhập số lớn hơn hoặc bằng 0",
      "expected_source": "specs/loyalty/program.md#3.2 hoặc \"Yêu cầu BA: ngân sách ≥ 0\" hoặc \"cần BA xác nhận\"",
      "repro_rate": "Luôn luôn – 3/3 lần",
      "evidence": "Sau bước 4 hiện thông báo \"Lưu thành công\" (nguyên văn); ô Ngân sách trong chi tiết hiển thị \"-1.000\".",
      "attachments": "(QA tự dán link ảnh/video, có thể để trống)",
      "fail_link": "https://<host-môi-trường-test>/programs/create (không token)",
      "impact": "Báo cáo ngân sách có thể sai",
      "tc_id": "TC-CTR-004",
      "req_ids": ["REQ-04"],
      "reporter": "<TÊN_QA>",
      "logged_at": "2026-11-09",
      "assignee": "<DEV>",
      "status": "New",
      "deadline": "",
      "ba_note": "", "dev_note": "", "retest_log": ""
    },
    {
      "kind": "ai",
      "title": "[KPI doanh số] AI cộng thiếu cột tháng trùng khi hỏi tổng cả năm",
      "module": "Bot KPI",
      "ai_error_type": "Sai số liệu",
      "severity": "S2 - Nghiêm trọng",
      "priority": 1,
      "platform": "Web",
      "env_name": "Test",
      "build": "Cấu hình bot / phiên bản dữ liệu train (hoặc \"Không rõ\")",
      "context": "Các lượt hỏi trước nếu câu hỏi phụ thuộc ngữ cảnh",
      "question": "cho tôi tổng cả năm",
      "ai_answer": "Tổng mục tiêu doanh số cả năm 2026 là 850 tỷ đồng",
      "diff": "Bảng có 2 cột tháng 4 và 2 cột tháng 5; AI chỉ cộng mỗi tháng một cột nên thiếu 70 tỷ",
      "expected": "920 tỷ đồng, nêu rõ đã cộng đủ các cột tháng",
      "expected_source": "<TÊN_TÀI_LIỆU>, sheet <TÊN_SHEET>, dòng Tổng",
      "repro_rate": "Thỉnh thoảng – 4/5 lần"
    }
  ]
}
```

## Trường bắt buộc

| `kind` | Bắt buộc |
|---|---|
| `functional` (mặc định) | `title`, `module`, `bug_type`, `severity`, `priority`, `platform`, `env_name`, `client`, `build`, `steps` (≥ 2 bước), `actual`, `expected`, `repro_rate`, `evidence` |
| `ai` | `title`, `module`, `ai_error_type`, `severity`, `priority`, `platform`, `env_name`, `question`, `ai_answer`, `diff`, `expected`, `expected_source`, `repro_rate` |

Các trường còn lại tùy chọn. `bug_id` bỏ trống thì script tự đánh `BUG-001` / `BUG-AI-001`. `status` bỏ trống là `New`, `logged_at` bỏ trống là hôm nay. Khóa bắt đầu bằng `_` (như `_todo`) là ghi chú trung gian, script dừng nếu `_todo` còn nội dung: điền xong phải xóa khóa này.

`env_name`, `client`, `build` chưa biết thì ghi `"Không rõ"` (không để trống, để dev biết là chưa biết chứ không phải quên).

## Giá trị hợp lệ

| Trường | Giá trị |
|---|---|
| `severity` | `S1 - Chặn`, `S2 - Nghiêm trọng`, `S3 - Trung bình`, `S4 - Nhẹ` |
| `priority` | `1` (cao), `2`, `3` (thấp) |
| `bug_type` | `Functional`, `UI`, `Validation`, `Data`, `Security`, `Performance`, `Compatibility`, `Content` |
| `ai_error_type` | `Sai số liệu`, `Bịa thông tin`, `Thiếu thông tin`, `Sai ngữ cảnh`, `Không trả lời dù có dữ liệu`, `Sai giọng điệu/định dạng`, `Lộ thông tin không được phép`, `Khác` |
| `platform` | `Web`, `Android`, `iOS`, `API`, `Khác` (bug AI: kênh như `Web`, `Khác`) |
| `repro_rate` | bắt đầu bằng `Luôn luôn`, `Thỉnh thoảng`, `Hiếm gặp` hoặc `Chưa tái hiện lại`, có thể kèm số lần: `Luôn luôn – 3/3 lần` |
| `status` | `New`, `In Progress`, `Dev done`, `Testing`, `Closed`, `Reopen`, `Stop`, `Chưa tái hiện`, `Not A Bug`, `Won't Fix` |

## Cách chọn mức độ nghiêm trọng và ưu tiên

- **Nghiêm trọng** là tác động kỹ thuật, do QA đề xuất: S1 chặn luồng chính/mất hoặc sai dữ liệu/bảo mật/sập; S2 chức năng quan trọng hỏng nhưng còn cách né; S3 chức năng phụ, validation, hiển thị sai nhưng không hỏng dữ liệu; S4 giao diện, chính tả.
- **Ưu tiên sửa** là độ gấp nghiệp vụ, BA/PM quyết: 1 trước, 3 sau. Khi nháp từ test case Fail: P0→S1/1, P1→S2/1, P2→S3/2, P3→S4/3, QA/BA chỉnh lại nếu khác.

## Bước và số thứ tự

`steps` là mảng chuỗi (hoặc chuỗi nhiều dòng). Script tự đánh số 1, 2, 3...; số gõ tay như `1.` hay `B2:` bị bỏ để không bị đánh số đôi. Một dòng một thao tác: "Nhập Ngân sách = -1000" tách khỏi "Bấm Lưu". Ghi tên hiển thị của nút/trường như trên giao diện.

## Từ test case Fail sang bug (`draft_bugs.py`)

Kết quả chạy thử có thể mang thêm các trường tùy chọn (xem `testcase-format.md`) để bug nháp gần đủ ngay:

| Trường trong `05_pretest_results.json` | Vào bug |
|---|---|
| `summary` | Phần hiện tượng của `title` (thiếu thì tiêu đề là "Không đạt: <tiêu đề TC>" và `_todo` nhắc viết lại) |
| `failed_step` (số bước, bắt đầu từ 1) | Bước đó được đánh dấu "← LỖI XẢY RA Ở BƯỚC NÀY" |
| `actual` | `actual` |
| `evidence` (hoặc `note`) | `evidence` |
| `repro` (ví dụ "Luôn luôn – 2/2 lần") | `repro_rate` |
| `client`, `build`, `account`, `link` (mức kết quả hoặc mức file) | `client`, `build`, `account`, `fail_link` |
| `env` (mức file) | `env_name` |

`client` và `build` harness không tự biết (không đọc phiên bản trình duyệt bằng JavaScript, không đọc nội dung APK): hỏi người dùng.
