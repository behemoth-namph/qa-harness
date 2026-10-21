"""Hằng số và bộ quét bảo mật dùng chung cho build_xlsx.py và write_results.py.

Quét bảo mật chạy TRƯỚC khi ghi bất cứ thứ gì vào file Excel: nếu phát hiện chuỗi giống
mật khẩu, token, khóa API, số thẻ, CCCD/CMND, số điện thoại hay email thật thì dừng và báo
vị trí (giá trị được che), không ghi file.
"""
import re

STATUSES = ["Not Run", "Pass", "Fail", "Blocked", "Skipped"]
PRIORITIES = ["P0", "P1", "P2", "P3"]
MAPPING_STATUSES = ["MATCH", "CONFLICT", "MISSING_IN_SPEC", "AMBIGUOUS", "SPEC_ONLY"]

# Tên miền email được phép (địa chỉ giả dùng cho dữ liệu test)
SAFE_EMAIL_DOMAINS = ("example.com", "example.org", "example.net", "test.local", "test.invalid", "mailinator.test")

_PLACEHOLDER = re.compile(r"^<[^<>]+>$|^\{\{[^{}]+\}\}$|^\*{3,}$")

SECRET_PATTERNS = [
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("api_key", re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9]{16,}\b|\bAKIA[0-9A-Z]{16}\b|\bghp_[A-Za-z0-9]{20,}\b|\bxox[bap]-[A-Za-z0-9-]{10,}\b")),
    ("bearer", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    ("password_value", re.compile(r"(?i)\b(?:password|passwd|mật khẩu|mat khau|pwd|secret|token|otp|mã otp)\s*[:=]\s*(\S+)")),
    ("credit_card", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    # Chỉ bắt khi đi kèm từ khóa, tránh nhầm với giá trị biên số như 999999999
    ("national_id", re.compile(r"(?i)\b(?:cccd|cmnd|cmt|căn cước|passport|hộ chiếu)\D{0,12}\d{9,12}\b")),
    ("phone_vn", re.compile(r"(?<!\d)(?:\+?84|0)(?:3|5|7|8|9)\d{8}(?!\d)")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")),
]


def _mask(s: str) -> str:
    s = s.strip()
    return (s[:2] + "***" + s[-1:]) if len(s) > 4 else "***"


def scan_text(text: str):
    """Trả về danh sách (loại, giá trị đã che) các chuỗi nhạy cảm tìm thấy trong text."""
    hits = []
    if not isinstance(text, str) or not text:
        return hits
    for kind, pat in SECRET_PATTERNS:
        for m in pat.finditer(text):
            if kind == "password_value":
                if _PLACEHOLDER.match(m.group(1).strip(".,;")):
                    continue
            if kind == "email":
                if m.group(1).lower().endswith(SAFE_EMAIL_DOMAINS):
                    continue
            if kind == "credit_card":
                digits = re.sub(r"\D", "", m.group(0))
                if len(digits) < 13 or len(set(digits)) < 3:
                    continue
            hits.append((kind, _mask(m.group(0))))
    return hits


def scan_obj(obj, path="$"):
    """Quét đệ quy mọi chuỗi trong dict/list; trả về [(path, loại, giá trị che)]."""
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            found += scan_obj(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found += scan_obj(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        found += [(path, kind, val) for kind, val in scan_text(obj)]
    return found


def fail_on_secrets(obj, label):
    import sys
    found = scan_obj(obj)
    if found:
        print(f"[BẢO MẬT] Dừng: phát hiện {len(found)} chuỗi nhạy cảm trong {label}. Không ghi file Excel.", file=sys.stderr)
        for path, kind, val in found[:30]:
            print(f"  - {path}: {kind} ({val})", file=sys.stderr)
        print("Thay bằng placeholder dạng <TEN_BIEN> hoặc email @example.com rồi chạy lại.", file=sys.stderr)
        sys.exit(3)
