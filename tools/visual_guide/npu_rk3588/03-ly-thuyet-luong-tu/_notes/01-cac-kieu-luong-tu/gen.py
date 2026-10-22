#!/usr/bin/env python3
"""Ghi chu chuyen de 01-cac-kieu-luong-tu (Phan 3): Hinh L.1 (tier T2 chung, khung lien he RK3588 la T1).

L.1 hl-1-static-dynamic-nonuniform-mixed: static va dynamic quantization (GHOLAMI tr.6, 7), uniform va non-uniform
    (GHOLAMI tr.7 Eq. 6; Y7Q tr.3), mixed precision (GHOLAMI tr.13, 14, Figure 8; NAGEL tr.8 chi xet homogeneous);
    lien he RK3588: UG232 tr.120 (linear, khoang deu), tr.122 (calibration set tinh range cua activation).
Duong cong chuong va vi tri muc luong tu trong panel B la minh hoa cua bo hinh, khong phai so lieu.

Chay: python3 gen.py [outdir] [figure-name ...]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VG = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, VG)
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

W = 900
CALC = "#EAF2FF"
IMG = os.path.abspath(os.path.join(VG, "..", "..", "_assets", "img"))


def tier(f):
    f.tier(808, 8, "T2 chung")


def txt(f, x, y, ls, size=12, dy=16, fill=INK, anchor="start"):
    for i, ln in enumerate(ls):
        f.rich(x, y + dy * i, ln, size=size, anchor=anchor, fill=fill)
    return y + dy * len(ls)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=3):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw}"{dash}/>')


def label(f, x, y, w, h, ls, size=12, fill="white", stroke="#333333", dashed=False, weight=400):
    rect(f, x, y, w, h, fill, stroke, dashed=dashed)
    top = y + h / 2 - (len(ls) - 1) * (size + 3) / 2
    for i, ln in enumerate(ls):
        f.text(x + w / 2, top + i * (size + 3), ln, size=size, weight=weight, anchor="middle")


def head(f, y, s):
    f.text(10, y, s, size=14, weight=700)


def axis_levels(f, x0, x1, y, levels, color, title):
    """Bell curve (illustrative) over an axis with quantization levels as ticks."""
    pts = []
    for i in range(81):
        t = i / 80
        x = x0 + t * (x1 - x0)
        z = (t - 0.5) / 0.16
        pts.append(f"{x:.1f},{y - 58 * math.exp(-z * z / 2):.1f}")
    f.a(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{GRAY}" stroke-width="1.2"/>')
    f.a(f'<path d="M{x0} {y} L{x1} {y}" stroke="{INK}" stroke-width="1.2"/>')
    for t in levels:
        x = x0 + t * (x1 - x0)
        f.a(f'<path d="M{x:.1f} {y - 7} L{x:.1f} {y + 7}" stroke="{color}" stroke-width="2"/>')
    f.text((x0 + x1) / 2, y + 20, title, size=12, weight=700, anchor="middle", fill=color)


def fig_l1():
    f = Fig(W, 1100)
    tier(f)
    f.text(10, 20, "Ba lựa chọn khi lượng tử: tính range lúc nào, lưới đều hay không, mỗi lớp mấy bit", size=16.5, weight=700)

    # ---- A. static vs dynamic ----
    head(f, 52, "A. Static và dynamic quantization của activation (GHOLAMI tr.6, 7)")
    f.text(20, 78, "Static", size=12.5, weight=700, fill=BLUE)
    label(f, 90, 64, 150, 30, ["calibration (trước)"], size=11.5, stroke=BLUE)
    f.line([(240, 79), (262, 79)], BLUE, THIN)
    label(f, 262, 64, 130, 30, ["range cố định"], size=11.5, fill=CALC, stroke=BLUE)
    f.line([(392, 79), (414, 79)], BLUE, THIN)
    label(f, 414, 64, 150, 30, ["mọi input dùng chung"], size=11.5, stroke=BLUE)
    f.text(20, 122, "Dynamic", size=12.5, weight=700, fill=RED)
    label(f, 90, 108, 150, 30, ["mỗi activation map"], size=11.5, stroke=RED)
    f.line([(240, 123), (262, 123)], RED, THIN)
    label(f, 262, 108, 130, 30, ["tính min, max lúc chạy"], size=11.5, fill="#FDECEC", stroke=RED)
    f.line([(392, 123), (414, 123)], RED, THIN)
    label(f, 414, 108, 150, 30, ["range riêng từng input"], size=11.5, stroke=RED)
    f.table(10, 150, [130, 210, 214], ["", "Static", "Dynamic"], [
        ["Range", "tính trước, cố định", "tính lúc chạy cho từng map"],
        ["Chi phí lúc chạy", "không thêm", "có thể rất cao"],
        ["Độ chính xác", "thường thấp hơn dynamic", "thường cao nhất"],
        ["Thực tế", "dùng nhiều nhất", "đắt nên ít dùng"],
    ], size=11.5, line_h=14)
    rect(f, 580, 64, 310, 206, fill="white", stroke=BLUE, rx=5)
    f.tier(592, 72, "T1 RK3588")
    txt(f, 592, 112, [
        [("UG232 tr.122: calibration set", "t")],
        [("\"is used to compute the quantization", "t")],
        [("range of activation values\".", "t")],
        [("Range của RKNN tính lúc build từ", "t")],
        [("dataset, không tính lại lúc chạy:", "t")],
        [("cách làm static (Hình 4.1, Hình 10.6).", "t")],
        [("Dynamic trên RKNN: không có trong", "i")],
        [("UG232 và API232 (tìm \"dynamic quant\").", "i")],
    ], size=11.5, dy=18)

    # ---- B. uniform vs non-uniform ----
    head(f, 300, "B. Uniform và non-uniform (GHOLAMI tr.7, Y7Q tr.3); đường chuông và vị trí mức là minh họa")
    axis_levels(f, 30, 420, 390, [i / 8 for i in range(9)], BLUE, "uniform: khoảng đều")
    nu = [0.0, 0.2, 0.32, 0.41, 0.5, 0.59, 0.68, 0.8, 1.0]
    axis_levels(f, 470, 860, 390, nu, RED, "non-uniform: dày ở nơi nhiều giá trị")
    rect(f, 10, 424, 880, 112, fill="white", stroke="#999999", rx=5)
    txt(f, 22, 442, [
        [("Định nghĩa (GHOLAMI Eq. 6): ", "b"), ("Q(r) = X", "c"), ("i", "c"), (" nếu r ∈ [Δ", "c"), ("i", "c"), (", Δ", "c"), ("i+1", "c"),
         (")", "c"), ("; bước và mức được phép cách nhau không đều,", "t")],
        [("\"neither Xi's nor Δi's are uniformly spaced\". ", "t"), ("Có thể chính xác hơn ở cùng số bit; thiết kế cho phân bố", "t")],
        [("hình chuông (bell-shaped) của weight và activation. Y7Q: chia clipping range \"unequally\" để giảm sai số.", "t")],
        [("RK3588 (T1, UG232 tr.120): ", "b"), ("\"In linear quantization, the intervals between fixed-point numbers are uniform\";", "t")],
        [("INT8 linear chia range thành 256 mức đều. Scale và zero-point của lưới đều: Hình 3.1.", "t")],
    ], size=12, dy=19)

    # ---- C. mixed precision ----
    head(f, 566, "C. Mixed precision: mỗi lớp một số bit (GHOLAMI tr.13, 14)")
    yb = f.original(10, 580, 520, os.path.join(IMG, "01-kien-thuc-nen/03-luong-tu-hoa/chien-luoc-ptq-qat-va-hon-hop/gholami-fig8-mixed-precision-quantization.png"),
                    ["GHOLAMI tr.13, Figure 8: mỗi lớp chọn 4 hoặc 8 bit,", "cân bằng độ trễ và độ nhạy của lớp."])
    rect(f, 560, 580, 330, yb - 580, fill="white", stroke="#999999", rx=6)
    txt(f, 572, 600, [
        [("Vì sao cần: ", "b"), ("lượng tử đều mọi lớp xuống", "t")],
        [("bit rất thấp có thể làm giảm độ chính", "t")],
        [("xác đáng kể (tr.13).", "t")],
        [("", "t")],
        [("Cách làm: ", "b"), ("giữ lớp nhạy và lớp hiệu quả", "t")],
        [("ở bit cao, lớp không nhạy ở bit thấp", "t")],
        [("(Figure 8); lớp được chia nhạy và", "t")],
        [("không nhạy (tr.14).", "t")],
        [("", "t")],
        [("Khó: ", "b"), ("số cách chọn bit tăng theo hàm", "t")],
        [("mũ của số lớp (tr.14).", "t")],
        [("", "t")],
        [("NAGEL tr.8: ", "b"), ("chỉ xét homogeneous", "t")],
        [("bit-width, không bàn mixed precision.", "t")],
        [("", "t")],
        [("RK3588: ", "b"), ("dạng của RKNN là hybrid", "t")],
        [("quantization, xem Hình 4.2.", "t")],
    ], size=12, dy=17.5)
    source(f, yb + 4, "Nguồn: GHOLAMI tr.6, 7, 13, 14 (Eq. 6, Figure 8); Y7Q tr.3; NAGEL tr.8; UG232 tr.120, tr.122.")
    return f


if __name__ == "__main__":
    run([("hl-1-static-dynamic-nonuniform-mixed", fig_l1)], HERE)
