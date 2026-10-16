#!/usr/bin/env python3
"""Phan 4 Luong tu RKNN: Hinh 4.1 den 4.4.

Primary sources (see chu-thich.md, table Nguon): API232 (RKNN-Toolkit2 API Reference 2.3.2), UG232 (RKNN SDK User Guide 2.3.2),
RKNNPY (rknn/api/rknn.py inside the 2.3.2 wheel), official examples of the toolkit (hybrid_quant, accuracy_analysis, onnx/yolov5),
and one T3 log (config() acceptance on PC).

Usage: python3 gen.py [outdir] [figure-name ...]
"""
import os
import sys
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

W = 900
UNK_FILL = "#FFF3F3"
LB = "#EAF2FF"      # phep tinh / suy ra cua bo hinh
RB = "#EAF6EA"      # so do T3
GR = "#EDEDED"      # gia tri bi gioi han sang chip khac
C = lambda s: [(s, "c")]  # noqa: E731


def tier(f):
    f.tier(808, 8, "T1 RK3588")


def wrap(s, n):
    return textwrap.wrap(s, n, break_long_words=False, break_on_hyphens=False)


def panel(f, x, y, w, lines, fill="white", stroke="#999999", size=12.5, line_h=19, dashed=False):
    """Bordered panel; each line is a str or rich parts list. Returns bottom y."""
    h = 14 + line_h * len(lines)
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="1"{dash}/>')
    for i, ln in enumerate(lines):
        f.rich(x + 12, y + 7 + line_h / 2 + line_h * i, ln, size=size)
    return y + h


def leaf(f, x, y, w, name, desc, fill="white", nw=112, size=12, dashed=False, min_h=30):
    """Option leaf: code name (bold mono) and wrapped description. Returns height."""
    lines = wrap(desc, int((w - nw - 12) / (size * 0.47)))
    h = max(min_h, 12 + 16 * len(lines))
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="#333333" '
        f'stroke-width="1.2"{dash}/>')
    f.text(x + 10, y + h / 2, name, size=12.5, weight=700, mono=True)
    top = y + h / 2 - (len(lines) - 1) * 8
    for i, ln in enumerate(lines):
        f.text(x + nw, top + 16 * i, ln, size=size)
    return h


def bus(f, x_from, y_from, x_bus, ys, x_to, color=BLUE):
    """Elbow from (x_from, y_from) to several targets at (x_to, ys[i])."""
    f.line([(x_from, y_from), (x_bus, y_from)], color, THIN, head=False)
    f.line([(x_bus, min(ys + [y_from])), (x_bus, max(ys + [y_from]))], color, THIN, head=False)
    for yy in ys:
        f.line([(x_bus, yy), (x_to, yy)], color, THIN)


