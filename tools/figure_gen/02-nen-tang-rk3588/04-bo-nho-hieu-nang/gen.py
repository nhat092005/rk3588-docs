#!/usr/bin/env python3
"""Chuyên đề: Bộ nhớ và Hiệu năng NPU RK3588 (04-bo-nho-hieu-nang).

Sinh hình vector SVG minh họa:
  1. rknn-02-zero-copy-vs-general-api:
     Trực quan hóa kiến trúc luân chuyển bộ nhớ:
     - General API: Phân mảnh địa chỉ ảo/vật lý, 2 lần CPU memcpy, tiêu tốn băng thông bus DDR.
     - Zero-Copy API: Cơ chế chia sẻ vùng nhớ dma-buf/DRM GEM, 0 lần memcpy, RKNPU IOMMU DMA trực tiếp.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

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
# 1. HÌNH ZERO-COPY VS GENERAL API (rknn-02-zero-copy-vs-general-api) - VISUAL-FIRST
# ==============================================================================
def fig_zero_copy_vs_general():
    H = 412
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(14, 22, "Kiến trúc luân chuyển bộ nhớ: General API vs Zero-Copy API trên RK3588",
           size=14, weight=700, fill=DARK)

    card_w = 415
    card_h = 345
    x1 = 18
    x2 = 447
    y_top = 44

    # ==========================================================================
    # CỘT TRÁI: GENERAL API (2 LẦN MEMCPY TRUNG GIAN QUA CPU)
    # ==========================================================================
    rect(f, x1, y_top, card_w, card_h, fill="#FFF9F9", stroke="#DC2626", sw=1.3, rx=6)
    rect(f, x1, y_top, card_w, 26, fill="#FFFFFF", stroke="#DC2626", sw=1.0, rx=6)
    rect(f, x1 + 8, y_top + 4, 6, 18, fill=RED, stroke=RED, sw=1, rx=2)
    f.text(x1 + 22, y_top + 14, "A. General API (rknn_inputs_set / rknn_outputs_get)",
           size=10.5, weight=700, fill="#991B1B")

    bx = x1 + 16
    bw = card_w - 32
    mid_x1 = x1 + card_w // 2

    # 1. User Input Buffer
    y1 = y_top + 34
    rect(f, bx, y1, bw, 28, fill="#FFFFFF", stroke="#94A3B8", sw=1.1, rx=3)
    f.text(bx + 10, y1 + 11, "Bộ đệm ứng dụng User (cv::Mat / Virtual RAM)", size=8.5, weight=700, fill=DARK)
    f.text(bx + 10, y1 + 21, "• Dữ liệu ảnh thô (RGB FP32 hoặc UINT8)", size=7.2, fill="#64748B")
    rect(f, bx + bw - 58, y1 + 4, 52, 18, fill="#F1F5F9", stroke="#94A3B8", rx=2)
    f.text(bx + bw - 32, y1 + 13, "User Space", size=7.0, fill="#475569", anchor="middle")

    # Mũi tên sao chép lần 1 (CPU memcpy)
    arrow(f, mid_x1, y1 + 28, mid_x1, y1 + 42, color=RED, sw=THIN)

    # Thẻ tác vụ CPU lần 1
    rect(f, bx + 16, y1 + 42, bw - 32, 22, fill="#FEF2F2", stroke=RED, sw=1.0, rx=3)
    f.text(mid_x1, y1 + 53, "CPU memcpy #1 + Tiền xử lý phần mềm (Chuyển kiểu/Normalize)",
           size=7.2, weight=700, fill=RED, anchor="middle")

    # 2. Driver Input DMA Buffer
    y2 = y1 + 78
    arrow(f, mid_x1, y1 + 64, mid_x1, y2, color=RED, sw=THIN)
    rect(f, bx, y2, bw, 28, fill="#FFFFFF", stroke=RED, sw=1.1, rx=3)
    f.text(bx + 10, y2 + 11, "Đệm trung gian NPU Driver (Physical DDR do Runtime cấp)", size=8.5, weight=700, fill=RED)
    f.text(bx + 10, y2 + 21, "• Vùng nhớ DMA độc lập trong Kernel", size=7.2, fill="#64748B")
    rect(f, bx + bw - 64, y2 + 4, 58, 18, fill="#FEF2F2", stroke=RED, rx=2)
    f.text(bx + bw - 35, y2 + 13, "Kernel Space", size=7.0, fill=RED, anchor="middle")

    # Mũi tên DMA nạp NPU
    y3 = y2 + 42
    arrow(f, mid_x1, y2 + 28, mid_x1, y3, color=INK, sw=THIN)

    # 3. NPU Execution Core
    rect(f, bx, y3, bw, 30, fill="#F1F5F9", stroke=DARK, sw=1.2, rx=3)
    f.text(mid_x1, y3 + 11, "RKNPU Core (3 Nhân 6 TOPS - 1 GHz)", size=8.5, weight=700, fill=DARK, anchor="middle")
    f.text(mid_x1, y3 + 22, "Tính toán mảng MAC INT8; xuất tensor thô ra bộ đệm đích", size=7.2, fill="#475569", anchor="middle")

    # Mũi tên DMA xuất DDR
    y4 = y3 + 44
    arrow(f, mid_x1, y3 + 30, mid_x1, y4, color=INK, sw=THIN)

    # 4. Driver Output DMA Buffer
    rect(f, bx, y4, bw, 28, fill="#FFFFFF", stroke=RED, sw=1.1, rx=3)
    f.text(bx + 10, y4 + 11, "Đệm xuất NPU Driver (Physical DDR do Runtime cấp)", size=8.5, weight=700, fill=RED)
    f.text(bx + 10, y4 + 21, "• Chứa tensor đầu ra thô của NPU", size=7.2, fill="#64748B")

    # Mũi tên sao chép lần 2
    arrow(f, mid_x1, y4 + 28, mid_x1, y4 + 42, color=RED, sw=THIN)

    # Thẻ tác vụ CPU lần 2
    rect(f, bx + 16, y4 + 42, bw - 32, 22, fill="#FEF2F2", stroke=RED, sw=1.0, rx=3)
    f.text(mid_x1, y4 + 53, "CPU memcpy #2 + Hậu xử lý chuyển kiểu (INT8 → FP32)",
           size=7.2, weight=700, fill=RED, anchor="middle")

    # 5. User Output Buffer
    y5 = y4 + 78
    arrow(f, mid_x1, y4 + 64, mid_x1, y5, color=RED, sw=THIN)
    rect(f, bx, y5, bw, 28, fill="#FFFFFF", stroke="#94A3B8", sw=1.1, rx=3)
    f.text(bx + 10, y5 + 11, "Bộ đệm đích User (Ứng dụng nhận mảng kết quả)", size=8.5, weight=700, fill=DARK)
    f.text(bx + 10, y5 + 21, "• Tốn 2 lần sao chép toàn phần dữ liệu qua CPU", size=7.2, fill="#DC2626")

    # Thẻ đánh giá hiệu năng góc dưới
    rect(f, bx, y5 + 34, bw, 22, fill="#FEF2F2", stroke="#DC2626", rx=3)
    f.text(mid_x1, y5 + 45, "Tải CPU: 50% - 80% | Độ trễ I/O: 5 - 15 ms | Tốn 2x băng thông DDR",
           size=7.6, weight=700, fill="#B91C1C", anchor="middle")

    # ==========================================================================
    # CỘT PHẢI: ZERO-COPY API (CHIA SẺ VÙNG NHỚ VẬT LÝ DMA-BUF)
    # ==========================================================================
    rect(f, x2, y_top, card_w, card_h, fill="#F0FDF4", stroke="#16A34A", sw=1.3, rx=6)
    rect(f, x2, y_top, card_w, 26, fill="#FFFFFF", stroke="#16A34A", sw=1.0, rx=6)
    rect(f, x2 + 8, y_top + 4, 6, 18, fill=GREEN, stroke=GREEN, sw=1, rx=2)
    f.text(x2 + 22, y_top + 14, "B. Zero-Copy API (rknn_create_mem / rknn_set_io_mem)",
           size=10.5, weight=700, fill="#15803D")

    bx2 = x2 + 16
    mid_x2 = x2 + card_w // 2

    # Khối nguồn phần cứng: Camera ISP / RGA
    zy1 = y_top + 34
    rect(f, bx2, zy1, bw, 28, fill="#FFFFFF", stroke="#16A34A", sw=1.1, rx=3)
    f.text(bx2 + 10, zy1 + 11, "Phần cứng đầu vào: Camera ISP / RGA 2D / Bộ giải mã VPU",
           size=8.5, weight=700, fill="#15803D")
    f.text(bx2 + 10, zy1 + 21, "• Ghi khung hình trực tiếp bằng DMA phần cứng", size=7.2, fill="#64748B")

    # Mũi tên ghi thẳng vào Shared DMA-BUF
    arrow(f, mid_x2, zy1 + 28, mid_x2, zy1 + 42, color=GREEN, sw=THIN)

    # KHỐI TRỌNG TÂM: VÙNG NHỚ VẬT LÝ CHIA SẺ SHARED INPUT DMA-BUF
    zy2 = zy1 + 42
    rect(f, bx2, zy2, bw, 66, fill="#ECFDF5", stroke="#059669", sw=1.4, rx=4)
    rect(f, bx2 + 8, zy2 + 5, bw - 16, 18, fill="#FFFFFF", stroke="#059669", rx=2)
    f.text(mid_x2, zy2 + 14, "Shared Input DMA-BUF (/dev/dma_heap hoặc DRM GEM fd)",
           size=8.5, weight=700, fill="#047857", anchor="middle")

    f.text(bx2 + 12, zy2 + 33, "• App User: Ánh xạ con trỏ qua mmap(fd) → 0 sao chép", size=7.5, fill="#334155")
    f.text(bx2 + 12, zy2 + 46, "• NPU Driver: Đăng ký fd qua rknn_set_io_mem() → 0 sao chép", size=7.5, fill="#15803D")
    f.text(bx2 + 12, zy2 + 58, "• Căn lề địa chỉ vật lý: Bội số 16 byte (stride-aligned)", size=7.2, fill="#64748B")

    # Mũi tên DMA trực tiếp vào RKNPU Core
    zy3 = zy2 + 80
    arrow(f, mid_x2, zy2 + 66, mid_x2, zy3, color=GREEN, sw=THIN)

    # NPU Core tự động tiền xử lý & tính toán
    rect(f, bx2, zy3, bw, 42, fill="#FFFFFF", stroke="#16A34A", sw=1.2, rx=3)
    f.text(mid_x2, zy3 + 11, "RKNPU Core (Tự động Tiền xử lý + Tính toán phần cứng)",
           size=8.5, weight=700, fill="#15803D", anchor="middle")
    f.text(mid_x2, zy3 + 22, "Phần cứng NPU tự trừ mean, nhân scale (Quantize) on-the-fly", size=7.5, fill="#047857", anchor="middle")
    f.text(mid_x2, zy3 + 33, "Thực thi mạng nơ-ron hoàn toàn độc lập, không tiêu tốn chu kỳ CPU", size=7.2, fill="#64748B", anchor="middle")

    # Mũi tên DMA xuất thẳng ra Shared Output DMA-BUF
    zy4 = zy3 + 56
    arrow(f, mid_x2, zy3 + 42, mid_x2, zy4, color=GREEN, sw=THIN)

    # KHỐI VÙNG NHỚ VẬT LÝ CHIA SẺ SHARED OUTPUT DMA-BUF
    rect(f, bx2, zy4, bw, 56, fill="#ECFDF5", stroke="#059669", sw=1.4, rx=4)
    rect(f, bx2 + 8, zy4 + 5, bw - 16, 18, fill="#FFFFFF", stroke="#059669", rx=2)
    f.text(mid_x2, zy4 + 14, "Shared Output DMA-BUF (Chia sẻ trực tiếp tới VOP / App)",
           size=8.5, weight=700, fill="#047857", anchor="middle")
    f.text(bx2 + 12, zy4 + 33, "• NPU xuất tensor trực tiếp vào buffer đích của bộ hiển thị VOP", size=7.5, fill="#334155")
    f.text(bx2 + 12, zy4 + 46, "• Nếu vùng nhớ bật cache: gọi rknn_mem_sync() để đồng bộ", size=7.2, fill="#64748B")

    # Thẻ đánh giá ưu điểm góc dưới
    rect(f, bx2, y5 + 34, bw, 22, fill="#ECFDF5", stroke="#059669", rx=3)
    f.text(mid_x2, y5 + 45, "0 lần memcpy | Tải CPU: ~0% | Độ trễ I/O: < 0.2 ms | Băng thông tối ưu",
           size=7.6, weight=700, fill="#047857", anchor="middle")

    source(f, H - 12, "[T1 UG232 tr.64-68, Fig. 5-5, 5-6] [T1 OPL tr.335-339] [T1 rknn_api.h]")
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
