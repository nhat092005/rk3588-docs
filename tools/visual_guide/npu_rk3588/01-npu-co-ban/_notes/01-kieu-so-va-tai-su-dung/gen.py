#!/usr/bin/env python3
"""Ghi chu chuyen de 01-kieu-so-va-tai-su-dung (Phan 1): Hinh U.1, U.2 (tier T2 chung, khung lien he RK3588 la T1).

U.1 hu-1-kieu-so-va-utilization: toc do matrix unit theo kieu so (TPU tr.3), phan ra chu ky cua TPU Table 3 (TPU tr.7)
    va cau giai thich CNN1 (TPU tr.6); lien he RK3588: so MAC moi chu ky theo kieu (TRM1 tr.1984), cot MacUsage(%)
    (UG232 tr.32), load khong phai MAC utilization (UG232 tr.137).
U.2 hu-2-tai-su-dung-va-double-buffering: spatial architecture va Fig. 1 (EYE tr.2), ba kieu input data reuse
    (EYE tr.3, tr.4), double buffering cua TPU (TPU tr.3).
So trong Table 3 go tay tu pdftotext -layout trang 7 cua TPU; vi du so hoc trong U.2 la phep tinh cua bo hinh.

Chay: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VG = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))  # docs/tools/visual_guide
sys.path.insert(0, VG)
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, Fig, run, source  # noqa: E402

W = 900
CALC = "#EAF2FF"      # phep tinh cua bo hinh
IMG = os.path.abspath(os.path.join(VG, "..", "..", "_assets", "img", "npu", "01_npu_fundamentals"))
C_USE, C_UNUSED, C_WSTALL, C_WSHIFT, C_NONMAT = "#2E7D32", "#A5D6A7", "#C62828", "#EF9A9A", "#BDBDBD"


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


def head(f, y, s):
    f.text(10, y, s, size=14, weight=700)


# ---------------------------------------------------------------------------------------------------------------
def fig_u1():
    f = Fig(W, 800)
    tier(f)
    f.text(10, 20, "Cùng một mảng MAC, vì sao không chạy ở đỉnh: kiểu số và shape của lớp", size=17, weight=700)

    # ---- A. kieu so -> toc do (TPU) ----
    head(f, 52, "A. TPU: tốc độ Matrix Unit theo độ rộng weight và activation (TPU tr.3)")
    rect(f, 10, 66, 450, 178, fill="white", stroke="#999999", rx=6)
    bars = [("8-bit weight, 8-bit activation", 1.0, "đầy đủ (256x256 MAC)"),
            ("8-bit và 16-bit trộn (một chiều 16)", 0.5, "half-speed"),
            ("cả hai 16-bit", 0.25, "quarter-speed")]
    full = 260
    for i, (name, r, lab) in enumerate(bars):
        y = 84 + i * 50
        f.text(24, y, name, size=12.5, weight=700)
        rect(f, 24, y + 10, full, 20, fill="#F2F2F2", stroke="#CCCCCC", sw=0.8, rx=2)
        rect(f, 24, y + 10, full * r, 20, fill=BLUE, stroke=BLUE, sw=0.8, rx=2)
        f.text(24 + full + 10, y + 20, f"x{r:g}  {lab}", size=12.5)
    txt(f, 24, 232, [[("Cùng phần cứng, đổi kiểu số là đổi số phép MAC mỗi chu kỳ.", "t")]], size=12)

    # RK3588 (T1)
    rect(f, 475, 66, 415, 178, fill="white", stroke=BLUE, rx=6)
    f.tier(487, 74, "T1 RK3588")
    f.text(600, 85, "Số MAC mỗi chu kỳ (TRM1 tr.1984)", size=12.5, weight=700)
    yb = f.table(487, 104, [110, 140, 140], ["Kiểu", "MAC/chu kỳ", "so với INT8"], [
        ["INT8", "1024 x 3 core", "1"],
        ["INT16", "512 x 3 core", "1/2"],
        ["FP16", "512 x 3 core", "1/2"],
        ["BF16", "512 x 3 core", "1/2"],
    ], size=12, line_h=14)
    f.text(487, yb + 12, "Cột cuối là phép tính của bộ hình: 512 / 1024.", size=11.5, fill=DARK, italic=True)

    f.unknown(10, 254, "RK3588 chạy weight 8-bit với activation 16-bit (trộn) ở tốc độ nào; TRM chỉ liệt kê từng kiểu.",
              w=880, size=12)

    # ---- B. Table 3 ----
    head(f, 302, "B. TPU Table 3: phần trăm chu kỳ của Matrix Unit (TPU tr.7), đỉnh 92 TOPS")
    rows = [("MLP0", [12.5, 0.3, 53.9, 15.9, 17.5], "12.3"),
            ("CNN0", [78.2, 0.0, 0.0, 0.0, 21.8], "86.0"),
            ("CNN1", [22.5, 23.7, 28.1, 7.0, 18.7], "14.1")]
    colors = [C_USE, C_UNUSED, C_WSTALL, C_WSHIFT, C_NONMAT]
    bx, bw = 80, 600
    f.text(bx + bw + 30, 322, "TOPS đạt", size=12.5, weight=700)
    for i, (name, vals, tops) in enumerate(rows):
        y = 334 + i * 44
        f.text(20, y + 14, name, size=13, weight=700, mono=True)
        x = bx
        for v, c in zip(vals, colors):
            wv = bw * v / 100
            if wv > 0:
                rect(f, x, y, wv, 28, fill=c, stroke="white", sw=0.8, rx=0)
                if wv >= 34:
                    f.text(x + wv / 2, y + 14, f"{v:g}%", size=11.5, weight=700,
                           fill="white" if c in (C_USE, C_WSTALL) else INK, anchor="middle")
            x += wv
        f.text(bx + bw + 30, y + 14, tops, size=13, weight=700, fill=RED if name == "CNN1" else INK)
    # legend
    leg = [(C_USE, "useful MACs (MAC giữ weight có ích)"), (C_UNUSED, "unused MACs (chu kỳ chạy nhưng MAC trống)"),
           (C_WSTALL, "weight stall (chờ nạp weight)"), (C_WSHIFT, "weight shift (dịch tile weight vào)"),
           (C_NONMAT, "non-matrix (không làm phép ma trận)")]
    for i, (c, lab) in enumerate(leg):
        lx, ly = (20 + (i % 2) * 440, 474 + (i // 2) * 20)
        rect(f, lx, ly - 7, 22, 14, fill=c, stroke="#999999", sw=0.6, rx=1)
        f.text(lx + 30, ly, lab, size=12)
    f.text(20, 540, "Hai phần xanh lá cộng lại là array active cycles (hàng 1 = hàng 2 + hàng 3 của Table 3).",
           size=11.5, fill=DARK, italic=True)

    rect(f, 10, 554, 880, 70, fill="#F7FBF7", stroke=GREEN, rx=5)
    txt(f, 22, 570, [
        [("CNN1 (TPU tr.6): ", "b"), ("\"only about half of the 65,536 MACs hold useful weights because some layers in CNN1", "t")],
        [("have shallow feature depths\". ", "t"), ("Lớp có ít kênh không lấp đầy mảng 256x256: chu kỳ vẫn chạy nhưng", "t")],
        [("nửa số MAC trống. MLP0 thì khác: 53.9% chu kỳ là chờ nạp weight (giới hạn bộ nhớ, Hình 1.4).", "t")],
    ], size=12.5, dy=18)

    # ---- C. RK3588 ----
    head(f, 648, "C. Liên hệ RK3588")
    f.tier(165, 637, "T1 RK3588")
    rect(f, 10, 662, 880, 58, fill="white", stroke=BLUE, rx=5)
    txt(f, 22, 678, [
        [("eval_perf có cột ", "t"), ("MacUsage(%)", "c"), (" = \"MAC usage\" của từng lớp (UG232 tr.32; công cụ đo ở Hình 7.3).", "t")],
        [("NPU load ", "t"), ("/sys/kernel/debug/rknpu/load", "c"), (" không phải MAC utilization: \"does not directly represent\" (UG232 tr.137).", "t")],
    ], size=12.5, dy=20)
    f.unknown(10, 728, "RK3588 lấp mảng MAC thế nào khi lớp có ít kênh; TRM không mô tả. Căn kênh theo bội: xem Hình 6.4.",
              w=880, size=12)
    source(f, 762, "Nguồn: TPU tr.3, tr.6, tr.7 (Table 3); TRM1 tr.1984; UG232 tr.32, tr.137.")
    return f


# ---------------------------------------------------------------------------------------------------------------
def fig_u2():
    f = Fig(W, 900)
    tier(f)
    f.text(10, 20, "Tái sử dụng dữ liệu trong spatial architecture và double buffering", size=17, weight=700)

    # ---- A. spatial architecture ----
    head(f, 52, "A. Spatial architecture (SA) (EYE tr.2)")
    yb = f.original(10, 64, 400, os.path.join(IMG, "eyeriss_fig1.png"),
                    ["EYE tr.2, Figure 1: hệ tăng tốc CNN gồm SA", "accelerator và off-chip DRAM; phóng to một PE."])
    rect(f, 440, 64, 450, yb - 64, fill="white", stroke="#999999", rx=6)
    txt(f, 452, 84, [
        [("Định nghĩa: ", "b"), ("lớp bộ tăng tốc khai thác song song nhờ", "t")],
        [("\"direct communication between an array of", "t")],
        [("relatively simple processing engines (PEs)\".", "t")],
        [("", "t")],
        [("So với SIMD/SIMT: ", "b"), ("SA hợp với ứng dụng có quan hệ", "t")],
        [("producer-consumer hoặc chia sẻ dữ liệu giữa một vùng PE.", "t")],
        [("", "t")],
        [("Bốn cấp lưu trữ: ", "b"), ("DRAM, global buffer, array", "t")],
        [("(liên PE) và RF; DRAM đắt nhất, RF rẻ nhất (Hình 1.3).", "t")],
        [("", "t")],
        [("Global buffer: ", "b"), ("khai thác input data reuse và che", "t")],
        [("độ trễ DRAM; thường khoảng 100–300kB.", "t")],
    ], size=12.5, dy=18)

    # ---- B. ba kieu reuse ----
    y0 = yb + 26
    head(f, y0, "B. Ba kiểu input data reuse (EYE tr.3, tr.4); ký hiệu theo EYE Table I")
    f.text(10, y0 + 20, "N = batch size, M = số filter (số kênh ofmap), H = cạnh ifmap, R = cạnh filter, E = cạnh ofmap",
           size=12, fill=DARK)
    yt = f.table(10, y0 + 34, [170, 300, 140, 90, 90, 90],
                 ["Kiểu reuse", "Dữ liệu được dùng lại", "Số lần", "CONV", "FC", "Ví dụ"], [
        ["convolutional", ("lines", ["mỗi weight trong cùng một mặt ifmap;", "mỗi pixel ifmap trong cùng một mặt filter"]),
         ("lines", ["E² lần", "thường R² lần"]), "có", "không", ("lines", ["6400", "9"])],
        ["filter", "mỗi weight qua N ifmap của batch", "N lần", "có", "có", "1"],
        ["ifmap", "mỗi pixel ifmap qua M filter", "M lần", "có", "có", "64"],
    ], size=12, line_h=16)
    rect(f, 10, yt + 8, 880, 44, fill=CALC, stroke="#90CAF9", rx=4)
    txt(f, 22, yt + 22, [
        [("Ví dụ của bộ hình: ", "b"), ("conv R = 3, E = 80, M = 64, N = 1: E² = 6400, R² = 9, M = 64. Với N = 1 (mỗi lần một ảnh),", "t")],
        [("filter reuse chỉ còn 1 lần, nên weight chỉ được dùng lại nhờ convolutional reuse.", "t")],
    ], size=12, dy=17)

    # ---- C. double buffering ----
    y1 = yt + 76
    head(f, y1, "C. Double buffering trong Matrix Unit của TPU (TPU tr.3)")
    lx, unit = 200, 70
    lanes = [("Một bộ đệm weight", [("shift", 0, 2), ("tính", 2, 2), ("shift", 4, 2), ("tính", 6, 2)]),
             ("Hai bộ đệm (double)", [("shift", 0, 2), ("tính", 2, 2), ("tính", 4, 2), ("tính", 6, 2)])]
    for i, (name, segs) in enumerate(lanes):
        y = y1 + 22 + i * 54
        f.text(20, y + 15, name, size=12.5, weight=700)
        for lab, s, d in segs:
            c = "#FFE0B2" if lab == "shift" else "#C8E6C9"
            rect(f, lx + s * unit, y, d * unit - 2, 30, fill=c, stroke="#888888", sw=0.8, rx=2)
            f.text(lx + s * unit + d * unit / 2, y + 15, lab, size=12, anchor="middle")
        if i == 1:
            for k, s in enumerate((2, 4)):
                rect(f, lx + s * unit, y + 32, 2 * unit - 2, 14, fill="#FFE0B2", stroke="#888888", sw=0.6, rx=2)
                f.text(lx + s * unit + unit, y + 39, f"shift tile {k + 2} vào bộ đệm thứ hai", size=10, anchor="middle")
    f.text(lx + 8 * unit + 12, y1 + 37, "MAC chờ", size=12, fill=RED)
    f.text(lx + 8 * unit + 12, y1 + 91, "MAC không chờ", size=12, fill=GREEN)
    rect(f, 10, y1 + 140, 880, 62, fill="white", stroke=GREEN, rx=5)
    txt(f, 22, y1 + 156, [
        [("TPU: ", "b"), ("\"one 64 KiB tile of weights plus one for double-buffering (to hide the 256 cycles it takes to shift a tile in)\".", "t")],
        [("Accumulator cũng nhân đôi: làm tròn lên 2048 rồi \"duplicated it so that the compiler could use double buffering\".", "t")],
        [("Trục thời gian ở trên là minh họa của bộ hình, chỉ có số 256 chu kỳ là của TPU.", "i")],
    ], size=12, dy=18)
    f.unknown(10, y1 + 212, ["RK3588 có double buffering dữ liệu trong buffer 384KB của core không; TRM1 tr.1984-2060 chỉ có",
                             "ping-pong cho thanh ghi cấu hình (Hình 2.5), không phải cho weight hay feature."], w=880, size=12)
    source(f, y1 + 256, "Nguồn: EYE tr.2, tr.3, tr.4 (Figure 1, Table I); TPU tr.3; TRM1 tr.1984-2060 (tìm \"double\", \"ping-pong\").")
    return f


if __name__ == "__main__":
    run([("hu-1-kieu-so-va-utilization", fig_u1), ("hu-2-tai-su-dung-va-double-buffering", fig_u2)], HERE)
