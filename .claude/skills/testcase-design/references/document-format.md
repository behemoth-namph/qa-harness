# Định dạng JSON mô tả tài liệu Word

`build_docx.py` đọc một file JSON và dựng `.docx` cục bộ. Chỉ mô tả **nội dung**; kiểu chữ, màu, bảng, chân trang do script lo để mọi tài liệu của harness trông đồng nhất.

## Khung

```json
{
  "title": "Đề xuất cập nhật spec – Đăng nhập",
  "subtitle": "Kết quả đối chiếu yêu cầu với spec",
  "meta": [["Dự án", "<TÊN_DỰ_ÁN>"], ["Ngày lập", "2026-11-06"], ["Trạng thái", "Chờ xác nhận"]],
  "orientation": "portrait",
  "footer": "Tài liệu nội bộ",
  "blocks": [ ... ]
}
```

| Trường | Bắt buộc | Ý nghĩa |
|---|---|---|
| `title` | có | Tiêu đề lớn đầu trang |
| `subtitle` | không | Dòng phụ dưới tiêu đề |
| `meta` | không | Bảng thông tin đầu tài liệu: danh sách cặp `[nhãn, giá trị]` |
| `orientation` | không | `portrait` (mặc định) hoặc `landscape`. Dùng `landscape` khi bảng có từ 5 cột trở lên |
| `footer` | không | Chữ ở chân trang, mặc định "Tài liệu nội bộ"; số trang tự thêm |
| `blocks` | có | Danh sách khối nội dung, theo thứ tự hiển thị |

## Các loại khối

| `type` | Trường | Dùng cho |
|---|---|---|
| `heading` | `level` (1–3), `text` | Tiêu đề mục. Dùng đúng cấp để Word có mục lục/điều hướng |
| `paragraph` | `text` | Đoạn văn. `text` là chuỗi, hoặc danh sách `{"text": "...", "bold": true, "italic": true}` để nhấn mạnh một phần |
| `bullets` | `items` | Danh sách gạch đầu dòng |
| `numbered` | `items` | Danh sách đánh số; mỗi khối `numbered` tự bắt đầu lại từ 1 |
| `table` | `header`, `rows`, `widths` (tùy chọn) | So sánh nhiều mục theo cùng thuộc tính. `widths` là tỉ lệ tương đối của các cột; mọi hàng phải có đủ số ô. Ô có thể chứa `\n` để xuống dòng |
| `keyvalue` | `items` | Bảng hai cột nhãn/giá trị cho thông tin ngắn |
| `note` | `text` | Khung nền vàng cho điều người đọc **phải để ý hoặc phải trả lời** |

## Nguyên tắc viết nội dung

- **Mở đầu bằng điều người đọc cần làm hoặc cần biết**, rồi mới đến chi tiết. Ví dụ mục "Tóm tắt" có số điểm cần quyết định và hạn.
- **Dùng bảng khi so sánh**, dùng gạch đầu dòng khi liệt kê ý độc lập, dùng đoạn văn khi giải thích lý do. Đừng nhồi chữ dài vào ô bảng.
- **Trích nguồn** (file, mục) trong cột riêng để người duyệt đối chiếu nhanh.
- **Không dùng ký hiệu Markdown** (`#`, `**`, `-`, dấu gạch ngược) trong `text`: Word không hiểu và sẽ hiện nguyên ký hiệu. Muốn đậm thì dùng `{"bold": true}`.
- Chỉ dùng placeholder hoặc dữ liệu giả (chính sách bảo mật). Script quét và dừng nếu thấy mật khẩu, token, email/số điện thoại thật.

## Lệnh

```
.venv/bin/python -I .claude/skills/testcase-design/scripts/build_docx.py \
  --input _workspace/doc_<tên>.json --output output/<Loại>_<tên-ngắn>_<YYYYMMDD>.docx
```

Mã thoát: `0` thành công; `2` JSON sai cấu trúc hoặc file đầu ra đã tồn tại (không ghi đè, đặt hậu tố `_v2`); `3` phát hiện dữ liệu nhạy cảm (sửa nội dung, không tắt bộ quét).

## Mẫu đặt tên

| Tài liệu | File JSON nguồn | File đầu ra |
|---|---|---|
| Đề xuất cập nhật spec | `_workspace/doc_spec_update.json` | `output/SpecUpdate_<tên>_<YYYYMMDD>.docx` |
| Thiếu sót và việc chưa hoàn thành | `_workspace/doc_gaps.json` | `output/QA_Gaps_<YYYYMMDD>.docx` |
| Ghi chú bảo mật | `_workspace/doc_security_notes.json` | `output/QA_SecurityNotes_<YYYYMMDD>.docx` |
| Tài liệu/đề xuất khác người dùng yêu cầu | `_workspace/doc_<tên>.json` | `output/<Loại>_<tên>_<YYYYMMDD>.docx` |
