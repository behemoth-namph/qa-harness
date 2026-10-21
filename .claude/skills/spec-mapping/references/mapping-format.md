# Định dạng file đối chiếu

## Đầu vào: `_workspace/01_requirements.json`

```json
{
  "input_summary": "Tóm tắt 1-2 câu yêu cầu đầu vào",
  "requirements": [
    {"id": "REQ-01", "text": "Một điểm yêu cầu nhỏ, kiểm chứng được", "source": "câu/đoạn gốc trong input"}
  ]
}
```

Mỗi REQ chỉ chứa một hành vi hoặc một quy tắc (ví dụ "mật khẩu tối thiểu 8 ký tự"), không gộp nhiều quy tắc.

## Đầu ra: `_workspace/02_mapping_<n>.json`

```json
{
  "files_covered": ["specs/auth/login.md"],
  "mappings": [
    {
      "req_id": "REQ-01",
      "status": "MATCH | CONFLICT | MISSING_IN_SPEC | AMBIGUOUS",
      "evidence": [{"file": "specs/auth/login.md", "section": "2.1 Mật khẩu", "quote": "Mật khẩu tối thiểu 8 ký tự"}],
      "discrepancy": "Chỉ điền khi status khác MATCH: điểm lệch nói bằng 1-2 câu",
      "question": "Câu hỏi gửi người đưa yêu cầu (chỉ khi cần xác nhận)",
      "options": ["Lựa chọn A (theo spec)", "Lựa chọn B (theo yêu cầu)"]
    }
  ],
  "spec_only": [
    {"id": "SPEC-01", "related_req": "REQ-01", "rule": "Tài khoản bị khóa 15 phút sau 5 lần nhập sai",
     "evidence": [{"file": "specs/auth/login.md", "section": "3.2", "quote": "..."}]}
  ]
}
```

## Sau khi hỏi người dùng: `_workspace/02_clarifications.json`

```json
{
  "decisions": [
    {"req_id": "REQ-02", "question": "...", "answer": "Theo spec: khóa sau 5 lần", "effective_text": "Khóa tài khoản sau 5 lần nhập sai liên tiếp", "note": "Spec cần cập nhật mục 3.2? (nếu có)"}
  ],
  "assumptions": [{"req_id": "REQ-05", "text": "Người dùng chọn bỏ qua, giả định ... "}],
  "spec_update_suggestions": ["specs/auth/login.md mục 2.1 nên ghi rõ ..."]
}
```
