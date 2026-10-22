#!/usr/bin/env python3
"""Chuyen de: Luong tu hoa va Chien luoc PTQ/QAT (03-luong-tu-hoa).

Sinh cac hinh vector SVG minh hoa:
  1. qnt-01-affine-mapping:
     Anh xa luong tu hoa Affine: truc so thuc lien tuc [alpha, beta], buoc nhay Scale (s),
     Zero-point (z), sai so lam tron (rounding) va sai so kep bien (clipping).
  2. qnt-02-qat-ste-backward:
     Co che QAT voi FakeQuant o lan truyen thuan va Straight-Through Estimator (STE)
     o lan truyen nguoc (dao ham bac thang xap xi bang 1 trong khoang clip).

Chay: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# docs/tools/figure_gen/01-kien-thuc-nen/03-luong-tu-hoa -> ../.. = docs/tools/figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "03-luong-tu-hoa"
    )
)

W = 880
BOX_STROKE = "#334155"


def tier(f, label, x=W - 130, y=14):
    f.tier(x, y, label)


def rect(f, x, y, w, h, fill="white", stroke=BOX_STROKE, sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{dash}/>')


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN, dashed=False):
    if color not in (BLUE, GREEN, RED, GRAY, INK):
        color = INK
    f.line([(x1, y1), (x2, y2)], color, width=sw, dashed=dashed, head=True)


# ==============================================================================
# 1. HINH ANH XA AFFINE (qnt-01-affine-mapping)
# ==============================================================================
def fig_affine_mapping():
    H = 465
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Nguyên lý ánh xạ lượng tử hóa Affine (Uniform Asymmetric Quantization)", size=13.5, weight=700, fill=DARK)

    # 1. Trục số thực liên tục x (Phía trên)
    f.text(30, 50, "1. Miền số thực liên tục x (FP32): x_min = α, x_max = β", size=10, weight=700, fill="#0F172A")

    # Vùng clipping âm (trái)
    rect(f, 30, 62, 90, 38, fill="#FEF2F2", stroke="#DC2626", sw=1.0, dashed=True)
    f.text(75, 78, "Clipping âm", size=9, weight=700, fill="#B91C1C", anchor="middle")
    f.text(75, 91, "x < α (tràn dưới)", size=8, fill="#7F1D1D", anchor="middle")

    # Miền động hữu ích [alpha, beta]
    rect(f, 125, 62, 370, 38, fill="#F0F7FF", stroke="#2563EB", sw=1.2)
    f.text(310, 78, "Miền giá trị lượng tử hóa hợp lệ [α, β]", size=10, weight=700, fill="#1E40AF", anchor="middle")
    f.text(310, 91, "Phạm vi động (Dynamic Range) = β - α", size=8.5, fill="#334155", anchor="middle")

    # Vùng clipping dương (phải)
    rect(f, 500, 62, 90, 38, fill="#FEF2F2", stroke="#DC2626", sw=1.0, dashed=True)
    f.text(545, 78, "Clipping dương", size=9, weight=700, fill="#B91C1C", anchor="middle")
    f.text(545, 91, "x > β (tràn trên)", size=8, fill="#7F1D1D", anchor="middle")

    # Trục số thực
    arrow(f, 20, 116, 600, 116, INK, THICK)
    ticks_real = [
        (125, "α = r_min"),
        (220, "-0.5"),
        (290, "0.0 (Zero thực)"),
        (380, "+1.2"),
        (495, "β = r_max"),
    ]
    for tx, lbl in ticks_real:
        f.line([(tx, 110), (tx, 122)], INK, width=1.5, head=False)
        f.text(tx, 133, lbl, size=8.5, fill="#0F172A", anchor="middle")

    # Mũi tên ánh xạ dọc từ Real xuống Int (thẳng dọc 100%)
    arrow(f, 290, 144, 290, 172, GREEN, THICK)
    rect(f, 305, 148, 108, 20, fill="#F0FDF4", stroke="#16A34A", sw=1.0)
    f.text(359, 160, "0.0 → z (chính xác)", size=7.8, fill="#166534", anchor="middle")

    arrow(f, 495, 144, 495, 172, BLUE, THICK)
    arrow(f, 125, 144, 125, 172, BLUE, THICK)

    # 2. Trục số nguyên rời rạc q (Phía dưới)
    rect(f, 125, 175, 370, 48, fill="#FFFBEB", stroke="#D97706", sw=1.2)
    f.text(310, 192, "2. Miền số nguyên rời rạc q (UINT8 / INT8): {0, 1, 2, ..., 255}", size=9.5, weight=700, fill="#92400E", anchor="middle")
    f.text(310, 208, "Khoảng cách giữa hai mức = Scale s = (β - α) / (q_max - q_min)", size=8.5, fill="#78350F", anchor="middle")

    # Trục số nguyên
    f.line([(125, 240), (495, 240)], "#D97706", width=2.0, head=False)
    ticks_int = [
        (125, "q_min = 0"),
        (185, "q_1"),
        (245, "q_2"),
        (290, "q = z (Zero-point)"),
        (360, "q_k"),
        (430, "q_n"),
        (495, "q_max = 255"),
    ]
    for tx, lbl in ticks_int:
        f.line([(tx, 234), (tx, 246)], "#D97706", width=1.8, head=False)
        f.text(tx, 257, lbl, size=8.5, fill="#92400E", anchor="middle")

    # Minh họa Rounding Error giữa hai mức q_1 và q_2
    rect(f, 175, 275, 150, 48, fill="#F8FAFC", stroke="#64748B", sw=1.1, rx=4)
    f.text(250, 291, "Sai số làm tròn (Rounding)", size=9, weight=700, fill="#0F172A", anchor="middle")
    f.text(250, 305, "ε ∈ [-s/2, +s/2] khi làm tròn", size=8.2, fill="#475569", anchor="middle")
    f.text(250, 317, "round(x/s) về số nguyên gần nhất", size=8, fill="#475569", anchor="middle")

    # Minh họa Clipping Error
    rect(f, 30, 275, 135, 48, fill="#FEF2F2", stroke="#DC2626", sw=1.1, rx=4)
    f.text(97, 291, "Sai số kẹp biên (Clipping)", size=9, weight=700, fill="#B91C1C", anchor="middle")
    f.text(97, 305, "Cắt cụt mọi giá trị ngoài", size=8.2, fill="#7F1D1D", anchor="middle")
    f.text(97, 317, "khoảng [α, β] về q_min/q_max", size=8, fill="#7F1D1D", anchor="middle")

    # 3. Khung phân biệt Asymmetric vs Symmetric (Bên phải)
    rect(f, 610, 50, 250, 355, fill="#F8FAFC", stroke="#64748B", sw=1.2, rx=5)
    rect(f, 610, 50, 250, 32, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=5)
    f.text(735, 70, "Đối xứng (Sym) vs Bất đối xứng (Asym)", size=9.8, weight=700, fill="#0F172A", anchor="middle")

    f.text(622, 98, "1. Lượng tử hóa Asymmetric (Affine):", size=9, weight=700, fill="#1E40AF")
    f.text(622, 114, "• Zero-point z ≠ 0, thuộc tập số nguyên.", size=8.5, fill="#334155")
    f.text(622, 128, "• Tối ưu cho Activation sau ReLU (x ≥ 0).", size=8.5, fill="#334155")
    f.text(622, 142, "• Tận dụng 100% dải biểu diễn 256 mức.", size=8.5, fill="#166534")
    f.text(622, 156, "• Nhược điểm: Phép nhân sinh số hạng chéo:", size=8.5, fill="#B91C1C")
    f.text(632, 170, "W*X = s_w*s_x*(q_w - z_w)*(q_x - z_x).", size=8, fill="#475569")

    f.line([(620, 184), (850, 184)], "#CBD5E1", width=THIN, head=False)

    f.text(622, 202, "2. Lượng tử hóa Symmetric:", size=9, weight=700, fill="#92400E")
    f.text(622, 218, "• Zero-point cố định z = 0, miền [-β, β].", size=8.5, fill="#334155")
    f.text(622, 232, "• Tiêu chuẩn vàng cho Trọng số (Weights).", size=8.5, fill="#166534")
    f.text(622, 246, "• Triệt tiêu hoàn toàn z_w, đơn giản hóa MAC:", size=8.5, fill="#166534")
    f.text(632, 260, "W*X = s_w*s_x * SUM(q_w * (q_x - z_x)).", size=8, fill="#475569")
    f.text(622, 276, "• Nhược điểm: Lãng phí dải âm nếu phân phối", size=8.5, fill="#B91C1C")
    f.text(632, 290, "dữ liệu lệch một phía (như ReLU).", size=8, fill="#475569")

    f.line([(620, 304), (850, 304)], "#CBD5E1", width=THIN, head=False)

    f.text(622, 322, "3. Công thức chuẩn (Nagel 2021 Eq. 4, 6):", size=9, weight=700, fill="#0F172A")
    f.text(625, 338, "q = clamp(round(x/s) + z; 0, 2^b - 1)", size=8.5, weight=700, fill="#1E40AF")
    f.text(625, 354, "x_hat = s * (q - z)", size=8.5, weight=700, fill="#166534")
    f.text(622, 372, "• Zero padding và ReLU không sinh sai số", size=8.5, fill="#0F172A")
    f.text(622, 386, "khi z là số nguyên chính xác [T2 Nagel].", size=8.5, fill="#475569")

    # 4. Hộp ghi chú tổng kết đánh đổi
    rect(f, 30, 338, 560, 76, fill="#F8FAFC", stroke="#64748B", sw=1.1, rx=4)
    f.text(42, 356, "Đánh đổi cốt lõi giữa Clipping Error và Rounding Error (Nagel 2021 tr.4):", size=9.8, weight=700, fill="#0F172A")
    f.text(42, 373, "• Mở rộng [α, β]: Giảm thiểu sai số kẹp biên (clipping) nhưng tăng bước nhảy s → tăng nhiễu làm tròn.", size=8.8, fill="#334155")
    f.text(42, 389, "• Thu hẹp [α, β]: Giảm bước nhảy s (lượng tử mịn hơn) nhưng làm cắt cụt các giá trị ngoại lai (outliers).", size=8.8, fill="#334155")

    y_src = 424
    source(f, y_src, "[T2 Nagel 2021 tr.4, tr.8] [T2 Gholami 2021 tr.5]")
    f.h = y_src + 22
    return f


# ==============================================================================
# 2. HINH QAT VA STE (qnt-02-qat-ste-backward)
# ==============================================================================
def fig_qat_ste_backward():
    H = 470
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Huấn luyện nhận thức lượng tử (QAT) và Ước lượng Gradient STE (Nagel / Gholami)", size=13.5, weight=700, fill=DARK)

    # 1. Lan truyền thuận (Forward Pass with FakeQuant) - Bên trên
    rect(f, 20, 50, 480, 148, fill="#F8FAFC", stroke="#64748B", sw=1.3, rx=5)
    rect(f, 20, 50, 480, 32, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=5)
    f.text(32, 71, "1. Lan truyền thuận: Mô phỏng lượng tử hóa (FakeQuant / Simulated Quant)", size=10, weight=700, fill="#1E40AF")

    # Input x (FP32)
    rect(f, 40, 95, 75, 42, fill="#FFFFFF", stroke="#2563EB", sw=1.1)
    f.text(77, 113, "Trọng số W", size=9.5, weight=700, fill="#1E40AF", anchor="middle")
    f.text(77, 126, "FP32 liên tục", size=8.5, fill="#475569", anchor="middle")

    # Khối FakeQuant
    rect(f, 155, 90, 175, 52, fill="#FFFFFF", stroke="#D97706", sw=1.2, rx=4)
    f.text(242, 108, "Khối FakeQuant (Simulated)", size=10, weight=700, fill="#92400E", anchor="middle")
    f.text(242, 122, "clamp(x, α, β) → round(x/s)", size=8.2, fill="#78350F", anchor="middle")
    f.text(242, 134, "→ dequantize = s × (q - z)", size=8.2, fill="#78350F", anchor="middle")

    # Output W_hat (FP32 nhưng rời rạc)
    rect(f, 370, 95, 105, 42, fill="#FFFFFF", stroke="#16A34A", sw=1.1)
    f.text(422, 113, "W_hat (FakeQuant)", size=9.5, weight=700, fill="#166534", anchor="middle")
    f.text(422, 126, "Giá trị rời rạc (FP32)", size=8.5, fill="#166534", anchor="middle")

    # Mũi tên forward (thẳng ngang 100%)
    arrow(f, 115, 116, 155, 116, BLUE, THICK)
    arrow(f, 330, 116, 370, 116, GREEN, THICK)

    f.text(35, 160, "• Thực thi bằng phép toán float nhưng ép giá trị rơi đúng vào các mức rời rạc.", size=8.8, fill="#334155")
    f.text(35, 175, "• Giúp đồ thị học cách thích ứng với nhiễu lượng tử ngay trong quá trình hội tụ.", size=8.8, fill="#334155")

    # 2. Lan truyền ngược (Backward Pass with STE) - Bên dưới
    rect(f, 20, 210, 480, 142, fill="#F8FAFC", stroke="#64748B", sw=1.3, rx=5)
    rect(f, 20, 210, 480, 32, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=5)
    f.text(32, 231, "2. Lan truyền ngược: Ước lượng Gradient STE (Straight-Through Estimator)", size=10, weight=700, fill="#0F172A")

    # Gradient từ Loss dL/dW_hat
    rect(f, 370, 255, 105, 42, fill="#FFFFFF", stroke="#64748B", sw=1.1)
    f.text(422, 273, "dL / dW_hat", size=9.5, weight=700, fill="#0F172A", anchor="middle")
    f.text(422, 286, "Gradient từ Loss", size=8.5, fill="#475569", anchor="middle")

    # Khối STE
    rect(f, 155, 250, 175, 52, fill="#FFFFFF", stroke="#DC2626", sw=1.2, rx=4)
    f.text(242, 268, "Ước lượng STE", size=10, weight=700, fill="#B91C1C", anchor="middle")
    f.text(242, 282, "dW_hat / dW ≈ 1 nếu α ≤ W ≤ β", size=8.2, fill="#B91C1C", anchor="middle")
    f.text(242, 294, "dW_hat / dW = 0 nếu W < α hoặc W > β", size=8.2, fill="#7F1D1D", anchor="middle")

    # Cập nhật trọng số FP32
    rect(f, 40, 255, 75, 42, fill="#FFFFFF", stroke="#2563EB", sw=1.1)
    f.text(77, 273, "Cập nhật W", size=9.5, weight=700, fill="#1E40AF", anchor="middle")
    f.text(77, 286, "W - η × dL/dW", size=8.5, fill="#475569", anchor="middle")

    # Mũi tên backward (từ phải sang trái, thẳng ngang 100%)
    arrow(f, 370, 276, 330, 276, RED, THICK)
    arrow(f, 155, 276, 115, 276, RED, THICK)

    f.text(35, 323, "• Phép làm tròn round(x) có đạo hàm bằng 0 khắp nơi, khiến SGD bị tê liệt.", size=8.8, fill="#334155")
    f.text(35, 338, "• STE bỏ qua làm tròn, truyền thẳng gradient 100% qua bộ lượng tử hóa [T2 Nagel].", size=8.8, fill="#334155")

    # 3. Đồ thị trực quan: Hàm bậc thang FakeQuant vs Đạo hàm STE (Bên phải)
    rect(f, 520, 50, 340, 335, fill="#F8FAFC", stroke="#64748B", sw=1.2, rx=5)
    rect(f, 520, 50, 340, 32, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=5)
    f.text(690, 71, "Đồ thị: Phép làm tròn bậc thang vs Đạo hàm STE", size=10, weight=700, fill="#0F172A", anchor="middle")

    # Đồ thị 1: FakeQuant(x) bậc thang
    f.text(535, 98, "(a) Hàm chuyển đổi FakeQuant(x): Bậc thang rời rạc", size=9, weight=700, fill="#0F172A")
    rect(f, 550, 106, 280, 106, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0)
    # Trục tọa độ X và Y
    f.line([(565, 196), (815, 196)], "#64748B", width=THIN, head=True)
    f.line([(575, 202), (575, 114)], "#64748B", width=THIN, head=True)
    f.text(810, 204, "x", size=8, fill="#64748B")
    f.text(568, 120, "y", size=8, fill="#64748B")

    # Đường lý tưởng y = x (dashed)
    f.line([(585, 190), (800, 122)], "#94A3B8", width=THIN, dashed=True)
    f.text(782, 112, "y = x (lý tưởng)", size=7.8, fill="#64748B", anchor="end")

    # Bậc thang lượng tử hóa (cạnh ngang giao qua đường lý tưởng)
    steps = [
        (585, 185), (635, 185),
        (635, 162), (695, 162),
        (695, 140), (755, 140),
        (755, 120), (800, 120),
    ]
    for i in range(len(steps) - 1):
        f.line([steps[i], steps[i + 1]], "#2563EB", width=THICK)
    f.text(585, 136, "Đạo hàm thật = 0", size=7.8, fill="#B91C1C")
    f.text(585, 148, "tại mặt phẳng", size=7.8, fill="#B91C1C")

    # Đồ thị 2: Đạo hàm STE d(y)/dx
    f.text(535, 226, "(b) Xấp xỉ đạo hàm STE: Hàm chữ nhật (Boxcar)", size=9, weight=700, fill="#0F172A")
    rect(f, 550, 234, 280, 100, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0)
    # Trục zero
    f.line([(565, 310), (815, 310)], "#64748B", width=THIN, head=True)
    f.text(570, 305, "0", size=8, fill="#64748B")

    # Đạo hàm STE = 1 trong khoảng [alpha, beta]
    # Dưới alpha: 0
    f.line([(565, 310), (620, 310)], "#DC2626", width=THICK, head=False)
    f.line([(620, 310), (620, 256)], "#DC2626", width=THIN, dashed=True, head=False)
    # Trong [alpha, beta]: 1
    f.line([(620, 256), (750, 256)], "#DC2626", width=THICK, head=False)
    f.text(685, 248, "d(y)/dx = 1.0 (STE)", size=8.5, weight=700, fill="#B91C1C", anchor="middle")
    f.line([(750, 256), (750, 310)], "#DC2626", width=THIN, dashed=True, head=False)
    # Trên beta: 0
    f.line([(750, 310), (815, 310)], "#DC2626", width=THICK, head=False)

    f.text(620, 322, "α (q_min)", size=8, fill="#0F172A", anchor="middle")
    f.text(750, 322, "β (q_max)", size=8, fill="#0F172A", anchor="middle")
    f.text(685, 324, "Vùng gradient truyền thẳng", size=8, fill="#166534", anchor="middle")

    f.text(535, 350, "• Ngoài [α, β]: gradient = 0 triệt tiêu các trọng số trôi quá xa.", size=8.2, fill="#475569")
    f.text(535, 365, "• Trong [α, β]: gradient giữ nguyên cho phép cập nhật FP32.", size=8.2, fill="#475569")

    # 4. Hộp kết luận
    rect(f, 20, 385, 840, 50, fill="#F8FAFC", stroke="#64748B", sw=1.1, rx=4)
    f.text(32, 403, "Ý nghĩa thực tiễn của QAT (Nagel 2021 tr.19, Gholami 2021 tr.9):", size=10, weight=700, fill="#0F172A")
    f.text(32, 419, "QAT giải quyết tình trạng sụt giảm độ chính xác ở các lớp cực kỳ nhạy cảm (như 4-bit hoặc activation hẹp) mà PTQ không khắc phục được.", size=8.8, fill="#334155")

    y_src = 445
    source(f, y_src, "[T2 Nagel 2021 tr.6, tr.19] [T2 Gholami 2021 tr.9]")
    f.h = y_src + 22
    return f


# ==============================================================================
# HAM RUN
# ==============================================================================
if __name__ == "__main__":
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("qnt-01-affine-mapping", fig_affine_mapping),
        ("qnt-02-qat-ste-backward", fig_qat_ste_backward),
    ]
    run(figures, DEFAULT_OUTDIR)
