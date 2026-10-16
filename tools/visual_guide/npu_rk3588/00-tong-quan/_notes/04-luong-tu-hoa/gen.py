"""Ghi chú chuyên đề: Lượng tử hóa trong NPU RK3588 (04-luong-tu-hoa).

Sinh 3 hình chuyên sâu chuẩn visual_guide:
  - hq-1-per-layer-quantization (T2 chung): Per-Layer (Per-Tensor) Quantization, Scale/ZP và Vấn đề Outlier kênh
  - hq-2-per-channel-quantization (T1 RK3588): Per-Channel Quantization cho Weight, cơ chế Rescale và lý do Activation chỉ Per-Layer
  - hq-3-danh-doi-luong-tu-va-quy-tac-chon-model (T2 chung): Đánh đổi lượng tử hóa INT8 và Quy tắc chọn model

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 4 cấp thư mục: quantization -> _notes -> 00-tong-quan -> npu_rk3588 -> docs/tools/visual_guide
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

W = 900
STAT = "#FFF1CC"      # Màu highlight bộ nhớ cục bộ / stationary
CALC = "#EAF2FF"      # Màu nền phép tính / logic
P0, P1 = "#DCE8FA", "#DDF0DE"
ORANGE = "#E65100"


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
# HÌNH Q.1: NGUYÊN LÝ PER-LAYER (PER-TENSOR) VÀ HIỆN TƯỢNG OUTLIER
# =====================================================================
def fig_per_layer():
    f = Fig(W, 1080)
    tier(f, "T2 chung")
    f.text(10, 48, "Nguyên lý Lượng tử hóa Per-Layer (Per-Tensor) và Vấn đề Outlier kênh", size=15.5, weight=700)

    # ---- PHẦN 1: ÁNH XẠ TOÁN HỌC SCALE VÀ ZERO-POINT ----
    ya, ha = 66, 215
    card(f, 10, ya, 880, ha, "1. Bản chất toán học: Ánh xạ Affine giữa Trục số thực và Lưới số nguyên INT8")

    # Cột trái: Công thức toán học
    f.a(f'<rect x="24" y="{ya + 36}" width="420" height="162" rx="4" fill="#FAFAFA" stroke="#999999" stroke-width="1"/>')
    f.text(36, ya + 54, "Công thức lượng tử hóa Affine (NAGEL Eq. 4 & 6):", size=12, weight=700, fill=DARK)
    txt(f, 36, ya + 74, [
        [("• Lượng tử hóa (Quantize): ", "b"), ("q = clamp(round(x / s) + z, -128, 127)", "c")],
        [("• Phục hồi (Dequantize): ", "b"), ("x ≈ s · (q - z)", "c")],
        [("• Scale factor (s): ", "b"), ("s = (x_max - x_min) / (q_max - q_min)", "c")],
        [("  (Bước nhảy giữa 2 nấc nguyên liên tiếp; s là số thực dương float)", "t")],
        [("• Zero-point (z): ", "b"), ("z = round(-x_min / s) + q_min", "c")],
        [("  (Số nguyên dịch chuyển để đảm bảo số 0 thực không bị sai số)", "t")],
    ], size=11, dy=17)

    # Cột phải: Trực quan trục số
    f.a(f'<rect x="460" y="{ya + 36}" width="410" height="162" rx="4" fill="#F0F8FF" stroke="{BLUE}" stroke-width="1.2"/>')
    f.text(472, ya + 54, "Trực quan hóa lưới lượng tử 256 mức (INT8):", size=12, weight=700, fill=BLUE)

    # Trục số thực float
    f.text(472, ya + 78, "Trục số thực x (FP32):", size=11, weight=700, fill=DARK)
    f.line([(472, ya + 96), (850, ya + 96)], DARK, THIN)
    f.text(472, ya + 110, "x_min (-10.0)", size=10, fill=RED)
    f.text(640, ya + 110, "0.0 (Zero)", size=10, weight=700, fill=BLUE)
    f.text(820, ya + 110, "x_max (+10.0)", size=10, fill=GREEN)

    # Mũi tên ánh xạ
    f.line([(660, ya + 116), (660, ya + 130)], BLUE, THICK)
    f.text(675, ya + 125, "s = 20/255 ≈ 0.078", size=10.5, weight=700, fill=BLUE)

    # Trục số nguyên INT8
    f.text(472, ya + 144, "Lưới số nguyên q (INT8):", size=11, weight=700, fill=DARK)
    f.line([(472, ya + 160), (850, ya + 160)], DARK, THIN)
    for tick_x in range(480, 850, 24):
        f.line([(tick_x, ya + 156), (tick_x, ya + 164)], BLUE, THIN)
    f.text(472, ya + 175, "q_min (-128)", size=10, fill=RED)
    f.text(640, ya + 175, "z = 0 (Zero-point)", size=10, weight=700, fill=BLUE)
    f.text(820, ya + 175, "q_max (+127)", size=10, fill=GREEN)

    # ---- PHẦN 2: CƠ CHẾ PER-LAYER (TOÀN TENSOR 1 SCALE) ----
    yb, hb = ya + ha + 16, 260
    card(f, 10, yb, 880, hb, "2. Cơ chế Per-Layer (Per-Tensor): Một bộ (s, z) duy nhất cho toàn bộ các kênh")

    txt(f, 24, yb + 36, [
        [("• Phạm vi áp dụng: ", "b"), ("Dùng ", "t"), ("1 giá trị Scale s và 1 giá trị Zero-point z", "b"), (" chung cho toàn bộ tensor [H, W, C].", "t")],
        [("• Quy tắc xác định: ", "b"), ("x_min và x_max được lấy từ cực trị của ", "t"), ("toàn bộ tất cả các kênh gộp lại", "b"), (" (UG232 tr.120).", "t")],
    ], size=12, dy=18)

    # Vẽ 3 kênh minh họa
    ch_y = yb + 80
    cw, ch = 260, 150

    # Kênh 0
    rect(f, 24, ch_y, cw, ch, "#FAFAFA", BLUE, 1.2)
    f.text(154, ch_y + 20, "Kênh 0: Phân bố hẹp", size=11.5, weight=700, anchor="middle", fill=BLUE)
    f.text(154, ch_y + 36, "Dải giá trị thực: [-1.2, +1.1]", size=11, anchor="middle", fill=DARK)
    f.a(f'<rect x="44" y="{ch_y + 48}" width="220" height="24" rx="3" fill="#EAF2FF" stroke="{BLUE}" stroke-width="1"/>')
    f.text(154, ch_y + 64, "Biên độ dao động nhỏ", size=10.5, anchor="middle", fill=BLUE)
    txt(f, 34, ch_y + 88, [
        [("• Dải mong muốn: ", "t"), ("[-1.2, +1.1]", "c")],
        [("• Nếu dùng scale chung s=0.196:", "b")],
        [("  Chỉ chiếm ", "t"), ("~12 mức INT8!", "b"), (" (Mất độ phân giải)", "t")],
    ], size=10.5, dy=16)

    # Kênh 1 (Outlier)
    rect(f, 320, ch_y, cw, ch, "#FFF8E1", RED, 1.4)
    f.text(450, ch_y + 20, "Kênh 1: Có Outlier cực lớn", size=11.5, weight=700, anchor="middle", fill=RED)
    f.text(450, ch_y + 36, "Dải giá trị thực: [-25.0, +25.0]", size=11, weight=700, anchor="middle", fill=RED)
    f.a(f'<rect x="340" y="{ch_y + 48}" width="220" height="24" rx="3" fill="#FFEBEE" stroke="{RED}" stroke-width="1.2"/>')
    f.text(450, ch_y + 64, "Outlier kéo giãn toàn bộ dải", size=10.5, weight=700, anchor="middle", fill=RED)
    txt(f, 330, ch_y + 88, [
        [("• Quyết định min-max của Layer:", "b")],
        [("  x_min = -25.0, x_max = +25.0", "c")],
        [("• Scale Layer: ", "b"), ("s = 50 / 255 = 0.196", "c")],
        [("  Kênh 1 chiếm trọn 256 mức INT8", "t")],
    ], size=10.5, dy=16)

    # Kênh 2
    rect(f, 616, ch_y, cw, ch, "#FAFAFA", BLUE, 1.2)
    f.text(746, ch_y + 20, "Kênh 2: Phân bố hẹp", size=11.5, weight=700, anchor="middle", fill=BLUE)
    f.text(746, ch_y + 36, "Dải giá trị thực: [-0.8, +0.9]", size=11, anchor="middle", fill=DARK)
    f.a(f'<rect x="636" y="{ch_y + 48}" width="220" height="24" rx="3" fill="#EAF2FF" stroke="{BLUE}" stroke-width="1"/>')
    f.text(746, ch_y + 64, "Biên độ dao động nhỏ", size=10.5, anchor="middle", fill=BLUE)
    txt(f, 626, ch_y + 88, [
        [("• Dải mong muốn: ", "t"), ("[-0.8, +0.9]", "c")],
        [("• Nếu dùng scale chung s=0.196:", "b")],
        [("  Chỉ chiếm ", "t"), ("~9 mức INT8!", "b"), (" (Co cụm nghiêm trọng)", "t")],
    ], size=10.5, dy=16)

    # ---- PHẦN 3: BẢNG SO SÁNH HIỆN TƯỢNG CO CỤM TRÊN LƯỚI INT8 ----
    yc = yb + hb + 16
    f.text(10, yc + 4, "Hậu quả của Per-Layer khi gặp Outlier: Phân bổ 256 mức lượng tử INT8", size=15, weight=700)
    y = f.table(10, yc + 18, [140, 200, 220, 320], ["Kênh trong Layer", "Dải số thực gốc", "Số mức INT8 thực tế sử dụng", "Hậu quả độ chính xác (GHOLAMI tr.6)"], [
        ["Kênh 0", "[-1.2, +1.1]", "12 / 256 mức (chỉ dùng ~4.7%)", ("lines", ["Mất sạch chi tiết đặc trưng nhỏ;", "làm tròn thô gây nhiễu lớn"])],
        ["Kênh 1 (Outlier)", "[-25.0, +25.0]", "256 / 256 mức (dùng 100%)", ("lines", ["Biểu diễn tốt kênh outlier,", "nhưng 'bắt cóc' toàn bộ độ phân giải"])],
        ["Kênh 2", "[-0.8, +0.9]", "9 / 256 mức (chỉ dùng ~3.5%)", ("lines", ["Gần như bị làm tròn thành hằng số;", "triệt tiêu tín hiệu gradient"])],
        ["Tổng kết Layer", "[-25.0, +25.0]", "Trung bình tận dụng rất thấp", ("lines", ["Bad quantization resolution;", "đây là nguyên nhân sụt mAP mô hình"])],
    ], size=11.5, line_h=15)

    # ---- LINK BOX ----
    y = link_box(f, 10, y + 14, 880, [
        [("NAGEL tr.4, 5: ", "b"), ("Lưới lượng tử đều 2^b mức; Per-tensor quantization dùng chung 1 quantizer cho cả tensor.", "t")],
        [("GHOLAMI tr.6: ", "b"), ("Layerwise quantization áp chung 1 range cho mọi filter, gây bad quantization resolution cho kênh hẹp.", "t")],
        [("UG232 tr.120: ", "b"), ("RKNN-Toolkit2 áp dụng Per-Layer cho activation và các giá trị trung gian trên NPU RK3588.", "t")],
        "unknown: ngưỡng outlier cụ thể mà RKNN thresholding tự động cắt (clip) trong thuật toán KL-Divergence.",
    ])

    source(f, y + 8, "Nguồn: NAGEL tr.4, 5 (Qualcomm Whitepaper); GHOLAMI tr.6 (Survey 2021); UG232 tr.120 (RKNN SDK User Guide).")
    return f


# =====================================================================
# HÌNH Q.2: NGUYÊN LÝ PER-CHANNEL CHO WEIGHT VÀ CƠ CHẾ RESCALE TRÊN NPU
# =====================================================================
def fig_per_channel():
    f = Fig(W, 1140)
    tier(f, "T1 RK3588")
    f.text(10, 48, "Nguyên lý Lượng tử hóa Per-Channel cho Weight và Cơ chế Rescale trên NPU", size=15.5, weight=700)

    # ---- PHẦN 1: CƠ CHẾ PER-CHANNEL CHO WEIGHT ----
    ya, ha = 66, 260
    card(f, 10, ya, 880, ha, "1. Cơ chế Per-Channel cho Trọng số (Weight): Mỗi Output Filter có một Scale riêng")

    txt(f, 24, ya + 36, [
        [("• Nguyên lý cốt lõi: ", "b"), ("Thay vì ép cả tensor trọng số dùng chung 1 scale, ", "t"), ("mỗi Output Channel c có bộ (s_w,c, z_w,c) riêng", "b"), (" (NAGEL tr.5).", "t")],
        [("• Khắc phục hoàn toàn Outlier: ", "b"), ("Filter nào có dải rộng thì dùng scale lớn; Filter có dải hẹp dùng scale nhỏ.", "t")],
        [("• ", "t"), ("100% các filter đều tận dụng tối đa 256 mức INT8", "b"), (", bảo toàn tối đa độ chính xác (NAGEL tr.8, GHOLAMI tr.7).", "t")],
    ], size=12, dy=18)

    # 3 Khối so sánh sau khi dùng Per-Channel
    ch_y = ya + 95
    cw, ch = 260, 145

    # Filter 0
    rect(f, 24, ch_y, cw, ch, "#E8F5E9", GREEN, 1.2)
    f.text(154, ch_y + 20, "Filter Kênh 0 (Output 0)", size=11.5, weight=700, anchor="middle", fill=GREEN)
    f.text(154, ch_y + 36, "Dải gốc: [-1.2, +1.1]", size=11, anchor="middle", fill=DARK)
    txt(f, 34, ch_y + 56, [
        [("• Scale riêng: ", "b"), ("s_w,0 = 2.3 / 255 ≈ 0.009", "c")],
        [("• Số mức INT8: ", "b"), ("256 / 256 mức!", "c")],
        [("• Độ mịn: ", "b"), ("Cực cao, không bị co cụm", "t")],
        [("• mAP: ", "b"), ("Bảo toàn hoàn hảo đặc trưng", "t")],
    ], size=10.5, dy=16)

    # Filter 1
    rect(f, 320, ch_y, cw, ch, "#E8F5E9", GREEN, 1.2)
    f.text(450, ch_y + 20, "Filter Kênh 1 (Output 1)", size=11.5, weight=700, anchor="middle", fill=GREEN)
    f.text(450, ch_y + 36, "Dải gốc: [-25.0, +25.0] (Outlier)", size=11, anchor="middle", fill=DARK)
    txt(f, 330, ch_y + 56, [
        [("• Scale riêng: ", "b"), ("s_w,1 = 50.0 / 255 ≈ 0.196", "c")],
        [("• Số mức INT8: ", "b"), ("256 / 256 mức!", "c")],
        [("• Độ mịn: ", "b"), ("Vừa đủ cho dải outlier lớn", "t")],
        [("• Không ảnh hưởng các kênh khác!", "b")],
    ], size=10.5, dy=16)

    # Filter 2
    rect(f, 616, ch_y, cw, ch, "#E8F5E9", GREEN, 1.2)
    f.text(746, ch_y + 20, "Filter Kênh 2 (Output 2)", size=11.5, weight=700, anchor="middle", fill=GREEN)
    f.text(746, ch_y + 36, "Dải gốc: [-0.8, +0.9]", size=11, anchor="middle", fill=DARK)
    txt(f, 626, ch_y + 56, [
        [("• Scale riêng: ", "b"), ("s_w,2 = 1.7 / 255 ≈ 0.0067", "c")],
        [("• Số mức INT8: ", "b"), ("256 / 256 mức!", "c")],
        [("• Độ mịn: ", "b"), ("Siêu chi tiết, cực chuẩn", "t")],
        [("• Giữ nguyên độ tương phản nhỏ", "t")],
    ], size=10.5, dy=16)

    # ---- PHẦN 2: CƠ CHẾ RESCALE TẠI ĐẦU RA ACCUMULATOR ----
    yb, hb = ya + ha + 16, 275
    card(f, 10, yb, 880, hb, "2. Cơ chế toán học và Bộ Rescale tại đầu ra Accumulator trên phần cứng NPU")

    f.a(f'<rect x="24" y="{yb + 36}" width="420" height="220" rx="4" fill="#FAFAFA" stroke="#999999" stroke-width="1"/>')
    f.text(36, yb + 54, "Tách Scale ra khỏi tổng tích chập (NAGEL tr.8):", size=12, weight=700, fill=DARK)
    txt(f, 36, yb + 74, [
        [("• Phép tính chập tại kênh ra c:", "b")],
        [("  y_c = Σ_j (w_c,j · x_j) ≈ Σ_j [ s_w,c · q_w · s_x · q_x ]", "c")],
        [("• Vì s_w,c và s_x không phụ thuộc vào j (kênh vào):", "b")],
        [("  y_c ≈ ", "t"), ("(s_w,c · s_x)", "b"), (" · Σ_j (q_w · q_x)", "c")],
        [("• Mảng MAC chỉ tính: ", "b"), ("Accumulator_c = Σ_j (q_w · q_x)", "c")],
        [("  (Phép cộng dồn INT32 thuần túy, 0 lần rescale giữa chừng).", "t")],
        [("• Rescale đầu ra: ", "b"), ("q_y,c = round( M_c · Accumulator_c ) + z_y", "c")],
        [("  với hệ số ", "t"), ("M_c = (s_w,c · s_x) / s_y", "b"), (" (nhân 1 lần tại đầu ra).", "t")],
    ], size=11, dy=17)

    # Sơ đồ khối Rescale phần cứng
    f.a(f'<rect x="460" y="{yb + 36}" width="410" height="220" rx="4" fill="#F0F8FF" stroke="{BLUE}" stroke-width="1.2"/>')
    f.text(472, yb + 54, "Luồng phần cứng NPU: Accumulator INT32 -> Rescale M_c -> INT8", size=11.5, weight=700, fill=BLUE)

    blk(f, 475, yb + 75, 110, 48, ["MAC Array", "INT8 nhân"], size=11, fill=P1)
    f.line([(585, yb + 99), (620, yb + 99)], DARK, THICK)

    blk(f, 620, yb + 75, 115, 48, ["Accumulator", "INT32 psums"], size=11, fill="#FFF9C4")
    f.line([(735, yb + 99), (770, yb + 99)], DARK, THICK)

    blk(f, 770, yb + 75, 85, 48, ["Rescale M_c", "Fixed-point"], size=11, fill="#FCE4EC")

    f.line([(812, yb + 123), (812, yb + 150)], BLUE, THICK)

    rect(f, 740, yb + 150, 115, 42, "#E8F5E9", GREEN, 1.4)
    f.text(797, yb + 168, "Output INT8", size=12, weight=700, anchor="middle", fill=GREEN)
    f.text(797, yb + 182, "vào CBUF / DPU", size=10, anchor="middle", fill=DARK)

    txt(f, 475, yb + 140, [
        [("• Hệ số M_c: ", "b"), ("Lưu sẵn trong thanh ghi cho từng kênh c.", "t")],
        [("• Tốc độ: ", "b"), ("Phần cứng nhân 1 chu kỳ clock tại DPU.", "t")],
        [("• Hoàn toàn không tốn băng thông RAM DDR ngoài.", "b")],
    ], size=10.5, dy=16)

    # ---- PHẦN 3: VÌ SAO ACTIVATION KHÔNG THỂ PER-CHANNEL? ----
    yc = yb + hb + 16
    f.text(10, yc + 4, "Vì sao RKNN và NPU RK3588 chỉ hỗ trợ Per-Channel cho Weight mà KHÔNG cho Activation?", size=15, weight=700)
    y = f.table(10, yc + 18, [150, 350, 380], ["Đặc điểm phần cứng", "Weight: Hỗ trợ Per-Channel (Khả thi)", "Activation: Bắt buộc Per-Layer (Không khả thi)"], [
        ["Vị trí hệ số Scale", ("lines", ["Scale s_w,c phụ thuộc kênh ra c;", "nằm NGOÀI dấu tổng tích chập Σ_j"]), ("lines", ["Nếu Activation per-channel, s_x,j đổi theo kênh vào j;", "Scale s_x,j nằm BÊN TRONG dấu tổng Σ_j!"])],
        ["Thao tác mảng MAC", ("lines", ["Mảng MAC cộng dồn các tích q_w · q_x tự do;", "thanh ghi Accumulator lưu psums INT32"]), ("lines", ["Buộc phải rescale từng psum trước khi cộng dồn;", "cần bộ nhân rescale tại MỖI ô PE của mảng MAC!"])],
        ["Độ phức tạp silicon", ("lines", ["Chỉ cần 1 bộ nhân rescale tại đầu ra thanh ghi;", "diện tích silicon cực nhỏ, chi phí gần như 0"]), ("lines", ["Mảng MAC 32×32 (1024 MAC) phình to gấp đôi diện tích;", "tiêu thụ năng lượng quá lớn, phần cứng không làm"])],
        ["Hỗ trợ trên RKNN", "Hỗ trợ 100% trong rknn.config / build", "Chỉ hỗ trợ Per-Layer (UG232 tr.120, NAGEL tr.8)"],
    ], size=11.5, line_h=15)

    # ---- LINK BOX ----
    y = link_box(f, 10, y + 14, 880, [
        [("UG232 tr.120: ", "b"), ("Per-Channel quantization is only applied to the weights, while activation values are still quantized using Per-Layer.", "t")],
        [("NAGEL tr.8: ", "b"), ("by applying a separate per-channel weight scale factor without requiring rescaling... not all commercial hardware supports it.", "t")],
        [("GHOLAMI tr.7: ", "b"), ("Channelwise quantization is currently the standard method for convolutional weights.", "t")],
        "unknown: số bit định dạng cố định chính xác (fixed-point precision) của thanh ghi chứa hệ số M_c trong khối DPU.",
    ])

    source(f, y + 8, "Nguồn: UG232 tr.120 (RKNN SDK User Guide); NAGEL tr.5, 8 (Qualcomm Whitepaper); GHOLAMI tr.7 (Survey 2021).")
    return f


# ==============================================================================
# HÌNH 3: ĐÁNH ĐỔI LƯỢNG TỬ HÓA VÀ QUY TẮC CHỌN MODEL (hq-3-danh-doi-luong-tu-va-quy-tac-chon-model)
# ==============================================================================
def fig_quantization_and_selection():
    f = Fig(W, 640)
    tier(f, "T2 chung")
    f.text(10, 24, "Đánh đổi Lượng tử hóa INT8 so với FP16 và Quy tắc chọn model của đề tài", size=16, weight=700, fill=DARK)

    # ---- PHẦN A: BẢN CHẤT PHẦN CỨNG INT8 VS FP16 TRÊN RK3588 ----
    f.text(10, 56, "A. Bản chất phần cứng: Tại sao NPU RK3588 ưu tiên lượng tử hóa INT8?", size=13.5, weight=700, fill=DARK)

    card_w = 425
    card_h = 130
    y_card = 72

    # Card 1: FP16
    rect(f, 10, y_card, card_w, card_h, fill="#FFF9C4", stroke="#FBC02D", sw=1.5, rx=5)
    f.text(10 + card_w / 2, y_card + 18, "FP16 (Float16) - Chuẩn suy luận dấu phẩy động", size=12, weight=700, fill="#B78103", anchor="middle")
    txt(f, 20, y_card + 36, [
        [("• Năng lực tính toán: ", "b"), ("512 MACs/chu kỳ/core [TRM1 tr.1984]", "t")],
        [("• Tổng 3 lõi @ 1 GHz: ", "b"), ("3.072 TFLOPS (phép tính số học)", "t")],
        [("• Dung lượng & Băng thông: ", "b"), ("2 bytes / tham số; chiếm nhiều SRAM/DDR", "t")],
        [("• Độ chính xác: ", "b"), ("Bảo toàn gần như nguyên vẹn kết quả FP32 của PC", "t")],
    ], size=11, dy=18)

    # Card 2: INT8
    rect(f, 465, y_card, card_w, card_h, fill="#E8F5E9", stroke=GREEN, sw=1.5, rx=5)
    f.text(465 + card_w / 2, y_card + 18, "INT8 (W8A8) - Chuẩn lượng tử hóa tối ưu NPU", size=12, weight=700, fill=GREEN, anchor="middle")
    txt(f, 475, y_card + 36, [
        [("• Năng lực tính toán: ", "b"), ("1024 MACs/chu kỳ/core (GẤP ĐÔI FP16) [TRM1 tr.1984]", "t")],
        [("• Tổng 3 lõi @ 1 GHz: ", "b"), ("6.144 TOPS (Vendor công bố 'up to 6TOPs') [DS tr.7]", "t")],
        [("• Dung lượng & Băng thông: ", "b"), ("1 byte / tham số; giảm 50% áp lực truyền dữ liệu DRAM", "t")],
        [("• Độ chính xác: ", "b"), ("Có sai số làm tròn (quantization noise), sụt giảm nhẹ mAP", "t")],
    ], size=11, dy=18)

    # Khung tính sai số lượng tử hóa
    y_q = y_card + card_h + 10
    rect(f, 10, y_q, W - 20, 48, fill=CALC, stroke="#90CAF9", sw=1.2, rx=4)
    txt(f, 20, y_q + 14, [
        [("Độ sụt giảm do lượng tử hóa (Quantization Drop): ", "b"),
         ("Delta_mAP = mAP50-95(FP32) - mAP50-95(INT8)", "b")],
        [("Mục tiêu tối ưu: ", "b"),
         ("Đạt tốc độ tăng gấp đôi của INT8 nhưng khống chế Delta_mAP ở mức tối thiểu", "t")],
    ], size=11.5, dy=17)

    # ---- PHẦN B: QUY TẮC CHỌN MODEL TRIỂN KHAI CỦA ĐỀ TÀI ----
    y_b = y_q + 64
    f.text(10, y_b, "B. Quy tắc chọn model triển khai của đề tài (Chốt trước khi có số thực nghiệm)", size=13.5, weight=700, fill=DARK)

    # Khung quy tắc
    rule_h = 92
    y_r = y_b + 12
    rect(f, 10, y_r, W - 20, rule_h, fill="#FBE9E7", stroke=ORANGE, sw=1.5, rx=5)
    f.text(20, y_r + 18, "QUY TẮC CHỌN MODEL [REPO tmp/02_decisions/2026-10-11_model-selection-rule.md:25]:", size=12, weight=700, fill=ORANGE)
    txt(f, 20, y_r + 36, [
        [("1. Tiêu chí chính: ", "b"),
         ("Chọn model NHANH NHẤT (trung vị Tier 1 eval_perf ở core_mask=AUTO) có mAP50-95 INT8 trên board", "t")],
        [("   ", "t"),
         ("KHÔNG THẤP HƠN YOLOv8n SiLU INT8 QUÁ 1.0 ĐIỂM (tuyệt đối, ví dụ 0.560 so 0.570).", "b")],
        [("2. Quy tắc an toàn (Fallback): ", "b"),
         ("Nếu không có model nào nhanh hơn rõ ràng (chênh lệch nằm trong biên độ nhiễu giữa các phiên), GIỮ YOLOV8N SILU.", "t")],
    ], size=11.5, dy=17)

    # ---- PHẦN C: BẢNG SO SÁNH 3 MÔ HÌNH ỨNG VIÊN ----
    y_c = y_r + rule_h + 16
    f.text(10, y_c, "C. Đặc tính kỹ thuật 3 mô hình ứng viên trên tập dữ liệu sfchd_5class", size=13.5, weight=700, fill=DARK)

    y_tab = f.table(10, y_c + 12, [180, 110, 170, 420], ["Mô hình ứng viên", "Activation", "Khả năng NPU đa lõi", "Ưu thế kỹ thuật & Đánh đổi thực nghiệm"], [
        ["YOLOv8n SiLU (Baseline)", "SiLU", "Chỉ Core 0 (ConvExSwish)", "Chuẩn đối chiếu; mAP50-95 cao nhất (0.5908); T_npu ~21.4 ms"],
        ["YOLOv8n ReLU (Fine-tuned)", "ReLU", "Chia 3 lõi (~35/34/32%)", "Nhanh hơn 35% trên NPU (~13.9 ms); Cần kiểm tra độ sụt mAP sau INT8"],
        ["YOLO26n (No-NMS Head)", "SiLU + PSA", "Chỉ Core 0", "Bỏ NMS trên CPU; NPU trễ hơn 13-16% do nhiều lớp nhỏ tuần tự"],
    ], size=11.5, line_h=15)

    source(f, y_tab + 8, "Nguồn: TRM1 tr.1984; DS tr.7; REPO tmp/02_decisions/2026-10-11_model-selection-rule.md; LOG 2026-10-10_yolo-phaseA; LOG 2026-10-10_t3-board-silu-resize.")
    return f


def main():
    figs = [
        ("hq-1-per-layer-quantization", fig_per_layer),
        ("hq-2-per-channel-quantization", fig_per_channel),
        ("hq-3-danh-doi-luong-tu-va-quy-tac-chon-model", fig_quantization_and_selection),
    ]
    run(figs, HERE)


if __name__ == "__main__":
    main()

