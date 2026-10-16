#!/usr/bin/env python3
"""Phan 2 Phan cung RK3588: Hinh 2.1 den 2.5.

Primary sources (see chu-thich.md, table Nguon): TRM1 (Ch.36 RKNN, Ch.7, address map, IRQ table), TRM2 Ch.1,
Datasheet V0.1, UG152, API232, SRAM usage md, rknpu driver 0.9.8 (DRV), rk3588s.dtsi (DTS), BAMB (arithmetic convention).

Usage: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from figlib import BLUE, DARK, GRAY, INK, RED, THIN, Fig, run, source  # noqa: E402

W = 900
UNK_FILL = "#FFF3F3"


def tier(f):
    f.tier(808, 8, "T1 RK3588")


def card(f, x, y, w, h, title, lines, size=12, title_size=15, dashed=False):
    """White box: bold title then plain lines (all centred)."""
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="white" stroke="#333333" '
        f'stroke-width="1.2"{dash}/>')
    f.text(x + w / 2, y + 17, title, size=title_size, weight=700, anchor="middle")
    for i, ln in enumerate(lines):
        f.text(x + w / 2, y + 38 + 16 * i, ln, size=size, anchor="middle")


def blk(f, x, y, w, h, lines, size=14, fill="white"):
    """Block with bold centred lines (used for block-diagram boxes)."""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="#333333" stroke-width="1.2"/>')
    top = y + h / 2 - (len(lines) - 1) * (size + 3) / 2
    for i, ln in enumerate(lines):
        f.text(x + w / 2, top + i * (size + 3), ln, size=size, weight=700, anchor="middle")


def panel(f, x, y, w, lines, fill="white", stroke="#999999", size=12.5, dashed=False):
    h = 14 + 19 * len(lines)
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="1"{dash}/>')
    for i, ln in enumerate(lines):
        f.rich(x + 12, y + 16 + 19 * i, ln, size=size)
    return y + h


# =====================================================================
# Hinh 2.1: NPU trong SoC
# =====================================================================
def fig_soc():
    f = Fig(W, 930)
    tier(f)
    # ---- band 1: NPU, three power domains ----
    f.layer(10, 40, 880, 204, ["NPU", "(TRM: RKNN)", "3 core"], side=True)

    def domain(x, w, name):
        f.a(f'<rect x="{x}" y="50" width="{w}" height="186" rx="8" fill="none" stroke="#888888" '
            f'stroke-width="1.2" stroke-dasharray="6 4"/>')
        f.text(x + 10, 62, name, size=13, weight=700, fill=DARK)

    domain(130, 340, "PD_NPUTOP")
    domain(490, 190, "PD_NPU1")
    domain(700, 180, "PD_NPU2")
    card(f, 140, 78, 118, 104, "MCU_NPU", ["16KB cache", "64KB TCM"])
    card(f, 268, 78, 192, 104, "NPU core 0", ["(TRM: RKNN C0)", "FDAB0000, 64KB", "ngắt 142 irq_rknn_c0"])
    card(f, 498, 78, 174, 104, "NPU core 1", ["(TRM: RKNN C1)", "FDAC0000, 64KB", "ngắt 143 irq_rknn_c1"])
    card(f, 708, 78, 164, 104, "NPU core 2", ["(TRM: RKNN C2)", "FDAD0000, 64KB", "ngắt 144 irq_rknn_c2"])
    f.text(140, 200, "cùng domain: PVTM_NPU, PVTPLL_NPU,", size=11.5, fill=DARK)
    f.text(140, 216, "WDT_NPU, TIMER_NPU", size=11.5, fill=DARK)

    # IOMMU (position on the data path not given)
    f.a('<path d="M230 254 L230 244" stroke="#888888" stroke-width="1.2" stroke-dasharray="4 3"/>')
    f.box(130, 254, 200, 42, "IOMMU (rknpu_mmu)", "DTS: iommus = <&rknpu_mmu>", dashed=True,
          title_size=14, sub_size=11.5)
    # ---- band 2: interconnect ----
    f.layer(10, 306, 880, 134, ["Interconnect", "(TRM2 Ch.1)"], side=True)
    f.a('<rect x="130" y="318" width="500" height="112" rx="4" fill="white" stroke="#333333" stroke-width="1.2"/>')
    f.text(380, 334, "SoC interconnect (cross-bar)", size=15, weight=700, anchor="middle")
    f.text(380, 354, "master: CPU, GPU, NPU, VOP, ISP, Other Masters", size=12, anchor="middle", fill=DARK)
    sx = [140, 250, 360, 470]
    for i, x in enumerate(sx):
        f.box(x, 380, 100, 34, f"scheduler{i}", dashed=True, title_size=13)
    for i, ln in enumerate(["4 DDR scheduler tích hợp:", "sắp xếp lại giao dịch", "để tối đa hiệu quả DDR"]):
        f.text(650, 340 + 18 * i, ln, size=12.5)

    # interfaces
    f.line([(372, 246), (372, 316)], BLUE, THIN)
    f.line([(388, 316), (388, 246)], BLUE, THIN)
    f.text(400, 262, "AXI master: lấy dữ liệu từ bộ nhớ", size=12, fill=BLUE)
    f.text(400, 279, "nối vào SoC AXI interconnect", size=12, fill=BLUE)
    f.line([(800, 296), (800, 246)], GRAY, THIN, dashed=True)
    f.text(790, 268, "AHB slave: cấu hình,", size=12, fill=DARK, anchor="end")
    f.text(790, 285, "debug, test", size=12, fill=DARK, anchor="end")

    # ---- band 3: memory ----
    f.layer(10, 452, 880, 164, ["BỘ NHỚ"], side=True)
    for i, x in enumerate(sx):
        f.line([(x + 50, 414), (x + 50, 470)], BLUE, THIN)
        f.box(x, 472, 100, 40, f"DDRCTL{i}", title_size=14)
    card(f, 640, 462, 240, 144, "System SRAM", [
        "SoC có 1MB SRAM, 956KB", "cấp được cho các IP",
        "NPU nhận tối đa 956KB, 4K align",
        "dùng chung với IP khác (codec)",
        "vùng của các IP không được chồng lấn"], size=12)

    # ---- bottom: original + legend + unknown ----
    yb = f.original(10, 632, 400, "../../npu_study/images/02_rk3588_npu_hardware/trm2_p16_fig1-1.png", [
        "TRM2 tr.16, Fig. 1-1 Interconnect Diagram",
        "NPU là một master; scheduler0-3 nối DDRCTL0-3."])
    y = f.legend(450, 632, 440, [
        ("blue", "AXI master: đường dữ liệu"),
        ("gray", "AHB slave: cấu hình (hình TRM không vẽ nơi nối ra)"),
        ("dashedbox", "miền nguồn (power domain) hoặc vị trí chưa rõ"),
    ])
    y = f.unknown(450, y + 12, [
        "vai trò của MCU_NPU với một job NPU;",
        "đường nối NPU tới system SRAM;",
        "vị trí IOMMU trên đường dữ liệu."], w=440)
    source(f, max(yb, y) + 8, "Nguồn: TRM1 tr.1984, 1985, 18, 24, 1091, 1093; TRM2 tr.16; DS tr.8; "
           "SRAM dòng 3, 21, 22; DTS dòng 3478.")
    return f


# =====================================================================
# Hinh 2.2: ben trong mot core
# =====================================================================
def fig_core():
    f = Fig(W, 1060)
    tier(f)
    f.layer(10, 40, 880, 550, ["NPU CORE"])
    blk(f, 40, 72, 560, 46, ["Memory Interface (AXI)"])
    blk(f, 640, 72, 220, 46, ["Register File Fetch"])
    blk(f, 640, 150, 220, 46, ["Register File /", "Interrupt Control"], size=13)
    blk(f, 640, 228, 220, 46, ["Config Interface (AHB)"], size=14)
    f.line([(600, 95), (638, 95)], BLUE)
    f.line([(750, 118), (750, 148)], INK)
    f.line([(750, 228), (750, 198)], INK)

    f.layer(40, 150, 270, 250, ["CNA"])
    blk(f, 54, 192, 118, 50, ["Weight", "Decompress"], size=13)
    blk(f, 190, 192, 110, 50, ["Zero-Skipping"], size=13)
    blk(f, 54, 300, 118, 50, ["Weight Data", "Load"], size=13)
    blk(f, 190, 300, 110, 50, ["Feature Data", "Load"], size=13)
    f.line([(113, 242), (113, 298)], BLUE)
    f.line([(245, 242), (245, 298)], BLUE)
    f.line([(175, 118), (175, 148)], BLUE)

    # DPU, PPU
    f.a('<rect x="335" y="150" width="140" height="230" rx="4" fill="white" stroke="#333333" stroke-width="1.2"/>')
    f.text(405, 168, "DPU", size=15, weight=700, anchor="middle")
    f.text(405, 185, "(Data Process Unit)", size=11, anchor="middle", fill=DARK)
    for i, ln in enumerate(["xử lý từng giá trị", "đơn (single data):", "leaky_relu, relu, relux,",
                            "sigmoid, tanh; ngoài ra:", "softmax, transpose,", "chuyển định dạng", "dữ liệu"]):
        f.text(405, 214 + 17 * i, ln, size=11.5, anchor="middle")
    f.a('<rect x="510" y="150" width="110" height="230" rx="4" fill="white" stroke="#333333" stroke-width="1.2"/>')
    f.text(565, 168, "PPU", size=15, weight=700, anchor="middle")
    f.text(565, 185, "(Planar Process", size=11, anchor="middle", fill=DARK)
    f.text(565, 199, "Unit)", size=11, anchor="middle", fill=DARK)
    for i, ln in enumerate(["hàm planar trên", "đầu ra của DPU:", "average, max,", "min pooling"]):
        f.text(565, 232 + 17 * i, ln, size=11.5, anchor="middle")
    f.line([(375, 118), (375, 148)], BLUE)
    f.line([(445, 148), (445, 120)], BLUE)
    f.line([(545, 118), (545, 148)], BLUE)
    f.line([(590, 148), (590, 120)], BLUE)
    f.line([(475, 265), (508, 265)], BLUE)

    # buffer, sequence controller, MAC, accumulator
    blk(f, 40, 457, 215, 70, ["384KB", "Buffer"], size=15)
    blk(f, 280, 457, 105, 70, ["Sequence", "Controller"], size=14)
    blk(f, 415, 410, 205, 40, ["Accumulator"], size=14)
    blk(f, 415, 470, 205, 44, ["MAC Array"], size=14)
    f.line([(113, 350), (113, 455)], BLUE)
    f.line([(225, 350), (225, 455)], BLUE)
    f.line([(255, 492), (278, 492)], BLUE)
    f.line([(385, 492), (413, 492)], BLUE)
    f.line([(515, 470), (515, 452)], BLUE)
    f.line([(440, 410), (440, 382)], BLUE)
    for n, (bx, by) in enumerate([(298, 163), (52, 469), (292, 469), (427, 482), (427, 422), (347, 163), (522, 163)], 1):
        f.badge(bx, by, str(n))
    f.text(54, 552, "INT8: MAC Array 32x32", size=12.5, fill=DARK)

    # bank panel
    f.a('<rect x="640" y="300" width="240" height="270" rx="6" fill="white" stroke="#999999" stroke-width="1"/>')
    f.text(652, 316, "Buffer chia thành bank", size=14, weight=700)
    f.text(652, 336, "thanh ghi weight_bank, data_bank", size=12, mono=True, fill=DARK)
    for i in range(8):
        f.a(f'<rect x="{652 + 26 * i}" y="352" width="26" height="30" fill="#F5F5F5" stroke="#555555"/>')
        f.text(652 + 26 * i + 13, 367, str(i), size=13, anchor="middle")
    f.text(652, 398, "chỉ số bank trong thanh ghi", size=11.5, fill=DARK)
    f.line([(665, 424), (820, 424)], BLUE)
    f.text(652, 442, "feature: từ bank 0 tăng dần,", size=12)
    f.text(652, 458, "tối đa bank 0-6", size=12)
    f.line([(835, 490), (678, 490)], INK)
    f.text(652, 508, "weight: từ bank 7 giảm dần,", size=12)
    f.text(652, 524, "tối đa bank 1-7", size=12)
    f.text(652, 548, "kích thước một bank: xem unknown", size=11.5, fill=DARK, italic=True)

    # bottom
    yb = f.original(10, 610, 330, "../../npu_study/images/02_rk3588_npu_hardware/trm1_p1985_fig36-2.png", [
        "TRM1 tr.1985, Fig. 36-2 RKNN Single Core", "Architecture"])
    y = f.legend(380, 610, 510, [
        ("blue", "luồng dữ liệu (đọc từ Fig. 36-2)"),
        ("ink", "đường cấu hình và thanh ghi"),
        ("badge", "thứ tự dữ liệu đi qua một core, từ 1 đến 7"),
    ])
    y = f.textbox(380, y + 12, 510, [
        "Zero-Skipping (thanh ghi fc_skip_en): khi feature của một pixel",
        "bằng 0, weight tương ứng không được fetch từ bộ nhớ hệ thống.",
        "TRM 36.3.2: Neural Network Accelerating Engine gồm convolution",
        "pre-process controller, internal buffer, MAC array, accumulator.",
    ], size=12.5)
    y = f.unknown(380, y + 12, [
        "khai triển tên CNA (và BS, BN, CBUF trong tên thanh ghi);",
        "kích thước một bank;",
        "MAC array có bỏ phép nhân 0 hay không (TRM1 tr.2006 chỉ",
        "nói weight không được fetch);",
        "định dạng nén weight mà Weight Decompress hỗ trợ."], w=510)
    source(f, max(yb, y) + 8, "Nguồn: TRM1 tr.1984, 1985, 1986, 2001, 2004, 2006 (Fig. 36-2 và thanh ghi).")
    return f


# =====================================================================
# Hinh 2.3: bang so
# =====================================================================
def fig_numbers():
    f = Fig(W, 900)
    tier(f)
    LB, RB = "#EAF2FF", "#EAF6EA"
    f.text(10, 50, "MAC mỗi chu kỳ (TRM1 tr.1984)", size=15, weight=700)
    f.table(10, 64, [70, 290, 90], ["Kiểu số", "Nguyên văn TRM", "Tổng (x3)"], [
        ["INT8", "1024x3 integer 8 MAC operations per cycle", "3072"],
        ["INT16", "512x3 integer 16 MAC operations per cycle", "1536"],
        ["FP16", "512x3 float 16 MAC operations per cycle", "1536"],
        ["BF16", "512x3 bfloat 16 MAC operations per cycle", "1536"],
        ["TF32", "256x3 tf32 MAC operation per cycle", "768"],
        ["INT4", "2048x3 integer 4 MAC operation per cycle", "6144"],
    ])
    f.text(10, 262, "x3 khớp với 3 core (TRM không viết 'per core'). Cột Tổng là phép nhân của bộ hình.",
           size=12, fill=DARK, italic=True)

    f.text(10, 296, "Trong SDK: rknn.config, quantized_dtype (API232 tr.7)", size=15, weight=700)
    f.table(10, 310, [130, 320], ["quantized_dtype", "Giới hạn chip ghi trong tài liệu"], [
        [C("w8a8"), "mặc định; RK2118 không hỗ trợ"],
        [C("w4a16"), "Only RK3576/RV1126B"],
        [C("w8a16"), "Only RK3562"],
        [C("w4a8"), "Not supported yet"],
        [C("w16a16i"), "Only RV1103/RV1106"],
        [C("w16a16i_dfp"), "Only RV1103/RV1106"],
    ])
    f.text(10, 512, "Với RK3588 chỉ w8a8 không bị giới hạn sang chip khác: INT4, BF16, TF32 có trong TRM", size=12.5)
    f.text(10, 530, "nhưng không có đường qua rknn.config (suy ra của bộ hình từ danh sách trên).", size=12.5)
    f.text(10, 550, "Ngoại lệ: Matmul C API hỗ trợ int4, int8, float16 (UG232 tr.41).", size=12.5, fill=DARK)

    f.text(480, 50, "Cấu trúc theo số", size=15, weight=700)
    f.table(480, 64, [190, 220], ["Mục", "Giá trị"], [
        ["INT8: MAC array", "32x32 (nn_mode = 3'd0), TRM1 tr.2001"],
        ["INT8: kernel group", "32 kernel / group, TRM1 tr.2000"],
        ["INT16, FP16: kernel group", "16 kernel / group, TRM1 tr.2000"],
        ["Buffer trong core", "384KB x3, TRM1 tr.1984"],
        ["System SRAM cho NPU", "tối đa 956KB, 4K align"],
    ], size=12)
    f.text(480, 244, "Tần số và 6 TOPS", size=15, weight=700)
    f.table(480, 258, [190, 220], ["Mục", "Giá trị"], [
        ["Datasheet: Max NPU frequency", "TBD (DS tr.31)"],
        ["Datasheet: tốc độ tính", "up to 6TOPs (DS tr.7)"],
        ["DTS OPP \"RK3588 npu\"", "300, 400 ... 1000 MHz"],
        ["DTS OPP \"RK3588J/M\"", "tối đa 950 MHz"],
    ], size=12)
    y = panel(f, 480, 402, 410, [
        [("Phép tính của bộ hình, không phải câu của vendor:", "b")],
        "1024 x 3 x 2 x 1 GHz = 6.144 TOPS (INT8, 3 core)",
        "2 phép/MAC: quy ước của T2 BAMB tr.1 (NXP),",
        "không phải tài liệu vendor.",
        "1 GHz: OPP cao nhất trong DTS; Datasheet ghi TBD.",
    ], fill=LB, stroke=BLUE)
    f.tier(480, y + 16, "T3 đo")
    panel(f, 480, y + 46, 410, [
        "Board RK3588S: eval_perf báo NPU Current Frequency",
        "List là 1000000000 khi đo (fix_freq=True).",
        "Chỉ giá trị có trong file log; các quan sát khác",
        "qua ssh chưa lưu log nên không đưa vào.",
    ], fill=RB, stroke="#2E7D32")

    y = f.legend(10, 670, 880, [
        ("fill:#FFFFFF", "nguyên văn hoặc số lấy từ tài liệu T1"),
        ("fill:" + LB, "phép tính của bộ hình (không phải câu của vendor)"),
        ("fill:" + RB, "T3: đo trên board, có file log"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho"),
    ])
    y = f.unknown(10, y + 12, [
        "quy ước đếm phép tính của vendor cho 6 TOPS;",
        "bố cục MAC array cho INT16, FP16, INT4;",
        "kích thước một bank của buffer 384KB."], w=880)
    source(f, y + 8, "Nguồn: TRM1 tr.1984, 2000, 2001; DS tr.7, 31; API232 tr.7; UG232 tr.41; DTS dòng 3534-3655, "
           "3658-3709; BAMB tr.1; LOG 2026-10-10.")
    return f


# =====================================================================
# Hinh 2.4: da loi va core mask
# =====================================================================
def fig_multicore():
    f = Fig(W, 960)
    tier(f)
    # ---- hardware ----
    f.layer(10, 40, 880, 160, ["PHẦN CỨNG", "TRM1 tr.1984"], side=True)
    for x, t, s in [(140, "Triple core co-work", "ghép ba core"),
                    (395, "Dual core co-work", "ghép hai core"),
                    (650, "Work independently", "mỗi core độc lập")]:
        f.box(x, 56, 230, 58, t, s, title_size=15, sub_size=13)
    f.unknown(140, 130, ["TRM liệt kê 5 giá trị nn_mode (32x32, 64x32, 96x32, 32x64, 32x96) và không gắn giá trị nào với dual hay triple;",
                         "cách chia việc giữa các core."], w=740)

    # ---- API ----
    f.layer(10, 214, 880, 232, ["API", "UG152 tr.26, 27"], side=True)
    f.table(140, 228, [200, 290], ["rknn_core_mask", "Ý nghĩa (UG152 tr.26)"], [
        [C("RKNN_NPU_CORE_AUTO"), "chọn core đang rảnh trong NPU"],
        [C("RKNN_NPU_CORE_0"), "chạy trên NPU0"],
        [C("RKNN_NPU_CORE_1"), "chạy trên NPU1"],
        [C("RKNN_NPU_CORE_2"), "chạy trên NPU2"],
        [C("RKNN_NPU_CORE_0_1"), "NPU0 và NPU1 cùng lúc"],
        [C("RKNN_NPU_CORE_0_1_2"), "NPU0, NPU1, NPU2 cùng lúc"],
    ])
    y = f.textbox(650, 228, 230, [
        [("Nhanh hơn khi nhiều core", "b")],
        [("(CORE_0_1, CORE_0_1_2):", "t")],
        "Conv, DepthwiseConvolution,",
        "Add, Concat, Relu, Clip,",
        "Relu6, ThresholdedRelu,",
        "Prelu, LeakyRelu",
    ], size=12.5)
    f.a(f'<rect x="650" y="{y + 10}" width="230" height="46" rx="6" fill="#F5F5F5" stroke="#999999"/>')
    f.text(765, y + 27, "Op khác: fallback về Core0", size=13, weight=700, anchor="middle")
    f.text(765, y + 45, "Số đo: Hình 10.3", size=12.5, anchor="middle", fill=BLUE)

    # ---- driver ----
    f.layer(10, 460, 880, 288, ["DRIVER", "rknpu 0.9.8"], side=True)
    cards = [
        ("1. Userspace gửi job", ["core_mask và", "subcore_task[5]:", "mỗi phần tử gồm", "task_start, task_number"]),
        ("2. Chọn core", ["mask hợp lệ: 0x1 0x2 0x4", "0x3 0x7 (khác: báo lỗi)", "AUTO = 0x0: core có", "task_num nhỏ nhất;", "hòa: core số nhỏ; chạy 1 core"]),
        ("3. Hàng đợi", ["mỗi core có todo_list", "riêng; job nhiều core", "vào hàng đợi của", "từng core được chọn"]),
        ("4. Commit xuống HW", ["khi mọi core của job", "đã lấy job (run_count", "về 0); xong khi", "interrupt_count về 0"]),
    ]
    xs = [140, 328, 516, 704]
    for (t, ls), x in zip(cards, xs):
        card(f, x, 476, 176, 124, t, ls, size=11.5, title_size=14)
    for x in xs[:-1]:
        f.line([(x + 176, 538), (x + 188, 538)], BLUE)
    y = f.textbox(140, 616, 740, [
        "Phần việc theo core do userspace gửi sẵn: với 1 hoặc 2 core, task của core i lấy từ subcore_task[i];",
        "với 3 core, lấy từ subcore_task[i + 2]. Chỉ rknpu_job.c đọc subcore_task, để lấy task_start và task_number.",
    ], size=12.5)
    f.unknown(140, y + 10, ["cách userspace chia việc của một job giữa các core (không gian, kênh hay batch);",
                            "vì sao op ngoài danh sách của UG152 tr.27 chạy về Core0."], w=740)

    y = f.legend(10, 766, 880, [
        ("blue", "thứ tự xử lý một job trong driver"),
        ("fill:#F5F5F5", "ba tầng theo nguồn: phần cứng (TRM), API (UG152), driver (mã nguồn)"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho"),
    ])
    source(f, y + 8, "Nguồn: TRM1 tr.1984; UG152 tr.26, 27; rknpu_job.c, rknpu_job.h, rknpu_ioctl.h (rknpu 0.9.8).")
    return f


# =====================================================================
# Hinh 2.5: mot job
# =====================================================================
def fig_job():
    f = Fig(W, 1190)
    tier(f)
    X0, X1, X2 = 150, 450, 750
    f.lifelines([(X0, "Phần mềm", "host"), (X1, "Bộ nhớ hệ thống", "danh sách thanh ghi"),
                 (X2, "NPU", "PC, Register File Fetch, CNA...")], 40, 818,
                phases=[(112, 150, "Giai đoạn 1. PC mode: chuẩn bị trong bộ nhớ hệ thống"),
                        (272, 210, "Giai đoạn 2. Host ghi thanh ghi PC (AHB slave), rồi bắt đầu"),
                        (492, 190, "Giai đoạn 3. NPU tự lấy cấu hình qua AXI"),
                        (692, 126, "Giai đoạn 4. Kết thúc")], bw=210, bh=56)
    f.msg(X0, X1, 168, BLUE, "khởi tạo thông tin thanh ghi", "Initial register information in system memory", num="1")
    f.note(190, 198, 500, [
        "mỗi thanh ghi 64 bit: [63:48] block đích, [47:16] giá trị, [15:0] offset",
        "op_en đặt cuối danh sách (TRM khuyến nghị mạnh)",
    ], size=12.5)
    f.msg(X0, X2, 328, BLUE, "ghi pc_interrupt_clear, pc_interrupt_mask", "", num="2", above_code=True)
    f.msg(X0, X2, 384, BLUE, "ghi pc_amount, pc_addr, pc_task_number, pc_task_dma_base", "", num="3", above_code=True)
    f.msg(X0, X2, 440, BLUE, "ghi pc_op_enable", "bắt đầu một nhóm task", num="4", above_code=True)
    f.msg(X2, X1, 548, BLUE, "đọc danh sách thanh ghi qua AXI", "AXI DMA, pc_sel = 0 (PC mode)", num="5")
    f.msg(X1, X2, 604, GRAY, "các mục 64 bit", "ghi vào block đích (CNA, CORE, DPU, PPU...)", num="6", dashed=True)
    f.note(560, 632, 320, [
        "ping-pong: cấu hình group 0 khi đang dùng group 1,",
        "và ngược lại (ghi S_POINTER để bật)",
    ], size=12)
    f.msg(X2, X0, 748, INK, "3 tín hiệu ngắt", "giữ nguyên cho đến khi host xóa", num="7")
    f.msg(X0, X2, 796, BLUE, "xóa ngắt", "pc_interrupt_clear", num="8", above_code=False)

    f.text(10, 842, "Sự kiện ngắt: 17 sự kiện, TRM mô tả bit 0 đến 13 (PC_INTERRUPT_MASK)", size=14.5, weight=700)
    f.table(10, 856, [90, 420, 370], ["Bit", "Sự kiện", "Ghi chú"], [
        ["0 đến 5", "CNA: feature, weight, csc (mỗi loại group 0 và 1)", ""],
        ["6, 7", "CORE group 0, group 1", ""],
        ["8, 9", "DPU group 0, group 1", ""],
        ["10, 11", "PPU group 0, group 1", ""],
        ["12, 13", "DMA read error, DMA write error", ""],
        ["14 đến 16", "TRM không mô tả", "unknown"],
    ], size=12.5, fills={5: UNK_FILL})
    y = f.textbox(10, 1050, 880, [
        [("Slave mode (pc_sel = 1)", "b"), (": CPU ghi thanh ghi trực tiếp qua AHB, không dùng danh sách trong bộ nhớ.", "t")],
    ], size=13)
    y = f.legend(10, y + 12, 880, [
        ("blue", "ghi thanh ghi, đọc danh sách qua AXI"),
        ("gray", "dữ liệu trả về từ bộ nhớ"),
        ("ink", "tín hiệu từ NPU về host"),
        ("badge", "thứ tự bước"),
    ])
    source(f, y + 10, "Nguồn: TRM1 tr.1994, 1995, 2052, 2053 (Fig. 36-3 PC flow).")
    return f


C = lambda s: [(s, "c")]  # noqa: E731

FIGS = [
    ("h2-1-npu-trong-soc", fig_soc),
    ("h2-2-ben-trong-loi", fig_core),
    ("h2-3-bang-so", fig_numbers),
    ("h2-4-da-loi-core-mask", fig_multicore),
    ("h2-5-mot-job", fig_job),
]

if __name__ == "__main__":
    run(FIGS, os.path.dirname(os.path.abspath(__file__)))
