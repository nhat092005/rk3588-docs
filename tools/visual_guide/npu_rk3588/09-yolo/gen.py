#!/usr/bin/env python3
"""Phan 9 YOLO: Hinh 9.1 den 9.4.

Primary sources (see chu-thich.md, table Nguon): ULT (ultralytics 8.4.154 in .venv: cfg/models/*.yaml, nn/modules/*.py,
nn/tasks.py, engine/exporter.py), LOG (tmp/04_debug-logs/2026-10-10_yolo-arch/out/*, 2026-10-10_yolo-phaseA/raw/layers_*.txt,
2026-10-10_t3-board-silu-resize/raw/*), OPL, UG232, API232, YOFF, UDOC.
Numbers are read from files (layer tables, op histograms, RKNN layer tables), not typed by hand. Files written by this part:
data/ops_via_exporter.json (YOLO(...).export, format="onnx", copy of the output of the existing script ops_via_exporter.py, whose
own output file was not kept in the log folder) and data/rknn_path_onnx.json (data/capture_rknn_path.py).

Usage: python3 gen.py [outdir] [figure-name ...]
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, THICK, Fig, run, source  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
LOGS = os.path.join(ROOT, "tmp", "04_debug-logs")
ARCH = os.path.join(LOGS, "2026-10-10_yolo-arch", "out")
PHASEA = os.path.join(LOGS, "2026-10-10_yolo-phaseA", "raw")
SILU = os.path.join(LOGS, "2026-10-10_t3-board-silu-resize", "raw")

UNK_FILL, LB, RB = "#FFF3F3", "#EAF2FF", "#EAF6EA"
ATT = "#C77800"  # not used for fills; attention blocks use a blue outline

C = lambda s: [(s, "c")]  # noqa: E731
B = lambda s: [(s, "b")]  # noqa: E731


# ------------------------------------------------------------------ data
def load_layer_table(name):
    """Rows of table_v8n.md / table_26n.md: dict(i, frm, type, params, gflops, shape)."""
    rows, total = [], None
    with open(os.path.join(ARCH, name), encoding="utf-8") as fh:
        for ln in fh:
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) != 6 or cells[0] in ("i", "---"):
                continue
            if cells[0] == "tổng":
                total = (cells[3], cells[4])
                continue
            dims = [int(x) for x in re.findall(r"\d+", cells[5])][1:]
            rows.append(dict(i=int(cells[0]), frm=cells[1], type=cells[2], params=cells[3], gflops=cells[4],
                             shape="x".join(str(d) for d in dims), raw=ln.strip()))
    return rows, total


def load_json(*parts):
    with open(os.path.join(*parts), encoding="utf-8") as fh:
        return json.load(fh)


def parse_layers(path):
    """RKNN eval_perf layer table -> list of dict(id, op, dtype, target, workload)."""
    out = []
    for ln in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"^(\d+)\s+(\S+)\s+(\S+)\s+(NPU|CPU)\s", ln)
        if not m:
            continue
        w = re.search(r"([\d.]+)%/([\d.]+)%/([\d.]+)%", ln)
        a = tuple(float(x) for x in w.groups())
        wl = "none" if sum(a) == 0 else ("core0" if a[1] == 0 and a[2] == 0 else "multi")
        out.append(dict(id=int(m.group(1)), op=m.group(2), dtype=m.group(3), target=m.group(4), wl=wl))
    return out


def layer_stats(path):
    rows = parse_layers(path)
    ops = collections.Counter(r["op"] for r in rows)
    wl = collections.defaultdict(collections.Counter)
    for r in rows:
        wl[r["op"]][r["wl"]] += 1
    cpu = [r["op"] for r in rows if r["target"] == "CPU" and r["op"] not in ("InputOperator", "OutputOperator")]
    npu = sum(1 for r in rows if r["target"] == "NPU")
    return dict(n=len(rows), ops=ops, wl=wl, cpu=cpu, npu=npu)


def fmt(n):
    return f"{int(n):,}"


def tier(f, label="T1 RK3588", x=None):
    f.tier(x if x is not None else f.w - 100 - (len(label) - 9) * 7.4, 8, label)


def box(f, x, y, w, h, fill="white", stroke="#333333", sw=1.2, dashed=False, rx=4):
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{sw}"{dash}/>')


def vtext(f, x, y, s, size=13, weight=700, fill=DARK):
    f.a(f'<text transform="translate({x} {y}) rotate(-90)" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="middle" dominant-baseline="central">{s}</text>')


def source2(f, y, lines):
    """Italic source line(s) under a figure, wrapped by hand; sets the figure height."""
    for i, ln in enumerate(lines):
        f.text(10, y + 18 + 17 * i, ln, size=12, fill=DARK, italic=True)
    f.h = y + 14 + 17 * len(lines)


def lines_block(f, x, y, lines, size=12.5, lh=17, anchor="start", fill=INK):
    for i, ln in enumerate(lines):
        f.rich(x, y + lh * i, ln, size=size, anchor=anchor, fill=fill)
    return y + lh * len(lines)


def panel(f, x, y, w, lines, fill="white", stroke="#999999", size=12.5, dashed=False, lh=19, pad=14):
    h = pad + lh * len(lines)
    box(f, x, y, w, h, fill=fill, stroke=stroke, sw=1, dashed=dashed, rx=6)
    for i, ln in enumerate(lines):
        f.rich(x + 12, y + pad / 2 + 9 + lh * i, ln, size=size)
    return y + h


def cell_box(f, x, y, w, h, title, sub=None, fill="white", stroke="#333333", sw=1.2, title_size=14, sub_size=12,
             mono=True, dashed=False):
    box(f, x, y, w, h, fill=fill, stroke=stroke, sw=sw, dashed=dashed)
    if sub:
        f.text(x + w / 2, y + h / 2 - 8, title, size=title_size, weight=700, anchor="middle", mono=mono)
        f.text(x + w / 2, y + h / 2 + 9, sub, size=sub_size, anchor="middle", fill=DARK)
    else:
        f.text(x + w / 2, y + h / 2, title, size=title_size, weight=700, anchor="middle", mono=mono)


# =====================================================================
# Hinh 9.1: YOLOv8n va YOLO26n canh nhau
# =====================================================================
ATTN_LAYERS = {"yolo26n": {10, 22}}


def column(f, x0, name, rows, total, stage_of, skips, detect_from, y0):
    """One model column. Returns the bottom y."""
    W, H, PITCH = 370, 30, 40
    ypos = {r["i"]: y0 + PITCH * k for k, r in enumerate(rows)}
    # header strip
    hx = x0
    for lab, dx, anc in [("i", 8, "start"), ("khối", 36, "start"), ("đầu ra CxHxW", 150, "start"),
                         ("tham số", W - 72, "end"), ("GFLOPs", W - 10, "end")]:
        f.text(hx + dx, y0 - 14, lab, size=12, weight=700, fill=DARK, anchor=anc)
    for k, r in enumerate(rows):
        y = ypos[r["i"]]
        t = r["type"]
        fill = "#F5F5F5" if t in ("C2f", "C3k2") else ("#E8E8E8" if t == "Detect" else "white")
        attn = r["i"] in ATTN_LAYERS.get(name, set())
        box(f, x0, y, W, H, fill=fill, stroke=BLUE if attn else "#333333", sw=2.6 if attn else 1.2)
        f.text(x0 + 8, y + H / 2, str(r["i"]), size=13, weight=700, mono=True)
        label = t if r["frm"] == "-1" else f"{t} {r['frm'].replace(' ', '')}"
        f.text(x0 + 36, y + H / 2, label, size=13.5, weight=700)
        f.text(x0 + 150, y + H / 2, r["shape"], size=12, mono=True)
        f.text(x0 + W - 72, y + H / 2, r["params"], size=12, anchor="end", mono=True)
        f.text(x0 + W - 10, y + H / 2, r["gflops"], size=12, anchor="end", mono=True)
        # sequential arrow into the next row (not into Detect: its inputs are the bus on the left)
        if k + 1 < len(rows) and rows[k + 1]["type"] != "Detect":
            f.line([(x0 + W / 2, y + H), (x0 + W / 2, y + PITCH)], INK, THIN)
    # skip lanes on the right: (src, dst, lane)
    lanes = {"A": x0 + W + 12, "B": x0 + W + 26, "C": x0 + W + 40}
    for src, dst, ln in skips:
        lx = lanes[ln]
        ys, yd = ypos[src] + H / 2, ypos[dst] + H / 2
        f.line([(x0 + W, ys), (lx, ys), (lx, yd), (x0 + W + 1, yd)], BLUE, THIN)
    # detect bus on the left
    dst_row = rows[-1]["i"]
    bx = x0 - 14
    yd = ypos[dst_row] + H / 2
    ys_all = [ypos[s] + H / 2 for s in detect_from]
    for ys in ys_all:
        f.a(f'<path d="M{x0} {ys} L{bx} {ys}" stroke="{BLUE}" stroke-width="{THIN}" fill="none"/>')
    f.line([(bx, ys_all[0]), (bx, yd), (x0 - 1, yd)], BLUE, THIN)
    # stage brackets (far left)
    for stage, (a, b) in stage_of.items():
        ya, yb = ypos[a], ypos[b] + H
        f.a(f'<rect x="{x0 - 38}" y="{ya}" width="8" height="{yb - ya}" fill="#DDDDDD" stroke="#888888"/>')
        vtext(f, x0 - 46, (ya + yb) / 2, stage, size=12.5)
    return ypos[rows[-1]["i"]] + H


def fig_v8n_26n():
    W = 1000
    v8, tv8 = load_layer_table("table_v8n.md")
    t26, t26t = load_layer_table("table_26n.md")
    ops = load_json(HERE, "data", "rknn_path_onnx.json")
    f = Fig(W, 1620)
    tier(f)
    f.text(10, 20, "YOLOv8n và YOLO26n: nc=5, đầu vào 640x640, đã fuse, đường RKNN (end2end tắt)", size=15, weight=700)
    y0 = 108
    for x0, name, rows, total, sub in [
        (62, "yolov8n", v8, tv8, "yolov8.yaml, scale n: [0.33, 0.25, 1024]"),
        (572, "yolo26n", t26, t26t, "yolo26.yaml, scale n: [0.50, 0.25, 1024]")]:
        f.text(x0 + 185, 50, "YOLOv8n" if name == "yolov8n" else "YOLO26n", size=19, weight=700, anchor="middle")
        f.text(x0 + 185, 72, sub, size=12.5, anchor="middle", fill=DARK, mono=True)
    # v8n: backbone 0-9, neck 10-21, head 22 ; 26n: backbone 0-10, neck 11-22, head 23
    column(f, 62, "yolov8n", v8, tv8, {"BACKBONE": (0, 9), "NECK": (10, 21), "HEAD": (22, 22)},
           [(6, 11, "A"), (12, 17, "A"), (4, 14, "B"), (9, 20, "C")], [15, 18, 21], y0)
    ybot = column(f, 572, "yolo26n", t26, t26t, {"BACKBONE": (0, 10), "NECK": (11, 22), "HEAD": (23, 23)},
                  [(6, 12, "A"), (13, 18, "A"), (4, 15, "B"), (10, 21, "C")], [16, 19, 22], y0)
    # totals
    ybot = y0 + 40 * 24 + 4
    f.text(62, y0 + 40 * 23 + 12, f"Tổng: {tv8[0]} tham số, {tv8[1]} GFLOPs", size=13.5, weight=700)
    f.text(572, y0 + 40 * 24 + 12, f"Tổng: {t26t[0]} tham số, {t26t[1]} GFLOPs", size=13.5, weight=700)
    # comparison table
    yt = y0 + 40 * 24 + 40
    d8 = next(r for r in v8 if r["type"] == "Detect")
    d26 = next(r for r in t26 if r["type"] == "Detect")
    p8, p26 = int(d8["params"].replace(",", "")), int(d26["params"].replace(",", ""))
    g8, g26 = float(d8["gflops"]), float(d26["gflops"])
    tot8, tot26 = float(tv8[1]), float(t26t[1])
    k8, k26 = ops["yolov8n"]["conv_kinds"], ops["yolo26n"]["conv_kinds"]

    def kinds(k):
        return "/".join(str(k.get(x, 0)) for x in ("1x1", "3x3 s1", "3x3 s2", "depthwise 3x3"))

    f.text(10, yt, "So sánh", size=15, weight=700)
    yb = f.table(10, yt + 14, [290, 320, 370], ["Hạng mục", "YOLOv8n", "YOLO26n"], [
        ["Khối backbone", "Conv, C2f, SPPF", "Conv, C3k2, SPPF, C2PSA"],
        ["Khối neck", "Upsample, Concat, C2f, Conv", "Upsample, Concat, C3k2, Conv (lớp 22: attn=True)"],
        ["Đầu Detect (yaml)", "reg_max 16 (có DFL; mặc định của tasks.py)", "reg_max 1 (không DFL), end2end: True"],
        ["Đầu ra khi end2end tắt", "[1, 9, 8400] = 4 hộp + 5 lớp", "[1, 9, 8400] = 4 hộp + 5 lớp"],
        ["Tham số của lớp Detect", f"{d8['params']} ({100 * p8 / int(tv8[0].replace(',', '')):.1f}% tổng)",
         f"{d26['params']} ({100 * p26 / int(t26t[0].replace(',', '')):.1f}% tổng)"],
        ["GFLOPs của lớp Detect", f"{d8['gflops']} ({100 * g8 / tot8:.1f}% tổng)",
         f"{d26['gflops']} ({100 * g26 / tot26:.1f}% tổng)"],
        [("lines", ["Conv trong ONNX: 1x1 / 3x3 s1 /", "3x3 s2 / depthwise 3x3"]), kinds(k8), kinds(k26)],
        ["Khối có attention (MatMul, Softmax)", "không", "lớp 10 (C2PSA) và lớp 22 (C3k2, attn=True)"],
    ], size=12.5)
    y = panel(f, 10, yb + 12, 980, [
        [("Phép tính của bộ hình", "b"), (": phần trăm của Detect = Detect / tổng, từ hai cột của bảng lớp.", "t")],
        "Tham số và GFLOPs: layer_table.py (FlopCounterMode, 2 FLOP mỗi MAC), model dựng từ yaml, trọng số ngẫu nhiên.",
        "Ranh giới BACKBONE / NECK / HEAD theo hai danh sách backbone: và head: của yaml; Detect là hàng cuối của head:.",
    ], fill=LB, stroke=BLUE, size=12)
    y = f.legend(10, y + 12, 980, [
        ("ink", "dòng dữ liệu theo thứ tự lớp (from = -1)"),
        ("blue", "đường nối ngoài thứ tự: cột from của yaml (Concat lấy lớp sớm hơn; Detect lấy ba lớp neck)"),
        ("fill:#F5F5F5", "khối CSP (C2f hoặc C3k2); khung xanh đậm: khối có attention"),
    ])
    source(f, y + 8, "Nguồn: ULT cfg/models/v8/yolov8.yaml, cfg/models/26/yolo26.yaml; LOG 2026-10-10_yolo-arch (table_v8n.md, "
           "table_26n.md); data/rknn_path_onnx.json.")
    f.h = f.h
    return f



# =====================================================================
# Hinh 9.2: cac khoi
# =====================================================================
def bx(f, x, y, w, h, title, sub="", fill="white", dashed=False, mono=False, ts=14, ss=12, stroke=None):
    if stroke:
        box(f, x, y, w, h, fill=fill, stroke=stroke, sw=2.2, dashed=dashed)
        cx = x + w / 2
        if sub:
            f.text(cx, y + h * 0.36, title, size=ts, weight=700, anchor="middle", mono=mono)
            f.text(cx, y + h * 0.70, sub, size=ss, anchor="middle", fill=DARK)
        else:
            f.text(cx, y + h / 2, title, size=ts, weight=700, anchor="middle", mono=mono)
    else:
        f.box(x, y, w, h, title, sub, dashed=dashed, mono=mono, title_size=ts, sub_size=ss, fill=fill)


def card(f, x, y, w, title, lines, size=12, fill="white", stroke="#999999", title_size=13.5, dashed=False):
    h = 28 + 17 * len(lines) + 6
    box(f, x, y, w, h, fill=fill, stroke=stroke, sw=1, dashed=dashed, rx=6)
    f.text(x + 10, y + 15, title, size=title_size, weight=700)
    for i, ln in enumerate(lines):
        f.rich(x + 10, y + 36 + 17 * i, ln, size=size)
    return y + h


def circ(f, cx, cy, s="+", r=11):
    f.a(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="white" stroke="#333333" stroke-width="1.2"/>')
    f.text(cx, cy + 0.5, s, size=15, weight=700, anchor="middle")


def fig_blocks():
    W = 1000
    ops = load_json(HERE, "data", "rknn_path_onnx.json")
    o26 = ops["yolo26n"]["ops"]
    f = Fig(W, 2300)
    tier(f)
    f.text(10, 20, "Khối CSP: C2f (YOLOv8n) và C3k2 (YOLO26n)", size=15, weight=700)
    # ---------------- A. C2f and C3k2 ----------------
    box(f, 10, 38, 480, 430, fill="white", stroke="#999999", sw=1, rx=6)
    box(f, 510, 38, 480, 430, fill="white", stroke="#999999", sw=1, rx=6)
    f.text(22, 54, "C2f (YOLOv8n)", size=15, weight=700)
    f.text(522, 54, "C3k2 (YOLO26n), kế thừa C2f", size=15, weight=700)

    def skeleton(x, mid_title, mid_sub, mid_h=92):
        cx = x + 75
        f.text(cx, 76, "x: c1 kênh", size=12.5, anchor="middle", fill=DARK)
        f.line([(cx, 84), (cx, 96)], INK, THIN)
        bx(f, x, 96, 150, 34, "Conv 1x1", "c1 → 2c", mono=True, ts=13.5)
        f.line([(cx, 130), (cx, 146)], INK, THIN)
        bx(f, x, 146, 150, 28, "split (c, c)", mono=True, ts=13)
        ym = 202
        # branch a straight down to concat
        yc = ym + mid_h + 30
        f.line([(x + 25, 174), (x + 25, yc)], BLUE, THIN)
        f.line([(cx + 25, 174), (cx + 25, ym)], BLUE, THIN)
        box(f, x + 45, ym, 130, mid_h, fill="#F5F5F5")
        f.text(x + 110, ym + 16, mid_title, size=13.5, weight=700, anchor="middle")
        f.line([(cx + 25, ym + mid_h), (cx + 25, yc)], BLUE, THIN)
        f.line([(x + 175, ym + mid_h / 2), (x + 200, ym + mid_h / 2), (x + 200, yc)], BLUE, THIN)
        bx(f, x, yc, 215, 28, "Concat (2+n) · c", mono=True, ts=13)
        f.line([(x + 107, yc + 28), (x + 107, yc + 42)], INK, THIN)
        bx(f, x, yc + 42, 215, 34, "Conv 1x1", "(2+n) · c → c2", mono=True, ts=13.5)
        f.line([(x + 107, yc + 76), (x + 107, yc + 92)], INK, THIN)
        f.text(x + 107, yc + 102, "ra: c2 kênh", size=12.5, anchor="middle", fill=DARK)
        return yc + 76

    skeleton(30, "Bottleneck x n", "", 92)
    f.text(30 + 45 + 65, 202 + 40, "Conv 3x3 c → c", size=12, anchor="middle", mono=True)
    f.text(30 + 45 + 65, 202 + 58, "Conv 3x3 c → c", size=12, anchor="middle", mono=True)
    f.text(30 + 45 + 65, 202 + 77, "(+ x nếu shortcut)", size=11.5, anchor="middle", fill=DARK)
    notes_x = 262
    lines_block(f, notes_x, 90, [
        [("c = int(c2 · e), e = 0.5", "c")],
        "Bottleneck: Conv 3x3, rồi Conv 3x3,",
        "kênh giữ nguyên (e = 1.0 trong C2f).",
        "Cộng x chỉ khi shortcut và c1 == c2.",
        "C2f mặc định shortcut=False; yaml",
        "YOLOv8n truyền True ở backbone, không",
        "truyền ở neck.",
        "Đầu ra của nửa a, nửa b và của mọi",
        "Bottleneck đều vào Concat.",
        "Exporter thay forward bằng",
        "forward_split (split thay chunk).",
    ], size=12, lh=16.5)
    card(f, 262, 330, 218, "Ví dụ YOLOv8n lớp 2 (log)", [
        "cv1: Conv 1x1 32 → 32", "Bottleneck: Conv 3x3 16 → 16 (hai lần)", "cv2: Conv 1x1 48 → 32"], size=11.5, fill=LB, stroke=BLUE)
    # C3k2
    skeleton(522, "m: n phần tử", "", 92)
    f.text(522 + 45 + 65, 202 + 48, "một trong ba loại", size=11.5, anchor="middle", fill=DARK)
    f.text(522 + 45 + 65, 202 + 66, "theo cờ attn, c3k", size=11.5, anchor="middle", mono=True)
    cy = 58
    cy = card(f, 745, 62, 238, "(1) attn=False, c3k=False", [
        "Bottleneck(c, c), e = 0.5:", "Conv 3x3 c → c/2, Conv 3x3 c/2 → c", "YOLO26n lớp 2, 4"], size=11.5) + 8
    cy = card(f, 745, cy, 238, "(2) c3k=True", [
        "C3k(c, c, 2): cv1 và cv2 là Conv 1x1", "c → c/2; 2 Bottleneck 3x3 sau cv1;", "Concat; cv3 Conv 1x1",
        "YOLO26n lớp 6, 8, 13, 16, 19"], size=11.5) + 8
    cy = card(f, 745, cy, 238, "(3) attn=True", [
        "Sequential(Bottleneck, PSABlock)", "attn được xét trước c3k", "YOLO26n lớp 22: [1024, True, 0.5, True]"],
        size=11.5, stroke=BLUE) + 6
    f.text(745, cy + 8, "Khung giống C2f; shortcut mặc định True.", size=11.5, fill=DARK)
    card(f, 745, cy + 20, 238, "Ví dụ YOLO26n lớp 2 (log)", [
        "cv1: Conv 1x1 32 → 32", "Bottleneck: Conv 3x3 16 → 8, 8 → 16", "cv2: Conv 1x1 48 → 64"], size=11, fill=LB, stroke=BLUE)

    # ---------------- B. SPPF ----------------
    yB = 484
    box(f, 10, yB, 980, 200, fill="white", stroke="#999999", sw=1, rx=6)
    f.text(22, yB + 16, "SPPF (cả hai model)", size=15, weight=700)
    yy = yB + 58
    f.text(30, yy + 22, "x", size=13, weight=700)
    f.line([(40, yy + 22), (62, yy + 22)], INK, THIN)
    bx(f, 62, yy, 116, 44, "Conv 1x1", "c1 → c1/2", mono=True, ts=13)
    xs = [210, 330, 450]
    f.line([(178, yy + 22), (208, yy + 22)], INK, THIN)
    for i, mx in enumerate(xs):
        bx(f, mx, yy, 100, 44, "MaxPool", "5x5, s1, pad 2", mono=True, ts=13, ss=11.5)
        if i < 2:
            f.line([(mx + 100, yy + 22), (xs[i + 1] - 1, yy + 22)], INK, THIN)
    bx(f, 600, yy, 120, 44, "Concat", "4 · c1/2", mono=True, ts=13)
    bx(f, 750, yy, 120, 44, "Conv 1x1", "→ c2", mono=True, ts=13)
    f.line([(720, yy + 22), (748, yy + 22)], INK, THIN)
    f.line([(550, yy + 22), (598, yy + 22)], INK, THIN)
    # bus above: cv1 and each maxpool output into Concat
    busy = yy - 16
    f.a(f'<path d="M120 {yy} L120 {busy} L660 {busy}" stroke="{BLUE}" stroke-width="{THIN}" fill="none"/>')
    for mx in xs[:2]:
        f.a(f'<path d="M{mx + 50} {yy} L{mx + 50} {busy}" stroke="{BLUE}" stroke-width="{THIN}" fill="none"/>')
    f.line([(660, busy), (660, yy - 1)], BLUE, THIN)
    circ(f, 905, yy + 22)
    f.line([(870, yy + 22), (893, yy + 22)], INK, THIN)
    f.line([(917, yy + 22), (960, yy + 22)], INK, THIN)
    f.text(968, yy + 22, "ra", size=12.5, anchor="start", fill=DARK)
    f.line([(36, yy + 32), (36, yy + 58), (905, yy + 58), (905, yy + 34)], BLUE, THIN, dashed=True)
    f.text(470, yy + 74, "shortcut (nét đứt): chỉ YOLO26n, và chỉ khi c1 == c2", size=12, fill=DARK, anchor="middle")
    lines_block(f, 22, yB + 152, [
        "YOLOv8n: cv1 có SiLU, không cộng x.   YOLO26n: truyền shortcut=True, và cv1 không có activation (act=False).   Ví dụ c1 = 256 (lớp 9, log):",
        "cv1 256 → 128, Concat 512 kênh, cv2 512 → 256. Lớp RKNN của cv1: ConvExSwish ở YOLOv8n, Conv trơn ở YOLO26n (T3, trọng số ngẫu nhiên).",
    ], size=12, lh=18)

    # ---------------- C. C2PSA / PSABlock / Attention ----------------
    yC = 700
    box(f, 10, yC, 980, 540, fill="white", stroke="#999999", sw=1, rx=6)
    f.text(22, yC + 16, "C2PSA, PSABlock, Attention (chỉ YOLO26n; cùng PSABlock trong C3k2 lớp 22)", size=15, weight=700)
    # C2PSA column
    x = 40
    f.text(x + 100, yC + 48, "C2PSA, lớp 10: 256 × 20 × 20", size=13, weight=700, anchor="middle")
    y1 = yC + 64
    bx(f, x, y1, 200, 36, "Conv 1x1", "256 → 256 (2c, c = 128)", mono=True, ts=13, ss=11.5)
    f.line([(x + 100, y1 + 36), (x + 100, y1 + 52)], INK, THIN)
    bx(f, x, y1 + 52, 200, 28, "split (128, 128)", mono=True, ts=13)
    f.line([(x + 20, y1 + 80), (x + 20, y1 + 236)], BLUE, THIN)
    f.line([(x + 120, y1 + 80), (x + 120, y1 + 100)], BLUE, THIN)
    bx(f, x + 50, y1 + 100, 140, 56, "PSABlock", "x n (n = 1)", fill="#F5F5F5", stroke=BLUE, ts=13.5)
    f.line([(x + 120, y1 + 156), (x + 120, y1 + 236)], BLUE, THIN)
    bx(f, x, y1 + 236, 200, 28, "Concat (256)", mono=True, ts=13)
    f.line([(x + 100, y1 + 264), (x + 100, y1 + 280)], INK, THIN)
    bx(f, x, y1 + 280, 200, 36, "Conv 1x1", "256 → 256", mono=True, ts=13, ss=11.5)
    f.line([(x + 100, y1 + 316), (x + 100, y1 + 334)], INK, THIN)
    f.text(x + 100, y1 + 346, "ra: 256 × 20 × 20", size=12.5, anchor="middle", fill=DARK)
    # PSABlock column
    x = 300
    f.text(x + 130, yC + 48, "PSABlock (c = 128), x: 128 × 20 × 20", size=13, weight=700, anchor="middle")
    bx(f, x + 20, y1 + 14, 220, 44, "Attention", "2 đầu, attn_ratio 0.5", fill="#F5F5F5", stroke=BLUE, ts=13.5)
    circ(f, x + 130, y1 + 96)
    f.line([(x + 130, y1 + 6), (x + 130, y1 + 14)], INK, THIN, head=False)
    f.line([(x + 130, y1 + 58), (x + 130, y1 + 84)], INK, THIN)
    f.line([(x + 4, y1 + 6), (x + 4, y1 + 96), (x + 117, y1 + 96)], BLUE, THIN, dashed=True)
    f.line([(x + 4, y1 + 6), (x + 130, y1 + 6)], BLUE, THIN, dashed=True, head=False)
    bx(f, x + 20, y1 + 126, 220, 36, "Conv 1x1 + SiLU", "128 → 256", mono=True, ts=13, ss=11.5)
    f.line([(x + 130, y1 + 107), (x + 130, y1 + 126)], INK, THIN)
    f.line([(x + 130, y1 + 162), (x + 130, y1 + 176)], INK, THIN)
    bx(f, x + 20, y1 + 176, 220, 36, "Conv 1x1, không act", "256 → 128", mono=True, ts=13, ss=11.5)
    circ(f, x + 130, y1 + 244)
    f.line([(x + 130, y1 + 212), (x + 130, y1 + 232)], INK, THIN)
    f.line([(x + 4, y1 + 96), (x + 4, y1 + 244), (x + 117, y1 + 244)], BLUE, THIN, dashed=True)
    f.line([(x + 130, y1 + 256), (x + 130, y1 + 276)], INK, THIN)
    f.text(x + 130, y1 + 288, "ra: 128 × 20 × 20", size=12.5, anchor="middle", fill=DARK)
    f.text(x + 130, y1 + 328, "x = x + attn(x);  x = x + ffn(x)", size=12, anchor="middle", mono=True)
    f.text(x + 130, y1 + 346, "(nét đứt: hai phép cộng residual)", size=12, anchor="middle", fill=DARK)
    # Attention column
    x = 600
    f.text(x + 195, yC + 48, "Attention (dim = 128, N = H · W = 400)", size=13, weight=700, anchor="middle")
    bx(f, x + 40, y1 - 4, 310, 38, "qkv: Conv 1x1, không act", "128 → 256", mono=True, ts=12.5, ss=11.5)
    f.line([(x + 195, y1 + 34), (x + 195, y1 + 48)], INK, THIN)
    bx(f, x + 40, y1 + 48, 310, 40, "view (2 đầu, 128, 400), split", "q: 32, k: 32, v: 64 kênh mỗi đầu", ts=12.5, ss=11.5)
    # left: q,k branch ; right: v
    f.line([(x + 110, y1 + 88), (x + 110, y1 + 112)], BLUE, THIN)
    f.line([(x + 290, y1 + 88), (x + 290, y1 + 112)], BLUE, THIN)
    bx(f, x, y1 + 112, 200, 60, "softmax((q·scale)ᵀ k)", "400 × 400 mỗi đầu", fill="#F5F5F5", stroke=BLUE, ts=12.5, ss=11.5)
    bx(f, x + 230, y1 + 112, 150, 60, "pe: Conv 3x3", "depthwise, không act", mono=False, ts=12.5, ss=11.5)
    # v also into v . attn^T
    f.line([(x + 110, y1 + 172), (x + 110, y1 + 196)], BLUE, THIN)
    bx(f, x + 30, y1 + 196, 160, 38, "v · attnᵀ", "view C, H, W", ts=12.5, ss=11.5)
    f.a(f'<path d="M{x + 290} {y1 + 100} L{x + 212} {y1 + 100} L{x + 212} {y1 + 215}" stroke="{BLUE}" stroke-width="{THIN}" fill="none" stroke-dasharray="5 4"/>')
    f.line([(x + 212, y1 + 215), (x + 191, y1 + 215)], BLUE, THIN, dashed=True)
    circ(f, x + 190 - 80, y1 + 270)
    f.line([(x + 110, y1 + 234), (x + 110, y1 + 270), (x + 121, y1 + 270)], INK, THIN) if False else None
    f.line([(x + 110, y1 + 234), (x + 110, y1 + 258)], INK, THIN)
    circ(f, x + 110, y1 + 270)
    f.line([(x + 305, y1 + 172), (x + 305, y1 + 270), (x + 122, y1 + 270)], BLUE, THIN)
    bx(f, x + 30, y1 + 296, 160, 36, "proj: Conv 1x1", "128 → 128, không act", mono=False, ts=12.5, ss=11.5)
    f.line([(x + 110, y1 + 282), (x + 110, y1 + 296)], INK, THIN)
    f.line([(x + 110, y1 + 332), (x + 110, y1 + 350)], INK, THIN)
    f.text(x + 110, y1 + 360, "ra: 128 × 20 × 20", size=12.5, anchor="middle", fill=DARK)
    y = card(f, x + 230, y1 + 292, 150, "ONNX (hai khối)", [
        f"MatMul {o26.get('MatMul', 0)}, Softmax {o26.get('Softmax', 0)},", f"Transpose {o26.get('Transpose', 0)}",
        "(đường RKNN)"], size=11.5, fill=LB, stroke=BLUE)
    yb = y1 + 392
    y = panel(f, 22, yb, 956, [
        "C3k2 lớp 22 (attn=True) = Sequential(Bottleneck 3x3 128 → 64 → 128, PSABlock) cùng cấu trúc attention (log, model.22).",
        "Đầu vào mỗi khối attention là lưới P5 20 x 20 của đầu vào 640 x 640: 400 token. Số đầu = max(c // 64, 1) = 2 với c = 128.",
        [("Trên RKNN (T3, trọng số ngẫu nhiên): cả hai khối thành lớp exSDPAttention, xem Hình 9.3 và 9.4.", "b")],
    ], size=12, lh=18)

    # ---------------- D. Detect ----------------
    yD = yC + 540 + 16
    box(f, 10, yD, 980, 640, fill="white", stroke="#999999", sw=1, rx=6)
    f.text(22, yD + 16, "Đầu Detect (nc = 5): ba mức P3, P4, P5 với đầu vào 64, 128, 256 kênh", size=15, weight=700)
    # left: v8n
    xl, xr = 24, 520
    f.text(xl, yD + 44, "YOLOv8n (legacy=True, reg_max 16)", size=14, weight=700)
    f.text(xr, yD + 44, "YOLO26n (legacy=False, reg_max 1)", size=14, weight=700)
    yy = yD + 62

    def stack(x, y, items, w=210, h=30, fill="white"):
        for i, (t, s) in enumerate(items):
            bx(f, x, y + i * (h + 12), w, h, t, s, mono=True, ts=12, ss=11, fill=fill)
            if i:
                f.line([(x + w / 2, y + i * (h + 12) - 12), (x + w / 2, y + i * (h + 12))], INK, THIN)
        return y + len(items) * (h + 12) - 12

    f.text(xl + 105, yy + 6, "nhánh hộp (cv2)", size=12.5, weight=700, anchor="middle")
    f.text(xl + 335, yy + 6, "nhánh lớp (cv3)", size=12.5, weight=700, anchor="middle")
    e1 = stack(xl, yy + 16, [("Conv 3x3", "x → 64"), ("Conv 3x3", "64 → 64"), ("Conv2d 1x1", "64 → 64 = 4 · 16")], w=210, h=36)
    e2 = stack(xl + 230, yy + 16, [("Conv 3x3", "x → 64"), ("Conv 3x3", "64 → 64"), ("Conv2d 1x1", "64 → 5")], w=210, h=36)
    ycat = e1 + 22
    f.line([(xl + 105, e1), (xl + 105, ycat)], BLUE, THIN)
    f.line([(xl + 335, e2), (xl + 335, ycat)], BLUE, THIN)
    bx(f, xl, ycat, 210, 40, "nối 3 mức", "boxes [1, 64, 8400]", mono=False, ts=12.5, ss=11.5)
    bx(f, xl + 230, ycat, 210, 40, "nối 3 mức", "scores [1, 5, 8400]", mono=False, ts=12.5, ss=11.5)
    yd = ycat + 62
    f.line([(xl + 105, ycat + 40), (xl + 105, yd)], BLUE, THIN)
    bx(f, xl, yd, 210, 54, "DFL", "softmax 16 bin, Conv 1x1 16 → 1", mono=False, ts=13, ss=11.5, fill="#F5F5F5")
    f.line([(xl + 105, yd + 54), (xl + 105, yd + 74)], BLUE, THIN)
    bx(f, xl, yd + 74, 210, 40, "dist2bbox · stride", "boxes [1, 4, 8400]", ts=12.5, ss=11.5)
    bx(f, xl + 230, yd + 74, 210, 40, "sigmoid", "scores [1, 5, 8400]", ts=12.5, ss=11.5)
    f.line([(xl + 335, ycat + 40), (xl + 335, yd + 74)], BLUE, THIN)
    f.line([(xl + 105, yd + 114), (xl + 105, yd + 134), (xl + 220, yd + 134)], BLUE, THIN, head=False)
    f.line([(xl + 335, yd + 114), (xl + 335, yd + 134), (xl + 220, yd + 134)], BLUE, THIN, head=False)
    f.line([(xl + 220, yd + 134), (xl + 220, yd + 150)], BLUE, THIN)
    bx(f, xl + 60, yd + 150, 320, 40, "ra: [1, 9, 8400]", "4 hộp (xywh) + 5 lớp", mono=True, ts=13, ss=11.5, fill="#E8E8E8")
    f.line([(xl + 220, yd + 190), (xl + 220, yd + 208)], GRAY, THIN, dashed=True)
    bx(f, xl + 60, yd + 208, 320, 36, "NMS ngoài đồ thị (host)", "", ts=12.5, dashed=True)
    # right: 26n
    f.text(xr + 105, yy + 6, "nhánh hộp (cv2)", size=12.5, weight=700, anchor="middle")
    f.text(xr + 335, yy + 6, "nhánh lớp (cv3)", size=12.5, weight=700, anchor="middle")
    e1 = stack(xr, yy + 16, [("Conv 3x3", "x → 16"), ("Conv 3x3", "16 → 16"), ("Conv2d 1x1", "16 → 4 = 4 · 1")], w=210, h=36)
    e2 = stack(xr + 230, yy + 16, [("DWConv 3x3", "x, depthwise"), ("Conv 1x1", "x → 64"), ("DWConv 3x3", "64, depthwise"),
                                   ("Conv 1x1", "64 → 64"), ("Conv2d 1x1", "64 → 5")], w=210, h=30)
    ycat2 = max(e1, e2) + 22
    f.line([(xr + 105, e1), (xr + 105, ycat2)], BLUE, THIN)
    f.line([(xr + 335, e2), (xr + 335, ycat2)], BLUE, THIN)
    bx(f, xr, ycat2, 210, 40, "nối 3 mức", "boxes [1, 4, 8400]", ts=12.5, ss=11.5)
    bx(f, xr + 230, ycat2, 210, 40, "nối 3 mức", "scores [1, 5, 8400]", ts=12.5, ss=11.5)
    yd2 = ycat2 + 62
    f.line([(xr + 105, ycat2 + 40), (xr + 105, yd2)], BLUE, THIN)
    bx(f, xr, yd2, 210, 40, "dfl = Identity", "không có DFL", ts=12.5, ss=11.5, fill="#F5F5F5")
    f.line([(xr + 105, yd2 + 40), (xr + 105, yd2 + 60)], BLUE, THIN)
    bx(f, xr, yd2 + 60, 210, 40, "dist2bbox · stride", "boxes [1, 4, 8400]", ts=12.5, ss=11.5)
    bx(f, xr + 230, yd2 + 60, 210, 40, "sigmoid", "scores [1, 5, 8400]", ts=12.5, ss=11.5)
    f.line([(xr + 335, ycat2 + 40), (xr + 335, yd2 + 60)], BLUE, THIN)
    ya = yd2 + 120
    f.line([(xr + 105, yd2 + 100), (xr + 105, ya)], BLUE, THIN, head=False)
    f.line([(xr + 335, yd2 + 100), (xr + 335, ya)], BLUE, THIN, head=False)
    f.a(f'<path d="M{xr + 105} {ya} L{xr + 335} {ya}" stroke="{BLUE}" stroke-width="{THIN}" fill="none"/>')
    f.line([(xr + 220, ya), (xr + 220, ya + 14)], BLUE, THIN)
    bx(f, xr, ya + 14, 215, 56, "(a) end2end tắt (RKNN)", "ra [1, 9, 8400], NMS ngoài", mono=False, ts=12.5, ss=11.5, fill="#E8E8E8")
    bx(f, xr + 225, ya + 14, 215, 56, "(b) end2end bật (nms=False)", "split, topk, gather", mono=False, ts=12.5, ss=11.5, fill="#E8E8E8", dashed=True)
    f.line([(xr + 332, ya + 70), (xr + 332, ya + 86)], GRAY, THIN, dashed=True)
    bx(f, xr + 225, ya + 86, 215, 40, "ra: [1, 300, 6]", "x1, y1, x2, y2, điểm, lớp", mono=True, ts=12.5, ss=11, dashed=True)
    # notes below the Detect panel
    yP = yD + 640 + 12
    y = panel(f, 10, yP, 980, [
        [("Mặc định xuất: ", "b"), ("nms không đặt, nên model.end2end = (nms is False) = False; với rknn dòng sau còn tắt lại end2end khi nms=False.", "t")],
        [("NMS-free không phải không hậu xử lý: ", "b"), ("(b) vẫn có topk và gather trong đồ thị (đầu ra tối đa 300 hộp); (a) không có chúng và cần NMS ngoài.", "t")],
        "Nhánh một-một (one2one) là bản sao của cv2, cv3 tạo khi end2end=True; fuse() xóa nhánh không dùng, nên (a) chỉ còn cv2, cv3.",
    ], size=12, lh=19, fill=LB, stroke=BLUE)
    y = f.unknown(10, y + 8, [
        "YOFF tr.6 gọi nhánh một-một là mặc định; UDOC và mã nguồn (validator.py:163, exporter.py:683) cho nhánh một-nhiều khi không đặt nms.",
        "Hai nguồn mâu thuẫn; hình theo mã nguồn. Đường RKNN dùng nhánh một-nhiều ở cả hai cách đọc."], w=980, size=11.5)
    yl = y + 12
    y = f.legend(10, yl, 980, [
        ("ink", "luồng tuần tự"), ("blue", "luồng song song hoặc rẽ nhánh (nửa a, nối tắt, hai nhánh hộp và lớp)"),
        ("fill:#F5F5F5", "khối con của khối đang vẽ; khung xanh đậm: có attention"),
        ("fill:" + LB, "số liệu hoặc nhận xét của bộ hình (từ log, đếm op)"),
    ])
    source2(f, y + 8, ["Nguồn: ULT nn/modules/block.py:229-240, 291-322, 460-484, 1072-1130, 1274-1336, 1339-1386, 1444-1496; head.py:107-142, 168-193,",
                       "241-285; tasks.py:2126-2127, 2194-2196; engine/validator.py:162-163; engine/exporter.py:682-688; LOG 2026-10-10_yolo-arch; YOFF tr.6; UDOC."])
    return f



# =====================================================================
# Hinh 9.3: duong xuat
# =====================================================================
def rknn_layer_counts(model):
    """Layer-type counts of the RKNN layer table; asserts the three core_mask files agree."""
    st = {m: layer_stats(os.path.join(PHASEA, f"layers_{model}_{m}.txt")) for m in ("AUTO", "CORE_0", "CORE_0_1_2")}
    assert st["AUTO"]["ops"] == st["CORE_0"]["ops"] == st["CORE_0_1_2"]["ops"]
    return st["AUTO"]


def fig_export():
    W = 1000
    ops = load_json(HERE, "data", "rknn_path_onnx.json")
    onnx_b = load_json(HERE, "data", "ops_via_exporter.json")
    L8, L26 = rknn_layer_counts("yolov8n"), rknn_layer_counts("yolo26n")
    f = Fig(W, 1500)
    tier(f)
    f.tier(f.w - 100 - 7.4 * 9 - 80, 8, "T3 đo")
    f.text(10, 20, 'YOLO(pt).export(format="rknn", quantize=8): từ lớp PyTorch đến lớp RKNN', size=15, weight=700)
    # ---------------- three stages ----------------
    sx = [10, 345, 680]
    sw = 310
    titles = ["1. PyTorch: chuẩn bị model", "2. ONNX", "3. RKNN (toolkit trên PC)"]
    steps = [
        [["end2end = (nms is False): mặc định False;", "với rknn còn tắt lại nếu nms=False.", "(exporter.py:683-688)"],
         ["C2f.forward = forward_split; C3k2 kế thừa", "C2f nên cũng đổi: split thay chunk.", "(exporter.py:908-910)"],
         ["Bọc _NormalizeCoords khi rknn, quantize=8,", "detect, end2end tắt: chia 4 tọa độ hộp", "cho [w, h, w, h], rồi slice và concat.", "(exporter.py:1100-1117)"]],
        [["opset = min(opset or 19, 19)", "(exporter.py:1538)"],
         ["torch2onnx: input images, output output0", "(exporter.py:1120-1128)"],
         ["onnxslim.slim khi simplify; mặc định True", "(default.yaml:90, exporter.py:1139)"],
         ["INT8: file ONNX bị xóa sau khi build", "(exporter.py:1564-1566)"]],
        [["config(mean_values 0, std_values 255,", "target_platform); load_onnx", "(rknn.py:74-76)"],
         ["build(do_quantization=True, dataset,", "rknn_batch_size); dataset.txt là danh sách", "ảnh calibration (rknn.py:77-80;", "exporter.py:1543-1552)"],
         ["export_rknn ghi file .rknn", "(rknn.py:81)"]],
    ]
    hh = 214
    for i in range(3):
        box(f, sx[i], 38, sw, hh, fill="white", stroke="#999999", sw=1, rx=6)
        f.text(sx[i] + 12, 54, titles[i], size=14.5, weight=700)
        y = 76
        for blk in steps[i]:
            for k, ln in enumerate(blk):
                f.text(sx[i] + 12, y, ln, size=12, fill=DARK if ln.startswith("(") else INK)
                y += 16
            y += 6
    for i in range(2):
        f.line([(sx[i] + sw, 150), (sx[i + 1] - 1, 150)], BLUE, THICK)
    # ---------------- Table A: ONNX ops ----------------
    yA = 270
    f.text(10, yA, "Op trong ONNX (YOLO(...).export, nc=5, 640x640, trọng số ngẫu nhiên)", size=13.5, weight=700)
    b8, b26 = onnx_b["yolov8n|B_opset19_simplify"]["ops"], onnx_b["yolo26n|B_opset19_simplify"]["ops"]
    r8, r26 = ops["yolov8n"]["ops"], ops["yolo26n"]["ops"]
    names = [k for k, _ in sorted(r26.items(), key=lambda kv: -max(kv[1], r8.get(kv[0], 0)))]
    for k in r8:
        if k not in names:
            names.append(k)
    rows, fills = [], {}
    for ri, k in enumerate(names):
        cells = [C(k), str(b8.get(k, 0)), str(r8.get(k, 0)), str(b26.get(k, 0)), str(r26.get(k, 0))]
        if b8.get(k, 0) != r8.get(k, 0) or b26.get(k, 0) != r26.get(k, 0):
            fills[ri] = LB
        rows.append(cells)
    rows.append([[("Tổng nút", "b")], str(sum(b8.values())), str(sum(r8.values())), str(sum(b26.values())), str(sum(r26.values()))])
    yAe = f.table(10, yA + 14, [100, 95, 95, 95, 95], ["Op", "v8n onnx", "v8n rknn", "26n onnx", "26n rknn"], rows, size=12, line_h=15,
                  fills=fills)
    f.text(10, yAe + 14, "onnx: format=onnx (opset 19, onnxslim). rknn: ONNX thật đưa vào onnx2rknn.", size=11.5, fill=DARK, italic=True)
    f.text(10, yAe + 30, "Nền xanh: hàng khác nhau, do _NormalizeCoords (Concat, Slice, Div).", size=11.5, fill=DARK, italic=True)
    # ---------------- Table B: RKNN layers ----------------
    f.text(510, yA, "Lớp RKNN (T3, INT8, eval_perf 2.3.2, NPU 1 GHz)", size=13.5, weight=700)
    order = ["ConvExSwish", "Conv", "ConvAdd", "Add", "Concat", "Split", "Reshape", "MaxPool", "Resize", "Mul", "Sub", "Sigmoid",
             "exSoftmax13", "Transpose", "exSDPAttention", "InputOperator", "OutputOperator"]
    assert set(order) == set(L8["ops"]) | set(L26["ops"])
    corr = {"ConvExSwish": "Conv + Sigmoid + Mul", "Conv": "Conv không có SiLU", "ConvAdd": "Conv + Add", "Add": "Add",
            "Concat": "Concat", "Split": "Split, Slice", "Reshape": "Reshape", "MaxPool": "MaxPool", "Resize": "Resize",
            "Mul": "Mul", "Sub": "Sub", "Sigmoid": "Sigmoid", "exSoftmax13": "Softmax của DFL", "Transpose": "Transpose của DFL",
            "exSDPAttention": "MatMul, Softmax (attention)", "InputOperator": "", "OutputOperator": ""}
    rowsB = []
    for k in order:
        tgt = "CPU" if (k in ("InputOperator", "OutputOperator", "Transpose")) else "NPU"
        rowsB.append([C(k), str(L8["ops"].get(k, 0)), str(L26["ops"].get(k, 0)), tgt, corr[k]])
    rowsB.append([[("Tổng lớp", "b")], str(L8["n"]), str(L26["n"]), "", ""])
    yBe = f.table(510, yA + 14, [120, 52, 52, 52, 204], ["Lớp", "v8n", "26n", "Đích", "Ứng với op ONNX (suy ra)"], rowsB, size=12, line_h=15,
                  fills={len(order): "#F5F5F5"})
    f.text(510, yBe + 14, f"Lớp CPU ngoài Input, Output: YOLOv8n {len(L8['cpu'])} (Transpose), YOLO26n {len(L26['cpu'])}.", size=11.5, fill=DARK, italic=True)
    # ---------------- derived identities ----------------
    yn = max(yAe + 44, yBe + 30)
    c_on8, c_on26 = r8["Conv"], r26["Conv"]
    c8 = L8["ops"].get("ConvExSwish", 0) + L8["ops"].get("Conv", 0) + L8["ops"].get("ConvAdd", 0)
    c26 = L26["ops"].get("ConvExSwish", 0) + L26["ops"].get("Conv", 0) + L26["ops"].get("ConvAdd", 0)
    a26 = L26["ops"].get("Add", 0) + L26["ops"].get("ConvAdd", 0)
    assert (c_on8, c_on26, c8, c26, a26, r26["Add"], L8["ops"]["Add"], r8["Add"]) == (64, 102, 64, 102, 22, 22, 8, 8)
    y = panel(f, 10, yn, 980, [
        [("Phép tính của bộ hình", "b"), (" (suy ra từ hai bảng, không phải câu của vendor):", "t")],
        f"Conv trong ONNX = ConvExSwish + Conv + ConvAdd:  YOLOv8n {c_on8} = {L8['ops']['ConvExSwish']} + {L8['ops']['Conv']} + 0;  "
        f"YOLO26n {c_on26} = {L26['ops']['ConvExSwish']} + {L26['ops']['Conv']} + {L26['ops']['ConvAdd']}.",
        f"Add trong ONNX của YOLO26n = Add + ConvAdd:  {r26['Add']} = {L26['ops']['Add']} + {L26['ops']['ConvAdd']};  YOLOv8n: {r8['Add']} = {L8['ops']['Add']} (không có ConvAdd).",
        f"Attention: ONNX có MatMul {r26['MatMul']}, Softmax {r26['Softmax']}, Transpose {r26['Transpose']}; bảng lớp RKNN không có lớp MatMul, Softmax, "
        f"Transpose, chỉ có {L26['ops']['exSDPAttention']} exSDPAttention.",
    ], fill=LB, stroke=BLUE, size=12, lh=19)
    y = panel(f, 10, y + 10, 980, [
        [("T3 (cấu trúc, trọng số ngẫu nhiên): ", "b"), ("YOLO26n: 180 lớp trên NPU, ngoài InputOperator và OutputOperator không có lớp CPU; ", "t"),
         ("YOLOv8n: 1 lớp CPU (Transpose).", "t")],
        "Điều kiện: nc=5, INT8, 40 ảnh calibration, ba core_mask (AUTO, CORE_0, CORE_0_1_2) cho cùng số lớp theo từng loại.",
    ], fill=RB, stroke=GREEN, size=12, lh=19)
    y = f.unknown(10, y + 10, [
        "ghép Conv + Sigmoid + Mul thành ConvExSwish: UG232 tr.142 chỉ liệt kê Conv+Sigmoid(Tanh/Elu/Silu...); tên ConvExSwish không có trong tài liệu T1;",
        "quy tắc nhận chuỗi MatMul, Softmax, MatMul thành exSDPAttention (UG232 tr.148 chỉ có GLU và LayerNorm);",
        "cách gộp hay tách Concat, Slice, Div, Reshape: số lớp RKNN lệch số nút ONNX (ví dụ Div 2 ở ONNX, không có lớp Div) và nguồn không giải thích."],
        w=980, size=11.5)
    y = f.legend(10, y + 10, 980, [
        ("fill:" + LB, "phép tính hoặc nhận xét của bộ hình"), ("fill:" + RB, "T3: đo trên board, có file log"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho"),
    ])
    source2(f, y + 8, ["Nguồn: ULT engine/exporter.py:683-688, 908-910, 1100-1128, 1139, 1538, 1543-1566; utils/export/rknn.py:74-81; utils/export/engine.py:17-48;",
                       "cfg/default.yaml:90; data/ops_via_exporter.json, data/rknn_path_onnx.json; LOG 2026-10-10_yolo-phaseA/raw/layers_*.txt; UG232 tr.142, 148."])
    return f



# =====================================================================
# Hinh 9.4: ma tran khoi x tieu chi
# =====================================================================
def _cw(ch, size, bold=False):
    if ord(ch) > 0x2E80:
        return size * 1.0
    return size * (0.52 if bold else 0.47)


def wrap(text, colw, size=11.5, bold=False):
    """Greedy word wrap by estimated glyph width (CJK counts as a full em)."""
    avail = colw - 18
    out, cur, w = [], "", 0.0
    for word in text.split(" "):
        ww = sum(_cw(c, size, bold) for c in word)
        sp = _cw(" ", size, bold) if cur else 0
        if cur and w + sp + ww > avail:
            out.append(cur)
            cur, w = word, ww
        else:
            cur = (cur + " " + word) if cur else word
            w += sp + ww
    if cur:
        out.append(cur)
    return out


def matrix(f, x, y, widths, header, rows, fills, size=11.5, lh=15):
    """rows: list of lists of str; fills: {(r, c): color}. Returns the bottom y."""
    head_h = 30
    f.a(f'<rect x="{x}" y="{y}" width="{sum(widths)}" height="{head_h}" fill="#E8E8E8"/>')
    cx = x
    for wd, hd in zip(widths, header):
        f.text(cx + 8, y + head_h / 2, hd, size=12.5, weight=700)
        cx += wd
    cy = y + head_h
    for ri, row in enumerate(rows):
        wrapped = [wrap(c, wd, size + (1 if ci == 0 else 0), ci == 0) for ci, (c, wd) in enumerate(zip(row, widths))]
        n = max(len(w) for w in wrapped)
        rh = 12 + lh * n
        cx = x
        for ci, (wd, w) in enumerate(zip(widths, wrapped)):
            if (ri, ci) in fills:
                f.a(f'<rect x="{cx}" y="{cy}" width="{wd}" height="{rh}" fill="{fills[(ri, ci)]}"/>')
            for k, ln in enumerate(w):
                f.text(cx + 8, cy + 6 + lh / 2 + lh * k, ln, size=size + (1 if ci == 0 else 0), weight=700 if ci == 0 else 400)
            cx += wd
        f.a(f'<path d="M{x} {cy} L{x + sum(widths)} {cy}" stroke="#BBBBBB" stroke-width="0.8"/>')
        cy += rh
    f.a(f'<rect x="{x}" y="{y}" width="{sum(widths)}" height="{cy - y}" fill="none" stroke="#999999" stroke-width="1"/>')
    cx = x
    for wd in widths[:-1]:
        cx += wd
        f.a(f'<path d="M{cx} {y} L{cx} {cy}" stroke="#CCCCCC" stroke-width="0.8"/>')
    return cy


def fig_matrix():
    W = 1100
    ops = load_json(HERE, "data", "rknn_path_onnx.json")
    o8, o26 = ops["yolov8n"], ops["yolo26n"]
    onnx_b = load_json(HERE, "data", "ops_via_exporter.json")
    e2e = onnx_b["yolo26n|C_opset19_simplify_end2end"]["ops"]
    S8 = layer_stats(os.path.join(PHASEA, "layers_yolov8n_CORE_0_1_2.txt"))
    S26 = layer_stats(os.path.join(PHASEA, "layers_yolo26n_CORE_0_1_2.txt"))
    ST = layer_stats(os.path.join(SILU, "trained_silu_5c_CORE_0_1_2_layers.txt"))
    assert ST["ops"] == S8["ops"] and {k: dict(v) for k, v in ST["wl"].items()} == {k: dict(v) for k, v in S8["wl"].items()}
    # depthwise 3x3 layers of YOLO26n (weight (1,C,3,3)), core_mask AUTO
    dw = []
    for ln in open(os.path.join(PHASEA, "layers_yolo26n_AUTO.txt"), encoding="utf-8", errors="replace"):
        if re.match(r"^\d+\s+\S+\s+\S+\s+(NPU|CPU)\s", ln) and re.search(r",\(1,\d+,3,3\),", ln):
            mac = re.search(r"\s(\d+\.\d+)/\d+\.\d+/\d+\.\d+\s", ln)
            dw.append((ln.split()[1], float(mac.group(1))))
    assert len(dw) == 8 and sum(1 for k, _ in dw if k == "ConvExSwish") == 6 and sum(1 for k, _ in dw if k == "Conv") == 2
    dw_lo, dw_hi = min(m for _, m in dw), max(m for _, m in dw)

    def wl(S, op):
        c = S["wl"][op]
        return c.get("multi", 0), c.get("core0", 0), c.get("none", 0), sum(c.values())

    cat8, cat26 = wl(S8, "Concat"), wl(S26, "Concat")
    add8, add26 = wl(S8, "Add"), wl(S26, "Add")
    cv8, cv26 = wl(S8, "Conv"), wl(S26, "Conv")
    cadd = wl(S26, "ConvAdd")
    cs8, cs26 = wl(S8, "ConvExSwish"), wl(S26, "ConvExSwish")
    sp8, sp26 = wl(S8, "Split"), wl(S26, "Split")
    mp8, mp26 = wl(S8, "MaxPool"), wl(S26, "MaxPool")
    rs8, rs26 = wl(S8, "Resize"), wl(S26, "Resize")
    sd = wl(S26, "exSDPAttention")
    assert (cs8[3], cs8[1], cs26[3], cs26[1]) == (57, 57, 87, 87) and sd[3] == 2 and sd[1] == 2
    assert (mp8[3], mp8[1], mp26[3], mp26[1], rs8[3], rs8[1], rs26[3], rs26[1]) == (3, 3, 3, 3, 2, 2, 2, 2)
    assert (sp8[3], sp8[1], sp26[3], sp26[1]) == (9, 9, 12, 12)
    assert cadd[0] == 4 and cv26[0] == 11 and cv26[3] == 11 and cv8[0] == 6 and cv8[3] == 7
    mx8, mx26 = wl(S8, "Mul"), wl(S26, "Mul")
    sb8, sb26 = wl(S8, "Sub"), wl(S26, "Sub")
    assert mx8[1] == 2 and mx26[1] == 2 and sb8[1] == 2 and sb26[1] == 2
    ca = o26["concat_axes"]; ca8 = o8["concat_axes"]
    t26 = "26n: cấu trúc, trọng số ngẫu nhiên"
    t8 = "v8n: ngẫu nhiên và đã huấn luyện"
    header = ["Khối kiến trúc", "Mục NPU trong OPL", "Điều kiện OPL so với đồ thị", "Đa lõi (OPL; UG232 tr.75)", "Ghép (UG232 tr.142)", "T3: lớp RKNN, INT8"]
    widths = [128, 200, 232, 160, 150, 230]
    rows, fills = [], {}

    def add(r, red=(), green=()):
        rows.append(r)
        for c in red:
            fills[(len(rows) - 1, c)] = UNK_FILL
        for c in green:
            fills[(len(rows) - 1, c)] = RB

    add(["Conv 1x1, 3x3 (mọi khối)", "3.2.5 Convolution, int8, float16",
         "kernel 1 và 3 ∈ [1, 31], stride 1 và 2 ∈ [1, 7]; ONNX: Conv 1x1, 3x3 s1, 3x3 s2",
         "OPL 支持; UG232 liệt kê Conv", "Conv+Sigmoid(Silu), Conv+Add có trong danh sách đã hỗ trợ",
         f"Conv trơn: {t26}: {cv26[0]}/{cv26[3]} lớp chia 3 lõi; {t8}: {cv8[0]}/{cv8[3]}"], green=[5])
    add(["Conv depthwise 3x3 (chỉ YOLO26n: 8)", "3.2.6 Depthwise Convolution",
         "kernel 3 ∈ [1, 8]; UG232 Table 8-2: kênh INT8 căn 64 cho depthwise",
         "OPL 支持; UG232 liệt kê DepthwiseConvolution", "6 lớp nhánh lớp thành ConvExSwish; 2 lớp pe của attention là Conv",
         f"{t26}: 8 lớp trên NPU, MacUsage {dw_lo:.2f} đến {dw_hi:.2f}% (core_mask AUTO)"], green=[5])
    add(["C2f (YOLOv8n)", "Conv 3.2.5, Split 3.2.59, Add 3.2.1, Concat 3.2.4: đều có mục NPU",
         "Split và Concat dùng axis 1, nằm trong {0, 1, 2, 3}",
         "Conv, Add 支持; Concat: OPL không có dòng, UG232 có; Split: không dòng",
         "Conv+Activation+Add có trong UG232; T3 với SiLU không ghép Add",
         f"{t8}: {cs8[3]} ConvExSwish, {add8[3]} Add, {S8['ops']['Concat']} Concat, {S8['ops']['Split']} Split đều NPU; Add đứng riêng"], green=[5])
    add(["C3k2, C3k (YOLO26n)", "như C2f (Conv, Split, Add, Concat)",
         "như C2f; C3k thêm Conv 1x1 và Concat",
         "như C2f",
         "Add đứng riêng; ConvAdd là của khối attention (proj, ffn.1)",
         f"{t26}: {cs26[3]} ConvExSwish, {add26[3]} Add, {cat26[3]} Concat, {sp26[3]} Split đều NPU"], green=[5])
    add(["SPPF (cả hai)", "MaxPool 3.2.44 (int8, float16)",
         "kernel 5 ∈ (0, 7], stride 1 ∈ (0, 8], pad 2 ∈ [0, 7]; OPL ghi ceil_mode: 不支持, ONNX ceil_mode = 0",
         "OPL không có dòng cho MaxPool",
         "UG232 không có quy tắc ghép MaxPool",
         f"{mp8[3]} MaxPool NPU, lõi 0 ở cả hai ({t26}; {t8}); cv1 của YOLO26n là Conv trơn, của YOLOv8n là ConvExSwish"], green=[5])
    add(["C2PSA, Attention (chỉ YOLO26n)", "MatMul chỉ có mục CPU 4.33; NPU có exMatMul 3.2.76, exSDPAttention 3.2.78; Softmax 3.2.56; Transpose 3.2.62",
         "exSDPAttention: channel ∈ (0, 8192]; Softmax: axis 1 hoặc 3 (ONNX axis -1); Transpose: điều kiện theo perm, không dự đoán được hành vi biên dịch",
         "exSDPAttention 不支持; Softmax 尚不支持; Transpose 暂不支持",
         "UG232 không có quy tắc ghép MatMul-Softmax-MatMul; API232 tr.10: enable_flash_attention (mặc định False) nhắc exSDPAttention",
         f"{t26}: {sd[3]} exSDPAttention INT8 NPU, lõi 0 ở CORE_0_1_2; không còn lớp MatMul, Softmax, Transpose"], green=[5], red=[2])
    add(["Detect YOLOv8n (DFL)", "Softmax 3.2.56, exSoftmax13 3.2.57, Sub 3.2.60, Transpose 3.2.62, Sigmoid 3.2.63, Mul 3.2.41",
         "Sub: broadcast chỉ [b, c, 1, 1] hoặc scalar; Div (từ _NormalizeCoords): OPL T1 chỉ float16",
         "Sub 不支持; exSoftmax13 尚不支持; Transpose 暂不支持; Mul OPL 支持 (UG232 không liệt kê)",
         "không có quy tắc",
         f"{t8}: exSoftmax13 NPU, {len(S8['cpu'])} Transpose CPU (tên lớp thuộc dfl), Sub {sb8[3]}, Mul {mx8[3]} lõi 0; không có lớp Div"], green=[5], red=[3])
    add(["Detect YOLO26n, end2end tắt (đường RKNN)", "Conv 3.2.5, Depthwise 3.2.6; không có DFL nên không có Softmax, Transpose",
         "nhánh hộp 4 kênh; nhánh lớp DWConv 3x3 + Conv 1x1 hai lần",
         "như Conv và Depthwise",
         "DWConv + SiLU ghép thành ConvExSwish (6 lớp)",
         f"{t26}: không có exSoftmax13, không có Transpose CPU; {S26['npu']} lớp NPU, 0 lớp CPU ngoài Input, Output"], green=[5])
    add(["Detect YOLO26n, end2end bật (nms=False)", "TopK, GatherElements, ReduceMax, Mod, Cast, Flatten: chỉ có mục CPU (chương 4); OPSUP: TopK Not Supported",
         f"ONNX có TopK {e2e.get('TopK', 0)}, GatherElements {e2e.get('GatherElements', 0)}, ReduceMax {e2e.get('ReduceMax', 0)}, Mod {e2e.get('Mod', 0)}, Cast {e2e.get('Cast', 0)}, Flatten {e2e.get('Flatten', 0)}",
         "không áp dụng", "không áp dụng",
         "không chạy: exporter tắt end2end với rknn (exporter.py:684-688); chưa đo, unknown"], red=[5])
    add(["Upsample (Resize nearest, 2x)", "Resize 3.2.54 (int8, float16); Upsample chỉ có mục CPU 4.67",
         "ONNX: nearest, scale 2 (OPL: nguyên lần 2 đến 8) đúng; coordinate_transformation_mode asymmetric không nằm trong 3 giá trị của OPL; nearest_mode floor: OPL 目前不支持设置",
         "Resize 不支持",
         "UG232 tr.176: toolkit đổi Resize thành ConvTranspose; optimization_level=2 đưa về CPU",
         f"{rs26[3]} Resize INT8 NPU, lõi 0 ({t26}; {t8}); YOLOv8n ở optimization_level 1, 2, 3 đều NPU"], green=[5], red=[2, 4])
    add(["Concat", "3.2.4 Concat (int8, float16)",
         f"axis ∈ {{0, 1, 2, 3}}: axis 1 ở {ca8.get('1', ca8.get(1))} nút (v8n), {ca.get('1', ca.get(1))} (26n); 2 nút axis -1 ở Detect trên tensor 3 chiều: OPL ghi shape 4 chiều, unknown",
         "OPL không có dòng; UG232 liệt kê Concat",
         "không có quy tắc",
         f"{t26}: {cat26[0]}/{cat26[3]} chia 3 lõi, {cat26[1]} lõi 0; {t8}: {cat8[0]}/{cat8[3]}, {cat8[1]} lõi 0"], green=[5], red=[2])
    add(["Split, Slice", "Split 3.2.59; Slice 3.2.55 (NPU khi steps == [1, 1, 1, 1], có ngoại lệ với subc)",
         "Split axis 1, và axis 2 ở attention; ONNX có Slice 4 nút (từ _NormalizeCoords): chưa kiểm được điều kiện steps",
         "OPL không có dòng; UG232 không liệt kê",
         "không có quy tắc",
         f"không có lớp Slice; Split {sp8[3]} (v8n) và {sp26[3]} (26n) NPU, tất cả lõi 0"], green=[5], red=[2])
    add(["Activation SiLU (Conv + Sigmoid + Mul)", "ConvolutionSwish 3.2.17; exSwish 3.2.69 (rời); Sigmoid 3.2.63; Mul 3.2.41",
         "ONNX: Conv, Sigmoid, Mul rời nhau",
         "ConvolutionSwish 暂不支持; Sigmoid 尚不支持",
         "Conv+Sigmoid(Tanh/Elu/Silu...) có trong danh sách đã hỗ trợ",
         f"ConvExSwish NPU, chỉ lõi 0 ở CORE_0_1_2: {cs26[3]}/{cs26[3]} ({t26}), {cs8[3]}/{cs8[3]} ({t8}); tên ConvExSwish không có trong OPL"], green=[5])
    f = Fig(W, 2200)
    tier(f)
    f.tier(f.w - 100 - 7.4 * 9 - 80, 8, "T3 đo")
    f.text(10, 20, "Khối kiến trúc so với tiêu chí NPU của RK3588", size=15, weight=700)
    yE = matrix(f, 0, 38, widths, header, rows, fills)
    y = f.legend(10, yE + 14, 1080, [
        ("fill:" + RB, "T3: lớp chạy trên NPU, có file log (điều kiện nêu trong ô)"),
        ("fill:" + UNK_FILL, "unknown, hoặc điều kiện của OPL không khớp với đồ thị ONNX, hoặc hai tài liệu nói khác nhau"),
    ])
    y = panel(f, 10, y + 10, 1080, [
        [("Đọc ô cuối: ", "b"), ("T3 cho biết lớp chạy NPU với cấu trúc này; không cho biết độ chính xác INT8 và không cho biết vì sao chậm hơn. "
                                  "Độ trễ: Số đo: Hình 10.2, 10.4.", "t")],
        [("Training-only: ", "b"), ("bỏ DFL (reg_max 1) và đầu một-một làm đổi đồ thị (xem Hình 9.2); ProgLoss, STAL, MuSGD không đổi đồ thị theo YOFF, Y26A.", "t")],
    ], size=12, lh=19)
    source2(f, y + 8, ["Nguồn: OPL 3.2.1-3.2.78 (tr.56-105), chương 4 (tr.320-333); UG232 tr.75, 142, 145, 148, 176; API232 tr.10; OPSUP dòng 189;",
                       "data/rknn_path_onnx.json, data/ops_via_exporter.json; LOG 2026-10-10_yolo-phaseA/raw/layers_*_CORE_0_1_2.txt, 2026-10-10_t3-board-silu-resize."])
    return f


FIGS = [
    ("h9-1-v8n-26n", fig_v8n_26n),
    ("h9-4-ma-tran-tieu-chi", fig_matrix),
    ("h9-3-duong-xuat", fig_export),
    ("h9-2-cac-khoi", fig_blocks),
]

if __name__ == "__main__":
    run(FIGS, HERE)
