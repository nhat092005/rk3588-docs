"""Ghi chú chuyên đề: Hàm kích hoạt ReLU và SiLU trên NPU RK3588 (03-ham-kich-hoat).

Sinh 3 hình chất lượng cao chuẩn visual_guide:
  - ha-1-toan-hoc-va-do-thi (T2 chung): So sánh toán học, đồ thị và đặc tính giữa ReLU và SiLU
  - ha-2-so-do-mach-phan-cung-va-residual (T1 RK3588): Sơ đồ mạch silicon MAC, Tích lũy Accumulator, Clamp vs LUT và Residual Add
  - ha-3-ghep-toan-tu-va-da-loi-opl (T1 RK3588): Cơ chế ghép toán tử Fused vs Disjoint và Hỗ trợ đa lõi OPL

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 4 cấp thư mục: activations -> _notes -> 00-tong-quan -> npu_rk3588 -> docs/tools/visual_guide
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
from figlib import BLUE, DARK, GREEN, INK, RED, Fig, run, source  # noqa: E402

W = 900
CALC = "#EAF2FF"      # Màu nền phép tính / số học
ORANGE = "#E65100"
PURPLE = "#7B1FA2"
TEAL = "#00796B"
BOX_BG = "#F8F9FA"


def tier(f, label):
    f.tier(W - 130, 10, label)


def txt(f, x, y, ls, size=12, dy=16, fill=INK, anchor="start"):
    for i, ln in enumerate(ls):
        f.rich(x, y + dy * i, ln, size=size, anchor=anchor, fill=fill)
    return y + dy * len(ls)


def rect(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=3):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


# ==============================================================================
# HÌNH 1: TOÁN HỌC VÀ ĐỒ THỊ
# ==============================================================================
def draw_axes_and_plots(f, x, y, w, h, func_type="relu"):
    """Vẽ trục toạ độ và đồ thị hàm số / đạo hàm."""
    rect(f, x, y, w, h, fill="#FCFDFD", stroke="#B0BEC5", sw=1.0, rx=4)
    ox = x + w * 0.45
    oy = y + h * 0.72
    scale_x = w * 0.12
    scale_y = h * 0.20

    # Lưới trục toạ độ
    f.a(f'<line x1="{x + 15}" y1="{oy}" x2="{x + w - 15}" y2="{oy}" stroke="#90A4AE" stroke-width="1.2"/>')
    f.a(f'<line x1="{ox}" y1="{y + 15}" x2="{ox}" y2="{y + h - 15}" stroke="#90A4AE" stroke-width="1.2"/>')
    f.text(x + w - 12, oy, "x", size=11, fill="#546E7A", anchor="start")
    f.text(ox, y + 10, "y", size=11, fill="#546E7A", anchor="middle")
    f.text(ox - 6, oy + 10, "0", size=10, fill="#78909C", anchor="end")

    if func_type == "relu":
        # ReLU: f(x) = max(0, x)
        pts_f = [(ox - 2.8 * scale_x, oy), (ox, oy), (ox + 2.5 * scale_x, oy - 2.5 * scale_y)]
        path_f = f"M {pts_f[0][0]} {pts_f[0][1]} L {pts_f[1][0]} {pts_f[1][1]} L {pts_f[2][0]} {pts_f[2][1]}"
        f.a(f'<path d="{path_f}" fill="none" stroke="{BLUE}" stroke-width="2.6"/>')

        # Đạo hàm f'(x): 0 khi x < 0; 1 khi x > 0
        f.a(f'<line x1="{ox - 2.8 * scale_x}" y1="{oy}" x2="{ox}" y2="{oy}" stroke="{RED}" stroke-width="1.8" stroke-dasharray="4 3"/>')
        f.a(f'<line x1="{ox}" y1="{oy - scale_y}" x2="{ox + 2.5 * scale_x}" y2="{oy - scale_y}" stroke="{RED}" stroke-width="1.8" stroke-dasharray="4 3"/>')
        f.a(f'<circle cx="{ox}" cy="{oy}" r="3" fill="none" stroke="{RED}" stroke-width="1.5"/>')
        f.a(f'<circle cx="{ox}" cy="{oy - scale_y}" r="3" fill="{RED}"/>')

        f.text(ox + 0.3 * scale_x, oy - 2.1 * scale_y, "f(x) = max(0, x)", size=11.5, weight=700, fill=BLUE)
        f.text(ox + 1.2 * scale_x, oy - scale_y + 14, "f'(x) = 1 (x > 0)", size=10.5, weight=600, fill=RED)
        f.text(ox - 2.5 * scale_x, oy + 14, "f'(x) = 0 (x < 0)", size=10.5, weight=600, fill=RED)

    else:
        # SiLU: f(x) = x / (1 + e^-x)
        pts_silu = []
        pts_dsilu = []
        for step in range(-28, 26):
            xv = step * 0.1
            sig = 1.0 / (1.0 + math.exp(-xv))
            yv = xv * sig
            dyv = sig + xv * sig * (1.0 - sig)
            pts_silu.append((ox + xv * scale_x, oy - yv * scale_y))
            pts_dsilu.append((ox + xv * scale_x, oy - dyv * scale_y))

        path_f = f"M {pts_silu[0][0]} {pts_silu[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in pts_silu[1:])
        f.a(f'<path d="{path_f}" fill="none" stroke="{GREEN}" stroke-width="2.6"/>')

        path_df = f"M {pts_dsilu[0][0]} {pts_dsilu[0][1]} " + " ".join(f"L {p[0]} {p[1]}" for p in pts_dsilu[1:])
        f.a(f'<path d="{path_df}" fill="none" stroke="{RED}" stroke-width="1.8" stroke-dasharray="4 3"/>')

        f.text(ox + 0.4 * scale_x, oy - 2.0 * scale_y, "f(x) = x · σ(x)", size=11.5, weight=700, fill=GREEN)
        f.text(ox + 1.3 * scale_x, oy - 0.7 * scale_y, "f'(x) trơn liên tục", size=10.5, weight=600, fill=RED)
        f.text(ox - 2.5 * scale_x, oy + 20, "Cực tiểu: x ≈ -1.28, y ≈ -0.28", size=9.5, fill="#555555")


def fig_math():
    f = Fig(W, 460)
    tier(f, "T2 chung")
    f.text(10, 24, "So sánh toán học, đồ thị và đặc tính giữa ReLU và SiLU", size=16, weight=700, fill=DARK)

    # ---- A. ĐỒ THỊ VÀ CÔNG THỨC ----
    f.text(10, 56, "A. Bản chất hàm số, đạo hàm và đồ thị trực quan", size=13.5, weight=700, fill=DARK)

    gw = 425
    gh = 160
    draw_axes_and_plots(f, 10, 72, gw, gh, func_type="relu")
    f.text(20, 90, "ReLU: f(x) = max(0, x)", size=12.5, weight=700, fill=DARK)
    f.text(20, 106, "Tuyến tính từng đoạn, dập âm về 0", size=10.5, fill="#555555")

    draw_axes_and_plots(f, 455, 72, gw, gh, func_type="silu")
    f.text(465, 90, "SiLU (Swish-1): f(x) = x · σ(x)", size=12.5, weight=700, fill=DARK)
    f.text(465, 106, "x / (1 + e⁻ˣ), phi tuyến trơn (OPL tr.47)", size=10.5, fill="#555555")

    y = 72 + gh + 18

    # ---- B. BẢNG SO SÁNH TOÀN DIỆN ----
    f.text(10, y, "B. So sánh toàn diện các đặc tính giữa hai hàm kích hoạt", size=13.5, weight=700, fill=DARK)
    y = f.table(10, y + 12, [125, 245, 260, 240], ["Khía cạnh", "ReLU (max(0, x))", "SiLU (x · sigmoid(x))", "Nhận xét & Nguồn"], [
        ["Đạo hàm f'(x)", "f'(x) = 1 khi x > 0; 0 khi x < 0", "f'(x) = σ(x) + x·σ(x)(1 - σ(x))", "SiLU có đạo hàm trơn liên tục"],
        ["Hiện tượng Dying", "Dễ chết nơ-ron nếu gradient dập về 0", "Tránh được nhờ dải gradient âm nhỏ", "SiLU giúp tối ưu mạng sâu tốt hơn"],
        ["Độ chính xác", "Thường thấp hơn SiLU 0.5 - 2% mAP", "Chuẩn trong YOLOv5/v8, mAP cao hơn", "SiLU performs with better accuracy [Y6 tr.8]"],
        ["Tốc độ ghép lớp", "Ghép trực tiếp vào Conv cực nhanh", "Tốn bảng tra (LUT) hoặc xấp xỉ", "ReLU speed advantage in Conv [Y6 tr.8]"],
        ["Đánh đổi trên NPU", "Ưu tiên độ trễ, tiết kiệm tài nguyên", "Ưu tiên độ chính xác cao nhất", "impact more prominent on NPUs [ACTNAS tr.8]"],
    ], size=11.5, line_h=15)

    source(f, y + 8, "Nguồn: OPL tr.47; Y6 tr.8; ACTNAS tr.6, tr.8.")
    return f


# ==============================================================================
# HÌNH 2: SƠ ĐỒ MẠCH PHẦN CỨNG VÀ RESIDUAL
# ==============================================================================
def fig_hw_circuit():
    f = Fig(W, 610)
    tier(f, "T1 RK3588")
    f.text(10, 24, "Vi kiến trúc Mạch Silicon NPU RK3588: MAC, Tích lũy, Clamp vs LUT và Residual Add", size=16, weight=700, fill=DARK)

    # ---- PHẦN A: SƠ ĐỒ LUỒNG DỮ LIỆU MẠCH SILICON KHỐI CNA VÀ DPU ----
    f.text(10, 54, "A. Luồng dữ liệu phần cứng bên trong một lõi NPU (CNA & DPU) [TRM1 tr.1985]", size=13.5, weight=700, fill=DARK)

    # Vẽ các khối phần cứng liên hoàn
    y_b = 94

    # 1. Khối CBUF & Pre-process Controller
    rect(f, 10, y_b, 170, 110, fill="#E3F2FD", stroke=BLUE, sw=1.5, rx=5)
    f.text(10 + 170 / 2, y_b + 18, "Bộ đệm CBUF 384KB", size=11.5, weight=700, fill=BLUE, anchor="middle")
    f.text(10 + 170 / 2, y_b + 32, "& Pre-process Controller", size=10, fill="#555555", anchor="middle")
    txt(f, 18, y_b + 50, [
        [("• Chứa Feature Map & Weight", "t")],
        [("• Điều phối nạp dữ liệu", "t")],
        [("  cho mảng tính chập [TRM1]", "t")],
    ], size=10, dy=15)

    # Mũi tên CBUF -> MAC Array
    f.a(f'<polygon points="186,{y_b+55} 198,{y_b+55} 194,{y_b+50} 202,{y_b+55} 194,{y_b+60} 198,{y_b+55}" fill="{DARK}" stroke="{DARK}" stroke-width="2"/>')

    # 2. Mảng MAC Array
    rect(f, 206, y_b, 185, 110, fill="#EDE7F6", stroke=PURPLE, sw=1.5, rx=5)
    f.text(206 + 185 / 2, y_b + 18, "Mảng MAC Array", size=11.5, weight=700, fill=PURPLE, anchor="middle")
    f.text(206 + 185 / 2, y_b + 32, "1024 MACs/lõi (INT8 32x32)", size=10, fill="#555555", anchor="middle")
    txt(f, 214, y_b + 50, [
        [("• Phép nhân chập Conv:", "t")],
        [("  Input x Weight [TRM1 tr.2001]", "t")],
        [("• Xuất ra các partial sums", "t")],
    ], size=10, dy=15)

    # Mũi tên MAC -> Accumulator
    f.a(f'<polygon points="397,{y_b+55} 409,{y_b+55} 405,{y_b+50} 413,{y_b+55} 405,{y_b+60} 409,{y_b+55}" fill="{DARK}" stroke="{DARK}" stroke-width="2"/>')

    # 3. Bộ tích lũy Accumulator
    rect(f, 417, y_b, 185, 110, fill="#FFF8E1", stroke=ORANGE, sw=1.5, rx=5)
    f.text(417 + 185 / 2, y_b + 18, "Bộ tích lũy Accumulator", size=11.5, weight=700, fill=ORANGE, anchor="middle")
    f.text(417 + 185 / 2, y_b + 32, "Thanh ghi tích lũy 32-bit", size=10, fill="#555555", anchor="middle")
    txt(f, 425, y_b + 50, [
        [("• Cộng dồn partial sums", "t")],
        [("• Nhận nhánh Residual Add", "b")],
        [("  cộng tắt trực tiếp tại đây!", "b")],
    ], size=10, dy=15)

    # Nhánh Residual Shortcut từ trên đi xuống Accumulator
    f.a(f'<line x1="417" y1="80" x2="509" y2="80" stroke="{TEAL}" stroke-width="2" stroke-dasharray="5 3"/>')
    f.a(f'<line x1="509" y1="80" x2="509" y2="{y_b}" stroke="{TEAL}" stroke-width="2" stroke-dasharray="5 3"/>')
    f.a(f'<polygon points="509,{y_b-1} 505,{y_b-8} 513,{y_b-8}" fill="{TEAL}"/>')
    f.text(417, 72, "Nhánh Residual Shortcut (Tensor đầu vào tầng trước)", size=10, weight=700, fill=TEAL)

    # Mũi tên Accumulator -> DPU
    f.a(f'<polygon points="608,{y_b+55} 620,{y_b+55} 616,{y_b+50} 624,{y_b+55} 616,{y_b+60} 620,{y_b+55}" fill="{DARK}" stroke="{DARK}" stroke-width="2"/>')

    # 4. Khối DPU (Data Processing Unit)
    rect(f, 628, y_b, 262, 110, fill="#E8F5E9", stroke=GREEN, sw=1.5, rx=5)
    f.text(628 + 262 / 2, y_b + 18, "Khối DPU (Data Processing Unit)", size=11.5, weight=700, fill=GREEN, anchor="middle")
    f.text(628 + 262 / 2, y_b + 32, "Thực thi hàm kích hoạt [TRM1 tr.1985]", size=10, fill="#555555", anchor="middle")
    txt(f, 636, y_b + 50, [
        [("• Đường A (ReLU): ", "b"), ("Mạch Clamp cắt số âm", "t")],
        [("• Đường B (SiLU): ", "b"), ("Bảng tra LUT / Bộ xấp xỉ", "t")],
        [("• Xuất Feature Map đã kích hoạt", "t")],
    ], size=10, dy=15)

    # ---- PHẦN B: ĐỐI CHIẾU CƠ CHẾ CLAMP VS BẢNG TRA LUT ----
    y_c = y_b + 110 + 20
    f.text(10, y_c, "B. Đối chiếu cơ chế phần cứng: Mạch cắt ngưỡng Clamp (ReLU) so với Bảng tra LUT (SiLU)", size=13.5, weight=700, fill=DARK)

    cw = 430
    ch = 120
    y_card = y_c + 14

    # Card 1: Clamp ReLU
    rect(f, 10, y_card, cw, ch, fill="#F1F8E9", stroke=GREEN, sw=1.5, rx=5)
    f.text(20, y_card + 18, "1. Cơ chế Clamp (ReLU / Leaky ReLU)", size=12, weight=700, fill=GREEN)
    txt(f, 20, y_card + 36, [
        [("• Bản chất mạch: ", "b"), ("Mạch so sánh logic số nguyên (Comparator Logic).", "t")],
        [("• Cơ chế: ", "b"), ("Kiểm tra bit dấu của thanh ghi Accumulator. Nếu x < 0 thì dập", "t")],
        [("  toàn bộ bit về 0; nếu x > 0 thì giữ nguyên giá trị.", "t")],
        [("• Chi phí phần cứng: ", "b"), ("Zero-cost (gần như 0 tốn thêm chu kỳ xung nhịp).", "b")],
        [("• Ghép lớp: ", "b"), ("Ghép trực tiếp sau Conv và Add thành ConvolutionAddRelu.", "t")],
    ], size=10.5, dy=16)

    # Card 2: LUT SiLU
    rect(f, 460, y_card, cw, ch, fill="#FFF3E0", stroke=ORANGE, sw=1.5, rx=5)
    f.text(470, y_card + 18, "2. Cơ chế Bảng tra LUT & Bộ xấp xỉ phần cứng (SiLU / Swish)", size=12, weight=700, fill=ORANGE)
    txt(f, 470, y_card + 36, [
        [("• Bản chất mạch: ", "b"), ("Bảng tra Look-Up Table (LUT) hoặc xấp xỉ đa thức.", "t")],
        [("• Cơ chế: ", "b"), ("Hàm x / (1 + e⁻ˣ) chứa số mũ e và phép chia, không thể tính", "t")],
        [("  bằng cổng logic đơn giản mà phải tra bảng giá trị rời rạc.", "t")],
        [("• Chi phí phần cứng: ", "b"), ("Tốn thêm chu kỳ đọc bộ đệm và diện tích silicon.", "b")],
        [("• Ghép lớp: ", "b"), ("RKNN ghép thành ConvolutionSwish nhưng chưa hỗ trợ đa lõi.", "t")],
    ], size=10.5, dy=16)

    # ---- PHẦN C: UNKNOWN CÔNG BỐ ----
    y_u = y_card + ch + 14
    y_end = f.unknown(10, y_u, [
        "Vi kiến trúc mạch tính toán nội bộ (bảng tra LUT hay bộ xấp xỉ phần cứng) cho hàm phi tuyến SiLU",
        "không được công bố trong tài liệu kỹ thuật của NPU RK3588 (TRM và Datasheet chỉ mô tả danh mục op).",
    ], w=880)

    source(f, y_end + 8, "Nguồn: TRM1 tr.1984-1985, tr.2001; DS tr.7; OPL tr.47, tr.60, tr.63.")
    return f


# ==============================================================================
# HÌNH 3: GHÉP TOÁN TỬ VÀ ĐA LÕI TRONG OPL
# ==============================================================================
def fig_fusion_multicore():
    f = Fig(W, 640)
    tier(f, "T1 RK3588")
    f.text(10, 24, "Cơ chế Ghép toán tử (Operator Fusion) và Hỗ trợ Đa lõi NPU RK3588 (OPL)", size=16, weight=700, fill=DARK)

    # ---- PHẦN A: TOÁN TỬ GHÉP VS TOÁN TỬ RỜI RẠC ----
    f.text(10, 56, "A. So sánh đường đi dữ liệu: Toán tử ghép (Fused) so với Toán tử tách rời (Disjoint)", size=13.5, weight=700, fill=DARK)

    fw = 430
    fh = 115
    y_f = 72

    # Khung Fused Operator
    rect(f, 10, y_f, fw, fh, fill="#E8F5E9", stroke=GREEN, sw=1.5, rx=5)
    f.text(20, y_f + 18, "Toán tử ghép (Fused Operator: ConvolutionRelu, ConvolutionSwish)", size=11.5, weight=700, fill=GREEN)
    txt(f, 20, y_f + 36, [
        [("• Đường đi dữ liệu: ", "b"), ("Chạy khép kín 100% trong SRAM nội bộ (CBUF 384KB).", "t")],
        [("• Cơ chế: ", "b"), ("Mảng MAC tính chập xong -> DPU áp dụng kích hoạt ngay lập tức.", "t")],
        [("• Hiệu quả: ", "b"), ("Không ghi feature map trung gian ra DRAM DDR. Băng thông tối ưu!", "b")],
    ], size=10.5, dy=17)

    # Khung Disjoint Operator
    rect(f, 460, y_f, fw, fh, fill="#FFEBEE", stroke=RED, sw=1.5, rx=5)
    f.text(470, y_f + 18, "Toán tử tách rời (Disjoint Operator: exSwish, Add rời)", size=11.5, weight=700, fill=RED)
    txt(f, 470, y_f + 36, [
        [("• Đường đi dữ liệu: ", "b"), ("Conv chạy xong -> Ghi feature map ra ngoài RAM DDR.", "t")],
        [("• Cơ chế: ", "b"), ("Sau đó NPU nạp lại dữ liệu từ DDR vào để chạy lớp exSwish.", "t")],
        [("• Hiệu quả: ", "b"), ("Gây tắc nghẽn băng thông bộ nhớ (memory-bound), độ trễ đội lên cao.", "b")],
    ], size=10.5, dy=17)

    # ---- PHẦN B: BẢNG TOÁN TỬ TRONG OPL VÀ ĐA LÕI ----
    y_b = y_f + fh + 18
    f.text(10, y_b, "B. Phân loại toán tử kích hoạt trong RKNN Compiler & Khả năng chạy đa lõi (OPL)", size=13.5, weight=700, fill=DARK)

    y_tab = f.table(10, y_b + 12, [135, 175, 230, 150, 190], ["Hàm kích hoạt", "Op sau ghép (Compiler)", "Cơ chế phần cứng NPU", "Hỗ trợ đa lõi (OPL)", "Đánh giá thực tế"], [
        ["ReLU", "ConvolutionRelu", "Clamp ngưỡng sau mảng MAC", "多核联合: 支持 [tr.60]", "Chia đều 3 core, tăng tốc ~35%"],
        ["SiLU (ghép)", "ConvolutionSwish", "Bảng tra LUT / xử lý phi tuyến", "多核联合: 暂不支持 [tr.63]", "Dồn 100% vào Core 0 (T3)"],
        ["SiLU (rời)", "exSwish", "Toán tử phần tử rời rạc", "多核联合: 尚不支持 [tr.98]", "Tốn bộ nhớ DDR, chỉ chạy Core 0"],
        ["ReLU + Add", "ConvolutionAddRelu", "MAC + Tích lũy + Clamp", "多核联合: 支持 [tr.63]", "Hỗ trợ shortcut residual 3 core"],
    ], size=11.5, line_h=15)

    # ---- PHẦN C: THỰC TẾ ĐO T3 VÀ QUY TẮC CHỌN MODEL ----
    y_c = y_tab + 18
    f.text(10, y_c, "C. Đo kiểm thực tế T3 trên board RK3588S và Quy tắc chọn model của đề tài", size=13.5, weight=700, fill=DARK)

    ch = 95
    rect(f, 10, y_c + 12, W - 20, ch, fill=CALC, stroke=BLUE, sw=1.4, rx=5)
    txt(f, 24, y_c + 28, [
        [("Đo thực tế trên board RK3588S (T3): ", "b"),
         ("Mô hình YOLOv8n SiLU dồn 100% cả 57 lớp ConvExSwish vào Core 0 (100%/0%/0%),", "t")],
        [(" ", "t"),
         ("không tận dụng được 3 core khi đặt core_mask=CORE_0_1_2 [LOG 2026-10-10_yolo-phaseA].", "t")],
        [("Tốc độ ReLU: ", "b"),
         ("Mô hình ReLU chạy nhanh hơn SiLU ~35% trên NPU nhờ ConvRelu chia đều trên cả 3 core [LOG].", "t")],
        [("Quy tắc chọn model (tmp/02_decisions/2026-10-11): ", "b"),
         ("Chọn model nhanh nhất có mAP50-95 INT8 không thấp hơn SiLU quá 1.0 điểm; nếu không rõ thì giữ SiLU.", "b")],
    ], size=11, dy=16)

    # ---- PHẦN D: UNKNOWN ----
    y_u = y_c + 12 + ch + 14
    y_end = f.unknown(10, y_u, [
        "Nguyên nhân vi kiến trúc cụ thể khiến NPU RK3588 không hỗ trợ đa lõi cho ConvolutionSwish và exSwish",
        "(trong khi ConvolutionRelu hỗ trợ hoàn toàn) không được tài liệu OPL giải thích chi tiết.",
    ], w=880)

    source(f, y_end + 8, "Nguồn: OPL tr.47, tr.60, tr.63, tr.98; LOG 2026-10-10_t3-board-silu-resize; REPO tmp/02_decisions/2026-10-11_model-selection-rule.md.")
    return f


def main():
    figs = [
        ("ha-1-toan-hoc-va-do-thi", fig_math),
        ("ha-2-so-do-mach-phan-cung-va-residual", fig_hw_circuit),
        ("ha-3-ghep-toan-tu-va-da-loi-opl", fig_fusion_multicore),
    ]
    run(figs, HERE)


if __name__ == "__main__":
    main()
