#!/usr/bin/env python3
"""Phan 10 So do thuc te: Hinh 10.1 den 10.7 (10.8 chua co so, khong co hinh). Run with .venv/bin/python (matplotlib).

Every number is read from the raw log files, CSV and JSON on disk (tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/raw,
2026-10-10_yolo-phaseA, 2026-10-10_t3-calibration-pc, ai/automation/runs, ai/automation/leaderboards); nothing is typed
by hand. Hinh 10.3 (build) is unchanged from the approved sample; 10.6 is a figlib diagram (SVG + chrome PNG), the rest
are matplotlib via chartlib.

Usage: python3 gen.py [outdir] [figure-name ...]
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from chartlib import BLUE, DARK, GRAY, GREEN, INK, RED, save, source_line, tier_label  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RAW = os.path.join(ROOT, "tmp", "04_debug-logs", "2026-10-10_t3-board-silu-resize", "raw")
LAYER_ROW = re.compile(r"^\s*(\d+)\s+(\S+)\s+\S+\s+(NPU|CPU)\s")
WORKLOAD = re.compile(r"(\d+(?:\.\d+)?)%/(\d+(?:\.\d+)?)%/(\d+(?:\.\d+)?)%\s+\d+\s+\S+\s*$")


def load(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as fh:
        return json.load(fh)


def workloads(layer_file):
    """op type -> list of (core0, core1, core2) percentages, from the WorkLoad(0/1/2) column."""
    out = {}
    with open(os.path.join(RAW, layer_file), encoding="utf-8") as fh:
        for ln in fh:
            m, w = LAYER_ROW.match(ln), WORKLOAD.search(ln)
            if m and w:
                out.setdefault(m.group(2), []).append(tuple(float(x) for x in w.groups()))
    return out


def build():
    s1, s2, s3 = load("summary.json"), load("summary2.json"), load("summary3.json")
    models = [("silu_opt3", s2, "silu_opt3", "SiLU, có Add\nngẫu nhiên"),
              ("silu_noadd", s2, "silu_noadd", "SiLU, không Add\nngẫu nhiên"),
              ("relu_opt3", s2, "relu_opt3", "ReLU, có Add\nngẫu nhiên"),
              ("relu_noadd", s2, "relu_noadd", "ReLU, không Add\nngẫu nhiên"),
              ("trained_silu_5c", s3, "trained_silu_5c", "SiLU, có Add\nđã huấn luyện")]
    masks = [("AUTO", GRAY), ("CORE_0", BLUE), ("CORE_0_1_2", GREEN)]

    fig = plt.figure(figsize=(11.5, 7.2))
    axa = fig.add_axes([0.065, 0.36, 0.55, 0.50])
    axb = fig.add_axes([0.765, 0.36, 0.22, 0.50])

    # ---- panel A ----
    bw = 0.26
    for j, (mask, col) in enumerate(masks):
        xs, med, lo, hi, pts = [], [], [], [], []
        for i, (_, src, key, _) in enumerate(models):
            r = src[f"{key}|{mask}"]
            xs.append(i + (j - 1) * bw)
            med.append(r["ms"])
            lo.append(r["ms"] - min(r["all_ms"]))
            hi.append(max(r["all_ms"]) - r["ms"])
            pts.append(r["all_ms"])
        axa.bar(xs, med, bw * 0.92, color=col, alpha=0.85, label=mask, zorder=2)
        axa.errorbar(xs, med, yerr=[lo, hi], fmt="none", ecolor=INK, elinewidth=1.2, capsize=3, zorder=4)
        for x, p in zip(xs, pts):
            axa.scatter([x + d for d in np.linspace(-0.05, 0.05, len(p))], p, s=7, color="white",
                        edgecolor=INK, linewidth=0.5, zorder=5)
    # session-to-session spread of silu_opt3 AUTO: run 1 (summary.json) vs run 2 (summary2.json)
    run1 = s1["silu_opt3"]["npu_latency_ms"]
    run2 = s2["silu_opt3|AUTO"]["ms"]
    axa.plot([-bw - 0.16, -bw + 0.16], [run1, run1], color=RED, lw=1.8, ls="--", zorder=6)
    axa.text(-0.45, 24.2, f"đường đứt đỏ: lượt 1 = {run1:.3f} ms\ncột xám (silu_opt3 AUTO): lượt 2 = {run2:.3f} ms",
             fontsize=9.5, color=RED, ha="left", va="center", zorder=7)
    axa.set_xticks(range(len(models)))
    axa.set_xticklabels([m[3] for m in models], fontsize=9.5)
    axa.set_ylabel("độ trễ (ms), trung vị của 5 lần")
    axa.set_ylim(0, 26)
    axa.legend(title="core_mask", loc="upper right", ncol=3, fontsize=9, title_fontsize=9)
    axa.set_title("A. Độ trễ: cột là trung vị, thanh sai số từ nhỏ nhất đến lớn nhất, chấm là 5 lần đo",
                  fontsize=11, loc="left", fontweight="bold")

    # ---- panel B ----
    sil, rel = workloads("silu_opt3_CORE_0_1_2_layers.txt"), workloads("relu_opt3_CORE_0_1_2_layers.txt")
    rows = [("ConvExSwish (SiLU)", sil["ConvExSwish"]), ("ConvRelu (ReLU)", rel["ConvRelu"]),
            ("ConvReluAdd (ReLU)", rel["ConvReluAdd"]), ("Add (model SiLU)", sil["Add"]),
            ("Concat (model SiLU)", sil["Concat"])]
    core_cols = [BLUE, "#7FBF86", GREEN]
    for i, (label, vals) in enumerate(rows):
        mean = np.mean(np.array(vals), axis=0)
        left = 0.0
        for c in range(3):
            axb.barh(i, mean[c], left=left, color=core_cols[c], edgecolor="white", height=0.62,
                     label=f"core {c}" if i == 0 else None, zorder=2)
            if mean[c] >= 9:
                axb.text(left + mean[c] / 2, i, f"{mean[c]:.0f}%", ha="center", va="center", fontsize=9,
                         color="white", fontweight="bold")
            left += mean[c]
        split = sum(1 for v in vals if v[1] > 0 or v[2] > 0)
        rows[i] = (f"{label}\n{split}/{len(vals)} lớp chia nhiều core", vals)
    axb.set_yticks(range(len(rows)))
    axb.set_yticklabels([r[0] for r in rows], fontsize=9.5)
    axb.invert_yaxis()
    axb.set_xlim(0, 100)
    axb.set_xlabel("% khối lượng (trung bình các lớp)")
    axb.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=9.5, frameon=False)
    axb.grid(axis="y", visible=False)
    axb.spines["right"].set_visible(False)
    fig.text(0.60, 0.94, "B. Chia việc giữa 3 core khi CORE_0_1_2", fontsize=11, fontweight="bold", ha="left")
    fig.text(0.60, 0.915, "WorkLoad(0/1/2) trong bảng lớp, một lần perf_debug", fontsize=9.5, color=DARK, ha="left")

    # ---- conditions ----
    lines = [
        "Điều kiện đo: RK3588S (Orange Pi 5), rknn-toolkit2 2.3.2, YOLOv8n INT8 640x640 nc=5, eval_perf với fix_freq=True,",
        "trung vị của 5 lần, cùng một phiên đo. Trọng số ngẫu nhiên, trừ trained_silu_5c là best.pt đã huấn luyện (40 ảnh calibration).",
        f"SiLU dao động giữa các phiên: silu_opt3 AUTO là {run1:.3f} ms ở lượt 1 và {run2:.3f} ms ở lượt 2 (cùng file .rknn), nên",
        "chênh lệch nhỏ giữa các cột SiLU không phải là kết luận. Số đo chỉ đúng cho model và điều kiện này.",
    ]
    for k, ln in enumerate(lines):
        fig.text(0.012, 0.225 - 0.04 * k, ln, fontsize=10.5, color=INK, ha="left")
    fig.add_artist(plt.Rectangle((0.006, 0.065), 0.988, 0.215, transform=fig.transFigure, fill=False,
                                 edgecolor="#999999", lw=1))
    fig.text(0.012, 0.262, "Điều kiện và lưu ý", fontsize=11, fontweight="bold", ha="left")
    source_line(fig, "Nguồn: tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/raw/summary.json, summary2.json, "
                "summary3.json, *_CORE_0_1_2_layers.txt.", y=0.012)
    tier_label(fig, "T3 đo")
    return fig


# =====================================================================
# Shared helpers for the new figures (10.1, 10.2, 10.4, 10.5, 10.6, 10.7)
# =====================================================================
import csv  # noqa: E402
import glob  # noqa: E402
import textwrap  # noqa: E402

import yaml  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ORANGE = "#B26A00"
PURPLE = "#6A3D9A"
DEBUG_DIR = os.path.join(ROOT, "tmp", "04_debug-logs")
PHASEA = os.path.join(DEBUG_DIR, "2026-10-10_yolo-phaseA")
CALIB = os.path.join(DEBUG_DIR, "2026-10-10_t3-calibration-pc")
RUNS = os.path.join(ROOT, "ai", "automation", "runs")
LEADERBOARD = os.path.join(ROOT, "ai", "automation", "leaderboards", "sfchd_5class.csv")
PERF_ROW = re.compile(r"^(\d+)\s+(\S+)\s+(\S+)\s+(NPU|CPU)\s+(\S+)\s+(\S+)\s+(\d+/\d+/\d+)\s+(\d+)\s+(.*)$")
RANK_ROW = re.compile(r"^(\S+)\s+(\d+)\s+\d+\s+\d+\s+\d+\s+(\d+)\s+([\d.]+)%")


def cond_box(fig, lines, bottom=0.065, title="Điều kiện và lưu ý"):
    """Bordered 'Điều kiện và lưu ý' box in the same style and spacing as Hình 10.3 (sizes in inches)."""
    h_in = fig.get_figheight()
    n = len(lines)
    box_in = 0.13 + 0.27 + 0.288 * (n - 1) + 0.29
    top = bottom + box_in / h_in
    fig.add_artist(Rectangle((0.006, bottom), 0.988, box_in / h_in, transform=fig.transFigure, fill=False,
                             edgecolor="#999999", lw=1))
    fig.text(0.012, top - 0.13 / h_in, title, fontsize=11, fontweight="bold", ha="left", va="baseline")
    for k, ln in enumerate(lines):
        fig.text(0.012, top - (0.13 + 0.27 + 0.288 * k) / h_in, ln, fontsize=10.5, color=INK, ha="left",
                 va="baseline")
    return top


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def perf_table(path):
    """Parse an eval_perf perf_debug table: layer rows, per-op ranking table, total, warning line."""
    rows, rank, total, warn = [], {}, None, None
    for ln in read_text(path).split("\n"):
        if ln.startswith("Warning:"):
            warn = ln.strip()
        m = PERF_ROW.match(ln)
        if m:
            rows.append(dict(id=int(m[1]), op=m[2], target=m[4], us=int(m[8]), name=m[9].split()[-1]))
        elif ln.startswith("Total Operator Elapsed"):
            total = int(ln.split(":")[1])
        else:
            r = RANK_ROW.match(ln)
            if r:
                rank[r[1]] = dict(calls=int(r[2]), us=int(r[3]), pct=float(r[4]))
    return dict(rows=rows, rank=rank, total=total, warn=warn)


def op_counts(path):
    out = {}
    for r in perf_table(path)["rows"]:
        out[r["op"]] = out.get(r["op"], 0) + 1
    return out


def short_layer(name):
    body = name.split(":", 1)[-1]
    parts = [p for p in body.split("/") if p]
    if parts and parts[0] == "model":
        parts = parts[1:]
    s = "/".join(parts[-3:])
    return s if len(s) <= 31 else s[:30] + "…"


def pct_drop(a, b):
    """percent by which b is lower than a"""
    return 100.0 * (1.0 - b / a)


# =====================================================================
# Hinh 10.1: SiLU so ReLU
# =====================================================================
def fig_silu_relu():
    s1, s2 = load("summary.json"), load("summary2.json")
    g1 = [("silu_opt1", s1["silu_opt1"]["npu_latency_ms"], s1["silu_opt1"]["all_ms"], "SiLU\nlevel 1", BLUE, False),
          ("silu_opt2", s1["silu_opt2"]["npu_latency_ms"], s1["silu_opt2"]["all_ms"], "SiLU\nlevel 2", BLUE, False),
          ("silu_opt3", s1["silu_opt3"]["npu_latency_ms"], s1["silu_opt3"]["all_ms"], "SiLU\nlevel 3", BLUE, False),
          ("relu_opt3", s1["relu_opt3"]["npu_latency_ms"], s1["relu_opt3"]["all_ms"], "ReLU\nlevel 3", GREEN, False)]

    def r2(k):
        return s2[f"{k}|AUTO"]["ms"], s2[f"{k}|AUTO"]["all_ms"]
    g2 = [("silu_opt3", *r2("silu_opt3"), "SiLU\ncó Add", BLUE, False),
          ("silu_noadd", *r2("silu_noadd"), "SiLU\nkhông Add", BLUE, True),
          ("relu_opt3", *r2("relu_opt3"), "ReLU\ncó Add", GREEN, False),
          ("relu_noadd", *r2("relu_noadd"), "ReLU\nkhông Add", GREEN, True)]
    xs1 = [0, 1, 2, 3]
    xs2 = [4.9, 5.9, 6.9, 7.9]

    fig = plt.figure(figsize=(11.5, 8.0))
    axa = fig.add_axes([0.065, 0.40, 0.575, 0.44])
    for xs, grp in ((xs1, g1), (xs2, g2)):
        for x, (_, med, pts, _, col, hatch) in zip(xs, grp):
            axa.bar(x, med, 0.72, color=col, alpha=0.85, hatch="///" if hatch else None,
                    edgecolor="white" if hatch else col, linewidth=0, zorder=2)
            axa.errorbar([x], [med], yerr=[[med - min(pts)], [max(pts) - med]], fmt="none", ecolor=INK,
                         elinewidth=1.2, capsize=3, zorder=4)
            axa.scatter([x + d for d in np.linspace(-0.12, 0.12, len(pts))], pts, s=8, color="white",
                        edgecolor=INK, linewidth=0.5, zorder=5)
            axa.text(x, 0.8, f"{med:.3f}", ha="center", va="bottom", fontsize=8.5, color="white",
                     fontweight="bold", zorder=6, bbox=dict(boxstyle="square,pad=0.15", fc=col, ec="none"))
    axa.set_xticks(xs1 + xs2)
    axa.set_xticklabels([g[3] for g in g1 + g2], fontsize=9.5)
    axa.set_xlim(-0.7, 8.6)
    axa.set_ylim(0, 36)
    axa.set_ylabel("độ trễ (ms), trung vị của 5 lần")
    axa.axvline(4.4, color="#999999", lw=1, ls=":")
    axa.text(1.5, 35.4, "Lượt 1 (summary.json): activation và Add đổi cùng lúc", ha="center", va="top", fontsize=9.5,
             fontweight="bold")
    axa.text(6.4, 35.4, "Lượt 2 (summary2.json): tách Add", ha="center", va="top", fontsize=9.5, fontweight="bold")
    # confound / separation annotations (percentages computed from the medians above)
    d1 = pct_drop(g1[2][1], g1[3][1])
    d2 = pct_drop(g2[1][1], g2[3][1])
    axa.text(1.5, 32.5, f"ReLU thấp hơn SiLU {d1:.1f}%\n(level 3), nhưng hai thay đổi\ntrộn lẫn: activation và Add",
             ha="center", va="top", fontsize=9.5, color=RED)
    axa.text(6.4, 32.5, f"chỉ đổi activation (cả hai\ncòn 2 Add rời): thấp hơn {d2:.1f}%\nchỉ đổi Add: trong độ trải",
             ha="center", va="top", fontsize=9.5, color=RED)
    # session spread of silu_opt3: run 1 median drawn across the run 2 silu_opt3 bar
    run1, run2 = g1[2][1], g2[0][1]
    axa.plot([xs2[0] - 0.46, xs2[0] + 0.46], [run1, run1], color=RED, lw=1.8, ls="--", zorder=7)
    axa.text(xs2[0], run1 - 0.6, f"lượt 1\n{run1:.3f}", ha="center", va="top", fontsize=8.5, color="white",
             fontweight="bold", zorder=8)
    import matplotlib.patches as mp
    axa.legend(handles=[mp.Patch(color=BLUE, alpha=0.85, label="SiLU"), mp.Patch(color=GREEN, alpha=0.85, label="ReLU"),
                        mp.Patch(facecolor="#BBBBBB", edgecolor="white", hatch="///", label="không Add (shortcut=False)")],
               loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=9, frameon=False)
    fig.text(0.065, 0.905, "A. Độ trễ NPU (AUTO): cột là trung vị, thanh sai số nhỏ nhất đến lớn nhất, chấm là 5 lần đo",
             fontsize=10.5, fontweight="bold", ha="left")

    # ---- panel B: op mapping counted from the layer tables ----
    rows = [("SiLU, có Add", "silu_opt3_layers.txt", BLUE), ("ReLU, có Add", "relu_opt3_layers.txt", GREEN),
            ("SiLU, không Add", "silu_noadd_CORE_0_layers.txt", BLUE),
            ("ReLU, không Add", "relu_noadd_CORE_0_layers.txt", GREEN)]
    cols = ["ConvExSwish", "ConvRelu", "ConvReluAdd", "Add"]
    cnt = [op_counts(os.path.join(RAW, f)) for _, f, _ in rows]
    axb = fig.add_axes([0.665, 0.40, 0.325, 0.44])
    axb.set_xlim(0, 1)
    axb.set_ylim(0, 1)
    axb.axis("off")
    x0, cw, lab_w = 0.0, 0.17, 0.32
    y_top, rh = 0.84, 0.16
    for j, c in enumerate(cols):
        axb.text(lab_w + cw * (j + 0.5), y_top + 0.04, c.replace("Conv", "Conv\n", 1) if len(c) > 8 else c,
                 ha="center", va="bottom", fontsize=9, fontweight="bold")
    for i, ((lab, f, col), cn) in enumerate(zip(rows, cnt)):
        y = y_top - rh * (i + 1)
        axb.text(0.0, y + rh / 2, lab, ha="left", va="center", fontsize=9.5)
        for j, c in enumerate(cols):
            n = cn.get(c, 0)
            axb.add_patch(Rectangle((lab_w + cw * j, y + 0.01), cw - 0.012, rh - 0.02,
                                    fc=col if n else "white", ec="#999999", lw=0.8, alpha=0.35 if n else 1))
            axb.text(lab_w + cw * (j + 0.5), y + rh / 2, str(n) if n else "0", ha="center", va="center", fontsize=11,
                     fontweight="bold" if n else "normal", color=INK if n else "#999999")
    sil, rel = cnt[0], cnt[1]
    sil_n, rel_n = cnt[2], cnt[3]
    note = (f"Lượt 1: {sil['ConvExSwish']} ConvExSwish thành {rel['ConvRelu']} ConvRelu + {rel['ConvReluAdd']} ConvReluAdd; "
            f"Add đứng riêng {sil['Add']} thành {rel['Add']} (ReLU ghép Add vào Conv). "
            f"Lượt 2 (không Add): Add đứng riêng còn {sil_n['Add']} ở cả hai; ReLU có {rel_n['ConvRelu']} ConvRelu.")
    axb.text(0.0, 0.14, "\n".join(textwrap.wrap(note, 58)), ha="left", va="top", fontsize=9, color=DARK)
    fig.text(0.665, 0.905, "B. Số lớp theo loại op trong bảng lớp", fontsize=11, fontweight="bold",
             ha="left")

    # ---- conditions ----
    spread = {k: max(v) - min(v) for k, v in
              [(g[0] + "_r1", g[2]) for g in g1] + [(g[0] + "_r2", g[2]) for g in g2]}
    silu_sp = [v for k, v in spread.items() if k.startswith("silu")]
    relu_sp = [v for k, v in spread.items() if k.startswith("relu")]
    lines = [
        "Điều kiện đo: RK3588S (Orange Pi 5), rknn-toolkit2 2.3.2, YOLOv8n INT8 640x640 nc=5, eval_perf với fix_freq=True, core_mask=AUTO,",
        "trung vị của 5 lần mỗi cột. Trọng số ngẫu nhiên: chỉ đo cấu trúc, ánh xạ op và độ trễ, không đo accuracy.",
        "Gây nhiễu ở lượt 1: relu_opt3 khác silu_opt3 ở hai điều cùng lúc, activation (SiLU thành ReLU) và việc ghép Add (Add rời giảm từ "
        f"{sil['Add']} xuống {rel['Add']}).",
        "Lượt 2 tách ra bằng biến thể noadd (shortcut=False ở 4 khối C2f của backbone): so silu_noadd với relu_noadd chỉ đổi activation;",
        "so relu_opt3 với relu_noadd chỉ đổi Add. Cột SiLU dao động giữa các phiên: silu_opt3 là "
        f"{run1:.3f} ms ở lượt 1 và {run2:.3f} ms ở lượt 2 (cùng file .rknn).",
        f"Độ trải (lớn nhất trừ nhỏ nhất) của SiLU từ {min(silu_sp):.3f} đến {max(silu_sp):.3f} ms, của ReLU từ {min(relu_sp):.3f} đến "
        f"{max(relu_sp):.3f} ms: đọc số SiLU như khoảng. Số đo chỉ đúng cho model và điều kiện này.",
    ]
    cond_box(fig, lines)
    source_line(fig, "Nguồn: tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/raw/summary.json, summary2.json, silu_opt3_layers.txt, "
                "relu_opt3_layers.txt, silu_noadd_CORE_0_layers.txt, relu_noadd_CORE_0_layers.txt.", y=0.012)
    tier_label(fig, "T3 đo")
    return fig


# =====================================================================
# Hinh 10.2: do tre tung lop (perf_debug)
# =====================================================================
OP_COLORS = {"ConvExSwish": BLUE, "Concat": GREEN, "exSoftmax13": RED, "exSDPAttention": ORANGE, "Transpose": PURPLE,
             "Split": "#8C564B", "Conv": "#17A2B8", "Add": "#D6609A", "Reshape": "#9AA02A", "khác": "#BBBBBB"}


def fig_per_layer():
    models = [("YOLOv8n SiLU, ngẫu nhiên\n(silu_opt3, lượt 1)", os.path.join(RAW, "silu_opt3_layers.txt")),
              ("YOLOv8n SiLU, đã huấn luyện\n(trained_silu_5c, lượt 3)", os.path.join(RAW, "trained_silu_5c_AUTO_layers.txt")),
              ("YOLO26n, ngẫu nhiên\n(phiên 1)", os.path.join(PHASEA, "raw", "layers_yolo26n_AUTO.txt"))]
    tabs = [perf_table(p) for _, p in models]
    fig = plt.figure(figsize=(11.5, 11.2))
    # ---- warning banner ----
    warn = tabs[0]["warn"]
    fig.add_artist(Rectangle((0.006, 0.935), 0.905, 0.052, transform=fig.transFigure, fc="#FFF3F3", ec=RED, lw=1.6))
    fig.text(0.012, 0.9695, "Cảnh báo: thời gian từng lớp lấy ở chế độ perf_debug có thể lớn hơn độ trễ thật.", fontsize=11.5,
             fontweight="bold", color=RED, ha="left", va="center")
    fig.text(0.012, 0.9455, f"eval_perf in: \"{warn}\" Vì vậy hình so sánh bằng tỉ lệ phần trăm, không so tổng tuyệt đối.",
             fontsize=9.8, color=INK, ha="left", va="center")

    # ---- panel A: top 8 layers per model (share of the debug total) ----
    xmax = 0
    tops = []
    for t in tabs:
        top = sorted(t["rows"], key=lambda r: -r["us"])[:8]
        tops.append(top)
        xmax = max(xmax, max(100.0 * r["us"] / t["total"] for r in top))
    left = [0.125, 0.445, 0.765]
    for k, ((title, _), t, top) in enumerate(zip(models, tabs, tops)):
        ax = fig.add_axes([left[k] + 0.125, 0.50, 0.075, 0.30])
        ys = list(range(len(top)))
        shares = [100.0 * r["us"] / t["total"] for r in top]
        ax.barh(ys, shares, color=[OP_COLORS.get(r["op"], OP_COLORS["khác"]) for r in top], height=0.68, zorder=2)
        for y, s in zip(ys, shares):
            ax.text(s + 0.15, y, f"{s:.1f}%", va="center", ha="left", fontsize=8.5)
        ax.set_yticks(ys)
        ax.set_yticklabels([f"#{r['id']} {r['op']}\n{short_layer(r['name'])}" for r in top], fontsize=7.6)
        ax.invert_yaxis()
        ax.set_xlim(0, xmax * 1.28)
        ax.set_xlabel("% tổng bảng debug", fontsize=9)
        ax.grid(axis="y", visible=False)
        ax.set_title(f"{title}\ntổng bảng debug {t['total']} us (không phải độ trễ)", fontsize=9.6, loc="right",
                     fontweight="bold", pad=6)
    fig.text(0.012, 0.905, "A. Tám lớp tốn thời gian nhất của mỗi model: phần trăm của tổng bảng debug (màu theo loại op)",
             fontsize=11, fontweight="bold", ha="left")

    # ---- panel B: share by op type from the Operator Time Consuming Ranking Table ----
    ops = []
    for t in tabs:
        for op, v in t["rank"].items():
            if v["pct"] >= 3.0 and op not in ops:
                ops.append(op)
    ops.sort(key=lambda o: -np.mean([t["rank"].get(o, {"pct": 0})["pct"] for t in tabs]))
    axb = fig.add_axes([0.20, 0.285, 0.50, 0.10])
    for i, t in enumerate(tabs):
        left_v = 0.0
        for op in ops:
            v = t["rank"].get(op, {"pct": 0.0})["pct"]
            axb.barh(i, v, left=left_v, color=OP_COLORS.get(op, OP_COLORS["khác"]), edgecolor="white", height=0.66,
                     zorder=2)
            if v >= 5.5:
                axb.text(left_v + v / 2, i, f"{v:.1f}", ha="center", va="center", fontsize=8.5, color="white",
                         fontweight="bold")
            left_v += v
        rest = 100.0 - left_v
        axb.barh(i, rest, left=left_v, color=OP_COLORS["khác"], edgecolor="white", height=0.66, zorder=2)
        axb.text(left_v + rest / 2, i, f"{rest:.1f}", ha="center", va="center", fontsize=8.5, color=INK)
    axb.set_yticks(range(3))
    axb.set_yticklabels([m[0].split("\n")[0] for m in models], fontsize=9)
    axb.invert_yaxis()
    axb.set_xlim(0, 100)
    axb.set_xlabel("% tổng bảng debug theo loại op (cột TimeRatio của bảng Operator Time Consuming Ranking)", fontsize=8.5)
    axb.grid(axis="y", visible=False)
    import matplotlib.patches as mp
    hand = [mp.Patch(color=OP_COLORS.get(o, OP_COLORS["khác"]), label=o) for o in ops] + \
           [mp.Patch(color=OP_COLORS["khác"], label="khác (còn lại)")]
    axb.legend(handles=hand, loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8.5, ncol=2)
    fig.text(0.012, 0.425, "B. Tỉ lệ thời gian theo loại op", fontsize=11, fontweight="bold", ha="left")

    # ---- conditions ----
    a, b, c = tabs
    cs = max(a["total"], b["total"])
    lines = [
        "Điều kiện đo: RK3588S (Orange Pi 5), rknn-toolkit2 2.3.2, INT8 640x640 nc=5, core_mask=AUTO, fix_freq=True; mỗi bảng là một lần",
        "eval_perf với perf_debug=True, nên không có độ trải: chênh lệch vài điểm phần trăm giữa các model hay các lớp không phải kết luận.",
        f"Cùng một đồ thị YOLOv8n cho tổng bảng debug {a['total']} us (trọng số ngẫu nhiên) và {b['total']} us (đã huấn luyện), "
        f"lệch {100.0 * (b['total'] - a['total']) / a['total']:.0f}%, trong khi tỉ lệ ConvExSwish là",
        f"{a['rank']['ConvExSwish']['pct']:.1f}% và {b['rank']['ConvExSwish']['pct']:.1f}%: tổng đổi theo lượt chạy, tỉ lệ ổn định hơn. "
        f"Với YOLO26n tổng bảng debug là {c['total']} us.",
        "Trọng số ngẫu nhiên trừ trained_silu_5c. NPU Cycles của bảng debug chỉ tính cho Conv, nên hình dùng cột Time(us), không dùng Cycles.",
    ]
    cond_box(fig, lines)
    source_line(fig, "Nguồn: tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/raw/silu_opt3_layers.txt, trained_silu_5c_AUTO_layers.txt; "
                "2026-10-10_yolo-phaseA/raw/layers_yolo26n_AUTO.txt.", y=0.012)
    tier_label(fig, "T3 đo")
    return fig


# =====================================================================
# Hinh 10.4: YOLOv8n so YOLO26n, 3 phien
# =====================================================================
def phaseA_stats():
    """Parse out/stats_latency.txt (written by stats_latency.py): one dict per core_mask."""
    out = {}
    lines = read_text(os.path.join(PHASEA, "out", "stats_latency.txt")).strip().split("\n")
    for ln in lines[1:]:
        m = re.match(r"(\S+) (\d+) (\d+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) \[(.*?)\] \[(.*?)\]", ln)
        out[m[1]] = dict(n26=int(m[2]), n8=int(m[3]), med26=float(m[4]), med8=float(m[5]), diff=float(m[6]),
                         U=float(m[7]), p=float(m[8]), lo=float(m[9]), hi=float(m[10]),
                         s26=[float(x) for x in m[11].split(",")], s8=[float(x) for x in m[12].split(",")])
    return out


def fig_v8n_26n():
    runs = json.loads(read_text(os.path.join(PHASEA, "raw", "phaseA.json")))["runs"]
    st = phaseA_stats()
    masks = ["AUTO", "CORE_0", "CORE_0_1_2"]
    sessions = sorted({r["session"] for r in runs})
    first = {}  # session -> which model ran first (order of runs in the json)
    for r in runs:
        first.setdefault(r["session"], r["model"])
    mk = {sessions[0]: "o", sessions[1]: "s", sessions[2]: "^"}
    name = {"yolov8n": "YOLOv8n", "yolo26n": "YOLO26n"}
    col = {"yolov8n": BLUE, "yolo26n": ORANGE}
    fig = plt.figure(figsize=(11.5, 8.8))
    axa = fig.add_axes([0.065, 0.40, 0.56, 0.45])
    for gi, mask in enumerate(masks):
        for mi, model in enumerate(["yolov8n", "yolo26n"]):
            xc = gi + (-0.2 if mi == 0 else 0.2)
            allv = []
            for r in runs:
                if r["model"] == model and r["mask"] == mask:
                    off = (r["session"] - sessions[1]) * 0.085
                    xs = [xc + off + d for d in np.linspace(-0.025, 0.025, len(r["all_ms"]))]
                    axa.scatter(xs, r["all_ms"], s=16, marker=mk[r["session"]], color=col[model], alpha=0.8,
                                edgecolor="white", linewidth=0.4, zorder=4)
                    allv += r["all_ms"]
            med = st[mask]["med8"] if model == "yolov8n" else st[mask]["med26"]
            axa.plot([xc - 0.17, xc + 0.17], [med, med], color=INK, lw=2.2, zorder=5)
            axa.plot([xc, xc], [min(allv), max(allv)], color=INK, lw=0.8, zorder=3)
            axa.text(xc, min(allv) - 0.35, f"{med:.2f}", ha="center", va="top", fontsize=8.5, fontweight="bold")
    axa.set_xticks(range(3))
    axa.set_xticklabels(masks, fontsize=10)
    axa.set_ylabel("độ trễ eval_perf (ms)")
    axa.set_ylim(14, 28.5)
    axa.set_xlim(-0.55, 2.55)
    import matplotlib.lines as ml
    hand = [ml.Line2D([], [], color=col[m], marker="o", ls="", label=name[m]) for m in col] + \
           [ml.Line2D([], [], color=GRAY, marker=mk[s], ls="", label=f"phiên {s}: {name[first[s]]} đo trước") for s in sessions] + \
           [ml.Line2D([], [], color=INK, lw=2.2, label="trung vị của 15 giá trị")]
    axa.legend(handles=hand, loc="upper left", ncol=2, fontsize=8.8, columnspacing=1.2)
    fig.text(0.065, 0.885, "A. Độ trễ: mỗi chấm là một lần đo, 15 giá trị mỗi nhóm (3 phiên x 5 lần), thanh dọc là nhỏ nhất đến lớn nhất",
             fontsize=11, fontweight="bold", ha="left")

    # ---- panel B: forest plot of the median difference ----
    axb = fig.add_axes([0.715, 0.575, 0.26, 0.275])
    for i, mask in enumerate(masks):
        s = st[mask]
        axb.errorbar([s["diff"]], [i], xerr=[[s["diff"] - s["lo"]], [s["hi"] - s["diff"]]], fmt="o", color=ORANGE,
                     ecolor=ORANGE, elinewidth=2, capsize=4, ms=6, zorder=4)
        axb.text(s["hi"] + 0.25, i, f"{s['diff']:.3f} (CI {s['lo']:.3f} đến {s['hi']:.3f})\np = {s['p']:.5f}", va="center",
                 ha="left", fontsize=8.2)
    axb.axvline(0, color=INK, lw=1)
    axb.set_yticks(range(3))
    axb.set_yticklabels(masks, fontsize=9.5)
    axb.set_xlim(-1, 14.5)
    axb.set_ylim(2.6, -0.6)
    axb.set_xlabel("YOLO26n trừ YOLOv8n, chênh lệch trung vị (ms)", fontsize=9)
    axb.grid(axis="y", visible=False)
    fig.text(0.715, 0.885, "B. Chênh lệch trung vị, CI 95% bootstrap,", fontsize=11, fontweight="bold", ha="left")
    fig.text(0.715, 0.863, "Mann-Whitney hai phía (p) trên 15 giá trị", fontsize=9.8, color=DARK, ha="left")

    # ---- panel C: session medians as a small monospace table ----
    fig.text(0.66, 0.50, "C. Trung vị mỗi phiên (ms), phiên 1, 2, 3", fontsize=11, fontweight="bold", ha="left")
    hdr = f"{'':11s}{'YOLOv8n':21s}YOLO26n"
    fig.text(0.66, 0.47, hdr, fontsize=8.0, family="monospace", ha="left")
    for i, mask in enumerate(masks):
        s = st[mask]
        row = f"{mask:11s}{' '.join(f'{v:6.3f}' for v in s['s8']):21s}{' '.join(f'{v:6.3f}' for v in s['s26'])}"
        fig.text(0.66, 0.44 - 0.028 * i, row, fontsize=8.0, family="monospace", ha="left")
    # how many of the 9 (session, mask) pairs have YOLO26n slower
    slower = sum(1 for mask in masks for a, b in zip(st[mask]["s26"], st[mask]["s8"]) if a > b)
    npair = sum(len(st[m]["s26"]) for m in masks)
    fig.text(0.66, 0.352, f"YOLO26n chậm hơn ở {slower} trên {npair} cặp (phiên, core_mask)", fontsize=9.3, color=DARK,
             ha="left")

    # ---- conditions ----
    thermal = max(r[k][t] for r in runs for k in ("before", "after") for t in ("soc-thermal", "npu-thermal"))
    npu = {tuple(r["freq_in_eval_perf"]["NPU"]) for r in runs}
    ddr = {tuple(r["freq_in_eval_perf"]["DDR"]) for r in runs}
    assert len(npu) == 1 and len(ddr) == 1
    order = ", ".join(f"phiên {s}: {name[first[s]]} trước" for s in sessions)
    lines = [
        f"Điều kiện đo: RK3588S (Orange Pi 5), rknn-toolkit2 2.3.2, eval_perf với fix_freq=True: NPU {npu.pop()[0]} Hz, DDR {ddr.pop()[0]} Hz",
        f"(đọc từ đầu ra eval_perf của {len(runs)} nhóm đo); nhiệt độ soc-thermal và npu-thermal tối đa {thermal:.1f} độ C. Thiết kế: 3 phiên cách nhau 180 giây,",
        f"thứ tự model xen kẽ ({order}), 3 core_mask, 5 lần eval_perf mỗi (model, core_mask, phiên).",
        "Model: YOLO('yolov8n.yaml') và YOLO('yolo26n.yaml'), nc=5, trọng số ngẫu nhiên, xuất bằng đường export(format=\"rknn\") thật của repo",
        "(opset 19, onnxslim), INT8, calibration 40 ảnh: chỉ cấu trúc và độ trễ, không có accuracy, nên không dùng để chọn model.",
        "15 giá trị mỗi nhóm không độc lập (5 lần lặp trong một phiên) và chỉ có 3 phiên mỗi model: p lạc quan; chiều chênh lệch vững hơn độ lớn.",
    ]
    cond_box(fig, lines)
    source_line(fig, "Nguồn: tmp/04_debug-logs/2026-10-10_yolo-phaseA/raw/phaseA.json, out/stats_latency.txt (stats_latency.py), README.md.",
                y=0.012)
    tier_label(fig, "T3 đo")
    return fig


# =====================================================================
# Hinh 10.5: duong cong train + FP32 test
# =====================================================================
RUN_DEFS = [("yolov8n_baseline", "YOLOv8n (SiLU)", BLUE), ("yolov8s_baseline", "YOLOv8s", GRAY),
            ("yolo26n_baseline", "YOLO26n", ORANGE), ("yolov8n_relu", "YOLOv8n ReLU (khởi tạo từ SiLU)", GREEN)]


def run_dir(key):
    return os.path.join(RUNS, f"sfchd_5class_{key}_100ep_s42")


def leaderboard_rows():
    with open(LEADERBOARD, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["protocol"] == "v1" and r["eval_set"] == "sfchd_test"]
    return {r["run_id"]: r for r in rows}


def metrics_csv(key):
    with open(os.path.join(run_dir(key), "metrics.csv"), encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    ep = [int(r["epoch"]) for r in rows]
    return ep, [float(r["metrics/mAP50(B)"]) for r in rows], [float(r["metrics/mAP50-95(B)"]) for r in rows]


def fig_train_curves():
    lb = leaderboard_rows()
    fig = plt.figure(figsize=(11.5, 9.0))
    axa = fig.add_axes([0.06, 0.44, 0.29, 0.40])
    axz = fig.add_axes([0.405, 0.44, 0.25, 0.40])
    axc = fig.add_axes([0.745, 0.44, 0.235, 0.40])
    data = {}
    for key, lab, c in RUN_DEFS:
        ep, m50, m5095 = metrics_csv(key)
        data[key] = (ep, m50, m5095)
        axa.plot(ep, m5095, color=c, lw=1.6, label=lab, zorder=3)
        axz.plot(ep, m5095, color=c, lw=1.6, zorder=3)
        axz.text(ep[-1] + 0.6, m5095[-1], f"{m5095[-1]:.3f}", color=c, fontsize=8.5, va="center", fontweight="bold")
    axa.set_xlabel("epoch")
    axa.set_ylabel("val mAP50-95 (mỗi epoch, trong lúc train)")
    axa.set_xlim(0, 100)
    axa.set_ylim(0.30, 0.66)
    axa.legend(loc="lower right", fontsize=8.2)
    zlo = 60
    axz.set_xlim(zlo, 108)
    ylo = min(min(d[2][zlo - 1:]) for d in data.values())
    yhi = max(max(d[2][zlo - 1:]) for d in data.values())
    axz.set_ylim(ylo - 0.01, yhi + 0.01)
    axz.set_xlabel("epoch (phóng to từ epoch %d)" % zlo)
    fig.text(0.06, 0.885, "A. Đường cong VAL: mAP50-95 sau mỗi epoch (tập val)", fontsize=11, fontweight="bold", ha="left")
    fig.text(0.405, 0.885, "A'. Phóng to cuối huấn luyện, nhãn là giá trị epoch 100", fontsize=11, fontweight="bold",
             ha="left")
    # ---- panel C: test numbers (dot plot, no truncated bars) ----
    for i, (key, lab, c) in enumerate(RUN_DEFS):
        r = lb[f"sfchd_5class_{key}_100ep_s42"]
        t = float(r["map50_95"])
        axc.scatter([t], [i], s=70, color=c, zorder=4)
        axc.text(t, i - 0.28, f"{t:.4f}", ha="center", va="bottom", fontsize=9, fontweight="bold", color=c)
        v = data[key][2][-1]
        axc.scatter([v], [i], s=55, marker="D", facecolor="white", edgecolor=c, linewidth=1.5, zorder=3)
    axc.set_yticks(range(len(RUN_DEFS)))
    axc.set_yticklabels([d[1].replace(" (khởi tạo từ SiLU)", "\n(khởi tạo từ SiLU)") for d in RUN_DEFS], fontsize=8.8)
    axc.invert_yaxis()
    axc.set_ylim(len(RUN_DEFS) - 0.4, -0.7)
    axc.set_xlim(0.55, 0.635)
    axc.set_xticks([0.56, 0.58, 0.60, 0.62])
    axc.set_xlabel("mAP50-95")
    axc.grid(axis="y", visible=False)
    import matplotlib.lines as ml
    axc.legend(handles=[ml.Line2D([], [], color=INK, marker="o", ls="", ms=7, label="TEST, FP32 (best.pt, protocol v1)"),
                        ml.Line2D([], [], color=INK, marker="D", ls="", mfc="white", ms=6, label="VAL, epoch 100 (đường cong A)")],
               loc="lower center", bbox_to_anchor=(0.45, 1.01), fontsize=8.3, frameon=False)
    fig.text(0.745, 0.935, "C. Số TEST của leaderboard", fontsize=11, fontweight="bold", ha="left")

    # ---- conditions ----
    args = {k: yaml.safe_load(read_text(os.path.join(run_dir(k), "args.yaml"))) for k, _, _ in RUN_DEFS}

    def transferred(k):
        logs = sorted(glob.glob(os.path.join(run_dir(k), "logs", "train_*.log")))
        m = re.search(r"Transferred (\d+/\d+) items", read_text(logs[-1]))
        return m.group(1)
    r0 = lb["sfchd_5class_yolov8n_baseline_100ep_s42"]
    epochs = {args[k]["epochs"] for k in args}
    seeds = {args[k]["seed"] for k in args}
    batches = ", ".join(f"{lab.split(' (')[0]} {args[k]['batch']}" for k, lab, _ in RUN_DEFS)
    lines = [
        f"Điều kiện: seed {seeds.pop()} duy nhất, {epochs.pop()} epoch, cùng dữ liệu sfchd_5class (dataset_fingerprint {r0['dataset_fingerprint']}), "
        f"optimizer {args['yolov8n_baseline']['optimizer']}.",
        f"Batch: {batches}.",
        f"Một lần huấn luyện mỗi model: chưa biết nhiễu giữa các seed, nên chênh lệch nhỏ giữa model (ví dụ {abs(float(lb['sfchd_5class_yolov8n_baseline_100ep_s42']['map50_95']) - float(lb['sfchd_5class_yolo26n_baseline_100ep_s42']['map50_95'])):.4f} giữa YOLOv8n và YOLO26n) không phải kết luận.",
        f"YOLOv8n ReLU khởi tạo từ yolov8n.pt SiLU rồi fine-tune (log train: Transferred {transferred('yolov8n_relu')} items, YOLOv8n baseline {transferred('yolov8n_baseline')}).",
        "Nhận định \"AP này có thể thấp hơn AP của ReLU train từ đầu\" là của bộ hình, chưa kiểm bằng thí nghiệm.",
        "VAL (đường cong A, kim cương ở C) là tập val sau mỗi epoch trong lúc train; TEST (chấm ở C) là tập test, best.pt, evaluator protocol v1:",
        "khác tập, khác evaluator, và best.pt không nhất thiết là epoch 100.",
    ]
    cond_box(fig, lines)
    source_line(fig, "Nguồn: ai/automation/runs/sfchd_5class_{yolov8n_baseline,yolov8s_baseline,yolo26n_baseline,yolov8n_relu}_100ep_s42/"
                "metrics.csv, args.yaml, logs/train_*.log; ai/automation/leaderboards/sfchd_5class.csv.", y=0.012)
    tier_label(fig, "T3 đo")
    return fig


# =====================================================================
# Hinh 10.7: mAP FP32 theo lop, cot FP16/INT8 cho
# =====================================================================
def fig_map_int8():
    lb = leaderboard_rows()
    classes = ["person", "helmet", "head", "safety_clothes", "self_clothes"]
    evals = {k: json.loads(read_text(os.path.join(run_dir(k), "eval", "pt_fp32_sfchd_test.json"))) for k, _, _ in RUN_DEFS}
    inst = {c: {evals[k]["per_class"][c]["instances"] for k in evals} for c in classes}
    assert all(len(v) == 1 for v in inst.values())
    nimg = {evals[k]["n_images"] for k in evals}
    assert len(nimg) == 1
    fig = plt.figure(figsize=(11.5, 8.5))
    axa = fig.add_axes([0.06, 0.40, 0.56, 0.44])
    bw = 0.2
    for j, (key, lab, c) in enumerate(RUN_DEFS):
        r = lb[f"sfchd_5class_{key}_100ep_s42"]
        vals = [float(r["map50_95"])] + [float(r[f"ap50_95_{cl}"]) for cl in classes]
        xs = [i + (j - 1.5) * bw for i in range(len(vals))]
        axa.bar(xs, vals, bw * 0.92, color=c, alpha=0.88, label=lab, zorder=2)
        for x, v in zip(xs, vals):
            axa.text(x, v + 0.008, f"{v:.3f}", ha="center", va="bottom", fontsize=6.8, rotation=90)
    axa.set_xticks(range(6))
    axa.set_xticklabels(["mAP50-95\n(tổng)"] + [f"{c}\n{next(iter(inst[c]))} ví dụ" for c in classes], fontsize=9)
    axa.axvline(0.5, color="#999999", lw=1, ls=":")
    axa.set_ylim(0, 0.95)
    axa.set_ylabel("AP50-95, FP32, tập test")
    axa.legend(loc="upper right", fontsize=8.3, ncol=2)
    fig.text(0.06, 0.885, "A. FP32 (best.pt, PyTorch), tập test sfchd_5class", fontsize=11, fontweight="bold", ha="left")
    for k, (x0, lab) in enumerate([(0.675, "B. FP16 trên board"), (0.835, "C. INT8 trên board")]):
        ax = fig.add_axes([x0, 0.40, 0.145, 0.44])
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
        ax.set_facecolor("#FFF3F3")
        for sp in ax.spines.values():
            sp.set_visible(True)
            sp.set_color(RED)
            sp.set_linestyle("--")
            sp.set_linewidth(1.3)
        ax.text(0.5, 0.5, "chờ\nmake phase3\n\nchưa có số", ha="center", va="center", fontsize=12, color=RED,
                transform=ax.transAxes)
        fig.text(x0, 0.885, lab, fontsize=11, fontweight="bold", ha="left")
    pr = evals["yolov8n_baseline"]["protocol"]
    lines = [
        f"Điều kiện: FP32 là weights/best.pt chạy bằng PyTorch trên tập test sfchd_5class ({nimg.pop()} ảnh), evaluator protocol v1: {pr['input']},",
        f"conf {pr['conf']}, iou {pr['iou']}, max_det {pr['max_det']}, multi_label. Seed 42, 100 epoch, một lần huấn luyện mỗi model.",
        "YOLOv8n ReLU khởi tạo từ trọng số SiLU rồi fine-tune; nhận định \"AP này có thể thấp hơn AP của ReLU train từ đầu\" là của bộ hình, chưa kiểm bằng thí nghiệm.",
        "Cột FP16 và INT8 (mAP của RKNN chạy trên board) chờ pipeline phase3: hình không điền giá trị nào và không suy INT8 từ FP32.",
        f"Số ví dụ mỗi lớp trên tập test: head {next(iter(inst['head']))} và self_clothes {next(iter(inst['self_clothes']))}, ít hơn nhiều so với person {next(iter(inst['person']))}; chỉ có seed 42 nên chưa biết nhiễu giữa các seed.",
        "Quy tắc chọn model dùng mAP50-95 INT8 tổng, không dùng AP từng lớp; nếu một lớp vi phạm PPE sụt mạnh sau INT8 cần xem riêng (chưa có số từng lớp).",
    ]
    cond_box(fig, lines)
    source_line(fig, "Nguồn: ai/automation/leaderboards/sfchd_5class.csv (protocol v1, sfchd_test), runs/*/eval/pt_fp32_sfchd_test.json, "
                "tmp/02_decisions/2026-10-11_model-selection-rule.md.", y=0.012)
    tier_label(fig, "T3 đo")
    return fig


# =====================================================================
# Hinh 10.6: calibration (figlib diagram, T3 PC)
# =====================================================================
def calib_table():
    """Parse the result table of the calibration README: label -> dict(dataset, minmax, infer)."""
    txt = read_text(os.path.join(CALIB, "README.md"))
    sec = txt.split("## Kết quả", 1)[1].split("## Không kết luận được", 1)[0]
    out = {}
    for ln in sec.split("\n"):
        if not ln.startswith("|") or ln.startswith("|---") or ln.startswith("| Phép thử"):
            continue
        c = [x.strip().replace("`", "") for x in ln.strip().strip("|").split("|")]
        if len(c) == 4:
            out[c[0]] = dict(dataset=c[1], mm=c[2], infer=c[3])
    unk = txt.split("## Không kết luận được", 1)[1]
    unknown = []
    for ln in unk.split("\n"):
        if ln.startswith("|") and not ln.startswith("|---") and not ln.startswith("| Câu hỏi"):
            unknown.append(ln.strip().strip("|").split("|")[0].strip())
    return out, unknown


def wrap(s, w):
    return textwrap.wrap(s, w) or [""]


def fig_calibration():
    from figlib import BLUE as FB, DARK as FD, GREEN as FG, RED as FR, Fig, source  # noqa: F401
    T, unknown = calib_table()
    f = Fig(900, 1000)
    f.tier(808, 8, "T3 đo")
    # --- header: the toy model ---
    f.rich(10, 44, [("Model thử: ", "b"), ("ONNX một Conv 1x1 đồng nhất, input NCHW [1,3,64,64]; toolkit 2.3.2, PC, không board; "
                                         "đọc min và max của tensor x từ quant_tab trong file .rknn.", "t")], size=13)
    f.rich(10, 64, [("Ảnh dùng là gradient 150 đến 250; mean=250, std=1, nên dải kỳ vọng sau chuẩn hóa là [-100, 0].", "t")], size=13)
    X1, W1, X2, W2, X3, W3 = 10, 285, 335, 255, 640, 250
    y = 90
    f.text(X1 + W1 / 2, y, "Ta đưa vào", size=14, weight=700, anchor="middle")
    f.text(X2 + W2 / 2, y, "Đọc được (min / max)", size=14, weight=700, anchor="middle")
    f.text(X3 + W3 / 2, y, "Suy ra", size=14, weight=700, anchor="middle")
    y += 14

    def row(title, lines_in, lines_obs, lines_inf, pic=None, min_h=0):
        nonlocal y
        f.text(X1, y + 10, title, size=14, weight=700, fill=FD)
        y += 24
        n = max(len(lines_in), len(lines_obs), len(lines_inf))
        h = max(14 + 17 * n, min_h)
        for x, w, ls, fill in ((X1, W1, lines_in, "white"), (X2, W2, lines_obs, "#E8F4EA"), (X3, W3, lines_inf, "white")):
            f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="#333333" stroke-width="1.2"/>')
            for i, ln in enumerate(ls):
                f.text(x + 10, y + 15 + 17 * i, ln, size=12.5)
        f.line([(X1 + W1, y + h / 2), (X2, y + h / 2)], FB)
        f.line([(X2 + W2, y + h / 2), (X3, y + h / 2)], FB)
        if pic:
            pic(y, h)
        y += h + 14

    def lines(s, w):
        return wrap(s, w)

    # 1 stretch
    t_ctrl, t_w, t_t = T["Đối chứng"], T["Ảnh rộng"], T["Ảnh cao"]
    def pic_stretch(y0, h):
        # wide image squeezed into a square (schematic)
        f.a(f'<rect x="{X1 + 205}" y="{y0 + 8}" width="64" height="32" fill="#DDE8F8" stroke="#333333"/>')
        f.line([(X1 + 237, y0 + 42), (X1 + 237, y0 + 54)], FB)
        f.a(f'<rect x="{X1 + 221}" y="{y0 + 56}" width="32" height="32" fill="#DDE8F8" stroke="#333333"/>')
        f.text(X1 + 214, y0 + 72, "(minh họa)", size=11, fill=FD, italic=True, anchor="end")
    row("1. Ảnh khác kích thước model",
        lines(f"{t_w['dataset']} (rộng); {t_t['dataset']} (cao); mean=250, std=1", 27),
        [f"ảnh rộng: {t_w['mm']}", f"ảnh cao: {t_t['mm']}", f"đối chứng 64x64: {t_ctrl['mm']}"],
        lines(t_w["infer"], 38), pic_stretch, 100)
    # 2 interpolation
    t_i = T["Nội suy"]
    def pic_interp(y0, h):
        for k in range(8):
            f.a(f'<rect x="{X1 + 205 + 8 * k}" y="{y0 + 8}" width="8" height="30" fill="{"#999999" if k % 2 == 0 else "#EEEEEE"}" stroke="#666666" stroke-width="0.5"/>')
        f.line([(X1 + 237, y0 + 42), (X1 + 237, y0 + 54)], FB)
        f.a(f'<rect x="{X1 + 221}" y="{y0 + 56}" width="32" height="30" fill="#C8C8C8" stroke="#666666"/>')
    row("2. Nội suy khi đổi kích thước", lines(t_i["dataset"], 27), [t_i["mm"]], lines(t_i["infer"], 38), pic_interp, 100)
    # 3 npy layout
    n1, n2 = T["npy NCHW float32 và uint8 [1,3,64,64]"], T["npy [3,64,64]"]
    n3, n4 = T["npy NHWC [1,64,64,3]"], T["npy [1,3,32,32]"]
    err = re.search(r"ValueError", n3["mm"]) and "ValueError"
    row("3. npy: layout và kích thước",
        ["npy NCHW float32 và uint8 [1,3,64,64]", "npy [3,64,64]", "npy NHWC [1,64,64,3]", "npy [1,3,32,32]"],
        [f"{n1['mm']}", f"{n2['mm']}", f"{err}: shape wrong, expect nchw", f"{err}: cùng dạng thông báo"],
        [f"{n1['infer']}", f"{n2['infer']}", f"{n3['infer']}", f"{n4['infer']}"])
    # 4 mean/std on npy
    m1, m0 = T["mean/std lên npy"], T["Đối chứng mean"]
    row("4. mean và std với npy",
        lines(m1["dataset"] + "; đối chứng: " + m0["dataset"], 44),
        [f"mean=250 std=2: {m1['mm']}", f"mean=0 std=1: {m0['mm']}"],
        lines(m1["infer"] + "; " + m0["infer"], 38))
    # 5 dtype
    d = T["quantized_dtype"]
    row("5. Tên quantized_dtype cũ",
        lines(d["dataset"], 44),
        lines(d["mm"], 40),
        lines(d["infer"] + ". Chấp nhận ở config() chưa chứng minh phần cứng hỗ trợ.", 38))
    # unknown + legend
    y += 2
    yb = f.unknown(10, y, [unknown[0] + " (chỉ loại được nearest);", unknown[1] + ";",
                           unknown[2] + "; " + unknown[3] + ";", unknown[4] + "; " + unknown[5] + "."], w=880)
    y = f.legend(10, yb + 10, 880, [("fill:#E8F4EA", "số đo T3 có file log (min và max đọc từ quant_tab của file .rknn)"),
                                    ("blue", "đưa vào, đọc được, suy ra (suy ra là của log, không phải câu của vendor)")])
    source(f, y + 8, "Nguồn: tmp/04_debug-logs/2026-10-10_t3-calibration-pc/README.md, probe.py (toolkit 2.3.2, một model thử).")
    return f


def save_svg_figure(name, f, outdir):
    """figlib diagram: write SVG and a 3x PNG through chrome (same as figlib.run)."""
    from figlib import to_png
    svg_path = os.path.join(outdir, name + ".svg")
    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write(f.svg())
    png = to_png(svg_path, os.path.join(outdir, name + ".png"), f.w, f.h)
    print(f"{name}: {f.w}x{f.h}{' + png' if png else ''}")


# Hinh 10.8 (h10-8-do-tre-map) has no data yet: no figure, only a status line in chu-thich.md.
FIGS = [("h10-1-silu-relu", fig_silu_relu, "mpl"), ("h10-2-do-tre-tung-lop", fig_per_layer, "mpl"),
        ("h10-3-da-loi", build, "mpl"), ("h10-4-v8n-26n", fig_v8n_26n, "mpl"),
        ("h10-5-duong-cong-train", fig_train_curves, "mpl"), ("h10-6-calibration", fig_calibration, "svg"),
        ("h10-7-map-int8", fig_map_int8, "mpl")]


if __name__ == "__main__":
    args = sys.argv[1:]
    names = [n for n, _, _ in FIGS]
    out = args[0] if args and args[0] not in names else HERE
    only = [a for a in args if a in names]
    for name, fn, kind in FIGS:
        if only and name not in only:
            continue
        if kind == "mpl":
            save(fn(), out, name)
        else:
            save_svg_figure(name, fn(), out)
