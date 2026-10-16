#!/usr/bin/env python3
"""Phan 6 Compiler va op: Hinh 6.1 den 6.4.

Primary sources (see chu-thich.md, table Nguon): OPL (RKNN Compiler Support Operator List 2.3.2, Chinese; PDF page
numbers, printed = PDF - 6), UG232 (RKNN SDK User Guide 2.3.2), UG152 (RKNN API User Guide 1.5.2), API232
(RKNN-Toolkit2 API Reference 2.3.2), OPSUP, CHANGELOG.md of the toolkit, SRAM usage md, ultralytics source (ULT),
T2 papers (TVM, LEE24, BAMB, FLEX, LENS) for the general-context boxes, and the T3 board log
tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/raw (layer tables are read and counted here, not typed).

Usage: python3 gen.py [outdir] [figure-name ...]
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

W = 900
UNK_FILL = "#FFF3F3"
LB = "#EAF2FF"      # phep tinh / suy ra cua bo hinh
RB = "#EAF6EA"      # so do T3
GY = "#F2F2F2"      # o phu
C = lambda s: [(s, "c")]  # noqa: E731

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
RAW = os.path.join(ROOT, "tmp", "04_debug-logs", "2026-10-10_t3-board-silu-resize", "raw")


# ---------------------------------------------------------------------------------------------
# T3: read the layer tables (never typed by hand)
# ---------------------------------------------------------------------------------------------
_ROW = re.compile(r"^(\d+)\s+(\S+)\s+(\S+)\s+(NPU|CPU)\s")
_WL = re.compile(r"(\d+\.\d)%/(\d+\.\d)%/(\d+\.\d)%")


def layers(name):
    rows = []
    with open(os.path.join(RAW, name), encoding="utf-8") as fh:
        for ln in fh:
            m = _ROW.match(ln)
            if not m:
                continue
            wl = _WL.search(ln)
            rows.append(dict(op=m.group(2), dtype=m.group(3), target=m.group(4),
                             wl=tuple(float(v) for v in wl.groups()) if wl else None))
    return rows


def stat(rows):
    """{op: dict(n, cpu, split, core0, zero)}: split = at least two cores have load, core0 = only core 0,
    zero = 0%/0%/0% (no load attributed)."""
    out = {}
    for r in rows:
        d = out.setdefault(r["op"], dict(n=0, cpu=0, split=0, core0=0, zero=0))
        d["n"] += 1
        d["cpu"] += r["target"] == "CPU"
        if r["wl"] is None:
            continue
        nz = [v > 0 for v in r["wl"]]
        if sum(nz) >= 2:
            d["split"] += 1
        elif nz[0]:
            d["core0"] += 1
        else:
            d["zero"] += 1
    return out


SILU = stat(layers("silu_opt3_CORE_0_1_2_layers.txt"))
RELU = stat(layers("relu_opt3_CORE_0_1_2_layers.txt"))
SILU_N = len(layers("silu_opt3_CORE_0_1_2_layers.txt"))
RELU_N = len(layers("relu_opt3_CORE_0_1_2_layers.txt"))
SILU_NPU = sum(1 for r in layers("silu_opt3_CORE_0_1_2_layers.txt") if r["target"] == "NPU")
# Resize target and dtype at optimization_level 1, 2, 3 (AUTO tables)
RESIZE_LV = {lv: [(r["target"], r["dtype"]) for r in layers(f"silu_opt{lv}_layers.txt") if r["op"] == "Resize"]
             for lv in (1, 2, 3)}


def expect(d, op, **kw):
    for k, v in kw.items():
        assert d[op][k] == v, (op, k, d[op][k], v)


# the figures quote these numbers: fail loudly if the raw files ever change
expect(SILU, "ConvExSwish", n=57, core0=57, split=0)
expect(SILU, "Conv", n=7, split=6, core0=1)
expect(SILU, "Concat", n=17, split=15, core0=2)
expect(SILU, "Split", n=9, core0=9)
expect(SILU, "MaxPool", n=3, core0=3)
expect(SILU, "Add", n=8, split=8)
expect(SILU, "Mul", n=2, core0=2)
expect(SILU, "Sub", n=2, core0=2)
expect(SILU, "Resize", n=2, core0=2)
expect(SILU, "Reshape", n=7, core0=4, zero=3)
expect(SILU, "Sigmoid", n=1, core0=1)
expect(SILU, "exSoftmax13", n=1, core0=1)
expect(SILU, "Transpose", n=1, cpu=1)
expect(RELU, "ConvRelu", n=51, split=51)
expect(RELU, "ConvReluAdd", n=6, split=6)
expect(RELU, "Add", n=2, split=2)
assert SILU_N == 119 and SILU_NPU == 116 and RELU_N == 113
assert all(v == [("NPU", "INT8")] * 2 for v in RESIZE_LV.values())
for absent in ("exSwish", "Upsample", "Slice"):
    assert absent not in SILU and absent not in RELU
_ops = {lv: {op: d["n"] for op, d in stat(layers(f"silu_opt{lv}_layers.txt")).items()} for lv in (1, 2, 3)}
assert _ops[1] == _ops[2] == _ops[3], "op table differs between optimization_level 1, 2, 3"
assert set(op for op, d in SILU.items() if d["cpu"]) == {"Transpose", "InputOperator", "OutputOperator"}


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
def tier(f, label="T1 RK3588", x=808):
    f.tier(x, 8, label)


def _units(s):
    """Display width in Latin-character units: CJK glyphs are about twice as wide."""
    return sum(2.1 if ord(ch) > 0x2E80 else 1 for ch in s)


def wrap(s, n):
    """Greedy word wrap by display width (n = Latin characters per line)."""
    n = max(8, n)
    out, cur = [], ""
    for word in s.split(" "):
        cand = word if not cur else cur + " " + word
        if cur and _units(cand) > n:
            out.append(cur)
            cur = word
        else:
            cur = cand
    out.append(cur)
    return out


def _lines(lines, w, size):
    out = []
    for ln in lines:
        out.extend(wrap(ln, int((w - 24) / (size * 0.47))) if isinstance(ln, str) else [ln])
    return out


def card_h(w, title, lines, size=12.5, lh=17, tsize=14, h_min=0):
    t = wrap(title, int((w - 24) / (tsize * 0.50))) if title else []
    n = len(_lines(lines, w, size))
    return max(h_min, 14 + 20 * len(t) + lh * n + (4 if t else 0))


def card(f, x, y, w, title, lines, fill="white", stroke="#999999", dashed=False, size=12.5, lh=17, tsize=14,
         h_min=0, tcolor=INK, mono_title=False):
    """Bordered card: bold title (wrapped) then body lines (str wrapped, or rich parts). Returns bottom y."""
    h = card_h(w, title, lines, size, lh, tsize, h_min)
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{1.3 if dashed else 1}"{dash}/>')
    ty = y + 7
    if title:
        for t in wrap(title, int((w - 24) / (tsize * 0.50))):
            f.text(x + 12, ty + 10, t, size=tsize, weight=700, fill=tcolor, mono=mono_title)
            ty += 20
        ty += 4
    for i, ln in enumerate(_lines(lines, w, size)):
        if isinstance(ln, str):
            f.text(x + 12, ty + 9 + lh * i, ln, size=size)
        else:
            f.rich(x + 12, ty + 9 + lh * i, ln, size=size)
    return y + h


def unk_card(f, x, y, w, title, lines, size=12.5, lh=17, h_min=0):
    return card(f, x, y, w, title, lines, fill=UNK_FILL, stroke=RED, dashed=True, size=size, lh=lh, h_min=h_min,
                tcolor=RED)


def arrow(f, x1, y1, x2, y2, label=None, lx=None, ly=None, color=BLUE):
    f.line([(x1, y1), (x2, y2)], color, THIN)
    if label:
        f.text(lx if lx is not None else (x1 + x2) / 2 + 6, ly if ly is not None else (y1 + y2) / 2, label,
               size=12.5, weight=700, fill=color, halo="white")


def grid(f, x, y, widths, header, rows, size=12, lh=16, fills=None, hl_cols=(), pad=7):
    """Table with per-cell wrapping and per-cell fills. cell: str (wrapped), list of str/rich parts, or
    ('c', str) for a code-font cell. fills: {(row, col): colour}. Returns bottom y."""
    def cell_lines(cell, w):
        if isinstance(cell, tuple):
            return [[(ln, "c")] for ln in wrap(cell[1], int((w - 14) / (size * 0.50)))]
        if isinstance(cell, str):
            return wrap(cell, int((w - 14) / (size * 0.47)))
        return list(cell)

    head_lines = [cell_lines(h, w) for h, w in zip(header, widths)]
    head_h = 12 + lh * max(len(h) for h in head_lines)
    tw = sum(widths)
    f.a(f'<rect x="{x}" y="{y}" width="{tw}" height="{head_h}" fill="#E8E8E8"/>')
    cx = x
    for hl, w in zip(head_lines, widths):
        for i, ln in enumerate(hl):
            f.rich(cx + 7, y + 6 + lh / 2 + lh * i, ln if not isinstance(ln, str) else [(ln, "b")], size=size)
        cx += w
    cy = y + head_h
    for ri, row in enumerate(rows):
        cl = [cell_lines(c, w) for c, w in zip(row, widths)]
        rh = 2 * pad + lh * max(len(c) for c in cl)
        cx = x
        for ci, (c, w) in enumerate(zip(cl, widths)):
            fill = (fills or {}).get((ri, ci))
            if fill:
                f.a(f'<rect x="{cx}" y="{cy}" width="{w}" height="{rh}" fill="{fill}"/>')
            cx += w
        f.a(f'<path d="M{x} {cy} L{x + tw} {cy}" stroke="#BBBBBB" stroke-width="0.8"/>')
        cx = x
        for c, w in zip(cl, widths):
            top = cy + rh / 2 - (len(c) - 1) * lh / 2
            for i, ln in enumerate(c):
                f.rich(cx + 7, top + lh * i, ln, size=size)
            cx += w
        cy += rh
    f.a(f'<rect x="{x}" y="{y}" width="{tw}" height="{cy - y}" fill="none" stroke="#999999" stroke-width="1"/>')
    cx = x
    for w in widths[:-1]:
        cx += w
        f.a(f'<path d="M{cx} {y} L{cx} {cy}" stroke="#CCCCCC" stroke-width="0.8"/>')
    return cy


# =====================================================================
# Hinh 6.1: op chay tren NPU hay CPU
# =====================================================================
def fig_flow():
    f = Fig(W, 1500)
    tier(f)
    f.text(10, 22, "Một op chạy trên NPU hay rơi sang CPU: những gì nguồn cho biết", size=15, weight=700)
    QX, QW, RX, RW = 10, 290, 360, 530
    y = 46

    # ---- row 1: toolkit accepts the op?
    q = "1. Toolkit nhận op này khi convert?"
    ql = ["OPSUP: bảng 'ONNX OPs supported by RKNN Toolkit2', cột Remarks (Not Supported hoặc trống). "
          "Giới hạn chi tiết nằm ở OPL."]
    al = ["UG232 tr.167: convert thử trực tiếp, nếu không hỗ trợ sẽ có thông báo.",
          "NonMaxSuppression ghi Not Supported trong OPSUP; UG232 tr.168 gợi ý bỏ phần hậu xử lý khỏi graph và xử lý "
          "riêng ở phía CPU.",
          "Op 6 chiều: UG232 tr.168 'RKNN does not support 6-dimensional OP'; phần lớn chỉ hỗ trợ 4 chiều."]
    h1 = max(card_h(QW, q, ql), card_h(RW, "Không nhận: dừng ở bước convert", al))
    b1 = card(f, QX, y, QW, q, ql, h_min=h1)
    card(f, RX, y, RW, "Không nhận: dừng ở bước convert", al, h_min=h1)
    arrow(f, QX + QW, y + h1 / 2, RX, y + h1 / 2, "Không", QX + QW + 4, y + h1 / 2 - 10)
    y = b1 + 34

    # ---- row 2: OPL entry and limits?
    q = "2. Op có mục trong OPL 3.2 (RK3588), và kích thước, kiểu dữ liệu, thuộc tính nằm trong giới hạn của mục đó?"
    arrow(f, QX + QW / 2, b1, QX + QW / 2, y, "Có", QX + QW / 2 + 8, b1 + 17)
    npu_l = ["Suy ra của bộ hình: UG232 tr.139 chỉ liệt kê ba lý do khiến op chạy ngoài NPU (hộp bên dưới); "
             "nguồn không có câu nói thẳng 'đủ điều kiện thì chạy trên NPU'."]
    opl_l = ["Mô tả; input list (shape, kiểu lượng tử hóa); output list; ràng buộc kiểu dữ liệu (int8, float16); "
             "thuộc tính; mục 其他支持 có dòng 多核联合 (chạy đa core).",
             "Mục 3.2 là RK3588: PDF 56 đến 107, 79 mục (phép đếm của bộ hình)."]
    hq = card_h(QW, q, [])
    ha = card_h(RW, "Đủ điều kiện: chạy trên NPU", npu_l)
    ho = card_h(RW, "Cấu trúc một mục OPL (ví dụ 3.2.1 Add, PDF 56)", opl_l)
    hh = max(hq, ha + ho + 10)
    b2 = card(f, QX, y, QW, q, [], h_min=hh)
    ya = card(f, RX, y, RW, "Đủ điều kiện: chạy trên NPU", npu_l, fill=LB, stroke=BLUE, h_min=ha)
    card(f, RX, ya + 10, RW, "Cấu trúc một mục OPL (ví dụ 3.2.1 Add, PDF 56)", opl_l, h_min=hh - ha - 10)
    arrow(f, QX + QW, y + ha / 2, RX, y + ha / 2, "Có", QX + QW + 4, y + ha / 2 - 10)
    y = b2 + 34

    # ---- row 3: not on NPU
    arrow(f, QX + QW / 2, b2, QX + QW / 2, y, "Không", QX + QW / 2 + 8, b2 + 17)
    ql = ["Trong bảng lớp (eval_perf) cột Target ghi CPU (UG232 tr.75 và tr.139 cho ví dụ bảng)."]
    rl = ["1. The operator size exceeds the limit (see the operator size limit in the OpList document)",
          "2. The operator does not yet support operation on NPU (check whether OpList supports this operator)",
          "3. NPU hardware limitations cannot support it"]
    h3 = max(card_h(QW, "3. Op không chạy trên NPU", ql), card_h(RW, "Ba lý do theo UG232 tr.139", rl))
    b3 = card(f, QX, y, QW, "3. Op không chạy trên NPU", ql, h_min=h3)
    card(f, RX, y, RW, "Ba lý do theo UG232 tr.139", rl, h_min=h3)
    arrow(f, QX + QW, y + h3 / 2, RX, y + h3 / 2)
    y = b3 + 30

    # ---- row 4: unknown
    arrow(f, QX + QW / 2, b3, QX + QW / 2, y)
    y = unk_card(f, 10, y, 880, "Rơi sang thiết bị nào, theo quy tắc nào: OPL không nêu", [
        "OPL mục 3.2 chỉ mô tả từng op NPU; chương 4 'CPU OPs' (PDF 319 đến 334) liệt kê op có phiên bản CPU, mục 4.1 chỉ "
        "ghi ngoại lệ của RK2118 và RV1106, RV1103, RV1106B, RV1103B. Nguồn không nói RK3588 dùng chương 4 thế nào.",
        "Đã biết: API232 tr.17 fallback_prior_device, 'gpu' hoặc 'cpu', mặc định 'cpu'; 'gpu' chỉ hợp lệ với chip có GPU.",
        "Chưa biết (unknown): quy tắc rơi về CPU của OPL; thuật toán chọn đích của op_target = 'auto'."]) + 22

    # ---- row 5: user overrides
    f.text(10, y, "Người dùng can thiệp", size=15, weight=700)
    y += 14
    ot = ["Ép đích chạy từng op: {'op0_output_name':'cpu', ...} hoặc theo op_type {'Add':'cpu'}.",
          "Giá trị: 'cpu', 'npu', 'gpu', 'auto'; 'auto' là tự chọn đích.",
          "Tên tensor đầu ra của op lấy từ kết quả accuracy_analysis."]
    ol = ["Mặc định 3. Giá trị 2 hoặc 1 tắt một số tối ưu có thể ảnh hưởng độ chính xác; 0 tắt hết.",
          "UG232 tr.176: với optimization_level=2 'the Resize Op will use the CPU'.",
          "T3: không tái hiện với Resize nearest 2x INT8 (Target = NPU ở level 1, 2, 3); bilinear và FP16 chưa thử, "
          "nên không kết luận UG232 sai."]
    h5 = max(card_h(430, "op_target (API232 tr.9)", ot), card_h(440, "optimization_level (API232 tr.8)", ol))
    card(f, 10, y, 430, "op_target (API232 tr.9)", ot, h_min=h5)
    y = card(f, 450, y, 440, "optimization_level (API232 tr.8)", ol, h_min=h5)
    y += 22

    # ---- row 6: how to see it
    f.text(10, y, "Cách xem op thật sự chạy ở đâu", size=15, weight=700)
    y += 14
    sl = ["Bảng lớp của eval_perf: cột Target (NPU hoặc CPU) và WorkLoad(0/1/2) (UG232 tr.75).",
          "accuracy_analysis trả tên tensor đầu ra của từng op, dùng làm khóa cho op_target (API232 tr.9)."]
    tl = [f"YOLOv8n INT8, {SILU_N} lớp: Target = CPU chỉ ở Transpose (1 lớp) cùng InputOperator và OutputOperator; "
          f"{SILU_NPU} lớp còn lại là NPU.",
          "Một model (trọng số ngẫu nhiên, 640x640, toolkit 2.3.2, RK3588S); đếm từ bảng lớp CORE_0_1_2."]
    h6 = max(card_h(430, "Công cụ của vendor", sl), card_h(440, "T3 đo", tl))
    card(f, 10, y, 430, "Công cụ của vendor", sl, h_min=h6)
    y = card(f, 450, y, 440, "T3 đo", tl, fill=RB, stroke=GREEN, h_min=h6, tcolor=GREEN)
    y += 22

    # ---- row 7: two meanings of fallback
    f.text(10, y, "Hai nghĩa khác nhau của 'fallback'", size=15, weight=700)
    y += 14
    l1 = ["API232 tr.17 fallback_prior_device: 'set fallback prior device when OP is not supported by NPU'. "
          "Op rời NPU, sang CPU (mặc định) hoặc GPU."]
    l2 = ["UG152 tr.27: 'Other type of op will fallback to Core0 to continue running.' Op không có tách task đa core "
          "chạy ở core 0, vẫn là NPU (Hình 2.4)."]
    h7 = max(card_h(430, "Rời NPU", l1), card_h(440, "Về core 0 của NPU", l2))
    card(f, 10, y, 430, "Rời NPU", l1, h_min=h7)
    y = card(f, 450, y, 440, "Về core 0 của NPU", l2, h_min=h7)
    y += 16

    y = f.legend(10, y, 880, [
        ("blue", "thứ tự xét"),
        ("fill:" + LB, "suy ra của bộ hình (không phải câu của vendor)"),
        ("fill:" + RB, "số đo T3 có file log"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho"),
    ])
    source(f, y + 8, "Nguồn: OPL PDF 56, 319, 335; UG232 tr.75, 139, 167, 168, 176; UG152 tr.27; API232 tr.8, 9, 17; "
           "OPSUP; LOG t3-board-silu-resize/raw.")
    return f


# =====================================================================
# Hinh 6.2: ma tran op YOLOv8-type tren NPU RK3588
# =====================================================================
def _t3(d, op, extra=None):
    s = d[op]
    parts = [f"{s['n']} lớp NPU"]
    if s["split"] and s["core0"]:
        parts.append(f"{s['split']} chia 3 core, {s['core0']} chỉ core 0")
    elif s["split"]:
        parts.append(f"cả {s['split']} chia 3 core")
    elif s["core0"] and not s["zero"]:
        parts.append(f"cả {s['core0']} chỉ core 0")
    if s["zero"]:
        parts.append(f"{s['core0']} chỉ core 0, {s['zero']} lớp 0%/0%/0%")
    return "; ".join(parts) + (f" ({extra})" if extra else "")


def fig_matrix():
    WW = 1000
    f = Fig(WW, 2000)
    tier(f, x=WW - 92)
    f.text(10, 22, "Op của detector kiểu YOLOv8 trên NPU RK3588: OPL (T1) đặt cạnh bảng lớp đo được (T3)",
           size=15, weight=700)
    y = 44
    y = card(f, 10, y, WW - 20, "T3: lớp nào nằm trên NPU, lớp nào trên CPU",
             [f"YOLOv8n INT8, {SILU_N} lớp, core_mask CORE_0_1_2: Target = CPU chỉ ở Transpose (1 lớp) cùng InputOperator "
              f"và OutputOperator; {SILU_NPU} lớp còn lại Target = NPU. Cột T3 đếm từ bảng lớp: 'chia 3 core' là lớp có "
              "tải ở ít nhất hai core, 'chỉ core 0' là 100%/0%/0%. Cột T3 là một model, trọng số ngẫu nhiên."],
             fill=RB, stroke=GREEN, tcolor=GREEN) + 14
    widths = [128, 112, 92, 300, 112, 236]
    hdr = ["Op (tên OPL)", "OPL mục; PDF (trang in)", "Trên NPU", "Ràng buộc chính (OPL)", "多核联合 (đa core)",
           "T3: lớp trong bảng lớp"]
    rows = [
        [("c", "Conv"), "3.2.5; 58-59 (52-53)", "có",
         "kernel_h, kernel_w ∈ [1,31]; stride ∈ [1,7]; pads ∈ [0,15]; dilations ∈ [1,31]; int8, float16; "
         "weight per-layer và per-channel",
         "支持", _t3(SILU, "Conv")],
        [("c", "ConvolutionSwish (SiLU)"), "3.2.17; 63 (57)", "có",
         "'说明及规格限制同Convolution': ràng buộc như Convolution",
         "暂不支持",
         f"ConvExSwish: {_t3(SILU, 'ConvExSwish')}. Tên khác ConvolutionSwish: chưa chứng minh cùng một op"],
        [("c", "exSwish (SiLU rời)"), "3.2.69; 98 (92)", "có",
         "int8, float16; 'Swish 函数也称为 SiLU 函数'", "尚不支持", "không có lớp tên exSwish"],
        [("c", "Sigmoid"), "3.2.63; 95 (89)", "có", "int8, float16", "尚不支持", _t3(SILU, "Sigmoid")],
        [("c", "Resize"), "3.2.54; 86-87 (80-81)", "một phần",
         "chỉ nhân nguyên 2 đến 8 theo H, W; mode chỉ nearest, linear; coordinate_transformation_mode chỉ half_pixel, "
         "pytorch_half_pixel, align_corners",
         "不支持", _t3(SILU, "Resize", "INT8, Target = NPU ở optimization_level 1, 2, 3")],
        [("c", "Upsample"), "không có trong 3.2; CPU 4.67: 329", "không thấy trong mục NPU",
         "mục CPU: bilinear, nearest2d", "không có", "không có lớp tên Upsample"],
        [("c", "Concat"), "3.2.4; 58 (52)", "có", "axis ∈ {0,1,2,3}; int8, float16", "không có dòng",
         _t3(SILU, "Concat")],
        [("c", "Split"), "3.2.59; 91 (85)", "có", "axis ∈ {0,1,2,3}; int8, float16", "không có dòng",
         _t3(SILU, "Split")],
        [("c", "MaxPool"), "3.2.44; 79-80 (73-74)", "có",
         "kernel ∈ (0,7]; strides ∈ (0,8]; pad ∈ [0,7]; auto_pad chỉ NOTSET; ceil_mode không hỗ trợ",
         "không có dòng", _t3(SILU, "MaxPool")],
        [("c", "Add"), "3.2.1; 56 (50)", "có",
         "int8, float16; broadcast theo luật Expand (3.2.34, PDF 68: h, w ∈ [1,8192])", "支持",
         f"silu: {_t3(SILU, 'Add')}. relu: {_t3(RELU, 'Add')}"],
        [("c", "Mul"), "3.2.41; 77 (71)", "có", "int8, float16; broadcast theo luật Expand", "支持",
         _t3(SILU, "Mul") + " (OPL ghi 支持)"],
        [("c", "Sub"), "3.2.60; 91-92 (85-86)", "có", "int8, float16; broadcast [b,c,1,1] hoặc [scalar]",
         "不支持", _t3(SILU, "Sub")],
        [("c", "Reshape"), "3.2.53; 86 (80)", "có", "int8, float16", "尚不支持", _t3(SILU, "Reshape")],
        [("c", "Transpose"), "3.2.62; 93-95 (87-89)", "có điều kiện",
         "giới hạn riêng cho từng perm, với p=8192, q=2048; T1 int8, T2 int16 hoặc float16", "暂不支持",
         "1 lớp INT8, Target = CPU (cùng InputOperator, OutputOperator)"],
        [("c", "Softmax / exSoftmax13"), "3.2.56, 3.2.57; 88-89 (82-83)", "có điều kiện",
         "axis chỉ 1 hoặc 3; '受限于 tranpose 的规格限制'", "尚不支持 (cả hai)",
         "exSoftmax13: " + _t3(SILU, "exSoftmax13")],
        [("c", "Slice"), "3.2.55; 88 (82)", "có điều kiện",
         "steps khác 1 chỉ khi thỏa điều kiện chứa subc (OPL không định nghĩa subc)", "không có dòng",
         "không có lớp tên Slice"],
    ]
    fills = {}
    for ri, r in enumerate(rows):
        fills[(ri, 5)] = RB
        if r[2] != "có":
            fills[(ri, 2)] = UNK_FILL if "không thấy" in r[2] else GY
        if r[4] == "không có dòng" or r[4] == "không có":
            fills[(ri, 4)] = GY
    y = grid(f, 10, y, widths, hdr, rows, size=12, lh=15.5, fills=fills, pad=6) + 14

    # ---- notes under the matrix
    cw = (WW - 20 - 20) // 3
    n1 = ["Mục 3.2 (PDF 56 đến 107) có 79 mục, 59 mục có dòng 多核联合: 11 支持, 18 暂不支持, 23 尚不支持, 7 不支持; "
          "20 mục không có dòng (phép đếm của bộ hình, khớp với bản đếm trong 00_index mục 7.1).",
          "OPL không định nghĩa 暂不支持, 尚不支持, 不支持: chưa phân biệt được nghĩa."]
    n2 = ["T3 phù hợp với cột OPL ở ConvolutionSwish (暂不支持, ConvExSwish chỉ core 0), ConvRelu và ConvReluAdd "
          "(cùng họ ConvolutionRelu 支持, chia 3 core; Hình 6.3), Resize, Split, Sub.",
          "Không khớp hoặc chưa rõ: Mul (OPL 支持, T3 core 0)."]
    n3 = ["Phép tính của bộ hình: Transpose duy nhất trên CPU có input (4,1,1,8400) và output (1,4,1,8400); nếu perm "
          "là [1,0,2,3], mục OPL ghi 'h1*w1<p' với p=8192, còn h1*w1 = 8400. Phù hợp với lý do 'size exceeds the limit', "
          "nhưng không có nguồn xác nhận (perm và lý do đều là suy ra)."]
    hn = max(card_h(cw, "Phép đếm của bộ hình", n1, size=12), card_h(cw, "T3 so với cột 多核联合", n2, size=12),
             card_h(cw, "Vì sao Transpose rơi về CPU?", n3, size=12))
    card(f, 10, y, cw, "Phép đếm của bộ hình", n1, fill=LB, stroke=BLUE, size=12, h_min=hn)
    card(f, 10 + cw + 10, y, cw, "T3 so với cột 多核联合", n2, fill=RB, stroke=GREEN, size=12, h_min=hn,
         tcolor=GREEN)
    y = card(f, 10 + 2 * (cw + 10), y, cw, "Vì sao Transpose rơi về CPU?", n3, fill=LB, stroke=BLUE, size=12,
             h_min=hn) + 14

    # ---- contradiction 3 and Resize
    f.text(10, y + 4, "Mâu thuẫn số 3: op nào chạy đa core?", size=15, weight=700)
    y += 20
    a = ["UG232 tr.75: 'The existing operators that support multi-core task segmentation include: Conv, "
         "DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, and LeakyRelu.' "
         "UG152 tr.27 có danh sách tương tự."]
    b = ["Relu, Clip/ReLU6, PRelu, LeakyRelu đều ghi 暂不支持 (3.2.49 đến 3.2.52, PDF 83 đến 86); Concat không có dòng "
         "多核联合; ThresholdedRelu không có trong OPL; Mul ghi 支持 nhưng không có trong danh sách UG232."]
    t = [f"Bảng lớp không có lớp Relu đứng riêng; ConvRelu ({RELU['ConvRelu']['n']}) và ConvReluAdd "
         f"({RELU['ConvReluAdd']['n']}) đều chia 3 core; Concat {SILU['Concat']['split']} trong {SILU['Concat']['n']} "
         "chia 3 core. Một model, nên không phân xử được."]
    hc = max(card_h(290, "Danh sách của UG232", a, size=12), card_h(290, "OPL mục 3.2", b, size=12),
             card_h(290, "T3", t, size=12))
    card(f, 10, y, 290, "Danh sách của UG232", a, size=12, h_min=hc)
    card(f, 310, y, 290, "OPL mục 3.2", b, size=12, h_min=hc)
    y = card(f, 610, y, 380, "T3", t, fill=RB, stroke=GREEN, size=12, h_min=hc, tcolor=GREEN)
    y += 14
    r1 = ["OPL PDF 86-87 liệt kê Resize (int8, float16) cho RK3588; UG232 tr.176 nói NPU 'does not currently support "
          "hardware-level Resize' và toolkit đổi Resize thành ConvTranspose.",
          "T3: hai lớp Resize INT8 đều Target = NPU ở optimization_level 1, 2, 3. Bilinear và FP16 chưa thử, nên không "
          "kết luận UG232 sai."]
    y = card(f, 10, y, WW - 20, "Resize: hai tài liệu T1 chưa thống nhất", r1, size=12) + 12
    u = ["ConvExSwish (tên trong bảng lớp) và ConvolutionSwish (tên trong OPL) có phải một op không; 'subc' trong điều "
         "kiện Slice; nghĩa chính xác của 多核联合 và ba cách viết 'không hỗ trợ'; danh sách 'YOLOv8 cần op nào' không có nguồn "
         "T1 hay T2 (bảng chỉ là op thường gặp, mỗi dòng có giá trị nhờ mục OPL của nó)."]
    y = unk_card(f, 10, y, WW - 20, "Chưa biết", u, size=12) + 14
    y = f.legend(10, y, WW - 20, [
        ("fill:" + RB, "T3 đo, có file log (một model, không phải kết luận chung)"),
        ("fill:" + GY, "OPL không có mục hoặc không có dòng; hoặc có điều kiện"),
        ("fill:" + UNK_FILL, "không thấy trong mục NPU"),
        ("fill:" + LB, "phép tính, suy ra của bộ hình"),
    ])
    source(f, y + 8, "Nguồn: OPL PDF 56 đến 107, 329 (trang in = PDF trừ 6); UG232 tr.75, 139, 176; UG152 tr.27; "
           "LOG t3-board-silu-resize/raw (silu_opt1, 2, 3 và CORE_0_1_2).")
    return f


# =====================================================================
# Hinh 6.3: fusion
# =====================================================================
def _chain(f, x, y, labels, w=96, h=32, gap=26, fills=None, size=13):
    """Row of op boxes joined by arrows. Returns right edge."""
    for i, lab in enumerate(labels):
        fill = (fills or {}).get(i, "white")
        f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="#333333" '
            f'stroke-width="1.2"/>')
        f.text(x + w / 2, y + h / 2, lab, size=size, weight=700, anchor="middle", mono=True)
        if i < len(labels) - 1:
            f.line([(x + w, y + h / 2), (x + w + gap, y + h / 2)], BLUE, THIN)
        x += w + gap
    return x - gap


def fig_fusion():
    f = Fig(W, 2000)
    tier(f)
    f.text(10, 22, "Fusion: Conv và activation thành một lớp, và người dùng can thiệp được đến đâu", size=15, weight=700)
    y = 44

    # ---- A. SiLU
    f.text(10, y + 8, "A. SiLU: Sigmoid và Mul sau Conv thành ConvExSwish", size=14.5, weight=700)
    y += 24
    f.a(f'<rect x="10" y="{y}" width="880" height="150" rx="6" fill="white" stroke="#999999"/>')
    f.text(24, y + 16, "Trước", size=13, weight=700)
    f.text(24, y + 34, "BN gộp vào Conv khi export (Ultralytics)", size=12, fill=DARK)
    _chain(f, 24, y + 56, ["Conv", "Sigmoid", "Mul"], w=92, gap=22)
    f.text(24, y + 104, "SiLU: y = x * sigmoid(x) (OPL 3.2.69)", size=12, fill=DARK)
    f.text(24, y + 124, "Trong ONNX: Conv, Sigmoid, Mul (README log T3)", size=12, fill=DARK)
    arrow(f, 354, y + 72, 424, y + 72)
    f.text(389, y + 54, "ghép", size=12.5, weight=700, fill=BLUE, anchor="middle", halo="white")
    f.text(389, y + 92, "luật: unknown", size=11.5, fill=RED, anchor="middle", halo="white")
    f.text(440, y + 16, "Sau (bảng lớp RKNN, T3)", size=13, weight=700)
    _chain(f, 440, y + 56, ["ConvExSwish"], w=150, h=32, fills={0: RB})
    f.text(602, y + 72, f"x {SILU['ConvExSwish']['n']} lớp, Target = NPU", size=12.5)
    f.text(440, y + 104, f"còn {SILU['Sigmoid']['n']} lớp Sigmoid riêng (Sigmoid:/model.22/Sigmoid) và "
           f"{SILU['Mul']['n']} Mul riêng", size=12, fill=DARK)
    f.text(440, y + 124, "CORE_0_1_2: cả 57 lớp ConvExSwish chỉ core 0", size=12, fill=DARK)
    y += 164
    ol = ["OPL có hai mục SiLU riêng: ConvolutionSwish 3.2.17 (Conv và Swish hợp nhất, PDF 63, 多核联合 暂不支持) và "
          "exSwish 3.2.69 (op rời, PDF 98, 尚不支持). ConvExSwish có phải ConvolutionSwish không: chưa chứng minh."]
    y = card(f, 10, y, 880, "Đối chiếu với OPL", ol, size=12) + 18

    # ---- B. ReLU
    f.text(10, y + 8, "B. ReLU: Conv và Relu thành ConvRelu, có Add thành ConvReluAdd", size=14.5, weight=700)
    y += 24
    f.a(f'<rect x="10" y="{y}" width="880" height="156" rx="6" fill="white" stroke="#999999"/>')
    f.text(24, y + 16, "Trước (thay SiLU bằng ReLU, cùng model)", size=13, weight=700)
    _chain(f, 24, y + 34, ["Conv", "Relu"], w=92, gap=22, h=30)
    f.text(24, y + 80, "Add riêng: 8 lớp ở bản SiLU, 2 lớp ở bản ReLU", size=12, fill=DARK)
    f.text(24, y + 100, "8 - 2 = 6, bằng số lớp ConvReluAdd (phép tính của bộ hình)", size=12, fill=DARK)
    arrow(f, 262, y + 50, 322, y + 50)
    f.text(292, y + 34, "ghép", size=12.5, weight=700, fill=BLUE, anchor="middle", halo="white")
    f.text(336, y + 16, "Sau (bảng lớp RKNN, T3)", size=13, weight=700)
    _chain(f, 336, y + 34, ["ConvRelu"], w=122, h=30, fills={0: RB})
    f.text(470, y + 49, f"x {RELU['ConvRelu']['n']} lớp, chia 3 core", size=12.5)
    _chain(f, 336, y + 76, ["ConvReluAdd"], w=122, h=30, fills={0: RB})
    f.text(470, y + 91, f"x {RELU['ConvReluAdd']['n']} lớp, chia 3 core", size=12.5)
    f.text(336, y + 124, f"Add riêng: {SILU['Add']['n']} (SiLU) xuống {RELU['Add']['n']} (ReLU), chia 3 core", size=12)
    f.text(336, y + 142, f"Tổng 57 = {RELU['ConvRelu']['n']} + {RELU['ConvReluAdd']['n']} lớp Conv kèm activation",
           size=12, fill=DARK)
    y += 170
    ol = ["OPL: ConvolutionRelu 3.2.7 (PDF 60) và ConvolutionAddRelu 3.2.19 (PDF 63, Output = Relu(Add(Conv(Input0), "
          "Input1))) đều ghi 多核联合 支持. UG232 tr.142 liệt kê Conv+Activation+Add (thứ tự khác OPL 3.2.19). "
          "Thứ tự bên trong lớp ConvReluAdd: unknown."]
    y = card(f, 10, y, 880, "Đối chiếu với OPL và UG232", ol, size=12) + 18

    # ---- C. OPL fused entries
    f.text(10, y + 8, "C. Các mục Conv hợp nhất trong OPL 3.2 và dòng 多核联合", size=14.5, weight=700)
    y += 24
    ok = ["ConvolutionRelu 3.2.7", "ConvolutionClip 3.2.8", "ConvolutionPRelu/LeakyRelu 3.2.9", "ConvolutionAdd 3.2.10",
          "ConvolutionAddRelu 3.2.19"]
    no = ["ConvolutionSigmoid 3.2.11", "ConvolutionTanh 3.2.12", "ConvolutionSoftplus 3.2.13",
          "ConvolutionHardSigmoid 3.2.14", "ConvolutionHardSwish 3.2.15", "ConvolutionElu 3.2.16",
          "ConvolutionSwish 3.2.17", "ConvolutionMish 3.2.18"]
    h = max(card_h(430, "支持 (đa core)", ok, size=12), card_h(440, "暂不支持 (chưa đa core)", no, size=12))
    card(f, 10, y, 430, "支持 (đa core)", ok, size=12, h_min=h, lh=16)
    y = card(f, 450, y, 440, "暂不支持 (chưa đa core)", no, size=12, h_min=h, lh=16) + 8
    y = card(f, 10, y, 880, "Đọc từ bảng của bộ hình", [
        "Dòng 多核联合 của 13 mục: họ Relu, Clip, PRelu, Add ghi 支持; họ Sigmoid, Tanh, Softplus, HardSigmoid, "
        "HardSwish, Elu, Swish, Mish ghi 暂不支持. T3 cho cùng chiều: ConvRelu chia 3 core, ConvExSwish chỉ core 0 "
        "(Hình 6.2, Hình 10.3). Đây là đối chiếu, OPL không giải thích vì sao."], fill=LB, stroke=BLUE, size=12) + 18

    # ---- D. user-level rules and original figure
    f.text(10, y + 8, "D. Luật fusion mức người dùng (UG232 chương 8)", size=14.5, weight=700)
    y += 24
    rules = [
        "8.4.2 (tr.141 đến 142): NPU hỗ trợ fusion một số op; đổi thứ tự Transpose và Clip để Conv và Clip hợp nhất "
        "(Figure 8-7). Bảng luật không nêu chip.",
        "Luật đã hỗ trợ: Conv+Relu, Conv+PRelu(LeakyRelu), Conv+Clip, Conv+Sigmoid(Tanh/Elu/Silu...), Conv+Add, "
        "Conv+Activation+Add.",
        "Kế hoạch tương lai: Activation+Add(Mul), Add(Mul)+Activation, Conv+Mul, Conv+Activation+Mul, "
        "Conv+Activation+Pooling, Conv+Activation+Add(Mul)+Pooling.",
        "8.4.1, 8.4.3, 8.4.4 (tr.141 đến 144): thay Transpose, Reshape bằng Conv; gộp Slice vào Conv; gộp op giống nhau.",
        "8.5.3 (tr.147 đến 148): Split+Sigmoid+Mul thành GLU; ReduceMean+Sub+Pow+... thành LayerNorm.",
        "Mặc định optimization_level = 3 bật mọi tối ưu (API232 tr.8). Toolkit tự tối ưu 'to a certain extent', "
        "'not omnipotent and perfect' (UG232 tr.141).",
    ]
    ytop = y
    yo = f.original(10, y, 400, "../../npu_study/images/06_compiler_operators/ug232_p142_fig8-7_fusion_rules.png", [
        "UG232 tr.142, Figure 8-7 và bảng luật fusion."])
    yr = card(f, 440, ytop, 450, "Người dùng làm được gì", rules, size=12, lh=16, h_min=yo - ytop)
    y = max(yo, yr) + 18

    # ---- E. unknown
    y = unk_card(f, 10, y, 880, "Compiler nội bộ của Rockchip: unknown", [
        "Thuật toán fusion, thứ tự pass, luật bắt cặp tổng quát (ngoài các cặp đo được ở trên) và optimization_level 1, 2 "
        "tắt rule nào: nguồn không cho. T3: bảng op giống hệt ở level 1, 2, 3 cho YOLOv8n SiLU.",
        "Nguồn T1 chỉ có tên pass trong log lỗi (UG232 tr.168: RKNNInitCastConst, RKNNMultiSurfacePass, "
        "RKNNTilingPass, RKNNProfileAnalysisPass, OpEmit) và tên hàm trong traceback (graph_optimizer.GraphOptimizer."
        "_fuse_ops, UG232 tr.166).",
        "CHANGELOG.md (toolkit): v2.3.2 'Enhanced graph optimization capabilities' (dòng 11); v2.1.0 'Support more "
        "operators and operator fusion' (dòng 51); chỉ ghi chức năng, không ghi cách làm."]) + 18

    # ---- F. T2 context
    f.text(10, y + 8, "Bối cảnh chung về tiling và scheduling (bài báo, không phải toolchain của Rockchip)", size=14.5,
           weight=700)
    f.tier(W - 83, y - 4, "T2 chung")
    y += 26
    g = [
        "TVM tr.3: 'Operator fusion combines multiple operators into a single kernel without saving the intermediate "
        "results in memory.'",
        "LEE24 tr.1: 'Operator fusion is a scheduling method for combining multiple operations to minimize off-chip "
        "memory access.' LEE24 tr.2: feature map phải chia thành tile vì 'the FM buffer (on-chip memory) is much "
        "smaller than dram'.",
        "BAMB tr.4 (NXP eIQ Neutron): 'the mid-end lowers and optimizes the graph through tiling, scheduling, and "
        "memory allocation'.",
        "FLEX tr.1: solver toán học tìm tiling và thứ tự vòng lặp cho một lớp DNN, rồi áp lên nhiều NPU.",
        "LENS tr.1: 'the compilers of commercial NPUs apply graph optimizations in unpredictable ways'.",
        "Không dùng các câu trên để suy ra cách Rockchip làm; buffer 384KB mỗi core là phần cứng (Hình 2.2), thuật toán "
        "tiling của Rockchip: unknown.",
    ]
    ycard = card(f, 10, y, 880, "T2 chung", g, fill="#F4FAF4", stroke=GREEN, size=12, lh=16, tcolor=GREEN)
    y = ycard + 18
    y = f.legend(10, y, 880, [
        ("blue", "ghép op"),
        ("fill:" + LB, "suy ra của bộ hình"),
        ("fill:" + RB, "số đo T3 có file log"),
        ("fill:#F4FAF4", "T2 chung: ngữ cảnh, không riêng RK3588"),
        ("fill:" + UNK_FILL, "unknown"),
    ])
    source(f, y + 8, "Nguồn: OPL PDF 60 đến 63, 98; UG232 tr.141 đến 148, 166 đến 168; API232 tr.8; CHANGELOG.md; ULT; "
           "TVM, LEE24, BAMB, FLEX, LENS; LOG t3.")
    return f


# =====================================================================
# Hinh 6.4: layout NC1HWC2 va cac khai niem alignment
# =====================================================================
def fig_layout():
    f = Fig(W, 2000)
    tier(f)
    f.text(10, 22, "NC1HWC2: cách xếp dữ liệu trong bộ nhớ NPU, và bốn khái niệm alignment khác nhau", size=15,
           weight=700)
    y = 44
    top = y

    # ---- left: address order
    f.text(10, y + 8, "Thứ tự địa chỉ (UG152 tr.56)", size=14.5, weight=700)
    y += 22
    names = [("C2", "đổi nhanh nhất"), ("W", ""), ("H", ""), ("C1", ""), ("N", "đổi chậm nhất")]
    bw, gap = 62, 20
    x = 10
    f.text(10, y + 6, "địa chỉ thấp", size=12, fill=DARK)
    f.text(10 + 5 * bw + 4 * gap, y + 6, "địa chỉ cao", size=12, fill=DARK, anchor="end")
    y += 20
    for i, (n, sub) in enumerate(names):
        f.a(f'<rect x="{x}" y="{y}" width="{bw}" height="34" rx="4" fill="white" stroke="#333333" stroke-width="1.2"/>')
        f.text(x + bw / 2, y + 17, n, size=15, weight=700, anchor="middle", mono=True)
        if i < 4:
            f.line([(x + bw, y + 17), (x + bw + gap, y + 17)], BLUE, THIN)
        if sub:
            f.text(x + bw / 2, y + 50, sub, size=11.5, fill=DARK, anchor="middle")
        x += bw + gap
    y += 66
    y = card(f, 10, y, 430, "C2 và C1", [
        "C2 là khối kênh nằm liền nhau, do nền tảng quyết định; C1 = làm tròn lên của C/C2 (UG232 tr.61).",
        "Các phần tử của một khối C2 ở cuối bị thiếu kênh thì thêm dữ liệu căn thừa, không hợp lệ (UG232 tr.61)."],
              size=12, lh=16) + 10

    f.text(10, y + 8, "C2 theo chip và kiểu dữ liệu", size=14.5, weight=700)
    y += 22
    y = grid(f, 10, y, [118, 70, 80, 162], ["Chip", "int8", "float16", "int16"], [
        ["RK3588", "16", "8", "8 (chỉ UG152)"],
        ["RK3566/RK3568", "8", "4", "4 (chỉ UG152)"],
    ], size=12, lh=16, pad=5, fills={(0, 1): LB, (0, 2): LB}) + 4
    for i, ln in enumerate(wrap("UG232 Table 5-1 không có cột int16; API232 tr.7 không nêu int16 cho RK3588: unknown ở "
                                "mức SDK.", 78)):
        f.text(10, y + 8 + 15 * i, ln, size=11.5, fill=DARK)
    y += 44

    # ---- example
    f.text(10, y + 8, "Ví dụ: tensor int8 (1,13,4,4)", size=14.5, weight=700)
    y += 22
    ex = ["RK3568 (UG232 tr.61): C2 = 8, C1 = 2, NC1HWC2 = (1,2,4,4,8); ở khối C2 thứ hai chỉ 5 phần tử đầu hợp lệ, "
          "còn 3 là dữ liệu căn thừa.",
          "RK3588, phép tính của bộ hình từ C1 = ceil(C/C2) và Table 5-1: int8, C2 = 16, C1 = 1, (1,1,4,4,16), 3 kênh "
          "căn thừa; float16, C2 = 8, C1 = 2, (1,2,4,4,8), 3 kênh căn thừa.",
          "Log mẫu SRAM (RK3588, ConvRelu INT8): (1,32,112,112) thành (1,2,112,112,16), khớp ceil(32/16) = 2; "
          "(1,512,7,7) thành (1,33,7,7,16) và (1,1024,7,7) thành (1,67,7,7,16), không khớp ceil(512/16) = 32 và "
          "ceil(1024/16) = 64: unknown vì sao."]
    y = card(f, 10, y, 430, None, ex, size=12, lh=16) + 12
    # ---- right: original
    yo = f.original(460, top, 410, "../../npu_study/images/06_compiler_operators/ug232_p61_fig5-1_table5-1.png", [
        "UG232 tr.61, Figure 5-1 và Table 5-1 (nhúng để thấy thứ tự 0 đến 31 và C2 theo chip)."])

    y = max(y, yo) + 14

    y = card(f, 10, y, 880, "Khi nào input dùng NC1HWC2", [
        "Query native input attr (UG232 tr.69, tr.177): input 4 chiều có số kênh 1, 3 hoặc 4 dùng NHWC; số kênh khác "
        "dùng NC1HWC2. Log mẫu SRAM: input (1,3,224,224) có NativeShape (1,1,224,224,3)."], size=12, lh=16) + 18

    # ---- four alignment notions
    f.text(10, y + 8, "Bốn khái niệm 'alignment' khác nhau, không gộp", size=14.5, weight=700)
    y += 24
    widths = [30, 150, 250, 330, 120]
    hdr = ["#", "Khái niệm", "Giá trị cho RK3588", "Điều kiện và nguồn", "Bắt buộc?"]
    rows = [
        ["1", "C2 của layout NC1HWC2",
         "int8: 16; float16: 8",
         "Kích thước khối kênh liền nhau trong NC1HWC2; UG232 tr.61 Table 5-1 (cột RK3576/RK3588/RV1126B).",
         "là định nghĩa của layout"],
        ["2", "Alignment width của input (zero-copy API)",
         "layer đầu, input 4 chiều, số kênh 1, 3, 4: int8 16, float16 8 (đọc từ hình); số kênh khác: 1",
         "OPL PDF 335: chỉ cho zero-copy API, w_stride query được, không đổi được; bảng RK3588 ở PDF 336 là ảnh. "
         "UG232 tr.65 Table 5-2: Width 16-byte aligned (RK3588).",
         "chỉ với zero-copy API"],
        ["3", "Alignment output của lớp cuối",
         "int8, NHWC: kênh 16; NC1HWC2: lớp cuối họ Conv 32, không phải Conv 16, H*W căn 4; float16: NHWC 8, "
         "NC1HWC2 16 hoặc 8",
         "OPL PDF 339 mục 5.2.2; ghi chú 1: NHWC có yêu cầu căn khi bước chuyển output do NPU làm, CPU làm thì không.",
         "có điều kiện"],
        ["4", "Căn kênh để chạy hiệu quả, thân thiện DDR",
         "int8: Conv input 32, Conv output 32, Depthwise 64, op khác 16; float16: 32, 16, 32, 8",
         "UG232 tr.144 đến 145 Table 8-2 (cột RK3588/RK3576/RV1126B): 'These rules are not mandatory.'",
         "không bắt buộc"],
    ]
    y = grid(f, 10, y, widths, hdr, rows, size=12, lh=16, pad=6, fills={(i, 4): GY for i in range(4)}) + 10
    y = card(f, 10, y, 880, "Số 16 xuất hiện ở cả bốn chỗ cho int8, nhưng nguồn không nối chúng", [
        "C2 int8 = 16 (1), width input int8 = 16 (2), kênh NHWC output int8 = 16 (3), kênh 'Other OP' int8 = 16 (4). "
        "Suy ra của bộ hình: không có câu nào nói chúng là một đại lượng; mỗi số thuộc một khái niệm với điều kiện riêng."],
              fill=LB, stroke=BLUE, size=12, lh=16) + 12
    y = unk_card(f, 10, y, 880, "Chưa biết", [
        "Cách compiler chọn C2 và C1 cho từng tensor; vì sao NativeShape trong log mẫu lệch quy tắc làm tròn lên "
        "(UG232 tr.61 không giải thích); các lớp OPL 5.2 coi là 'họ Conv' (卷积类算子) gồm op nào."], size=12,
                 lh=16) + 18

    # ---- T2 context
    y = card(f, 10, y, 880, "T2 chung: layout trong compiler nói chung (không phải toolchain của Rockchip)", [
        "TVM tr.4: 'We then perform the proper layout transformation between a producer and a consumer if their "
        "preferred data layouts do not match.'",
        "BAMB tr.5 (NXP eIQ Neutron): 'Formats are crucial for optimizing compute utilization.'",
        "Hai câu mô tả compiler khác; chúng không nói NC1HWC2 của Rockchip được chọn theo cách đó."],
             fill="#F4FAF4", stroke=GREEN, tcolor=GREEN, size=12, lh=16) + 18
    y = f.legend(10, y, 880, [
        ("blue", "thứ tự địa chỉ từ thấp đến cao"),
        ("fill:" + LB, "phép tính, suy ra của bộ hình"),
        ("fill:" + GY, "không bắt buộc, hoặc có điều kiện"),
        ("fill:#F4FAF4", "T2 chung"),
        ("fill:" + UNK_FILL, "unknown"),
    ])
    source(f, y + 8, "Nguồn: UG152 tr.56; UG232 tr.61, 65, 69, 144, 145, 177; OPL PDF 335 đến 339; SRAM dòng 148 đến 173; "
           "TVM tr.4; BAMB tr.5.")
    return f


FIGS = [
    ("h6-1-npu-hay-cpu", fig_flow),
    ("h6-2-ma-tran-op-yolo", fig_matrix),
    ("h6-3-fusion", fig_fusion),
    ("h6-4-layout", fig_layout),
]

def _int_h(build):
    def inner():
        fig = build()
        fig.h = int(-(-fig.h // 1))   # chrome --window-size needs an integer height
        return fig
    return inner


if __name__ == "__main__":
    FIGS = [(n, _int_h(b)) for n, b in FIGS]
    run(FIGS, os.path.dirname(os.path.abspath(__file__)))
