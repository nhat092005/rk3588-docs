#!/usr/bin/env python3
"""Chuyên đề: Kiến trúc YOLOv8n của đề xuất (03-phuong-phap/01-tang-ai/02-kien-truc-model).

Sinh 4 hình vector SVG:
  1. ya-01-tong-quan-23-lop: toàn bộ 23 lớp (L0 đến L22), kích thước tensor, tham số, GFLOPs, các đường nối tắt.
  2. ya-02-conv-bottleneck-c2f: khối Conv, Bottleneck và C2f (ví dụ L6).
  3. ya-03-sppf-va-noi-neck: khối SPPF (L9) và nút ghép neck (L10 đến L12).
  4. ya-04-detect-head: đầu Detect (L22), nhánh box và cls cho ba mức, giải mã DFL.

Nguồn số liệu: ultralytics 8.4.154, cfg/models/v8/yolov8.yaml với scale n và nc=5, đối chiếu với
experiments/runs/ppe5_yolov8n_baseline_100ep_s0/weights/best.pt (3 011 823 tham số, 355 tensor trong state_dict).
Mọi con số tham số và MACs được tính lại từ công thức ở đầu file rồi assert với số đo thật (MEASURED_PARAMS), nên
gõ sai một hằng số là script dừng.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(HERE, "..", "..", "..", "..", "_assets", "generated", "03-phuong-phap", "01-tang-ai",
                 "02-kien-truc-model"))

ORANGE, PURPLE, TEAL = "#E65100", "#7B1FA2", "#00796B"
GRID = "#E2E8F0"
BOX_STROKE = "#333333"
NC = 5

# ---------------------------------------------------------------- model arithmetic (verified against the real model)
def conv_p(cin, cout, k):
    """Conv2d(bias=False) + BatchNorm2d (gamma, beta)."""
    return k * k * cin * cout + 2 * cout


def c2f_p(c1, c2, n):
    c = c2 // 2
    return conv_p(c1, 2 * c, 1) + n * 2 * conv_p(c, c, 3) + conv_p((2 + n) * c, c2, 1)


def c2f_macs(c1, c2, n, hw):
    c = c2 // 2
    return hw * (c1 * 2 * c + n * 2 * c * c * 9 + (2 + n) * c * c2)


def sppf_p(c1, c2):
    c = c1 // 2
    return conv_p(c1, c, 1) + conv_p(4 * c, c2, 1)


def sppf_macs(c1, c2, hw):
    c = c1 // 2
    return hw * (c1 * c + 4 * c * c2)


HEAD_CH = (64, 128, 256)          # channels of L15, L18, L21
HEAD_HW = (80 * 80, 40 * 40, 20 * 20)
C2_BOX, C3_CLS = 64, 64           # max(16, 64 // 4, 4 * 16) and max(64, min(5, 100))


def head_branch_p(cin, cout_last):
    return conv_p(cin, 64, 3) + conv_p(64, 64, 3) + 64 * cout_last + cout_last


def head_p():
    box = [head_branch_p(c, 4 * 16) for c in HEAD_CH]
    cls = [head_branch_p(c, NC) for c in HEAD_CH]
    return box, cls, 16  # DFL: Conv2d(16, 1, 1, bias=False), weights fixed to 0..15


def head_macs():
    tot = 0
    for c, hw in zip(HEAD_CH, HEAD_HW):
        tot += hw * (c * 64 * 9 + 64 * 64 * 9 + 64 * 64) + hw * (c * 64 * 9 + 64 * 64 * 9 + 64 * NC)
    return tot + 16 * 4 * 8400  # DFL conv sees (B, 16, 4, 8400)


# (idx, module, from, text, c_in, c_out, out_c, out_hw_side, params, macs)
def build_layers():
    L = []

    def conv(i, cin, cout, side):
        L.append(dict(i=i, m="Conv", f="-1", cin=cin, cout=cout, side=side, p=conv_p(cin, cout, 3),
                      macs=9 * cin * cout * side * side, note="3×3, s2"))

    def c2f(i, cin, cout, n, side, sc):
        L.append(dict(i=i, m="C2f", f="-1", cin=cin, cout=cout, side=side, n=n, sc=sc, p=c2f_p(cin, cout, n),
                      macs=c2f_macs(cin, cout, n, side * side), note=f"n={n}"))

    conv(0, 3, 16, 320)
    conv(1, 16, 32, 160)
    c2f(2, 32, 32, 1, 160, True)
    conv(3, 32, 64, 80)
    c2f(4, 64, 64, 2, 80, True)
    conv(5, 64, 128, 40)
    c2f(6, 128, 128, 2, 40, True)
    conv(7, 128, 256, 20)
    c2f(8, 256, 256, 1, 20, True)
    L.append(dict(i=9, m="SPPF", f="-1", cin=256, cout=256, side=20, p=sppf_p(256, 256),
                  macs=sppf_macs(256, 256, 400), note="k=5"))
    L.append(dict(i=10, m="Upsample", f="-1", cin=256, cout=256, side=40, p=0, macs=0, note="×2 nearest"))
    L.append(dict(i=11, m="Concat", f="10, 6", cin=384, cout=384, side=40, p=0, macs=0, note=""))
    c2f(12, 384, 128, 1, 40, False)
    L.append(dict(i=13, m="Upsample", f="-1", cin=128, cout=128, side=80, p=0, macs=0, note="×2 nearest"))
    L.append(dict(i=14, m="Concat", f="13, 4", cin=192, cout=192, side=80, p=0, macs=0, note=""))
    c2f(15, 192, 64, 1, 80, False)
    conv(16, 64, 64, 40)
    L.append(dict(i=17, m="Concat", f="16, 12", cin=192, cout=192, side=40, p=0, macs=0, note=""))
    c2f(18, 192, 128, 1, 40, False)
    conv(19, 128, 128, 20)
    L.append(dict(i=20, m="Concat", f="19, 9", cin=384, cout=384, side=20, p=0, macs=0, note=""))
    c2f(21, 384, 256, 1, 20, False)
    box, cls, dfl = head_p()
    L.append(dict(i=22, m="Detect", f="15, 18, 21", cin=0, cout=0, side=0, p=sum(box) + sum(cls) + dfl,
                  macs=head_macs(), note=""))
    return L


# Measured with ultralytics 8.4.154: sum(p.numel() for p in model.model[i].parameters()), DetectionModel("yolov8n.yaml", nc=5)
MEASURED_PARAMS = [464, 4672, 7360, 18560, 49664, 73984, 197632, 295424, 460288, 164608, 0, 0, 148224, 0, 0,
                   37248, 36992, 0, 123648, 147712, 0, 493056, 752287]
# Conv2d-only MACs measured with forward hooks on the same model at 640×640 (0 for non-conv layers)
MEASURED_MACS = [44236800, 117964800, 183500800, 117964800, 314572800, 117964800, 314572800, 117964800,
                 183500800, 65536000, 0, 0, 235929600, 0, 0, 235929600, 58982400, 0, 196608000, 58982400, 0,
                 196608000, 1482700800]
LAYERS = build_layers()
for _l in LAYERS:
    assert _l["p"] == MEASURED_PARAMS[_l["i"]], (_l["i"], _l["p"], MEASURED_PARAMS[_l["i"]])
    assert _l["macs"] == MEASURED_MACS[_l["i"]], (_l["i"], _l["macs"], MEASURED_MACS[_l["i"]])
TOTAL_P = sum(_l["p"] for _l in LAYERS)
TOTAL_MACS = sum(_l["macs"] for _l in LAYERS)
assert TOTAL_P == 3011823, TOTAL_P
BB_P = sum(_l["p"] for _l in LAYERS[:10])
NK_P = sum(_l["p"] for _l in LAYERS[10:22])
HD_P = LAYERS[22]["p"]
BB_M = sum(_l["macs"] for _l in LAYERS[:10])
NK_M = sum(_l["macs"] for _l in LAYERS[10:22])
HD_M = LAYERS[22]["macs"]


def fmt(n):
    return f"{n:,}".replace(",", " ")


def gf(macs):
    return f"{2 * macs / 1e9:.3f}"


# ---------------------------------------------------------------- drawing helpers
def rect(f, x, y, w, h, fill="white", stroke=BOX_STROKE, sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw}"{dash}/>')


def arrow(f, pts, color=BLUE, sw=THIN, dashed=False):
    f.line(pts, color, width=sw, dashed=dashed, head=True)


def chip(f, x, y, w, label, color):
    rect(f, x, y, w, 22, fill=color, stroke=color, sw=1, rx=3)
    f.text(x + w / 2, y + 11, label, size=12, weight=700, fill="white", anchor="middle")


# ================================================================ 1. TONG QUAN 23 LOP
# Bố cục theo Figure 1 của arXiv 2501.13400 (YOLOv8 to YOLO11): ba khung nét đứt, kích thước tensor trên mũi tên,
# chỉ số lớp bên phải khối, bảng d/w/mc, ba khối Detect. Số liệu là của mô hình thật (xem MEASURED_PARAMS ở trên).
OV = {  # fill, stroke, text
    "Conv": ("#DCE8F8", "#3F5F8F", INK),
    "C2f": ("#B2E3E3", "#2E8B8B", INK),
    "SPPF": ("#B8C4CC", "#6B7A85", INK),
    "Upsample": ("#00695C", "#004D40", "white"),
    "Concat": ("#0D47E0", "#0A35A8", "white"),
    "Detect": ("#1E9BE8", "#0F6FB5", "white"),
}
FRAME_BB, FRAME_NECK, FRAME_HEAD = "#2E7D32", "#D81B60", "#7B1FA2"
VARIANTS = [("n", "0.33", "0.25", "1024"), ("s", "0.33", "0.50", "1024"), ("m", "0.67", "0.75", "768"),
            ("l", "1.00", "1.00", "512"), ("x", "1.00", "1.25", "512")]  # yolov8.yaml dòng 10-15
BASE_REPEATS = {2: 3, 4: 6, 6: 6, 8: 3, 12: 3, 15: 3, 18: 3, 21: 3}  # yolov8.yaml: số lặp trước khi nhân d = 0.33
P_LEVEL = {0: "P1", 1: "P2", 3: "P3", 5: "P4", 7: "P5", 15: "P3", 18: "P4", 21: "P5"}  # chú thích -P trong yolov8.yaml


def head_level_p(k):
    return head_branch_p(HEAD_CH[k], 64) + head_branch_p(HEAD_CH[k], NC)


def head_level_macs(k):
    c, hw = HEAD_CH[k], HEAD_HW[k]
    return hw * (c * 64 * 9 + 64 * 64 * 9 + 64 * 64) + hw * (c * 64 * 9 + 64 * 64 * 9 + 64 * NC)


assert sum(head_level_p(k) for k in range(3)) + 16 == HD_P
assert sum(head_level_macs(k) for k in range(3)) + 16 * 4 * 8400 == HD_M
for _i, _b in BASE_REPEATS.items():
    assert max(round(_b * 0.33), 1) == LAYERS[_i]["n"], _i


def size_of(i):
    l = LAYERS[i]
    return f'{l["cout"]}×{l["side"]}×{l["side"]}'


def ov_node(f, x, y, w, h, i):
    l = LAYERS[i]
    m = l["m"]
    fill, stroke, tc = OV[m]
    rect(f, x, y, w, h, fill=fill, stroke=stroke, sw=1.2, rx=3)
    cx = x + w / 2
    if m in ("Upsample", "Concat"):
        f.text(cx, y + 10, m, size=12, weight=700, fill=tc, anchor="middle")
        if m == "Upsample":
            f.text(cx, y + 23, "scale=2, nearest", size=10, fill=tc, anchor="middle", mono=True)
        else:
            a, b = l["f"].split(", ")
            f.text(cx, y + 23, f"L{a} + L{b}", size=10, fill=tc, anchor="middle", mono=True)
    else:
        if m == "Conv":
            cfg = "k=3, s=2, p=1"
        elif m == "C2f":
            cfg = f'shortcut={l["sc"]}, n={BASE_REPEATS[i]}×d={l["n"]}'
        else:
            cfg = "k=5"
        f.text(cx, y + 11, m, size=12.5, weight=700, fill=tc, anchor="middle")
        f.text(cx, y + 24, cfg, size=10, fill=tc, anchor="middle", mono=True)
        f.text(cx, y + 37, f'{l["cin"]}→{l["cout"]} kênh', size=10, fill=tc, anchor="middle")
        f.text(cx, y + 49, f'{fmt(l["p"])} tham số · {gf(l["macs"])} GFLOPs', size=10, fill=tc, anchor="middle")
    f.text(x + w + 7, y + 8, f"L{i}", size=11, weight=700, fill=INK)
    if i in P_LEVEL:
        f.text(x + w + 7, y + 20, P_LEVEL[i], size=10, weight=700, fill=INK)


def fig_overview():
    W = 1175
    f = Fig(W, 1180)
    P, NH, SH, y0 = 90, 56, 32, 118
    xb, xt, xu, bw = 40, 400, 690, 200
    cxb, cxt, cxu = xb + bw / 2, xt + bw / 2, xu + bw / 2
    xd, dw, dh = 1000, 140, 76
    R = lambda k: y0 + P * k  # noqa: E731
    top = {i: R(i) for i in range(10)}
    c14, c11 = R(4) + NH / 2, R(6) + NH / 2
    g = ((c11 - c14) - (SH / 2 + SH + NH + SH / 2)) / 3
    top[14] = c14 - SH / 2
    top[13] = top[14] + SH + g
    top[12] = top[13] + SH + g
    top[11] = top[12] + NH + g
    assert abs(top[11] - (c11 - SH / 2)) < 1e-6
    top[10] = top[11] + SH + 36
    top[15] = top[14] - 40 - NH
    top[17] = top[12] + NH / 2 - SH / 2
    top[16] = top[17] - 40 - NH
    top[18] = top[17] + SH + 36
    top[19] = top[18] + NH + 36
    top[20] = R(9) + NH / 2 - SH / 2
    top[21] = top[20] + SH + 36
    hh = lambda i: SH if LAYERS[i]["m"] in ("Upsample", "Concat") else NH  # noqa: E731
    ctr = lambda i: top[i] + hh(i) / 2  # noqa: E731
    colx = {**{i: xb for i in range(10)}, **{i: xt for i in range(10, 16)}, **{i: xu for i in range(16, 22)}}
    for i in range(22):
        ov_node(f, colx[i], top[i], bw, hh(i), i)

    INKL = INK

    def lab(x, y, s, color=INK, anchor="start"):
        f.text(x, y, s, size=10, fill=color, anchor=anchor, halo="white")

    def seg(pts, color=INKL):
        f.line(pts, color, width=1.5, head=True)

    def dot(x, y, color):
        f.a(f'<circle cx="{x:g}" cy="{y:g}" r="3" fill="{color}"/>')

    # vertical main flow
    f.text(cxb + 6, R(0) - 26, "3×640×640", size=10, fill=INK, halo="white")
    seg([(cxb, R(0) - 16), (cxb, R(0))])
    for i in range(1, 10):
        seg([(cxb, top[i - 1] + NH), (cxb, top[i])])
        lab(cxb + 6, (top[i - 1] + NH + top[i]) / 2, size_of(i - 1))
    for a, b in ((10, 11), (11, 12), (12, 13), (13, 14), (14, 15)):          # top-down, upward
        seg([(cxt, top[a]), (cxt, top[b] + hh(b))])
        lab(cxt + 6, (top[a] + top[b] + hh(b)) / 2, size_of(a))
    for a, b in ((16, 17), (17, 18), (18, 19), (19, 20), (20, 21)):          # bottom-up, downward
        seg([(cxu, top[a] + hh(a)), (cxu, top[b])])
        lab(cxu + 6, (top[a] + hh(a) + top[b]) / 2, size_of(a))
    # L9 -> L10 (main) and L9 -> L20 (skip)
    y9 = ctr(9)
    seg([(xb + bw, y9 - 9), (cxt, y9 - 9), (cxt, top[10] + SH)])
    lab(315, y9 - 19, size_of(9), anchor="middle")
    seg([(xb + bw, y9), (xu, y9)], GREEN)
    lab(315, y9 + 10, size_of(9), GREEN, anchor="middle")
    # skips into Concat (green)
    seg([(xb + bw, ctr(14)), (xt, ctr(14))], GREEN)
    lab(315, ctr(14) - 9, size_of(4), GREEN, anchor="middle")
    seg([(xb + bw, ctr(11)), (xt, ctr(11))], GREEN)
    lab(315, ctr(11) - 9, size_of(6), GREEN, anchor="middle")
    seg([(xt + bw, ctr(17)), (xu, ctr(17))], GREEN)
    lab(645, ctr(17) - 9, size_of(12), GREEN, anchor="middle")
    # L15 -> Detect P3 (red) and L15 -> L16 (main)
    c15 = ctr(15)
    seg([(xt + bw, c15), (xd, c15)], RED)
    lab(800, c15 - 9, size_of(15), RED, anchor="middle")
    dot(cxu, c15, RED)
    seg([(cxu, c15), (cxu, top[16])])
    lab(cxu + 6, (c15 + top[16]) / 2, size_of(15))
    for i in (18, 21):
        seg([(xu + bw, ctr(i)), (xd, ctr(i))], RED)
        lab(xu + bw + 8, ctr(i) + 11, size_of(i), RED)

    # frames and titles
    bot = top[21] + NH + 18
    for (fx, fy, fw, fh, col, title) in (
            (25, y0 - 44, 260, R(9) + NH + 18 - (y0 - 44), FRAME_BB, "Backbone"),
            (345, top[15] - 34, 620, bot - (top[15] - 34), FRAME_NECK, "Neck"),
            (985, top[15] - 34, 170, bot - (top[15] - 34), FRAME_HEAD, "Head")):
        f.a(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="2" fill="none" stroke="{col}" '
            f'stroke-width="2" stroke-dasharray="7 4"/>')
        f.text(fx + fw / 2, fy - 16, title, size=19, weight=700, fill=col, anchor="middle")

    # three Detect blocks (L22: one module, three levels)
    for k, i in enumerate((15, 18, 21)):
        cy = ctr(i)
        fill, stroke, tc = OV["Detect"]
        rect(f, xd, cy - dh / 2, dw, dh, fill=fill, stroke=stroke, sw=1.2, rx=3)
        f.text(xd + dw / 2, cy - dh / 2 + 11, "L22  Detect", size=12.5, weight=700, fill=tc, anchor="middle")
        f.text(xd + dw / 2, cy - dh / 2 + 25, f'nhánh {("P3", "P4", "P5")[k]}: box 64 + cls {NC}', size=10, fill=tc,
               anchor="middle")
        f.text(xd + dw / 2, cy - dh / 2 + 40, f"{fmt(head_level_p(k))} tham số", size=10, fill=tc, anchor="middle")
        f.text(xd + dw / 2, cy - dh / 2 + 54, f"{gf(head_level_macs(k))} GFLOPs", size=10, fill=tc, anchor="middle")
    mid = (ctr(15) + ctr(18)) / 2
    for j, (t, w_) in enumerate((("L22 là một module", 400), ("ba nhánh dùng chung DFL", 400),
                                 (f"(16 tham số, {gf(16 * 4 * 8400)} GFLOPs)", 400), (f"tổng L22: {fmt(HD_P)} tham số", 700),
                                 (f"{gf(HD_M)} GFLOPs", 700), ("8400 anchor, out 1×9×8400", 400))):
        f.text(1070, mid - 45 + j * 17, t, size=10.5, weight=w_, fill=INK, anchor="middle")

    # tables and legend (top band)
    f.table(330, 45, [96, 112, 112, 112], ["Model variant", "d (depth_multiple)", "w (width_multiple)", "mc (max_channels)"],
            [[v, d, w_, mc] for v, d, w_, mc in VARIANTS], size=10.5, line_h=16, fills={0: "#FFF3C4"})
    f.text(330, 213, "Dòng n (nền vàng) là mô hình trong tài liệu này. Mọi số kênh = min(kênh gốc, mc) × w.", size=10.5, fill=DARK)
    rows = [
        ["Backbone L0-L9", fmt(BB_P), f"{BB_P / TOTAL_P * 100:.1f}%", gf(BB_M), f"{BB_M / TOTAL_MACS * 100:.1f}%"],
        ["Neck L10-L21", fmt(NK_P), f"{NK_P / TOTAL_P * 100:.1f}%", gf(NK_M), f"{NK_M / TOTAL_MACS * 100:.1f}%"],
        ["Head L22", fmt(HD_P), f"{HD_P / TOTAL_P * 100:.1f}%", gf(HD_M), f"{HD_M / TOTAL_MACS * 100:.1f}%"],
        ["Tổng", fmt(TOTAL_P), "100%", gf(TOTAL_MACS), "100%"],
    ]
    f.table(830, 45, [112, 74, 44, 56, 44], ["Giai đoạn", "Tham số", "%", "GFLOPs", "%"], rows, size=10.5, line_h=16)
    lx, ly = 330, 245
    for k, (c, t) in enumerate(((INKL, "luồng chính"), (GREEN, "nối tắt vào Concat"), (RED, "đặc trưng P3, P4, P5 vào Detect"))):
        x = lx + (0, 140, 308)[k]  # chữ rộng 52 và 80 px ở size 11, khoảng trống giữa các mục 45 px
        f.line([(x, ly), (x + 34, ly)], c, 1.5, False, head=False)
        f.text(x + 42, ly, t, size=11, fill=INK)
    f.text(lx, ly + 20, "Kích thước C×H×W ghi trên mũi tên là đầu ra của khối nằm trước mũi tên.", size=10.5, fill=DARK)
    f.text(lx, ly + 38, "L22 chia theo nhánh P3/P4/P5 chỉ để vẽ. Tham số và GFLOPs chia từng mức cộng với DFL ra đúng tổng L22.",
           size=10.5, fill=DARK)

    f.text(10, bot + 18, "Nguồn: ultralytics 8.4.154 yolov8.yaml (scale n, nc=5) và best.pt run ppe5_yolov8n_baseline_100ep_s0. "
                         "GFLOPs = 2 × MACs của Conv2d ở 640×640.", size=12, fill=DARK, italic=True)
    source(f, bot + 18, "Bố cục theo Figure 1 của arXiv 2501.13400 (YOLOv8 to YOLO11: A Comprehensive Architecture In-depth Comparative Review).")
    return f


# ================================================================ 2. CONV / BOTTLENECK / C2F
def fig_conv_bottleneck_c2f():
    W, H = 1040, 640
    f = Fig(W, H)
    f.text(14, 20, "Ba khối cơ sở: Conv, Bottleneck và C2f (ví dụ số lấy từ L6, ảnh vào 640×640)", size=15, weight=700,
           fill=DARK)

    # ---- panel (a) Conv
    xa, wa = 18, 250
    rect(f, xa, 40, wa, 565, fill="#F8FAFC", stroke=BLUE, sw=1.3, rx=5)
    chip(f, xa + 10, 50, 120, "(a) Conv", BLUE)
    cx = xa + wa / 2
    f.text(cx, 90, "Đầu vào C_in×H×W", size=12, fill=INK, anchor="middle")
    arrow(f, [(cx, 100), (cx, 118)])
    stack = [("Conv2d", "bias=False, padding = k//2", "#EFF6FF", BLUE),
             ("BatchNorm2d", "eps=0.001, momentum=0.03", "#F0FDF4", GREEN),
             ("SiLU", "x · sigmoid(x)", "#FFF7ED", ORANGE)]
    y = 118
    for t, s, fl, st in stack:
        rect(f, xa + 25, y, wa - 50, 50, fill=fl, stroke=st, sw=1.3)
        f.text(cx, y + 17, t, size=13, weight=700, fill=st if st != GREEN else "#1B5E20", anchor="middle")
        f.text(cx, y + 35, s, size=10.5, fill=INK, anchor="middle")
        if t != "SiLU":
            arrow(f, [(cx, y + 50), (cx, y + 68)])
        y += 68
    arrow(f, [(cx, y - 18), (cx, y)])
    f.text(cx, y + 12, "Đầu ra C_out×H'×W'", size=12, fill=INK, anchor="middle")
    f.text(xa + 14, 368, "Số tham số của một Conv", size=12.5, weight=700, fill=DARK)
    f.text(xa + 14, 390, "k² · C_in · C_out  (Conv2d, không bias)", size=11.5, fill=INK)
    f.text(xa + 14, 410, "+ 2 · C_out  (gamma và beta của BN)", size=11.5, fill=INK)
    f.text(xa + 14, 438, "Ví dụ L0: 3×3×3×16 = 432", size=11.5, fill=INK)
    f.text(xa + 14, 458, "         + 2×16 = 32  →  464", size=11.5, fill=INK)
    f.text(xa + 14, 494, "Tham số BN khác (mean, var)", size=11.5, fill=INK)
    f.text(xa + 14, 512, "là buffer, không tính vào 464.", size=11.5, fill=INK)
    f.text(xa + 14, 548, "Mọi Conv trong v8n dùng SiLU", size=11.5, fill=INK)
    f.text(xa + 14, 566, "(kể cả cv1 của SPPF, gán lại", size=11.5, fill=INK)
    f.text(xa + 14, 584, "ở ultralytics/nn/tasks.py:2194).", size=11.5, fill=INK)

    # ---- panel (b) Bottleneck
    xb, wb = 282, 250
    rect(f, xb, 40, wb, 565, fill="#F8FAFC", stroke=GREEN, sw=1.3, rx=5)
    chip(f, xb + 10, 50, 150, "(b) Bottleneck", GREEN)
    bx = xb + wb / 2
    f.text(bx - 20, 90, "Đầu vào c×H×W", size=12, fill=INK, anchor="middle")
    arrow(f, [(bx - 20, 100), (bx - 20, 118)])
    rect(f, xb + 25, 118, 170, 56, fill="#EFF6FF", stroke=BLUE, sw=1.3)
    f.text(bx - 20, 135, "cv1: Conv 3×3, s1", size=12, weight=700, fill=BLUE, anchor="middle")
    f.text(bx - 20, 154, "c → c (e=1.0 trong C2f)", size=10.5, fill=INK, anchor="middle")
    arrow(f, [(bx - 20, 174), (bx - 20, 192)])
    rect(f, xb + 25, 192, 170, 56, fill="#EFF6FF", stroke=BLUE, sw=1.3)
    f.text(bx - 20, 209, "cv2: Conv 3×3, s1", size=12, weight=700, fill=BLUE, anchor="middle")
    f.text(bx - 20, 228, "c → c", size=10.5, fill=INK, anchor="middle")
    arrow(f, [(bx - 20, 248), (bx - 20, 276)])
    f.a(f'<circle cx="{bx - 20}" cy="288" r="12" fill="white" stroke="{ORANGE}" stroke-width="1.5"/>')
    f.text(bx - 20, 288, "+", size=16, weight=700, fill=ORANGE, anchor="middle")
    arrow(f, [(bx - 20, 300), (bx - 20, 322)])
    f.text(bx - 20, 334, "Đầu ra c×H×W", size=12, fill=INK, anchor="middle")
    f.line([(bx - 20, 108), (xb + 215, 108), (xb + 215, 288), (bx - 8, 288)], GREEN, THIN, True)
    f.text(xb + 200, 98, "shortcut", size=10.5, weight=700, fill=GREEN, anchor="end")
    f.text(xb + 14, 370, "Cộng tắt chỉ khi shortcut=True", size=12, weight=700, fill=DARK)
    f.text(xb + 14, 390, "và C_in == C_out (block.py:480).", size=11.5, fill=INK)
    f.text(xb + 14, 420, "Backbone (L2, L4, L6, L8):", size=11.5, fill=INK)
    f.text(xb + 14, 438, "shortcut = True, có cộng tắt.", size=11.5, fill=INK)
    f.text(xb + 14, 462, "Neck (L12, L15, L18, L21):", size=11.5, fill=INK)
    f.text(xb + 14, 480, "shortcut = False, không cộng tắt.", size=11.5, fill=INK)
    f.text(xb + 14, 516, "Tham số khi c = 64 (L6):", size=11.5, weight=700, fill=DARK)
    f.text(xb + 14, 536, f"2 × ({fmt(conv_p(64, 64, 3))}) = {fmt(2 * conv_p(64, 64, 3))}", size=11.5, fill=INK)
    f.text(xb + 14, 556, f"Mỗi Conv 3×3: 64·64·9 + 2·64 = {fmt(conv_p(64, 64, 3))}", size=10.5, fill=GRAY)

    # ---- panel (c) C2f, example L6: C1=128 C2=128 n=2 c=64, 40x40
    xc, wc = 546, 476
    rect(f, xc, 40, wc, 565, fill="#F6FBF7", stroke=GREEN, sw=1.3, rx=5)
    chip(f, xc + 10, 50, 200, "(c) C2f, ví dụ L6", GREEN)
    f.text(xc + 218, 61, "C_in = C_out = 128, n = 2, c = 64, lưới 40×40", size=11, fill=INK)
    mx = xc + 130
    f.text(mx, 92, "Đầu vào 128×40×40", size=12, fill=INK, anchor="middle")
    arrow(f, [(mx, 102), (mx, 118)])
    rect(f, mx - 105, 118, 210, 44, fill="#EFF6FF", stroke=BLUE, sw=1.3)
    f.text(mx, 134, "cv1: Conv 1×1", size=12, weight=700, fill=BLUE, anchor="middle")
    f.text(mx, 151, "128 → 2c = 128", size=11, fill=INK, anchor="middle")
    arrow(f, [(mx, 162), (mx, 180)])
    rect(f, mx - 105, 180, 210, 34, fill="#FFF7ED", stroke=ORANGE, sw=1.3)
    f.text(mx, 197, "chunk(2, dim=1) → y0, y1", size=11.5, weight=700, fill=ORANGE, anchor="middle")
    # y0 bypass on the left
    f.line([(mx - 60, 214), (mx - 60, 232), (xc + 28, 232), (xc + 28, 438), (xc + 54, 438)], GREEN, THIN, False)
    f.text(xc + 34, 246, "y0: 64×40×40", size=10.5, weight=700, fill=GREEN)
    # y1 chain
    arrow(f, [(mx + 55, 214), (mx + 55, 250)])
    f.text(mx + 62, 228, "y1: 64×40×40", size=10.5, weight=700, fill=GREEN)
    f.line([(mx + 55, 232), (mx - 20, 232), (mx - 20, 426)], GREEN, THIN, False)
    rect(f, mx - 5, 250, 120, 50, fill="#F0FDF4", stroke=GREEN, sw=1.3)
    f.text(mx + 55, 266, "Bottleneck 1", size=12, weight=700, fill="#1B5E20", anchor="middle")
    f.text(mx + 55, 285, "64 → 64 → 64", size=11, fill=INK, anchor="middle")
    arrow(f, [(mx + 55, 300), (mx + 55, 336)])
    rect(f, mx - 5, 336, 120, 50, fill="#F0FDF4", stroke=GREEN, sw=1.3)
    f.text(mx + 55, 352, "Bottleneck 2", size=12, weight=700, fill="#1B5E20", anchor="middle")
    f.text(mx + 55, 371, "64 → 64 → 64", size=11, fill=INK, anchor="middle")
    # taps b1 and b2 to concat
    f.line([(mx + 115, 275), (mx + 150, 275), (mx + 150, 426)], GREEN, THIN, False)
    f.text(mx + 158, 340, "b1", size=11, weight=700, fill=GREEN)
    f.line([(mx + 115, 361), (mx + 128, 361), (mx + 128, 426)], GREEN, THIN, False)
    f.text(mx + 90, 405, "b2", size=11, weight=700, fill=GREEN)
    # concat
    rect(f, xc + 54, 426, 244, 40, fill="#FFF7ED", stroke=ORANGE, sw=1.3)
    f.text(xc + 176, 441, "Concat (y0, y1, b1, b2)", size=12, weight=700, fill=ORANGE, anchor="middle")
    f.text(xc + 176, 457, "(2+n)·c = 4 × 64 = 256 kênh", size=10.5, fill=INK, anchor="middle")
    arrow(f, [(xc + 176, 466), (xc + 176, 490)])
    rect(f, xc + 76, 490, 200, 44, fill="#EFF6FF", stroke=BLUE, sw=1.3)
    f.text(xc + 176, 506, "cv2: Conv 1×1", size=12, weight=700, fill=BLUE, anchor="middle")
    f.text(xc + 176, 523, "256 → 128", size=11, fill=INK, anchor="middle")
    arrow(f, [(xc + 176, 534), (xc + 176, 554)])
    f.text(xc + 176, 566, "Đầu ra 128×40×40", size=12, fill=INK, anchor="middle")
    # parameter breakdown on the right
    p1, pb, p2 = conv_p(128, 128, 1), 2 * (2 * conv_p(64, 64, 3)), conv_p(256, 128, 1)
    assert p1 + pb + p2 == LAYERS[6]["p"]
    f.text(xc + 316, 280, "Tham số L6", size=12.5, weight=700, fill=DARK)
    for k, (t, v) in enumerate((("cv1 1×1", p1), ("2 Bottleneck", pb), ("cv2 1×1", p2))):
        f.text(xc + 316, 304 + 20 * k, t, size=11.5, fill=INK)
        f.text(xc + 456, 304 + 20 * k, fmt(v), size=11.5, fill=INK, anchor="end", mono=True)
    f.a(f'<line x1="{xc + 316}" y1="364" x2="{xc + 456}" y2="364" stroke="{GRAY}" stroke-width="1"/>')
    f.text(xc + 316, 378, "Tổng", size=11.5, weight=700, fill=INK)
    f.text(xc + 456, 378, fmt(LAYERS[6]["p"]), size=11.5, weight=700, fill=INK, anchor="end", mono=True)
    f.text(xc + 316, 410, "GFLOPs (2 × MACs):", size=11.5, fill=INK)
    f.text(xc + 456, 428, f"{gf(LAYERS[6]['macs'])}", size=12, weight=700, fill=INK, anchor="end", mono=True)
    f.text(xc + 316, 468, "Công thức tổng quát:", size=11, weight=700, fill=DARK)
    f.text(xc + 316, 486, "c = C_out/2", size=10.5, fill=INK, mono=True)
    f.text(xc + 316, 502, "cv1: C_in → 2c", size=10.5, fill=INK, mono=True)
    f.text(xc + 316, 518, "cv2: (2+n)c → C_out", size=10.5, fill=INK, mono=True)
    source(f, 612, "Nguồn: ultralytics 8.4.154 nn/modules/block.py (C2f dòng 291-315, Bottleneck dòng 460-484), conv.py (Conv dòng 39-78).")
    return f


# ================================================================ 3. SPPF + NECK NODE
def fig_sppf_neck():
    W, H = 1040, 560
    f = Fig(W, H)
    f.text(14, 20, "Khối SPPF (L9) và nút ghép của neck (L10 đến L12)", size=15, weight=700, fill=DARK)

    # ---- SPPF
    xa, wa = 18, 480
    rect(f, xa, 40, wa, 480, fill="#FAF5FF", stroke=PURPLE, sw=1.3, rx=5)
    chip(f, xa + 10, 50, 190, "L9  SPPF (k=5, n=3)", PURPLE)
    cx = xa + 150
    f.text(cx, 92, "Đầu vào 256×20×20 (từ L8)", size=12, fill=INK, anchor="middle")
    arrow(f, [(cx, 102), (cx, 120)])
    rect(f, cx - 100, 120, 200, 44, fill="#EFF6FF", stroke=BLUE, sw=1.3)
    f.text(cx, 136, "cv1: Conv 1×1 + SiLU", size=12, weight=700, fill=BLUE, anchor="middle")
    f.text(cx, 153, "256 → 128", size=11, fill=INK, anchor="middle")
    # three maxpool chain
    yy = [196, 252, 308]
    names = ["MaxPool 5×5 (s1, p2)", "MaxPool 5×5 (s1, p2)", "MaxPool 5×5 (s1, p2)"]
    rf = ["vùng nhìn 5×5", "tương đương 9×9", "tương đương 13×13"]
    arrow(f, [(cx, 164), (cx, yy[0])])
    for k in range(3):
        rect(f, cx - 100, yy[k], 200, 38, fill="#F5F5F5", stroke=BOX_STROKE, sw=1.2)
        f.text(cx, yy[k] + 13, names[k], size=11.5, weight=700, fill=DARK, anchor="middle")
        f.text(cx, yy[k] + 29, f"128×20×20 · {rf[k]}", size=10.5, fill=INK, anchor="middle")
        if k < 2:
            arrow(f, [(cx, yy[k] + 38), (cx, yy[k + 1])])
    # taps to concat
    cat_y = 372
    f.line([(cx - 100, 142), (xa + 34, 142), (xa + 34, cat_y + 20), (xa + 62, cat_y + 20)], GREEN, THIN, False)
    f.text(xa + 22, 392, "x0", size=11, weight=700, fill=GREEN)
    for k, ty_ in enumerate(yy):
        xr = cx + 130 + 14 * k
        f.line([(cx + 100, ty_ + 19), (xr, ty_ + 19), (xr, cat_y)], GREEN, THIN, False)
    rect(f, xa + 62, cat_y, 300, 40, fill="#FFF7ED", stroke=ORANGE, sw=1.3)
    f.text(xa + 212, cat_y + 14, "Concat (x0, x1, x2, x3)", size=12, weight=700, fill=ORANGE, anchor="middle")
    f.text(xa + 212, cat_y + 30, "4 × 128 = 512 kênh", size=10.5, fill=INK, anchor="middle")
    arrow(f, [(xa + 212, cat_y + 40), (xa + 212, cat_y + 62)])
    rect(f, xa + 112, cat_y + 62, 200, 44, fill="#EFF6FF", stroke=BLUE, sw=1.3)
    f.text(xa + 212, cat_y + 78, "cv2: Conv 1×1 + SiLU", size=12, weight=700, fill=BLUE, anchor="middle")
    f.text(xa + 212, cat_y + 95, "512 → 256", size=11, fill=INK, anchor="middle")
    arrow(f, [(xa + 212, cat_y + 106), (xa + 212, cat_y + 124)])
    f.text(xa + 212, cat_y + 136, "Đầu ra 256×20×20 (P5 cho L20 và L10)", size=12, fill=INK, anchor="middle")
    s1, s2 = conv_p(256, 128, 1), conv_p(512, 256, 1)
    assert s1 + s2 == LAYERS[9]["p"]
    f.text(xa + 330, 120, "Tham số L9", size=12.5, weight=700, fill=DARK)
    f.text(xa + 330, 142, "cv1", size=11.5, fill=INK)
    f.text(xa + 466, 142, fmt(s1), size=11.5, fill=INK, anchor="end", mono=True)
    f.text(xa + 330, 162, "cv2", size=11.5, fill=INK)
    f.text(xa + 466, 162, fmt(s2), size=11.5, fill=INK, anchor="end", mono=True)
    f.text(xa + 330, 184, "MaxPool", size=11.5, fill=INK)
    f.text(xa + 466, 184, "0", size=11.5, fill=INK, anchor="end", mono=True)
    f.text(xa + 330, 206, "Tổng", size=11.5, weight=700, fill=INK)
    f.text(xa + 466, 206, fmt(LAYERS[9]["p"]), size=11.5, weight=700, fill=INK, anchor="end", mono=True)
    f.text(xa + 330, 236, f"{gf(LAYERS[9]['macs'])} GFLOPs", size=11.5, fill=INK)

    # ---- neck node L10..L12
    xb, wb = 514, 508
    rect(f, xb, 40, wb, 480, fill="#FFF7ED", stroke=ORANGE, sw=1.3, rx=5)
    chip(f, xb + 10, 50, 230, "L10 đến L12  nút top-down P4", ORANGE)
    mx = xb + 130
    f.text(mx, 92, "L9: 256×20×20", size=12, fill=INK, anchor="middle")
    arrow(f, [(mx, 102), (mx, 120)])
    rect(f, mx - 105, 120, 210, 44, fill="#FFF7ED", stroke=ORANGE, sw=1.3)
    f.text(mx, 136, "L10  Upsample ×2 nearest", size=12, weight=700, fill=ORANGE, anchor="middle")
    f.text(mx, 153, "256×20×20 → 256×40×40", size=10.5, fill=INK, anchor="middle")
    arrow(f, [(mx, 164), (mx, 196)])
    rect(f, mx - 105, 196, 210, 44, fill="#FFF7ED", stroke=ORANGE, sw=1.3)
    f.text(mx, 212, "L11  Concat (L10, L6)", size=12, weight=700, fill=ORANGE, anchor="middle")
    f.text(mx, 229, "256 + 128 = 384 kênh, 40×40", size=10.5, fill=INK, anchor="middle")
    f.text(xb + 270, 160, "L6: 128×40×40", size=11, weight=700, fill=GREEN)
    f.line([(xb + 300, 170), (xb + 300, 218), (mx + 105, 218)], GREEN, THIN, False)
    arrow(f, [(mx, 240), (mx, 272)])
    rect(f, mx - 105, 272, 210, 44, fill="#F0FDF4", stroke=GREEN, sw=1.3)
    f.text(mx, 288, "L12  C2f ×1 (shortcut=False)", size=12, weight=700, fill="#1B5E20", anchor="middle")
    f.text(mx, 305, "384 → 128, c = 64", size=10.5, fill=INK, anchor="middle")
    arrow(f, [(mx, 316), (mx, 340)])
    f.text(mx, 352, "Đầu ra 128×40×40", size=12, fill=INK, anchor="middle")
    q1, q2, q3 = conv_p(384, 128, 1), 2 * conv_p(64, 64, 3), conv_p(192, 128, 1)
    assert q1 + q2 + q3 == LAYERS[12]["p"]
    f.text(xb + 270, 268, "Tham số L12", size=12.5, weight=700, fill=DARK)
    for k, (t, v) in enumerate((("cv1 1×1 (384→128)", q1), ("1 Bottleneck", q2), ("cv2 1×1 (192→128)", q3))):
        f.text(xb + 270, 290 + 20 * k, t, size=11, fill=INK)
        f.text(xb + 490, 290 + 20 * k, fmt(v), size=11, fill=INK, anchor="end", mono=True)
    f.text(xb + 270, 356, "Tổng", size=11.5, weight=700, fill=INK)
    f.text(xb + 490, 356, fmt(LAYERS[12]["p"]), size=11.5, weight=700, fill=INK, anchor="end", mono=True)
    f.text(xb + 270, 380, f"{gf(LAYERS[12]['macs'])} GFLOPs", size=11.5, fill=INK)
    f.text(xb + 16, 400, "Ghép theo chiều kênh (dim=1). Upsample và Concat", size=11.5, fill=INK)
    f.text(xb + 16, 418, "không có tham số, nhưng Concat buộc hai nhánh phải", size=11.5, fill=INK)
    f.text(xb + 16, 436, "cùng H×W: nhờ L10 phóng 20×20 lên 40×40 khớp L6.", size=11.5, fill=INK)
    f.text(xb + 16, 464, "Cùng mẫu cho L13-L15 (P3, nối L4) và", size=11.5, fill=INK)
    f.text(xb + 16, 482, "L16-L21 (nối L12 và L9, bước xuống bằng Conv s2).", size=11.5, fill=INK)
    source(f, 528, "Nguồn: ultralytics 8.4.154 nn/modules/block.py (SPPF dòng 211-240), cfg/models/v8/yolov8.yaml dòng 33-47.")
    return f


# ================================================================ 4. DETECT HEAD
def fig_detect():
    W, H = 1040, 700
    f = Fig(W, H)
    f.text(14, 20, "Đầu Detect (L22): nhánh box và nhánh cls tách riêng cho P3, P4, P5, rồi giải mã DFL", size=15,
           weight=700, fill=DARK)
    box_p, cls_p, dfl = head_p()
    levels = [("P3/8", 64, 80), ("P4/16", 128, 40), ("P5/32", 256, 20)]
    xi, wi = 18, 118
    x1 = 196
    bw, gap = 120, 14
    rowh = 40
    gy = [76, 196, 316]
    chip(f, xi, 40, 100, "Đầu vào", INK)
    chip(f, x1, 40, 330, "Mỗi mức hai nhánh song song: box (xanh), cls (đỏ)", INK)
    chip(f, x1 + 3 * bw + 3 * gap + 10, 40, 100, "Đầu ra", INK)
    for k, (name, cin, side) in enumerate(levels):
        y = gy[k]
        rect(f, 8, y - 6, 724, 114, fill="#FAFAFA", stroke=GRID, sw=1, rx=5, dashed=True)
        rect(f, xi, y + 22, wi, 44, fill="#F0FDF4", stroke=GREEN, sw=1.3)
        f.text(xi + wi / 2, y + 38, name, size=12.5, weight=700, fill="#1B5E20", anchor="middle")
        f.text(xi + wi / 2, y + 55, f"{cin}×{side}×{side}", size=11, fill=INK, anchor="middle", mono=True)
        for row, (kind, last, ylab) in enumerate((("box", 64, y), ("cls", NC, y + 54))):
            ry = ylab
            arrow(f, [(xi + wi, y + 44), (xi + wi + 28, y + 44), (xi + wi + 28, ry + rowh / 2), (x1, ry + rowh / 2)],
                  BLUE if kind == "box" else RED)
            col = BLUE if kind == "box" else RED
            labels = [(f"Conv 3×3 s1", f"{cin} → 64"), (f"Conv 3×3 s1", "64 → 64"),
                      (f"Conv2d 1×1 (bias)", f"64 → {last}")]
            for j, (a, b) in enumerate(labels):
                bx = x1 + j * (bw + gap)
                fill = "#EFF6FF" if j < 2 else ("#E3F2FD" if kind == "box" else "#FDECEA")
                rect(f, bx, ry, bw, rowh, fill=fill, stroke=col, sw=1.3)
                f.text(bx + bw / 2, ry + 14, a, size=11, weight=700, fill=col, anchor="middle")
                f.text(bx + bw / 2, ry + 30, b, size=10.5, fill=INK, anchor="middle", mono=True)
                if j < 2:
                    arrow(f, [(bx + bw, ry + rowh / 2), (bx + bw + gap, ry + rowh / 2)], col)
            ox = x1 + 3 * bw + 3 * gap
            arrow(f, [(x1 + 2 * (bw + gap) + bw, ry + rowh / 2), (ox + 6, ry + rowh / 2)], col)
            f.text(ox + 12, ry + 13, f"{'box' if kind == 'box' else 'cls'}: {last}×{side}×{side}", size=11, weight=700,
                   fill=col)
            pv = (box_p if kind == "box" else cls_p)[k]
            f.text(ox + 12, ry + 30, f"{fmt(pv)} tham số", size=10.5, fill=DARK)

    # decoder column
    xd, wd = 760, 270
    chip(f, xd, 40, 200, "Giải mã (inference)", ORANGE)
    steps = [
        ("Flatten + Concat 3 mức", "boxes 1×64×8400, scores 1×5×8400", "#F8FAFC", INK),
        ("DFL", "reshape 4×16, softmax trên 16 bin,\nnhân trọng số 0..15 rồi cộng: 64 → 4", "#FFF7ED", ORANGE),
        ("dist2bbox", "anchor ∓ khoảng cách l, t, r, b\nrồi đổi sang tâm và rộng cao (xywh)", "#FFF7ED", ORANGE),
        ("× stride", "8, 16, 32 theo từng mức,\nđơn vị lưới sang pixel", "#FFF7ED", ORANGE),
        ("sigmoid(scores)", "5 điểm lớp trong (0, 1)", "#FEF2F2", RED),
        ("Concat theo kênh", "out 1×9×8400 (4 box + 5 cls)", "#F8FAFC", INK),
    ]
    sy = 70
    for k, (t, s, fl, st) in enumerate(steps):
        two = "\n" in s
        hh = 56 if two else 44
        rect(f, xd, sy, wd, hh, fill=fl, stroke=st, sw=1.3)
        f.text(xd + wd / 2, sy + 14, t, size=12, weight=700, fill=st, anchor="middle")
        for j, ln in enumerate(s.split("\n")):
            f.text(xd + wd / 2, sy + 31 + 14 * j, ln, size=10.5, fill=INK, anchor="middle")
        if k < len(steps) - 1:
            arrow(f, [(xd + wd / 2, sy + hh), (xd + wd / 2, sy + hh + 16)])
        sy += hh + 16
    f.text(xd + wd / 2, sy + 10, "DFL = Conv2d 1×1 cố định, trọng số 0..15", size=10.5, fill=GRAY, anchor="middle")

    # bottom: parameter table
    rows = []
    for k, (name, cin, side) in enumerate(levels):
        rows.append([name, f"{cin}×{side}×{side}", fmt(box_p[k]), fmt(cls_p[k]), fmt(box_p[k] + cls_p[k]),
                     f"{side * side}"])
    rows.append(["DFL (cố định)", "16 bin", "-", "-", fmt(dfl), "-"])
    rows.append(["Tổng L22", "", fmt(sum(box_p)), fmt(sum(cls_p)), fmt(HD_P), "8400"])
    f.table(18, 500, [140, 110, 120, 120, 120, 100], ["Mức", "Đầu vào", "Box (tham số)", "Cls (tham số)", "Tổng mức", "Số anchor"],
            rows, size=11.5, line_h=19)
    f.text(18, 690, "Tâm anchor là (i + 0.5, j + 0.5) trong lưới của mức đó, nhân stride ra pixel ảnh vào. "
                    "Số anchor = 80² + 40² + 20² = 6400 + 1600 + 400 = 8400.", size=11.5, fill=INK)
    source(f, 706, "Nguồn: ultralytics 8.4.154 nn/modules/head.py (Detect dòng 107-137, 178-210), block.py (DFL dòng 60-82), utils/tal.py (make_anchors, dist2bbox).")
    return f


def main():
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("ya-01-tong-quan-23-lop", fig_overview),
        ("ya-02-conv-bottleneck-c2f", fig_conv_bottleneck_c2f),
        ("ya-03-sppf-va-noi-neck", fig_sppf_neck),
        ("ya-04-detect-head", fig_detect),
    ]
    run(figures, DEFAULT_OUTDIR)


if __name__ == "__main__":
    main()
