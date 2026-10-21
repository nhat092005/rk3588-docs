#!/usr/bin/env python3
"""Chuyên đề: Convolution và CNN (03-convolution-va-cnn.rst).

Sinh 4 hình minh họa kỹ thuật chuẩn visual_guide:
  - cv-1-stride-padding-dilation (T2 chung):
    Cơ chế Padding, Stride và Atrous Dilation trong Convolution.
  - cv-2-co-che-receptive-field (T2 chung):
    Cơ chế mở rộng Receptive Field qua các tầng CNN (2 lớp 3x3 vs 1 lớp 5x5).
  - cv-3-ha-bac-im2col-va-gemm (T2 chung):
    Hạ bậc tích chập về nhân ma trận GEMM qua biến đổi im2col.
  - cv-4-depthwise-pointwise-va-group-conv (T2 chung):
    Phổ phân rã tích chập: Standard Conv, Group Conv và Depthwise Separable Conv.

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 2 cấp: 03-convolution-va-cnn -> 01-kien-thuc-nen -> figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "01-nen-tang-ai", "03-convolution-va-cnn"
    )
)

W = 900


def tier(f, label):
    f.tier(W - 130, 10, label)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=3):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def card(f, x, y, w, h, title, size_t=13.5, dashed=False, fill="white", stroke="#333333"):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="1.2"{dash}/>')
    f.text(x + w / 2, y + 16, title, size=size_t, weight=700, anchor="middle", fill=INK)


def txt(f, x, y, ls, size=11.5, dy=16, fill=INK, anchor="start"):
    for i, ln in enumerate(ls):
        f.rich(x, y + dy * i, ln, size=size, anchor=anchor, fill=fill)
    return y + dy * len(ls)


def link_box(f, x, y, w, ls, size=11.5):
    """Hộp 'Liên hệ RK3588' viền xanh, huy hiệu T1."""
    h = 36 + 18 * len(ls)
    rect(f, x, y, w, h, "white", BLUE, 1.8, rx=6)
    f.tier(x + 10, y + 8, "T1 RK3588")
    f.text(x + 112, y + 19, "Liên hệ phần cứng NPU RK3588", size=13, weight=700, fill=BLUE)
    txt(f, x + 14, y + 42, ls, size=size, dy=18)
    return y + h


# =====================================================================
# HÌNH CV-1: STRIDE, PADDING VÀ ATROUS DILATION
# =====================================================================
def fig_stride_padding_dilation():
    f = Fig(W, 440)
    tier(f, "T2 chung")
    f.text(10, 42, "Cơ chế Padding, Stride và Atrous Dilation trong Convolution 2D", size=15.5, weight=700)

    # 3 PANELS
    pw = 280
    gap = 16
    py = 64
    ph = 345

    # Panel A: Padding
    pa_x = 10
    card(f, pa_x, py, pw, ph, "1. Padding (Đệm viền)", fill="#FAFAFA")
    txt(f, pa_x + 12, py + 34, [
        [("• Mục đích: ", "b"), ("Giữ nguyên kích thước hoặc", "t")],
        [("  kiểm soát mức thu nhỏ không gian.", "t")],
        [("• Same padding: ", "b"), ("Chọn ", "t"), ("p = k - 1", "c"), (" để", "t")],
        [("  đầu ra bằng kích thước đầu vào.", "t")],
    ], size=10.5, dy=14.5)

    # Lưới Padding: 4x4 data + p=1 viền quanh = 6x6
    cs_a = 21
    grid_ax = pa_x + 77
    grid_ay = py + 100
    for r in range(6):
        for c in range(6):
            is_pad = (r == 0 or r == 5 or c == 0 or c == 5)
            is_patch = (1 <= r <= 3 and 1 <= c <= 3)
            fill_c = "#FFF9C4" if is_patch else ("#F0F0F0" if is_pad else "#E3F2FD")
            stroke_c = "#E65100" if is_patch else ("#B0BEC5" if is_pad else BLUE)
            sw = 1.3 if is_patch else 0.8
            rect(f, grid_ax + c * cs_a, grid_ay + r * cs_a, cs_a, cs_a, fill_c, stroke_c, sw)
            val = "0" if is_pad else "x"
            tc = "#90A4AE" if is_pad else (DARK if not is_patch else "#E65100")
            f.text(grid_ax + c * cs_a + cs_a / 2, grid_ay + r * cs_a + cs_a / 2, val, size=9.2, anchor="middle", fill=tc)

    f.text(pa_x + pw / 2, grid_ay + 6 * cs_a + 14, "Ảnh 4×4 đệm p=1 thành 6×6", size=10.2, weight=700, anchor="middle", fill=DARK)

    # Kết quả sau conv 3x3
    rect(f, pa_x + 12, py + 254, pw - 24, 78, "#FFFFFF", "#CFD8DC", 1)
    txt(f, pa_x + 18, py + 268, [
        [("• Kích thước ra: ", "b"), ("(4 - 3 + 2 + 1) = ", "t"), ("4 × 4", "c")],
        [("• Viền màu xám ", "t"), ("0", "c"), (": Giá trị đệm padding.", "t")],
        [("• Vùng vàng: Cửa sổ kernel 3×3 đầu tiên.", "t")],
        [("• Bảo toàn thông tin rìa ảnh qua nhiều lớp.", "t")],
    ], size=9.8, dy=14.5)

    # Panel B: Stride
    pb_x = pa_x + pw + gap
    card(f, pb_x, py, pw, ph, "2. Stride (Bước trượt)", fill="#FAFAFA")
    txt(f, pb_x + 12, py + 34, [
        [("• Mục đích: ", "b"), ("Giảm độ phân giải không gian", "t")],
        [("  thay thế pooling, giảm MACs.", "t")],
        [("• s = 1: Trượt liên tục từng pixel.", "t")],
        [("• s = 2: Nhảy cách quãng 2 pixel.", "t")],
    ], size=10.5, dy=14.5)

    # Lưới Stride: 5x5, kernel 3x3, stride=2
    cs_b = 23
    grid_bx = pb_x + 82
    grid_by = py + 104
    for r in range(5):
        for c in range(5):
            is_w1 = (r < 3 and c < 3)
            is_w2 = (r < 3 and 2 <= c <= 4)
            fill_c = "#FFE082" if is_w1 else ("#E1BEE7" if is_w2 else "#FFFFFF")
            if is_w1 and is_w2:
                fill_c = "#FFCCBC"
            stroke_c = "#888888"
            rect(f, grid_bx + c * cs_b, grid_by + r * cs_b, cs_b, cs_b, fill_c, stroke_c, 0.9)
            f.text(grid_bx + c * cs_b + cs_b / 2, grid_by + r * cs_b + cs_b / 2, f"{r}{c}", size=8.8, anchor="middle", fill=DARK)

    # Khung viền 2 bước trượt
    rect(f, grid_bx, grid_by, 3 * cs_b, 3 * cs_b, "none", "#E65100", 1.8)
    rect(f, grid_bx + 2 * cs_b, grid_by, 3 * cs_b, 3 * cs_b, "none", "#8E24AA", 1.8, dashed=True)
    f.text(pb_x + pw / 2, grid_by + 5 * cs_b + 14, "Kernel 3×3 trượt với Stride s=2", size=10.2, weight=700, anchor="middle", fill=DARK)

    rect(f, pb_x + 12, py + 254, pw - 24, 78, "#FFFFFF", "#CFD8DC", 1)
    txt(f, pb_x + 18, py + 268, [
        [("• Khung cam liền: Vị trí 1 tại cột 0.", "t")],
        [("• Khung tím đứt: Vị trí 2 tại cột 2 (nhảy 2 ô).", "t")],
        [("• Kích thước ra: ", "b"), ("⌊(5 - 3)/2⌋ + 1 = ", "t"), ("2 × 2", "c")],
        [("• Giảm 4 lần số lượng pixel bản đồ đặc trưng.", "t")],
    ], size=9.8, dy=14.5)

    # Panel C: Atrous Dilation
    pc_x = pb_x + pw + gap
    card(f, pc_x, py, pw, ph, "3. Dilation (Giãn nở)", fill="#FAFAFA")
    txt(f, pc_x + 12, py + 34, [
        [("• Mục đích: ", "b"), ("Mở rộng receptive field", "t")],
        [("  mà không tăng số lượng trọng số.", "t")],
        [("• d = 1: Kernel chuẩn liền kề nhau.", "t")],
        [("• d = 2: Chèn 1 ô trống giữa các điểm.", "t")],
    ], size=10.5, dy=14.5)

    # Lưới Dilation: 5x5 footprint với 3x3 trọng số phân tán
    cs_c = 23
    grid_cx = pc_x + 82
    grid_cy = py + 104
    for r in range(5):
        for c in range(5):
            is_weight = (r % 2 == 0 and c % 2 == 0)
            fill_c = "#C8E6C9" if is_weight else "#FFFFFF"
            stroke_c = "#2E7D32" if is_weight else "#CCCCCC"
            sw = 1.4 if is_weight else 0.7
            rect(f, grid_cx + c * cs_c, grid_cy + r * cs_c, cs_c, cs_c, fill_c, stroke_c, sw)
            val = "w" if is_weight else ""
            if val:
                f.text(grid_cx + c * cs_c + cs_c / 2, grid_cy + r * cs_c + cs_c / 2, val, size=9.8, weight=700, anchor="middle", fill="#2E7D32")

    rect(f, grid_cx, grid_cy, 5 * cs_c, 5 * cs_c, "none", "#2E7D32", 1.5, dashed=True)
    f.text(pc_x + pw / 2, grid_cy + 5 * cs_c + 14, "Dilation d=2: Footprint 5×5 (9 weights)", size=10.2, weight=700, anchor="middle", fill="#2E7D32")

    rect(f, pc_x + 12, py + 254, pw - 24, 78, "#FFFFFF", "#CFD8DC", 1)
    txt(f, pc_x + 18, py + 268, [
        [("• Kích thước hiệu dụng: ", "b"), ("k' = 3 + 2(2-1) = ", "t"), ("5", "c")],
        [("• Chỉ chứa đúng 9 trọng số thực tế (ô xanh).", "t")],
        [("• Ô trắng trung gian: Bỏ qua (không tính).", "t")],
        [("• Dùng rộng rãi trong segmentation & dilated YOLO.", "t")],
    ], size=9.8, dy=14.5)

    # SOURCE DƯỚI 3 PANEL
    source(f, py + ph + 4, "Nguồn: [T2 D2L tr.248-250], [T2 CUDNN tr.3], [T1 TRM1 tr.1985]. Padding bảo toàn biên; Stride thu nhỏ; Dilation mở rộng trường quan sát.")
    return f


# =====================================================================
# HÌNH CV-2: CƠ CHẾ RECEPTIVE FIELD
# =====================================================================
def fig_receptive_field():
    f = Fig(W, 375)
    tier(f, "T2 chung")
    f.text(10, 42, "Cơ chế mở rộng Receptive Field (Trường tiếp nhận) qua các tầng CNN", size=15.5, weight=700)

    # KHỐI TRỰC QUAN XẾP CHỒNG 2 LỚP CONV 3x3
    ya, ha = 64, 280
    card(f, 10, ya, 880, ha, "Xếp chồng 2 lớp Conv 3×3: Nơ-ron tầng sâu quan sát toàn bộ vùng ảnh 5×5", fill="#FAFAFA")

    # Layer 0: Input 5x5
    cs0 = 24
    l0_x, l0_y = 35, ya + 52
    f.text(l0_x + 2.5 * cs0, l0_y - 10, "Layer 0: Ảnh đầu vào 5×5", size=11.5, weight=700, anchor="middle", fill=DARK)
    for r in range(5):
        for c in range(5):
            rect(f, l0_x + c * cs0, l0_y + r * cs0, cs0, cs0, "#FFF9C4", "#F57F17", 1.2)
            f.text(l0_x + c * cs0 + cs0 / 2, l0_y + r * cs0 + cs0 / 2, f"{r}{c}", size=9, anchor="middle", fill="#E65100")
    f.text(l0_x + 2.5 * cs0, l0_y + 5 * cs0 + 14, "RF = 5×5 (25 pixel)", size=10, weight=700, anchor="middle", fill="#E65100")

    # Mũi tên Conv 1
    f.line([(l0_x + 5 * cs0 + 8, ya + 112), (l0_x + 5 * cs0 + 50, ya + 112)], BLUE, THICK)
    f.text(l0_x + 5 * cs0 + 29, ya + 98, "Conv 3×3", size=10, weight=700, anchor="middle", fill=BLUE)
    f.text(l0_x + 5 * cs0 + 29, ya + 126, "Lớp 1", size=9.5, anchor="middle", fill=DARK)

    # Layer 1: Feature Map 3x3
    cs1 = 26
    l1_x = l0_x + 5 * cs0 + 64
    l1_y = ya + 74
    f.text(l1_x + 1.5 * cs1, ya + 42, "Layer 1: Map 3×3", size=11.5, weight=700, anchor="middle", fill=DARK)
    for r in range(3):
        for c in range(3):
            rect(f, l1_x + c * cs1, l1_y + r * cs1, cs1, cs1, "#E1BEE7", "#8E24AA", 1.2)
            f.text(l1_x + c * cs1 + cs1 / 2, l1_y + r * cs1 + cs1 / 2, f"m{r}{c}", size=9.5, anchor="middle", fill="#4A148C")
    f.text(l1_x + 1.5 * cs1, l1_y + 3 * cs1 + 14, "Mỗi pixel nhìn 3×3", size=9.8, weight=700, anchor="middle", fill="#8E24AA")

    # Mũi tên Conv 2
    f.line([(l1_x + 3 * cs1 + 8, ya + 112), (l1_x + 3 * cs1 + 50, ya + 112)], BLUE, THICK)
    f.text(l1_x + 3 * cs1 + 29, ya + 98, "Conv 3×3", size=10, weight=700, anchor="middle", fill=BLUE)
    f.text(l1_x + 3 * cs1 + 29, ya + 126, "Lớp 2", size=9.5, anchor="middle", fill=DARK)

    # Layer 2: Output 1x1
    cs2 = 34
    l2_x = l1_x + 3 * cs1 + 64
    l2_y = ya + 95
    f.text(l2_x + cs2 / 2, ya + 42, "Layer 2: Ra 1×1", size=11.5, weight=700, anchor="middle", fill=DARK)
    rect(f, l2_x, l2_y, cs2, cs2, "#C8E6C9", "#2E7D32", 1.8)
    f.text(l2_x + cs2 / 2, l2_y + cs2 / 2, "z", size=13.5, weight=700, anchor="middle", fill="#1B5E20")
    f.text(l2_x + cs2 / 2, l2_y + cs2 + 14, "RF = 5×5", size=10, weight=700, anchor="middle", fill="#2E7D32")

    # Hộp công thức mở rộng RF lấp đầy khoảng trống phía dưới bên trái
    rf_box_y = ya + 204
    rect(f, 30, rf_box_y, 485, 64, "#F0F4F8", BLUE, 1)
    f.text(42, rf_box_y + 16, "Công thức tích lũy Receptive Field qua từng tầng:", size=10.5, weight=700, fill=BLUE)
    txt(f, 42, rf_box_y + 32, [
        [("• Công thức: ", "b"), ("RF_k = RF_{k-1} + (k_l - 1) · s_{prev}", "c"), ("  (với stride s = 1)", "t")],
        [("• Tầng 1: ", "b"), ("1 + (3 - 1) = ", "t"), ("3 × 3", "c"), ("  |  ", "t"), ("Tầng 2: ", "b"), ("3 + (3 - 1) = ", "t"), ("5 × 5 (Bao trùm toàn bộ ảnh gốc)", "c")],
    ], size=9.8, dy=14.5)

    # Bảng phân tích nón tiếp nhận bên phải
    box_rx = 530
    rect(f, box_rx, ya + 36, 345, 232, "#FFFFFF", "#90A4AE", 1)
    f.text(box_rx + 172, ya + 54, "Định nghĩa & Quy luật tích lũy:", size=11.5, weight=700, anchor="middle", fill=DARK)
    txt(f, box_rx + 14, ya + 74, [
        [("• Trích dẫn D2L tr.245: ", "b")],
        [('  "its receptive field refers to all the elements', "t")],
        [('  that may affect the calculation of x during', "t")],
        [('  the forward propagation."', "t")],
        [("• Bước 1: ", "b"), ("1 phần tử ở Layer 1 phụ thuộc", "t")],
        [("  vào vùng 3×3 của Layer 0.", "t")],
        [("• Bước 2: ", "b"), ("1 phần tử ", "t"), ("z", "c"), (" ở Layer 2 phụ thuộc", "t")],
        [("  vào toàn bộ 3×3 của Layer 1.", "t")],
        [("• Kết luận: ", "b"), ("Receptive field của ", "t"), ("z", "c"), (" trên", "t")],
        [("  ảnh gốc Layer 0 bao phủ trọn vẹn ", "t"), ("5 × 5", "c"), ("!", "b")],
    ], size=10.6, dy=19)

    source(f, ya + ha + 4, "Nguồn: [T2 D2L tr.245, tr.279]. Xếp chồng hai lớp 3x3 cho cùng receptive field 5x5 nhưng giảm 28% tham số và tăng tính phi tuyến.")
    return f


# =====================================================================
# HÌNH CV-3: HẠ BẬC IM2COL VÀ NHÂN MA TRẬN GEMM
# =====================================================================
def fig_im2col_gemm():
    f = Fig(W, 445)
    tier(f, "T2 chung")
    f.text(10, 42, "Hạ bậc tích chập về nhân ma trận GEMM qua biến đổi im2col", size=15.5, weight=700)

    # KHỐI 1: CƠ CHẾ BÓC TÁCH CỬA SỔ TRƯỢT VÀ TRẢI PHẲNG (im2col)
    ya, ha = 64, 230
    card(f, 10, ya, 880, ha, "1. Biến đổi im2col: Trải các cửa sổ trượt 3D thành các cột ma trận", fill="#FAFAFA")

    # Feature Map 3x3x1
    cs = 26
    ix, iy = 30, ya + 50
    f.text(ix + 1.5 * cs, ya + 38, "Input Map (3×3)", size=11, weight=700, anchor="middle", fill=DARK)
    for r in range(3):
        for c in range(3):
            is_p0 = (r < 2 and c < 2)
            fill_c = "#FFE082" if is_p0 else "#FFFFFF"
            stroke_c = "#E65100" if is_p0 else "#90A4AE"
            rect(f, ix + c * cs, iy + r * cs, cs, cs, fill_c, stroke_c, 1.2 if is_p0 else 0.8)
            f.text(ix + c * cs + cs / 2, iy + r * cs + cs / 2, f"x{r}{c}", size=9.5, anchor="middle", fill=DARK)
    rect(f, ix, iy, 2 * cs, 2 * cs, "none", "#E65100", 1.6)
    f.text(ix + cs, iy + 3 * cs + 14, "Cửa sổ 0 (2×2)", size=9.5, weight=700, anchor="middle", fill="#E65100")

    # Khung giải thích patch dưới Input Map để lấp đầy khoảng trống
    rect(f, ix - 6, ya + 158, 126, 58, "#F0F4F8", "#CFD8DC", 1)
    txt(f, ix, ya + 170, [
        [("• 4 cửa sổ trượt 2×2", "b")],
        [("• Mỗi patch: 4 pixel", "t")],
        [("• Duỗi thành 1 cột", "c")],
    ], size=9.2, dy=14)

    # Mũi tên unroll
    f.line([(ix + 3 * cs + 18, ya + 90), (ix + 3 * cs + 64, ya + 90)], BLUE, THICK)
    f.text(ix + 3 * cs + 41, ya + 76, "im2col", size=10.5, weight=700, anchor="middle", fill=BLUE)
    f.text(ix + 3 * cs + 41, ya + 104, "Trải phẳng", size=9.2, anchor="middle", fill=DARK)

    # Ma trận D_m (duỗi theo cột: CRS x NPQ)
    mx = ix + 3 * cs + 78
    f.text(mx + 110, ya + 38, "Ma trận dữ liệu D_m (CRS × NPQ = 4 × 4)", size=11, weight=700, anchor="middle", fill=DARK)
    f.table(mx, ya + 48, [70, 38, 38, 38, 38], ["Thành phần", "Col 0", "Col 1", "Col 2", "Col 3"], [
        ["k00", "x00", "x01", "x10", "x11"],
        ["k01", "x01", "x02", "x11", "x12"],
        ["k10", "x10", "x11", "x20", "x21"],
        ["k11", "x11", "x12", "x21", "x22"],
    ], size=9.8, line_h=13.5, fills={0: "#FFF8E1", 1: "#FFF8E1", 2: "#FFF8E1", 3: "#FFF8E1"})
    f.text(mx + 110, ya + 178, "Mỗi cột là 1 cửa sổ trượt duỗi thẳng [T2 CUDNN tr.4]", size=9.5, italic=True, anchor="middle", fill="#E65100")

    # Khối ghi chú bên phải về trùng lặp dữ liệu
    note_x = mx + 242
    rect(f, note_x, ya + 38, 290, 178, "#FFFFFF", "#CFD8DC", 1)
    f.text(note_x + 145, ya + 56, "Hiện tượng Trùng lặp dữ liệu:", size=11.2, weight=700, anchor="middle", fill=RED)
    txt(f, note_x + 12, ya + 76, [
        [("• Trích dẫn CUDNN tr.4-5: ", "b")],
        [('  "each element of D is duplicated', "t")],
        [('  up to RS times in D_m."', "t")],
        [("• Điểm ảnh ", "t"), ("x11", "c"), (" xuất hiện trong ", "t"), ("cả 4 cột", "b"), ("!", "t")],
        [("• Đánh đổi lớn: ", "b"), ("Nếu tạo ma trận ", "t"), ("D_m", "c")],
        [("  tường minh trong RAM, dung lượng bộ", "t")],
        [("  nhớ phình to gấp ", "t"), ("K × K = 4 đến 9 lần", "c"), (".", "t")],
        [("• Gây nghẽn băng thông DRAM nghiêm trọng.", "t")],
    ], size=9.8, dy=17.5)

    # KHỐI 2: PHÉP NHÂN MA TRẬN GEMM (F_m x D_m = O_m)
    yb, hb = ya + ha + 12, 145
    card(f, 10, yb, 880, hb, "2. Phép nhân GEMM và Tái tạo Tensor đầu ra (O_m = F_m × D_m)", fill="#FAFAFA")

    # Căn đều phương trình GEMM ở giữa khung Card 2
    f_x = 45
    f_y = yb + 50
    f.text(f_x + 75, yb + 38, "Filters F_m (K × CRS)", size=10.5, weight=700, anchor="middle", fill=DARK)
    f.table(f_x, f_y, [46, 26, 26, 26, 26], ["Fil", "w0", "w1", "w2", "w3"], [
        ["Out 0", "w00", "w01", "w10", "w11"],
        ["Out 1", "w'0", "w'1", "w'2", "w'3"],
    ], size=9.2, line_h=13.5, fills={0: "#E8F5E9", 1: "#E8F5E9"})

    # Dấu nhân
    f.text(f_x + 172, f_y + 32, "×", size=20, weight=700, anchor="middle", fill=DARK)

    # Ma trận D_m thu nhỏ
    d_x = f_x + 195
    f.text(d_x + 85, yb + 38, "Data D_m (CRS × NPQ)", size=10.5, weight=700, anchor="middle", fill=DARK)
    f.table(d_x, f_y, [50, 30, 30, 30, 30], ["K", "c0", "c1", "c2", "c3"], [
        ["Row 0", "•", "•", "•", "•"],
        ["Row 1", "•", "•", "•", "•"],
    ], size=9.2, line_h=13.5, fills={0: "#FFF8E1", 1: "#FFF8E1"})

    # Dấu bằng
    f.text(d_x + 195, f_y + 32, "=", size=20, weight=700, anchor="middle", fill=DARK)

    # Ma trận O_m
    o_x = d_x + 218
    f.text(o_x + 85, yb + 38, "Output O_m (K × NPQ)", size=10.5, weight=700, anchor="middle", fill=GREEN)
    f.table(o_x, f_y, [50, 30, 30, 30, 30], ["Out", "p0", "p1", "p2", "p3"], [
        ["Ch 0", "y00", "y01", "y10", "y11"],
        ["Ch 1", "y'0", "y'1", "y'2", "y'3"],
    ], size=9.2, line_h=13.5, fills={0: "#C8E6C9", 1: "#C8E6C9"})

    # Reshape thành Tensor 3D
    f.line([(o_x + 185, f_y + 32), (o_x + 225, f_y + 32)], GREEN, THICK)
    f.text(o_x + 205, f_y + 18, "Reshape", size=9.5, weight=700, anchor="middle", fill=GREEN)

    t_x = o_x + 235
    rect(f, t_x, f_y, 145, 74, "#E8F5E9", GREEN, 1.2)
    f.text(t_x + 72, f_y + 20, "Output Tensor 3D", size=10.2, weight=700, anchor="middle", fill=GREEN)
    f.text(t_x + 72, f_y + 38, "C_out × H_out × W_out", size=9.2, anchor="middle", fill=DARK)
    f.text(t_x + 72, f_y + 56, "2 × 2 × 2", size=10.5, weight=700, anchor="middle", fill=GREEN)

    # SOURCE DƯỚI KHỐI 2
    source(f, yb + hb + 4, "Nguồn: [T2 CUDNN tr.4, tr.5, Fig. 1], [T2 D2L tr.658], [T1 TRM1 tr.1985]. Tích chập đưa về GEMM; NPU RK3588 dùng Implicit GEMM.")
    return f


# =====================================================================
# HÌNH CV-4: DEPTHWISE, POINTWISE VÀ GROUP CONVOLUTION
# =====================================================================
def fig_dwconv_group_conv():
    f = Fig(W, 375)
    tier(f, "T2 chung")
    f.text(10, 42, "Phổ phân rã tích chập: Standard Conv, Group Conv và Depthwise Separable Conv", size=15.5, weight=700)

    # 3 CỘT SO SÁNH TRỰC DIỆN LUỒNG KÊNH
    ya, ha = 64, 280
    pw = 280
    gap = 16

    # Cột 1: Standard Convolution
    p1_x = 10
    card(f, p1_x, ya, pw, ha, "1. Standard Conv (g = 1)", fill="#FAFAFA")
    txt(f, p1_x + 12, ya + 34, [
        [("• Kết nối dày đặc: ", "b"), ("Mọi kênh vào nối với", "t")],
        [("  mọi kênh ra (Full channel mixing).", "t")],
        [("• Filter 3D: ", "b"), ("K × K × C_in", "c"), (" cho mỗi kênh ra.", "t")],
    ], size=10.2, dy=14.5)

    # Vẽ sơ đồ kết nối kênh dày đặc
    s1_y = ya + 92
    # Input channels (4 kênh)
    for i in range(4):
        rect(f, p1_x + 25, s1_y + i * 26, 45, 18, "#E3F2FD", BLUE, 1)
        f.text(p1_x + 47, s1_y + i * 26 + 9, f"In {i}", size=8.5, anchor="middle", fill=DARK)
        # Đường nối dày đặc tới 4 kênh ra
        for j in range(4):
            f.a(f'<line x1="{p1_x + 70}" y1="{s1_y + i * 26 + 9}" x2="{p1_x + 210}" y2="{s1_y + j * 26 + 9}" stroke="#B0BEC5" stroke-width="0.7"/>')

    # Output channels
    for j in range(4):
        rect(f, p1_x + 210, s1_y + j * 26, 45, 18, "#E8F5E9", GREEN, 1)
        f.text(p1_x + 232, s1_y + j * 26 + 9, f"Out {j}", size=8.5, anchor="middle", fill=DARK)

    # Bảng số liệu cột 1
    rect(f, p1_x + 12, ya + 208, pw - 24, 60, "#FFFFFF", "#CFD8DC", 1)
    txt(f, p1_x + 18, ya + 222, [
        [("• Trọng số: ", "b"), ("C_out · C_in · K²", "c")],
        [("• Phép MAC: ", "b"), ("H · W · C_out · C_in · K²", "c")],
        [("• Chi phí tính toán cao nhất.", "t")],
    ], size=9.5, dy=13.5)

    # Cột 2: Group Convolution
    p2_x = p1_x + pw + gap
    card(f, p2_x, ya, pw, ha, "2. Group Conv (1 < g < C_in)", fill="#FAFAFA")
    txt(f, p2_x + 12, ya + 34, [
        [("• Chia ", "t"), ("g nhóm độc lập: ", "b"), ("Không có sự trao", "t")],
        [("  đổi thông tin giữa các nhóm khác nhau.", "t")],
        [("• Ma trận dạng khối chéo (block-diagonal).", "t")],
    ], size=10.2, dy=14.5)

    # Sơ đồ kết nối chia 2 nhóm (g=2)
    s2_y = ya + 96
    # Nhóm 0 (kênh 0, 1)
    rect(f, p2_x + 16, s2_y - 2, pw - 32, 48, "none", BLUE, 1, dashed=True)
    f.text(p2_x + 28, s2_y - 2, " Nhóm 0 (Kênh 0, 1) ", size=8.2, weight=700, fill=BLUE, halo="white")
    for i in range(2):
        rect(f, p2_x + 25, s2_y + i * 22, 45, 16, "#E3F2FD", BLUE, 1)
        f.text(p2_x + 47, s2_y + i * 22 + 8, f"In {i}", size=8.2, anchor="middle", fill=DARK)
        for j in range(2):
            f.a(f'<line x1="{p2_x + 70}" y1="{s2_y + i * 22 + 8}" x2="{p2_x + 195}" y2="{s2_y + j * 22 + 8}" stroke="{BLUE}" stroke-width="0.9"/>')
        rect(f, p2_x + 195, s2_y + i * 22, 45, 16, "#E8F5E9", GREEN, 1)
        f.text(p2_x + 217, s2_y + i * 22 + 8, f"Out {i}", size=8.2, anchor="middle", fill=DARK)

    # Nhóm 1 (kênh 2, 3)
    s2_y1 = s2_y + 56
    rect(f, p2_x + 16, s2_y1 - 2, pw - 32, 48, "none", "#E65100", 1, dashed=True)
    f.text(p2_x + 28, s2_y1 - 2, " Nhóm 1 (Kênh 2, 3) ", size=8.2, weight=700, fill="#E65100", halo="white")
    for i in range(2):
        rect(f, p2_x + 25, s2_y1 + i * 22, 45, 16, "#FFE082", "#E65100", 1)
        f.text(p2_x + 47, s2_y1 + i * 22 + 8, f"In {i+2}", size=8.2, anchor="middle", fill=DARK)
        for j in range(2):
            f.a(f'<line x1="{p2_x + 70}" y1="{s2_y1 + i * 22 + 8}" x2="{p2_x + 195}" y2="{s2_y1 + j * 22 + 8}" stroke="#E65100" stroke-width="0.9"/>')
        rect(f, p2_x + 195, s2_y1 + i * 22, 45, 16, "#E8F5E9", GREEN, 1)
        f.text(p2_x + 217, s2_y1 + i * 22 + 8, f"Out {i+2}", size=8.2, anchor="middle", fill=DARK)

    rect(f, p2_x + 12, ya + 208, pw - 24, 60, "#FFFFFF", "#CFD8DC", 1)
    txt(f, p2_x + 18, ya + 222, [
        [("• Trọng số: ", "b"), ("(C_out · C_in · K²) / g", "c")],
        [("• Phép MAC: ", "b"), ("Giảm chính xác ", "t"), ("g lần", "b")],
        [("• D2L tr.309: Ma trận dạng block-diagonal.", "t")],
    ], size=9.5, dy=13.5)

    # Cột 3: Depthwise Separable Conv
    p3_x = p2_x + pw + gap
    card(f, p3_x, ya, pw, ha, "3. Depthwise Separable (g = C_in)", fill="#FAFAFA")
    txt(f, p3_x + 12, ya + 34, [
        [("• Tách thành 2 bước riêng biệt: ", "b")],
        [("  1) Depthwise: Lọc không gian từng kênh.", "t")],
        [("  2) Pointwise (1×1): Trộn đặc trưng kênh.", "t")],
    ], size=10.2, dy=14.5)

    # Sơ đồ DW + PW
    s3_y = ya + 90
    # DW: song song 1-1
    for i in range(3):
        rect(f, p3_x + 20, s3_y + i * 21, 38, 16, "#E3F2FD", BLUE, 1)
        f.text(p3_x + 39, s3_y + i * 21 + 8, f"Ch {i}", size=8, anchor="middle")
        f.a(f'<line x1="{p3_x + 58}" y1="{s3_y + i * 21 + 8}" x2="{p3_x + 95}" y2="{s3_y + i * 21 + 8}" stroke="{BLUE}" stroke-width="1.2"/>')
        rect(f, p3_x + 95, s3_y + i * 21, 45, 16, "#FFF9C4", "#F57F17", 1)
        f.text(p3_x + 117, s3_y + i * 21 + 8, "K×K×1", size=8, weight=700, anchor="middle", fill="#E65100")
        f.a(f'<line x1="{p3_x + 140}" y1="{s3_y + i * 21 + 8}" x2="{p3_x + 165}" y2="{s3_y + i * 21 + 8}" stroke="{GREEN}" stroke-width="1.2"/>')

    # Pointwise box
    rect(f, p3_x + 165, s3_y, 45, 58, "#E8F5E9", GREEN, 1.2)
    f.text(p3_x + 187, s3_y + 22, "PW 1×1", size=9, weight=700, anchor="middle", fill=GREEN)
    f.text(p3_x + 187, s3_y + 38, "Trộn kênh", size=8, anchor="middle", fill=DARK)

    f.a(f'<line x1="{p3_x + 210}" y1="{s3_y + 29}" x2="{p3_x + 235}" y2="{s3_y + 29}" stroke="{GREEN}" stroke-width="1.4"/>')
    rect(f, p3_x + 235, s3_y + 9, 36, 40, "#C8E6C9", GREEN, 1)
    f.text(p3_x + 253, s3_y + 29, "Out", size=9, weight=700, anchor="middle", fill=DARK)

    # Khung tóm tắt bổ sung ở giữa lấp khoảng trống cột 3
    rect(f, p3_x + 12, ya + 156, pw - 24, 44, "#F0F4F8", GREEN, 1)
    f.text(p3_x + pw / 2, ya + 170, "Tách rời: Spatial (DW) + Channel (PW)", size=8.5, weight=700, anchor="middle", fill=GREEN)
    f.text(p3_x + pw / 2, ya + 186, "Tiết kiệm 8.41× FLOPs tính toán với K=3", size=8.5, anchor="middle", fill=DARK)

    rect(f, p3_x + 12, ya + 208, pw - 24, 60, "#FFFFFF", "#CFD8DC", 1)
    txt(f, p3_x + 18, ya + 222, [
        [("• Tỷ lệ cắt giảm: ", "b"), ("1/C_out + 1/K²", "c")],
        [("• Với K=3: Giảm ", "t"), ("8 đến 9 lần", "b"), (" phép MAC!", "t")],
        [("• MOBILENET tr.3, Eq. 5: Tiết kiệm lớn.", "t")],
    ], size=9.5, dy=13.5)

    # SOURCE DƯỚI 3 PANEL
    source(f, ya + ha + 4, "Nguồn: [T2 MOBILENET tr.2, tr.3], [T2 D2L tr.309]. Depthwise separable conv giảm 8-9 lần tính toán so với standard conv.")
    return f


# =====================================================================
# HÌNH CV-5: POOLING VÀ UPSAMPLE
# =====================================================================
def fig_pooling_upsample():
    f = Fig(W, 425)
    tier(f, "T2 chung")
    f.text(10, 42, "Cơ chế Pooling (Downsampling) và Upsampling trong CNN", size=15.5, weight=700)

    py = 64
    ph = 330

    # PANEL A: POOLING (DOWNSAMPLING)
    pa_x = 10
    pa_w = 430
    card(f, pa_x, py, pa_w, ph, "1. Pooling (Downsampling: Max Pool vs Avg Pool)", fill="#FAFAFA")
    txt(f, pa_x + 12, py + 34, [
        [("• Bản chất: ", "b"), ("Toán tử trượt không tham số (", "t"), ("Params = 0", "c"), ("), xử lý độc lập từng kênh.", "t")],
        [("• Cửa sổ 2×2, Stride = 2: ", "b"), ("Giảm 1/2 chiều cao và chiều rộng (1/4 diện tích không gian).", "t")],
    ], size=10.2, dy=14.5)

    # Input 4x4
    in_x = pa_x + 16
    in_y = py + 86
    cs_p = 22
    vals_4x4 = [
        [12, 20, 30, 0],
        [8, 12, 2, 0],
        [34, 70, 110, 25],
        [112, 100, 40, 12],
    ]
    colors_4x4 = [
        ["#E3F2FD", "#E3F2FD", "#FFE0B2", "#FFE0B2"],
        ["#E3F2FD", "#E3F2FD", "#FFE0B2", "#FFE0B2"],
        ["#E8F5E9", "#E8F5E9", "#F3E5F5", "#F3E5F5"],
        ["#E8F5E9", "#E8F5E9", "#F3E5F5", "#F3E5F5"],
    ]
    strokes_4x4 = [
        [BLUE, BLUE, "#FB8C00", "#FB8C00"],
        [BLUE, BLUE, "#FB8C00", "#FB8C00"],
        [GREEN, GREEN, "#8E24AA", "#8E24AA"],
        [GREEN, GREEN, "#8E24AA", "#8E24AA"],
    ]

    for r in range(4):
        for c in range(4):
            rect(f, in_x + c * cs_p, in_y + r * cs_p, cs_p, cs_p, colors_4x4[r][c], strokes_4x4[r][c], 1.0)
            f.text(in_x + c * cs_p + cs_p / 2, in_y + r * cs_p + cs_p / 2, str(vals_4x4[r][c]), size=9.5, anchor="middle", weight=600)

    f.text(in_x + 2 * cs_p, in_y + 4 * cs_p + 14, "Đầu vào 4×4 (4 vùng 2×2)", size=10, weight=700, anchor="middle", fill=DARK)

    # Nhánh Max Pooling
    out_max_x = pa_x + 195
    out_max_y = py + 76
    f.line([(in_x + 4 * cs_p + 6, in_y + 20), (out_max_x - 6, out_max_y + 22)], BLUE, THIN)
    f.text(out_max_x + 2 * cs_p + 10, out_max_y - 8, "Max Pooling (2×2, s=2)", size=10.5, weight=700, fill=BLUE)

    max_vals = [[20, 30], [112, 110]]
    for r in range(2):
        for c in range(2):
            rect(f, out_max_x + c * cs_p, out_max_y + r * cs_p, cs_p, cs_p, colors_4x4[r * 2][c * 2], strokes_4x4[r * 2][c * 2], 1.2)
            f.text(out_max_x + c * cs_p + cs_p / 2, out_max_y + r * cs_p + cs_p / 2, str(max_vals[r][c]), size=10, anchor="middle", weight=700)

    txt(f, out_max_x + 2 * cs_p + 10, out_max_y + 16, [
        [("• Lấy giá trị cực đại trong từng ô 2×2.", "t")],
        [("• Giữ lại đặc trưng biên, vân nổi bật.", "t")],
        [("• Bất biến với dịch chuyển nhỏ.", "t")],
    ], size=9.5, dy=13.5)

    # Nhánh Average Pooling
    out_avg_x = pa_x + 195
    out_avg_y = py + 165
    f.line([(in_x + 4 * cs_p + 6, in_y + 68), (out_avg_x - 6, out_avg_y + 22)], GREEN, THIN)
    f.text(out_avg_x + 2 * cs_p + 10, out_avg_y - 8, "Average Pooling (2×2, s=2)", size=10.5, weight=700, fill=GREEN)

    avg_vals = [[13, 8], [79, 47]]
    for r in range(2):
        for c in range(2):
            rect(f, out_avg_x + c * cs_p, out_avg_y + r * cs_p, cs_p, cs_p, colors_4x4[r * 2][c * 2], strokes_4x4[r * 2][c * 2], 1.2)
            f.text(out_avg_x + c * cs_p + cs_p / 2, out_avg_y + r * cs_p + cs_p / 2, str(avg_vals[r][c]), size=10, anchor="middle", weight=700)

    txt(f, out_avg_x + 2 * cs_p + 10, out_avg_y + 16, [
        [("• Lấy trung bình cộng từng ô 2×2.", "t")],
        [("• Làm mịn đặc trưng, triệt tiêu nhiễu.", "t")],
        [("• Dùng ở Global Avg Pool (GAP) cuối mạng.", "t")],
    ], size=9.5, dy=13.5)

    # Ghi chú dưới Panel A
    rect(f, pa_x + 12, py + 252, pa_w - 24, 68, "#FFFFFF", "#CFD8DC", 1)
    txt(f, pa_x + 18, py + 266, [
        [("• Không có tham số học: ", "b"), ("Params = 0, chỉ thực hiện phép so sánh hoặc cộng chia.", "t")],
        [("• Xử lý kênh độc lập: ", "b"), ("Số kênh ra = Số kênh vào (C_out = C_in), không trộn kênh.", "t")],
        [("• NPU RK3588: Xử lý trực tiếp trong nhân DPU mà không tiêu tốn mảng MAC.", "t")],
    ], size=9.6, dy=14.5)

    # PANEL B: UPSAMPLING (MỞ RỘNG KHÔNG GIAN)
    pb_x = 460
    pb_w = 430
    card(f, pb_x, py, pb_w, ph, "2. Upsampling (Nội suy Nearest vs Transposed Conv)", fill="#FAFAFA")
    txt(f, pb_x + 12, py + 34, [
        [("• Bản chất: ", "b"), ("Phục hồi hoặc mở rộng độ phân giải không gian (FPN, Decoder).", "t")],
        [("• Hai cách tiếp cận: ", "b"), ("Nội suy không tham số (Nearest) vs Tích chập học được.", "t")],
    ], size=10.2, dy=14.5)

    # Input 2x2
    in2_x = pb_x + 16
    in2_y = py + 86
    cs_u2 = 28
    u_vals_2x2 = [[1, 2], [3, 4]]
    u_cols_2x2 = [["#E3F2FD", "#FFE0B2"], ["#E8F5E9", "#F3E5F5"]]
    u_strs_2x2 = [[BLUE, "#FB8C00"], [GREEN, "#8E24AA"]]

    for r in range(2):
        for c in range(2):
            rect(f, in2_x + c * cs_u2, in2_y + r * cs_u2, cs_u2, cs_u2, u_cols_2x2[r][c], u_strs_2x2[r][c], 1.2)
            f.text(in2_x + c * cs_u2 + cs_u2 / 2, in2_y + r * cs_u2 + cs_u2 / 2, str(u_vals_2x2[r][c]), size=12, anchor="middle", weight=700)

    f.text(in2_x + cs_u2, in2_y + 2 * cs_u2 + 14, "Đầu vào 2×2", size=10, weight=700, anchor="middle", fill=DARK)

    # Nhánh Nearest Neighbor Upsample
    out_nn_x = pb_x + 180
    out_nn_y = py + 74
    f.line([(in2_x + 2 * cs_u2 + 6, in2_y + 16), (out_nn_x - 6, out_nn_y + 26)], BLUE, THIN)
    f.text(out_nn_x + 4 * 14 + 10, out_nn_y - 8, "Nearest Neighbor (Scale 2×)", size=10.5, weight=700, fill=BLUE)

    cs_nn = 13.5
    for r in range(4):
        for c in range(4):
            sr = 0 if r < 2 else 1
            sc = 0 if c < 2 else 1
            rect(f, out_nn_x + c * cs_nn, out_nn_y + r * cs_nn, cs_nn, cs_nn, u_cols_2x2[sr][sc], u_strs_2x2[sr][sc], 0.8)
            f.text(out_nn_x + c * cs_nn + cs_nn / 2, out_nn_y + r * cs_nn + cs_nn / 2, str(u_vals_2x2[sr][sc]), size=8.5, anchor="middle")

    txt(f, out_nn_x + 4 * cs_nn + 10, out_nn_y + 14, [
        [("• Sao chép giá trị gần nhất vào ô 2×2.", "t")],
        [("• Params = 0, không cần học trọng số.", "t")],
        [("• Cực nhẹ, ưu tiên dùng trong YOLO Neck.", "t")],
    ], size=9.5, dy=13.5)

    # Nhánh Transposed Convolution (Deconvolution)
    out_tc_x = pb_x + 180
    out_tc_y = py + 165
    f.line([(in2_x + 2 * cs_u2 + 6, in2_y + 40), (out_tc_x - 6, out_tc_y + 26)], RED, THIN)
    f.text(out_tc_x + 4 * 14 + 10, out_tc_y - 8, "Transposed Conv (Deconv Wᵀ)", size=10.5, weight=700, fill=RED)

    for r in range(4):
        for c in range(4):
            rect(f, out_tc_x + c * cs_nn, out_tc_y + r * cs_nn, cs_nn, cs_nn, "#FFFDE7", "#F57F17", 0.8)
            f.text(out_tc_x + c * cs_nn + cs_nn / 2, out_tc_y + r * cs_nn + cs_nn / 2, "w·x", size=7.5, anchor="middle", fill="#F57F17")

    txt(f, out_tc_x + 4 * cs_nn + 10, out_tc_y + 14, [
        [("• Nhân từng điểm ảnh với kernel W", "t")],
        [("  rồi cộng dồn.", "t")],
        [("• Có tham số: C_out × C_in × k².", "t")],
        [("• Tương đương nhân với ma trận chuyển vị Wᵀ.", "t")],
    ], size=9.5, dy=13.5)

    # Ghi chú dưới Panel B
    rect(f, pb_x + 12, py + 252, pb_w - 24, 68, "#FFFFFF", "#CFD8DC", 1)
    txt(f, pb_x + 18, py + 266, [
        [("• So sánh tài nguyên: ", "b"), ("Nearest Neighbor không tốn MAC, chỉ sao chép bộ nhớ.", "t")],
        [("• Transposed Conv: ", "b"), ("Tốn mảng MAC và dễ gây hiệu ứng ca-rô (checkerboard artifacts).", "t")],
        [("• Kiến trúc hiện đại: ", "b"), ("YOLOv5/v8, RetinaNet đều dùng Resize Nearest trong FPN/PAN.", "t")],
    ], size=9.6, dy=14.5)

    # SOURCE DƯỚI 2 PANEL
    source(f, py + ph + 4, "Nguồn: [T2 D2L tr.258, tr.261, tr.655, tr.658]. Pooling không tham số; Transposed conv tương đương Wᵀ.")
    return f


# =====================================================================
# HÌNH CV-6: KHỐI RESIDUAL VÀ TOÁN TỬ ADD
# =====================================================================
def fig_residual_add():
    f = Fig(W, 425)
    tier(f, "T2 chung")
    f.text(10, 42, "Cấu trúc Khối Residual, Nhánh Shortcut và Dung hợp Toán tử Add", size=15.5, weight=700)

    py = 64
    ph = 330

    # PANEL A: IDENTITY SHORTCUT
    pa_x = 10
    pa_w = 280
    card(f, pa_x, py, pa_w, ph, "1. Identity Residual (C_in = C_out)", fill="#FAFAFA")
    txt(f, pa_x + 12, py + 34, [
        [("• Điều kiện: ", "b"), ("Cùng số kênh, Stride = 1.", "t")],
        [("• Nhánh tắt: ", "b"), ("Dây nối trực tiếp ", "t"), ("x", "c"), (" không qua trọng số.", "t")],
    ], size=10.2, dy=14.5)

    # Sơ đồ khối Identity
    cxa = pa_x + 115
    # Input x
    rect(f, cxa - 50, py + 68, 100, 26, "#E3F2FD", BLUE, 1.2)
    f.text(cxa, py + 81, "Đầu vào x", size=11, weight=700, anchor="middle", fill=BLUE)

    # Điểm rẽ nhánh
    f.line([(cxa, py + 94), (cxa, py + 106)], INK, THIN, head=False)
    f.a(f'<circle cx="{cxa}" cy="{py + 106}" r="3.5" fill="{INK}"/>')

    # Nhánh chính (Weight Layer 1 & 2)
    f.line([(cxa, py + 106), (cxa, py + 118)], INK, THIN)
    rect(f, cxa - 60, py + 118, 120, 24, "white", DARK, 1.2)
    f.text(cxa, py + 130, "Conv 3×3, BN, ReLU", size=9.8, weight=600, anchor="middle")

    f.line([(cxa, py + 142), (cxa, py + 154)], INK, THIN)
    rect(f, cxa - 60, py + 154, 120, 24, "white", DARK, 1.2)
    f.text(cxa, py + 166, "Conv 3×3, BN", size=9.8, weight=600, anchor="middle")

    f.line([(cxa, py + 178), (cxa, py + 196)], INK, THIN)

    # Nhánh Identity Shortcut (rẽ phải, chạy xuống, rẽ trái)
    f.line([(cxa, py + 106), (pa_x + 225, py + 106), (pa_x + 225, py + 208), (cxa + 14, py + 208)], BLUE, THICK)
    f.text(pa_x + 230, py + 155, "Identity x", size=10, weight=700, fill=BLUE)

    # Toán tử Add
    f.a(f'<circle cx="{cxa}" cy="{py + 208}" r="12" fill="#FFF9C4" stroke="#FBC02D" stroke-width="1.5"/>')
    f.text(cxa, py + 208, "+", size=16, weight=700, anchor="middle", fill="#E65100")

    # Sau Add qua ReLU cuối
    f.line([(cxa, py + 220), (cxa, py + 234)], INK, THIN)
    rect(f, cxa - 40, py + 234, 80, 22, "#F5F5F5", DARK, 1.2)
    f.text(cxa, py + 245, "ReLU", size=10.5, weight=700, anchor="middle", fill=INK)

    # Output y
    f.line([(cxa, py + 256), (cxa, py + 268)], INK, THIN)
    rect(f, cxa - 60, py + 268, 120, 26, "#E3F2FD", BLUE, 1.2)
    f.text(cxa, py + 281, "Đầu ra y = F(x) + x", size=10.2, weight=700, anchor="middle", fill=BLUE)

    # Box giải thích gradient
    f.text(pa_x + pa_w / 2, py + 312, "Gradient: ∂L/∂x = ∂L/∂y · (∂F/∂x + 1)", size=9.8, weight=700, anchor="middle", fill=DARK)

    # PANEL B: PROJECTION SHORTCUT
    pb_x = 306
    pb_w = 280
    card(f, pb_x, py, pb_w, ph, "2. Projection Residual (C_in ≠ C_out)", fill="#FAFAFA")
    txt(f, pb_x + 12, py + 34, [
        [("• Điều kiện: ", "b"), ("Tăng kênh hoặc giảm không gian (Stride=2).", "t")],
        [("• Nhánh tắt: ", "b"), ("Phải qua ", "t"), ("Conv 1×1 (s=2)", "c"), (" để khớp shape.", "t")],
    ], size=10.2, dy=14.5)

    # Sơ đồ khối Projection
    cxb = pb_x + 115
    # Input x [H × W × C_in]
    rect(f, cxb - 55, py + 68, 110, 26, "#E3F2FD", BLUE, 1.2)
    f.text(cxb, py + 81, "x [H × W × C_in]", size=10.2, weight=700, anchor="middle", fill=BLUE)

    # Điểm rẽ nhánh
    f.line([(cxb, py + 94), (cxb, py + 106)], INK, THIN, head=False)
    f.a(f'<circle cx="{cxb}" cy="{py + 106}" r="3.5" fill="{INK}"/>')

    # Nhánh chính (Stride=2)
    f.line([(cxb, py + 106), (cxb, py + 118)], INK, THIN)
    rect(f, cxb - 62, py + 118, 124, 24, "white", DARK, 1.2)
    f.text(cxb, py + 130, "Conv 3×3 (s=2), BN, ReLU", size=9.2, weight=600, anchor="middle")

    f.line([(cxb, py + 142), (cxb, py + 154)], INK, THIN)
    rect(f, cxb - 62, py + 154, 124, 24, "white", DARK, 1.2)
    f.text(cxb, py + 166, "Conv 3×3, BN", size=9.2, weight=600, anchor="middle")

    f.line([(cxb, py + 178), (cxb, py + 196)], INK, THIN)

    # Nhánh Projection Shortcut qua Conv 1x1 (hoàn toàn tách biệt, không đè lấn)
    x_sc = pb_x + 228
    f.line([(cxb, py + 106), (x_sc, py + 106), (x_sc, py + 138)], BLUE, THIN)
    rect(f, x_sc - 38, py + 138, 76, 26, "#E3F2FD", BLUE, 1.2, rx=3)
    f.text(x_sc, py + 151, "Conv 1×1 (s=2)", size=9, weight=700, anchor="middle", fill=BLUE)
    f.line([(x_sc, py + 164), (x_sc, py + 208), (cxb + 14, py + 208)], BLUE, THIN)

    # Toán tử Add
    f.a(f'<circle cx="{cxb}" cy="{py + 208}" r="12" fill="#FFF9C4" stroke="#FBC02D" stroke-width="1.5"/>')
    f.text(cxb, py + 208, "+", size=16, weight=700, anchor="middle", fill="#E65100")

    # Sau Add qua ReLU cuối
    f.line([(cxb, py + 220), (cxb, py + 234)], INK, THIN)
    rect(f, cxb - 40, py + 234, 80, 22, "#F5F5F5", DARK, 1.2)
    f.text(cxb, py + 245, "ReLU", size=10.5, weight=700, anchor="middle", fill=INK)

    # Output y
    f.line([(cxb, py + 256), (cxb, py + 268)], INK, THIN)
    rect(f, cxb - 62, py + 268, 124, 26, "#E3F2FD", BLUE, 1.2)
    f.text(cxb, py + 281, "y [H/2 × W/2 × C_out]", size=10, weight=700, anchor="middle", fill=BLUE)

    # Box giải thích Params trên shortcut
    f.text(pb_x + pb_w / 2, py + 312, "Shortcut có trọng số: C_out × C_in × 1×1", size=9.8, weight=700, anchor="middle", fill=DARK)

    # PANEL C: ADD FUSION TRÊN RK3588
    pc_x = 602
    pc_w = 288
    card(f, pc_x, py, pc_w, ph, "3. Dung hợp Add (Fusion) trên RK3588", fill="#FAFAFA")
    txt(f, pc_x + 12, py + 34, [
        [("• Vấn đề: ", "b"), ("Nếu Add tách rời, NPU phải ghi và đọc", "t")],
        [("  2 mảng tensor qua lại bộ nhớ DRAM ngoài.", "t")],
        [("• Giải pháp RKNN: ", "b"), ("Dung hợp Add trực tiếp vào SRAM.", "t")],
    ], size=10.2, dy=14.5)

    # So sánh 2 sơ đồ: Trên không fusion, dưới có fusion
    # Không fusion
    rect(f, pc_x + 12, py + 78, pc_w - 24, 84, "white", "#E0E0E0", 1)
    f.text(pc_x + 20, py + 92, "A. Không dung hợp (Tiêu tốn DRAM)", size=10.2, weight=700, fill=RED)
    rect(f, pc_x + 20, py + 104, 70, 20, "white", DARK, 1)
    f.text(pc_x + 55, py + 114, "Conv Layer", size=9, anchor="middle")
    f.line([(pc_x + 90, py + 114), (pc_x + 110, py + 114)], RED, THIN)
    rect(f, pc_x + 110, py + 104, 60, 20, "#FFEBEE", RED, 1)
    f.text(pc_x + 140, py + 114, "Ghi DRAM", size=8.5, weight=700, anchor="middle", fill=RED)
    f.line([(pc_x + 170, py + 114), (pc_x + 190, py + 114)], RED, THIN)
    rect(f, pc_x + 190, py + 104, 65, 20, "white", DARK, 1)
    f.text(pc_x + 222, py + 114, "Add Operator", size=9, anchor="middle")
    f.text(pc_x + 20, py + 140, "=> Đọc/ghi DRAM 3 lần, nghẽn băng thông bộ nhớ ngoài.", size=9.2, fill=DARK)

    # Có fusion trên RKNN
    rect(f, pc_x + 12, py + 185, pc_w - 24, 130, "#E8F5E9", GREEN, 1.2)
    f.text(pc_x + 20, py + 201, "B. Dung hợp RKNN (Add Fusion trên SRAM)", size=10.2, weight=700, fill=GREEN)

    rect(f, pc_x + 20, py + 215, pc_w - 40, 42, "white", GREEN, 1.2)
    f.text(pc_x + (pc_w - 40) / 2 + 20, py + 228, "[Khối Fused: Conv + BN + Add + ReLU]", size=10, weight=700, anchor="middle", fill=GREEN)
    f.text(pc_x + (pc_w - 40) / 2 + 20, py + 244, "Thực thi trọn vẹn trong SRAM nội bộ NPU", size=9.2, anchor="middle", fill=DARK)

    f.line([(pc_x + pc_w / 2, py + 257), (pc_x + pc_w / 2, py + 272)], GREEN, THIN)
    rect(f, pc_x + 60, py + 272, pc_w - 120, 22, "#E8F5E9", GREEN, 1)
    f.text(pc_x + pc_w / 2, py + 283, "Ghi DRAM duy nhất 1 lần", size=9.5, weight=700, anchor="middle", fill=GREEN)

    f.text(pc_x + 20, py + 306, "=> Tiết kiệm 66% lưu lượng DRAM, hạ độ trễ pipeline.", size=9.2, weight=700, fill=GREEN)

    # SOURCE DƯỚI 3 PANEL
    source(f, py + ph + 4, "Nguồn: [T2 D2L tr.304, tr.306, Fig. 8.6.2]. Khối ResNet học ánh xạ phần dư g(x) = f(x) - x; liên hệ RKNN Graph Fusion.")
    return f


# =====================================================================
# HÌNH CV-7: PHÂN TẦNG ĐẶC TRƯNG VÀ GHÉP KHỐI CNN
# =====================================================================
def fig_feature_hierarchy():
    f = Fig(W, 380)
    tier(f, "T2 chung")
    f.text(10, 42, "Phân tầng Đặc trưng (Feature Hierarchy) và Luồng Tensor trong CNN", size=15.5, weight=700)

    # Helper vẽ khối 3D Tensor (Cuboid) có tâm mặt trước tại (cx, cy)
    def draw_cuboid(cx, cy, w, h, dx, dy, fill, stroke, sw=1.1):
        # Tọa độ góc trên bên trái mặt trước
        fx = cx - (w + dx) / 2
        fy = cy - h / 2
        # Mặt trên (Top face)
        pts_top = [f"{fx},{fy}", f"{fx + dx},{fy - dy}", f"{fx + w + dx},{fy - dy}", f"{fx + w},{fy}"]
        f.a(f'<polygon points="{" ".join(pts_top)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="0.8"/>')
        # Mặt bên phải (Right face)
        pts_side = [f"{fx + w},{fy}", f"{fx + w + dx},{fy - dy}", f"{fx + w + dx},{fy + h - dy}", f"{fx + w},{fy + h}"]
        f.a(f'<polygon points="{" ".join(pts_side)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" opacity="0.6"/>')
        # Mặt trước (Front face)
        f.a(f'<rect x="{fx}" y="{fy}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        return fx, fx + w + dx

    # KHUNG PHẦN 1: TIẾN TRÌNH TRỰC QUAN LUỒNG KIẾN TRÚC
    py = 64
    ph = 224
    # Vẽ khung không dùng card() để tránh tiêu đề card ở giữa đè lên tiêu đề các Stage
    rect(f, 10, py, 880, ph, fill="#FAFAFA", stroke="#333333", sw=1.2, rx=5)
    f.text(24, py + 16, "Tiến trình phân tầng đặc trưng: Từ điểm ảnh thô đến biểu diễn ngữ nghĩa trừu tượng", size=12.5, weight=700, fill=DARK)

    # ĐỊNH NGHĨA 4 TRỤC ĐỨNG TRUNG TÂM (CENTER AXES)
    cx0 = 75   # Ảnh đầu vào
    cx1 = 205  # Tầng nông (Stage 1)
    cx2 = 345  # Tầng giữa (Stage 3)
    cx3 = 495  # Tầng sâu (Stage 5)
    cy_mid = 205  # Đường trục nằm ngang trung tâm của các khối Tensor

    # --- 1. TIÊU ĐỀ TRÊN CÙNG CỦA MỖI STAGE (y = 100) ---
    f.text(cx0, 100, "Ảnh đầu vào", size=11, weight=700, anchor="middle", fill=BLUE)
    f.text(cx1, 100, "Tầng nông (Stage 1)", size=11, weight=700, anchor="middle", fill=GREEN)
    f.text(cx2, 100, "Tầng giữa (Stage 3)", size=11, weight=700, anchor="middle", fill="#E65100")
    f.text(cx3, 100, "Tầng sâu (Stage 5)", size=11, weight=700, anchor="middle", fill="#8E24AA")

    # --- 2. BONG BÓNG MINH HỌA ĐẶC TRƯNG THỊ GIÁC (y = 118, h = 42) ---
    by = 118
    bh = 42

    # Bubble 0: Pixel RGB
    bw0 = 92
    bx0 = cx0 - bw0 / 2
    rect(f, bx0, by, bw0, bh, "white", BLUE, 1, rx=4)
    # Icon pixel grid 3x3
    for r in range(3):
        for c in range(3):
            pcol = "#FFCDD2" if c == 0 else ("#C8E6C9" if c == 1 else "#BBDEFB")
            rect(f, bx0 + 36 + c * 7, by + 5 + r * 7, 6, 6, pcol, "#B0BEC5", 0.6)
    f.text(cx0, by + 32, "Điểm ảnh RGB thô", size=8.5, weight=700, anchor="middle", fill=BLUE)

    # Bubble 1: Edges & Corners
    bw1 = 98
    bx1 = cx1 - bw1 / 2
    rect(f, bx1, by, bw1, bh, "white", GREEN, 1, rx=4)
    f.a(f'<line x1="{bx1 + 14}" y1="{by + 13}" x2="{bx1 + 28}" y2="{by + 13}" stroke="{DARK}" stroke-width="1.8"/>')
    f.a(f'<line x1="{bx1 + 38}" y1="{by + 6}" x2="{bx1 + 38}" y2="{by + 20}" stroke="{DARK}" stroke-width="1.8"/>')
    f.a(f'<line x1="{bx1 + 48}" y1="{by + 19}" x2="{bx1 + 60}" y2="{by + 7}" stroke="{DARK}" stroke-width="1.8"/>')
    f.a(f'<path d="M{bx1 + 70} {by + 7} L{bx1 + 70} {by + 19} L{bx1 + 82} {by + 19}" fill="none" stroke="{DARK}" stroke-width="1.8"/>')
    f.text(cx1, by + 32, "Cạnh biên & Góc nhọn", size=8.5, weight=700, anchor="middle", fill=GREEN)

    # Bubble 2: Textures & Motifs
    bw2 = 102
    bx2 = cx2 - bw2 / 2
    rect(f, bx2, by, bw2, bh, "white", "#FBC02D", 1, rx=4)
    for k in range(3):
        f.a(f'<line x1="{bx2 + 14 + k * 5}" y1="{by + 6}" x2="{bx2 + 14 + k * 5}" y2="{by + 20}" stroke="{DARK}" stroke-width="1.2"/>')
    f.a(f'<circle cx="{bx2 + 42}" cy="{by + 13}" r="6" fill="none" stroke="{DARK}" stroke-width="1.2"/>')
    f.a(f'<rect x="{bx2 + 58}" y="{by + 7}" width="11" height="11" fill="none" stroke="{DARK}" stroke-width="1.2"/>')
    f.a(f'<path d="M{bx2 + 77} {by + 17} Q{bx2 + 83} {by + 7} {bx2 + 89} {by + 17}" fill="none" stroke="{DARK}" stroke-width="1.2"/>')
    f.text(cx2, by + 32, "Hoa văn & Vân lưới", size=8.5, weight=700, anchor="middle", fill="#E65100")

    # Bubble 3: Object Parts
    bw3 = 106
    bx3 = cx3 - bw3 / 2
    rect(f, bx3, by, bw3, bh, "white", "#8E24AA", 1, rx=4)
    f.a(f'<circle cx="{bx3 + 16}" cy="{by + 13}" r="4.5" fill="none" stroke="{DARK}" stroke-width="1.2"/>')
    f.a(f'<circle cx="{bx3 + 28}" cy="{by + 13}" r="4.5" fill="none" stroke="{DARK}" stroke-width="1.2"/>')
    f.a(f'<line x1="{bx3 + 20.5}" y1="{by + 13}" x2="{bx3 + 23.5}" y2="{by + 13}" stroke="{DARK}" stroke-width="1.2"/>')
    f.a(f'<circle cx="{bx3 + 48}" cy="{by + 13}" r="7" fill="none" stroke="{DARK}" stroke-width="1.2"/>')
    f.a(f'<circle cx="{bx3 + 48}" cy="{by + 13}" r="2.5" fill="{DARK}"/>')
    f.a(f'<rect x="{bx3 + 67}" y="{by + 7}" width="16" height="12" rx="3" fill="none" stroke="{DARK}" stroke-width="1.2"/>')
    f.text(cx3, by + 32, "Bộ phận vật thể ngữ nghĩa", size=8.2, weight=700, anchor="middle", fill="#8E24AA")

    # --- 3. VẼ CÁC KHỐI 3D TENSOR CÂN GIỮA TRỤC DỌC ---
    l0, r0 = draw_cuboid(cx0, cy_mid, 50, 50, 8, 6, "#E3F2FD", BLUE)
    l1, r1 = draw_cuboid(cx1, cy_mid, 40, 40, 16, 12, "#E8F5E9", GREEN)
    l2, r2 = draw_cuboid(cx2, cy_mid, 30, 30, 30, 18, "#FFF9C4", "#FBC02D")
    l3, r3 = draw_cuboid(cx3, cy_mid, 20, 20, 54, 26, "#F3E5F5", "#8E24AA")

    # Mũi tên kết nối giữa các khối chạy thẳng hàng ngang ở cy_mid
    f.line([(r0 + 6, cy_mid), (l1 - 6, cy_mid)], BLUE, THIN)
    f.text((r0 + l1) / 2, cy_mid - 11, "s=2", size=8.5, weight=700, anchor="middle", fill=BLUE)

    f.line([(r1 + 6, cy_mid), (l2 - 6, cy_mid)], BLUE, THIN)
    f.text((r1 + l2) / 2, cy_mid - 11, "s=4", size=8.5, weight=700, anchor="middle", fill=BLUE)

    f.line([(r2 + 6, cy_mid), (l3 - 6, cy_mid)], BLUE, THIN)
    f.text((r2 + l3) / 2, cy_mid - 11, "s=4", size=8.5, weight=700, anchor="middle", fill=BLUE)

    # --- 4. NHÃN KÍCH THƯỚC VÀ THÔNG SỐ DƯỚI MỖI KHỐI (y = 248, 262) ---
    f.text(cx0, 248, "640 × 640 × 3", size=9.8, weight=700, anchor="middle", fill=DARK)
    f.text(cx0, 262, "(Pixel RGB)", size=8.8, anchor="middle", fill=GRAY)

    f.text(cx1, 248, "320 × 320 × 64", size=9.8, weight=700, anchor="middle", fill=DARK)
    f.text(cx1, 262, "(RF: 3×3 – 7×7)", size=8.8, anchor="middle", fill=GRAY)

    f.text(cx2, 248, "80 × 80 × 256", size=9.8, weight=700, anchor="middle", fill=DARK)
    f.text(cx2, 262, "(RF: 15×15 – 35×35)", size=8.8, anchor="middle", fill=GRAY)

    f.text(cx3, 248, "20 × 20 × 1024", size=9.8, weight=700, anchor="middle", fill=DARK)
    f.text(cx3, 262, "(RF: Bao trùm toàn ảnh)", size=8.8, anchor="middle", fill=GRAY)

    # --- 5. TÁCH NHÁNH SANG TASK HEADS (BÊN PHẢI) ---
    hx = 612
    hw = 264
    y_head_a = 98
    h_head_a = 54
    cy_head_a = y_head_a + h_head_a / 2  # 125

    y_head_b = 168
    h_head_b = 82
    cy_head_b = y_head_b + h_head_b / 2  # 209

    # Đường phân nhánh đối xứng từ r3
    x_split = 572
    f.line([(r3 + 6, cy_mid), (x_split, cy_mid)], DARK, THIN, head=False)
    f.line([(x_split, cy_mid), (x_split, cy_head_a), (hx - 6, cy_head_a)], INK, THIN)
    f.line([(x_split, cy_mid), (x_split, cy_head_b), (hx - 6, cy_head_b)], INK, THIN)

    # Head A: Phân loại
    rect(f, hx, y_head_a, hw, h_head_a, "#F5F5F5", DARK, 1.2, rx=4)
    f.text(hx + 10, y_head_a + 16, "Nhánh Phân loại (Classification Head)", size=9.8, weight=700, fill=INK)
    f.text(hx + 10, y_head_a + 34, "GAP → Vector [1024] → Dense → Softmax", size=8.8, fill=DARK)

    # Head B: Phát hiện vật thể (YOLO)
    rect(f, hx, y_head_b, hw, h_head_b, "#F5F5F5", DARK, 1.2, rx=4)
    f.text(hx + 10, y_head_b + 16, "Nhánh Phát hiện vật thể (YOLO Neck & Head)", size=9.8, weight=700, fill=INK)
    f.text(hx + 10, y_head_b + 34, "Trích xuất đặc trưng đa tỷ lệ P3, P4, P5", size=8.8, fill=DARK)
    f.text(hx + 10, y_head_b + 48, "Đưa vào PANet/FPN Neck → Detect Head", size=8.8, fill=DARK)
    f.text(hx + 10, y_head_b + 64, "→ Dự đoán tọa độ Bounding Box + Phân loại", size=8.8, fill=DARK)

    # --- KHUNG PHẦN 2: THANH QUY LUẬT CO GIÃN TENSOR (y = 296, h = 50) ---
    rect(f, 10, 296, 880, 50, "white", DARK, 1.1, rx=4)
    # Dòng 1: Không gian
    rect(f, 18, 302, 135, 17, "#F5F5F5", DARK, 0.8, rx=3)
    f.text(85, 311, "KHÔNG GIAN (H × W)", size=8.5, weight=700, anchor="middle", fill=INK)
    f.text(165, 311, "Giảm dần 32× (640 → 20) qua Stride/Pooling để nén tọa độ không gian và mở rộng Receptive Field.", size=9.2, fill=DARK)

    # Dòng 2: Kênh
    rect(f, 18, 323, 135, 17, "#F5F5F5", DARK, 0.8, rx=3)
    f.text(85, 332, "SỐ LƯỢNG KÊNH (C)", size=8.5, weight=700, anchor="middle", fill=INK)
    f.text(165, 332, "Tăng dần >340× (3 → 1024) theo cấp số nhân để mở rộng không gian biểu diễn ngữ nghĩa vật thể.", size=9.2, fill=DARK)

    # SOURCE DƯỚI KHUNG TIẾN TRÌNH VÀ QUY LUẬT
    source(f, 346 + 4, "Nguồn: [T2 D2L tr.263-265, tr.279]. CNN trừu tượng hóa đặc trưng từ cục bộ hình học sang ngữ nghĩa toàn cục; liên hệ NPU RK3588.")
    return f


FIGS = [
    ("cv-1-stride-padding-dilation", fig_stride_padding_dilation),
    ("cv-2-co-che-receptive-field", fig_receptive_field),
    ("cv-3-ha-bac-im2col-va-gemm", fig_im2col_gemm),
    ("cv-4-depthwise-pointwise-va-group-conv", fig_dwconv_group_conv),
    ("cv-5-pooling-va-upsample", fig_pooling_upsample),
    ("cv-6-khoi-residual-va-toan-tu-add", fig_residual_add),
    ("cv-7-phan-tang-dac-trung-cnn-feature-hierarchy", fig_feature_hierarchy),
]


def run_svg_only(figs, outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, build in figs:
        fig = build()
        svg_path = os.path.join(outdir, name + ".svg")
        with open(svg_path, "w", encoding="utf-8") as fh:
            fh.write(fig.svg())
        print(f"Generated {svg_path}: {fig.w}x{fig.h}")


if __name__ == "__main__":
    args = sys.argv[1:]
    outdir = args[0] if args and not any(args[0] == n for n, _ in FIGS) else DEFAULT_OUTDIR
    only = [a for a in args if any(a == n for n, _ in FIGS)]
    active = [(n, b) for n, b in FIGS if not only or n in only]
    run_svg_only(active, outdir)
