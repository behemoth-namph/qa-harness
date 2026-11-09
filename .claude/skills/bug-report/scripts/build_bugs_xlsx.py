"""Tạo file Excel log bug chuẩn để giao cho dev.

Cách chạy (từ thư mục gốc dự án):
    .venv/bin/python -I .claude/skills/bug-report/scripts/build_bugs_xlsx.py \
        --input _workspace/06_bugs.json --output output/BugLog_<ten>_<YYYYMMDD>.xlsx
    # File mẫu trống để QA tự điền:
    .venv/bin/python -I .claude/skills/bug-report/scripts/build_bugs_xlsx.py \
        --template --output output/BugLog_Mau_<YYYYMMDD>.xlsx

Sheet: Hướng dẫn, Tổng quan, Bug Chức năng, Bug AI (chỉ khi có bug AI hoặc ở chế độ --template).
Mã thoát: 0 thành công; 2 sai cấu trúc/thiếu trường bắt buộc/file đầu ra đã tồn tại (không ghi đè);
3 phát hiện dữ liệu nhạy cảm hoặc link chứa tham số xác thực; 4 có cảnh báo chất lượng khi dùng --strict.
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bug_common import (AI_COLUMNS, FUNCTIONAL_COLUMNS, PRIORITIES, PLATFORMS, SEVERITIES, STATUSES,  # noqa: E402
                        BUG_TYPES, AI_ERROR_TYPES, REPRO_RATES, fail_on_credential_urls, fail_on_secrets,
                        normalize_priority, step_list, text, validate_bug)

from openpyxl import Workbook  # noqa: E402
from openpyxl.formatting.rule import CellIsRule  # noqa: E402
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from openpyxl.worksheet.datavalidation import DataValidation  # noqa: E402

GROUP_FILL = {"id": "1F3864", "env": "385723", "repro": "7F3F00", "evidence": "5B2C6F", "track": "404040"}
GROUP_NOTE = [("id", "Nhận diện bug", "1F3864"), ("env", "Môi trường", "385723"),
              ("repro", "Tái hiện: làm gì, thấy gì, mong đợi gì", "7F3F00"),
              ("evidence", "Dẫn chứng và truy vết", "5B2C6F"), ("track", "Theo dõi xử lý", "404040")]
HEADER_FONT = Font(bold=True, color="FFFFFF")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
KIND_SHEET = {"functional": "Bug Chức năng", "ai": "Bug AI"}
KIND_COLUMNS = {"functional": FUNCTIONAL_COLUMNS, "ai": AI_COLUMNS}
PREFIX = {"functional": "BUG", "ai": "BUG-AI"}


def cell_value(b, key, kind):
    v = b.get(key)
    if key == "steps":
        return "\n".join(f"{i}. {s}" for i, s in enumerate(step_list(v), 1))
    if key == "req_ids" and isinstance(v, list):
        return ", ".join(v)
    if key == "priority":
        return normalize_priority(v)
    if key == "status" and not v:
        return "New"
    if key == "logged_at" and not v:
        return datetime.now().strftime("%Y-%m-%d")
    return text(v)


def style_header(ws, columns):
    for idx, (_, _, _, grp) in enumerate(columns, 1):
        c = ws.cell(1, idx)
        c.fill = PatternFill("solid", fgColor=GROUP_FILL[grp])
        c.font, c.border = HEADER_FONT, BORDER
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    ws.row_dimensions[1].height = 48


def add_list_validation(ws, col_letter, items, last, warn_only=False):
    formula = '"' + ",".join(items) + '"'
    assert len(formula) <= 255, "danh sách quá dài cho validation nội tuyến"
    dv = DataValidation(type="list", formula1=formula, allow_blank=True)
    if warn_only:
        dv.errorStyle = "warning"
    ws.add_data_validation(dv)
    dv.add(f"{col_letter}2:{col_letter}{last}")


def build_log_sheet(wb, kind, bugs):
    columns = KIND_COLUMNS[kind]
    ws = wb.create_sheet(KIND_SHEET[kind])
    ws.append([c[1] for c in columns])
    style_header(ws, columns)
    for b in bugs:
        ws.append([cell_value(b, k, kind) for k, _, _, _ in columns])
    for idx, (_, _, w, _) in enumerate(columns, 1):
        ws.column_dimensions[get_column_letter(idx)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment, c.border = WRAP, BORDER
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{max(len(bugs) + 1, 2)}"
    col = {k: get_column_letter(i) for i, (k, _, _, _) in enumerate(columns, 1)}
    last = max(len(bugs) + 1, 2) + 500
    add_list_validation(ws, col["severity"], SEVERITIES, last)
    add_list_validation(ws, col["priority"], [str(p) for p in PRIORITIES], last)
    add_list_validation(ws, col["status"], STATUSES, last)
    add_list_validation(ws, col["platform"], PLATFORMS, last)
    add_list_validation(ws, col["repro_rate"], REPRO_RATES, last, warn_only=True)  # cho phép thêm "– 3/3 lần"
    if kind == "functional":
        add_list_validation(ws, col["bug_type"], BUG_TYPES, last)
    else:
        add_list_validation(ws, col["ai_error_type"], AI_ERROR_TYPES, last)
    st = f"{col['status']}2:{col['status']}{last}"
    for val, color in (("Closed", "C6EFCE"), ("New", "FFC7CE"), ("Reopen", "FF9999"), ("In Progress", "FFEB9C"),
                       ("Dev done", "BDD7EE"), ("Testing", "DDEBF7"), ("Chưa tái hiện", "F8CBAD"),
                       ("Not A Bug", "D9D9D9"), ("Won't Fix", "D9D9D9"), ("Stop", "D9D9D9")):
        ws.conditional_formatting.add(st, CellIsRule(operator="equal", formula=[f'"{val}"'], fill=PatternFill("solid", bgColor=color)))
    sv = f"{col['severity']}2:{col['severity']}{last}"
    for val, color in ((SEVERITIES[0], "FF9999"), (SEVERITIES[1], "FFC7CE"), (SEVERITIES[2], "FFEB9C")):
        ws.conditional_formatting.add(sv, CellIsRule(operator="equal", formula=[f'"{val}"'], fill=PatternFill("solid", bgColor=color)))
    return ws, col, last


def put_table(ws, header, rows, widths=None):
    ws.append(header)
    r = ws.max_row
    for c in ws[r]:
        c.fill, c.font, c.border = PatternFill("solid", fgColor="1F3864"), HEADER_FONT, BORDER
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
    for row in rows:
        ws.append(row)
        for c in ws[ws.max_row]:
            c.alignment, c.border = WRAP, BORDER


def build_guide(wb, template):
    ws = wb.create_sheet("Hướng dẫn", 0)
    for col, w in zip("ABCD", (30, 56, 56, 40)):
        ws.column_dimensions[col].width = w

    def title(t):
        ws.append([])
        ws.append([t])
        ws.cell(ws.max_row, 1).font = Font(bold=True, size=12, color="1F3864")

    ws.append(["LOG BUG – HƯỚNG DẪN GHI BUG ĐỂ DEV TÁI HIỆN ĐƯỢC"])
    ws.cell(1, 1).font = Font(bold=True, size=14)
    ws.append(["Nguyên tắc: dev đọc bug này mà không được hỏi lại QA. Mỗi bug phải trả lời đủ 6 câu dưới đây."])
    ws.cell(2, 1).alignment = Alignment(wrap_text=False)

    title("1. Sáu câu mỗi bug phải trả lời (ứng với cột nào)")
    put_table(ws, ["Câu hỏi của dev", "Cột trả lời", "Viết thế nào cho đủ"], [
        ["Lỗi ở đâu?", "Tiêu đề, Màn hình/Module, Chức năng", "Tiêu đề dạng [Màn hình > Chức năng] hiện tượng cụ thể. Không viết \"Lỗi tạo chương trình\"."],
        ["Tôi phải chuẩn bị gì?", "Môi trường test, Trình duyệt/Thiết bị + OS, Phiên bản/build, Tài khoản/vai trò, Điều kiện tiên quyết, Dữ liệu test", "Ghi môi trường nào, build nào, vai trò nào (placeholder), dữ liệu cần có sẵn. Chưa biết thì ghi \"Không rõ\", không để trống."],
        ["Tôi làm gì để thấy lỗi?", "Các bước tái hiện", "Mỗi dòng một thao tác, nêu tên nút/trường/giá trị. Người chưa từng dùng chức năng vẫn làm theo được."],
        ["Tôi thấy gì?", "Kết quả thực tế", "Mô tả hiện tượng: thông báo, giá trị hiển thị, màn hình hiện ra. Không viết \"không chạy\", \"bị lỗi\" trơn."],
        ["Lẽ ra phải thấy gì, theo đâu?", "Kết quả mong đợi, Căn cứ mong đợi", "Hành vi đúng cụ thể và nguồn (spec file/mục, yêu cầu BA, ticket). Thiếu nguồn thì ghi \"cần BA xác nhận\"."],
        ["Có chắc không, bằng chứng đâu?", "Tần suất tái hiện, Dẫn chứng bằng chữ, Link ảnh/video, Link màn hình lỗi", "Ghi đã làm lại mấy lần thì ra lỗi mấy lần. Chép nguyên văn thông báo/giá trị. Link ảnh do QA tự dán."],
    ])

    title("2. Mức độ nghiêm trọng (tác động kỹ thuật) và ưu tiên sửa (độ gấp theo nghiệp vụ)")
    put_table(ws, ["Giá trị", "Khi nào dùng"], [
        [SEVERITIES[0], "Chặn luồng chính, mất/sai dữ liệu, lỗi bảo mật, sập ứng dụng. Không có cách né."],
        [SEVERITIES[1], "Chức năng quan trọng hỏng hoặc sai kết quả tính toán, nhưng còn cách né hoặc chỉ một nhóm người dùng bị ảnh hưởng."],
        [SEVERITIES[2], "Chức năng phụ sai, validation thiếu, hiển thị sai không làm hỏng dữ liệu."],
        [SEVERITIES[3], "Giao diện lệch, chính tả, thẩm mỹ."],
        ["Ưu tiên sửa 1 / 2 / 3", "1 = sửa trước (cao), 2 = trung bình, 3 = thấp. BA/PM quyết định; QA đề xuất. Giữ thang 1/2/3 của file log cũ (không dùng 0, Normal, Low)."],
    ])

    title("3. Trạng thái và ai đổi")
    put_table(ws, ["Trạng thái", "Ý nghĩa", "Ai đổi"], [
        ["New", "QA vừa log, chưa ai nhận.", "QA"],
        ["In Progress", "Dev đang sửa.", "Dev"],
        ["Dev done", "Dev đã sửa xong, ghi build đã fix vào DEV note, chờ QA test lại.", "Dev"],
        ["Testing", "QA đang test lại.", "QA"],
        ["Closed", "Đã test lại, đạt. Ghi ngày và build vào Lịch sử test lại.", "QA"],
        ["Reopen", "Test lại vẫn lỗi. Ghi chi tiết lần test lại vào Lịch sử test lại.", "QA"],
        ["Chưa tái hiện", "Dev không tái hiện được. QA bổ sung bước, môi trường, dẫn chứng rồi trả về In Progress.", "Dev"],
        ["Not A Bug", "Đúng thiết kế/spec. Dev ghi căn cứ vào DEV note, BA xác nhận.", "Dev + BA"],
        ["Won't Fix", "Biết lỗi nhưng quyết định không sửa. Ghi lý do và người quyết định.", "BA/PM"],
        ["Stop", "Tạm dừng, chưa xử lý (chờ quyết định hoặc chờ bên thứ ba).", "BA/PM"],
    ])

    title("4. Tần suất tái hiện")
    put_table(ws, ["Giá trị", "Ý nghĩa"], [
        ["Luôn luôn – 3/3 lần", "Làm lại đúng các bước thì lần nào cũng ra lỗi. Ghi số lần đã thử."],
        ["Thỉnh thoảng – 2/5 lần", "Có lần ra, có lần không. Ghi thêm điều kiện nghi ngờ (mạng chậm, dữ liệu lớn, thao tác nhanh) vào Điều kiện tiên quyết."],
        ["Hiếm gặp – 1/5 lần", "Thấy một lần, thử lại hầu như không ra. Nêu rõ trong Dẫn chứng lần gặp đó làm gì."],
        ["Chưa tái hiện lại", "Mới thấy một lần, chưa thử lại. Nên thử lại trước khi giao dev."],
    ])
    ws.append(["Với bug AI: tần suất là hỏi lại cùng câu hỏi N lần, AI sai mấy lần (câu trả lời AI có thể khác nhau giữa các lần)."])

    title("5. Quy tắc an toàn dữ liệu (file này được chia sẻ cho dev)")
    for line in (
        "Không dán mật khẩu, OTP, token, khóa API vào bất kỳ ô nào. Cần nêu tài khoản thì ghi vai trò hoặc placeholder, vd <TEST_ADMIN>.",
        "Link màn hình lỗi: chỉ link môi trường test, đã bỏ tham số xác thực (token, key, secret, session...). Script sẽ chặn link còn chứa chúng.",
        "Dữ liệu test dùng giá trị giả (email @example.com, số điện thoại giả). Không chép dữ liệu thật của khách hàng; chỉ nêu loại dữ liệu.",
        "Ảnh/video: QA tự chụp, che dữ liệu nhạy cảm rồi dán link vào cột Link ảnh/video. Công cụ harness không chụp, lưu hay tải ảnh lên dịch vụ nào.",
    ):
        ws.append([line])

    if template:
        title("6. Ví dụ: cách ghi thường gặp và cách ghi chuẩn (dữ liệu minh họa, không phải bug thật)")
        put_table(ws, ["Cột", "Cách ghi thường gặp (dev phải hỏi lại)", "Cách ghi chuẩn (dev tự tái hiện được)"], [
            ["Tiêu đề", "Ô text ngân sách cho phép nhập số âm", "[Quản lý chương trình > Tạo chương trình] Ô Ngân sách chấp nhận số âm và lưu thành công"],
            ["Môi trường", "(để trống)", "Web | Test (<TÊN_MÔI_TRƯỜNG_TEST>) | Chrome <PHIÊN_BẢN>, macOS | build <MÃ_BUILD> | <TEST_ADMIN> vai trò Quản trị chương trình"],
            ["Điều kiện, dữ liệu", "(để trống)", "Đã đăng nhập bằng tài khoản test có quyền tạo chương trình. Tên chương trình: <TEN_CT_TEST>; Ngân sách: -1000"],
            ["Các bước", "(để trống)", "1. Vào menu Quản lý chương trình > Tạo chương trình\n2. Nhập Tên chương trình = <TEN_CT_TEST> và các trường bắt buộc khác bằng giá trị hợp lệ\n3. Nhập Ngân sách = -1000\n4. Bấm nút Lưu"],
            ["Kết quả thực tế", "(không có, chỉ nêu \"cho phép nhập số âm\")", "Lưu thành công, không có thông báo lỗi. Mở chi tiết chương trình thấy Ngân sách hiển thị -1.000."],
            ["Kết quả mong đợi", "Không cho nhập số âm", "Không cho lưu; hiện thông báo lỗi dưới ô Ngân sách yêu cầu nhập số lớn hơn hoặc bằng 0"],
            ["Căn cứ mong đợi", "(để trống)", "Yêu cầu BA: ngân sách phải ≥ 0 (<SPEC_HOẶC_TICKET>)"],
            ["Tần suất, dẫn chứng", "(để trống)", "Luôn luôn – 3/3 lần. Sau bước 4 hiện thông báo \"Lưu thành công\" (nguyên văn); ô Ngân sách trong chi tiết hiển thị \"-1.000\"."],
        ])
        ws.append([])
        put_table(ws, ["Cột (bug AI)", "Cách ghi thường gặp", "Cách ghi chuẩn"], [
            ["Tiêu đề", "Sai tổng", "[KPI doanh số] AI cộng thiếu cột tháng trùng khi hỏi tổng cả năm"],
            ["Câu hỏi, phản hồi", "(chỉ có ảnh cap)", "Câu hỏi nguyên văn: \"cho tôi tổng cả năm\". Phản hồi AI chép nguyên văn: \"Tổng mục tiêu doanh số cả năm 2026 là 850 tỷ đồng\"."],
            ["Điểm sai cụ thể", "(để trống)", "Bảng có 2 cột tháng 4 và 2 cột tháng 5; AI chỉ cộng mỗi tháng một cột nên thiếu 70 tỷ so với tổng đúng 920 tỷ."],
            ["Mong muốn, nguồn đúng", "(để trống hoặc chỉ link ảnh)", "Phản hồi nêu 920 tỷ đồng và nói rõ đã cộng đủ các cột tháng. Nguồn: <TÊN_TÀI_LIỆU>, sheet <TÊN_SHEET>, dòng Tổng."],
            ["Tần suất", "(để trống)", "Hỏi lại 5 lần, sai 4/5 lần (một lần AI cộng đúng)."],
        ])


def build(data, out_path, template):
    wb = Workbook()
    wb.remove(wb.active)
    bugs = data.get("bugs", [])
    counters = {"functional": 0, "ai": 0}
    by_kind = {"functional": [], "ai": []}
    for b in bugs:
        kind = b.get("kind", "functional")
        counters[kind] += 1
        b.setdefault("bug_id", f"{PREFIX[kind]}-{counters[kind]:03d}")
        by_kind[kind].append(b)

    build_guide(wb, template)
    ov = wb.create_sheet("Tổng quan", 1)
    sheets = {}
    for kind in ("functional", "ai"):
        if by_kind[kind] or template:
            sheets[kind] = build_log_sheet(wb, kind, by_kind[kind])

    meta = data.get("meta", {})
    ov.column_dimensions["A"].width = 34
    ov.column_dimensions["B"].width = 64
    for k, v in (("Tên bộ bug", meta.get("title", "")), ("Dự án / sản phẩm", meta.get("project", "")),
                 ("Nguồn bug", meta.get("source", "")), ("Môi trường test chung", meta.get("env_note", "")),
                 ("Ngày tạo", meta.get("created") or datetime.now().strftime("%Y-%m-%d")),
                 ("Người lập", meta.get("reporter", ""))):
        ov.append([k, v])
        ov.cell(ov.max_row, 1).font = Font(bold=True)
        ov.cell(ov.max_row, 2).alignment = WRAP
    ov.append([])
    ov.append(["Thống kê", "Số lượng"])
    for c in ov[ov.max_row]:
        c.fill, c.font, c.border = PatternFill("solid", fgColor="1F3864"), HEADER_FONT, BORDER

    def total(key, value=None):
        parts = []
        for ws, col, last in sheets.values():
            rng = f"'{ws.title}'!${col[key]}$2:${col[key]}${last}"
            parts.append(f"COUNTA({rng})" if value is None else f'COUNTIF({rng},"{value}")')
        return "=" + ("+".join(parts) if parts else "0")

    ov.append(["Tổng số bug", total("bug_id")])
    total_row = ov.max_row
    status_row = {}
    for s in STATUSES:
        ov.append([f"Trạng thái: {s}", total("status", s)])
        status_row[s] = ov.max_row
    for s in SEVERITIES:
        ov.append([f"Mức độ: {s}", total("severity", s)])
    for p in PRIORITIES:
        ov.append([f"Ưu tiên sửa: {p}", total("priority", p)])
    # Còn mở = tổng trừ các trạng thái đã khép (đã xử lý xong hoặc chủ động không xử lý)
    closed_like = ("Closed", "Not A Bug", "Won't Fix", "Stop")
    ov.append(["Bug còn mở (trừ Closed, Not A Bug, Won't Fix, Stop)",
               f"=B{total_row}-" + "-".join(f"B{status_row[s]}" for s in closed_like)])

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    wb.save(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input")
    ap.add_argument("--output", required=True)
    ap.add_argument("--template", action="store_true", help="tạo file mẫu trống kèm ví dụ trong sheet Hướng dẫn")
    ap.add_argument("--strict", action="store_true", help="coi cảnh báo chất lượng là lỗi (mã 4)")
    a = ap.parse_args()
    if os.path.exists(a.output):
        print(f"[LỖI] {a.output} đã tồn tại, không ghi đè. Đặt hậu tố _v2, _v3.", file=sys.stderr)
        sys.exit(2)
    data = {"meta": {}, "bugs": []}
    if a.input:
        with open(a.input, encoding="utf-8") as f:
            data = json.load(f)
    elif not a.template:
        print("[LỖI] Cần --input (hoặc --template).", file=sys.stderr)
        sys.exit(2)

    bugs = [b for b in data.get("bugs", [])]
    if not bugs and not a.template:
        print("[LỖI] bugs rỗng", file=sys.stderr)
        sys.exit(2)
    errs, warns, seen = [], [], set()
    for i, b in enumerate(bugs):
        e, w = validate_bug(b, i)
        errs += e
        warns += w
        todo = b.get("_todo")
        if todo:
            errs.append(f"bugs[{i}] ({b.get('bug_id') or b.get('title', '?')[:30]}): còn mục chưa điền theo `_todo`: {todo}")
        bid = b.get("bug_id")
        if bid:
            if bid in seen:
                errs.append(f"Bug ID trùng: {bid}")
            seen.add(bid)
    titles = [(b.get("module"), text(b.get("title")).lower()) for b in bugs]
    for t in {t for t in titles if titles.count(t) > 1}:
        warns.append(f"Có {titles.count(t)} bug trùng tiêu đề trong '{t[0]}': có thể là trùng lặp")
    if errs:
        print("[LỖI CẤU TRÚC / THIẾU THÔNG TIN]", file=sys.stderr)
        for e in errs[:60]:
            print("  -", e, file=sys.stderr)
        sys.exit(2)
    payload = {k: v for k, v in data.items()}
    fail_on_secrets(payload, os.path.basename(a.input or "template"))
    fail_on_credential_urls(payload, os.path.basename(a.input or "template"))
    if warns:
        print("[CẢNH BÁO CHẤT LƯỢNG] (dev có thể phải hỏi lại QA nếu không sửa)", file=sys.stderr)
        for w in warns[:60]:
            print("  -", w, file=sys.stderr)
        if a.strict:
            sys.exit(4)
    build(data, a.output, a.template)
    print(f"Đã tạo {a.output}: {len(bugs)} bug" + (" (file mẫu)" if a.template else "") +
          (f", {len(warns)} cảnh báo chất lượng" if warns else ""))


if __name__ == "__main__":
    main()
