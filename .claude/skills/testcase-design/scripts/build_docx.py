"""Tạo tài liệu Word (.docx) cho người đọc từ một file JSON mô tả nội dung.

Cách chạy (từ thư mục gốc dự án):
    .venv/bin/python -I .claude/skills/testcase-design/scripts/build_docx.py \
        --input _workspace/doc_<ten>.json --output output/<Loai>_<ten>_<YYYYMMDD>.docx

Không cần thư viện ngoài: file .docx được dựng bằng zipfile + XML. Mọi xử lý diễn ra cục bộ.
Định dạng JSON ở .claude/skills/testcase-design/references/document-format.md.
Thoát với mã 2 nếu JSON sai cấu trúc hoặc file đầu ra đã tồn tại, mã 3 nếu phát hiện chuỗi nhạy cảm.
"""
import argparse
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from xlsx_common import fail_on_secrets  # noqa: E402

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')
HEAD_FILL, KEY_FILL, NOTE_FILL = "1F3864", "E7ECF4", "FFF4CE"
BLOCK_TYPES = ("heading", "paragraph", "bullets", "numbered", "table", "keyvalue", "note")
_BAD_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def esc(s):
    return escape(_BAD_XML.sub("", str(s)))


def runs(content, bold=False, italic=False, color=None):
    """content: chuỗi, hoặc danh sách chuỗi / {"text", "bold", "italic"}. Xuống dòng bằng \\n."""
    items = content if isinstance(content, list) else [content]
    out = []
    for it in items:
        d = it if isinstance(it, dict) else {"text": it}
        props = ""
        if bold or d.get("bold"):
            props += "<w:b/><w:bCs/>"
        if italic or d.get("italic"):
            props += "<w:i/><w:iCs/>"
        if color:
            props += f'<w:color w:val="{color}"/>'
        rpr = f"<w:rPr>{props}</w:rPr>" if props else ""
        body = "<w:br/>".join(f'<w:t xml:space="preserve">{esc(p)}</w:t>' for p in str(d.get("text", "")).split("\n"))
        out.append(f"<w:r>{rpr}{body}</w:r>")
    return "".join(out)


def para(content, style=None, before_text="", ppr_tail="", **fmt):
    """Thứ tự phần tử trong pPr theo schema: pStyle, numPr, pBdr, shd, spacing, ind, jc."""
    ppr = (f'<w:pStyle w:val="{style}"/>' if style else "") + before_text + ppr_tail
    return f"<w:p>{'<w:pPr>' + ppr + '</w:pPr>' if ppr else ''}{runs(content, **fmt)}</w:p>"


def cell(text, width, fill=None, bold=False, color=None, text_style="TableText"):
    shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
    lines = str(text).split("\n") if not isinstance(text, list) else [text]
    paras = "".join(para(ln, style=text_style, bold=bold, color=color) for ln in lines)
    return f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shd}</w:tcPr>{paras}</w:tc>'


def table(header, rows, weights, text_width):
    ncol = len(header) if header else len(rows[0])
    weights = weights or [1] * ncol
    total = float(sum(weights))
    widths = [int(text_width * w / total) for w in weights]
    widths[-1] += text_width - sum(widths)
    border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>'
                     for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    xml = (f'<w:tbl><w:tblPr><w:tblW w:w="{text_width}" w:type="dxa"/><w:tblBorders>{border}</w:tblBorders>'
           '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
           '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr>'
           "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>")
    if header:
        xml += ("<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>"
                + "".join(cell(h, w, fill=HEAD_FILL, bold=True, color="FFFFFF") for h, w in zip(header, widths)) + "</w:tr>")
    for r in rows:
        xml += "<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(cell(c, w) for c, w in zip(r, widths)) + "</w:tr>"
    return xml + "</w:tbl>" + para("", style="TableText")  # đoạn đệm: Word cần một đoạn sau bảng


