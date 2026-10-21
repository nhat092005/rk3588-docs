#!/usr/bin/env python3
"""Chuyên đề: Chuẩn hóa và activation (04-chuan-hoa-va-activation.rst).

Sinh 8 hình minh họa kỹ thuật SVG riêng biệt, sắc nét, không khoảng trắng thừa:
  - act-1-relu (T2 chung): Đồ thị ReLU và đạo hàm, card lý thuyết và callout rõ ràng
  - act-2-leaky-relu (T2 chung): Đồ thị LeakyReLU (alpha=0.1), so sánh với ReLU và giữ dòng gradient
  - act-3-sigmoid-va-tanh (T2 chung): 2 panel riêng biệt so sánh Sigmoid và Tanh, không chồng lấn
  - act-4-silu (T2 chung): Đồ thị SiLU (Swish-1) và đạo hàm, thung lũng cực tiểu x ≈ -1.28 và tiệm cận y=x
  - act-5-gelu (T2 chung): Đồ thị GELU và đạo hàm, cực tiểu x ≈ -0.75 và vai trò trong Transformer
  - act-6-khong-gian-tensor-cac-chuan-hoa (T2 chung / T1 RK3588): Không gian 3D chuẩn Wu & He (BN, LN, IN, GN)
  - act-7-co-che-batchnorm-train-vs-inference (T2 chung / T1 RK3588): Sơ đồ luồng dữ liệu Train vs Inference
  - act-8-conv-bn-act-va-conv-bn-folding (T2 chung / T1 RK3588): Gộp toán tử Conv-BN Folding và DRAM

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 2 cấp: 04-chuan-hoa-va-activation -> 01-kien-thuc-nen -> figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "01-nen-tang-ai", "04-chuan-hoa-va-activation"
    )
)

W = 860
PURPLE = "#7B1FA2"
GRID = "#E2E8F0"


def tier(f, label, x=W - 130, y=4):
    f.tier(x, y, label)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def seg(f, x1, y1, x2, y2, color=GRAY, sw=1.0, dashed=False):
    f.line([(x1, y1), (x2, y2)], color, width=sw, dashed=dashed, head=False)


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN):
    if color not in (BLUE, GREEN, RED, GRAY, INK):  # figlib chỉ định nghĩa đầu mũi tên cho 5 màu này
        color = INK
    f.line([(x1, y1), (x2, y2)], color, width=sw, head=True)


def draw_axes_box(f, x, y, w, h, ox_ratio=0.43, oy_ratio=0.72, x_steps=[-2, -1, 1, 2], y_steps=[1, 2], sc_x=42, sc_y=34):
    """Vẽ nền khung và hệ trục tọa độ x, y cân đối, ôm khít đồ thị."""
    rect(f, x, y, w, h, fill="#FCFDFD", stroke="#B0BEC5", sw=1.0, rx=4)
    ox = x + w * ox_ratio
    oy = y + h * oy_ratio

    # Lưới toạ độ nét đứt mờ
    for s in x_steps:
        px = ox + s * sc_x
        if x + 10 < px < x + w - 10:
            seg(f, px, y + 12, px, y + h - 10, GRID, 0.8, dashed=True)
    for s in y_steps:
        py = oy - s * sc_y
        if y + 12 < py < y + h - 10:
            seg(f, x + 10, py, x + w - 10, py, GRID, 0.8, dashed=True)

    # Trục x và y
    seg(f, x + 10, oy, x + w - 10, oy, "#90A4AE", 1.2)
    seg(f, ox, y + 12, ox, y + h - 10, "#90A4AE", 1.2)
    f.text(x + w - 8, oy, "x", size=10, fill="#546E7A")
    f.text(ox, y + 8, "y", size=10, fill="#546E7A", anchor="middle")
    f.text(ox - 5, oy + 8, "0", size=9, fill="#78909C", anchor="end")

    return ox, oy, sc_x, sc_y


# ==============================================================================
# 1. HÌNH RELU (act-1-relu)
# ==============================================================================
def fig_relu():
    H = 195
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(15, 18, "Hàm kích hoạt ReLU (Rectified Linear Unit) và Đạo hàm", size=14.5, weight=700, fill=DARK)

    card_w = 460
    card_h = 138
    rect(f, 15, 28, card_w, card_h, fill="#F8FAFC", stroke="#CBD5E1", sw=1.0, rx=5)
    f.text(25, 43, "ReLU: f(x) = max(0, x)", size=12, weight=700, fill=BLUE)
    f.text(25, 63, "• Miền dương (x > 0): f(x) = x, f'(x) = 1; chống triệt tiêu gradient, hội tụ nhanh.", size=9.2, fill=DARK)
    f.text(25, 84, "• Miền âm (x < 0) [Dying ReLU]: f(x) = 0, f'(x) = 0; nơ-ron ngừng học nếu rơi vào âm.", size=9.2, fill=DARK)
    f.text(25, 105, "• Điểm gãy x = 0: Đạo hàm không xác định, nhảy bậc 0 → 1 (thực tế gán 0 hoặc 1).", size=9.2, fill=DARK)
    f.text(25, 126, "• Phần cứng NPU RK3588: Ghép trực tiếp vào DPU (toán tử MAX), 0 overhead DRAM.", size=9.2, weight=700, fill=BLUE)
    f.text(25, 147, "• Thân thiện INT8: Tuyến tính từng đoạn giúp lượng tử hóa số nguyên cực kỳ chính xác.", size=9.2, fill="#555555")

    gx = card_w + 27
    gw = W - gx - 15
    ox, oy, sc_x, sc_y = draw_axes_box(f, gx, 28, gw, card_h, ox_ratio=0.43, oy_ratio=0.72, x_steps=[-2, -1, 1, 2, 3], y_steps=[1, 2], sc_x=42, sc_y=34)

    max_x = (gw - (ox - gx) - 20) / sc_x
    max_y_step = min(max_x, (oy - (28 + 14)) / sc_y)

    # Đường hàm ReLU: f(x) = max(0, x)
    seg(f, ox - 2.8 * sc_x, oy, ox, oy, BLUE, 2.8)
    seg(f, ox, oy, ox + max_y_step * sc_x, oy - max_y_step * sc_y, BLUE, 2.8)

    # Đường đạo hàm f'(x): 0 khi x < 0; 1 khi x > 0
    seg(f, ox - 2.8 * sc_x, oy + 2, ox, oy + 2, RED, 1.8, dashed=True)
    seg(f, ox, oy - 1.0 * sc_y, ox + (max_x + 0.2) * sc_x, oy - 1.0 * sc_y, RED, 1.8, dashed=True)
    f.a(f'<circle cx="{ox}" cy="{oy + 2}" r="3.0" fill="none" stroke="{RED}" stroke-width="1.5"/>')
    f.a(f'<circle cx="{ox}" cy="{oy - 1.0 * sc_y}" r="3.0" fill="{RED}"/>')

    # Nhãn trên đồ thị (đặt vị trí không đè đường hay trục)
    f.text(ox - 0.4 * sc_x, oy - 1.9 * sc_y, "f(x) = max(0, x)", size=10.5, weight=700, fill=BLUE, anchor="end")
    f.text(ox + 1.8 * sc_x, oy - 1.0 * sc_y + 13, "f'(x) = 1 (x > 0)", size=9.5, weight=600, fill=RED)
    f.text(ox - 1.5 * sc_x, oy + 14, "f'(x) = 0 (x < 0)", size=9.2, weight=600, fill=RED, anchor="middle")

    # Callouts
    arrow(f, ox + 35, oy + 24, ox + 4, oy + 4, DARK, 1.1)
    f.text(ox + 38, oy + 26, "Điểm gãy x=0", size=8.8, weight=700, fill=DARK)

    arrow(f, ox - 1.5 * sc_x, oy - 20, ox - 1.5 * sc_x, oy - 3, RED, 1.1)
    f.text(ox - 1.5 * sc_x, oy - 25, "Dying ReLU (dập tắt gradient)", size=8.8, weight=700, fill=RED, anchor="middle")

    source(f, 28 + card_h + 2, "Nguồn: Nair & Hinton (ICML 2010), Dive into Deep Learning (2023).")
    return f


# ==============================================================================
# 2. HÌNH LEAKY RELU (act-2-leaky-relu)
# ==============================================================================
def fig_leaky_relu():
    H = 195
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(15, 18, "Hàm kích hoạt LeakyReLU: Giữ dòng gradient miền âm", size=14.5, weight=700, fill=DARK)

    card_w = 460
    card_h = 138
    rect(f, 15, 28, card_w, card_h, fill="#F8FAFC", stroke="#CBD5E1", sw=1.0, rx=5)
    f.text(25, 43, "LeakyReLU (α = 0.1): f(x) = max(αx, x)", size=12, weight=700, fill=BLUE)
    f.text(25, 63, "• Khắc phục Dying ReLU: Miền âm duy trì độ dốc nhỏ α, giữ gradient rò rỉ liên tục.", size=9.2, fill=DARK)
    f.text(25, 84, "• Cơ chế tự phục hồi: Nơ-ron không bao giờ chết hẳn, luôn có cơ hội cập nhật lại.", size=9.2, fill=DARK)
    f.text(25, 105, "• Đạo hàm: f'(x) = 1 khi x > 0; f'(x) = α khi x < 0; nhảy bậc tại điểm gãy x = 0.", size=9.2, fill=DARK)
    f.text(25, 126, "• Phần cứng NPU RK3588: Ghép trực tiếp vào DPU ALU, tốc độ thực thi tương đương ReLU.", size=9.2, weight=700, fill=BLUE)
    f.text(25, 147, "• Thân thiện INT8: Vẫn là tuyến tính từng đoạn, dễ lượng tử hóa và bảo toàn độ chính xác.", size=9.2, fill="#555555")

    gx = card_w + 27
    gw = W - gx - 15
    ox, oy, sc_x, sc_y = draw_axes_box(f, gx, 28, gw, card_h, ox_ratio=0.43, oy_ratio=0.72, x_steps=[-2, -1, 1, 2, 3], y_steps=[1, 2], sc_x=42, sc_y=34)

    alpha = 0.1
    max_x = (gw - (ox - gx) - 20) / sc_x
    max_y_step = min(max_x, (oy - (28 + 14)) / sc_y)

    # Đường LeakyReLU
    seg(f, ox - 2.8 * sc_x, oy + 2.8 * alpha * sc_y, ox, oy, BLUE, 2.8)
    seg(f, ox, oy, ox + max_y_step * sc_x, oy - max_y_step * sc_y, BLUE, 2.8)

    # Đường nét đứt mờ ReLU gốc để so sánh
    seg(f, ox - 2.0 * sc_x, oy - 6, ox, oy - 6, "#BDBDBD", 1.2, dashed=True)
    f.text(ox - 6, oy - 14, "ReLU gốc (dập 0)", size=8.5, fill="#757575", anchor="end")

    # Đường đạo hàm LeakyReLU
    seg(f, ox - 2.8 * sc_x, oy + alpha * sc_y + 14, ox, oy + alpha * sc_y + 14, RED, 1.8, dashed=True)
    seg(f, ox, oy - 1.0 * sc_y, ox + (max_x + 0.2) * sc_x, oy - 1.0 * sc_y, RED, 1.8, dashed=True)
    f.a(f'<circle cx="{ox}" cy="{oy + alpha * sc_y + 14}" r="3.0" fill="none" stroke="{RED}" stroke-width="1.5"/>')
    f.a(f'<circle cx="{ox}" cy="{oy - 1.0 * sc_y}" r="3.0" fill="{RED}"/>')

    # Nhãn trên đồ thị
    f.text(ox - 0.4 * sc_x, oy - 1.9 * sc_y, "f(x) = max(αx, x)", size=10.5, weight=700, fill=BLUE, anchor="end")
    f.text(ox + 1.8 * sc_x, oy - 1.0 * sc_y + 13, "f'(x) = 1 (x > 0)", size=9.5, weight=600, fill=RED)
    f.text(ox - 1.6 * sc_x, oy + 26, "f'(x) = α = 0.1 (x < 0)", size=8.8, weight=600, fill=RED, anchor="middle")

    # Callout nhánh dốc chỉ từ trên xuống, không chạm ReLU gốc hay đường đạo hàm
    arrow(f, ox - 2.3 * sc_x, oy - 18, ox - 2.3 * sc_x, oy + 2.3 * alpha * sc_y - 2, BLUE, 1.1)
    f.text(ox - 2.3 * sc_x, oy - 22, "Nhánh dốc α = 0.1", size=8.5, weight=700, fill=BLUE, anchor="middle")

    source(f, 28 + card_h + 2, "Nguồn: Maas et al. (ICML 2013), Rockchip TRM (2022).")
    return f


# ==============================================================================
# 3. HÌNH SIGMOID VÀ TANH (act-3-sigmoid-va-tanh)
# ==============================================================================
def fig_sigmoid_va_tanh():
    H = 240
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(15, 18, "So sánh hai hàm kích hoạt mũ: Sigmoid và Tanh", size=14.5, weight=700, fill=DARK)

    pw = 408
    ph = 186

    # ---------------- PANEL TRÁI: SIGMOID ----------------
    px1 = 15
    rect(f, px1, 28, pw, ph, fill="#FCFDFD", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(px1 + 12, 46, "Hàm Sigmoid: σ(x) = 1 / (1 + e^-x)", size=11.5, weight=700, fill=BLUE)

    ox1 = px1 + 195
    oy1 = 126
    sc_x1 = 44
    sc_y1 = 56

    for s in [-2, -1, 1, 2]:
        seg(f, ox1 + s * sc_x1, 66, ox1 + s * sc_x1, oy1 + 14, GRID, 0.8, dashed=True)
    seg(f, px1 + 12, oy1, px1 + pw - 12, oy1, "#90A4AE", 1.2)
    seg(f, ox1, 66, ox1, oy1 + 14, "#90A4AE", 1.2)
    f.text(px1 + pw - 10, oy1, "x", size=10, fill="#546E7A")
    f.text(ox1, 60, "y", size=10, fill="#546E7A", anchor="middle")
    f.text(ox1 - 5, oy1 + 8, "0", size=9, fill="#78909C", anchor="end")
    f.text(ox1 - 5, oy1 - sc_y1 - 7, "1.0", size=9, fill="#78909C", anchor="end")

    seg(f, px1 + 12, oy1 - sc_y1, px1 + pw - 12, oy1 - sc_y1, "#CFD8DC", 0.8, dashed=True)

    pts_sig = []
    pts_dsig = []
    for step in range(-32, 33):
        xv = step * 0.1
        sg = 1.0 / (1.0 + math.exp(-xv))
        dsg = sg * (1.0 - sg)
        pts_sig.append((ox1 + xv * sc_x1, oy1 - sg * sc_y1))
        pts_dsig.append((ox1 + xv * sc_x1, oy1 - dsg * sc_y1))

    path_sig = f"M {pts_sig[0][0]:.1f} {pts_sig[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_sig[1:])
    f.a(f'<path d="{path_sig}" fill="none" stroke="{BLUE}" stroke-width="2.5"/>')

    path_dsig = f"M {pts_dsig[0][0]:.1f} {pts_dsig[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_dsig[1:])
    f.a(f'<path d="{path_dsig}" fill="none" stroke="{RED}" stroke-width="1.6" stroke-dasharray="4 3"/>')

    f.text(ox1 + 1.2 * sc_x1, oy1 - 1.15 * sc_y1, "σ(x) ∈ (0, 1)", size=10, weight=700, fill=BLUE)
    arrow(f, ox1 - 1.5 * sc_x1, oy1 - 0.55 * sc_y1, ox1 - 4, oy1 - 0.25 * sc_y1, RED, 1.1)
    f.text(ox1 - 1.5 * sc_x1, oy1 - 0.55 * sc_y1 - 4, "σ'(0) = 0.25", size=9.0, weight=700, fill=RED, anchor="middle")

    # Ghi chú chân panel Sigmoid
    rect(f, px1 + 8, 150, pw - 16, 56, fill="#F8FAFC", stroke="#CFD8DC", sw=0.8, rx=3)
    f.text(px1 + 14, 168, "• Vùng bão hòa: |x| > 3 → σ'(x) ≈ 0, gây triệt tiêu gradient ở mạng sâu.", size=8.8, fill=DARK)
    f.text(px1 + 14, 188, "• Nhược điểm: Không Zero-Centered (luôn dương), khiến cập nhật gradient zigzag.", size=8.8, fill=DARK)

    # ---------------- PANEL PHẢI: TANH ----------------
    px2 = px1 + pw + 14
    rect(f, px2, 28, pw, ph, fill="#FCFDFD", stroke="#B0BEC5", sw=1.0, rx=5)
    f.text(px2 + 12, 46, "Hàm Tanh: tanh(x) = (e^x - e^-x) / (e^x + e^-x)", size=11.5, weight=700, fill=PURPLE)

    ox2 = px2 + 195
    oy2 = 112
    sc_x2 = 44
    sc_y2 = 36

    for s in [-2, -1, 1, 2]:
        seg(f, ox2 + s * sc_x2, 66, ox2 + s * sc_x2, oy2 + 36, GRID, 0.8, dashed=True)
    seg(f, px2 + 12, oy2, px2 + pw - 12, oy2, "#90A4AE", 1.2)
    seg(f, ox2, 66, ox2, oy2 + 36, "#90A4AE", 1.2)
    f.text(px2 + pw - 10, oy2, "x", size=10, fill="#546E7A")
    f.text(ox2, 60, "y", size=10, fill="#546E7A", anchor="middle")
    f.text(ox2 + 6, oy2 + 8, "0", size=9, fill="#78909C", anchor="start")
    f.text(ox2 - 5, oy2 - sc_y2 - 7, "1.0", size=9, fill="#78909C", anchor="end")
    f.text(ox2 + 5, oy2 + sc_y2 - 7, "-1.0", size=9, fill="#78909C", anchor="start")

    seg(f, px2 + 12, oy2 - sc_y2, px2 + pw - 12, oy2 - sc_y2, "#CFD8DC", 0.8, dashed=True)
    seg(f, px2 + 12, oy2 + sc_y2, px2 + pw - 12, oy2 + sc_y2, "#CFD8DC", 0.8, dashed=True)

    pts_tanh = []
    pts_dtanh = []
    for step in range(-32, 33):
        xv = step * 0.1
        th = math.tanh(xv)
        dth = 1.0 - th * th
        pts_tanh.append((ox2 + xv * sc_x2, oy2 - th * sc_y2))
        pts_dtanh.append((ox2 + xv * sc_x2, oy2 - dth * sc_y2))

    path_tanh = f"M {pts_tanh[0][0]:.1f} {pts_tanh[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_tanh[1:])
    f.a(f'<path d="{path_tanh}" fill="none" stroke="{PURPLE}" stroke-width="2.5"/>')

    path_dtanh = f"M {pts_dtanh[0][0]:.1f} {pts_dtanh[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_dtanh[1:])
    f.a(f'<path d="{path_dtanh}" fill="none" stroke="{RED}" stroke-width="1.6" stroke-dasharray="4 3"/>')

    f.text(ox2 + 1.2 * sc_x2, oy2 - 0.5 * sc_y2, "Tanh(x) ∈ (-1, 1)", size=10, weight=700, fill=PURPLE)
    arrow(f, ox2 - 1.4 * sc_x2 + 36, oy2 - 0.7 * sc_y2 - 4, ox2 - 6, oy2 - sc_y2 + 3, RED, 1.1)
    f.text(ox2 - 1.4 * sc_x2, oy2 - 0.7 * sc_y2 - 4, "tanh'(0) = 1.0", size=9.0, weight=700, fill=RED, anchor="middle")

    # Ghi chú chân panel Tanh
    rect(f, px2 + 8, 150, pw - 16, 56, fill="#F8FAFC", stroke="#CFD8DC", sw=0.8, rx=3)
    f.text(px2 + 14, 168, "• Ưu điểm: Zero-Centered (đối xứng qua gốc 0), tối ưu gradient nhanh hơn Sigmoid.", size=8.8, fill=DARK)
    f.text(px2 + 14, 188, "• Nhược điểm: Vẫn bão hòa ở 2 biên khi |x| lớn; cần bảng tra LUT trên NPU.", size=8.8, fill=DARK)

    source(f, 28 + ph + 2, "Nguồn: LeCun et al. (Efficient BackProp 1998), Goodfellow et al. (Deep Learning 2016).")
    return f


# ==============================================================================
# 4. HÌNH SILU (act-4-silu)
# ==============================================================================
def fig_silu():
    H = 195
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(15, 18, "Hàm kích hoạt SiLU (Swish-1): Phi tuyến trơn và Không đơn điệu", size=14.5, weight=700, fill=DARK)

    card_w = 460
    card_h = 138
    rect(f, 15, 28, card_w, card_h, fill="#F8FAFC", stroke="#CBD5E1", sw=1.0, rx=5)
    f.text(25, 43, "SiLU (Swish-1): f(x) = x · σ(x) = x / (1 + e^-x)", size=12, weight=700, fill=BLUE)
    f.text(25, 63, "• Phi tuyến trơn: Đạo hàm trơn tru tại mọi x, không đứt gãy tại 0, bề mặt loss phẳng mịn.", size=9.2, fill=DARK)
    f.text(25, 84, "• Không đơn điệu: Cực tiểu x ≈ -1.28 (y ≈ -0.28), bảo lưu gradient âm chống chết nơ-ron.", size=9.2, fill=DARK)
    f.text(25, 105, "• Tiệm cận: f(x) → x khi x → +∞ (tương tự ReLU); f(x) → 0 khi x → -∞.", size=9.2, fill=DARK)
    f.text(25, 126, "• Ứng dụng: Chuẩn mực trong YOLOv5, YOLOv8, YOLO11 mang lại mAP vượt trội hơn ReLU.", size=9.2, weight=700, fill=BLUE)
    f.text(25, 147, "• Phần cứng NPU RK3588: Đòi hỏi bảng tra LUT trong DPU hoặc xấp xỉ phần cứng.", size=9.2, fill="#555555")

    gx = card_w + 27
    gw = W - gx - 15
    ox, oy, sc_x, sc_y = draw_axes_box(f, gx, 28, gw, card_h, ox_ratio=0.43, oy_ratio=0.72, x_steps=[-2, -1, 1, 2, 3], y_steps=[1, 2], sc_x=42, sc_y=34)

    max_x = (gw - (ox - gx) - 20) / sc_x
    max_y_step = min(max_x, (oy - (28 + 14)) / sc_y)

    # Đường tiệm cận y=x ở miền dương
    seg(f, ox, oy, ox + max_y_step * sc_x, oy - max_y_step * sc_y, "#B0BEC5", 1.2, dashed=True)
    f.text(ox + max_y_step * sc_x - 4, oy - max_y_step * sc_y - 8, "Tiệm cận y = x", size=8.5, fill="#78909C", anchor="end")

    pts_silu = []
    pts_dsilu = []
    for step in range(-28, 29):
        xv = step * 0.1
        if xv > max_y_step:
            break
        sig = 1.0 / (1.0 + math.exp(-xv))
        yv = xv * sig
        dyv = sig + xv * sig * (1.0 - sig)
        pts_silu.append((ox + xv * sc_x, oy - yv * sc_y))
        pts_dsilu.append((ox + xv * sc_x, oy - dyv * sc_y))

    path_silu = f"M {pts_silu[0][0]:.1f} {pts_silu[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_silu[1:])
    f.a(f'<path d="{path_silu}" fill="none" stroke="{BLUE}" stroke-width="2.8"/>')

    path_dsilu = f"M {pts_dsilu[0][0]:.1f} {pts_dsilu[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_dsilu[1:])
    f.a(f'<path d="{path_dsilu}" fill="none" stroke="{RED}" stroke-width="1.8" stroke-dasharray="4 3"/>')

    f.text(ox - 0.4 * sc_x, oy - 1.9 * sc_y, "f(x) = x · σ(x) (SiLU)", size=10.5, weight=700, fill=BLUE, anchor="end")
    f.text(ox + 1.8 * sc_x, oy - 1.0 * sc_y + 13, "f'(x) trơn liên tục", size=9.5, weight=600, fill=RED)

    # Callout cực tiểu
    val_x = ox - 1.28 * sc_x
    val_y = oy - (-0.28) * sc_y
    f.a(f'<circle cx="{val_x:.1f}" cy="{val_y:.1f}" r="3.0" fill="{BLUE}"/>')
    arrow(f, val_x, oy + 24, val_x, val_y + 3, BLUE, 1.1)
    f.text(ox - 6, oy + 29, "Cực tiểu: x ≈ -1.28, y ≈ -0.28", size=8.5, weight=700, fill=BLUE, anchor="end")

    source(f, 28 + card_h + 2, "Nguồn: Ramachandran et al. (Swish 2017), Elfwing et al. (SiLU 2018), Rockchip OPL tr.47.")
    return f


# ==============================================================================
# 5. HÌNH GELU (act-5-gelu)
# ==============================================================================
def fig_gelu():
    H = 195
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(15, 18, "Hàm kích hoạt GELU: Chuẩn mực trong Vision Transformer", size=14.5, weight=700, fill=DARK)

    card_w = 460
    card_h = 138
    rect(f, 15, 28, card_w, card_h, fill="#F8FAFC", stroke="#CBD5E1", sw=1.0, rx=5)
    f.text(25, 43, "GELU: f(x) = x · Φ(x) = x · P(X ≤ x),  X ~ N(0, 1)", size=11.5, weight=700, fill=BLUE)
    f.text(25, 63, "• Xấp xỉ thực thi: f(x) ≈ 0.5x · [1 + tanh(√(2/π) · (x + 0.044715x³))].", size=9.2, fill=DARK)
    f.text(25, 84, "• Bản chất: Kết hợp đặc tính Dropout ngẫu nhiên và hàm trơn trong một toán tử duy nhất.", size=9.2, fill=DARK)
    f.text(25, 105, "• Điểm cực tiểu: x ≈ -0.75 (y ≈ -0.17), làm phẳng bề mặt tối ưu và hội tụ nhanh.", size=9.2, fill=DARK)
    f.text(25, 126, "• Ứng dụng: Chuẩn mực trong Vision Transformer (ViT, Swin) và các mô hình LLM.", size=9.2, weight=700, fill=BLUE)
    f.text(25, 147, "• Phần cứng NPU RK3588: Đòi hỏi bảng tra LUT trong DPU; chi phí cao hơn ReLU.", size=9.2, fill="#555555")

    gx = card_w + 27
    gw = W - gx - 15
    ox, oy, sc_x, sc_y = draw_axes_box(f, gx, 28, gw, card_h, ox_ratio=0.43, oy_ratio=0.72, x_steps=[-2, -1, 1, 2, 3], y_steps=[1, 2], sc_x=42, sc_y=34)

    max_x = (gw - (ox - gx) - 20) / sc_x
    max_y_step = min(max_x, (oy - (28 + 14)) / sc_y)

    # Tiệm cận y = x
    seg(f, ox, oy, ox + max_y_step * sc_x, oy - max_y_step * sc_y, "#B0BEC5", 1.2, dashed=True)
    f.text(ox + max_y_step * sc_x - 4, oy - max_y_step * sc_y - 8, "Tiệm cận y = x", size=8.5, fill="#78909C", anchor="end")

    pts_gelu = []
    pts_dgelu = []
    for step in range(-28, 29):
        xv = step * 0.1
        if xv > max_y_step:
            break
        phi = 0.5 * (1.0 + math.erf(xv / math.sqrt(2.0)))
        yv = xv * phi
        xv2 = xv + 0.001
        phi2 = 0.5 * (1.0 + math.erf(xv2 / math.sqrt(2.0)))
        dyv = (xv2 * phi2 - yv) / 0.001
        pts_gelu.append((ox + xv * sc_x, oy - yv * sc_y))
        pts_dgelu.append((ox + xv * sc_x, oy - dyv * sc_y))

    path_gelu = f"M {pts_gelu[0][0]:.1f} {pts_gelu[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_gelu[1:])
    f.a(f'<path d="{path_gelu}" fill="none" stroke="{BLUE}" stroke-width="2.8"/>')

    path_dgelu = f"M {pts_dgelu[0][0]:.1f} {pts_dgelu[0][1]:.1f} " + " ".join(f"L {p[0]:.1f} {p[1]:.1f}" for p in pts_dgelu[1:])
    f.a(f'<path d="{path_dgelu}" fill="none" stroke="{RED}" stroke-width="1.8" stroke-dasharray="4 3"/>')

    f.text(ox - 0.4 * sc_x, oy - 1.9 * sc_y, "f(x) = x · Φ(x) (GELU)", size=10.5, weight=700, fill=BLUE, anchor="end")
    f.text(ox + 1.8 * sc_x, oy - 1.0 * sc_y + 13, "f'(x) trơn liên tục", size=9.5, weight=600, fill=RED)

    # Callout cực tiểu
    val_x = ox - 0.75 * sc_x
    val_y = oy - (-0.17) * sc_y
    f.a(f'<circle cx="{val_x:.1f}" cy="{val_y:.1f}" r="3.0" fill="{BLUE}"/>')
    arrow(f, val_x, oy + 24, val_x, val_y + 3, BLUE, 1.1)
    f.text(ox - 6, oy + 29, "Cực tiểu: x ≈ -0.75, y ≈ -0.17", size=8.5, weight=700, fill=BLUE, anchor="end")

    source(f, 28 + card_h + 2, "Nguồn: Hendrycks & Gimpel (GELU 2016), Dosovitskiy et al. (ViT 2020).")
    return f



# ==============================================================================
# 6. HÌNH KHÔNG GIAN TENSOR CHUẨN WU & HE 2018 (act-6)
# ==============================================================================
def fig_tensor_spaces():
    H = 350
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(10, 18, "Không gian tensor của 4 phương pháp chuẩn hóa (Chuẩn Wu & He, ECCV 2018)", size=14.5, weight=700, fill=DARK)

    box_w = 200
    box_h = 264
    xs = [10, 220, 430, 640]
    methods = [
        ("Batch Normalization (BN)", BLUE, "#F8FAFC", "Gom toàn bộ N và (H, W)", "Theo từng Kênh (C)"),
        ("Layer Normalization (LN)", BLUE, "#F8FAFC", "Gom toàn bộ C và (H, W)", "Theo từng Mẫu (N)"),
        ("Instance Normalization (IN)", BLUE, "#F8FAFC", "Gom không gian (H, W)", "Riêng 1 Kênh, 1 Mẫu"),
        ("Group Normalization (GN)", BLUE, "#F8FAFC", "Gom C/G kênh và (H, W)", "Theo nhóm Kênh (C/G)"),
    ]

    for i, (name, col, bg_col, sub, tag) in enumerate(methods):
        bx = xs[i]
        rect(f, bx, 32, box_w, box_h, fill="white", stroke="#B0BEC5", sw=1.0, rx=4)
        f.text(bx + box_w / 2, 46, name, size=10.5, weight=700, fill=DARK, anchor="middle")

        cx0 = bx + 36
        cy0 = 168
        cw = 85
        ch = 85
        dx = 38
        dy = -24

        f.a(f'<polygon points="{cx0},{cy0} {cx0+cw},{cy0} {cx0+cw+dx},{cy0+dy} {cx0+dx},{cy0+dy}" fill="none" stroke="#B0BEC5" stroke-dasharray="3 2"/>')
        f.a(f'<rect x="{cx0}" y="{cy0-ch}" width="{cw}" height="{ch}" fill="none" stroke="#B0BEC5" stroke-width="1.0"/>')
        f.a(f'<polygon points="{cx0},{cy0-ch} {cx0+cw},{cy0-ch} {cx0+cw+dx},{cy0-ch+dy} {cx0+dx},{cy0-ch+dy}" fill="none" stroke="#B0BEC5" stroke-width="1.0"/>')
        f.a(f'<polygon points="{cx0+cw},{cy0-ch} {cx0+cw+dx},{cy0-ch+dy} {cx0+cw+dx},{cy0+dy} {cx0+cw},{cy0}" fill="none" stroke="#B0BEC5" stroke-width="1.0"/>')

        if i == 0:  # BN
            sl_y = cy0 - ch * 0.55
            sl_h = 24
            f.a(f'<rect x="{cx0}" y="{sl_y-sl_h}" width="{cw}" height="{sl_h}" fill="{col}" fill-opacity="0.85" stroke="{col}" stroke-width="1.2"/>')
            f.a(f'<polygon points="{cx0},{sl_y-sl_h} {cx0+cw},{sl_y-sl_h} {cx0+cw+dx},{sl_y-sl_h+dy} {cx0+dx},{sl_y-sl_h+dy}" fill="{col}" fill-opacity="0.6" stroke="{col}" stroke-width="1.2"/>')
            f.a(f'<polygon points="{cx0+cw},{sl_y-sl_h} {cx0+cw+dx},{sl_y-sl_h+dy} {cx0+cw+dx},{sl_y+dy} {cx0+cw},{sl_y}" fill="{col}" fill-opacity="0.95" stroke="{col}" stroke-width="1.2"/>')
        elif i == 1:  # LN
            n_off_x = dx * 0.35
            n_off_y = dy * 0.35
            n_w_d = dx * 0.35
            n_h_d = dy * 0.35
            f.a(f'<rect x="{cx0+n_off_x}" y="{cy0-ch+n_off_y}" width="{cw}" height="{ch}" fill="{col}" fill-opacity="0.85" stroke="{col}" stroke-width="1.2"/>')
            f.a(f'<polygon points="{cx0+n_off_x},{cy0-ch+n_off_y} {cx0+cw+n_off_x},{cy0-ch+n_off_y} {cx0+cw+n_off_x+n_w_d},{cy0-ch+n_off_y+n_h_d} {cx0+n_off_x+n_w_d},{cy0-ch+n_off_y+n_h_d}" fill="{col}" fill-opacity="0.6" stroke="{col}" stroke-width="1.2"/>')
            f.a(f'<polygon points="{cx0+cw+n_off_x},{cy0-ch+n_off_y} {cx0+cw+n_off_x+n_w_d},{cy0-ch+n_off_y+n_h_d} {cx0+cw+n_off_x+n_w_d},{cy0+n_off_y+n_h_d} {cx0+cw+n_off_x},{cy0+n_off_y}" fill="{col}" fill-opacity="0.95" stroke="{col}" stroke-width="1.2"/>')
        elif i == 2:  # IN
            sl_y = cy0 - ch * 0.55
            sl_h = 24
            n_off_x = dx * 0.35
            n_off_y = dy * 0.35
            n_w_d = dx * 0.35
            n_h_d = dy * 0.35
            f.a(f'<rect x="{cx0+n_off_x}" y="{sl_y-sl_h+n_off_y}" width="{cw}" height="{sl_h}" fill="{col}" fill-opacity="0.85" stroke="{col}" stroke-width="1.2"/>')
            f.a(f'<polygon points="{cx0+n_off_x},{sl_y-sl_h+n_off_y} {cx0+cw+n_off_x},{sl_y-sl_h+n_off_y} {cx0+cw+n_off_x+n_w_d},{sl_y-sl_h+n_off_y+n_h_d} {cx0+n_off_x+n_w_d},{sl_y-sl_h+n_off_y+n_h_d}" fill="{col}" fill-opacity="0.6" stroke="{col}" stroke-width="1.2"/>')
            f.a(f'<polygon points="{cx0+cw+n_off_x},{sl_y-sl_h+n_off_y} {cx0+cw+n_off_x+n_w_d},{sl_y-sl_h+n_off_y+n_h_d} {cx0+cw+n_off_x+n_w_d},{sl_y+n_off_y+n_h_d} {cx0+cw+n_off_x},{sl_y+n_off_y}" fill="{col}" fill-opacity="0.95" stroke="{col}" stroke-width="1.2"/>')
        elif i == 3:  # GN
            sl_y = cy0 - ch * 0.40
            sl_h = 42
            n_off_x = dx * 0.35
            n_off_y = dy * 0.35
            n_w_d = dx * 0.35
            n_h_d = dy * 0.35
            f.a(f'<rect x="{cx0+n_off_x}" y="{sl_y-sl_h+n_off_y}" width="{cw}" height="{sl_h}" fill="{col}" fill-opacity="0.85" stroke="{col}" stroke-width="1.2"/>')
            f.a(f'<polygon points="{cx0+n_off_x},{sl_y-sl_h+n_off_y} {cx0+cw+n_off_x},{sl_y-sl_h+n_off_y} {cx0+cw+n_off_x+n_w_d},{sl_y-sl_h+n_off_y+n_h_d} {cx0+n_off_x+n_w_d},{sl_y-sl_h+n_off_y+n_h_d}" fill="{col}" fill-opacity="0.6" stroke="{col}" stroke-width="1.2"/>')
            f.a(f'<polygon points="{cx0+cw+n_off_x},{sl_y-sl_h+n_off_y} {cx0+cw+n_off_x+n_w_d},{sl_y-sl_h+n_off_y+n_h_d} {cx0+cw+n_off_x+n_w_d},{sl_y+n_off_y+n_h_d} {cx0+cw+n_off_x},{sl_y+n_off_y}" fill="{col}" fill-opacity="0.95" stroke="{col}" stroke-width="1.2"/>')

        f.text(cx0 - 5, cy0 - ch / 2, "C ↑", size=9.5, weight=700, fill="#546E7A", anchor="end")
        f.text(cx0 + cw / 2, cy0 + 12, "(H, W) →", size=9.5, weight=700, fill="#546E7A", anchor="middle")
        f.text(cx0 + cw + dx + 3, cy0 + dy / 2, "N ↗", size=9.5, weight=700, fill="#546E7A")

        # Thẻ thông tin dưới khối 3D (vừa khít, ôm sát nội dung)
        rect(f, bx + 5, cy0 + 20, box_w - 10, 104, fill=bg_col, stroke="#B0BEC5", sw=1.0, rx=4)
        f.text(bx + box_w / 2, cy0 + 34, tag, size=10, weight=700, fill=DARK, anchor="middle")
        f.text(bx + 10, cy0 + 50, f"• Gom: {sub}", size=8.8, weight=600, fill=DARK)
        if i == 0:
            f.text(bx + 10, cy0 + 66, "• Thống kê: μ_c, σ²_c trên (B×H×W)", size=8.5, fill=DARK)
            f.text(bx + 10, cy0 + 81, "• Ưu điểm: Gộp triệt để vào Conv", size=8.5, weight=700, fill=GREEN)
            f.text(bx + 10, cy0 + 96, "• Hạn chế: Kém khi batch B ≤ 4", size=8.5, fill=DARK)
            f.text(bx + 10, cy0 + 111, "• Phần cứng: Chi phí suy luận = 0", size=8.5, weight=700, fill=BLUE)
        elif i == 1:
            f.text(bx + 10, cy0 + 66, "• Thống kê: μ_n, σ²_n trên (C×H×W)", size=8.5, fill=DARK)
            f.text(bx + 10, cy0 + 81, "• Ưu điểm: Độc lập với Batch Size", size=8.5, fill=DARK)
            f.text(bx + 10, cy0 + 96, "• Hạn chế: Khó gập vào Conv trên NPU", size=8.5, fill=RED)
            f.text(bx + 10, cy0 + 111, "• Phần cứng: Tốn chu kỳ ALU động", size=8.5, fill=DARK)
        elif i == 2:
            f.text(bx + 10, cy0 + 66, "• Thống kê: μ_n,c, σ²_n,c trên (H×W)", size=8.5, fill=DARK)
            f.text(bx + 10, cy0 + 81, "• Ưu điểm: Khử tương phản toàn cục", size=8.5, fill=DARK)
            f.text(bx + 10, cy0 + 96, "• Hạn chế: Mất thông tin độ sáng nền", size=8.5, fill=DARK)
            f.text(bx + 10, cy0 + 111, "• Phần cứng: Tính riêng từng ảnh", size=8.5, fill=DARK)
        elif i == 3:
            f.text(bx + 10, cy0 + 66, "• Thống kê: μ_n,g, σ²_n,g trên (C/G×H×W)", size=8.5, fill=DARK)
            f.text(bx + 10, cy0 + 81, "• Ưu điểm: Rất ổn định khi batch nhỏ", size=8.5, fill=DARK)
            f.text(bx + 10, cy0 + 96, "• Hạn chế: Tốn tính toán hơn BN", size=8.5, fill=DARK)
            f.text(bx + 10, cy0 + 111, "• Phần cứng: Nhóm C/G linh hoạt", size=8.5, fill=DARK)

    source(f, 32 + box_h + 4, "Nguồn: Group Normalization (Wu & He, ECCV 2018), Dive into Deep Learning (2023).")
    return f


# ==============================================================================
# 7. HÌNH BATCHNORM TRAIN VS INFERENCE (act-7)
# ==============================================================================
def fig_batchnorm_train_vs_inference():
    H = 430
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(10, 18, "Cơ chế toán học BatchNorm: Huấn luyện (Train) vs Suy luận (Inference)", size=14.5, weight=700, fill=DARK)

    pw = 415
    ph = 362

    # Panel A: Chế độ Huấn luyện
    rect(f, 10, 32, pw, ph, fill="white", stroke="#333333", sw=1.2, rx=5)
    f.text(10 + pw / 2, 48, "Panel A: Chế độ Huấn luyện (model.train())", size=11.5, weight=700, fill=DARK, anchor="middle")

    rect(f, 22, 64, 115, 38, fill="#E3F2FD", stroke=BLUE, sw=1.2, rx=4)
    f.text(79, 79, "Mini-batch X", size=10.5, weight=700, fill=BLUE, anchor="middle")
    f.text(79, 93, "Kích thước (B, C, H, W)", size=8.5, fill="#555555", anchor="middle")

    arrow(f, 137, 83, 170, 83, BLUE, 1.3)

    rect(f, 170, 64, 240, 38, fill="#FAFAFA", stroke=DARK, sw=1.2, rx=4)
    f.text(290, 77, "1. Thống kê tức thời từ Batch:", size=9.8, weight=700, fill=DARK, anchor="middle")
    f.text(290, 92, "μ_B = Σ x_i / m,  σ²_B = Σ (x_i - μ_B)² / m", size=8.8, fill=DARK, anchor="middle")

    arrow(f, 290, 102, 290, 118, DARK, 1.2)

    rect(f, 170, 118, 240, 38, fill="#FAFAFA", stroke=DARK, sw=1.2, rx=4)
    f.text(290, 131, "2. Chuẩn hóa về N(0, 1):", size=9.8, weight=700, fill=DARK, anchor="middle")
    f.text(290, 146, "x̂_i = (x_i - μ_B) / √(σ²_B + ε)", size=9.0, fill=DARK, anchor="middle")

    arrow(f, 290, 156, 290, 172, DARK, 1.2)

    rect(f, 170, 172, 240, 38, fill="#FAFAFA", stroke=DARK, sw=1.2, rx=4)
    f.text(290, 185, "3. Khôi phục biểu diễn (Scale & Shift):", size=9.8, weight=700, fill=DARK, anchor="middle")
    f.text(290, 200, "y_i = γ · x̂_i + β  (γ, β là tham số học)", size=8.8, fill=DARK, anchor="middle")

    arrow(f, 290, 210, 290, 226, DARK, 1.2)

    rect(f, 225, 226, 130, 30, fill="#E3F2FD", stroke=BLUE, sw=1.5, rx=4)
    f.text(290, 241, "Đầu ra huấn luyện Y", size=10, weight=700, fill=BLUE, anchor="middle")

    rect(f, 22, 268, 388, 116, fill="#FAFAFA", stroke="#B0BEC5", sw=1.2, rx=4)
    f.text(32, 283, "Cơ chế cập nhật trạng thái tích lũy (Running Stats EMA):", size=9.8, weight=700, fill=DARK)
    f.text(32, 299, "• μ_run ← (1 - η) · μ_run + η · μ_B  (hệ số động lượng η = 0.1)", size=8.8, fill=DARK)
    f.text(32, 315, "• σ²_run ← (1 - η) · σ²_run + η · [m/(m-1)] · σ²_B  (hiệu chỉnh Bessel)", size=8.8, fill=DARK)
    f.text(32, 331, "• Bộ đệm non-trainable: Không tính gradient lan truyền ngược.", size=8.8, fill=DARK)
    f.text(32, 347, "• Cung cấp giá trị thống kê cố định phục vụ giai đoạn suy luận.", size=8.8, fill=DARK)
    f.text(32, 363, "• Lưu trữ trực tiếp trong checkpoint (.pt / .onnx).", size=8.8, weight=700, fill=DARK)

    # Nhánh EMA nối từ Thống kê tức thời xuống hộp EMA
    f.a('<path d="M 410,83 L 418,83 L 418,260 L 370,260 L 370,267" fill="none" stroke="#444444" stroke-width="1.2"/>')
    f.a('<polygon points="370,267 367,261 373,261" fill="#444444"/>')

    # Panel B: Chế độ Suy luận
    rect(f, 435, 32, pw, ph, fill="white", stroke="#333333", sw=1.2, rx=5)
    f.text(435 + pw / 2, 48, "Panel B: Chế độ Suy luận (model.eval())", size=11.5, weight=700, fill=DARK, anchor="middle")

    rect(f, 447, 64, 120, 38, fill="#E3F2FD", stroke=BLUE, sw=1.2, rx=4)
    f.text(507, 79, "Ảnh đầu vào X", size=10.5, weight=700, fill=BLUE, anchor="middle")
    f.text(507, 93, "Kích thước (1, C, H, W)", size=8.5, fill="#555555", anchor="middle")

    rect(f, 595, 64, 240, 38, fill="#FFF5F5", stroke=RED, sw=1.2, dashed=True, rx=4)
    f.text(715, 77, "CẤM TÍNH THỐNG KÊ BATCH!", size=9.8, weight=700, fill=RED, anchor="middle")
    f.text(715, 92, "Phương sai của 1 ảnh = 0, làm vỡ tensor!", size=8.5, fill=DARK, anchor="middle")
    arrow(f, 567, 83, 593, 83, RED, 1.2)

    rect(f, 595, 118, 240, 38, fill="#FAFAFA", stroke=DARK, sw=1.2, rx=4)
    f.text(715, 131, "Nạp Running Stats cố định từ Checkpoint:", size=9.5, weight=700, fill=DARK, anchor="middle")
    f.text(715, 146, "μ = μ_run,   σ² = σ²_run", size=9.5, weight=700, fill=DARK, anchor="middle")

    f.a('<path d="M 507,102 L 507,191 L 593,191" fill="none" stroke="#1E5BB8" stroke-width="1.3"/>')
    f.a('<polygon points="593,191 587,188 587,194" fill="#1E5BB8"/>')

    arrow(f, 715, 156, 715, 172, DARK, 1.3)

    rect(f, 595, 172, 240, 38, fill="#FAFAFA", stroke=DARK, sw=1.5, rx=4)
    f.text(715, 185, "Phép biến đổi Tuyến tính Affine Tất định:", size=9.5, weight=700, fill=DARK, anchor="middle")
    f.text(715, 200, "y = (γ / √(σ²_run + ε)) · (x - μ_run) + β", size=8.8, weight=700, fill=DARK, anchor="middle")

    arrow(f, 715, 210, 715, 226, DARK, 1.3)

    rect(f, 650, 226, 130, 30, fill="#E3F2FD", stroke=BLUE, sw=1.5, rx=4)
    f.text(715, 241, "Đầu ra tất định Y", size=10, weight=700, fill=BLUE, anchor="middle")

    rect(f, 447, 268, 388, 116, fill="#FAFAFA", stroke="#B0BEC5", sw=1.2, rx=4)
    f.text(457, 283, "Tính chất tất định (Deterministic) & Lợi thế phần cứng:", size=9.8, weight=700, fill=DARK)
    f.text(457, 299, "• Đầu ra của 1 bức ảnh không phụ thuộc vào các ảnh khác.", size=8.8, fill=DARK)
    f.text(457, 315, "• Là phép biến đổi tuyến tính 100% tất định trên từng kênh.", size=8.8, fill=DARK)
    f.text(457, 331, "• Cho phép gộp hoàn toàn vào lớp Conv đứng trước (Conv-BN folding).", size=9.0, weight=700, fill=GREEN)
    f.text(457, 347, "• Triệt tiêu hoàn toàn chi phí tính toán của BN lúc suy luận trên NPU.", size=8.8, fill=DARK)
    f.text(457, 363, "• Tăng tốc thực tế 20 - 35% cho mạng suy luận.", size=8.8, weight=700, fill=DARK)

    source(f, 32 + ph + 4, "Nguồn: Ioffe & Szegedy (ICML 2015), PyTorch BatchNorm Documentation.")
    return f


# ==============================================================================
# 8. HÌNH CONV-BN-ACT VÀ CONV-BN FOLDING (act-8)
# ==============================================================================
def fig_conv_bn_folding():
    H = 406
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(10, 18, "Đường ống Conv-BN-Act và kỹ thuật Conv-BN Folding trên NPU RK3588", size=14.5, weight=700, fill=DARK)

    pw = 415
    ph = 338

    # Panel A: Trước khi gộp
    rect(f, 10, 32, pw, ph, fill="white", stroke="#333333", sw=1.2, rx=5)
    f.text(10 + pw / 2, 48, "Panel A: Trước khi gộp (3 toán tử tách rời, nghẽn DRAM)", size=11.5, weight=700, fill=DARK, anchor="middle")

    bx_a = 22
    bw_a = 185

    # Conv2d
    rect(f, bx_a, 62, bw_a, 36, fill="#E3F2FD", stroke=BLUE, sw=1.2, rx=4)
    f.text(bx_a + bw_a / 2, 75, "nn.Conv2d", size=10.5, weight=700, fill=BLUE, anchor="middle")
    f.text(bx_a + bw_a / 2, 89, "Trọng số W, bias = 0", size=8.5, fill=DARK, anchor="middle")

    rect(f, 225, 62, 185, 36, fill="#F0F7FF", stroke=BLUE, sw=1.0, rx=4)
    f.text(233, 75, "• Conv bỏ bias:", size=9.0, weight=700, fill=BLUE)
    f.text(233, 89, "  BN trừ TB làm triệt tiêu b.", size=8.5, fill=DARK)
    arrow(f, bx_a + bw_a, 80, 223, 80, BLUE, 1.2)

    arrow(f, bx_a + bw_a / 2, 98, bx_a + bw_a / 2, 114, DARK, 1.2)

    rect(f, 225, 102, 185, 16, fill="white", stroke=RED, sw=0.8, rx=2)
    f.text(317, 110, "Ghi SRAM/DRAM tensor z", size=8.0, fill=RED, anchor="middle")

    # BatchNorm2d
    rect(f, bx_a, 118, bw_a, 36, fill="#FAFAFA", stroke=DARK, sw=1.2, rx=4)
    f.text(bx_a + bw_a / 2, 131, "nn.BatchNorm2d", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(bx_a + bw_a / 2, 145, "Tham số: γ, β, μ_run, σ²_run", size=8.5, fill=DARK, anchor="middle")

    rect(f, 225, 118, 185, 36, fill="white", stroke=RED, sw=1.0, rx=4)
    f.text(233, 131, "• Nghẽn bộ nhớ DRAM:", size=9.0, weight=700, fill=RED)
    f.text(233, 145, "  Đọc lại z từ RAM để tính affine.", size=8.5, fill=DARK)
    arrow(f, bx_a + bw_a, 136, 223, 136, RED, 1.2)

    arrow(f, bx_a + bw_a / 2, 154, bx_a + bw_a / 2, 170, DARK, 1.2)

    rect(f, 225, 158, 185, 16, fill="white", stroke=RED, sw=0.8, rx=2)
    f.text(317, 166, "Ghi SRAM/DRAM tensor y", size=8.0, fill=RED, anchor="middle")

    # Activation
    rect(f, bx_a, 174, bw_a, 34, fill="#FAFAFA", stroke=DARK, sw=1.2, rx=4)
    f.text(bx_a + bw_a / 2, 186, "Activation (SiLU / ReLU)", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(bx_a + bw_a / 2, 199, "Toán tử phi tuyến", size=8.5, fill=DARK, anchor="middle")

    # Hộp nhược điểm phần cứng ở dưới (vừa khít, ôm sát nội dung)
    rect(f, 20, 218, 390, 142, fill="white", stroke=RED, sw=1.2, rx=4)
    f.text(30, 233, "Nhược điểm phần cứng khi chưa gộp:", size=10, weight=700, fill=RED)
    f.text(30, 252, "• Tốn băng thông: Conv ghi z ra DRAM, sau đó BN đọc lại z để tính affine.", size=8.8, fill=DARK)
    f.text(30, 271, "• Lãng phí chu kỳ NPU: Tiêu tốn hàng triệu phép tính số học vô ích cho BN.", size=8.8, fill=DARK)
    f.text(30, 290, "• Tăng độ trễ suy luận: NPU phải chuyển đổi kernel thực thi liên tục.", size=8.8, fill=DARK)
    f.text(30, 309, "• Cản trở lượng tử hóa INT8 trực tiếp trên ma trận trọng số.", size=8.8, fill=DARK)
    f.text(30, 328, "• Tiêu hao năng lượng: Truy cập DRAM tiêu tốn năng lượng gấp 100 lần ALU.", size=8.8, weight=700, fill=RED)
    f.text(30, 347, "• Giảm băng thông phục vụ các tác vụ song song khác trên SoC.", size=8.8, fill="#555555")

    # Panel B: Sau khi gộp Conv-BN Folding
    rect(f, 435, 32, pw, ph, fill="white", stroke="#333333", sw=1.2, rx=5)
    f.text(435 + pw / 2, 48, "Panel B: Sau khi gộp Conv-BN Folding (Tối ưu hóa RKNN)", size=11.5, weight=700, fill=DARK, anchor="middle")

    bx_b = 447
    bw_b = 190

    # Fused Conv2d
    rect(f, bx_b, 62, bw_b, 48, fill="#E3F2FD", stroke=BLUE, sw=1.6, rx=5)
    f.text(bx_b + bw_b / 2, 76, "Fused Conv2d", size=11.5, weight=700, fill=BLUE, anchor="middle")
    f.text(bx_b + bw_b / 2, 91, "Trọng số mới: W_fused", size=9.0, weight=600, fill=DARK, anchor="middle")
    f.text(bx_b + bw_b / 2, 103, "Bias mới: b_fused", size=9.0, weight=600, fill=DARK, anchor="middle")

    rect(f, 650, 62, 185, 48, fill="white", stroke=GREEN, sw=1.0, rx=4)
    f.text(658, 76, "• Lớp BN biến mất hoàn toàn:", size=9.0, weight=700, fill=GREEN)
    f.text(658, 91, "  Gộp toán học vào W và b.", size=8.5, fill=DARK)
    f.text(658, 103, "  Chi phí tính toán BN = 0.", size=8.5, weight=700, fill=GREEN)
    arrow(f, bx_b + bw_b, 86, 648, 86, DARK, 1.2)

    arrow(f, bx_b + bw_b / 2, 110, bx_b + bw_b / 2, 122, DARK, 1.3)

    rect(f, 650, 116, 185, 20, fill="white", stroke=GREEN, sw=0.8, rx=2)
    f.text(742, 126, "Nội bộ ALU (Không qua DRAM)", size=8.0, weight=700, fill=GREEN, anchor="middle")

    # Activation
    rect(f, bx_b, 122, bw_b, 34, fill="#FAFAFA", stroke=DARK, sw=1.5, rx=5)
    f.text(bx_b + bw_b / 2, 134, "Activation (SiLU / ReLU)", size=10.5, weight=700, fill=DARK, anchor="middle")
    f.text(bx_b + bw_b / 2, 147, "Tích hợp thẳng vào đầu ra Conv", size=8.5, fill=DARK, anchor="middle")

    # Hộp công thức Conv-BN Folding bên dưới (vừa khít, ôm sát nội dung)
    rect(f, 447, 166, 390, 194, fill="#FAFAFA", stroke="#B0BEC5", sw=1.2, rx=5)
    f.text(457, 182, "Công thức toán học Conv-BN Folding:", size=10.5, weight=700, fill=DARK)
    f.text(457, 197, "Hệ số co giãn từng kênh c: s_c = γ_c / √(σ²_c + ε)", size=9.0, fill=DARK)

    rect(f, 460, 205, 364, 38, fill="white", stroke=BLUE, sw=1.0, rx=4)
    f.text(642, 219, "W_fused[c, :, :, :] = s_c · W[c, :, :, :]", size=9.8, weight=700, fill=BLUE, anchor="middle")
    f.text(642, 233, "b_fused[c] = s_c · (b_c - μ_c) + β_c", size=9.8, weight=700, fill=BLUE, anchor="middle")

    f.text(457, 257, "• Triệt tiêu hoàn toàn lớp BN: Chi phí tính toán của BN = 0.", size=8.8, weight=700, fill=GREEN)
    f.text(457, 273, "• Tiết kiệm DRAM 100%: Không ghi tensor trung gian ra bộ nhớ ngoài.", size=8.8, fill=DARK)
    f.text(457, 289, "• Tối ưu INT8: Lượng tử hóa trực tiếp trên ma trận trọng số W_fused.", size=8.8, fill=DARK)
    f.text(457, 305, "• Tăng tốc thực tế: Giảm 20 - 35% độ trễ tổng thể của mạng CNN.", size=8.8, fill=DARK)
    f.text(457, 321, "• Tương thích hoàn hảo: RKNN-Toolkit2 tự động thực hiện khi convert.", size=8.8, weight=700, fill=BLUE)
    f.text(457, 337, "• Triển khai zero-code: Mô hình ONNX chuẩn được RKNN tối ưu đồ thị sẵn.", size=8.8, fill="#555555")

    source(f, 32 + ph + 4, "Nguồn: Rockchip RKNN-Toolkit2 User Guide, Whitepaper on Neural Network Quantization (Nagel et al., 2021).")
    return f


FIGS = [
    ("act-1-relu", fig_relu),
    ("act-2-leaky-relu", fig_leaky_relu),
    ("act-3-sigmoid-va-tanh", fig_sigmoid_va_tanh),
    ("act-4-silu", fig_silu),
    ("act-5-gelu", fig_gelu),
    ("act-6-khong-gian-tensor-cac-chuan-hoa", fig_tensor_spaces),
    ("act-7-co-che-batchnorm-train-vs-inference", fig_batchnorm_train_vs_inference),
    ("act-8-conv-bn-act-va-conv-bn-folding", fig_conv_bn_folding),
]


if __name__ == "__main__":
    run(FIGS, DEFAULT_OUTDIR)
