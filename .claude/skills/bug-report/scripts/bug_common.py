"""Hằng số, cột và bộ kiểm chất lượng dùng chung cho build_bugs_xlsx.py và draft_bugs.py.

Mục tiêu của bộ kiểm: một bug đưa cho dev phải đủ để dev tự tái hiện mà không phải hỏi lại.
Các trường bắt buộc và quy tắc dưới đây rút ra từ khảo sát file log bug thực của dự án
(nhiều bug thiếu bước tái hiện, môi trường, dẫn chứng; giá trị ưu tiên/trạng thái không thống nhất).
"""
import os
import re
import sys
from urllib.parse import parse_qsl, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "testcase-design", "scripts"))
from xlsx_common import fail_on_secrets, scan_text  # noqa: E402,F401

STATUSES = ["New", "In Progress", "Dev done", "Testing", "Closed", "Reopen", "Stop",
            "Chưa tái hiện", "Not A Bug", "Won't Fix"]
SEVERITIES = ["S1 - Chặn", "S2 - Nghiêm trọng", "S3 - Trung bình", "S4 - Nhẹ"]
PRIORITIES = [1, 2, 3]  # 1 = cao, 3 = thấp (giữ thang 1/2/3 của file log cũ)
BUG_TYPES = ["Functional", "UI", "Validation", "Data", "Security", "Performance", "Compatibility", "Content"]
AI_ERROR_TYPES = ["Sai số liệu", "Bịa thông tin", "Thiếu thông tin", "Sai ngữ cảnh",
                  "Không trả lời dù có dữ liệu", "Sai giọng điệu/định dạng", "Lộ thông tin không được phép", "Khác"]
PLATFORMS = ["Web", "Android", "iOS", "API", "Khác"]
REPRO_RATES = ["Luôn luôn", "Thỉnh thoảng", "Hiếm gặp", "Chưa tái hiện lại"]
KINDS = ["functional", "ai"]

# (khóa, tiêu đề cột, độ rộng, nhóm). Nhóm chỉ để tô màu tiêu đề cho dễ tìm.
FUNCTIONAL_COLUMNS = [
    ("bug_id", "Bug ID", 12, "id"),
    ("title", "Tiêu đề bug\n[Màn hình > Chức năng] hiện tượng", 42, "id"),
    ("module", "Màn hình / Module", 22, "id"),
    ("feature", "Chức năng", 20, "id"),
    ("bug_type", "Loại bug", 14, "id"),
    ("severity", "Mức độ nghiêm trọng", 16, "id"),
    ("priority", "Ưu tiên sửa\n(1 cao – 3 thấp)", 12, "id"),
    ("platform", "Nền tảng", 10, "env"),
    ("env_name", "Môi trường test", 20, "env"),
    ("client", "Trình duyệt / Thiết bị + OS", 24, "env"),
    ("build", "Phiên bản / build", 18, "env"),
    ("account", "Tài khoản / vai trò dùng\n(placeholder)", 22, "env"),
    ("preconditions", "Điều kiện tiên quyết", 32, "repro"),
    ("test_data", "Dữ liệu test\n(placeholder / dữ liệu giả)", 28, "repro"),
    ("steps", "Các bước tái hiện\n(mỗi dòng một thao tác)", 52, "repro"),
    ("actual", "Kết quả thực tế\n(hiện tượng lỗi)", 40, "repro"),
    ("expected", "Kết quả mong đợi", 38, "repro"),
    ("expected_source", "Căn cứ mong đợi\n(spec / yêu cầu / ticket)", 26, "repro"),
    ("repro_rate", "Tần suất tái hiện\n(vd: Luôn luôn – 3/3 lần)", 20, "repro"),
    ("evidence", "Dẫn chứng bằng chữ\n(thông báo nguyên văn, giá trị, vị trí)", 42, "evidence"),
    ("attachments", "Link ảnh / video\n(QA tự dán)", 28, "evidence"),
    ("fail_link", "Link màn hình lỗi\n(môi trường test, không token)", 34, "evidence"),
    ("impact", "Ảnh hưởng / phạm vi", 28, "evidence"),
    ("tc_id", "Test case liên quan", 14, "evidence"),
    ("req_ids", "Req ID", 12, "evidence"),
    ("reporter", "Người log", 12, "track"),
    ("logged_at", "Ngày log", 12, "track"),
    ("assignee", "Dev phụ trách", 12, "track"),
    ("status", "Trạng thái", 14, "track"),
    ("deadline", "Deadline", 12, "track"),
    ("ba_note", "BA note", 28, "track"),
    ("dev_note", "DEV note\n(nguyên nhân, cách sửa, build đã fix)", 32, "track"),
    ("retest_log", "Lịch sử test lại\n(ngày – build – kết quả)", 34, "track"),
]

