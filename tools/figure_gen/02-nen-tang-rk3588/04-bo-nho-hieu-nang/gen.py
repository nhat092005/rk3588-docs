#!/usr/bin/env python3
"""Chuyên đề: Bộ nhớ và Hiệu năng NPU RK3588 (04-bo-nho-hieu-nang).

Sinh hình vector SVG minh họa:
  1. rknn-02-zero-copy-vs-general-api:
     So sánh cơ chế quản lý bộ nhớ và luồng dữ liệu:
     - General API: 2 lần CPU memcpy, CPU chuyển kiểu dữ liệu, tốn băng thông bus DDR.
     - Zero-Copy API: Bộ đệm chia sẻ DMA-BUF / DRM, 0 lần memcpy, NPU tự tiền xử lý INT8.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# docs/tools/figure_gen/02-nen-tang-rk3588/04-bo-nho-hieu-nang -> ../../.. = docs/tools/figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "02-nen-tang-rk3588", "04-bo-nho-hieu-nang"
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
# 1. HÌNH ZERO-COPY VS GENERAL API (rknn-02-zero-copy-vs-general-api)
# ==============================================================================
def fig_zero_copy_vs_general():
    H = 478
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(14, 20, "So sánh cơ chế luân chuyển bộ nhớ: General API vs Zero-Copy API trên RK3588", size=13.5, weight=700, fill=DARK)

    col_w = 415
    col_h = 358
    x1 = 20
    x2 = 445
    y_card = 46

    # ==========================================================================
    # CỘT TRÁI: GENERAL API (API THÔNG THƯỜNG - TỐN MEMCPY)
    # ==========================================================================
    rect(f, x1, y_card, col_w, col_h, fill="#FFF9F9", stroke=RED, sw=1.3, rx=5)
    # Header strip
    rect(f, x1, y_card, col_w, 34, fill="#FFFFFF", stroke=RED, sw=1.0, rx=5)
    rect(f, x1 + 10, y_card + 7, 8, 20, fill=RED, stroke=RED, sw=1, rx=2)
    f.text(x1 + 26, y_card + 17, "1. General API: rknn_inputs_set / rknn_outputs_get", size=10.5, weight=700, fill=RED)

    # Bước 1: User Virtual Memory
    rect(f, x1 + 14, 88, col_w - 28, 30, fill="#FFFFFF", stroke="#CBD5E1", sw=1.1, rx=3)
    f.text(x1 + col_w // 2, 103, "1. Bộ đệm ứng dụng User (RAM CPU / Virtual Address)", size=8.5, weight=700, fill="#0F172A", anchor="middle")

    # Mũi tên copy lần 1 (CPU memcpy) và nhãn bên cạnh
    mid1 = x1 + col_w // 2
    arrow(f, mid1, 118, mid1, 148, color=RED, sw=THIN)
    f.text(mid1 + 10, 133, "CPU memcpy (Lần 1) + CPU Normalize/Quantize", size=7.8, weight=700, fill=RED)

    # Bước 2: NPU Input Buffer (DRAM cấp riêng)
    rect(f, x1 + 14, 148, col_w - 28, 30, fill="#FFFFFF", stroke=RED, sw=1.1, rx=3)
    f.text(x1 + col_w // 2, 163, "2. NPU Input Memory (DDR do Runtime cấp riêng)", size=8.5, weight=700, fill=RED, anchor="middle")

    # Mũi tên DMA vào NPU
    arrow(f, mid1, 178, mid1, 196, color=INK, sw=THIN)
    f.text(mid1 + 10, 187, "DMA tải từ DDR vào SRAM", size=7.5, fill="#475569")

    # Bước 3: NPU Core tính toán
    rect(f, x1 + 14, 196, col_w - 28, 34, fill="#F1F5F9", stroke="#475569", sw=1.2, rx=3)
    f.text(x1 + col_w // 2, 207, "3. NPU Core RK3588 (Thực thi mô hình INT8 / 1 GHz)", size=8.8, weight=700, fill="#0F172A", anchor="middle")
    f.text(x1 + col_w // 2, 221, "Tính toán trên mảng MAC; xuất kết quả dạng tensor thô", size=7.5, fill="#64748B", anchor="middle")

    # Mũi tên DMA ra DDR
    arrow(f, mid1, 230, mid1, 248, color=INK, sw=THIN)
    f.text(mid1 + 10, 239, "DMA ghi kết quả ra DDR", size=7.5, fill="#475569")

    # Bước 4: NPU Output Buffer (DRAM cấp riêng)
    rect(f, x1 + 14, 248, col_w - 28, 30, fill="#FFFFFF", stroke=RED, sw=1.1, rx=3)
    f.text(x1 + col_w // 2, 263, "4. NPU Output Memory (DDR do Runtime cấp riêng)", size=8.5, weight=700, fill=RED, anchor="middle")

    # Mũi tên copy lần 2 (CPU memcpy) và nhãn bên cạnh
    arrow(f, mid1, 278, mid1, 308, color=RED, sw=THIN)
    f.text(mid1 + 10, 293, "CPU memcpy (Lần 2) + CPU Dequantize/Layout", size=7.8, weight=700, fill=RED)

    # Bước 5: User Output Buffer
    rect(f, x1 + 14, 308, col_w - 28, 30, fill="#FFFFFF", stroke="#CBD5E1", sw=1.1, rx=3)
    f.text(x1 + col_w // 2, 323, "5. User Output Buffer (Ứng dụng nhận kết quả FP32)", size=8.5, weight=700, fill="#0F172A", anchor="middle")

    # Khung đánh giá nhược điểm
    rect(f, x1 + 14, 344, col_w - 28, 52, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=3)
    f.text(x1 + 22, 357, "Nhược điểm hiệu năng General API (UG232 tr.64):", size=8.2, weight=700, fill=RED)
    f.text(x1 + 22, 370, "• Tốn 2 lần CPU memcpy ở mỗi frame, gây nghẽn nhân CPU.", size=7.8, fill="#334155")
    f.text(x1 + 22, 384, "• Tăng gấp đôi lưu lượng bus DDR do phải trung chuyển bộ đệm.", size=7.8, fill="#334155")

    # ==========================================================================
    # CỘT PHẢI: ZERO-COPY API (BỘ NHỚ CHIA SẺ DMA-BUF - 0 LẦN MEMCPY)
    # ==========================================================================
    rect(f, x2, y_card, col_w, col_h, fill="#F0FDF4", stroke=GREEN, sw=1.3, rx=5)
    # Header strip
    rect(f, x2, y_card, col_w, 34, fill="#FFFFFF", stroke=GREEN, sw=1.0, rx=5)
    rect(f, x2 + 10, y_card + 7, 8, 20, fill=GREEN, stroke=GREEN, sw=1, rx=2)
    f.text(x2 + 26, y_card + 17, "2. Zero-Copy API: rknn_create_mem / rknn_set_io_mem", size=10.5, weight=700, fill=GREEN)

    # Bước 1: Shared Input DMA-BUF
    mid2 = x2 + col_w // 2
    rect(f, x2 + 14, 88, col_w - 28, 48, fill="#FFFFFF", stroke=GREEN, sw=1.2, rx=3)
    f.text(x2 + 22, 102, "1. Shared Input DMA-BUF (Cấp phát trước bằng DRM / DMA)", size=8.8, weight=700, fill=GREEN)
    f.text(x2 + 22, 116, "• Camera ISP / Bộ giải mã phần cứng RGA ghi trực tiếp vào buffer này.", size=7.8, fill="#334155")
    f.text(x2 + 22, 128, "• Liên kết tức thì qua rknn_set_io_mem() | 0 lần memcpy!", size=7.8, weight=700, fill="#1E40AF")

    # Mũi tên trực tiếp từ DMA-BUF vào NPU và nhãn bên cạnh
    arrow(f, mid2, 136, mid2, 170, color=GREEN, sw=THIN)
    f.text(mid2 + 10, 153, "Direct DMA Read (Đọc thẳng từ DMA-BUF)", size=7.8, weight=700, fill=GREEN)

    # Bước 2: NPU Core tự làm tiền xử lý & tính toán
    rect(f, x2 + 14, 170, col_w - 28, 64, fill="#FFFFFF", stroke=GREEN, sw=1.2, rx=3)
    f.text(mid2, 184, "2. NPU Core RK3588 (Xử lý toàn bộ trên phần cứng NPU)", size=8.8, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 22, 199, "• Tự động trừ mean, nhân scale (Quantize) bằng phần cứng NPU.", size=8, fill="#166534")
    f.text(x2 + 22, 213, "• Tính toán 1024 MACs INT8 không phụ thuộc CPU.", size=8, fill="#334155")
    f.text(x2 + 22, 226, "• Bắt buộc input width căn lề bội số 16 byte [T1 OPL tr.335].", size=7.8, fill="#D97706")

    # Mũi tên trực tiếp từ NPU ra Output DMA-BUF và nhãn bên cạnh
    arrow(f, mid2, 234, mid2, 268, color=GREEN, sw=THIN)
    f.text(mid2 + 10, 251, "Direct DMA Write (Ghi thẳng vào DMA-BUF)", size=7.8, weight=700, fill=GREEN)

    # Bước 3: Shared Output DMA-BUF
    rect(f, x2 + 14, 268, col_w - 28, 48, fill="#FFFFFF", stroke=GREEN, sw=1.2, rx=3)
    f.text(x2 + 22, 282, "3. Shared Output DMA-BUF (Chia sẻ trực tiếp tới VOP / App)", size=8.8, weight=700, fill=GREEN)
    f.text(x2 + 22, 296, "• NPU xuất tensor trực tiếp vào vùng nhớ đích của bộ hiển thị VOP.", size=7.8, fill="#334155")
    f.text(x2 + 22, 308, "• Nếu bộ nhớ cacheable: gọi rknn_mem_sync() để đồng bộ cache [T1].", size=7.8, fill="#1E40AF")

    # Khung đánh giá ưu điểm
    rect(f, x2 + 14, 324, col_w - 28, 72, fill="#FFFFFF", stroke=GREEN, sw=1.0, rx=3)
    f.text(x2 + 22, 337, "Ưu thế vượt trội của Zero-Copy API (UG232 tr.64):", size=8.2, weight=700, fill=GREEN)
    f.text(x2 + 22, 350, "+ Triệt tiêu 100% memcpy: Giảm tải CPU từ 50-80% xuống gần 0%.", size=7.8, fill="#166534")
    f.text(x2 + 22, 363, "+ Tiết kiệm 50% băng thông DDR: Dữ liệu nạp thẳng từ DMA-BUF vào NPU.", size=7.8, fill="#166534")
    f.text(x2 + 22, 376, "+ Giảm độ trễ I/O: Giảm độ trễ truyền dữ liệu từ 5-15 ms xuống < 0.2 ms.", size=7.8, fill="#166534")
    f.text(x2 + 22, 388, "+ Ràng buộc: Chỉ gọi được từ C/C++ API (Python wheel không hỗ trợ).", size=7.8, fill="#64748B")

    # ==========================================================================
    # KHỐI KẾT LUẬN DƯỚI CÙNG
    # ==========================================================================
    rect(f, 20, 412, 840, 48, fill="#F8FAFC", stroke="#64748B", sw=1.1, rx=4)
    f.text(32, 424, "Bản chất tối ưu hóa Zero-Copy trên Rockchip RK3588:", size=9.5, weight=700, fill="#0F172A")
    f.text(32, 439, "• General API tốn 2 lần CPU memcpy và chuyển đổi kiểu ở mỗi khung hình, làm nghẽn băng thông DDR và CPU.", size=8.5, fill="#334155")
    f.text(32, 452, "• Zero-Copy dùng chung DMA-BUF/DRM giữa Camera/ISP và NPU, NPU tự tiền xử lý INT8, đưa độ trễ I/O về < 0.2 ms [T1 UG232 tr.64, OPL tr.335].", size=8.5, fill="#334155")

    source(f, H - 10, "[T1 UG232 tr.64-68, Fig. 5-5, 5-6] [T1 OPL tr.335-339] [T1 rknn_api.h]")
    return f


# ==============================================================================
# HÀM RUN
# ==============================================================================
if __name__ == "__main__":
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("rknn-02-zero-copy-vs-general-api", fig_zero_copy_vs_general),
    ]
    run(figures, DEFAULT_OUTDIR)
