#!/usr/bin/env python3
"""Chuyên đề: Loss và backpropagation (05-loss-va-backpropagation.rst).

Sinh 6 hình minh họa kỹ thuật vector SVG chuẩn visual_guide:
  - bp-1-chu-trinh-huan-luyen-4-buoc (T2 chung):
    Vòng lặp khép kín 4 bước huấn luyện: Forward, Loss, Backward và Cập nhật tham số.
  - bp-2-co-che-mse-vs-cross-entropy (T2 chung):
    So sánh Squared Error (MSE) cho hồi quy và Cross-Entropy kèm Softmax cho phân loại.
  - bp-3-hinh-hoc-ho-loss-iou (T2 chung):
    Hình học và vùng phạt của 4 biến thể loss bounding box: IoU, GIoU, DIoU và CIoU.
  - bp-4-do-thi-tinh-toan-va-chain-rule-2-2-1 (T2 chung):
    Đồ thị tính toán số hai chiều Forward & Backward trên mạng 2-2-1 và nút chặn Dying ReLU.
  - bp-5-quy-dao-toi-uu-sgd-momentum-adam (T2 chung):
    Quỹ đạo hội tụ của SGD, Momentum và Adam trên mặt đẳng mức thung lũng (Ravine).
  - bp-6-learning-rate-va-scheduler (T2 chung):
    Tác động của Learning Rate và các đường cong Scheduler (Warmup, Cosine, Step Decay).

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 2 cấp: 05-loss-va-backpropagation -> 01-kien-thuc-nen -> figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "01-nen-tang-ai", "05-loss-va-backpropagation"
    )
)

W = 860
PURPLE = "#7B1FA2"
ORANGE = "#E65100"
GRID = "#E2E8F0"


def tier(f, label, x=W - 130, y=4):
    f.tier(x, y, label)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def seg(f, x1, y1, x2, y2, color=GRAY, sw=1.0, dashed=False):
    f.line([(x1, y1), (x2, y2)], color, width=sw, dashed=dashed, head=False)


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN):
    if color not in (BLUE, GREEN, RED, GRAY, INK):
        color = INK
    f.line([(x1, y1), (x2, y2)], color, width=sw, head=True)


# ==============================================================================
# 1. HÌNH CHU TRÌNH HUẤN LUYỆN 4 BƯỚC (bp-1)
# ==============================================================================
def fig_training_cycle():
    H = 345
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(12, 18, "Chu trình huấn luyện mạng nơ-ron 4 bước khép kín: Forward, Loss, Backward, Update", size=14, weight=700, fill=DARK)

    bw = 185
    bh = 110
    top_y = 42
    bot_y = 195

    # 4 Khối quy trình chính
    # B1: Forward (trên trái)
    rect(f, 15, top_y, bw, bh, fill="#F0F7FF", stroke=BLUE, sw=1.4, rx=6)
    f.badge(32, top_y + 18, "1", BLUE)
    f.text(48, top_y + 18, "Lan truyền xuôi (Forward)", size=10.5, weight=700, fill=BLUE)
    f.text(25, top_y + 40, "• Tính ŷ = f(x; θ) qua các tầng", size=8.8, fill=DARK)
    f.text(25, top_y + 57, "• Lưu trữ tensor kích hoạt z, h", size=8.8, fill=DARK)
    f.text(25, top_y + 74, "• Giữ bộ đệm trong bộ nhớ VRAM", size=8.8, fill=DARK)
    f.text(25, top_y + 91, "• Tốn bộ nhớ tỉ lệ thuận độ sâu", size=8.6, fill="#555555")

    # B2: Loss (trên phải)
    rect(f, 660, top_y, bw, bh, fill="#FFF9C4", stroke="#FBC02D", sw=1.4, rx=6)
    f.badge(677, top_y + 18, "2", ORANGE)
    f.text(693, top_y + 18, "Tính hàm mất mát (Loss)", size=10.5, weight=700, fill=ORANGE)
    f.text(670, top_y + 40, "• Đo sai lệch giữa ŷ và nhãn y", size=8.8, fill=DARK)
    f.text(670, top_y + 57, "• L = l(ŷ, y) (MSE / Cross-Entropy)", size=8.8, weight=600, fill=DARK)
    f.text(670, top_y + 74, "• L ≥ 0, tiến dần về 0 khi đúng", size=8.8, fill=DARK)
    f.text(670, top_y + 91, "• Điểm xuất phát của gradient", size=8.6, weight=700, fill=RED)

    # B3: Backward (dưới phải)
    rect(f, 660, bot_y, bw, bh, fill="#FFEBEE", stroke=RED, sw=1.4, rx=6)
    f.badge(677, bot_y + 18, "3", RED)
    f.text(693, bot_y + 18, "Lan truyền ngược (Backward)", size=10.5, weight=700, fill=RED)
    f.text(670, bot_y + 40, "• Quy tắc chuỗi (Chain Rule)", size=8.8, fill=DARK)
    f.text(670, bot_y + 57, "• Tính ∇_θ L = ∂L/∂θ theo từng lớp", size=8.8, weight=700, fill=RED)
    f.text(670, bot_y + 74, "• Tái sử dụng activations đã lưu", size=8.8, fill=DARK)
    f.text(670, bot_y + 91, "• Giải phóng bộ đệm forward", size=8.6, fill="#555555")

    # B4: Update (dưới trái)
    rect(f, 15, bot_y, bw, bh, fill="#E8F5E9", stroke=GREEN, sw=1.4, rx=6)
    f.badge(32, bot_y + 18, "4", GREEN)
    f.text(48, bot_y + 18, "Cập nhật tham số (Optimizer)", size=10.5, weight=700, fill=GREEN)
    f.text(25, bot_y + 40, "• Thuật toán: SGD, Momentum, Adam", size=8.8, fill=DARK)
    f.text(25, bot_y + 57, "• θ ← θ - η · Δθ (đi ngược dốc)", size=8.8, weight=700, fill=GREEN)
    f.text(25, bot_y + 74, "• Điều chỉnh tốc độ học qua Scheduler", size=8.8, fill=DARK)
    f.text(25, bot_y + 91, "• Chuẩn bị tham số cho bước sau", size=8.6, fill="#555555")

    # Mũi tên kết nối luồng
    # Mũi tên 1 -> 2: Forward đi ngang sang phải
    arrow(f, 15 + bw + 5, top_y + 55, 655, top_y + 55, BLUE, THICK)
    f.text(430, top_y + 40, "Luồng Tensor Forward (Giá trị kích hoạt ŷ, z, h)", size=10, weight=700, fill=BLUE, anchor="middle")

    # Mũi tên 2 -> 3: Loss đi thẳng xuống Backward
    arrow(f, 752, top_y + bh + 5, 752, bot_y - 5, RED, THICK)
    f.text(760, (top_y + bh + bot_y) / 2, "Khởi tạo ∂L/∂o", size=9.2, weight=700, fill=RED)

    # Mũi tên 3 -> 4: Backward đi ngang sang trái
    arrow(f, 655, bot_y + 55, 15 + bw + 5, bot_y + 55, RED, THICK)
    f.text(430, bot_y + 40, "Luồng Gradient Backward (Đạo hàm riêng ∂L/∂θ)", size=10, weight=700, fill=RED, anchor="middle")

    # Mũi tên 4 -> 1: Update quay ngược lên Forward
    arrow(f, 107, bot_y - 5, 107, top_y + bh + 5, GREEN, THICK)
    f.text(115, (top_y + bh + bot_y) / 2, "Trọng số mới θ*", size=9.2, weight=700, fill=GREEN)

    # Hộp trung tâm tóm tắt bản chất học
    cw = 380
    ch = 95
    rect(f, 240, 126, cw, ch, fill="#FAFAFA", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(240 + cw / 2, 142, "Bản chất toán học của quá trình học", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(255, 161, "• Hàm mục tiêu: Tìm θ* = argmin L(θ) trên tập dữ liệu.", size=9.0, fill=DARK)
    f.text(255, 178, "• Xung đột bộ nhớ: Backward cần giữ lại toàn bộ activations của", size=9.0, fill=DARK)
    f.text(255, 195, "  lượt Forward, làm bộ nhớ lúc huấn luyện gấp 3 - 5 lần lúc suy luận.", size=9.0, fill=DARK)
    f.text(255, 212, "• Đơn vị chu trình: 1 Minibatch = 1 bước lặp; 1 Epoch = quét hết dataset.", size=8.8, fill="#555555")

    source(f, 312, "Nguồn: Dive into Deep Learning (2023, Mục 3.1 & 5.3), Deep Learning (Goodfellow et al., 2016).")
    return f


# ==============================================================================
# 2. HÌNH MSE VS CROSS-ENTROPY (bp-2)
# ==============================================================================
def fig_mse_vs_cross_entropy():
    H = 345
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(12, 18, "So sánh cơ chế toán học hàm Loss: Squared Error (MSE) vs Cross-Entropy", size=14, weight=700, fill=DARK)

    pw = 410
    ph = 275

    # Panel A: Squared Error (Hồi quy)
    rect(f, 15, 34, pw, ph, fill="white", stroke="#333333", sw=1.2, rx=5)
    f.text(15 + pw / 2, 50, "Panel A: Squared Error (MSE) cho Hồi quy", size=11, weight=700, fill=DARK, anchor="middle")

    rect(f, 25, 65, 390, 52, fill="#F0F7FF", stroke=BLUE, sw=1.0, rx=4)
    f.text(35, 80, "Công thức: l(y, ŷ) = ½ (ŷ - y)²   |   Đạo hàm: ∂l/∂ŷ = ŷ - y", size=9.8, weight=700, fill=BLUE)
    f.text(35, 96, "• Đạo hàm tuyến tính theo độ lệch: Độ dốc kéo về tỷ lệ thuận với sai số.", size=8.8, fill=DARK)
    f.text(35, 110, "• Tương đương ước lượng hợp lý cực đại (MLE) khi nhiễu cộng tính Gaussian.", size=8.5, fill="#555555")

    # Khung đồ thị MSE Parabol
    gx_a = 30
    gy_a = 125
    gw_a = 380
    gh_a = 110
    rect(f, gx_a, gy_a, gw_a, gh_a, fill="#FCFDFD", stroke="#CFD8DC", sw=1.0, rx=3)

    ox_a = gx_a + gw_a / 2
    oy_a = gy_a + gh_a - 18
    seg(f, gx_a + 15, oy_a, gx_a + gw_a - 15, oy_a, "#90A4AE", 1.2)
    seg(f, ox_a, gy_a + 10, ox_a, oy_a + 10, "#90A4AE", 1.2)
    f.text(gx_a + gw_a - 15, oy_a - 6, "ŷ - y", size=9, fill="#546E7A", anchor="end")
    f.text(ox_a, gy_a + 8, "Loss", size=9, fill="#546E7A", anchor="middle")
    f.text(ox_a - 4, oy_a + 9, "0", size=8.5, fill="#78909C", anchor="end")

    # Vẽ parabol: y = a * x^2
    pts_parabol = []
    for step in range(-35, 36):
        dx = step * 4.2
        dy = (step / 35.0) ** 2 * 80
        pts_parabol.append((ox_a + dx, oy_a - dy))
    path_p = f"M {pts_parabol[0][0]:.1f} {pts_parabol[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_parabol[1:])
    f.a(f'<path d="{path_p}" fill="none" stroke="{BLUE}" stroke-width="2.4"/>')

    # Vẽ đường đạo hàm gạch đứt (tuyến tính): dy/dx = x, giới hạn trong khung
    seg(f, ox_a - 60, oy_a + 8, ox_a + 110, oy_a - 55, RED, 1.5, dashed=True)
    f.text(ox_a + 40, oy_a - 58, "Đạo hàm: ŷ - y", size=8.8, weight=700, fill=RED)
    f.text(ox_a - 90, gy_a + 22, "l = ½(ŷ - y)² (Parabol)", size=9.5, weight=700, fill=BLUE)

    rect(f, 25, 244, 390, 56, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(35, 258, "Đặc tính kỹ thuật:", size=9.2, weight=700, fill=DARK)
    f.text(35, 273, "• Khi sai số lớn (outliers): Loss tăng bậc hai, gradient cực đại kéo lệch model.", size=8.6, fill=DARK)
    f.text(35, 289, "• Khi gần điểm tối ưu: Đạo hàm tiến êm dịu về 0, không bị nhảy bước.", size=8.6, fill=DARK)

    # Panel B: Cross-Entropy (Phân loại)
    rect(f, 435, 34, pw, ph, fill="white", stroke="#333333", sw=1.2, rx=5)
    f.text(435 + pw / 2, 50, "Panel B: Cross-Entropy + Softmax cho Phân loại", size=11, weight=700, fill=DARK, anchor="middle")

    rect(f, 445, 65, 390, 52, fill="#FFF9C4", stroke="#FBC02D", sw=1.0, rx=4)
    f.text(455, 80, "Công thức: l = -log(ŷ_c)   |   Đạo hàm logit: ∂l/∂o_j = ŷ_j - y_j", size=9.8, weight=700, fill=ORANGE)
    f.text(455, 96, "• Đạo hàm theo logit cực kỳ trang nhã: Bằng xác suất dự đoán trừ nhãn One-hot.", size=8.8, fill=DARK)
    f.text(455, 110, "• Ghép Softmax + Cross-Entropy triệt tiêu số mũ, chống tràn số cực tốt.", size=8.5, fill="#555555")

    # Khung đồ thị -log(p)
    gx_b = 450
    gy_b = 125
    gw_b = 380
    gh_b = 110
    rect(f, gx_b, gy_b, gw_b, gh_b, fill="#FCFDFD", stroke="#CFD8DC", sw=1.0, rx=3)

    ox_b = gx_b + 40
    oy_b = gy_b + gh_b - 18
    seg(f, ox_b - 10, oy_b, gx_b + gw_b - 15, oy_b, "#90A4AE", 1.2)
    seg(f, ox_b, gy_b + 10, ox_b, oy_b + 10, "#90A4AE", 1.2)
    f.text(gx_b + gw_b - 15, oy_b - 6, "ŷ_c", size=9, fill="#546E7A", anchor="end")
    f.text(ox_b, gy_b + 8, "Loss", size=9, fill="#546E7A", anchor="middle")
    f.text(ox_b - 4, oy_b + 9, "0", size=8.5, fill="#78909C", anchor="end")

    # Mốc x=1.0 (xác suất 100%)
    sc_prob = 280
    x_1 = ox_b + sc_prob
    seg(f, x_1, gy_b + 10, x_1, oy_b, GRID, 1.0, dashed=True)
    f.text(x_1, oy_b + 9, "1.0", size=8.5, fill="#546E7A", anchor="middle")

    # Vẽ đường cong l = -log(p) từ p=0.04 đến p=1.0
    pts_ce = []
    for step in range(3, 101):
        p = step / 100.0
        val = -math.log(p)
        px = ox_b + p * sc_prob
        py = oy_b - min(85, val * 24)
        pts_ce.append((px, py))
    path_ce = f"M {pts_ce[0][0]:.1f} {pts_ce[0][1]:.1f} " + " ".join(f"L {pt[0]:.1f} {pt[1]:.1f}" for pt in pts_ce[1:])
    f.a(f'<path d="{path_ce}" fill="none" stroke="{ORANGE}" stroke-width="2.4"/>')

    f.text(ox_b + 80, gy_b + 22, "l = -log(ŷ_c) (Tiệm cận vô cùng)", size=9.5, weight=700, fill=ORANGE)
    arrow(f, ox_b + 65, gy_b + 42, ox_b + 25, gy_b + 25, RED, 1.1)
    f.text(ox_b + 70, gy_b + 46, "Phạt vô hạn nếu ŷ_c → 0!", size=8.5, weight=700, fill=RED)

    rect(f, 445, 244, 390, 56, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(455, 258, "Đặc tính kỹ thuật:", size=9.2, weight=700, fill=DARK)
    f.text(455, 273, "• Khi dự đoán sai tự tin (ŷ_c ≈ 0): Loss vọt lên vô hạn, gradient cực mạnh ép học lại.", size=8.6, fill=DARK)
    f.text(455, 289, "• Khi dự đoán chuẩn xác (ŷ_c ≈ 1.0): Loss triệt tiêu về 0, gradient ∂l/∂o tiệm cận 0.", size=8.6, fill=DARK)

    source(f, 312, "Nguồn: Dive into Deep Learning (2023, Mục 3.1 & 4.1), Deep Learning (Goodfellow et al., 2016).")
    return f


# ==============================================================================
# 3. HÌNH HỌ LOSS IOU CHO BBOX REGRESSION (bp-3)
# ==============================================================================
def fig_iou_loss_family():
    H = 345
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(12, 18, "Hình học các biến thể hàm mất mát Bounding Box trong Object Detection: Họ IoU", size=14, weight=700, fill=DARK)

    box_w = 200
    box_h = 275
    xs = [15, 225, 435, 645]

    # Panel 1: IoU Loss
    bx1 = xs[0]
    rect(f, bx1, 34, box_w, box_h, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(bx1 + box_w / 2, 48, "1. Standard IoU Loss", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(bx1 + box_w / 2, 63, "L_IoU = 1 - IoU", size=9.8, weight=700, fill=BLUE, anchor="middle")

    # Minh họa 2 box giao nhau
    gx1 = bx1 + 10
    gy1 = 74
    rect(f, gx1, gy1, 180, 88, fill="#F8FAFC", stroke="#CFD8DC", sw=1.0, rx=3)

    # Box A (dự đoán) và Box B (ground truth)
    rect(f, gx1 + 14, gy1 + 10, 68, 56, fill="#E3F2FD", stroke=BLUE, sw=1.4, rx=2)
    rect(f, gx1 + 54, gy1 + 24, 72, 54, fill="#E8F5E9", stroke=GREEN, sw=1.4, rx=2)

    # Vùng giao A ∩ B
    rect(f, gx1 + 54, gy1 + 24, 28, 42, fill="#FFE082", stroke="#E65100", sw=1.2, rx=1)
    f.text(gx1 + 68, gy1 + 48, "A ∩ B", size=8.5, weight=700, fill="#B71C1C", anchor="middle")
    f.text(gx1 + 20, gy1 + 26, "Box A", size=8.5, weight=600, fill=BLUE)
    f.text(gx1 + 78, gy1 + 70, "Box B (GT)", size=8.2, weight=600, fill=GREEN)

    rect(f, bx1 + 8, 168, box_w - 16, 132, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=3)
    f.text(bx1 + 14, 183, "Đặc tính toán học:", size=9.0, weight=700, fill=DARK)
    f.text(bx1 + 14, 199, "• IoU = |A ∩ B| / |A ∪ B|", size=8.5, weight=600, fill=BLUE)
    f.text(bx1 + 14, 215, "• Bất biến theo tỉ lệ hộp.", size=8.5, fill=DARK)
    f.text(bx1 + 14, 231, "• Giá trị: 0 ≤ IoU ≤ 1.0.", size=8.5, fill=DARK)
    f.text(bx1 + 14, 248, "Nhược điểm chí tử:", size=9.0, weight=700, fill=RED)
    f.text(bx1 + 14, 264, "• Khi A và B không giao nhau:", size=8.5, fill=DARK)
    f.text(bx1 + 14, 279, "  IoU = 0 => L_IoU = 1.0", size=8.5, weight=700, fill=RED)
    f.text(bx1 + 14, 294, "  ∇_θ = 0: Mất sạch gradient!", size=8.5, weight=700, fill=RED)

    # Panel 2: GIoU Loss
    bx2 = xs[1]
    rect(f, bx2, 34, box_w, box_h, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(bx2 + box_w / 2, 48, "2. Generalized IoU (GIoU)", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(bx2 + box_w / 2, 63, "L_GIoU = 1 - IoU + |C\\(A∪B)|/|C|", size=9.0, weight=700, fill=BLUE, anchor="middle")

    # Minh họa hộp bao nhỏ nhất C
    gx2 = bx2 + 10
    gy2 = 74
    # Hộp C bao quanh cả 2 box rời nhau
    rect(f, gx2, gy2, 180, 88, fill="#FFFDE7", stroke="#F57F17", sw=1.2, dashed=True, rx=3)
    f.text(gx2 + 8, gy2 + 13, "Hộp bao nhỏ nhất C", size=8.0, weight=700, fill="#E65100")

    # Box A và Box B rời nhau
    rect(f, gx2 + 10, gy2 + 22, 45, 46, fill="#E3F2FD", stroke=BLUE, sw=1.3, rx=2)
    f.text(gx2 + 32, gy2 + 49, "Box A", size=8.5, weight=600, fill=BLUE, anchor="middle")

    rect(f, gx2 + 125, gy2 + 32, 45, 46, fill="#E8F5E9", stroke=GREEN, sw=1.3, rx=2)
    f.text(gx2 + 147, gy2 + 59, "Box B", size=8.5, weight=600, fill=GREEN, anchor="middle")

    # Vùng trống ở giữa
    rect(f, gx2 + 60, gy2 + 26, 60, 44, fill="#FFF8E1", stroke="#FFA000", sw=0.8, rx=2)
    f.text(gx2 + 90, gy2 + 43, "Vùng trống", size=8.0, weight=700, fill="#D84315", anchor="middle")
    f.text(gx2 + 90, gy2 + 58, "|C \\ (A ∪ B)|", size=8.0, weight=700, fill="#D84315", anchor="middle")

    rect(f, bx2 + 8, 168, box_w - 16, 132, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=3)
    f.text(bx2 + 14, 183, "Đặc tính toán học:", size=9.0, weight=700, fill=DARK)
    f.text(bx2 + 14, 199, "• Phạt diện tích trống trong C.", size=8.5, fill=DARK)
    f.text(bx2 + 14, 215, "• Vẫn có gradient khi box rời nhau.", size=8.5, weight=700, fill=GREEN)
    f.text(bx2 + 14, 231, "• Khoảng giá trị: 0 ≤ L_GIoU ≤ 2.", size=8.5, fill=DARK)
    f.text(bx2 + 14, 248, "Hạn chế thực tế:", size=9.0, weight=700, fill=RED)
    f.text(bx2 + 14, 264, "• Khi một box bao trọn box kia,", size=8.5, fill=DARK)
    f.text(bx2 + 14, 279, "  phần trống = 0 => thoái hóa IoU.", size=8.5, fill=DARK)
    f.text(bx2 + 14, 294, "• Hội tụ chậm vì ưu tiên phình to.", size=8.5, fill="#555555")

    # Panel 3: DIoU Loss
    bx3 = xs[2]
    rect(f, bx3, 34, box_w, box_h, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(bx3 + box_w / 2, 48, "3. Distance-IoU (DIoU)", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(bx3 + box_w / 2, 63, "L_DIoU = 1 - IoU + ρ² / c²", size=9.8, weight=700, fill=BLUE, anchor="middle")

    # Minh họa khoảng cách tâm và đường chéo c
    gx3 = bx3 + 10
    gy3 = 74
    # Hộp C bao quanh (w=180, h=88)
    rect(f, gx3, gy3, 180, 88, fill="#F8FAFC", stroke="#78909C", sw=1.1, dashed=True, rx=3)

    # Box A ở góc trên bên trái: x=gx3+10, y=gy3+8, w=44, h=38
    cx_a = gx3 + 32
    cy_a = gy3 + 27
    rect(f, gx3 + 10, gy3 + 8, 44, 38, fill="#E3F2FD", stroke=BLUE, sw=1.3, rx=2)
    f.a(f'<circle cx="{cx_a}" cy="{cy_a}" r="2.5" fill="{BLUE}"/>')
    f.text(cx_a - 10, cy_a - 4, "b", size=8.5, weight=700, fill=BLUE, anchor="middle")

    # Box B ở góc dưới bên phải: x=gx3+126, y=gy3+42, w=44, h=38
    cx_b = gx3 + 148
    cy_b = gy3 + 61
    rect(f, gx3 + 126, gy3 + 42, 44, 38, fill="#E8F5E9", stroke=GREEN, sw=1.3, rx=2)
    f.a(f'<circle cx="{cx_b}" cy="{cy_b}" r="2.5" fill="{GREEN}"/>')
    f.text(cx_b, cy_b - 6, "b_gt", size=8.2, weight=700, fill=GREEN, anchor="middle")

    # Đoạn thẳng đỏ nối 2 tâm b và b_gt
    seg(f, cx_a, cy_a, cx_b, cy_b, RED, 1.6)

    # Nhãn khoảng cách tâm d = ρ đặt ở góc trên an toàn, không giao cắt đường chéo c
    rect(f, gx3 + 68, gy3 + 14, 52, 20, fill="white", stroke=RED, sw=0.8, rx=2)
    f.text(gx3 + 94, gy3 + 28, "d = ρ", size=8.5, weight=700, fill=RED, anchor="middle")

    # Đường chéo c của C: nối từ góc dưới-trái lên góc trên-phải
    seg(f, gx3 + 6, gy3 + 82, gx3 + 174, gy3 + 6, "#546E7A", 1.1, dashed=True)
    f.text(gx3 + 168, gy3 + 18, "c", size=9.0, weight=700, fill="#546E7A", anchor="end")

    rect(f, bx3 + 8, 168, box_w - 16, 132, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=3)
    f.text(bx3 + 14, 183, "Đặc tính toán học:", size=9.0, weight=700, fill=DARK)
    f.text(bx3 + 14, 199, "• Phạt chuẩn hóa khoảng cách tâm.", size=8.5, fill=DARK)
    f.text(bx3 + 14, 215, "• Kéo trực tiếp 2 tâm lại gần nhau.", size=8.5, weight=700, fill=GREEN)
    f.text(bx3 + 14, 231, "Ưu điểm vượt trội:", size=9.0, weight=700, fill=BLUE)
    f.text(bx3 + 14, 248, "• Tốc độ hội tụ nhanh hơn hẳn GIoU.", size=8.5, fill=DARK)
    f.text(bx3 + 14, 264, "• Dùng làm tiêu chí lọc DIoU-NMS.", size=8.5, fill=DARK)
    f.text(bx3 + 14, 279, "• Không phình to diện tích vô ích.", size=8.5, fill=DARK)
    f.text(bx3 + 14, 294, "• Chưa xét tới tỉ lệ khung hình w/h.", size=8.5, fill="#555555")

    # Panel 4: CIoU Loss
    bx4 = xs[3]
    rect(f, bx4, 34, box_w, box_h, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(bx4 + box_w / 2, 48, "4. Complete IoU (CIoU)", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(bx4 + box_w / 2, 63, "L_CIoU = L_DIoU + α · v", size=9.8, weight=700, fill=BLUE, anchor="middle")

    # Minh họa tỉ lệ cạnh w/h
    gx4 = bx4 + 10
    gy4 = 74
    rect(f, gx4, gy4, 180, 88, fill="#F8FAFC", stroke="#CFD8DC", sw=1.0, rx=3)

    # Box A: hẹp và cao
    rect(f, gx4 + 12, gy4 + 10, 42, 68, fill="#E3F2FD", stroke=BLUE, sw=1.4, rx=2)
    f.text(gx4 + 33, gy4 + 38, "w / h", size=8.5, weight=700, fill=BLUE, anchor="middle")
    f.text(gx4 + 33, gy4 + 54, "(Hẹp, cao)", size=7.8, fill="#555555", anchor="middle")

    # Box B: rộng và thấp
    rect(f, gx4 + 116, gy4 + 25, 54, 38, fill="#E8F5E9", stroke=GREEN, sw=1.4, rx=2)
    f.text(gx4 + 143, gy4 + 42, "w* / h*", size=8.5, weight=700, fill=GREEN, anchor="middle")
    f.text(gx4 + 143, gy4 + 54, "(Rộng, thấp)", size=7.8, fill="#555555", anchor="middle")

    # Biểu tượng so sánh lệch tỉ lệ ở giữa
    rect(f, gx4 + 62, gy4 + 24, 46, 40, fill="white", stroke="#EF9A9A", sw=1.0, rx=3)
    f.text(gx4 + 85, gy4 + 40, "≠", size=15, weight=700, fill=RED, anchor="middle")
    f.text(gx4 + 85, gy4 + 56, "+ α · v", size=8.5, weight=700, fill=RED, anchor="middle")

    rect(f, bx4 + 8, 168, box_w - 16, 132, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=3)
    f.text(bx4 + 14, 183, "Đặc tính 3 yếu tố hình học:", size=9.0, weight=700, fill=DARK)
    f.text(bx4 + 14, 199, "1. Diện tích chồng lấn (IoU)", size=8.5, fill=DARK)
    f.text(bx4 + 14, 215, "2. Khoảng cách tâm (ρ² / c²)", size=8.5, fill=DARK)
    f.text(bx4 + 14, 231, "3. Nhất quán tỉ lệ cạnh (α · v)", size=8.5, weight=700, fill=GREEN)
    f.text(bx4 + 14, 248, "Chuẩn mực hiện đại:", size=9.0, weight=700, fill=BLUE)
    f.text(bx4 + 14, 264, "• Hàm loss mặc định trong YOLOv8.", size=8.5, weight=700, fill=BLUE)
    f.text(bx4 + 14, 279, "• α ưu tiên overlap trước tỉ lệ.", size=8.5, fill=DARK)
    f.text(bx4 + 14, 294, "• Cân đối hoàn hảo vị trí & hình dáng.", size=8.5, fill=DARK)

    source(f, 312, "Nguồn: GIoU (Rezatofighi et al., CVPR 2019), DIoU/CIoU (Zheng et al., AAAI 2020), Ultralytics YOLO.")
    return f


# ==============================================================================
# 4. HÌNH ĐỒ THỊ TÍNH TOÁN VÀ CHAIN RULE MẠNG 2-2-1 (bp-4)
# ==============================================================================
def fig_chain_rule_2_2_1():
    H = 345
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(12, 18, "Đồ thị tính toán hai chiều Forward & Backward trên mạng 2-2-1 (Khớp 100% ví dụ số)", size=14, weight=700, fill=DARK)

    # Đồ thị tính toán 2 chiều:
    # Hàng trên: Các node Forward (từ trái qua phải)
    # Hàng dưới: Các hộp Gradient Backward (từ phải qua trái theo quy tắc chuỗi)

    # Header Forward và Backward
    f.text(430, 33, "LUỒNG FORWARD TÍNH ACTIVATIONS VÀ LOSS →", size=9.5, weight=700, fill=BLUE, anchor="middle")
    f.text(430, 154, "← LUỒNG BACKWARD QUY TẮC CHUỖI TÍNH GRADIENT", size=9.5, weight=700, fill=RED, anchor="middle")

    # 1. Node Input x
    x1, y1, w1, h1 = 15, 42, 115, 42
    rect(f, x1, y1, w1, h1, fill="#F0F7FF", stroke=BLUE, sw=1.2, rx=4)
    f.text(x1 + w1 / 2, y1 + 16, "Đầu vào x", size=9.0, weight=700, fill=BLUE, anchor="middle")
    f.text(x1 + w1 / 2, y1 + 32, "x = [1, 2]ᵀ", size=9.5, weight=700, fill=DARK, anchor="middle")

    # Node Trọng số W(1)
    xw1, yw1, ww1, hw1 = 15, 94, 115, 46
    rect(f, xw1, yw1, ww1, hw1, fill="#EDE7F6", stroke="#5E35B1", sw=1.2, rx=4)
    f.text(xw1 + ww1 / 2, yw1 + 16, "Trọng số W⁽¹⁾ (2×2)", size=8.5, weight=700, fill="#5E35B1", anchor="middle")
    f.text(xw1 + ww1 / 2, yw1 + 34, "[[1, -1], [0.5, 0.5]]", size=8.5, fill=DARK, anchor="middle")

    # 2. Node Tuyến tính z
    x2, y2, w2, h2 = 185, 62, 125, 60
    rect(f, x2, y2, w2, h2, fill="#E3F2FD", stroke=BLUE, sw=1.3, rx=4)
    f.text(x2 + w2 / 2, y2 + 16, "Tuyến tính z = W⁽¹⁾x", size=9.0, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + w2 / 2, y2 + 34, "z = [-1, 1.5]ᵀ", size=9.5, weight=700, fill=BLUE, anchor="middle")
    f.text(x2 + w2 / 2, y2 + 50, "z₁ = -1;  z₂ = 1.5", size=8.2, fill="#555555", anchor="middle")

    # Mũi tên Forward từ Cột 1 -> Cột 2
    arrow(f, x1 + w1, y1 + 21, x2, y2 + 18, BLUE, THICK)
    arrow(f, xw1 + ww1, yw1 + 23, x2, y2 + 42, "#5E35B1", THICK)

    # 3. Node Activation h và Trọng số W(2)
    x3, y3, w3, h3 = 365, 42, 125, 44
    rect(f, x3, y3, w3, h3, fill="#E8F5E9", stroke=GREEN, sw=1.3, rx=4)
    f.text(x3 + w3 / 2, y3 + 16, "Kích hoạt h = ReLU(z)", size=8.8, weight=700, fill=GREEN, anchor="middle")
    f.text(x3 + w3 / 2, y3 + 32, "h = [0, 1.5]ᵀ", size=9.5, weight=700, fill=GREEN, anchor="middle")

    xw2, yw2, ww2, hw2 = 365, 96, 125, 44
    rect(f, xw2, yw2, ww2, hw2, fill="#EDE7F6", stroke="#5E35B1", sw=1.2, rx=4)
    f.text(xw2 + ww2 / 2, yw2 + 16, "Trọng số W⁽²⁾ (1×2)", size=8.5, weight=700, fill="#5E35B1", anchor="middle")
    f.text(xw2 + ww2 / 2, yw2 + 32, "W⁽²⁾ = [1, 2]", size=9.0, weight=700, fill=DARK, anchor="middle")

    # Mũi tên Forward từ Cột 2 -> Cột 3 (một mũi tên duy nhất)
    arrow(f, x2 + w2, y2 + 18, x3, y3 + 22, BLUE, THICK)
    f.text(338, 54, "ReLU", size=8.0, weight=700, fill=BLUE, anchor="middle")

    # 4. Node Đầu ra o và Nhãn y
    x4, y4, w4, h4 = 545, 42, 125, 44
    rect(f, x4, y4, w4, h4, fill="#E3F2FD", stroke=BLUE, sw=1.3, rx=4)
    f.text(x4 + w4 / 2, y4 + 16, "Đầu ra mạng o = W⁽²⁾h", size=8.8, weight=700, fill=BLUE, anchor="middle")
    f.text(x4 + w4 / 2, y4 + 32, "o = 1·0 + 2·1.5 = 3.0", size=9.0, weight=700, fill=BLUE, anchor="middle")

    xy, yy, wy, hy = 545, 96, 125, 44
    rect(f, xy, yy, wy, hy, fill="#FFF3E0", stroke=ORANGE, sw=1.2, rx=4)
    f.text(xy + wy / 2, yy + 16, "Nhãn đích y", size=8.8, weight=700, fill=ORANGE, anchor="middle")
    f.text(xy + wy / 2, yy + 32, "y = 1.0", size=9.0, weight=700, fill=DARK, anchor="middle")

    # Mũi tên Forward từ Cột 3 -> Cột 4
    arrow(f, x3 + w3, y3 + 22, x4, y4 + 18, GREEN, THICK)
    arrow(f, xw2 + ww2, yw2 + 22, x4, y4 + 32, "#5E35B1", THICK)

    # 5. Node Loss L
    x5, y5, w5, h5 = 715, 52, 130, 78
    rect(f, x5, y5, w5, h5, fill="#FFF9C4", stroke="#FBC02D", sw=1.5, rx=5)
    f.text(x5 + w5 / 2, y5 + 18, "Hàm Loss L(o, y)", size=9.5, weight=700, fill=ORANGE, anchor="middle")
    f.text(x5 + w5 / 2, y5 + 38, "L = ½(o - y)²", size=10.5, weight=700, fill=RED, anchor="middle")
    f.text(x5 + w5 / 2, y5 + 56, "= ½(3 - 1)² = 2.0", size=10, weight=700, fill=DARK, anchor="middle")
    f.text(x5 + w5 / 2, y5 + 70, "Điểm bắt đầu backward", size=7.8, fill="#78909C", anchor="middle")

    # Mũi tên Forward từ Cột 4 -> Cột 5
    arrow(f, x4 + w4, y4 + 22, x5, y5 + 24, BLUE, THICK)
    arrow(f, xy + wy, yy + 22, x5, y5 + 54, ORANGE, THICK)

    # HÀNG DƯỚI: CÁC BƯỚC GRADIENT BACKWARD
    y_bg = 166
    h_bg = 74

    # Bước 1: dL/do (ở Cột 5)
    xb1 = 715
    rect(f, xb1, y_bg, 130, h_bg, fill="#FFEBEE", stroke=RED, sw=1.2, rx=4)
    f.text(xb1 + 65, y_bg + 15, "1. Đạo hàm Loss", size=8.8, weight=700, fill=RED, anchor="middle")
    f.text(xb1 + 65, y_bg + 32, "∂L/∂o = o - y", size=9.2, weight=700, fill=DARK, anchor="middle")
    f.text(xb1 + 65, y_bg + 48, "= 3 - 1 = 2.0", size=10, weight=700, fill=RED, anchor="middle")
    f.text(xb1 + 65, y_bg + 64, "Độ dốc tại ngõ ra", size=7.8, fill="#555555", anchor="middle")

    # Mũi tên đỏ từ Loss xuống Bước 1
    arrow(f, x5 + w5 / 2, y5 + h5, xb1 + 65, y_bg, RED, THICK)

    # Bước 2: dL/dW(2) & dL/dh (ở Cột 4)
    xb2 = 515
    wb2 = 155
    rect(f, xb2, y_bg, wb2, h_bg, fill="#FFEBEE", stroke=RED, sw=1.2, rx=4)
    f.text(xb2 + wb2 / 2, y_bg + 15, "2. Phân nhánh tại o", size=8.8, weight=700, fill=RED, anchor="middle")
    f.text(xb2 + wb2 / 2, y_bg + 31, "∂L/∂W⁽²⁾ = (∂L/∂o) hᵀ = [0, 3]", size=8.5, weight=700, fill=DARK, anchor="middle")
    f.text(xb2 + wb2 / 2, y_bg + 47, "∂L/∂h = W⁽²⁾ᵀ(∂L/∂o) = [2, 4]ᵀ", size=8.5, weight=700, fill=RED, anchor="middle")
    f.text(xb2 + wb2 / 2, y_bg + 64, "(2 · [0, 1.5] và [1, 2]ᵀ · 2)", size=7.8, fill="#555555", anchor="middle")

    # Mũi tên đỏ từ Bước 1 sang Bước 2
    arrow(f, xb1, y_bg + 37, xb2 + wb2, y_bg + 37, RED, THICK)

    # Bước 3: dL/dz với Nút chặn Dying ReLU (ở Cột 3)
    xb3 = 310
    wb3 = 165
    rect(f, xb3, y_bg, wb3, h_bg, fill="#FFCDD2", stroke="#B71C1C", sw=1.6, rx=4)
    f.text(xb3 + wb3 / 2, y_bg + 15, "3. Nút chặn Dying ReLU", size=9.0, weight=700, fill="#B71C1C", anchor="middle")
    f.text(xb3 + wb3 / 2, y_bg + 31, "∂L/∂z = (∂L/∂h) ⊙ ReLU'(z)", size=8.5, weight=700, fill=RED, anchor="middle")
    f.text(xb3 + wb3 / 2, y_bg + 47, "= [2·0, 4·1]ᵀ = [0, 4]ᵀ", size=9.5, weight=700, fill=DARK, anchor="middle")
    f.text(xb3 + wb3 / 2, y_bg + 64, "z₁ = -1 < 0 => ReLU'(-1) = 0!", size=8.2, weight=700, fill="#B71C1C", anchor="middle")

    # Mũi tên đỏ từ Bước 2 sang Bước 3
    arrow(f, xb2, y_bg + 37, xb3 + wb3, y_bg + 37, RED, THICK)

    # Bước 4: dL/dW(1) (ở Cột 1-2)
    xb4 = 15
    wb4 = 255
    rect(f, xb4, y_bg, wb4, h_bg, fill="#FFEBEE", stroke=RED, sw=1.2, rx=4)
    f.text(xb4 + wb4 / 2, y_bg + 15, "4. Gradient cập nhật trọng số Lớp 1", size=9.0, weight=700, fill=RED, anchor="middle")
    f.text(xb4 + wb4 / 2, y_bg + 31, "∂L/∂W⁽¹⁾ = (∂L/∂z) xᵀ = [0, 4]ᵀ [1, 2] = [[0, 0], [4, 8]]", size=8.6, weight=700, fill=DARK, anchor="middle")
    f.text(xb4 + wb4 / 2, y_bg + 47, "• Dòng 1 hoàn toàn bằng 0 do z₁ bị ReLU dập tắt!", size=8.0, weight=700, fill="#B71C1C", anchor="middle")
    f.text(xb4 + wb4 / 2, y_bg + 63, "• Dòng 2 nhận gradient [4, 8] để kéo sai số về 0.", size=8.0, fill="#2E7D32", anchor="middle")

    # Mũi tên đỏ từ Bước 3 sang Bước 4
    arrow(f, xb3, y_bg + 37, xb4 + wb4, y_bg + 37, RED, THICK)

    # KHUNG KẾT QUẢ CẬP NHẬT SGD Ở ĐÁY (2 CỘT RÕ RÀNG)
    rect(f, 15, 250, 830, 56, fill="#E8F5E9", stroke=GREEN, sw=1.2, rx=4)

    # Cột 1: Cập nhật trọng số
    f.text(25, 266, "Cập nhật trọng số SGD (η = 0.05):", size=9.2, weight=700, fill=GREEN)
    f.text(25, 282, "• W⁽²⁾ mới = [1, 2] - 0.05 · [0, 3] = [1, 1.85]", size=8.5, fill=DARK)
    f.text(25, 297, "• W⁽¹⁾ mới = W⁽¹⁾ - 0.05 · [[0, 0], [4, 8]] = [[1, -1], [0.3, 0.1]]", size=8.5, fill=DARK)

    # Cột 2: Kiểm chứng Forward lại
    f.text(465, 266, "Kỳ diệu của Gradient Descent (Forward lại):", size=9.2, weight=700, fill=BLUE)
    f.text(465, 282, "• z mới = [-1, 0.5]ᵀ  =>  h mới = [0, 0.5]ᵀ  =>  o mới = 0.925", size=8.5, fill=DARK)
    f.text(465, 297, "• Loss mới: L = ½(0.925 - 1)² ≈ 0.0028  (Giảm 99.86% sai số!)", size=8.6, weight=700, fill=GREEN)

    source(f, 316, "Nguồn: Dive into Deep Learning (2023, Mục 5.3), Tự tính toán số học đối chiếu PyTorch autograd 2.4.0.")
    return f


# ==============================================================================
# 5. HÌNH QUỸ ĐẠO TỐI ƯU HÓA: SGD, MOMENTUM, ADAM (bp-5)
# ==============================================================================
def fig_optimizers_trajectory():
    H = 345
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(12, 18, "Quỹ đạo tối ưu hóa trong không gian hàm mất mát thung lũng (Ravine): SGD, Momentum, Adam", size=14, weight=700, fill=DARK)

    # Khung biểu đồ Contour bên trái (chiếm 480px)
    gw = 480
    gh = 270
    rect(f, 15, 36, gw, gh, fill="#FCFDFD", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(25, 52, "Không gian tham số Loss Surface dạng thung lũng hẹp", size=10.5, weight=700, fill=DARK)

    ox = 15 + gw / 2 + 10
    oy = 36 + gh / 2

    # Vẽ các elip đồng mức thể hiện thung lũng (trục x thoải, trục y dốc, nằm gọn trong khung)
    for a, b in [(185, 95), (145, 72), (105, 48), (68, 28), (32, 13)]:
        f.a(f'<ellipse cx="{ox}" cy="{oy}" rx="{a}" ry="{b}" fill="none" stroke="#CFD8DC" stroke-width="1.2"/>')

    # Điểm cực tiểu toàn cục
    f.a(f'<circle cx="{ox}" cy="{oy}" r="3.5" fill="{GREEN}"/>')
    f.text(ox + 8, oy - 6, "θ* (Cực tiểu)", size=9.0, weight=700, fill=GREEN)

    start_x = ox - 165
    start_y = oy - 80
    f.a(f'<circle cx="{start_x}" cy="{start_y}" r="3.5" fill="{DARK}"/>')
    f.text(start_x - 8, start_y - 6, "Khởi tạo θ₀", size=9.0, weight=700, fill=DARK, anchor="end")

    # 1. Đường quỹ đạo SGD thuần: Dao động zigzag cực mạnh, tiến rất chậm
    pts_sgd = [
        (start_x, start_y),
        (start_x + 22, oy + 72),
        (start_x + 44, oy - 60),
        (start_x + 66, oy + 48),
        (start_x + 88, oy - 38),
        (start_x + 108, oy + 28),
        (start_x + 125, oy - 18),
        (start_x + 138, oy + 12),
    ]
    path_sgd = f"M {pts_sgd[0][0]} {pts_sgd[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in pts_sgd[1:])
    f.a(f'<path d="{path_sgd}" fill="none" stroke="{RED}" stroke-width="1.8" stroke-dasharray="4 3"/>')

    # 2. Đường Momentum: Triệt tiêu dao động, tích lũy vận tốc lướt dọc đáy
    pts_mom = [
        (start_x, start_y),
        (start_x + 30, oy + 38),
        (start_x + 70, oy - 12),
        (start_x + 115, oy + 6),
        (start_x + 150, oy - 2),
        (ox - 5, oy),
    ]
    path_mom = f"M {pts_mom[0][0]} {pts_mom[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in pts_mom[1:])
    f.a(f'<path d="{path_mom}" fill="none" stroke="{BLUE}" stroke-width="2.4"/>')

    # 3. Đường Adam: Điều chỉnh bước nhảy theo từng trục, tiến thẳng
    pts_adam = [
        (start_x, start_y),
        (start_x + 48, oy - 35),
        (start_x + 100, oy - 12),
        (start_x + 140, oy - 3),
        (ox, oy),
    ]
    path_adam = f"M {pts_adam[0][0]} {pts_adam[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in pts_adam[1:])
    f.a(f'<path d="{path_adam}" fill="none" stroke="{GREEN}" stroke-width="2.6"/>')

    # Nhãn quỹ đạo (vẽ sau các đường và không chồng đè nhau)
    rect(f, start_x + 65, oy - 2, 85, 15, fill="#FCFDFD", stroke="none")
    f.text(start_x + 68, oy + 9, "Momentum", size=9.0, weight=700, fill=BLUE)

    rect(f, start_x + 55, oy - 55, 115, 15, fill="#FCFDFD", stroke="none")
    f.text(start_x + 58, oy - 43, "Adam (Thẳng & nhanh)", size=9.0, weight=700, fill=GREEN)

    f.text(pts_sgd[-1][0] + 5, pts_sgd[-1][1], "SGD (Zigzag)", size=9.0, weight=700, fill=RED)

    # Chú thích trục độ dốc
    arrow(f, ox - 160, oy + 70, ox - 160, oy + 115, "#78909C", 1.0)
    f.text(ox - 155, oy + 105, "Độ dốc lớn (sườn núi)", size=8.0, fill="#546E7A")
    arrow(f, ox + 20, oy + 100, ox + 90, oy + 100, "#78909C", 1.0)
    f.text(ox + 30, oy + 112, "Độ dốc thoải (đáy thung lũng)", size=8.0, fill="#546E7A")

    # Bảng phân tích 3 bộ tối ưu bên phải (chiếm 340px)
    rx = 510
    rw = 335

    # Card SGD
    rect(f, rx, 36, rw, 78, fill="#FFEBEE", stroke=RED, sw=1.1, rx=4)
    f.text(rx + 12, 50, "1. Stochastic Gradient Descent (SGD)", size=10, weight=700, fill=RED)
    f.text(rx + 12, 66, "• Quy tắc: θ ← θ - η · gₜ", size=8.8, weight=600, fill=DARK)
    f.text(rx + 12, 82, "• Nhược điểm: Bị chi phối bởi độ dốc tức thời. Trong thung lũng,", size=8.5, fill=DARK)
    f.text(rx + 12, 97, "  SGD nảy qua lại giữa 2 vách, tiến dọc đáy cực kỳ chậm.", size=8.5, fill=DARK)

    # Card Momentum
    rect(f, rx, 122, rw, 85, fill="#F0F7FF", stroke=BLUE, sw=1.1, rx=4)
    f.text(rx + 12, 136, "2. SGD kèm Momentum (Xung lượng)", size=10, weight=700, fill=BLUE)
    f.text(rx + 12, 152, "• Vận tốc: vₜ ← β · vₜ₋₁ + gₜ  |  θ ← θ - η · vₜ", size=8.8, weight=600, fill=BLUE)
    f.text(rx + 12, 169, "• Cơ chế: Trung bình trượt (EMA) làm triệt tiêu các thành phần", size=8.5, fill=DARK)
    f.text(rx + 12, 185, "  dao động đổi dấu liên tục, cộng dồn vận tốc theo hướng đáy.", size=8.5, fill=DARK)
    f.text(rx + 12, 200, "• Tăng tốc hội tụ rõ rệt trong các mạng CNN sâu.", size=8.5, weight=700, fill=BLUE)

    # Card Adam
    rect(f, rx, 215, rw, 91, fill="#E8F5E9", stroke=GREEN, sw=1.1, rx=4)
    f.text(rx + 12, 229, "3. Adam (Adaptive Moment Estimation)", size=10, weight=700, fill=GREEN)
    f.text(rx + 12, 245, "• Bậc 1: vₜ (hướng đi)  |  Bậc 2: sₜ (bình phương gradient)", size=8.8, weight=600, fill=GREEN)
    f.text(rx + 12, 262, "• Hiệu chỉnh bước: θ ← θ - η · v̂ₜ / (√ŝₜ + ε)", size=8.8, weight=600, fill=DARK)
    f.text(rx + 12, 278, "• Ưu điểm độc tôn: Tự động co bước ở chiều dốc mạnh và tăng", size=8.5, fill=DARK)
    f.text(rx + 12, 294, "  bước ở chiều dốc thoải, hội tụ ổn định gần như độc lập với scale.", size=8.5, fill=DARK)

    source(f, 312, "Nguồn: Dive into Deep Learning (2023, Mục 12.4, 12.6 & 12.10), Adam (Kingma & Ba, ICLR 2015).")
    return f


# ==============================================================================
# 6. HÌNH LEARNING RATE VÀ SCHEDULER (bp-6)
# ==============================================================================
def fig_learning_rate_and_schedulers():
    H = 345
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(12, 18, "Ảnh hưởng của Learning Rate và các chiến lược điều chỉnh (Schedulers)", size=14, weight=700, fill=DARK)

    pw = 410
    ph = 275

    # Panel A: Tác động của Learning Rate η
    rect(f, 15, 34, pw, ph, fill="white", stroke="#333333", sw=1.2, rx=5)
    f.text(15 + pw / 2, 50, "Panel A: 3 tình huống lựa chọn Learning Rate (η)", size=11, weight=700, fill=DARK, anchor="middle")

    # Khung đồ thị 3 đường loss theo thời gian
    gx_a = 28
    gy_a = 66
    gw_a = 384
    gh_a = 150
    rect(f, gx_a, gy_a, gw_a, gh_a, fill="#FCFDFD", stroke="#CFD8DC", sw=1.0, rx=3)

    ox_a = gx_a + 30
    oy_a = gy_a + gh_a - 18
    seg(f, ox_a, oy_a, gx_a + gw_a - 15, oy_a, "#90A4AE", 1.2)
    seg(f, ox_a, gy_a + 12, ox_a, oy_a + 6, "#90A4AE", 1.2)
    f.text(gx_a + gw_a - 15, oy_a + 12, "Số bước lặp (Steps)", size=8.8, fill="#546E7A", anchor="end")
    f.text(ox_a, gy_a + 8, "Loss", size=8.8, fill="#546E7A", anchor="middle")

    # Đường 1: η quá lớn (Đỏ) - Nhảy vọt, phân kỳ
    pts_high = [(ox_a, oy_a - 75), (ox_a + 25, oy_a - 90), (ox_a + 55, oy_a - 55), (ox_a + 85, oy_a - 110), (ox_a + 115, oy_a - 35), (ox_a + 145, oy_a - 120)]
    path_high = f"M {pts_high[0][0]} {pts_high[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in pts_high[1:])
    f.a(f'<path d="{path_high}" fill="none" stroke="{RED}" stroke-width="2.0"/>')
    f.text(pts_high[-1][0] + 6, pts_high[-1][1], "η quá lớn (Phân kỳ / Vọt lố)", size=8.5, weight=700, fill=RED)

    # Đường 2: η quá nhỏ (Xám) - Giảm li ti, hội tụ cực chậm
    pts_low = [(ox_a, oy_a - 80)]
    for i in range(1, 11):
        pts_low.append((ox_a + i * 18, oy_a - 80 + i * 2.8))
    path_low = f"M {pts_low[0][0]} {pts_low[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in pts_low[1:])
    f.a(f'<path d="{path_low}" fill="none" stroke="{GRAY}" stroke-width="1.8" stroke-dasharray="4 3"/>')
    f.text(pts_low[-1][0] + 6, pts_low[-1][1], "η quá nhỏ (Hội tụ rùa bò)", size=8.5, fill=GRAY)

    # Đường 3: η tối ưu (Xanh lá) - Giảm mượt mà và hội tụ sâu
    pts_opt = [(ox_a, oy_a - 80)]
    for i in range(1, 11):
        val = 80 * math.exp(-i * 0.35)
        pts_opt.append((ox_a + i * 18, oy_a - val))
    path_opt = f"M {pts_opt[0][0]} {pts_opt[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in pts_opt[1:])
    f.a(f'<path d="{path_opt}" fill="none" stroke="{GREEN}" stroke-width="2.4"/>')
    f.text(pts_opt[-1][0] + 6, pts_opt[-1][1] - 4, "η tối ưu (Hội tụ mượt)", size=9.0, weight=700, fill=GREEN)

    rect(f, 25, 224, 390, 75, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(35, 239, "Nguyên lý toán học:", size=9.2, weight=700, fill=DARK)
    f.text(35, 254, "• Khai triển Taylor: f(x - η∇f) ≈ f(x) - η||∇f||² chỉ đúng khi bước η nhỏ.", size=8.5, fill=DARK)
    f.text(35, 270, "• Nếu η quá lớn: Vượt quá bán kính xấp xỉ bậc 1, loss bật nảy phân kỳ.", size=8.5, fill=DARK)
    f.text(35, 286, "• Giải pháp: Dùng Learning Rate Scheduler điều chỉnh η linh hoạt.", size=8.5, weight=700, fill=BLUE)

    # Panel B: Các đường cong Scheduler theo Epoch
    rect(f, 435, 34, pw, ph, fill="white", stroke="#333333", sw=1.2, rx=5)
    f.text(435 + pw / 2, 50, "Panel B: Các chiến lược Scheduler hiện đại", size=11, weight=700, fill=DARK, anchor="middle")

    # Khung đồ thị Schedulers
    gx_b = 448
    gy_b = 66
    gw_b = 384
    gh_b = 150
    rect(f, gx_b, gy_b, gw_b, gh_b, fill="#FCFDFD", stroke="#CFD8DC", sw=1.0, rx=3)

    ox_b = gx_b + 30
    oy_b = gy_b + gh_b - 18
    seg(f, ox_b, oy_b, gx_b + gw_b - 15, oy_b, "#90A4AE", 1.2)
    seg(f, ox_b, gy_b + 12, ox_b, oy_b + 6, "#90A4AE", 1.2)
    f.text(gx_b + gw_b - 15, oy_b + 12, "Epochs", size=8.8, fill="#546E7A", anchor="end")
    f.text(gx_b + 10, gy_b + 8, "Learning Rate η", size=8.8, fill="#546E7A")

    max_h = 100
    # 1. Step Decay (Đỏ nét đứt): Giảm giật cấp tại milestone
    pts_step = [
        (ox_b, oy_b - max_h),
        (ox_b + 100, oy_b - max_h),
        (ox_b + 100, oy_b - max_h * 0.5),
        (ox_b + 200, oy_b - max_h * 0.5),
        (ox_b + 200, oy_b - max_h * 0.25),
        (ox_b + 310, oy_b - max_h * 0.25),
    ]
    path_step = f"M {pts_step[0][0]} {pts_step[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in pts_step[1:])
    f.a(f'<path d="{path_step}" fill="none" stroke="{RED}" stroke-width="1.8" stroke-dasharray="4 3"/>')
    f.text(ox_b + 210, oy_b - max_h * 0.55, "Step Decay (Giảm theo bậc)", size=8.5, weight=700, fill=RED)

    # 2. Warmup + Cosine Annealing (Xanh dương nét liền) - Chuẩn trong YOLO
    warm_x = 45
    pts_cos = [(ox_b, oy_b - max_h * 0.05)]
    # Warmup tăng tuyến tính
    pts_cos.append((ox_b + warm_x, oy_b - max_h))
    # Cosine suy giảm êm
    tot_steps = 300 - warm_x
    for i in range(1, 31):
        ratio = i / 30.0
        # Cosine từ 1 về 0.05
        cos_val = 0.05 + 0.95 * 0.5 * (1 + math.cos(math.pi * ratio))
        pts_cos.append((ox_b + warm_x + ratio * tot_steps, oy_b - max_h * cos_val))
    path_cos = f"M {pts_cos[0][0]:.1f} {pts_cos[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_cos[1:])
    f.a(f'<path d="{path_cos}" fill="none" stroke="{BLUE}" stroke-width="2.5"/>')
    f.text(ox_b + 115, oy_b - max_h * 0.88, "Warmup + Cosine Annealing", size=9.0, weight=700, fill=BLUE)

    # Vùng Warmup
    f.a(f'<rect x="{ox_b}" y="{gy_b + 12}" width="{warm_x}" height="{gh_b - 30}" fill="{BLUE}" fill-opacity="0.1"/>')
    f.text(ox_b + warm_x / 2, oy_b - 12, "Warmup", size=8.0, weight=700, fill=BLUE, anchor="middle")

    rect(f, 445, 224, 390, 75, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(455, 239, "Chiến lược Warmup + Cosine (Khuyến nghị trong YOLO):", size=9.2, weight=700, fill=DARK)
    f.text(455, 254, "• Warmup: Tăng dần η ở 3 - 5 epoch đầu để ổn định trọng số, tránh sốc gradient.", size=8.5, fill=DARK)
    f.text(455, 270, "• Cosine Decay: Giảm mượt mà không gây sốc, giữ độ dốc vừa đủ ở pha cuối.", size=8.5, fill=DARK)
    f.text(455, 286, "• Giúp mô hình chạm tới cực tiểu sắc nét hơn hẳn Step Decay.", size=8.5, weight=700, fill=BLUE)

    source(f, 312, "Nguồn: Dive into Deep Learning (2023, Mục 12.11), SGDR: Cosine Annealing (Loshchilov & Hutter, ICLR 2017).")
    return f


FIGS = [
    ("bp-1-chu-trinh-huan-luyen-4-buoc", fig_training_cycle),
    ("bp-2-co-che-mse-vs-cross-entropy", fig_mse_vs_cross_entropy),
    ("bp-3-hinh-hoc-ho-loss-iou", fig_iou_loss_family),
    ("bp-4-do-thi-tinh-toan-va-chain-rule-2-2-1", fig_chain_rule_2_2_1),
    ("bp-5-quy-dao-toi-uu-sgd-momentum-adam", fig_optimizers_trajectory),
    ("bp-6-learning-rate-va-scheduler", fig_learning_rate_and_schedulers),
]


if __name__ == "__main__":
    run(FIGS, DEFAULT_OUTDIR)