AI_COLUMNS = [
    ("bug_id", "Bug ID", 12, "id"),
    ("title", "Tiêu đề bug\n[Chủ đề] điểm sai của AI", 42, "id"),
    ("module", "Bot / Chủ đề", 22, "id"),
    ("ai_error_type", "Loại lỗi AI", 22, "id"),
    ("severity", "Mức độ nghiêm trọng", 16, "id"),
    ("priority", "Ưu tiên sửa\n(1 cao – 3 thấp)", 12, "id"),
    ("platform", "Kênh / nền tảng", 12, "env"),
    ("env_name", "Môi trường test", 20, "env"),
    ("build", "Cấu hình bot / phiên bản dữ liệu train", 28, "env"),
    ("context", "Ngữ cảnh hội thoại\n(các lượt trước nếu có)", 34, "repro"),
    ("question", "Câu hỏi đã hỏi AI\n(nguyên văn)", 36, "repro"),
    ("ai_answer", "Phản hồi của AI\n(nguyên văn)", 48, "repro"),
    ("diff", "Điểm sai cụ thể\n(sai ở đâu, vì sao sai)", 40, "repro"),
    ("expected", "Phản hồi mong muốn", 44, "repro"),
    ("expected_source", "Nguồn đúng\n(tài liệu + mục/trang/ô)", 32, "repro"),
    ("repro_rate", "Tần suất tái hiện\n(hỏi lại N lần, sai mấy lần)", 22, "repro"),
    ("attachments", "Link ảnh cap đoạn chat\n(QA tự dán)", 28, "evidence"),
    ("impact", "Ảnh hưởng / phạm vi", 28, "evidence"),
    ("reporter", "Người log", 12, "track"),
    ("logged_at", "Ngày log", 12, "track"),
    ("assignee", "Dev phụ trách", 12, "track"),
    ("status", "Trạng thái", 14, "track"),
    ("deadline", "Deadline", 12, "track"),
    ("ba_note", "BA note", 28, "track"),
    ("dev_note", "DEV note\n(nguyên nhân, cách sửa, build đã fix)", 32, "track"),
    ("retest_log", "Lịch sử test lại\n(ngày – build – kết quả)", 34, "track"),
]

REQUIRED = {
    "functional": ["title", "module", "bug_type", "severity", "priority", "platform", "env_name", "client",
                   "build", "steps", "actual", "expected", "repro_rate", "evidence"],
    "ai": ["title", "module", "ai_error_type", "severity", "priority", "platform", "env_name", "question",
           "ai_answer", "diff", "expected", "expected_source", "repro_rate"],
}
# Nhãn theo từng loại bug (cùng khóa nhưng nhãn khác, vd `build` ở bug AI là cấu hình bot)
FIELD_LABEL = {
    "functional": {k: h.split("\n")[0] for k, h, _, _ in FUNCTIONAL_COLUMNS},
    "ai": {k: h.split("\n")[0] for k, h, _, _ in AI_COLUMNS},
}

# Tham số trong URL hoạt động như mật khẩu: link chứa chúng không được vào file bug (file được chia sẻ rộng).
_CRED_NAME = re.compile(r"token|secret|passw|pwd|api[_-]?key|access[_-]?key|auth|session|jwt|otp", re.I)
_CRED_EXACT = {"key", "sid", "sig", "signature", "code_verifier"}
_URL = re.compile(r"https?://[^\s<>\"']+", re.I)

_VAGUE_ONLY = re.compile(r"^\W*(lỗi|bị lỗi|không chạy|không hoạt động|sai|không được|fail|bug)\W*$", re.I)
_NUMBERING = re.compile(r"^\s*(?:B|Bước\s*)?\d+\s*[:.)\-–]\s*", re.I)


def step_list(v):
    """Chuẩn hóa `steps` thành danh sách câu (bỏ số thứ tự gõ tay để tự đánh số lại)."""
    if v is None:
        return []
    items = v if isinstance(v, list) else str(v).splitlines()
    out = []
    for x in items:
        s = _NUMBERING.sub("", str(x)).strip()
        if s:
            out.append(s)
    return out


def text(v):
    if v is None:
        return ""
    if isinstance(v, list):
        return "\n".join(str(x) for x in v)
    return str(v).strip()


def normalize_priority(v):
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return v


