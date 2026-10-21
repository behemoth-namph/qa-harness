# QA Harness

Bộ agent và skill cho [Claude Code](https://claude.com/claude-code) giúp QA:

1. Nhận yêu cầu / user story / bug.
2. Đối chiếu với spec của dự án trong `specs/` và phân loại điểm khớp, mâu thuẫn, thiếu, mơ hồ.
3. Hỏi lại người đưa yêu cầu về các điểm sai/thiếu.
4. Thiết kế test case đầy đủ, được một agent khác rà soát, rồi xuất file Excel vào `output/`.
5. Nếu bạn đồng ý, chạy thử các test case trên môi trường test bằng Claude in Chrome và ghi kết quả vào cùng file Excel.

Harness chỉ chứa quy trình, không chứa spec hay dữ liệu của dự án nào. Mỗi dự án dùng một bản clone riêng.

## Yêu cầu

- Claude Code (CLI hoặc extension VS Code)
- Python 3.9 trở lên
- Chỉ khi chạy thử trên trình duyệt: extension Claude in Chrome
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
4. Nhận file Excel tại `output/TestCases_<tên>_<YYYYMMDD>.xlsx`.
5. Khi được hỏi có chạy thử bằng Chrome không: chọn Có thì **tự cung cấp link môi trường test** (không phải production) và **tự đăng nhập trực tiếp trên Chrome**.

## Cấu trúc

```
.claude/
  agents/     spec-analyst, testcase-designer, testcase-reviewer, browser-tester
  skills/
    qa-orchestrator/       điều phối toàn bộ quy trình
    spec-mapping/          đối chiếu yêu cầu với spec
    testcase-design/       thiết kế test case, xuất và ghi kết quả vào Excel
    browser-pretest/       chạy thử bằng Chrome
    qa-security-policy/    quy tắc bảo mật bắt buộc cho mọi bước
  settings.json            các tool bị chặn (đọc mật khẩu/cookie/network, tải file lên...)
CLAUDE.md                  điều kiện gọi harness
specs/                     spec của dự án (không đưa lên git)
output/                    file Excel test case (không đưa lên git)
_workspace/                file trung gian, tự sinh khi chạy (không đưa lên git)
```

## Bảo mật

Chi tiết ở `.claude/skills/qa-security-policy/SKILL.md`. Tóm tắt:

- Spec và yêu cầu không được gửi ra dịch vụ ngoài máy. `WebFetch` và `WebSearch` bị chặn trong `.claude/settings.json`.
- Agent không xử lý mật khẩu, OTP, token. Bạn tự đăng nhập trên Chrome.
- `javascript_tool`, `read_network_requests`, `gif_creator`... bị chặn để agent không đọc cookie, storage hay header xác thực.
- Test case chỉ dùng placeholder hoặc dữ liệu giả. Script xuất Excel quét mật khẩu, token, thẻ, CCCD, số điện thoại, email thật và dừng nếu phát hiện.
- Chỉ chạy trên môi trường test đã xác nhận, không làm thao tác không thể hoàn tác (xóa hàng loạt, thanh toán, gửi email/SMS thật).

`specs/*`, `output/*` và `_workspace/` chứa thông tin nội bộ của dự án và đã nằm trong `.gitignore`. Không dùng `git add -f` cho các thư mục này, và không sửa `.claude/settings.json` để nới các quy tắc chặn.

## Tùy chỉnh

- Cả 4 agent đang dùng model `sonnet`. Đổi trong phần frontmatter của `.claude/agents/*.md` nếu cần.
- Khi sửa agent hoặc skill, ghi lại thay đổi vào bảng "Biến động" trong `CLAUDE.md`.