def keyvalue(items, text_width):
    widths = [int(text_width * 0.28), 0]
    widths[1] = text_width - widths[0]
    border = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>'
                     for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    xml = (f'<w:tbl><w:tblPr><w:tblW w:w="{text_width}" w:type="dxa"/><w:tblBorders>{border}</w:tblBorders>'
           '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
           '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr>'
           + "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>")
    for k, v in items:
        xml += ("<w:tr><w:trPr><w:cantSplit/></w:trPr>" + cell(k, widths[0], fill=KEY_FILL, bold=True)
                + cell(v, widths[1]) + "</w:tr>")
    return xml + "</w:tbl>" + para("", style="TableText")


def validate(doc):
    errs = []
    if not isinstance(doc, dict):
        return ["JSON gốc phải là một object"]
    if not str(doc.get("title", "")).strip():
        errs.append("thiếu 'title'")
    blocks = doc.get("blocks")
    if not isinstance(blocks, list) or not blocks:
        errs.append("'blocks' phải là danh sách không rỗng")
        return errs
    if len(blocks) > 2000:
        errs.append("quá 2000 khối nội dung")
    if doc.get("orientation", "portrait") not in ("portrait", "landscape"):
        errs.append("'orientation' chỉ nhận portrait hoặc landscape")
    for i, b in enumerate(blocks):
        where = f"blocks[{i}]"
        t = b.get("type") if isinstance(b, dict) else None
        if t not in BLOCK_TYPES:
            errs.append(f"{where}: type phải thuộc {BLOCK_TYPES}")
            continue
        if t == "heading" and (b.get("level") not in (1, 2, 3) or not str(b.get("text", "")).strip()):
            errs.append(f"{where}: heading cần level 1-3 và text")
        elif t in ("paragraph", "note") and not b.get("text"):
            errs.append(f"{where}: {t} cần text")
        elif t in ("bullets", "numbered") and (not isinstance(b.get("items"), list) or not b["items"]):
            errs.append(f"{where}: {t} cần items là danh sách không rỗng")
        elif t == "keyvalue" and (not isinstance(b.get("items"), list) or any(not isinstance(p, list) or len(p) != 2 for p in b["items"])):
            errs.append(f"{where}: keyvalue cần items là danh sách các cặp [nhãn, giá trị]")
        elif t == "table":
            header, rows = b.get("header"), b.get("rows")
            if not isinstance(rows, list) or not rows or any(not isinstance(r, list) for r in rows):
                errs.append(f"{where}: table cần rows là danh sách các hàng (mỗi hàng là danh sách ô)")
                continue
            ncol = len(header) if header else len(rows[0])
            if any(len(r) != ncol for r in rows):
                errs.append(f"{where}: mọi hàng phải có đúng {ncol} ô")
            w = b.get("widths")
            if w is not None and (not isinstance(w, list) or len(w) != ncol or any(not isinstance(x, (int, float)) or x <= 0 for x in w)):
                errs.append(f"{where}: widths phải là {ncol} số dương")
    return errs


