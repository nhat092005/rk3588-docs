#!/usr/bin/env python3
"""Ghi chú chuyên đề: Convolution trong NPU (Trực quan, Toán học, im2col, CNA RK3588, DWConv, Pointwise, Group Conv và Residual Add).

Sinh 6 hình chất lượng cao chuẩn visual_guide (không chồng lấn text, layout chuẩn pixel):
  - hc-0-truc-quan-convolution (T2 chung): Trực quan hóa phép nhân chập, ví dụ số từng bước, trượt và vai trò ReLU
  - hc-1-toan-va-im2col (T2 chung): Cửa sổ trượt 2D, psums, biến đổi im2col sang GEMM và bảng so sánh
  - hc-2-cna-va-fusion (T1 RK3588): Luồng phần cứng CNA trong lõi RK3588, residual add, BN folding và hỗ trợ đa lõi
  - hc-3-dwconv-va-pointwise (T2 chung): So sánh Depthwise Convolution (3x3), Pointwise Convolution (1x1) và Depthwise Separable Conv
  - hc-4-group-convolution (T2 chung): Group Convolution, phổ liên tục G=1 -> G=Cin và tác động lên mảng MAC 32x32 RK3588
  - hc-5-toan-tu-add-va-residual-block (T2 chung): Toán tử Element-wise Add, khối Residual Block, gradient highway và cơ chế Add ghép on-chip RK3588

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 4 cấp thư mục: convolution -> _notes -> 00-tong-quan -> npu_rk3588 -> docs/tools/visual_guide
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

W = 900
STAT = "#FFF1CC"      # Màu highlight bộ nhớ cục bộ / stationary
CALC = "#EAF2FF"      # Màu nền phép tính / logic
P0, P1 = "#DCE8FA", "#DDF0DE"


def tier(f, label):
    f.tier(W - 130, 10, label)


def txt(f, x, y, ls, size=12, dy=16, fill=INK, anchor="start"):
    """In chuỗi các dòng (str hoặc rich parts) xếp chồng từ toạ độ y; trả về y tiếp theo."""
    for i, ln in enumerate(ls):
        f.rich(x, y + dy * i, ln, size=size, anchor=anchor, fill=fill)
    return y + dy * len(ls)


def card(f, x, y, w, h, title, size_t=14, dashed=False, fill="white"):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="#333333" stroke-width="1.2"{dash}/>')
    f.text(x + w / 2, y + 17, title, size=size_t, weight=700, anchor="middle")


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=3):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def label(f, x, y, w, h, ls, size=12, fill="white", stroke="#333333", dashed=False, weight=400, color=INK):
    """Hộp bo góc với các dòng chữ căn giữa."""
    rect(f, x, y, w, h, fill, stroke, dashed=dashed)
    top = y + h / 2 - (len(ls) - 1) * (size + 3) / 2
    for i, ln in enumerate(ls):
        f.text(x + w / 2, top + i * (size + 3), ln, size=size, weight=weight, anchor="middle", fill=color)


def blk(f, x, y, w, h, lines, size=12.5, fill="white", weight=700, mono=False):
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="#333333" stroke-width="1.2"/>')
    top = y + h / 2 - (len(lines) - 1) * (size + 3) / 2
    for i, ln in enumerate(lines):
        f.text(x + w / 2, top + i * (size + 3), ln, size=size, weight=weight, anchor="middle", mono=mono)


def link_box(f, x, y, w, ls, size=12.5):
    """Hộp 'Liên hệ RK3588' viền xanh, huy hiệu T1 chuẩn visual_guide."""
    h = 40 + 19 * len(ls)
    rect(f, x, y, w, h, "white", BLUE, 1.8, rx=6)
    f.tier(x + 10, y + 8, "T1 RK3588")
    f.text(x + 112, y + 19, "Liên hệ RK3588: điều nguồn T1 nói và điều chưa biết", size=13.5, weight=700)
    txt(f, x + 14, y + 44, ls, size=size, dy=19)
    return y + h


# =====================================================================
# HÌNH C.0: BẢN CHẤT TRỰC QUAN CỦA CONVOLUTION
# =====================================================================
def fig_intuitive():
    f = Fig(W, 1140)
    tier(f, "T2 chung")
    f.text(10, 48, "Bản chất trực quan của Convolution: Chiếc kính lúp dò tìm đặc trưng", size=15.5, weight=700)

    # ---- 1. ẨN DỤ CỐT LÕI ----
    ya, ha = 66, 95
    card(f, 10, ya, 880, ha, "1. Ẩn dụ đời thường: Tấm bìa mẫu dò tìm trên bức ảnh")
    txt(f, 24, ya + 36, [
        [("• ", "t"), ("Convolution là gì? ", "b"), ("Là hành động cầm một ", "t"), ("tấm bìa khoét lỗ nhỏ (Filter/Kernel)", "b"), (", trên đó vẽ sẵn mẫu cần tìm.", "t")],
        [("• Trượt tấm bìa khắp bức ảnh: ", "t"), ("Tại mỗi vị trí, so sánh xem ảnh bên dưới có khớp với mẫu không.", "t")],
        [("• Trùng khớp cao -> Cho điểm dương lớn (sáng rực). ", "b"), ("Không khớp -> Ra điểm âm hoặc 0 (qua ReLU thành 0).", "t")],
    ], size=12.5, dy=18)

    # ---- 2. VÍ DỤ SỐ TỪNG BƯỚC: TÍCH VÀ CHẬP TẠI 1 VỊ TRÍ ----
    yb, hb = ya + ha + 16, 270
    card(f, 10, yb, 880, hb, "2. Phép tính tại 1 vị trí: Vì sao gọi là \"TÍCH CHẬP\"? (Ví dụ số cụ thể)")

    cs = 34
    f.text(30, yb + 40, "Vùng ảnh 3×3 (Nét dọc giữa):", size=11.5, weight=700, fill=DARK)
    ax, ay = 30, yb + 52
    img_data = [
        [0, 10, 0],
        [0, 10, 0],
        [0, 10, 0],
    ]
    for r in range(3):
        for c in range(3):
            val = img_data[r][c]
            bg = "#FFE082" if c == 1 else "white"
            rect(f, ax + c * cs, ay + r * cs, cs, cs, bg, "#555555", 1.2)
            f.text(ax + c * cs + cs / 2, ay + r * cs + cs / 2, str(val), size=12, weight=700 if c == 1 else 400, anchor="middle", fill=INK)
    f.text(ax + 1.5 * cs, ay + 3 * cs + 16, "Cột giữa = 10", size=11, fill="#E65100", anchor="middle")

    f.text(160, yb + 104, "×", size=24, weight=700, anchor="middle", fill=DARK)
    f.text(160, yb + 122, "TÍCH", size=11, weight=700, anchor="middle", fill=BLUE)

    f.text(190, yb + 40, "Bộ lọc Filter 3×3 (Dò nét dọc):", size=11.5, weight=700, fill=DARK)
    fx, fy = 190, yb + 52
    filt_data = [
        [-1, 2, -1],
        [-1, 2, -1],
        [-1, 2, -1],
    ]
    for r in range(3):
        for c in range(3):
            val = filt_data[r][c]
            bg = "#E8F5E9" if c == 1 else "#FAFAFA"
            rect(f, fx + c * cs, fy + r * cs, cs, cs, bg, "#555555", 1.2)
            f.text(fx + c * cs + cs / 2, fy + r * cs + cs / 2, str(val), size=12, weight=700 if c == 1 else 400, anchor="middle", fill=GREEN if c == 1 else INK)
    f.text(fx + 1.5 * cs, fy + 3 * cs + 16, "Trọng số giữa = +2", size=11, fill=GREEN, anchor="middle")

    f.text(320, yb + 104, "=", size=24, weight=700, anchor="middle", fill=DARK)

    f.text(350, yb + 40, "Nhân từng ô tương ứng:", size=11.5, weight=700, fill=DARK)
    px, py = 350, yb + 52
    prod_data = [
        [0, 20, 0],
        [0, 20, 0],
        [0, 20, 0],
    ]
    for r in range(3):
        for c in range(3):
            val = prod_data[r][c]
            bg = "#FFF9C4" if c == 1 else "white"
            rect(f, px + c * cs, py + r * cs, cs, cs, bg, "#555555", 1)
            f.text(px + c * cs + cs / 2, py + r * cs + cs / 2, str(val), size=12, weight=700 if c == 1 else 400, anchor="middle", fill=INK)
    f.text(px + 1.5 * cs, py + 3 * cs + 16, "10 × 2 = 20 mỗi hàng", size=11, fill=DARK, anchor="middle")

    f.line([(475, yb + 104), (515, yb + 104)], BLUE, THICK)
    f.text(495, yb + 88, "CHẬP", size=11, weight=700, anchor="middle", fill=BLUE)
    f.text(495, yb + 120, "(Cộng dồn)", size=10.5, anchor="middle", fill=DARK)

    f.text(535, yb + 40, "1 Điểm đầu ra (Output):", size=11.5, weight=700, fill=DARK)
    ox, oy = 555, yb + 68
    rect(f, ox, oy, 62, 62, "#C8E6C9", GREEN, 2, rx=4)
    f.text(ox + 31, oy + 31, "60", size=24, weight=700, anchor="middle", fill=GREEN)
    f.text(ox + 31, oy + 76, "0 + 20 + 0 +", size=11, anchor="middle", fill=DARK)
    f.text(ox + 31, oy + 92, "0 + 20 + 0 +", size=11, anchor="middle", fill=DARK)
    f.text(ox + 31, oy + 108, "0 + 20 + 0 = 60", size=11, weight=700, anchor="middle", fill=GREEN)

    f.a(f'<rect x="660" y="{yb + 36}" width="215" height="215" rx="4" fill="#F0F8FF" stroke="{BLUE}" stroke-width="1.2"/>')
    f.text(672, yb + 56, "Ý nghĩa của con số 60:", size=12.5, weight=700, fill=BLUE)
    txt(f, 682, yb + 76, [
        [("• Điểm số +60 rất lớn!", "b"), (" Báo hiệu:", "t")],
        [("  \"Nét dọc xuất hiện tại đây!\"", "b")],
        [("• Nếu vùng ảnh toàn số 0:", "t")],
        [("  Tổng tính ra = 0.", "c")],
        [("• Nếu vùng bị lệch (xem mục 3):", "t")],
        [("  Tổng ra số âm (-30).", "c")],
        [("  Qua hàm kích hoạt ReLU:", "b")],
        [("  max(0, -30) -> triệt tiêu về 0!", "c")],
    ], size=11.5, dy=17)

    # ---- 3. QUÁ TRÌNH TRƯỢT VÀ VAI TRÒ RELU ----
    yc, hc = yb + hb + 16, 330
    card(f, 10, yc, 880, hc, "3. Quá trình trượt (Sliding Window) qua ảnh 5×5 & Tác dụng của hàm ReLU")

    f.text(25, yc + 38, "Vị trí A (Lệch tâm, col 0..2):", size=11.5, weight=700, fill=RED)
    s1_x, s1_y, s_cs = 25, yc + 52, 28
    for r in range(5):
        for c in range(5):
            val = 10 if c == 2 else 0
            bg = "#FFE082" if c == 2 else "white"
            rect(f, s1_x + c * s_cs, s1_y + r * s_cs, s_cs, s_cs, bg, "#666666", 1)
            f.text(s1_x + c * s_cs + s_cs / 2, s1_y + r * s_cs + s_cs / 2, str(val), size=10, anchor="middle")
    f.a(f'<rect x="{s1_x}" y="{s1_y}" width="{3 * s_cs}" height="{3 * s_cs}" fill="none" stroke="{RED}" stroke-width="2.2" stroke-dasharray="4 2"/>')
    txt(f, s1_x, s1_y + 5 * s_cs + 15, [
        [("Patch chạm mép nét dọc:", "b"), (" [0, 0, 10]", "t")],
        [("Nhân filter: 10 × (-1) × 3 = ", "t"), ("-30", "c")],
        [("-> Kết quả phép Conv = ", "t"), ("-30", "b"), (" (Số âm)", "t")],
    ], size=11, dy=15)

    f.text(210, yc + 38, "Vị trí B (Trúng tâm, col 1..3):", size=11.5, weight=700, fill=GREEN)
    s2_x, s2_y = 210, yc + 52
    for r in range(5):
        for c in range(5):
            val = 10 if c == 2 else 0
            bg = "#FFE082" if c == 2 else "white"
            rect(f, s2_x + c * s_cs, s2_y + r * s_cs, s_cs, s_cs, bg, "#666666", 1)
            f.text(s2_x + c * s_cs + s_cs / 2, s2_y + r * s_cs + s_cs / 2, str(val), size=10, anchor="middle")
    f.a(f'<rect x="{s2_x + s_cs}" y="{s2_y}" width="{3 * s_cs}" height="{3 * s_cs}" fill="none" stroke="{GREEN}" stroke-width="2.4"/>')
    txt(f, s2_x, s2_y + 5 * s_cs + 15, [
        [("Patch trúng nét dọc:", "b"), (" [0, 10, 0]", "t")],
        [("Nhân filter: 10 × (+2) × 3 = ", "t"), ("+60", "c")],
        [("-> Kết quả phép Conv = ", "t"), ("+60", "b"), (" (Cực đại)", "t")],
    ], size=11, dy=15)

    f.line([(370, yc + 120), (410, yc + 120)], BLUE, THICK)
    f.text(390, yc + 105, "Trượt hết ảnh", size=10.5, anchor="middle", fill=DARK)

    f.text(420, yc + 38, "Feature Map (Trước ReLU):", size=11.5, weight=700, fill=DARK)
    m1_x, m1_y = 425, yc + 65
    raw_conv = [
        [-30, 60, -30],
        [-30, 60, -30],
        [-30, 60, -30],
    ]
    for r in range(3):
        for c in range(3):
            val = raw_conv[r][c]
            bg = "#C8E6C9" if c == 1 else "#FFEBEE"
            tc = GREEN if c == 1 else RED
            rect(f, m1_x + c * s_cs, m1_y + r * s_cs, s_cs, s_cs, bg, tc, 1.2)
            f.text(m1_x + c * s_cs + s_cs / 2, m1_y + r * s_cs + s_cs / 2, str(val), size=10.5, weight=700, anchor="middle", fill=tc)
    f.text(m1_x + 1.5 * s_cs, m1_y + 3 * s_cs + 16, "Còn số âm -30", size=11, fill=RED, anchor="middle")

    f.line([(530, yc + 120), (575, yc + 120)], RED, THICK)
    f.text(552, yc + 105, "ReLU", size=11.5, weight=700, fill=RED)
    f.text(552, yc + 135, "max(0, x)", size=10.5, anchor="middle", fill=DARK)

    f.text(585, yc + 38, "Feature Map (Sau ReLU):", size=11.5, weight=700, fill=GREEN)
    m2_x, m2_y = 590, yc + 65
    relu_conv = [
        [0, 60, 0],
        [0, 60, 0],
        [0, 60, 0],
    ]
    for r in range(3):
        for c in range(3):
            val = relu_conv[r][c]
            bg = "#C8E6C9" if c == 1 else "white"
            tc = GREEN if c == 1 else GRAY
            rect(f, m2_x + c * s_cs, m2_y + r * s_cs, s_cs, s_cs, bg, GREEN if c == 1 else "#888888", 1.4 if c == 1 else 1)
            f.text(m2_x + c * s_cs + s_cs / 2, m2_y + r * s_cs + s_cs / 2, str(val), size=11, weight=700 if c == 1 else 400, anchor="middle", fill=tc)
    f.text(m2_x + 1.5 * s_cs, m2_y + 3 * s_cs + 16, "Cột 60 sáng rực!", size=11, weight=700, fill=GREEN, anchor="middle")

    f.a(f'<rect x="705" y="{yc + 50}" width="170" height="235" rx="4" fill="white" stroke="#999999" stroke-width="1"/>')
    f.text(715, yc + 68, "Quy luật cốt lõi:", size=12, weight=700, fill=DARK)
    txt(f, 715, yc + 88, [
        [("1. Kích thước thu gọn:", "b")],
        [("   Ảnh 5×5 trượt filter", "t")],
        [("   3×3 ra output 3×3.", "t")],
        [("2. Vai trò của ReLU:", "b")],
        [("   Gọt bỏ hoàn toàn các", "t")],
        [("   giá trị âm (-30 -> 0),", "t")],
        [("   chỉ giữ lại nét khớp.", "t")],
        [("3. Nhiều Channels:", "b")],
        [("   Nếu dùng 16 filter", "t")],
        [("   khác nhau sẽ ra 16", "t")],
        [("   Feature Map (kênh).", "t")],
    ], size=11, dy=16)

    # ---- 4. VÌ SAO AI XẾP CHỒNG NHIỀU LỚP CONVOLUTION ----
    yd, hd = yc + hc + 16, 205
    card(f, 10, yd, 880, hd, "4. Vì sao Mạng nơ-ron (CNN / YOLO) xếp chồng nhiều lớp Convolution liên tiếp?")

    cw = 270
    card(f, 24, yd + 36, cw, 150, "Cấp 1: Lớp Conv Nông (Đầu)", 12.5, fill="#EAF2FF")
    txt(f, 34, yd + 66, [
        [("• Bộ lọc tìm nét cơ bản:", "b")],
        [("  Cạnh ngang, cạnh dọc, góc nhọn,", "t")],
        [("  độ tương phản sáng/tối.", "t")],
        [("• Receptive field nhỏ (3×3 pixel).", "t")],
        [("• Đặc trưng vật lý cục bộ.", "t")],
    ], size=11.5, dy=17)

    f.line([(24 + cw + 4, yd + 110), (24 + cw + 24, yd + 110)], BLUE, THICK)

    card(f, 318, yd + 36, cw, 150, "Cấp 2: Lớp Conv Giữa (Thân)", 12.5, fill="#FFF8E1")
    txt(f, 328, yd + 66, [
        [("• Ghép các nét thành hình:", "b")],
        [("  Đường cong, vân họa tiết,", "t")],
        [("  bộ phận nhỏ (mắt, mũi, vành xe).", "t")],
        [("• Receptive field mở rộng hơn.", "t")],
        [("• Kết hợp từ các Feature Map cấp 1.", "t")],
    ], size=11.5, dy=17)

    f.line([(318 + cw + 4, yd + 110), (318 + cw + 24, yd + 110)], BLUE, THICK)

    card(f, 612, yd + 36, cw, 150, "Cấp 3: Lớp Conv Sâu (Đuôi)", 12.5, fill="#E8F5E9")
    txt(f, 622, yd + 66, [
        [("• Nhận diện vật thể hoàn chỉnh:", "b")],
        [("  Khuôn mặt người, con mèo, ô tô.", "t")],
        [("• Receptive field bao trùm toàn ảnh.", "t")],
        [("• Ra quyết định phân loại &", "t")],
        [("  đóng khung vật thể (YOLO detect).", "b")],
    ], size=11.5, dy=17)

    source(f, yd + hd + 10, "Nguồn: Giáo trình Deep Learning & Computer Vision nền tảng; LeCun et al. (CNNs); Eyeriss (2016).")
    return f


# =====================================================================
# HÌNH C.1: TOÁN HỌC CONVOLUTION, IM2COL, GEMM VÀ PARTIAL SUMS (PSUMS)
# =====================================================================
def fig_im2col():
    f = Fig(W, 1050)
    tier(f, "T2 chung")
    f.text(10, 48, "Bản chất toán học Convolution 2D, Partial Sums (psums) và biến đổi im2col sang GEMM", size=15.5, weight=700)

    # ---- KHỐI 1: CỬA SỔ TRƯỢT 2D VÀ PARTIAL SUMS ----
    ya, ha = 66, 275
    card(f, 10, ya, 880, ha, "1. Cửa sổ trượt 2D & Cơ chế Tích lũy từng phần (Partial Sums - psums)")

    gx, gy, cs = 30, ya + 50, 36
    f.text(30, ya + 38, "Input Map (H × W × Cin):", size=11.5, weight=700, fill=DARK)
    for r in range(4):
        for c in range(4):
            is_patch = (r < 2 and c < 2)
            fill_c = "#FFE082" if is_patch else "white"
            stroke_c = "#E65100" if is_patch else "#888888"
            sw = 1.4 if is_patch else 0.8
            rect(f, gx + c * cs, gy + r * cs, cs, cs, fill_c, stroke_c, sw)
            f.text(gx + c * cs + cs / 2, gy + r * cs + cs / 2, f"x{r}{c}", size=11, anchor="middle", fill=INK)

    f.text(gx + 2 * cs, gy + 4 * cs + 18, "Patch 0 (2×2)", size=11.5, weight=700, fill="#E65100", anchor="middle")
    f.text(195, ya + 120, "⊛", size=28, weight=700, anchor="middle", fill=DARK)

    f.text(225, ya + 38, "Weight Filter (K × K):", size=11.5, weight=700, fill=DARK)
    kx, ky = 225, ya + 68
    for r in range(2):
        for c in range(2):
            rect(f, kx + c * cs, ky + r * cs, cs, cs, "#FFE082", "#E65100", 1.4)
            f.text(kx + c * cs + cs / 2, ky + r * cs + cs / 2, f"w{r}{c}", size=11, weight=700, anchor="middle", fill="#E65100")

    f.line([(315, ya + 120), (345, ya + 120)], BLUE, THICK)

    f.text(360, ya + 38, "Output Map (3×3):", size=11.5, weight=700, fill=DARK)
    ox, oy = 360, ya + 56
    for r in range(3):
        for c in range(3):
            is_out = (r == 0 and c == 0)
            fill_c = "#C8E6C9" if is_out else "white"
            stroke_c = "#2E7D32" if is_out else "#888888"
            sw = 1.4 if is_out else 0.8
            rect(f, ox + c * cs, oy + r * cs, cs, cs, fill_c, stroke_c, sw)
            if is_out:
                f.text(ox + c * cs + cs / 2, oy + r * cs + cs / 2, "y00", size=11, weight=700, anchor="middle", fill=GREEN)
            else:
                f.text(ox + c * cs + cs / 2, oy + r * cs + cs / 2, f"y{r}{c}", size=10.5, anchor="middle", fill=GRAY)
    f.text(ox + 1.5 * cs, oy + 3 * cs + 18, "y00 = Σ psums", size=11.5, weight=700, fill=GREEN, anchor="middle")

    f.a(f'<rect x="500" y="{ya + 34}" width="370" height="225" rx="4" fill="white" stroke="#999999" stroke-width="1"/>')
    f.text(512, ya + 52, "Đặc tính toán học và Partial Sums (psums):", size=12.5, weight=700, fill=DARK)
    txt(f, 512, ya + 72, [
        [("• Công thức 1 điểm đầu ra: ", "b")],
        [("  y(h,w) = Σ Σ Σ x(h+i, w+j, c) · w(i, j, c, out) + bias", "c")],
        [("• Tích lũy từng phần (Partial Sums - psums):", "b")],
        [("  Mỗi tích w·x tạo ra 1 psum trung gian, cộng dồn vào thanh", "t")],
        [("  ghi accumulator. EYE tr.4: psums are reduced into ofmap.", "t")],
        [("• Số phép MAC cho 1 lớp: ", "b"), ("Hout · Wout · Cout · (K² · Cin)", "c")],
        [("• Weight Sharing: ", "b"), ("Bộ trọng số K×K quét trên toàn ảnh.", "t")],
        [("• Spatial Reuse: ", "b"), ("Điểm ảnh x lân cận được dùng lại tới K² lần.", "t")],
    ], size=11, dy=17)

    # ---- KHỐI 2: BIẾN ĐỔI IM2COL VÀ GEMM ----
    yb, hb = ya + ha + 16, 310
    card(f, 10, yb, 880, hb, "2. Biến đổi im2col (Image to Column) & Phép nhân ma trận GEMM")

    f.text(24, yb + 38, "Chuyển từng cửa sổ trượt thành một hàng/cột ma trận để biến tích chập thành A × B = C:", size=12.5, fill=DARK)

    label(f, 24, yb + 60, 240, 28, ["Ma trận Input đã trải (im2col)"], size=12, weight=700, fill="#F0F4F8")
    f.text(144, yb + 100, "M = Hout × Wout (9 vị trí cửa sổ)", size=11, anchor="middle", fill=DARK)
    f.text(144, yb + 116, "K = K × K × Cin (4 trọng số)", size=11, anchor="middle", fill=DARK)

    f.table(24, yb + 130, [70, 42, 42, 42, 42], ["Cửa sổ", "w00", "w01", "w10", "w11"], [
        ["Patch 0", "x00", "x01", "x10", "x11"],
        ["Patch 1", "x01", "x02", "x11", "x12"],
        ["Patch 2", "x02", "x03", "x12", "x13"],
        ["...", "...", "...", "...", "..."],
        ["Patch 8", "x22", "x23", "x32", "x33"],
    ], size=11, line_h=15, fills={0: "#FFF8E1"})

    f.text(282, yb + 195, "×", size=24, weight=700, anchor="middle", fill=DARK)

    label(f, 300, yb + 60, 220, 28, ["Ma trận Trọng số (Filters)"], size=12, weight=700, fill="#FFF8E1")
    f.text(410, yb + 100, "K = K × K × Cin (4 giá trị)", size=11, anchor="middle", fill=DARK)
    f.text(410, yb + 116, "N = Cout (số bộ lọc đầu ra)", size=11, anchor="middle", fill=DARK)

    f.table(300, yb + 130, [65, 50, 50, 50], ["Trọng số", "Fil 0", "Fil 1", "Fil Cout"], [
        ["w00", "w00,0", "w00,1", "..."],
        ["w01", "w01,0", "w01,1", "..."],
        ["w10", "w10,0", "w10,1", "..."],
        ["w11", "w11,0", "w11,1", "..."],
    ], size=11, line_h=16, fills={0: "#FFF8E1"})

    f.text(540, yb + 195, "=", size=24, weight=700, anchor="middle", fill=DARK)

    label(f, 560, yb + 60, 160, 28, ["Ma trận Đầu ra (GEMM)"], size=12, weight=700, fill="#E8F5E9")
    f.text(640, yb + 100, "M × N = 9 × Cout", size=11, anchor="middle", fill=DARK)
    f.table(560, yb + 130, [50, 55, 55], ["Patch", "Out 0", "Out 1"], [
        ["0 (y00)", "y00,0", "y00,1"],
        ["1 (y01)", "y01,0", "y01,1"],
        ["2 (y02)", "y02,0", "y02,1"],
        ["...", "...", "..."],
        ["8 (y22)", "y22,0", "y22,1"],
    ], size=11, line_h=16, fills={0: "#C8E6C9"})

    f.a(f'<rect x="735" y="{yb + 60}" width="135" height="235" rx="4" fill="white" stroke="#333333" stroke-width="1.2"/>')
    f.text(802, yb + 78, "Vì sao dùng GEMM?", size=12, weight=700, anchor="middle", fill=DARK)
    txt(f, 742, yb + 98, [
        [("1. Tận dụng", "b")],
        [("mảng systolic", "t")],
        [("và MAC array", "t")],
        [("2. Thư viện BLAS", "b")],
        [("tối ưu sẵn", "t")],
        [("3. Đánh đổi:", "b")],
        [("bộ nhớ RAM tăng", "t")],
        [("gấp K² lần nếu", "t")],
        [("copy thật ra RAM.", "t")],
        [("4. Implicit GEMM:", "b")],
        [("NPU nạp on-the-fly,", "t")],
        [("không tốn RAM.", "t")],
    ], size=11, dy=14)

    # ---- BẢNG SO SÁNH ----
    yc = yb + hb + 16
    f.text(10, yc + 4, "So sánh ba cách thực thi Convolution trên bộ xử lý", size=15, weight=700)
    y = f.table(10, yc + 18, [130, 240, 250, 260], ["Phương thức", "Sliding Window Trực tiếp", "im2col + GEMM Tường minh", "Implicit GEMM Phần cứng NPU"], [
        ["Cách làm", ("lines", ["Vòng lặp for lồng nhau", "duyệt qua từng ô ảnh"]), ("lines", ["Tạo ma trận trung gian trong RAM", "rồi gọi hàm nhân GEMM"]), ("lines", ["Bộ điều khiển phần cứng tự giải mã", "địa chỉ nạp trực tiếp vào PE"])],
        ["Bộ nhớ phụ", "0 byte (không cần đệm)", ("lines", ["Tăng K × K lần dung lượng", "input trong bộ nhớ RAM"]), ("lines", ["0 byte RAM ngoài", "(chỉ dùng buffer nội bộ CBUF)"])],
        ["Hiệu năng", ("lines", ["Kém trên GPU/NPU vì", "truy cập không liên tục"]), ("lines", ["Tính toán nhanh nhưng nghẽn", "băng thông bộ nhớ DRAM"]), ("lines", ["Tối ưu nhất: tận dụng 100% mảng MAC", "mà không tốn băng thông DDR"])],
        ["Nơi dùng", "CPU thuần, vi điều khiển MCU", "Caffe, framework thời kỳ đầu", "NPU chuyên dụng (TPU, RK3588 CNA)"],
    ], size=11.5, line_h=15)

    # ---- LINK BOX ----
    y = link_box(f, 10, y + 14, 880, [
        [("TRM1 tr.1985: ", "b"), ("Khối CNA chứa \"convolution pre-process controller\" chịu trách nhiệm nạp dữ liệu từ CBUF.", "t")],
        "Bộ điều khiển này giải quyết bài toán im2col trực tiếp ở cấp phần cứng, nạp dữ liệu on-the-fly vào MAC array 32x32.",
        "Nhờ đó, NPU RK3588 đạt đỉnh tính toán mà không bị nhân bản dữ liệu gây tràn RAM DDR hay bộ đệm CBUF 384KB.",
        "unknown: sơ đồ mạch chi tiết của bộ sinh địa chỉ bên trong convolution pre-process controller.",
    ])

    source(f, y + 8, "Nguồn: EYE tr.2, 4 (Eyeriss dataflow 2016); TPU tr.3 (Jouppi 2017); TRM1 tr.1985 (RK3588 CNA).")
    return f


# =====================================================================
# HÌNH C.2: PHẦN CỨNG CNA LÕI RK3588, RESIDUAL ADD VÀ BATCHNORM FOLDING
# =====================================================================
def fig_cna_fusion():
    f = Fig(W, 1140)
    tier(f, "T1 RK3588")
    f.text(10, 48, "Cấu trúc khối CNA trong lõi NPU RK3588, Residual Add và BatchNorm Folding", size=15.5, weight=700)

    # ---- PHẦN 1: OPERATOR FUSION VÀ BATCHNORM FOLDING ----
    ya, ha = 66, 260
    card(f, 10, ya, 880, ha, "1. Cơ chế ghép toán tử (Operator Fusion) & Gộp Batch Normalization (BN Folding)")

    f.a(f'<rect x="24" y="{ya + 36}" width="380" height="205" rx="5" fill="#FAFAFA" stroke="#999999" stroke-width="1"/>')
    f.text(36, ya + 54, "Đồ thị ban đầu (PyTorch / ONNX xuất khẩu):", size=12.5, weight=700, fill=DARK)
    blk(f, 40, ya + 72, 85, 48, ["Conv 2D", "[W, B]"], size=12, fill="#EAF2FF")
    f.line([(125, ya + 96), (155, ya + 96)], INK, THIN)
    blk(f, 155, ya + 72, 105, 48, ["BatchNorm", "[μ, σ², γ, β]"], size=11.5, fill="#FFF8E1")
    f.line([(260, ya + 96), (290, ya + 96)], INK, THIN)
    blk(f, 290, ya + 72, 100, 48, ["Activation", "ReLU / SiLU"], size=12, fill="#E8F5E9")

    f.line([(100, ya + 120), (100, ya + 145), (340, ya + 145), (340, ya + 120)], RED, THIN, dashed=True)
    f.text(220, ya + 158, "Không ghép: Phải ghi & đọc tensor trung gian ra RAM DDR", size=11.5, fill=RED, anchor="middle", weight=700)
    txt(f, 40, ya + 178, [
        [("• Tốn băng thông bộ nhớ ngoài (Memory Wall)", "t")],
        [("• Tăng độ trễ khung hình và công suất tiêu thụ", "t")],
    ], size=11.5, dy=16)

    f.line([(415, ya + 130), (465, ya + 130)], BLUE, THICK)
    f.text(440, ya + 115, "rknn.build()", size=11.5, weight=700, anchor="middle", fill=BLUE)
    f.text(440, ya + 148, "Compiler", size=11, anchor="middle", fill=DARK)

    f.a(f'<rect x="475" y="{ya + 36}" width="400" height="205" rx="5" fill="#F0F8FF" stroke="{BLUE}" stroke-width="1.4"/>')
    f.text(488, ya + 54, "Đồ thị sau ghép trên NPU RK3588 (Khép kín trong lõi):", size=12.5, weight=700, fill=BLUE)
    blk(f, 490, ya + 70, 250, 56, [
        "ConvRelu / ConvExSwish",
        "W_fused = γ·W / √(σ² + ε)",
        "B_fused = β + γ·(B - μ) / √(σ² + ε)",
    ], size=11, fill="white")
    f.badge(755, ya + 98, "✓", GREEN)

    txt(f, 490, ya + 140, [
        [("1. Gộp toán học BN vào Conv (Offline BN Folding, NAGEL tr.6):", "b")],
        [("   Trọng số W và Bias B được gộp trước, loại bỏ hoàn toàn lớp BN.", "t")],
        [("2. Nối trực tiếp Activation trong phần cứng DPU:", "b")],
        [("   Kết quả từ accumulator đi thẳng vào DPU, 0 lần ra RAM DDR.", "t")],
    ], size=11.5, dy=18)

    # ---- PHẦN 2: CẤU TRÚC PHẦN CỨNG CNA TRONG LÕI NPU ----
    yb, hb = ya + ha + 16, 435
    card(f, 10, yb, 880, hb, "2. Đường dẫn dữ liệu phần cứng khối CNA, Mảng MAC và Nhánh tắt Residual Add (TRM1 Ch.36)")

    f.a(f'<rect x="20" y="{yb + 36}" width="860" height="385" rx="6" fill="#FAFAFA" stroke="#666666" stroke-width="1.2"/>')
    f.text(32, yb + 54, "NPU CORE (Lõi 0 / Lõi 1 / Lõi 2)", size=13.5, weight=700, fill=DARK)

    blk(f, 40, yb + 70, 200, 42, ["Memory Interface (AXI)"], size=13)
    f.line([(140, yb + 112), (140, yb + 140)], BLUE, THICK)
    f.text(148, yb + 128, "nạp ngoài", size=10.5, fill=BLUE)

    blk(f, 40, yb + 140, 200, 80, ["384KB Buffer (CBUF)", "Internal Buffer", "8 banks (0..7)"], size=13, fill=STAT)
    f.badge(48, yb + 148, "1")

    txt(f, 48, yb + 235, [
        [("• Bank 0-6: feature data", "t")],
        [("• Bank 7-1: weight data", "t")],
    ], size=11, dy=15)

    f.line([(240, yb + 180), (280, yb + 180)], BLUE, THICK)

    rect(f, 280, yb + 70, 190, 240, "white", "#333333", 1.2, rx=5)
    f.text(375, yb + 90, "CNA Controller", size=14, weight=700, anchor="middle")
    f.text(375, yb + 106, "(Convolution Pre-process)", size=11, anchor="middle", fill=DARK)
    f.badge(290, yb + 80, "2")

    blk(f, 295, yb + 118, 160, 36, ["Feature Data Load"], size=11.5)
    blk(f, 295, yb + 160, 160, 36, ["Weight Data Load"], size=11.5)
    blk(f, 295, yb + 202, 160, 36, ["Zero-Skipping"], size=11.5)
    blk(f, 295, yb + 244, 160, 36, ["Weight Decompress"], size=11.5)

    f.line([(470, yb + 180), (510, yb + 180)], BLUE, THICK)

    rect(f, 510, yb + 70, 180, 255, "white", "#333333", 1.2, rx=5)
    f.text(600, yb + 90, "Tính toán Tích chập", size=14, weight=700, anchor="middle")
    f.badge(520, yb + 80, "3")

    blk(f, 525, yb + 115, 150, 40, ["Sequence Controller"], size=11.5)
    blk(f, 525, yb + 165, 150, 65, ["INT8 MAC Array", "32×32 mode", "(1024 MACs/cycle)"], size=12, fill=P1)
    blk(f, 525, yb + 242, 150, 48, ["Accumulator INT32", "psums + Residual Add"], size=11.5, fill="#FFF9C4")

    # Nhánh Residual Add (Skip Connection) nối thẳng vào Accumulator qua khe giữa khối 2 và 3
    f.line([(240, yb + 160), (255, yb + 160), (255, yb + 56), (490, yb + 56), (490, yb + 266), (525, yb + 266)], GREEN, THICK)
    f.badge(255, yb + 56, "+", GREEN)
    f.text(272, yb + 52, "Residual Shortcut (CBUF/Input1) → Nối vào Accumulator (OPL tr.61, 63)", size=10, weight=700, fill=GREEN, anchor="start")

    f.line([(690, yb + 266), (730, yb + 266)], BLUE, THICK)

    rect(f, 730, yb + 70, 135, 255, "white", "#333333", 1.2, rx=5)
    f.text(797, yb + 90, "Hậu xử lý (Post)", size=13.5, weight=700, anchor="middle")
    f.badge(740, yb + 80, "4")

    blk(f, 742, yb + 115, 110, 75, ["DPU Unit", "ReLU, SiLU,", "Leaky ReLU,", "Sigmoid, Tanh"], size=11, fill="#FCE4EC")
    f.line([(797, yb + 190), (797, yb + 215)], BLUE, THIN)
    blk(f, 742, yb + 215, 110, 75, ["PPU Unit", "Planar Process:", "MaxPool,", "AvgPool"], size=11, fill="#F3E5F5")

    # Đường hồi tiếp
    f.line([(797, yb + 290), (797, yb + 345), (32, yb + 345), (32, yb + 180), (38, yb + 180)], BLUE, THIN, dashed=True)
    f.text(430, yb + 338, "Ghi ngược Feature Map đầu ra vào CBUF (chuẩn bị cho layer tiếp theo) hoặc qua AXI ra DDR", size=11.5, fill=BLUE, anchor="middle", weight=700)

    f.a(f'<rect x="24" y="{yb + 360}" width="850" height="50" rx="4" fill="#FFF3F3" stroke="{RED}" stroke-width="1.2" stroke-dasharray="5 3"/>')
    f.text(36, yb + 378, "Lưu ý quan trọng khi chạy Đa lõi trên RK3588 (T1 & T3):", size=12, weight=700, fill=RED)
    f.rich(36, yb + 394, [
        ("• ", "t"), ("ConvRelu & ConvolutionAddRelu:", "b"), (" hỗ trợ chia 3 lõi mượt mà (OPL tr.60, 63). ", "t"),
        ("• ", "t"), ("ConvolutionSwish (SiLU):", "b"), (" OPL ghi ", "t"),
        ("多核联合: 暂不支持", "c"), (" (chưa hỗ trợ đa lõi); trên board dồn 100% về Core 0.", "t")
    ], size=11.5)

    # ---- BẢNG SO SÁNH ACTIVATION ----
    yc = yb + hb + 16
    f.text(10, yc + 4, "So sánh các toán tử kết hợp Convolution và Residual Add trên RK3588", size=15, weight=700)
    y = f.table(10, yc + 18, [130, 160, 150, 180, 260], ["Toán tử ghép", "Op sau khi Fusion", "Khối phần cứng", "Hỗ trợ Đa lõi (3 core)", "Đặc điểm hiệu năng"], [
        ["Conv + ReLU", "ConvRelu", "CNA + DPU", "Có (hỗ trợ đầy đủ)", ("lines", ["Tối ưu nhất cho phần cứng RK3588,", "chia đều tải tính toán cho cả 3 core"])],
        ["Conv + Add + ReLU", "ConvolutionAddRelu", "Accumulator + DPU", "Có (hỗ trợ đầy đủ)", ("lines", ["Residual Add nối on-chip vào accumulator,", "không tốn băng thông RAM DDR ngoài"])],
        ["Conv + SiLU (Swish)", "ConvExSwish", "CNA + DPU", ("lines", ["Chưa hỗ trợ", "(toàn bộ về Core 0)"]), ("lines", ["Chính xác cao cho YOLO,", "nhưng không tăng tốc khi chạy 3 core"])],
        ["Conv + Add (trần)", "ConvolutionAdd", "CNA Accumulator", "Có (hỗ trợ đầy đủ)", ("lines", ["Cộng dồn shortcut trực tiếp trên thanh ghi,", "kết quả chuyển tiếp sang PPU/RAM"])],
    ], size=11.5, line_h=15)

    # ---- LINK BOX ----
    y = link_box(f, 10, y + 14, 880, [
        [("TRM1 tr.1984-1985, 2001: ", "b"), ("Mỗi core NPU chứa riêng biệt 384KB CBUF, mảng MAC INT8 32x32 và DPU/PPU.", "t")],
        [("OPL tr.61, 63: ", "b"), ("Toán tử ConvolutionAdd và ConvolutionAddRelu hỗ trợ đa lõi; ConvolutionSwish tạm chưa hỗ trợ.", "t")],
        [("UG232 tr.142 & NAGEL tr.6: ", "b"), ("Quy tắc ghép Conv+Activation+Add và gộp toán học Batch Normalization (BN folding).", "t")],
        "unknown: bảng tra cứu (LUT) chi tiết của DPU khi tính toán hàm phi tuyến Swish/Sigmoid.",
    ])

    source(f, y + 8, "Nguồn: TRM1 tr.1984-1985, 2001; OPL tr.61, 63; UG232 tr.142; NAGEL tr.6; LOG 2026-10-10_t3-board-silu-resize.")
    return f


# =====================================================================
# HÌNH C.3: DEPTHWISE CONVOLUTION (DWCONV) VÀ POINTWISE CONVOLUTION (1x1)
# =====================================================================
def fig_dwconv_pointwise():
    f = Fig(W, 1100)
    tier(f, "T2 chung")
    f.text(10, 48, "So sánh kiến trúc Depthwise Convolution (DWConv) và Pointwise Convolution (1x1)", size=15.5, weight=700)

    # ---- PHẦN 1: STANDARD CONVOLUTION (ĐỐI CHỨNG) ----
    ya, ha = 66, 175
    card(f, 10, ya, 880, ha, "1. Standard Convolution 2D: Lọc không gian & Trộn kênh đồng thời trong 1 bước")

    txt(f, 24, ya + 36, [
        [("• Cấu trúc bộ lọc: ", "b"), ("Gồm ", "t"), ("Cout", "c"), (" bộ lọc kích thước ", "t"), ("K × K × Cin", "c"), (". Quét đồng thời trên mọi kênh đầu vào.", "t")],
        [("• Số phép tính MAC: ", "b"), ("Hout × Wout × Cout × (K² · Cin)", "c"), (" (Chi phí tính toán cao nhất).", "t")],
        [("• Đặc tính: ", "b"), ("Trộn không gian và kênh hoàn hảo, nhưng số lượng tham số lớn: ", "t"), ("Cout × Cin × K²", "c"), (" trọng số.", "t")],
    ], size=12, dy=18)

    # Trực quan mini
    rect(f, 24, ya + 95, 120, 64, "#EAF2FF", BLUE, 1.2)
    f.text(84, ya + 120, "Input Feature Map", size=11, weight=700, anchor="middle", fill=BLUE)
    f.text(84, ya + 138, "[H, W, Cin]", size=11, anchor="middle", fill=DARK)

    f.line([(150, ya + 127), (200, ya + 127)], DARK, THICK)

    rect(f, 206, ya + 95, 210, 64, "#FFF8E1", "#E65100", 1.2)
    f.text(311, ya + 115, "Cout Filter 3D Chuẩn", size=11.5, weight=700, anchor="middle", fill="#E65100")
    f.text(311, ya + 132, "Kích thước K × K × Cin", size=11, anchor="middle", fill=DARK)
    f.text(311, ya + 148, "(Mỗi filter phủ trọn Cin kênh)", size=10, anchor="middle", fill=GRAY)

    f.line([(422, ya + 127), (472, ya + 127)], DARK, THICK)

    rect(f, 478, ya + 95, 130, 64, "#E8F5E9", GREEN, 1.2)
    f.text(543, ya + 120, "Output Map", size=11, weight=700, anchor="middle", fill=GREEN)
    f.text(543, ya + 138, "[Hout, Wout, Cout]", size=11, anchor="middle", fill=DARK)

    f.a(f'<rect x="630" y="{ya + 95}" width="245" height="64" rx="4" fill="#F5F5F5" stroke="#777777" stroke-width="1"/>')
    f.text(752, ya + 114, "Ưu điểm: Tái sử dụng dữ liệu cao", size=11, weight=700, anchor="middle", fill=DARK)
    f.text(752, ya + 132, "Nhược điểm: Rất nặng FLOPs và RAM", size=10.5, anchor="middle", fill=RED)
    f.text(752, ya + 148, "MOBONE tr.4, EYE tr.4", size=10, anchor="middle", fill=GRAY)

    # ---- PHẦN 2: DEPTHWISE SEPARABLE CONV (DWCONV + POINTWISE) ----
    yb, hb = ya + ha + 16, 400
    card(f, 10, yb, 880, hb, "2. Depthwise Separable Convolution: Tách rời Không gian và Trộn kênh (MobileNet / YOLO)")

    # Nửa trái: Depthwise Convolution
    f.a(f'<rect x="24" y="{yb + 36}" width="410" height="348" rx="5" fill="#FAFAFA" stroke="{BLUE}" stroke-width="1.2"/>')
    f.text(229, yb + 56, "Bước 1: Depthwise Convolution (DWConv)", size=13, weight=700, anchor="middle", fill=BLUE)
    f.text(229, yb + 72, "Chỉ lọc không gian từng kênh riêng lẻ (Spatial Filtering)", size=11, anchor="middle", fill=DARK)

    # Lưới kênh trực quan DWConv
    c_w, c_h = 75, 42
    for i in range(3):
        cy = yb + 95 + i * 50
        rect(f, 36, cy, c_w, c_h, "#EAF2FF", BLUE, 1)
        f.text(36 + c_w / 2, cy + 24, f"Kênh In {i}", size=11, weight=700, anchor="middle")

        f.line([(118, cy + 21), (150, cy + 21)], DARK, THIN)

        rect(f, 154, cy, 100, c_h, "#FFF8E1", "#E65100", 1)
        f.text(204, cy + 18, f"Filter {i} (2D)", size=10.5, weight=700, anchor="middle", fill="#E65100")
        f.text(204, cy + 32, "K × K × 1", size=10, anchor="middle", fill=DARK)

        f.line([(260, cy + 21), (292, cy + 21)], DARK, THIN)

        rect(f, 296, cy, c_w, c_h, "#E8F5E9", GREEN, 1)
        f.text(296 + c_w / 2, cy + 24, f"Kênh Out {i}", size=11, weight=700, anchor="middle")

    f.text(36 + c_w / 2, yb + 252, "⋮ (Cin kênh)", size=11, anchor="middle", fill=GRAY)
    f.text(204, yb + 252, "⋮ (Cin bộ lọc 2D)", size=11, anchor="middle", fill=GRAY)
    f.text(296 + c_w / 2, yb + 252, "⋮ (Cin kênh)", size=11, anchor="middle", fill=GRAY)

    txt(f, 36, yb + 276, [
        [("• Không trộn kênh: ", "b"), ("Mỗi kênh chỉ nhân với filter của chính nó.", "t")],
        [("• Số phép MAC: ", "b"), ("Hout × Wout × Cin × K²", "c"), (" (Giảm Cout lần).", "t")],
        [("• Điểm yếu trên NPU: ", "b"), ("Arithmetic Intensity rất thấp (ít tính,", "t")],
        [("  nạp nhiều). Dễ bị ", "t"), ("memory-bound", "b"), (" trên RK3588 (SURV tr.19).", "t")],
    ], size=11, dy=16)

    # Nửa phải: Pointwise Convolution (1x1)
    f.a(f'<rect x="450" y="{yb + 36}" width="420" height="348" rx="5" fill="#FAFAFA" stroke="{GREEN}" stroke-width="1.2"/>')
    f.text(660, yb + 56, "Bước 2: Pointwise Convolution (PWConv 1×1)", size=13, weight=700, anchor="middle", fill=GREEN)
    f.text(660, yb + 72, "Chỉ trộn đặc trưng xuyên kênh (Cross-Channel Mixing)", size=11, anchor="middle", fill=DARK)

    # Trực quan Pointwise
    rect(f, 465, yb + 110, 100, 110, "#EAF2FF", BLUE, 1.2)
    f.text(515, yb + 155, "Feature Map", size=11, weight=700, anchor="middle", fill=BLUE)
    f.text(515, yb + 172, "[H, W, Cin]", size=10.5, anchor="middle", fill=DARK)

    f.line([(572, yb + 165), (612, yb + 165)], DARK, THICK)

    rect(f, 620, yb + 100, 120, 130, "#FFF8E1", "#E65100", 1.2)
    f.text(680, yb + 130, "Cout Bộ lọc", size=11.5, weight=700, anchor="middle", fill="#E65100")
    f.text(680, yb + 148, "1 × 1 × Cin", size=12, weight=700, anchor="middle", fill=DARK)
    f.text(680, yb + 168, "Không quét không gian", size=10, anchor="middle", fill=GRAY)
    f.text(680, yb + 184, "K = 1", size=11, weight=700, anchor="middle", fill=DARK)

    f.line([(748, yb + 165), (788, yb + 165)], DARK, THICK)

    rect(f, 795, yb + 110, 65, 110, "#E8F5E9", GREEN, 1.2)
    f.text(827, yb + 155, "Output", size=11, weight=700, anchor="middle", fill=GREEN)
    f.text(827, yb + 172, "[Cout]", size=10.5, anchor="middle", fill=DARK)

    txt(f, 465, yb + 276, [
        [("• Trộn thông tin: ", "b"), ("Tổng hợp tuyến tính các kênh tại mỗi điểm ảnh.", "t")],
        [("• Số phép MAC: ", "b"), ("Hout × Wout × Cin × Cout", "c"), (" (K = 1).", "t")],
        [("• Ưu thế trên NPU: ", "b"), ("Tương đương phép nhân ma trận thuần túy GEMM,", "t")],
        [("  tận dụng tối đa mảng MAC array 32×32 của RK3588 (TRM1 tr.2001).", "t")],
    ], size=11, dy=16)

    # ---- PHẦN 3: SO SÁNH ĐỊNH LƯỢNG FLOPs & THAM SỐ ----
    yc = yb + hb + 16
    f.text(10, yc + 4, "So sánh định lượng giữa Standard Conv và Depthwise Separable Conv (K=3, Cin=64, Cout=128)", size=15, weight=700)
    y = f.table(10, yc + 18, [180, 220, 220, 260], ["Đặc tính", "Standard Conv (3×3)", "DWConv + Pointwise (3×3)", "Mức giảm / Nhận xét phần cứng"], [
        ["Số tham số (Weights)", "128 × 64 × 9 = 73,728", "(64 × 9) + (64 × 128) = 8,768", ("lines", ["Giảm 8.41 lần tham số", "(Tương đương giảm ~88% bộ nhớ)"])],
        ["Phép tính MAC mỗi pixel", "64 × 128 × 9 = 73,728", "(64 × 9) + (64 × 128) = 8,768", ("lines", ["Tỷ lệ: 1/Cout + 1/K² ≈ 1/128 + 1/9", "Tiết kiệm 8.41 lần FLOPs tính toán"])],
        ["Khả năng tái sử dụng dữ liệu", "Cao (Spatial + Channel reuse)", ("lines", ["DWConv: Thấp (Spatial chỉ 1 kênh)", "PWConv: Cao (GEMM đa kênh)"]), ("lines", ["DWConv dễ rơi vào memory-bound", "PWConv đạt thông lượng MAC cao"])],
        ["Độ phù hợp mảng MAC NPU", "Rất tốt (Lấp đầy mảng 32×32)", ("lines", ["DWConv: MAC usage thấp (0.3 - 1.2%)", "PWConv: MAC usage cao (>80%)"]), ("lines", ["YOLO26n kết hợp DWConv trong block", "để cân bằng latency và accuracy"])],
    ], size=11.5, line_h=15)

    # ---- LINK BOX ----
    y = link_box(f, 10, y + 14, 880, [
        [("MOBONE tr.4 & SURV tr.19: ", "b"), ("Khối cơ bản của MobileNet gồm 3x3 depthwise convolution theo sau là 1x1 pointwise.", "t")],
        [("EYE tr.4: ", "b"), ("psums được gom tụ tại cuối cửa sổ; DWConv có lượng psum ít hơn nhiều so với Standard Conv.", "t")],
        [("Số đo thực tế trên RK3588 (LOG yolo-phaseA): ", "b"), ("Các lớp depthwise 3x3 trong YOLO26n có MacUsage chỉ từ 0.30% đến 1.24%.", "t")],
        "unknown: cơ chế nạp trọng số chuyên biệt (nếu có) của CNA Controller cho depthwise convolution.",
    ])

    source(f, y + 8, "Nguồn: MOBONE tr.4 (MobileOne 2023); SURV tr.19; EYE tr.4 (Eyeriss 2016); TRM1 tr.2001; LOG 2026-10-10_yolo-phaseA.")
    return f


# =====================================================================
# HÌNH C.4: GROUP CONVOLUTION VÀ PHỔ LIÊN TỤC G=1 ĐẾN G=Cin
# =====================================================================
def fig_group_conv():
    f = Fig(W, 1080)
    tier(f, "T2 chung")
    f.text(10, 48, "Group Convolution (Tích chập nhóm) và phổ liên tục giữa các biến thể", size=15.5, weight=700)

    # ---- PHẦN 1: NGUYÊN LÝ GROUP CONVOLUTION ----
    ya, ha = 66, 260
    card(f, 10, ya, 880, ha, "1. Cơ chế chia nhóm độc lập trong Group Convolution (G = 2)")

    txt(f, 24, ya + 36, [
        [("• Nguyên lý: ", "b"), ("Chia ", "t"), ("Cin", "c"), (" kênh vào và ", "t"), ("Cout", "c"), (" kênh ra thành ", "t"), ("G nhóm độc lập", "b"), (" (không giao nhau).", "t")],
        [("• Mỗi nhóm tính chập riêng: ", "b"), ("Nhóm g chỉ lấy ", "t"), ("Cin/G", "c"), (" kênh vào để tính với ", "t"), ("Cout/G", "c"), (" bộ lọc kích thước ", "t"), ("K × K × (Cin/G)", "c"), (".", "t")],
        [("• Mức giảm tham số và FLOPs: ", "b"), ("Giảm chính xác đúng ", "t"), ("G lần", "b"), (" so với Standard Convolution: ", "t"), ("(Hout · Wout · Cout · K² · Cin) / G", "c"), (".", "t")],
    ], size=12, dy=18)

    # Sơ đồ kết nối Group 0 và Group 1
    gy = ya + 105
    # Nhóm 0
    rect(f, 40, gy, 140, 56, "#EAF2FF", BLUE, 1.2)
    f.text(110, gy + 22, "Nhóm 0: Input Channels", size=11, weight=700, anchor="middle", fill=BLUE)
    f.text(110, gy + 40, "Kênh 0 .. Cin/2 - 1", size=10.5, anchor="middle", fill=DARK)

    f.line([(180, gy + 28), (240, gy + 28)], BLUE, THICK)

    rect(f, 240, gy, 180, 56, "#FFF8E1", "#E65100", 1.2)
    f.text(330, gy + 22, "Filters Nhóm 0 (Cout/2)", size=11, weight=700, anchor="middle", fill="#E65100")
    f.text(330, gy + 40, "K × K × (Cin/2)", size=10.5, anchor="middle", fill=DARK)

    f.line([(420, gy + 28), (480, gy + 28)], BLUE, THICK)

    rect(f, 480, gy, 150, 56, "#E8F5E9", GREEN, 1.2)
    f.text(555, gy + 22, "Nhóm 0: Output", size=11, weight=700, anchor="middle", fill=GREEN)
    f.text(555, gy + 40, "Kênh 0 .. Cout/2 - 1", size=10.5, anchor="middle", fill=DARK)

    # Nhóm 1
    gy1 = gy + 70
    rect(f, 40, gy1, 140, 56, "#EAF2FF", BLUE, 1.2)
    f.text(110, gy1 + 22, "Nhóm 1: Input Channels", size=11, weight=700, anchor="middle", fill=BLUE)
    f.text(110, gy1 + 40, "Kênh Cin/2 .. Cin - 1", size=10.5, anchor="middle", fill=DARK)

    f.line([(180, gy1 + 28), (240, gy1 + 28)], "#6A1B9A", THICK)

    rect(f, 240, gy1, 180, 56, "#F3E5F5", "#6A1B9A", 1.2)
    f.text(330, gy1 + 22, "Filters Nhóm 1 (Cout/2)", size=11, weight=700, anchor="middle", fill="#6A1B9A")
    f.text(330, gy1 + 40, "K × K × (Cin/2)", size=10.5, anchor="middle", fill=DARK)

    f.line([(420, gy1 + 28), (480, gy1 + 28)], "#6A1B9A", THICK)

    rect(f, 480, gy1, 150, 56, "#E8F5E9", GREEN, 1.2)
    f.text(555, gy1 + 22, "Nhóm 1: Output", size=11, weight=700, anchor="middle", fill=GREEN)
    f.text(555, gy1 + 40, "Kênh Cout/2 .. Cout - 1", size=10.5, anchor="middle", fill=DARK)

    # Khung lưu ý không giao cắt
    f.a(f'<rect x="660" y="{gy}" width="210" height="126" rx="4" fill="#FFF9C4" stroke="#F57F17" stroke-width="1"/>')
    f.text(765, gy + 20, "Tính chất cô lập:", size=11.5, weight=700, anchor="middle", fill="#E65100")
    txt(f, 672, gy + 38, [
        [("• Không có đường nối chéo", "b")],
        [("  giữa Nhóm 0 và Nhóm 1.", "t")],
        [("• Kênh vào nhóm nào chỉ", "t")],
        [("  sinh kênh ra nhóm đó.", "t")],
        [("• Muốn trộn lại: Cần thêm", "t")],
        [("  lớp Channel Shuffle hoặc", "b")],
        [("  Pointwise Conv 1×1 phía sau.", "b")],
    ], size=10.5, dy=14)

    # ---- PHẦN 2: PHỔ LIÊN TỤC GIỮA CÁC BIẾN THỂ (G=1 -> G=Cin) ----
    yb, hb = ya + ha + 16, 260
    card(f, 10, yb, 880, hb, "2. Phổ liên tục giữa các biến thể Convolution qua tham số nhóm G")

    pw = 270
    # Cột 1: G = 1
    card(f, 24, yb + 36, pw, 205, "Cực đại kết nối: G = 1", 12.5, fill="#EAF2FF")
    txt(f, 34, yb + 66, [
        [("• Tên gọi: ", "b"), ("Standard Convolution 2D", "t")],
        [("• Cấu trúc: ", "b"), ("Mọi kênh vào kết nối với mọi", "t")],
        [("  bộ lọc đầu ra (Fully Connected).", "t")],
        [("• FLOPs: ", "b"), ("100% (Chuẩn gốc)", "c")],
        [("• Giao tiếp kênh: ", "b"), ("Tối đa (Cin × Cout)", "t")],
        [("• Hiệu năng NPU: ", "b"), ("Tận dụng mảng", "t")],
        [("  MAC tối đa (32×32 mode dễ lấp đầy).", "t")],
    ], size=11, dy=17)

    # Cột 2: 1 < G < Cin
    card(f, 318, yb + 36, pw, 205, "Phân nhóm song song: 1 < G < Cin", 12.5, fill="#FFF8E1")
    txt(f, 328, yb + 66, [
        [("• Tên gọi: ", "b"), ("Group Convolution", "t")],
        [("• Cấu trúc: ", "b"), ("Chia thành G cụm độc lập", "t")],
        [("  (ResNeXt, ShuffleNet, OPL group).", "t")],
        [("• FLOPs: ", "b"), ("Giảm 1/G lần", "c")],
        [("• Giao tiếp kênh: ", "b"), ("Chỉ trong nội bộ nhóm", "t")],
        [("• Hiệu năng NPU: ", "b"), ("Nếu Cin/G < 32,", "t")],
        [("  dễ bị lãng phí MAC trống (underuse).", "t")],
    ], size=11, dy=17)

    # Cột 3: G = Cin
    card(f, 612, yb + 36, pw, 205, "Cực đại phân tách: G = Cin", 12.5, fill="#E8F5E9")
    txt(f, 622, yb + 66, [
        [("• Tên gọi: ", "b"), ("Depthwise Convolution (DW)", "t")],
        [("• Cấu trúc: ", "b"), ("Mỗi kênh là 1 nhóm riêng biệt", "t")],
        [("  (Cin nhóm, mỗi nhóm 1 kênh vào/ra).", "t")],
        [("• FLOPs: ", "b"), ("Giảm Cin lần (Cực tiểu)", "c")],
        [("• Giao tiếp kênh: ", "b"), ("0% (Không trộn kênh)", "t")],
        [("• Hiệu năng NPU: ", "b"), ("Arithmetic Intensity", "t")],
        [("  rất thấp, dễ memory-bound (SURV).", "t")],
    ], size=11, dy=17)

    # ---- PHẦN 3: BẢNG SO SÁNH PHẦN CỨNG NPU RK3588 ----
    yc = yb + hb + 16
    f.text(10, yc + 4, "So sánh định lượng các chế độ Group Convolution trên NPU RK3588 (Cin=64, Cout=64, K=3)", size=15, weight=700)
    y = f.table(10, yc + 18, [150, 180, 180, 180, 190], ["Chỉ số", "G = 1 (Standard)", "G = 2", "G = 4", "G = 64 (Depthwise)"], [
        ["Kênh vào mỗi nhóm", "64 kênh", "32 kênh", "16 kênh", "1 kênh"],
        ["Số trọng số (Weights)", "64 × 64 × 9 = 36,864", "18,432 (giảm 2×)", "9,216 (giảm 4×)", "576 (giảm 64×)"],
        ["FLOPs lý thuyết", "100%", "50%", "25%", "1.56%"],
        ["Lấp đầy MAC 32×32 RK3588", ("lines", ["100% (Hoàn hảo,", "chia hết cho 32)"]), ("lines", ["100% (Vừa vặn,", "32 kênh/nhóm)"]), ("lines", ["50% (Bị hổng,", "chỉ 16 kênh/nhóm)"]), ("lines", ["< 5% (Rất thấp,", "chỉ 1 kênh/nhóm)"])],
        ["Độ trễ thực tế", "Nhanh trên MAC", "Giảm đáng kể", "Giảm ít hơn kỳ vọng", "Memory-bound nghẽn nạp"],
    ], size=11, line_h=15)

    # ---- LINK BOX ----
    y = link_box(f, 10, y + 14, 880, [
        [("TRM1 tr.2001: ", "b"), ("Mảng MAC của RK3588 vận hành ở chế độ INT8 32x32 mode (1024 MACs/cycle mỗi lõi).", "t")],
        [("OPL tr.60: ", "b"), ("Toán tử Convolution hỗ trợ thuộc tính \"• group: int\" trên phần cứng RK3588.", "t")],
        [("Quy tắc thiết kế mạng: ", "b"), ("Nên chọn số kênh mỗi nhóm (Cin/G) là bội số của 32 để tận dụng tối đa chiều rộng phần cứng.", "t")],
        "unknown: cơ chế phân bổ cụ thể của CNA Controller khi group không chia hết cho 32.",
    ])

    source(f, y + 8, "Nguồn: OPL tr.60 (RKNN Compiler Operator List); TRM1 tr.2001 (RK3588 TRM); MOBONE tr.4; SURV tr.19.")
    return f


# =====================================================================
# HÌNH C.5: TOÁN TỬ ADD VÀ RESIDUAL BLOCK (RESNET / CSP / YOLO)
# =====================================================================
def fig_add_residual():
    f = Fig(W, 1180)
    tier(f, "T2 chung")
    f.text(10, 48, "Toán tử Element-wise Add và Khối Residual Block: Từ bản chất toán học đến mạch ghép NPU", size=15.5, weight=700)

    # ---- 1. BẢN CHẤT TOÁN HỌC CỦA ELEMENT-WISE ADD ----
    ya, ha = 66, 215
    card(f, 10, ya, 880, ha, "1. Bản chất toán học của phép cộng Element-wise Add: C(h, w, c) = A(h, w, c) + B(h, w, c)")

    # Ma trận A (3x3)
    cs = 34
    ax, ay = 30, ya + 62
    f.text(ax + 1.5 * cs, ya + 46, "Ma trận A (Nhánh Conv F(x))", size=11.5, weight=700, fill=DARK, anchor="middle")
    mat_a = [
        [12, -4, 8],
        [3, 7, -2],
        [15, 0, 6],
    ]
    for r in range(3):
        for c in range(3):
            val = mat_a[r][c]
            bg = "#FFE082" if (r, c) == (0, 0) else ("#DCE8FA" if (r, c) == (0, 1) else "white")
            rect(f, ax + c * cs, ay + r * cs, cs, cs, bg, "#555555", 1.2)
            f.text(ax + c * cs + cs / 2, ay + r * cs + cs / 2, str(val), size=12, weight=700 if (r, c) in [(0, 0), (0, 1)] else 400, anchor="middle", fill=INK)

    # Dấu +
    f.text(155, ay + 1.5 * cs, "+", size=24, weight=700, anchor="middle", fill=DARK)

    # Ma trận B (3x3)
    bx, by = 180, ya + 62
    f.text(bx + 1.5 * cs, ya + 46, "Ma trận B (Nhánh Shortcut x)", size=11.5, weight=700, fill=DARK, anchor="middle")
    mat_b = [
        [5, 6, -3],
        [9, -2, 4],
        [1, 8, -5],
    ]
    for r in range(3):
        for c in range(3):
            val = mat_b[r][c]
            bg = "#FFE082" if (r, c) == (0, 0) else ("#DCE8FA" if (r, c) == (0, 1) else "white")
            rect(f, bx + c * cs, by + r * cs, cs, cs, bg, "#555555", 1.2)
            f.text(bx + c * cs + cs / 2, by + r * cs + cs / 2, str(val), size=12, weight=700 if (r, c) in [(0, 0), (0, 1)] else 400, anchor="middle", fill=INK)

    # Dấu =
    f.text(305, ay + 1.5 * cs, "=", size=24, weight=700, anchor="middle", fill=DARK)

    # Ma trận C (3x3)
    cx_mat, cy_mat = 330, ya + 62
    f.text(cx_mat + 1.5 * cs, ya + 46, "Ma trận C = A + B", size=11.5, weight=700, fill=DARK, anchor="middle")
    mat_c = [
        [17, 2, 5],
        [12, 5, 2],
        [16, 8, 1],
    ]
    for r in range(3):
        for c in range(3):
            val = mat_c[r][c]
            bg = "#C8E6C9" if (r, c) in [(0, 0), (0, 1)] else "white"
            rect(f, cx_mat + c * cs, cy_mat + r * cs, cs, cs, bg, "#555555", 1.2)
            f.text(cx_mat + c * cs + cs / 2, cy_mat + r * cs + cs / 2, str(val), size=12, weight=700 if (r, c) in [(0, 0), (0, 1)] else 400, anchor="middle", fill=INK)

    # Ví dụ số chi tiết bên dưới ma trận
    txt(f, 30, ya + 180, [
        [("• Tọa độ [0,0]: ", "b"), ("12 + 5 = 17 (ô vàng)", "t"), ("  |  ", "t"), ("• Tọa độ [0,1]: ", "b"), ("(-4) + 6 = 2 (ô lam -> ô lục)", "t")],
        [("• Nguyên lý: ", "b"), ("Cộng trực tiếp từng phần tử có cùng chỉ số [r, c, k]. Không nhân ma trận, không trượt cửa sổ.", "t")],
    ], size=11.5, dy=17)

    # Khung Shape Matching bên phải
    rect(f, 460, ya + 36, 415, 165, fill="#FFF8E1", stroke="#FFA000", sw=1.2, rx=4)
    f.text(667, ya + 53, "ĐIỀU KIỆN BẮT BUỘC: SHAPE MATCHING", size=12, weight=700, anchor="middle", fill="#E65100")
    txt(f, 474, ya + 74, [
        [("1. Hai tensor BẮT BUỘC cùng kích thước: ", "b"), ("Shape(A) == Shape(B) == [H, W, C]", "c")],
        [("2. Khi nào lệch kích thước? ", "b")],
        [("   • Khi khối Conv có stride = 2 (kích thước H, W giảm đi một nửa).", "t")],
        [("   • Khi số kênh đầu ra Cout khác số kênh đầu vào Cin.", "t")],
        [("3. Giải pháp: Projection Shortcut (Conv 1×1):", "b")],
        [("   Nhánh shortcut phải chèn thêm lớp ", "t"), ("Conv 1×1 (stride=s, Cout)", "c"), (" để đưa", "t")],
        [("   tensor x về đúng kích thước với F(x) trước khi thực hiện phép ADD.", "t")],
    ], size=11, dy=16)

    # ---- 2. CẤU TRÚC KHỐI RESIDUAL BLOCK VÀ GRADIENT HIGHWAY ----
    yb, hb = ya + ha + 16, 275
    card(f, 10, yb, 880, hb, "2. Cấu trúc khối Residual Block kinh điển và Đạo hàm chống triệt tiêu Gradient")

    # Sơ đồ khối Residual Block (x=24..420)
    label(f, 90, yb + 34, 180, 26, ["Đầu vào: Tensor x [H, W, C]"], size=11.5, weight=700, fill="#E3F2FD")
    f.line([(180, yb + 60), (180, yb + 72)], DARK, width=THIN, head=True)

    # Điểm rẽ nhánh (180, yb + 72)
    f.a(f'<circle cx="180" cy="{yb + 72}" r="3.5" fill="{DARK}"/>')
    f.line([(180, yb + 72), (180, yb + 86)], DARK, width=THIN, head=True)
    label(f, 90, yb + 86, 180, 25, ["Conv 3×3 + BatchNorm"], size=11.5, weight=700, fill="#FFF8E1")
    f.line([(180, yb + 111), (180, yb + 123)], DARK, width=THIN, head=True)
    label(f, 120, yb + 123, 120, 22, ["ReLU"], size=11, weight=700, fill="#F3E5F5")
    f.line([(180, yb + 145), (180, yb + 157)], DARK, width=THIN, head=True)
    label(f, 90, yb + 157, 180, 25, ["Conv 3×3 + BatchNorm"], size=11.5, weight=700, fill="#FFF8E1")
    f.line([(180, yb + 182), (180, yb + 200)], DARK, width=THIN, head=True)
    f.text(188, yb + 193, "F(x)", size=11, weight=700, fill=BLUE)

    # Nhánh shortcut
    f.line([(180, yb + 72), (320, yb + 72), (320, yb + 215), (205, yb + 215)], "#2E7D32", width=THICK, head=True)
    f.text(328, yb + 135, "Nhánh tắt Identity: x", size=11, weight=700, fill="#2E7D32", anchor="start")
    f.text(328, yb + 151, "(Không qua tính toán,", size=10, fill=DARK, anchor="start")
    f.text(328, yb + 165, " bảo toàn 100% tín hiệu)", size=10, fill=DARK, anchor="start")

    # Nút tròn ADD
    f.a(f'<circle cx="180" cy="{yb + 215}" r="15" fill="#C8E6C9" stroke="#2E7D32" stroke-width="1.8"/>')
    f.text(180, yb + 215, "+", size=20, weight=700, anchor="middle", fill="#1B5E20")
    f.text(152, yb + 215, "ADD", size=10.5, weight=700, anchor="end", fill="#1B5E20")

    # Từ nút ADD đi xuống ReLU và Output
    f.line([(180, yb + 230), (180, yb + 242)], DARK, width=THIN, head=True)
    label(f, 90, yb + 242, 180, 24, ["ReLU (Kích hoạt sau cộng)"], size=11, weight=700, fill="#E8F5E9")

    # Phân tích Gradient Highway bên phải (x=460..875)
    rect(f, 460, yb + 34, 415, 230, fill="white", stroke="#333333", sw=1.2, rx=4)
    f.text(667, yb + 51, "VÌ SAO CẦN PHÉP CỘNG SHORTCUT? (GRADIENT HIGHWAY)", size=11.5, weight=700, anchor="middle", fill=BLUE)

    rect(f, 475, yb + 67, 385, 34, fill="#E8F5E9", stroke="#2E7D32", sw=1.2, rx=3)
    f.text(667, yb + 84, "Đầu ra: y = F(x) + x   ===>   Đạo hàm: ∂y/∂x = ∂F(x)/∂x + 1", size=12, weight=700, anchor="middle", fill="#1B5E20")

    txt(f, 474, yb + 115, [
        [("• Vấn đề mạng thuần (Plain Net không shortcut):", "b")],
        [("  Khi lan truyền ngược, gradient nhân liên tiếp qua hàng chục ma trận trọng số.", "t")],
        [("  Nếu các giá trị đạo hàm < 1, gradient nhanh chóng triệt tiêu về 0 (Vanishing).", "t")],
        [("• Hằng số \"+1\" thần kỳ (Gradient Highway):", "b")],
        [("  Ngay cả khi các lớp tích chập F(x) có ", "t"), ("∂F(x)/∂x ≈ 0", "c"), (", đạo hàm tổng vẫn giữ", "t")],
        [("  nguyên giá trị ", "t"), ("ít nhất là 1", "b"), (". Tín hiệu lỗi truyền thẳng về các tầng đầu tiên!", "t")],
        [("• Dễ tối ưu hơn: ", "b"), ("Mạng chỉ cần học phần sai số thặng dư ", "t"), ("F(x) = H(x) - x", "c"), (".", "t")],
        [("  Nếu lớp không mang lại lợi ích, mạng chỉ cần ép F(x) -> 0 (ánh xạ đồng nhất).", "t")],
    ], size=10.8, dy=15.5)

    # ---- 3. CƠ CHẾ PHẦN CỨNG NPU RK3588: ADD RỜI VS ADD GHÉP ----
    yc, hc = yb + hb + 16, 250
    card(f, 10, yc, 880, hc, "3. Cơ chế phần cứng NPU RK3588: Add rời (Disjoint) vs Add ghép on-chip (Fused)")

    # Khối trái: Add rời
    rect(f, 24, yc + 34, 415, 204, fill="#FFF5F5", stroke="#E53935", sw=1.2, rx=4)
    f.text(231, yc + 52, "Add Rời (Disjoint Add) - Nghẽn Băng Thông DDR", size=12, weight=700, anchor="middle", fill="#C62828")
    txt(f, 36, yc + 72, [
        [("• Luồng thực thi:", "b")],
        [("  1. Lớp Conv tính xong F(x) -> ", "t"), ("Ghi ra RAM DDR", "b"), (" (DMA Write 1).", "t")],
        [("  2. Nhánh shortcut x cũng nằm tại ", "t"), ("RAM DDR", "b"), (".", "t")],
        [("  3. Lớp Add riêng: NPU DMA đọc F(x) và x từ DDR (", "t"), ("DMA Read 2 lần", "b"), (").", "t")],
        [("  4. Thực hiện phép cộng -> ", "t"), ("Ghi kết quả y ra DDR", "b"), (" (DMA Write 2).", "t")],
        [("• Hậu quả phần cứng:", "b")],
        [("  • Tốn ", "t"), ("2 lần ghi + 2 lần đọc RAM DDR", "c"), (" cho mỗi khối residual.", "t")],
        [("  • Đẩy NPU vào trạng thái ", "t"), ("Memory-Bound", "b"), (" (nghẽn bus AXI).", "t")],
        [("  • Các đơn vị MAC phải dừng chờ (stall), làm tụt FPS thực tế.", "t")],
    ], size=10.8, dy=14.8)

    # Khối phải: Add ghép on-chip
    rect(f, 460, yc + 34, 415, 204, fill="#F1F8E9", stroke="#43A047", sw=1.2, rx=4)
    f.text(667, yc + 52, "Add Ghép On-Chip (Fused ConvolutionAdd / ConvAddRelu)", size=12, weight=700, anchor="middle", fill="#2E7D32")
    txt(f, 472, yc + 72, [
        [("• Luồng thực thi phần cứng RK3588 (OPL tr.61, 63):", "b")],
        [("  1. Khối Conv tính toán psums trong ", "t"), ("Mảng MAC INT8 32×32", "b"), (".", "t")],
        [("  2. Nhánh Shortcut (Input1) nạp từ CBUF trực tiếp vào ", "t"), ("Accumulator INT32", "b"), ("!", "t")],
        [("  3. Phép cộng F(x) + x hoàn tất ", "t"), ("ngay trên thanh ghi on-chip", "b"), (".", "t")],
        [("  4. Chuyển thẳng sang ", "t"), ("DPU để kích hoạt ReLU", "b"), (" mà không qua DDR.", "t")],
        [("• Lợi ích vượt trội:", "b")],
        [("  • ", "t"), ("0 lần truy cập DDR ngoài", "b"), (" giữa Conv và Add (Tiết kiệm 100% I/O phụ).", "t")],
        [("  • RKNN Compiler phân bổ song song trên ", "t"), ("cả 3 lõi NPU (Core 0, 1, 2)", "b"), (".", "t")],
        [("  • Đạt thông lượng cực đại, triệt tiêu hoàn toàn Memory Wall.", "t")],
    ], size=10.8, dy=14.8)

    # ---- 4. BẢNG SO SÁNH ĐỊNH LƯỢNG ----
    yd = yc + hc + 16
    f.text(10, yd + 4, "So sánh chi tiết Add rời và Add ghép on-chip trên NPU RK3588", size=15, weight=700)
    y = f.table(10, yd + 18, [160, 350, 360], ["Chỉ số so sánh", "Add rời (Disjoint Add)", "Add ghép on-chip (ConvolutionAdd)"], [
        ["Vị trí thực hiện phép cộng", "Khối ALU / Vector Unit độc lập", "Thanh ghi tích lũy Accumulator (trong CNA)"],
        ["Truy cập RAM DDR", ("lines", ["Ghi Conv ra DDR, sau đó nạp lại", "cả 2 tensor vào để cộng (2 Read + 2 Write)"]), "0 lần truy cập DDR (Khép kín 100% on-chip)"],
        ["Băng thông bộ nhớ", "Tốn gấp đôi băng thông, dễ nghẽn bus AXI", "Tiết kiệm tối đa băng thông, loại bỏ Memory Wall"],
        ["Hỗ trợ đa lõi RK3588", "Phụ thuộc vào kernel Add độc lập", "Hỗ trợ chia đều trên cả 3 Core 0, 1, 2 (OPL tr.61, 63)"],
        ["Toán tử RKNN đại diện", "Toán tử Add riêng lẻ (kém tối ưu)", "ConvolutionAdd, ConvolutionAddRelu (Tối ưu cao nhất)"],
    ], size=11, line_h=15.5)

    # ---- LINK BOX ----
    y = link_box(f, 10, y + 14, 880, [
        [("OPL tr.61: ", "b"), ("Toán tử ConvolutionAdd: \"Convolution 与 Add 融合计算, Output = Add(Conv(Input0), Input1)\", hỗ trợ đa lõi RK3588.", "t")],
        [("OPL tr.63: ", "b"), ("Toán tử ConvolutionAddRelu: \"Convolution 与 Add 及 Relu 融合计算, Output = Relu(Add(Conv(Input0), Input1))\", hỗ trợ đa lõi RK3588.", "t")],
        [("TRM1 tr.1985: ", "b"), ("Khối CNA gồm mac array và accumulator INT32, nối trực tiếp sang DPU (relu, leaky_relu).", "t")],
        [("MOBONE tr.4: ", "b"), ("Khối cơ bản với \"reparameterizable skip connection [13] with batchnorm along\" trong kiến trúc di động hiện đại.", "t")],
    ])

    source(f, y + 8, "Nguồn: OPL tr.61, 63 (RKNN Compiler Operator List); TRM1 tr.1985 (RK3588 TRM); MOBONE tr.4.")
    return f


def main():
    figs = [
        ("hc-0-truc-quan-convolution", fig_intuitive),
        ("hc-1-toan-va-im2col", fig_im2col),
        ("hc-2-cna-va-fusion", fig_cna_fusion),
        ("hc-3-dwconv-va-pointwise", fig_dwconv_pointwise),
        ("hc-4-group-convolution", fig_group_conv),
        ("hc-5-toan-tu-add-va-residual-block", fig_add_residual),
    ]
    run(figs, HERE)


if __name__ == "__main__":
    main()