def find_credential_urls(obj, path="$"):
    """Trả về [(đường dẫn, tên tham số)] cho URL có tham số giống thông tin xác thực. Không trả giá trị."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            hits += find_credential_urls(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += find_credential_urls(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        for m in _URL.finditer(obj):
            u = urlparse(m.group(0).rstrip(".,;)"))
            if u.username or u.password:
                hits.append((path, "userinfo trong URL"))
            names = [n for n, _ in parse_qsl(u.query, keep_blank_values=True)]
            names += [n for n, _ in parse_qsl(u.fragment, keep_blank_values=True)]
            for n in names:
                if _CRED_NAME.search(n) or n.lower() in _CRED_EXACT:
                    hits.append((path, n))
    return hits


def fail_on_credential_urls(obj, label):
    hits = find_credential_urls(obj)
    if hits:
        print(f"[BẢO MẬT] Dừng: {len(hits)} link trong {label} chứa tham số xác thực. Không ghi file đầu ra.", file=sys.stderr)
        for path, name in hits[:30]:
            print(f"  - {path}: tham số '{name}'", file=sys.stderr)
        print("Bỏ phần tham số đó khỏi link (giữ lại phần đường dẫn và các tham số định danh thường) rồi chạy lại.", file=sys.stderr)
        sys.exit(3)


def validate_bug(b, idx):
    """Trả về (lỗi, cảnh báo) cho một bug. Lỗi chặn ghi file; cảnh báo chỉ nhắc (và chặn khi --strict)."""
    errs, warns = [], []
    kind = b.get("kind", "functional")
    tag = f"bugs[{idx}] ({b.get('bug_id') or b.get('title', '?')[:30]})"
    if kind not in KINDS:
        return [f"{tag}: kind '{kind}' không thuộc {KINDS}"], warns
    label = FIELD_LABEL[kind]
    for k in REQUIRED[kind]:
        v = b.get(k)
        if k == "steps":
            if len(step_list(v)) < 2:
                errs.append(f"{tag}: '{label[k]}' cần ít nhất 2 bước (một thao tác một dòng); dev phải làm theo được mà không đoán")
        elif v is None or text(v) == "":
            errs.append(f"{tag}: thiếu '{label[k]}'" + (" (chưa biết thì ghi rõ \"Không rõ\", đừng để trống)" if k in ("client", "build", "env_name") else ""))
    if errs:
        return errs, warns

    enums = [("severity", SEVERITIES), ("platform", PLATFORMS)]
    enums += [("bug_type", BUG_TYPES)] if kind == "functional" else [("ai_error_type", AI_ERROR_TYPES)]
    for k, allowed in enums:
        if b.get(k) not in allowed:
            errs.append(f"{tag}: {label[k]} '{b.get(k)}' không thuộc {allowed}")
    if normalize_priority(b.get("priority")) not in PRIORITIES:
        errs.append(f"{tag}: Ưu tiên '{b.get('priority')}' không thuộc {PRIORITIES}")
    st = b.get("status") or "New"
    if st not in STATUSES:
        errs.append(f"{tag}: Trạng thái '{st}' không thuộc {STATUSES}")
    if not any(text(b.get("repro_rate")).startswith(r) for r in REPRO_RATES):
        errs.append(f"{tag}: Tần suất tái hiện phải bắt đầu bằng một trong {REPRO_RATES} (vd \"Luôn luôn – 3/3 lần\")")
    if errs:
        return errs, warns

    title = text(b.get("title"))
    if len(title) < 15 or _VAGUE_ONLY.match(title):
        warns.append(f"{tag}: tiêu đề quá ngắn/chung chung; nêu màn hình + hiện tượng cụ thể")
    if kind == "functional":
        actual, expected = text(b.get("actual")), text(b.get("expected"))
        if len(actual) < 25 or _VAGUE_ONLY.match(actual):
            warns.append(f"{tag}: 'Kết quả thực tế' quá chung; ghi dev thấy gì (thông báo, giá trị, màn hình nào)")
        if actual.strip().lower() == expected.strip().lower():
            warns.append(f"{tag}: kết quả thực tế giống hệt kết quả mong đợi, bug mô tả chưa đúng chỗ lệch")
        if len(text(b.get("evidence"))) < 20:
            warns.append(f"{tag}: dẫn chứng bằng chữ quá ngắn; chép nguyên văn thông báo/giá trị đã thấy")
        for s in step_list(b.get("steps")):
            if len(s) < 6:
                warns.append(f"{tag}: bước '{s}' quá ngắn; nêu rõ nút/trường/giá trị")
        link = text(b.get("fail_link"))
        if link and not re.match(r"^https?://", link):
            warns.append(f"{tag}: Link màn hình lỗi nên bắt đầu bằng http(s)://")
    else:
        if text(b.get("ai_answer")).strip() == text(b.get("expected")).strip():
            warns.append(f"{tag}: phản hồi AI giống hệt phản hồi mong muốn")
        if len(text(b.get("diff"))) < 25:
            warns.append(f"{tag}: 'Điểm sai cụ thể' quá ngắn; chỉ rõ đoạn nào sai và đúng phải là gì")
    return errs, warns