def build_parts(doc):
    landscape = doc.get("orientation") == "landscape"
    page_w, page_h, margin = (16838, 11906, 1134) if landscape else (11906, 16838, 1134)
    text_width = page_w - 2 * margin

    body = [para(doc["title"], style="Title")]
    if doc.get("subtitle"):
        body.append(para(doc["subtitle"], style="Subtitle"))
    if doc.get("meta"):
        body.append(keyvalue(doc["meta"], text_width))

    numbered_lists = 0
    for b in doc["blocks"]:
        t = b["type"]
        if t == "heading":
            body.append(para(b["text"], style=f"Heading{b['level']}"))
        elif t == "paragraph":
            body.append(para(b["text"]))
        elif t == "note":
            border = f'<w:pBdr><w:left w:val="single" w:sz="24" w:space="6" w:color="E0A800"/></w:pBdr>'
            body.append(para(b["text"], before_text=border + f'<w:shd w:val="clear" w:color="auto" w:fill="{NOTE_FILL}"/>',
                             ppr_tail='<w:spacing w:before="120" w:after="120"/><w:ind w:left="240"/>'))
        elif t == "bullets":
            for it in b["items"]:
                body.append(para(it, style="ListParagraph", before_text='<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'))
        elif t == "numbered":
            numbered_lists += 1
            num_id = numbered_lists + 1
            for it in b["items"]:
                body.append(para(it, style="ListParagraph", before_text=f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num_id}"/></w:numPr>'))
        elif t == "keyvalue":
            body.append(keyvalue(b["items"], text_width))
        elif t == "table":
            body.append(table(b.get("header"), b["rows"], b.get("widths"), text_width))

    orient = ' w:orient="landscape"' if landscape else ""
    sect = ('<w:sectPr><w:footerReference w:type="default" r:id="rId3"/>'
            f'<w:pgSz w:w="{page_w}" w:h="{page_h}"{orient}/>'
            f'<w:pgMar w:top="{margin}" w:right="{margin}" w:bottom="{margin}" w:left="{margin}" w:header="567" w:footer="567" w:gutter="0"/></w:sectPr>')
    document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{"".join(body)}{sect}</w:body></w:document>'

    def style(sid, name, based="Normal", ppr="", rpr="", nxt="Normal", extra=""):
        return (f'<w:style w:type="paragraph" w:styleId="{sid}"><w:name w:val="{name}"/>'
                + (f'<w:basedOn w:val="{based}"/>' if based else "") + f'<w:next w:val="{nxt}"/>{extra}<w:qFormat/>'
                + (f"<w:pPr>{ppr}</w:pPr>" if ppr else "") + (f"<w:rPr>{rpr}</w:rPr>" if rpr else "") + "</w:style>")

    styles = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {NS}><w:docDefaults><w:rPrDefault><w:rPr>'
              '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/><w:sz w:val="22"/><w:szCs w:val="22"/>'
              '<w:lang w:val="vi-VN" w:eastAsia="vi-VN" w:bidi="ar-SA"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr>'
              '<w:spacing w:after="120" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
              '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
              + style("Title", "Title", ppr='<w:spacing w:before="0" w:after="80"/>', rpr='<w:b/><w:color w:val="1F3864"/><w:sz w:val="44"/><w:szCs w:val="44"/>')
              + style("Subtitle", "Subtitle", ppr='<w:spacing w:after="200"/>', rpr='<w:color w:val="595959"/><w:sz w:val="26"/><w:szCs w:val="26"/>')
              + style("Heading1", "heading 1", ppr='<w:keepNext/><w:spacing w:before="360" w:after="120"/><w:outlineLvl w:val="0"/>', rpr='<w:b/><w:color w:val="1F3864"/><w:sz w:val="32"/><w:szCs w:val="32"/>')
              + style("Heading2", "heading 2", ppr='<w:keepNext/><w:spacing w:before="280" w:after="100"/><w:outlineLvl w:val="1"/>', rpr='<w:b/><w:color w:val="2F5496"/><w:sz w:val="26"/><w:szCs w:val="26"/>')
              + style("Heading3", "heading 3", ppr='<w:keepNext/><w:spacing w:before="200" w:after="80"/><w:outlineLvl w:val="2"/>', rpr='<w:b/><w:color w:val="404040"/><w:sz w:val="23"/><w:szCs w:val="23"/>')
              + style("ListParagraph", "List Paragraph", ppr='<w:spacing w:after="60"/><w:ind w:left="720"/>')
              + style("TableText", "Table Text", ppr='<w:spacing w:before="0" w:after="40" w:line="240" w:lineRule="auto"/>', rpr='<w:sz w:val="20"/><w:szCs w:val="20"/>')
              + style("Footer", "footer", ppr='<w:spacing w:after="0"/><w:jc w:val="center"/>', rpr='<w:color w:val="7F7F7F"/><w:sz w:val="18"/><w:szCs w:val="18"/>')
              + "</w:styles>")

    def lvl(fmt, text):
        return (f'<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="{fmt}"/><w:lvlText w:val="{text}"/><w:lvlJc w:val="left"/>'
                '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl>')

    # Mỗi danh sách số có abstractNum riêng: không phụ thuộc việc trình đọc có hiểu startOverride hay không
    abstracts = f'<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/>{lvl("bullet", "•")}</w:abstractNum>'
    nums = '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>'
    for n in range(1, numbered_lists + 1):
        abstracts += f'<w:abstractNum w:abstractNumId="{n}"><w:multiLevelType w:val="singleLevel"/>{lvl("decimal", "%1.")}</w:abstractNum>'
        nums += f'<w:num w:numId="{n + 1}"><w:abstractNumId w:val="{n}"/></w:num>'
    numbering = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering {NS}>{abstracts}{nums}</w:numbering>'

    footer_text = esc(doc.get("footer", "Tài liệu nội bộ"))
    footer = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {NS}><w:p><w:pPr><w:pStyle w:val="Footer"/></w:pPr>'
              f'<w:r><w:t xml:space="preserve">{footer_text} · Trang </w:t></w:r><w:r><w:fldChar w:fldCharType="begin"/></w:r>'
              '<w:r><w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r><w:fldChar w:fldCharType="separate"/></w:r>'
              '<w:r><w:t>1</w:t></w:r><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>')

    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    doc_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f'<Relationship Id="rId1" Type="{rel}/styles" Target="styles.xml"/><Relationship Id="rId2" Type="{rel}/numbering" Target="numbering.xml"/>'
                f'<Relationship Id="rId3" Type="{rel}/footer" Target="footer1.xml"/></Relationships>')
    root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 f'<Relationship Id="rId1" Type="{rel}/officeDocument" Target="word/document.xml"/>'
                 '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>')
    wml = "application/vnd.openxmlformats-officedocument.wordprocessingml"
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
                     f'<Override PartName="/word/document.xml" ContentType="{wml}.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="{wml}.styles+xml"/>'
                     f'<Override PartName="/word/numbering.xml" ContentType="{wml}.numbering+xml"/><Override PartName="/word/footer1.xml" ContentType="{wml}.footer+xml"/>'
                     '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>')
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f'<dc:title>{esc(doc["title"])}</dc:title><dc:creator>QA Harness</dc:creator>'
            f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created></cp:coreProperties>')
    return {"[Content_Types].xml": content_types, "_rels/.rels": root_rels, "word/document.xml": document, "word/styles.xml": styles,
            "word/numbering.xml": numbering, "word/footer1.xml": footer, "word/_rels/document.xml.rels": doc_rels, "docProps/core.xml": core}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    if not args.output.lower().endswith(".docx"):
        print("[LỖI] --output phải có đuôi .docx", file=sys.stderr)
        sys.exit(2)
    if os.path.exists(args.output):
        print(f"[LỖI] {args.output} đã tồn tại. Không ghi đè; đặt tên khác (hậu tố _v2, _v3).", file=sys.stderr)
        sys.exit(2)
    with open(args.input, encoding="utf-8") as f:
        doc = json.load(f)
    errs = validate(doc)
    if errs:
        print("[LỖI CẤU TRÚC] " + str(len(errs)) + " vấn đề:", file=sys.stderr)
        for e in errs[:30]:
            print("  - " + e, file=sys.stderr)
        sys.exit(2)
    fail_on_secrets(doc, "nội dung tài liệu")

    parts = build_parts(doc)
    for name, xml in parts.items():  # tự kiểm: mọi phần phải là XML hợp lệ trước khi ghi
        ET.fromstring(xml.encode("utf-8"))
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as z:
        for name, xml in parts.items():
            z.writestr(name, xml)
    print(f"Đã tạo {args.output} ({len(doc['blocks'])} khối nội dung)")


if __name__ == "__main__":
    main()
