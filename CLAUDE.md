# QA Harness

## Harness: Phân tích yêu cầu và test case QA

**Mục tiêu:** Đối chiếu yêu cầu đầu vào với spec trong `specs/`, hỏi lại điểm sai/thiếu, xuất test case Excel vào `output/`, và chạy thử bằng Claude in Chrome nếu người dùng đồng ý.

**Hợp đồng bảo mật:** đọc `.claude/skills/qa-security-policy/SKILL.md` trước mọi bước. Không gửi spec ra ngoài máy, không xử lý mật khẩu (người dùng tự đăng nhập trên Chrome), không dùng dữ liệu thật, chỉ chạy trên môi trường test đã xác nhận.

**Hạ tầng:** `.venv/` (openpyxl, pypdf). Spec ở `specs/`, Excel ở `output/`, trung gian ở `_workspace/`.

**Điều kiện gọi:** khi người dùng đưa yêu cầu/tính năng/user story/bug cần phân tích, viết test case, đối chiếu spec hoặc kiểm thử (kể cả cập nhật, bổ sung, chạy lại pretest), dùng skill `qa-orchestrator`. Câu hỏi đơn giản về harness thì trả lời trực tiếp.

**Biến động:**
| Ngày | Thay đổi | Đối tượng | Lý do |
|---|---|---|---|
| 2026-10-19 | Dựng harness v2 lần đầu | Toàn bộ | - |
| 2026-10-20 | Link mở để chạy test do người dùng tự cung cấp, agent không tự đoán URL | qa-orchestrator, browser-pretest, browser-tester | Người dùng yêu cầu |
| 2026-10-19 | Đổi model của cả 4 agent sang sonnet | .claude/agents/*, qa-orchestrator | Người dùng yêu cầu chỉ dùng sonnet, không dùng opus |
