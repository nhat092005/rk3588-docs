#!/usr/bin/env python3
"""Phan 3 Ly thuyet luong tu: Hinh 3.1 den 3.5 (tier T2 chung, tru ghi chu T1 lien he RKNN).

Primary sources (see chu-thich.md, table Nguon): NAGEL (Nagel 2021 whitepaper), GHOLAMI (survey), QYOLO (Q-YOLO),
Y7Q (quantization of YOLOv7), QAREP (QARepVGG); UG232 tr.120 only for the "Lien he RKNN" notes.
All curves in Hinh 3.3 are synthetic illustrations (labelled on the figure); every number elsewhere comes from a cited page.

Usage: python3 gen.py [outdir] [figure-name ...]
Local helpers (diamond, rbox, textbox2, hd) are defined here; proposed for figlib if reused by other parts.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, THICK, Fig, run, source  # noqa: E402

W = 900
UNK_FILL = "#FFF3F3"
CALC_FILL = "#EAF1FB"      # "phep tinh cua bo hinh" (blue-ish) per visual_guide README
LAYER = "#F5F5F5"


def tier(f):
    f.tier(808, 8, "T2 chung")


def hd(f, y, s, x=10):
    """Section heading."""
    f.text(x, y, s, size=15, weight=700)
    return y


def rbox(f, x, y, w, h, lines, size=12.5, fill="white", stroke="#333333", dash=False, bold_first=True, rx=4,
         color=INK):
    d = ' stroke-dasharray="5 3"' if dash else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="1.2"{d}/>')
    if isinstance(lines, str):
        lines = [lines]
    n = len(lines)
    top = y + h / 2 - (n - 1) * (size + 4) / 2
    for i, ln in enumerate(lines):
        f.text(x + w / 2, top + i * (size + 4), ln, size=size, weight=700 if (i == 0 and bold_first) else 400,
               anchor="middle", fill=color)


def diamond(f, cx, cy, w, h, label, size=12, fill="#DDE6F3"):
    f.a(f'<path d="M{cx - w / 2} {cy} L{cx} {cy - h / 2} L{cx + w / 2} {cy} L{cx} {cy + h / 2} Z" fill="{fill}" '
        f'stroke="#333333" stroke-width="1.2"/>')
    f.text(cx, cy, label, size=size, weight=700, anchor="middle")


def textbox2(f, x, y, w, lines, size=12.5, fill="white", stroke="#999999", dash=False, lh=18):
    """Bordered box of left-aligned lines (str or rich parts). Returns bottom y."""
    h = 16 + lh * len(lines)
    d = ' stroke-dasharray="5 3"' if dash else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="1"{d}/>')
    for i, ln in enumerate(lines):
        f.rich(x + 12, y + 8 + lh / 2 + lh * i, ln, size=size)
    return y + h


def tick(f, x, y0, y1, color="#888888", w=1):
    f.a(f'<path d="M{x} {y0} L{x} {y1}" stroke="{color}" stroke-width="{w}"/>')


def dotted(f, x0, y0, x1, y1, color="#999999"):
    f.a(f'<path d="M{x0} {y0} L{x1} {y1}" stroke="{color}" stroke-width="1" stroke-dasharray="2 3"/>')


# =====================================================================
# Hinh 3.1: affine quantization
# =====================================================================
def fig_affine():
    f = Fig(W, 1200)
    tier(f)
    hd(f, 20, "A. Ánh xạ affine: trục thực sang lưới số nguyên (ký hiệu NAGEL, bit-width b)")
    yr, yi = 112, 252
    x_min, x_zero, x_max = 150, 330, 750
    # clip regions
    f.a(f'<rect x="60" y="76" width="{x_min - 60}" height="52" fill="{UNK_FILL}" stroke="none"/>')
    f.a(f'<rect x="{x_max}" y="76" width="{840 - x_max}" height="52" fill="{UNK_FILL}" stroke="none"/>')
    f.text(105, 90, "x < q_min", size=12, anchor="middle", fill=RED)
    f.text(795, 90, "x > q_max", size=12, anchor="middle", fill=RED)
    f.text(105, 118, "bị cắt", size=11.5, anchor="middle", fill=RED)
    f.text(795, 118, "bị cắt", size=11.5, anchor="middle", fill=RED)
    # real axis
    f.line([(60, yr), (846, yr)], INK, THIN)
    f.text(10, yr, "x thực", size=13, weight=700)
    for x in range(x_min, x_max + 1, 20):
        tick(f, x, yr - 5, yr + 5, "#888888")
    tick(f, x_zero, yr - 12, yr + 12, BLUE, 2)
    tick(f, x_min, yr - 12, yr + 12, INK, 2)
    tick(f, x_max, yr - 12, yr + 12, INK, 2)
    f.text(x_min, 56, "q_min = -s z", size=13, anchor="middle", weight=700)
    f.text(x_zero, 56, "số 0 thực", size=13, anchor="middle", weight=700, fill=BLUE)
    f.text(x_max, 56, "q_max = s (2^b - 1 - z)", size=13, anchor="middle", weight=700)
    # step bracket
    f.a(f'<path d="M450 136 L450 142 L470 142 L470 136" fill="none" stroke="{DARK}" stroke-width="1"/>')
    f.text(460, 156, "bước s (step size)", size=12, anchor="middle", fill=DARK)
    # integer axis
    f.line([(60, yi), (846, yi)], INK, THIN)
    f.text(10, yi, "x_int", size=13, weight=700)
    for x in range(x_min, x_max + 1, 20):
        tick(f, x, yi - 5, yi + 5, "#888888")
    tick(f, x_zero, yi - 12, yi + 12, BLUE, 2)
    tick(f, x_min, yi - 12, yi + 12, INK, 2)
    tick(f, x_max, yi - 12, yi + 12, INK, 2)
    f.text(x_min, yi + 26, "0", size=13, anchor="middle", weight=700)
    f.text(x_zero, yi + 26, "z (zero-point, số nguyên)", size=13, anchor="middle", weight=700, fill=BLUE)
    f.text(x_max, yi + 26, "2^b - 1", size=13, anchor="middle", weight=700)
    for x in (x_min, x_zero, x_max):
        dotted(f, x, yr + 14, x, yi - 14)
    # clamp arrows
    f.line([(105, 132), (146, yi - 6)], GRAY, THIN, dashed=True)
    f.line([(795, 132), (754, yi - 6)], GRAY, THIN, dashed=True)
    f.text(20, 215, "clamp về 0", size=12, fill=DARK)
    f.text(890, 215, "clamp về 2^b - 1", size=12, fill=DARK, anchor="end")
    # quantize / dequantize arrows
    f.line([(550, yr + 16), (550, yi - 16)], BLUE, THIN)
    f.rich(540, 176, "x_int = clamp(round(x/s) + z; 0, 2^b - 1)   (Eq. 4)", size=12.5, anchor="end", halo="white")
    f.line([(630, yi - 16), (630, yr + 16)], GRAY, THIN, dashed=True)
    f.rich(640, 172, "x^ = s (x_int - z)", size=12.5, halo="white")
    f.rich(640, 190, "(Eq. 6)", size=12.5, halo="white")
    y = textbox2(f, 10, 296, 880, [
        "z là số nguyên nên số 0 thực rơi đúng vào một điểm lưới: padding bằng 0 và ReLU không gây sai số lượng tử hóa (NAGEL tr.4).",
        "Sai số làm tròn nằm trong [-s/2, s/2]; mở rộng range bằng cách tăng s thì sai số làm tròn tăng (NAGEL tr.4), xem Hình 3.3.",
    ])

    # ---- B ----
    yb = y + 22
    hd(f, yb, "B. Dấu của zero-point: hai quy ước ngược nhau; bộ hình dùng NAGEL làm chuẩn")
    y = f.table(10, yb + 14, [150, 285, 215, 230], ["Nguồn", "Lượng tử hóa", "Giải lượng tử hóa", "Dấu zero-point"], [
        ["NAGEL Eq. 4, 6 (tr.4)", "x_int = clamp(round(x/s) + z; 0, 2^b - 1)", "x^ = s (x_int - z)",
         [("+z khi lượng tử hóa (chuẩn)", "b")]],
        ["GHOLAMI Eq. 2, 3 (tr.5)", "Q(r) = Int(r/S) - Z", "r~ = S (Q(r) + Z)", "-Z khi lượng tử hóa"],
        ["QYOLO Eq. 3, 5 (tr.6)", "Q = clip(round(x/s_x) + zp_x, 0, 2^b - 1)", "x~ = (x^ - zp_x) s_x", "cùng dấu NAGEL"],
    ], size=12.5)

    # ---- C ----
    yc = y + 28
    hd(f, yc, "C. Symmetric và asymmetric: ba lưới (NAGEL Figure 3, Eq. 4, 8)")
    cards = [
        ("Symmetric signed", "z = 0", "lưới -2^(b-1) ... 2^(b-1) - 1 (Eq. 8c)",
         ["hợp với phân bố gần đối xứng quanh 0 (NAGEL tr.5)",
          "8 bit: restricted range [-127, 127],", "full range [-128, 127] (GHOLAMI tr.5)"],
         (0.5, 0.18, 0.82), ("-2^(b-1)", "0", "2^(b-1) - 1")),
        ("Symmetric unsigned", "z = 0", "lưới 0 ... 2^b - 1 (Eq. 8b)",
         ["hợp với phân bố một phía, ví dụ", "activation ReLU (NAGEL tr.5)", ""],
         (0.0, 0.0, 0.78), ("0", "", "2^b - 1")),
        ("Asymmetric", "z là số nguyên tùy ý", "lưới 0 ... 2^b - 1 (Eq. 4)",
         ["range cắt chặt hơn symmetric (GHOLAMI tr.5)", "thêm tham số offset z, có thể tốn tính toán",
          "khi suy luận (NAGEL tr.8)"],
         (0.3, 0.1, 0.9), ("0", "z", "2^b - 1")),
    ]
    cy = yc + 14
    for i, (title, zline, grid, notes, (zpos, a, b), labels) in enumerate(cards):
        x = 10 + i * 297
        f.a(f'<rect x="{x}" y="{cy}" width="286" height="276" rx="6" fill="white" stroke="#999999" stroke-width="1"/>')
        f.text(x + 143, cy + 18, title, size=15, weight=700, anchor="middle")
        f.text(x + 143, cy + 40, zline, size=13, anchor="middle", fill=BLUE, weight=700)
        f.text(x + 143, cy + 60, grid, size=12, anchor="middle", fill=DARK)
        ax0, ax1 = x + 20, x + 266
        yr2, yi2 = cy + 100, cy + 156
        f.line([(ax0, yr2), (ax1 + 4, yr2)], INK, THIN)
        f.line([(ax0, yi2), (ax1 + 4, yi2)], INK, THIN)
        f.text(ax1 - 20, yr2 - 16, "x thực", size=11.5, fill=DARK, anchor="end")
        f.text(ax1 - 20, yi2 + 16, "x_int", size=11.5, fill=DARK, anchor="end")
        span = ax1 - ax0
        xa, xb = ax0 + a * span, ax0 + b * span
        f.a(f'<rect x="{xa:g}" y="{yr2 - 8}" width="{xb - xa:g}" height="16" fill="#C9D9F2" stroke="{BLUE}" stroke-width="1"/>')
        # zero marker
        xz = ax0 + (zpos if i != 1 else 0.0) * span if i != 1 else xa
        if i == 0:
            xz = (xa + xb) / 2
        if i == 2:
            xz = xa + 0.3 * (xb - xa)
        tick(f, xz, yr2 - 14, yr2 + 14, RED, 2)
        f.text(xz + 4, yr2 + 22, "0 thực", size=11, fill=RED)
        tick(f, xa, yi2 - 8, yi2 + 8, INK, 2)
        tick(f, xb, yi2 - 8, yi2 + 8, INK, 2)
        dotted(f, xa, yr2 + 8, xa, yi2 - 8)
        dotted(f, xb, yr2 + 8, xb, yi2 - 8)
        l0, lz, l1 = labels
        f.text(xa, yi2 + 30, l0, size=11.5, anchor="middle", weight=700)
        f.text(xb, yi2 + 30, l1, size=11.5, anchor="middle", weight=700)
        if i == 0:
            tick(f, xz, yi2 - 8, yi2 + 8, RED, 2)
            f.text(xz, yi2 + 30, "0", size=11.5, anchor="middle", weight=700, fill=RED)
        if i == 2:
            tick(f, xz, yi2 - 8, yi2 + 8, RED, 2)
            dotted(f, xz, yr2 + 14, xz, yi2 - 8, RED)
            f.text(xz, yi2 + 30, "z", size=11.5, anchor="middle", weight=700, fill=RED)
        for j, ln in enumerate(notes):
            f.text(x + 14, cy + 218 + 17 * j, ln, size=12)
    f.text(10, cy + 294, "Hình minh họa khái niệm, không vẽ theo số đo; thanh xanh là range [q_min, q_max] của dữ liệu.",
           size=11.5, fill=DARK, italic=True)

    # ---- D ----
    yd = cy + 318
    hd(f, yd, "D. Chọn kiểu nào cho weight và activation")
    yy = textbox2(f, 10, yd + 14, 480, [
        "Cách chọn thường gặp: weight symmetric, activation asymmetric (NAGEL tr.8);",
        "khuyến nghị này cũng nằm trong pipeline PTQ chuẩn của NAGEL (tr.16).",
        "Lý do (NAGEL tr.8): weight asymmetric nhân activation asymmetric sinh thêm",
        "một số hạng phụ thuộc dữ liệu x_int, phải tính cho mỗi batch (tốn độ trễ và",
        "điện năng); weight symmetric tránh số hạng này.",
        "Đo trên YOLOv5s (bảng phải): activation asymmetric tốt hơn symmetric,",
        "chênh lệch lớn hơn ở 4 bit.",
    ], size=12.5)
    f.text(510, yd + 22, "Q-YOLO Table 2 (tr.9): AP, YOLOv5s, activation", size=12.5, weight=700)
    f.text(510, yd + 40, "(real-valued 37.4; điều kiện Q-YOLO, COCO val2017)", size=12, fill=DARK)
    y2 = f.table(510, yd + 54, [90, 140, 150], ["Bit (W-A)", "Asymmetric", "Symmetric"], [
        ["6-6", "35.9", "34.4"],
        ["4-4", "14.0", "2.7"],
    ], size=12.5)
    y3 = textbox2(f, 510, y2 + 12, 380, [
        [("Liên hệ RKNN (T1):", "b"), (" UG232 tr.120 mô tả linear symmetric", "t")],
        "(zero point của INT8 là 0) và linear asymmetric. Xem Hình 4.1.",
    ], size=12.5, stroke=BLUE)
    y_end = max(yy, y3)
    source(f, y_end + 10, "Nguồn: NAGEL tr.4, 5, 8, 16; GHOLAMI tr.5; QYOLO tr.6, 9; UG232 tr.120. "
           "Ký hiệu NAGEL là chuẩn; GHOLAMI đổi dấu z.")
    return f


# =====================================================================
# Hinh 3.2: do min
# =====================================================================
def fig_granularity():
    f = Fig(W, 1300)
    tier(f)
    hd(f, 20, "A. Một bộ (s, z) cho bao nhiêu phần tử của tensor weight?")
    ranges = [30, 55, 100, 90]          # synthetic half-widths of the four filters (illustration only)
    cards = [
        ("Per-tensor", "cả tensor dùng 1 quantizer", ["NAGEL tr.5: \"This is called", "per-tensor quantization.\"",
                                                      "mọi accumulator cùng scale s_w s_x (tr.5)"]),
        ("Per-channel", "mỗi output channel 1 quantizer", ["NAGEL tr.5: \"per-channel quantization\"", "cho weight (mỗi output channel)",
                                                           "không cần rescale accumulator (tr.8)"]),
        ("Group (sub-channelwise)", "mỗi nhóm channel 1 quantizer", ["độ mịn cao hơn, thêm overhead", "(NAGEL tr.5, GHOLAMI tr.7)",
                                                                     "đa số bộ tăng tốc chưa hỗ trợ (NAGEL tr.5)"]),
    ]
    cy = 34
    for i, (title, sub, notes) in enumerate(cards):
        x = 10 + i * 297
        f.a(f'<rect x="{x}" y="{cy}" width="286" height="262" rx="6" fill="white" stroke="#999999" stroke-width="1"/>')
        f.text(x + 143, cy + 18, title, size=15, weight=700, anchor="middle")
        f.text(x + 143, cy + 38, sub, size=12.5, anchor="middle", fill=BLUE, weight=700)
        c = x + 143
        sc = 0.9
        for j, r in enumerate(ranges):
            yy = cy + 62 + j * 30
            f.text(x + 8, yy, f"F{j + 1}", size=11.5, fill=DARK)
            f.a(f'<rect x="{c - r * sc:g}" y="{yy - 8}" width="{2 * r * sc:g}" height="16" fill="#C9D9F2" stroke="{BLUE}" stroke-width="1"/>')
            tick(f, c, yy - 11, yy + 11, "#888888")
        # quantizer ranges
        if i == 0:
            R = 100 * sc
            f.a(f'<rect x="{c - R:g}" y="{cy + 50}" width="{2 * R:g}" height="{4 * 30 - 4}" fill="none" stroke="{RED}" stroke-width="1.6" stroke-dasharray="5 3"/>')
        elif i == 1:
            for j, r in enumerate(ranges):
                yy = cy + 62 + j * 30
                f.a(f'<rect x="{c - r * sc - 2:g}" y="{yy - 11}" width="{2 * r * sc + 4:g}" height="22" fill="none" stroke="{RED}" stroke-width="1.6" stroke-dasharray="5 3"/>')
        else:
            for (j0, j1, r) in ((0, 1, 55), (2, 3, 100)):
                y0 = cy + 62 + j0 * 30 - 11
                y1 = cy + 62 + j1 * 30 + 11
                f.a(f'<rect x="{c - r * sc - 3:g}" y="{y0}" width="{2 * r * sc + 6:g}" height="{y1 - y0}" fill="none" stroke="{RED}" stroke-width="1.6" stroke-dasharray="5 3"/>')
        for j, ln in enumerate(notes):
            f.text(x + 12, cy + 196 + 18 * j, ln, size=11.5)
    f.text(10, cy + 278, "Thanh xanh: range của filter F1 đến F4; khung đỏ nét đứt: range của quantizer. Range F1 đến F4 là dữ liệu minh họa, không phải số đo; "
           "ý tưởng: GHOLAMI tr.6 (Figure 3).", size=11.5, fill=DARK, italic=True)

    # ---- B: two meanings ----
    yb = cy + 312
    hd(f, yb, "B. \"Channel-wise\" có hai nghĩa")
    gy = yb + 22
    cw, chh = 56, 30

    def grid(x0, mode):
        # rows = output filters, columns = input channels
        for r in range(3):
            f.text(x0 - 6, gy + 22 + r * chh + chh / 2, f"Filter {r + 1}", size=11.5, anchor="end", fill=DARK)
        for cc in range(3):
            f.text(x0 + cc * cw + cw / 2, gy + 10, f"C{cc + 1}", size=11.5, anchor="middle", fill=DARK)
        for r in range(3):
            for cc in range(3):
                fill = "white"
                f.a(f'<rect x="{x0 + cc * cw}" y="{gy + 22 + r * chh}" width="{cw}" height="{chh}" fill="{fill}" stroke="#AAAAAA" stroke-width="1"/>')
        if mode == "row":
            for r in range(3):
                f.a(f'<rect x="{x0 + 1}" y="{gy + 22 + r * chh + 2}" width="{3 * cw - 2}" height="{chh - 4}" fill="#C9D9F2" fill-opacity="0.6" stroke="{BLUE}" stroke-width="1.5"/>')
        else:
            for r in range(3):
                for cc in range(3):
                    f.a(f'<rect x="{x0 + cc * cw + 2}" y="{gy + 22 + r * chh + 2}" width="{cw - 4}" height="{chh - 4}" fill="#C9D9F2" fill-opacity="0.6" stroke="{BLUE}" stroke-width="1.5"/>')
    grid(90, "row")
    f.text(10, gy + 120, "NAGEL tr.5, GHOLAMI tr.7: \"per-channel\" và \"channelwise\"", size=12.5, weight=700)
    f.text(10, gy + 138, "là mỗi output filter (một hàng) một quantizer", size=12.5)
    grid(510, "cell")
    f.text(430, gy + 120, "Y7Q tr.4: \"filter-wise\" là mỗi filter; \"channel-wise\" là mỗi channel", size=12.5, weight=700)
    f.text(430, gy + 138, "của một filter (một ô) có quantizer riêng", size=12.5)
    f.text(10, gy + 162, "Mỗi ô là một lát kernel của một cặp (filter, channel). Y7Q tr.4: nhiều lớp YOLOv7 có kernel 1x1 (một giá trị mỗi ô) không lượng tử hóa được "
           "kiểu channel-wise, nên tỉ lệ tiết kiệm bộ nhớ giảm.", size=11.5, fill=DARK, italic=True)

    # ---- C: numbers ----
    yc = gy + 190
    hd(f, yc, "C. Số đo: per-tensor so với per-channel (điều kiện khác nhau giữa các bảng, không so chéo)")
    f.text(10, yc + 22, "NAGEL Table 1: ImageNet top-1 (%), chỉ lượng tử hóa weight, Min-Max", size=12.5, weight=700)
    f.text(10, yc + 39, "(FP32: ResNet18 69.68, MobileNetV2 71.72; R18 = ResNet18)", size=11.5, fill=DARK)
    t1 = f.table(10, yc + 50, [110, 62, 62, 100, 62], ["Min-Max", "R18 W8", "R18 W4", "MobileNetV2 W8", "W4"], [
        ["per-tensor", "69.57", "0.12", "71.16", "0.59"],
        ["per-channel", "69.60", "44.49", "71.21", "18.40"],
    ], size=12)
    f.text(450, yc + 22, "NAGEL Table 6: EfficientDet-D1, COCO mAP, FP32 40.08", size=12.5, weight=700)
    f.text(450, yc + 39, "(detection nhưng không phải YOLO)", size=11.5, fill=DARK)
    t2 = f.table(450, yc + 50, [110, 110, 110], ["EfficientDet-D1", "per-tensor", "per-channel"], [
        ["W8A8", "38.29", "38.67"],
        ["W4A8", "0.31", "35.08"],
    ], size=12)
    f.text(10, t1 + 14, "per-tensor: hai hàng bài không ghi (Per-channel); suy ra của bộ hình.", size=11, fill=DARK, italic=True)
    y0 = max(t1, t2) + 34
    f.text(10, y0, "Y7Q Table I: YOLOv7, COCO mAP, chỉ lượng tử hóa weight 4 bit, affine uniform; baseline FP16 mAP 0.691", size=12.5, weight=700)
    t3 = f.table(10, y0 + 12, [200, 100, 200, 380],
                 ["Granularity (Y7Q)", "mAP", "Tiết kiệm bộ nhớ", "Ghi chú"], [
                     ["filter-wise", "0.491", "~3.97x", ""],
                     ["channel-wise", "0.621", "~1.68x", "nhiều lớp YOLOv7 có kernel 1x1 không lượng tử hóa được kiểu này"],
                     ["C-shape-wise", "0.657", "~3.93x", ""],
                     ["F-shape-wise", "0.635", "~3.93x", ""],
                 ], size=12)
    f.text(10, t3 + 16, "Y7Q chỉ lượng tử hóa weight 4 bit: không dùng để bác bỏ per-channel kiểu NAGEL ở INT8.",
           size=12, fill=DARK, italic=True)

    # ---- D: RK3588 ----
    yd = t3 + 36
    hd(f, yd, "D. Liên hệ RK3588 (T1) và lý do phần cứng")
    y1 = textbox2(f, 10, yd + 14, 430, [
        [("Liên hệ RK3588 (T1):", "b")],
        "UG232 tr.120: \"In RKNN-Toolkit2, Per-Channel quantization is only",
        "applied to the weights\"; activation vẫn per-layer. Xem Hình 4.1.",
    ], size=12.5, stroke=BLUE)
    y2 = textbox2(f, 460, yd + 14, 430, [
        [("Vì sao activation khó per-channel (T2)", "b")],
        "NAGEL tr.8: không tách được scale ra khỏi tổng, phải rescale accumulator",
        "cho mỗi input channel; không phải phần cứng nào cũng hỗ trợ per-channel weight.",
    ], size=12.5)
    source(f, max(y1, y2) + 10, "Nguồn: NAGEL tr.5, 8, 9 (Table 1), 17 (Table 6); GHOLAMI tr.6, 7; Y7Q tr.3, 4; UG232 tr.120.")
    return f

# =====================================================================
# Hinh 3.3: clipping vs rounding, range setting
# =====================================================================
def fig_clipping():
    f = Fig(W, 1300)
    tier(f)
    hd(f, 20, "A. Hai loại sai số của một quantizer và vì sao range quyết định đánh đổi")
    # ---- panel (a): synthetic curves ----
    f.text(10, 48, "(a) Sai số theo độ rộng range [q_min, q_max]", size=13, weight=700)
    x0, x1, y0, y1 = 70, 410, 250, 80          # plot area: x range, y (bottom, top)
    f.line([(x0, y0), (x1 + 20, y0)], INK, THIN)
    f.line([(x0, y0), (x0, y1 - 10)], INK, THIN)
    f.text(x0 + 6, y1 - 12, "sai số", size=12, fill=DARK)
    f.text((x0 + x1) / 2, y0 + 20, "độ rộng range (bước s tăng theo range)", size=12, anchor="middle", fill=DARK)
    n = 80

    def clip(t):
        return 0.95 * (math.exp(-5.5 * t) - math.exp(-5.5)) / (1 - math.exp(-5.5))

    def rnd(t):
        return 0.8 * t

    def px(t, e):
        return x0 + 8 + t * (x1 - x0 - 8), y0 - e * (y0 - y1)

    def path(fn):
        return "M" + " L".join("%.1f %.1f" % px(i / n, fn(i / n)) for i in range(n + 1))

    ts = [i / 400 for i in range(401)]
    tstar = min(ts, key=lambda t: clip(t) + rnd(t))
    f.a(f'<path d="{path(clip)}" fill="none" stroke="{RED}" stroke-width="2.4"/>')
    f.a(f'<path d="{path(rnd)}" fill="none" stroke="{BLUE}" stroke-width="2.4"/>')
    f.a(f'<path d="{path(lambda t: clip(t) + rnd(t))}" fill="none" stroke="{INK}" stroke-width="1.6" stroke-dasharray="6 4"/>')
    xs, _ = px(tstar, 0)
    f.a(f'<path d="M{xs:.1f} {y0} L{xs:.1f} {y1 - 6}" stroke="{GREEN}" stroke-width="1.4" stroke-dasharray="3 3"/>')
    xm, _ = px(1.0, 0)
    f.a(f'<path d="M{xm:.1f} {y0} L{xm:.1f} {y1 - 6}" stroke="{GRAY}" stroke-width="1.4" stroke-dasharray="3 3"/>')
    f.text(xs + 6, y1 - 2, "MSE chọn range ở đây", size=11.5, fill=GREEN, weight=700, halo="white")
    f.text(xm - 6, y1 - 2, "min-max", size=11.5, fill=DARK, weight=700, anchor="end", halo="white")
    f.text(90, 100, "sai số clipping giảm", size=11.5, fill=RED, weight=700, halo="white")
    f.text(268, 205, "sai số làm tròn tăng (theo s)", size=11.5, fill=BLUE, weight=700, halo="white")
    f.text(190, 205, "tổng (suy ra)", size=11.5, fill=INK, halo="white")
    f.text(10, 296, "dữ liệu minh họa, không phải số đo", size=12, fill=RED, italic=True)
    # ---- panel (b): outlier distribution ----
    f.text(460, 48, "(b) Phân bố có outlier: cùng số mức, range khác nhau", size=13, weight=700)

    def bx(v):
        return 470 + (v + 5) / 15 * 410

    base = 190
    f.line([(465, base), (890, base)], INK, THIN)
    pts = []
    for i in range(0, 91):
        v = -4.5 + i * 9.0 / 90
        pts.append((bx(v), base - 100 * math.exp(-0.5 * (v / 1.2) ** 2)))
    d = "M" + " L".join("%.1f %.1f" % p for p in pts)
    f.a(f'<path d="{d} L{bx(4.5):.1f} {base} L{bx(-4.5):.1f} {base} Z" fill="#C9D9F2" stroke="{BLUE}" stroke-width="1.2"/>')
    f.a(f'<rect x="{bx(9) - 2:.1f}" y="{base - 26}" width="4" height="26" fill="{BLUE}"/>')
    f.text(bx(9), base - 38, "outlier", size=12, anchor="middle", fill=RED, weight=700)
    f.text(bx(0), base - 108, "đa số giá trị", size=12, anchor="middle", fill=DARK)
    levels = 17

    def ruler(lo, hi, y, color):
        f.a(f'<path d="M{bx(lo):.1f} {y} L{bx(hi):.1f} {y}" stroke="{color}" stroke-width="1.6"/>')
        for i in range(levels):
            xx = bx(lo) + i * (bx(hi) - bx(lo)) / (levels - 1)
            tick(f, xx, y - 6, y + 6, color, 1.4)

    ruler(-3.6, 9.0, 216, GRAY)
    f.text(470, 238, "min-max: range phủ cả outlier, bước s lớn", size=12, fill=DARK, weight=700)
    ruler(-3.6, 3.8, 258, GREEN)
    f.text(470, 280, "MSE: range hẹp hơn, outlier bị clip, bước s nhỏ", size=12, fill=GREEN, weight=700)
    f.text(460, 298, "dữ liệu minh họa, không phải số đo; số mức bằng nhau vì cùng bit-width (suy ra của bộ hình)",
           size=11.5, fill=RED, italic=True)
    y = textbox2(f, 10, 312, 880, [
        "Hình dạng hai đường cong (a) theo NAGEL tr.4: mở rộng range bằng cách tăng s giảm sai số clipping nhưng tăng sai số làm tròn (nằm trong [-s/2, s/2]).",
        "Min-max: không clipping error, nhưng outlier mạnh gây sai số làm tròn quá mức (NAGEL tr.9). MSE (Eq. 16) tối thiểu hóa sai số giữa tensor gốc và đã lượng tử hóa.",
    ], size=12)

    # ---- B: methods ----
    yb = y + 22
    hd(f, yb, "B. Các cách chọn range, theo tên trong từng nguồn")
    L = lambda *a: ("lines", list(a))   # noqa: E731
    y = f.table(10, yb + 14, [112, 330, 150, 288], ["Phương pháp", "Công thức hoặc ý chính", "Nguồn", "Điều nguồn nói"], [
        ["Min-max", L("q_min = min V; q_max = max V (Eq. 14, 15)"), "NAGEL tr.9; QYOLO tr.6", L("không có clipping error;", "nhạy với outlier")],
        ["MSE", L("argmin ||V - V^(q_min, q_max)||_F^2 (Eq. 16)", "grid search, golden section hoặc giải tích"), "NAGEL tr.9; QYOLO tr.6",
         L("giảm ảnh hưởng của outlier lớn", "(QYOLO Eq. 7 cùng ý)")],
        ["Cross-entropy", L("argmin H(ψ(v), ψ(v^)) (Eq. 17)", "ψ = softmax, v = logits lớp cuối"), "NAGEL tr.10",
         L("giữ thứ tự giá trị lớn nhất;", "MSE coi mọi giá trị như nhau")],
        ["BN-based", L("q_min = min(β - α γ),", "q_max = max(β + α γ), α = 6 (Eq. 18, 19)"), "NAGEL tr.10, 16",
         L("dùng tham số BN; pipeline", "data-free (tr.16)")],
        ["Percentile", L("dùng phân vị thay cho min/max", "(giá trị lớn/nhỏ thứ i làm β/α)"), "GHOLAMI tr.6",
         L("tránh outlier làm tăng range", "và giảm độ phân giải")],
        ["KL divergence", L("chọn α, β để cực tiểu KL divergence", "giữa giá trị thực và đã lượng tử hóa"), "GHOLAMI tr.6",
         L("nguồn gọi là \"information loss\";", "NAGEL không nêu KL (unknown)")],
        ["UH (Q-YOLO)", L("l_x = -0.2785 cố định; u_x = argmin MSE(x, Q)", "histogram 2048 bin, asymmetric"), "QYOLO tr.7",
         L("cho activation của YOLO trong bài", "(YOLOv5, YOLOv7)")],
    ], size=12)

    # ---- C: numbers ----
    yc = y + 24
    hd(f, yc, "C. Số đo của NAGEL: min-max so với MSE (ImageNet top-1 %, trung bình 5 lần, phân loại ảnh, không phải detection)")
    f.text(10, yc + 24, "Table 1: weight symmetric, per-tensor, activation FP32", size=12.5, weight=700)
    f.text(10, yc + 41, "(FP32: ResNet18 69.68, MobileNetV2 71.72; R18 = ResNet18)", size=11.5, fill=DARK)
    t1 = f.table(10, yc + 52, [100, 62, 62, 100, 62], ["Weight", "R18 W8", "R18 W4", "MobileNetV2 W8", "W4"], [
        ["Min-Max", "69.57", "0.12", "71.16", "0.59"],
        ["MSE", "69.45", "18.82", "71.15", "13.77"],
    ], size=12)
    f.text(450, yc + 24, "Table 2: activation asymmetric, weight FP32", size=12.5, weight=700)
    f.text(450, yc + 41, "(MSE + Xent: cross-entropy cho lớp cuối)", size=11.5, fill=DARK)
    t2 = f.table(450, yc + 52, [112, 62, 62, 100, 62], ["Activation", "R18 A8", "R18 A4", "MobileNetV2 A8", "A4"], [
        ["Min-Max", "69.60", "18.82", "70.96", "0.53"],
        ["MSE", "69.59", "31.40", "71.35", "13.57"],
        ["MSE + Xent", "69.60", "59.07", "71.36", "30.94"],
        ["BN (α = 6)", "69.54", "23.83", "71.32", "0.66"],
    ], size=12)

    f.text(10, t1 + 14, "per-tensor: hai hàng bài không ghi (Per-channel); suy ra của bộ hình.", size=11, fill=DARK, italic=True)
    # ---- D ----
    yd = max(t1, t2) + 24
    hd(f, yd, "D. Dữ liệu calibration và liên hệ RKNN")
    y1 = textbox2(f, 10, yd + 14, 430, [
        [("Dữ liệu (T2)", "b")],
        "Weight thường không cần dữ liệu calibration; activation thường",
        "cần vài batch (NAGEL tr.9). AdaRound dùng dữ liệu cho weight (tr.16).",
        "500 đến 1000 ảnh không nhãn: khuyến nghị của NAGEL tr.16;",
        "Q-YOLO dùng 1500 ảnh COCO train2017 (tr.8). Đều là điều kiện",
        "thí nghiệm, không phải quy tắc chung.",
    ], size=12)
    y2 = textbox2(f, 460, yd + 14, 430, [
        [("Liên hệ RKNN (T1)", "b")],
        "UG232 tr.120, 121 có ba algorithm: Normal, KL-Divergence, MMSE.",
        "Normal \"does not introduce truncation error\" nhưng nhạy outlier",
        "(cùng ý min-max); MMSE giảm ảnh hưởng outlier (cùng ý MSE).",
        "Tương ứng tên là suy ra của bộ hình. Xem Hình 4.1.",
    ], size=12, stroke=BLUE)
    source(f, max(y1, y2) + 10, "Nguồn: NAGEL tr.4, 9, 10, 16; GHOLAMI tr.6; QYOLO tr.4, 6, 7, 8; UG232 tr.120, 121. "
           "Đường cong (a) và phân bố (b) là minh họa.")
    return f

# =====================================================================
# Hinh 3.4: int8 arithmetic
# =====================================================================
def fig_int8():
    f = Fig(W, 1300)
    tier(f)
    hd(f, 20, "A. Nhân ma trận số nguyên: INT8 x INT8, cộng dồn vào INT32, rồi requantization (NAGEL Figure 2)")
    rbox(f, 10, 52, 150, 48, ["Weight W_int", "INT8"], size=13)
    rbox(f, 10, 128, 150, 48, ["Input x_int", "INT8"], size=13)
    rbox(f, 215, 88, 130, 52, ["MAC", "INT8 x INT8"], size=13)
    rbox(f, 400, 88, 160, 52, ["Accumulator", "INT32"], size=13, fill=LAYER)
    rbox(f, 400, 36, 160, 36, ["Bias b^", "32-bit"], size=12)
    rbox(f, 615, 88, 130, 52, ["Requantization"], size=13)
    rbox(f, 790, 88, 100, 52, ["Memory", "INT8"], size=13)
    f.line([(160, 76), (215, 104)], BLUE, THIN)
    f.line([(160, 152), (215, 124)], BLUE, THIN)
    f.line([(345, 114), (400, 114)], BLUE, THIN)
    f.line([(480, 72), (480, 88)], BLUE, THIN)
    f.line([(560, 114), (615, 114)], BLUE, THIN)
    f.line([(745, 114), (790, 114)], BLUE, THIN)
    f.text(480, 156, "tích lũy các tích INT8", size=11.5, anchor="middle", fill=DARK)
    f.text(680, 156, "đưa về INT8 cho lớp sau", size=11.5, anchor="middle", fill=DARK)
    y = textbox2(f, 10, 190, 880, [
        [("A^_n = b^_n + s_w s_x  Sum_m  W_int[n,m] x_int[m]", "c"), ("   (Eq. 3)", "t")],
        "Scale s_w và s_x áp cho cả tensor nên tách được ra khỏi tổng, phép MAC chạy hoàn toàn trên số nguyên (NAGEL tr.3).",
        "Accumulator cần rộng hơn (thường 32 bit), nếu không có nguy cơ tràn số khi cộng dồn nhiều tích; bias thường lưu 32 bit (NAGEL tr.3).",
        "Activation 32 bit phải ghi ra bộ nhớ rồi lớp sau đọc lại, nên lượng tử hóa ngược về INT8 bằng bước requantization (NAGEL tr.3).",
        "Vị trí của accumulator trong một core NPU RK3588: Hình 2.2.",
    ], size=12)

    # ---- B: BN folding ----
    yb = y + 22
    hd(f, yb, "B. Gộp BN vào lớp liền trước (BN folding)")
    r1 = yb + 30
    rbox(f, 10, r1, 110, 40, ["Conv"], size=13)
    rbox(f, 150, r1, 150, 40, ["BatchNorm"], size=13)
    rbox(f, 330, r1, 90, 40, ["Act"], size=13)
    f.line([(120, r1 + 20), (150, r1 + 20)], BLUE, THIN)
    f.line([(300, r1 + 20), (330, r1 + 20)], BLUE, THIN)
    f.text(185, r1 + 58, "γ, β, μ, σ cố định lúc suy luận", size=11.5, anchor="middle", fill=DARK)
    f.line([(215, r1 + 70), (215, r1 + 98)], INK, THIN)
    f.text(228, r1 + 84, "gộp", size=12, fill=DARK)
    r2 = r1 + 106
    rbox(f, 10, r2, 200, 40, ["Conv với W~, b~"], size=13)
    rbox(f, 240, r2, 90, 40, ["Act"], size=13)
    f.line([(210, r2 + 20), (240, r2 + 20)], BLUE, THIN)
    yy = textbox2(f, 10, r2 + 52, 430, [
        [("W~[k,:] = γ_k W[k,:] / sqrt(σ_k^2 + ε)   (Eq. 11)", "c")],
        [("b~_k = β_k - γ_k μ_k / sqrt(σ_k^2 + ε)   (Eq. 12)", "c")],
        "Loại hẳn phép BN khỏi mạng; tránh thêm chuyển dữ liệu và",
        "lượng tử hóa đầu ra của lớp (NAGEL tr.6, 7).",
    ], size=12)

    # ---- C: activation fusing ----
    f.text(460, yb, "C. Activation đi cùng requantization", size=15, weight=700)
    c1 = yb + 30
    f.text(460, c1, "Có đơn vị áp non-linearity trước requantization", size=12.5, weight=700)
    rbox(f, 460, c1 + 12, 90, 36, ["Conv"], size=12.5)
    rbox(f, 575, c1 + 12, 90, 36, ["ReLU"], size=12.5)
    rbox(f, 690, c1 + 12, 120, 36, ["Requantize"], size=12.5)
    f.line([(550, c1 + 30), (575, c1 + 30)], BLUE, THIN)
    f.line([(665, c1 + 30), (690, c1 + 30)], BLUE, THIN)
    f.text(460, c1 + 64, "chỉ cần mô phỏng requantization sau non-linearity; ReLU: đặt giá trị", size=11.5, fill=DARK)
    f.text(460, c1 + 81, "nhỏ nhất của activation quantizer bằng 0 (NAGEL tr.7)", size=11.5, fill=DARK)
    c2 = c1 + 104
    f.text(460, c2, "Sigmoid, Swish, không có hỗ trợ riêng", size=12.5, weight=700)
    rbox(f, 460, c2 + 12, 80, 36, ["Conv"], size=12.5)
    rbox(f, 560, c2 + 12, 90, 36, ["Quantize"], size=12.5, fill="#FFF8E5")
    rbox(f, 670, c2 + 12, 70, 36, ["Act"], size=12.5)
    rbox(f, 760, c2 + 12, 90, 36, ["Quantize"], size=12.5, fill="#FFF8E5")
    for xa, xb_ in ((540, 560), (650, 670), (740, 760)):
        f.line([(xa, c2 + 30), (xb_, c2 + 30)], BLUE, THIN)
    f.text(460, c2 + 64, "thêm bước quantize trước và sau non-linearity; có thể ảnh hưởng lớn tới độ", size=11.5, fill=DARK)
    f.text(460, c2 + 81, "chính xác của model lượng tử hóa (NAGEL tr.7)", size=11.5, fill=DARK)
    yq = textbox2(f, 460, c2 + 96, 430, [
        [("SiLU và sụt độ chính xác (QYOLO tr.7):", "b")],
        "tác giả viết hiện tượng \"can be attributed to\" việc dùng SiLU; đây là",
        "quan sát của tác giả, không phải chứng minh.",
    ], size=12, stroke=RED, dash=True)

    # ---- D: add, concat, pooling ----
    yd = max(yy, yq) + 22
    hd(f, yd, "D. Các lớp khác: cộng, concat, pooling (NAGEL tr.7, 8)")
    L = lambda *a: ("lines", list(a))   # noqa: E731
    yt = f.table(10, yd + 14, [135, 300, 435], ["Lớp", "Điều NAGEL nói", "Cần làm"], [
        ["Max pooling", L("input và output cùng một lưới lượng tử"), L("không cần lượng tử hóa activation")],
        ["Average pooling", L("trung bình của các số nguyên chưa chắc là số nguyên"),
         L("cần một bước quantize sau pooling, dùng chung quantizer cho input và output")],
        ["Element-wise addition", L("range của hai đầu vào phải khớp chính xác"),
         L("thêm bước requantization (mô phỏng thô), hoặc buộc chung lưới", "(có thể cần fine-tune)")],
        ["Concatenation", L("hai nhánh thường không chung tham số,", "lưới có thể không chồng nhau"),
         L("cần requantization; cũng có thể tối ưu mạng để hai nhánh chung tham số")],
    ], size=12)
    # ruler sketch for add
    ys = yt + 22
    f.text(10, ys, "Minh họa phép cộng: hai đầu vào khác lưới", size=12.5, weight=700)
    f.text(10, ys + 16, "(lưới vẽ theo ý tưởng, không theo số đo)", size=11.5, fill=RED, italic=True)

    def ruler(x0, y, step, n, color, label):
        f.a(f'<path d="M{x0} {y} L{x0 + step * n} {y}" stroke="{color}" stroke-width="1.6"/>')
        for i in range(n + 1):
            tick(f, x0 + i * step, y - 6, y + 6, color, 1.4)
        f.text(x0 + step * n + 12, y, label, size=12, fill=color)

    ruler(300, ys + 4, 12, 16, BLUE, "đầu vào 1 (scale s1)")
    ruler(300, ys + 32, 17, 11, GREEN, "đầu vào 2 (scale s2)")
    f.line([(400, ys + 44), (400, ys + 66)], INK, THIN)
    f.text(412, ys + 56, "requantization về lưới chung rồi mới cộng", size=12, fill=DARK)
    ruler(300, ys + 80, 12, 16, DARK, "lưới chung")
    yu = f.unknown(10, ys + 112, [
        "Add và Concat của YOLOv8 (C2f, SPPF...) và mức sụt độ chính xác của chúng: không nguồn nào trong bộ có số cho YOLOv8,",
        "nguồn chỉ nêu nguyên tắc; mọi nhận định về lượng tử hóa YOLOv8 là unknown. Fusion trên RKNN: Hình 6.3."], w=880, size=12)
    source(f, yu + 10, "Nguồn: NAGEL tr.3, 4 (Figure 2), 6, 7, 8; QYOLO tr.7. Hình khối và lưới là minh họa khái niệm.")
    return f

# =====================================================================
# Hinh 3.5: PTQ, QAT, simulated quantization, STE, debug flowchart
# =====================================================================
TURQ = "#BFE6EC"


def fig_ptq_qat():
    f = Fig(W, 2200)
    tier(f)
    hd(f, 20, "A. PTQ và QAT: hai quy trình (GHOLAMI Figure 4)")

    def flow(x0, title, names, data_name, data_idx, notes):
        f.a(f'<rect x="{x0}" y="34" width="435" height="214" rx="6" fill="white" stroke="#999999" stroke-width="1"/>')
        f.text(x0 + 217, 52, title, size=14.5, weight=700, anchor="middle")
        bw, gap = 92, 17
        for i, nm in enumerate(names):
            bx_ = x0 + 12 + i * (bw + gap)
            rbox(f, bx_, 70, bw, 42, nm, size=11.5, fill=("#EAF1FB" if i in (data_idx,) else "white"))
            if i:
                f.line([(bx_ - gap, 91), (bx_, 91)], BLUE, THIN)
        dx = x0 + 12 + data_idx * (bw + gap)
        rbox(f, dx, 134, bw, 30, [data_name], size=11, fill="#F5F5F5", bold_first=False)
        f.line([(dx + bw / 2, 134), (dx + bw / 2, 112)], GRAY, THIN, dashed=True)
        for j, ln in enumerate(notes):
            f.text(x0 + 12, 184 + 16 * j, ln, size=11.5)

    flow(10, "PTQ", [["Pre-trained", "model"], ["Calibration"], ["Quantization"], ["Quantized", "model"]],
         "Calibration data", 1,
         ["không cần pipeline train gốc (NAGEL tr.8)",
          "activation thường cần vài batch dữ liệu (NAGEL tr.9)",
          "khuyến nghị 500 đến 1000 ảnh không nhãn (NAGEL tr.16)",
          "hạn chế khi lượng tử hóa activation 4 bit trở xuống (tr.19)"])
    flow(455, "QAT", [["Pre-trained", "model"], ["Quantization"], ["Retraining /", "Finetuning"], ["Quantized", "model"]],
         "Training data", 2,
         ["mô hình hóa nhiễu lượng tử khi train, tìm nghiệm tốt hơn PTQ",
          "đổi lại: train lâu hơn, cần dữ liệu có nhãn, tìm siêu tham số",
          "(NAGEL tr.19)",
          "khởi tạo từ model pretrained và các bước PTQ để hội tụ nhanh (tr.23)"])

    # ---- B: simulated quantization + STE ----
    yb = 272
    hd(f, yb, "B. Simulated quantization và STE (NAGEL Figure 4b, Figure 10)")
    rbox(f, 10, yb + 24, 64, 30, ["Weights"], size=11.5)
    rbox(f, 10, yb + 70, 64, 30, ["Input"], size=11.5)
    rbox(f, 10, yb + 116, 64, 30, ["Biases"], size=11.5)
    rbox(f, 96, yb + 24, 70, 30, ["Quantizer"], size=11.5, fill="#FFF8E5")
    rbox(f, 200, yb + 64, 80, 44, ["Conv"], size=13)
    rbox(f, 310, yb + 70, 70, 32, ["Activation"], size=11.5)
    rbox(f, 410, yb + 70, 70, 32, ["Quantizer"], size=11.5, fill="#FFF8E5")
    rbox(f, 500, yb + 70, 60, 32, ["Output"], size=11.5)
    f.line([(74, yb + 39), (96, yb + 39)], BLUE, THIN)
    f.line([(166, yb + 39), (225, yb + 64)], BLUE, THIN)
    f.line([(74, yb + 85), (200, yb + 86)], BLUE, THIN)
    f.line([(74, yb + 131), (230, yb + 108)], BLUE, THIN)
    f.line([(280, yb + 86), (310, yb + 86)], BLUE, THIN)
    f.line([(380, yb + 86), (410, yb + 86)], BLUE, THIN)
    f.line([(480, yb + 86), (500, yb + 86)], BLUE, THIN)
    # backward path
    f.a(f'<path d="M530 {yb + 102} L530 {yb + 150} L240 {yb + 150} L240 {yb + 112}" fill="none" stroke="{GRAY}" '
        f'stroke-width="1.6" stroke-dasharray="5 4" marker-end="url(#{f.marker(GRAY, THIN)})"/>')
    f.text(250, yb + 138, "backward: gradient bỏ qua Quantizer (STE)", size=11.5, fill=DARK)
    yy = textbox2(f, 10, yb + 166, 550, [
        "Quantizer đặt giữa weight và Conv, và sau Activation; bias thường không lượng tử hóa (NAGEL tr.6).",
        "Vào và ra của Quantizer đều là số float, nhưng ra nằm trên lưới lượng tử (NAGEL tr.6).",
        [("STE: d round(y) / dy = 1 (Eq. 36)", "c")],
        [("d x^/dx = 1 nếu q_min <= x <= q_max, ngược lại 0 (Eq. 37)", "c")],
        "Đạo hàm của làm tròn bằng 0 hoặc không xác định, nên không train được nếu thiếu STE (NAGEL tr.19).",
    ], size=11.5, lh=17)
    f.text(580, yb + 8, "\"Simulated quantization\" có hai nghĩa", size=13.5, weight=700)
    ya = textbox2(f, 580, yb + 18, 310, [
        [("NAGEL tr.6: công cụ mô phỏng", "b")],
        "chạy phép tính float với khối",
        "Quantizer để thử lượng tử hóa và",
        "tăng tốc QAT trên GPU.",
    ], size=11.5, lh=16)
    yg = textbox2(f, 580, ya + 8, 310, [
        [("GHOLAMI tr.12: kiểu triển khai", "b")],
        "tham số lưu bit thấp nhưng phép",
        "tính float, phải dequantize trước",
        "phép tính; khác integer-only (mọi",
        "phép tính bằng số nguyên).",
    ], size=11.5, lh=16)
    f.text(580, yg + 14, "Khuyến nghị của bộ hình: khi viết, nói rõ đang dùng nghĩa nào.", size=11.5, fill=DARK, italic=True)

    # ---- C: standard PTQ pipeline ----
    yc = max(yy, yg + 28) + 18
    hd(f, yc, "C. Quy trình PTQ chuẩn của NAGEL (Figure 8; hộp xanh là bước bắt buộc, hộp ngọc là lựa chọn khuyến nghị)")
    y0 = yc + 18
    cy = y0 + 76
    BLU = "#DDE6F3"
    rbox(f, 10, cy - 22, 110, 44, ["Pre-trained", "FP Model"], size=12, fill=BLU)
    rbox(f, 138, cy - 22, 62, 44, ["CLE"], size=12, fill=BLU)
    rbox(f, 218, cy - 22, 120, 44, ["Add", "Quantizers"], size=12, fill=BLU)
    rbox(f, 356, cy - 22, 120, 44, ["Weight Range", "Setting"], size=12, fill=BLU)
    diamond(f, 540, cy, 100, 60, "Use Data?", size=11.5, fill="#C5D2E6")
    rbox(f, 610, cy - 48, 110, 36, ["AdaRound"], size=12, fill=BLU)
    rbox(f, 610, cy + 12, 110, 36, ["Bias", "Correction"], size=12, fill=BLU)
    rbox(f, 765, cy - 22, 125, 44, ["Activation Range", "Setting"], size=12, fill=BLU)
    for a_, b_ in ((120, 138), (200, 218), (338, 356), (476, 490)):
        f.line([(a_, cy), (b_, cy)], BLUE, THIN)
    f.line([(588, cy - 14), (610, cy - 30)], BLUE, THIN)
    f.line([(588, cy + 14), (610, cy + 30)], BLUE, THIN)
    f.line([(720, cy - 30), (765, cy - 8)], BLUE, THIN)
    f.line([(720, cy + 30), (765, cy + 8)], BLUE, THIN)
    f.text(578, cy - 44, "Yes", size=11.5, fill=DARK)
    f.text(578, cy + 48, "No", size=11.5, fill=DARK)
    chip = lambda x, y, w, t: rbox(f, x, y, w, 24, [t], size=11, fill=TURQ, bold_first=False, rx=8)   # noqa: E731
    chip(224, y0 + 2, 108, "Symmetric Weights")
    f.line([(278, y0 + 26), (278, cy - 22)], GRAY, THIN)
    chip(212, cy + 40, 132, "Asymmetric Activations")
    f.line([(278, cy + 40), (278, cy + 22)], GRAY, THIN)
    chip(362, y0 + 2, 108, "MSE Range Setting")
    f.line([(416, y0 + 26), (416, cy - 22)], GRAY, THIN)
    chip(771, y0 + 2, 108, "MSE Range Setting")
    f.line([(825, y0 + 26), (825, cy - 22)], GRAY, THIN)

    # cards: CLE, bias correction, AdaRound, QAREP
    yk = cy + 78
    cards = [
        ("CLE (NAGEL tr.10 đến 12)", [
            "cân bằng dynamic range giữa", "các lớp liên tiếp nhờ f(sx) = s f(x)",
            "của ReLU (Eq. 20); MobileNetV2", "INT8: 0.12 -> 69.91 (Table 3)",
            "ImageNet top-1, FP32 71.72"], BLUE),
        ("Bias correction (tr.12 đến 14)", [
            "sai số lượng tử hóa thường lệch;", "trừ ΔW E[x] vào bias, không tốn",
            "thêm khi suy luận (Eq. 26);", "MobileNetV2 INT8: 0.12 -> 52.02",
            "(Table 4)"], BLUE),
        ("AdaRound (tr.13 đến 15)", [
            "làm tròn gần nhất chưa tối ưu cho", "task loss; AdaRound tối ưu cách làm",
            "tròn weight bằng ít dữ liệu không", "nhãn. ResNet18, mọi lớp: nearest",
            "23.99, AdaRound 68.60 (Table 5)"], BLUE),
        ("Model re-param (QAREP tr.1, 6, 7)", [
            "PTQ không đều: RepVGG-A0 72.4 ->", "52.2 INT8 (8-bit symmetric);",
            "YOLOv6s-RepVGG 42.4 -> 35.0 mAP", "(Table 8). Xem Hình 8.1."], RED),
    ]
    for i, (t, ls, col) in enumerate(cards):
        x = 10 + i * 222
        f.a(f'<rect x="{x}" y="{yk}" width="212" height="132" rx="6" fill="white" stroke="{col}" stroke-width="1.2"/>')
        f.text(x + 8, yk + 14, t, size=12, weight=700)
        for j, ln in enumerate(ls):
            f.text(x + 8, yk + 36 + 16 * j, ln, size=11.5)

    # ---- D: debug flowchart ----
    yd = yk + 152
    hd(f, yd, "D. Lưu đồ debug PTQ (NAGEL Figure 9) và hình gốc")
    fy = yd + 26

    def node(cx, cyy, w, h, label, fill="#DDE6F3", size=11.5):
        rbox(f, cx - w / 2, fyy(cyy) - h / 2, w, h, [label], size=size, fill=fill)

    def fyy(v):
        return fy + v

    def dia(cx, cyy, label="error < ε"):
        diamond(f, cx, fyy(cyy), 118, 46, label, size=11)

    def ln(pts, color=INK, dashed=False, head=True):
        f.line([(a, fyy(b)) for a, b in pts], color, THIN, dashed, head)

    cx, rx_ = 190, 470
    node(cx, 16, 130, 28, "Quantized Model", TURQ)
    node(cx, 64, 150, 28, "Set b_W = b_A = 32")
    dia(cx, 122, "error ≈ 0")
    node(rx_, 122, 100, 28, "Fix Model")
    ln([(cx, 30), (cx, 50)]); ln([(cx, 78), (cx, 99)])
    ln([(cx + 59, 122), (rx_ - 50, 122)]); f.text(cx + 66, fyy(114), "NO", size=10.5, fill=DARK)
    ln([(rx_, 108), (rx_, 16), (cx + 65, 16)])
    f.text(cx + 8, fyy(150), "YES", size=10.5, fill=DARK)
    # outer frame
    f.a(f'<rect x="20" y="{fyy(170)}" width="360" height="650" rx="6" fill="none" stroke="#888888" stroke-dasharray="6 4"/>')
    f.text(28, fyy(184), "for X ∈ {Activations, Weights}", size=11.5, fill=DARK, italic=True)
    ln([(cx, 145), (cx, 200)])
    node(cx, 215, 180, 28, "Quantize all tensors in X")
    ln([(cx, 229), (cx, 252)])
    dia(cx, 275)
    ln([(cx - 59, 275), (34, 275), (34, 198)]); f.text(70, fyy(267), "YES", size=10.5, fill=DARK)
    ln([(cx, 298), (cx, 320)]); f.text(cx + 6, fyy(309), "NO", size=10.5, fill=DARK)
    node(cx, 335, 120, 28, "Fix problem")
    f.text(42, fyy(300), "Activations", size=11, weight=700)
    f.text(268, fyy(296), "Weights", size=11, weight=700)
    for k, t in enumerate(["Range Setting", "Adjust CLE"]):
        rbox(f, 42, fyy(312 + 28 * k), 84, 22, [t], size=10.5, fill="#F5F5F5", bold_first=False, rx=6)
    for k, t in enumerate(["AdaRound", "Per channel", "CLE", "Bias correction"]):
        rbox(f, 266, fyy(306 + 26 * k), 100, 22, [t], size=10.5, fill="#F5F5F5", bold_first=False, rx=6)
    ln([(cx, 349), (cx, 407)])
    dia(cx, 430)
    ln([(cx - 59, 430), (34, 430), (34, 275)], head=False); f.text(70, fyy(422), "YES", size=10.5, fill=DARK)
    ln([(cx, 453), (cx, 500)]); f.text(cx + 6, fyy(464), "NO", size=10.5, fill=DARK)
    # inner frame
    f.a(f'<rect x="60" y="{fyy(470)}" width="270" height="330" rx="6" fill="#EEF1F6" stroke="#888888" stroke-dasharray="6 4"/>')
    f.text(68, fyy(484), "for layer l = 0, ..., L", size=11.5, fill=DARK, italic=True)
    node(cx, 520, 150, 28, "Set b_W = b_A = 32")
    node(cx, 566, 160, 28, "Quantize tensor Z(l)")
    ln([(cx, 534), (cx, 552)]); ln([(cx, 580), (cx, 597)])
    dia(cx, 620)
    ln([(cx - 59, 620), (74, 620), (74, 504)]); f.text(100, fyy(612), "YES", size=10.5, fill=DARK)
    ln([(cx, 643), (cx, 654)]); f.text(cx + 6, fyy(648), "NO", size=10.5, fill=DARK)
    node(cx, 668, 160, 28, "Visualize tensor Z(l)")
    node(cx, 708, 170, 28, "Fix problem in Z(l)")
    ln([(cx, 682), (cx, 694)]); ln([(cx, 722), (cx, 737)])
    dia(cx, 760)
    ln([(cx - 59, 760), (74, 760), (74, 620)], head=False)
    f.text(100, fyy(752), "YES", size=10.5, fill=DARK)
    ln([(60, 790), (34, 790), (34, 430)], head=False); f.text(38, fyy(802), "END", size=10.5, fill=DARK)
    f.text(cx + 6, fyy(792), "NO", size=10.5, fill=DARK)
    node(cx, 860, 80, 28, "QAT")
    ln([(cx, 783), (cx, 846)])
    ln([(380, 400), (rx_, 400), (rx_, 786)]); f.text(388, fyy(392), "END", size=10.5, fill=DARK)
    node(rx_, 800, 130, 28, "Quantize Model")
    ln([(rx_, 814), (rx_, 837)])
    dia(rx_, 860)
    ln([(rx_ - 59, 860), (cx + 40, 860)]); f.text(rx_ - 105, fyy(852), "NO", size=10.5, fill=DARK)
    node(rx_, 925, 130, 44, "Final Quantized Model", "#F3C9C9")
    ln([(rx_, 883), (rx_, 903)]); f.text(rx_ + 6, fyy(893), "YES", size=10.5, fill=DARK)
    ln([(cx, 874), (cx, 925), (rx_ - 65, 925)])
    # right column: originals + table + unknown
    p8 = f.original(580, fy - 10, 290, "../../npu_study/images/03_quantization_theory/nagel_fig8.png", [
        "NAGEL tr.16, Figure 8", "Standard PTQ pipeline."])
    p9 = f.original(580, p8 + 10, 290, "../../npu_study/images/03_quantization_theory/nagel_p18_fig9.png", [
        "NAGEL tr.18, Figure 9", "PTQ debugging flow chart."])
    ty = p9 + 12
    f.text(580, ty + 8, "Weight hay activation (QYOLO Table 3, tr.10)", size=11.5, weight=700)
    f.text(580, ty + 24, "AP COCO, điều kiện Q-YOLO; real-valued: v5s 37.4, v5m 45.1", size=11, fill=DARK)
    tt = f.table(580, ty + 34, [100, 105, 105], ["W-A bit", "YOLOv5s", "YOLOv5m"], [
        ["6-32 weight", "36.7 (-0.7)", "44.7 (-0.4)"],
        ["32-6 activ.", "36.6 (-0.8)", "44.3 (-0.8)"],
        ["4-32 weight", "19.6 (-16.3)", "34.6 (-9.4)"],
        ["32-4 activ.", "30.6 (-5.3)", "37.7 (-6.3)"],
    ], size=11, line_h=15)
    tu = f.unknown(580, tt + 10, ["giá trị ngưỡng ε của Figure 9;", "lượng tử hóa YOLOv8 (SiLU, C2f, DFL)"], w=310, size=11.5)
    endy = max(fyy(960), tu)
    yl = f.legend(10, endy + 6, 880, [
        ("blue", "luồng xử lý (lưu đồ vẽ lại từ Figure 9; nhãn giữ nguyên tiếng Anh của bài)"),
        ("fill:#DDE6F3", "bước hoặc điều kiện của bài"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho"),
    ])
    source(f, yl + 8, "Nguồn: GHOLAMI tr.8 (Figure 4), 9, 12; NAGEL tr.6, 10 đến 19; QYOLO tr.10; QAREP tr.1, 6, 7. Cách chọn đo: xem Hình 10.7 (INT8 mAP, chờ pipeline).")
    return f


FIGS = [
    ("h3-1-affine", fig_affine),
    ("h3-2-do-min", fig_granularity),
    ("h3-3-clipping-rounding", fig_clipping),
    ("h3-4-phep-tinh-int8", fig_int8),
    ("h3-5-ptq-qat", fig_ptq_qat),
]

if __name__ == "__main__":
    run(FIGS, os.path.dirname(os.path.abspath(__file__)))
