"""Ghi chú chuyên đề: Hiệu năng NPU RK3588, Độ trễ và Lượng tử hóa (05-hieu-nang-npu).

Sinh 2 hình chất lượng cao chuẩn visual_guide:
  - hp-1-latency-pipeline-va-da-loi (T2 chung): Pipeline độ trễ, FPS đơn luồng vs Đa luồng và Kiến trúc 3-core NPU
  - hp-2-flops-mac-tops-va-nghich-ly-bo-nho (T2 chung): Định lượng FLOPs, MACs, TOPS và Nghịch lý bộ nhớ trên NPU RK3588

Chạy: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# 4 cấp thư mục: 05-hieu-nang-npu -> _notes -> 00-tong-quan -> npu_rk3588 -> docs/tools/visual_guide
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "..", "..")))
from figlib import BLUE, DARK, GREEN, INK, RED, Fig, run, source  # noqa: E402

W = 900
CALC = "#EAF2FF"      # Nền khối tính toán / số học
ORANGE = "#E65100"
PURPLE = "#7B1FA2"
TEAL = "#00796B"
GRAY_BG = "#F5F5F5"


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
# HÌNH P.1: PIPELINE ĐỘ TRỄ VÀ ĐA LÕI NPU (hp-1-latency-pipeline-va-da-loi)
# ==============================================================================
def fig_latency_pipeline():
    f = Fig(W, 640)
    tier(f, "T2 chung")
    f.text(10, 24, "Pipeline Độ trễ, FPS Đơn luồng so với Đa luồng và Kiến trúc 3-Core NPU", size=16, weight=700, fill=DARK)

    # ---- PHẦN A: PIPELINE ĐỘ TRỄ ĐẦU-CUỐI ----
    f.text(10, 56, "A. Pipeline độ trễ đầu-cuối (End-to-End Latency) của một khung hình", size=13.5, weight=700, fill=DARK)

    # Vẽ 3 khối Pipeline liên hoàn
    box_w = 265
    box_h = 95
    y_p = 72

    # 1. Pre-processing
    rect(f, 10, y_p, box_w, box_h, fill="#F0F7FF", stroke=BLUE, sw=1.5, rx=5)
    f.text(10 + box_w / 2, y_p + 18, "1. Pre-processing (T_pre)", size=12, weight=700, fill=BLUE, anchor="middle")
    f.text(10 + box_w / 2, y_p + 34, "Phần cứng: CPU (ARM Cortex) / RGA", size=10.5, weight=600, fill="#555555", anchor="middle")
    txt(f, 20, y_p + 52, [
        [("• Decode frame, Letterbox về 640x640", "t")],
        [("• Đổi màu BGR -> RGB, scale 1/255, int8", "t")],
    ], size=11, dy=16)

    # Mũi tên 1 -> 2
    f.a(f'<polygon points="282,{y_p+47} 292,{y_p+47} 289,{y_p+42} 297,{y_p+47} 289,{y_p+52} 292,{y_p+47}" fill="{DARK}" stroke="{DARK}" stroke-width="2"/>')

    # 2. NPU Inference
    rect(f, 305, y_p, box_w, box_h, fill="#F1F8E9", stroke=GREEN, sw=1.5, rx=5)
    f.text(305 + box_w / 2, y_p + 18, "2. NPU Inference (T_npu)", size=12, weight=700, fill=GREEN, anchor="middle")
    f.text(305 + box_w / 2, y_p + 34, "Phần cứng: RK3588 NPU (3 Cores)", size=10.5, weight=600, fill="#555555", anchor="middle")
    txt(f, 315, y_p + 52, [
        [("• DMA đưa tensor vào SRAM nội bộ NPU", "t")],
        [("• Mảng MAC tính chập Conv, kích hoạt", "t")],
    ], size=11, dy=16)

    # Mũi tên 2 -> 3
    f.a(f'<polygon points="577,{y_p+47} 587,{y_p+47} 584,{y_p+42} 592,{y_p+47} 584,{y_p+52} 587,{y_p+47}" fill="{DARK}" stroke="{DARK}" stroke-width="2"/>')

    # 3. Post-processing
    rect(f, 600, y_p, box_w + 25, box_h, fill="#FFF8E1", stroke=ORANGE, sw=1.5, rx=5)
    f.text(600 + (box_w + 25) / 2, y_p + 18, "3. Post-processing (T_post)", size=12, weight=700, fill=ORANGE, anchor="middle")
    f.text(600 + (box_w + 25) / 2, y_p + 34, "Phần cứng: CPU (ARM Cortex)", size=10.5, weight=600, fill="#555555", anchor="middle")
    txt(f, 610, y_p + 52, [
        [("• Giải mã hộp DFL, khôi phục toạ độ box", "t")],
        [("• Lọc ngưỡng tin cậy, thuật toán NMS", "t")],
    ], size=11, dy=16)

    # Khung công thức tổng hợp
    y_f = y_p + box_h + 10
    rect(f, 10, y_f, W - 20, 48, fill=CALC, stroke="#90CAF9", sw=1.2, rx=4)
    txt(f, 20, y_f + 14, [
        [("Tổng độ trễ chu trình: ", "b"), ("T_E2E = T_pre + T_npu + T_post", "b"), ("  |  ", "t"),
         ("FPS độ trễ (1 camera đơn luồng): ", "b"), ("FPS_latency = 1000 / T_E2E_mean", "t"),
         (" [ai/automation/tables.py:288]", "i")],
        [("Lưu ý: ", "b"), ("Đo riêng lẻ NPU chỉ phản ánh T_npu. Trải nghiệm hệ thống video thời gian thực phụ thuộc toàn bộ T_E2E.", "t")],
    ], size=11.5, dy=17)

    # ---- PHẦN B: KIẾN TRÚC 3 LÕI VÀ CORE_MASK ----
    y_b = y_f + 64
    f.text(10, y_b, "B. Cấu trúc 3 lõi NPU RK3588 và hành vi lập lịch core_mask", size=13.5, weight=700, fill=DARK)

    # Vẽ 3 Core Blocks
    cw = 270
    ch = 95
    y_core = y_b + 14

    cores = [
        ("NPU Core 0 (0x1)", "Mặc định ở core_mask=AUTO", "#E3F2FD", BLUE,
         "• Gánh toàn bộ lớp nếu model có op",
         "  không chia lõi (như ConvExSwish)"),
        ("NPU Core 1 (0x2)", "Lõi mở rộng 1", "#EDE7F6", PURPLE,
         "• Hoạt động khi đặt CORE_0_1_2 trên",
         "  model ReLU hoặc chạy context riêng"),
        ("NPU Core 2 (0x4)", "Lõi mở rộng 2", "#E0F2F1", TEAL,
         "• Hoạt động khi đặt CORE_0_1_2 trên",
         "  model ReLU hoặc chạy context riêng"),
    ]

    for i, (cname, csub, cbg, cstroke, ln1, ln2) in enumerate(cores):
        cx = 10 + i * (cw + 25)
        rect(f, cx, y_core, cw, ch, fill=cbg, stroke=cstroke, sw=1.5, rx=5)
        f.text(cx + cw / 2, y_core + 16, cname, size=12, weight=700, fill=cstroke, anchor="middle")
        f.text(cx + cw / 2, y_core + 31, csub, size=10, weight=600, fill="#666666", anchor="middle")
        txt(f, cx + 12, y_core + 48, [
            [(ln1, "t")],
            [(ln2, "t")],
        ], size=11, dy=16)

    # ---- PHẦN C: BẢNG SO SÁNH CHẾ ĐỘ THỰC THI ----
    y_c = y_core + ch + 18
    f.text(10, y_c, "C. So sánh chế độ thực thi: Đơn luồng tuần tự vs Đa luồng Throughput (3 Contexts)", size=13.5, weight=700, fill=DARK)

    y_tab = f.table(10, y_c + 12, [175, 145, 150, 410], ["Chế độ triển khai", "Thiết lập core_mask", "Số NPU Core dùng", "Đặc tính hiệu năng & Ứng dụng"], [
        ["Đơn luồng tuần tự (SiLU)", "AUTO (0x1)", "Chỉ Core 0 (100%)", "Xử lý 1 camera, T_npu ~21 ms; 2 lõi còn lại nghỉ (ConvExSwish không chia lõi)"],
        ["Đơn luồng đa lõi (ReLU)", "CORE_0_1_2 (0x7)", "Cả 3 Core (~35/34/32%)", "Toán tử ConvRelu chia đều 3 lõi; T_npu giảm ~35% xuống ~13.9 ms"],
        ["Đa luồng song song (3 Luồng)", "3 Contexts riêng biệt", "Core 0, Core 1, Core 2", "3 camera song song; Thông lượng tăng xấp xỉ gấp 3 (Throughput FPS)"],
    ], size=11.5, line_h=15)

    source(f, y_tab + 8, "Nguồn: REPO ai/automation/tables.py:288, 325; LOG 2026-10-10_yolo-phaseA/README.md:22; LOG 2026-10-10_t3-board-silu-resize/README.md:74.")
    return f


# ==============================================================================
# HÌNH P.2: FLOPs, MACs, TOPS VÀ NGHỊCH LÝ BỘ NHỚ (hp-2-flops-mac-tops-va-nghich-ly-bo-nho)
# ==============================================================================
def fig_flops_roofline():
    f = Fig(W, 830)
    tier(f, "T2 chung")
    f.text(10, 24, "Định lượng FLOPs, MACs, TOPS và Nghịch lý Bộ nhớ (Memory-Bound) trên NPU RK3588", size=15.5, weight=700, fill=DARK)

    # ---- PHẦN A: BẢN CHẤT TOÁN HỌC: 1 MAC = 2 FLOPS ----
    ya = 50
    f.text(10, ya, "A. Bản chất toán học: Quy đổi 1 MAC = 2 FLOPs trong phép tính mạng nơ-ron", size=13.5, weight=700, fill=DARK)

    ha = 100
    rect(f, 10, ya + 12, W - 20, ha, fill="#F0F7FF", stroke=BLUE, sw=1.4, rx=5)
    f.text(30, ya + 32, "Công thức cốt lõi: 1 phép MAC (Multiply-Accumulate) = 1 Phép nhân + 1 Phép cộng dồn = 2 FLOPs", size=12.5, weight=700, fill=BLUE)

    txt(f, 30, ya + 54, [
        [("• Biểu thức MAC: ", "b"), ("y = y + (w · x)", "c"), ("  ==>  ", "t"), ("Gồm 1 phép nhân (w·x) và 1 phép cộng (+y) = 2 FLOPs.", "t")],
        [("• Phép tính Conv 2D: ", "b"), ("Số MAC = Hout × Wout × Cout × (K² × Cin)", "c")],
        [("  ==> ", "t"), ("FLOPs lý thuyết = 2 × Số MAC = 2 × Hout × Wout × Cout × (K² × Cin)", "b")],
    ], size=11.5, dy=17)

    # Khung ví dụ YOLOv8n bên phải
    rect(f, 540, ya + 22, 330, 80, fill="white", stroke="#90CAF9", sw=1.2, rx=4)
    f.text(550, ya + 40, "Ví dụ thực tế trong YOLOv8n (640×640):", size=11, weight=700, fill=DARK)
    txt(f, 550, ya + 58, [
        [("• Tổng toàn mạng: ", "t"), ("3,006,623 tham số, 8.087 GFLOPs", "b")],
        [("• Riêng lớp Detect: ", "t"), ("2.965 GFLOPs (chiếm 36.7% toàn mạng)", "c")],
        [("  [LOG 2026-10-10_yolo-arch/out/table_v8n.md]", "i")],
    ], size=10.5, dy=15)

    # ---- PHẦN B: PHÂN BIỆT 3 CHỈ SỐ DỄ NHẦM LẪN ----
    yb = ya + ha + 26
    f.text(10, yb, "B. Phân biệt ba khái niệm dễ gây nhầm lẫn: FLOPs vs FLOPS/TOPS vs Latency", size=13.5, weight=700, fill=DARK)

    cw = 280
    ch = 185
    y_card = yb + 12

    # Card 1: FLOPs
    rect(f, 10, y_card, cw, ch, fill="#E8F5E9", stroke=GREEN, sw=1.4, rx=5)
    f.text(10 + cw / 2, y_card + 20, "1. FLOPs (Khối lượng việc)", size=12.5, weight=700, fill=GREEN, anchor="middle")
    f.text(10 + cw / 2, y_card + 36, "Floating Point Operations (chữ s thường)", size=10, fill="#555555", anchor="middle")
    txt(f, 22, y_card + 56, [
        [("• Bản chất: ", "b"), ("Tổng số phép tính số học lý thuyết cần chạy.", "t")],
        [("• Đơn vị: ", "b"), ("FLOPs, GFLOPs (10⁹), TFLOPs (10¹²).", "t")],
        [("• Ý nghĩa: ", "b"), ("Đo kích thước mô hình (độ phức tạp giải thuật).", "t")],
        [("• Độc lập phần cứng: ", "b"), ("Mô hình giữ nguyên cấu trúc thì FLOPs bất biến.", "t")],
    ], size=11, dy=16)

    # Card 2: FLOPS / TOPS
    rect(f, 310, y_card, cw, ch, fill="#E3F2FD", stroke=BLUE, sw=1.4, rx=5)
    f.text(310 + cw / 2, y_card + 20, "2. FLOPS / TOPS (Tốc độ máy)", size=12.5, weight=700, fill=BLUE, anchor="middle")
    f.text(310 + cw / 2, y_card + 36, "Operations Per Second (chữ S hoa = mỗi giây)", size=10, fill="#555555", anchor="middle")
    txt(f, 322, y_card + 56, [
        [("• Bản chất: ", "b"), ("Năng lực tính toán cực đại của phần cứng/giây.", "t")],
        [("• Đơn vị: ", "b"), ("GFLOPS, TFLOPS, TOPS (Tera Ops/sec).", "t")],
        [("• Thông số RK3588: ", "b"), ("3 Cores, 1024 MACs/core/cycle INT8.", "t")],
        [("• Cực đại công bố: ", "b"), ("\"up to 6TOPs\" INT8 @ 1 GHz [DS tr.7].", "t")],
    ], size=11, dy=16)

    # Card 3: Latency & FPS
    rect(f, 610, y_card, cw, ch, fill="#FFF8E1", stroke=ORANGE, sw=1.4, rx=5)
    f.text(610 + cw / 2, y_card + 20, "3. Latency & FPS (Trải nghiệm thực)", size=12.5, weight=700, fill=ORANGE, anchor="middle")
    f.text(610 + cw / 2, y_card + 36, "Thời gian trễ (ms) và Khung hình/giây", size=10, fill="#555555", anchor="middle")
    txt(f, 622, y_card + 56, [
        [("• Bản chất: ", "b"), ("Thời gian chờ thực tế từ lúc đưa ảnh tới lúc có kết quả.", "t")],
        [("• Phụ thuộc: ", "b"), ("Băng thông bộ nhớ (DDR/SRAM), driver, overhead từng lớp.", "t")],
        [("• Thực tế quyết định: ", "b"), ("Mô hình tối ưu trên chip là mô hình có FPS cao nhất, không", "t")],
        [("  chỉ riêng FLOPs trên giấy!", "t")],
    ], size=11, dy=16)

    # ---- PHẦN C: NGHỊCH LÝ FLOPS VÀ ROOFLINE MODEL ----
    yc = y_card + ch + 20
    f.text(10, yc, "C. Nghịch lý FLOPs và Mô hình Roofline trên NPU RK3588 (Vì sao FLOPs thấp vẫn chạy chậm?)", size=13.5, weight=700, fill=DARK)

    box_paradox_w = 430
    box_paradox_h = 195
    y_para = yc + 12

    # Cột 1: Nghịch lý thực tế YOLO26n vs YOLOv8n
    rect(f, 10, y_para, box_paradox_w, box_paradox_h, fill="#FFEBEE", stroke=RED, sw=1.4, rx=5)
    f.text(10 + box_paradox_w / 2, y_para + 20, "NGHỊCH LÝ THỰC NGHIỆM: YOLO26n vs YOLOV8n", size=12, weight=700, fill=RED, anchor="middle")
    txt(f, 22, y_para + 42, [
        [("• YOLOv8n (Gốc): ", "b"), ("8.087 GFLOPs  ==>  Latency NPU: ", "t"), ("16.14 ms", "b")],
        [("• YOLO26n: ", "b"), ("5.314 GFLOPs (", "t"), ("Giảm 34% FLOPs lý thuyết!", "b"), (")", "t")],
        [("  ==> Latency NPU: ", "t"), ("18.66 ms (Chậm hơn 15% trên RK3588!)", "b")],
        [("• Vì sao nghịch lý xảy ra? ", "b")],
        [("  1. Phân mảnh lớp: YOLO26n có tới ", "t"), ("180 lớp NPU", "b"), (" (so với 116 lớp).", "t")],
        [("     Mỗi lớp nhỏ tốn overhead DMA setup và context switch.", "t")],
        [("  2. Lớp Depthwise 3×3 hiệu suất MAC cực thấp (chỉ ", "t"), ("0.30% - 1.24%", "c"), (")", "t")],
        [("     khiến mảng MAC 32×32 liên tục bị bỏ đói (underutilized).", "t")],
    ], size=10.8, dy=15.5)

    # Cột 2: Giải thích qua Mô hình Roofline
    rect(f, 460, y_para, box_paradox_w, box_paradox_h, fill="#F1F8E9", stroke=GREEN, sw=1.4, rx=5)
    f.text(460 + box_paradox_w / 2, y_para + 20, "CƠ CHẾ KỸ THUẬT: MÔ HÌNH ROOFLINE & MEMORY-BOUND", size=12, weight=700, fill=GREEN, anchor="middle")
    txt(f, 472, y_para + 42, [
        [("• Cường độ tính toán (Arithmetic Intensity): ", "b")],
        [("  Arithmetic Intensity = FLOPs / Byte nạp từ RAM DDR", "c")],
        [("• Hai vùng vận hành của NPU RK3588:", "b")],
        [("  1. Vùng Compute-Bound (Standard Conv, Pointwise 1×1):", "t")],
        [("     Tái sử dụng dữ liệu cao trong CBUF -> Đạt đỉnh 6 TOPS.", "t")],
        [("  2. Vùng Memory-Bound (Depthwise Conv, Resize, Split):", "t")],
        [("     Tính toán quá ít so với lượng byte phải nạp qua bus AXI.", "t")],
        [("     NPU bị nghẽn bus bộ nhớ DDR, dù FLOPs thấp vẫn chờ lâu!", "t")],
        [("• Kết luận: ", "b"), ("Giảm FLOPs bằng cách băm nhỏ lớp thường làm giảm FPS!", "t")],
    ], size=10.8, dy=15.5)

    # ---- LINK BOX T1 RK3588 ----
    y_link = y_para + box_paradox_h + 14
    rect(f, 10, y_link, W - 20, 110, fill="white", stroke=BLUE, sw=1.8, rx=6)
    f.tier(20, y_link + 8, "T1 RK3588")
    f.text(122, y_link + 19, "Liên hệ RK3588: điều nguồn T1 nói và số liệu thực nghiệm", size=13.5, weight=700, fill=DARK)
    txt(f, 24, y_link + 44, [
        [("TRM1 tr.1984: ", "b"), ("NPU RK3588 gồm 3 lõi, cấu hình \"1024x3 integer 8 MAC operations per cycle\".", "t")],
        [("DS tr.7: ", "b"), ("Datasheet công bố năng lực tính toán cực đại đạt \"up to 6TOPs\" ở kiểu dữ liệu INT8.", "t")],
        [("LOG 2026-10-10_yolo-arch/layer_table.py:2: ", "b"), ("GFLOPs tính bằng PyTorch FlopCounterMode (2 FLOPs per MAC).", "t")],
        [("LOG 2026-10-10_yolo-phaseA: ", "b"), ("YOLO26n 5.314 GFLOPs (18.66 ms) chậm hơn YOLOv8n 8.087 GFLOPs (16.14 ms) trên board.", "t")],
    ], size=11, dy=16)

    source(f, y_link + 110 + 8, "Nguồn: TRM1 tr.1984 (RK3588 TRM); DS tr.7 (Datasheet); LOG 2026-10-10_yolo-arch; LOG 2026-10-10_yolo-phaseA.")
    return f


def main():
    figs = [
        ("hp-1-latency-pipeline-va-da-loi", fig_latency_pipeline),
        ("hp-2-flops-mac-tops-va-nghich-ly-bo-nho", fig_flops_roofline),
    ]
    run(figs, HERE)


if __name__ == "__main__":
    main()