# =====================================================================
# Hinh 4.1: cay lua chon rknn.config cho RK3588
# =====================================================================
def fig_options():
    f = Fig(W, 1700)
    tier(f)
    f.text(10, 22, "rknn.config() cho target_platform='rk3588': ba lựa chọn lượng tử hóa", size=15, weight=700)
    LX, LW = 420, 470       # leaves
    PX, PW = 190, 205       # parameter nodes
    y = 46
    groups = [
        ("quantized_dtype", "mặc định: w8a8", [
            ("w8a8", "mặc định. Weight 8-bit, activation 8-bit, asymmetric. RK2118 không hỗ trợ", "white"),
            ("w4a16", "weight 4-bit, activation 16-bit floating point. Only RK3576/RV1126B", GR),
            ("w8a16", "weight 8-bit, activation 16-bit floating point. Only RK3562", GR),
            ("w4a8", "weight 4-bit, activation 8-bit. Not supported yet", GR),
            ("w16a16i", "weight và activation 16-bit asymmetric. Only RV1103/RV1106", GR),
            ("w16a16i_dfp", "weight và activation 16-bit dynamic fixed-point. Only RV1103/RV1106", GR),
        ]),
        ("quantized_algorithm", "mặc định: normal", [
            ("normal", "mặc định. Nhanh. Khoảng 20-100 ảnh calibration", "white"),
            ("mmse", "chậm hơn do lặp vét cạn, thường chính xác hơn normal. Khoảng 20-50 ảnh", "white"),
            ("kl_divergence", "lâu hơn normal, ít hơn mmse; có thể tốt hơn khi phân bố feature không đều. "
                              "Khoảng 20-100 ảnh", "white"),
            ("gdq", "chỉ hợp lệ với w4a16 và w8a16; hơn 200 ảnh. RK3588: không dùng "
                    "(suy ra của bộ hình từ hai câu của API232 tr.7 và tr.8)", LB),
        ]),
        ("quantized_method", "mặc định: channel", [
            ("layer", "mỗi weight chỉ một bộ tham số lượng tử", "white"),
            ("channel", "mặc định. Mỗi channel của weight một bộ tham số; thường chính xác hơn layer", "white"),
            ("group{SIZE}", "chia weight của mỗi output channel thành nhiều nhóm theo input channel, "
                            "SIZE là bội của 32 từ 32 đến 256 (group32, group128). Chỉ hợp lệ khi "
                            "quantized_dtype = w4a16, nên RK3588: không dùng (suy ra của bộ hình)", LB),
        ]),
    ]
    centres = []
    for name, sub, leaves in groups:
        top = y
        mids = []
        for ln, desc, fill in leaves:
            h = leaf(f, LX, y, LW, ln, desc, fill)
            mids.append(y + h / 2)
            y += h + 6
        centres.append((name, sub, (mids[0] + mids[-1]) / 2, mids))
        y += 8
    # parameter nodes and connectors
    rcy = centres[1][2]
    for name, sub, cy, mids in centres:
        f.box(PX, cy - 28, PW, 56, name, sub, mono=True, title_size=15, sub_size=12.5)
        bus(f, PX + PW, cy, LX - 14, mids, LX)
    # root node and elbows to the three parameter nodes
    f.box(10, rcy - 28, 140, 56, "rknn.config()", "target_platform", mono=True, title_size=14.5, sub_size=11.5)
    f.text(10, rcy + 42, "= 'rk3588'", size=12, fill=DARK, mono=True)
    ys = [c[2] for c in centres]
    f.line([(150, rcy), (170, rcy)], BLUE, THIN, head=False)
    f.line([(170, min(ys)), (170, max(ys))], BLUE, THIN, head=False)
    for yy in ys:
        f.line([(170, yy), (PX, yy)], BLUE, THIN)

    # ---- per-channel scope + build() ----
    y += 6
    f.text(10, y + 10, "Phạm vi của per-channel", size=15, weight=700)
    f.text(460, y + 10, "build(): do_quantization và dataset", size=15, weight=700)
    y0 = y + 26
    # left mini-diagram
    f.a(f'<rect x="10" y="{y0}" width="430" height="222" rx="6" fill="white" stroke="#999999" stroke-width="1"/>')
    f.text(24, y0 + 18, "weight (per-channel)", size=13, weight=700)
    for i, lab in enumerate(["channel 0", "channel 1", "channel ..."]):
        f.a(f'<rect x="24" y="{y0 + 34 + 28 * i}" width="130" height="22" fill="#F5F5F5" stroke="#555555"/>')
        f.text(89, y0 + 45 + 28 * i, lab, size=12, anchor="middle")
        f.line([(156, y0 + 45 + 28 * i), (186, y0 + 45 + 28 * i)], BLUE, THIN)
        f.text(192, y0 + 45 + 28 * i, "bộ tham số riêng", size=12, fill=BLUE)
    f.text(24, y0 + 134, "activation, giá trị trung gian (per-layer)", size=13, weight=700)
    f.a(f'<rect x="24" y="{y0 + 150}" width="130" height="22" fill="#F5F5F5" stroke="#555555"/>')
    f.text(89, y0 + 161, "toàn bộ tensor", size=12, anchor="middle")
    f.line([(156, y0 + 161), (186, y0 + 161)], BLUE, THIN)
    f.text(192, y0 + 161, "một bộ tham số chung", size=12, fill=BLUE)
    f.text(24, y0 + 190, "Per-channel chỉ áp dụng cho weight; activation và giá trị trung gian", size=12.5)
    f.text(24, y0 + 207, "vẫn lượng tử theo per-layer (UG232 tr.120).", size=12.5)

    # right: build() cases
    rows = [
        ("True (mặc định)", "lượng tử hóa; cần dataset calibration để tính tham số lượng tử"),
        ("False, nạp model float", "không lượng tử; weight đổi từ float32 sang float16, gần như không mất độ "
                                   "chính xác (build FP16)"),
        ("False, nạp model đã lượng tử", "dùng tham số lượng tử có sẵn trong model"),
    ]
    ry = y0
    for lab, desc in rows:
        lines = wrap(desc, 36)
        h = max(36, 14 + 16 * len(lines))
        f.a(f'<rect x="460" y="{ry}" width="430" height="{h}" rx="4" fill="white" stroke="#333333" stroke-width="1.2"/>')
        if len(lab) <= 22:
            f.text(470, ry + h / 2, lab, size=12, weight=700, mono=True)
        if len(lab) > 22:
            a, b = lab.split(", ")[0] + ",", lab.split(", ")[1]
            f.text(470, ry + h / 2 - 8, a, size=12, weight=700, mono=True)
            f.text(470, ry + h / 2 + 8, b, size=12, weight=700, mono=True)
        for i, ln in enumerate(lines):
            f.text(650, ry + h / 2 - (len(lines) - 1) * 8 + 16 * i, ln, size=12)
        ry += h + 6
    y_q = f.textbox(460, ry, 430, [
        [("QAT: ", "b"), ("load_pytorch nhận model QAT (cần torch 1.9.0 trở lên);", "t")],
        "RKNN nhận model sinh từ giao diện FX (prepare_qat_fx).",
    ], size=12)
    y = max(y0 + 222, y_q) + 18

    # ---- calibration ----
    f.text(10, y + 6, "Dữ liệu calibration (tham số dataset của build)", size=15, weight=700)
    y += 22
    yt = f.table(10, y, [130, 200], ["Thuật toán", "Số ảnh đề xuất (API232 tr.8)"], [
        [C("normal"), "about 20-100 pieces"],
        [C("mmse"), "about 20-50 pieces"],
        [C("kl_divergence"), "about 20-100 pieces"],
        [C("gdq"), "more than 200 pieces"],
    ], size=12, fills={3: LB})
    f.text(10, yt + 14, "gdq: không dùng cho RK3588 (xem trên). UG232 ghi khoảng khác:", size=12, fill=DARK)
    f.text(10, yt + 30, "xem Hình 4.4, hàng 4.", size=12, fill=DARK)
    rules = [
        "Mỗi dòng dataset.txt là một mẫu (jpg, png hoặc npy); nhiều input thì các file cùng dòng cách nhau bằng dấu cách (API232 tr.14).",
        "Chọn ảnh cùng bối cảnh dự đoán, phủ các phân bố dữ liệu của ứng dụng (API232 tr.14; UG232 tr.122).",
        "Thêm ảnh làm thuật toán chạy lâu hơn, chưa chắc chính xác hơn (UG232 tr.122).",
        "Ảnh khác kích thước input được tự resize, nhưng nên dùng đúng kích thước; npy phải đúng shape (UG232 tr.165).",
        "Input không phải ảnh RGB/BGR: nên dùng npy (UG232 tr.158). quant_img_RGB2BGR chỉ tác động jpg, png, bmp (API232 tr.7).",
        "mean/std áp dụng lên dữ liệu calibration trước khi lượng tử (UG232 tr.132). rknn_batch_size không ảnh hưởng bước này (UG232 tr.165).",
    ]
    lines = []
    for r in rules:
        wl = wrap(r, 69)
        lines += [("• " + wl[0])] + ["   " + s for s in wl[1:]]
    yr = panel(f, 360, y - 2, 530, lines, size=11.5, line_h=16)
    y = max(yt + 38, yr) + 8
    f.text(360, y + 4, "Số đo cách resize, NCHW, mean/std: Hình 10.6", size=12.5, fill=BLUE)
    y += 28

    # ---- T3 ----
    f.tier(10, y, "T3 đo")
    y = panel(f, 10, y + 30, 880, [
        "PC, toolkit 2.3.2, config(target_platform='rk3588'), quantized_dtype: w8a8, w16a16i, w16a16i_dfp và asymmetric_quantized-8 trả 0;",
        "w8a16 và w4a16 báo \"not support in 'rk3588'\". Chấp nhận ở config() chưa chứng minh phần cứng hỗ trợ: w16a16i trả 0 dù",
        "API232 tr.7 ghi chỉ RV1103/RV1106.",
    ], fill=RB, stroke=GREEN, size=12.5, line_h=18)
    y = f.legend(10, y + 14, 880, [
        ("fill:#FFFFFF", "giá trị không bị API232 giới hạn sang chip khác (nguyên văn tài liệu T1)"),
        ("fill:" + GR, "API232 ghi giới hạn sang chip khác hoặc chưa hỗ trợ"),
        ("fill:" + LB, "suy ra của bộ hình từ hai câu T1 (không phải câu của vendor)"),
        ("fill:" + RB, "T3: đo trên PC, có file log"),
    ])
    y = f.unknown(10, y + 12, [
        "số bin và cách clipping của normal, mmse, kl_divergence trong toolkit (UG232 tr.120 đến 121 chỉ mô tả bằng lời);",
        "số ảnh calibration phù hợp cho miền hẹp như PPE."], w=880)
    source(f, y + 8, "Nguồn: API232 tr.7, 8, 13, 14; RKNNPY rknn.py:56-58, 84-87, 188; UG232 tr.120, 122, 127, 132, 158, 165; "
           "LOG 2026-10-10_t3-calibration-pc.")
    return f


