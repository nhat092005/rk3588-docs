#!/usr/bin/env python3
"""Phan 8 Thiet ke model: Hinh 8.1 va 8.2.

Primary sources (see chu-thich.md, table Nguon): T2 papers in docs/_assets/pdf/papers/08_npu_friendly_arch (REPVGG, MOBONE, Y6, QAREP, ACTNAS),
docs/_assets/pdf/papers/06_nas (S3NAS), docs/_assets/pdf/papers/05_rk3588 (DAHD, EDGE, LNB, RK66); T1 vendor documents (OPL, UG152, UG232);
T3: log 2026-10-10_t3-board-silu-resize and the leaderboard/run files of the ReLU variant (REPO).

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
C = lambda s: [(s, "c")]  # noqa: E731


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


def bullets(items, n):
    """Wrap each item to n chars with a bullet and hanging indent."""
    out = []
    for it in items:
        wl = wrap(it, n)
        out += ["• " + wl[0]] + ["   " + s for s in wl[1:]]
    return out


# =====================================================================
# Hinh 8.1: re-parameterization
# =====================================================================
def sum_node(f, cx, cy):
    f.a(f'<circle cx="{cx}" cy="{cy}" r="11" fill="white" stroke="#333333" stroke-width="1.2"/>')
    f.text(cx, cy + 0.5, "+", size=16, weight=700, anchor="middle")


def bar_group(f, x0, y0, h_axis, vmax, label, pairs, bw=34, gap=6):
    """pairs: list of (name, fp32, int8, drop_text). Bars: FP32 light grey, INT8 dark grey. Returns right x."""
    x = x0
    for name, fp, i8, drop in pairs:
        for k, (val, fill) in enumerate(((fp, "#CFCFCF"), (i8, "#555555"))):
            bh = h_axis * val / vmax
            bx = x + k * (bw + gap)
            f.a(f'<rect x="{bx}" y="{y0 - bh:g}" width="{bw}" height="{bh:g}" fill="{fill}" stroke="#333333" '
                f'stroke-width="0.8"/>')
            f.text(bx + bw / 2, y0 - bh - 9, f"{val:.1f}", size=12.5, weight=700, anchor="middle")
        f.text(x + bw + gap / 2, y0 + 14, name[0], size=12.5, weight=700, anchor="middle")
        f.text(x + bw + gap / 2, y0 + 30, name[1], size=12, anchor="middle", fill=DARK)
        f.text(x + bw + gap / 2, y0 + 47, drop, size=12.5, weight=700, anchor="middle", fill=RED)
        x += 2 * bw + gap + 34
    return x


def fig_reparam():
    f = Fig(W, 1500)
    f.tier(808, 8, "T2 chung")
    f.text(10, 22, "Structural re-parameterization: nhiều nhánh lúc train, một Conv 3x3 lúc deploy", size=15, weight=700)

    # ---------------- A: merge ----------------
    f.text(10, 52, "A. Gộp nhánh (REPVGG tr.5, Hình 4)", size=14.5, weight=700)
    top = 64
    # left block: schematic
    f.a(f'<rect x="10" y="{top}" width="430" height="322" rx="6" fill="white" stroke="#999999" stroke-width="1"/>')
    f.text(24, top + 18, "Lúc train", size=13.5, weight=700)
    f.text(300, top + 18, "Lúc deploy", size=13.5, weight=700)
    tx = [24, 118, 212]     # branch x
    bwd = 86
    by = top + 90
    f.box(120, top + 34, 90, 28, "input", title_size=13)
    f.line([(165, top + 62), (165, top + 74)], BLUE, THIN, head=False)
    f.line([(tx[0] + bwd / 2, top + 74), (tx[2] + bwd / 2, top + 74)], BLUE, THIN, head=False)
    for x, t, s in zip(tx, ["Conv 3x3", "Conv 1x1", "Identity"], ["+ BN", "+ BN", "+ BN"]):
        f.line([(x + bwd / 2, top + 74), (x + bwd / 2, by)], BLUE, THIN)
        f.box(x, by, bwd, 54, t, s, title_size=13, sub_size=12.5)
        f.line([(x + bwd / 2, by + 54), (x + bwd / 2, by + 78)], BLUE, THIN, head=False)
    f.line([(tx[0] + bwd / 2, by + 78), (tx[2] + bwd / 2, by + 78)], BLUE, THIN, head=False)
    f.line([(165, by + 78), (165, by + 92)], BLUE, THIN)
    sum_node(f, 165, by + 104)
    f.line([(165, by + 115), (165, by + 132)], BLUE, THIN)
    f.box(120, by + 134, 90, 30, "ReLU", title_size=13)
    # arrow to deploy
    f.line([(236, by + 104), (292, by + 104)], BLUE, 3.0)
    f.text(264, by + 88, "gộp", size=12.5, anchor="middle", fill=BLUE, weight=700)
    f.box(300, by + 70, 124, 54, "Conv 3x3", "có bias", title_size=13.5, sub_size=12.5, fill=LB)
    f.line([(362, by + 124), (362, by + 134)], BLUE, THIN)
    f.box(317, by + 134, 90, 30, "ReLU", title_size=13)
    for i, ln in enumerate(["Nhánh identity chỉ có khi C1 = C2, H1 = H2, W1 = W2;",
                            "nếu không thì chỉ có hai nhánh đầu.",
                            "Ô nền xanh nhạt: dạng deploy do bộ hình vẽ theo Hình 4 của REPVGG."]):
        f.text(24, top + 270 + 16 * i, ln, size=11.5, fill=DARK)

    steps = bullets([
        "Mỗi BN và conv đứng trước gộp thành một conv có bias.",
        "Identity coi như conv 1x1 với ma trận đơn vị.",
        "Bias cuối là tổng ba bias; kernel 3x3 cuối là kernel 3x3 cộng hai kernel 1x1 đặt vào điểm giữa "
        "(zero-pad 1x1 lên 3x3).",
        "Điều kiện: cùng stride; padding của lớp 1x1 ít hơn lớp 3x3 một pixel.",
        "Sau gộp, thân model chỉ còn một loại op: Conv 3x3 + ReLU (REPVGG tr.2).",
    ], 74)
    yb = panel(f, 10, top + 334, 430, steps, size=12, line_h=17)
    # right block: original
    yo = f.original(460, top, 410, "../../npu_study/images/08_model_design_for_npu/repvgg_p5_fig4.png",
                    ["REPVGG tr.5, Figure 4: (A) cấu trúc, (B) tham số"])
    ya = max(yb, yo) + 14

    # three papers table
    f.text(10, ya + 4, "Ba bài dùng re-param và thiết bị đo tốc độ của từng bài", size=14.5, weight=700)
    yt = f.table(10, ya + 18, [90, 400, 390], ["Bài", "Lúc train, lúc inference", "Thiết bị đo tốc độ (không có NPU)"], [
        [C("REPVGG"), "3x3 + 1x1 + identity, mỗi nhánh có BN; Conv 3x3 + ReLU", "NVIDIA 1080Ti (Table 4, tr.7)"],
        [C("MOBONE"), "3x3 depthwise rồi 1x1 pointwise, có nhánh; không còn nhánh",
         "iPhone 12 (Core ML); Table 9 còn cột CPU và GPU"],
        [C("Y6"), "RepBlock; stack Conv 3x3 (RepConv) + ReLU", "Tesla T4, TensorRT, FP16 (Table 1, tr.8)"],
    ], size=12, line_h=16)
    f.text(10, yt + 14, "Không bài nào đo RepVGG hay MobileOne trên NPU; xem ô unknown bên dưới.", size=12, fill=DARK)

    # ---------------- B: PTQ side effect ----------------
    yb2 = yt + 40
    f.tier(10, yb2, "T2 chung")
    f.text(100, yb2 + 11, "B. Tác dụng phụ: PTQ làm RepVGG tụt mạnh, QARepVGG sửa", size=14.5, weight=700)
    ytop = yb2 + 36
    f.a(f'<rect x="10" y="{ytop}" width="880" height="312" rx="6" fill="white" stroke="#999999" stroke-width="1"/>')
    f.text(24, ytop + 18, "ImageNet top-1 (%), RepVGG-A0", size=13, weight=700)
    f.text(470, ytop + 18, "COCO mAP (%), YOLOv6s", size=13, weight=700)
    base = ytop + 200
    # axes
    for x0 in (40, 486):
        f.a(f'<path d="M{x0} {base} L{x0 + 380} {base}" stroke="#666666" stroke-width="1"/>')
    bar_group(f, 70, base, 150, 80, "A0", [(("RepVGG-A0", "(official)"), 72.4, 52.2, "-20.2"),
                                           (("QARepVGG-A0", ""), 72.2, 70.4, "-1.8")])
    bar_group(f, 516, base, 150, 80, "v6s", [(("YOLOv6s", "RepVGG"), 42.4, 35.0, "-7.4"),
                                             (("YOLOv6s", "QARepVGG"), 42.3, 41.0, "-1.3")])
    # legend for bars
    lx, ly = 570, ytop + 26
    f.a(f'<rect x="{lx + 130}" y="{ly + 8}" width="14" height="12" fill="#CFCFCF" stroke="#333333" stroke-width="0.8"/>')
    f.text(lx + 150, ly + 14, "FP32", size=12.5)
    f.a(f'<rect x="{lx + 195}" y="{ly + 8}" width="14" height="12" fill="#555555" stroke="#333333" stroke-width="0.8"/>')
    f.text(lx + 215, ly + 14, "INT8 (PTQ)", size=12.5)
    f.text(24, ytop + 276, "Số dưới mỗi cặp cột (đỏ): chênh lệch INT8 so với FP32. Thiết lập của bài: PTQ chuẩn, 8-bit symmetric uniform, "
           "NVIDIA PyTorch-Quantization,", size=11.5, fill=DARK)
    f.text(24, ytop + 293, "weight và input của conv, FC đều 8-bit kể cả lớp đầu và cuối; đo trên bản deploy sau khi gộp nhánh. "
           "Không phải RKNN.", size=11.5, fill=DARK)
    # fix panel
    yf = ytop + 326
    fixes = bullets([
        "QARepVGG: bỏ BN khỏi nhánh identity và nhánh 1x1, thêm một BN sau phép cộng ba nhánh (QAREP tr.5).",
        "Vẫn gộp được thành một Conv 3x3 như RepVGG (QAREP tr.1, Figure 1); FP32 gần RepVGG, INT8 sát FP32.",
        "Nguyên nhân theo tác giả: BN từng nhánh đổi phương sai nên cộng ba nhánh làm phương sai tăng, và trọng số sau gộp có "
        "outlier không kiểm soát được (QAREP tr.3, 4, 5).",
    ], 120)
    yf = panel(f, 10, yf, 880, fixes, size=12, line_h=17)

    # ---------------- C: RK3588 ----------------
    yc = yf + 18
    f.text(10, yc, "C. Liên hệ RK3588", size=14.5, weight=700)
    f.tier(160, yc - 11, "T1 RK3588")
    yc += 14
    yc = panel(f, 10, yc, 880, [
        [("Biểu diễn được trên NPU (suy ra của bộ hình): ", "b"),
         ("dạng sau gộp là Conv 3x3 + ReLU; OPL có Conv (kernel_h, kernel_w thuộc [1, 31], int8 và float16)", "t")],
        "và ConvolutionRelu (Convolution và Relu fusion) trong mục NPU của RK3588 (OPL tr.58 đến 60).",
        [("Fusion Conv trên RK3588: ", "b"), ("xem Hình 6.3. Kiểu số RKNN mặc định là w8a8 asymmetric (API232 tr.7), "
                                              "khác thiết lập symmetric của QAREP.", "t")],
    ], fill=LB, stroke=BLUE, size=12, line_h=19)
    yu = f.unknown(10, yc + 12, [
        "RK3588 có nhanh hơn nhờ re-param hay không (REPVGG tr.2 chỉ là giả thuyết của tác giả về chip chuyên dụng, không có số đo);",
        "RepVGG qua RKNN INT8 trên RK3588 có tụt như QAREP đo bằng PyTorch-Quantization hay không;",
        "không có nguồn T1 hay T3 trả lời hai câu trên; QARepVGG cũng chưa có số RK3588."], w=880)
    yl = f.legend(10, yu + 12, 880, [
        ("fill:#FFFFFF", "nguyên văn nguồn (T2 paper, T1 vendor)"),
        ("fill:" + LB, "suy ra của bộ hình, không phải câu của nguồn"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho"),
    ])
    source(f, yl + 8, "Nguồn: REPVGG tr.2, 5, 7; MOBONE tr.1, 4, 7; Y6 tr.3, 4, 8; QAREP tr.1, 3, 4, 5, 6, 7; OPL tr.58 đến 60; "
           "API232 tr.7.")
    return f


# =====================================================================
# Hinh 8.2: checklist
# =====================================================================
LX, LW = 262, 628           # leaf column
QX, QW = 10, 196            # question column
TIER_W = {"T1 RK3588": 14 + 7.4 * 9, "T2 chung": 14 + 7.4 * 8, "T3 đo": 14 + 7.4 * 5}


def leaf(f, y, tier, title, body, src, fill="white", dashed=False):
    """Decision-tree leaf with tier badge, bold title, wrapped body and an italic source line. Returns height."""
    lines = []
    for b in body:
        lines += wrap(b, int((LW - 24) / 6.2))
    h = 12 + 20 + 16 * len(lines) + 20
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{LX}" y="{y}" width="{LW}" height="{h}" rx="4" fill="{fill}" stroke="#333333" '
        f'stroke-width="1.2"{dash}/>')
    bw = f.tier(LX + 8, y + 6, tier) - (LX + 8)
    f.text(LX + 8 + bw + 10, y + 17, title, size=12.5, weight=700)
    for i, ln in enumerate(lines):
        f.text(LX + 12, y + 40 + 16 * i, ln, size=12)
    f.text(LX + 12, y + h - 12, src, size=11, fill=DARK, italic=True)
    return h


def question(f, cy, n, lines):
    h = 14 + 18 * len(lines)
    f.a(f'<rect x="{QX}" y="{cy - h / 2}" width="{QW}" height="{h}" rx="8" fill="#F5F5F5" stroke="#333333" '
        f'stroke-width="1.4"/>')
    f.badge(QX + 18, cy - h / 2 + 18, str(n))
    for i, ln in enumerate(lines):
        f.text(QX + 34 if i == 0 else QX + 12, cy - h / 2 + 18 + 18 * i if i == 0 else cy - h / 2 + 18 + 18 * i, ln,
               size=12.5, weight=700)
    return h


def group(f, y, n, qlines, leaves):
    """Draw the leaves from y, then the question node centred on them. Returns (bottom y, node cy, node h)."""
    ys, mids = y, []
    for lf in leaves:
        h = leaf(f, ys, *lf[:4], **lf[4]) if len(lf) == 5 else leaf(f, ys, *lf)
        mids.append(ys + h / 2)
        ys += h + 8
    cy = (mids[0] + mids[-1]) / 2
    nh = question(f, cy, n, qlines)
    xb = LX - 28
    f.line([(QX + QW, cy), (xb, cy)], BLUE, THIN, head=False)
    f.line([(xb, min(mids)), (xb, max(mids))], BLUE, THIN, head=False)
    for m in mids:
        f.line([(xb, m), (LX, m)], BLUE, THIN)
    return ys, cy, nh


def fig_checklist():
    f = Fig(W, 2600)
    f.text(10, 22, "Checklist thiết kế model cho NPU RK3588: mỗi lá có tier và nguồn", size=15, weight=700)
    f.tier(664, 8, "T1 RK3588")
    f.tier(752, 8, "T2 chung")
    f.tier(832, 8, "T3 đo")
    y = 44
    centers = []

    # Q1 ---------------------------------------------------------------
    y, cy, nh = group(f, y, 1, ["Op nào của model", "có mục NPU", "trong OPL?"], [
        ("T1 RK3588", "Conv: kernel, stride, pad, dilation", [
            "kernel_h, kernel_w thuộc [1, 31]; stride_h, stride_w thuộc [1, 7]; pads thuộc [0, 15]; dilations thuộc "
            "[1, 31]; kiểu int8, float16. Depthwise Conv: kernel_h, kernel_w thuộc [1, 8]."],
         "OPL tr.58, 59 (mục 3.2.5, 3.2.6)"),
        ("T1 RK3588", "Resize có mục NPU, Upsample không", [
            "Resize: chỉ phóng đại nguyên lần 2 đến 8 theo H và W; mode chỉ nearest, linear; coordinate_transformation_mode "
            "chỉ half_pixel, pytorch_half_pixel, align_corners. Upsample: không có mục trong phần NPU (tìm toàn bộ OPL, "
            "phép kiểm của bộ hình), chỉ có mục CPU 4.67 (bilinear, nearest2d)."],
         "OPL tr.87 (mục 3.2.54), tr.329 (mục 4.67)"),
        ("T3 đo", "Một model: Resize nearest 2x chạy NPU", [
            "YOLOv8n nc=5, trọng số ngẫu nhiên, INT8: 2 lớp Resize nearest 2x có Target NPU ở optimization_level 1, 2, 3. "
            "UG232 nói optimization_level=2 đưa Resize về CPU và toolkit đổi Resize thành ConvTranspose: không tái hiện "
            "được ở model này; chưa thử bilinear, FP16. OPL và UG232 chưa phân xử (Hình 6.2)."],
         "LOG 2026-10-10_t3-board-silu-resize/README.md; UG232 tr.176", dict(fill=RB)),
    ])
    centers.append((cy, nh))
    y += 14

    # Q2 ---------------------------------------------------------------
    y, cy, nh = group(f, y, 2, ["Op có chạy chia", "trên 3 NPU core", "không?"], [
        ("T1 RK3588", "Danh sách multi-core, op khác rơi về Core0", [
            "Với RKNN_NPU_CORE_0_1 và RKNN_NPU_CORE_0_1_2, các op này được tăng tốc tốt hơn: Conv, "
            "DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, Prelu, LeakyRelu. Op loại khác "
            "rơi về Core0 để chạy tiếp (UG152). UG232 liệt kê cùng danh sách."],
         "UG152 tr.27; UG232 tr.75"),
        ("T1 RK3588", "OPL ghi khác ở vài op (chưa phân xử)", [
            "OPL mục 3.2.51 PRelu ghi 多核联合: 暂不支持, trong khi UG152 và UG232 liệt kê PRelu; Conv và Depthwise "
            "Conv ghi 支持. Bộ hình không chọn phía nào."],
         "OPL tr.59, 60, 85; UG152 tr.27", dict(fill=UNK_FILL, dashed=True)),
        ("T3 đo", "Một model: op nào chia ba lõi", [
            "YOLOv8n nc=5, trọng số ngẫu nhiên, INT8, CORE_0_1_2: Split (9), MaxPool (3), Resize (2), Sub (2), Mul (2), "
            "Sigmoid (1), exSoftmax13 (1) đều WorkLoad 100%/0%/0%; 8 Add chia ba lõi; 15 trong 17 Concat chia ba lõi "
            "(phép đếm của bộ hình trên file lớp)."],
         "LOG 2026-10-10_t3-board-silu-resize/raw/silu_opt3_CORE_0_1_2_layers.txt", dict(fill=RB)),
    ])
    centers.append((cy, nh))
    y += 14

    # Q3 ---------------------------------------------------------------
    y, cy, nh = group(f, y, 3, ["Chọn activation:", "SiLU hay ReLU?"], [
        ("T1 RK3588", "Op gộp Conv và activation trong OPL", [
            "ConvolutionRelu (mục 3.2.7): 多核联合 支持. ConvolutionSwish (mục 3.2.17, SiLU): 多核联合 暂不支持; cả hai "
            "\"说明及规格限制同Convolution\". UG232: Conv+Sigmoid(Tanh/Elu/Silu...) nằm ở cột fusion đã hỗ trợ (Hình 6.3)."],
         "OPL tr.60, 63; UG232 tr.142"),
        ("T3 đo", "Một model: ConvExSwish chỉ lõi 0, ConvRelu chia ba lõi", [
            "YOLOv8n nc=5, trọng số ngẫu nhiên, INT8, 640x640, CORE_0_1_2: 57 lớp ConvExSwish đều "
            "100%/0%/0%; 51 ConvRelu và 6 ConvReluAdd chia ba lõi (khoảng 35%/32.5%/32.5%). Một model, một board. "
            "Độ trễ: Hình 10.1, Hình 10.3."],
         "LOG 2026-10-10_t3-board-silu-resize/README.md, raw/*_CORE_0_1_2_layers.txt", dict(fill=RB)),
        ("T3 đo", "FP32: ReLU thấp hơn SiLU 0.0073 mAP50-95", [
            "YOLOv8n 5 lớp, seed 42, tập test SFCHD, protocol v1: ReLU 0.5835, SiLU 0.5908 (hiệu là phép tính của bộ hình). "
            "ReLU khởi tạo từ yolov8n.pt, trọng số SiLU, nên AP của nó là cận dưới thực tế (nhận định của bộ hình, chưa "
            "kiểm bằng huấn luyện từ đầu). Chỉ FP32, một seed; INT8 trên board chờ pipeline: Hình 10.7."],
         "REPO ai/automation/leaderboards/sfchd_5class.csv (cột map50_95); REPO ai/models/README.md", dict(fill=RB)),
        ("T2 chung", "Paper: ReLU nhanh hơn SiLU, trên thiết bị khác RK3588", [
            "Y6 (TensorRT, Tesla T4): \"ReLU has a greater speed advantage because of its fusion into convolution\". "
            "ACTNAS (3 NPU không nêu tên): \"ReLU is fast but often less precise, while SiLU offers higher accuracy at the "
            "expense of speed\". Hai bài này không đo RK3588."],
         "Y6 tr.8; ACTNAS tr.1, 3"),
    ])
    centers.append((cy, nh))
    y += 14

    # Q4 ---------------------------------------------------------------
    y, cy, nh = group(f, y, 4, ["Từng lớp có đạt", "tiêu chí hiệu năng", "của UG232?"], [
        ("T1 RK3588", "Căn chỉnh channel (RK3588, Table 8-2)", [
            "Conv: channel vào 32 và ra 32 với int8 (float16: vào 32, ra 16); Depthwise Conv: 64 với int8 (float16: 32); "
            "op khác: 16 với int8. Channel đạt căn chỉnh thì utilization cao hơn."],
         "UG232 tr.145, 146"),
        ("T1 RK3588", "Kích thước kernel và utilization (tham khảo kinh nghiệm)", [
            "Utilization tương đối cao khi KH*KW*KC*type_bytes < 6K Bytes; Ksize/Kstride càng lớn càng cao "
            "(Ksize=3, Kstride=1 tốt hơn Ksize=2, Kstride=1); giảm khi Height*Width của output < 16; channel vào < 256 tương "
            "đối cao, > 512 giảm dần."],
         "UG232 tr.146, 147"),
        ("T1 RK3588", "Giảm ba loại op kém hiệu quả (Table 8-5)", [
            "Data transfer: Transpose, Reshape, Split, Concat. Size transformation: Resize, Tile, Pooling, Pad. "
            "Non-Relu activation function: Sigmoid, Tanh, Softplus, Hardswish. Khối YOLO so với bảng này: Hình 9.4."],
         "UG232 tr.146"),
        ("T1 RK3588", "Ghép op của phần cứng", [
            "Đã hỗ trợ: Conv+Relu, Conv+PRelu(LeakyRelu), Conv+Clip, Conv+Sigmoid(Tanh/Elu/Silu...), Conv+Add, "
            "Conv+Activation+Add. Kế hoạch tương lai: Conv+Mul, Conv+Activation+Mul. Chi tiết: Hình 6.3."],
         "UG232 tr.142"),
    ])
    centers.append((cy, nh))
    y += 14

    # Q5 ---------------------------------------------------------------
    y, cy, nh = group(f, y, 5, ["Dùng re-param,", "NAS hay sửa", "kiến trúc YOLO?"], [
        ("T2 chung", "Re-param không đảm bảo INT8 tốt (Hình 8.1)", [
            "Bản PTQ chuẩn 8-bit symmetric, NVIDIA PyTorch-Quantization: RepVGG-A0 72.4 xuống 52.2 (top-1); "
            "YOLOv6s-RepVGG 42.4 xuống 35.0 (mAP); QARepVGG: 72.2 xuống 70.4 và 42.3 xuống 41.0. RK3588: unknown."],
         "QAREP tr.1, 6, 7 (Table 5, 8)"),
        ("T2 chung", "NAS: S3NAS (bộ mô phỏng) và ActNAS (3 NPU ẩn danh)", [
            "S3NAS: bộ ước lượng độ trễ xây từ bộ mô phỏng NPU; MIDAP \"has not been implemented as a real hardware chip yet\"; "
            "filter là bội của 16 để tối đa MAC utilization trên MIDAP. ActNAS: tìm activation từng lớp; model tối ưu cho "
            "NPU1 \"very low speedup on other devices\". Không có NAS cho Rockchip."],
         "S3NAS tr.1, 4, 9; ACTNAS tr.2, 8"),
        ("T2 chung", "DAHD [RK3588, Orange Pi 5 Plus]: model sửa chạy chậm hơn", [
            "YOLOv8 thêm DBB và attention (bài về hút thuốc): INT8 inference-time 79.1 ms so với 56.3 ms của YOLOv8s; "
            "tác giả: \"increased structural complexity has resulted in a decline in inference speed\". Nhiều sửa đổi "
            "cùng lúc, FPS đo bằng thread pool."],
         "DAHD tr.1, 5, 17, 18 (Table 6), 20"),
        ("T2 chung", "EDGE [RK3588, RKNN INT8, không sửa model]: YOLO11n chậm hơn YOLOv8n", [
            "\"YOLO11n, with fewer parameters than YOLOv8n, exhibited higher latency on all three SoCs\"; nguyên nhân "
            "C2f, C3k2 chỉ là giả thuyết của tác giả (\"suggesting\"). RK3588 đo ở chế độ một NPU core."],
         "EDGE tr.4, 5"),
        ("T2 chung", "LNB [RK3568] và RK66 [RK3566]: không dùng cho RK3588", [
            "LNB: FPS đo trên RTX 3090; ở board RK3568 chỉ đếm lỗi trên 20 ảnh, không có độ trễ NPU. RK66: FP32 vì các thử "
            "nghiệm INT8 \"produced invalid results due to quantization noise\"; nguyên nhân chỉ là suy đoán (\"likely\")."],
         "LNB tr.20; RK66 tr.4, 12"),
    ])
    centers.append((cy, nh))
    # chain arrows between question nodes
    for (c1, h1), (c2, h2) in zip(centers, centers[1:]):
        f.line([(QX + QW / 2, c1 + h1 / 2), (QX + QW / 2, c2 - h2 / 2)], BLUE, THIN)
        f.text(QX + QW / 2 + 8, (c1 + h1 / 2 + c2 - h2 / 2) / 2, "tiếp", size=12, fill=BLUE)

    y += 8
    yu = f.unknown(10, y, [
        "re-param (RepVGG, MobileOne) có giảm độ trễ hoặc mất độ chính xác INT8 trên RK3588 hay không;",
        "độ chính xác INT8 của ReLU so với SiLU trên board (chờ pipeline, Hình 10.7); ReLU ở đây mới có FP32;",
        "ConvExSwish có ép chạy đa lõi được không (log ghi chưa thử); vì sao YOLO11 chậm hơn YOLOv8 trên RK3588;",
        "NAS đo độ trễ trên NPU Rockchip; số của RK3566, RK3568 có bằng RK3588 hay không (nguồn không đo)."], w=880)
    yl = f.legend(10, yu + 12, 880, [
        ("fill:#FFFFFF", "nguyên văn nguồn T1 hoặc T2"),
        ("fill:" + RB, "T3: đo của chúng ta, có file log hoặc run, chỉ cho model và board đã ghi"),
        ("fill:" + UNK_FILL, "mâu thuẫn chưa phân xử hoặc unknown"),
        ("blue", "thứ tự hỏi khi thiết kế; mỗi câu hỏi có các lá, mỗi lá một tier"),
    ])
    f.text(10, yl + 26, "Nguồn: OPL tr.58 đến 63, 85, 87, 329; UG152 tr.27; UG232 tr.75, 142, 145 đến 147, 176; Y6 tr.8; ACTNAS tr.1 đến 3, 8;",
           size=12, fill=DARK, italic=True)
    source(f, yl + 26, "S3NAS tr.1, 4, 9; DAHD tr.1, 5, 17, 18, 20; EDGE tr.4, 5; LNB tr.20; RK66 tr.4, 12; "
           "LOG t3-board-silu-resize; REPO leaderboard.")
    return f


FIGS = [
    ("h8-1-reparam", fig_reparam),
    ("h8-2-checklist", fig_checklist),
]

if __name__ == "__main__":
    run(FIGS, os.path.dirname(os.path.abspath(__file__)))
