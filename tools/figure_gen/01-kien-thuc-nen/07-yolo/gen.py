#!/usr/bin/env python3
"""Chuyên đề: Kiến trúc YOLO và Biến đổi đồ thị suy luận (07-yolo).

Sinh 3 hình vector SVG minh họa:
  1. yolo-01-c2f-vs-c3k2:
     So sánh cấu trúc dòng truyền đặc trưng giữa khối C2f (YOLOv8) và C3k2 (YOLO26).
  2. yolo-02-head-dfl-vs-nms-free:
     Đối chiếu đầu dự đoán Decoupled Head: YOLOv8 có DFL (reg_max=16, cần NMS) vs YOLO26 NMS-free (reg_max=1).
  3. yolo-03-train-to-infer-pipeline:
     Biến đổi toàn diện từ Training Graph (Dual heads, BatchNorm động, Loss) sang Inference Graph (Single head, Conv-BN fuse).

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# docs/tools/figure_gen/01-kien-thuc-nen/07-yolo -> ../.. = docs/tools/figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "07-yolo"
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
# 1. HÌNH SO SÁNH KHỐI C2F VÀ C3K2 (yolo-01-c2f-vs-c3k2)
# ==============================================================================
def fig_c2f_vs_c3k2():
    H = 465
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "So sánh kiến trúc khối trích xuất đặc trưng: C2f (YOLOv8) vs C3k2 (YOLO26)", size=13.5, weight=700, fill=DARK)

    col_w = 412
    x1 = 18
    x2 = 450

    # Panel Trái: Khối C2f trong YOLOv8
    rect(f, x1, 40, col_w, 395, fill="#F8FAFC", stroke=BLUE, sw=1.3, rx=5)
    rect(f, x1 + 10, 50, 150, 22, fill=BLUE, stroke=BLUE, sw=1, rx=3)
    f.text(x1 + 85, 61, "KHỐI C2F (YOLOv8)", size=10, weight=700, fill="white", anchor="middle")
    f.text(x1 + 170, 61, "Cross Stage Partial + All-Taps Concat", size=9.5, weight=700, fill=BLUE)

    # Input tensor
    rect(f, x1 + 116, 78, 180, 26, fill="white", stroke=BOX_STROKE, sw=1, rx=3)
    f.text(x1 + col_w / 2, 91, "Input: Tensor (Cin, H, W)", size=9, weight=700, fill=DARK, anchor="middle")

    arrow(f, x1 + col_w / 2, 104, x1 + col_w / 2, 118, color=BLUE, sw=THIN)

    # cv1: Conv 1x1 -> 2*Cout
    rect(f, x1 + 96, 118, 220, 28, fill="#EFF6FF", stroke=BLUE, sw=1.2, rx=3)
    f.text(x1 + col_w / 2, 132, "cv1: Conv 1×1 (Cin -> 2×Cout)", size=9.5, weight=700, fill=BLUE, anchor="middle")

    arrow(f, x1 + col_w / 2, 146, x1 + col_w / 2, 162, color=BLUE, sw=THIN)

    # Phép Split (Chia đôi kênh)
    rect(f, x1 + 126, 162, 160, 24, fill="#FEF3C7", stroke=ORANGE, sw=1, rx=2)
    f.text(x1 + col_w / 2, 174, "Split thành 2 nửa: y0, y1", size=8.8, weight=700, fill=ORANGE, anchor="middle")

    # Nhánh 1: Đường tắt y0 (Bypass) bên trái (Manhattan orthogonal 100%, có nhãn trên đường dẫn)
    f.line([(x1 + 150, 186), (x1 + 150, 198), (x1 + 52, 198), (x1 + 52, 319), (x1 + 76, 319)], color=ORANGE, width=THICK, head=True)
    f.text(x1 + 100, 190, "y0 (Bypass)", size=8, weight=700, fill=ORANGE, anchor="middle")

    # Nhánh 2: Chuỗi n Bottlenecks bên phải
    arrow(f, x1 + 250, 186, x1 + 250, 202, color=BLUE, sw=THIN)
    rect(f, x1 + 170, 202, 160, 34, fill="white", stroke=BOX_STROKE, sw=1.2, rx=3)
    f.text(x1 + 250, 214, "Bottleneck 1 (3×3 Conv)", size=8.8, weight=700, fill=DARK, anchor="middle")
    f.text(x1 + 250, 228, "Conv 3×3 + BN + SiLU", size=7.8, fill=GRAY, anchor="middle")

    # Tap b1 từ Bottleneck 1 đi vòng sang phải vào Concat
    f.line([(x1 + 330, 219), (x1 + 356, 219), (x1 + 356, 319), (x1 + 336, 319)], color=BLUE, width=THIN, head=True)
    f.text(x1 + 356, 212, "b1 (Tap)", size=7.5, weight=700, fill=BLUE, anchor="middle")

    arrow(f, x1 + 250, 236, x1 + 250, 252, color=BLUE, sw=THIN)
    rect(f, x1 + 170, 252, 160, 34, fill="white", stroke=BOX_STROKE, sw=1.2, rx=3)
    f.text(x1 + 250, 264, "Bottleneck n (3×3 Conv)", size=8.8, weight=700, fill=DARK, anchor="middle")
    f.text(x1 + 250, 278, "Đường tắt residual nội bộ", size=7.8, fill=GRAY, anchor="middle")

    # Nhánh gom Concat (Thẳng đứng từ Bottlenecks)
    arrow(f, x1 + 250, 286, x1 + 250, 306, color=BLUE, sw=THIN)

    rect(f, x1 + 76, 306, 260, 26, fill="#FEF3C7", stroke=ORANGE, sw=1, rx=3)
    f.text(x1 + col_w / 2, 319, "Concat (y0, y1, b1, ..., bn)", size=9.2, weight=700, fill=ORANGE, anchor="middle")

    arrow(f, x1 + col_w / 2, 332, x1 + col_w / 2, 346, color=BLUE, sw=THIN)

    # cv2: Conv 1x1 -> Cout
    rect(f, x1 + 96, 346, 220, 26, fill="#EFF6FF", stroke=BLUE, sw=1.2, rx=3)
    f.text(x1 + col_w / 2, 359, "cv2: Conv 1×1 ((2+n)×Cout -> Cout)", size=9, weight=700, fill=BLUE, anchor="middle")

    # Đánh giá Panel 1
    rect(f, x1 + 15, 380, col_w - 30, 46, fill="white", stroke=GRID, sw=1, rx=3)
    f.text(x1 + 25, 394, "Đặc tính C2f: Giữ gradient phong phú qua Concat đa tầng.", size=8.5, weight=700, fill=DARK)
    f.text(x1 + 25, 410, "Nhược điểm: Bắt buộc đệm (2+n) tensor trung gian, tốn SRAM.", size=8.2, fill=GRAY)

    # Panel Phải: Khối C3k2 trong YOLO26
    rect(f, x2, 40, col_w, 395, fill="#F6FBF7", stroke=GREEN, sw=1.3, rx=5)
    rect(f, x2 + 10, 50, 160, 22, fill=GREEN, stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 90, 61, "KHỐI C3K2 (YOLO26)", size=10, weight=700, fill="white", anchor="middle")
    f.text(x2 + 180, 61, "Khối con tùy biến (Không Tap trung gian)", size=9.2, weight=700, fill=GREEN)

    # Input tensor
    rect(f, x2 + 116, 78, 180, 26, fill="white", stroke=BOX_STROKE, sw=1, rx=3)
    f.text(x2 + col_w / 2, 91, "Input: Tensor (Cin, H, W)", size=9, weight=700, fill=DARK, anchor="middle")

    arrow(f, x2 + col_w / 2, 104, x2 + col_w / 2, 118, color=GREEN, sw=THIN)

    # cv1: Conv 1x1
    rect(f, x2 + 96, 118, 220, 28, fill="#F0FDF4", stroke=GREEN, sw=1.2, rx=3)
    f.text(x2 + col_w / 2, 132, "cv1: Conv 1×1 (Cin -> 2×e×Cout)", size=9.5, weight=700, fill=GREEN, anchor="middle")

    arrow(f, x2 + col_w / 2, 146, x2 + col_w / 2, 162, color=GREEN, sw=THIN)

    # Phép Split
    rect(f, x2 + 126, 162, 160, 24, fill="#FEF3C7", stroke=ORANGE, sw=1, rx=2)
    f.text(x2 + col_w / 2, 174, "Split thành 2 nửa: y0, y1", size=8.8, weight=700, fill=ORANGE, anchor="middle")

    # Nhánh 1: Đường tắt y0 bên trái
    f.line([(x2 + 150, 186), (x2 + 150, 198), (x2 + 52, 198), (x2 + 52, 319), (x2 + 76, 319)], color=ORANGE, width=THICK, head=True)
    f.text(x2 + 100, 190, "y0 (Bypass)", size=8, weight=700, fill=ORANGE, anchor="middle")

    # Nhánh 2: Chuỗi Module con m đa năng bên phải (Chọn theo độ sâu mạng)
    arrow(f, x2 + 270, 186, x2 + 270, 202, color=GREEN, sw=THIN)
    rect(f, x2 + 156, 202, 228, 84, fill="white", stroke=GREEN, sw=1.2, rx=3)
    f.text(x2 + 270, 214, "Chuỗi Module con m (n lần lặp):", size=8.8, weight=700, fill="#166534", anchor="middle")
    f.text(x2 + 270, 228, "• Khi c3k=False (Tầng nông P3):", size=7.8, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + 270, 240, "  Dùng Bottleneck nhẹ (e=0.25, giảm 50% kênh)", size=7.5, fill=GREEN, anchor="middle")
    f.text(x2 + 270, 255, "• Khi c3k=True (Tầng sâu P4, P5):", size=7.8, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + 270, 267, "  Dùng khối C3k (3× Conv 1×1 + 2× Conv 3×3)", size=7.5, fill=PURPLE, anchor="middle")
    f.text(x2 + 270, 279, "  Tại P5 kết hợp PSABlock (Self-Attention)", size=7.2, fill="#475569", anchor="middle")

    # Concat (Chỉ gom đúng 2 luồng: y0 và đầu ra cuối m(y1), KHÔNG TAP trung gian)
    arrow(f, x2 + 270, 286, x2 + 270, 306, color=GREEN, sw=THIN)

    rect(f, x2 + 76, 306, 260, 26, fill="#FEF3C7", stroke=ORANGE, sw=1, rx=3)
    f.text(x2 + col_w / 2, 319, "Concat (y0, m(y1)) [Chỉ đúng 2 tensor]", size=9.2, weight=700, fill=ORANGE, anchor="middle")

    arrow(f, x2 + col_w / 2, 332, x2 + col_w / 2, 346, color=GREEN, sw=THIN)

    # cv2: Conv 1x1 -> Cout
    rect(f, x2 + 96, 346, 220, 26, fill="#F0FDF4", stroke=GREEN, sw=1.2, rx=3)
    f.text(x2 + col_w / 2, 359, "cv2: Conv 1×1 (2×e×Cout -> Cout)", size=9, weight=700, fill=GREEN, anchor="middle")

    # Đánh giá Panel 2
    rect(f, x2 + 15, 380, col_w - 30, 46, fill="white", stroke=GRID, sw=1, rx=3)
    f.text(x2 + 25, 394, "Đặc tính C3k2: Tùy biến linh hoạt theo độ sâu tầng mạng.", size=8.5, weight=700, fill=DARK)
    f.text(x2 + 25, 410, "Tiết kiệm 37% FLOPs; loại bỏ toàn bộ Tap giúp giải phóng ngay SRAM.", size=8.2, fill=GREEN)

    source(f, H - 24, "Nguồn: Ultralytics (yolov8.yaml:20-47, yolo26.yaml:22-50), Sapkota et al. (YOLO26 2025 tr.5, tr.17)")
    return f


# ==============================================================================
# 2. HÌNH ĐỐI CHIẾU DETECT HEAD: DFL VS NMS-FREE (yolo-02-head-dfl-vs-nms-free)
# ==============================================================================
def fig_head_dfl_vs_nms_free():
    H = 465
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Đối chiếu Đầu dự đoán (Detect Head): YOLOv8 có DFL (reg_max=16) vs YOLO26 NMS-Free (reg_max=1)", size=13.5, weight=700, fill=DARK)

    col_w = 412
    x1 = 18
    x2 = 450

    # Panel Trái: YOLOv8 Head (DFL + Cần NMS)
    rect(f, x1, 40, col_w, 395, fill="#FFF9F9", stroke=RED, sw=1.3, rx=5)
    rect(f, x1 + 10, 50, 165, 22, fill=RED, stroke=RED, sw=1, rx=3)
    f.text(x1 + 92, 61, "YOLOv8 DECOUPLED HEAD", size=9.8, weight=700, fill="white", anchor="middle")
    f.text(x1 + 185, 61, "Hồi quy phân phối DFL + NMS", size=9.2, weight=700, fill=RED)

    # Khung Neck input
    rect(f, x1 + 35, 74, col_w - 70, 24, fill="#F8FAFC", stroke=GRID, sw=1, rx=3)
    f.text(x1 + col_w / 2, 86, "Bản đồ đặc trưng P3, P4, P5 từ Neck", size=8.8, fill=DARK, anchor="middle")

    arrow(f, x1 + 113, 100, x1 + 113, 116, color=RED, sw=THIN)
    arrow(f, x1 + 302, 100, x1 + 302, 116, color=BLUE, sw=THIN)

    # 2 nhánh song song: Reg (Trái) & Cls (Phải)
    # Nhánh Cls tầng trích đặc trưng (x=215, w=175)
    rect(f, x1 + 215, 118, 175, 38, fill="#EFF6FF", stroke=BLUE, sw=1.2, rx=3)
    f.text(x1 + 302, 131, "Nhánh Phân loại (Cls Conv)", size=9, weight=700, fill=BLUE, anchor="middle")
    f.text(x1 + 302, 145, "2× Conv 3×3 (Kênh ẩn C=64)", size=8, fill=DARK, anchor="middle")

    # Nhánh Reg tầng trích đặc trưng (x=22, w=182)
    rect(f, x1 + 22, 118, 182, 38, fill="#FEE2E2", stroke=RED, sw=1.2, rx=3)
    f.text(x1 + 113, 131, "Nhánh Hồi quy (Reg Conv)", size=9, weight=700, fill=RED, anchor="middle")
    f.text(x1 + 113, 145, "2× Conv 3×3 (Kênh ẩn C=64)", size=8, fill=DARK, anchor="middle")

    arrow(f, x1 + 113, 158, x1 + 113, 174, color=RED, sw=THIN)
    arrow(f, x1 + 302, 158, x1 + 302, 174, color=BLUE, sw=THIN)

    # Khung xử lý DFL phức tạp (Trái)
    rect(f, x1 + 22, 176, 182, 100, fill="white", stroke=RED, sw=1.2, rx=3)
    f.text(x1 + 113, 190, "GIẢI MÃ DFL (Distribution)", size=8.8, weight=700, fill=RED, anchor="middle")
    f.text(x1 + 113, 206, "1. Conv 1×1 -> 64 kênh (4×16)", size=7.8, fill=DARK, anchor="middle")
    f.text(x1 + 113, 222, "2. Softmax phi tuyến 16 bin", size=7.8, weight=700, fill=RED, anchor="middle")
    f.text(x1 + 113, 238, "3. MatMul tích phân [0..15]", size=7.8, fill=DARK, anchor="middle")
    f.text(x1 + 113, 254, "4. Tọa độ hộp = 4 kênh", size=7.8, fill=GREEN, anchor="middle")
    f.text(x1 + 113, 267, "8,400 anchor candidates", size=7.2, fill=GRAY, anchor="middle")

    # Khung dự đoán Cls (Phải - cân đối hoàn hảo về chiều cao với DFL)
    rect(f, x1 + 215, 176, 175, 100, fill="white", stroke=BLUE, sw=1.2, rx=3)
    f.text(x1 + 302, 190, "DỰ ĐOÁN XÁC SUẤT LỚP", size=8.8, weight=700, fill=BLUE, anchor="middle")
    f.text(x1 + 302, 206, "1. Conv 1×1 -> 80 classes logit", size=7.8, fill=DARK, anchor="middle")
    f.text(x1 + 302, 222, "2. Hàm Sigmoid kích hoạt xác suất", size=7.8, fill=DARK, anchor="middle")
    f.text(x1 + 302, 238, "3. Sinh nhiều hộp trùng lặp", size=7.8, weight=700, fill=RED, anchor="middle")
    f.text(x1 + 302, 254, "4. Gán nhãn One-to-Many (TAL)", size=7.8, fill=DARK, anchor="middle")
    f.text(x1 + 302, 267, "Cần CPU lọc loại bỏ dư thừa", size=7.2, fill=GRAY, anchor="middle")

    # Mũi tên từ cả 2 nhánh đồng đều đi xuống NMS (độ dài chỉ 18px, hoàn toàn cân xứng)
    arrow(f, x1 + 113, 277, x1 + 113, 292, color=RED, sw=THIN)
    arrow(f, x1 + 302, 277, x1 + 302, 292, color=BLUE, sw=THIN)

    # Đưa vào Hậu xử lý NMS trên CPU
    rect(f, x1 + 22, 294, col_w - 44, 36, fill="#FFF1F2", stroke=RED, sw=1.3, rx=4)
    f.text(x1 + col_w / 2, 307, "HẬU XỬ LÝ NMS TRÊN CPU (Non-Maximum Suppression)", size=9.2, weight=700, fill=RED, anchor="middle")
    f.text(x1 + col_w / 2, 321, "Lọc triệt tiêu hộp dư thừa bằng ngưỡng IoU; độ trễ phi tất định", size=8, fill=DARK, anchor="middle")

    arrow(f, x1 + col_w / 2, 332, x1 + col_w / 2, 346, color=RED, sw=THIN)

    # Kết quả cuối
    rect(f, x1 + 65, 348, col_w - 130, 24, fill="white", stroke=BOX_STROKE, sw=1, rx=3)
    f.text(x1 + col_w / 2, 360, "Tập hộp dự đoán cuối cùng (Variable count)", size=8.5, weight=700, fill=DARK, anchor="middle")

    # Đánh giá Panel 1
    rect(f, x1 + 15, 380, col_w - 30, 46, fill="white", stroke=GRID, sw=1, rx=3)
    f.text(x1 + 25, 394, "Rào cản NPU: Softmax phi tuyến cực kỳ khó lượng tử hóa INT8.", size=8.2, weight=700, fill=RED)
    f.text(x1 + 25, 410, "NMS chạy trên CPU chiếm tới 30-50% tổng độ trễ thực thi tại biên.", size=8.2, fill=GRAY)

    # Panel Phải: YOLO26 Head (Direct Regression + NMS-Free)
    rect(f, x2, 40, col_w, 395, fill="#F6FBF7", stroke=GREEN, sw=1.3, rx=5)
    rect(f, x2 + 10, 50, 165, 22, fill=GREEN, stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 92, 61, "YOLO26 DECOUPLED HEAD", size=9.8, weight=700, fill="white", anchor="middle")
    f.text(x2 + 185, 61, "Hồi quy trực tiếp + NMS-Free", size=9.2, weight=700, fill=GREEN)

    # Khung Neck input
    rect(f, x2 + 35, 74, col_w - 70, 24, fill="#F8FAFC", stroke=GRID, sw=1, rx=3)
    f.text(x2 + col_w / 2, 86, "Bản đồ đặc trưng P3, P4, P5 từ Neck", size=8.8, fill=DARK, anchor="middle")

    arrow(f, x2 + 113, 100, x2 + 113, 116, color=GREEN, sw=THIN)
    arrow(f, x2 + 302, 100, x2 + 302, 116, color=BLUE, sw=THIN)

    # Nhánh Cls tầng trích đặc trưng (x=215, w=175)
    rect(f, x2 + 215, 118, 175, 38, fill="#EFF6FF", stroke=BLUE, sw=1.2, rx=3)
    f.text(x2 + 302, 131, "Nhánh Phân loại (Cls Conv)", size=9, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + 302, 145, "2× Conv 3×3 (Kênh ẩn C=64)", size=8, fill=DARK, anchor="middle")

    # Nhánh Reg tầng trích đặc trưng (x=22, w=182)
    rect(f, x2 + 22, 118, 182, 38, fill="#DCFCE7", stroke=GREEN, sw=1.2, rx=3)
    f.text(x2 + 113, 131, "Nhánh Hồi quy (Reg Conv)", size=9, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 113, 145, "2× Conv 3×3 (Kênh ẩn C=64)", size=8, fill=DARK, anchor="middle")

    arrow(f, x2 + 113, 158, x2 + 113, 174, color=GREEN, sw=THIN)
    arrow(f, x2 + 302, 158, x2 + 302, 174, color=BLUE, sw=THIN)

    # Khung Hồi quy trực tiếp đơn giản (Trái)
    rect(f, x2 + 22, 176, 182, 100, fill="white", stroke=GREEN, sw=1.2, rx=3)
    f.text(x2 + 113, 190, "HỒI QUY TRỰC TIẾP (Direct)", size=8.8, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 113, 206, "1. Conv 1×1 -> Đúng 4 kênh (reg_max=1)", size=7.8, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 113, 222, "2. Loại bỏ hoàn toàn DFL & Softmax", size=7.8, fill=DARK, anchor="middle")
    f.text(x2 + 113, 238, "3. Không Reshape, không bảng LUT", size=7.8, fill=DARK, anchor="middle")
    f.text(x2 + 113, 254, "4. Tọa độ hộp tính bằng thuần INT8", size=7.8, fill=GREEN, anchor="middle")
    f.text(x2 + 113, 267, "q_out = M × (q_in * q_w) + Z_out", size=7.2, fill=GRAY, anchor="middle")

    # Khung dự đoán Cls NMS-Free (Phải - cân đối chiều cao)
    rect(f, x2 + 215, 176, 175, 100, fill="white", stroke=BLUE, sw=1.2, rx=3)
    f.text(x2 + 302, 190, "PHÂN LOẠI ĐỐI SÁNH 1-1", size=8.8, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + 302, 206, "1. Conv 1×1 -> 80 classes logit", size=7.8, fill=DARK, anchor="middle")
    f.text(x2 + 302, 222, "2. Sigmoid kích hoạt xác suất", size=7.8, fill=DARK, anchor="middle")
    f.text(x2 + 302, 238, "3. Huấn luyện Hungarian 1-1", size=7.8, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 302, 254, "4. Đúng 1 dự đoán cho 1 vật thể", size=7.8, fill=GREEN, anchor="middle")
    f.text(x2 + 302, 267, "Triệt tiêu trùng lặp ngay từ NPU", size=7.2, fill=GRAY, anchor="middle")

    # Mũi tên từ cả 2 nhánh đồng đều đi xuống Top-K (độ dài chỉ 18px, hoàn toàn cân xứng)
    arrow(f, x2 + 113, 277, x2 + 113, 292, color=GREEN, sw=THIN)
    arrow(f, x2 + 302, 277, x2 + 302, 292, color=BLUE, sw=THIN)

    # Cơ chế NMS-Free (Top-K tĩnh)
    rect(f, x2 + 22, 294, col_w - 44, 36, fill="#F0FDF4", stroke=GREEN, sw=1.3, rx=4)
    f.text(x2 + col_w / 2, 307, "CƠ CHẾ NMS-FREE (Lọc Top-K Tĩnh Đơn Định)", size=9.2, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + col_w / 2, 321, "Không cần CPU IoU loop; thời gian thực thi cố định (deterministic latency)", size=8, fill=DARK, anchor="middle")

    arrow(f, x2 + col_w / 2, 332, x2 + col_w / 2, 346, color=GREEN, sw=THIN)

    # Kết quả cuối
    rect(f, x2 + 65, 348, col_w - 130, 24, fill="white", stroke=BOX_STROKE, sw=1, rx=3)
    f.text(x2 + col_w / 2, 360, "Tập hộp dự đoán chuẩn xác (Thời gian đơn định)", size=8.5, weight=700, fill=GREEN, anchor="middle")

    # Đánh giá Panel 2
    rect(f, x2 + 15, 380, col_w - 30, 46, fill="white", stroke=GRID, sw=1, rx=3)
    f.text(x2 + 25, 394, "Lợi thế NPU: Lượng tử hóa INT8 thuần số nguyên, tính toán cực nhanh.", size=8.2, weight=700, fill=GREEN)
    f.text(x2 + 25, 410, "Độ trễ đơn định (deterministic latency), xuất trực tiếp end2end không phụ thuộc CPU.", size=8.2, fill=DARK)

    source(f, H - 24, "Nguồn: Ultralytics (yolo26.yaml:9-10), Chakrabarty et al. (YOLO26 2026 tr.5, tr.8)")
    return f


# ==============================================================================
# 3. HÌNH BIẾN ĐỔI ĐỒ THỊ TỪ TRAIN SANG INFER (yolo-03-train-to-infer-pipeline)
# ==============================================================================
def fig_train_to_infer_pipeline():
    H = 465
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Quá trình biến đổi từ Đồ thị Huấn luyện (Training DAG) sang Đồ thị Suy luận (Inference DAG)", size=13.5, weight=700, fill=DARK)

    # 3 Cột tuần tự: Training Graph -> Chuyển đổi -> Inference Graph
    # Cột 1: Training Graph (x=16, w=250)
    x1 = 16
    w1 = 250
    rect(f, x1, 40, w1, 395, fill="#FFF9F9", stroke=RED, sw=1.3, rx=5)
    rect(f, x1 + 10, 50, 160, 22, fill=RED, stroke=RED, sw=1, rx=3)
    f.text(x1 + 90, 61, "ĐỒ THỊ HUẤN LUYỆN (Train)", size=9.2, weight=700, fill="white", anchor="middle")

    train_boxes = [
        ("Input đa tỷ lệ (Dynamic)", "Kích thước biến thiên (320..640)", "#F8FAFC", DARK, 78, 34),
        ("Lớp tích chập tuần tự", "Conv(W) tách biệt BatchNorm(mean, var)", "#FEE2E2", RED, 118, 34),
        ("Đầu kép (Dual Heads)", "Nhánh một-nhiều (Aux) + Nhánh 1-1", "#FFFBEB", ORANGE, 158, 34),
        ("Cụm tính Loss (Phức tạp)", "ProgLoss, STAL, CIoU, DFL, BCE", "#FEE2E2", RED, 198, 34),
        ("Băng ghi Gradient (Autograd)", "Lưu intermediate activations trên VRAM", "#FFF1F2", RED, 238, 34),
        ("Cập nhật Optimizer", "Momentum, AdamW trạng thái động", "#F8FAFC", DARK, 278, 34),
    ]
    for title, desc, bg, color, by, bh in train_boxes:
        rect(f, x1 + 10, by, w1 - 20, bh, fill=bg, stroke=color, sw=1, rx=3)
        f.text(x1 + w1 / 2, by + 12, title, size=8.5, weight=700, fill=color, anchor="middle")
        f.text(x1 + w1 / 2, by + 25, desc, size=7.8, fill=DARK, anchor="middle")

    rect(f, x1 + 10, 320, w1 - 20, 105, fill="white", stroke=GRID, sw=1, rx=3)
    f.text(x1 + 18, 336, "Đặc điểm pha huấn luyện:", size=8.8, weight=700, fill=DARK)
    f.text(x1 + 18, 354, "• Đồ thị động, kích thước lớn", size=8, fill=RED)
    f.text(x1 + 18, 372, "• Bộ nhớ VRAM tiêu tốn nhiều", size=8, fill=DARK)
    f.text(x1 + 18, 390, "• Không thể chạy trên NPU biên", size=8, fill=GRAY)
    f.text(x1 + 18, 408, "• Nhiều nhánh chỉ dùng backward", size=8, fill=GRAY)

    # Cột 2: Các bước biến đổi trung gian (x=296, w=280)
    x2 = 296
    w2 = 280
    rect(f, x2, 40, w2, 395, fill="#F0F7FF", stroke=BLUE, sw=1.3, rx=5)
    rect(f, x2 + 10, 50, 185, 22, fill=BLUE, stroke=BLUE, sw=1, rx=3)
    f.text(x2 + 102, 61, "CƠ CHẾ BIẾN ĐỔI (model.fuse)", size=9.2, weight=700, fill="white", anchor="middle")

    transforms = [
        ("1. Conv + BatchNorm Fusion", "Gấp affine BN vào trọng số: W_fuse, b_fuse", BLUE, 78),
        ("2. Cắt tỉa nhánh phụ trợ (Prune)", "Xóa bỏ hoàn toàn One-to-Many Auxiliary Head", ORANGE, 134),
        ("3. Ngắt toàn bộ nút tính Loss", "ProgLoss, CIoU chỉ dùng train, không export", DARK, 190),
        ("4. Khóa hằng số (Constant Fold)", "Cố định input (1,3,640,640), gỡ dead code", GREEN, 246),
        ("5. Loại bỏ DFL & NMS (YOLO26)", "Thay bằng hồi quy trực tiếp 4 kênh tuyến tính", TEAL, 302),
    ]
    for title, desc, color, ty in transforms:
        rect(f, x2 + 10, ty, w2 - 20, 44, fill="white", stroke=color, sw=1.2, rx=3)
        f.text(x2 + w2 / 2, ty + 15, title, size=8.8, weight=700, fill=color, anchor="middle")
        f.text(x2 + w2 / 2, ty + 30, desc, size=7.8, fill=DARK, anchor="middle")

    rect(f, x2 + 10, 356, w2 - 20, 69, fill="white", stroke=GRID, sw=1, rx=3)
    f.text(x2 + w2 / 2, 372, "Chuyển trạng thái: model.eval()", size=8.8, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + w2 / 2, 390, "Tắt requires_grad, vô hiệu hóa Dropout", size=8, fill=DARK, anchor="middle")
    f.text(x2 + w2 / 2, 408, "Giải phóng toàn bộ cache gradient", size=8, fill=GRAY, anchor="middle")

    # Mũi tên từ Cột 1 sang Cột 2 (gap = 30px, from 266 to 296)
    arrow(f, x1 + w1 + 3, 230, x2 - 3, 230, color=BLUE, sw=THICK)

    # Cột 3: Inference Graph (x=606, w=258)
    x3 = 606
    w3 = 258
    rect(f, x3, 40, w3, 395, fill="#F6FBF7", stroke=GREEN, sw=1.3, rx=5)
    rect(f, x3 + 10, 50, 175, 22, fill=GREEN, stroke=GREEN, sw=1, rx=3)
    f.text(x3 + 97, 61, "ĐỒ THỊ SUY LUẬN (Inference)", size=9.2, weight=700, fill="white", anchor="middle")

    infer_boxes = [
        ("Input tĩnh: (1, 3, 640, 640)", "Bộ đệm tĩnh, không cấp phát động", "#F0FDF4", GREEN, 78, 34),
        ("Các lớp Tích chập đã gộp", "Conv duy nhất có bias tích hợp sẵn", "#F8FAFC", DARK, 118, 34),
        ("Chỉ giữ Đầu một-một (1-to-1)", "Đầu ra đơn nhất, sẵn sàng NMS-free", "#F0FDF4", GREEN, 158, 34),
        ("Khối Attention P5 (C2PSA)", "4× MatMul, 2× Softmax cố định", "#FAF5FF", PURPLE, 198, 34),
        ("Hồi quy trực tiếp 4 kênh", "0 Softmax phân mảnh, thuần INT8", "#F0FDF4", GREEN, 238, 34),
        ("Đầu ra: Box(4) + Score(80)", "Tối ưu hóa bảng trang IOMMU & DMA", "#F8FAFC", DARK, 278, 34),
    ]
    for title, desc, bg, color, by, bh in infer_boxes:
        rect(f, x3 + 10, by, w3 - 20, bh, fill=bg, stroke=color, sw=1, rx=3)
        f.text(x3 + w3 / 2, by + 12, title, size=8.5, weight=700, fill=color, anchor="middle")
        f.text(x3 + w3 / 2, by + 25, desc, size=7.8, fill=DARK, anchor="middle")

    rect(f, x3 + 10, 320, w3 - 20, 105, fill="white", stroke=GRID, sw=1, rx=3)
    f.text(x3 + 18, 336, "Lợi thế triển khai phần cứng:", size=8.8, weight=700, fill=DARK)
    f.text(x3 + 18, 354, "• Đồ thị tĩnh (DAG) tất định", size=8, weight=700, fill=GREEN)
    f.text(x3 + 18, 372, "• Dễ dàng lượng tử hóa INT8", size=8, fill=DARK)
    f.text(x3 + 18, 390, "• Giảm 30% tham số, 37% FLOPs", size=8, fill=GREEN)
    f.text(x3 + 18, 408, "• Không phụ thuộc NMS trên CPU", size=8, fill=GREEN)

    # Mũi tên từ Cột 2 sang Cột 3 (gap = 30px, from 576 to 606)
    arrow(f, x2 + w2 + 3, 230, x3 - 3, 230, color=GREEN, sw=THICK)

    source(f, H - 24, "Nguồn: Ultralytics (yolo26.yaml:13), Sapkota et al. (YOLO26 2025 tr.17), Jocher (YOLO26 2026 tr.11)")
    return f


def main():
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("yolo-01-c2f-vs-c3k2", fig_c2f_vs_c3k2),
        ("yolo-02-head-dfl-vs-nms-free", fig_head_dfl_vs_nms_free),
        ("yolo-03-train-to-infer-pipeline", fig_train_to_infer_pipeline),
    ]
    run(figures, DEFAULT_OUTDIR)


if __name__ == "__main__":
    main()
