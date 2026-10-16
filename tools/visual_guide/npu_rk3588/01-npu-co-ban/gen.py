#!/usr/bin/env python3
"""Phan 1 NPU co ban: Hinh 1.1 den 1.5 (tier T2 chung; moi hinh co khung "Lien he RK3588" T1).

Primary sources (see chu-thich.md, table Nguon): EYE, TPU, JUNG, FLEX, LP (docs/_assets/pdf/papers/01_hardware/), TRM1 tr.1984, 2001, UG152 tr.26-27.
Hinh 1.3 and 1.4 are matplotlib charts (run with .venv/bin/python); 1.1, 1.2, 1.5 are SVG diagrams (figlib).
Numbers typed by hand in 1.3: EYE Table IV (page 8 of the PDF, verified with pdftotext), no log file exists for them.
Hinh 1.4 draws a conceptual roofline with illustrative axes (no numbers on the axes); the TPU numbers in its table are
Table 1 (tr.2) and the text of tr.6.

Usage: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import matplotlib.pyplot as plt  # noqa: E402
from chartlib import BLUE as CBLUE, DARK as CDARK, GRAY as CGRAY, GREEN as CGREEN, INK as CINK  # noqa: E402
from chartlib import RED as CRED, save, source_line, tier_label  # noqa: E402
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

W = 900
UNK_FILL = "#FFF3F3"
CALC = "#EAF2FF"      # phep tinh cua bo hinh
STAT = "#FFF1CC"      # thu PE giu yen
P0, P1 = "#DCE8FA", "#DDF0DE"


def tier(f):
    f.tier(808, 8, "T2 chung")


def txt(f, x, y, ls, size=12, dy=16, fill=INK, anchor="start"):
    """Plain lines (str or parts) stacked from y; returns the next free y."""
    for i, ln in enumerate(ls):
        f.rich(x, y + dy * i, ln, size=size, anchor=anchor, fill=fill)
    return y + dy * len(ls)


def card(f, x, y, w, h, title, size_t=14, dashed=False, fill="white"):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="#333333" '
        f'stroke-width="1.2"{dash}/>')
    f.text(x + w / 2, y + 17, title, size=size_t, weight=700, anchor="middle")


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=3):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw}"{dash}/>')


def label(f, x, y, w, h, ls, size=12, fill="white", stroke="#333333", dashed=False, weight=400, color=INK):
    """Box with centred text lines."""
    rect(f, x, y, w, h, fill, stroke, dashed=dashed)
    top = y + h / 2 - (len(ls) - 1) * (size + 3) / 2
    for i, ln in enumerate(ls):
        f.text(x + w / 2, top + i * (size + 3), ln, size=size, weight=weight, anchor="middle", fill=color)


def original_crop(f, x, y, w, path, caption, keep=0.93):
    """Like Fig.original() but keeps only the left `keep` fraction of the PNG (the crop contains a sliver of the
    neighbouring text column). The SVG clipPath hides the rest; the file itself is unchanged."""
    import base64
    import struct
    full = os.path.normpath(os.path.join(HERE, "..", path))
    with open(full, "rb") as fh:
        data = fh.read()
    iw, ih = struct.unpack(">II", data[16:24])
    full_w = w / keep
    h = round(full_w * ih / iw)
    lines = [caption] if isinstance(caption, str) else list(caption)
    ph = 30 + h + 10 + 17 * len(lines) + 4
    cid = f"crop{int(x)}_{int(y)}"
    f.a(f'<rect x="{x}" y="{y}" width="{w + 20}" height="{ph}" rx="6" fill="white" stroke="#999999" stroke-width="1"/>')
    f.text(x + 10, y + 16, "Hình gốc", size=14, weight=700)
    f.a(f'<clipPath id="{cid}"><rect x="{x + 10}" y="{y + 30}" width="{w}" height="{h}"/></clipPath>')
    f.a(f'<image x="{x + 10}" y="{y + 30}" width="{full_w:g}" height="{h}" clip-path="url(#{cid})" '
        f'href="data:image/png;base64,{base64.b64encode(data).decode("ascii")}"/>')
    f.a(f'<rect x="{x + 10}" y="{y + 30}" width="{w}" height="{h}" fill="none" stroke="#CCCCCC"/>')
    for i, ln in enumerate(lines):
        f.text(x + 10, y + 30 + h + 14 + 17 * i, ln, size=12, fill=DARK, italic=True)
    return y + ph


def link_box(f, x, y, w, ls, size=12.5, unknown=None):
    """'Lien he RK3588' note: white box, blue border, T1 badge. Returns bottom y."""
    h = 40 + 19 * len(ls)
    rect(f, x, y, w, h, "white", BLUE, 1.8, rx=6)
    f.tier(x + 10, y + 8, "T1 RK3588")
    f.text(x + 112, y + 19, "Liên hệ RK3588: điều nguồn T1 nói và điều chưa biết", size=13.5, weight=700)
    txt(f, x + 14, y + 44, ls, size=size, dy=19)
    return y + h


# =====================================================================
# Hinh 1.1: MAC, PE, PE array
# =====================================================================
def fig_mac_pe():
    f = Fig(W, 1100)
    tier(f)
    f.text(10, 50, "Ba đơn vị khác nhau trong nguồn T2", size=15, weight=700)
    ya, ha = 66, 318

    # ---- column 1: MAC ----
    card(f, 10, ya, 290, ha, "MAC")
    f.text(155, ya + 36, "multiply-and-accumulate (nhân rồi cộng dồn)", size=12, anchor="middle", fill=DARK)
    label(f, 24, ya + 62, 92, 28, ["weight"], size=12)
    label(f, 24, ya + 106, 92, 28, ["ifmap pixel"], size=12)
    cx, cy = 156, ya + 98
    for ox, s in [(0, "x"), (48, "+")]:
        f.a(f'<circle cx="{cx + ox}" cy="{cy}" r="13" fill="white" stroke="#333333" stroke-width="1.2"/>')
        f.text(cx + ox, cy + 1, s, size=17, weight=700, anchor="middle")
    f.line([(116, ya + 76), (cx - 10, cy - 8)], BLUE)
    f.line([(116, ya + 120), (cx - 10, cy + 8)], BLUE)
    f.line([(cx + 13, cy), (cx + 33, cy)], BLUE)
    label(f, 224, ya + 84, 62, 28, ["psum"], size=12)
    f.line([(cx + 61, cy), (222, cy)], BLUE)
    f.line([(255, ya + 112), (255, ya + 146), (cx + 48, ya + 146), (cx + 48, cy + 15)], GRAY, dashed=True)
    f.text(cx - 6, ya + 160, "cộng dồn vào psum", size=11.5, fill=DARK)
    txt(f, 22, ya + 188, [
        "EYE tr.4: C·R² psum được cộng lại",
        "thành một pixel ofmap.",
        "EYE tr.2: ALU trong PE làm được",
        "MAC và phép cộng.",
    ], size=12, dy=17)

    # ---- column 2: PE (EYE) ----
    card(f, 315, ya, 290, ha, "PE (processing engine), EYE")
    f.text(460, ya + 36, "Fig. 1 (zoom-in): ba thành phần", size=12, anchor="middle", fill=DARK)
    label(f, 326, ya + 62, 64, 92, ["pFIFO"], size=13, weight=700)
    label(f, 412, ya + 62, 88, 92, ["ALU", "datapath", "MAC, cộng"], size=12, weight=700)
    label(f, 522, ya + 62, 72, 92, ["RF"], size=13, weight=700, fill=STAT)
    f.line([(392, ya + 100), (410, ya + 100)], BLUE)
    f.line([(410, ya + 116), (392, ya + 116)], BLUE)
    f.line([(502, ya + 108), (520, ya + 108)], GRAY, head=False)
    txt(f, 326, ya + 172, [
        "pFIFO: điều khiển lưu lượng vào và ra ALU",
        "RF: local scratchpad (bộ nhớ cục bộ)",
        "ALU: làm được MAC và cộng",
    ], size=12, dy=17)
    f.text(326, ya + 232, "MAC chỉ là một phần của PE.", size=12.5, weight=700)

    # ---- column 3: TPU matrix unit ----
    card(f, 620, ya, 270, ha, "Matrix Multiply Unit, TPU")
    f.text(755, ya + 36, "256x256 MACs, 8-bit (tr.3)", size=12, anchor="middle", fill=DARK)
    gx, gy, cs, gap = 648, ya + 56, 30, 8
    for r in range(4):
        for c in range(4):
            rect(f, gx + c * (cs + gap), gy + r * (cs + gap), cs, cs, "white", "#555555", 1)
            f.text(gx + c * (cs + gap) + cs / 2, gy + r * (cs + gap) + cs / 2, "MAC", size=9, anchor="middle")
    f.text(gx + 4 * (cs + gap) + 2, gy + 60, "...", size=16, weight=700)
    f.text(gx + 4 * (cs + gap) + 2, gy + 110, "...", size=16, weight=700)
    f.line([(gx + 76, gy + 4 * (cs + gap) - 2), (gx + 76, gy + 4 * (cs + gap) + 20)], BLUE)
    yy = gy + 4 * (cs + gap) + 22
    label(f, gx, yy, 4 * (cs + gap) - gap, 24, ["Accumulators 32-bit"], size=11.5)
    txt(f, 632, yy + 38, ["Tích 16-bit gom vào 4 MiB", "accumulator 32-bit (tr.3).", "Bài không dùng chữ PE."],
        size=11.5, dy=15)

    # ---- row B: PE array in EYE ----
    yb = ya + ha + 18
    f.text(10, yb + 4, "PE array trong Eyeriss: bốn cấp lưu trữ", size=15, weight=700)
    yb += 16
    rect(f, 10, yb, 575, 232, "#F5F5F5", "#666666", 1.2, rx=8)
    label(f, 24, yb + 80, 76, 56, ["DRAM", "ngoài chip"], size=12, weight=700)
    label(f, 140, yb + 80, 92, 56, ["Global", "buffer"], size=12, weight=700)
    f.line([(102, yb + 98), (138, yb + 98)], BLUE)
    f.line([(138, yb + 118), (102, yb + 118)], BLUE)
    f.line([(234, yb + 98), (326, yb + 98)], BLUE)
    f.line([(326, yb + 118), (234, yb + 118)], BLUE)
    f.text(120, yb + 150, "iFIFO / oFIFO", size=11, anchor="middle", fill=DARK)
    f.text(285, yb + 150, "iFIFO / oFIFO", size=11, anchor="middle", fill=DARK)
    px, py = 330, yb + 36
    for r in range(3):
        for c in range(3):
            rect(f, px + c * 76, py + r * 56, 56, 40, "white", "#333333", 1.2)
            f.text(px + c * 76 + 28, py + r * 56 + 12, "PE", size=12, weight=700, anchor="middle")
            rect(f, px + c * 76 + 8, py + r * 56 + 21, 40, 14, STAT, "#555555", 0.8, rx=2)
            f.text(px + c * 76 + 28, py + r * 56 + 28, "RF", size=10, anchor="middle")
            if c < 2:
                f.a(f'<path d="M{px + c * 76 + 56} {py + r * 56 + 20} L{px + c * 76 + 76} {py + r * 56 + 20}" '
                    f'stroke="{GRAY}" stroke-width="1.4"/>')
            if r < 2:
                f.a(f'<path d="M{px + c * 76 + 28} {py + r * 56 + 40} L{px + c * 76 + 28} {py + r * 56 + 56}" '
                    f'stroke="{GRAY}" stroke-width="1.4"/>')
    f.text(px + 94, py - 14, "PE array, nối bằng NoC", size=12, anchor="middle", fill=DARK)
    f.text(24, yb + 194, "Bốn cấp: DRAM, global buffer, array (liên PE), RF (EYE tr.2).", size=11.5, fill=DARK)
    f.text(24, yb + 212, "Global buffer thường cỡ 100-300kB; RF thường dưới 1kB mỗi PE.", size=11.5, fill=DARK)

    f.text(600, yb - 2, "Chip Eyeriss (EYE tr.5, Fig. 4)", size=13.5, weight=700)
    f.table(600, yb + 12, [150, 140], ["Mục", "Giá trị"], [
        ["Process", "65nm CMOS"], ["# of PEs", "168"], ["RF Size/PE", "0.5 kB"],
        ["Buffer Size", "108 kB"], ["Clock Rate", "200 MHz"], ["Precision", "16-bit Fixed-Point"],
    ], size=12, line_h=15)

    # ---- row C: comparison ----
    yc = yb + 248
    f.text(10, yc + 4, "So sánh hai cách gọi", size=15, weight=700)
    y = f.table(10, yc + 18, [130, 380, 370], ["Mục", "EYE (Eyeriss)", "TPU"], [
        ["Tên đơn vị", "PE (processing engine)", "MAC; chữ PE không có trong bài"],
        ["Bên trong", "ALU datapath (MAC, cộng), RF, pFIFO", "Matrix Multiply Unit gồm 256x256 MAC"],
        ["Số lượng", "168 PE trên chip Eyeriss", "65,536 MAC"],
    ], size=12.5)
    y = f.textbox(10, y + 10, 880, [
        [("Không đồng nhất ", "b"), ("một PE với một MAC: PE của EYE có thêm RF và pFIFO; TPU đếm theo MAC.", "t")],
        "Số PE, số MAC, 65 nm và 28 nm là của paper, không phải của RK3588.",
    ], size=12.5)
    y = link_box(f, 10, y + 12, 880, [
        [("TRM1 tr.1984: ", "b"), ("\"1024x3 integer 8 MAC operations per cycle\"; TRM1 tr.2001: \"Int8 mac array 32x32 mode\".", "t")],
        "32 x 32 = 1024 là phép tính của bộ hình (khớp với số trên); TRM không nói một ô 32x32 là một PE.",
        "unknown: một \"PE\" của RK3588 là gì; bố cục MAC array cho INT16, FP16, INT4. Xem Hình 2.2, Hình 2.3.",
    ])
    source(f, y + 8, "Nguồn: EYE tr.2, 3, 4, 5; TPU tr.1, 3; TRM1 tr.1984, 2001.")
    return f


# =====================================================================
# Hinh 1.2: dataflow
# =====================================================================
def mini_pe(f, x, y, kind):
    rect(f, x, y, 188, 84, "white", "#333333", 1.2)
    f.text(x + 8, y + 11, "PE", size=12, weight=700)
    if kind == "nlr":
        label(f, x + 8, y + 24, 100, 52, ["không có RF"], size=11.5, dashed=True, stroke="#888888", color=DARK)
    else:
        txt_rf = {"ws": ["weight"], "os": ["psum của", "1 pixel ofmap"], "rs": ["cặp hàng", "filter, ifmap"]}[kind]
        label(f, x + 8, y + 24, 100, 52, ["RF"] + txt_rf, size=11.5, fill=STAT, stroke="#555555")
    label(f, x + 124, y + 24, 56, 52, ["ALU"], size=12, weight=700)
    f.line([(x + 108, y + 50), (x + 122, y + 50)], GRAY, head=False)


def fig_dataflow():
    f = Fig(W, 1300)
    tier(f)
    f.text(10, 50, "Bốn dataflow của EYE: PE giữ yên thứ gì trong RF", size=15, weight=700)
    ycard, hcard = 66, 418
    xs = [10, 232, 454, 676]
    spec = [
        ("Weight stationary", "WS, EYE tr.4", "ws", [
            ("Giữ yên", ["Mỗi weight nằm yên trong", "RF; PE chạy hết N·E² phép", "dùng weight đó."]),
            ("Chuyển động", ["Pixel ifmap được broadcast", "tới các PE; psum cộng dồn", "qua các PE."]),
            ("Hệ quả", ["Psum không luôn cộng được", "ngay, tạm lưu ở global", "buffer."]),
            ("Tối đa hóa", ["Convolutional reuse và filter", "reuse của weight trong RF", "(Table III)."]),
        ]),
        ("Output stationary", "OS, EYE tr.4, 5", "os", [
            ("Giữ yên", ["Tích lũy của mỗi pixel", "ofmap nằm yên trong PE;", "psum nằm trong cùng RF."]),
            ("Chuyển động", ["Mọi tái dùng đầu vào khác", "làm ở mức array (liên PE);", "RF chỉ cộng dồn psum."]),
            ("Biến thể", ["SOC-MOP, MOC-MOP, MOC-SOP", "(Fig. 3)."]),
            ("Tối đa hóa", ["Psum accumulation trong RF", "(Table III)."]),
        ]),
        ("Row stationary", "RS, EYE tr.5, 6, 7", "rs", [
            ("Giữ yên", ["Mỗi primitive (1 hàng weight,", "1 hàng ifmap, ra 1 hàng", "psum) chạy trong một PE;", "cặp hàng nằm yên."]),
            ("Chuyển động", ["Hàng filter dùng lại theo", "chiều ngang, hàng ifmap theo", "đường chéo, hàng psum cộng", "dồn theo chiều dọc (Fig. 6)."]),
            ("Tối đa hóa", ["RF dùng cho mọi loại tái", "dùng và psum accumulation", "(tr.6)."]),
        ]),
        ("No local reuse", "NLR, EYE tr.5", "nlr", [
            ("Giữ yên", ["Không tái dùng ở mức RF."]),
            ("Chuyển động", ["Tái dùng ifmap và cộng dồn", "psum bằng giao tiếp giữa", "các PE; các PE cùng nhóm", "đọc cùng pixel ifmap, khác", "weight."]),
            ("Phần cứng", ["Mảng PE chỉ có ALU; chừa", "diện tích lớn cho global", "buffer, nơi lưu psum và", "dữ liệu vào."]),
        ]),
    ]
    for x, (t, sub, kind, blocks) in zip(xs, spec):
        card(f, x, ycard, 212, hcard, t)
        f.text(x + 106, ycard + 36, sub, size=11.5, anchor="middle", fill=DARK)
        mini_pe(f, x + 12, ycard + 50, kind)
        y = ycard + 150
        for head, ls in blocks:
            f.text(x + 12, y, head, size=12, weight=700, fill=BLUE)
            y = txt(f, x + 12, y + 17, ls, size=11.5, dy=15) + 8
    # stationary legend under the cards
    yl = ycard + hcard + 12
    f.a(f'<rect x="10" y="{yl}" width="38" height="16" rx="2" fill="{STAT}" stroke="#BBBBBB"/>')
    f.text(58, yl + 8, "thứ PE giữ yên trong RF (stationary)", size=12.5)
    f.text(330, yl + 8, "Systolic là cách dữ liệu chảy, stationary là thứ PE giữ: xem Hình 1.5.", size=12.5, fill=DARK)

    # ---- original + notes ----
    yo = yl + 30
    yb = original_crop(f, 10, yo, 380, "../../npu_study/images/01_npu_fundamentals/eyeriss_fig5.png", [
        "EYE tr.6, Fig. 5: một 1D convolution primitive trong PE",
        "(R = 3, H = 5): 9 phép Op1 đến Op9, ra 3 psum.",
        "Đã cắt phần chữ thừa bên phải ảnh gốc."])
    y = f.textbox(420, yo, 470, [
        [("Đọc Hình gốc", "b"), (" (RS chạy một primitive trong một PE):", "t")],
        "weight 1 2 3 trượt qua hàng ifmap 1 2 3 4 5;",
        "mỗi ba phép nhân-cộng cho một psum (đọc từ hình).",
    ], size=12.5)
    y = f.textbox(420, y + 10, 470, [
        [("Không dataflow nào tối ưu mọi thứ cùng lúc", "b")],
        "EYE tr.4: tái dùng đầu vào tối đa không đạt được đồng thời",
        "với cộng dồn psum ngay, vì các psum từ cùng filter hay",
        "ifmap không cộng được với nhau.",
        "EYE tr.5: các dataflow cũ không tính đồng thời mọi loại.",
    ], size=12)
    y = f.textbox(420, y + 10, 470, [
        [("Bài khác nhìn khác nhau", "b")],
        "LP tr.2: chọn output stationary, \"commonly used\".",
        "FLEX tr.1: phân loại lịch thực thi theo dữ liệu giữ trên",
        "chip: input, output, weight-stationary.",
    ], size=12)
    y = max(yb, y) + 14
    y = link_box(f, 10, y, 880, [
        "unknown: RK3588 dùng dataflow nào (weight, output, row stationary hay khác). TRM1 tr.1984-2060, TRM2, DS, UG152, API232",
        "không có các từ khóa dataflow, stationary, systolic, tiling, processing element (02_ mục 2.11). Xem Hình 2.2.",
        [("T1 biết: ", "b"), ("TRM1 tr.2001 \"Int8 mac array 32x32 mode\"; TRM1 tr.1984 buffer \"384KBx3 internal buffer\".", "t")],
    ])
    source(f, y + 8, "Nguồn: EYE tr.4, 5, 6, 7; FLEX tr.1; LP tr.2; TRM1 tr.1984, 2001.")
    return f


# =====================================================================
# Hinh 1.5: systolic va da loi
# =====================================================================
def fig_systolic():
    f = Fig(W, 1900)
    tier(f)
    # ---------------- A: systolic ----------------
    f.text(10, 50, "A. Systolic: dữ liệu chảy qua mảng (TPU Fig. 4)", size=15, weight=700)
    ya = 66
    rect(f, 10, ya, 430, 440, "#F5F5F5", "#666666", 1.2, rx=8)
    gx, gy, cw, ch, gx_gap, gy_gap = 100, ya + 66, 52, 38, 22, 22
    ncol, nrow = 4, 4
    for r in range(nrow):
        for c in range(ncol):
            label(f, gx + c * (cw + gx_gap), gy + r * (ch + gy_gap), cw, ch, ["MAC"], size=11.5)
        f.line([(gx - 40, gy + r * (ch + gy_gap) + ch / 2), (gx - 2, gy + r * (ch + gy_gap) + ch / 2)], BLUE)
        for c in range(ncol - 1):
            xx = gx + c * (cw + gx_gap) + cw
            f.line([(xx + 1, gy + r * (ch + gy_gap) + ch / 2), (xx + gx_gap - 1, gy + r * (ch + gy_gap) + ch / 2)], BLUE)
    for c in range(ncol):
        xx = gx + c * (cw + gx_gap) + cw / 2
        f.line([(xx, gy - 28), (xx, gy - 2)], GRAY, dashed=True)
        for r in range(nrow - 1):
            yy = gy + r * (ch + gy_gap) + ch
            f.line([(xx, yy + 1), (xx, yy + gy_gap - 1)], INK)
        yy = gy + (nrow - 1) * (ch + gy_gap) + ch
        f.line([(xx, yy + 1), (xx, yy + 24)], INK)
        label(f, xx - 28, yy + 26, 56, 26, ["Acc +"], size=11)
    f.text(16, gy + ch / 2 - 14, "dữ liệu vào", size=11, fill=BLUE)
    f.text(gx + 4 * (cw + gx_gap) - 14, gy - 40, "weight nạp từ trên (preload)", size=11.5, fill=DARK, anchor="end")
    f.text(gx + 4 * (cw + gx_gap) - 14, gy + 4 * (ch + gy_gap) + 40, "partial sum chảy xuống accumulator", size=11.5,
           fill=DARK, anchor="end")
    f.a(f'<path d="M{gx + 4 * (cw + gx_gap) - 20} {gy - 4} L{gx - 8} {gy + 4 * (ch + gy_gap) - 20}" '
        f'stroke="{RED}" stroke-width="1.4" stroke-dasharray="6 4" fill="none"/>')
    f.text(16, gy + 190, "wavefront", size=11.5, fill=RED)
    f.text(16, gy + 206, "chéo", size=11.5, fill=RED)
    f.text(24, ya + 420, "Hình vẽ lại: thu gọn còn 4x4 ô (TPU: 256x256).", size=11.5, fill=DARK)
    f.text(24, ya + 402, "Chiều mũi tên theo Fig. 4: dữ liệu từ trái, weight từ trên, partial sum đi xuống.", size=11.5, fill=DARK)

    y = f.textbox(455, ya, 435, [
        [("Mục đích (TPU tr.4)", "b")],
        "dùng systolic execution để tiết kiệm năng lượng bằng",
        "cách giảm đọc và ghi Unified Buffer.",
        "Dữ liệu từ nhiều hướng đến các ô đều đặn, rồi được kết hợp;",
        "một phép nhân-cộng 256 phần tử đi qua ma trận như",
        "một diagonal wavefront.",
        "Weight nạp trước; matrix unit giữ một tile weight 64 KiB",
        "cộng một tile cho double-buffering (tr.3).",
    ], size=12)
    f.text(455, y + 18, "Systolic và stationary: hai khái niệm khác nhau", size=13.5, weight=700)
    y = f.table(455, y + 30, [60, 375], ["Bài", "Điều bài nói"], [
        ["EYE", ("lines", ["tr.7: WS, \"the PE array operates as a systolic array\"", "với rất ít điều khiển cục bộ."])],
        ["LP", ("lines", ["tr.2: mảng systolic, dataflow chọn là output", "stationary."])],
        ["TPU", ("lines", ["không dùng chữ \"stationary\" (đã tìm toàn bài);", "systolic mô tả cách dữ liệu chảy."])],
    ], size=11.5, line_h=15)
    y = f.textbox(455, y + 10, 435, [
        [("Suy ra của bộ hình: ", "b"), ("systolic là cách truyền dữ liệu,", "t")],
        "stationary là thứ PE giữ lại; hai thứ dùng chung được.",
    ], size=12)

    # ---------------- B: layer split ----------------
    yb = max(ya + 440, y) + 24
    f.text(10, yb + 6, "B. Chia một lớp cho hai core (JUNG Fig. 5, Table 1)", size=15, weight=700)
    yb += 20
    f.a(f'<rect x="10" y="{yb}" width="880" height="296" rx="8" fill="#F5F5F5" stroke="#666666" stroke-width="1.2"/>')

    def split_block(x, y, w, h, name, mode):
        """mode: 'split' (halves for P0, P1) or 'repl' (both cores hold a full copy)."""
        if mode == "split":
            rect(f, x, y, w / 2, h, P0, "#333333", 1.2, rx=0)
            rect(f, x + w / 2, y, w / 2, h, P1, "#333333", 1.2, rx=0)
            f.text(x + w / 4, y + h / 2, "P0", size=11, anchor="middle")
            f.text(x + 3 * w / 4, y + h / 2, "P1", size=11, anchor="middle")
        else:
            rect(f, x, y, w, h, "white", "#333333", 1.2, rx=0)
            rect(f, x + 6, y + 6, w - 12, h - 12, "white", GRAY, 1, dashed=True, rx=0)
            f.text(x + w / 2, y + h / 2, "P0 và P1", size=11, anchor="middle")
        f.text(x + w / 2, y + h + 14, name, size=12, weight=700, anchor="middle")
        f.text(x + w / 2, y + h + 30, "chia đôi" if mode == "split" else "nhân bản", size=11.5, anchor="middle",
               fill=DARK)

    f.text(24, yb + 22, "Spatial partitioning", size=13.5, weight=700)
    for i, (n, m) in enumerate([("input", "split"), ("kernel", "repl"), ("output", "split")]):
        split_block(30 + i * 100, yb + 40, 84, 50, n, m)
    f.text(24, yb + 150, "Channel partitioning", size=13.5, weight=700)
    for i, (n, m) in enumerate([("input", "repl"), ("kernel", "split"), ("output", "split")]):
        split_block(30 + i * 100, yb + 172, 84, 50, n, m)
    txt(f, 340, yb + 22, [
        [("Spatial (Table 1, hàng 1)", "b")],
        "input và output chia theo chiều cao hoặc rộng; kernel",
        "nhân bản ở cả hai core. Không cần cộng thêm.",
    ], size=12, dy=17)
    txt(f, 340, yb + 100, [
        [("Channel (hàng 3)", "b")],
        "kernel và output chia theo kênh; input nhân bản ở cả hai",
        "core. Không cần cộng thêm.",
    ], size=12, dy=17)
    txt(f, 340, yb + 180, [
        [("Hai hàng có dấu * (hàng 2 và 4)", "b"), (" cần partial sum reduction,", "t")],
        "tức thêm giao tiếp và tính toán: JUNG không ưa dùng.",
        [("tr.9: ", "b"), ("hướng chia ảnh hưởng cân bằng tải vì ràng buộc alignment;", "t")],
        "hướng kênh đòi alignment lớn hơn hướng không gian.",
    ], size=12, dy=17)
    f.text(24, yb + 282, "JUNG: Samsung, SoC mobile ba core; không phải Rockchip.", size=11.5, fill=DARK, italic=True)

    # ---------------- C: tiling + scheduling ----------------
    yc = yb + 296 + 24
    f.text(10, yc + 6, "C. Tiling trong một core và lập lịch giữa các lớp", size=15, weight=700)
    yc += 20
    rect(f, 10, yc, 430, 258, "#F5F5F5", "#666666", 1.2, rx=8)
    f.text(24, yc + 20, "Tiling: chia một lớp thành tile, chạy kiểu pipeline", size=13.5, weight=700)
    x0, unit = 88, 54
    rows = ["load", "compute", "store"]
    for i, rname in enumerate(rows):
        yy = yc + 52 + i * 38
        f.text(24, yy + 14, rname, size=12.5, weight=700)
        for t in range(3):
            fill = [P0, P1, "#FFF1CC"][t]
            label(f, x0 + (t + i) * unit, yy, unit - 3, 28, [f"tile {t}"], size=11, fill=fill)
    f.a(f'<path d="M{x0} {yc + 168} L{x0 + 5 * unit} {yc + 168}" stroke="{GRAY}" stroke-width="1.4"/>')
    f.line([(x0 + 4 * unit, yc + 168), (x0 + 5 * unit + 6, yc + 168)], GRAY)
    f.text(x0 + 5 * unit + 8, yc + 168, "thời gian", size=11.5, fill=DARK)
    txt(f, 24, yc + 190, [
        "Minh họa của bộ hình theo JUNG tr.4: DMA tới global memory",
        "chồng lên tính toán nhờ double buffering và pipeline load,",
        "compute, store. FLEX tr.2: tiling = chia tính toán một lớp",
        "thành các phép trên tile nhỏ hơn.",
    ], size=11.5, dy=15)

    f.text(455, yc + 12, "Lập lịch: ba bài, ba quyết định khác nhau", size=13.5, weight=700)
    y = f.table(455, yc + 24, [60, 130, 245], ["Bài", "Quyết định", "Điều bài nói"], [
        ["JUNG", ("lines", ["thứ tự lớp: depth-first", "so với breadth-first"]),
         ("lines", ["tr.5: depth-first \"increases chances", "of data reuse\"; breadth-first loại bớt", "phụ thuộc giữa các lớp kế tiếp."])],
        ["FLEX", ("lines", ["thứ tự tile: out-of-order", "list scheduling"]),
         ("lines", ["tr.1: lập lịch động workload đã tile", "cho mọi NPU (list scheduling)."])],
        ["LP", ("lines", ["nhiều DNN: temporal-", "sharing hay spatial-", "sharing"]),
         ("lines", ["tr.1: temporal: DNN chiếm toàn bộ", "phần cứng theo lớp; spatial: mỗi DNN", "được cấp tài nguyên cố định."])],
    ], size=11, line_h=14)

    # memory models
    ym = yc + 258 + 22
    f.text(10, ym + 4, "Ba mô hình bộ nhớ đa core khác nhau", size=13.5, weight=700)
    y3 = f.table(10, ym + 18, [60, 820], ["Bài", "Bộ nhớ và kết nối (trích nguồn)"], [
        ["JUNG", "tr.2: \"distributed, isolated local memory per core\"; local memory quản lý tường minh bằng load và store tới global memory."],
        ["FLEX", "tr.2: \"A shared on-chip scratchpad memory, labeled Global Buffer\" dùng chung giữa các core."],
        ["LP", "tr.2: nhiều NPU đồng nhất nối với router, dữ liệu mỗi NPU đi qua NoC; tắc nghẽn NoC và DRAM ảnh hưởng hiệu năng hệ thống."],
    ], size=11.5, line_h=15)
    y = f.textbox(10, y3 + 10, 880, [
        [("Không có một kiến trúc \"NPU đa core\" duy nhất. ", "b"),
         ("Cách chia (không gian hay kênh) và lập lịch phụ thuộc mô hình bộ nhớ của từng bài.", "t")],
    ], size=12.5)
    y = link_box(f, 10, y + 12, 880, [
        [("T1 biết: ", "b"), ("TRM1 tr.1984 \"Support triple core co-work, dual core co-work, and work independently\"; UG152 tr.26 có", "t")],
        "core mask AUTO, CORE_0, CORE_0_1, CORE_0_1_2...; UG152 tr.27: op không nằm trong danh sách \"will fallback to Core0\". Xem Hình 2.4.",
        [("unknown: ", "b"), ("cách RK3588 chia một lớp cho nhiều core (không gian, kênh hay batch); có dùng systolic hay tiling như", "t")],
        "trên không (TRM không có các từ khóa này, 02_ mục 2.11). Không suy ra từ JUNG, FLEX, LP. Số đo: Hình 10.3.",
    ])
    source(f, y + 8, "Nguồn: TPU tr.3, 4; LP tr.1, 2; EYE tr.7; JUNG tr.1, 2, 4, 5, 9; FLEX tr.1, 2; TRM1 tr.1984; UG152 tr.26, 27.")
    return f


# =====================================================================
# Hinh 1.3: chi phi bo nho (chart)
# =====================================================================
def chart_memory():
    # EYE Table IV (PDF page 8): normalised energy cost relative to a MAC operation, commercial 65 nm process.
    levels = [("RF", "0.5 kB", 1), ("Array\n(liên PE)", "1-2 mm", 2), ("Global buffer", "> 100 kB", 6), ("DRAM", "", 200)]
    fig = plt.figure(figsize=(11.5, 7.6))
    axa = fig.add_axes([0.07, 0.47, 0.40, 0.40])
    axb = fig.add_axes([0.60, 0.47, 0.37, 0.40])

    cols = [CGREEN, "#7FBF86", "#8FA9D6", CBLUE]
    for i, (name, cond, val) in enumerate(levels):
        axa.bar(i, val, 0.62, color=cols[i], zorder=2)
        axa.text(i, val * 1.18, f"{val}x", ha="center", va="bottom", fontsize=12, fontweight="bold")
    axa.set_yscale("log")
    axa.set_ylim(0.6, 700)
    axa.set_xticks(range(4))
    axa.set_xticklabels([f"{n}\n({c})" if c else n for n, c, _ in levels], fontsize=10)
    axa.set_ylabel("năng lượng một lần truy cập, tương đối so với 1 MAC\n(thang log)")
    axa.set_title("A. Năng lượng theo cấp bộ nhớ (EYE Table IV)", fontsize=11, loc="left", fontweight="bold")

    # panel B: Eq. (3) with Fig. 8 example (a, b, c, d) = (1, 2, 3, 4): total 24 reuses
    abcd = [1, 2, 3, 4]
    ec = {"DRAM": 200, "Global buffer": 6, "Array": 2, "RF": 1}
    reads = [abcd[0], abcd[0] * abcd[1], abcd[0] * abcd[1] * abcd[2], abcd[0] * abcd[1] * abcd[2] * abcd[3]]
    parts = [("DRAM", reads[0], CBLUE), ("Global buffer", reads[1], "#8FA9D6"),
             ("Array", reads[2], "#7FBF86"), ("RF", reads[3], CGREEN)]
    total = sum(r * ec[n] for n, r, _ in parts)
    left = 0
    for k, (n, r, c) in enumerate(parts):
        e = r * ec[n]
        axb.barh(0, e, left=left, color=c, edgecolor="white", height=0.5, zorder=2)
        axb.barh(0, 0, color=c, label=f"{n}: {r} x {ec[n]} = {e}")
        if n == "DRAM":
            axb.text(left + e / 2, 0, f"{n}\n{r} x {ec[n]} = {e}", ha="center", va="center", fontsize=9.5,
                     color="white", fontweight="bold")
        left += e
    axb.legend(loc="lower left", fontsize=9, frameon=True, title="số lượt đọc x EC = năng lượng", title_fontsize=9)
    axb.set_xlim(0, total * 1.02)
    axb.set_ylim(-0.9, 0.9)
    axb.set_yticks([])
    axb.set_xlabel("tổng năng lượng truy cập (đơn vị: một phép MAC)")
    axb.grid(axis="y", visible=False)
    axb.set_title("B. Ví dụ Eq. (3): 24 lần dùng lại chia a=1, b=2, c=3, d=4", fontsize=11, loc="left", fontweight="bold")
    axb.text(3, 0.62, f"tổng = {total}; DRAM chiếm {ec['DRAM'] * reads[0]}/{total} = "
             f"{100 * ec['DRAM'] * reads[0] / total:.0f}% dù chỉ 1 trong 24 lần đọc",
             fontsize=9.5, color=CDARK, ha="left", va="center")
    fig.text(0.07, 0.355, "Panel B là phép tính của bộ hình theo Eq. (3): a x EC(DRAM) + ab x EC(global buffer) + abc x EC(array) + abcd x EC(RF),\n"
             "với EC lấy từ Table IV và số lượt đọc 1, 2, 6, 24 (a=1, b=2, c=3, d=4, ví dụ của Fig. 8). Con số tổng 248 không in trong paper.",
             fontsize=9.2, color=CDARK, ha="left", va="top")

    lines = [
        "Điều kiện của số trong Table IV: chuẩn hóa so với một phép MAC; \"extracted from a commercial 65 nm process\" (EYE tr.8). Đây là số của paper,",
        "không phải của RK3588. Global buffer > 100 kB, Array 1-2 mm, RF 0.5 kB. Chi phí DRAM và global buffer gồm cả iFIFO/oFIFO; Array gồm",
        "iFIFO/oFIFO/pFIFO hai phía và điện dung dây. Là tỷ lệ \"relative to a MAC operation\", không phải số đo tuyệt đối.",
    ]
    for k, ln in enumerate(lines):
        fig.text(0.015, 0.244 - 0.030 * k, ln, fontsize=9.5, color=CINK, ha="left", va="center")
    fig.add_artist(plt.Rectangle((0.008, 0.165), 0.984, 0.125, transform=fig.transFigure, fill=False, edgecolor="#999999", lw=1))
    fig.text(0.015, 0.272, "Điều kiện và lưu ý", fontsize=10.5, fontweight="bold", ha="left", va="center")

    fig.add_artist(plt.Rectangle((0.008, 0.045), 0.984, 0.105, transform=fig.transFigure, fill=False, edgecolor=CBLUE, lw=1.6))
    fig.text(0.015, 0.138, "Liên hệ RK3588 (T1)", fontsize=10.5, fontweight="bold", color=CBLUE, ha="left", va="center")
    rk = [
        "unknown: hệ số năng lượng theo cấp bộ nhớ của RK3588, và việc nối các cấp T1 (buffer \"384KBx3 internal buffer\", TRM1 tr.1984; system SRAM tối đa",
        "956KB cho NPU, SRAM dòng 21; DDR qua interconnect, TRM2 tr.16) với bốn cấp của EYE. Xem Hình 2.1, 2.2; đường dữ liệu: Hình 7.1 (chưa làm).",
    ]
    for k, ln in enumerate(rk):
        fig.text(0.015, 0.108 - 0.032 * k, ln, fontsize=9.5, color=CINK, ha="left", va="center")
    source_line(fig, "Nguồn: EYE tr.2, tr.8 (Table IV, Eq. 3); TRM1 tr.1984; TRM2 tr.16; SRAM dòng 21.", y=0.008)
    tier_label(fig, "T2 chung")
    return fig


# =====================================================================
# Hinh 1.4: roofline (concept + TPU numbers)
# =====================================================================
def chart_roofline():
    import numpy as np
    fig = plt.figure(figsize=(11.5, 8.4))
    ax = fig.add_axes([0.07, 0.42, 0.42, 0.46])
    x = np.logspace(0, 4, 200)
    bw, peak = 1.0, 400.0     # illustrative units only; no tick labels are shown
    y = np.minimum(x * bw, peak)
    ridge = peak / bw
    ax.plot(x, y, color=CBLUE, lw=3, zorder=3)
    ax.axvline(ridge, color=CGRAY, ls="--", lw=1.2, zorder=2)
    ax.fill_between(x[x <= ridge], 1, y[x <= ridge], color="#EEF3FB", zorder=1)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1, 1e4)
    ax.set_ylim(1, 1500)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.minorticks_off()
    ax.grid(False)
    ax.set_xlabel("operational intensity (thấp -> cao)")
    ax.set_ylabel("hiệu năng đạt được (thấp -> cao)")
    ax.plot([12], [9], "o", color=CRED, ms=9, zorder=5)
    ax.text(15, 6, "chương trình A:\ncường độ thấp", color=CRED, fontsize=9.5, va="top")
    ax.plot([2200], [peak * 0.88], "s", color=CGREEN, ms=9, zorder=5)
    ax.text(2000, peak * 0.50, "chương trình B:\ncường độ cao", color=CGREEN, fontsize=9.5, va="top", ha="center")
    ax.text(1500, 10, "dữ liệu minh họa,\nkhông phải số đo", color=CRED, fontsize=10.5, fontweight="bold", va="bottom", ha="center",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=CRED, lw=1.2))
    ax.text(3, 11, "phần nghiêng: băng thông bộ nhớ\n(memory-bound)", color=CBLUE, fontsize=9.5, rotation=34,
            ha="left", va="bottom", rotation_mode="anchor")
    ax.text(ridge * 1.15, peak * 1.12, "phần phẳng: đỉnh tính toán\n(compute-bound)", color=CBLUE, fontsize=9.5, ha="left", va="bottom")
    ax.text(ridge * 0.9, 1.6, "ridge point", color=CDARK, fontsize=9.5, rotation=90, ha="right", va="bottom")
    ax.set_title("A. Roofline khái niệm (minh họa)", fontsize=11, loc="left", fontweight="bold")

    # right panel: definitions + TPU numbers (text)
    fig.text(0.54, 0.915, "B. Cường độ tính toán: hai cách định nghĩa", fontsize=11, fontweight="bold", ha="left")
    defs = [
        ("HPC (TPU tr.5):", "trục X là floating-point operations per DRAM byte accessed"),
        ("TPU (tr.6):", "integer operations per byte of weights read (đã lượng tử, weight không nằm vừa trên chip)"),
    ]
    for k, (a, b) in enumerate(defs):
        fig.text(0.54, 0.875 - 0.045 * k, a, fontsize=9.8, fontweight="bold", ha="left", va="center")
        fig.text(0.64, 0.875 - 0.045 * k, b, fontsize=9.3, ha="left", va="center", wrap=True)
    fig.text(0.54, 0.775, "C. Sáu ứng dụng của TPU (số của TPU, không phải RK3588)", fontsize=11, fontweight="bold", ha="left")
    apps = [("MLP0", 200, "memory bound"), ("MLP1", 168, "memory bound"), ("LSTM0", 64, "memory bound"),
            ("LSTM1", 96, "memory bound"), ("CNN0", 2888, "computation bound"), ("CNN1", 1750, "computation bound")]
    fig.text(0.54, 0.735, "ứng dụng", fontsize=9.5, fontweight="bold", ha="left")
    fig.text(0.65, 0.735, "TPU Ops / Weight Byte (Table 1, tr.2)", fontsize=9.5, fontweight="bold", ha="left")
    fig.text(0.86, 0.735, "tr.6", fontsize=9.5, fontweight="bold", ha="left")
    for k, (n, v, c) in enumerate(apps):
        yy = 0.70 - 0.032 * k
        fig.text(0.54, yy, n, fontsize=9.5, ha="left", va="center")
        fig.text(0.65, yy, f"{v}", fontsize=9.5, ha="left", va="center")
        fig.text(0.86, yy, c, fontsize=9.5, ha="left", va="center", color=CBLUE if c.startswith("memory") else CGREEN)
    fig.text(0.54, 0.495, "Fig. 5: ridge point ở 1350 operations per byte of weight memory fetched.\n"
             "CNN1 có cường độ rất cao nhưng chỉ đạt 14.1 TOPS, CNN0 đạt 86 TOPS (tr.6).",
             fontsize=9.3, ha="left", va="center", color=CINK)

    lines = [
        "Kết luận \"MLP và LSTM bị giới hạn bộ nhớ, CNN bị giới hạn tính toán\" chỉ đúng cho 6 ứng dụng của TPU (TPU tr.2: \"Four of the six NN apps are",
        "memory-bandwidth limited\"; tr.6). Không suy ra cho mọi NPU hay cho YOLO. Hình A vẽ khái niệm với trục không có số: chương trình A, B và các",
        "đường là minh họa; phần phẳng là \"peak computation rate\", phần nghiêng là băng thông bộ nhớ (TPU tr.5). Mô hình giả định ứng dụng không nằm",
        "vừa trong cache trên chip. Không dùng \"15X - 30X\" của TPU (so với Haswell và K80, 2015) như lợi ích chung của NPU.",
    ]
    for k, ln in enumerate(lines):
        fig.text(0.015, 0.282 - 0.030 * k, ln, fontsize=9.5, color=CINK, ha="left", va="center")
    fig.add_artist(plt.Rectangle((0.008, 0.172), 0.984, 0.145, transform=fig.transFigure, fill=False, edgecolor="#999999", lw=1))
    fig.text(0.015, 0.302, "Điều kiện và lưu ý", fontsize=10.5, fontweight="bold", ha="left", va="center")

    fig.add_artist(plt.Rectangle((0.008, 0.045), 0.984, 0.115, transform=fig.transFigure, fill=False, edgecolor=CBLUE, lw=1.6))
    fig.text(0.015, 0.148, "Liên hệ RK3588 (T1)", fontsize=10.5, fontweight="bold", color=CBLUE, ha="left", va="center")
    rk = [
        "T1 biết: \"1024x3 integer 8 MAC operations per cycle\" (TRM1 tr.1984); Datasheet ghi \"computing power is up to 6TOPs\" (DS tr.7) nhưng",
        "\"Max NPU frequency\" là TBD (DS tr.31): xem Hình 2.3. unknown: ridge point của RK3588 (cần đỉnh tính toán và băng thông DDR NPU nhận được).",
    ]
    for k, ln in enumerate(rk):
        fig.text(0.015, 0.118 - 0.032 * k, ln, fontsize=9.5, color=CINK, ha="left", va="center")
    source_line(fig, "Nguồn: TPU tr.2, 5, 6; TRM1 tr.1984; DS tr.7, 31.", y=0.008)
    tier_label(fig, "T2 chung")
    return fig


FIGS = [
    ("h1-1-mac-pe", fig_mac_pe),
    ("h1-2-dataflow", fig_dataflow),
    ("h1-5-systolic-da-loi", fig_systolic),
]
CHARTS = [("h1-3-chi-phi-bo-nho", chart_memory), ("h1-4-roofline", chart_roofline)]

if __name__ == "__main__":
    args = sys.argv[1:]
    outdir = args[0] if args and not any(args[0] == n for n, _ in FIGS + CHARTS) else HERE
    only = [a for a in args if any(a == n for n, _ in FIGS + CHARTS)]
    sys.argv = [sys.argv[0], outdir] + [n for n in only if any(n == m for m, _ in FIGS)]
    run([(n, b) for n, b in FIGS if not only or n in only], outdir)
    for name, build in CHARTS:
        if not only or name in only:
            save(build(), outdir, name)
