#!/usr/bin/env python3
"""Chuyên đề: Mạng nơ-ron (mang-no-ron.rst).

Sinh hình minh họa chuẩn visual_guide:
  - mnr-1-cau-truc-giai-phau-neuron (T2 chung):
    Sơ đồ giải phẫu Neuron toán học (chuẩn McCulloch-Pitts / Haykin)
    và dòng tính toán số cụ thể bám sát 100% văn bản mục 1 (y = -0.65).

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# figlib nằm ở docs/tools/figure_gen/figlib.py
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "01-nen-tang-ai", "mang-no-ron"))

W = 900
H = 320


def tier(f, label):
    f.tier(W - 130, 10, label)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=3):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def fig_neuron_anatomy():
    """HÌNH 1: Cấu trúc giải phẫu Neuron và Phép biến đổi Affine (ŷ = wᵀx + b)."""
    f = Fig(W, H)
    tier(f, "T2 chung")

    f.text(20, 24, "CẤU TRÚC NEURON VÀ PHÉP BIẾN ĐỔI AFFINE (ŷ = wᵀx + b)", size=13, weight=700, fill=DARK)
    f.text(20, 42, "Mô hình toán học của một neuron: Đầu vào, trọng số, bias, bộ cộng tích lũy và ví dụ tính số thực tế", size=9.2, fill=GRAY)

    # ==============================================================================
    # NỬA TRÁI: SƠ ĐỒ GIẢI PHẪU NEURON (MCCULLOCH-PITTS / HAYKIN MODEL)
    # ==============================================================================
    rect(f, 20, 56, 455, 230, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    # Tiêu đề ngắn gọn, tránh va chạm ngang với node Bias
    f.text(32, 72, "1. SƠ ĐỒ GIẢI PHẪU NEURON (AFFINE)", size=8.8, weight=700, fill=DARK)

    # Cột đầu vào (Input Layer: x_1, x_2, ..., x_d)
    in_x = 52
    rect(f, in_x - 22, 86, 44, 186, fill="#FFFFFF", stroke="#B0BEC5", sw=0.8, rx=4)
    f.text(in_x, 97, "Đầu vào", size=7.2, weight=700, fill="#455A64", anchor="middle")
    f.rich(in_x, 109, [("x ∈ ℝ", "b"), ("ᵈ", "t")], size=7.5, fill="#1E88E5", anchor="middle")

    # Node x1
    f.a(f'<circle cx="{in_x}" cy="{132}" r="13" fill="#E3F2FD" stroke="#1E88E5" stroke-width="1.2"/>')
    f.text(in_x, 132, "x₁", size=8.5, weight=700, fill="#0D47A1", anchor="middle")

    # Node x2
    f.a(f'<circle cx="{in_x}" cy="{170}" r="13" fill="#E3F2FD" stroke="#1E88E5" stroke-width="1.2"/>')
    f.text(in_x, 170, "x₂", size=8.5, weight=700, fill="#0D47A1", anchor="middle")

    # Dấu chấm lửng
    for dy in [193, 199, 205]:
        f.a(f'<circle cx="{in_x}" cy="{dy}" r="1.5" fill="#78909C"/>')

    # Node xd
    f.a(f'<circle cx="{in_x}" cy="{232}" r="13" fill="#E3F2FD" stroke="#1E88E5" stroke-width="1.2"/>')
    f.rich(in_x, 232, [("x", "b"), ("d", "t")], size=8.0, fill="#0D47A1", anchor="middle")

    # THÂN NEURON (BỘ CỘNG TÍCH LŨY: Summing Junction)
    sum_cx, sum_cy, sum_r = 265, 176, 44
    f.a(f'<circle cx="{sum_cx}" cy="{sum_cy}" r="{sum_r}" fill="#FFFFFF" stroke="#37474F" stroke-width="1.8"/>')
    f.text(sum_cx, sum_cy - 22, "THÂN NEURON", size=7.2, weight=700, fill="#546E7A", anchor="middle")
    f.text(sum_cx, sum_cy - 2, "∑", size=26, weight=700, fill=DARK, anchor="middle")
    f.text(sum_cx, sum_cy + 20, "Bộ cộng tích lũy", size=6.8, weight=700, fill="#546E7A", anchor="middle")

    # Tiêu đề cột trọng số
    f.text(140, 97, "Trọng số (w)", size=7.2, weight=700, fill=GRAY, anchor="middle")
    f.text(140, 109, "(Khớp thần kinh)", size=6.4, fill="#90A4AE", anchor="middle")

    # LIÊN KẾT TRỌNG SỐ (Synaptic Connections with Weights on Edges)
    inputs_spec = [
        (132, "w₁"),
        (170, "w₂"),
        (232, "wd"),
    ]

    for y_in, label in inputs_spec:
        alpha = math.atan2(sum_cy - y_in, sum_cx - in_x)
        sx, sy = in_x + 13 * math.cos(alpha), y_in + 13 * math.sin(alpha)
        ex, ey = sum_cx - sum_r * math.cos(alpha), sum_cy - sum_r * math.sin(alpha)
        f.a(f'<path d="M {sx:.1f} {sy:.1f} L {ex:.1f} {ey:.1f}" stroke="#1E88E5" stroke-width="1.4" fill="none" marker-end="url(#{f.marker(BLUE, 1.4)})"/>')

        lx = sx + 0.44 * (ex - sx)
        ly = sy + 0.44 * (ey - sy)
        rect(f, lx - 14, ly - 8, 28, 16, fill="#FFFFFF", stroke="#90CAF9", sw=0.9, rx=3)
        if label == "wd":
            f.rich(lx, ly, [("w", "b"), ("d", "t")], size=7.5, fill="#0D47A1", anchor="middle")
        else:
            f.text(lx, ly, label, size=8.0, weight=700, fill="#0D47A1", anchor="middle")

    # NHÁNH BIAS (OFFSET / ĐỘ LỆCH) - dời xuống y = 98 để cách xa hoàn toàn dòng tiêu đề
    bias_cx, bias_cy = sum_cx, 98
    f.a(f'<circle cx="{bias_cx}" cy="{bias_cy}" r="12" fill="#FFF8E1" stroke="#FFB300" stroke-width="1.3"/>')
    f.text(bias_cx, bias_cy, "+b", size=8.5, weight=700, fill="#E65100", anchor="middle")
    f.text(bias_cx + 18, bias_cy - 4, "Bias b (độ lệch / offset)", size=7.2, weight=700, fill="#BF360C")
    f.text(bias_cx + 18, bias_cy + 7, "Dịch chuyển độc lập", size=6.5, fill="#D84315")
    f.a(f'<path d="M {bias_cx} {bias_cy + 12} L {bias_cx} {sum_cy - sum_r}" stroke="#E65100" stroke-width="1.5" fill="none" marker-end="url(#{f.marker(INK, 1.5)})"/>')

    # ĐẦU RA NEURON
    out_start_x = sum_cx + sum_r
    out_node_x = 408
    f.a(f'<path d="M {out_start_x} {sum_cy} L {out_node_x - 22} {sum_cy}" stroke="{INK}" stroke-width="2.2" fill="none" marker-end="url(#{f.marker(INK, 2.2)})"/>')
    f.text((out_start_x + out_node_x - 22) / 2, sum_cy - 12, "Tín hiệu ra", size=7.2, weight=700, fill="#2E7D32", anchor="middle")

    # Node đầu ra tròn thanh thoát
    out_node_r = 20
    f.a(f'<circle cx="{out_node_x}" cy="{sum_cy}" r="{out_node_r}" fill="#E8F5E9" stroke="#2E7D32" stroke-width="1.6"/>')
    f.text(out_node_x, sum_cy, "ŷ", size=17, weight=700, fill="#1B5E20", anchor="middle")
    f.rich(out_node_x, sum_cy + 28, [("ŷ = ", "b"), ("wᵀx + b", "c")], size=7.5, fill="#1B5E20", anchor="middle")
    f.text(out_node_x, sum_cy + 42, "(Biến đổi Affine)", size=6.8, italic=True, fill="#388E3C", anchor="middle")

    # ==============================================================================
    # NỬA PHẢI: MINH HỌA TÍNH SỐ THỰC TẾ (X: 490 -> 880, W: 390)
    # ==============================================================================
    rect(f, 490, 56, 390, 230, fill="#FFFFFF", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(502, 70, "2. MINH HỌA TÍNH SỐ THỰC TẾ (VÍ DỤ TỰ TÍNH TRONG BÀI)", size=8.8, weight=700, fill="#1565C0")

    # Thông số đầu vào
    rect(f, 502, 84, 366, 34, fill="#F5F5F5", stroke="#CFD8DC", sw=0.8, rx=3)
    f.text(510, 95, "Dữ liệu ví dụ mục 1:", size=7.5, weight=700, fill=DARK)
    f.rich(510, 107, [
        ("• x = (1.0, 2.0, 3.0)", "c"),
        ("  |  w = (0.5, -1.0, 0.25)", "c"),
        ("  |  b = 0.1", "c"),
    ], size=7.2, fill=DARK)

    # Bước 1: Ba tích riêng biệt
    p1_y = 124
    rect(f, 502, p1_y, 366, 42, fill="#FAFAFA", stroke="#E0E0E0", sw=0.8, rx=3)
    f.text(510, p1_y + 11, "Bước 1: Tính tích từng đặc trưng với trọng số (wᵢ · xᵢ)", size=7.5, weight=700, fill="#0D47A1")

    item_w = (366 - 20) / 3
    # Tích 1
    rect(f, 510, p1_y + 19, item_w, 18, fill="#E3F2FD", stroke="#90CAF9", sw=0.8, rx=2)
    f.rich(510 + item_w / 2, p1_y + 28, [("w₁x₁ = 0.5 × 1.0 = ", "t"), ("+0.50", "b")], size=6.8, fill="#0D47A1", anchor="middle")

    # Tích 2
    rect(f, 510 + item_w + 4, p1_y + 19, item_w, 18, fill="#FFEBEE", stroke="#EF9A9A", sw=0.8, rx=2)
    f.rich(510 + item_w + 4 + item_w / 2, p1_y + 28, [("w₂x₂ = -1.0 × 2.0 = ", "t"), ("-2.00", "b")], size=6.8, fill="#C62828", anchor="middle")

    # Tích 3
    rect(f, 510 + (item_w + 4) * 2, p1_y + 19, item_w, 18, fill="#E3F2FD", stroke="#90CAF9", sw=0.8, rx=2)
    f.rich(510 + (item_w + 4) * 2 + item_w / 2, p1_y + 28, [("w₃x₃ = 0.25 × 3.0 = ", "t"), ("+0.75", "b")], size=6.8, fill="#0D47A1", anchor="middle")

    # Bước 2: Tổng các tích và cộng bias
    p2_y = 172
    rect(f, 502, p2_y, 366, 42, fill="#FAFAFA", stroke="#E0E0E0", sw=0.8, rx=3)
    f.text(510, p2_y + 11, "Bước 2: Tính tổng có trọng số rồi cộng bias (wᵀx + b)", size=7.5, weight=700, fill="#0D47A1")
    f.rich(510, p2_y + 27, [
        ("Tổng các tích = ", "t"),
        ("0.5 - 2.0 + 0.75 = ", "t"),
        ("-0.75", "b"),
        ("  |  Cộng bias: ", "t"),
        ("-0.75 + 0.1 = ", "t"),
        ("-0.65", "b"),
    ], size=7.5, fill=DARK)

    # Bước 3: Hộp kết luận
    p3_y = 220
    rect(f, 502, p3_y, 366, 56, fill="#E8F5E9", stroke="#4CAF50", sw=1.2, rx=4)
    f.text(510, p3_y + 14, "KẾT QUẢ ĐẦU RA NEURON (AFFINE TRANSFORMATION):", size=8.0, weight=700, fill="#1B5E20")
    f.rich(510, p3_y + 31, [
        ("y = w₁x₁ + w₂x₂ + w₃x₃ + b = 0.5 - 2.0 + 0.75 + 0.1 = ", "t"),
        ("-0.65", "b"),
    ], size=7.5, fill="#1B5E20")
    f.text(510, p3_y + 45, "✓ Khớp 100% với công thức và kết quả tính toán trong bài học.", size=7.0, italic=True, fill="#2E7D32")

    source(f, 296, "Nguồn: Dive into Deep Learning (D2L 2023, tr. 83-84, 90); Số liệu tự tính bám sát văn bản bài học.")
    return f


def fig_mlp_architecture():
    """HÌNH 2: Kiến trúc mạng Perceptron đa tầng (MLP 4-5-3) và quy tắc đếm lớp."""
    f = Fig(W, 350)
    tier(f, "T2 chung")

    f.text(20, 24, "CẤU TRÚC MẠNG NHIỀU LỚP (MLP) VÀ QUY TẮC ĐẾM LỚP", size=13, weight=700, fill=DARK)
    f.text(20, 42, "Mô hình mạng Perceptron đa tầng 4-5-3 (D2L Fig. 5.1.1): Cấu trúc Fully Connected và quy tắc xác định số lớp", size=9.2, fill=GRAY)

    # ==============================================================================
    # NỬA TRÁI: ĐỒ HÌNH MẠNG MLP 4-5-3 (D2L FIG. 5.1.1)
    # ==============================================================================
    box_y = 56
    box_h = 254
    rect(f, 20, box_y, 455, box_h, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(32, 70, "1. ĐỒ HÌNH MẠNG MLP 4-5-3 (D2L FIG. 5.1.1)", size=8.5, weight=700, fill=DARK)

    # Vị trí các cột
    x_in = 75
    x_hid = 230
    x_out = 385

    # Tiêu đề các cột
    f.text(x_in, 86, "Lớp đầu vào", size=7.8, weight=700, fill="#455A64", anchor="middle")
    f.text(x_in, 98, "(4 đặc trưng)", size=6.6, fill="#78909C", anchor="middle")

    f.text(x_hid, 86, "Lớp ẩn (Hidden)", size=7.8, weight=700, fill="#E65100", anchor="middle")
    f.text(x_hid, 98, "(5 đơn vị ẩn · W⁽¹⁾)", size=6.6, fill="#FB8C00", anchor="middle")

    f.text(x_out, 86, "Lớp đầu ra (Output)", size=7.8, weight=700, fill="#1B5E20", anchor="middle")
    f.text(x_out, 98, "(3 kết quả · W⁽²⁾)", size=6.6, fill="#43A047", anchor="middle")

    # Nhãn liên kết giữa các tầng đặt phía trên vùng bó dây
    f.rich((x_in + x_hid) / 2, 98, [("Liên kết W⁽¹⁾", "b")], size=6.8, fill="#1E88E5", anchor="middle")
    f.rich((x_hid + x_out) / 2, 98, [("Liên kết W⁽²⁾", "b")], size=6.8, fill="#2E7D32", anchor="middle")

    # Căn giữa đối xứng toàn bộ 3 cụm node quanh tâm Y = 182
    y_center = 182
    y_ins = [y_center - 54, y_center - 18, y_center + 18, y_center + 54]
    y_hids = [y_center - 60, y_center - 30, y_center, y_center + 30, y_center + 60]
    y_outs = [y_center - 40, y_center, y_center + 40]

    # 1. Vẽ các đường nối Fully Connected giữa Input và Hidden (4x5 = 20 đường)
    for yi in y_ins:
        for yh in y_hids:
            alpha = math.atan2(yh - yi, x_hid - x_in)
            sx = x_in + 13 * math.cos(alpha)
            sy = yi + 13 * math.sin(alpha)
            ex = x_hid - 13 * math.cos(alpha)
            ey = yh - 13 * math.sin(alpha)
            f.a(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#90CAF9" stroke-width="0.8"/>')

    # 2. Vẽ các đường nối Fully Connected giữa Hidden và Output (5x3 = 15 đường)
    for yh in y_hids:
        for yo in y_outs:
            alpha = math.atan2(yo - yh, x_out - x_hid)
            sx = x_hid + 13 * math.cos(alpha)
            sy = yh + 13 * math.sin(alpha)
            ex = x_out - 13 * math.cos(alpha)
            ey = yo - 13 * math.sin(alpha)
            f.a(f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" stroke="#C8E6C9" stroke-width="0.9"/>')

    subscripts = ["₁", "₂", "₃", "₄", "₅"]

    # 3. Vẽ các Node Lớp Đầu Vào
    for idx, yi in enumerate(y_ins):
        f.a(f'<circle cx="{x_in}" cy="{yi}" r="13" fill="#E3F2FD" stroke="#1E88E5" stroke-width="1.3"/>')
        f.text(x_in, yi, f"x{subscripts[idx]}", size=8.5, weight=700, fill="#0D47A1", anchor="middle")

    # 4. Vẽ các Node Lớp Ẩn
    for idx, yh in enumerate(y_hids):
        f.a(f'<circle cx="{x_hid}" cy="{yh}" r="13" fill="#FFF3E0" stroke="#FB8C00" stroke-width="1.3"/>')
        f.text(x_hid, yh, f"h{subscripts[idx]}", size=8.5, weight=700, fill="#E65100", anchor="middle")

    # 5. Vẽ các Node Lớp Đầu Ra
    for idx, yo in enumerate(y_outs):
        f.a(f'<circle cx="{x_out}" cy="{yo}" r="13" fill="#E8F5E9" stroke="#43A047" stroke-width="1.3"/>')
        f.text(x_out, yo, f"o{subscripts[idx]}", size=8.5, weight=700, fill="#1B5E20", anchor="middle")

    # Chú thích chân cột
    foot_y = 265
    foot_h = 32

    rect(f, x_in - 42, foot_y, 84, foot_h, fill="#ECEFF1", stroke="#CFD8DC", sw=0.8, rx=4)
    f.text(x_in, foot_y + 11, "0 phép tính", size=6.8, weight=700, fill="#546E7A", anchor="middle")
    f.text(x_in, foot_y + 22, "(Không tính lớp)", size=6.2, italic=True, fill="#90A4AE", anchor="middle")

    rect(f, x_hid - 50, foot_y, 100, foot_h, fill="#FFE0B2", stroke="#FFB74D", sw=0.8, rx=4)
    f.text(x_hid, foot_y + 11, "Lớp tính toán 1", size=6.8, weight=700, fill="#E65100", anchor="middle")
    f.text(x_hid, foot_y + 22, "(Lớp ẩn - 5 units)", size=6.2, italic=True, fill="#FB8C00", anchor="middle")

    rect(f, x_out - 50, foot_y, 100, foot_h, fill="#C8E6C9", stroke="#81C784", sw=0.8, rx=4)
    f.text(x_out, foot_y + 11, "Lớp tính toán 2", size=6.8, weight=700, fill="#1B5E20", anchor="middle")
    f.text(x_out, foot_y + 22, "(Lớp ra - 3 units)", size=6.2, italic=True, fill="#43A047", anchor="middle")

    # ==============================================================================
    # NỬA PHẢI: BẢN CHẤT KIẾN TRÚC & QUY TẮC ĐẾM LỚP
    # ==============================================================================
    rect(f, 490, box_y, 390, box_h, fill="#FFFFFF", stroke="#B0BEC5", sw=1.0, rx=4)
    f.text(502, 70, "2. BẢN CHẤT KIẾN TRÚC & QUY TẮC ĐẾM LỚP", size=8.5, weight=700, fill="#1565C0")

    # Khối 1: Quy tắc đếm lớp kinh điển
    k1_y = 84
    k1_h = 56
    rect(f, 502, k1_y, 366, k1_h, fill="#FFFDE7", stroke="#FFF59D", sw=0.8, rx=3)
    f.text(512, k1_y + 12, "★ QUY TẮC ĐẾM SỐ LỚP CỦA MLP (D2L tr.169):", size=7.6, weight=700, fill="#F57F17")
    f.rich(512, k1_y + 27, [("• ", "b"), ("Mạng có 3 tầng node, nhưng chỉ được tính là ", "t"), ("MẠNG 2 LỚP (2-layer MLP).", "b")], size=7.2, fill=DARK)
    f.text(512, k1_y + 42, "• Lớp đầu vào không được tính vì không thực hiện phép tính và không có tham số.", size=6.8, fill="#5D4037")

    # Khối 2: Bảng đối chiếu 3 tầng
    k2_y = 148
    k2_h = 80
    rect(f, 502, k2_y, 366, k2_h, fill="#FAFAFA", stroke="#CFD8DC", sw=0.8, rx=3)
    # Header bảng
    f.a(f'<rect x="502" y="{k2_y}" width="366" height="20" fill="#ECEFF1" rx="3"/>')
    f.text(514, k2_y + 10, "Tầng", size=7.0, weight=700, fill="#37474F")
    f.text(566, k2_y + 10, "Vai trò & Phép biến đổi", size=7.0, weight=700, fill="#37474F")
    f.text(835, k2_y + 10, "Số đơn vị", size=7.0, weight=700, fill="#37474F", anchor="middle")

    # Hàng 1: Đầu vào
    f.a(f'<line x1="502" y1="{k2_y + 20}" x2="868" y2="{k2_y + 20}" stroke="#CFD8DC" stroke-width="0.6"/>')
    f.text(514, k2_y + 30, "Đầu vào", size=7.0, weight=700, fill="#0D47A1")
    f.text(566, k2_y + 30, "Nhận vector đặc trưng x ∈ ℝ⁴ (không tham số)", size=6.8, fill=DARK)
    f.text(835, k2_y + 30, "4", size=7.2, weight=700, fill="#0D47A1", anchor="middle")

    # Hàng 2: Lớp ẩn
    f.a(f'<line x1="502" y1="{k2_y + 40}" x2="868" y2="{k2_y + 40}" stroke="#CFD8DC" stroke-width="0.6"/>')
    f.text(514, k2_y + 50, "Lớp ẩn", size=7.0, weight=700, fill="#E65100")
    f.rich(566, k2_y + 50, [("Fully connected: ", "t"), ("h = φ(W⁽¹⁾x + b⁽¹⁾)", "c"), (" (đơn vị ẩn)", "t")], size=6.8, fill=DARK)
    f.text(835, k2_y + 50, "5", size=7.2, weight=700, fill="#E65100", anchor="middle")

    # Hàng 3: Đầu ra
    f.a(f'<line x1="502" y1="{k2_y + 60}" x2="868" y2="{k2_y + 60}" stroke="#CFD8DC" stroke-width="0.6"/>')
    f.text(514, k2_y + 70, "Đầu ra", size=7.0, weight=700, fill="#1B5E20")
    f.rich(566, k2_y + 70, [("Fully connected: ", "t"), ("o = W⁽²⁾h + b⁽²⁾", "c"), (" (xuất kết quả)", "t")], size=6.8, fill=DARK)
    f.text(835, k2_y + 70, "3", size=7.2, weight=700, fill="#1B5E20", anchor="middle")

    # Khối 3: Định nghĩa Fully Connected
    k3_y = 236
    k3_h = 64
    rect(f, 502, k3_y, 366, k3_h, fill="#E8F5E9", stroke="#A5D6A7", sw=0.8, rx=3)
    f.text(512, k3_y + 12, "BẢN CHẤT LIÊN KẾT ĐẦY ĐỦ (FULLY CONNECTED):", size=7.5, weight=700, fill="#1B5E20")
    f.text(512, k3_y + 27, "• Mỗi neuron tầng sau nhận tín hiệu từ toàn bộ neuron ở tầng ngay trước nó.", size=6.8, fill="#2E7D32")
    f.rich(512, k3_y + 42, [("• Tổng tham số của mạng: ", "t"), ("(4×5 + 5) + (5×3 + 3) = 25 + 18 = 43 tham số.", "b")], size=7.0, fill="#1B5E20")
    f.text(512, k3_y + 54, "  (20 trọng số + 5 bias lớp ẩn; 15 trọng số + 3 bias lớp ra).", size=6.4, italic=True, fill="#388E3C")

    source(f, 320, "Nguồn: Dive into Deep Learning (D2L 2023, tr. 167, 169 - Fig. 5.1.1).")
    return f


def fig_forward_pass_example():
    """HÌNH 3: Quá trình Lan truyền xuôi (Forward Pass) qua ví dụ số mạng 2-2-1."""
    f = Fig(W, 350)
    tier(f, "T2 chung")

    f.text(20, 24, "LAN TRUYỀN XUÔI (FORWARD PASS) QUA VÍ DỤ SỐ MẠNG 2-2-1", size=13, weight=700, fill=DARK)
    f.text(20, 42, "Minh họa tiến trình tính toán: Biến đổi affine z = W⁽¹⁾x, phi tuyến h = ReLU(z) và đầu ra o = W⁽²⁾h", size=9.2, fill=GRAY)

    # ==============================================================================
    # NỬA TRÁI: ĐỒ THỊ MẠNG 2-2-1 VÀ LUỒNG TÍN HIỆU SỐ
    # ==============================================================================
    box_y = 56
    box_h = 258
    rect(f, 20, box_y, 455, box_h, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(32, 70, "1. ĐỒ THỊ MẠNG 2-2-1 VÀ LUỒNG TÍN HIỆU SỐ", size=8.5, weight=700, fill=DARK)
    f.text(32, 83, "Đầu vào x = (1, 2) · Không bias · Kích hoạt ReLU tại lớp ẩn", size=7.0, fill=GRAY)

    # Vị trí các cột
    x_in = 65
    x_hid = 236
    x_out = 415

    # Tiêu đề các cột (nâng cao lên để tạo khoảng thở với đỉnh node ẩn)
    f.text(x_in, 95, "Lớp vào x", size=7.6, weight=700, fill="#0284C7", anchor="middle")
    f.text(x_in, 107, "x ∈ ℝ²", size=6.6, fill="#0369A1", anchor="middle")

    f.text(x_hid, 95, "Lớp ẩn h = ReLU(z)", size=7.6, weight=700, fill="#7C3AED", anchor="middle")
    f.text(x_hid, 107, "2 đơn vị ẩn · W⁽¹⁾", size=6.6, fill="#6D28D9", anchor="middle")

    f.text(x_out, 95, "Lớp ra o", size=7.6, weight=700, fill="#EA580C", anchor="middle")
    f.text(x_out, 107, "1 đơn vị ra · W⁽²⁾", size=6.6, fill="#C2410C", anchor="middle")

    # Tọa độ các node (hạ nhẹ để không chạm mép chữ tiêu đề)
    cy_in1 = 138
    cy_in2 = 216
    y_out = 177

    # 1. Vẽ các đường nối giữa Input và Hidden
    # x1 -> h1 (ngang)
    f.a(f'<line x1="{x_in + 16}" y1="{cy_in1}" x2="{x_hid - 42}" y2="{cy_in1}" stroke="#94A3B8" stroke-width="1.2" marker-end="url(#{f.marker("#94A3B8", 1.2)})"/>')
    # x2 -> h2 (ngang)
    f.a(f'<line x1="{x_in + 16}" y1="{cy_in2}" x2="{x_hid - 42}" y2="{cy_in2}" stroke="#94A3B8" stroke-width="1.2" marker-end="url(#{f.marker("#94A3B8", 1.2)})"/>')
    # x1 -> h2 (chéo xuống)
    f.a(f'<line x1="{x_in + 16}" y1="{cy_in1}" x2="{x_hid - 42}" y2="{cy_in2}" stroke="#CBD5E1" stroke-width="1.0" marker-end="url(#{f.marker("#CBD5E1", 1.0)})"/>')
    # x2 -> h1 (chéo lên)
    f.a(f'<line x1="{x_in + 16}" y1="{cy_in2}" x2="{x_hid - 42}" y2="{cy_in1}" stroke="#CBD5E1" stroke-width="1.0" marker-end="url(#{f.marker("#CBD5E1", 1.0)})"/>')

    # Trọng số W(1) trên các liên kết
    # w11 = 1 (trên line x1->h1)
    rect(f, 118, 122, 26, 13, fill="#FFFFFF", stroke="#CBD5E1", sw=0.8, rx=2)
    f.text(131, 128, "w=1", size=6.5, weight=700, fill="#0284C7", anchor="middle")

    # w22 = 0.5 (dưới line x2->h2)
    rect(f, 115, 220, 32, 13, fill="#FFFFFF", stroke="#CBD5E1", sw=0.8, rx=2)
    f.text(131, 226, "w=0.5", size=6.5, weight=700, fill="#0284C7", anchor="middle")

    # w21 = 0.5 (trên chéo x1->h2, lệch về phía x1 t=0.3)
    rect(f, 101, 155, 32, 13, fill="#FFFFFF", stroke="#CBD5E1", sw=0.8, rx=2)
    f.text(117, 161, "w=0.5", size=6.5, weight=700, fill="#0284C7", anchor="middle")

    # w12 = -1 (trên chéo x2->h1, lệch về phía h1 t=0.7)
    rect(f, 146, 155, 28, 13, fill="#FFFFFF", stroke="#CBD5E1", sw=0.8, rx=2)
    f.text(160, 161, "w=-1", size=6.5, weight=700, fill="#DC2626", anchor="middle")

    # 2. Vẽ các đường nối giữa Hidden và Output
    # h1 -> o (tín hiệu triệt tiêu do h1 = 0 -> vẽ nét đứt mờ)
    f.a(f'<line x1="{x_hid + 42}" y1="{cy_in1}" x2="{x_out - 40}" y2="{y_out}" stroke="#94A3B8" stroke-width="1.1" stroke-dasharray="3 3" marker-end="url(#{f.marker("#94A3B8", 1.1)})"/>')
    # h2 -> o (tín hiệu kích hoạt -> nét liền đậm)
    f.a(f'<line x1="{x_hid + 42}" y1="{cy_in2}" x2="{x_out - 40}" y2="{y_out}" stroke="#7C3AED" stroke-width="1.5" marker-end="url(#{f.marker("#7C3AED", 1.5)})"/>')

    # Trọng số W(2)
    # w1 = 1
    rect(f, 312, 144, 30, 13, fill="#FFFFFF", stroke="#CBD5E1", sw=0.8, rx=2)
    f.text(327, 150, "w₁=1", size=6.5, weight=700, fill="#64748B", anchor="middle")

    # w2 = 2
    rect(f, 312, 203, 30, 13, fill="#FFFFFF", stroke="#DDD6FE", sw=0.8, rx=2)
    f.text(327, 209, "w₂=2", size=6.5, weight=700, fill="#7C3AED", anchor="middle")

    # 3. Vẽ các Node Lớp Đầu Vào
    f.a(f'<circle cx="{x_in}" cy="{cy_in1}" r="16" fill="#E0F2FE" stroke="#0284C7" stroke-width="1.4"/>')
    f.text(x_in, cy_in1, "x₁ = 1", size=8.0, weight=700, fill="#0369A1", anchor="middle")

    f.a(f'<circle cx="{x_in}" cy="{cy_in2}" r="16" fill="#E0F2FE" stroke="#0284C7" stroke-width="1.4"/>')
    f.text(x_in, cy_in2, "x₂ = 2", size=8.0, weight=700, fill="#0369A1", anchor="middle")

    # 4. Vẽ các Node Lớp Ẩn (hộp hiển thị z và h)
    # Node ẩn 1: z1 = -1 -> h1 = 0 (bị triệt tiêu)
    rect(f, x_hid - 42, cy_in1 - 21, 84, 42, fill="#F8FAFC", stroke="#94A3B8", sw=1.2, dashed=True, rx=6)
    f.text(x_hid, cy_in1 - 7, "z₁ = -1.0", size=7.2, weight=700, fill="#64748B", anchor="middle")
    f.rich(x_hid, cy_in1 + 8, [("h₁ = ", "t"), ("0.0", "b")], size=8.0, fill="#DC2626", anchor="middle")
    f.text(x_hid, cy_in1 + 28, "(ReLU triệt tiêu)", size=6.0, weight=700, fill="#DC2626", anchor="middle")

    # Node ẩn 2: z2 = 1.5 -> h2 = 1.5 (kích hoạt)
    rect(f, x_hid - 42, cy_in2 - 21, 84, 42, fill="#F5F3FF", stroke="#7C3AED", sw=1.5, rx=6)
    f.text(x_hid, cy_in2 - 7, "z₂ = +1.5", size=7.2, weight=700, fill="#6D28D9", anchor="middle")
    f.rich(x_hid, cy_in2 + 8, [("h₂ = ", "t"), ("1.5", "b")], size=8.0, fill="#7C3AED", anchor="middle")
    f.text(x_hid, cy_in2 + 28, "(kích hoạt > 0)", size=6.0, weight=700, fill="#16A34A", anchor="middle")

    # 5. Vẽ Node Lớp Đầu Ra
    rect(f, x_out - 40, y_out - 23, 80, 46, fill="#FFF7ED", stroke="#EA580C", sw=1.6, rx=8)
    f.text(x_out, y_out - 10, "o = W⁽²⁾h", size=7.2, weight=700, fill="#9A3412", anchor="middle")
    f.text(x_out, y_out + 8, "= 3.0", size=11.0, weight=700, fill="#EA580C", anchor="middle")
    f.text(x_out, y_out + 31, "(kết quả mạng)", size=6.2, fill="#9A3412", anchor="middle")

    # Khung ghi chú chân bên trái
    rect(f, 30, 262, 435, 42, fill="#F1F5F9", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(38, 274, "• Bản chất: ReLU cắt cụt phần âm (z₁ = -1 < 0 ⇒ h₁ = 0), làm tắt hoàn toàn nhánh ẩn 1.", size=6.6, fill="#334155")
    f.rich(38, 290, [
        ("• Toàn bộ kết quả ra phụ thuộc nhánh ẩn 2: ", "t"),
        ("o = 1·(0) + 2·(1.5) = 0 + 3.0 = 3.0.", "b"),
    ], size=6.6, fill="#1E293B")

    # ==============================================================================
    # NỬA PHẢI: TIẾN TRÌNH TÍNH TOÁN 3 BƯỚC (FORWARD PASS)
    # ==============================================================================
    p_x = 485
    p_w = 395
    rect(f, p_x, box_y, p_w, box_h, fill="#FAFAFA", stroke="#CFD8DC", sw=1.0, rx=4)
    f.text(p_x + 12, 70, "2. TIẾN TRÌNH TÍNH TOÁN 3 BƯỚC (FORWARD PASS)", size=8.5, weight=700, fill=DARK)
    f.text(p_x + 12, 83, "Công thức tổng quát bám sát D2L Mục 5.3 [tr. 180]", size=7.0, fill=GRAY)

    # Bước 1: Biến đổi Affine z = W(1)x
    b1_y = 90
    b1_h = 67
    rect(f, p_x + 12, b1_y, p_w - 24, b1_h, fill="#F0F9FF", stroke="#BAE6FD", sw=0.9, rx=4)
    f.text(p_x + 20, b1_y + 12, "BƯỚC 1: BIẾN ĐỔI AFFINE ẨN  z = W⁽¹⁾x", size=7.4, weight=700, fill="#0369A1")
    f.rich(p_x + 20, b1_y + 27, [("• z₁ = 1·(1) + (-1)·(2) = 1 - 2 = ", "t"), ("-1.0", "b")], size=7.0, fill="#0C4A6E")
    f.rich(p_x + 20, b1_y + 41, [("• z₂ = 0.5·(1) + 0.5·(2) = 0.5 + 1.0 = ", "t"), ("1.5", "b")], size=7.0, fill="#0C4A6E")
    f.rich(p_x + 20, b1_y + 55, [("⇒ Vector trung gian: ", "t"), ("z = [-1.0,  1.5]ᵀ", "c")], size=6.8, fill="#0369A1")

    # Bước 2: Hàm kích hoạt phi tuyến h = ReLU(z)
    b2_y = 161
    b2_h = 67
    rect(f, p_x + 12, b2_y, p_w - 24, b2_h, fill="#FAF5FF", stroke="#E9D5FF", sw=0.9, rx=4)
    f.text(p_x + 20, b2_y + 12, "BƯỚC 2: HÀM KÍCH HOẠT PHI TUYẾN  h = φ(z) = ReLU(z)", size=7.4, weight=700, fill="#6B21A8")
    f.rich(p_x + 20, b2_y + 27, [("• h₁ = ReLU(-1.0) = max(-1.0, 0) = ", "t"), ("0.0", "b"), ("  (âm bị chặn dưới)", "t")], size=7.0, fill="#581C87")
    f.rich(p_x + 20, b2_y + 41, [("• h₂ = ReLU(1.5) = max(1.5, 0) = ", "t"), ("1.5", "b"), ("  (dương giữ nguyên)", "t")], size=7.0, fill="#581C87")
    f.rich(p_x + 20, b2_y + 55, [("⇒ Vector kích hoạt ẩn: ", "t"), ("h = [0.0,  1.5]ᵀ", "c")], size=6.8, fill="#6B21A8")

    # Bước 3: Tổ hợp tuyến tính đầu ra o = W(2)h
    b3_y = 232
    b3_h = 76
    rect(f, p_x + 12, b3_y, p_w - 24, b3_h, fill="#FFF7ED", stroke="#FED7AA", sw=0.9, rx=4)
    f.text(p_x + 20, b3_y + 12, "BƯỚC 3: TỔ HỢP TUYẾN TÍNH ĐẦU RA  o = W⁽²⁾h", size=7.4, weight=700, fill="#C2410C")
    f.rich(p_x + 20, b3_y + 27, [("• o = [1,  2] · [0.0,  1.5]ᵀ = 1·(0.0) + 2·(1.5)", "t")], size=7.0, fill="#7C2D12")
    f.rich(p_x + 20, b3_y + 41, [("• o = 0.0 + 3.0 = ", "t"), ("3.0", "b")], size=7.2, fill="#7C2D12")

    # Huy hiệu kết quả
    rect(f, p_x + 20, b3_y + 53, p_w - 40, 18, fill="#FFEDD5", stroke="#FB923C", sw=0.8, rx=3)
    f.text(p_x + p_w / 2, b3_y + 62, "KẾT QUẢ FORWARD PASS ĐẦU RA: o = 3.0", size=7.2, weight=700, fill="#9A3412", anchor="middle")

    source(f, 324, "Nguồn: Dive into Deep Learning (D2L 2023, tr. 180 - Section 5.3: Forward Propagation qua ví dụ số).")
    return f


def _contour_segments(fn, level, lo=-3.0, hi=3.0, n=90):
    """Đường mức fn(x1, x2) = level bằng cách cắt từng tam giác của lưới (nội suy tuyến tính)."""
    step = (hi - lo) / n
    segs = []
    for i in range(n):
        for j in range(n):
            x0, y0 = lo + i * step, lo + j * step
            x1, y1 = x0 + step, y0 + step
            for tri in (((x0, y0), (x1, y0), (x1, y1)), ((x0, y0), (x1, y1), (x0, y1))):
                v = [fn(px, py) - level for px, py in tri]
                pts = []
                for a_, b_ in ((0, 1), (1, 2), (2, 0)):
                    if (v[a_] > 0) != (v[b_] > 0):
                        t = v[a_] / (v[a_] - v[b_])
                        pts.append((tri[a_][0] + t * (tri[b_][0] - tri[a_][0]),
                                    tri[a_][1] + t * (tri[b_][1] - tri[a_][1])))
                if len(pts) == 2:
                    segs.append((pts[0], pts[1]))
    return segs


def fig_linear_collapse():
    """HÌNH 4: Vì sao mạng cần phi tuyến. Mạng 2-2-1 của mục 3: đường mức của đầu ra o khi bỏ ReLU và khi có ReLU."""
    f = Fig(W, 462)
    tier(f, "T2 chung")

    # Mạng 2-2-1 không bias (trùng mục 3 và mục 5 của trang): W1 = [[1,-1],[.5,.5]], W2 = [1, 2]
    def relu(v):
        return max(v, 0.0)

    def o_linear(x1, x2):
        return 1 * (x1 - x2) + 2 * (0.5 * x1 + 0.5 * x2)          # = 2 x1

    def o_relu(x1, x2):
        return 1 * relu(x1 - x2) + 2 * relu(0.5 * x1 + 0.5 * x2)  # = ReLU(x1 - x2) + ReLU(x1 + x2)

    assert abs(o_linear(1, 2) - 2.0) < 1e-9 and abs(o_relu(1, 2) - 3.0) < 1e-9

    f.text(20, 24, "Vì sao mạng cần phi tuyến", size=16, weight=700, fill=DARK)
    f.text(20, 44, "Mạng 2-2-1 không bias của mục 3. Đồ thị là đầu ra o theo (x₁, x₂), mỗi đường nối các điểm có cùng o.",
           size=12, fill=GRAY)

    p_y, p_h, p_w = 58, 296, 435
    ps, lo, hi = 190, -3.0, 3.0          # cạnh đồ thị (px) và miền hiển thị

    def panel(x, title, fn, shade_poly, lines, point_val, accent):
        rect(f, x, p_y, p_w, p_h, fill="#FAFAFA", stroke="#999999", sw=1.0, rx=5)
        f.text(x + 12, p_y + 18, title, size=14, weight=700, fill=DARK)
        gx, gy = x + 38, p_y + 40

        def px(v):
            return gx + (v - lo) / (hi - lo) * ps

        def py(v):
            return gy + ps - (v - lo) / (hi - lo) * ps

        # vùng o <= 0 tô xám
        pts = " ".join(f"{px(a):.1f},{py(b):.1f}" for a, b in shade_poly)
        f.a(f'<polygon points="{pts}" fill="#E0E0E0"/>')
        rect(f, gx, gy, ps, ps, fill="none", stroke="#444444", sw=1.2, rx=0)
        # đường mức o = 1..5
        for lv in (1, 2, 3, 4, 5):
            for (a1, b1), (a2, b2) in _contour_segments(fn, lv):
                strong = lv == point_val
                f.a(f'<line x1="{px(a1):.1f}" y1="{py(b1):.1f}" x2="{px(a2):.1f}" y2="{py(b2):.1f}" '
                    f'stroke="{accent if strong else "#777777"}" stroke-width="{2.4 if strong else 1.0}" '
                    f'stroke-linecap="round"/>')
        # trục, nhãn
        for t in (-3, 0, 3):
            f.text(px(t), gy + ps + 11, str(t), size=10.5, fill=DARK, anchor="middle")
            f.text(gx - 6, py(t), str(t), size=10.5, fill=DARK, anchor="end")
        f.text(gx + ps / 2, gy + ps + 26, "x₁", size=12, fill=INK, anchor="middle", italic=True)
        f.text(gx - 26, gy + ps / 2, "x₂", size=12, fill=INK, anchor="middle", italic=True)
        # điểm x = (1, 2)
        f.a(f'<circle cx="{px(1):.1f}" cy="{py(2):.1f}" r="4.5" fill="{accent}" stroke="white" stroke-width="1.2"/>')
        f.a(f'<circle cx="{gx + 6:.1f}" cy="{gy + ps + 46:.1f}" r="4.5" fill="{accent}" stroke="white" stroke-width="1.2"/>')
        f.text(gx + 16, gy + ps + 46, f"Điểm x = (1, 2) cho o = {point_val:.1f}", size=12, weight=700, fill=accent)
        # số mức o ghi trên mép trên của đồ thị, tại chỗ mỗi đường mức cắt mép đó
        f.text(gx - 20, gy - 7, "o =", size=10.5, fill=DARK, anchor="end")
        for lv in (1, 2, 3, 4, 5):
            xs = [lo + k * 0.01 for k in range(int((hi - lo) / 0.01) + 1)]
            for u, v in zip(xs, xs[1:]):
                if (fn(u, hi) - lv > 0) != (fn(v, hi) - lv > 0):
                    f.text(px((u + v) / 2), gy - 7, str(lv), size=10.5, fill=accent if lv == point_val else DARK,
                           weight=700 if lv == point_val else 400, anchor="middle")
                    break
        # cột chữ bên phải
        tx = gx + ps + 16
        for j, (parts, sz) in enumerate(lines):
            f.rich(tx, p_y + 50 + j * 19, parts, size=sz)

    panel(10, "1. Không có activation", o_linear,
          [(-3, -3), (0, -3), (0, 3), (-3, 3)],
          [([("z = W₁x = (-1, 1.5)", "t")], 11.5),
           ([("h = z, không đổi", "t")], 11.5),
           ([("o = W₂h = 2.0", "t")], 11.5),
           ([("Gộp: W = W₂W₁ = [2, 0]", "t")], 11.5),
           ([("nên o = 2x₁, chỉ phụ thuộc x₁", "t")], 11.5),
           ([("", "t")], 11.5),
           ([("Đường mức là các đường", "b")], 12),
           ([("thẳng song song.", "b")], 12),
           ([("", "t")], 11.5),
           ([("Vùng xám: o ≤ 0.", "t")], 11)],
          2, DARK)
    panel(455, "2. Có activation ReLU", o_relu,
          [(0, 0), (-3, 3), (-3, -3)],
          [([("z = W₁x = (-1, 1.5)", "t")], 11.5),
           ([("h = ReLU(z) = (0, 1.5)", "t")], 11.5),
           ([("o = W₂h = 3.0", "t")], 11.5),
           ([("o = ReLU(x₁ − x₂)", "t")], 11.5),
           ([("   + ReLU(x₁ + x₂)", "t")], 11.5),
           ([("", "t")], 11.5),
           ([("Đường mức bị gãy khúc,", "b")], 12),
           ([("không còn là đường thẳng.", "b")], 12),
           ([("", "t")], 11.5),
           ([("Vùng xám: o = 0.", "t")], 11)],
          3, BLUE)

    band_y = p_y + p_h + 10
    rect(f, 10, band_y, W - 20, 46, fill="white", stroke="#999999", sw=1.0, rx=5)
    f.rich(24, band_y + 15, [("Affine của affine vẫn là affine (5.1.2): ", "b"),
                              ("O = XW + b, với W = W⁽¹⁾W⁽²⁾ và b = b⁽¹⁾W⁽²⁾ + b⁽²⁾.", "t")], size=12.5)
    f.text(24, band_y + 33, "Hình dùng vector cột và bỏ bias, nên ở đây W = W₂W₁. Cùng đầu vào (1, 2) cho 2.0 khi bỏ ReLU và 3.0 khi có ReLU.",
           size=11.5, fill=DARK)

    source(f, band_y + 52, "Nguồn: D2L tr.170 (mục 5.1.1, công thức 5.1.2). Mạng 2-2-1, đường mức và các số o do trang tự tính, trùng với mục 3 và 5.")
    return f


def main():
    figs = [
        ("mnr-1-cau-truc-giai-phau-neuron", fig_neuron_anatomy),
        ("mnr-2-cau-truc-mang-mlp-4-5-3", fig_mlp_architecture),
        ("mnr-3-lan-truyen-xuoi-vi-du-so", fig_forward_pass_example),
        ("mnr-4-vi-sao-mang-can-phi-tuyen", fig_linear_collapse),
    ]
    run(figs, DEFAULT_OUTDIR)


if __name__ == "__main__":
    main()


