#!/usr/bin/env python3
"""Chuyen de: Kien truc NPU va Dataflow (02-npu).

Sinh cac hinh vector SVG minh hoa:
  1. npu-01-pe-mac-structure:
     Vi kien truc cua mot Processing Element (PE) / MAC Unit: duong du lieu ALU,
     thanh ghi trong so/kich hoat, bo tich luy 32-bit va duong truyen systolic.
  2. npu-02-dataflow-comparison:
     So sanh co che luan chuyen du lieu: Weight Stationary (WS), Output Stationary (OS),
     va Row Stationary (RS - Eyeriss).

Chay: python3 gen.py [outdir] [--png] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# docs/tools/figure_gen/01-kien-thuc-nen/02-npu -> ../.. = docs/tools/figure_gen
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

DEFAULT_OUTDIR = os.path.abspath(
    os.path.join(
        HERE, "..", "..", "..", "..", "_assets", "generated", "01-kien-thuc-nen", "02-npu"
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
# 1. HINH VI KIEN TRUC PROCESSING ELEMENT (npu-01-pe-mac-structure)
# ==============================================================================
def fig_pe_mac_structure():
    H = 495
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "Vi kiến trúc một Processing Element (PE) và đường dữ liệu MAC (TPU / Eyeriss)", size=12.5, weight=700, fill=DARK)

    # 1. Khối nguồn dữ liệu vào (Bên trái & Phía trên)
    # Kích hoạt vào (x=20..155, y=120..164, center y=142)
    rect(f, 20, 120, 135, 44, fill="#F0F7FF", stroke=BLUE, sw=1.2)
    f.text(87, 136, "Kích hoạt vào x_i", size=10.5, weight=700, fill="#1E40AF", anchor="middle")
    f.text(87, 152, "INT8 / FP16 (từ SRAM)", size=9, fill="#334155", anchor="middle")

    # Trọng số vào (x=20..155, y=198..242, center y=220)
    rect(f, 20, 198, 135, 44, fill="#FFFBEB", stroke="#D97706", sw=1.2)
    f.text(87, 214, "Trọng số vào w_i", size=10.5, weight=700, fill="#92400E", anchor="middle")
    f.text(87, 230, "INT8 / FP16 (DRAM/SRAM)", size=9, fill="#334155", anchor="middle")

    # Partial sum từ hàng trên (Systolic input dọc, center x=535, y=18..58)
    rect(f, 465, 18, 140, 40, fill="#F0FDF4", stroke=GREEN, sw=1.2)
    f.text(535, 33, "Psum vào (từ PE trên)", size=10, weight=700, fill=GREEN, anchor="middle")
    f.text(535, 47, "32-bit INT32 / FP32", size=8.5, fill="#334155", anchor="middle")

    # 2. Khung bao toàn bộ PE (gọn gàng, thoáng đãng)
    pe_x, pe_y, pe_w, pe_h = 175, 68, 535, 236
    rect(f, pe_x, pe_y, pe_w, pe_h, fill="#F8FAFC", stroke="#475569", sw=1.5, rx=6)
    f.text(pe_x + 14, pe_y + 15, "PROCESSING ELEMENT (PE)", size=10.5, weight=700, fill="#0F172A")
    f.text(pe_x + 14, pe_y + 27, "RF nội bộ + Datapath ALU", size=8, fill="#475569")

    # Các thanh ghi đệm cục bộ trong PE
    # Activation Latch (x=195..305, y=120..164, center y=142)
    rect(f, 195, 120, 110, 44, fill="#FFFFFF", stroke=BLUE, sw=1.1)
    f.text(250, 137, "Activation Latch", size=10, weight=700, fill="#1E40AF", anchor="middle")
    f.text(250, 152, "Thanh ghi 8-bit", size=8.5, fill="#334155", anchor="middle")

    # Weight Register File (RF) (x=195..305, y=198..242, center y=220)
    rect(f, 195, 198, 110, 44, fill="#FFFFFF", stroke="#D97706", sw=1.1)
    f.text(250, 215, "Weight RF", size=10, weight=700, fill="#92400E", anchor="middle")
    f.text(250, 230, "< 1 kB SRAM nội", size=8.5, fill="#334155", anchor="middle")

    # Bộ nhân (*) (center x=390, center y=205, y=180..230)
    rect(f, 345, 180, 90, 50, fill="#FFFFFF", stroke="#334155", sw=1.3, rx=4)
    f.text(390, 199, "Bộ nhân (*)", size=10.5, weight=700, fill="#0F172A", anchor="middle")
    f.text(390, 215, "8b × 8b → 16b", size=8.5, fill="#475569", anchor="middle")

    # MUX lựa chọn Psum (center x=535, y=130..156)
    rect(f, 510, 130, 50, 26, fill="#FFFFFF", stroke="#475569", sw=1.1)
    f.text(535, 143, "MUX", size=9, weight=700, fill="#0F172A", anchor="middle")

    # Bộ cộng (+) ALU 32-bit (center x=535, center y=205, y=180..230)
    rect(f, 490, 180, 90, 50, fill="#FFFFFF", stroke="#334155", sw=1.3, rx=4)
    f.text(535, 199, "Bộ cộng (+)", size=10.5, weight=700, fill="#0F172A", anchor="middle")
    f.text(535, 215, "ALU 32-bit", size=8.5, fill="#475569", anchor="middle")

    # Thanh ghi Psum (center x=535, y=248..286)
    rect(f, 480, 248, 110, 38, fill="#FFFFFF", stroke=GREEN, sw=1.1)
    f.text(535, 262, "Thanh ghi Psum", size=10, weight=700, fill=GREEN, anchor="middle")
    f.text(535, 275, "Tích lũy 32-bit", size=8.2, fill="#334155", anchor="middle")

    # ---------------------------------------------------------
    # ĐƯỜNG KẾT NỐI ORTHOGONAL & SYSTOLIC ROUTING
    # ---------------------------------------------------------
    # 1. Từ bên ngoài vào Latch (thẳng ngang tại y=142)
    arrow(f, 155, 142, 195, 142, BLUE, THICK)

    # 2. Từ bên ngoài vào RF (thẳng ngang tại y=220)
    arrow(f, 155, 220, 195, 220, INK, THICK)

    # 3. Từ Latch vào Bộ nhân
    f.line([(305, 142), (325, 142), (325, 195), (345, 195)], BLUE, width=THICK, head=True)

    # 4. Từ RF vào Bộ nhân
    arrow(f, 305, 220, 345, 220, INK, THICK)

    # 5. Từ Bộ nhân sang Bộ cộng (thẳng ngang tại y=205)
    arrow(f, 435, 205, 490, 205, INK, THICK)
    f.text(462, 195, "16-bit", size=8.5, fill="#334155", anchor="middle")

    # 6. Systolic Forwarding x_i (truyền ngang sang PE kế tiếp tại y=104, có cầu nhảy tại x=535)
    mk_blue = f.marker(BLUE, THICK)
    f.line([(305, 134), (320, 134), (320, 104), (527, 104)], BLUE, width=THICK, head=False)
    f.a(f'<path d="M 527 104 A 8 8 0 0 1 543 104 L 724 104" fill="none" stroke="{BLUE}" stroke-width="{THICK}" marker-end="url(#{mk_blue})"/>')
    f.text(420, 94, "Systolic Forwarding x_i (truyền ngang sang PE kế)", size=8.5, fill="#1E40AF", anchor="middle")

    # Khối tiếp nhận PE bên phải
    rect(f, 730, 84, 130, 42, fill="#F0F7FF", stroke=BLUE, sw=1.1)
    f.text(795, 99, "Tới PE(r, c+1)", size=10, weight=700, fill="#1E40AF", anchor="middle")
    f.text(795, 113, "Nhận tiếp x_i", size=8.5, fill="#334155", anchor="middle")

    # 7. Luồng Psum dọc: Từ trên vào MUX (tai x=535)
    arrow(f, 535, 58, 535, 130, GREEN, THICK)

    # 8. Từ MUX xuống Bộ cộng (thẳng dọc tại x=535)
    arrow(f, 535, 156, 535, 180, INK, THICK)

    # 9. Vòng phản hồi Loop OS: Từ Thanh ghi Psum quay lại MUX
    f.line([(590, 267), (618, 267), (618, 143), (560, 143)], GREEN, width=THICK, head=True)
    f.text(626, 205, "Loop OS", size=8.5, weight=700, fill=GREEN)

    # 10. Từ Bộ cộng xuống Thanh ghi Psum (thẳng dọc tại x=535)
    arrow(f, 535, 230, 535, 248, GREEN, THIN)

    # 11. Systolic Psum forward xuống PE hàng dưới
    arrow(f, 535, 286, 535, 324, GREEN, THICK)
    rect(f, 465, 324, 140, 40, fill="#F0FDF4", stroke=GREEN, sw=1.1)
    f.text(535, 339, "Tới PE(r+1, c)", size=10, weight=700, fill=GREEN, anchor="middle")
    f.text(535, 353, "Cộng dồn dọc Psum", size=8.5, fill="#334155", anchor="middle")

    # 3. Hai thẻ đối chiếu kiến trúc và năng lượng cân đối ở phía dưới
    card_y = 380
    card_h = 78
    # Thẻ 1: Đặc tính vi kiến trúc & Năng lượng
    rect(f, 20, card_y, 415, card_h, fill="#F8FAFC", stroke="#64748B", sw=1.1, rx=4)
    f.text(32, card_y + 16, "Đặc tính vi kiến trúc & Năng lượng (Chen 2016, Jouppi 2017):", size=9.5, weight=700, fill="#0F172A")
    f.text(32, card_y + 34, "• Kiểu số: Nhân 8-bit integer tốn ít năng lượng & diện tích hơn 6× FP16 [T2 Jouppi tr.1].", size=8.5, fill="#334155")
    f.text(32, card_y + 49, "• Bộ nhớ cục bộ: Register File (RF) < 1 kB tiết kiệm năng lượng ~200× DRAM [T2 Chen tr.8].", size=8.5, fill="#334155")
    f.text(32, card_y + 64, "• Xử lý cục bộ: Giảm thiểu truy cập ngoài chip bằng cách tái sử dụng dữ liệu tại PE.", size=8.5, fill="#334155")

    # Thẻ 2: Cơ chế luân chuyển dữ liệu (Dataflow)
    rect(f, 445, card_y, 415, card_h, fill="#F8FAFC", stroke="#64748B", sw=1.1, rx=4)
    f.text(457, card_y + 16, "Cơ chế luân chuyển dữ liệu trong mảng PE (Dataflow):", size=9.5, weight=700, fill="#0F172A")
    f.text(457, card_y + 34, "• Weight Stationary (WS): W cố định trong RF, x_i truyền ngang, Psum cộng dồn dọc.", size=8.5, fill="#334155")
    f.text(457, card_y + 49, "• Output Stationary (OS): Psum tích lũy cục bộ trong thanh ghi qua Loop OS.", size=8.5, fill="#334155")
    f.text(457, card_y + 64, "• Systolic Array: Các PE chuyển tiếp trực tiếp cho nhau, tiết kiệm băng thông bus.", size=8.5, fill="#334155")

    y_src = 454
    source(f, y_src, "[T2 Chen 2016 tr.2, tr.8] [T2 Jouppi 2017 tr.1, tr.3]")
    return f


# ==============================================================================
# 2. HINH SO SANH DATAFLOW (npu-02-dataflow-comparison)
# ==============================================================================
def fig_dataflow_comparison():
    H = 430
    f = Fig(W, H)
    tier(f, "T2 chung")
    f.text(14, 20, "So sánh cơ chế luân chuyển dữ liệu: Weight Stationary, Output Stationary và Row Stationary", size=13.5, weight=700, fill=DARK)

    # 3 Cột: WS, OS, RS
    col_w = 268
    col_h = 338
    gap = 18
    x0 = 20

    configs = [
        ("Weight Stationary (WS)", "W cố định RF | Act ngang | Psum dọc", "#2563EB", 0),
        ("Output Stationary (OS)", "Psum cố định RF | Act ngang | W dọc", "#7C3AED", 1),
        ("Row Stationary (RS)", "1D Conv RF | Tối ưu 3 kiểu tái sử dụng", "#059669", 2),
    ]

    for title, subtitle, accent_color, idx in configs:
        cx = x0 + idx * (col_w + gap)
        # Khung cột chính
        rect(f, cx, 52, col_w, col_h, fill="#F8FAFC", stroke="#64748B", sw=1.2, rx=5)
        # Header strip cao 42px chứa cả Title và Subtitle gọn gàng, không đè lên lưới PE
        rect(f, cx, 52, col_w, 42, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=5)
        rect(f, cx + 10, 59, 8, 28, fill=accent_color, stroke=accent_color, sw=1, rx=2)
        f.text(cx + 26, 70, title, size=11, weight=700, fill="#0F172A")
        f.text(cx + 26, 85, subtitle, size=8.2, fill="#475569")

        # Sơ đồ mảng PE 2x2 (w=236, h=146) từ y=102 đến y=248
        rect(f, cx + 16, 102, 236, 146, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0)

        # 4 PE: hàng 0 tại y=118 (h=32), hàng 1 tại y=174 (h=32)
        for r in range(2):
            for c in range(2):
                px = cx + 36 + c * 92
                py = 118 + r * 56
                rect(f, px, py, 64, 32, fill="#F8FAFC", stroke="#475569", sw=1.0)
                if idx == 0:
                    f.text(px + 32, py + 14, f"W_{r}{c} giữ", size=8.5, weight=700, fill="#0F172A", anchor="middle")
                    f.text(px + 32, py + 25, "trong RF", size=7.8, fill="#475569", anchor="middle")
                elif idx == 1:
                    f.text(px + 32, py + 14, f"Y_{r}{c} giữ", size=8.5, weight=700, fill="#0F172A", anchor="middle")
                    f.text(px + 32, py + 25, "tích lũy", size=7.8, fill="#475569", anchor="middle")
                else:
                    f.text(px + 32, py + 14, f"1D-Conv", size=8.5, weight=700, fill="#0F172A", anchor="middle")
                    f.text(px + 32, py + 25, f"R{r}, C{c}", size=7.8, fill="#475569", anchor="middle")

        # Luồng dữ liệu cho cả 2 hàng: Activation đi ngang ở Hàng 0 (y=134) và Hàng 1 (y=190)
        for py in [134, 190]:
            arrow(f, cx + 10, py, cx + 36, py, BLUE, THICK)
            arrow(f, cx + 100, py, cx + 128, py, BLUE, THICK)
            arrow(f, cx + 192, py, cx + 214, py, BLUE, THICK)
            rect(f, cx + 214, py - 9, 32, 18, fill="#F0F7FF", stroke=BLUE, sw=1.0)
            f.text(cx + 230, py + 1, "x_out", size=7.5, fill="#1E40AF", anchor="middle")

        # Luồng dọc ở cả Cột 0 (x = cx + 68) và Cột 1 (x = cx + 160)
        for c, px in enumerate([cx + 68, cx + 160]):
            if idx == 0:
                # WS: Psum cộng dồn dọc xuống dưới
                arrow(f, px, 150, px, 174, GREEN, THICK)
                arrow(f, px, 206, px, 226, GREEN, THICK)
                rect(f, px - 22, 226, 44, 18, fill="#F0FDF4", stroke=GREEN, sw=1.0)
                f.text(px, 237, f"Psum_{c}", size=7.8, fill=GREEN, anchor="middle")
            elif idx == 1:
                # OS: Trọng số W trượt dọc qua các hàng (nhập từ trên xuống, không vướng chữ)
                arrow(f, px, 102, px, 118, "#D97706", THIN)
                arrow(f, px, 150, px, 174, "#D97706", THICK)
                arrow(f, px, 204, px, 226, "#D97706", THICK)
                rect(f, px - 20, 226, 40, 18, fill="#FFFBEB", stroke="#D97706", sw=1.0)
                f.text(px, 237, "w_out", size=7.8, fill="#92400E", anchor="middle")
            else:
                # RS: Psum 1D conv cộng dồn dọc
                arrow(f, px, 150, px, 174, GREEN, THICK)
                arrow(f, px, 206, px, 226, GREEN, THICK)
                rect(f, px - 22, 226, 44, 18, fill="#F0FDF4", stroke=GREEN, sw=1.0)
                f.text(px, 237, f"Psum_{c}", size=7.8, fill=GREEN, anchor="middle")

    # Chú thích chi tiết từng cột (bắt đầu tại y=256)
    # Cột 1: WS
    x1 = x0
    f.text(x1 + 14, 263, "Cơ chế chính:", size=9.5, weight=700, fill="#0F172A")
    f.text(x1 + 14, 278, "• Trọng số W nạp một lần, đứng yên trong RF.", size=8.5, fill="#334155")
    f.text(x1 + 14, 292, "• Kích hoạt x trượt qua các PE cùng hàng.", size=8.5, fill="#334155")
    f.text(x1 + 14, 306, "• Psum truyền dọc tích lũy dần theo cột.", size=8.5, fill="#334155")
    f.text(x1 + 14, 324, "Ưu / Nhược điểm:", size=9.5, weight=700, fill="#0F172A")
    f.text(x1 + 14, 339, "+ Tối đa hóa tái sử dụng (reuse) trọng số W.", size=8.5, fill="#166534")
    f.text(x1 + 14, 353, "- Psum phải di chuyển nhiều, tốn bộ đệm.", size=8.5, fill="#B91C1C")
    f.text(x1 + 14, 367, "• Đại diện: Google TPU, NVDLA.", size=8.5, fill="#475569")
    f.text(x1 + 14, 381, "• Phù hợp lớp có trọng số lớn, batch nhỏ.", size=8.5, fill="#475569")

    # Cột 2: OS
    x2 = x1 + col_w + gap
    f.text(x2 + 14, 263, "Cơ chế chính:", size=9.5, weight=700, fill="#0F172A")
    f.text(x2 + 14, 278, "• Psum của một pixel Y đứng yên trong PE.", size=8.5, fill="#334155")
    f.text(x2 + 14, 292, "• Trọng số và Kích hoạt trượt/broadcast tới.", size=8.5, fill="#334155")
    f.text(x2 + 14, 306, "• Tích lũy xong mới xuất kết quả ra ngoài.", size=8.5, fill="#334155")
    f.text(x2 + 14, 324, "Ưu / Nhược điểm:", size=9.5, weight=700, fill="#0F172A")
    f.text(x2 + 14, 339, "+ Triệt tiêu hoàn toàn việc di chuyển Psum.", size=8.5, fill="#166534")
    f.text(x2 + 14, 353, "- Cần nạp lại Act và W nhiều lần từ buffer.", size=8.5, fill="#B91C1C")
    f.text(x2 + 14, 367, "• Đại diện: ShiDianNao, Layer-Puzzle.", size=8.5, fill="#475569")
    f.text(x2 + 14, 381, "• Phù hợp lớp có ofmap lớn, tích lũy sâu.", size=8.5, fill="#475569")

    # Cột 3: RS
    x3 = x2 + col_w + gap
    f.text(x3 + 14, 263, "Cơ chế chính:", size=9.5, weight=700, fill="#0F172A")
    f.text(x3 + 14, 278, "• Tách conv 2D thành các primitive 1D conv.", size=8.5, fill="#334155")
    f.text(x3 + 14, 292, "• 1 hàng filter & 1 hàng ifmap nằm trong RF.", size=8.5, fill="#334155")
    f.text(x3 + 14, 306, "• RF tận dụng cả 3 kiểu reuse: conv, filter, ifmap.", size=8.5, fill="#334155")
    f.text(x3 + 14, 324, "Ưu / Nhược điểm:", size=9.5, weight=700, fill="#0F172A")
    f.text(x3 + 14, 339, "+ Tiết kiệm 1.4× - 2.5× năng lượng so với WS/OS.", size=8.5, fill="#166534")
    f.text(x3 + 14, 353, "- Phần cứng và bộ lập lịch NoC phức tạp hơn.", size=8.5, fill="#B91C1C")
    f.text(x3 + 14, 367, "• Đại diện: Eyeriss (Chen 2016).", size=8.5, fill="#475569")
    f.text(x3 + 14, 381, "• Cân bằng tối ưu giữa reuse và reduction.", size=8.5, fill="#475569")

    y_src = 388
    source(f, y_src, "[T2 Chen 2016 tr.4-6] [T2 Jouppi 2017 tr.3] [T2 Gao 2023 tr.2]")
    return f


# ==============================================================================
# HAM RUN
# ==============================================================================
if __name__ == "__main__":
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("npu-01-pe-mac-structure", fig_pe_mac_structure),
        ("npu-02-dataflow-comparison", fig_dataflow_comparison),
    ]
    run(figures, DEFAULT_OUTDIR)
