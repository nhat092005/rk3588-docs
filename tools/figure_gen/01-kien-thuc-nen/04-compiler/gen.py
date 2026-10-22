#!/usr/bin/env python3
"""Chuyên đề: Trình biên dịch AI (04-compiler).

Sinh các hình vector SVG minh họa:
  1. ir-01-three-tier-lowering:
     Pipeline hạ bậc 3 tầng IR (Graph IR -> Loop IR -> Hardware ISA) với các đối tượng thao tác và kỹ thuật tối ưu.
  2. fus-01-unfused-vs-fused:
     So sánh luồng thực thi Unfused (3 lần đọc/ghi DRAM) vs Fused (1 lần DRAM, xử lý trong SRAM/PE Accumulator).
  3. cmp-01-tiling-spatial-halo:
     Phân khối không gian (Spatial Tiling) và vùng biên đè chồng Halo trong tích chập 3x3.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# docs/tools/figure_gen/01-kien-thuc-nen/04-compiler -> ../.. = docs/tools/figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "04-compiler"
    )
)

W = 880
PURPLE = "#7B1FA2"
ORANGE = "#E65100"
TEAL = "#00796B"
GRID = "#E2E8F0"
BOX_STROKE = "#333333"


def tier(f, label, x=W - 130, y=14):
    f.tier(x, y, label)


def rect(f, x, y, w, h, fill="white", stroke=BOX_STROKE, sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN, dashed=False):
    if color not in (BLUE, GREEN, RED, GRAY, INK):
        color = INK
    f.line([(x1, y1), (x2, y2)], color, width=sw, dashed=dashed, head=True)


# ==============================================================================
# 1. HÌNH HẠ BẬC 3 TẦNG BIỂU DIỄN TRUNG GIAN (ir-01-three-tier-lowering)
# ==============================================================================
def fig_three_tier_lowering():
    H = 500
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Quá trình hạ bậc 3 tầng biểu diễn trung gian trong AI Compiler (TVM / eIQ Neutron)", size=13.5, weight=700, fill=DARK)

    # Khung bao 3 tầng theo chiều dọc
    tiers_data = [
        {
            "num": "TẦNG 1",
            "name": "Đồ thị tính toán mức cao (High-Level Graph IR)",
            "sub": "Đồ thị có hướng không chu trình (DAG) - Trừu tượng hóa toán tử và shape tensor toàn cục",
            "bg": "#F0F7FF",
            "border": BLUE,
            "y": 42,
            "h": 120,
            "inputs": ["Mô hình đầu vào: ONNX / PyTorch / TensorFlow", "Toán tử trừu tượng: Conv2D, Add, ReLU, Concat", "Tensor đa chiều với shape tĩnh (N, C, H, W)"],
            "opts": ["Gộp toán tử (Operator Fusion): Injective + Complex-out", "Gấp hằng số (Constant Folding): Gộp BN vào Conv", "Lập kế hoạch bộ nhớ tĩnh (Static Memory Planning)"],
        },
        {
            "num": "TẦNG 2",
            "name": "Biểu diễn mức vòng lặp (Loop-Level IR / AST)",
            "sub": "Vòng lặp lồng nhau (Nested Loops) - Phân tách định nghĩa thuật toán khỏi lịch trình (Schedule)",
            "bg": "#F6FBF7",
            "border": GREEN,
            "y": 198,
            "h": 120,
            "inputs": ["Vòng lặp lồng duyệt tensor: for n, c_out, h, w, c_in", "Bộ đệm tạm thời (Intermediate buffers)", "Đặc tả tính toán khai báo (Tensor Expression)"],
            "opts": ["Phân khối (Tiling): Chia nhỏ khớp dung lượng SRAM", "Đổi thứ tự vòng lặp (Loop Reordering): Tăng data reuse", "Duỗi vòng lặp (Unrolling), Compute-at, Cache Read/Write"],
        },
        {
            "num": "TẦNG 3",
            "name": "Lệnh phần cứng vi mã (Hardware Instructions / ISA)",
            "sub": "Mã máy cụ thể của phần cứng mục tiêu - Điều khiển trực tiếp PE Array, SRAM và kênh DMA",
            "bg": "#FFF8F2",
            "border": ORANGE,
            "y": 354,
            "h": 120,
            "inputs": ["Thanh ghi tích lũy (PE Accumulators), thanh ghi cấu hình", "Địa chỉ vật lý SRAM on-chip và DDR off-chip", "Kênh DMA, bộ đếm xung nhịp, cờ ngắt phần cứng"],
            "opts": ["Tensorization: Khớp khối vòng lặp vào lệnh nhân ma trận NPU", "Lập lịch DMA: Nạp trước double-buffering ẩn độ trễ DRAM", "Phát sinh vi mã (Microcode / Descriptor) nạp lệnh thực thi"],
        },
    ]

    for t in tiers_data:
        y = t["y"]
        h = t["h"]
        # Khung tầng
        rect(f, 14, y, W - 28, h, fill=t["bg"], stroke=t["border"], sw=1.3, rx=5)

        # Header tầng
        rect(f, 24, y + 10, 68, 20, fill=t["border"], stroke=t["border"], sw=1, rx=3)
        f.text(58, y + 20, t["num"], size=10, weight=700, fill="white", anchor="middle")

        f.text(102, y + 20, t["name"], size=12, weight=700, fill=DARK)
        f.text(102, y + 36, t["sub"], size=9.5, fill=GRAY)

        # Cột trái: Đối tượng thao tác (x=24, w=400, h=64)
        rect(f, 24, y + 48, 400, 64, fill="white", stroke=GRID, sw=1, rx=3)
        f.text(32, y + 59, "Đối tượng và dữ liệu thao tác:", size=9.5, weight=700, fill=DARK)
        for i, item in enumerate(t["inputs"]):
            f.text(42, y + 74 + i * 14, f"•  {item}", size=8.8, fill=INK)

        # Cột phải: Nhiệm vụ và tối ưu hóa chính (x=436, w=418, h=64)
        rect(f, 436, y + 48, 418, 64, fill="white", stroke=GRID, sw=1, rx=3)
        f.text(444, y + 59, "Tối ưu hóa và chuyển đổi then chốt:", size=9.5, weight=700, fill=DARK)
        for i, item in enumerate(t["opts"]):
            f.text(454, y + 74 + i * 14, f"•  {item}", size=8.8, fill=INK)

    # 2 mũi tên chuyển tầng (Hạ bậc / Lowering)
    arrow(f, W / 2, 162, W / 2, 196, color=BLUE, sw=THICK)
    f.text(W / 2 + 12, 179, "Hạ bậc đồ thị (Graph Lowering) & Lập lịch thuật toán", size=9, weight=700, fill=BLUE)

    arrow(f, W / 2, 318, W / 2, 352, color=GREEN, sw=THICK)
    f.text(W / 2 + 12, 335, "Hạ bậc mã máy (Codegen / Tensorization) & Ánh xạ NPU", size=9, weight=700, fill=GREEN)

    source(f, H - 24, "Nguồn: Chen et al. (TVM, OSDI 2018 tr.3-4), Bamborini et al. (eIQ Neutron 2023 tr.4)")
    return f


# ==============================================================================
# 2. HÌNH ĐỐI CHIẾU UNFUSED VS FUSED DRAM ACCESS (fus-01-unfused-vs-fused)
# ==============================================================================
def fig_unfused_vs_fused():
    H = 505
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "So sánh luồng thực thi Unfused vs Fused: Giảm 66.7% lưu lượng trung chuyển DRAM", size=13.5, weight=700, fill=DARK)

    col_w = 412
    x1 = 18
    x2 = 450

    # ---------------------------------------------------------
    # Panel 1: Unfused (Trái) - Luồng tuần tự qua DRAM từng bước
    # ---------------------------------------------------------
    rect(f, x1, 40, col_w, 436, fill="#FFF9F9", stroke=RED, sw=1.3, rx=5)
    rect(f, x1 + 10, 50, 145, 22, fill=RED, stroke=RED, sw=1, rx=3)
    f.text(x1 + 82, 61, "UNFUSED (Không gộp)", size=10, weight=700, fill="white", anchor="middle")
    f.text(x1 + 165, 61, "3 Kernel độc lập - 6 lần truy cập DRAM", size=9.8, weight=700, fill=RED)

    # 1. Đọc Input từ DRAM
    rect(f, x1 + 25, 80, col_w - 50, 26, fill="#FEE2E2", stroke=RED, sw=1, rx=3)
    f.text(x1 + col_w / 2, 93, "DRAM: Tensor đầu vào (200 KB)", size=9.5, weight=700, fill=RED, anchor="middle")

    arrow(f, x1 + col_w / 2, 108, x1 + col_w / 2, 122, color=RED, sw=THIN)
    f.text(x1 + col_w / 2 + 8, 115, "[1] Đọc", size=8, fill=RED)

    # Kernel 1: Conv2D
    rect(f, x1 + 35, 124, col_w - 70, 36, fill="white", stroke=BOX_STROKE, sw=1.2, rx=4)
    f.text(x1 + col_w / 2, 136, "Kernel 1: Tích chập (Conv2D)", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(x1 + col_w / 2, 149, "Tính toán xong phải đẩy kết quả ra DRAM", size=8.5, fill=GRAY, anchor="middle")

    arrow(f, x1 + col_w / 2, 162, x1 + col_w / 2, 176, color=RED, sw=THIN)
    f.text(x1 + col_w / 2 + 8, 169, "[2] Ghi", size=8, fill=RED)

    # 2. Đệm DRAM Tensor trung gian 1
    rect(f, x1 + 25, 178, col_w - 50, 26, fill="#FEE2E2", stroke=RED, sw=1, rx=3)
    f.text(x1 + col_w / 2, 191, "DRAM: Tensor trung gian 1 (200 KB)", size=9.5, weight=700, fill=RED, anchor="middle")

    arrow(f, x1 + col_w / 2, 206, x1 + col_w / 2, 220, color=RED, sw=THIN)
    f.text(x1 + col_w / 2 + 8, 213, "[3] Đọc", size=8, fill=RED)

    # Kernel 2: BatchNorm
    rect(f, x1 + 35, 222, col_w - 70, 36, fill="white", stroke=BOX_STROKE, sw=1.2, rx=4)
    f.text(x1 + col_w / 2, 234, "Kernel 2: Chuẩn hóa BatchNorm / Scale", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(x1 + col_w / 2, 247, "Đọc lại từ DRAM, tính affine rồi lại ghi tiếp", size=8.5, fill=GRAY, anchor="middle")

    arrow(f, x1 + col_w / 2, 260, x1 + col_w / 2, 274, color=RED, sw=THIN)
    f.text(x1 + col_w / 2 + 8, 267, "[4] Ghi", size=8, fill=RED)

    # 3. Đệm DRAM Tensor trung gian 2
    rect(f, x1 + 25, 276, col_w - 50, 26, fill="#FEE2E2", stroke=RED, sw=1, rx=3)
    f.text(x1 + col_w / 2, 289, "DRAM: Tensor trung gian 2 (200 KB)", size=9.5, weight=700, fill=RED, anchor="middle")

    arrow(f, x1 + col_w / 2, 304, x1 + col_w / 2, 318, color=RED, sw=THIN)
    f.text(x1 + col_w / 2 + 8, 311, "[5] Đọc", size=8, fill=RED)

    # Kernel 3: ReLU
    rect(f, x1 + 35, 320, col_w - 70, 36, fill="white", stroke=BOX_STROKE, sw=1.2, rx=4)
    f.text(x1 + col_w / 2, 332, "Kernel 3: Hàm kích hoạt (ReLU)", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(x1 + col_w / 2, 345, "Cắt ngưỡng max(0, x) rồi ghi kết quả cuối", size=8.5, fill=GRAY, anchor="middle")

    arrow(f, x1 + col_w / 2, 358, x1 + col_w / 2, 372, color=RED, sw=THIN)
    f.text(x1 + col_w / 2 + 8, 365, "[6] Ghi", size=8, fill=RED)

    # 4. Ghi Output vào DRAM
    rect(f, x1 + 25, 374, col_w - 50, 26, fill="#FEE2E2", stroke=RED, sw=1, rx=3)
    f.text(x1 + col_w / 2, 387, "DRAM: Tensor đầu ra cuối (200 KB)", size=9.5, weight=700, fill=RED, anchor="middle")

    # Tổng kết Unfused
    rect(f, x1 + 15, 414, col_w - 30, 50, fill="white", stroke=RED, sw=1.2, rx=4)
    f.text(x1 + col_w / 2, 429, "Tổng cộng: 3 lần Đọc + 3 lần Ghi = 1,204 KB DRAM", size=9.5, weight=700, fill=RED, anchor="middle")
    f.text(x1 + col_w / 2, 447, "Trung chuyển lãng phí: 802,816 bytes (DRAM stall cao)", size=8.5, fill=DARK, anchor="middle")

    # ---------------------------------------------------------
    # Panel 2: Fused (Phải) - 1 Kernel duy nhất trên On-chip SRAM
    # ---------------------------------------------------------
    rect(f, x2, 40, col_w, 436, fill="#F6FBF7", stroke=GREEN, sw=1.3, rx=5)
    rect(f, x2 + 10, 50, 130, 22, fill=GREEN, stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 75, 61, "FUSED (Đã gộp)", size=10, weight=700, fill="white", anchor="middle")
    f.text(x2 + 150, 61, "1 Kernel duy nhất - 2 lần truy cập DRAM", size=9.8, weight=700, fill=GREEN)

    # 1. Đọc Input từ DRAM
    rect(f, x2 + 25, 80, col_w - 50, 24, fill="#DCFCE7", stroke=GREEN, sw=1, rx=3)
    f.text(x2 + col_w / 2, 92, "DRAM: Tensor đầu vào (200 KB)", size=9.5, weight=700, fill=GREEN, anchor="middle")

    arrow(f, x2 + col_w / 2, 104, x2 + col_w / 2, 126, color=GREEN, sw=THICK)
    f.text(x2 + col_w / 2 + 10, 116, "[1] Đọc duy nhất", size=8.5, weight=700, fill=GREEN)

    # Khung On-Chip Fused Kernel (h=218, ends at 346)
    rect(f, x2 + 20, 128, col_w - 40, 218, fill="white", stroke=GREEN, sw=1.3, rx=4)
    rect(f, x2 + 28, 136, col_w - 56, 20, fill="#F0FDF4", stroke=GREEN, sw=1, rx=3)
    f.text(x2 + col_w / 2, 146, "NPU ON-CHIP SRAM & PE ARRAY (KERNEL GỘP)", size=9.8, weight=700, fill=GREEN, anchor="middle")

    # Bên trong Kernel: 3 bước
    # Bước 1
    rect(f, x2 + 35, 160, col_w - 70, 36, fill="#F8FAFC", stroke=BLUE, sw=1, rx=3)
    f.text(x2 + col_w / 2, 171, "Bước 1: Constant Folding (Pha Biên Dịch)", size=9.2, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + col_w / 2, 185, "Gấp trước BN vào trọng số Conv: W_fused, b_fused", size=8.2, fill=DARK, anchor="middle")

    arrow(f, x2 + col_w / 2, 198, x2 + col_w / 2, 212, color=GREEN, sw=THIN)

    # Bước 2
    rect(f, x2 + 35, 214, col_w - 70, 36, fill="#F8FAFC", stroke=DARK, sw=1, rx=3)
    f.text(x2 + col_w / 2, 225, "Bước 2: Mảng PE tính Tích chập (Conv2D)", size=9.2, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + col_w / 2, 239, "Giá trị tích lũy giữ trọn trên thanh ghi Accumulator", size=8.2, fill=GRAY, anchor="middle")

    arrow(f, x2 + col_w / 2, 252, x2 + col_w / 2, 266, color=GREEN, sw=THIN)

    # Bước 3
    rect(f, x2 + 35, 268, col_w - 70, 36, fill="#F8FAFC", stroke=DARK, sw=1, rx=3)
    f.text(x2 + col_w / 2, 279, "Bước 3: Fused ReLU tại lối ra PE", size=9.2, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + col_w / 2, 293, "Cắt max(0, x) không tốn thêm chu kỳ xung nhịp riêng", size=8.2, fill=GRAY, anchor="middle")

    # Điểm nhấn on-chip
    f.text(x2 + col_w / 2, 328, "★ Không có bất kỳ byte trung gian nào ghi ra DRAM", size=8.5, weight=700, fill=GREEN, anchor="middle")

    arrow(f, x2 + col_w / 2, 348, x2 + col_w / 2, 372, color=GREEN, sw=THICK)
    f.text(x2 + col_w / 2 + 10, 360, "[2] Ghi duy nhất", size=8.5, weight=700, fill=GREEN)

    # Ghi Output vào DRAM
    rect(f, x2 + 25, 374, col_w - 50, 26, fill="#DCFCE7", stroke=GREEN, sw=1, rx=3)
    f.text(x2 + col_w / 2, 387, "DRAM: Tensor đầu ra cuối (200 KB)", size=9.5, weight=700, fill=GREEN, anchor="middle")

    # Tổng kết Fused
    rect(f, x2 + 15, 414, col_w - 30, 50, fill="white", stroke=GREEN, sw=1.2, rx=4)
    f.text(x2 + col_w / 2, 429, "Tổng cộng: 1 lần Đọc + 1 lần Ghi = 401 KB (-66.7%)", size=9.5, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + col_w / 2, 447, "Tiết kiệm 802,816 bytes; Tăng tốc 1.2x - 2.0x (TVM)", size=8.5, fill=DARK, anchor="middle")

    source(f, H - 24, "Nguồn: Chen et al. (TVM, OSDI 2018 tr.3-4), Lee et al. (IEEE TVLSI 2024 tr.1)")
    return f


# ==============================================================================
# 3. HÌNH PHÂN KHỐI TILING VÀ CHI PHÍ BIÊN HALO (cmp-01-tiling-spatial-halo)
# ==============================================================================
def fig_tiling_spatial_halo():
    H = 475
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Phân khối không gian (Spatial Tiling) và vùng biên đè chồng (Halo Region) trong Conv 3x3", size=13.5, weight=700, fill=DARK)

    col_w = 412
    x1 = 18
    x2 = 450

    # Panel 1: Cấu trúc 1 Tile và Vùng Halo
    rect(f, x1, 40, col_w, 402, fill="#F8FAFC", stroke=BLUE, sw=1.3, rx=5)
    rect(f, x1 + 10, 50, 145, 22, fill=BLUE, stroke=BLUE, sw=1, rx=3)
    f.text(x1 + 82, 61, "CẤU TRÚC MỘT TILE", size=10, weight=700, fill="white", anchor="middle")
    f.text(x1 + 165, 61, "Mở rộng 1 px mỗi phía cho Kernel 3x3", size=9.5, weight=700, fill=BLUE)

    # Lưới hình học biểu diễn Tile đầu vào 10x10 và Lõi đầu ra 8x8
    gx = x1 + 116
    gy = 96
    gw = 180
    gh = 180

    # Vùng Halo ngoài (10x10)
    rect(f, gx, gy, gw, gh, fill="#FEF3C7", stroke=ORANGE, sw=1.5, rx=3)
    f.text(x1 + col_w / 2, gy - 10, "Tile đầu vào: 10 × 10 = 100 điểm ảnh (Gồm Halo vàng)", size=9.5, weight=700, fill=ORANGE, anchor="middle")

    # Vùng lõi đầu ra (8x8)
    cx = gx + 22
    cy = gy + 22
    cw = gw - 44
    ch = gh - 44
    rect(f, cx, cy, cw, ch, fill="#EFF6FF", stroke=BLUE, sw=1.8, rx=2)
    f.text(cx + cw / 2, cy + ch / 2 - 10, "VÙNG LÕI HỮU ÍCH", size=10.5, weight=700, fill=BLUE, anchor="middle")
    f.text(cx + cw / 2, cy + ch / 2 + 8, "Tile đầu ra: 8 × 8 = 64 điểm ảnh", size=9, fill=DARK, anchor="middle")
    f.text(cx + cw / 2, cy + ch / 2 + 24, "(Dữ liệu sinh ra feature map mới)", size=7.8, fill=GRAY, anchor="middle")

    # Nhãn chỉ báo vùng Halo
    f.text(gx + gw / 2, gy + 11, "Vùng đệm Halo (padding = 1 pixel mỗi phía)", size=8.2, fill=ORANGE, anchor="middle")
    f.text(gx + gw / 2, gy + gh - 11, "36 điểm ảnh phụ trợ nạp từ DRAM cho Conv 3×3", size=8.2, fill=ORANGE, anchor="middle")

    # Phân tích chi phí Panel 1
    rect(f, x1 + 15, 304, col_w - 30, 126, fill="white", stroke=GRID, sw=1, rx=4)
    f.text(x1 + 25, 320, "Phân tích chi phí biên (Overhead) trên Tile 8×8:", size=9.5, weight=700, fill=DARK)
    f.text(x1 + 35, 340, "• Dữ liệu hữu ích tính toán đầu ra: 64 phần tử (64.0%)", size=8.8, fill=INK)
    f.text(x1 + 35, 360, "• Dữ liệu Halo phụ trợ trường tiếp nhận: 36 phần tử (36.0%)", size=8.8, fill=ORANGE)
    f.text(x1 + 35, 380, "• Tỷ lệ chi phí biên lãng phí: 36 / 64 = 56.25% dung lượng nạp", size=8.8, weight=700, fill=RED)
    f.text(x1 + 35, 400, "• Kernel càng lớn (5×5, 7×7), vùng Halo càng phình to", size=8.5, fill=GRAY)
    f.text(x1 + 35, 418, "• Nếu không có Halo, các điểm biên tile đầu ra sẽ bị tính sai", size=8.2, italic=True, fill=GRAY)

    # Panel 2: Chồng lấn giữa hai Tile kề cận
    rect(f, x2, 40, col_w, 402, fill="#F8FAFC", stroke=GREEN, sw=1.3, rx=5)
    rect(f, x2 + 10, 50, 185, 22, fill=GREEN, stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 102, 61, "CHỒNG LẤN HAI TILE KỀ NHAU", size=10, weight=700, fill="white", anchor="middle")
    f.text(x2 + 205, 61, "Đọc lặp dữ liệu biên từ DRAM", size=9.5, weight=700, fill=GREEN)

    # Sơ đồ hai tile kề cận ghép nhau
    t2_y = 96
    rect(f, x2 + 25, t2_y, 165, 110, fill="#EFF6FF", stroke=BLUE, sw=1.5, rx=3)
    f.text(x2 + 85, t2_y + 35, "Tile A (NPU Core 0)", size=9.5, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + 85, t2_y + 55, "Tính outH 0..7", size=8.5, fill=DARK, anchor="middle")

    rect(f, x2 + 155, t2_y, 165, 110, fill="#F0FDF4", stroke=GREEN, sw=1.5, rx=3)
    f.text(x2 + 255, t2_y + 35, "Tile B (NPU Core 1)", size=9.5, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 255, t2_y + 55, "Tính outH 8..15", size=8.5, fill=DARK, anchor="middle")

    # Vùng chồng lấn Halo giữa A và B (Chính xác từ x2+155 đến x2+190, rộng 35px)
    rect(f, x2 + 155, t2_y, 35, 110, fill="#FEF3C7", stroke=RED, sw=1.5, dashed=True, rx=2)
    f.text(x2 + 172, t2_y + 45, "HALO", size=7.8, weight=700, fill=RED, anchor="middle")
    f.text(x2 + 172, t2_y + 58, "CHUNG", size=7.2, weight=700, fill=RED, anchor="middle")

    f.text(x2 + col_w / 2, t2_y + 124, "Dải Halo biên chung bị DMA nạp 2 lần từ DRAM", size=8.8, weight=700, fill=RED, anchor="middle")

    # Bảng đánh đổi kích thước Tile (Trade-off table)
    rect(f, x2 + 15, 236, col_w - 30, 194, fill="white", stroke=GRID, sw=1, rx=4)
    f.text(x2 + 25, 252, "Đánh đổi kích thước Tile (Tile Size Trade-off):", size=9.5, weight=700, fill=DARK)

    # Khung tile nhỏ 8x8
    rect(f, x2 + 25, 264, col_w - 50, 42, fill="#FFF9F9", stroke=RED, sw=1, rx=3)
    f.text(x2 + 35, 276, "Tile nhỏ (8 × 8) - Tiết kiệm dung lượng SRAM:", size=9, weight=700, fill=RED)
    f.text(x2 + 35, 292, "Halo = 36 px (Overhead 56.25%) -> DMA đọc lặp nhiều, nghẽn bus DRAM", size=8.2, fill=DARK)

    # Khung tile lớn 32x32
    rect(f, x2 + 25, 312, col_w - 50, 42, fill="#F6FBF7", stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 35, 324, "Tile lớn (32 × 32) - Tối ưu băng thông:", size=9, weight=700, fill=GREEN)
    f.text(x2 + 35, 340, "Halo = 132 px (Overhead 12.89%) -> Giảm đọc lặp nhưng đòi hỏi SRAM lớn", size=8.2, fill=DARK)

    # Ghi chú kết luận
    f.text(x2 + 25, 370, "Ràng buộc: Dung lượng Tile + Double Buffer <= Dung lượng SRAM on-chip", size=8.2, weight=700, fill=DARK)
    f.text(x2 + 25, 388, "Tiling theo dòng (line parallelism) bảo toàn burst transfers của bus DRAM", size=8.2, fill=DARK)
    f.text(x2 + 25, 406, "Compiler phải giải bài toán quy hoạch ràng buộc (Constraint Programming)", size=8.2, fill=GRAY)

    source(f, H - 24, "Nguồn: Bamberg et al. (eIQ Neutron 2023 tr.4, tr.8), Lee et al. (IEEE TVLSI 2024 tr.2)")
    return f


def main():
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("ir-01-three-tier-lowering", fig_three_tier_lowering),
        ("fus-01-unfused-vs-fused", fig_unfused_vs_fused),
        ("cmp-01-tiling-spatial-halo", fig_tiling_spatial_halo),
    ]
    run(figures, DEFAULT_OUTDIR)


if __name__ == "__main__":
    main()
