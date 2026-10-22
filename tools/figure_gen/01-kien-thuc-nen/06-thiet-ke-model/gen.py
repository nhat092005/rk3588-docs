#!/usr/bin/env python3
"""Chuyên đề: Thiết kế mô hình thân thiện NPU (06-thiet-ke-model).

Sinh các hình vector SVG minh họa:
  1. rep-01-repvgg-fusion-flow:
     Quy trình tái tham số hóa cấu trúc RepVGG:
     Huấn luyện đa nhánh (3x3+BN, 1x1+BN, Identity+BN) -> 4 bước biến đổi đại số -> Suy luận đơn nhánh Conv 3x3 duy nhất.

Chạy: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# docs/tools/figure_gen/01-kien-thuc-nen/06-thiet-ke-model -> ../.. = docs/tools/figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "06-thiet-ke-model"
    )
)

W = 880
BOX_STROKE = "#333333"


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
# 1. HÌNH TÁI THAM SỐ HÓA REPVGG (rep-01-repvgg-fusion-flow)
# ==============================================================================
def draw_kernel_3x3(f, x, y, center_fill, center_text, border_text="0", cell=13):
    """Vẽ ma trận kernel 3x3 minh họa trực quan offline fusion"""
    for r in range(3):
        for c in range(3):
            is_center = (r == 1 and c == 1)
            fill = center_fill if is_center else "#F8FAFC"
            stroke = "#64748B" if is_center else "#CBD5E1"
            txt = center_text if is_center else border_text
            tcolor = "#0F172A" if is_center else "#64748B"
            rect(f, x + c * cell, y + r * cell, cell, cell, fill=fill, stroke=stroke, sw=0.8)
            f.text(x + c * cell + cell / 2, y + r * cell + cell / 2, txt, size=6.8, weight=700 if is_center else 400, fill=tcolor, anchor="middle")


def fig_repvgg_fusion_flow():
    H = 460
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Quy trình tái tham số hóa RepVGG: Huấn luyện đa nhánh → Suy luận đơn nhánh (Ding 2021)", size=13.5, weight=700, fill=DARK)

    # 1. Cột trái: Khối đa nhánh khi Huấn luyện (Training Topology)
    w1 = 214
    cx1 = 20
    mid1 = cx1 + w1 // 2  # 127
    rect(f, cx1, 52, w1, 314, fill="#F8FAFC", stroke="#64748B", sw=1.3, rx=5)
    rect(f, cx1, 52, w1, 32, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=5)
    f.text(mid1, 72, "1. Khi Huấn luyện (Multi-Branch)", size=10.5, weight=700, fill="#0F172A", anchor="middle")

    # Input tensor
    rect(f, 34, 90, 186, 24, fill="#FFFFFF", stroke="#2563EB", sw=1.1)
    f.text(mid1, 102, "Tensor đầu vào M^(1)", size=9, weight=700, fill="#1E40AF", anchor="middle")

    # 3 nhánh song song:
    # Nhánh 1: Conv 3x3 + BN
    rect(f, 62, 126, 126, 28, fill="#FFFFFF", stroke="#D97706", sw=1.1)
    f.text(125, 137, "Conv 3×3 + BN", size=8.5, weight=700, fill="#92400E", anchor="middle")
    f.text(125, 147, "Trích đặc trưng sâu", size=7.2, fill="#475569", anchor="middle")

    # Nhánh 2: Conv 1x1 + BN
    rect(f, 62, 162, 126, 28, fill="#FFFFFF", stroke="#2563EB", sw=1.1)
    f.text(125, 173, "Conv 1×1 + BN", size=8.5, weight=700, fill="#1E40AF", anchor="middle")
    f.text(125, 183, "Tương quan kênh", size=7.2, fill="#475569", anchor="middle")

    # Nhánh 3: Identity + BN
    rect(f, 62, 198, 126, 28, fill="#FFFFFF", stroke="#64748B", sw=1.1)
    f.text(125, 209, "Identity + BN", size=8.5, weight=700, fill="#334155", anchor="middle")
    f.text(125, 219, "Đường tắt gradient", size=7.2, fill="#475569", anchor="middle")

    # Đường dẫn Manhattan phân phối từ Input vào 3 nhánh (Bên trái: bus tại x=38)
    f.line([(mid1, 114), (mid1, 120), (38, 120), (38, 212)], BLUE, width=THICK, head=False)
    arrow(f, 38, 140, 60, 140, BLUE, THICK)
    arrow(f, 38, 176, 60, 176, BLUE, THICK)
    arrow(f, 38, 212, 60, 212, BLUE, THICK)

    # Nút cộng dạng khối hợp nhất rõ ràng (Element-wise Addition Block)
    rect(f, 34, 250, 186, 26, fill="#FEF3C7", stroke="#D97706", sw=1.2, rx=3)
    f.text(mid1, 263, "Bộ cộng phần tử (+ Element-wise Add)", size=8.8, weight=700, fill="#92400E", anchor="middle")

    # 3 đường dẫn riêng biệt từ cả 3 nhánh cắm thẳng đứng vào Bộ cộng
    # Nhánh 1 (Conv 3x3) đi vòng xa bên phải tại x=206 cắm xuống Bộ cộng tại y=248
    f.line([(188, 140), (206, 140), (206, 248)], INK, width=THIN, head=True)
    # Nhánh 2 (Conv 1x1) đi vòng gần bên phải tại x=194 cắm xuống Bộ cộng tại y=248
    f.line([(188, 176), (194, 176), (194, 248)], INK, width=THIN, head=True)
    # Nhánh 3 (Identity) cắm thẳng từ đáy xuống tâm x=mid1=127
    arrow(f, mid1, 228, mid1, 248, INK, THIN)

    # Từ Bộ cộng xuống Output M^(2)
    arrow(f, mid1, 278, mid1, 296, INK, THIN)

    # Output M^(2)
    rect(f, 34, 298, 186, 26, fill="#FFFFFF", stroke="#2563EB", sw=1.1)
    f.text(mid1, 311, "Đầu ra M^(2) (trước ReLU)", size=9, weight=700, fill="#1E40AF", anchor="middle")

    f.text(26, 335, "• Nhiều nhánh giúp gradient hội tụ tốt.", size=8, fill="#334155")
    f.text(26, 348, "• Tốn thêm SRAM để giữ bản sao M^(1).", size=8, fill="#B91C1C")
    f.text(26, 360, "• Phân mảnh toán tử trên NPU [T2 REPVGG].", size=8, fill="#475569")

    # 2. Cột giữa: 4 Bước biến đổi đại số tương đương (Algebraic Fusion)
    w2 = 368
    x2 = 258
    rect(f, x2, 52, w2, 314, fill="#F8FAFC", stroke="#64748B", sw=1.3, rx=5)
    rect(f, x2, 52, w2, 32, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=5)
    f.text(x2 + w2 // 2, 72, "2. Bốn bước biến đổi toán học offline (Ding 2021)", size=10.5, weight=700, fill="#0F172A", anchor="middle")

    # Bước 1: Gộp BN vào Conv
    rect(f, x2 + 12, 92, w2 - 24, 46, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=3)
    f.text(x2 + 20, 107, "Bước 1: Gộp BN vào từng nhánh Conv & Identity", size=9, weight=700, fill="#1E40AF")
    f.text(x2 + 20, 123, "W' = (γ / σ) × W,   b' = β - (μ × γ / σ)  [T2 REPVGG Eq. 3]", size=8.5, fill="#334155")

    # Bước 2: Đệm 0 kernel 1x1 về 3x3 (có ma trận minh họa)
    rect(f, x2 + 12, 144, w2 - 24, 46, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=3)
    f.text(x2 + 20, 159, "Bước 2: Đệm không (Zero-pad) kernel 1×1 thành 3×3", size=9, weight=700, fill="#0F172A")
    f.text(x2 + 20, 175, "pad(W'_1x1): Đặt 1×1 vào tâm ma trận 3×3", size=8.3, fill="#334155")
    draw_kernel_3x3(f, x2 + w2 - 56, 149, "#DBEAFE", "w'")

    # Bước 3: Chuyển Identity thành kernel 3x3 (có ma trận minh họa)
    rect(f, x2 + 12, 196, w2 - 24, 46, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=3)
    f.text(x2 + 20, 211, "Bước 3: Chuyển nhánh Identity thành kernel 3×3 đơn vị", size=9, weight=700, fill="#0F172A")
    f.text(x2 + 20, 227, "pad(W'_id): Tâm = γ_0/σ_0 (nếu i==j), biên = 0", size=8.3, fill="#334155")
    draw_kernel_3x3(f, x2 + w2 - 56, 201, "#FEF3C7", "1")

    # Bước 4: Cộng dồn trọng số và bias
    rect(f, x2 + 12, 248, w2 - 24, 54, fill="#FFFFFF", stroke="#D97706", sw=1.2, rx=3)
    f.text(x2 + 20, 264, "Bước 4: Cộng đại số toàn bộ trọng số và vector bias", size=9, weight=700, fill="#92400E")
    f.text(x2 + 20, 279, "W_final = W'_3x3 + pad(W'_1x1) + pad(W'_id)", size=8.5, weight=700, fill="#92400E")
    f.text(x2 + 20, 293, "b_final = b'_3x3 + b'_1x1 + b'_id  (Biến đổi tuyến tính)", size=8, fill="#334155")
    draw_kernel_3x3(f, x2 + w2 - 56, 255, "#DCFCE7", "w", border_text="w")

    f.text(x2 + 20, 318, "• Tương đương toán học 100% với mạng gốc [T2 REPVGG tr.5].", size=8.5, fill="#166534")
    f.text(x2 + 20, 332, "• Quá trình hợp nhất diễn ra hoàn toàn offline trước khi nạp.", size=8.5, fill="#334155")
    f.text(x2 + 20, 346, "• Triệt tiêu hoàn toàn toán tử Add (+) trong runtime NPU.", size=8.5, fill="#475569")

    # 3. Cột phải: Suy luận đơn nhánh (Inference Plain Topology)
    w3 = 214
    x3 = 648
    mid3 = x3 + w3 // 2  # 755
    rect(f, x3, 52, w3, 314, fill="#F8FAFC", stroke="#16A34A", sw=1.3, rx=5)
    rect(f, x3, 52, w3, 32, fill="#FFFFFF", stroke="#16A34A", sw=1.0, rx=5)
    f.text(mid3, 72, "3. Khi Suy luận (Single Conv)", size=10.5, weight=700, fill="#166534", anchor="middle")

    # Input tensor
    rect(f, x3 + 20, 92, 174, 26, fill="#FFFFFF", stroke="#16A34A", sw=1.1)
    f.text(mid3, 108, "Tensor đầu vào M^(1)", size=9, weight=700, fill="#166534", anchor="middle")

    arrow(f, mid3, 118, mid3, 148, GREEN, THICK)

    # Khối Conv 3x3 duy nhất đã gộp
    rect(f, x3 + 18, 148, 178, 76, fill="#F0FDF4", stroke="#16A34A", sw=1.3, rx=5)
    f.text(mid3, 170, "DUY NHẤT CONV 3×3", size=10, weight=700, fill="#166534", anchor="middle")
    f.text(mid3, 186, "W_final (kernel 3×3)", size=8.5, fill="#166534", anchor="middle")
    f.text(mid3, 200, "+ b_final (bias 1D)", size=8.5, fill="#166534", anchor="middle")
    f.text(mid3, 214, "+ Hàm kích hoạt ReLU", size=8.5, fill="#166534", anchor="middle")

    arrow(f, mid3, 224, mid3, 254, GREEN, THICK)

    # Output tensor
    rect(f, x3 + 20, 254, 174, 26, fill="#FFFFFF", stroke="#16A34A", sw=1.1)
    f.text(mid3, 270, "Tensor đầu ra M^(2)", size=9, weight=700, fill="#166534", anchor="middle")

    f.text(x3 + 14, 302, "+ Tối ưu bộ nhớ SRAM:", size=9, weight=700, fill="#166534")
    f.text(x3 + 14, 317, "  Giải phóng ngay M^(1) khi tính xong.", size=8.5, fill="#334155")
    f.text(x3 + 14, 332, "+ Tăng tốc thông lượng phần cứng:", size=9, weight=700, fill="#166534")
    f.text(x3 + 14, 347, "  Không overhead khởi động kernel [T2].", size=8.5, fill="#334155")

    # Mũi tên liên kết chuyển đổi giữa 3 cột
    arrow(f, 234, 204, 258, 204, INK, THICK)
    arrow(f, 626, 204, 648, 204, GREEN, THICK)

    # 4. Hộp kết luận dưới cùng
    rect(f, 20, 380, 840, 48, fill="#F8FAFC", stroke="#64748B", sw=1.1, rx=4)
    f.text(32, 398, "Ý nghĩa then chốt trên NPU vi xử lý biên (Rockchip RK3588):", size=10, weight=700, fill="#0F172A")
    f.text(32, 414, "NPU hoạt động hiệu quả nhất với các lớp Conv 3×3 tuần tự dày đặc. Tái tham số hóa RepVGG loại bỏ hoàn toàn các toán tử Add và BN rời rạc, tối đa hóa tỷ lệ lấp đầy mảng PE MAC [T2 REPVGG tr.2, Chu 2024 QARepVGG tr.1].", size=8.8, fill="#334155")

    y_src = 438
    source(f, y_src, "[T2 Ding et al. RepVGG 2021 tr.2, tr.5] [T2 Chu et al. QARepVGG 2024 tr.1, tr.5]")
    f.h = y_src + 22
    return f


# ==============================================================================
# HÀM RUN
# ==============================================================================
if __name__ == "__main__":
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("rep-01-repvgg-fusion-flow", fig_repvgg_fusion_flow),
    ]
    run(figures, DEFAULT_OUTDIR)
