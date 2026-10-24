#!/usr/bin/env python3
"""Chuyên đề: Toolchain và Runtime NPU RK3588 (03-toolchain-runtime).

Sinh hình vector SVG minh họa:
  1. rknn-01-layout-nc1hwc2:
     Trực quan hóa cấu trúc bộ nhớ và luồng thực thi phần cứng của định dạng NC1HWC2:
     - So sánh bố cục bộ nhớ NCHW (Strided Access) vs NC1HWC2 (Contiguous 16-Byte Burst).
     - Ánh xạ 1 chu kỳ burst trực tiếp vào mảng 16-lane SIMD MAC của RKNPU Core.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "02-nen-tang-rk3588", "03-toolchain-runtime"
    )
)

W = 880
BOX_STROKE = "#334155"
ORANGE = "#D97706"


def tier(f, label, x=W - 130, y=14):
    f.tier(x, y, label)


def rect(f, x, y, w, h, fill="white", stroke=BOX_STROKE, sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    r_attr = f' rx="{rx}" ry="{rx}"' if rx else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}"{r_attr} fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN, dashed=False):
    if color not in (BLUE, GREEN, RED, GRAY, INK):
        color = INK
    f.line([(x1, y1), (x2, y2)], color, width=sw, dashed=dashed, head=True)


# ==============================================================================
# 1. HÌNH BIẾN ĐỔI LAYOUT NC1HWC2 (rknn-01-layout-nc1hwc2) - VISUAL-FIRST
# ==============================================================================
def fig_layout_nc1hwc2():
    H = 376
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(14, 22, "Cơ chế biến đổi Layout NC1HWC2 và ánh xạ 16-Lane SIMD MAC trên RKNPU RK3588",
           size=14, weight=700, fill=DARK)

    # --------------------------------------------------------------------------
    # KHỐI TRÊN BÊN TRÁI: NCHW LOGICAL (STRIDED MEMORY ACCESS)
    # --------------------------------------------------------------------------
    card_w = 415
    card_h = 172
    x_left = 18
    y_top = 44

    rect(f, x_left, y_top, card_w, card_h, fill="#F8FAFC", stroke="#94A3B8", sw=1.3, rx=6)
    rect(f, x_left, y_top, card_w, 26, fill="#FFFFFF", stroke="#94A3B8", sw=1.0, rx=6)
    rect(f, x_left + 8, y_top + 4, 6, 18, fill=RED, stroke=RED, sw=1, rx=2)
    f.text(x_left + 22, y_top + 14, "A. Bố cục logic NCHW: Truy cập bộ nhớ bị phân tán",
           size=11, weight=700, fill="#991B1B")

    # 3 mặt phẳng kênh c0, c1, c12
    pw, ph = 46, 38
    p0_y = y_top + 34

    # Kênh c0
    rect(f, x_left + 16, p0_y, pw, ph, fill="#EFF6FF", stroke=BLUE, sw=1.1, rx=2)
    f.text(x_left + 16 + pw / 2, p0_y + 10, "Kênh c0", size=7.8, weight=700, fill=BLUE, anchor="middle")
    rect(f, x_left + 22, p0_y + 17, 15, 15, fill=BLUE, stroke=BLUE, rx=2)
    f.text(x_left + 29.5, p0_y + 24.5, "p0", size=7.2, weight=700, fill="white", anchor="middle")

    # Kênh c1
    rect(f, x_left + 70, p0_y, pw, ph, fill="#EFF6FF", stroke=BLUE, sw=1.1, rx=2)
    f.text(x_left + 70 + pw / 2, p0_y + 10, "Kênh c1", size=7.8, weight=700, fill=BLUE, anchor="middle")
    rect(f, x_left + 76, p0_y + 17, 15, 15, fill=BLUE, stroke=BLUE, rx=2)
    f.text(x_left + 83.5, p0_y + 24.5, "p0", size=7.2, weight=700, fill="white", anchor="middle")

    f.text(x_left + 124, p0_y + 20, "...", size=13, weight=700, fill=GRAY, anchor="middle")

    # Kênh c12
    rect(f, x_left + 136, p0_y, pw, ph, fill="#EFF6FF", stroke=BLUE, sw=1.1, rx=2)
    f.text(x_left + 136 + pw / 2, p0_y + 10, "Kênh c12", size=7.8, weight=700, fill=BLUE, anchor="middle")
    rect(f, x_left + 142, p0_y + 17, 15, 15, fill=BLUE, stroke=BLUE, rx=2)
    f.text(x_left + 149.5, p0_y + 24.5, "p0", size=7.2, weight=700, fill="white", anchor="middle")

    f.text(x_left + 196, y_top + 42, "Tensor logic: (1, 13, 4, 4)", size=8.8, weight=700, fill=DARK)
    f.text(x_left + 196, y_top + 56, "• Bước nhảy 2 kênh: H×W = 16B", size=8.2, fill="#64748B")
    f.text(x_left + 196, y_top + 69, "• p0 phân tán tại 13 vị trí rời rạc", size=8.2, fill="#DC2626")

    # Thanh RAM tuyến tính NCHW
    mem_y = y_top + 88
    f.text(x_left + 16, mem_y - 5, "Dòng địa chỉ DDR vật lý (NCHW):", size=8.2, weight=700, fill=DARK)

    bw = 32
    bh = 22
    bx0 = x_left + 16

    rect(f, bx0, mem_y + 2, bw, bh, fill=BLUE, stroke=BLUE, rx=2)
    f.text(bx0 + bw / 2, mem_y + 2 + bh / 2, "c0[0]", size=7.2, weight=700, fill="white", anchor="middle")

    rect(f, bx0 + 34, mem_y + 2, 46, bh, fill="#E2E8F0", stroke="#94A3B8", rx=2)
    f.text(bx0 + 57, mem_y + 2 + bh / 2, "c0[1..15]", size=7.2, fill="#475569", anchor="middle")

    rect(f, bx0 + 82, mem_y + 2, bw, bh, fill=BLUE, stroke=BLUE, rx=2)
    f.text(bx0 + 82 + bw / 2, mem_y + 2 + bh / 2, "c1[0]", size=7.2, weight=700, fill="white", anchor="middle")

    rect(f, bx0 + 116, mem_y + 2, 46, bh, fill="#E2E8F0", stroke="#94A3B8", rx=2)
    f.text(bx0 + 139, mem_y + 2 + bh / 2, "c1[1..15]", size=7.2, fill="#475569", anchor="middle")

    f.text(bx0 + 172, mem_y + 2 + bh / 2, "...", size=12, weight=700, fill=GRAY, anchor="middle")

    rect(f, bx0 + 188, mem_y + 2, bw, bh, fill=BLUE, stroke=BLUE, rx=2)
    f.text(bx0 + 188 + bw / 2, mem_y + 2 + bh / 2, "c12[0]", size=7.2, weight=700, fill="white", anchor="middle")

    rect(f, bx0 + 222, mem_y + 2, 46, bh, fill="#E2E8F0", stroke="#94A3B8", rx=2)
    f.text(bx0 + 245, mem_y + 2 + bh / 2, "c12[1..15]", size=7.2, fill="#475569", anchor="middle")

    # Nhãn cảnh báo hiệu năng
    rect(f, x_left + 14, mem_y + 32, card_w - 28, 42, fill="#FEF2F2", stroke="#DC2626", sw=1.1, rx=4)
    f.text(x_left + card_w / 2, mem_y + 46, "13 lần nhảy địa chỉ (Stride = 16 byte) để đọc đủ pixel p0",
           size=8.5, weight=700, fill="#B91C1C", anchor="middle")
    f.text(x_left + card_w / 2, mem_y + 61, "Gây phân mảnh bus DDR và lãng phí băng thông nạp dữ liệu",
           size=8, fill="#7F1D1D", anchor="middle")

    # --------------------------------------------------------------------------
    # KHỐI TRÊN BÊN PHẢI: NC1HWC2 PHYSICAL (CONTIGUOUS 16-BYTE BURST)
    # --------------------------------------------------------------------------
    x_right = 447
    rect(f, x_right, y_top, card_w, card_h, fill="#F8FAFC", stroke="#059669", sw=1.3, rx=6)
    rect(f, x_right, y_top, card_w, 26, fill="#FFFFFF", stroke="#059669", sw=1.0, rx=6)
    rect(f, x_right + 8, y_top + 4, 6, 18, fill=GREEN, stroke=GREEN, sw=1, rx=2)
    f.text(x_right + 22, y_top + 14, "B. Bố cục vật lý NC1HWC2: Đóng gói cụm 16 byte liên tục",
           size=11, weight=700, fill="#047857")

    f.text(x_right + 14, y_top + 36, "Quy tắc RKNPU (INT8): C2 = 16, C1 = ⌈13/16⌉ = 1 → Shape (1, 1, 4, 4, 16)",
           size=8.2, weight=700, fill="#065F46")
    f.text(x_right + 14, y_top + 49, "Thứ tự địa chỉ trong bộ nhớ: C2 → W → H → C1 → N",
           size=8, fill="#334155")

    # Vẽ 16 ô byte liền kề nhau
    cell_w = 23
    cell_h = 26
    cell_y = y_top + 59
    cell_x0 = x_right + 14

    for i in range(13):
        cx = cell_x0 + i * cell_w
        rect(f, cx, cell_y, cell_w - 2, cell_h, fill="#ECFDF5", stroke="#059669", sw=1.1, rx=2)
        f.text(cx + (cell_w - 2) / 2, cell_y + 9, f"c{i}", size=7.2, weight=700, fill="#047857", anchor="middle")
        f.text(cx + (cell_w - 2) / 2, cell_y + 19, "1B", size=6.5, fill="#64748B", anchor="middle")

    for i in range(13, 16):
        cx = cell_x0 + i * cell_w
        rect(f, cx, cell_y, cell_w - 2, cell_h, fill="#FEF2F2", stroke="#DC2626", sw=1.1, dashed=True, rx=2)
        f.text(cx + (cell_w - 2) / 2, cell_y + 9, "0", size=7.2, weight=700, fill="#DC2626", anchor="middle")
        f.text(cx + (cell_w - 2) / 2, cell_y + 19, "pad", size=6.5, fill="#DC2626", anchor="middle")

    rect(f, cell_x0, cell_y + cell_h + 3, 13 * cell_w - 2, 2, fill=GREEN, stroke=GREEN, rx=1)
    f.text(cell_x0 + (13 * cell_w) / 2, cell_y + cell_h + 12, "13 kênh hợp lệ",
           size=7.2, weight=700, fill="#047857", anchor="middle")

    rect(f, cell_x0 + 13 * cell_w, cell_y + cell_h + 3, 3 * cell_w - 2, 2, fill=RED, stroke=RED, rx=1)
    f.text(cell_x0 + 14.5 * cell_w, cell_y + cell_h + 12, "3B đệm 0",
           size=7.2, weight=700, fill="#DC2626", anchor="middle")

    rect(f, x_right + 14, cell_y + cell_h + 20, card_w - 28, 48, fill="#F0FDF4", stroke="#059669", sw=1.1, rx=4)
    f.text(x_right + card_w / 2, cell_y + cell_h + 35, "Đúng 1 chu kỳ đọc Bus Burst 16 byte (128-bit AXI)",
           size=8.8, weight=700, fill="#047857", anchor="middle")
    f.text(x_right + card_w / 2, cell_y + cell_h + 51, "Tải trọn vẹn mọi kênh của pixel p0 vào đệm SRAM NPU mà không cần nhảy địa chỉ.",
           size=8, fill="#065F46", anchor="middle")

    # --------------------------------------------------------------------------
    # KHỐI DƯỚI: ÁNH XẠ TRỰC TIẾP VÀO 16-LANE SIMD MAC TRÊN NPU CORE
    # --------------------------------------------------------------------------
    y_bot = 226
    card_h_bot = 140
    rect(f, x_left, y_bot, W - 36, card_h_bot, fill="#FFFFFF", stroke="#3B82F6", sw=1.4, rx=6)
    rect(f, x_left, y_bot, W - 36, 26, fill="#EFF6FF", stroke="#3B82F6", sw=1.0, rx=6)
    rect(f, x_left + 8, y_bot + 4, 6, 18, fill=BLUE, stroke=BLUE, sw=1, rx=2)
    f.text(x_left + 22, y_bot + 14, "C. Ánh xạ phần cứng: 16 Byte nạp song song vào 16-Lane SIMD MAC (1 Chu kỳ xung nhịp)",
           size=11, weight=700, fill="#1E40AF")

    # 16 Lane SIMD
    lane_y = y_bot + 34
    lw = 47
    lh = 46
    lane_x0 = x_left + 16
    gap = 5

    for i in range(13):
        lx = lane_x0 + i * (lw + gap)
        rect(f, lx, lane_y, lw, lh, fill="#F0FDF4", stroke="#16A34A", sw=1.1, rx=3)
        f.text(lx + lw / 2, lane_y + 11, f"Lane {i}", size=7.2, weight=700, fill="#15803D", anchor="middle")
        f.text(lx + lw / 2, lane_y + 24, f"x_{i}·w_{i}", size=7.5, weight=700, fill=DARK, anchor="middle")
        f.text(lx + lw / 2, lane_y + 36, "8b MAC", size=6.8, fill="#64748B", anchor="middle")

    for i in range(13, 16):
        lx = lane_x0 + i * (lw + gap)
        rect(f, lx, lane_y, lw, lh, fill="#FEF2F2", stroke="#DC2626", sw=1.1, dashed=True, rx=3)
        f.text(lx + lw / 2, lane_y + 11, f"Lane {i}", size=7.2, weight=700, fill="#DC2626", anchor="middle")
        f.text(lx + lw / 2, lane_y + 24, "0 · 0", size=7.5, weight=700, fill="#DC2626", anchor="middle")
        f.text(lx + lw / 2, lane_y + 36, "Idle (Pad)", size=6.8, fill="#DC2626", anchor="middle")

    # Cây cộng gom Psum Adder Tree
    tree_y = lane_y + lh + 8
    total_lanes_w = 16 * (lw + gap) - gap
    rect(f, lane_x0, tree_y, total_lanes_w, 24, fill="#EFF6FF", stroke="#2563EB", sw=1.1, rx=3)
    f.text(lane_x0 + total_lanes_w / 2, tree_y + 13,
           "Cây cộng gom 16 phần tử (Adder Tree): Psum = ∑_{i=0}^{12} (x_i · w_i) + 0 → Hoàn tất tích vô hướng trong 1 chu kỳ",
           size=8.5, weight=700, fill="#1E40AF", anchor="middle")

    # Thanh trạng thái hiệu suất
    stat_y = tree_y + 30
    rect(f, lane_x0, stat_y, 395, 22, fill="#ECFDF5", stroke="#059669", rx=2)
    f.text(lane_x0 + 197, stat_y + 11, "Hiệu suất tính toán MAC: 13 / 16 Lane hoạt động (81.25%)",
           size=8.2, weight=700, fill="#047857", anchor="middle")

    rect(f, lane_x0 + 407, stat_y, 419, 22, fill="#FFFBEB", stroke=ORANGE, rx=2)
    f.text(lane_x0 + 616, stat_y + 11, "Khuyến nghị thiết kế YOLO: Kênh C là bội số của 16 → Đạt đỉnh 100% Lane hữu dụng",
           size=8.2, weight=700, fill="#B45309", anchor="middle")

    source(f, H - 12, "[T1 UG232 tr.61, Fig. 5-1, Table 5-1] [T1 UG152 tr.56] [T1 TRM1 tr.1984-1985]")
    return f


# ==============================================================================
# HÀM RUN
# ==============================================================================
if __name__ == "__main__":
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("rknn-01-layout-nc1hwc2", fig_layout_nc1hwc2),
    ]
    run(figures, DEFAULT_OUTDIR)
