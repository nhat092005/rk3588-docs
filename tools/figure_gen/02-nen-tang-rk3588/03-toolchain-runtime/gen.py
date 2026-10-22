#!/usr/bin/env python3
"""Chuyên đề: Toolchain và Runtime NPU RK3588 (03-toolchain-runtime).

Sinh hình vector SVG minh họa:
  1. rknn-01-layout-nc1hwc2:
     Cơ chế biến đổi định dạng dữ liệu NC1HWC2 trên phần cứng NPU Rockchip RK3588:
     - Tầng 1: Biến đổi hình học từ NCHW logic sang NC1HWC2 vật lý (C2=16, C1=⌈C/C2⌉).
     - Tầng 2: Ánh xạ 16 byte liên tục vào 16 lane SIMD MAC của NPU Core RK3588.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# docs/tools/figure_gen/02-nen-tang-rk3588/03-toolchain-runtime -> ../../.. = docs/tools/figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

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
# 1. HÌNH BIẾN ĐỔI LAYOUT NC1HWC2 (rknn-01-layout-nc1hwc2)
# ==============================================================================
def fig_layout_nc1hwc2():
    H = 475
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(14, 20, "Cơ chế biến đổi định dạng Layout NC1HWC2 trên NPU Rockchip RK3588", size=13.5, weight=700, fill=DARK)

    col_w = 415
    col_h = 358
    x1 = 20
    x2 = 445
    y_card = 46

    # ==========================================================================
    # CỘT TRÁI: BIẾN ĐỔI HÌNH HỌC TENSOR (NCHW -> NC1HWC2)
    # ==========================================================================
    rect(f, x1, y_card, col_w, col_h, fill="#F8FAFC", stroke="#64748B", sw=1.3, rx=5)
    # Header strip
    rect(f, x1, y_card, col_w, 34, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=5)
    rect(f, x1 + 10, y_card + 7, 8, 20, fill=BLUE, stroke=BLUE, sw=1, rx=2)
    f.text(x1 + 26, y_card + 17, "1. Biến đổi hình học: NCHW → NC1HWC2 (C2=16)", size=10.5, weight=700, fill="#0F172A")

    # Khối 1: Tensor logic ban đầu NCHW
    rect(f, x1 + 14, 88, col_w - 28, 54, fill="#FFFFFF", stroke="#CBD5E1", sw=1.1, rx=3)
    f.text(x1 + 24, 102, "Tensor logic NCHW: (N=1, C=13, H=4, W=4)", size=9, weight=700, fill=BLUE)
    f.text(x1 + 24, 116, "• Kênh C = 13 (không chia hết cho 16)", size=8.2, fill="#334155")
    f.text(x1 + 24, 129, "• Khoảng cách giữa 2 kênh cùng pixel: H × W = 16 byte (Strided Access)", size=8, fill="#DC2626")

    # Mũi tên chuyển đổi giữa Khối 1 và Khối 2 (dùng THIN để thân dài rõ ràng, không lỗi lint)
    mid_x1 = x1 + 130
    arrow(f, mid_x1, 142, mid_x1, 164, color=BLUE, sw=THIN)
    f.text(mid_x1 + 10, 153, "Quy tắc RK3588 (INT8): C2=16, C1=⌈13/16⌉=1", size=8, weight=700, fill=BLUE)

    # Khối 2: Tensor phần cứng NC1HWC2
    rect(f, x1 + 14, 164, col_w - 28, 116, fill="#FFFFFF", stroke=BLUE, sw=1.2, rx=3)
    f.text(x1 + 24, 178, "Tensor phần cứng NC1HWC2: (1, 1, 4, 4, 16)", size=9, weight=700, fill=BLUE)
    f.text(x1 + 24, 192, "Thứ tự địa chỉ tăng dần: C2 → W → H → C1 → N (C2 đổi nhanh nhất)", size=8, fill="#475569")

    # Vẽ 16 ô byte đại diện cho khối C2 (387 - 352 = 35px lề chia đôi)
    cell_w = 22
    cell_h = 24
    cell_y = 203
    cell_x0 = x1 + 20

    # 13 ô kênh hợp lệ (c_0 .. c_12)
    for i in range(13):
        cx = cell_x0 + i * cell_w
        rect(f, cx, cell_y, cell_w, cell_h, fill="#EFF6FF", stroke=BLUE, sw=1.0, rx=2)
        f.text(cx + cell_w / 2, cell_y + cell_h / 2, f"c{i}", size=7.5, weight=700, fill="#1E40AF", anchor="middle")

    # 3 ô kênh đệm zero-padding (c_13 .. c_15)
    for i in range(13, 16):
        cx = cell_x0 + i * cell_w
        rect(f, cx, cell_y, cell_w, cell_h, fill="#FEF2F2", stroke="#DC2626", sw=1.0, dashed=True, rx=2)
        f.text(cx + cell_w / 2, cell_y + cell_h / 2, "0", size=7.5, weight=700, fill="#DC2626", anchor="middle")

    # Thanh màu phân định dưới 16 ô (dùng rect thanh mảnh, không mũi tên)
    rect(f, cell_x0, cell_y + 27, 13 * cell_w, 3, fill=BLUE, stroke=BLUE, sw=1, rx=1)
    f.text(cell_x0 + (13 * cell_w) / 2, cell_y + 38, "13 byte dữ liệu hợp lệ (Valid Channels)", size=7.5, fill="#1E40AF", anchor="middle")

    rect(f, cell_x0 + 13 * cell_w + 2, cell_y + 27, 3 * cell_w - 2, 3, fill="#DC2626", stroke="#DC2626", sw=1, rx=1)
    f.text(cell_x0 + 13 * cell_w + 33, cell_y + 38, "3 byte đệm", size=7.5, fill="#DC2626", anchor="middle")

    f.text(x1 + col_w // 2, cell_y + 53, "→ Trọn 16 byte của cùng pixel (h, w) nằm LIỀN NHAU trong bộ nhớ RAM/SRAM", size=8, weight=700, fill="#0F172A", anchor="middle")

    # Khối 3: Đặc tính lưu trữ và định tuyến bộ nhớ
    rect(f, x1 + 14, 288, col_w - 28, 106, fill="#FFFFFF", stroke="#CBD5E1", sw=1.1, rx=3)
    f.text(x1 + 24, 303, "Đặc tính vi kiến trúc bộ nhớ NPU RK3588:", size=8.8, weight=700, fill="#0F172A")
    f.text(x1 + 24, 319, "• Không phân tán: Đọc 16 kênh trong 1 chu kỳ burst bus duy nhất.", size=8.2, fill="#166534")
    f.text(x1 + 24, 334, "• Định dạng riêng: NC1HWC2 là layout nội bộ chuyên biệt của RKNPU.", size=8.2, fill="#334155")
    f.text(x1 + 24, 349, "• Bảng quy chuẩn C2: INT8 = 16 | FP16 = 8 | INT16 = 8 [T1 UG152 tr.56].", size=8.2, fill="#1E40AF")
    f.text(x1 + 24, 364, "• Chip khác: RK3566/RK3568 có C2=8 (INT8) và C2=4 (FP16) [T1 UG232].", size=8.2, fill="#64748B")

    # ==========================================================================
    # CỘT PHẢI: ÁNH XẠ PHẦN CỨNG (16-LANE SIMD MAC)
    # ==========================================================================
    rect(f, x2, y_card, col_w, col_h, fill="#F8FAFC", stroke="#64748B", sw=1.3, rx=5)
    # Header strip
    rect(f, x2, y_card, col_w, 34, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=5)
    rect(f, x2 + 10, y_card + 7, 8, 20, fill=GREEN, stroke=GREEN, sw=1, rx=2)
    f.text(x2 + 26, y_card + 17, "2. Ánh xạ phần cứng: Nạp vào 16-Lane SIMD MAC", size=10.5, weight=700, fill="#0F172A")

    # Khối 1: Nạp từ SRAM/DDR vào 384KB Internal Buffer
    rect(f, x2 + 14, 88, col_w - 28, 54, fill="#FFFFFF", stroke="#CBD5E1", sw=1.1, rx=3)
    f.text(x2 + 24, 102, "Khối CNA (Convolution Neural Accelerator) nạp dữ liệu:", size=9, weight=700, fill=GREEN)
    f.text(x2 + 24, 116, "• Nạp trọn khối C2 (16 byte) vào Internal Buffer 384KB của Core NPU.", size=8.2, fill="#334155")
    f.text(x2 + 24, 129, "• Trọng số (Weight) và Kích hoạt (Feature) đều căn chỉnh theo khối C2.", size=8.2, fill="#334155")

    mid_x2 = x2 + 120
    arrow(f, mid_x2, 142, mid_x2, 164, color=GREEN, sw=THIN)
    f.text(mid_x2 + 10, 153, "Nạp song song 16 byte vào mảng nhân SIMD", size=8, weight=700, fill=GREEN)

    # Khối 2: Mảng 16-Lane SIMD MAC Multipliers
    rect(f, x2 + 14, 164, col_w - 28, 116, fill="#F0FDF4", stroke=GREEN, sw=1.2, rx=3)
    f.text(x2 + 24, 178, "Mảng 16-Lane SIMD Multipliers (1024 MACs INT8 / Core):", size=9, weight=700, fill=GREEN)

    # Vẽ 4 cụm đại diện cho 16 lane (Lane 0, Lane 1, ... Lane 12, Lane 13-15)
    lane_y = 194
    lane_w = 82
    lane_h = 34

    # Cụm 1: Lane 0
    rect(f, x2 + 24, lane_y, lane_w, lane_h, fill="#FFFFFF", stroke=GREEN, sw=1.0, rx=3)
    f.text(x2 + 24 + lane_w / 2, lane_y + 11, "Lane 0 (c0)", size=7.8, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 24 + lane_w / 2, lane_y + 24, "x_0 × w_0", size=8, fill="#0F172A", anchor="middle")

    # Cụm 2: Lane 1
    rect(f, x2 + 116, lane_y, lane_w, lane_h, fill="#FFFFFF", stroke=GREEN, sw=1.0, rx=3)
    f.text(x2 + 116 + lane_w / 2, lane_y + 11, "Lane 1 (c1)", size=7.8, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 116 + lane_w / 2, lane_y + 24, "x_1 × w_1", size=8, fill="#0F172A", anchor="middle")

    # Dấu ... ở giữa
    f.text(x2 + 210, lane_y + 17, "...", size=14, weight=700, fill="#64748B", anchor="middle")

    # Cụm 3: Lane 12
    rect(f, x2 + 220, lane_y, lane_w, lane_h, fill="#FFFFFF", stroke=GREEN, sw=1.0, rx=3)
    f.text(x2 + 220 + lane_w / 2, lane_y + 11, "Lane 12 (c12)", size=7.8, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 220 + lane_w / 2, lane_y + 24, "x_12 × w_12", size=8, fill="#0F172A", anchor="middle")

    # Cụm 4: Lane 13-15 (Lãng phí do padding)
    rect(f, x2 + 312, lane_y, lane_w, lane_h, fill="#FEF2F2", stroke="#DC2626", sw=1.0, dashed=True, rx=3)
    f.text(x2 + 312 + lane_w / 2, lane_y + 11, "Lane 13..15", size=7.8, weight=700, fill="#DC2626", anchor="middle")
    f.text(x2 + 312 + lane_w / 2, lane_y + 24, "0 × 0 (Lãng phí)", size=8, fill="#DC2626", anchor="middle")

    # Cây cộng gom Psum (Accumulator)
    arrow(f, x2 + col_w // 2, lane_y + lane_h, x2 + col_w // 2, lane_y + lane_h + 16, color=GREEN, sw=THIN)
    rect(f, x2 + 50, lane_y + lane_h + 16, col_w - 100, 22, fill="#FFFFFF", stroke=GREEN, sw=1.0, rx=3)
    f.text(x2 + col_w // 2, lane_y + lane_h + 27, "Cây cộng gom Accumulator: Psum = ∑ (x_i × w_i) trong 1 chu kỳ", size=8, weight=700, fill=GREEN, anchor="middle")

    # Khối 3: Khuyến nghị tối ưu hóa mô hình từ hãng
    rect(f, x2 + 14, 288, col_w - 28, 106, fill="#FFFBEB", stroke=ORANGE, sw=1.2, rx=3)
    f.text(x2 + 24, 303, "Khuyến nghị thiết kế mô hình từ Rockchip (UG232 mục 8.4):", size=8.8, weight=700, fill="#92400E")
    f.text(x2 + 24, 319, "+ Kênh C chia hết cho 16/32: 100% Lane MAC tính toán, 0 byte lãng phí.", size=8.2, fill="#166534")
    f.text(x2 + 24, 334, "- Kênh C không chia hết: Phải nhân vô ích với 0, giảm hiệu suất tính toán.", size=8.2, fill="#B91C1C")
    f.text(x2 + 24, 349, "• Không bắt buộc: Mô hình kênh bất kỳ vẫn chạy đúng nhờ zero-padding.", size=8.2, fill="#334155")
    f.text(x2 + 24, 364, "• Tối ưu thực tế: Nên thiết kế số kênh là bội số của 16/32 để đạt đỉnh TOPS.", size=8.2, fill="#92400E")

    # ==========================================================================
    # KHỐI KẾT LUẬN DƯỚI CÙNG (3 dòng rõ ràng, không tràn mép)
    # ==========================================================================
    rect(f, 20, 412, 840, 50, fill="#F8FAFC", stroke="#64748B", sw=1.1, rx=4)
    f.text(32, 424, "Bản chất định dạng NC1HWC2 trên NPU RK3588:", size=9.5, weight=700, fill="#0F172A")
    f.text(32, 439, "• Biến đổi truy cập bộ nhớ từ phân tán (strided access trên NCHW) thành truy cập cụm tuyến tính 16-byte burst.", size=8.5, fill="#334155")
    f.text(32, 452, "• Khớp hoàn hảo với chiều rộng vector bus của 3 lõi NPU (mỗi lõi đạt 1024 MACs INT8/chu kỳ tại 1 GHz) [T1 UG232, TRM1].", size=8.5, fill="#334155")

    source(f, H - 10, "[T1 UG232 tr.61, Fig. 5-1, Table 5-1] [T1 UG152 tr.56] [T1 TRM1 tr.1984-1985]")
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
