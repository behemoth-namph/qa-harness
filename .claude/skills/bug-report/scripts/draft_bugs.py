"""Soạn nháp bug từ các test case Fail trong kết quả chạy thử.

    .venv/bin/python -I .claude/skills/bug-report/scripts/draft_bugs.py \
        --testcases _workspace/03_testcases.json --results _workspace/05_pretest_results.json \
        --output _workspace/06_bugs.json [--reporter "<tên QA>"]

Mỗi TC Fail thành một bug nháp: các bước, điều kiện, dữ liệu, kết quả mong đợi, căn cứ spec, Req ID lấy
nguyên từ test case (đã chi tiết sẵn); kết quả thực tế và dẫn chứng lấy từ kết quả chạy thử.
Mục chưa biết (trình duyệt/thiết bị, build, tần suất tái hiện, dẫn chứng...) KHÔNG được đoán: để trống
và liệt kê trong `_todo` để orchestrator hỏi người dùng trước khi dựng Excel.
Không ghi đè file đầu ra có sẵn (mã 2). Mã 3 nếu phát hiện dữ liệu nhạy cảm.
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bug_common import REQUIRED, fail_on_credential_urls, fail_on_secrets, step_list, text  # noqa: E402

SEVERITY_BY_TC_PRIORITY = {"P0": "S1 - Chặn", "P1": "S2 - Nghiêm trọng", "P2": "S3 - Trung bình", "P3": "S4 - Nhẹ"}
PRIORITY_BY_TC_PRIORITY = {"P0": 1, "P1": 1, "P2": 2, "P3": 3}
BUG_TYPE_BY_TC_TYPE = {"Functional": "Functional", "UI": "UI", "Validation": "Validation", "Boundary": "Validation",
                       "Negative": "Functional", "Permission": "Security", "Security": "Security",
                       "Integration": "Data", "Compatibility": "Compatibility", "Performance": "Performance"}
MARK = "  ← LỖI XẢY RA Ở BƯỚC NÀY"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--testcases", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--reporter", default="")
    a = ap.parse_args()
    if os.path.exists(a.output):
        print(f"[LỖI] {a.output} đã tồn tại, không ghi đè.", file=sys.stderr)
        sys.exit(2)
    with open(a.testcases, encoding="utf-8") as f:
        tcs = json.load(f)
    with open(a.results, encoding="utf-8") as f:
        res = json.load(f)
    fail_on_secrets(res, os.path.basename(a.results))
    fail_on_credential_urls(res, os.path.basename(a.results))
    by_id = {t["tc_id"]: t for t in tcs.get("test_cases", [])}

    bugs, missing = [], []
    for r in res.get("results", []):
        if r.get("status") != "Fail":
            continue
        tc = by_id.get(r["tc_id"])
        if not tc:
            missing.append(r["tc_id"])
            continue
        steps = step_list(tc.get("steps"))
        fs = r.get("failed_step")
        if isinstance(fs, int) and 1 <= fs <= len(steps):
            steps[fs - 1] += MARK
        module, feature = tc.get("module", ""), tc.get("feature", "")
        head = f"[{module} > {feature}]" if feature else f"[{module}]"
        summary = text(r.get("summary"))
        title = f"{head} {summary}" if summary else f"{head} Không đạt: {text(tc.get('title'))}"
        platform = tc.get("platform") or "Web"
        exp = tc.get("expected")
        expected = "\n".join(f"{i}. {x}" for i, x in enumerate(exp, 1)) if isinstance(exp, list) and len(exp) > 1 else text(exp)
        bug = {
            "kind": "functional",
            "title": title,
            "module": module,
            "feature": feature,
            "bug_type": BUG_TYPE_BY_TC_TYPE.get(tc.get("type"), "Functional"),
            "severity": SEVERITY_BY_TC_PRIORITY.get(tc.get("priority"), "S3 - Trung bình"),
            "priority": PRIORITY_BY_TC_PRIORITY.get(tc.get("priority"), 2),
            "platform": platform,
            "env_name": text(res.get("env")),
            "client": text(r.get("client")) or text(res.get("client")),
            "build": text(r.get("build")) or text(res.get("build")),
            "account": text(r.get("account")) or text(res.get("account")),
            "preconditions": text(tc.get("preconditions")),
            "test_data": text(tc.get("test_data")),
            "steps": steps,
            "actual": text(r.get("actual")),
            "expected": expected,
            "expected_source": text(tc.get("spec_ref")),
            "repro_rate": text(r.get("repro")),
            "evidence": text(r.get("evidence")) or text(r.get("note")),
            "attachments": "",
            "fail_link": text(r.get("link")),
            "tc_id": tc["tc_id"],
            "req_ids": tc.get("req_ids") or [],
            "reporter": a.reporter or text(res.get("executed_by")),
            "logged_at": datetime.now().strftime("%Y-%m-%d"),
            "status": "New",
        }
        todo = [k for k in REQUIRED["functional"] if k != "steps" and not text(bug.get(k))]
        if not summary:
            todo.append("title (viết lại cho nêu hiện tượng, đang là tiêu đề test case)")
        bug["_todo"] = todo
        bugs.append(bug)

    out = {"meta": {"title": text(tcs.get("meta", {}).get("title")) or "Bug từ chạy thử",
                    "source": f"Chạy thử: {text(res.get('run_label'))} ({text(res.get('executed_by'))})",
                    "env_note": text(res.get("env")),
                    "created": datetime.now().strftime("%Y-%m-%d"), "reporter": a.reporter},
           "bugs": bugs}
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    with open(a.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Đã soạn {len(bugs)} bug nháp vào {a.output}")
    pending = [(b["tc_id"], b["_todo"]) for b in bugs if b["_todo"]]
    for tid, todo in pending:
        print(f"  {tid}: cần bổ sung {todo}")
    if missing:
        print("Không tìm thấy TC trong testcases.json:", ", ".join(missing), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