# =====================================================================
# Hinh 4.2: hybrid quantization
# =====================================================================
def chain(f, x, y, items, gap=34, h=44):
    """Horizontal chain of boxes joined by blue arrows; items: (w, title, sub). Returns list of (x, w)."""
    pos = []
    for w, title, sub in items:
        f.box(x, y, w, h, title, sub, mono=True, title_size=13.5, sub_size=11.5)
        pos.append((x, w))
        x += w + gap
    for (x1, w1), (x2, _) in zip(pos, pos[1:]):
        f.line([(x1 + w1, y + h / 2), (x2, y + h / 2)], BLUE, THIN)
    return pos


def fig_hybrid():
    f = Fig(W, 1300)
    tier(f)
    # ---- step 1 ----
    f.layer(10, 40, 880, 176, ["BƯỚC 1", "UG232 tr.123"], side=True)
    pos = chain(f, 140, 56, [(88, "RKNN()", ""), (98, "config()", ""), (112, "load_*", "onnx, pytorch..."),
                              (212, "hybrid_quantization_step1", "dataset, proposal, custom_hybrid"),
                              (88, "release()", "")], gap=36)
    sx, sw = pos[3]
    cx = sx + sw / 2
    f.line([(cx, 100), (cx, 114)], BLUE, THIN, head=False)
    files = [(140, "<model_name>.model", "model tạm"), (390, "<model_name>.data", "file dữ liệu"),
             (640, "<model_name>.quantization.cfg", "file cấu hình lượng tử")]
    f.line([(files[0][0] + 115, 114), (files[2][0] + 115, 114)], BLUE, THIN, head=False)
    for fx, t, s in files:
        f.line([(fx + 115, 114), (fx + 115, 134)], BLUE, THIN)
        f.box(fx, 136, 230, 44, t, s, mono=True, title_size=13, sub_size=12)
    f.text(140, 200, "Thứ tự gọi lấy từ hình vẽ của UG232 (đọc từ hình); tên file lấy từ API232 tr.20.", size=11.5,
           fill=DARK, italic=True)

    # ---- step 2 ----
    f.layer(10, 232, 880, 196, ["BƯỚC 2", "sửa file cfg", "UG232 tr.124"], side=True)
    code = ["custom_quantize_layers:", "  Conv__350:0: float16", "  Conv__358:0: float16", "quantize_parameters:",
            "  <tên tensor>:", "    qtype, qmethod, dtype,", "    min, max, scale, zero_point"]
    f.a('<rect x="140" y="246" width="300" height="140" rx="4" fill="white" stroke="#333333" stroke-width="1.2"/>')
    for i, ln in enumerate(code):
        f.text(150, 262 + 18 * i, ln, size=12, mono=True, weight=700 if not ln.startswith(" ") else 400)
    f.text(140, 400, "Mẫu cfg theo UG232 tr.124 (rút gọn).", size=11.5, fill=DARK, italic=True)
    notes = [
        "custom_quantize_layers: thêm tên tensor và kiểu; đổi phép tính của lớp đó sang kiểu chỉ định.",
        "Chọn lớp theo kết quả accuracy analysis (Hình 4.3); xem tên tensor bằng cách mở .model với Netron.",
        "Lớp về FP16 chạy chậm hơn trên NPU: đổi tốc độ lấy độ chính xác.",
        "Không khuyến nghị sửa quantize_parameters.",
        "Kiểu cho phép: UG232 tr.124 chỉ float16, ví dụ step1.py:47 ghi thêm int8, int16 (Hình 4.4, hàng 5).",
    ]
    lines = []
    for i, n in enumerate(notes):
        wl = wrap(n, 56)
        lines += ["• " + wl[0]] + ["   " + s for s in wl[1:]]
    panel(f, 460, 246, 420, lines, size=12, line_h=17)

    # ---- step 3 ----
    f.layer(10, 444, 880, 198, ["BƯỚC 3", "UG232 tr.124"], side=True)
    pos = chain(f, 140, 460, [(88, "RKNN()", ""), (250, "hybrid_quantization_step2", "model_input, data_input, cfg"),
                              (150, "export_rknn()", "export_path"), (88, "release()", "")], gap=42)
    (s2x, s2w), (exx, exw) = pos[1], pos[2]
    f.a(f'<rect x="{s2x - 4}" y="512" width="{s2w + 8}" height="114" rx="6" fill="{LB}" stroke="{BLUE}" '
        f'stroke-width="1.3"/>')
    for i, ln in enumerate(["Trả về 0 hoặc -1. Ba tham số:", "đường dẫn .model, .data và",
                            ".quantization.cfg đã sửa; không có", "tham số đường dẫn xuất file.",
                            "Suy ra của bộ hình: file .rknn", "do export_rknn lưu."]):
        f.text(s2x + 6, 526 + 17 * i, ln, size=12, weight=700 if i == 5 else 400)
    f.line([(exx + exw / 2, 504), (exx + exw / 2, 538)], BLUE, THIN)
    f.box(exx - 10, 540, exw + 20, 44, "<model>.rknn", "file model xuất ra", mono=True, title_size=13, sub_size=12)
    f.text(exx - 10, 600, "Chỉ export_rknn lưu file (API232 tr.15).", size=11.5, fill=DARK, italic=True)

    # ---- step 4 ----
    f.layer(10, 650, 880, 52, ["BƯỚC 4"], side=True)
    f.text(140, 676, "Suy luận bằng model .rknn tạo ở bước 3 (UG232 tr.125).", size=13)

    # ---- auto_hybrid ----
    f.text(10, 728, "auto_hybrid: để toolkit chọn lớp, không sửa tay", size=15, weight=700)
    f.box(250, 744, 400, 44, "rknn.build(auto_hybrid=True)", "do_quantization, dataset", mono=True, title_size=13.5,
          sub_size=12)
    f.line([(450, 788), (450, 800)], BLUE, THIN, head=False)
    f.line([(215, 800), (685, 800)], BLUE, THIN, head=False)
    f.line([(215, 800), (215, 816)], BLUE, THIN)
    f.line([(685, 800), (685, 816)], BLUE, THIN)
    f.box(10, 818, 410, 54, "do_quantization=True", "model đang được lượng tử hóa", mono=True, title_size=13.5, sub_size=12)
    f.box(470, 818, 420, 54, "do_quantization=False", "model chưa lượng tử hóa", mono=True, title_size=13.5, sub_size=12)
    f.line([(215, 872), (215, 886)], BLUE, THIN)
    f.line([(680, 872), (680, 886)], BLUE, THIN)
    panel(f, 10, 888, 410, [
        "Lớp có cosine distance và euclidean distance dưới ngưỡng",
        "chỉ định: tính bằng FP16 (hiện chỉ cho w8a8).",
        "UG232 tr.125: hiện chỉ hỗ trợ tự chỉnh từ int8 sang fp16.",
    ], size=12, line_h=18)
    panel(f, 470, 888, 420, [
        "Lớp vượt khoảng giá trị của FP16: tính bằng INT16.",
        "Cần dataset để tính khoảng giá trị từng lớp",
        "(UG232 tr.125).",
    ], size=12, line_h=18)
    y = panel(f, 10, 962, 880, [
        [("Ngưỡng đặt trong config(): ", "b"), ("auto_hybrid_cos_thresh", "c"), (" mặc định 0.98; ", "t"),
         ("auto_hybrid_euc_thresh", "c"), (" mặc định None, nghĩa là không bật (API232 tr.10).", "t")],
        "Mặc định chỉ lớp có cosine distance thấp hơn ngưỡng bị chuyển sang FP16; euclidean distance chưa bật (UG232 tr.125).",
    ], fill=LB, stroke=BLUE, size=12, line_h=19)
    y = f.legend(10, y + 14, 880, [
        ("blue", "thứ tự gọi API"),
        ("fill:" + LB, "suy ra của bộ hình từ nguồn T1 (không phải câu của vendor)"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho, hoặc hai nguồn mâu thuẫn chưa phân xử"),
    ])
    y = f.unknown(10, y + 12, [
        "hướng so sánh của auto_hybrid_euc_thresh: API232 tr.14 viết \"below\", UG232 tr.125 viết \"greater than\" (Hình 4.4, hàng 6);",
        "kiểu int8, int16 trong custom_quantize_layers có chạy được trên RK3588 hay không;",
        "với proposal=False, cfg có được điền lớp gợi ý hay không; ngữ nghĩa của quantized_hybrid_level (rknn.py:59)."],
        w=880)
    source(f, y + 8, "Nguồn: API232 tr.10, 14, 15, 20, 21; UG232 tr.123, 124, 125, 134; RKNNPY rknn.py:200-234; "
           "examples/functions/hybrid_quant/step1.py, step2.py.")
    return f


# =====================================================================
# Hinh 4.3: phan tich sai so
# =====================================================================
def fig_accuracy():
    f = Fig(W, 1500)
    tier(f)
    f.text(10, 22, "A. accuracy_analysis: điều kiện gọi, ba thư mục, bốn nhóm cột sai số", size=15, weight=700)
    y = f.textbox(10, 38, 880, [
        [("Gọi được: ", "b"), ("sau build hoặc hybrid_quantization_step2 (API232 tr.22).", "t")],
        [("Không dùng được: ", "b"), ("sau load_rknn, vì model .rknn thiếu thông tin model gốc (UG232 tr.30; API232 tr.15).", "t")],
        [("Lỗi: ", "b"), ("nếu model gốc là QAT và target=None (API232 tr.22).", "t")],
    ], size=12.5)
    # inputs and directories
    top = y + 18
    f.box(10, top + 42, 120, 56, "inputs", "jpg png bmp npy", mono=True, title_size=14, sub_size=11.5)
    dirs = [("golden/", "từng lớp, chạy cả model float trên simulator", 0),
            ("simulator/", "từng lớp, chạy cả model lượng tử trên simulator (đầu ra đổi sang float32)", 1),
            ("runtime/", "chỉ khi đặt target: từng lớp, chạy cả model lượng tử trên NPU (đổi sang float32)", 2)]
    dys = []
    for name, desc, i in dirs:
        yy = top + 62 * i
        dashed = i == 2
        lines = wrap(desc, 62)
        f.a(f'<rect x="190" y="{yy}" width="470" height="54" rx="4" fill="white" stroke="#333333" '
            f'stroke-width="1.2"{" stroke-dasharray=\"5 3\"" if dashed else ""}/>')
        f.text(200, yy + 27, name, size=13, weight=700, mono=True)
        for k, ln in enumerate(lines):
            f.text(300, yy + 27 - (len(lines) - 1) * 8 + 16 * k, ln, size=12)
        dys.append(yy + 27)
    bus(f, 130, top + 70, 160, dys, 190)
    f.text(680, top + 6, "target đặt hay không", size=13, weight=700)
    for i, ln in enumerate(["Không đặt target: chỉ golden,", "simulator, error_analysis.txt.", "Đặt target: thêm runtime/ và",
                            "cột runtime_error."]):
        f.text(680, top + 28 + 17 * i, ln, size=12)
    yt = top + 62 * 3 + 6
    f.text(10, yt + 6, "error_analysis.txt: bốn nhóm cột, mỗi nhóm có cos và euc (UG232 tr.30, 31)", size=14, weight=700)
    yt = f.table(10, yt + 20, [150, 100, 630], ["Nhóm", "Cột", "So sánh"], [
        [C("simulator_error"), C("entire"), "từ đầu đến lớp hiện tại: kết quả simulator so với golden; sai số tích lũy qua các lớp"],
        [C("simulator_error"), C("single"), "lấy đầu vào golden của lớp hiện tại; so kết quả simulator với golden"],
        [C("runtime_error"), C("entire"), "từ đầu đến lớp hiện tại: kết quả chạy thật trên board so với golden"],
        [C("runtime_error"), C("single_sim"), "lấy đầu vào golden của lớp hiện tại; so kết quả chạy thật ở board với kết quả simulator"],
    ], size=12, fills={2: "#F7F7F7", 3: "#F7F7F7"})
    f.text(10, yt + 14, "entire là sai số tích lũy qua các lớp; single phản ánh sai số của riêng lớp (README ví dụ accuracy_analysis). "
           "API232 tr.22 đặt tên khác: Hình 4.4, hàng 7.", size=12, fill=DARK)

    # ---- B: vendor flow ----
    yb = yt + 44
    f.text(10, yb, "B. Quy trình xử lý lỗi độ chính xác của vendor (UG232 chương 7, Hình 7-1)", size=15, weight=700)
    yb += 18
    stages = [(10, "Simulator FP16", "trước hết, trên PC"), (240, "Simulator Quant", "sau khi FP16 đúng"),
              (470, "Connect Test", "nối board"), (700, "Runtime Test", "chạy thật trên board")]
    for sx, t, s in stages:
        f.box(sx, yb + 24, 190, 50, t, s, title_size=15, sub_size=12, fill="#EEEEEE" if sx < 400 else "white")
    for (x1, _, _), (x2, _, _) in zip(stages, stages[1:]):
        f.line([(x1 + 190, yb + 49), (x2, yb + 49)], BLUE, THIN)
        f.text((x1 + 190 + x2) / 2, yb + 38, "ok", size=12, anchor="middle", fill=BLUE)
    f.text(120, yb + 10, "bắt đầu: Runtime Error", size=12, fill=DARK)
    f.text(700, yb + 10, "kết thúc: Runtime OK", size=12, fill=DARK)
    lists = [
        (10, "FP16 sai thì kiểm tra", [
            "mean_values / std_values", "inputs / outputs", "input_size_list",
            "tham số inference (RGB/BGR, NHWC)", "tràn FP16 (-65504 đến 65504)",
            "Cách làm: build với do_quantization=False, init_runtime(target=None), so với model gốc bằng cosine distance."]),
        (240, "Quant sai thì kiểm tra", [
            "quant_img_RGB2BGR", "optimization_level", "dataset (thường 20 đến 200 ảnh)", "quantized_method",
            "quantized_algorithm", "Hybrid Quant", "QAT",
            "Cách làm: accuracy_analysis(target=None)."]),
        (470, "Connect Test sai thì", [
            "init_runtime(target=...) rồi so với kết quả simulator; accuracy_analysis có target: xem cột "
            "single_sim của runtime_error (vàng hoặc đỏ); gửi phản hồi cho Rockchip NPU team."]),
        (700, "Runtime Test sai thì", [
            "tham số C API (input, output); pre-process và post-process phải giống phía simulator; "
            "RKNN_LOG_LEVEL=5 để dump từng lớp thành numpy (/userdata/dumps trên Linux)."]),
    ]
    ly = yb + 100
    wl = [[ln for it in items for ln in wrap(it, 27)] for _, _, items in lists]
    hmax = max(34 + 16 * len(x) for x in wl)
    for (lx, title, items), lines in zip(lists, wl):
        f.line([(lx + 95, yb + 74), (lx + 95, ly)], GRAY, THIN, dashed=True)
        f.text(lx + 74, yb + 88, "fail", size=12, fill=DARK)
        f.a(f'<rect x="{lx}" y="{ly}" width="190" height="{hmax}" rx="4" fill="{"#EEEEEE" if lx < 400 else "white"}" '
            f'stroke="#333333" stroke-width="1.2"/>')
        f.text(lx + 10, ly + 15, title, size=13, weight=700)
        for i, it in enumerate(lines):
            f.text(lx + 10, ly + 34 + 16 * i, it, size=11.5)
    y = ly + hmax + 18

    # ladder of the Quant stage
    f.text(10, y, "Khi Simulator Quant sai: thứ tự thử của UG232 tr.133 đến 135", size=14, weight=700)
    y += 14
    ladder = [
        ("Kiểm cấu hình: quant_img_RGB2BGR, optimization_level, dataset", "thử một ảnh trước; chưa đủ thì tăng lên khoảng 20 đến 200"),
        ("quantized_method: layer sang channel", "channel thường chính xác hơn layer nhiều"),
        ("quantized_algorithm: normal sang kl_divergence hoặc mmse", "thời gian lượng tử tăng, runtime không bị ảnh hưởng"),
        ("Hybrid cho lớp có cột single của simulator_error giảm mạnh", "xét cả vị trí lớp (lỗi tích lũy); lớp cuối có thể chuyển sang post-processing"),
        ("QAT", "khi hybrid vẫn chưa đủ chính xác, hoặc đủ nhưng hiệu năng chưa đạt (UG232 tr.126, 135)"),
    ]
    for i, (a, b) in enumerate(ladder):
        yy = y + 8 + 40 * i
        f.a(f'<rect x="40" y="{yy}" width="850" height="34" rx="4" fill="white" stroke="#333333" stroke-width="1.2"/>')
        f.badge(24, yy + 17, str(i + 1))
        f.text(52, yy + 11, a, size=12.5, weight=700)
        f.text(52, yy + 26, b, size=11.5, fill=DARK)
        if i:
            f.line([(24, yy - 6), (24, yy + 5)], BLUE, THIN, head=False)
    y = y + 8 + 40 * len(ladder) + 6

    # ---- bottom: original + legend + unknown ----
    yo = f.original(10, y, 430, "../../npu_study/images/04_quantization_rknn/ug232_p131_fig7-1.png", [
        "UG232 tr.131, Figure 7-1 The step of accuracy analysis"])
    yl = f.legend(480, y, 410, [
        ("blue", "ok: sang bước tiếp theo"),
        ("gray", "fail: kiểm tra danh sách bên dưới"),
        ("fill:#EEEEEE", "phía simulator (PC)"),
        ("fill:#FFFFFF", "phía board (nối board hoặc chạy thật)"),
    ])
    yl = f.unknown(480, yl + 12, [
        "ngưỡng cosine để coi là \"đạt\" (UG232 tr.135 chỉ",
        "nhắc màu vàng hoặc đỏ);",
        "golden tính bằng FP32 hay FP16 (Hình 4.4, hàng 8);",
        "quy trình áp dụng cho YOLOv8 hay PPE."], w=410)
    source(f, max(yo, yl) + 8, "Nguồn: API232 tr.15, 22; UG232 tr.30, 31, 126, 131, 132, 133, 134, 135, 136.")
    return f


# =====================================================================
# Hinh 4.4: mau thuan tai lieu
# =====================================================================
def fig_conflicts():
    f = Fig(W, 1500)
    tier(f)
    f.text(10, 22, "10 chỗ bộ tài liệu 2.3.2 không nhất quán, và guide theo phía nào", size=15, weight=700)
    FS = 11.5

    def cell(s, n):
        return ("lines", wrap(s, n))

    NA, NB, NF = 49, 49, 26
    rows = [
        ["1", ("lines", ["quantized_dtype", "mặc định"]),
         cell("API232 tr.7: mặc định \"w8a8\"; rknn.py:56 khớp: quantized_dtype='w8a8'", NA),
         cell("UG232 tr.22 và tr.122: mặc định 'asymmetric_quantized-8'; tr.122: chỉ hỗ trợ linear asymmetric INT8", NB),
         cell("A. T3 PC: config() vẫn nhận tên cũ, quant_tab giống w8a8", NF)],
        ["2", ("lines", ["Thuật toán"]),
         cell("API232 tr.8: normal, mmse, kl_divergence, gdq; rknn.py:85 khớp", NA),
         cell("UG232 tr.22, 122, 159: chỉ normal, mmse, kl_divergence", NB),
         cell("A. gdq không dùng cho RK3588 (Hình 4.1)", NF)],
        ["3", ("lines", ["do_quantization", "mặc định"]),
         cell("API232 tr.14: True; rknn.py:188: do_quantization=True", NA),
         cell("UG232 tr.122: \"the default value being 'False'\"", NB),
         cell("A. Code xác nhận", NF)],
        ["4", ("lines", ["Số ảnh", "calibration"]),
         cell("API232 tr.8: normal và kl_divergence 20-100, mmse 20-50, gdq hơn 200; UG232 tr.28 khớp ba thuật toán đầu", NA),
         cell("UG232 tr.122, 133, 134: 20-200 ảnh; tr.159: normal và kl_divergence 20-200, mmse 20-50", NB),
         cell("A theo từng thuật toán; UG232 chỉ là khoảng rộng, chưa phân xử", NF)],
        ["5", ("lines", ["Kiểu trong", "custom_quantize_layers"]),
         cell("UG232 tr.124: kiểu hiện có chỉ \"float16\"", NA),
         cell("step1.py:47: 'int8', 'int16', 'float16'", NB),
         cell("Chưa phân xử; int8, int16 trên RK3588: unknown", NF)],
        ["6", ("lines", ["Hướng so sánh", "euclidean của", "auto_hybrid"]),
         cell("API232 tr.14: chuyển FP16 khi cosine và euclidean distance \"below the specified thresholds\"", NA),
         cell("UG232 tr.125: \"lesser than the cosine distance threshold or the greater than euclidean distance threshold\"", NB),
         cell("Chưa phân xử: unknown", NF)],
        ["7", ("lines", ["Tên cột", "error_analysis.txt"]),
         cell("API232 tr.22: entire_error, single_error", NA),
         cell("UG232 tr.31: simulator_error (entire, single), runtime_error (entire, single_sim)", NB),
         cell("B (ngoại lệ của quy tắc ưu tiên): khớp README ví dụ và Hình 3-2", NF)],
        ["8", ("lines", ["Golden tính", "bằng FP32 hay FP16"]),
         cell("API232 tr.22: dump \"fp32 & quant\"", NA),
         cell("UG232 tr.131: \"RKNPU currently does not support FP32 calculations\"", NB),
         cell("Chưa phân xử: unknown", NF)],
        ["9", ("lines", ["quant_img_RGB2BGR"]),
         cell("UG232 tr.22, Note: thứ tự inference là RGB2BGR trước rồi mới mean, std (cùng trang, câu trước đó lại nói không có tác dụng ở bước inference)", NA),
         cell("UG232 tr.158: chỉ ảnh hưởng việc đọc ảnh ở bước lượng tử; API232 tr.7: không ghi vào model RKNN cuối", NB),
         cell("B (hai nguồn khớp nhau)", NF)],
        ["10", ("lines", ["Số ảnh trong ví dụ", "so với khuyến nghị"]),
         cell("UG232 tr.122: khuyến nghị 20-200 ảnh", NA),
         cell("dataset.txt của ví dụ onnx/yolov5, hybrid_quant, accuracy_analysis, quantize_algorithm_mmse: mỗi file 1 dòng", NB),
         cell("A. Ví dụ không phải căn cứ; lý do ví dụ dùng 1 ảnh: unknown", NF)],
    ]
    fills = {4: UNK_FILL, 5: UNK_FILL, 7: UNK_FILL, 9: LB}
    y = f.table(10, 40, [30, 134, 288, 288, 140], ["#", "Nội dung", "Phía A", "Phía B", "Guide theo"], rows,
                size=FS, line_h=15, fills=fills)
    y += 18
    y = panel(f, 10, y, 880, [
        [("Quy tắc ưu tiên: ", "b"), ("API232 và rknn.py khớp nhau về mặc định và danh sách giá trị (hàng 1 đến 3), nên guide theo hai nguồn này.", "t")],
        "UG232 tr.22, 122 mô tả khác code ở hàng 1 đến 3; UG232 ghi ngày phát hành 2025-04-03, sau API232 (2025-4-1).",
        "Hàng 5, 6, 8 không có code hay nguồn thứ ba phân xử nên để unknown. Hàng 7 theo UG232 vì khớp ví dụ chính thức.",
        "Hàng 10 là ví dụ so với khuyến nghị, không phải hai trang tài liệu mâu thuẫn nhau.",
    ], size=12, line_h=19)
    y = panel(f, 10, y + 12, 880, [
        [("Cảnh báo phạm vi (không phải mâu thuẫn): ", "b"),
         ("trong 24 dòng target_platform= của examples/, 18 là rk3566, 5 là rk3588 và 1 là rk3562;", "t")],
        "khi dùng mẫu của vendor cho RK3588 phải đổi target_platform. Ví dụ: README của accuracy_analysis ghi mặc định 'rk3566'.",
    ], size=12, line_h=19)
    y = f.legend(10, y + 14, 880, [
        ("fill:#FFFFFF", "guide chọn được một phía theo nguồn (cột cuối ghi phía nào)"),
        ("fill:" + UNK_FILL, "chưa phân xử: unknown"),
        ("fill:" + LB, "so ví dụ với khuyến nghị, không phải hai trang tài liệu"),
    ])
    source(f, y + 8, "Nguồn: API232 tr.7, 8, 14, 22; UG232 tr.22, 28, 31, 122, 124, 125, 131, 133, 134, 158, 159; "
           "RKNNPY rknn.py:56, 85, 188; step1.py:47; LOG t3-calibration-pc.")
    return f


FIGS = [
    ("h4-1-ho-tro-rk3588", fig_options),
    ("h4-2-hybrid", fig_hybrid),
    ("h4-3-phan-tich-sai-so", fig_accuracy),
    ("h4-4-mau-thuan-tai-lieu", fig_conflicts),
]

if __name__ == "__main__":
    run(FIGS, os.path.dirname(os.path.abspath(__file__)))
