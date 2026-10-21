#!/usr/bin/env python3
"""Kiểm trích dẫn nguyên văn `"..." [T1 NHÃN tr.N]` trong .rst với trang PDF.

Dùng: python3 tools/check_quotes.py <file.rst|thư mục> ...
Chỉ in các trích dẫn không tìm thấy ở trang N (báo "gần" nếu thấy ở N-1/N+1).
Nhãn không có PDF (DRV, DTS, SRAM-zh) bị bỏ qua.
"""
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent
ROOT = DOCS.parent
PDF = {
    "TRM1": DOCS / "_assets/pdf/datasheet/trm/rk3588_part1.pdf",
    "TRM2": DOCS / "_assets/pdf/datasheet/trm/rk3588_part2.pdf",
    "DS V1.7": DOCS / "_assets/pdf/datasheet/soc/Rockchip_RK3588S_Datasheet_V1.7.pdf",
    "DS V1.3": DOCS / "_assets/pdf/datasheet/soc/Rockchip_RK3588_Datasheet_V1.3_20220328.pdf",
    "DS V0.1": DOCS / "_assets/pdf/datasheet/soc/02_RK3588_Datasheet_V0.1-20210727.pdf",
    "UG152": DOCS / "_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf",
    "API232": DOCS / "_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf",
    "OPL": DOCS / "_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf",
    "UG232": ROOT / "3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf",
    "QS232": ROOT / "3rdparty/rknn-toolkit2/doc/01_Rockchip_RKNPU_Quick_Start_RKNN_SDK_V2.3.2_EN.pdf",
}
CITE = re.compile(r"\[T[12] (?P<label>[A-Za-z0-9 .]+?) (?:tr|pdf)\.? ?(?P<page>\d+)[^\]]*\]")
Q1 = r'"(?:(?!\n\n)[^"]){12,}"'
# chuỗi trích dẫn nối nhau ("a" / "b" hoặc "a" ... "b") ngay trước nhãn nguồn
CHAIN = re.compile(r"(?P<q>" + Q1 + r"(?:\s*(?:/|\.\.\.)?\s*" + Q1 + r")*)\s*[.,]?\s*(?P<c>" + CITE.pattern + ")")
QUOTE = re.compile(r'"((?:(?!\n\n)[^"])+)"')


def norm(s):
    return re.sub(r"[^0-9a-z]+", "", s.lower())


@lru_cache(maxsize=None)
def page_text(label, page):
    if page < 1:
        return ""
    out = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), str(PDF[label]), "-"],
        capture_output=True, text=True).stdout
    return norm(out)


def segments(q):
    return [norm(p) for p in re.split(r"\s*(?:\.\.\.|…| / )\s*", q) if len(norm(p)) >= 10]


def check(path):
    bad = 0
    text = path.read_text(encoding="utf-8")
    for m in CHAIN.finditer(text):
        label = m["label"]
        if label not in PDF:
            continue
        page = int(m["page"])
        for q in QUOTE.findall(m["q"]):
            for seg in segments(q):
                if seg in page_text(label, page):
                    continue
                near = [p for p in (page - 1, page + 1) if seg in page_text(label, p)]
                line = text.count("\n", 0, m.start()) + 1
                tag = f"gần tr.{near[0]}" if near else "KHÔNG THẤY"
                print(f"{path.name}:{line} {label} tr.{page} {tag}: {q[:70]}")
                bad += 1
                break
    return bad


def main():
    files = []
    for a in sys.argv[1:]:
        p = Path(a)
        files += sorted(p.rglob("*.rst")) if p.is_dir() else [p]
    total = sum(check(f) for f in files)
    print(f"check_quotes: {total} lệch / {len(files)} file")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
