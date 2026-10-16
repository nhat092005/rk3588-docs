#!/usr/bin/env python3
"""Phan 0 Tong quan: Hinh 0.1 (ban do khoi) va 0.2 (duong di model).

Sources: see chu-thich.md, table Nguon (opening questions of parts 1-10 and the decision log; for Hinh 0.2 the rows
already verified in parts 2, 4, 5, 6, 7, 9).
Usage: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THICK, THIN, Fig, run, source  # noqa: E402

W = 900
T1F, T2F, T3F, DEC = "#EAF2FF", "#EAF6EA", "#FDECEC", "#EEEEEE"


def wrap(s, px, size):
    """Greedy wrap by approximate glyph width (0.5 em per char)."""
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if len(t) * size * 0.5 > px and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def blk(f, x, y, w, h, lines, size=12.5, fill="white", weight=700, mono=False):
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="#333333" stroke-width="1.2"/>')
    top = y + h / 2 - (len(lines) - 1) * (size + 3) / 2
    for i, ln in enumerate(lines):
        f.text(x + w / 2, top + i * (size + 3), ln, size=size, weight=weight, anchor="middle", mono=mono)


# =====================================================================
# Hinh 0.1
# =====================================================================
NODES = {
    1: ("NPU cơ bản", "T2", ["tính convolution bằng những đơn vị nào;", "vì sao cách giữ và di chuyển dữ liệu quan trọng hơn số phép nhân"], "Hình 1.1 đến 1.5", "không"),
    2: ("Phần cứng RK3588", "T1", ["gồm những khối nào, nối với SoC bằng đường nào"], "Hình 2.1 đến 2.5", "1"),
    3: ("Lý thuyết lượng tử", "T2", ["biến thành số nguyên INT8 như thế nào, sai số đến từ đâu"], "Hình 3.1 đến 3.5", "không"),
    4: ("Lượng tử RKNN", "T1", ["cho chọn những kiểu, thuật toán, phương pháp lượng tử nào, làm sao tìm lớp gây sai số"], "Hình 4.1 đến 4.4", "3"),
    5: ("Toolchain", "T1", ["phải gọi những hàm nào ở đâu;", "phần mềm trên board xếp thành những tầng nào"], "Hình 5.1 đến 5.3", "4"),
    6: ("Compiler và op", "T1", ["chạy trên NPU RK3588 hay rơi sang CPU, có được ghép với op đứng trước và chia cho ba core không"], "Hình 6.1 đến 6.4", "2"),
    7: ("Bộ nhớ và hiệu năng", "T1", ["nằm ở những bộ nhớ nào, một con số độ trễ đo đoạn nào của một frame"], "Hình 7.1 đến 7.3", "2"),
    8: ("Thiết kế model", "MIX", ["tiêu chí nào đã có nguồn T1 (vendor), T2 (paper) hoặc T3;", "điều gì vẫn là unknown trên RK3588"], "Hình 8.1, 8.2", "3 (Hình 3.5), 6 (Hình 6.3)"),
    9: ("YOLO", "T1", ["YOLOv8n và YOLO26n khác nhau ở khối nào, mỗi khối đi qua đường xuất RKNN thành lớp nào trên NPU RK3588"], "Hình 9.1 đến 9.4", "4, 5, 6"),
}
FILL = {"T1": T1F, "T2": T2F, "T3": T3F}
LAB = {"T1": "T1 RK3588", "T2": "T2 chung", "T3": "T3 đo"}


def node(f, n, x, y, w=260, h=142):
    name, tier, q, figs, need = NODES[n]
    if tier == "MIX":
        f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{T2F}" stroke="#333333" stroke-width="1.4"/>')
        f.a(f'<path d="M{x + w / 2} {y + 1} H{x + w - 6} Q{x + w} {y} {x + w} {y + 6} V{y + h - 6} Q{x + w} {y + h} '
            f'{x + w - 6} {y + h - 1} H{x + w / 2} Z" fill="{T1F}"/>')
        f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="none" stroke="#333333" stroke-width="1.4"/>')
    else:
        f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{FILL[tier]}" stroke="#333333" '
            f'stroke-width="1.4"/>')
    f.text(x + 10, y + 16, f"Phần {n}: {name}", size=14.5, weight=700)
    yy = y + 38
    for part in q:
        for ln in wrap(part, w - 22, 12):
            f.text(x + 10, yy, ln, size=12, fill=INK)
            yy += 15
    f.text(x + 10, y + h - 40, f"cần biết trước: {need}", size=11.5, fill=DARK, italic=True)
    f.text(x + 10, y + h - 20, figs, size=12.5, weight=700, fill=BLUE)
    if tier == "MIX":
        f.tier(x + w - 160, y + h - 31, "T2 chung")
        f.tier(x + w - 84, y + h - 31, "T1 RK3588")
    else:
        w2 = 14 + 7.4 * len(LAB[tier])
        f.tier(x + w - w2 - 8, y + h - 31, LAB[tier])


def fig_map():
    f = Fig(W, 1200)
    f.text(10, 20, "Bản đồ đường học: mỗi ô là một phần, mũi tên là cần biết trước", size=16, weight=700)
    f.tier(808, 8, "T1 RK3588") if False else None
    X = [10, 320, 630]
    R0, R1, R2 = 50, 232, 414
    node(f, 1, X[0], R0)
    node(f, 3, X[1], R0)
    node(f, 8, X[2], R0)
    node(f, 2, X[0], R1)
    node(f, 4, X[1], R1)
    node(f, 5, X[2], R1)
    node(f, 7, X[0], R2)
    node(f, 6, X[1], R2)
    node(f, 9, X[2], R2)
    h = 142
    # arrows (prerequisite)
    f.line([(140, R0 + h), (140, R1)], BLUE)
    f.line([(450, R0 + h), (450, R1)], BLUE)
    f.line([(580, R0 + 70), (630, R0 + 70)], BLUE)           # 3 -> 8
    f.line([(580, R1 + 70), (630, R1 + 70)], BLUE)           # 4 -> 5
    f.line([(140, R1 + h), (140, R2)], BLUE)                 # 2 -> 7
    f.line([(270, R1 + 105), (320, R2 + 40)], BLUE)          # 2 -> 6
    f.line([(580, R1 + 115), (630, R2 + 30)], BLUE)          # 4 -> 9
    f.line([(760, R1 + h), (760, R2)], BLUE)                 # 5 -> 9
    f.line([(580, R2 + 85), (630, R2 + 85)], BLUE)           # 6 -> 9
    # part 10 (T3) and 11 (decision)
    R3, R4 = 592, 770
    f.a(f'<rect x="10" y="{R3}" width="880" height="140" rx="6" fill="{T3F}" stroke="{RED}" stroke-width="1.8"/>')
    f.text(20, R3 + 16, "Phần 10: Số đo thực tế", size=14.5, weight=700)
    for i, ln in enumerate(wrap("những điều ở phần cứng và API (phần 2) có thấy được trong số đo thật trên board RK3588S không, "
                                "và số đo nào đủ chắc để kết luận. Mỗi biểu đồ có câu dự đoán trước khi xem và link hai chiều với hình khái niệm.",
                                840, 12)):
        f.text(20, R3 + 38 + 15 * i, ln, size=12)
    f.text(20, R3 + 80, "cần biết trước: Phần 1 đến 9 (mũi tên từ 7 và 9; các phần còn lại cung cấp khái niệm cho từng hình)",
           size=11.5, fill=DARK, italic=True)
    f.text(20, R3 + 120, "Hình 10.1 đến 10.8", size=12.5, weight=700, fill=BLUE)
    f.tier(890 - 8 - 14 - 7.4 * 5, R3 + 109, "T3 đo")
    f.line([(140, R2 + h), (140, R3)], BLUE)
    f.line([(760, R2 + h), (760, R3)], BLUE)
    f.line([(450, R3 + 140), (450, R4)], BLUE, THICK)
    f.a(f'<rect x="10" y="{R4}" width="880" height="170" rx="6" fill="{DEC}" stroke="{INK}" stroke-width="2.4"/>')
    f.text(20, R4 + 17, "Phần 11: Chọn model (câu hỏi của dự án)", size=15, weight=700)
    f.text(20, R4 + 42, "Chọn YOLOv8n SiLU, YOLOv8n ReLU hay YOLO26n cho NPU RK3588?", size=16, weight=700, fill=INK)
    for i, ln in enumerate(wrap("Quy tắc chốt trước khi có số: chọn model nhanh nhất có mAP50-95 INT8 không thấp hơn "
                                "YOLOv8n SiLU INT8 quá 1.0 điểm; nếu không model nào nhanh hơn rõ ràng thì giữ YOLOv8n SiLU "
                                "(tmp/02_decisions/2026-10-11_model-selection-rule.md).", 840, 12.5)):
        f.text(20, R4 + 68 + 16 * i, ln, size=12.5)
    f.text(20, R4 + 112, "Hình 11.1, 11.2 (phần này chưa có chu-thich.md)", size=12.5, weight=700, fill=BLUE)
    f.text(20, R4 + 150, "cần biết trước: Phần 10 (và qua nó Phần 1 đến 9)", size=11.5, fill=DARK, italic=True)
    f.text(20, R4 + 132, "loại: quyết định (không phải khái niệm hay số đo)", size=11.5, fill=DARK, italic=True)

    # bottom: legend, how to study, unknown
    yb = R4 + 170 + 14
    y = f.legend(10, yb, 430, [
        ("blue", "mũi tên: cần biết trước (suy ra của bộ hình)"),
        ("fill:" + T2F, "T2 chung: paper, không riêng RK3588"),
        ("fill:" + T1F, "T1 RK3588: vendor, mã nguồn chính thức"),
        ("fill:" + T3F, "T3 đo: log của chúng ta"),
        ("fill:" + DEC, "quyết định: quy tắc chọn model"),
    ])
    y2 = f.textbox(460, yb, 430, [
        "Cách học",
        "1. Đi theo mũi tên: học phần có mũi tên tới trước.",
        "2. Mỗi hình có huy hiệu tier (T1, T2, T3).",
        "3. Khung nét đứt đỏ là unknown: nguồn không cho.",
        "4. Phần 10: dự đoán trước khi xem hình.",
        "5. Tích ô \"đã học\" trong trang HTML (index.html).",
    ], size=12.5)
    y3 = f.unknown(10, max(y, y2) + 12, [
        "mAP50-95 INT8 của cả ba model: chưa có (chờ pipeline phase3, phase4), nên",
        "chưa có câu trả lời cho Phần 11; Hình 10.7 và 10.8 chờ số."], w=880)
    source(f, y3 + 8, "Nguồn: câu hỏi mở đầu trong REPO docs/tools/visual_guide/npu_rk3588/NN-*/chu-thich.md; "
           "tmp/02_decisions/2026-10-11_model-selection-rule.md; 2026-10-11_hoc-theo-hinh.md.")
    return f


# =====================================================================
# Hinh 0.2
# =====================================================================
LX, MX, RX, RW = 10, 160, 575, 305


def band(f, y, h, label, sub, explain, wrong):
    f.layer(LX, y, 880, h, [label, sub], side=False) if False else None
    f.a(f'<rect x="{LX}" y="{y}" width="880" height="{h}" rx="8" fill="#F5F5F5" stroke="#666666" stroke-width="1.2"/>')
    f.text(LX + 12, y + 18, label, size=14.5, weight=700, fill="#333333")
    for i, ln in enumerate(wrap(sub, 120, 12)):
        f.text(LX + 12, y + 38 + 15 * i, ln, size=12, fill=DARK)
    # right panel
    f.a(f'<rect x="{RX}" y="{y + 8}" width="{RW}" height="{h - 16}" rx="5" fill="white" stroke="#999999"/>')
    yy = y + 22
    f.text(RX + 8, yy, "Giải thích ở:", size=12.5, weight=700, fill=BLUE)
    for ln in wrap(explain, RW - 100, 12.5):
        f.text(RX + 92, yy, ln, size=12.5, fill=BLUE)
        yy += 15
    yy += 5
    f.text(RX + 8, yy, "Có thể sai:", size=12.5, weight=700, fill=RED)
    yy += 16
    for item in wrong:
        lines = wrap(item, RW - 26, 12)
        f.text(RX + 8, yy, "-", size=12)
        for ln in lines:
            f.text(RX + 18, yy, ln, size=12)
            yy += 14.5
        yy += 3
    assert yy <= y + h - 6, (label, yy, y + h)


def fig_path():
    f = Fig(W, 1300)
    f.tier(808, 8, "T1 RK3588")
    f.tier(716, 8, "T3 đo")
    f.text(10, 20, "Đường đi của một model qua cả ngăn xếp, từ best.pt đến NPU", size=16, weight=700)
    y1, h1 = 44, 150
    y2, h2 = y1 + h1 + 30, 232
    y3, h3 = y2 + h2 + 30, 160
    y4, h4 = y3 + h3 + 30, 150
    y5, h5 = y4 + h4 + 30, 192
    # ---- 1 PC: Ultralytics
    band(f, y1, h1, "1. PC: Ultralytics", "export ra ONNX",
         "Hình 9.3 (đường xuất), 9.1, 9.2 (khối YOLO)",
         ["ONNX đưa vào toolkit khác ONNX của format=onnx: YOLOv8n Concat 17 thành 18, Slice 2 thành 4, "
          "Div 1 thành 2 vì _NormalizeCoords (Hình 9.3)."])
    blk(f, MX, y1 + 14, 150, 44, ["best.pt", "(weights/best.pt)"], size=12.5)
    f.line([(MX + 150, y1 + 36), (MX + 195, y1 + 36)], BLUE)
    blk(f, MX + 195, y1 + 14, 150, 44, ["ONNX", "YOLO(...).export"], size=12.5)
    f.text(MX + 355, y1 + 28, "format rknn,", size=11.5, fill=DARK)
    f.text(MX + 355, y1 + 44, "quantize 8", size=11.5, fill=DARK)
    for i, ln in enumerate(["opset = min(opset or 19, 19); onnxslim.slim; end2end tắt",
                            "_NormalizeCoords bọc đầu ra (mã Ultralytics) khi format rknn, quantize 8"]):
        f.text(MX, y1 + 78 + 17 * i, ln, size=12)
    f.text(MX, y1 + 78 + 34, "(ONNX này bị xóa sau khi build INT8: đồ thị chứa tọa độ đã chuẩn hóa)", size=11.5, fill=DARK, italic=True)
    # ---- 2 PC: toolkit
    band(f, y2, h2, "2. PC: toolkit", "RKNN-Toolkit2: ONNX sang RKNN INT8",
         "Hình 5.1 (chuỗi API), 4.1 (kiểu lượng tử), 6.1 (op), 6.3 (fusion)",
         ["Sai số lượng tử hóa: bước sau chỉ đúng khi simulator đúng; tìm lớp gây sai số bằng accuracy analysis (Hình 4.3).",
          "Op chạy ngoài NPU: YOLOv8n INT8 chỉ Transpose (cùng InputOperator, OutputOperator) có Target = CPU (Hình 6.1, T3).",
          "Không đặt target_platform: model chỉ chạy được trên RK3566/RK3568 (Hình 5.1)."])
    names = ["config", "load_onnx", "build", "export_rknn"]
    for i, nm in enumerate(names):
        x = MX + i * 104
        blk(f, x, y2 + 14, 88, 34, [nm], size=12.5, mono=True)
        if i < 3:
            f.line([(x + 88, y2 + 31), (x + 104, y2 + 31)], BLUE)
    lines = ["config: target_platform='rk3588'; quantized_dtype không truyền, mặc định w8a8",
             "load_onnx: model là đường dẫn .onnx",
             "build: do_quantization (mặc định True) và dataset hiệu chỉnh lượng tử (calibration)",
             "export_rknn: lưu model ra file .rknn"]
    for i, ln in enumerate(lines):
        f.text(MX, y2 + 70 + 18 * i, ln, size=12)
    f.text(MX, y2 + 70 + 18 * 4 + 6, "Thứ tự Configuration, Loading, Building, Export theo UG232 tr.9;", size=11.5, fill=DARK, italic=True)
    f.text(MX, y2 + 70 + 18 * 4 + 22, "w8a8 mặc định là suy ra của bộ hình (config của Ultralytics không có quantized_dtype).", size=11.5, fill=DARK, italic=True)
    # ---- 3 board runtime
    band(f, y3, h3, "3. Board: runtime", "Python hoặc C",
         "Hình 5.2 (ba cách chạy), 5.3 (ngăn xếp board), 2.4 (core_mask)",
         ["Phiên bản RKNN Server, Runtime library và RKNN-Toolkit2 phải khớp; log của ta: librknnrt 2.3.0 với toolkit 2.3.2 là nguyên nhân lỗi kết nối (Hình 5.2, T3)."])
    blk(f, MX, y3 + 14, 195, 38, ["RKNN-Toolkit-Lite2 (Python)"], size=12.5)
    blk(f, MX + 205, y3 + 14, 195, 38, ["RKNPU2 C API"], size=12.5)
    f.line([(MX + 97, y3 + 52), (MX + 97, y3 + 72)], BLUE)
    f.line([(MX + 302, y3 + 52), (MX + 302, y3 + 72)], BLUE)
    blk(f, MX, y3 + 74, 400, 36, ["librknnrt.so (RKNPU2 Runtime)"], size=13)
    f.text(MX, y3 + 128, "core_mask: AUTO, CORE_0, CORE_1, CORE_2, CORE_0_1, CORE_0_1_2", size=12, mono=True)
    # ---- 4 driver
    band(f, y4, h4, "4. Kernel: driver", "rknpu 0.9.8",
         "Hình 5.3 (driver), 2.4 (chọn core), 2.5 (một job)",
         ["core_mask ngoài 0x1, 0x2, 0x4, 0x3, 0x7 (và AUTO = 0x0) làm driver báo lỗi Unknown core mask (Hình 2.4)."])
    labs = [["node", "renderD129"], ["ioctl", "SUBMIT"], ["job theo", "core_mask"], ["ghi thanh ghi,", "nhận ngắt"]]
    for i, lb in enumerate(labs):
        x = MX + i * 104
        blk(f, x, y4 + 14, 88, 46, lb, size=11.5)
        if i < 3:
            f.line([(x + 88, y4 + 37), (x + 104, y4 + 37)], BLUE)
    f.text(MX, y4 + 82, "AUTO (0x0): chọn core có task_num nhỏ nhất, job chạy trên 1 core", size=12)
    f.text(MX, y4 + 100, "driver trên board đọc được từ node version: v0.9.8 (T3)", size=12)
    # ---- 5 NPU + DDR
    band(f, y5, h5, "5. Phần cứng: NPU", "3 core, DDR",
         "Hình 2.1 (NPU trong SoC), 2.2 (trong core), 2.3 (số liệu), 7.1 (đường dữ liệu)",
         ["SiLU không chia nhiều core: cả 57 lớp ConvExSwish chạy 100%/0%/0% khi CORE_0_1_2 (Hình 6.3, 10.3, T3).",
          "SRAM của SoC chưa dùng cho NPU trên board này: kernel CONFIG_ROCKCHIP_RKNPU_SRAM not set (Hình 7.1, T3)."])
    f.a(f'<rect x="{MX}" y="{y5 + 14}" width="300" height="104" rx="6" fill="white" stroke="#333333" stroke-width="1.4"/>')
    f.text(MX + 10, y5 + 30, "NPU: 3 core, mỗi core gồm", size=13, weight=700)
    mini = ["CNA", "MAC array", "DPU", "PPU"]
    for i, nm in enumerate(mini):
        x = MX + 10 + i * 71
        blk(f, x, y5 + 46, 62, 34, [nm], size=10.5 if len(nm) > 4 else 12.5)
        if i < 3:
            f.line([(x + 62, y5 + 63), (x + 71, y5 + 63)], BLUE)
    f.text(MX + 10, y5 + 98, "buffer 384KB mỗi core (nằm trong core)", size=12)
    blk(f, MX + 340, y5 + 30, 60, 62, ["DDR"], size=14)
    f.line([(MX + 300, y5 + 52), (MX + 340, y5 + 52)], BLUE)
    f.line([(MX + 340, y5 + 70), (MX + 300, y5 + 70)], BLUE)
    f.text(MX + 320, y5 + 38, "AXI", size=11.5, anchor="middle", fill=BLUE)
    # stage arrows
    ax = MX + 200
    for (ya, yb_, lab) in [(y1 + h1, y2, "file .onnx"), (y2 + h2, y3, "file .rknn"),
                           (y3 + h3, y4, "librknnrt mở /dev/dri/renderD129"), (y4 + h4, y5, "ghi thanh ghi, ngắt")]:
        f.line([(ax, ya + 1), (ax, yb_ - 1)], BLUE, THICK)
        f.text(ax + 12, (ya + yb_) / 2, lab, size=12, fill=BLUE, halo="white")
    y = y5 + h5 + 14
    ye = f.legend(10, y, 430, [
        ("blue", "đường đi của model và dữ liệu, từ trên xuống"),
        ("fill:#FFFFFF", "Giải thích ở: hình khái niệm của bộ hình"),
        ("fill:#FFFFFF", "Có thể sai: điểm đã có nguồn T1 hoặc số đo T3"),
    ])
    y3u = f.unknown(460, y, [
        "librknnrt gọi ioctl nào theo thứ tự nào;",
        "vai trò của MCU_NPU với một job NPU;",
        "đường nối NPU tới system SRAM.",
    ], w=430)
    source(f, max(ye, y3u) + 8, "Nguồn: ULT exporter.py, engine.py, rknn.py; API232 tr.7-15; UG232 tr.9-173; QS232 tr.15; HDR; DRV; TRM1 tr.1984-1985; TRM2 tr.16; OPL tr.63; LOG.")
    return f


if __name__ == "__main__":
    run([("h0-1-ban-do-khoi", fig_map), ("h0-2-duong-di-model", fig_path)], os.path.dirname(os.path.abspath(__file__)))
