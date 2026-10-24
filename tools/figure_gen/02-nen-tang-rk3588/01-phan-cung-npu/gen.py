#!/usr/bin/env python3
"""Chuyên đề: Phần cứng NPU RK3588 (01-phan-cung-npu).

Sinh hình vector SVG minh họa:
  1. npu-01-triple-core-architecture:
     Kiến trúc 3 lõi RKNPU (6 TOPS), bộ đệm nội tại, System SRAM và đường bus DDR.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "02-nen-tang-rk3588", "01-phan-cung-npu"
    )
)

W = 880
BOX_STROKE = "#334155"
ORANGE = "#D97706"


def tier(f, label="T1 RK3588", x=W - 130, y=14):
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
# 1. HÌNH KIẾN TRÚC 3 LÕI NPU RK3588 (npu-01-triple-core-architecture)
# ==============================================================================
def fig_triple_core_arch():
    H = 412
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(14, 22, "Kiến trúc 3 lõi NPU RK3588 (6 TOPS), Bộ nhớ đệm SRAM và Bus kết nối DDR",
           size=14, weight=700, fill=DARK)

    # Khung toàn bộ hệ NPU Subsystem
    y_top = 44
    card_w = 852
    rect(f, 14, y_top, card_w, 204, fill="#F8FAFC", stroke="#1E40AF", sw=1.4, rx=6)
    rect(f, 14, y_top, card_w, 26, fill="#EFF6FF", stroke="#1E40AF", sw=1.0, rx=6)
    rect(f, 22, y_top + 4, 6, 18, fill=BLUE, stroke=BLUE, sw=1, rx=2)
    f.text(36, y_top + 14, "Phân vùng NPU Subsystem (Điện áp độc lập VD_NPU: 0.675V - 0.95V, Xung nhịp max 1.0 GHz)",
           size=10.5, weight=700, fill="#1E40AF")

    # 3 Khối Core NPU
    core_w = 266
    core_h = 162
    core_y = y_top + 34
    gap = 14
    cx0 = 24

    core_names = ["NPU Core 0", "NPU Core 1", "NPU Core 2"]
    masks = ["core_mask = 0b001", "core_mask = 0b010", "core_mask = 0b100"]

    for i in range(3):
        cx = cx0 + i * (core_w + gap)
        rect(f, cx, core_y, core_w, core_h, fill="white", stroke="#3B82F6", sw=1.2, rx=4)
        rect(f, cx, core_y, core_w, 24, fill="#DBEAFE", stroke="#3B82F6", sw=1.0, rx=4)
        f.text(cx + core_w / 2, core_y + 11, f"{core_names[i]} (2.0 TOPS INT8)", size=9, weight=700, fill="#1E3A8A", anchor="middle")

        # Khối CNA (Convolution Neural Accelerator)
        rect(f, cx + 8, core_y + 30, core_w - 16, 38, fill="#F0FDF4", stroke="#16A34A", rx=2)
        f.text(cx + core_w / 2, core_y + 42, "CNA: 1024 MACs INT8 (1 GHz)", size=8.2, weight=700, fill="#15803D", anchor="middle")
        f.text(cx + core_w / 2, core_y + 55, "Hỗ trợ INT4/INT8/INT16/FP16/BF16", size=7.2, fill="#64748B", anchor="middle")

        # Khối BNA (Batch Normalization & Activation)
        rect(f, cx + 8, core_y + 72, core_w - 16, 26, fill="#FFFBEB", stroke=ORANGE, rx=2)
        f.text(cx + core_w / 2, core_y + 85, "BNA: Activation (SiLU, ReLU) & Elementwise", size=7.5, weight=700, fill="#B45309", anchor="middle")

        # Internal Buffer riêng của từng core
        rect(f, cx + 8, core_y + 102, core_w - 16, 30, fill="#EFF6FF", stroke=BLUE, rx=2)
        f.text(cx + core_w / 2, core_y + 113, "Internal Buffer riêng: 384 KB SRAM", size=8, weight=700, fill="#1D4ED8", anchor="middle")
        f.text(cx + core_w / 2, core_y + 124, "Lưu trữ trọng số cục bộ & activation tile", size=7.0, fill="#64748B", anchor="middle")

        # Nhãn Core Mask
        rect(f, cx + 8, core_y + 136, core_w - 16, 18, fill="#F8FAFC", stroke="#94A3B8", rx=2)
        f.text(cx + core_w / 2, core_y + 145, masks[i], size=7.2, weight=700, fill="#475569", anchor="middle")

    # --------------------------------------------------------------------------
    # KHỐI SYSTEM SRAM VÀ AXI INTERCONNECT
    # --------------------------------------------------------------------------
    y_bus = y_top + 212
    # 3 mũi tên bus 2 chiều từ 3 Core xuống AXI Bus
    for i in range(3):
        bx = cx0 + i * (core_w + gap) + core_w / 2
        arrow(f, bx, core_y + core_h, bx, y_bus, color=BLUE, sw=THIN)

    # Bus AXI Interconnect chung
    rect(f, 14, y_bus, card_w, 24, fill="#1E293B", stroke="#0F172A", rx=3)
    f.text(14 + card_w / 2, y_bus + 12, "Bus mạng nội bộ: AXI Interconnect 128-bit (Băng thông liên kết nội khối cực cao)",
           size=8.5, weight=700, fill="white", anchor="middle")

    # Mũi tên từ Bus xuống System SRAM & IOMMU
    y_mid = y_bus + 38
    arrow(f, 220, y_bus + 24, 220, y_mid, color=INK, sw=THIN)
    arrow(f, 660, y_bus + 24, 660, y_mid, color=INK, sw=THIN)

    # System SRAM 4MB
    rect(f, 24, y_mid, 395, 46, fill="#ECFDF5", stroke="#059669", sw=1.3, rx=4)
    rect(f, 32, y_mid + 5, 379, 18, fill="#FFFFFF", stroke="#059669", rx=2)
    f.text(221, y_mid + 14, "Shared System SRAM: 4.0 MB (TRM Part 1 Ch. 34)", size=8.5, weight=700, fill="#047857", anchor="middle")
    f.text(221, y_mid + 34, "Chia sẻ cho cả 3 core NPU, GPU và CPU | Giảm truy xuất DDR ngoài", size=7.5, fill="#065F46", anchor="middle")

    # NPU IOMMU (2 khối IOMMU cho 3 core)
    rect(f, 447, y_mid, 419, 46, fill="#FFF7ED", stroke="#EA580C", sw=1.3, rx=4)
    rect(f, 455, y_mid + 5, 403, 18, fill="#FFFFFF", stroke="#EA580C", rx=2)
    f.text(656, y_mid + 14, "NPU IOMMU (2 Bộ: IOMMU 0 cho Core 0/1, IOMMU 1 cho Core 2)", size=8.2, weight=700, fill="#C2410C", anchor="middle")
    f.text(656, y_mid + 34, "Ánh xạ địa chỉ ảo sang vật lý (Zero-Copy DMA) | Căn lề 16/64-byte", size=7.5, fill="#9A3412", anchor="middle")

    # Mũi tên từ IOMMU và SRAM xuống DDR Memory Controller
    y_ddr = y_mid + 60
    arrow(f, 440, y_mid + 46, 440, y_ddr, color=INK, sw=THIN)

    # Khối Bộ điều khiển DDR (DMC) và 4 Kênh DDR
    rect(f, 14, y_ddr, card_w, 48, fill="#F1F5F9", stroke="#475569", sw=1.3, rx=4)
    rect(f, 22, y_ddr + 6, card_w - 16, 18, fill="#FFFFFF", stroke="#475569", rx=2)
    f.text(14 + card_w / 2, y_ddr + 15, "Bộ điều khiển bộ nhớ DMC: 4 Kênh DDR độc lập (Ch0, Ch1, Ch2, Ch3 - 64-bit LPDDR4x/LPDDR5)",
           size=8.5, weight=700, fill=DARK, anchor="middle")
    f.text(14 + card_w / 2, y_ddr + 36, "Băng thông cực đại đạt 68.2 GB/s | Độ trễ burst bus thấp nhất khi nạp định dạng NC1HWC2",
           size=7.8, fill="#334155", anchor="middle")

    source(f, H - 12, "[T1 TRM1 tr.1984-1995, Ch.36] [T1 TRM1 Ch.34 System SRAM] [T1 TRM2 Ch.1-2 Interconnect & DMC]")
    return f


FIGURES = [
    ("npu-01-triple-core-architecture", fig_triple_core_arch),
]

if __name__ == "__main__":
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    run(FIGURES, DEFAULT_OUTDIR)
