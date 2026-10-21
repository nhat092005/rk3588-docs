#!/usr/bin/env python3
"""Chuyên đề: Huấn luyện và suy luận (06-huan-luyen-va-suy-luan.rst).

Sinh 3 hình minh họa trực quan vector SVG chuẩn visual_guide:
  - hl-1-ma-tran-eval-vs-nograd:
    Sơ đồ mạng nơ-ron thực tế trong 4 góc ma trận (dropped nodes, backward tape, input gradients).
  - hl-2-pipeline-suy-luan-rk3588:
    Minh họa hình học LetterBox (đệm xám 114), NPU 3-core tensor flow, và NMS lọc hộp dày đặc về 1 hộp.
  - hl-3-luong-xuat-model-pytorch-sang-rknn:
    Biến đổi đồ thị tính toán: Conv+BN gộp thành Fused Conv, RepConv 3 nhánh gộp về 1 kernel, và lưới lượng tử INT8.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 2 cấp: 06-huan-luyen-va-suy-luan -> 01-kien-thuc-nen -> figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "01-nen-tang-ai", "06-huan-luyen-va-suy-luan"
    )
)

W = 860
PURPLE = "#7B1FA2"
ORANGE = "#E65100"
TEAL = "#00796B"
GRID = "#E2E8F0"


def tier(f, label, x=W - 130, y=4):
    f.tier(x, y, label)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def circle(f, cx, cy, r, fill="white", stroke="#333333", sw=1.2, dashed=False):
    dash = ' stroke-dasharray="3 2"' if dashed else ""
    f.a(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN, dashed=False):
    if color not in (BLUE, GREEN, RED, GRAY, INK):
        color = INK
    f.line([(x1, y1), (x2, y2)], color, width=sw, dashed=dashed, head=True)


# ==============================================================================
# 1. HÌNH MA TRẬN TRỰC QUAN EVAL VS NO_GRAD (hl-1)
# ==============================================================================
def fig_matrix_eval_nograd():
    H = 465
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(12, 18, "Ma trận phối hợp PyTorch: Cấu trúc mạng (Dropout, BN) và Luồng Gradient theo 4 trạng thái", size=13.5, weight=700, fill=DARK)

    # Khung ma trận 2x2
    col_w = 340
    x_col1 = 165
    x_col2 = 515

    # Header Cột (Autograd)
    rect(f, x_col1, 38, col_w, 36, fill="#F8FAFC", stroke="#CBD5E1", sw=1.2, rx=4)
    f.text(x_col1 + col_w / 2, 53, "Autograd BẬT: torch.enable_grad() (Mặc định)", size=9.8, weight=700, fill=DARK, anchor="middle")
    f.text(x_col1 + col_w / 2, 67, "Ghi chép đồ thị DAG, lưu intermediate activations vào VRAM", size=8.2, fill=GRAY, anchor="middle")

    rect(f, x_col2, 38, col_w, 36, fill="#F8FAFC", stroke="#CBD5E1", sw=1.2, rx=4)
    f.text(x_col2 + col_w / 2, 53, "Autograd TẮT: with torch.no_grad()", size=9.8, weight=700, fill=DARK, anchor="middle")
    f.text(x_col2 + col_w / 2, 67, "Tắt ghi DAG, kết quả requires_grad=False, giải phóng bộ nhớ", size=8.2, fill=GRAY, anchor="middle")

    # Hàng 1 (train) & Hàng 2 (eval)
    row_h = 160
    y_row1 = 82
    y_row2 = 250
    y_hdr_w = 140

    # Header Hàng 1: train
    rect(f, 15, y_row1, y_hdr_w, row_h, fill="#EFF6FF", stroke=BLUE, sw=1.2, rx=4)
    f.text(25, y_row1 + 22, "model.train()", size=11, weight=700, fill=BLUE)
    f.text(25, y_row1 + 40, "Chế độ Huấn luyện", size=9, weight=600, fill=DARK)
    f.text(25, y_row1 + 65, "Dropout: BẬT", size=8.6, weight=700, fill=RED)
    f.text(25, y_row1 + 79, "Loại ngẫu nhiên nút (p > 0)", size=8.0, fill=GRAY)
    f.text(25, y_row1 + 102, "BatchNorm: CẬP NHẬT", size=8.6, weight=700, fill=BLUE)
    f.text(25, y_row1 + 116, "Dùng μ_B, σ²_B của batch", size=8.0, fill=GRAY)
    f.text(25, y_row1 + 130, "Tích lũy running stats", size=8.0, fill=GRAY)

    # Header Hàng 2: eval
    rect(f, 15, y_row2, y_hdr_w, row_h, fill="#F0FDF4", stroke=GREEN, sw=1.2, rx=4)
    f.text(25, y_row2 + 22, "model.eval()", size=11, weight=700, fill=GREEN)
    f.text(25, y_row2 + 40, "Chế độ Đánh giá / Suy luận", size=9, weight=600, fill=DARK)
    f.text(25, y_row2 + 65, "Dropout: TẮT", size=8.6, weight=700, fill=GREEN)
    f.text(25, y_row2 + 79, "Hàm đồng nhất (Identity)", size=8.0, fill=GRAY)
    f.text(25, y_row2 + 102, "BatchNorm: CỐ ĐỊNH", size=8.6, weight=700, fill=GREEN)
    f.text(25, y_row2 + 116, "Dùng μ_run, σ²_run đã khóa", size=8.0, fill=GRAY)
    f.text(25, y_row2 + 130, "Không đổi running stats", size=8.0, fill=GRAY)

    # --- Ô 1 (Trên - Trái): train() + grad ---
    rect(f, x_col1, y_row1, col_w, row_h, fill="#FFFFFF", stroke=GREEN, sw=1.5, rx=4)
    rect(f, x_col1 + 8, y_row1 + 8, 140, 18, fill="#DCFCE7", stroke=GREEN, sw=1, rx=3)
    f.text(x_col1 + 78, y_row1 + 20, "HUẤN LUYỆN CHUẨN", size=8.2, weight=700, fill=GREEN, anchor="middle")

    # Inputs (x1, x2)
    circle(f, x_col1 + 35, y_row1 + 52, 9, fill="#E2E8F0", stroke=DARK)
    f.text(x_col1 + 35, y_row1 + 55, "x₁", size=7.8, weight=700, fill=DARK, anchor="middle")
    circle(f, x_col1 + 35, y_row1 + 90, 9, fill="#E2E8F0", stroke=DARK)
    f.text(x_col1 + 35, y_row1 + 93, "x₂", size=7.8, weight=700, fill=DARK, anchor="middle")

    # Hidden (h1 active, h2 DROPPED)
    circle(f, x_col1 + 105, y_row1 + 52, 9, fill="#DCFCE7", stroke=GREEN)
    f.text(x_col1 + 105, y_row1 + 55, "h₁", size=7.8, weight=700, fill=GREEN, anchor="middle")
    circle(f, x_col1 + 105, y_row1 + 90, 11, fill="#FEE2E2", stroke=RED, dashed=True)
    f.text(x_col1 + 105, y_row1 + 94, "✕", size=8.5, weight=700, fill=RED, anchor="middle")
    f.text(x_col1 + 105, y_row1 + 110, "Drop (p)", size=7.0, fill=RED, anchor="middle")

    # Output (y)
    circle(f, x_col1 + 175, y_row1 + 71, 9, fill="#E0F2FE", stroke=BLUE)
    f.text(x_col1 + 175, y_row1 + 74, "ŷ", size=7.8, weight=700, fill=BLUE, anchor="middle")

    # Forward arrows
    arrow(f, x_col1 + 46, y_row1 + 52, x_col1 + 94, y_row1 + 52, color=BLUE, sw=1.3)
    arrow(f, x_col1 + 46, y_row1 + 90, x_col1 + 94, y_row1 + 56, color=BLUE, sw=1.3)
    arrow(f, x_col1 + 116, y_row1 + 52, x_col1 + 164, y_row1 + 68, color=BLUE, sw=1.3)

    # Backward gradient flow
    arrow(f, x_col1 + 164, y_row1 + 76, x_col1 + 116, y_row1 + 60, color=RED, sw=1.3, dashed=True)
    arrow(f, x_col1 + 94, y_row1 + 52, x_col1 + 46, y_row1 + 52, color=RED, sw=1.3, dashed=True)
    f.text(x_col1 + 140, y_row1 + 94, "∇_w L", size=8.2, weight=700, fill=RED, anchor="middle")

    f.text(x_col1 + 200, y_row1 + 46, "• Forward: lưu cache VRAM", size=8.0, fill=DARK)
    f.text(x_col1 + 200, y_row1 + 62, "• Dropout: triệt tiêu nút h₂", size=8.0, fill=DARK)
    f.text(x_col1 + 200, y_row1 + 78, "• BN: μ_B, σ²_B từ mini-batch", size=8.0, fill=DARK)
    f.text(x_col1 + 200, y_row1 + 94, "• Backward: tính đạo hàm", size=8.0, weight=600, fill=GREEN)
    f.text(x_col1 + 200, y_row1 + 110, "• Sẵn sàng optimizer.step()", size=8.0, fill=GRAY)
    f.text(x_col1 + 15, y_row1 + 140, "-> Trạng thái chuẩn trong vòng lặp huấn luyện chính.", size=8.0, fill=GRAY)

    # --- Ô 2 (Trên - Phải): train() + no_grad() ---
    rect(f, x_col2, y_row1, col_w, row_h, fill="#FFF5F5", stroke=RED, sw=1.5, rx=4)
    rect(f, x_col2 + 8, y_row1 + 8, 155, 18, fill="#FEE2E2", stroke=RED, sw=1, rx=3)
    f.text(x_col2 + 85, y_row1 + 20, "LỖI LOGIC: QUÊN EVAL()", size=8.2, weight=700, fill=RED, anchor="middle")

    circle(f, x_col2 + 35, y_row1 + 52, 9, fill="#E2E8F0", stroke=DARK)
    f.text(x_col2 + 35, y_row1 + 55, "x₁", size=7.8, weight=700, fill=DARK, anchor="middle")
    circle(f, x_col2 + 35, y_row1 + 90, 9, fill="#E2E8F0", stroke=DARK)
    f.text(x_col2 + 35, y_row1 + 93, "x₂", size=7.8, weight=700, fill=DARK, anchor="middle")

    circle(f, x_col2 + 105, y_row1 + 52, 9, fill="#E2E8F0", stroke=DARK)
    f.text(x_col2 + 105, y_row1 + 55, "h₁", size=7.8, weight=700, fill=DARK, anchor="middle")
    circle(f, x_col2 + 105, y_row1 + 90, 11, fill="#FEE2E2", stroke=RED, dashed=True)
    f.text(x_col2 + 105, y_row1 + 94, "✕", size=8.5, weight=700, fill=RED, anchor="middle")
    f.text(x_col2 + 105, y_row1 + 110, "Drop (p)", size=7.0, fill=RED, anchor="middle")

    circle(f, x_col2 + 175, y_row1 + 71, 9, fill="#E2E8F0", stroke=DARK)
    f.text(x_col2 + 175, y_row1 + 74, "ŷ", size=7.8, weight=700, fill=DARK, anchor="middle")

    arrow(f, x_col2 + 46, y_row1 + 52, x_col2 + 94, y_row1 + 52, color=BLUE, sw=1.3)
    arrow(f, x_col2 + 116, y_row1 + 52, x_col2 + 164, y_row1 + 68, color=BLUE, sw=1.3)

    # Biểu tượng cấm backward tape
    rect(f, x_col2 + 120, y_row1 + 82, 52, 18, fill="#FEE2E2", stroke=RED, sw=1, rx=2)
    f.text(x_col2 + 146, y_row1 + 94, "No DAG", size=7.2, weight=700, fill=RED, anchor="middle")

    f.text(x_col2 + 195, y_row1 + 46, "• Tiết kiệm RAM (tắt DAG)", size=8.0, fill=DARK)
    f.text(x_col2 + 195, y_row1 + 62, "• CẢNH BÁO: Dropout vẫn bật", size=8.0, weight=700, fill=RED)
    f.text(x_col2 + 200, y_row1 + 76, "-> Dự đoán bị nhiễu ngẫu nhiên!", size=7.5, fill=RED)
    f.text(x_col2 + 195, y_row1 + 92, "• BN vẫn cập nhật running stats", size=8.0, weight=700, fill=RED)
    f.text(x_col2 + 200, y_row1 + 106, "-> Làm trôi lệch trọng số gốc!", size=7.5, fill=RED)
    f.text(x_col2 + 15, y_row1 + 140, "-> Lỗi ngầm cực kỳ nguy hiểm trong inference pipeline.", size=8.0, fill=GRAY)

    # --- Ô 3 (Dưới - Trái): eval() + grad ---
    rect(f, x_col1, y_row2, col_w, row_h, fill="#FAF5FF", stroke=PURPLE, sw=1.5, rx=4)
    rect(f, x_col1 + 8, y_row2 + 8, 165, 18, fill="#F3E8FF", stroke=PURPLE, sw=1, rx=3)
    f.text(x_col1 + 90, y_row2 + 20, "TÁC VỤ GRADIENT ĐẶC BIỆT", size=8.2, weight=700, fill=PURPLE, anchor="middle")

    circle(f, x_col1 + 35, y_row2 + 52, 9, fill="#F3E8FF", stroke=PURPLE)
    f.text(x_col1 + 35, y_row2 + 55, "x₁", size=7.8, weight=700, fill=PURPLE, anchor="middle")
    circle(f, x_col1 + 35, y_row2 + 90, 9, fill="#F3E8FF", stroke=PURPLE)
    f.text(x_col1 + 35, y_row2 + 93, "x₂", size=7.8, weight=700, fill=PURPLE, anchor="middle")

    circle(f, x_col1 + 105, y_row2 + 52, 9, fill="#F3E8FF", stroke=PURPLE)
    f.text(x_col1 + 105, y_row2 + 55, "h₁", size=7.8, weight=700, fill=PURPLE, anchor="middle")
    circle(f, x_col1 + 105, y_row2 + 90, 9, fill="#F3E8FF", stroke=PURPLE)
    f.text(x_col1 + 105, y_row2 + 93, "h₂", size=7.8, weight=700, fill=PURPLE, anchor="middle")
    f.text(x_col1 + 105, y_row2 + 110, "100% nút", size=7.0, fill=PURPLE, anchor="middle")

    circle(f, x_col1 + 175, y_row2 + 71, 9, fill="#F3E8FF", stroke=PURPLE)
    f.text(x_col1 + 175, y_row2 + 74, "ŷ", size=7.8, weight=700, fill=PURPLE, anchor="middle")

    # Forward
    arrow(f, x_col1 + 46, y_row2 + 52, x_col1 + 94, y_row2 + 52, color=BLUE, sw=1.2)
    arrow(f, x_col1 + 116, y_row2 + 71, x_col1 + 164, y_row2 + 71, color=BLUE, sw=1.2)

    # Backward chạy thẳng về x
    arrow(f, x_col1 + 164, y_row2 + 78, x_col1 + 116, y_row2 + 78, color=RED, sw=1.3, dashed=True)
    arrow(f, x_col1 + 94, y_row2 + 58, x_col1 + 46, y_row2 + 58, color=RED, sw=1.3, dashed=True)
    arrow(f, x_col1 + 94, y_row2 + 90, x_col1 + 46, y_row2 + 90, color=RED, sw=1.3, dashed=True)
    f.text(x_col1 + 22, y_row2 + 120, "∂L/∂x", size=8.0, weight=700, fill=RED, anchor="middle")

    f.text(x_col1 + 195, y_row2 + 46, "• Dropout tắt, BN khóa cố định", size=8.0, fill=DARK)
    f.text(x_col1 + 195, y_row2 + 62, "• Autograd tính đạo hàm input x", size=8.0, weight=600, fill=PURPLE)
    f.text(x_col1 + 195, y_row2 + 78, "• Ứng dụng: FGSM Attack,", size=8.0, fill=DARK)
    f.text(x_col1 + 200, y_row2 + 92, "  Grad-CAM giải thích mô hình", size=7.8, fill=GRAY)
    f.text(x_col1 + 195, y_row2 + 108, "• Quên no_grad -> tràn VRAM!", size=8.0, weight=700, fill=RED)
    f.text(x_col1 + 15, y_row2 + 140, "-> Chỉ dùng khi cố ý cần phân tích gradient.", size=8.0, fill=GRAY)

    # --- Ô 4 (Dưới - Phải): eval() + no_grad() ---
    rect(f, x_col2, y_row2, col_w, row_h, fill="#FFFFFF", stroke=BLUE, sw=1.5, rx=4)
    rect(f, x_col2 + 8, y_row2 + 8, 150, 18, fill="#DBEAFE", stroke=BLUE, sw=1, rx=3)
    f.text(x_col2 + 83, y_row2 + 20, "SUY LUẬN CHUẨN (INFER)", size=8.2, weight=700, fill=BLUE, anchor="middle")

    circle(f, x_col2 + 35, y_row2 + 52, 9, fill="#E2E8F0", stroke=DARK)
    f.text(x_col2 + 35, y_row2 + 55, "x₁", size=7.8, weight=700, fill=DARK, anchor="middle")
    circle(f, x_col2 + 35, y_row2 + 90, 9, fill="#E2E8F0", stroke=DARK)
    f.text(x_col2 + 35, y_row2 + 93, "x₂", size=7.8, weight=700, fill=DARK, anchor="middle")

    circle(f, x_col2 + 105, y_row2 + 52, 9, fill="#DBEAFE", stroke=BLUE)
    f.text(x_col2 + 105, y_row2 + 55, "h₁", size=7.8, weight=700, fill=BLUE, anchor="middle")
    circle(f, x_col2 + 105, y_row2 + 90, 9, fill="#DBEAFE", stroke=BLUE)
    f.text(x_col2 + 105, y_row2 + 93, "h₂", size=7.8, weight=700, fill=BLUE, anchor="middle")

    circle(f, x_col2 + 175, y_row2 + 71, 9, fill="#DBEAFE", stroke=BLUE)
    f.text(x_col2 + 175, y_row2 + 74, "ŷ", size=7.8, weight=700, fill=BLUE, anchor="middle")

    arrow(f, x_col2 + 46, y_row2 + 52, x_col2 + 94, y_row2 + 52, color=BLUE, sw=1.3)
    arrow(f, x_col2 + 46, y_row2 + 90, x_col2 + 94, y_row2 + 56, color=BLUE, sw=1.3)
    arrow(f, x_col2 + 46, y_row2 + 90, x_col2 + 94, y_row2 + 90, color=BLUE, sw=1.3)
    arrow(f, x_col2 + 116, y_row2 + 52, x_col2 + 164, y_row2 + 68, color=BLUE, sw=1.3)
    arrow(f, x_col2 + 116, y_row2 + 90, x_col2 + 164, y_row2 + 74, color=BLUE, sw=1.3)

    rect(f, x_col2 + 122, y_row2 + 98, 62, 16, fill="#DCFCE7", stroke=GREEN, sw=1, rx=2)
    f.text(x_col2 + 153, y_row2 + 109, "0 VRAM DAG", size=7.0, weight=700, fill=GREEN, anchor="middle")

    f.text(x_col2 + 195, y_row2 + 46, "• Giải phóng 100% RAM đồ thị", size=8.0, weight=600, fill=BLUE)
    f.text(x_col2 + 195, y_row2 + 62, "• Toàn bộ cấu trúc xác định", size=8.0, fill=DARK)
    f.text(x_col2 + 195, y_row2 + 78, "• BN cố định μ_run, σ²_run", size=8.0, fill=DARK)
    f.text(x_col2 + 195, y_row2 + 94, "• Sẵn sàng gộp Conv-BN", size=8.0, weight=600, fill=GREEN)
    f.text(x_col2 + 200, y_row2 + 108, "  để xuất sang ONNX / RKNN", size=7.8, fill=GRAY)
    f.text(x_col2 + 15, y_row2 + 140, "-> Cấu hình bắt buộc khi triển khai thực tế trên RK3588.", size=8.0, fill=GRAY)

    source(f, 420, "Nguồn: T1 PyTorch docs torch.nn.Module [PTMOD] và torch.no_grad [PTGRAD]. eval() kiểm soát layer; no_grad() kiểm soát autograd.")
    return f


# ==============================================================================
# 2. HÌNH PIPELINE SUY LUẬN TRỰC QUAN TRÊN RK3588 (hl-2)
# ==============================================================================
def fig_pipeline_rk3588():
    H = 485
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(12, 18, "Minh họa hình học Pipeline suy luận phát hiện vật thể trên RK3588 (NumPy & RKNN)", size=13.5, weight=700, fill=DARK)

    # 3 Cột panel chính: w=240, khoảng cách giữa các cột = 55px
    col_w = 240
    col_h = 230
    x1 = 15
    x2 = 310
    x3 = 605
    y_box = 42

    # --- PANEL 1: TIỀN XỬ LÝ HÌNH HỌC (LetterBox) ---
    rect(f, x1, y_box, col_w, col_h, fill="#F8FAFC", stroke=BLUE, sw=1.3, rx=5)
    rect(f, x1, y_box, col_w, 28, fill="#EFF6FF", stroke=BLUE, sw=1.3, rx=5)
    f.text(x1 + 12, y_box + 19, "1. TIỀN XỬ LÝ (LetterBox 640)", size=9.8, weight=700, fill=BLUE)

    # Vẽ ảnh gốc tỷ lệ rộng (16:9)
    rect(f, x1 + 15, y_box + 38, 86, 50, fill="#E2E8F0", stroke=DARK, sw=1.2)
    circle(f, x1 + 58, y_box + 58, 7, fill="#94A3B8", stroke=DARK)
    f.line([(x1 + 58, y_box + 65), (x1 + 58, y_box + 80)], DARK, width=1.4, head=False)
    f.text(x1 + 110, y_box + 54, "(H₀, W₀, 3) BGR", size=8.2, weight=600, fill=DARK)
    f.text(x1 + 110, y_box + 68, "Ảnh gốc 1080×1920", size=7.8, fill=GRAY)

    # Mũi tên biến đổi xuống
    arrow(f, x1 + 58, y_box + 92, x1 + 58, y_box + 112, color=BLUE, sw=1.4)
    f.text(x1 + 68, y_box + 105, "Resize dài về 640", size=7.5, fill=BLUE)

    # Vẽ ảnh vuông LetterBox 640x640 với 2 dải đệm xám 114
    rect(f, x1 + 15, y_box + 118, 86, 86, fill="#FFFFFF", stroke=DARK, sw=1.2)
    # Dải đệm trên (114, 114, 114)
    rect(f, x1 + 15, y_box + 118, 86, 17, fill="#727272", stroke="none")
    f.text(x1 + 58, y_box + 129, "padh = 114", size=6.8, fill="white", anchor="middle")
    # Vùng ảnh resized ở giữa
    rect(f, x1 + 15, y_box + 135, 86, 52, fill="#E2E8F0", stroke="none")
    circle(f, x1 + 58, y_box + 155, 6, fill="#94A3B8", stroke=DARK)
    f.line([(x1 + 58, y_box + 161), (x1 + 58, y_box + 175)], DARK, width=1.4, head=False)
    # Dải đệm dưới (114, 114, 114)
    rect(f, x1 + 15, y_box + 187, 86, 17, fill="#727272", stroke="none")
    f.text(x1 + 58, y_box + 198, "padh = 114", size=6.8, fill="white", anchor="middle")

    f.text(x1 + 110, y_box + 140, "(1, 640, 640, 3)", size=8.5, weight=700, fill=GREEN)
    f.text(x1 + 110, y_box + 156, "uint8 RGB [NHWC]", size=8.0, fill=DARK)
    f.text(x1 + 110, y_box + 172, "Lưu meta khôi phục:", size=7.8, fill=GRAY)
    f.text(x1 + 110, y_box + 186, "gain, padw, padh", size=7.8, fill=GRAY)

    f.text(x1 + 120, y_box + 218, "Ảnh vuông đệm chuẩn board", size=7.5, fill=GRAY, anchor="middle")

    # Mũi tên liên trạm 1 -> 2: từ 255 đến 310 (dài 55px)
    arrow(f, x1 + col_w + 4, y_box + col_h / 2, x2 - 5, y_box + col_h / 2, color=BLUE, sw=1.6)
    f.text((x1 + col_w + x2) / 2, y_box + col_h / 2 - 7, "uint8 NHWC", size=7.5, weight=700, fill=BLUE, anchor="middle")

    # --- PANEL 2: FORWARD NPU TRÊN 3 CORE RK3588 ---
    rect(f, x2, y_box, col_w, col_h, fill="#F8FAFC", stroke=GREEN, sw=1.3, rx=5)
    rect(f, x2, y_box, col_w, 28, fill="#F0FDF4", stroke=GREEN, sw=1.3, rx=5)
    f.text(x2 + 12, y_box + 19, "2. FORWARD NPU (RK3588 3-Core)", size=9.8, weight=700, fill=GREEN)

    # Khung NPU Hardware
    rect(f, x2 + 12, y_box + 36, 216, 68, fill="#DCFCE7", stroke=GREEN, sw=1.2, rx=4)
    f.text(x2 + 20, y_box + 49, "Phần cứng NPU RK3588 (6 TOPS)", size=8.2, weight=700, fill=GREEN)

    # 3 Chip Core NPU
    rect(f, x2 + 20, y_box + 56, 58, 40, fill="#FFFFFF", stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 49, y_box + 71, "Core 0", size=7.8, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + 49, y_box + 84, "Backbone", size=7.0, fill=GRAY, anchor="middle")

    rect(f, x2 + 88, y_box + 56, 58, 40, fill="#FFFFFF", stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 117, y_box + 71, "Core 1", size=7.8, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + 117, y_box + 84, "Neck Fused", size=7.0, fill=GRAY, anchor="middle")

    rect(f, x2 + 156, y_box + 56, 58, 40, fill="#FFFFFF", stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 185, y_box + 71, "Core 2", size=7.8, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + 185, y_box + 84, "Detect Head", size=7.0, fill=GRAY, anchor="middle")

    arrow(f, x2 + 120, y_box + 108, x2 + 120, y_box + 124, color=GREEN, sw=1.4)

    # 3 Thang đo Feature Maps P3, P4, P5
    rect(f, x2 + 12, y_box + 126, 66, 50, fill="#FFFFFF", stroke="#CBD5E1", sw=1, rx=3)
    f.text(x2 + 45, y_box + 141, "P3 / 8", size=8.0, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + 45, y_box + 154, "80×80", size=7.5, fill=BLUE, anchor="middle")
    f.text(x2 + 45, y_box + 167, "6400 boxes", size=7.0, fill=GRAY, anchor="middle")

    rect(f, x2 + 87, y_box + 126, 66, 50, fill="#FFFFFF", stroke="#CBD5E1", sw=1, rx=3)
    f.text(x2 + 120, y_box + 141, "P4 / 16", size=8.0, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + 120, y_box + 154, "40×40", size=7.5, fill=BLUE, anchor="middle")
    f.text(x2 + 120, y_box + 167, "1600 boxes", size=7.0, fill=GRAY, anchor="middle")

    rect(f, x2 + 162, y_box + 126, 66, 50, fill="#FFFFFF", stroke="#CBD5E1", sw=1, rx=3)
    f.text(x2 + 195, y_box + 141, "P5 / 32", size=8.0, weight=700, fill=DARK, anchor="middle")
    f.text(x2 + 195, y_box + 154, "20×20", size=7.5, fill=BLUE, anchor="middle")
    f.text(x2 + 195, y_box + 167, "400 boxes", size=7.0, fill=GRAY, anchor="middle")

    f.text(x2 + 120, y_box + 194, "Đầu ra thô: (1, 4 + nc, 8400)", size=8.5, weight=700, fill=GREEN, anchor="middle")
    f.text(x2 + 120, y_box + 210, "Tổng cộng 8400 hộp dự đoán dạng xywh", size=7.5, fill=GRAY, anchor="middle")

    # Mũi tên liên trạm 2 -> 3: từ 550 đến 605 (dài 55px)
    arrow(f, x2 + col_w + 4, y_box + col_h / 2, x3 - 5, y_box + col_h / 2, color=GREEN, sw=1.6)
    f.text((x2 + col_w + x3) / 2, y_box + col_h / 2 - 7, "8400 boxes", size=7.5, weight=700, fill=GREEN, anchor="middle")

    # --- PANEL 3: HẬU XỬ LÝ (NMS & KHÔI PHỤC TOẠ ĐỘ) ---
    rect(f, x3, y_box, col_w, col_h, fill="#F8FAFC", stroke=ORANGE, sw=1.3, rx=5)
    rect(f, x3, y_box, col_w, 28, fill="#FFFBEB", stroke=ORANGE, sw=1.3, rx=5)
    f.text(x3 + 12, y_box + 19, "3. HẬU XỬ LÝ (NMS & Rescale)", size=9.8, weight=700, fill=ORANGE)

    # Bước 1: Hộp chồng lấn
    rect(f, x3 + 15, y_box + 38, 86, 68, fill="#FFFFFF", stroke=DARK, sw=1.2)
    circle(f, x3 + 55, y_box + 68, 6, fill="#94A3B8", stroke=DARK)
    f.line([(x3 + 55, y_box + 74), (x3 + 55, y_box + 90)], DARK, width=1.4, head=False)
    # Hộp đúng (xanh lá)
    rect(f, x3 + 40, y_box + 56, 30, 42, fill="none", stroke=GREEN, sw=1.4)
    f.text(x3 + 55, y_box + 46, "0.89", size=6.6, weight=700, fill=GREEN, anchor="middle")
    # Hộp trùng (đỏ)
    rect(f, x3 + 37, y_box + 53, 34, 45, fill="none", stroke=RED, sw=1, dashed=True)
    f.text(x3 + 82, y_box + 46, "0.72", size=6.5, fill=RED, anchor="middle")

    f.text(x3 + 110, y_box + 50, "Lọc conf > 0.25", size=8.0, weight=700, fill=DARK)
    f.text(x3 + 110, y_box + 64, "và NMS IoU > 0.7", size=8.0, weight=700, fill=ORANGE)
    f.text(x3 + 110, y_box + 78, "Triệt tiêu các hộp", size=7.5, fill=GRAY)
    f.text(x3 + 110, y_box + 92, "dự đoán trùng lặp", size=7.5, fill=GRAY)

    arrow(f, x3 + 55, y_box + 110, x3 + 55, y_box + 128, color=ORANGE, sw=1.4)
    f.text(x3 + 65, y_box + 121, "Trừ padw/h & chia gain", size=7.4, fill=ORANGE)

    # Bước 2: Ảnh gốc hoàn chỉnh với 1 hộp duy nhất
    rect(f, x3 + 15, y_box + 134, 96, 56, fill="#E2E8F0", stroke=DARK, sw=1.2)
    circle(f, x3 + 60, y_box + 158, 7, fill="#94A3B8", stroke=DARK)
    f.line([(x3 + 60, y_box + 165), (x3 + 60, y_box + 180)], DARK, width=1.4, head=False)
    rect(f, x3 + 44, y_box + 148, 32, 38, fill="none", stroke=GREEN, sw=1.6)
    f.text(x3 + 60, y_box + 143, "person: 0.89", size=6.8, weight=700, fill=GREEN, anchor="middle")

    f.text(x3 + 120, y_box + 150, "Đầu ra cuối: (N, 6)", size=8.5, weight=700, fill=GREEN)
    f.text(x3 + 120, y_box + 166, "[x1, y1, x2, y2, conf, cls]", size=7.2, fill=DARK)
    f.text(x3 + 120, y_box + 180, "Tọa độ pixel gốc", size=7.5, fill=GRAY)

    f.text(x3 + 120, y_box + 218, "Hộp chuẩn xác trên ảnh ban đầu", size=7.5, fill=GRAY, anchor="middle")

    # --- KHUNG CALLOUT SO SÁNH PC VS BOARD ---
    box_y = 286
    box_h = 135
    rect(f, 15, box_y, 830, box_h, fill="#FAFAFA", stroke="#94A3B8", sw=1.2, rx=6)
    rect(f, 15, box_y, 830, 24, fill="#F1F5F9", stroke="#94A3B8", sw=1.2, rx=6)
    f.text(25, box_y + 16, "3 ĐIỂM KHÁC BIỆT CỐT TỬ GIỮA BOARD (RKNN NPU) VÀ PC (PYTORCH GPU)", size=9.5, weight=700, fill=DARK)

    card_w = 264
    # Card 1: Layout
    rect(f, 23, box_y + 32, card_w, 92, fill="#FFFFFF", stroke="#CBD5E1", sw=1, rx=4)
    f.text(32, box_y + 48, "1. Thứ tự trục (Tensor Layout)", size=8.8, weight=700, fill=BLUE)
    f.text(32, box_y + 65, "• PC PyTorch: NCHW float32 (1, 3, 640, 640)", size=8.2, fill=DARK)
    f.text(32, box_y + 80, "• Board RKNN: NHWC uint8 (1, 640, 640, 3)", size=8.2, fill=DARK)
    f.text(32, box_y + 96, "-> NPU tự đảo trục trong phần cứng, không tốn CPU.", size=7.8, fill=GRAY)
    f.text(32, box_y + 110, "   Tránh được overhead transpose của Python.", size=7.8, fill=GRAY)

    # Card 2: Chuẩn hóa chia 255
    rect(f, 297, box_y + 32, card_w, 92, fill="#FFFFFF", stroke="#CBD5E1", sw=1, rx=4)
    f.text(306, box_y + 48, "2. Vị trí phép chia 255 (Normalization)", size=8.8, weight=700, fill=RED)
    f.text(306, box_y + 65, "• PC: PyTorch forward chia float32 / 255.0", size=8.2, fill=DARK)
    f.text(306, box_y + 80, "• Board: Nung mean=0, std=255 vào file .rknn", size=8.2, fill=DARK)
    f.text(306, box_y + 96, "-> CẢNH BÁO: Board chia 255 trước sẽ bị chia 2 lần,", size=7.8, weight=700, fill=RED)
    f.text(306, box_y + 110, "   làm sai lệch hoàn toàn kết quả phát hiện!", size=7.8, weight=700, fill=RED)

    # Card 3: Thư viện
    rect(f, 571, box_y + 32, card_w, 92, fill="#FFFFFF", stroke="#CBD5E1", sw=1, rx=4)
    f.text(580, box_y + 48, "3. Môi trường thực thi (Dependencies)", size=8.8, weight=700, fill=GREEN)
    f.text(580, box_y + 65, "• PC: PyTorch, CUDA, Ultralytics engine (~4 GB)", size=8.2, fill=DARK)
    f.text(580, box_y + 80, "• Board: Thuần NumPy, OpenCV, RKNN C-API (<80 MB)", size=8.2, fill=DARK)
    f.text(580, box_y + 96, "-> Loại bỏ hoàn toàn overhead nặng nề của PyTorch,", size=7.8, fill=GRAY)
    f.text(580, box_y + 110, "   giảm thiểu RAM tiêu thụ, tối ưu tốc độ thời gian thực.", size=7.8, fill=GRAY)

    source(f, 412, "Nguồn: T3 ai/board/common.py:19-125, ai/core/backends.py:31; T1 ultralytics utils/export/rknn.py:74.")
    return f


# ==============================================================================
# 3. HÌNH BIẾN ĐỔI ĐỒ THỊ PYTORCH -> ONNX -> RKNN (hl-3)
# ==============================================================================
def fig_export_flow():
    H = 485
    f = Fig(W, H)
    tier(f, "T1 RK3588")
    f.text(12, 18, "Minh họa biến đổi đồ thị tính toán: PyTorch (.pt) -> Fuse Conv-BN -> ONNX -> Lượng tử hóa RKNN", size=13.5, weight=700, fill=DARK)

    # 4 Cột chặng biến đổi: w=180, gap=36px
    bw = 180
    bh = 230
    y_box = 42
    x1 = 15
    x2 = 231
    x3 = 447
    x4 = 663

    # --- CHẶNG 1: ĐỒ THỊ PYTORCH ĐỘNG ---
    rect(f, x1, y_box, bw, bh, fill="#FFFFFF", stroke=RED, sw=1.3, rx=5)
    rect(f, x1, y_box, bw, 28, fill="#FEE2E2", stroke=RED, sw=1.3, rx=5)
    f.text(x1 + bw / 2, y_box + 19, "1. PyTorch Model (.pt)", size=9.2, weight=700, fill=RED, anchor="middle")

    rect(f, x1 + 25, y_box + 36, 130, 22, fill="#F8FAFC", stroke=DARK, sw=1.2, rx=3)
    f.text(x1 + 90, y_box + 50, "Conv2d (W, b)", size=8.0, weight=700, fill=DARK, anchor="middle")

    arrow(f, x1 + 90, y_box + 58, x1 + 90, y_box + 74, color=DARK, sw=1.2)

    rect(f, x1 + 25, y_box + 74, 130, 22, fill="#FEE2E2", stroke=RED, sw=1.2, rx=3)
    f.text(x1 + 90, y_box + 88, "BatchNorm2d (γ,β,μ,σ²)", size=7.8, weight=700, fill=RED, anchor="middle")

    arrow(f, x1 + 90, y_box + 96, x1 + 90, y_box + 112, color=DARK, sw=1.2)

    circle(f, x1 + 90, y_box + 124, 14, fill="#E0F2FE", stroke=BLUE)
    f.text(x1 + 90, y_box + 128, "SiLU", size=7.5, weight=700, fill=BLUE, anchor="middle")

    # Khối RepConv đa nhánh
    rect(f, x1 + 12, y_box + 144, 156, 56, fill="#F8FAFC", stroke=GRAY, sw=1, dashed=True, rx=3)
    f.text(x1 + 90, y_box + 157, "RepConv Đa nhánh", size=7.6, weight=700, fill=DARK, anchor="middle")
    rect(f, x1 + 18, y_box + 164, 40, 20, fill="#FFFFFF", stroke=DARK, sw=1, rx=2)
    f.text(x1 + 38, y_box + 177, "3×3", size=7.2, fill=DARK, anchor="middle")
    rect(f, x1 + 70, y_box + 164, 40, 20, fill="#FFFFFF", stroke=DARK, sw=1, rx=2)
    f.text(x1 + 90, y_box + 177, "1×1", size=7.2, fill=DARK, anchor="middle")
    rect(f, x1 + 122, y_box + 164, 40, 20, fill="#FFFFFF", stroke=DARK, sw=1, rx=2)
    f.text(x1 + 142, y_box + 177, "Skip", size=7.2, fill=DARK, anchor="middle")

    f.text(x1 + 90, y_box + 218, "Nhiều node tách rời, tốn RAM DDR", size=7.2, weight=600, fill=RED, anchor="middle")

    # Mũi tên 1 -> 2: từ 195 đến 231 (dài 36px)
    arrow(f, x1 + bw + 4, y_box + bh / 2, x2 - 5, y_box + bh / 2, color=RED, sw=1.6)
    f.text((x1 + bw + x2) / 2, y_box + bh / 2 - 7, "eval()", size=7.5, weight=700, fill=RED, anchor="middle")

    # --- CHẶNG 2: GỘP CONV-BN VÀ TÁI THAM SỐ HOÁ ---
    rect(f, x2, y_box, bw, bh, fill="#FFFFFF", stroke=ORANGE, sw=1.3, rx=5)
    rect(f, x2, y_box, bw, 28, fill="#FEF3C7", stroke=ORANGE, sw=1.3, rx=5)
    f.text(x2 + bw / 2, y_box + 19, "2. Gộp Fuse & Reparam", size=9.2, weight=700, fill=ORANGE, anchor="middle")

    rect(f, x2 + 12, y_box + 36, 156, 88, fill="#FEF3C7", stroke=ORANGE, sw=1.2, rx=4)
    f.text(x2 + 90, y_box + 50, "Conv-BN Folding (fuse())", size=8.0, weight=700, fill=ORANGE, anchor="middle")
    f.text(x2 + 90, y_box + 66, "W_fused = W · (γ / σ)", size=8.0, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + 90, y_box + 82, "b_fused = (b - μ)·(γ/σ) + β", size=8.0, weight=700, fill=BLUE, anchor="middle")
    rect(f, x2 + 20, y_box + 92, 140, 24, fill="#DCFCE7", stroke=GREEN, sw=1, rx=3)
    f.text(x2 + 90, y_box + 107, "Xóa 100% lớp BatchNorm!", size=7.8, weight=700, fill=GREEN, anchor="middle")

    rect(f, x2 + 12, y_box + 134, 156, 64, fill="#F8FAFC", stroke=DARK, sw=1.2, rx=4)
    f.text(x2 + 90, y_box + 149, "Tái tham số hóa RepConv", size=7.8, weight=700, fill=DARK, anchor="middle")
    arrow(f, x2 + 90, y_box + 154, x2 + 90, y_box + 170, color=ORANGE, sw=1.3)
    rect(f, x2 + 30, y_box + 170, 120, 20, fill="#FFFFFF", stroke=GREEN, sw=1.2, rx=2)
    f.text(x2 + 90, y_box + 183, "1 Kernel 3×3 duy nhất", size=7.8, weight=700, fill=GREEN, anchor="middle")

    f.text(x2 + 90, y_box + 218, "Đồ thị phẳng, sẵn sàng xuất", size=7.2, weight=600, fill=ORANGE, anchor="middle")

    # Mũi tên 2 -> 3: từ 411 đến 447 (dài 36px)
    arrow(f, x2 + bw + 4, y_box + bh / 2, x3 - 5, y_box + bh / 2, color=ORANGE, sw=1.6)
    f.text((x2 + bw + x3) / 2, y_box + bh / 2 - 7, "export", size=7.5, weight=700, fill=ORANGE, anchor="middle")

    # --- CHẶNG 3: ĐỒ THỊ ONNX TĨNH ---
    rect(f, x3, y_box, bw, bh, fill="#FFFFFF", stroke=BLUE, sw=1.3, rx=5)
    rect(f, x3, y_box, bw, 28, fill="#DBEAFE", stroke=BLUE, sw=1.3, rx=5)
    f.text(x3 + bw / 2, y_box + 19, "3. Đồ thị ONNX (.onnx)", size=9.2, weight=700, fill=BLUE, anchor="middle")

    rect(f, x3 + 20, y_box + 36, 140, 22, fill="#F8FAFC", stroke=DARK, sw=1.2, rx=3)
    f.text(x3 + 90, y_box + 50, "Input (1, 3, 640, 640)", size=7.6, fill=DARK, anchor="middle")

    arrow(f, x3 + 90, y_box + 58, x3 + 90, y_box + 74, color=DARK, sw=1.2)

    rect(f, x3 + 16, y_box + 74, 148, 34, fill="#DCFCE7", stroke=GREEN, sw=1.3, rx=3)
    f.text(x3 + 90, y_box + 88, "Fused Conv (W_f, b_f)", size=8.0, weight=700, fill=GREEN, anchor="middle")
    f.text(x3 + 90, y_box + 101, "Conv + BN đã là 1 node duy nhất", size=6.8, fill=DARK, anchor="middle")

    arrow(f, x3 + 90, y_box + 108, x3 + 90, y_box + 124, color=DARK, sw=1.2)

    circle(f, x3 + 90, y_box + 134, 14, fill="#E0F2FE", stroke=BLUE)
    f.text(x3 + 90, y_box + 138, "SiLU", size=7.5, weight=700, fill=BLUE, anchor="middle")

    arrow(f, x3 + 90, y_box + 148, x3 + 90, y_box + 162, color=DARK, sw=1.2)

    rect(f, x3 + 20, y_box + 162, 140, 22, fill="#F8FAFC", stroke=DARK, sw=1.2, rx=3)
    f.text(x3 + 90, y_box + 176, "Detect Head (Static)", size=7.6, fill=DARK, anchor="middle")

    rect(f, x3 + 30, y_box + 190, 120, 20, fill="#DBEAFE", stroke=BLUE, sw=1, rx=3)
    f.text(x3 + 90, y_box + 203, "ONNX Opset 19", size=7.8, weight=700, fill=BLUE, anchor="middle")

    f.text(x3 + 90, y_box + 218, "Đồ thị tĩnh, chuẩn hóa toán tử", size=7.2, weight=600, fill=BLUE, anchor="middle")

    # Mũi tên 3 -> 4: từ 627 đến 663 (dài 36px)
    arrow(f, x3 + bw + 4, y_box + bh / 2, x4 - 5, y_box + bh / 2, color=BLUE, sw=1.6)
    f.text((x3 + bw + x4) / 2, y_box + bh / 2 - 7, "build", size=7.5, weight=700, fill=BLUE, anchor="middle")

    # --- CHẶNG 4: LƯỢNG TỬ HÓA VÀ BIÊN DỊCH RKNN ---
    rect(f, x4, y_box, bw, bh, fill="#FFFFFF", stroke=GREEN, sw=1.3, rx=5)
    rect(f, x4, y_box, bw, 28, fill="#DCFCE7", stroke=GREEN, sw=1.3, rx=5)
    f.text(x4 + bw / 2, y_box + 19, "4. NPU RKNN (.rknn)", size=9.2, weight=700, fill=GREEN, anchor="middle")

    rect(f, x4 + 12, y_box + 36, 156, 88, fill="#F0FDF4", stroke=GREEN, sw=1.2, rx=4)
    f.text(x4 + 90, y_box + 49, "Lượng tử hóa INT8 / FP16", size=7.8, weight=700, fill=GREEN, anchor="middle")

    f.text(x4 + 20, y_box + 64, "FP32:", size=7.2, fill=DARK)
    f.line([(x4 + 50, y_box + 63), (x4 + 150, y_box + 63)], BLUE, width=2.0, head=False)
    f.text(x4 + 100, y_box + 58, "Liên tục (float)", size=6.6, fill=BLUE, anchor="middle")

    arrow(f, x4 + 90, y_box + 67, x4 + 90, y_box + 85, color=DARK, sw=1.2)

    f.text(x4 + 20, y_box + 96, "INT8:", size=7.2, fill=DARK)
    for i in range(7):
        cx = x4 + 50 + i * 16
        circle(f, cx, y_box + 94, 3, fill=GREEN, stroke=GREEN)
    f.text(x4 + 100, y_box + 108, "256 mức [-128..127]", size=6.6, weight=700, fill=GREEN, anchor="middle")
    f.text(x4 + 100, y_box + 118, "q = round(x / S) + Z", size=6.8, weight=600, fill=DARK, anchor="middle")

    rect(f, x4 + 12, y_box + 132, 156, 40, fill="#FFFFFF", stroke=GRAY, sw=1, rx=3)
    f.text(x4 + 90, y_box + 146, "Chuẩn hóa nung trong model:", size=7.2, fill=DARK, anchor="middle")
    f.text(x4 + 90, y_box + 160, "mean=0, std=255", size=7.8, weight=700, fill=GREEN, anchor="middle")

    rect(f, x4 + 20, y_box + 180, 140, 20, fill="#DCFCE7", stroke=GREEN, sw=1, rx=3)
    f.text(x4 + 90, y_box + 193, "Target: rk3588 (3 Core)", size=7.8, weight=700, fill=GREEN, anchor="middle")

    f.text(x4 + 90, y_box + 218, "Nạp trực tiếp lên NPU Rock 5B", size=7.2, weight=600, fill=GREEN, anchor="middle")

    # --- KHUNG TÓM TẮT TẦM QUAN TRỌNG CỦA FUSE & EVAL ---
    box_y = 286
    box_h = 135
    rect(f, 15, box_y, 830, box_h, fill="#FAFAFA", stroke="#94A3B8", sw=1.2, rx=6)
    rect(f, 15, box_y, 830, 24, fill="#F1F5F9", stroke="#94A3B8", sw=1.2, rx=6)
    f.text(25, box_y + 16, "VÌ SAO BẮT BUỘC PHẢI CHUYỂN EVAL VÀ GỘP CONV-BN TRƯỚC KHI XUẤT NPU?", size=9.5, weight=700, fill=DARK)

    f.text(25, box_y + 42, "1. Triệt tiêu hoàn toàn chi phí bộ nhớ của BatchNorm:", size=9, weight=700, fill=BLUE)
    f.text(35, box_y + 57, "Trên phần cứng NPU, nếu giữ nguyên lớp BatchNorm độc lập, NPU phải ghi tensor kết quả của Conv ra RAM DDR rồi nạp lại để tính BN.", size=8.4, fill=DARK)
    f.text(35, box_y + 71, "Khi gộp (fuse) thành một phép affine duy nhất W_fused và b_fused, chi phí tính toán và độ trễ truy xuất bộ nhớ của BN giảm về đúng 0.", size=8.4, fill=DARK)

    f.text(25, box_y + 90, "2. Đảm bảo tính tất định và ổn định lượng tử hóa INT8:", size=9, weight=700, fill=GREEN)
    f.text(35, box_y + 105, "Ở chế độ eval(), thống kê BN cố định -> đồ thị phẳng hơn, dải giá trị kích hoạt ổn định, hạn chế tối đa sai số kẹp biên (clipping error)", size=8.4, fill=DARK)
    f.text(35, box_y + 119, "khi rknn-toolkit2 hiệu chuẩn lượng tử hóa 8-bit trên tập dữ liệu mẫu.", size=8.4, fill=DARK)

    source(f, 412, "Nguồn: T1 Ultralytics engine/exporter.py:859-863, nn/tasks.py:240-274; T3 ai/core/rknn/baseline.py:22-24.")
    return f


# ==============================================================================
# DANH MỤC CÁC HÌNH
# ==============================================================================
FIGS = [
    ("hl-1-ma-tran-eval-vs-nograd", fig_matrix_eval_nograd),
    ("hl-2-pipeline-suy-luan-rk3588", fig_pipeline_rk3588),
    ("hl-3-luong-xuat-model-pytorch-sang-rknn", fig_export_flow),
]

if __name__ == "__main__":
    run(FIGS, DEFAULT_OUTDIR)
