#!/usr/bin/env python3
"""Chuyên đề: Trình biên dịch AI (04-compiler).

Sinh các hình vector SVG minh họa:
  1. ir-01-three-tier-lowering:
     Pipeline hạ bậc 3 tầng IR (Graph IR -> Loop IR -> Hardware ISA) với các đối tượng thao tác và kỹ thuật tối ưu.
  2. fus-01-unfused-vs-fused:
     So sánh luồng thực thi Unfused (3 lần đọc/ghi DRAM) vs Fused (1 lần DRAM, xử lý trong SRAM/PE Accumulator).
  3. fus-02-constant-folding-and-op-fusion:
     Cơ chế Constant Folding và gộp toán tử tĩnh ở pha biên dịch (Compile-time) đối chiếu đồ thị trước vs sau tối ưu.
  4. cmp-01-tiling-spatial-halo:
     Phân khối không gian (Spatial Tiling) và vùng biên đè chồng Halo trong tích chập 3x3.
  5. tvm-01-optimization-and-autotvm:
     Kiến trúc Compiler TVM: Tối ưu hai tầng (Graph/Op IR, Operator Fusion, Compute vs Schedule) và lập lịch tự động AutoTVM bằng mô hình học máy.
  6. neu-01-hw-sw-codesign:
     Kiến trúc đồng thiết kế HW/SW trong eIQ Neutron: Compiler CP Solver điều phối NPU Subsystem đa nhân và TCM.
  7. neu-02-effective-vs-peak-tops:
     Nghịch lý TOPS danh định và Băng thông DRAM: Đối chiếu NPU 11 TOPS nghẽn bộ nhớ vs eIQ Neutron 2 TOPS có HW/SW co-design.

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
AMBER = "#D97706"
TEAL = "#00796B"
GRID = "#E2E8F0"
BOX_STROKE = "#333333"


def tier(f, label, x=W - 130, y=14):
    f.tier(x, y, label)


def rect(f, x, y, w, h, fill="white", stroke=BOX_STROKE, sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN, dashed=False):
    if color not in (BLUE, GREEN, RED, GRAY, INK, AMBER):
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
    H = 510
    f = Fig(W, H)
    tier(f, "T2 chung", x=W - 130, y=12)
    f.text(14, 20, "So sánh Luồng Thực thi Unfused vs Fused: Bản chất Vật lý và Lưu lượng DRAM", size=13.0, weight=700, fill=DARK)
    f.text(14, 34, "Đối chiếu luân chuyển Off-chip DRAM (ngoài chip) và On-chip NPU (trong chip) [Chen 2018 TVM, Lee 2024]", size=7.2, fill="#64748B")

    col_w = 414
    x1 = 18
    x2 = 448
    card_y = 46
    card_h = 436

    # KHUNG NGOÀI CÙNG
    rect(f, x1, card_y, col_w, card_h, fill="#FAFAFA", stroke=RED, sw=1.2, rx=5)
    rect(f, x2, card_y, col_w, card_h, fill="#FAFAFA", stroke=GREEN, sw=1.2, rx=5)

    # HEADER STRIP
    rect(f, x1, card_y, col_w, 30, fill="#FFFFFF", stroke=RED, sw=1.0, rx=5)
    rect(f, x1 + 8, card_y + 5, 5, 20, fill=RED, stroke=RED, sw=1, rx=2)
    f.text(x1 + 18, card_y + 11, "A. KỊCH BẢN UNFUSED (3 KERNEL RỜI RẠC)", size=9.6, weight=700, fill="#991B1B")
    f.text(x1 + 18, card_y + 22, "Bão hòa băng thông bus: 6 lượt truy cập DRAM cho 1 chuỗi tính", size=6.8, fill="#B91C1C")

    rect(f, x2, card_y, col_w, 30, fill="#FFFFFF", stroke=GREEN, sw=1.0, rx=5)
    rect(f, x2 + 8, card_y + 5, 5, 20, fill=GREEN, stroke=GREEN, sw=1, rx=2)
    f.text(x2 + 18, card_y + 11, "B. KỊCH BẢN FUSED (1 KERNEL GỘP ON-CHIP)", size=9.6, weight=700, fill="#047857")
    f.text(x2 + 18, card_y + 22, "Khép kín trên chip: Chỉ 2 lượt DRAM (1 đọc vào, 1 ghi ra)", size=6.8, fill="#047857")

    # ==============================================================================
    # TẦNG 1: OFF-CHIP DRAM (y: 80, h: 54)
    # ==============================================================================
    rect(f, x1 + 6, 80, col_w - 12, 54, fill="#FFF1F2", stroke=RED, sw=1.0, rx=3)
    f.text(x1 + 12, 89, "OFF-CHIP DRAM (Bộ nhớ ngoài chip - LPDDR4X) [~200 pJ/bit, Băng thông hạn hẹp]", size=6.8, weight=700, fill="#991B1B")

    tw = 92
    tx0 = x1 + 10
    # Tensor Input X
    rect(f, tx0 + 0 * 97, 98, tw, 30, fill="#EFF6FF", stroke=BLUE, sw=0.8, rx=2)
    f.text(tx0 + 0 * 97 + tw / 2, 107, "Tensor Input X", size=6.8, weight=700, fill=BLUE, anchor="middle")
    f.text(tx0 + 0 * 97 + tw / 2, 118, "196.0 KiB", size=6.6, fill="#1E40AF", anchor="middle")

    # Temp Y1
    rect(f, tx0 + 1 * 97, 98, tw, 30, fill="#FEE2E2", stroke=RED, sw=0.8, rx=2)
    f.text(tx0 + 1 * 97 + tw / 2, 107, "Temp Y1 (Conv)", size=6.8, weight=700, fill=RED, anchor="middle")
    f.text(tx0 + 1 * 97 + tw / 2, 118, "196.0 KiB lãng phí", size=6.6, fill="#991B1B", anchor="middle")

    # Temp Y2
    rect(f, tx0 + 2 * 97, 98, tw, 30, fill="#FEE2E2", stroke=RED, sw=0.8, rx=2)
    f.text(tx0 + 2 * 97 + tw / 2, 107, "Temp Y2 (BN)", size=6.8, weight=700, fill=RED, anchor="middle")
    f.text(tx0 + 2 * 97 + tw / 2, 118, "196.0 KiB lãng phí", size=6.6, fill="#991B1B", anchor="middle")

    # Output Y3
    rect(f, tx0 + 3 * 97, 98, tw, 30, fill="#ECFDF5", stroke=GREEN, sw=0.8, rx=2)
    f.text(tx0 + 3 * 97 + tw / 2, 107, "Tensor Output Y3", size=6.8, weight=700, fill=GREEN, anchor="middle")
    f.text(tx0 + 3 * 97 + tw / 2, 118, "196.0 KiB", size=6.6, fill="#047857", anchor="middle")

    # DRAM bên phải (Fused)
    rect(f, x2 + 6, 80, col_w - 12, 54, fill="#F0FDF4", stroke=GREEN, sw=1.0, rx=3)
    f.text(x2 + 12, 89, "OFF-CHIP DRAM (Bộ nhớ ngoài chip) [Chỉ lưu Input và Output cuối cùng]", size=6.8, weight=700, fill="#047857")

    rect(f, x2 + 12, 98, 100, 30, fill="#EFF6FF", stroke=BLUE, sw=0.8, rx=2)
    f.text(x2 + 62, 107, "Tensor Input X", size=6.8, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + 62, 118, "196.0 KiB", size=6.6, fill="#1E40AF", anchor="middle")

    rect(f, x2 + 118, 98, 168, 30, fill="#FFFFFF", stroke="#10B981", sw=0.8, dashed=True, rx=2)
    f.text(x2 + 202, 107, "TRIỆT TIÊU TENSOR TRUNG GIAN", size=6.8, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 202, 118, "0 Byte DRAM cho Y1 và Y2 (-100%)", size=6.6, fill="#059669", anchor="middle")

    rect(f, x2 + 292, 98, 110, 30, fill="#ECFDF5", stroke=GREEN, sw=0.8, rx=2)
    f.text(x2 + 347, 107, "Tensor Output Y3", size=6.8, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 347, 118, "196.0 KiB", size=6.6, fill="#047857", anchor="middle")

    # ==============================================================================
    # TẦNG 2: GIAO TIẾP BUS DRAM / KÊNH NoC (y: 134 đến 224, h = 90)
    # ==============================================================================
    f.line([(x1 + 6, 134), (x1 + col_w - 6, 134)], "#CBD5E1", width=0.8, dashed=True, head=False)
    f.line([(x1 + 6, 224), (x1 + col_w - 6, 224)], "#CBD5E1", width=0.8, dashed=True, head=False)

    # Huy hiệu phân loại kênh bên trái
    rect(f, x1 + 8, 142, 40, 72, fill="#F8FAFC", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x1 + 28, 153, "KÊNH", size=6.6, weight=700, fill="#64748B", anchor="middle")
    f.text(x1 + 28, 164, "BUS", size=6.6, weight=700, fill="#64748B", anchor="middle")
    f.text(x1 + 28, 175, "DRAM", size=6.6, weight=700, fill="#64748B", anchor="middle")
    f.text(x1 + 28, 186, "NoC", size=6.6, weight=700, fill="#64748B", anchor="middle")
    f.text(x1 + 28, 202, "6 lượt", size=6.6, weight=700, fill=RED, anchor="middle")

    # 6 Mũi tên khứ hồi bên trái (từ 134 đến 224)
    # 1. Đọc X: DRAM -> NPU
    arrow(f, 74, 134, 74, 224, color=RED, sw=1.5)
    f.text(78, 178, "[1] Đọc X", size=6.6, weight=700, fill=RED)

    # 2. Ghi Y1: NPU -> DRAM
    arrow(f, 150, 224, 150, 134, color=RED, sw=1.5)
    f.text(154, 178, "[2] Ghi Y1", size=6.6, weight=700, fill=RED)

    # 3. Đọc Y1: DRAM -> NPU
    arrow(f, 192, 134, 192, 224, color=RED, sw=1.5)
    f.text(196, 178, "[3] Đọc Y1", size=6.6, weight=700, fill=RED)

    # 4. Ghi Y2: NPU -> DRAM
    arrow(f, 250, 224, 250, 134, color=RED, sw=1.5)
    f.text(254, 178, "[4] Ghi Y2", size=6.6, weight=700, fill=RED)

    # 5. Đọc Y2: DRAM -> NPU
    arrow(f, 292, 134, 292, 224, color=RED, sw=1.5)
    f.text(296, 178, "[5] Đọc Y2", size=6.6, weight=700, fill=RED)

    # 6. Ghi Y3: NPU -> DRAM
    arrow(f, 368, 224, 368, 134, color=RED, sw=1.5)
    f.text(372, 178, "[6] Ghi Y3", size=6.6, weight=700, fill=RED)

    # Bus bên phải (Fused)
    f.line([(x2 + 6, 134), (x2 + col_w - 6, 134)], "#CBD5E1", width=0.8, dashed=True, head=False)
    f.line([(x2 + 6, 224), (x2 + col_w - 6, 224)], "#CBD5E1", width=0.8, dashed=True, head=False)

    # Huy hiệu phân loại kênh bên phải
    rect(f, x2 + 8, 142, 40, 72, fill="#F0FDF4", stroke="#86EFAC", sw=0.8, rx=3)
    f.text(x2 + 28, 153, "KÊNH", size=6.6, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 28, 164, "BUS", size=6.6, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 28, 175, "DRAM", size=6.6, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 28, 186, "NoC", size=6.6, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 28, 202, "2 lượt", size=6.6, weight=700, fill=GREEN, anchor="middle")

    # Mũi tên 1: Đọc X
    arrow(f, x2 + 62, 134, x2 + 62, 224, color=GREEN, sw=2.0)
    f.text(x2 + 66, 178, "[1] Đọc X", size=6.6, weight=700, fill=GREEN)

    # Khu vực thông suốt ở giữa
    rect(f, x2 + 116, 148, 172, 60, fill="#ECFDF5", stroke=GREEN, sw=0.8, rx=4)
    f.text(x2 + 202, 161, "BUS ĐƯỢC GIẢI PHÓNG TRIỆT ĐỂ", size=7.2, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 202, 174, "• Triệt tiêu hoàn toàn 4 lượt truyền tensor trung gian", size=6.6, fill="#059669", anchor="middle")
    f.text(x2 + 202, 186, "• Giảm 66.7% áp lực kênh nhớ, NPU stall-free", size=6.6, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 202, 198, "• Dành trọn băng thông DRAM cho các tác vụ khác", size=6.6, fill="#059669", anchor="middle")

    # Mũi tên 2: Ghi Y3
    arrow(f, x2 + 347, 224, x2 + 347, 134, color=GREEN, sw=2.0)
    f.text(x2 + 341, 178, "[2] Ghi Y3", size=6.6, weight=700, fill=GREEN, anchor="end")

    # ==============================================================================
    # TẦNG 3: ON-CHIP NPU COMPUTE ENGINE (y: 224, h: 144)
    # ==============================================================================
    rect(f, x1 + 6, 224, col_w - 12, 144, fill="#FFFFFF", stroke=RED, sw=1.0, rx=3)
    rect(f, x1 + 6, 224, col_w - 12, 14, fill="#FEE2E2", stroke=RED, sw=0.7, rx=2)
    f.text(x1 + 12, 231, "NPU ON-CHIP CORE: 3 KERNEL CHẠY NGẮT QUÃNG QUA 3 LẦN LẬP LỊCH", size=6.8, weight=700, fill="#991B1B")

    kw = 125
    kx0 = x1 + 10
    # Kernel 1: Conv2D
    rect(f, kx0 + 0 * 130, 242, kw, 86, fill="#FFF9F9", stroke=DARK, sw=0.9, rx=3)
    f.text(kx0 + 0 * 130 + kw / 2, 251, "Kernel 1: Conv2D", size=7.2, weight=700, fill=DARK, anchor="middle")
    f.text(kx0 + 0 * 130 + 6, 265, "• Mảng PE nhân cộng MAC", size=6.6, fill="#475569")
    f.text(kx0 + 0 * 130 + 6, 277, "• Tính xong kết quả Y1", size=6.6, fill="#475569")
    rect(f, kx0 + 0 * 130 + 4, 291, kw - 8, 16, fill="#FEE2E2", stroke=RED, sw=0.6, rx=2)
    f.text(kx0 + 0 * 130 + kw / 2, 299, "Xả Y1 ra DRAM [2]", size=6.6, weight=700, fill=RED, anchor="middle")
    f.text(kx0 + 0 * 130 + kw / 2, 316, "(PE dừng chờ nạp)", size=6.6, fill="#991B1B", anchor="middle")

    # Kernel 2: BN / Scale
    rect(f, kx0 + 1 * 130, 242, kw, 86, fill="#FFF9F9", stroke=DARK, sw=0.9, rx=3)
    f.text(kx0 + 1 * 130 + kw / 2, 251, "Kernel 2: BatchNorm", size=7.2, weight=700, fill=DARK, anchor="middle")
    f.text(kx0 + 1 * 130 + 6, 265, "• Đọc lại Y1 từ DRAM [3]", size=6.6, fill="#475569")
    f.text(kx0 + 1 * 130 + 6, 277, "• Tính co giãn affine", size=6.6, fill="#475569")
    rect(f, kx0 + 1 * 130 + 4, 291, kw - 8, 16, fill="#FEE2E2", stroke=RED, sw=0.6, rx=2)
    f.text(kx0 + 1 * 130 + kw / 2, 299, "Xả Y2 ra DRAM [4]", size=6.6, weight=700, fill=RED, anchor="middle")
    f.text(kx0 + 1 * 130 + kw / 2, 316, "(Lại tốn chi phí gọi op)", size=6.6, fill="#991B1B", anchor="middle")

    # Kernel 3: ReLU
    rect(f, kx0 + 2 * 130, 242, kw, 86, fill="#FFF9F9", stroke=DARK, sw=0.9, rx=3)
    f.text(kx0 + 2 * 130 + kw / 2, 251, "Kernel 3: ReLU", size=7.2, weight=700, fill=DARK, anchor="middle")
    f.text(kx0 + 2 * 130 + 6, 265, "• Đọc lại Y2 từ DRAM [5]", size=6.6, fill="#475569")
    f.text(kx0 + 2 * 130 + 6, 277, "• Cắt ngưỡng max(0, x)", size=6.6, fill="#475569")
    rect(f, kx0 + 2 * 130 + 4, 291, kw - 8, 16, fill="#ECFDF5", stroke=GREEN, sw=0.6, rx=2)
    f.text(kx0 + 2 * 130 + kw / 2, 299, "Ghi Y3 ra DRAM [6]", size=6.6, weight=700, fill="#047857", anchor="middle")
    f.text(kx0 + 2 * 130 + kw / 2, 316, "(Hoàn tất chuỗi)", size=6.6, fill="#475569", anchor="middle")

    rect(f, x1 + 10, 334, col_w - 20, 26, fill="#FFF1F2", stroke=RED, sw=0.6, rx=2)
    f.text(x1 + 16, 343, "• Nghẽn bus: 6 lượt chuyển liên tục gây memory stall, PE phải dừng chờ nạp", size=6.6, weight=700, fill="#991B1B")
    f.text(x1 + 16, 353, "• Overhead: 3 lần chuyển đổi ngữ cảnh NPU (context switch); bỏ phí băng thông SRAM", size=6.6, fill="#991B1B")

    # NPU bên phải (Fused)
    rect(f, x2 + 6, 224, col_w - 12, 144, fill="#FFFFFF", stroke=GREEN, sw=1.0, rx=3)
    rect(f, x2 + 6, 224, col_w - 12, 14, fill="#DCFCE7", stroke=GREEN, sw=0.7, rx=2)
    f.text(x2 + 12, 231, "NPU ON-CHIP CORE: 1 FUSED KERNEL KHÉP KÍN TRÊN SRAM & MẢNG PE", size=6.8, weight=700, fill="#047857")

    rect(f, x2 + 10, 242, col_w - 20, 16, fill="#EFF6FF", stroke=BLUE, sw=0.8, rx=2)
    f.text(x2 + col_w / 2, 250, "Compiler (Offline Pass): BN gộp vào Conv -> W_fused = γ·W/σ, b_fused (Triệt tiêu op BN)", size=6.6, weight=700, fill="#1E40AF", anchor="middle")

    fk_w = 118
    fk_x0 = x2 + 10
    # Khối 1: Mảng PE
    rect(f, fk_x0, 264, fk_w, 64, fill="#F0FDF4", stroke=GREEN, sw=0.9, rx=3)
    f.text(fk_x0 + fk_w / 2, 273, "Mảng PE (Systolic)", size=7.2, weight=700, fill="#047857", anchor="middle")
    f.text(fk_x0 + 6, 286, "• Nạp X từ On-chip SRAM", size=6.6, fill="#475569")
    f.text(fk_x0 + 6, 298, "• Nhân tích chập W_fused", size=6.6, fill="#475569")
    f.text(fk_x0 + 6, 310, "• MAC chạy tối đa 100%", size=6.6, weight=700, fill="#047857")

    arrow(f, fk_x0 + fk_w, 296, fk_x0 + fk_w + 14, 296, color=GREEN, sw=1.5)

    # Khối 2: Accumulator RF
    rect(f, fk_x0 + fk_w + 14, 264, fk_w, 64, fill="#F0FDF4", stroke=GREEN, sw=0.9, rx=3)
    f.text(fk_x0 + fk_w + 14 + fk_w / 2, 273, "Accumulator RF", size=7.2, weight=700, fill="#047857", anchor="middle")
    f.text(fk_x0 + fk_w + 20, 286, "• Giữ nguyên giá trị Y1", size=6.6, fill="#475569")
    f.text(fk_x0 + fk_w + 20, 298, "• Cộng trực tiếp b_fused", size=6.6, fill="#475569")
    f.text(fk_x0 + fk_w + 20, 310, "• 0 Byte xả ra DRAM", size=6.6, weight=700, fill="#047857")

    arrow(f, fk_x0 + 2 * fk_w + 14, 296, fk_x0 + 2 * fk_w + 28, 296, color=GREEN, sw=1.5)

    # Khối 3: Hardware Fused ReLU
    rect(f, fk_x0 + 2 * fk_w + 28, 264, fk_w, 64, fill="#F0FDF4", stroke=GREEN, sw=0.9, rx=3)
    f.text(fk_x0 + 2 * fk_w + 28 + fk_w / 2, 273, "Hardware Fused ReLU", size=7.2, weight=700, fill="#047857", anchor="middle")
    f.text(fk_x0 + 2 * fk_w + 34, 286, "• Mạch logic max(0, x)", size=6.6, fill="#475569")
    f.text(fk_x0 + 2 * fk_w + 34, 298, "• 0 tốn chu kỳ xung nhịp", size=6.6, fill="#475569")
    f.text(fk_x0 + 2 * fk_w + 34, 310, "• Ghi thẳng ra đệm output", size=6.6, weight=700, fill="#047857")

    rect(f, x2 + 10, 334, col_w - 20, 26, fill="#ECFDF5", stroke=GREEN, sw=0.6, rx=2)
    f.text(x2 + 16, 343, "• Ưu thế: Luồng xử lý khép kín trong On-chip SRAM, PE hoạt động stall-free", size=6.6, weight=700, fill="#047857")
    f.text(x2 + 16, 353, "• Tiết kiệm năng lượng ~95% cho phần xử lý trung gian (~5 pJ vs ~200 pJ/bit)", size=6.6, fill="#047857")

    # ==============================================================================
    # TẦNG 4: ĐỊNH LƯỢNG LƯU LƯỢNG DRAM & HIỆU QUẢ TĂNG TỐC (y: 376, h: 100)
    # ==============================================================================
    rect(f, x1 + 6, 376, col_w - 12, 100, fill="#FFF9F9", stroke=RED, sw=1.0, rx=3)
    f.text(x1 + 12, 386, "Định lượng Lưu lượng DRAM (Feature Map INT8 64×56×56 = 196.0 KiB):", size=6.8, weight=700, fill=DARK)

    bar_w = col_w - 28
    rect(f, x1 + 14, 395, bar_w, 18, fill="#FEE2E2", stroke=RED, sw=0.8, rx=2)
    f.text(x1 + 14 + bar_w / 2, 404, "Tổng lưu lượng DRAM: 1,204.2 KB (100% - Bão hòa kênh nhớ)", size=6.8, weight=700, fill="#991B1B", anchor="middle")

    f.text(x1 + 14, 423, "• Tổng lượt truy cập: 3 lần Đọc (588 KiB) + 3 lần Ghi (588 KiB) = 6 lượt", size=6.6, fill=DARK)
    f.text(x1 + 14, 436, "• Lưu lượng trung gian lãng phí: 802,816 bytes (~784 KiB chiếm 66.7%)", size=6.6, weight=700, fill=RED)
    f.text(x1 + 14, 449, "• Trạng thái phần cứng: NPU bị memory bound, hiệu suất tính toán PE giảm sút", size=6.6, fill="#475569")
    f.text(x1 + 14, 462, "• Năng lượng tiêu hao: Rất cao do liên tục nạp/xả tụ điện đường truyền bus ngoài", size=6.6, fill="#475569")

    # Bên phải: Fused
    rect(f, x2 + 6, 376, col_w - 12, 100, fill="#F0FDF4", stroke=GREEN, sw=1.0, rx=3)
    f.text(x2 + 12, 386, "Định lượng Lưu lượng DRAM (Feature Map INT8 64×56×56 = 196.0 KiB):", size=6.8, weight=700, fill=DARK)

    f_used_w = bar_w * 0.333
    rect(f, x2 + 14, 395, f_used_w, 18, fill="#047857", stroke="#064E3B", sw=0.8, rx=2)
    f.text(x2 + 14 + f_used_w / 2, 404, "401.4 KB", size=6.6, weight=700, fill="white", anchor="middle")

    rect(f, x2 + 14 + f_used_w, 395, bar_w - f_used_w, 18, fill="#ECFDF5", stroke="#10B981", sw=0.8, dashed=True, rx=2)
    f.text(x2 + 14 + f_used_w + (bar_w - f_used_w) / 2, 404, "TIẾT KIỆM 66.7% LƯU LƯỢNG (-802.8 KB)", size=6.6, weight=700, fill="#047857", anchor="middle")

    f.text(x2 + 14, 423, "• Tổng lượt truy cập: 1 lần Đọc (196 KiB) + 1 lần Ghi (196 KiB) = 2 lượt (Giảm 3.0x)", size=6.6, weight=700, fill="#047857")
    f.text(x2 + 14, 436, "• Tăng tốc suy luận: Đạt 1.2x - 2.0x speedup nhờ triệt tiêu hoàn toàn memory stall [TVM]", size=6.6, weight=700, fill="#047857")
    f.text(x2 + 14, 449, "• Trạng thái phần cứng: Chuyển dịch từ Memory-bound sang Compute-bound tối ưu", size=6.6, fill="#047857")
    f.text(x2 + 14, 462, "• Tiết kiệm năng lượng: Giảm ~60% toàn hệ thống nhờ giữ dữ liệu trên SRAM nội bộ", size=6.6, fill="#475569")

    source(f, H - 18, "Nguồn: T2 Chen 2018 (TVM, OSDI tr.3-4); T2 Lee 2024 (IEEE TVLSI tr.1); T2 Bamberg 2023 (eIQ Neutron tr.3).")
    return f


# ==============================================================================
# 2B. HÌNH CONSTANT FOLDING VÀ GỘP TOÁN TỬ TĨNH (fus-02-constant-folding-and-op-fusion)
# ==============================================================================
def fig_constant_folding_and_op_fusion():
    H = 515
    f = Fig(W, H)
    tier(f, "T2 chung", x=W - 130, y=12)
    f.text(14, 20, "Cơ chế Constant Folding và Gộp Toán Tử Tĩnh ở Pha Biên Dịch (Compile-Time)", size=13.0, weight=700, fill=DARK)
    f.text(14, 34, "Phát hiện nhánh tính toán bất biến, thực thi trước (pre-compute) và tinh giản đồ thị suy luận [Chen 2018 TVM, Bamberg 2025]", size=7.2, fill="#64748B")

    col_w = 414
    x1 = 18
    x2 = 448
    card_y = 46
    card_h = 430

    # KHUNG NGOÀI CÙNG
    rect(f, x1, card_y, col_w, card_h, fill="#FAFAFA", stroke=RED, sw=1.2, rx=5)
    rect(f, x2, card_y, col_w, card_h, fill="#FAFAFA", stroke=GREEN, sw=1.2, rx=5)

    # HEADER STRIP
    rect(f, x1, card_y, col_w, 30, fill="#FFFFFF", stroke=RED, sw=1.0, rx=5)
    rect(f, x1 + 8, card_y + 5, 5, 20, fill=RED, stroke=RED, sw=1, rx=2)
    f.text(x1 + 18, card_y + 11, "A. ĐỒ THỊ GỐC TRƯỚC TỐI ƯU (CHƯA FOLDING)", size=9.6, weight=700, fill="#991B1B")
    f.text(x1 + 18, card_y + 22, "Chứa nhiều node hằng số tĩnh, biến đổi layout và nhánh dư thừa phát sinh khi train", size=6.8, fill="#B91C1C")

    rect(f, x2, card_y, col_w, 30, fill="#FFFFFF", stroke=GREEN, sw=1.0, rx=5)
    rect(f, x2 + 8, card_y + 5, 5, 20, fill=GREEN, stroke=GREEN, sw=1, rx=2)
    f.text(x2 + 18, card_y + 11, "B. ĐỒ THỊ SAU CONSTANT FOLDING (RUNTIME GRAPH)", size=9.6, weight=700, fill="#047857")
    f.text(x2 + 18, card_y + 22, "Compiler tính sẵn 1 lần lúc biên dịch (Offline), triệt tiêu hoàn toàn runtime overhead", size=6.8, fill="#047857")

    # ==============================================================================
    # KHỐI 1: GẤP BATCH NORMALIZATION VÀO CONV (BN FOLDING) (y: 82, h: 124)
    # ==============================================================================
    b1_y = 82
    b1_h = 124

    # Khung trái
    rect(f, x1 + 6, b1_y, col_w - 12, b1_h, fill="#FFF9F9", stroke="#F87171", sw=0.9, rx=4)
    f.text(x1 + 14, b1_y + 11, "1. Gấp Batch Normalization vào Conv (Trước tối ưu)", size=7.2, weight=700, fill="#991B1B")

    # Flow bên trái
    rect(f, x1 + 14, b1_y + 20, 56, 32, fill="#EFF6FF", stroke=BLUE, sw=0.8, rx=2)
    f.text(x1 + 42, b1_y + 29, "Input X", size=6.8, weight=700, fill=BLUE, anchor="middle")
    f.text(x1 + 42, b1_y + 41, "Tensor động", size=6.6, fill="#1E40AF", anchor="middle")

    arrow(f, x1 + 70, b1_y + 36, x1 + 86, b1_y + 36, color=DARK, sw=1.0)

    rect(f, x1 + 86, b1_y + 20, 86, 32, fill="#FFFFFF", stroke=DARK, sw=0.8, rx=2)
    f.text(x1 + 129, b1_y + 29, "Conv2D", size=6.8, weight=700, fill=DARK, anchor="middle")
    f.text(x1 + 129, b1_y + 41, "W tĩnh, b tĩnh", size=6.6, fill="#64748B", anchor="middle")

    arrow(f, x1 + 172, b1_y + 36, x1 + 188, b1_y + 36, color=DARK, sw=1.0)

    rect(f, x1 + 188, b1_y + 20, 64, 32, fill="#FEE2E2", stroke=RED, sw=0.8, rx=2)
    f.text(x1 + 220, b1_y + 29, "Temp Y", size=6.8, weight=700, fill=RED, anchor="middle")
    f.text(x1 + 220, b1_y + 41, "Ghi ra DRAM", size=6.6, fill="#991B1B", anchor="middle")

    arrow(f, x1 + 252, b1_y + 36, x1 + 268, b1_y + 36, color=RED, sw=1.0)

    rect(f, x1 + 268, b1_y + 20, 132, 32, fill="#FEE2E2", stroke=RED, sw=0.8, rx=2)
    f.text(x1 + 334, b1_y + 29, "BatchNorm (4 hằng số)", size=6.8, weight=700, fill=RED, anchor="middle")
    f.text(x1 + 334, b1_y + 41, "μ, σ², γ, β tĩnh", size=6.6, fill="#991B1B", anchor="middle")

    # Bảng giải thích chi tiết
    rect(f, x1 + 14, b1_y + 58, col_w - 28, 58, fill="#FFFFFF", stroke="#FECACA", sw=0.8, rx=3)
    f.text(x1 + 20, b1_y + 68, "• Lúc train: μ, σ² cập nhật liên tục qua từng batch dữ liệu.", size=6.6, fill=DARK)
    f.text(x1 + 20, b1_y + 80, "• Lúc suy luận: Toàn bộ 4 tham số BN đều cố định (không đổi theo input).", size=6.6, fill=DARK)
    f.text(x1 + 20, b1_y + 92, "• Nhược điểm chưa gộp: Tốn thêm 1 kernel, tính lặp lại phép chia affine.", size=6.6, fill="#991B1B")
    f.text(x1 + 20, b1_y + 104, "• Hậu quả: Ghi/đọc tensor tạm Y ra bộ nhớ ngoài làm trễ pipeline.", size=6.6, fill="#991B1B")

    # Khung phải: Conv đã hấp thụ BN
    rect(f, x2 + 6, b1_y, col_w - 12, b1_h, fill="#F0FDF4", stroke="#86EFAC", sw=0.9, rx=4)
    f.text(x2 + 14, b1_y + 11, "1. Conv đã Hấp thụ BatchNorm: W_fused và b_fused [T2 TVM tr.3]", size=7.2, weight=700, fill="#047857")

    rect(f, x2 + 14, b1_y + 20, 64, 32, fill="#EFF6FF", stroke=BLUE, sw=0.8, rx=2)
    f.text(x2 + 46, b1_y + 29, "Input X", size=6.8, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + 46, b1_y + 41, "DRAM/SRAM", size=6.6, fill="#1E40AF", anchor="middle")

    arrow(f, x2 + 78, b1_y + 36, x2 + 96, b1_y + 36, color=GREEN, sw=1.2)

    rect(f, x2 + 96, b1_y + 20, 196, 32, fill="#ECFDF5", stroke=GREEN, sw=1.0, rx=2)
    f.text(x2 + 194, b1_y + 29, "Conv2D (W_fused, b_fused)", size=6.8, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 194, b1_y + 41, "Node BatchNorm biến mất 100%!", size=6.6, weight=700, fill="#059669", anchor="middle")

    arrow(f, x2 + 292, b1_y + 36, x2 + 310, b1_y + 36, color=GREEN, sw=1.2)

    rect(f, x2 + 310, b1_y + 20, 90, 32, fill="#ECFDF5", stroke=GREEN, sw=0.8, rx=2)
    f.text(x2 + 355, b1_y + 29, "Output Z", size=6.8, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 355, b1_y + 41, "Đặc trưng mới", size=6.6, fill="#059669", anchor="middle")

    rect(f, x2 + 14, b1_y + 58, col_w - 28, 58, fill="#FFFFFF", stroke="#86EFAC", sw=0.8, rx=3)
    f.text(x2 + 20, b1_y + 68, "• Trọng số gộp: W_fused = W · [ γ / √(σ² + ε) ]", size=6.8, weight=700, fill="#047857")
    f.text(x2 + 20, b1_y + 80, "• Bias gộp: b_fused = (b - μ) · [ γ / √(σ² + ε) ] + β", size=6.8, weight=700, fill="#047857")
    f.text(x2 + 20, b1_y + 92, "• Compiler tính trước 1 lần duy nhất trên máy phát triển (host/compile-time).", size=6.6, fill=DARK)
    f.text(x2 + 20, b1_y + 104, "• Hiệu quả: Tiết kiệm 100% thời gian chạy BN; triệt tiêu tensor tạm Y.", size=6.6, weight=700, fill="#047857")

    # ==============================================================================
    # KHỐI 2: BIẾN ĐỔI LAYOUT & HÌNH HỌC TĨNH (y: 212, h: 108)
    # ==============================================================================
    b2_y = 212
    b2_h = 108

    # Khung trái
    rect(f, x1 + 6, b2_y, col_w - 12, b2_h, fill="#FFFBEB", stroke="#FDE68A", sw=0.9, rx=4)
    f.text(x1 + 14, b2_y + 11, "2. Phép biến đổi Layout & Hình học (Trước tối ưu)", size=7.2, weight=700, fill="#92400E")

    rect(f, x1 + 14, b2_y + 20, 88, 30, fill="#FFFFFF", stroke=DARK, sw=0.8, rx=2)
    f.text(x1 + 58, b2_y + 29, "Weight W", size=6.8, weight=700, fill=DARK, anchor="middle")
    f.text(x1 + 58, b2_y + 41, "NCHW (FP32)", size=6.6, fill="#64748B", anchor="middle")

    arrow(f, x1 + 102, b2_y + 35, x1 + 120, b2_y + 35, color=DARK, sw=1.0)

    rect(f, x1 + 120, b2_y + 20, 150, 30, fill="#FFFBEB", stroke="#D97706", sw=0.8, rx=2)
    f.text(x1 + 195, b2_y + 29, "Toán tử Transpose / Reshape", size=6.8, weight=700, fill="#B45309", anchor="middle")
    f.text(x1 + 195, b2_y + 41, "Đổi layout lúc khởi động/chạy", size=6.6, fill="#92400E", anchor="middle")

    arrow(f, x1 + 270, b2_y + 35, x1 + 288, b2_y + 35, color=DARK, sw=1.0)

    rect(f, x1 + 288, b2_y + 20, 112, 30, fill="#FFFFFF", stroke=DARK, sw=0.8, rx=2)
    f.text(x1 + 344, b2_y + 29, "Layout NC1HWC2", size=6.8, weight=700, fill=DARK, anchor="middle")
    f.text(x1 + 344, b2_y + 41, "Nạp vào NPU PE", size=6.6, fill="#475569", anchor="middle")

    rect(f, x1 + 14, b2_y + 56, col_w - 28, 44, fill="#FFFFFF", stroke="#FDE68A", sw=0.8, rx=3)
    f.text(x1 + 20, b2_y + 67, "• Trọng số mô hình xuất từ PyTorch thường ở định dạng NCHW.", size=6.6, fill=DARK)
    f.text(x1 + 20, b2_y + 79, "• Nếu không folding: Runtime phải gọi kernel Transpose hoặc lệnh memcpy.", size=6.6, fill="#B45309")
    f.text(x1 + 20, b2_y + 91, "• Lãng phí: Gây trễ khởi động mô hình (load time) và cấp phát bộ nhớ thừa.", size=6.6, fill="#92400E")

    # Khung phải: Gấp layout tĩnh
    rect(f, x2 + 6, b2_y, col_w - 12, b2_h, fill="#F0FDF4", stroke="#86EFAC", sw=0.9, rx=4)
    f.text(x2 + 14, b2_y + 11, "2. Gấp Layout Tĩnh vào File Nhị Phân (Offline Packing) [T2 BAMB tr.5]", size=7.2, weight=700, fill="#047857")

    rect(f, x2 + 14, b2_y + 20, 196, 30, fill="#ECFDF5", stroke=GREEN, sw=0.8, rx=2)
    f.text(x2 + 112, b2_y + 29, "W_packed (Format NC1HWC2)", size=6.8, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 112, b2_y + 41, "Đã đóng gói sẵn trong file .rknn", size=6.6, fill="#059669", anchor="middle")

    arrow(f, x2 + 210, b2_y + 35, x2 + 240, b2_y + 35, color=GREEN, sw=1.2)
    f.text(x2 + 225, b2_y + 44, "DMA", size=6.6, weight=700, fill="#047857", anchor="middle")

    rect(f, x2 + 240, b2_y + 20, 160, 30, fill="#EFF6FF", stroke=BLUE, sw=0.8, rx=2)
    f.text(x2 + 320, b2_y + 29, "NPU SRAM / Core Buffer", size=6.8, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + 320, b2_y + 41, "PE đọc trực tiếp, 0 memcpy", size=6.6, fill="#1E40AF", anchor="middle")

    rect(f, x2 + 14, b2_y + 56, col_w - 28, 44, fill="#FFFFFF", stroke="#86EFAC", sw=0.8, rx=3)
    f.text(x2 + 20, b2_y + 67, "• Compiler thực hiện toàn bộ Transpose, Reshape, Flatten trước khi ghi file.", size=6.6, fill=DARK)
    f.text(x2 + 20, b2_y + 79, "• Định dạng bộ nhớ khớp 100% với cấu trúc phần cứng NPU (NC1HWC2).", size=6.6, fill="#047857")
    f.text(x2 + 20, b2_y + 91, "• Lợi ích: Triệt tiêu hoàn toàn toán tử Transpose; nạp tức thời qua kênh DMA.", size=6.6, weight=700, fill="#047857")

    # ==============================================================================
    # KHỐI 3: HỆ SỐ LƯỢNG TỬ VÀ DEAD CODE ELIMINATION (y: 326, h: 108)
    # ==============================================================================
    b3_y = 326
    b3_h = 108

    # Khung trái
    rect(f, x1 + 6, b3_y, col_w - 12, b3_h, fill="#F8FAFC", stroke="#CBD5E1", sw=0.9, rx=4)
    f.text(x1 + 14, b3_y + 11, "3. Tính toán Hệ số Động & Nhánh Chết (Trước tối ưu)", size=7.2, weight=700, fill=DARK)

    rect(f, x1 + 14, b3_y + 20, 186, 30, fill="#FFFFFF", stroke="#CBD5E1", sw=0.8, rx=2)
    f.text(x1 + 107, b3_y + 29, "Hệ số Float32: S_x · S_w / S_y", size=6.8, fill="#475569", anchor="middle")
    f.text(x1 + 107, b3_y + 41, "Chia số thực lặp lại mỗi frame", size=6.6, fill=RED, anchor="middle")

    rect(f, x1 + 208, b3_y + 20, 192, 30, fill="#FFF1F2", stroke="#FCA5A5", sw=0.8, rx=2)
    f.text(x1 + 304, b3_y + 29, "Nhánh chết (Dropout / Aux Head)", size=6.8, fill=RED, anchor="middle")
    f.text(x1 + 304, b3_y + 41, "Không nối ra Output dự đoán", size=6.6, fill="#991B1B", anchor="middle")

    rect(f, x1 + 14, b3_y + 56, col_w - 28, 44, fill="#FFFFFF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x1 + 20, b3_y + 67, "• Giữ phép tính Float32 đòi hỏi NPU kích hoạt ALU FP đắt đỏ hoặc nghẽn CPU.", size=6.6, fill=DARK)
    f.text(x1 + 20, b3_y + 79, "• Nhánh dead-code làm tăng kích thước model file và chiếm RAM vô ích.", size=6.6, fill="#64748B")
    f.text(x1 + 20, b3_y + 91, "• Trạng thái: Đồ thị cồng kềnh, phân mảnh tài nguyên phần cứng.", size=6.6, fill="#64748B")

    # Khung phải: Fixed-point & Pruning
    rect(f, x2 + 6, b3_y, col_w - 12, b3_h, fill="#F0FDF4", stroke="#86EFAC", sw=0.9, rx=4)
    f.text(x2 + 14, b3_y + 11, "3. Fixed-point Folding & Dead Code Elimination [T2 TVM tr.3]", size=7.2, weight=700, fill="#047857")

    rect(f, x2 + 14, b3_y + 20, 186, 30, fill="#ECFDF5", stroke=GREEN, sw=0.8, rx=2)
    f.text(x2 + 107, b3_y + 29, "Multiplier M_0 (INT32) & Shift n", size=6.8, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 107, b3_y + 41, "Tính sẵn 1 lần ở pha lượng tử hóa", size=6.6, fill="#059669", anchor="middle")

    rect(f, x2 + 208, b3_y + 20, 192, 30, fill="#FFFFFF", stroke="#10B981", sw=0.8, dashed=True, rx=2)
    f.text(x2 + 304, b3_y + 29, "Cắt tỉa 100% Nhánh Chết", size=6.8, weight=700, fill="#047857", anchor="middle")
    f.text(x2 + 304, b3_y + 41, "Triệt tiêu hoàn toàn khỏi đồ thị", size=6.6, fill="#059669", anchor="middle")

    rect(f, x2 + 14, b3_y + 56, col_w - 28, 44, fill="#FFFFFF", stroke="#86EFAC", sw=0.8, rx=3)
    f.text(x2 + 20, b3_y + 67, "• Chuyển đổi toàn bộ tỷ lệ scale thành phép nhân nguyên và dịch bit siêu tốc.", size=6.6, fill=DARK)
    f.text(x2 + 20, b3_y + 79, "• Dead code elimination thu nhỏ kích thước file nhị phân, tiết kiệm RAM runtime.", size=6.6, fill="#047857")
    f.text(x2 + 20, b3_y + 91, "• Trạng thái: Đồ thị suy luận tinh giản tối đa, chỉ tính dữ liệu động.", size=6.6, fill="#047857")

    # ==============================================================================
    # DẢI TỔNG KẾT SO SÁNH (y: 438, h: 34)
    # ==============================================================================
    rect(f, x1 + 6, 438, col_w - 12, 34, fill="#FFF1F2", stroke="#F87171", sw=0.8, rx=3)
    f.text(x1 + 14, 448, "Tổng kết Chưa Folding: Tốn nhiều kernel gọi riêng, overhead bộ nhớ lớn", size=6.8, weight=700, fill="#991B1B")
    f.text(x1 + 14, 461, "Runtime gánh chịu các phép tính hằng số lặp lại ở mọi frame ảnh suy luận.", size=6.6, fill="#B91C1C")

    rect(f, x2 + 6, 438, col_w - 12, 34, fill="#F0FDF4", stroke="#10B981", sw=0.8, rx=3)
    f.text(x2 + 14, 448, "Tổng kết Sau Folding: Đồ thị suy luận tối giản tuyệt đối, 0 overhead tĩnh", size=6.8, weight=700, fill="#047857")
    f.text(x2 + 14, 461, "Toàn bộ hằng số tính trước ở máy build; NPU tập trung 100% cho tính toán động.", size=6.6, fill="#065F46")

    # Dòng nguồn đáy trang
    source(f, 474, "Nguồn: T2 TVM tr.3 (Chen et al., OSDI 2018: Constant folding & graph simplification); T2 BAMB tr.5 (Bamberg et al., 2025: Static layout transforms & NPU weight packing).")

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


# ==============================================================================
# 4. HÌNH KIẾN TRÚC TỐI ƯU TVM & AUTOTVM (tvm-01-optimization-and-autotvm)
# ==============================================================================
def fig_tvm_optimization_and_autotvm():
    """HÌNH 4: Kiến trúc Tối ưu hai tầng và Lập lịch Tự động AutoTVM."""
    H = 510
    f = Fig(W, H)
    f.a('<defs><marker id="mD97706n" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 0.5L10 5L0 9.5z" fill="#D97706"/></marker></defs>')
    tier(f, "T2 chung", x=W - 130, y=12)
    f.text(18, 22, "Kiến trúc Compiler TVM: Tối ưu Hai Tầng và Lập lịch Tự động AutoTVM",
           size=13.0, weight=700, fill=DARK)
    f.text(18, 36, "Phân loại toán tử, Operator Fusion, phân tách Compute/Schedule và mô hình chi phí ML [Chen et al., OSDI 2018]",
           size=7.5, fill="#64748B")

    card_y = 48
    card_h = 420

    # ==========================================================================
    # CỘT TRÁI: PANEL A - HAI TẦNG TỐI ƯU (GRAPH IR & TENSOR EXPRESSION)
    # ==========================================================================
    x_a = 18
    w_a = 416
    rect(f, x_a, card_y, w_a, card_h, fill="#F8FAFC", stroke="#2563EB", sw=1.3, rx=6)
    rect(f, x_a, card_y, w_a, 32, fill="#EFF6FF", stroke="#2563EB", sw=1.0, rx=6)
    rect(f, x_a + 8, card_y + 6, 5, 20, fill=BLUE, stroke=BLUE, sw=1, rx=2)
    f.text(x_a + 18, card_y + 13, "A. Hai Tầng Tối ưu: Cấp Đồ thị & Cấp Toán tử", size=9.6, weight=700, fill="#1E40AF")
    f.text(x_a + 18, card_y + 24, "4 nhóm toán tử, Operator Fusion và phân tách Compute vs Schedule [T2 TVM tr.3-4]", size=6.8, fill="#475569")

    # A1. Graph-level Optimization & Operator Fusion
    y_a1 = 86
    h_a1 = 196
    rect(f, x_a + 6, y_a1, w_a - 12, h_a1, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_a + 6, y_a1, w_a - 12, 16, fill="#EFF6FF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_a + 12, y_a1 + 8, "1. Tối ưu Cấp Đồ thị & 4 Nhóm Toán tử (Operator Fusion)", size=7.2, weight=700, fill="#1E40AF")

    # 4 Operator Categories pills
    y_cat = y_a1 + 22
    cats = [
        ("Injective (1-1)", "ReLU, Add, BiasAdd", "#EFF6FF", "#3B82F6", "#1D4ED8", "#1E40AF"),
        ("Reduction (Gom)", "Sum, Max pooling", "#FEF3C7", "#F59E0B", "#B45309", "#92400E"),
        ("Complex-out-fusable", "Conv2D, MatMul", "#F3E8FF", "#A855F7", "#7E22CE", "#6B21A8"),
        ("Opaque (Khó gộp)", "Sort, toán tử đặc thù", "#F1F5F9", "#64748B", "#334155", "#475569"),
    ]
    w_cat = 96
    for i, (c_name, c_sub, c_bg, c_bd, c_t1, c_t2) in enumerate(cats):
        cx = x_a + 10 + i * 99
        rect(f, cx, y_cat, w_cat, 28, fill=c_bg, stroke=c_bd, sw=0.8, rx=2)
        f.text(cx + w_cat / 2, y_cat + 8, c_name, size=6.6, weight=700, fill=c_t1, anchor="middle")
        f.text(cx + w_cat / 2, y_cat + 19, c_sub, size=6.6, fill=c_t2, anchor="middle")

    # Visualizing Operator Fusion
    y_fus = y_cat + 34
    f.text(x_a + 12, y_fus + 7, "Chưa gộp (Unfused): 3 kernel riêng biệt, tensor trung gian qua DRAM:", size=6.6, fill="#475569")

    # Unfused boxes
    y_u = y_fus + 14
    rect(f, x_a + 12, y_u, 76, 20, fill="#F3E8FF", stroke="#A855F7", sw=0.9, rx=2)
    f.text(x_a + 50, y_u + 10, "Conv2D [Complex]", size=6.6, weight=700, fill="#7E22CE", anchor="middle")

    arrow(f, x_a + 88, y_u + 10, x_a + 110, y_u + 10, color=RED, sw=1.1)

    rect(f, x_a + 110, y_u, 78, 20, fill="#EFF6FF", stroke="#3B82F6", sw=0.9, rx=2)
    f.text(x_a + 149, y_u + 10, "BiasAdd [Injective]", size=6.6, fill="#1D4ED8", anchor="middle")

    arrow(f, x_a + 188, y_u + 10, x_a + 210, y_u + 10, color=RED, sw=1.1)

    rect(f, x_a + 210, y_u, 68, 20, fill="#EFF6FF", stroke="#3B82F6", sw=0.9, rx=2)
    f.text(x_a + 244, y_u + 10, "ReLU [Injective]", size=6.6, fill="#1D4ED8", anchor="middle")

    # Unfused penalty badge
    rect(f, x_a + 286, y_u, 118, 20, fill="#FEF2F2", stroke="#EF4444", sw=0.8, rx=2)
    f.text(x_a + 345, y_u + 10, "3 lần đọc/ghi DRAM nghẽn bus!", size=6.6, weight=700, fill="#B91C1C", anchor="middle")

    # Fused pipeline
    y_f = y_u + 26
    f.text(x_a + 12, y_f + 7, "Đã gộp (Fused): 1 kernel hợp nhất, dữ liệu giữ trọn trong thanh ghi/SRAM:", size=6.6, weight=700, fill="#047857")

    y_fb = y_f + 14
    rect(f, x_a + 12, y_fb, 266, 22, fill="#ECFDF5", stroke="#10B981", sw=1.2, rx=3)
    f.text(x_a + 145, y_fb + 11, "Fused Kernel: [ Conv2D + BiasAdd + ReLU ]", size=6.8, weight=700, fill="#047857", anchor="middle")

    rect(f, x_a + 286, y_fb, 118, 22, fill="#F0FDF4", stroke="#22C55E", sw=0.8, rx=2)
    f.text(x_a + 345, y_fb + 7.5, "Tăng tốc 1.2x - 2.0x", size=6.8, weight=700, fill="#15803D", anchor="middle")
    f.text(x_a + 345, y_fb + 16.5, "Triệt tiêu ghi bộ nhớ ngoài", size=6.6, fill="#166534", anchor="middle")

    # Fusion Rule Takeaway Box
    y_ftk = y_fb + 28
    rect(f, x_a + 10, y_ftk, w_a - 20, 46, fill="#EFF6FF", stroke="#3B82F6", sw=0.8, rx=3)
    f.text(x_a + 14, y_ftk + 8, "Quy tắc hợp nhất toán tử của TVM [T2 TVM tr.3]:", size=6.8, weight=700, fill="#1E40AF")
    f.text(x_a + 14, y_ftk + 20, "• Injective + Injective -> Injective mới  |  Reduction + Injective đầu vào -> Gộp", size=6.6, fill="#1E3A8A")
    f.text(x_a + 14, y_ftk + 32, "• Complex-out-fusable (Conv2D) gộp toàn bộ toán tử Injective ở ngõ ra thành 1 kernel duy nhất", size=6.6, fill="#1E3A8A")

    # A2. Operator-level Optimization: Compute vs Schedule
    y_a2 = 288
    h_a2 = 174
    rect(f, x_a + 6, y_a2, w_a - 12, h_a2, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_a + 6, y_a2, w_a - 12, 16, fill="#F0FDF4", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_a + 12, y_a2 + 8, "2. Tối ưu Cấp Toán tử: Phân tách Compute vs Schedule (Tensor Expression)", size=7.2, weight=700, fill="#047857")

    # 2 Comparison Columns
    y_cs = y_a2 + 22
    w_cs = 194

    # Compute Box
    rect(f, x_a + 10, y_cs, w_cs, 78, fill="#F8FAFC", stroke="#64748B", sw=0.9, rx=3)
    f.text(x_a + 16, y_cs + 10, "Compute: Tính CÁI GÌ (Thuật toán)", size=6.8, weight=700, fill=DARK)
    f.text(x_a + 16, y_cs + 22, "Khai báo toán học thuần túy (Bất biến):", size=6.6, fill="#475569")
    rect(f, x_a + 16, y_cs + 29, w_cs - 12, 22, fill="#FFFFFF", stroke="#CBD5E1", sw=0.7, rx=2)
    f.text(x_a + 16 + (w_cs - 12) / 2, y_cs + 40, "C[i,j] = sum_k(A[i,k] * B[k,j])", size=6.6, mono=True, weight=700, fill="#1E40AF", anchor="middle")
    f.text(x_a + 16, y_cs + 60, "Không phụ thuộc phần cứng", size=6.6, fill="#047857")
    f.text(x_a + 16, y_cs + 70, "Bảo đảm tính đúng đắn toán học", size=6.6, fill="#047857")

    # Schedule Box
    rect(f, x_a + 210, y_cs, w_cs, 78, fill="#ECFDF5", stroke="#10B981", sw=0.9, rx=3)
    f.text(x_a + 216, y_cs + 10, "Schedule: Tính NHƯ THẾ NÀO (Lịch trình)", size=6.8, weight=700, fill="#047857")
    f.text(x_a + 216, y_cs + 22, "Biến đổi vòng lặp theo phần cứng mục tiêu:", size=6.6, fill="#065F46")
    f.text(x_a + 216, y_cs + 35, "• Tiling / Split: Chia khối ma trận vào SRAM", size=6.6, fill="#047857")
    f.text(x_a + 216, y_cs + 47, "• Reorder / Unroll: Tối ưu thanh ghi & cache", size=6.6, fill="#047857")
    f.text(x_a + 216, y_cs + 59, "• Vectorize: Lệnh SIMD đa chiều", size=6.6, fill="#047857")
    f.text(x_a + 216, y_cs + 71, "• Tensorize: Lệnh phần cứng GEMM/Systolic", size=6.6, weight=700, fill="#065F46")

    # Summary Takeaway Box
    y_cstk = y_cs + 84
    rect(f, x_a + 10, y_cstk, w_a - 20, 60, fill="#FFFBEB", stroke="#F59E0B", sw=0.8, rx=3)
    f.text(x_a + 14, y_cstk + 9, "Bản chất cốt lõi của Tensor Expression [T2 TVM tr.4]:", size=6.8, weight=700, fill="#92400E")
    f.text(x_a + 14, y_cstk + 21, "• Phân tách rạch ròi: Cùng 1 biểu thức Compute có hàng triệu Schedule khác nhau", size=6.6, fill="#78350F")
    f.text(x_a + 14, y_cstk + 33, "• Tự do thử nghiệm hoán đổi thứ tự lặp, tile kích thước mà KHÔNG sợ làm sai lệch kết quả!", size=6.6, weight=700, fill="#B45309")
    f.text(x_a + 14, y_cstk + 47, "-> Mở đường cho hệ thống tự động tìm kiếm lịch trình (Auto-tuning / AutoTVM).", size=6.6, fill="#92400E")

    # ==========================================================================
    # CỘT PHẢI: PANEL B - AUTOTVM & MÔ HÌNH CHI PHÍ HỌC MÁY
    # ==========================================================================
    x_b = 446
    w_b = 416
    rect(f, x_b, card_y, w_b, card_h, fill="#F8FAFC", stroke="#7C3AED", sw=1.3, rx=6)
    rect(f, x_b, card_y, w_b, 32, fill="#F5F3FF", stroke="#7C3AED", sw=1.0, rx=6)
    rect(f, x_b + 8, card_y + 6, 5, 20, fill="#7C3AED", stroke="#7C3AED", rx=2)
    f.text(x_b + 18, card_y + 13, "B. AutoTVM: Lập lịch Tự động bằng Học máy", size=9.6, weight=700, fill="#5B21B6")
    f.text(x_b + 18, card_y + 24, "Không gian lịch trình khổng lồ và vòng lặp học máy khép kín [T2 TVM tr.8-9]", size=6.8, fill="#475569")

    # B1. Thách thức Schedule Space vs Blackbox
    y_b1 = 86
    h_b1 = 90
    rect(f, x_b + 6, y_b1, w_b - 12, h_b1, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_b + 6, y_b1, w_b - 12, 16, fill="#F5F3FF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_b + 12, y_b1 + 8, "1. Thách thức: Bùng nổ Không gian Lịch trình (Schedule Space)", size=7.2, weight=700, fill="#6D28D9")

    # Comparison 2 boxes
    y_b1c = y_b1 + 22
    w_b1c = 194

    rect(f, x_b + 10, y_b1c, w_b1c, 62, fill="#FEF2F2", stroke="#EF4444", sw=0.8, rx=3)
    f.text(x_b + 16, y_b1c + 9, "Không gian hàng triệu cấu hình:", size=6.8, weight=700, fill="#B91C1C")
    f.text(x_b + 16, y_b1c + 21, "• Tổ hợp: Tile size x Loop order x Unroll", size=6.6, fill="#7F1D1D")
    f.text(x_b + 16, y_b1c + 33, "• Blackbox Auto-tuning: Đo từng cấu hình", size=6.6, fill="#7F1D1D")
    f.text(x_b + 16, y_b1c + 45, "  trên bo mạch thật -> Quá chậm, bất khả thi!", size=6.6, weight=700, fill="#991B1B")

    rect(f, x_b + 210, y_b1c, w_b1c, 62, fill="#ECFDF5", stroke="#10B981", sw=0.8, rx=3)
    f.text(x_b + 216, y_b1c + 9, "Giải pháp TVM: Học máy định hướng:", size=6.8, weight=700, fill="#047857")
    f.text(x_b + 216, y_b1c + 21, "• ML-based Cost Model (XGBoost/Tree-RNN)", size=6.6, weight=700, fill="#065F46")
    f.text(x_b + 216, y_b1c + 33, "• Dự đoán độ trễ từ cây cú pháp Loop AST", size=6.6, fill="#047857")
    f.text(x_b + 216, y_b1c + 45, "• Chỉ đo phần cứng với cấu hình hứa hẹn!", size=6.6, weight=700, fill="#15803D")

    # B2. Closed-Loop ML Tuning Architecture
    y_b2 = 182
    h_b2 = 154
    rect(f, x_b + 6, y_b2, w_b - 12, h_b2, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_b + 6, y_b2, w_b - 12, 16, fill="#F5F3FF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_b + 12, y_b2 + 8, "2. Vòng lặp Khép kín Tự động Tối ưu (Closed-Loop ML Tuning)", size=7.2, weight=700, fill="#6D28D9")

    # 3 Stage Boxes on Top
    y_st = y_b2 + 24
    w_st = 114
    h_st = 40

    # Stage 1: Explorer
    x_s1 = x_b + 10
    rect(f, x_s1, y_st, w_st, h_st, fill="#EFF6FF", stroke="#3B82F6", sw=1.0, rx=3)
    f.text(x_s1 + w_st / 2, y_st + 10, "[1] Schedule Explorer", size=6.8, weight=700, fill="#1D4ED8", anchor="middle")
    f.text(x_s1 + w_st / 2, y_st + 21, "Genetic Search / SA", size=6.6, fill="#1E40AF", anchor="middle")
    f.text(x_s1 + w_st / 2, y_st + 30, "Sinh cấu hình ứng viên", size=6.6, fill="#475569", anchor="middle")

    arrow(f, x_s1 + w_st, y_st + h_st / 2, x_s1 + w_st + 18, y_st + h_st / 2, color=BLUE, sw=1.2)

    # Stage 2: Loop AST
    x_s2 = x_s1 + w_st + 18
    rect(f, x_s2, y_st, w_st + 4, h_st, fill="#FEF3C7", stroke="#F59E0B", sw=1.0, rx=3)
    f.text(x_s2 + (w_st + 4) / 2, y_st + 10, "[2] Loop AST Features", size=6.8, weight=700, fill="#B45309", anchor="middle")
    f.text(x_s2 + (w_st + 4) / 2, y_st + 21, "Trích đặc trưng vòng lặp", size=6.6, fill="#92400E", anchor="middle")
    f.text(x_s2 + (w_st + 4) / 2, y_st + 30, "Memory footprint, stride", size=6.6, fill="#78350F", anchor="middle")

    arrow(f, x_s2 + w_st + 4, y_st + h_st / 2, x_s2 + w_st + 22, y_st + h_st / 2, color=AMBER, sw=1.2)

    # Stage 3: ML Model
    x_s3 = x_s2 + w_st + 22
    rect(f, x_s3, y_st, w_st + 4, h_st, fill="#F3E8FF", stroke="#9333EA", sw=1.0, rx=3)
    f.text(x_s3 + (w_st + 4) / 2, y_st + 10, "[3] ML Cost Model", size=6.8, weight=700, fill="#7E22CE", anchor="middle")
    f.text(x_s3 + (w_st + 4) / 2, y_st + 21, "XGBoost / Tree-RNN", size=6.6, weight=700, fill="#6B21A8", anchor="middle")
    f.text(x_s3 + (w_st + 4) / 2, y_st + 30, "Dự đoán độ trễ cực nhanh", size=6.6, fill="#475569", anchor="middle")

    # Downward arrow to Hardware Evaluation
    y_hw = y_st + 56
    arrow(f, x_s3 + (w_st + 4) / 2, y_st + h_st, x_s3 + (w_st + 4) / 2, y_hw, color="#7C3AED", sw=1.2)
    f.text(x_s3 + (w_st + 4) / 2 - 6, y_st + h_st + 8, "Top-K", size=6.6, weight=700, fill="#7C3AED", anchor="end")

    # Stage 4: Hardware Measurement Box
    x_hw = x_b + 230
    w_hw = 174
    rect(f, x_hw, y_hw, w_hw, 35, fill="#ECFDF5", stroke="#10B981", sw=1.2, rx=3)
    f.text(x_hw + w_hw / 2, y_hw + 9, "[4] Đo Thực Tế Trên Hardware", size=6.8, weight=700, fill="#047857", anchor="middle")
    f.text(x_hw + w_hw / 2, y_hw + 19, "Target Device: CPU / GPU / NPU", size=6.6, fill="#065F46", anchor="middle")
    f.text(x_hw + w_hw / 2, y_hw + 27, "Biên dịch & đo thời gian thực tế", size=6.6, fill="#475569", anchor="middle")

    # Feedback Loop (Red arrow from Hardware back to Stage 1 and Stage 3)
    f.line([(x_hw, y_hw + 17.5), (x_s1 + w_st / 2, y_hw + 17.5)], color=RED, width=1.2, dashed=True)
    arrow(f, x_s1 + w_st / 2, y_hw + 17.5, x_s1 + w_st / 2, y_st + h_st, color=RED, sw=1.2, dashed=True)

    # Feedback badge on the line
    rect(f, x_b + 38, y_hw + 6.5, 172, 22, fill="#FEF2F2", stroke="#EF4444", sw=0.8, rx=2)
    f.text(x_b + 124, y_hw + 13, "Phản hồi: Thời gian đo thực tế", size=6.6, weight=700, fill="#B91C1C", anchor="middle")
    f.text(x_b + 124, y_hw + 22, "huấn luyện lại mô hình chi phí ML", size=6.6, fill="#7F1D1D", anchor="middle")

    # ML Benefit note
    y_mltk = y_hw + 41
    rect(f, x_b + 10, y_mltk, w_b - 20, 22, fill="#F5F3FF", stroke="#8B5CF6", sw=0.8, rx=3)
    f.text(x_b + 14, y_mltk + 7, "Ưu thế cốt lõi của ML Cost Model [T2 TVM tr.8]:", size=6.8, weight=700, fill="#5B21B6")
    f.text(x_b + 14, y_mltk + 16, "Càng đo nhiều mô hình càng chính xác; loại bỏ 99% cấu hình tồi trước khi đo!", size=6.6, fill="#6D28D9")

    # B3. Quantitative Results & Tradeoffs
    y_b3 = 342
    h_b3 = 120
    rect(f, x_b + 6, y_b3, w_b - 12, h_b3, fill="#FFFBEB", stroke="#F59E0B", sw=0.9, rx=4)
    f.text(x_b + 12, y_b3 + 12, "3. Đánh đổi & Giá trị Thực tiễn của TVM [Chen 2018]:", size=7.0, weight=700, fill="#92400E")
    f.text(x_b + 12, y_b3 + 27, "• Tốc độ hội tụ: Nhanh hơn 2x - 10x so với auto-tuning hộp đen không có ML", size=6.6, fill="#78350F")
    f.text(x_b + 12, y_b3 + 41, "• Hiệu năng Kernel: Đạt 85% - 105% so với thư viện viết tay của chuyên gia (cuDNN)", size=6.6, fill="#78350F")
    f.text(x_b + 12, y_b3 + 55, "• Tính di động (Portability): 1 codebase thống nhất cho CPU, GPU và NPU chuyên dụng", size=6.6, weight=700, fill="#B45309")
    f.text(x_b + 12, y_b3 + 71, "• Cơ chế Tensorization: Ánh xạ vòng lặp vào lệnh ma trận phần cứng (GEMM/Systolic)", size=6.6, fill="#78350F")
    f.text(x_b + 12, y_b3 + 89, "Ranh giới: RK3588 dùng RKNN toolkit kín, không công bố có dùng ML cost model hay không", size=6.6, italic=True, fill="#92400E")
    f.text(x_b + 12, y_b3 + 103, "Các kỹ thuật TVM dùng để hiểu nguyên lý chung, không gán trực tiếp cho RKNN", size=6.6, italic=True, fill="#92400E")

    # Dòng nguồn đáy trang
    source(f, card_y + card_h + 10, "Nguồn: T2 TVM tr.3-4 (Chen et al., OSDI 2018: Graph/Op Optimization & Fusion); T2 TVM tr.8-9 (AutoTVM ML Cost Model & Loop AST).")

    return f


# ==============================================================================
# 5. HÌNH ĐỒNG THIẾT KẾ HW/SW TRONG EIQ NEUTRON (neu-01-hw-sw-codesign)
# ==============================================================================
def fig_eiq_neutron_hw_sw_codesign():
    H = 510
    f = Fig(W, H)
    tier(f, "T2 chung", x=W - 130, y=12)
    f.text(18, 22, "Kiến trúc Đồng thiết kế HW/SW trong eIQ Neutron: Compiler CP Solver và NPU Subsystem",
           size=13.0, weight=700, fill=DARK)
    f.text(18, 36, "Vòng lặp co-design: Bộ giải Quy hoạch Ràng buộc (CP) điều phối Vi kiến trúc đa nhân và TCM [T2 BAMB tr.3-5]",
           size=7.5, fill="#64748B")

    card_y = 48
    card_h = 422
    x_a = 18
    w_a = 416
    x_b = 446
    w_b = 416

    # ==========================================================================
    # CỘT TRÁI: SOFTWARE - EIQ NEUTRON COMPILER STACK
    # ==========================================================================
    rect(f, x_a, card_y, w_a, card_h, fill="#F8FAFC", stroke="#2563EB", sw=1.3, rx=6)
    rect(f, x_a, card_y, w_a, 32, fill="#EFF6FF", stroke="#2563EB", sw=1.0, rx=6)
    rect(f, x_a + 8, card_y + 6, 5, 20, fill=BLUE, stroke=BLUE, sw=1, rx=2)
    f.text(x_a + 18, card_y + 13, "A. eIQ Neutron Compiler: Quy hoạch Ràng buộc (CP Solver)", size=9.6, weight=700, fill="#1E40AF")
    f.text(x_a + 18, card_y + 24, "Frontend IR, CP-based Spatial/Temporal Tiling & Layer Fusion [T2 BAMB tr.4]", size=6.8, fill="#475569")

    # A1. Frontend & Graph Ingestion
    y_a1 = 86
    h_a1 = 54
    rect(f, x_a + 6, y_a1, w_a - 12, h_a1, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_a + 6, y_a1, w_a - 12, 16, fill="#EFF6FF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_a + 12, y_a1 + 8, "1. Frontend: Ingest Đồ thị Mô hình (LiteRT / ONNX IR)", size=7.2, weight=700, fill="#1E40AF")

    # Mini DAG nodes with arrow length >= 15px
    y_dag = y_a1 + 22
    dag_nodes = [("Conv2D", 54), ("ReLU", 42), ("Conv2D", 54), ("Add", 38)]
    cur_x = x_a + 10
    for idx, (n_name, n_w) in enumerate(dag_nodes):
        rect(f, cur_x, y_dag, n_w, 20, fill="#F1F5F9", stroke="#64748B", sw=0.8, rx=2)
        f.text(cur_x + n_w / 2, y_dag + 10, n_name, size=6.6, weight=700, fill=DARK, anchor="middle")
        if idx < len(dag_nodes) - 1:
            arrow(f, cur_x + n_w + 1, y_dag + 10, cur_x + n_w + 17, y_dag + 10, color=BLUE, sw=1.0)
            cur_x += n_w + 18
        else:
            cur_x += n_w + 8
    rect(f, cur_x, y_dag, 118, 20, fill="#EFF6FF", stroke="#3B82F6", sw=0.8, rx=2)
    f.text(cur_x + 59, y_dag + 10, "DAG Tensor đa chiều", size=6.6, fill="#1D4ED8", anchor="middle")

    # A2. Mid-End CP Solver
    y_a2 = 146
    h_a2 = 158
    rect(f, x_a + 6, y_a2, w_a - 12, h_a2, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_a + 6, y_a2, w_a - 12, 16, fill="#EFF6FF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_a + 12, y_a2 + 8, "2. Mid-End CP Solver: Giải đồng thời 3 Ràng buộc Tối ưu [T2 BAMB tr.4]", size=7.2, weight=700, fill="#1E40AF")

    # 3 Optimization Targets
    y_t = y_a2 + 20
    # Target 1: Spatial Tiling
    rect(f, x_a + 10, y_t, w_a - 20, 36, fill="#F0FDF4", stroke="#22C55E", sw=0.8, rx=3)
    f.text(x_a + 16, y_t + 9, "a) Phân khối Không gian (Spatial Tiling): Chọn Line Parallelism", size=6.8, weight=700, fill="#15803D")
    f.text(x_a + 16, y_t + 22, "• Chia outH cho 4 Engine -> Trọng số phát broadcast dùng chung, giảm 4x đọc SRAM [BAMB tr.4]", size=6.6, fill="#166534")

    # Target 2: Temporal Tiling
    y_t2 = y_t + 40
    rect(f, x_a + 10, y_t2, w_a - 20, 36, fill="#F8FAFC", stroke="#64748B", sw=0.8, rx=3)
    f.text(x_a + 16, y_t2 + 9, "b) Phân khối Thời gian (Temporal Tiling): Cắt lát theo bộ đệm", size=6.8, weight=700, fill=DARK)
    f.text(x_a + 16, y_t2 + 22, "• Ràng buộc cứng: Tổng footprint tile + phụ thuộc <= Dung lượng TCM (1 MiB) [BAMB tr.4, tr.7]", size=6.6, fill="#475569")

    # Target 3: Layer Fusion
    y_t3 = y_t2 + 40
    rect(f, x_a + 10, y_t3, w_a - 20, 44, fill="#FFFBEB", stroke="#F59E0B", sw=0.8, rx=3)
    f.text(x_a + 16, y_t3 + 9, "c) Hợp nhất Lớp (Layer Fusion): Thực thi xen kẽ các lớp", size=6.8, weight=700, fill="#B45309")
    f.text(x_a + 16, y_t3 + 22, "• Đẩy thẳng output lớp trước làm input lớp sau trong TCM; triệt tiêu hoàn toàn tràn DRAM", size=6.6, fill="#78350F")
    f.text(x_a + 16, y_t3 + 34, "• Không xung đột Bank: CP xếp địa chỉ so le cho non-arbitrated TCM (0 stall) [BAMB tr.3]", size=6.6, weight=700, fill="#B45309")

    # A3. Backend DAE Codegen
    y_a3 = 310
    h_a3 = 152
    rect(f, x_a + 6, y_a3, w_a - 12, h_a3, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_a + 6, y_a3, w_a - 12, 16, fill="#EFF6FF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_a + 12, y_a3 + 8, "3. Backend Codegen: Lập lịch Tách biệt Truy cập - Tính toán (DAE)", size=7.2, weight=700, fill="#1E40AF")

    # 3 Lanes of DAE Jobs
    y_j = y_a3 + 22
    lanes = [
        ("Compute Jobs", "Gọi C-kernel điều khiển 4 Engine (N=M=16, 2NM op/chu kỳ)", "#F0FDF4", "#22C55E", "#15803D"),
        ("Data-mover Jobs", "DMA strided transfers nạp DRAM <-> TCM và copy TCM-to-TCM", "#EFF6FF", "#3B82F6", "#1D4ED8"),
        ("Sync Barriers", "Rào chắn đồng bộ trạng thái giữa các timestep tick trong MCU", "#FFF7ED", "#FB923C", "#C2410C"),
    ]
    for idx, (l_title, l_desc, l_bg, l_bd, l_tc) in enumerate(lanes):
        ly = y_j + idx * 30
        rect(f, x_a + 10, ly, 92, 24, fill=l_bg, stroke=l_bd, sw=0.8, rx=2)
        f.text(x_a + 56, ly + 12, l_title, size=6.6, weight=700, fill=l_tc, anchor="middle")
        rect(f, x_a + 106, ly, w_a - 120, 24, fill="#F8FAFC", stroke="#CBD5E1", sw=0.7, rx=2)
        f.text(x_a + 112, ly + 12, l_desc, size=6.6, fill=DARK)

    # DAE Takeaway box
    y_dtk = y_j + 94
    rect(f, x_a + 10, y_dtk, w_a - 20, 28, fill="#ECFDF5", stroke="#10B981", sw=0.8, rx=3)
    f.text(x_a + 14, y_dtk + 9, "Bản chất DAE: DMA nạp trước tile t+1 song song khi Engine tính tile t", size=6.8, weight=700, fill="#047857")
    f.text(x_a + 14, y_dtk + 20, "Ẩn hoàn toàn độ trễ bộ nhớ ngoài DRAM sau tính toán! [T2 BAMB tr.4]", size=6.6, fill="#065F46")

    # ==========================================================================
    # CỘT PHẢI: HARDWARE - EIQ NEUTRON NPU SUBSYSTEM
    # ==========================================================================
    rect(f, x_b, card_y, w_b, card_h, fill="#F0FDF4", stroke="#16A34A", sw=1.3, rx=6)
    rect(f, x_b, card_y, w_b, 32, fill="#DCFCE7", stroke="#16A34A", sw=1.0, rx=6)
    rect(f, x_b + 8, card_y + 6, 5, 20, fill=GREEN, stroke=GREEN, sw=1, rx=2)
    f.text(x_b + 18, card_y + 13, "B. eIQ Neutron NPU Subsystem: Mảng Tính toán & TCM", size=9.6, weight=700, fill="#15803D")
    f.text(x_b + 18, card_y + 24, "RISC-V MCU, Multi-Banked TCM, 4 Engine Broadcast & Line Parallelism [T2 BAMB tr.3]", size=6.8, fill="#475569")

    # B1. RISC-V Controller & DMA Mover
    y_b1 = 86
    h_b1 = 54
    rect(f, x_b + 6, y_b1, w_b - 12, h_b1, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_b + 6, y_b1, w_b - 12, 16, fill="#DCFCE7", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_b + 12, y_b1 + 8, "1. Điều khiển & Luân chuyển: RISC-V Controller & DMA Engine", size=7.2, weight=700, fill="#15803D")

    w_sub = (w_b - 28) // 2
    # Left: RISC-V Controller
    rect(f, x_b + 10, y_b1 + 20, w_sub, 28, fill="#F8FAFC", stroke="#64748B", sw=0.8, rx=2)
    f.text(x_b + 16, y_b1 + 29, "RISC-V MCU Controller", size=6.8, weight=700, fill=DARK)
    f.text(x_b + 16, y_b1 + 40, "Dispatch DAE jobs theo tick [BAMB tr.3]", size=6.6, fill="#64748B")

    # Right: DMA Engine
    rect(f, x_b + 18 + w_sub, y_b1 + 20, w_sub, 28, fill="#F8FAFC", stroke="#64748B", sw=0.8, rx=2)
    f.text(x_b + 24 + w_sub, y_b1 + 29, "DMA Engine & Data Mover", size=6.8, weight=700, fill=DARK)
    f.text(x_b + 24 + w_sub, y_b1 + 40, "Strided transfers DRAM <-> TCM", size=6.6, fill="#64748B")

    # B2. Tightly Coupled Memory (TCM - 1 MiB Multi-Banked)
    y_b2 = 146
    h_b2 = 58
    rect(f, x_b + 6, y_b2, w_b - 12, h_b2, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_b + 6, y_b2, w_b - 12, 16, fill="#DCFCE7", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_b + 12, y_b2 + 8, "2. Tightly Coupled Memory (TCM): 1 MiB SRAM On-chip chia 8 Bank", size=7.2, weight=700, fill="#15803D")

    # 8 Bank cells
    y_bnk = y_b2 + 20
    w_bnk = 44
    gap_bnk = 6
    for b in range(8):
        bx = x_b + 10 + b * (w_bnk + gap_bnk)
        rect(f, bx, y_bnk, w_bnk, 20, fill="#EFF6FF", stroke="#3B82F6", sw=0.8, rx=2)
        f.text(bx + w_bnk / 2, y_bnk + 10, f"Bank {b}", size=6.6, weight=700, fill="#1E40AF", anchor="middle")
    f.text(x_b + 12, y_b2 + 49, "Non-arbitrated SRAM: Compiler sắp xếp địa chỉ không xung đột -> Băng thông tối đa, giá thành thấp [BAMB tr.3]", size=6.6, fill="#15803D")

    # B3. 4 Compute Engines & Line Parallelism
    y_b3 = 210
    h_b3 = 192
    rect(f, x_b + 6, y_b3, w_b - 12, h_b3, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_b + 6, y_b3, w_b - 12, 16, fill="#DCFCE7", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_b + 12, y_b3 + 8, "3. 4 Compute Engines (2 TOPS): Line Parallelism & Shared Broadcast Bus", size=7.2, weight=700, fill="#15803D")

    # Shared Broadcast Bus Bar
    y_bus = y_b3 + 22
    rect(f, x_b + 10, y_bus, w_b - 20, 20, fill="#FFFBEB", stroke="#D97706", sw=1.0, rx=3)
    f.text(x_b + 16, y_bus + 10, "Shared Operand Bus (Broadcast): Trọng số W đọc 1 lần từ TCM -> Phát đồng thời cho 4 Engine", size=6.8, weight=700, fill="#B45309")

    # 4 Engines Visual
    y_eng = y_bus + 26
    eng_h = 24
    for e in range(4):
        ey = y_eng + e * (eng_h + 5)
        # Engine Label
        rect(f, x_b + 10, ey, 62, eng_h, fill="#EFF6FF", stroke="#2563EB", sw=0.8, rx=2)
        f.text(x_b + 41, ey + 12, f"Engine {e}", size=6.6, weight=700, fill="#1E40AF", anchor="middle")

        # Line input
        rect(f, x_b + 76, ey, 72, eng_h, fill="#F8FAFC", stroke="#64748B", sw=0.7, rx=2)
        f.text(x_b + 112, ey + 12, f"Dòng outH {e}", size=6.6, fill=DARK, anchor="middle")

        # Dot Product Unit
        rect(f, x_b + 152, ey, 102, eng_h, fill="#ECFDF5", stroke="#10B981", sw=0.8, rx=2)
        f.text(x_b + 203, ey + 12, "Dot-Product (16x16)", size=6.6, weight=700, fill="#047857", anchor="middle")

        # Accumulator & Act
        rect(f, x_b + 258, ey, 78, eng_h, fill="#F1F5F9", stroke="#64748B", sw=0.7, rx=2)
        f.text(x_b + 297, ey + 12, "Scratchpad+Act", size=6.6, fill=DARK, anchor="middle")

        # Output Target Bank
        rect(f, x_b + 340, ey, 58, eng_h, fill="#DCFCE7", stroke="#16A34A", sw=0.8, rx=2)
        f.text(x_b + 369, ey + 12, f"-> Bank {e}", size=6.6, weight=700, fill="#15803D", anchor="middle")

    # Line Parallelism Note
    y_enote = y_eng + 4 * (eng_h + 5) + 2
    f.text(x_b + 12, y_enote + 8, "Bản chất Line Parallelism: 4 Engine tính 4 dòng song song, dùng chung tham số", size=6.8, weight=700, fill="#15803D")
    f.text(x_b + 12, y_enote + 20, "Ghi kết quả vào 4 Bank TCM riêng biệt -> Không tranh chấp bus dữ liệu! [BAMB tr.4]", size=6.6, fill="#166534")

    # B4. Off-chip DRAM Box
    y_b4 = 408
    h_b4 = 54
    rect(f, x_b + 6, y_b4, w_b - 12, h_b4, fill="#FFF9F9", stroke="#EF4444", sw=0.9, rx=4)
    rect(f, x_b + 6, y_b4, w_b - 12, 16, fill="#FEF2F2", stroke="#EF4444", sw=0.8, rx=3)
    f.text(x_b + 12, y_b4 + 8, "4. Bộ nhớ ngoài SoC DRAM (Off-chip DDR - 12 GB/s): Giảm tải tối đa", size=7.2, weight=700, fill="#B91C1C")
    f.text(x_b + 12, y_b4 + 26, "• Chỉ nạp trọng số ban đầu và ghi kết quả cuối; hoàn toàn ẩn sau tính toán nhờ DAE", size=6.6, fill="#7F1D1D")
    f.text(x_b + 12, y_b4 + 38, "• Nhờ HW/SW Co-Design: 100% activation trung gian nằm trong TCM, triệt tiêu nghẽn DRAM!", size=6.6, weight=700, fill="#B91C1C")

    # Dòng nguồn đáy trang
    source(f, card_y + card_h + 10, "Nguồn: T2 BAMB tr.3-5 (Bamberg et al., IEEE Transactions on Computers 2025: eIQ Neutron NPU Architecture & Compiler Co-Design).")

    return f


# ==============================================================================
# 6. HÌNH NGHỊCH LÝ TOPS VÀ BĂNG THÔNG DRAM (neu-02-effective-vs-peak-tops)
# ==============================================================================
def fig_eiq_neutron_effective_vs_peak_tops():
    card_y = 48
    card_h = 300
    H = card_y + card_h + 28
    f = Fig(W, H)
    tier(f, "T2 chung", x=W - 130, y=12)
    f.text(18, 22, "Nghịch lý TOPS Danh định và Băng thông DRAM: So sánh Thực nghiệm trên eIQ Neutron",
           size=13.0, weight=700, fill=DARK)
    f.text(18, 36, "Đối chiếu giữa NPU rời rạc 11 TOPS nghẽn bộ nhớ vs eIQ Neutron 2 TOPS có HW/SW Co-Design [T2 BAMB Table I & III]",
           size=7.5, fill="#64748B")

    x_a = 18
    w_a = 416
    x_b = 446
    w_b = 416

    # ==========================================================================
    # CỘT TRÁI: NPU RỜI RẠC 11 TOPS (MEMORY-BOUND)
    # ==========================================================================
    rect(f, x_a, card_y, w_a, card_h, fill="#FFF9F9", stroke="#DC2626", sw=1.3, rx=6)
    rect(f, x_a, card_y, w_a, 32, fill="#FEF2F2", stroke="#DC2626", sw=1.0, rx=6)
    rect(f, x_a + 8, card_y + 6, 5, 20, fill=RED, stroke=RED, sw=1, rx=2)
    f.text(x_a + 18, card_y + 13, "A. NPU Rời rạc 11 TOPS: Nghẽn Băng thông DRAM", size=9.6, weight=700, fill="#B91C1C")
    f.text(x_a + 18, card_y + 24, "Mảng MAC lớn nhưng thiếu Co-Design với Compiler & SRAM [T2 BAMB tr.1, tr.9]", size=6.8, fill="#7F1D1D")

    # Metrics Box
    y_m1 = 86
    rect(f, x_a + 8, y_m1, w_a - 16, 78, fill="#FFFFFF", stroke="#CBD5E1", sw=0.9, rx=4)
    f.text(x_a + 14, y_m1 + 12, "Số liệu Đo lường Thực tế trên Phần cứng [Table I & Table III]:", size=7.0, weight=700, fill=DARK)

    # 4 Metric pills
    metrics_a = [
        ("Peak TOPS Danh định", "11.0 TOPS", "#F1F5F9", "#64748B", DARK),
        ("Effective ResNet50", "0.89 TOPS (8.1%)", "#FEF2F2", "#EF4444", "#B91C1C"),
        ("Effective EfficientNet", "0.26 TOPS (2.4%)", "#FEF2F2", "#EF4444", "#B91C1C"),
        ("Độ trễ MobileNetV3", "2.0 ms (LTP: 22.3)", "#FEF2F2", "#EF4444", "#B91C1C"),
    ]
    for idx, (m_l, m_v, m_bg, m_bd, m_tc) in enumerate(metrics_a):
        row = idx // 2
        col = idx % 2
        px = x_a + 14 + col * 196
        py = y_m1 + 24 + row * 24
        rect(f, px, py, 190, 20, fill=m_bg, stroke=m_bd, sw=0.7, rx=2)
        f.text(px + 6, py + 10, m_l + ":", size=6.6, fill=DARK)
        f.text(px + 184, py + 10, m_v, size=6.6, weight=700, fill=m_tc, anchor="end")

    # Physical Visualization: Idle MACs
    y_p1 = 170
    rect(f, x_a + 8, y_p1, w_a - 16, 80, fill="#FFFFFF", stroke="#DC2626", sw=1.0, rx=4)
    rect(f, x_a + 8, y_p1, w_a - 16, 16, fill="#FEF2F2", stroke="#DC2626", sw=0.8, rx=3)
    f.text(x_a + 14, y_p1 + 8, "Cơ chế Vật lý: Mảng MAC Đói Dữ liệu (DRAM Starvation)", size=7.2, weight=700, fill="#B91C1C")

    # Huge Idle MAC array representation
    rect(f, x_a + 14, y_p1 + 22, 160, 48, fill="#F1F5F9", stroke="#94A3B8", sw=0.8, dashed=True, rx=3)
    f.text(x_a + 94, y_p1 + 38, "Mảng MAC 11 TOPS", size=7.0, weight=700, fill="#64748B", anchor="middle")
    f.text(x_a + 94, y_p1 + 54, "97.6% thời gian NHÀN RỖI!", size=6.8, weight=700, fill="#B91C1C", anchor="middle")

    # Saturated DRAM bus
    arrow(f, x_a + 180, y_p1 + 46, x_a + 230, y_p1 + 46, color=RED, sw=THICK)
    f.text(x_a + 205, y_p1 + 34, "Nghẽn DRAM", size=6.6, weight=700, fill=RED, anchor="middle")

    rect(f, x_a + 236, y_p1 + 22, 158, 48, fill="#FEF2F2", stroke="#EF4444", sw=0.9, rx=3)
    f.text(x_a + 315, y_p1 + 38, "DRAM Bus 100% Quá tải", size=7.0, weight=700, fill="#B91C1C", anchor="middle")
    f.text(x_a + 315, y_p1 + 54, "Tensor trung gian tràn ra DDR", size=6.6, fill="#7F1D1D", anchor="middle")

    # Takeaway Box
    y_tk1 = 256
    rect(f, x_a + 8, y_tk1, w_a - 16, 84, fill="#FEF2F2", stroke="#EF4444", sw=0.8, rx=4)
    f.text(x_a + 14, y_tk1 + 12, "Kết luận Vật lý về NPU Rời rạc [T2 BAMB tr.1, tr.9]:", size=7.0, weight=700, fill="#991B1B")
    f.text(x_a + 14, y_tk1 + 28, "• TOPS danh định cao chỉ phản ánh số nhân MAC trên silicon, không phản ánh hiệu năng", size=6.6, fill="#7F1D1D")
    f.text(x_a + 14, y_tk1 + 44, "• Thiếu SRAM và thiếu Layer Fusion -> Mọi tensor trung gian đều phải qua DRAM ngoài", size=6.6, fill="#7F1D1D")
    f.text(x_a + 14, y_tk1 + 60, "• Kết quả: NPU 11 TOPS chậm hơn cả NPU 2 TOPS trên EfficientNet Lite0!", size=6.6, weight=700, fill="#B91C1C")
    f.text(x_a + 14, y_tk1 + 74, "• Độ trễ MobileNetV3 đạt 2.0 ms (chậm hơn 2.5x so với eIQ Neutron có co-design)", size=6.6, fill="#7F1D1D")

    # ==========================================================================
    # CỘT PHẢI: EIQ NEUTRON 2 TOPS (COMPUTE-BOUND VỚI CO-DESIGN)
    # ==========================================================================
    rect(f, x_b, card_y, w_b, card_h, fill="#F0FDF4", stroke="#16A34A", sw=1.3, rx=6)
    rect(f, x_b, card_y, w_b, 32, fill="#DCFCE7", stroke="#16A34A", sw=1.0, rx=6)
    rect(f, x_b + 8, card_y + 6, 5, 20, fill=GREEN, stroke=GREEN, sw=1, rx=2)
    f.text(x_b + 18, card_y + 13, "B. eIQ Neutron 2 TOPS: Tối ưu nhờ HW/SW Co-Design", size=9.6, weight=700, fill="#15803D")
    f.text(x_b + 18, card_y + 24, "Mảng tính toán vừa phải, giữ trọn dữ liệu trong TCM nhờ CP Solver [T2 BAMB tr.8-9]", size=6.8, fill="#166534")

    # Metrics Box
    rect(f, x_b + 8, y_m1, w_b - 16, 78, fill="#FFFFFF", stroke="#CBD5E1", sw=0.9, rx=4)
    f.text(x_b + 14, y_m1 + 12, "Số liệu Đo lường Thực tế trên Phần cứng [Table I & Table III]:", size=7.0, weight=700, fill=DARK)

    # 4 Metric pills
    metrics_b = [
        ("Peak TOPS Danh định", "2.0 TOPS (Tiết kiệm silicon)", "#F1F5F9", "#64748B", DARK),
        ("Effective ResNet50", "0.73 TOPS (Hiệu suất 36.5%)", "#ECFDF5", "#22C55E", "#15803D"),
        ("Effective EfficientNet", "0.82 TOPS (41.0% - Gấp 3.15x!)", "#ECFDF5", "#22C55E", "#15803D"),
        ("Độ trễ MobileNetV3", "0.8 ms (Nhanh gấp 2.5x!)", "#ECFDF5", "#22C55E", "#15803D"),
    ]
    for idx, (m_l, m_v, m_bg, m_bd, m_tc) in enumerate(metrics_b):
        row = idx // 2
        col = idx % 2
        px = x_b + 14 + col * 196
        py = y_m1 + 24 + row * 24
        rect(f, px, py, 190, 20, fill=m_bg, stroke=m_bd, sw=0.7, rx=2)
        f.text(px + 6, py + 10, m_l + ":", size=6.6, fill=DARK)
        f.text(px + 184, py + 10, m_v, size=6.6, weight=700, fill=m_tc, anchor="end")

    # Physical Visualization: Active MACs + TCM Locality
    rect(f, x_b + 8, y_p1, w_b - 16, 80, fill="#FFFFFF", stroke="#16A34A", sw=1.0, rx=4)
    rect(f, x_b + 8, y_p1, w_b - 16, 16, fill="#DCFCE7", stroke="#16A34A", sw=0.8, rx=3)
    f.text(x_b + 14, y_p1 + 8, "Cơ chế Vật lý: Khai thác Triệt để TCM On-Chip (Memory Locality)", size=7.2, weight=700, fill="#15803D")

    # Efficient MAC array
    rect(f, x_b + 14, y_p1 + 22, 160, 48, fill="#ECFDF5", stroke="#10B981", sw=0.9, rx=3)
    f.text(x_b + 94, y_p1 + 38, "Mảng 4 Engine (2 TOPS)", size=7.0, weight=700, fill="#047857", anchor="middle")
    f.text(x_b + 94, y_p1 + 54, "Hiệu suất tính toán cao (Compute-bound)", size=6.6, fill="#065F46", anchor="middle")

    # High-speed TCM bus
    arrow(f, x_b + 180, y_p1 + 46, x_b + 230, y_p1 + 46, color=GREEN, sw=THICK)
    f.text(x_b + 205, y_p1 + 34, "TCM Hit 100%", size=6.6, weight=700, fill=GREEN, anchor="middle")

    rect(f, x_b + 236, y_p1 + 22, 158, 48, fill="#F0FDF4", stroke="#22C55E", sw=0.9, rx=3)
    f.text(x_b + 315, y_p1 + 38, "TCM On-Chip (1 MiB SRAM)", size=7.0, weight=700, fill="#15803D", anchor="middle")
    f.text(x_b + 315, y_p1 + 54, "Layer Fusion giữ trọn activation", size=6.6, fill="#166534", anchor="middle")

    # Takeaway Box
    rect(f, x_b + 8, y_tk1, w_b - 16, 84, fill="#F0FDF4", stroke="#22C55E", sw=0.8, rx=4)
    f.text(x_b + 14, y_tk1 + 12, "Bài học Cốt lõi cho Kiến trúc Suy luận Biên [T2 BAMB tr.9]:", size=7.0, weight=700, fill="#15803D")
    f.text(x_b + 14, y_tk1 + 28, "• Đồng thiết kế HW/SW thông minh, không phải raw TOPS, quyết định hiệu năng biên thực tế", size=6.6, weight=700, fill="#15803D")
    f.text(x_b + 14, y_tk1 + 44, "• Tích hợp SRAM on-chip vừa vặn kết hợp CP tiling/fusion loại bỏ 90% truy cập DRAM", size=6.6, fill="#166534")
    f.text(x_b + 14, y_tk1 + 60, "• Tiết kiệm năng lượng và chi phí silicon mà vẫn đạt tốc độ suy luận vượt trội", size=6.6, fill="#166534")
    f.text(x_b + 14, y_tk1 + 74, "• Độ trễ MobileNetV3 chỉ 0.8 ms (vượt trội so với 2.0 ms của NPU 11 TOPS không co-design)", size=6.6, fill="#166534")

    # Dòng nguồn đáy trang
    source(f, card_y + card_h + 10, "Nguồn: T2 BAMB tr.1, tr.8-9 (Bamberg et al., IEEE 2025: Real-world effective TOPS vs advertised peak TOPS on production MPUs).")

    return f


def main():
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("ir-01-three-tier-lowering", fig_three_tier_lowering),
        ("fus-01-unfused-vs-fused", fig_unfused_vs_fused),
        ("fus-02-constant-folding-and-op-fusion", fig_constant_folding_and_op_fusion),
        ("cmp-01-tiling-spatial-halo", fig_tiling_spatial_halo),
        ("tvm-01-optimization-and-autotvm", fig_tvm_optimization_and_autotvm),
        ("neu-01-hw-sw-codesign", fig_eiq_neutron_hw_sw_codesign),
        ("neu-02-effective-vs-peak-tops", fig_eiq_neutron_effective_vs_peak_tops),
    ]
    run(figures, DEFAULT_OUTDIR)


if __name__ == "__main__":
    main()
