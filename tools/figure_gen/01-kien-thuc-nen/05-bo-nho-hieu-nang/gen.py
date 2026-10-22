#!/usr/bin/env python3
"""Chuyên đề: Bộ nhớ và hiệu năng (05-bo-nho-hieu-nang).

Sinh các hình vector SVG minh họa:
  1. prf-01-latency-breakdown-pipeline:
     Bóc tách 4 chặng độ trễ T_E2E (Pre -> Load -> NPU -> Post) và đối chiếu dòng thời gian Tuần tự vs Đường ống (Pipelining).
  2. prf-02-roofline-model:
     Mô hình Roofline xác định giới hạn hiệu năng: Vùng dốc nghẽn bộ nhớ (Memory-bound) và Vùng trần nghẽn tính toán (Compute-bound).
  3. mem-01-inplace-depthwise:
     Kỹ thuật In-place Depthwise Convolution: Tiết kiệm bộ nhớ đỉnh (Peak SRAM) từ 2N xuống N+1.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# docs/tools/figure_gen/01-kien-thuc-nen/05-bo-nho-hieu-nang -> ../.. = docs/tools/figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "05-bo-nho-hieu-nang"
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


def circle(f, cx, cy, r, fill="white", stroke=BOX_STROKE, sw=1.2, dashed=False):
    dash = ' stroke-dasharray="3 2"' if dashed else ""
    f.a(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN, dashed=False):
    if color not in (BLUE, GREEN, RED, GRAY, INK):
        color = INK
    f.line([(x1, y1), (x2, y2)], color, width=sw, dashed=dashed, head=True)


# ==============================================================================
# 1. HÌNH BÓC TÁCH 4 CHẶNG ĐỘ TRỄ VÀ ĐƯỜNG ỐNG PIPELINE (prf-01-latency-breakdown-pipeline)
# ==============================================================================
def fig_latency_breakdown_pipeline():
    H = 472
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Bóc tách 4 chặng độ trễ trọn gói (End-to-End) và trục thời gian Tuần tự vs Đường ống đa luồng", size=13.5, weight=700, fill=DARK)

    # Khung 4 chặng nối tiếp ở trên (y=42, h=118)
    rect(f, 18, 42, W - 36, 120, fill="#F8FAFC", stroke=BLUE, sw=1.3, rx=5)
    f.text(28, 58, "CẤU TRÚC 4 CHẶNG ĐỘ TRỄ: T_E2E = T_pre + T_load + T_npu + T_post", size=10.5, weight=700, fill=DARK)

    stages = [
        ("1. Tiền xử lý (T_pre)", "Camera, Giải mã JPEG, BGR->RGB", "Resize, Letterbox đệm viền, Float", BLUE, "#EFF6FF", 28, 186),
        ("2. Nạp dữ liệu (T_load)", "Sao chép bộ nhớ / Memory copy", "Zero-copy dma-buf tiệm cận ~0 ms", ORANGE, "#FFFBEB", 234, 186),
        ("3. Suy luận NPU (T_npu)", "Mảng systolic parallel PE chạy", "Conv, MatMul, Activation, Pooling", GREEN, "#F0FDF4", 440, 206),
        ("4. Hậu xử lý (T_post)", "Trích xuất tensor, khôi phục tọa độ", "Lọc Score thresholding, chạy NMS CPU", PURPLE, "#FAF5FF", 666, 186),
    ]

    for title, sub1, sub2, color, bg, sx, sw in stages:
        rect(f, sx, 72, sw, 76, fill=bg, stroke=color, sw=1.2, rx=4)
        f.text(sx + sw / 2, 88, title, size=10, weight=700, fill=color, anchor="middle")
        f.text(sx + sw / 2, 108, sub1, size=8.5, fill=DARK, anchor="middle")
        f.text(sx + sw / 2, 126, sub2, size=8.5, fill=GRAY, anchor="middle")
        if sx + sw < W - 50:
            arrow(f, sx + sw + 2, 110, sx + sw + 18, 110, color=DARK, sw=THIN)

    # So sánh trục thời gian tuần tự vs đường ống (y=176, h=262)
    col_w = 412
    x1 = 18
    x2 = 450

    # Panel Trái: Tuần tự (NPU bị bỏ rảnh nhiều)
    rect(f, x1, 176, col_w, 262, fill="#FFF9F9", stroke=RED, sw=1.3, rx=5)
    rect(f, x1 + 10, 186, 175, 22, fill=RED, stroke=RED, sw=1, rx=3)
    f.text(x1 + 97, 197, "THỰC THI TUẦN TỰ (Sequential)", size=9.8, weight=700, fill="white", anchor="middle")
    f.text(x1 + 195, 197, "1 Luồng CPU - NPU bị bỏ rảnh (Idle)", size=9.2, weight=700, fill=RED)

    # Frame 1 timeline
    y_tl1 = 222
    f.text(x1 + 16, y_tl1 + 12, "Frame 1:", size=9, weight=700, fill=DARK)
    rect(f, x1 + 65, y_tl1, 75, 24, fill="#EFF6FF", stroke=BLUE, sw=1, rx=2)
    f.text(x1 + 102, y_tl1 + 12, "T_pre (12ms)", size=8.2, fill=BLUE, anchor="middle")

    rect(f, x1 + 143, y_tl1, 105, 24, fill="#F0FDF4", stroke=GREEN, sw=1, rx=2)
    f.text(x1 + 195, y_tl1 + 12, "T_npu (18ms)", size=8.2, weight=700, fill=GREEN, anchor="middle")

    rect(f, x1 + 251, y_tl1, 85, 24, fill="#FAF5FF", stroke=PURPLE, sw=1, rx=2)
    f.text(x1 + 293, y_tl1 + 12, "T_post (15ms)", size=8.2, fill=PURPLE, anchor="middle")

    # Frame 2 timeline
    y_tl2 = 254
    f.text(x1 + 16, y_tl2 + 12, "Frame 2:", size=9, weight=700, fill=DARK)
    rect(f, x1 + 65, y_tl2, 271, 24, fill="#F8FAFC", stroke=GRID, sw=1, dashed=True, rx=2)
    f.text(x1 + 200, y_tl2 + 12, "Chờ tuần tự đến lượt... (NPU hoàn toàn Idle)", size=8.5, fill=GRAY, anchor="middle")

    rect(f, x1 + 339, y_tl2, 60, 24, fill="#EFF6FF", stroke=BLUE, sw=1, rx=2)
    f.text(x1 + 369, y_tl2 + 12, "T_pre", size=8.2, fill=BLUE, anchor="middle")

    # Đánh giá tuần tự
    rect(f, x1 + 15, 292, col_w - 30, 136, fill="white", stroke=GRID, sw=1, rx=4)
    f.text(x1 + 25, 308, "Đặc tính luồng tuần tự đơn giản:", size=9.5, weight=700, fill=DARK)
    f.text(x1 + 35, 328, "• Tổng độ trễ 1 khung hình: T_E2E = 12 + 18 + 15 = 45 ms", size=8.8, fill=INK)
    f.text(x1 + 35, 348, "• Thông lượng tối đa: 1000 / 45 ≈ 22.2 FPS", size=8.8, fill=INK)
    f.text(x1 + 35, 368, "• Tỷ lệ NPU bận: 18 / 45 = 40.0% (Lãng phí 60% năng lực NPU)", size=8.8, weight=700, fill=RED)
    f.text(x1 + 35, 388, "• NPU bị nghẽn chờ CPU hoàn tất Pre/Post-processing", size=8.8, fill=DARK)
    f.text(x1 + 35, 408, "• Không khai thác được năng lực đa lõi của SoC", size=8.2, fill=GRAY)

    # Panel Phải: Đường ống Pipeline (Gối đầu đa luồng)
    rect(f, x2, 176, col_w, 262, fill="#F6FBF7", stroke=GREEN, sw=1.3, rx=5)
    rect(f, x2 + 10, 186, 185, 22, fill=GREEN, stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 102, 197, "ĐƯỜNG ỐNG ĐA LUỒNG (Pipelined)", size=9.8, weight=700, fill="white", anchor="middle")
    f.text(x2 + 205, 197, "Gối đầu CPU & NPU song song", size=9.2, weight=700, fill=GREEN)

    # 3 Luồng song song theo thời gian
    y_pl1 = 220
    f.text(x2 + 16, y_pl1 + 12, "Luồng 1 (Pre):", size=8.5, weight=700, fill=BLUE)
    rect(f, x2 + 95, y_pl1, 80, 22, fill="#EFF6FF", stroke=BLUE, sw=1, rx=2)
    f.text(x2 + 135, y_pl1 + 11, "Pre F1 (12m)", size=8.2, fill=BLUE, anchor="middle")
    rect(f, x2 + 178, y_pl1, 80, 22, fill="#EFF6FF", stroke=BLUE, sw=1, rx=2)
    f.text(x2 + 218, y_pl1 + 11, "Pre F2 (12m)", size=8.2, fill=BLUE, anchor="middle")
    rect(f, x2 + 261, y_pl1, 80, 22, fill="#EFF6FF", stroke=BLUE, sw=1, rx=2)
    f.text(x2 + 301, y_pl1 + 11, "Pre F3 (12m)", size=8.2, fill=BLUE, anchor="middle")

    y_pl2 = 246
    f.text(x2 + 16, y_pl2 + 12, "Luồng 2 (NPU):", size=8.5, weight=700, fill=GREEN)
    rect(f, x2 + 178, y_pl2, 100, 22, fill="#F0FDF4", stroke=GREEN, sw=1.3, rx=2)
    f.text(x2 + 228, y_pl2 + 11, "NPU F1 (18ms)", size=8.2, weight=700, fill=GREEN, anchor="middle")
    rect(f, x2 + 281, y_pl2, 100, 22, fill="#F0FDF4", stroke=GREEN, sw=1.3, rx=2)
    f.text(x2 + 331, y_pl2 + 11, "NPU F2 (18ms)", size=8.2, weight=700, fill=GREEN, anchor="middle")

    y_pl3 = 272
    f.text(x2 + 16, y_pl3 + 12, "Luồng 3 (Post):", size=8.5, weight=700, fill=PURPLE)
    rect(f, x2 + 281, y_pl3, 90, 22, fill="#FAF5FF", stroke=PURPLE, sw=1, rx=2)
    f.text(x2 + 326, y_pl3 + 11, "Post F1 (15m)", size=8.2, fill=PURPLE, anchor="middle")

    # Đánh giá đường ống
    rect(f, x2 + 15, 302, col_w - 30, 126, fill="white", stroke=GRID, sw=1, rx=4)
    f.text(x2 + 25, 318, "Đặc tính kiến trúc đường ống gối đầu:", size=9.5, weight=700, fill=DARK)
    f.text(x2 + 35, 336, "• Thông lượng bị chặn bởi chặng dài nhất: max(12, 18, 15) = 18 ms", size=8.8, fill=INK)
    f.text(x2 + 35, 354, "• Thông lượng ổn định: 1000 / 18 ≈ 55.6 FPS (Tăng 2.5× thông lượng)", size=8.8, weight=700, fill=GREEN)
    f.text(x2 + 35, 372, "• Tỷ lệ NPU bận: tiệm cận ~100% công suất thực tế", size=8.8, weight=700, fill=GREEN)
    f.text(x2 + 35, 390, "• Độ trễ 1 frame (E2E) giữ nguyên 45 ms, nhưng mỗi 18 ms xuất 1 kết quả", size=8.5, fill=DARK)
    f.text(x2 + 35, 408, "• Đòi hỏi hàng đợi buffer trung gian (Thread Queues) giữa các chặng", size=8.2, fill=GRAY)

    source(f, H - 24, "Nguồn: Jouppi et al. (TPU 2017 tr.1, tr.8), Chen et al. (Eyeriss 2016 tr.8)")
    return f


# ==============================================================================
# 2. HÌNH MÔ HÌNH ROOFLINE: COMPUTE-BOUND VS MEMORY-BOUND (prf-02-roofline-model)
# ==============================================================================
def fig_roofline_model():
    H = 460
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Mô hình Roofline: Xác định giới hạn hiệu năng theo Băng thông bộ nhớ và Năng lực tính toán mảng MAC", size=13.5, weight=700, fill=DARK)

    # Khung biểu đồ Roofline (Bên trái: x=18, w=480, h=390)
    gx = 55
    gy = 80
    gw = 425
    gh = 230

    rect(f, 18, 42, 480, 390, fill="#F8FAFC", stroke=BLUE, sw=1.3, rx=5)
    f.text(28, 58, "BIỂU ĐỒ ROOFLINE: P_attainable = min(P_peak, BW × I)", size=10.5, weight=700, fill=DARK)

    # Slanted memory boundary: from (gx, gy + gh) to (gx + 180, gy + 30)
    # Ridge point: x_ridge = gx + 180 = 235, y_ridge = gy + 30 = 110
    # Compute boundary: horizontal line from (235, 110) to (gx + gw, 110)

    # Vùng Memory-bound (Trái, màu cam nhạt)
    f.a(f'<polygon points="{gx},{gy+gh} 235,110 235,{gy+gh}" fill="#FFFBEB" opacity="0.8"/>')
    # Vùng Compute-bound (Phải, màu xanh nhạt)
    f.a(f'<polygon points="235,110 {gx+gw},110 {gx+gw},{gy+gh} 235,{gy+gh}" fill="#F0FDF4" opacity="0.8"/>')

    # Trục tọa độ
    f.line([(gx, gy + gh), (gx + gw + 10, gy + gh)], DARK, width=1.8, head=True)  # Trục X
    f.line([(gx, gy + gh), (gx, gy + 10)], DARK, width=1.8, head=True)  # Trục Y

    f.text(gx + 8, gy + 15, "Hiệu năng P (TOPS, log)", size=8.5, weight=700, fill=DARK)
    f.text(gx + gw + 5, gy + gh + 14, "Cường độ I (FLOPs/Byte, log)", size=8.5, weight=700, fill=DARK, anchor="end")

    # Đường Roofline đậm
    # Đường dốc (Slanted Memory Bound)
    f.line([(gx, gy + gh), (235, 110)], RED, width=3.0)
    # Đường trần (Flat Compute Plateau)
    f.line([(235, 110), (gx + gw, 110)], GREEN, width=3.0)

    # Điểm Ridge Point
    circle(f, 235, 110, 5, fill=ORANGE, stroke=DARK, sw=1.5)
    f.text(235, 96, "Ridge Point (I_ridge = P_peak / BW)", size=8.5, weight=700, fill=ORANGE, anchor="middle")
    f.line([(235, 115), (235, gy + gh)], ORANGE, width=1.2, dashed=True)
    f.text(235, gy + gh + 14, "I_ridge", size=8.5, weight=700, fill=ORANGE, anchor="middle")

    # Nhãn trần P_peak và dốc BW
    f.text(gx + gw - 10, 96, "Trần tính toán: P_peak", size=9, weight=700, fill=GREEN, anchor="end")
    f.text(68, 138, "Độ dốc = Băng thông DRAM (BW)", size=8.2, weight=700, fill=RED)

    # Các điểm toán tử thực tế (Nằm chính xác trên đường biên Roofline)
    # 1. Depthwise Conv (Memory-bound, x=135, y=221)
    circle(f, 135, 221, 4.5, fill=RED, stroke=DARK, sw=1.2)
    f.text(145, 225, "Depthwise Conv (I thấp)", size=8.2, weight=700, fill=RED)

    # 2. Injective op (ReLU, Add, x=90, y=271)
    circle(f, 90, 271, 4.5, fill=RED, stroke=DARK, sw=1.2)
    f.text(100, 275, "ReLU / Add / Norm", size=8, fill=DARK)

    # 3. Standard Dense Conv 3x3 (Compute-bound, x=310, y=110)
    circle(f, 310, 110, 4.5, fill=GREEN, stroke=DARK, sw=1.2)
    f.text(310, 128, "Dense Conv 3×3 (I cao)", size=8.2, weight=700, fill=GREEN, anchor="middle")

    # 4. GEMM / Fully-Connected (x=410, y=110)
    circle(f, 410, 110, 4.5, fill=GREEN, stroke=DARK, sw=1.2)
    f.text(410, 128, "GEMM lớn", size=8.2, fill=DARK, anchor="middle")

    # Nhãn phân vùng lớn trên biểu đồ
    f.text(150, gy + gh - 18, "VÙNG NGHẼN BỘ NHỚ", size=9.2, weight=700, fill=RED, anchor="middle")
    f.text(150, gy + gh - 6, "(Memory-Bound)", size=8, fill=RED, anchor="middle")

    f.text(350, gy + gh - 18, "VÙNG NGHẼN TÍNH TOÁN", size=9.2, weight=700, fill=GREEN, anchor="middle")
    f.text(350, gy + gh - 6, "(Compute-Bound)", size=8, fill=GREEN, anchor="middle")

    # Chú thích tóm tắt dưới biểu đồ Panel trái
    rect(f, 28, 342, 460, 78, fill="white", stroke=GRID, sw=1, rx=3)
    f.text(38, 356, "Quy luật ứng dụng mô hình Roofline:", size=9.2, weight=700, fill=DARK)
    f.text(48, 374, "• Nếu I < I_ridge: Lớp mạng bị đói dữ liệu; tăng xung nhịp NPU KHÔNG giảm độ trễ", size=8.5, fill=RED)
    f.text(48, 392, "• Nếu I >= I_ridge: Mảng MAC bão hòa công suất; tối ưu băng thông DDR vô tác dụng", size=8.5, fill=GREEN)
    f.text(48, 410, "• Năng lượng truy cập DRAM gấp ~200× phép tính MAC on-chip (Chen 2016)", size=8.2, fill=GRAY)

    # Panel Phải: Chiến lược Tối ưu hóa theo 2 vùng (x=508, w=354, h=390)
    col_w2 = 354
    x2 = 508
    rect(f, x2, 42, col_w2, 390, fill="#F8FAFC", stroke=GREEN, sw=1.3, rx=5)
    f.text(x2 + 12, 58, "HỆ QUẢ VÀ CHIẾN LƯỢC TỐI ƯU HÓA", size=10.5, weight=700, fill=DARK)

    # Khung Memory-bound strategy
    rect(f, x2 + 12, 72, col_w2 - 24, 154, fill="#FFF9F9", stroke=RED, sw=1.2, rx=4)
    rect(f, x2 + 20, 80, 175, 20, fill=RED, stroke=RED, sw=1, rx=3)
    f.text(x2 + 107, 90, "CHIẾN LƯỢC KHI MEMORY-BOUND", size=8.8, weight=700, fill="white", anchor="middle")

    mem_opts = [
        "1. Gộp toán tử (Operator Fusion):",
        "   Gộp Conv+BN+ReLU triệt tiêu đọc/ghi trung gian ra DRAM",
        "2. Tăng kích thước Tile (Tiling Optimization):",
        "   Khai thác tối đa dung lượng SRAM để giảm chi phí biên Halo",
        "3. Chuyển đổi sang cấu trúc tái sử dụng cao:",
        "   Dùng Inverted Bottleneck hoặc nhóm kênh (Grouped Conv)",
        "4. Nâng cấp kênh nhớ: Chạy LPDDR5 4 kênh (Quad-channel)",
    ]
    for i, line in enumerate(mem_opts):
        f.text(x2 + 22, 114 + i * 16, line, size=8.2, fill=DARK)

    # Khung Compute-bound strategy
    rect(f, x2 + 12, 234, col_w2 - 24, 146, fill="#F6FBF7", stroke=GREEN, sw=1.2, rx=4)
    rect(f, x2 + 20, 242, 185, 20, fill=GREEN, stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 112, 252, "CHIẾN LƯỢC KHI COMPUTE-BOUND", size=8.8, weight=700, fill="white", anchor="middle")

    comp_opts = [
        "1. Lượng tử hóa độ chính xác thấp (Quantization):",
        "   Chuyển FP16 sang INT8 tăng gấp 2× đến 4× thông lượng PE",
        "2. Cắt tỉa mô hình (Channel Pruning / Sparsity):",
        "   Loại bỏ các kênh trọng số gần 0 để giảm tổng phép tính MAC",
        "3. Tái tham số hóa (Structural Re-parameterization):",
        "   Huấn luyện đa nhánh, suy luận thu về 1 nhánh duy nhất",
        "4. Tăng tần số xung nhịp NPU (Khóa mức xung cao nhất)",
    ]
    for i, line in enumerate(comp_opts):
        f.text(x2 + 22, 274 + i * 16, line, size=8.2, fill=DARK)

    rect(f, x2 + 12, 388, col_w2 - 24, 34, fill="white", stroke=GRID, sw=1, rx=3)
    f.text(x2 + col_w2 / 2, 399, "Mục tiêu tối ưu: Đẩy toán tử tiến gần Ridge Point", size=8.8, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + col_w2 / 2, 412, "Khai thác tối đa mảng tính toán mà không bị nghẽn bus bộ nhớ", size=8.2, fill=GRAY, anchor="middle")

    source(f, H - 24, "Nguồn: Jouppi et al. (TPU 2017 tr.5), Chen et al. (Eyeriss 2016 tr.8)")
    return f


# ==============================================================================
# 3. HÌNH IN-PLACE DEPTHWISE CONVOLUTION (mem-01-inplace-depthwise)
# ==============================================================================
def fig_inplace_depthwise():
    H = 435
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Kỹ thuật In-place Depthwise Convolution: Cắt giảm bộ nhớ đỉnh từ 2N xuống N+1 (MCUNet)", size=13.5, weight=700, fill=DARK)

    # Cột trái: Phương pháp thông thường (Không In-place)
    w_col = 405
    col_h = 235
    rect(f, 20, 52, w_col, col_h, fill="#F8FAFC", stroke="#0284C7", sw=1.3, rx=5)
    rect(f, 20, 52, w_col, 32, fill="#E0F2FE", stroke="#0284C7", sw=1.0, rx=5)
    f.text(20 + w_col // 2, 72, "(a) Depthwise truyền thống: Bộ nhớ đỉnh = 2N", size=10.5, weight=700, fill="#0369A1", anchor="middle")

    # Input Buffer N lát (xếp cạnh nhau, không đè)
    rect(f, 35, 96, 160, 92, fill="#FFFFFF", stroke="#0284C7", sw=1.1)
    f.text(115, 112, "Input Buffer (N lát)", size=9, weight=700, fill="#0369A1", anchor="middle")
    for i in range(4):
        rect(f, 45 + i * 36, 122, 32, 54, fill="#E0F2FE", stroke="#0284C7", sw=1.0)
        f.text(45 + i * 36 + 16, 152, f"In_{i}", size=8, fill="#0369A1", anchor="middle")

    # Output Buffer N lát
    rect(f, 250, 96, 160, 92, fill="#FFFFFF", stroke="#E65100", sw=1.1)
    f.text(330, 112, "Output Buffer (N lát)", size=9, weight=700, fill="#E65100", anchor="middle")
    for i in range(4):
        rect(f, 260 + i * 36, 122, 32, 54, fill="#FFF3E0", stroke="#E65100", sw=1.0)
        f.text(260 + i * 36 + 16, 152, f"Out_{i}", size=8, fill="#E65100", anchor="middle")

    # Mũi tên tính toán giữa 2 buffer
    arrow(f, 195, 149, 250, 149, INK, THICK)
    f.text(222, 140, "DW Conv", size=8, weight=700, fill="#0F172A", anchor="middle")

    # Thanh đo bộ nhớ đỉnh truyền thống
    rect(f, 35, 196, 375, 24, fill="#FEE2E2", stroke="#EF4444", sw=1.1)
    f.text(222, 212, "Bộ nhớ đỉnh (Peak SRAM) = In (N) + Out (N) = 2N lát", size=9, weight=700, fill="#B91C1C", anchor="middle")

    f.text(32, 233, "- Cả hai tensor In và Out phải tồn tại đồng thời trong SRAM.", size=8.5, fill="#1E293B")
    f.text(32, 247, "- Lãng phí lớn tại các lớp Depthwise ở tầng đầu (H, W lớn).", size=8.5, fill="#1E293B")
    f.text(32, 261, "- Dễ gây tràn bộ nhớ trên vi điều khiển hoặc NPU có SRAM nhỏ.", size=8.5, fill="#1E293B")
    f.text(32, 275, "- Thường là nút thắt bộ nhớ chính trong MobileNetV2 [T2 MCU tr.6].", size=8.5, fill="#475569")

    # Cột phải: In-place Depthwise (TinyEngine)
    x_r = 455
    rect(f, x_r, 52, w_col, col_h, fill="#F8FAFC", stroke="#059669", sw=1.3, rx=5)
    rect(f, x_r, 52, w_col, 32, fill="#D1FAE5", stroke="#059669", sw=1.0, rx=5)
    f.text(x_r + w_col // 2, 72, "(b) In-place Depthwise (TinyEngine): Bộ nhớ đỉnh = N + 1", size=10.5, weight=700, fill="#065F46", anchor="middle")

    # Shared Memory Buffer N lát
    rect(f, x_r + 16, 96, 216, 92, fill="#FFFFFF", stroke="#059669", sw=1.1)
    f.text(x_r + 124, 112, "Shared Buffer (N lát kênh)", size=9, weight=700, fill="#065F46", anchor="middle")

    # 4 slices: slice 0 đã ghi đè (xanh), slice 1 đang tính (vàng), slice 2-3 chờ (xanh dương)
    rect(f, x_r + 26, 122, 44, 54, fill="#D1FAE5", stroke="#059669", sw=1.1)
    f.text(x_r + 48, 146, "Out_0", size=8.5, weight=700, fill="#065F46", anchor="middle")
    f.text(x_r + 48, 160, "(đã đè)", size=7, fill="#047857", anchor="middle")

    rect(f, x_r + 76, 122, 44, 54, fill="#FEF3C7", stroke="#D97706", sw=1.2)
    f.text(x_r + 98, 146, "In_1", size=8.5, weight=700, fill="#B45309", anchor="middle")
    f.text(x_r + 98, 160, "(đang tính)", size=7, fill="#78350F", anchor="middle")

    rect(f, x_r + 126, 122, 44, 54, fill="#E0F2FE", stroke="#0284C7", sw=1.0)
    f.text(x_r + 148, 146, "In_2", size=8.5, fill="#0369A1", anchor="middle")
    f.text(x_r + 148, 160, "(chờ)", size=7, fill="#0284C7", anchor="middle")

    rect(f, x_r + 176, 122, 44, 54, fill="#E0F2FE", stroke="#0284C7", sw=1.0)
    f.text(x_r + 198, 146, "In_3", size=8.5, fill="#0369A1", anchor="middle")
    f.text(x_r + 198, 160, "(chờ)", size=7, fill="#0284C7", anchor="middle")

    # Aux Slice Buffer (1 lát)
    rect(f, x_r + 288, 102, 102, 80, fill="#EDE7F6", stroke="#7C3AED", sw=1.2, rx=4)
    f.text(x_r + 339, 122, "Aux Buffer (1 lát)", size=9, weight=700, fill="#6D28D9", anchor="middle")
    f.text(x_r + 339, 138, "1 x H x W đệm tạm", size=8, fill="#5B21B6", anchor="middle")
    f.text(x_r + 339, 154, "Chứa Out_1 tạm", size=8, fill="#4527A0", anchor="middle")

    # Mũi tên trực tiếp giữa Shared Buffer và Aux Buffer
    arrow(f, x_r + 232, 130, x_r + 288, 130, BLUE, THICK)
    f.text(x_r + 260, 118, "Tính K_1", size=7.5, fill="#0369A1", anchor="middle")

    arrow(f, x_r + 288, 160, x_r + 232, 160, GREEN, THICK)
    f.text(x_r + 260, 174, "Ghi đè In_1", size=7.5, fill="#059669", anchor="middle")

    # Thanh đo bộ nhớ đỉnh TinyEngine
    rect(f, x_r + 16, 196, 375, 24, fill="#DCFCE7", stroke="#16A34A", sw=1.1)
    f.text(x_r + 203, 212, "Bộ nhớ đỉnh (Peak SRAM) = Shared (N) + Aux (1) = N + 1 lát", size=9, weight=700, fill="#15803D", anchor="middle")

    f.text(x_r + 15, 233, "- Mỗi kênh c của Depthwise chỉ phụ thuộc duy nhất vào kênh c đầu vào.", size=8.5, fill="#1E293B")
    f.text(x_r + 15, 247, "- Tính xong kênh c, In_c hết hạn -> Ghi đè Out_c vào chính ô In_c.", size=8.5, fill="#1E293B")
    f.text(x_r + 15, 261, "- Tiết kiệm (N-1)/2N ≈ 50% dung lượng SRAM tại các lớp Depthwise [T2 MCU tr.6].", size=8.5, fill="#15803D")
    f.text(x_r + 15, 275, "- Hoàn toàn bảo toàn độ chính xác toán học (Exact mathematical equivalence).", size=8.5, fill="#475569")

    # 4. Hộp kết luận so sánh dưới cùng
    rect(f, 20, 298, 840, 46, fill="#F8FAFC", stroke="#64748B", sw=1.1, rx=4)
    f.text(32, 315, "So sánh bộ nhớ đỉnh kích hoạt (Peak Working Memory) giữa các kiến trúc:", size=10, weight=700, fill="#0F172A")
    f.text(32, 331, "Conv chuẩn (2N) > Depthwise chuẩn (2N) > In-place Depthwise (N+1). Khi N=192 kênh, bộ nhớ đỉnh giảm từ 384 lát xuống 193 lát [T2 MCU tr.6].", size=8.8, fill="#1E293B")

    y_src = 354
    source(f, y_src, "[T2 Lin 2020 MCUNet tr.6] [T2 Paissan 2021 PhiNets tr.6, tr.8]")
    f.h = y_src + 22
    return f


def main():
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("prf-01-latency-breakdown-pipeline", fig_latency_breakdown_pipeline),
        ("prf-02-roofline-model", fig_roofline_model),
        ("mem-01-inplace-depthwise", fig_inplace_depthwise),
    ]
    run(figures, DEFAULT_OUTDIR)


if __name__ == "__main__":
    main()
