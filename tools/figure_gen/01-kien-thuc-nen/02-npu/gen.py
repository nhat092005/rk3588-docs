#!/usr/bin/env python3
"""Chuyen de: Kien truc NPU va Dataflow (02-npu).

Sinh cac hinh vector SVG minh hoa:
  1. npu-01-pe-mac-structure:
     Vi kien truc cua mot Processing Element (PE) / MAC Unit: duong du lieu ALU,
     thanh ghi trong so/kich hoat, bo tich luy 32-bit va duong truyen systolic.
  2. npu-02-dataflow-comparison:
     So sanh co che luan chuyen du lieu: Weight Stationary (WS), Output Stationary (OS),
     va Row Stationary (RS - Eyeriss).
  3. npu-03-sparsity-zero-skipping:
     Co che Sparsity va Zero-skipping: nguon goc du lieu thua (ReLU, pruning),
     3 khoi phan cung khai thac va danh doi kien truc (Eyeriss, TPU, RK3588).

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


AMBER = "#D97706"


def arrow(f, x1, y1, x2, y2, color=BLUE, sw=THIN, dashed=False):
    if color not in (BLUE, GREEN, RED, GRAY, INK, AMBER):
        color = INK
    f.line([(x1, y1), (x2, y2)], color, width=sw, dashed=dashed, head=True)


def badge(f, x, y, num_str, col="#2563EB"):
    """Small phase badge e.g. [1], [2], [3], [4]"""
    rect(f, x, y, 16, 12, fill=col, stroke=col, sw=0.8, rx=2)
    f.text(x + 8, y + 6.5, num_str, size=6.6, weight=700, fill="white", anchor="middle")


# 1. HINH VI KIEN TRUC PROCESSING ELEMENT (npu-01-pe-mac-structure)
# ==============================================================================
def fig_pe_mac_structure():
    """HÌNH 1: Vi kiến trúc Processing Element (PE) và chu trình thực thi trong 1 chu kỳ clock."""
    H = 434
    f = Fig(W, H)
    f.a('<defs><marker id="mD97706n" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 0.5L10 5L0 9.5z" fill="#D97706"/></marker></defs>')
    tier(f, "T2 chung", x=W - 130, y=12)
    f.text(18, 22, "Vi kiến trúc Processing Element (PE) và Chu trình Thực thi trong 1 Chu kỳ Clock",
           size=13.0, weight=700, fill=DARK)
    f.text(18, 36, "3 thành phần cốt lõi (pFIFO, Register File < 1 kB, ALU Datapath) và diễn biến 4 pha thực thi [Chen 2016, Jouppi 2017]",
           size=7.5, fill="#64748B")

    card_y = 48
    card_h = 348

    # ==========================================================================
    # CỘT TRÁI: PANEL A - VI KIẾN TRÚC PHẦN CỨNG PE & 3 THÀNH PHẦN CỐT LÕI
    # ==========================================================================
    x_a = 18
    w_a = 478
    rect(f, x_a, card_y, w_a, card_h, fill="#F8FAFC", stroke="#2563EB", sw=1.3, rx=6)
    rect(f, x_a, card_y, w_a, 22, fill="#EFF6FF", stroke="#2563EB", sw=1.0, rx=6)
    rect(f, x_a + 8, card_y + 4, 5, 14, fill=BLUE, stroke=BLUE, rx=2)
    f.text(x_a + 20, card_y + 12, "A. Vi kiến trúc Phần cứng PE & 3 Thành phần Cốt lõi (Chen 2016)",
           size=9.8, weight=700, fill="#1E40AF")

    # Systolic Neighbors ngoài PE
    # 1. Neighbor trái: PE(r, c-1)
    rect(f, 24, 122, 46, 32, fill="#FFFFFF", stroke="#94A3B8", sw=1.0, rx=3)
    f.text(47, 138, "PE(r,c-1)", size=6.8, weight=700, fill="#64748B", anchor="middle")
    arrow(f, 70, 138, 98, 138, color=BLUE, sw=1.8)
    f.text(81, 129, "x_in", size=6.8, weight=700, fill="#1E40AF", anchor="middle")

    # 2. Neighbor trên: PE(r-1, c)
    rect(f, 332, 74, 68, 16, fill="#FFFFFF", stroke="#94A3B8", sw=1.0, rx=3)
    f.text(366, 82, "PE(r-1, c)", size=6.8, weight=700, fill="#64748B", anchor="middle")
    f.line([(366, 90), (366, 106)], color=GREEN, width=1.8, head=False)
    f.text(404, 82, "P_in [32b]", size=6.8, weight=700, fill="#047857")

    # 3. Neighbor phải: PE(r, c+1)
    rect(f, 442, 122, 46, 32, fill="#FFFFFF", stroke="#94A3B8", sw=1.0, rx=3)
    f.text(465, 138, "PE(r,c+1)", size=6.8, weight=700, fill="#64748B", anchor="middle")
    arrow(f, 416, 138, 442, 138, color=BLUE, sw=1.8)
    f.text(429, 129, "x_out", size=6.8, weight=700, fill="#1E40AF", anchor="middle")

    # 4. Neighbor dưới: PE(r+1, c)
    rect(f, 332, 366, 68, 18, fill="#FFFFFF", stroke="#94A3B8", sw=1.0, rx=3)
    f.text(366, 375, "PE(r+1, c)", size=6.8, weight=700, fill="#64748B", anchor="middle")
    arrow(f, 366, 348, 366, 366, color=GREEN, sw=1.8)
    f.text(404, 375, "P_out [32b]", size=6.8, weight=700, fill="#047857")

    # KHUNG PE CORE CHÍNH
    pe_x = 92
    pe_y = 106
    pe_w = 324
    pe_h = 242
    rect(f, pe_x, pe_y, pe_w, pe_h, fill="#FFFFFF", stroke="#1E293B", sw=1.4, rx=6)
    rect(f, pe_x + 6, pe_y + 4, 146, 14, fill="#F1F5F9", stroke="#CBD5E1", sw=0.8, rx=2)
    f.text(pe_x + 10, pe_y + 11, "Processing Element: PE(r, c)", size=6.8, weight=700, fill="#334155")

    # --------------------------------------------------------------------------
    # THÀNH PHẦN 3 KHUNG CHỨA (ALU Datapath container) - Vẽ trước để không che con
    # --------------------------------------------------------------------------
    alu_x = 246
    alu_y = 168
    alu_w = 164
    alu_h = 180
    rect(f, alu_x, alu_y, alu_w, alu_h, fill="#F8FAFC", stroke="#0F172A", sw=1.2, dashed=True, rx=4)
    rect(f, alu_x + 4, alu_y + 4, 108, 13, fill="#F1F5F9", stroke="#CBD5E1", sw=0.7, rx=2)
    f.text(alu_x + 8, alu_y + 10.5, "3. ALU Datapath (MAC)", size=6.8, weight=700, fill=DARK)

    # --------------------------------------------------------------------------
    # THÀNH PHẦN 1: pFIFO Buffer (Hàng đợi điều phối vào/ra)
    # --------------------------------------------------------------------------
    q_x = 98
    q_y = 124
    q_w = 98
    q_h = 46
    rect(f, q_x, q_y, q_w, q_h, fill="#EFF6FF", stroke=BLUE, sw=1.0, rx=3)
    f.text(q_x + 6, q_y + 10, "1. pFIFO Buffer (Vào/Ra)", size=7.0, weight=700, fill="#1E40AF")

    # Ô slot trong pFIFO
    slot_w = 20
    slot_h = 20
    sy = q_y + 18
    rect(f, q_x + 5, sy, slot_w, slot_h, fill="#DBEAFE", stroke="#93C5FD", sw=0.8, rx=2)
    f.text(q_x + 15, sy + 10, "x[3]", size=6.8, fill="#1E40AF", anchor="middle")
    rect(f, q_x + 27, sy, slot_w, slot_h, fill="#DBEAFE", stroke="#93C5FD", sw=0.8, rx=2)
    f.text(q_x + 37, sy + 10, "x[2]", size=6.8, fill="#1E40AF", anchor="middle")
    rect(f, q_x + 49, sy, slot_w, slot_h, fill="#DBEAFE", stroke="#93C5FD", sw=0.8, rx=2)
    f.text(q_x + 59, sy + 10, "x[1]", size=6.8, fill="#1E40AF", anchor="middle")
    # slot 0: Active / Popping
    rect(f, q_x + 71, sy, 22, slot_h, fill=BLUE, stroke="#1E40AF", sw=1.0, rx=2)
    f.text(q_x + 82, sy + 6.5, "+3", size=7.2, weight=700, fill="white", anchor="middle")
    f.text(q_x + 82, sy + 14.5, "8b", size=6.6, weight=700, fill="#93C5FD", anchor="middle")

    # Đường rẽ từ pFIFO:
    # 1. Đi ngang thẳng trục y=138 sang x Forward Reg
    arrow(f, q_x + q_w, 138, 368, 138, color=BLUE, sw=1.5)
    rect(f, 368, 124, 34, 28, fill="#EFF6FF", stroke=BLUE, sw=1.0, rx=2)
    f.text(385, 133, "x-Reg", size=6.8, weight=700, fill="#1E40AF", anchor="middle")
    f.text(385, 143, "8b >", size=6.8, fill="#1E40AF", anchor="middle")
    f.line([(402, 138), (pe_x + pe_w, 138)], color=BLUE, width=1.5, head=False)

    # 2. Rẽ xuống Bộ nhân ALU (Pha 1: Nạp toán hạng)
    f.a('<circle cx="206" cy="138" r="2.5" fill="#1E40AF"/>')
    f.line([(206, 138), (206, 194)], color=BLUE, width=1.5, head=False)
    arrow(f, 206, 194, 252, 194, color=BLUE, sw=1.5)
    f.text(210, 186, "x_i=+3 [8b]", size=6.6, weight=700, fill="#1E40AF")

    # --------------------------------------------------------------------------
    # THÀNH PHẦN 2: Register File (RF < 1 kB, Local Scratchpad)
    # --------------------------------------------------------------------------
    rf_x = 98
    rf_y = 184
    rf_w = 98
    rf_h = 64
    rect(f, rf_x, rf_y, rf_w, rf_h, fill="#FFFBEB", stroke=AMBER, sw=1.0, rx=3)
    f.text(rf_x + 6, rf_y + 10, "2. RF (<1 kB Scratchpad)", size=7.0, weight=700, fill="#92400E")

    # 3 Hàng thanh ghi RF (Hàng w[0] căn thẳng trục y=212 nối thẳng vào Bộ nhân)
    rect(f, rf_x + 5, rf_y + 22, rf_w - 10, 12, fill="#FEF3C7", stroke=AMBER, sw=0.9, rx=1.5)
    f.text(rf_x + 9, 212, "w[0] = -2", size=6.8, weight=700, fill="#92400E")
    f.text(rf_x + 89, 212, "INT8", size=6.6, weight=700, fill="#B45309", anchor="end")

    rect(f, rf_x + 5, rf_y + 36, rf_w - 10, 12, fill="#FFFFFF", stroke="#FDE68A", sw=0.6, rx=1)
    f.text(rf_x + 9, 226, "w[1] = +5", size=6.6, fill="#B45309")
    f.text(rf_x + 89, 226, "INT8", size=6.6, fill="#B45309", anchor="end")

    rect(f, rf_x + 5, rf_y + 49, rf_w - 10, 12, fill="#FFFFFF", stroke="#FDE68A", sw=0.6, rx=1)
    f.text(rf_x + 9, 239, "w[2] = +1", size=6.6, fill="#B45309")
    f.text(rf_x + 89, 239, "INT8", size=6.6, fill="#B45309", anchor="end")

    # Dây từ Weight RF vào Bộ nhân ALU (Thẳng hàng ngang hoàn toàn, không gấp khúc)
    arrow(f, rf_x + rf_w, 212, 252, 212, color=AMBER, sw=1.5)
    f.text(224, 222, "w_i=-2 [8b]", size=6.6, weight=700, fill="#92400E", anchor="middle")

    # --------------------------------------------------------------------------
    # THÀNH PHẦN 3 CHI TIẾT (Bên trong ALU Datapath)
    # --------------------------------------------------------------------------
    # 3.1 Bộ nhân ALU (Multiplier) - Pha 2
    mul_x = 252
    mul_y = 186
    mul_w = 66
    mul_h = 44
    rect(f, mul_x, mul_y, mul_w, mul_h, fill="#EFF6FF", stroke=BLUE, sw=1.1, rx=3)
    f.text(mul_x + 33, mul_y + 10, "MUL (*) [Pha 2]", size=7.0, weight=700, fill="#1E40AF", anchor="middle")
    f.text(mul_x + 33, mul_y + 22, "8b x 8b -> 16b", size=6.6, mono=True, fill=DARK, anchor="middle")
    f.text(mul_x + 33, mul_y + 34, "(+3) x (-2) = -6", size=6.8, weight=700, fill="#1E40AF", anchor="middle")

    # Dây ra từ Bộ nhân đến Bộ cộng
    f.line([(mul_x + 33, mul_y + mul_h), (mul_x + 33, 256)], color=BLUE, width=1.5, head=False)
    arrow(f, mul_x + 33, 256, 326, 256, color=BLUE, sw=1.5)
    f.text(252, 266, "prod=-6 [16b]", size=6.8, weight=700, fill="#1E40AF")

    # 3.2 Bộ cộng ALU 32-bit (Adder) - Pha 3
    add_x = 326
    add_y = 236
    add_w = 76
    add_h = 44
    rect(f, add_x, add_y, add_w, add_h, fill="#ECFDF5", stroke=GREEN, sw=1.1, rx=3)
    f.text(add_x + 38, add_y + 10, "ADD (+) 32b [Pha 3]", size=7.0, weight=700, fill="#047857", anchor="middle")
    f.text(add_x + 38, add_y + 22, "P_in + prod", size=6.6, fill=DARK, anchor="middle")
    f.text(add_x + 38, add_y + 34, "10 + (-6) = +4", size=7.0, weight=700, fill="#047857", anchor="middle")

    # Dây P_in từ PE trên vào Bộ cộng (thẳng trục x=366)
    arrow(f, 366, 106, 366, add_y, color=GREEN, sw=1.8)
    f.text(370, 115, "P_in=10", size=6.6, weight=700, fill="#047857")

    # 3.3 Thanh ghi Psum (Accumulator Reg) - Pha 4
    ps_x = 338
    ps_y = 296
    ps_w = 56
    ps_h = 28
    arrow(f, 366, add_y + add_h, 366, ps_y, color=GREEN, sw=1.8)
    rect(f, ps_x, ps_y, ps_w, ps_h, fill="#F0FDF4", stroke=GREEN, sw=1.1, rx=2)
    f.text(ps_x + 28, ps_y + 10, "Psum Reg [P4]", size=6.8, weight=700, fill="#047857", anchor="middle")
    f.text(ps_x + 28, ps_y + 20, "+4 [32b] >", size=6.8, weight=700, fill="#047857", anchor="middle")

    # Dây từ Psum Reg xuống đáy PE Core (dây nối, đầu mũi tên nằm ở đoạn ngoài PE)
    f.line([(366, ps_y + ps_h), (366, pe_y + pe_h)], color=GREEN, width=1.8, head=False)

    # Thẻ tóm tắt nguyên lý năng lượng đáy Panel A
    ey_x = 98
    ey_y = 252
    ey_w = 120
    ey_h = 90
    rect(f, ey_x, ey_y, ey_w, ey_h, fill="#F8FAFC", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(ey_x + 6, ey_y + 11, "Đặc tính Phần cứng (Chen):", size=6.8, weight=700, fill="#334155")
    f.text(ey_x + 6, ey_y + 25, "• RF < 1 kB SRAM nội:", size=6.6, fill="#475569")
    f.text(ey_x + 12, ey_y + 36, "Tiết kiệm ~200x vs DRAM", size=6.6, weight=700, fill="#92400E")
    f.text(ey_x + 6, ey_y + 49, "• pFIFO chống nghẽn NoC:", size=6.6, fill="#475569")
    f.text(ey_x + 12, ey_y + 60, "Cấp luồng đều cho ALU", size=6.6, fill="#1E40AF")
    f.text(ey_x + 6, ey_y + 73, "• Đạt 1 MAC/PE/chu kỳ", size=6.6, weight=700, fill="#047857")
    f.text(ey_x + 12, ey_y + 83, "khi đủ dữ liệu [Chen tr.7]", size=6.6, fill="#475569")

    # ==========================================================================
    # CỘT PHẢI: PANEL B - DẠNG SÓNG XUNG NHỊP VÀ 4 PHA THỰC THI 1 CHU KỲ
    # ==========================================================================
    x_b = 504
    w_b = 358
    rect(f, x_b, card_y, w_b, card_h, fill="#F8FAFC", stroke="#059669", sw=1.3, rx=6)
    rect(f, x_b, card_y, w_b, 22, fill="#ECFDF5", stroke="#059669", sw=1.0, rx=6)
    rect(f, x_b + 8, card_y + 4, 5, 14, fill=GREEN, stroke=GREEN, rx=2)
    f.text(x_b + 20, card_y + 12, "B. Diễn biến 1 Chu kỳ Clock: Dạng sóng & 4 Pha Thực thi",
           size=9.8, weight=700, fill="#047857")

    # 1. Dạng sóng xung nhịp CLK
    wf_x = 514
    wf_y = 75
    wf_w = 338
    wf_h = 52
    rect(f, wf_x, wf_y, wf_w, wf_h, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    f.text(wf_x + 8, wf_y + 10, "Xung nhịp Clock (CLK)", size=7.0, weight=700, fill="#334155")

    # Đường sóng vuông
    clk_pts = [
        (524, wf_y + 34), (544, wf_y + 34),
        (544, wf_y + 20), (664, wf_y + 20),
        (664, wf_y + 34), (784, wf_y + 34),
        (784, wf_y + 20), (840, wf_y + 20)
    ]
    d_clk = "M" + " L".join(f"{px:g} {py:g}" for px, py in clk_pts)
    f.a(f'<path d="{d_clk}" fill="none" stroke="#2563EB" stroke-width="1.8"/>')

    # Nhãn sườn xung
    f.text(544, wf_y + 43.5, "Sườn lên t (Nạp)", size=6.8, weight=700, fill="#2563EB", anchor="middle")
    f.text(784, wf_y + 43.5, "Sườn lên t+1 (Chốt)", size=6.8, weight=700, fill="#047857", anchor="middle")

    # Mũi tên khoảng chu kỳ T
    f.text(700, wf_y + 10, "<--- Chu kỳ Clock T (1 Cycle) --->", size=6.8, weight=700, fill=DARK, anchor="middle")

    # 2. 4 Giai đoạn lan truyền tín hiệu (Pipeline Stages)
    stages = [
        ("1", "Pha 1: Nạp toán hạng", "0% - 15% T", "Lấy x_i từ pFIFO, w_i từ RF, P_in từ PE phía trên",
         "x_i = +3 [8b]  |  w_i = -2 [8b]  |  P_in = +10 [32b]", BLUE, "#EFF6FF", "#1E40AF"),
        ("2", "Pha 2: Nhân số học", "15% - 50% T", "Lan truyền qua mạch nhân mảng Booth trong ALU",
         "prod = x_i x w_i = (+3) x (-2) = -6 [16b signed, ~0.2 pJ]", "#D97706", "#FFFBEB", "#92400E"),
        ("3", "Pha 3: Cộng tích lũy", "50% - 85% T", "Mở rộng dấu 16b->32b và cộng vào Partial Sum",
         "P_out = P_in + prod = (+10) + (-6) = +4 [32b CLA chống tràn]", GREEN, "#ECFDF5", "#047857"),
        ("4", "Pha 4: Chuyển tiếp Systolic", "85% - 100% T", "Chốt thanh ghi và chuyển tiếp sang PE kế cận",
         "P_out = +4 (xuống PE dưới)  |  x_i = +3 (sang PE phải) [Hoàn tất]", "#1E293B", "#F1F5F9", "#1E293B"),
    ]

    st_y = 132
    st_h = 36
    st_gap = 6
    for i, (b_num, title, time_span, desc, detail, col, bg, text_col) in enumerate(stages):
        cur_y = st_y + i * (st_h + st_gap)
        rect(f, wf_x, cur_y, wf_w, st_h, fill="#FFFFFF", stroke=col, sw=1.0, rx=3)
        # Badge pha số
        badge(f, wf_x + 6, cur_y + 5, b_num, col)
        # Tiêu đề pha
        f.text(wf_x + 26, cur_y + 11, title, size=7.0, weight=700, fill=col)
        # Khung thời gian
        f.text(wf_x + 130, cur_y + 11, time_span, size=6.8, weight=700, fill="#475569")
        # Mô tả hành động
        f.text(wf_x + 185, cur_y + 11, desc, size=6.6, fill=DARK)
        # Dữ liệu cụ thể
        f.text(wf_x + 10, cur_y + 26, detail, size=6.8, mono=True, fill=text_col)

    # 3. Đặc tả thực thi ở đáy Panel B
    bot_y = 300
    bot_h = 84
    rect(f, wf_x, bot_y, wf_w, bot_h, fill="#ECFDF5", stroke=GREEN, sw=1.0, rx=3)
    f.text(wf_x + 8, bot_y + 12, "HỢP ĐỒNG THỰC THI 1 CHU KỲ CLOCK (THROUGHPUT CONTRACT):",
           size=7.2, weight=700, fill="#047857")
    f.text(wf_x + 8, bot_y + 28, "• Thông lượng: Đạt đúng 1 MAC / PE / chu kỳ khi đủ dữ liệu [Chen 2016 tr.7]",
           size=6.8, fill=DARK)
    f.text(wf_x + 8, bot_y + 44, "• Không có bong bóng tính toán (stall-free) nhờ pFIFO và RF đệm luồng",
           size=6.8, fill=DARK)
    f.text(wf_x + 8, bot_y + 60, "• Truyền Systolic 2D: X truyền ngang, Psum truyền dọc đồng bộ chu kỳ",
           size=6.8, fill=DARK)
    f.text(wf_x + 8, bot_y + 75, "• Năng lượng thấp: ~0.2 pJ/MAC (INT8) so với ~1.2 pJ/MAC (FP16) [Jouppi 2017]",
           size=6.8, weight=700, fill="#047857")

    # Dòng nguồn
    source(f, card_y + card_h + 10, "Nguồn: T2 Chen 2016 tr.2, tr.7; T2 Jouppi 2017 tr.1, tr.3. Một PE gồm 3 thành phần: pFIFO, RF (< 1 kB), ALU Datapath (MAC/add).")
    return f


# ==============================================================================
# 2. HINH SO SANH DATAFLOW (npu-02-dataflow-comparison)
# ==============================================================================
def fig_dataflow_comparison():
    H = 506
    f = Fig(W, H)
    f.a('<defs><marker id="mD97706n" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 0.5L10 5L0 9.5z" fill="#D97706"/></marker></defs>')
    tier(f, "T2 chung", x=W - 130, y=12)
    f.text(18, 22, "So sánh Cơ chế Luân chuyển Dữ liệu NPU: Weight Stationary, Output Stationary và Row Stationary",
           size=13.0, weight=700, fill=DARK)
    f.text(18, 36, "Phân tích vi kiến trúc PE, luồng truyền không gian 2D và đánh đổi năng lượng [Chen 2016, Jouppi 2017, Gao 2023]",
           size=7.5, fill="#64748B")

    col_w = 272
    col_h = 420
    gap = 14
    x0 = 18
    card_y = 48

    configs = [
        ("Weight Stationary (WS)", "Google TPU / NVDLA", "#2563EB", 0),
        ("Output Stationary (OS)", "ShiDianNao / Layer-Puzzle", "#7C3AED", 1),
        ("Row Stationary (RS)", "Eyeriss (Chen 2016)", "#059669", 2),
    ]

    for title, subtitle, accent_color, idx in configs:
        cx = x0 + idx * (col_w + gap)

        # Khung cột chính
        rect(f, cx, card_y, col_w, col_h, fill="#F8FAFC", stroke="#64748B", sw=1.2, rx=6)

        # 1. Header Strip (y: 48, h: 36)
        rect(f, cx, card_y, col_w, 36, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=6)
        rect(f, cx + 8, card_y + 6, 5, 24, fill=accent_color, stroke=accent_color, sw=1, rx=2)
        f.text(cx + 20, card_y + 14, title, size=10.0, weight=700, fill="#0F172A")
        f.text(cx + 20, card_y + 26, f"Kiến trúc đại diện: {subtitle}", size=6.8, fill="#475569")

        # 2. Khối con 1: Vi kiến trúc lưu trữ nội PE (y: 88, h: 92)
        y_pe = card_y + 40
        h_pe = 92
        rect(f, cx + 8, y_pe, col_w - 16, h_pe, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
        rect(f, cx + 8, y_pe, col_w - 16, 14, fill="#F1F5F9", stroke="#CBD5E1", sw=0.8, rx=3)

        if idx == 0:
            # WS PE Datapath: X ngang, Psum dọc, W cố định trong RF
            f.text(cx + 14, y_pe + 7, "Cấu trúc nội PE: W cố định trong RF", size=7.2, weight=700, fill="#1E40AF")

            # Weight RF (trên Multiplier)
            rect(f, cx + 52, y_pe + 17, 58, 18, fill="#EFF6FF", stroke=BLUE, sw=1.0, rx=2)
            f.text(cx + 81, y_pe + 26, "W cố định", size=6.6, weight=700, fill="#1E40AF", anchor="middle")
            arrow(f, cx + 81, y_pe + 35, cx + 81, y_pe + 48, color=BLUE, sw=1.2)

            # Multiplier
            rect(f, cx + 60, y_pe + 48, 42, 28, fill="#F8FAFC", stroke=DARK, sw=1.0, rx=3)
            f.text(cx + 81, y_pe + 57, "MUL (*)", size=7.0, weight=700, fill=DARK, anchor="middle")
            f.text(cx + 81, y_pe + 68, "X x W", size=6.6, mono=True, fill="#64748B", anchor="middle")

            # X_in từ trái vào MUL
            arrow(f, cx + 18, y_pe + 62, cx + 60, y_pe + 62, color=BLUE, sw=1.5)
            f.text(cx + 36, y_pe + 54, "X_in", size=6.8, weight=700, fill=BLUE, anchor="middle")

            # Dây nối MUL sang ADD
            arrow(f, cx + 102, y_pe + 62, cx + 140, y_pe + 62, color=DARK, sw=1.2)

            # Adder (+)
            rect(f, cx + 140, y_pe + 48, 44, 28, fill="#ECFDF5", stroke=GREEN, sw=1.0, rx=3)
            f.text(cx + 162, y_pe + 57, "ADD (+)", size=7.0, weight=700, fill="#047857", anchor="middle")
            f.text(cx + 162, y_pe + 68, "32b Psum", size=6.6, mono=True, fill="#047857", anchor="middle")

            # P_in từ trên xuống Adder, P_out xuống dưới
            arrow(f, cx + 162, y_pe + 22, cx + 162, y_pe + 48, color=GREEN, sw=1.5)
            f.text(cx + 172, y_pe + 32, "P_in", size=6.8, weight=700, fill=GREEN)
            arrow(f, cx + 162, y_pe + 76, cx + 162, y_pe + 89, color=GREEN, sw=1.5)
            f.text(cx + 174, y_pe + 83, "P_out", size=6.6, weight=700, fill=GREEN)

            # Thẻ tóm tắt đặc tính WS
            rect(f, cx + 196, y_pe + 38, 58, 42, fill="#EFF6FF", stroke=BLUE, sw=0.9, rx=3)
            f.text(cx + 225, y_pe + 49, "Đặc tính WS:", size=6.6, weight=700, fill="#1E40AF", anchor="middle")
            f.text(cx + 225, y_pe + 60, "W đứng yên", size=6.6, fill="#1E40AF", anchor="middle")
            f.text(cx + 225, y_pe + 71, "Psum dồn dọc", size=6.6, fill="#047857", anchor="middle")

        elif idx == 1:
            # OS PE Datapath: X ngang, W dọc, Psum Y cố định trong Acc RF
            f.text(cx + 14, y_pe + 7, "Cấu trúc nội PE: Psum Y cố định trong RF", size=7.2, weight=700, fill="#7C3AED")

            # Multiplier
            rect(f, cx + 46, y_pe + 48, 40, 28, fill="#F8FAFC", stroke=DARK, sw=1.0, rx=3)
            f.text(cx + 66, y_pe + 57, "MUL (*)", size=7.0, weight=700, fill=DARK, anchor="middle")
            f.text(cx + 66, y_pe + 68, "X x W", size=6.6, mono=True, fill="#64748B", anchor="middle")

            # X_in từ trái
            arrow(f, cx + 16, y_pe + 62, cx + 46, y_pe + 62, color=BLUE, sw=1.5)
            f.text(cx + 31, y_pe + 54, "X_in", size=6.8, weight=700, fill=BLUE, anchor="middle")

            # W_in từ trên và W_fwd xuống dưới
            arrow(f, cx + 66, y_pe + 22, cx + 66, y_pe + 48, color="#D97706", sw=1.5)
            f.text(cx + 76, y_pe + 32, "W_in", size=6.8, weight=700, fill="#92400E")
            arrow(f, cx + 66, y_pe + 76, cx + 66, y_pe + 89, color="#D97706", sw=1.5)
            f.text(cx + 76, y_pe + 83, "W_fwd", size=6.6, weight=700, fill="#92400E")

            # Adder (+)
            rect(f, cx + 110, y_pe + 48, 38, 28, fill="#F8FAFC", stroke=DARK, sw=1.0, rx=3)
            f.text(cx + 129, y_pe + 62, "ADD (+)", size=7.0, weight=700, fill=DARK, anchor="middle")
            arrow(f, cx + 86, y_pe + 62, cx + 110, y_pe + 62, color=DARK, sw=1.2)

            # Accumulator RF (Cố định)
            rect(f, cx + 164, y_pe + 34, 88, 46, fill="#ECFDF5", stroke=GREEN, sw=1.1, rx=3)
            f.text(cx + 208, y_pe + 44, "Psum Acc RF", size=7.0, weight=700, fill="#047857", anchor="middle")
            rect(f, cx + 170, y_pe + 54, 76, 18, fill="#DCFCE7", stroke=GREEN, sw=0.8, rx=2)
            f.text(cx + 208, y_pe + 63, "Y_ij cố định tích lũy", size=6.6, weight=700, fill="#047857", anchor="middle")

            # Dây nối sang Acc và loopback
            arrow(f, cx + 148, y_pe + 62, cx + 164, y_pe + 62, color=GREEN, sw=1.2)
            f.line([(cx + 180, y_pe + 34), (cx + 180, y_pe + 26), (cx + 129, y_pe + 26), (cx + 129, y_pe + 48)],
                   GREEN, width=1.0, head=True)

        else:
            # RS PE Datapath: 1D Conv Primitive trong RF
            f.text(cx + 14, y_pe + 7, "Cấu trúc nội PE: 1D Conv Primitive trong RF", size=7.2, weight=700, fill="#047857")

            # Multi-bank RF
            rect(f, cx + 14, y_pe + 22, 100, 48, fill="#F0FDF4", stroke=GREEN, sw=1.0, rx=3)
            f.text(cx + 64, y_pe + 30, "RF đa vùng (Multi-bank)", size=6.8, weight=700, fill="#047857", anchor="middle")
            rect(f, cx + 18, y_pe + 36, 92, 14, fill="#FEF3C7", stroke="#D97706", sw=0.7, rx=1.5)
            f.text(cx + 64, y_pe + 43, "W-row cố định (R từ)", size=6.6, weight=700, fill="#92400E", anchor="middle")
            rect(f, cx + 18, y_pe + 52, 92, 14, fill="#DBEAFE", stroke=BLUE, sw=0.7, rx=1.5)
            f.text(cx + 64, y_pe + 59, "X-row trượt (W từ)", size=6.6, weight=700, fill="#1E40AF", anchor="middle")

            # 1D MAC Unit
            rect(f, cx + 130, y_pe + 26, 54, 40, fill="#ECFDF5", stroke=GREEN, sw=1.1, rx=3)
            f.text(cx + 157, y_pe + 38, "1D MAC", size=7.0, weight=700, fill="#047857", anchor="middle")
            f.text(cx + 157, y_pe + 51, "Primitive", size=6.6, fill="#047857", anchor="middle")
            arrow(f, cx + 114, y_pe + 46, cx + 130, y_pe + 46, color=GREEN, sw=1.2)

            # 1D Psum Accumulator
            rect(f, cx + 198, y_pe + 26, 58, 40, fill="#FFFFFF", stroke=DARK, sw=1.0, rx=3)
            f.text(cx + 227, y_pe + 38, "Psum RF", size=7.0, weight=700, fill=DARK, anchor="middle")
            f.text(cx + 227, y_pe + 51, "Tích lũy 1D", size=6.6, fill="#475569", anchor="middle")
            arrow(f, cx + 184, y_pe + 46, cx + 198, y_pe + 46, color=GREEN, sw=1.2)

            f.text(cx + 14, y_pe + 80, "• Tối ưu cả 3 kiểu reuse (conv, filter, ifmap)", size=6.8, fill="#047857")

        # 3. Khối con 2: Luồng truyền không gian trên Mảng PE 2x2 (y: 186, h: 148)
        y_arr = y_pe + h_pe + 6
        h_arr = 148
        rect(f, cx + 8, y_arr, col_w - 16, h_arr, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
        rect(f, cx + 8, y_arr, col_w - 16, 14, fill="#F8FAFC", stroke="#CBD5E1", sw=0.8, rx=3)
        f.text(cx + 14, y_arr + 7, "Luồng truyền không gian trên Mảng PE 2D", size=7.2, weight=700, fill=DARK)

        # 4 PE (2x2)
        pe_grid = [
            (cx + 52, y_arr + 28, "PE(0,0)"),
            (cx + 150, y_arr + 28, "PE(0,1)"),
            (cx + 52, y_arr + 86, "PE(1,0)"),
            (cx + 150, y_arr + 86, "PE(1,1)"),
        ]

        for px, py, plabel in pe_grid:
            rect(f, px, py, 60, 36, fill="#F8FAFC", stroke="#475569", sw=1.0, rx=3)
            f.text(px + 30, py + 10.5, plabel, size=6.8, weight=700, fill=DARK, anchor="middle")

            if idx == 0:
                rect(f, px + 8, py + 18, 44, 14, fill="#DBEAFE", stroke=BLUE, sw=0.8, rx=2)
                f.text(px + 30, py + 25, "W cố định", size=6.6, weight=700, fill="#1E40AF", anchor="middle")
            elif idx == 1:
                rect(f, px + 8, py + 18, 44, 14, fill="#DCFCE7", stroke=GREEN, sw=0.8, rx=2)
                f.text(px + 30, py + 25, "Y cố định", size=6.6, weight=700, fill="#047857", anchor="middle")
            else:
                rect(f, px + 8, py + 18, 44, 14, fill="#FEF3C7", stroke="#D97706", sw=0.8, rx=2)
                f.text(px + 30, py + 25, "1D-Conv", size=6.6, weight=700, fill="#92400E", anchor="middle")

        # Routing Arrows
        if idx == 0:
            # WS: X ngang, Psum dọc
            # P_in=0 vào đỉnh 2 cột
            arrow(f, cx + 82, y_arr + 15, cx + 82, y_arr + 28, color=GREEN, sw=1.5)
            f.text(cx + 96, y_arr + 21, "P_in=0", size=6.6, weight=700, fill="#047857")
            arrow(f, cx + 180, y_arr + 15, cx + 180, y_arr + 28, color=GREEN, sw=1.5)
            f.text(cx + 194, y_arr + 21, "P_in=0", size=6.6, weight=700, fill="#047857")

            # Row 0 X
            arrow(f, cx + 18, y_arr + 46, cx + 52, y_arr + 46, color=BLUE, sw=1.5)
            f.text(cx + 35, y_arr + 39, "X_row0", size=6.6, weight=700, fill=BLUE, anchor="middle")
            arrow(f, cx + 112, y_arr + 46, cx + 150, y_arr + 46, color=BLUE, sw=1.5)
            arrow(f, cx + 210, y_arr + 46, cx + 228, y_arr + 46, color=BLUE, sw=1.5)
            rect(f, cx + 228, y_arr + 38, 28, 16, fill="#EFF6FF", stroke=BLUE, sw=0.8, rx=2)
            f.text(cx + 242, y_arr + 46, "x_out", size=6.6, weight=700, fill="#1E40AF", anchor="middle")

            # Row 1 X
            arrow(f, cx + 18, y_arr + 104, cx + 52, y_arr + 104, color=BLUE, sw=1.5)
            f.text(cx + 35, y_arr + 97, "X_row1", size=6.6, weight=700, fill=BLUE, anchor="middle")
            arrow(f, cx + 112, y_arr + 104, cx + 150, y_arr + 104, color=BLUE, sw=1.5)
            arrow(f, cx + 210, y_arr + 104, cx + 228, y_arr + 104, color=BLUE, sw=1.5)
            rect(f, cx + 228, y_arr + 96, 28, 16, fill="#EFF6FF", stroke=BLUE, sw=0.8, rx=2)
            f.text(cx + 242, y_arr + 104, "x_out", size=6.6, weight=700, fill="#1E40AF", anchor="middle")

            # Col 0 Psum
            arrow(f, cx + 82, y_arr + 64, cx + 82, y_arr + 86, color=GREEN, sw=1.8)
            f.text(cx + 96, y_arr + 75, "Psum", size=6.6, weight=700, fill=GREEN)
            arrow(f, cx + 82, y_arr + 122, cx + 82, y_arr + 135, color=GREEN, sw=1.8)
            f.text(cx + 82, y_arr + 140, "Y_out0", size=6.8, weight=700, fill="#047857", anchor="middle")

            # Col 1 Psum
            arrow(f, cx + 180, y_arr + 64, cx + 180, y_arr + 86, color=GREEN, sw=1.8)
            f.text(cx + 194, y_arr + 75, "Psum", size=6.6, weight=700, fill=GREEN)
            arrow(f, cx + 180, y_arr + 122, cx + 180, y_arr + 135, color=GREEN, sw=1.8)
            f.text(cx + 180, y_arr + 140, "Y_out1", size=6.8, weight=700, fill="#047857", anchor="middle")

        elif idx == 1:
            # OS: X ngang, W dọc, Y đứng yên
            # Row 0 X
            arrow(f, cx + 18, y_arr + 46, cx + 52, y_arr + 46, color=BLUE, sw=1.5)
            f.text(cx + 35, y_arr + 39, "X_row0", size=6.6, weight=700, fill=BLUE, anchor="middle")
            arrow(f, cx + 112, y_arr + 46, cx + 150, y_arr + 46, color=BLUE, sw=1.5)
            arrow(f, cx + 210, y_arr + 46, cx + 228, y_arr + 46, color=BLUE, sw=1.5)
            rect(f, cx + 228, y_arr + 38, 28, 16, fill="#EFF6FF", stroke=BLUE, sw=0.8, rx=2)
            f.text(cx + 242, y_arr + 46, "x_out", size=6.6, weight=700, fill="#1E40AF", anchor="middle")

            # Row 1 X
            arrow(f, cx + 18, y_arr + 104, cx + 52, y_arr + 104, color=BLUE, sw=1.5)
            f.text(cx + 35, y_arr + 97, "X_row1", size=6.6, weight=700, fill=BLUE, anchor="middle")
            arrow(f, cx + 112, y_arr + 104, cx + 150, y_arr + 104, color=BLUE, sw=1.5)
            arrow(f, cx + 210, y_arr + 104, cx + 228, y_arr + 104, color=BLUE, sw=1.5)
            rect(f, cx + 228, y_arr + 96, 28, 16, fill="#EFF6FF", stroke=BLUE, sw=0.8, rx=2)
            f.text(cx + 242, y_arr + 104, "x_out", size=6.6, weight=700, fill="#1E40AF", anchor="middle")

            # Col 0 W (thẳng trục x = cx + 82)
            arrow(f, cx + 82, y_arr + 15, cx + 82, y_arr + 28, color="#D97706", sw=1.5)
            f.text(cx + 96, y_arr + 21, "W0", size=6.6, weight=700, fill="#92400E")
            arrow(f, cx + 82, y_arr + 64, cx + 82, y_arr + 86, color="#D97706", sw=1.5)
            f.text(cx + 96, y_arr + 75, "W", size=6.6, weight=700, fill="#92400E")

            # Col 1 W (thẳng trục x = cx + 180)
            arrow(f, cx + 180, y_arr + 15, cx + 180, y_arr + 28, color="#D97706", sw=1.5)
            f.text(cx + 194, y_arr + 21, "W1", size=6.6, weight=700, fill="#92400E")
            arrow(f, cx + 180, y_arr + 64, cx + 180, y_arr + 86, color="#D97706", sw=1.5)
            f.text(cx + 194, y_arr + 75, "W", size=6.6, weight=700, fill="#92400E")

            # Output Y khi hoàn tất tích lũy
            f.line([(cx + 82, y_arr + 122), (cx + 82, y_arr + 135)], "#7C3AED", width=1.5, dashed=True, head=True)
            f.text(cx + 82, y_arr + 140, "Y_0 (xong)", size=6.8, weight=700, fill="#7C3AED", anchor="middle")
            f.line([(cx + 180, y_arr + 122), (cx + 180, y_arr + 135)], "#7C3AED", width=1.5, dashed=True, head=True)
            f.text(cx + 180, y_arr + 140, "Y_1 (xong)", size=6.8, weight=700, fill="#7C3AED", anchor="middle")

        else:
            # RS: Tái sử dụng không gian 3 hướng (Chen 2016 Fig. 6)
            # 1. Hàng W truyền ngang (Filter reuse)
            arrow(f, cx + 18, y_arr + 40, cx + 52, y_arr + 40, color="#D97706", sw=1.5)
            f.text(cx + 35, y_arr + 30, "W_row0", size=6.6, weight=700, fill="#92400E", anchor="middle")
            arrow(f, cx + 112, y_arr + 40, cx + 150, y_arr + 40, color="#D97706", sw=1.5)
            f.text(cx + 131, y_arr + 30, "W-row >", size=6.6, weight=700, fill="#92400E", anchor="middle")
            arrow(f, cx + 210, y_arr + 40, cx + 228, y_arr + 40, color="#D97706", sw=1.5)
            rect(f, cx + 228, y_arr + 32, 28, 16, fill="#FFFBEB", stroke="#D97706", sw=0.8, rx=2)
            f.text(cx + 242, y_arr + 40, "w_out", size=6.6, weight=700, fill="#92400E", anchor="middle")

            arrow(f, cx + 18, y_arr + 98, cx + 52, y_arr + 98, color="#D97706", sw=1.5)
            f.text(cx + 35, y_arr + 88, "W_row1", size=6.6, weight=700, fill="#92400E", anchor="middle")
            arrow(f, cx + 112, y_arr + 98, cx + 150, y_arr + 98, color="#D97706", sw=1.5)
            f.text(cx + 131, y_arr + 88, "W-row >", size=6.6, weight=700, fill="#92400E", anchor="middle")
            arrow(f, cx + 210, y_arr + 98, cx + 228, y_arr + 98, color="#D97706", sw=1.5)
            rect(f, cx + 228, y_arr + 90, 28, 16, fill="#FFFBEB", stroke="#D97706", sw=0.8, rx=2)
            f.text(cx + 242, y_arr + 98, "w_out", size=6.6, weight=700, fill="#92400E", anchor="middle")

            # 2. Hàng X truyền chéo (Chen 2016 Fig 6b: Ifmap reuse along anti-diagonal)
            # PE(1,0) chia sẻ hàng X lên PE(0,1)
            arrow(f, cx + 104, y_arr + 86, cx + 150, y_arr + 62, color=BLUE, sw=1.5, dashed=True)
            f.text(cx + 131, y_arr + 55, "X chéo ^", size=6.6, weight=700, fill=BLUE, anchor="middle")

            # 3. Psum cộng dồn dọc (Chen 2016 Fig 6c: Psum reduction)
            # Col 0:
            arrow(f, cx + 82, y_arr + 64, cx + 82, y_arr + 86, color=GREEN, sw=1.8)
            f.text(cx + 96, y_arr + 75, "Psum", size=6.6, weight=700, fill=GREEN)
            arrow(f, cx + 82, y_arr + 122, cx + 82, y_arr + 135, color=GREEN, sw=1.8)
            f.text(cx + 82, y_arr + 140, "Psum_2D", size=6.8, weight=700, fill="#047857", anchor="middle")

            # Col 1:
            arrow(f, cx + 180, y_arr + 64, cx + 180, y_arr + 86, color=GREEN, sw=1.8)
            f.text(cx + 194, y_arr + 75, "Psum", size=6.6, weight=700, fill=GREEN)
            arrow(f, cx + 180, y_arr + 122, cx + 180, y_arr + 135, color=GREEN, sw=1.8)
            f.text(cx + 180, y_arr + 140, "Psum_2D", size=6.8, weight=700, fill="#047857", anchor="middle")

        # 4. Khối con 3: Bảng Đánh giá & So sánh Kỹ thuật (y: 340, h: 114)
        y_tbl = y_arr + h_arr + 6
        h_tbl = 114
        rect(f, cx + 8, y_tbl, col_w - 16, h_tbl, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
        rect(f, cx + 8, y_tbl, col_w - 16, 14, fill="#F1F5F9", stroke="#CBD5E1", sw=0.8, rx=3)
        f.text(cx + 14, y_tbl + 7, "Đặc tả Kỹ thuật & Đánh đổi Năng lượng", size=7.2, weight=700, fill=DARK)

        metrics = [
            ("Lưu cố định PE:", "Trọng số W trong RF" if idx == 0 else "Psum Y trong RF Acc" if idx == 1 else "W-row + 1D Conv",
             "#1E40AF" if idx == 0 else "#7C3AED" if idx == 1 else "#047857"),
            ("Luồng NoC chính:", "X ngang | Psum dọc" if idx == 0 else "X ngang | W dọc" if idx == 1 else "W ngang, X chéo, P dọc",
             DARK),
            ("Điểm nghẽn chính:", "Psum 32b di chuyển" if idx == 0 else "Nạp lại X và W từ SRAM" if idx == 1 else "Điều khiển NoC phức tạp",
             "#B91C1C" if idx in (0, 1) else "#B45309"),
            ("Năng lượng tiêu thụ:", "1.4x - 2.5x tốn hơn" if idx == 0 else "1.3x - 2.0x tốn hơn" if idx == 1 else "1.0x (Tối ưu nhất)",
             "#B91C1C" if idx == 0 else "#D97706" if idx == 1 else "#166534"),
        ]

        row_h = 24
        for r_idx, (m_label, m_val, m_col) in enumerate(metrics):
            ry = y_tbl + 18 + r_idx * row_h
            if r_idx % 2 == 1:
                rect(f, cx + 10, ry, col_w - 20, row_h - 2, fill="#F8FAFC", stroke="#F1F5F9", sw=0.5, rx=2)
            f.text(cx + 14, ry + 11, m_label, size=6.8, weight=700, fill="#475569")

            # Value Badge
            if r_idx == 3:
                bg_col = "#FEF2F2" if idx == 0 else "#FFFBEB" if idx == 1 else "#ECFDF5"
                border_col = "#EF4444" if idx == 0 else "#F59E0B" if idx == 1 else "#10B981"
                rect(f, cx + 116, ry + 3, 134, 16, fill=bg_col, stroke=border_col, sw=0.8, rx=3)
                f.text(cx + 183, ry + 11, m_val, size=6.8, weight=700, fill=m_col, anchor="middle")
            else:
                f.text(cx + 118, ry + 11, m_val, size=6.8, weight=700 if r_idx == 0 else 400, fill=m_col)

    # Dòng nguồn đáy trang
    source(f, card_y + col_h + 10, "Nguồn: T2 Chen 2016 tr.4-6 (Eyeriss RS); T2 Jouppi 2017 tr.3 (TPU WS); T2 Gao 2023 tr.2 (Layer-Puzzle OS).")

    return f


# ==============================================================================
# 3. HINH CO CHE SPARSITY VA ZERO-SKIPPING (npu-03-sparsity-zero-skipping)
# ==============================================================================
def fig_sparsity_zero_skipping():
    """HÌNH 3: Cơ chế Sparsity và Zero-skipping trong Phần cứng Bộ tăng tốc AI / NPU."""
    H = 510
    f = Fig(W, H)
    f.a('<defs><marker id="mD97706n" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="10" markerHeight="10" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 0.5L10 5L0 9.5z" fill="#D97706"/></marker></defs>')
    tier(f, "T2 chung", x=W - 130, y=12)
    f.text(18, 22, "Cơ chế Sparsity và Zero-skipping trong Phần cứng Bộ tăng tốc AI / NPU",
           size=13.0, weight=700, fill=DARK)
    f.text(18, 36, "Nguồn dữ liệu thưa (ReLU/Pruning), 3 khối phần cứng khai thác và đánh đổi kiến trúc [Chen 2016, Jouppi 2017]",
           size=7.5, fill="#64748B")

    card_y = 48
    card_h = 420

    # ==========================================================================
    # CỘT TRÁI: PANEL A - NGUỒN DỮ LIỆU THƯA (SPARSITY SOURCES)
    # ==========================================================================
    x_a = 18
    w_a = 246
    rect(f, x_a, card_y, w_a, card_h, fill="#F8FAFC", stroke="#64748B", sw=1.2, rx=6)
    rect(f, x_a, card_y, w_a, 32, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=6)
    rect(f, x_a + 8, card_y + 6, 5, 20, fill=BLUE, stroke=BLUE, sw=1, rx=2)
    f.text(x_a + 18, card_y + 13, "A. Nguồn Dữ liệu Thưa (Sparsity)", size=9.6, weight=700, fill="#0F172A")
    f.text(x_a + 18, card_y + 24, "Hai nguồn phát sinh số 0 trong suy luận", size=6.8, fill="#475569")

    # A1. Activation Sparsity (ReLU)
    y_a1 = 86
    h_a1 = 134
    rect(f, x_a + 6, y_a1, w_a - 12, h_a1, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_a + 6, y_a1, w_a - 12, 16, fill="#EFF6FF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_a + 12, y_a1 + 8, "1. Activation Sparsity (Hàm kích hoạt)", size=7.2, weight=700, fill="#1E40AF")

    f.text(x_a + 12, y_a1 + 24, "ReLU biến toàn bộ giá trị âm thành 0:", size=6.8, fill="#334155")
    f.text(x_a + 12, y_a1 + 36, "f(x) = max(0, x)", size=6.8, mono=True, weight=700, fill="#1E40AF")

    # 1D Vector Trước ReLU (5 cells)
    vec_vals_pre = ["-1.4", "+0.7", "-0.8", "+2.3", "-0.5"]
    vec_is_pos = [False, True, False, True, False]
    cell_w, cell_h = 42, 15
    start_vx = x_a + 10
    vy_pre = y_a1 + 46
    for i in range(5):
        cx = start_vx + i * 45
        c_fill = "#ECFDF5" if vec_is_pos[i] else "#F1F5F9"
        c_strk = "#10B981" if vec_is_pos[i] else "#94A3B8"
        c_txt = "#047857" if vec_is_pos[i] else "#64748B"
        rect(f, cx, vy_pre, cell_w, cell_h, fill=c_fill, stroke=c_strk, sw=0.8, rx=2)
        f.text(cx + cell_w / 2, vy_pre + cell_h / 2, vec_vals_pre[i], size=6.6, mono=True, weight=700 if vec_is_pos[i] else 400, fill=c_txt, anchor="middle")

    # Arrow down ReLU
    arrow(f, x_a + w_a / 2 - 20, vy_pre + cell_h + 1, x_a + w_a / 2 - 20, vy_pre + cell_h + 16, color=BLUE, sw=1.2)
    f.text(x_a + w_a / 2 - 12, vy_pre + cell_h + 8.5, "ReLU -> biến âm thành 0", size=6.6, weight=700, fill=BLUE)

    # 1D Vector Sau ReLU
    vec_vals_post = ["0.0", "+0.7", "0.0", "+2.3", "0.0"]
    vy_post = vy_pre + cell_h + 18
    for i in range(5):
        cx = start_vx + i * 45
        c_fill = "#ECFDF5" if vec_is_pos[i] else "#FEF2F2"
        c_strk = "#10B981" if vec_is_pos[i] else "#EF4444"
        c_txt = "#047857" if vec_is_pos[i] else "#DC2626"
        rect(f, cx, vy_post, cell_w, cell_h, fill=c_fill, stroke=c_strk, sw=0.8, rx=2)
        f.text(cx + cell_w / 2, vy_post + cell_h / 2, vec_vals_post[i], size=6.6, mono=True, weight=700, fill=c_txt, anchor="middle")

    # Badge thực nghiệm Cnvlutin
    by_a1 = vy_post + cell_h + 6
    rect(f, x_a + 10, by_a1, w_a - 20, 26, fill="#FEF2F2", stroke="#FCA5A5", sw=0.8, rx=3)
    f.text(x_a + 14, by_a1 + 7, "• Cnvlutin: 44% activation bằng 0", size=6.8, weight=700, fill="#991B1B")
    f.text(x_a + 14, by_a1 + 18, "  (do ReLU biến âm thành 0) [Jouppi 2017]", size=6.6, fill="#7F1D1D")

    # A2. Weight Sparsity (Pruning)
    y_a2 = 226
    h_a2 = 136
    rect(f, x_a + 6, y_a2, w_a - 12, h_a2, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_a + 6, y_a2, w_a - 12, 16, fill="#F0FDF4", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_a + 12, y_a2 + 8, "2. Weight Sparsity (Cắt tỉa trọng số)", size=7.2, weight=700, fill="#047857")

    f.text(x_a + 12, y_a2 + 24, "Lọc bỏ trọng số nhỏ (|w| < ngưỡng theta):", size=6.8, fill="#334155")

    # 3x3 Dense Kernel vs 3x3 Pruned Kernel
    kw, kh = 22, 13
    kx0 = x_a + 18
    ky0 = y_a2 + 34
    dense_k = [["+0.9", "-0.1", "+0.4"],
               ["-0.0", "+1.8", "+0.0"],
               ["+0.3", "-0.0", "-1.2"]]
    pruned_k = [["+0.9", " 0  ", "+0.4"],
                [" 0  ", "+1.8", " 0  "],
                ["+0.3", " 0  ", "-1.2"]]
    is_zero = [[False, True, False],
               [True, False, True],
               [False, True, False]]

    for r in range(3):
        for c in range(3):
            rx = kx0 + c * (kw + 2)
            ry = ky0 + r * (kh + 2)
            rect(f, rx, ry, kw, kh, fill="#F8FAFC", stroke="#94A3B8", sw=0.7, rx=1)
            f.text(rx + kw / 2, ry + kh / 2, dense_k[r][c], size=6.6, mono=True, fill=DARK, anchor="middle")

    # Arrow Pruning
    arrow(f, kx0 + 3 * (kw + 2) + 4, ky0 + kh * 1.5 + 2, kx0 + 3 * (kw + 2) + 26, ky0 + kh * 1.5 + 2, color=GREEN, sw=1.2)
    f.text(kx0 + 3 * (kw + 2) + 15, ky0 + kh * 1.5 - 6, "Prune", size=6.6, weight=700, fill=GREEN, anchor="middle")

    kx1 = kx0 + 3 * (kw + 2) + 32
    for r in range(3):
        for c in range(3):
            rx = kx1 + c * (kw + 2)
            ry = ky0 + r * (kh + 2)
            z = is_zero[r][c]
            c_fill = "#FEF2F2" if z else "#ECFDF5"
            c_strk = "#EF4444" if z else "#10B981"
            c_txt = "#DC2626" if z else "#047857"
            rect(f, rx, ry, kw, kh, fill=c_fill, stroke=c_strk, sw=0.7, rx=1)
            f.text(rx + kw / 2, ry + kh / 2, pruned_k[r][c], size=6.6, mono=True, weight=700 if z else 400, fill=c_txt, anchor="middle")

    f.text(kx0 + 12, ky0 + 3 * (kh + 2) + 8, "Ma trận Dense", size=6.6, fill="#64748B")
    f.text(kx1 + 10, ky0 + 3 * (kh + 2) + 8, "Ma trận Sparse (Thưa)", size=6.6, weight=700, fill="#047857")

    # Badge thực nghiệm EIE
    by_a2 = y_a2 + 94
    rect(f, x_a + 10, by_a2, w_a - 20, 36, fill="#ECFDF5", stroke="#34D399", sw=0.8, rx=3)
    f.text(x_a + 14, by_a2 + 8, "• EIE: giảm trọng số ~10 lần nhờ pruning,", size=6.8, weight=700, fill="#065F46")
    f.text(x_a + 14, by_a2 + 19, "  kết hợp mã hóa Huffman nén [Jouppi 2017]", size=6.6, fill="#047857")
    f.text(x_a + 14, by_a2 + 29, "  (áp dụng trên AlexNet / VGG-16)", size=6.6, italic=True, fill="#059669")

    # A3. Tóm tắt bản chất số 0
    y_a3 = 368
    h_a3 = 94
    rect(f, x_a + 6, y_a3, w_a - 12, h_a3, fill="#FFFBEB", stroke="#F59E0B", sw=0.8, rx=4)
    f.text(x_a + 12, y_a3 + 11, "Đặc tính đại số của số 0 trong MAC:", size=7.0, weight=700, fill="#92400E")
    f.text(x_a + 12, y_a3 + 26, "• Tích số: 0 x W = 0  hoặc  A x 0 = 0", size=6.8, fill="#78350F")
    f.text(x_a + 12, y_a3 + 40, "• Tích lũy: Psum_mới = Psum_cũ + 0 = Psum_cũ", size=6.8, fill="#78350F")
    f.text(x_a + 12, y_a3 + 55, "=> Bỏ qua MAC không làm đổi kết quả!", size=6.8, weight=700, fill="#B45309")
    f.text(x_a + 12, y_a3 + 74, "Lưu ý: Tỷ lệ 0 của YOLO cụ thể là unknown", size=6.6, italic=True, fill="#92400E")

    # ==========================================================================
    # CỘT GIỮA: PANEL B - 3 KHỐI PHẦN CỨNG KHAI THÁC SPARSITY (CHEN 2016)
    # ==========================================================================
    x_b = 270
    w_b = 318
    rect(f, x_b, card_y, w_b, card_h, fill="#F8FAFC", stroke="#2563EB", sw=1.3, rx=6)
    rect(f, x_b, card_y, w_b, 32, fill="#EFF6FF", stroke="#2563EB", sw=1.0, rx=6)
    rect(f, x_b + 8, card_y + 6, 5, 20, fill=BLUE, stroke=BLUE, sw=1, rx=2)
    f.text(x_b + 18, card_y + 13, "B. 3 Khối Phần cứng Khai thác Sparsity", size=9.6, weight=700, fill="#1E40AF")
    f.text(x_b + 18, card_y + 24, "Vi kiến trúc nhận diện, bỏ qua và nén dữ liệu [Chen 2016]", size=6.8, fill="#475569")

    # B1. Zero Detector
    y_b1 = 86
    h_b1 = 78
    rect(f, x_b + 6, y_b1, w_b - 12, h_b1, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_b + 6, y_b1, w_b - 12, 16, fill="#EFF6FF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_b + 12, y_b1 + 8, "1. Zero Detector (Mạch nhận biết số 0)", size=7.2, weight=700, fill="#1E40AF")

    # Datapath box
    rect(f, x_b + 12, y_b1 + 26, 58, 24, fill="#EFF6FF", stroke=BLUE, sw=1.0, rx=2)
    f.text(x_b + 41, y_b1 + 33, "Feature A", size=6.6, weight=700, fill="#1E40AF", anchor="middle")
    f.text(x_b + 41, y_b1 + 43, "(hoặc W)", size=6.6, fill="#475569", anchor="middle")

    arrow(f, x_b + 70, y_b1 + 38, x_b + 88, y_b1 + 38, color=BLUE, sw=1.2)

    rect(f, x_b + 88, y_b1 + 24, 102, 28, fill="#F8FAFC", stroke=DARK, sw=1.0, rx=3)
    f.text(x_b + 139, y_b1 + 33, "Zero Detector", size=6.8, weight=700, fill=DARK, anchor="middle")
    f.text(x_b + 139, y_b1 + 44, "So sánh A == 0 ?", size=6.6, fill="#2563EB", anchor="middle")

    arrow(f, x_b + 190, y_b1 + 31, x_b + 214, y_b1 + 31, color=GREEN, sw=1.2)
    rect(f, x_b + 214, y_b1 + 22, 88, 16, fill="#ECFDF5", stroke=GREEN, sw=0.8, rx=2)
    f.text(x_b + 258, y_b1 + 30, "!=0: Thực thi MAC", size=6.6, weight=700, fill="#047857", anchor="middle")

    arrow(f, x_b + 190, y_b1 + 45, x_b + 214, y_b1 + 45, color=RED, sw=1.2, dashed=True)
    rect(f, x_b + 214, y_b1 + 39, 88, 16, fill="#FEF2F2", stroke=RED, sw=0.8, rx=2)
    f.text(x_b + 258, y_b1 + 47, "==0: Bỏ qua / Gate", size=6.6, weight=700, fill="#B91C1C", anchor="middle")

    f.text(x_b + 12, y_b1 + 65, "Kiểm tra bit dữ liệu trước khi phát lệnh đọc bộ nhớ và cấp xung clock", size=6.6, fill="#475569")

    # B2. Zero-skipping & ALU Clock Gating
    y_b2 = 170
    h_b2 = 144
    rect(f, x_b + 6, y_b2, w_b - 12, h_b2, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_b + 6, y_b2, w_b - 12, 16, fill="#ECFDF5", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_b + 12, y_b2 + 8, "2. Zero-skipping Execution & Clock Gating", size=7.2, weight=700, fill="#047857")

    # Flow 1 (Thực thi khi != 0)
    y_fl1 = y_b2 + 24
    rect(f, x_b + 12, y_fl1, 74, 20, fill="#EFF6FF", stroke=BLUE, sw=0.9, rx=2)
    f.text(x_b + 49, y_fl1 + 10, "Nạp W từ RF", size=6.6, fill="#1E40AF", anchor="middle")
    arrow(f, x_b + 86, y_fl1 + 10, x_b + 104, y_fl1 + 10, color=BLUE, sw=1.1)

    rect(f, x_b + 104, y_fl1, 84, 20, fill="#ECFDF5", stroke=GREEN, sw=0.9, rx=2)
    f.text(x_b + 146, y_fl1 + 10, "ALU MAC (* +)", size=6.6, weight=700, fill="#047857", anchor="middle")
    arrow(f, x_b + 188, y_fl1 + 10, x_b + 206, y_fl1 + 10, color=GREEN, sw=1.1)

    rect(f, x_b + 206, y_fl1, 94, 20, fill="#DCFCE7", stroke=GREEN, sw=0.9, rx=2)
    f.text(x_b + 253, y_fl1 + 10, "Psum += A * W", size=6.6, mono=True, weight=700, fill="#047857", anchor="middle")

    # Flow 2 (Bỏ qua khi == 0)
    y_fl2 = y_b2 + 50
    rect(f, x_b + 12, y_fl2, 74, 20, fill="#FEF2F2", stroke=RED, sw=0.9, rx=2)
    f.text(x_b + 49, y_fl2 + 10, "Skip nạp W", size=6.6, weight=700, fill="#B91C1C", anchor="middle")
    arrow(f, x_b + 86, y_fl2 + 10, x_b + 104, y_fl2 + 10, color=RED, sw=1.1, dashed=True)

    rect(f, x_b + 104, y_fl2, 84, 20, fill="#FEF2F2", stroke=RED, sw=0.9, rx=2)
    f.text(x_b + 146, y_fl2 + 10, "Clock Gating ALU", size=6.6, weight=700, fill="#B91C1C", anchor="middle")
    arrow(f, x_b + 188, y_fl2 + 10, x_b + 206, y_fl2 + 10, color=GRAY, sw=1.1)

    rect(f, x_b + 206, y_fl2, 94, 20, fill="#F8FAFC", stroke=GRAY, sw=0.9, rx=2)
    f.text(x_b + 253, y_fl2 + 10, "Psum giữ nguyên", size=6.6, fill="#64748B", anchor="middle")

    # Card lợi ích cốt lõi
    by_b2 = y_b2 + 76
    rect(f, x_b + 10, by_b2, w_b - 20, 58, fill="#F0FDF4", stroke="#22C55E", sw=0.8, rx=3)
    f.text(x_b + 14, by_b2 + 8, "Hai lợi ích phần cứng theo Chen 2016 tr.7:", size=6.8, weight=700, fill="#15803D")
    f.text(x_b + 14, by_b2 + 20, "1. Memory Skip: Chỉ đọc dữ liệu khác 0, tránh nạp W thừa", size=6.6, fill="#166534")
    f.text(x_b + 14, by_b2 + 32, "2. MAC Gating: Tắt xung clock ALU khi nhân 0, triệt tiêu", size=6.6, fill="#166534")
    f.text(x_b + 14, by_b2 + 45, "   công suất chuyển mạch động (P_dyn = alpha * C * V^2 * f)", size=6.6, mono=True, fill="#14532D")

    # B3. Sparse Data Compression (RLE)
    y_b3 = 320
    h_b3 = 142
    rect(f, x_b + 6, y_b3, w_b - 12, h_b3, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_b + 6, y_b3, w_b - 12, 16, fill="#FFFBEB", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_b + 12, y_b3 + 8, "3. Sparse Data Compression (Mã hóa RLE)", size=7.2, weight=700, fill="#92400E")

    f.text(x_b + 12, y_b3 + 24, "Dữ liệu thưa chưa nén (8 phần tử = 8 giá trị):", size=6.6, fill="#475569")

    # Uncompressed stream cells
    stream_vals = ["0", "0", "+5", "0", "0", "0", "0", "-3"]
    stream_zeros = [True, True, False, True, True, True, True, False]
    sw_cell = 34
    sx0 = x_b + 14
    sy_raw = y_b3 + 34
    for i in range(8):
        cx = sx0 + i * 36
        z = stream_zeros[i]
        c_fill = "#FEF2F2" if z else "#EFF6FF"
        c_strk = "#EF4444" if z else "#3B82F6"
        c_txt = "#DC2626" if z else "#1D4ED8"
        rect(f, cx, sy_raw, sw_cell, 15, fill=c_fill, stroke=c_strk, sw=0.8, rx=2)
        f.text(cx + sw_cell / 2, sy_raw + 7.5, stream_vals[i], size=6.6, mono=True, weight=700 if not z else 400, fill=c_txt, anchor="middle")

    # Arrow Down to RLE
    arrow(f, x_b + w_b / 2 - 20, sy_raw + 16, x_b + w_b / 2 - 20, sy_raw + 31, color=AMBER, sw=1.2)
    f.text(x_b + w_b / 2 - 12, sy_raw + 23.5, "Mã hóa Run-Length (RLE)", size=6.6, weight=700, fill="#D97706")

    # Compressed RLE Packets
    sy_rle = sy_raw + 33
    rect(f, x_b + 24, sy_rle, 126, 17, fill="#ECFDF5", stroke=GREEN, sw=0.8, rx=2)
    f.text(x_b + 87, sy_rle + 8.5, "(run=2 zeros, val=+5)", size=6.6, mono=True, fill="#047857", anchor="middle")

    rect(f, x_b + 158, sy_rle, 126, 17, fill="#ECFDF5", stroke=GREEN, sw=0.8, rx=2)
    f.text(x_b + 221, sy_rle + 8.5, "(run=4 zeros, val=-3)", size=6.6, mono=True, fill="#047857", anchor="middle")

    # Note tác dụng nén
    by_b3 = sy_rle + 22
    rect(f, x_b + 10, by_b3, w_b - 20, 36, fill="#FFFBEB", stroke="#F59E0B", sw=0.8, rx=3)
    f.text(x_b + 14, by_b3 + 8, "Tác dụng nén phần cứng [Chen 2016 tr.7, Jouppi 2017 tr.14]:", size=6.8, weight=700, fill="#92400E")
    f.text(x_b + 14, by_b3 + 19, "• Giảm dung lượng SRAM và DRAM cần lưu trữ", size=6.6, fill="#78350F")
    f.text(x_b + 14, by_b3 + 29, "• Giảm lưu lượng truyền qua mạng NoC / bus kết nối", size=6.6, fill="#78350F")

    # ==========================================================================
    # CỘT PHẢI: PANEL C - SO SÁNH KIẾN TRÚC & ĐÁNH ĐỔI HIỆU NĂNG
    # ==========================================================================
    x_c = 596
    w_c = 266
    rect(f, x_c, card_y, w_c, card_h, fill="#F8FAFC", stroke="#64748B", sw=1.2, rx=6)
    rect(f, x_c, card_y, w_c, 32, fill="#FFFFFF", stroke="#64748B", sw=1.0, rx=6)
    rect(f, x_c + 8, card_y + 6, 5, 20, fill="#7C3AED", stroke="#7C3AED", rx=2)
    f.text(x_c + 18, card_y + 13, "C. So sánh Kiến trúc & Đánh đổi", size=9.6, weight=700, fill="#4C1D95")
    f.text(x_c + 18, card_y + 24, "TPU vs Eyeriss vs RK3588 & Giới hạn [Jouppi, TRM]", size=6.8, fill="#475569")

    # C1. 3 Hướng Tiếp cận Kiến trúc
    y_c1 = 86
    h_c1 = 186
    rect(f, x_c + 6, y_c1, w_c - 12, h_c1, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_c + 6, y_c1, w_c - 12, 16, fill="#F5F3FF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_c + 12, y_c1 + 8, "1. 3 Hướng Tiếp cận Kiến trúc", size=7.2, weight=700, fill="#6D28D9")

    # Item TPU
    rect(f, x_c + 10, y_c1 + 20, w_c - 20, 42, fill="#FEF2F2", stroke="#EF4444", sw=0.8, rx=3)
    f.text(x_c + 14, y_c1 + 29, "Google TPU v1: Bỏ qua Sparsity", size=6.8, weight=700, fill="#B91C1C")
    f.text(x_c + 14, y_c1 + 40, "'Omitted for time-to-deploy reasons' [Jouppi tr.3]", size=6.6, italic=True, fill="#7F1D1D")
    f.text(x_c + 14, y_c1 + 51, "Ma trận dày, tính đủ 0xW, thông lượng cố định", size=6.6, fill="#475569")

    # Item Eyeriss
    rect(f, x_c + 10, y_c1 + 66, w_c - 20, 42, fill="#ECFDF5", stroke="#10B981", sw=0.8, rx=3)
    f.text(x_c + 14, y_c1 + 75, "MIT Eyeriss: Khai thác toàn diện", size=6.8, weight=700, fill="#047857")
    f.text(x_c + 14, y_c1 + 86, "Tích hợp RLE + Zero-gating + Skip MAC", size=6.6, fill="#065F46")
    f.text(x_c + 14, y_c1 + 97, "Tiết kiệm năng lượng PE và giảm lưu lượng NoC", size=6.6, fill="#047857")

    # Item RK3588
    rect(f, x_c + 10, y_c1 + 112, w_c - 20, 68, fill="#EFF6FF", stroke="#3B82F6", sw=0.8, rx=3)
    f.text(x_c + 14, y_c1 + 121, "Rockchip RK3588: CNA FC Zero-skipping", size=6.8, weight=700, fill="#1D4ED8")
    f.text(x_c + 14, y_c1 + 132, "'Feature=0 -> weight is not fetched' [TRM1 tr.2006]", size=6.6, italic=True, fill="#1E40AF")
    f.text(x_c + 14, y_c1 + 144, "Bật qua cna_fc_con0/1/2, conv_mode=3, bypass BS", size=6.6, fill="#475569")
    f.text(x_c + 14, y_c1 + 157, "[Unknown]: MAC array có clock gating hay không", size=6.6, weight=700, fill="#B91C1C")
    f.text(x_c + 14, y_c1 + 169, "(TRM không khẳng định bỏ phép nhân trong lõi)", size=6.6, fill="#64748B")

    # C2. Đánh đổi Hiệu năng & Tốc độ Tăng tốc
    y_c2 = 278
    h_c2 = 184
    rect(f, x_c + 6, y_c2, w_c - 12, h_c2, fill="#FFFFFF", stroke="#CBD5E1", sw=1.0, rx=4)
    rect(f, x_c + 6, y_c2, w_c - 12, 16, fill="#F5F3FF", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_c + 12, y_c2 + 8, "2. Tốc độ Tăng tốc: Lý thuyết vs Thực tế", size=7.2, weight=700, fill="#6D28D9")

    # Công thức toán học
    rect(f, x_c + 10, y_c2 + 20, w_c - 20, 32, fill="#F5F3FF", stroke="#8B5CF6", sw=0.8, rx=3)
    f.text(x_c + 14, y_c2 + 29, "Công thức Speedup lý thuyết (z = tỷ lệ zero):", size=6.6, fill="#5B21B6")
    f.text(x_c + w_c / 2, y_c2 + 42, "Speedup = 1 / (1 - z)", size=7.2, weight=700, fill="#6D28D9", anchor="middle")

    # Số liệu định lượng Cnvlutin
    rect(f, x_c + 10, y_c2 + 56, w_c - 20, 46, fill="#F8FAFC", stroke="#CBD5E1", sw=0.8, rx=3)
    f.text(x_c + 14, y_c2 + 66, "Với z = 44% (Cnvlutin [Jouppi 2017]):", size=6.6, weight=700, fill="#334155")
    f.text(x_c + 14, y_c2 + 78, "• Lý thuyết tối đa: 1 / (1 - 0.44) = 1.79x", size=6.6, fill="#1E40AF")
    f.text(x_c + 14, y_c2 + 90, "• Thực tế Cnvlutin: đạt trung bình 1.40x", size=6.6, weight=700, fill="#D97706")

    # Lý do chênh lệch (Hardware Overhead)
    f.text(x_c + 12, y_c2 + 112, "Lý do thực tế thấp hơn (Overhead phần cứng):", size=6.6, weight=700, fill="#475569")
    f.text(x_c + 12, y_c2 + 124, "• Chi phí trễ nhận diện số 0 và giải nén RLE", size=6.6, fill="#64748B")
    f.text(x_c + 12, y_c2 + 136, "• Mất cân bằng tải (workload imbalance) giữa PE", size=6.6, fill="#64748B")

    # Kết luận vàng
    rect(f, x_c + 10, y_c2 + 146, w_c - 20, 32, fill="#FFFBEB", stroke="#F59E0B", sw=0.8, rx=3)
    f.text(x_c + 14, y_c2 + 156, "Kết luận: Bỏ qua 0 chỉ có lợi khi phần cứng", size=6.6, weight=700, fill="#B45309")
    f.text(x_c + 14, y_c2 + 168, "được thiết kế cho nó và dữ liệu đủ thưa!", size=6.6, weight=700, fill="#B45309")

    # Dòng nguồn đáy trang
    source(f, card_y + card_h + 10, "Nguồn: T2 Chen 2016 tr.7 (Eyeriss Sparsity & RLE); T2 Jouppi 2017 tr.3, tr.14 (TPU Dense, Cnvlutin, EIE); T1 TRM1 tr.2006, tr.2055 (RK3588 CNA).")

    return f


# ==============================================================================
# HAM RUN
# ==============================================================================
if __name__ == "__main__":
    os.makedirs(DEFAULT_OUTDIR, exist_ok=True)
    figures = [
        ("npu-01-pe-mac-structure", fig_pe_mac_structure),
        ("npu-02-dataflow-comparison", fig_dataflow_comparison),
        ("npu-03-sparsity-zero-skipping", fig_sparsity_zero_skipping),
    ]
    run(figures, DEFAULT_OUTDIR)

