#!/usr/bin/env python3
"""Phan 7 Bo nho va hieu nang: Hinh 7.1 den 7.3.

Primary sources (see chu-thich.md, table Nguon): UG232 (ch.3, 5, 8, 10), UG152 (4.8), API232, RT232, HDR (rknn_api.h),
SRAM usage md, rknpu driver 0.9.8 (DRV), rk3588s.dtsi (DTS), DS, TRM1/TRM2, repo scripts (ai/core/rknn/benchmark.py,
ai/board/bench_npu.py), T3 logs (2026-10-10_t3-board-silu-resize), MCU/PHI (T2).

Usage: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

W = 900
UNK_FILL = "#FFF3F3"
LB = "#EAF2FF"     # phep tinh / suy ra cua bo hinh
RB = "#EAF6EA"     # so do T3 co file log
AM = "#FFF8E1"     # mot phan: co log T3 va co phan chua do
CP = "#FDECEA"     # buoc copy
AP = "#EDEDED"     # thoi gian cua ung dung
C = lambda s: [(s, "c")]  # noqa: E731


def tier(f):
    f.tier(808, 8, "T1 RK3588")


def wrap(s, n):
    return textwrap.wrap(s, n, break_long_words=False, break_on_hyphens=False)


def panel(f, x, y, w, lines, fill="white", stroke="#999999", size=12.5, line_h=19, dashed=False):
    """Bordered panel; each line is a str or rich parts list. Returns bottom y."""
    h = 14 + line_h * len(lines)
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="1"{dash}/>')
    for i, ln in enumerate(lines):
        f.rich(x + 12, y + 7 + line_h / 2 + line_h * i, ln, size=size)
    return y + h


def card(f, x, y, w, h, title, lines, size=12, title_size=15, dashed=False, fill="white"):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="#333333" '
        f'stroke-width="1.2"{dash}/>')
    f.text(x + w / 2, y + 17, title, size=title_size, weight=700, anchor="middle")
    for i, ln in enumerate(lines):
        f.text(x + w / 2, y + 38 + 16 * i, ln, size=size, anchor="middle")


def step(f, x, y, w, h, title, sub, fill="white", dashed=False, size=13):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="#333333" '
        f'stroke-width="1.2"{dash}/>')
    f.text(x + w / 2, y + h * 0.36, title, size=size, weight=700, anchor="middle")
    f.text(x + w / 2, y + h * 0.72, sub, size=11.5, anchor="middle", fill=DARK)


def rows_table(f, x, y, widths, header, rows, size=11.5, line_h=15, fills=None, dashed=None):
    """Table with per-row fill; cells are lists of lines. Returns bottom y. (helper local to this part)"""
    cells_fill = fills or {}
    f.a(f'<rect x="{x}" y="{y}" width="{sum(widths)}" height="28" fill="#E8E8E8"/>')
    cx = x
    for wd, hd in zip(widths, header):
        f.text(cx + 8, y + 14, hd, size=12.5, weight=700)
        cx += wd
    cy = y + 28
    for ri, row in enumerate(rows):
        n = max(len(c) for c in row)
        rh = 10 + line_h * n
        cx = x
        for ci, (wd, cell) in enumerate(zip(widths, row)):
            fill = cells_fill.get((ri, ci))
            if fill:
                dash = ' stroke-dasharray="5 3"' if (dashed and (ri, ci) in dashed) else ""
                stroke = RED if (dashed and (ri, ci) in dashed) else "none"
                f.a(f'<rect x="{cx}" y="{cy}" width="{wd}" height="{rh}" fill="{fill}" stroke="{stroke}"{dash}/>')
            for i, ln in enumerate(cell):
                f.rich(cx + 8, cy + 5 + line_h / 2 + i * line_h, ln, size=size)
            cx += wd
        f.a(f'<path d="M{x} {cy} L{x + sum(widths)} {cy}" stroke="#BBBBBB" stroke-width="0.8"/>')
        cy += rh
    f.a(f'<rect x="{x}" y="{y}" width="{sum(widths)}" height="{cy - y}" fill="none" stroke="#999999" stroke-width="1"/>')
    cx = x
    for wd in widths[:-1]:
        cx += wd
        f.a(f'<path d="M{cx} {y} L{cx} {cy}" stroke="#CCCCCC" stroke-width="0.8"/>')
    return cy


def source2(f, y, *lines):
    """Several italic source lines (the single-line helper in figlib overflows on long lists)."""
    for i, ln in enumerate(lines[:-1]):
        f.text(10, y + 18 + 17 * i, ln, size=12, fill=DARK, italic=True)
    source(f, y + 17 * (len(lines) - 1), lines[-1])


def open_layer(f):
    """Reserve a slot in the draw order for a layer frame whose height is only known after its content is drawn."""
    f.a("")
    return len(f.out) - 1


def close_layer(f, slot, x, y, w, bottom, title):
    h = bottom - y
    f.out[slot] = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#F5F5F5" stroke="#666666" stroke-width="1.2"/>'
                   f'<text x="{x + 14}" y="{y + 19}" font-size="15" font-weight="700" fill="#333333" '
                   f'dominant-baseline="central">{title}</text>')
    return bottom


def cells(texts, widths, size=11.5, factor=0.53):
    """Wrap each text to the column width; returns a list of wrapped-line lists."""
    return [wrap(t, max(8, int((wd - 16) / (size * factor)))) for t, wd in zip(texts, widths)]


# =====================================================================
# Hinh 7.1: duong du lieu
# =====================================================================
def fig_path():
    f = Fig(W, 2000)
    tier(f)
    # ---- layer A: memories and the NPU ----
    f.layer(10, 40, 880, 346, ["Hai bộ nhớ của SoC và buffer trong core NPU"])
    card(f, 30, 76, 250, 112, "DDR", ["bộ điều khiển: LPDDR4, LPDDR4X, LPDDR5",
                                      "4 kênh x16 bit, tối đa 2 rank mỗi kênh", "4 scheduler nối DDRCTL0 đến 3"], size=11.5)
    f.tier(30, 198, "T3 đo")
    panel(f, 30, 224, 250, ["eval_perf in DDR Current Frequency", "List: 2112000000 (đơn vị Hz)."],
          fill=RB, stroke="#2E7D32", size=12, line_h=18)
    f.unknown(30, 276, ["loại DRAM, số kênh và băng thông", "đỉnh của board RK3588S."], w=250, size=12)
    # SRAM
    card(f, 296, 158, 250, 146, "System SRAM", ["SoC có 1MB SRAM,", "956KB cấp được cho các IP",
                                                "NPU: tối đa 956KB, căn 4K",
                                                "loại bộ nhớ NPU đặt vào được:", "Internal và Weight"], size=12)
    # NPU
    f.a('<rect x="620" y="76" width="250" height="232" rx="4" fill="white" stroke="#333333" stroke-width="1.2"/>')
    f.text(745, 93, "NPU (3 core)", size=15, weight=700, anchor="middle")
    for i in range(3):
        bx = 630 + 78 * i
        f.a(f'<rect x="{bx}" y="112" width="72" height="66" rx="3" fill="#F5F5F5" stroke="#555555"/>')
        f.text(bx + 36, 128, f"core {i}", size=12, weight=700, anchor="middle")
        f.text(bx + 36, 148, "buffer", size=11.5, anchor="middle")
        f.text(bx + 36, 164, "384KB", size=12, weight=700, anchor="middle")
    f.text(745, 200, "384KB x3: buffer bên trong core", size=12, anchor="middle")
    f.text(745, 217, "(Hình 2.2, Hình 2.3)", size=12, anchor="middle", fill=BLUE)
    f.text(745, 244, "khác với 956KB của SRAM SoC", size=12, anchor="middle", fill=DARK)
    f.text(745, 261, "(không cùng một bộ nhớ)", size=12, anchor="middle", fill=DARK)
    # links
    f.line([(280, 128), (618, 128)], BLUE, THIN)
    f.line([(618, 146), (282, 146)], BLUE, THIN)
    f.text(450, 98, "AXI master: NPU lấy dữ liệu từ bộ nhớ", size=12, fill=BLUE, anchor="middle")
    f.text(450, 113, "nối vào SoC AXI interconnect (Hình 2.1)", size=12, fill=BLUE, anchor="middle")
    f.line([(546, 232), (618, 232)], RED, THIN, dashed=True, head=False)
    f.text(582, 218, "unknown", size=11.5, fill=RED, anchor="middle")
    yb = f.textbox(30, 332, 840, [
        [("Đường nối NPU tới SRAM (đường đỏ đứt) nguồn không cho; ", "t"),
         ("NPU chỉ được tài liệu nói là lấy dữ liệu qua AXI master.", "t")],
    ], size=12.5)

    # ---- layer B: three conditions to enable SRAM for the NPU ----
    y0 = 402
    slot_b = open_layer(f)
    ws = [74, 466, 320]
    rows = [
        ["Kernel", "driver RKNPU >= 0.8.0 và CONFIG_ROCKCHIP_RKNPU_SRAM=y.",
         "Board: CONFIG_ROCKCHIP_RKNPU_SRAM not set, driver 0.9.8. Trong driver, SRAM chỉ được cấp khi "
         "IS_ENABLED(CONFIG_ROCKCHIP_RKNPU_SRAM) (rknpu_gem.c:720); rknpu_mem.c không có mã SRAM; rknpu/mm không có (suy ra)."],
        ["DTS", "cấp SRAM từ system SRAM cho node rknpu: tối đa 956KB, căn 4K, thêm rockchip,sram = <&rknpu_sram>; "
                "vùng của IP khác (ví dụ codec) không được chồng lấn.",
         "DTS trong repo (không phải DTB đọc từ board): syssram 0xef000 chia cho rkvdec0_sram 0x78000 và "
         "rkvdec1_sram 0x77000; node rknpu không có rockchip,sram."],
        ["Runtime", "librknnrt >= 1.3.4b14 (SRAM md) hoặc >= 1.6.0 (UG232): mâu thuẫn. Bật bằng biến môi trường "
                    "RKNN_INTERNAL_MEM_TYPE=sram, RKNN_WEIGHT_MEM_TYPE=sram (Internal và Weight) hoặc cờ "
                    "RKNN_FLAG_ENABLE_SRAM (chỉ Internal Tensor): hai cách mâu thuẫn.",
         "unknown: hiệu lực các cờ SRAM của C API trên board này; A/B có và không SRAM chưa đo."],
    ]
    wr = [[wrap(r[0], 9), *cells(r[1:], ws[1:])] for r in rows]
    fills = {(0, 2): RB, (2, 2): UNK_FILL}
    yt = rows_table(f, 20, y0 + 30, ws, ["Lớp", "Điều kiện (T1)", "Trên board RK3588S"], wr, fills=fills, dashed={(2, 2)})
    yt = panel(f, 20, yt + 12, 860, [
        [("Chưa rõ trong tài liệu: ", "b"), ("RKNN_FLAG_SHARE_SRAM có trong header (HDR dòng 72) và RT232 mô tả như dùng được, "
                                           "nhưng UG232 nói", "t")],
        [("\"has not yet been implemented\"; RKNN_FLAG_MEMORY_TRY_ALLOC_SRAM chỉ có ở header (HDR dòng 385).", "t")],
        "UG232: SRAM giúp giảm áp lực băng thông DDR nhưng có thể ảnh hưởng thời gian suy luận: một đánh đổi cần đo, "
        "không phải lợi ích chắc chắn.",
    ], size=12, line_h=19)
    close_layer(f, slot_b, 10, y0, 880, yt + 10, "Bật SRAM cho NPU: ba lớp điều kiện (kernel, DTS, runtime)")

    # ---- layer C: copy vs zero-copy ----
    y1 = yt + 28
    slot_c = open_layer(f)
    f.text(30, y1 + 44, "General API (UG232 Figure 5-5)", size=14, weight=700)
    f.text(470, y1 + 44, "Zero-copy API (UG232 Figure 5-6), chỉ C API", size=14, weight=700)
    bw, bh, gap = 400, 50, 24
    sy = y1 + 58
    gl = [("Input từ bộ nhớ ngoài", "copy vào input memory của NPU mỗi frame (CPU)", CP),
          ("Normalize, Quantize, NHWC => NC1HWC2", "CPU; hoặc NPU khi thỏa căn lề zero-copy (input vẫn do CPU copy)", "white"),
          ("Model Inference", "NPU", LB),
          ("NC1HWC2 => NCHW/NHWC, Dequantize", "CPU", "white")]
    for i, (t, s, fl) in enumerate(gl):
        step(f, 30, sy + i * (bh + gap), bw, bh, t, s, fill=fl)
        if i:
            f.line([(230, sy + i * (bh + gap) - gap), (230, sy + i * (bh + gap))], BLUE, THIN)
    zl = [("Input: bộ nhớ cấp trước", "NPU hay nguồn khác (ví dụ DRM) dùng trực tiếp, không copy", "white"),
          ("Normalize, Quantize, Model Inference", "tất cả chạy trên NPU", LB),
          ("NC1HWC2 => NCHW, Dequantize", "CPU, hoặc NPU (hình gốc vẽ hai nhánh)", "white")]
    for i, (t, s, fl) in enumerate(zl):
        step(f, 470, sy + i * (bh + gap), bw, bh, t, s, fill=fl)
        if i:
            f.line([(670, sy + i * (bh + gap) - gap), (670, sy + i * (bh + gap))], BLUE, THIN)
    yz = sy + 2 * (bh + gap) + bh + 16
    panel(f, 470, yz, 400, [
        "UG232: zero-copy giảm chi phí copy bộ nhớ,",
        "hiệu năng tốt hơn và ít băng thông hơn;",
        "general API và zero-copy không gọi chung.",
    ], size=12, line_h=18)
    yc = sy + 4 * (bh + gap) - gap + 18
    ws2 = [190, 670]
    r2 = [
        ["Căn lề input zero-copy", "RK3588: input 4 chiều có 1, 3 hoặc 4 kênh cần Width 16-byte aligned; input không phải 4 chiều cần "
                                   "Total size 16-byte aligned (Table 5-2). Lý do quy tắc 16 byte: unknown."],
        ["Query layout input", "dùng RKNN_QUERY_NATIVE_INPUT_ATTR, không phải RKNN_QUERY_INPUT_ATTR (UG232); ví dụ "
                               "rknn_create_mem_demo.cpp dòng 205 dùng RKNN_QUERY_INPUT_ATTR: mâu thuẫn."],
        ["Cờ cấp phát (header)", "RKNN_FLAG_MEMORY_CACHEABLE = 1 << 0 (mặc định), RKNN_FLAG_MEMORY_NON_CACHEABLE = 1 << 1, "
                                 "RKNN_FLAG_MEMORY_TRY_ALLOC_SRAM = 1 << 2."],
        ["Đồng bộ cache", "bộ nhớ cacheable cần rknn_mem_sync: TO_DEVICE sau khi CPU ghi, trước khi NPU truy cập; "
                          "FROM_DEVICE sau khi NPU ghi."],
        ["Python", "RKNN-Toolkit-Lite2 2.3.2 (rknn_lite.py) không có hàm cấp phát bộ nhớ, zero-copy hay đồng bộ cache: "
                   "script tier 2 của repo (RKNNLite) dùng general API (suy ra)."],
    ]
    wr2 = [[wrap(r[0], 30), wrap(r[1], int((ws2[1] - 16) / (11.5 * 0.53)))] for r in r2]
    yt2 = rows_table(f, 20, yc, ws2, ["Điều kiện và cờ", "Nội dung (T1)"], wr2)
    close_layer(f, slot_c, 10, y1, 880, yt2 + 12, "Copy hay zero-copy: dữ liệu vào và ra khỏi NPU")
    layer_c_h = yt2 + 12 - y1

    # ---- bottom: unknown, not measured, T2 ----
    yb = y1 + layer_c_h + 16
    yb = f.unknown(10, yb, [
        "băng thông đỉnh DDR của board (không nguồn nào nêu GB/s); số kênh DDR của RK3588S;",
        "độ trễ và băng thông của SRAM nhìn từ NPU, và NPU nối cổng AXI slave nào;",
        "hiệu lực của các cờ SRAM trong C API trên board này.",
    ], w=880)
    yb = panel(f, 10, yb + 12, 880, [
        [("Chưa đo (UG232 và tài liệu có, T3 chưa làm): ", "b"),
         ("băng thông DDR đạt được; A/B có và không SRAM; zero-copy so với general API;", "t")],
        "cacheable so với non-cacheable; NC1HWC2 so với NHWC; tranh chấp DDR khi CPU, GPU, RGA cùng chạy.",
    ], fill="#F5F5F5", stroke="#999999", size=12, line_h=19, dashed=True)
    f.tier(10, yb + 14, "T2 chung")
    yb = panel(f, 10, yb + 40, 880, [
        "MCUNet (vi điều khiển, không có DRAM): \"SRAM constrains the activation size (read&write); Flash constrains the model size",
        "(read-only).\" PhiNets tách computational cost, working memory, parameter memory. Chỉ là ngữ cảnh thiết kế mạng có",
        "nhận biết bộ nhớ: không đo băng thông DDR hay NPU, không dùng làm bằng chứng cho RK3588.",
    ], fill="white", stroke="#2E7D32", size=12, line_h=19)
    y = f.legend(10, yb + 14, 880, [
        ("blue", "AXI master: NPU lấy dữ liệu từ bộ nhớ"),
        ("fill:" + RB, "T3: số đo hoặc đọc trên board, có file log"),
        ("fill:" + CP, "bước copy dữ liệu giữa bộ nhớ ngoài và NPU"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho"),
    ])
    source2(f, y + 8, "Nguồn: TRM1 tr.1984, 1985; TRM2 tr.16; DS tr.8; UG232 tr.64, 65, 69, 106, 107, 108, 112; RT232 tr.19, 34, 38;",
            "SRAM dòng 3, 4, 10, 11, 21, 22, 48, 54, 61, 68; HDR dòng 69, 72, 381-386; DRV rknpu_gem.c:720; DTS dòng 6868-6882;",
            "REPO 3rdparty/rknpu-driver-0.9.8/SOURCE.txt:7; LOG t3-board-silu-resize; MCU tr.1, 3; PHI tr.1.")
    return f


# =====================================================================
# Hinh 7.2: thanh phan do tre
# =====================================================================
def seg(f, x, y, w, h, title, sub, fill):
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#333333" stroke-width="1.2"/>')
    f.text(x + w / 2, y + h * 0.36, title, size=12.5, weight=700, anchor="middle")
    f.text(x + w / 2, y + h * 0.74, sub, size=11, anchor="middle", fill=DARK)


def bar(f, y, x1, x2, text, fill="white", stroke="#333333", dashed=False, h=28, size=12, tcolor=INK):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x1}" y="{y}" width="{x2 - x1}" height="{h}" rx="4" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="1.4"{dash}/>')
    f.text((x1 + x2) / 2, y + h / 2, text, size=size, anchor="middle", fill=tcolor)


def fig_latency():
    f = Fig(W, 2000)
    tier(f)
    f.text(10, 22, "Một con số độ trễ đo đoạn nào của một frame", size=15, weight=700)
    X0 = 200
    wd = [120, 90, 250, 90, 120]
    xs = [X0]
    for w_ in wd:
        xs.append(xs[-1] + w_)
    f.text(10, 70, "Một frame trên board", size=13, weight=700)
    f.text(10, 87, "(thứ tự thời gian,", size=12, fill=DARK)
    f.text(10, 103, "không theo tỉ lệ)", size=12, fill=DARK)
    for i, (t, s, fl) in enumerate([("pre-process", "ứng dụng", AP), ("copy vào", "I/O sang NPU", CP),
                                    ("NPU chạy model", "inference", LB), ("copy ra", "NPU sang I/O", CP),
                                    ("post-process", "ứng dụng", AP)]):
        seg(f, xs[i], 60, wd[i], 52, t, s, fl)
    f.text(X0, 126, "Màu theo cách chia của vendor (UG232): xám = user application time, hồng = input-output copy time, "
           "xanh = inference time.", size=11.5, fill=DARK)

    rows = [
        (150, "Tier 2: bench_npu.py", "trên board, RKNNLite"),
        (192, "Tier 2: e2e", ""),
        (236, "Tier 1: eval_perf", "PC điều khiển board"),
        (278, "C API: PERF_RUN", "chưa dùng"),
        (320, "PC nối board:", "rknn.inference() của Toolkit2"),
    ]
    for y, a, b in rows:
        f.text(10, y + (8 if b else 14), a, size=12.5, weight=700)
        if b:
            f.text(10, y + 23, b, size=11.5, fill=DARK)
    bar(f, 150, xs[0], xs[1], "pre", AP)
    bar(f, 150, xs[1], xs[4], "npu = thời gian lời gọi rknn.inference()", "white", dashed=True)
    bar(f, 150, xs[4], xs[5], "post", AP)
    bar(f, 192, xs[0], xs[5], "e2e: từ trước pre-process đến sau post-process", "white")
    bar(f, 236, xs[2], xs[3], "Total Time(us)", LB, stroke=BLUE)
    f.text(xs[3] + 10, 250, "unknown: có gồm copy hay không", size=11.5, fill=RED)
    bar(f, 278, xs[2], xs[3], "không gồm set input/output", "white", stroke=BLUE)
    f.text(xs[3] + 10, 292, "tài liệu RT232 tr.25", size=11.5, fill=DARK)
    bar(f, 320, xs[1], xs[4], "gồm truyền dữ liệu PC-board", CP, stroke="#333333")
    f.text(xs[4] + 10, 334, "chậm hơn eval_perf", size=11.5, fill=DARK)
    f.text(xs[0] - 4, 366, "Đọc file ảnh và giải mã đứng ngoài thang thời gian: tier 2 không tính (bench_npu.py).",
           size=12, fill=DARK, italic=True)
    f.text(10, 392, "Dấu nét đứt quanh npu: repo không tách copy khỏi chạy model bên trong lời gọi; "
           "gồm cả copy là suy ra của bộ hình.", size=11.5, fill=DARK)

    # ---- comparison table ----
    ws = [130, 375, 375]
    rows_t = [
        ["Chạy ở", "PC, điều khiển board qua rknn_server (benchmark.py)", "trên board, RKNNLite (bench_npu.py)"],
        ["Số đo chính", "eval_perf(fix_freq=True): Total Time(us) của model",
         "pre, npu, post, e2e bằng time.perf_counter quanh từng bước"],
        ["Lặp, thống kê", "5 lần eval_perf mỗi phiên, lấy trung vị",
         "20 warmup, một lượt qua tập test; mean, p50, p95, std"],
        ["Chế độ riêng", "perf_debug và eval_mem chạy ở phiên riêng vì đổi thời gian đo; "
                         "tổng của bảng lớp là thời gian chế độ debug, không phải độ trễ",
         "ghi tần số trước và sau, đo VmRSS, CPU, nhiệt độ NPU trong lượt đo"],
        ["Bảng Table G", "cột NPU (tier 1) = median of 5 eval_perf calls",
         "cột NPU P50 (tier 2), Pre, Post, E2E; FPS_latency = 1000 / E2E mean"],
    ]
    wr = [[wrap(r[0], 20), *cells(r[1:], ws[1:])] for r in rows_t]
    yt = rows_table(f, 10, 414, ws, ["", "Tier 1 (ai/core/rknn/benchmark.py)", "Tier 2 (ai/board/bench_npu.py)"], wr)

    # ---- T3 and unknown ----
    f.tier(10, yt + 16, "T3 đo")
    y = panel(f, 10, yt + 42, 880, [
        [("YOLOv8n INT8 nc=5 640x640, trọng số ngẫu nhiên, SiLU, AUTO, lượt 1 (tier 1, NPU 1000000000 Hz):", "b")],
        "eval_perf không debug, 5 lần: 17.769, 19.154, 19.432, 17.984, 19.628 ms, trung vị 19.154 ms.",
        "perf_debug=True, một lần: Total Operator Elapsed Per Frame Time 18606 us = NPUTime 17761 + CPU 845 (Transpose 823).",
        "Cùng model, CORE_0, lượt 2: trung vị 20.019 ms (18.17 đến 22.257); perf_debug một lần: 23482 us, lớn hơn cả 5 lần không debug.",
        "Hai cặp cho chiều chênh lệch khác nhau: tổng debug không phải độ trễ để báo cáo, chỉ để tìm lớp tốn thời gian.",
    ], fill=RB, stroke="#2E7D32", size=12, line_h=19)
    y = panel(f, 10, y + 12, 880, [
        [("Chưa có: ", "b"), ("log T3 của tier 2 (bench_npu.py, bench_throughput.py) trong tmp/04_debug-logs/; "
                              "mức chênh perf_debug so với không debug chưa đo riêng.", "t")],
    ], fill="#F5F5F5", stroke="#999999", size=12, line_h=19, dashed=True)
    y = f.unknown(10, y + 12, [
        "ranh giới của Total Time(us): có gồm thời gian đặt input và lấy output hay không;",
        "tách copy khỏi chạy model bên trong rknn.inference() của RKNNLite.",
    ], w=880)
    y = f.legend(10, y + 12, 880, [
        ("fill:" + AP, "thời gian của ứng dụng (pre-process, post-process)"),
        ("fill:" + CP, "copy giữa bộ nhớ ngoài và NPU"),
        ("fill:" + LB, "NPU chạy model (inference time)"),
        ("fill:" + RB, "T3: số đo trên board, có file log"),
    ])
    source2(f, y + 8, "Nguồn: UG232 tr.31, 136, 137, 171, 175, 177; API232 tr.18; RT232 tr.25;",
            "REPO ai/core/rknn/benchmark.py, ai/board/bench_npu.py, ai/board/common.py, ai/automation/tables.py; LOG t3-board-silu-resize.")
    return f


# =====================================================================
# Hinh 7.3: cong cu do
# =====================================================================
def fig_tools():
    f = Fig(W, 2000)
    tier(f)
    f.text(10, 22, "Công cụ đo bộ nhớ và hiệu năng: tài liệu có, dự án đã dùng", size=15, weight=700)
    ws = [124, 272, 262, 222]
    R = [
        ("eval_perf (perf_debug=False)",
         "tổng thời gian chạy model lấy từ phần cứng; in Current Frequency List của CPU, NPU, DDR (NPU và DDR tính bằng Hz). "
         "fix_freq=True (mặc định): thử cố định tần số CPU, NPU, DDR.",
         "chỉ có ở RKNN-Toolkit2 trên PC có nối board, RKNN-Toolkit-Lite2 không có. Tần số cố định là điều kiện để số đo có nghĩa.",
         "ĐÃ DÙNG (T3): 5 lần, trung vị; silu_opt3 AUTO 19.154 ms. Hiệu lực fix_freq: chưa đo.", RB),
        ("eval_perf (perf_debug=True)",
         "thời gian từng lớp Time(us); cột DDRCycles, NPUCycles, MaxCycles, MacUsage(%), WorkLoad(0/1/2), RW(KB); "
         "Total Memory Read/Write Per Frame Size(KB). So DDRCycles với NPUCycles (chỉ Conv): DDRCycles lớn hơn nhiều thì Conv bị giới hạn bởi băng thông, nhỏ hơn nhiều thì bởi tính toán.",
         "chế độ debug thêm mã và có thể tắt cơ chế song song nên thời gian dài hơn; "
         "RW(KB) và DDRCycles là đo hay tính từ mô hình: unknown.",
         "ĐÃ DÙNG (T3): bảng lớp; silu_opt3: 39007.21 KB mỗi frame.", RB),
        ("eval_memory (eval_mem=True)",
         "bộ nhớ của model: Weight Memory, Internal Tensor Memory, Other Memory, Total Memory. Không phải băng thông.",
         "RKNN-Toolkit2 trên PC có nối board. Đã viết trong benchmark.py (phiên riêng).",
         "CHƯA ĐO: có trong mã, không có log T3.", "white"),
        ("rknn_query (C API)",
         "PERF_RUN: thời gian chạy model, không gồm set input/output (us). PERF_DETAIL: thời gian từng lớp, cần cờ "
         "RKNN_FLAG_COLLECT_PERF_MASK lúc init, làm giảm frame rate. MEM_SIZE: weight, internal, total_sram_size, free_sram_size.",
         "chỉ ở C API: wheel RKNN-Toolkit-Lite2 2.3.2 không có hàm này; tier 2 của repo dùng Python.",
         "CHỈ TÀI LIỆU: chưa dùng, chưa đo.", "white"),
        ("rknpu/load (debugfs)",
         "NPU load: phần trăm thời gian NPU chạy task trong một đơn vị thời gian, mỗi core một số. Driver: busy time của "
         "cửa sổ trước chia (RKNPU_LOAD_INTERVAL / 100), tối đa 100. Không phải MAC utilization.",
         "cửa sổ RKNPU_LOAD_INTERVAL = 1000000000 dùng trong ktime_set(0, ...): chu kỳ 1 s là suy ra. Load thấp: NPU chờ job, "
         "kiểm copy, pre và post, đa luồng.",
         "MỘT PHẦN (T3): đọc một lần bằng sudo (2026-10-10), log không ghi NPU đang làm gì; giá trị 0% mỗi core. Khi đang chạy: chưa đo.", AM),
        ("devfreq và rknpu/freq",
         "cur_freq của NPU (fdab0000.npu) và DDR (dmc) trong /sys/class/devfreq; rknpu/freq; cố định tần số bằng governor "
         "userspace hoặc ghi rknpu/freq.",
         "rknpu/freq: driver sau 0.8.2; RK3588 cần firmware mới. lock_freq.sh của repo dùng governor performance, "
         "không dùng userspace.",
         "MỘT PHẦN (T3): NPU cur_freq 1000000000 ghi trong phaseA.json (dòng 36) và rknpu/freq 1000000000 (đọc bằng sudo); DDR dmc cur_freq: chưa có log.", AM),
        ("rknpu/mm, dmesg, SRAM",
         "rknpu/mm: bitmap SRAM (mỗi bit 4KB) và total, used, free; dmesg grep rknpu: dòng sram region.",
         "rknpu/mm chỉ có khi CONFIG_ROCKCHIP_RKNPU_SRAM bật.",
         "KHÔNG ÁP DỤNG: board có config not set; rknpu/mm không có (suy ra).", "white"),
        ("RKNN_LOG_LEVEL",
         "biến môi trường của runtime: mức 4 in thời gian từng lớp; log tốn thời gian nên đo độ trễ một frame đặt mức 1.",
         "dùng với C API trên board.",
         "CHỈ TÀI LIỆU: chưa dùng.", "white"),
    ]
    fills, dashed = {}, set()
    wr = []
    for ri, (a, b, c, d, fl) in enumerate(R):
        wr.append([wrap(a, 19), *cells([b, c, d], ws[1:])])
        if fl != "white":
            fills[(ri, 3)] = fl
    yt = rows_table(f, 10, 40, ws, ["Công cụ", "Đo gì (và không đo gì)", "Điều kiện, lưu ý", "Dự án đã dùng chưa"], wr, fills=fills)
    y = f.unknown(10, yt + 16, [
        "RW(KB) và DDRCycles là số đo hay tính từ mô hình; cơ chế fix_freq đặt tần số qua nút nào;",
        "chu kỳ lấy mẫu thực của rknpu/load (mới đọc một lần, không biết NPU đang làm gì); băng thông đỉnh DDR của board.",
    ], w=880)
    y = panel(f, 10, y + 12, 880, [
        [("Chưa đo (khối 07, mục 7.6): ", "b"), ("eval_memory; RKNN_QUERY_PERF_RUN và PERF_DETAIL bằng C API; rknpu/load khi chạy;", "t")],
        "hiệu lực của fix_freq; tranh chấp DDR khi CPU, GPU, RGA cùng chạy; băng thông DDR đạt được.",
    ], fill="#F5F5F5", stroke="#999999", size=12, line_h=19, dashed=True)
    y = f.legend(10, y + 14, 880, [
        ("fill:" + RB, "đã dùng: có file log T3 trên đĩa"),
        ("fill:" + AM, "một phần: có log T3 cho một phần, phần còn lại chưa đo"),
        ("fill:#FFFFFF", "chỉ tài liệu hoặc mã, chưa có log T3"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho"),
    ])
    source2(f, y + 8, "Nguồn: UG232 tr.31, 32, 33, 136, 137, 138, 177; UG152 tr.72, 73, 74; API232 tr.16, 18, 19; RT232 tr.25;",
            "HDR dòng 42-45, 139-143, 349-356; DRV rknpu_debugger.c, rknpu_drv.c, rknpu_drv.h; LOG t3-board-silu-resize, yolo-phaseA; "
            "REPO benchmark.py, lock_freq.sh.")
    return f


FIGS = [
    ("h7-1-duong-du-lieu", fig_path),
    ("h7-2-thanh-phan-do-tre", fig_latency),
    ("h7-3-cong-cu-do", fig_tools),
]

if __name__ == "__main__":
    run(FIGS, os.path.dirname(os.path.abspath(__file__)))
