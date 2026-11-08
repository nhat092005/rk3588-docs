"""Hình cho các trang của nhóm Kết quả đo NPU (04-tang-npu-ket-qua), vẽ bằng matplotlib từ results/*.json.

Dùng: .venv/bin/python docs/tools/figure_gen/03-phuong-phap/04-tang-npu-ket-qua/gen.py [outdir] [tên_ảnh ...]
Mỗi hình ghi vào thư mục con theo tên trang. Số trong hình lấy nguyên từ JSON mà generator của trang dùng cho bảng.
"""
import json
import os
import sys
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
OUTROOT = os.path.join(ROOT, "docs", "_assets", "generated", "03-phuong-phap", "04-tang-npu-ket-qua")
BLUE, GRAY, INK, GREEN, RED, LGRAY = "#1E5BB8", "#555555", "#222222", "#2E7D32", "#C62828", "#BBBBBB"
SET_NAME = {"css_test": "css_test", "ppe2286_ext": "ppe2286_ext"}
MASKS = ["CORE_0", "CORE_0_1", "CORE_0_1_2", "AUTO"]

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
                     "svg.fonttype": "none", "svg.hashsalt": "rk3588", "font.size": 10})


def J(name):
    return json.load(open(os.path.join(ROOT, "results", name), encoding="utf-8"))


def wrap(s, n=14):
    return "\n".join(textwrap.wrap(s, n)) or s


def clean(ax, grid="y"):
    ax.grid(axis=grid, color="#E6E6E6", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


def hline(ax, y, label, color=GRAY):
    ax.axhline(y, color=color, linestyle="--", linewidth=0.8, zorder=2)
    ax.text(1.006, y, label, transform=ax.get_yaxis_transform(), fontsize=7.5, va="center", color=color)


def vline(ax, x, label, color=GRAY):
    ax.axvline(x, color=color, linestyle="--", linewidth=0.8, zorder=2)
    ax.text(x, 1.01, label, transform=ax.get_xaxis_transform(), fontsize=7.5, ha="center", va="bottom", color=color)


def finish(fig, h, notes, handles=None, ncol=3, left=0.1, right=0.955, top=0.9, extra=0.0, wspace=None, hspace=0.18):
    if handles:
        fig.legend(handles=handles, loc="upper center", ncol=ncol, frameon=False, fontsize=8.5, bbox_to_anchor=(0.52, 0.995))
    fig.text(0.01, 0.004, "\n".join(notes), fontsize=7.2, style="italic", color="#444444", va="bottom", ha="left")
    bottom = (0.3 + 0.125 * len(notes) + extra) / h
    kw = {"hspace": hspace}
    if wspace is not None:
        kw["wspace"] = wspace
    fig.subplots_adjust(left=left, right=right, top=top if not handles else top, bottom=bottom, **kw)


def mk(marker, color, label, face=True, size=6.5):
    return Line2D([], [], marker=marker, linestyle="", markersize=size, label=label, color=color,
                  markerfacecolor=color if face else "none", markeredgecolor=color)


MODEL_STYLE = {"silu": ("SiLU", "s", GRAY, False), "relu": ("ReLU", "o", BLUE, True)}


def scat(ax, xs, ys, marker, color, face=True, s=40, z=4):
    ax.scatter(xs, ys, s=s, marker=marker, facecolors=color if face else "none", edgecolors=color, linewidths=1.2, zorder=z)


# ----------------------------------------------------------------------------------------------- page 01
def fig_g4_phu_resize():
    G = J("g4_latency_workload.json")
    h = 3.9
    fig, axes = plt.subplots(1, 2, figsize=(7.4, h), gridspec_kw={"width_ratios": [1, 1.6]})
    ax = axes[0]
    for i, m in enumerate(("silu", "relu")):
        cov = [c * 100 for c in G["gate_a"][m]["coverage_per_session"]]
        scat(ax, [i - 0.07], [cov[0]], "o", BLUE, True, 44)
        scat(ax, [i + 0.07], [cov[1]], "o", BLUE, False, 90, 3)
        ax.annotate(f"{cov[0]:.1f}%", (i, cov[0]), textcoords="offset points", xytext=(0, 12), ha="center", fontsize=8.5)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["SiLU", "ReLU"]); ax.set_xlim(-0.6, 1.6); ax.set_ylim(-5, 112)
    ax.set_ylabel("Độ phủ đa nhân (%)"); clean(ax)
    ax = axes[1]
    xs, labels = [], []
    k = 0
    for m in ("silu", "relu"):
        for r in G["resize"][m]:
            tag = r["name"].split("/")[2] if r["name"].count("/") >= 3 else r["name"]
            scat(ax, [k - 0.1], [r["time_us_core012"]], "o", BLUE, True, 44)
            scat(ax, [k + 0.1], [r["time_us_core0"]], "s", GRAY, False, 46)
            labels.append(f"{'SiLU' if m == 'silu' else 'ReLU'}\n{tag}"); k += 1
    ax.set_xticks(range(k)); ax.set_xticklabels(labels, fontsize=8); ax.set_xlim(-0.6, k - 0.4)
    ax.set_ylim(0, max(r["time_us_core0"] for m in G["resize"] for r in G["resize"][m]) * 1.3)
    ax.set_ylabel("Thời gian dòng Resize (µs)"); clean(ax)
    hd = [mk("o", BLUE, "phiên 1 (đặc)", True, 5), mk("o", BLUE, "phiên 2 (vòng)", False, 8), mk("o", BLUE, "CORE_0_1_2"),
          mk("s", GRAY, "CORE_0", False)]
    finish(fig, h, ["Board RK3588, YOLOv8n INT8 (SiLU và ReLU), P2. Trái: độ phủ của hai phiên đo (điều kiện A). Phải: hai dòng Resize mỗi model.",
                    "File: results/g4_latency_workload.json (khóa gate_a, resize)"], hd, ncol=4, wspace=0.32)
    return fig


def fig_g4_theo_op():
    G = J("g4_latency_workload.json")
    ops = sorted({o for m in G["by_op"] for o in G["by_op"][m]},
                 key=lambda o: -max(G["by_op"][m].get(o, {}).get("time_share_core0", 0) for m in G["by_op"]))
    h = 0.34 * len(ops) + 2.0
    fig, ax = plt.subplots(figsize=(7.4, h))
    for m, off in (("silu", -0.12), ("relu", 0.12)):
        name, mkr, col, face = MODEL_STYLE[m]
        pts = [(i + off, G["by_op"][m][o]["time_share_core0"] * 100) for i, o in enumerate(ops) if o in G["by_op"][m]]
        scat(ax, [p[1] for p in pts], [p[0] for p in pts], mkr, col, face, 40)
    ax.set_yticks(range(len(ops))); ax.set_yticklabels(ops, fontsize=8.5); ax.invert_yaxis()
    ax.set_xlabel("Tỉ lệ thời gian của op trên CORE_0 (%)"); ax.set_ylabel("Op")
    clean(ax, "x")
    finish(fig, h, ["Board RK3588, YOLOv8n INT8, CORE_0, chế độ debug. Op không xuất hiện trong một model thì không có điểm của model đó.",
                    "File: results/g4_latency_workload.json (khóa by_op)"],
           [mk("s", GRAY, "SiLU", False), mk("o", BLUE, "ReLU")], ncol=2, left=0.22, extra=0.45, top=0.95)
    return fig


def fig_g4_latency():
    G = J("g4_latency_workload.json")
    h = 4.0
    fig, axes = plt.subplots(1, 2, figsize=(7.4, h), gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]
    for m, off in (("silu", -0.15), ("relu", 0.15)):
        name, mkr, col, face = MODEL_STYLE[m]
        for i, mask in enumerate(MASKS):
            c = G["conditions"][f"{m}|{mask}"]
            for sm in c["session_medians"]:
                ax.scatter([i + off], [sm], s=8, color=LGRAY, zorder=2)
            scat(ax, [i + off], [c["median"]], mkr, col, face, 44)
    ax.set_xticks(range(4)); ax.set_xticklabels([m.replace("CORE_", "CORE ").replace("_", "+") for m in MASKS], fontsize=8.5)
    ax.set_xlim(-0.5, 3.5); ax.set_ylabel("Median latency (ms)"); clean(ax)
    ax = axes[1]
    for m, off in (("silu", -0.12), ("relu", 0.12)):
        name, mkr, col, face = MODEL_STYLE[m]
        for i, mask in enumerate(("CORE_0_1", "CORE_0_1_2")):
            scat(ax, [i + off], [G["gate_b"][f"{m}|{mask}"]["drop_pct"]], mkr, col, face, 44)
    hline(ax, 5, "5%")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["CORE 0+1", "CORE 0+1+2"], fontsize=8.5); ax.set_xlim(-0.5, 1.5)
    ax.set_ylabel("Giảm latency so với CORE_0 (%)"); clean(ax)
    finish(fig, h, ["Board RK3588, YOLOv8n INT8, P2, hai phiên. Chấm xám nhỏ là median của từng phiên.",
                    "Đường đứt 5% là ngưỡng giảm tối thiểu của điều kiện B. File: results/g4_latency_workload.json (khóa conditions, gate_b)"],
           [mk("s", GRAY, "SiLU", False), mk("o", BLUE, "ReLU"), mk("o", LGRAY, "median từng phiên", True, 3.5)], ncol=3, wspace=0.42, top=0.9)
    return fig


GATE_KEYS = ["css_test|int8", "css_test|fp16", "css_test|fp32", "ppe2286_ext|int8", "ppe2286_ext|fp16", "ppe2286_ext|fp32"]
DT_COL = {"int8": BLUE, "fp16": GREEN, "fp32": GRAY}
METRICS = [("map50_95", "AP50-95"), ("NoHelmet", "AP NoHelmet"), ("Vest", "AP Vest")]


def fig_g4_cong_c():
    E = J("eval_g4.json")
    h = 4.2
    fig, ax = plt.subplots(figsize=(7.4, h))
    for j, key in enumerate(GATE_KEYS):
        st, dt = key.split("|")
        off = (j - 2.5) * 0.11
        for i, (mk_, _) in enumerate(METRICS):
            scat(ax, [i + off], [E["gate_c"][key]["diff_pp"][mk_]], "o" if st == "css_test" else "s", DT_COL[dt],
                 st == "css_test", 38)
    hline(ax, -1.0, "-1.0")
    ax.set_xticks(range(3)); ax.set_xticklabels([n for _, n in METRICS]); ax.set_xlim(-0.5, 2.5)
    ax.set_ylabel("Chênh ReLU so với SiLU (điểm %)"); clean(ax)
    hd = [mk("o", BLUE, "INT8"), mk("o", GREEN, "FP16"), mk("o", GRAY, "FP32"), mk("o", INK, "css_test (đặc)", True, 6),
          mk("s", INK, "ppe2286_ext (vòng)", False, 6)]
    finish(fig, h, ["Điều kiện C: ReLU trừ SiLU, seed 0, 100 epoch. Đường đứt -1.0 điểm là ngưỡng của cổng C.",
                    "File: results/eval_g4.json (khóa gate_c)"], hd, ncol=5)
    return fig


NOISE_ROWS = [f"{s}|{d}" for s, d in (("css_test", "int8"), ("css_test", "fp16"), ("css_test", "fp32"), ("ppe2286_ext", "int8"))]


def fig_g4_nhieu_seed():
    E = J("eval_g4.json")
    rows = [(k, mk_, name) for k in NOISE_ROWS for mk_, name in METRICS]
    h = 0.3 * len(rows) + 2.0
    fig, ax = plt.subplots(figsize=(7.4, h))
    for i, (k, mk_, name) in enumerate(rows):
        for vals, off, mkr, col, face in ((E["noise"][k][mk_]["values"], -0.14, "s", GRAY, False),
                                          (E["relu_noise"][k][mk_]["values"], 0.14, "o", BLUE, True)):
            ax.scatter(vals, [i + off] * len(vals), s=30, marker=mkr, facecolors=col if face else "none", edgecolors=col,
                       linewidths=1.1, zorder=4)
    labels = [f"{k.split('|')[0]} {k.split('|')[1].upper()} {name}" for k, _, name in rows]
    ax.set_yticks(range(len(rows))); ax.set_yticklabels(labels, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("AP (%)"); clean(ax, "x")
    finish(fig, h, ["Ba seed (0, 1, 2) mỗi model, 100 epoch. Mỗi hàng có ba điểm SiLU và ba điểm ReLU.",
                    "File: results/eval_g4.json (khóa noise, relu_noise)"],
           [mk("s", GRAY, "SiLU, ba seed", False), mk("o", BLUE, "ReLU, ba seed")], ncol=2, left=0.3, top=0.95, extra=0.45)
    return fig


def fig_g4_relu_3seed():
    E = J("eval_g4.json")
    per = E["relu_seed_gate_c"]["per_seed"]
    h = 3.6
    fig, ax = plt.subplots(figsize=(7.4, h))
    cols = {"map50_95": BLUE, "NoHelmet": RED, "Vest": GREEN}
    for j, (mk_, name) in enumerate(METRICS):
        for i, r in enumerate(per):
            scat(ax, [i + (j - 1) * 0.16], [r["diff_pp"][mk_]], "o", cols[mk_], True, 40)
    hline(ax, -1.0, "-1.0")
    ax.set_xticks(range(len(per))); ax.set_xticklabels([f"seed {r['seed']}" for r in per]); ax.set_xlim(-0.5, len(per) - 0.5)
    ax.set_ylabel("Chênh ReLU so với SiLU cùng seed (điểm %)"); clean(ax)
    finish(fig, h, ["css_test, INT8, ba seed. Đường đứt -1.0 điểm là ngưỡng của cổng C. File: results/eval_g4.json (khóa relu_seed_gate_c)"],
           [mk("o", cols[k], n) for k, n in METRICS], ncol=3)
    return fig


# ----------------------------------------------------------------------------------------------- page 02
VARIANTS = [("silu", "SiLU"), ("relu", "ReLU"), ("leakyrelu", "LeakyReLU"), ("relu6", "ReLU6"), ("relu200", "ReLU 200 epoch")]


def fig_bv_giam_latency():
    V1, V2 = J("g4v_latency_workload.json"), J("g4v_latency_workload_2.json")
    h = 3.9
    fig, ax = plt.subplots(figsize=(7.4, h))
    for V, off, mkr, col, face in ((V1, -0.13, "o", BLUE, True), (V2, 0.13, "s", GRAY, False)):
        for i, (m, _) in enumerate(VARIANTS):
            g = V["gate_b"][m]
            if "chưa kết luận" in g["verdict"]:
                ax.scatter([i + off], [g["drop_pct"]], s=60, marker="X", color=RED, zorder=5)
            else:
                scat(ax, [i + off], [g["drop_pct"]], mkr, col, face, 42)
    hline(ax, 5, "5%")
    ax.set_xticks(range(len(VARIANTS))); ax.set_xticklabels([wrap(n, 10) for _, n in VARIANTS], fontsize=8.5); ax.set_xlim(-0.5, len(VARIANTS) - 0.5)
    ax.set_ylabel("Giảm latency CORE_0_1_2 so với CORE_0 (%)"); clean(ax)
    finish(fig, h, ["Board RK3588, YOLOv8n INT8, P2, hai lần chạy thí nghiệm. Đường đứt 5% là ngưỡng giảm tối thiểu của điều kiện B.",
                    "Dấu X là ô có P2 không thực hiện đúng (chưa kết luận). File: results/g4v_latency_workload.json, g4v_latency_workload_2.json"],
           [mk("o", BLUE, "lần chạy 1"), mk("s", GRAY, "lần chạy 2", False), mk("X", RED, "P2 không thực hiện đúng")], ncol=3)
    return fig


def fig_bv_cong_c():
    E = J("eval_g4.json")
    rows = []
    for k, name in (("leakyrelu", "LeakyReLU"), ("relu6", "ReLU6"), ("relu200", "ReLU 200 epoch")):
        rows.append((name, {d: E["variants"][k][f"css_test|{d}"]["diff_vs_silu_pp"]["map50_95"] for d in ("int8", "fp16", "fp32")}))
    rows.append(("ReLU", {d: E["gate_c"][f"css_test|{d}"]["diff_pp"]["map50_95"] for d in ("int8", "fp16", "fp32")}))
    rows.append(("SiLU 200 epoch\n(đối chứng)", {d: E["silu200_vs_silu100"][f"css_test|{d}"]["map50_95"] for d in ("int8", "fp16", "fp32")}))
    h = 3.9
    fig, ax = plt.subplots(figsize=(7.4, h))
    for j, d in enumerate(("int8", "fp16", "fp32")):
        for i, (n, v) in enumerate(rows):
            scat(ax, [i + (j - 1) * 0.16], [v[d]], "o", DT_COL[d], True, 40)
    hline(ax, -1.0, "-1.0")
    ax.set_xticks(range(len(rows))); ax.set_xticklabels([wrap(n, 11) if "\n" not in n else n for n, _ in rows], fontsize=8.5)
    ax.set_xlim(-0.5, len(rows) - 0.5); ax.set_ylabel("Chênh AP50-95 (điểm %)"); clean(ax)
    finish(fig, h, ["css_test, ba kiểu số. Chênh so với SiLU seed 0, 100 epoch, riêng SiLU 200 epoch là chênh so với SiLU 100 epoch.",
                    "Đường đứt -1.0 điểm là ngưỡng cổng C của INT8. File: results/eval_g4.json (khóa variants, gate_c, silu200_vs_silu100)"],
           [mk("o", DT_COL[d], d.upper()) for d in ("int8", "fp16", "fp32")], ncol=3)
    return fig


# ----------------------------------------------------------------------------------------------- page 03
def fig_nhan_s1():
    G, T = J("g4_latency_workload.json"), J("thr_p3.json")
    h = 3.9
    fig, axes = plt.subplots(1, 2, figsize=(7.4, h))
    ax = axes[0]
    for i, mask in enumerate(MASKS[:3]):
        c = G["conditions"][f"silu|{mask}"]
        for sm in c["session_medians"]:
            ax.scatter([i], [sm], s=9, color=LGRAY, zorder=2)
        scat(ax, [i], [c["median"]], "o", BLUE, True, 46)
    ax.set_xticks(range(3)); ax.set_xticklabels(["CORE 0", "CORE 0+1", "CORE 0+1+2"], fontsize=8.5); ax.set_xlim(-0.5, 2.5)
    ax.set_ylabel("Median latency P2 (ms)"); clean(ax)
    ax = axes[1]
    for i, c in enumerate(("T1", "T2", "T3")):
        cf = T["configs"][c]
        ax.scatter([i] * len(cf["fps_runs"]), cf["fps_runs"], s=14, color=LGRAY, zorder=2)
        scat(ax, [i], [cf["fps"]], "o", BLUE, True, 46)
    ax.set_xticks(range(3)); ax.set_xticklabels(["CORE 0", "CORE 0+1", "CORE 0+1+2"], fontsize=8.5); ax.set_xlim(-0.5, 2.5)
    ax.set_ylabel("Thông lượng P3, một context (FPS)"); clean(ax)
    finish(fig, h, ["Board RK3588, YOLOv8n INT8 (SiLU), một context. Chấm xám là từng phiên (trái) hoặc từng lần chạy (phải), chấm xanh là median. Trục y không bắt đầu từ 0.",
                    "File: results/g4_latency_workload.json (khóa conditions), results/thr_p3.json (khóa configs)"],
           [mk("o", BLUE, "median"), mk("o", LGRAY, "từng phiên hoặc lần chạy", True, 3.5)], ncol=2, wspace=0.34)
    return fig


def fig_nhan_cau_hinh():
    T = J("thr_p3.json")
    cs = ["T1", "T4", "T5", "T6", "T7"]
    h = 4.3
    fig, ax = plt.subplots(figsize=(7.4, h))
    for i, c in enumerate(cs):
        cf = T["configs"][c]
        ax.scatter([i] * len(cf["fps_runs"]), cf["fps_runs"], s=16, color=LGRAY, zorder=2)
        scat(ax, [i], [cf["fps"]], "o", BLUE, True, 46)
    ax.set_xticks(range(len(cs))); ax.set_xticklabels([wrap(T["configs"][c]["label"], 16) for c in cs], fontsize=8)
    ax.set_xlim(-0.5, len(cs) - 0.5); ax.set_ylabel("Thông lượng P3 (FPS)"); clean(ax)
    finish(fig, h, ["Board RK3588, YOLOv8n INT8 (SiLU). Ba lần chạy mỗi cấu hình (xám), median (xanh). T7 là chẩn đoán, không phải cổng.",
                    "File: results/thr_p3.json (khóa configs)"], [mk("o", BLUE, "median ba lần chạy"), mk("o", LGRAY, "từng lần chạy", True, 3.5)], ncol=2)
    return fig


def fig_nhan_30fps():
    T = J("thr_p3.json")
    cs = ["T1", "T2", "T3", "T4", "T5", "T6"]
    h = 4.6
    fig, axes = plt.subplots(2, 1, figsize=(7.4, h), sharex=True)
    for i, c in enumerate(cs):
        cf = T["configs"][c]
        scat(axes[0], [i], [cf["fps"]], "o", BLUE, True, 46)
        scat(axes[1], [i], [cf["t_pre"] + cf["t_npu"] + cf["t_post"]], "o", BLUE, True, 46)
    hline(axes[0], 30, "30 FPS"); hline(axes[1], 1000 / 30, "33.33 ms")
    axes[0].set_ylabel("Thông lượng (FPS)"); axes[1].set_ylabel("T_pre + T_npu + T_post (ms)")
    axes[1].set_xticks(range(len(cs))); axes[1].set_xticklabels([wrap(T["configs"][c]["label"], 15) for c in cs], fontsize=8)
    axes[1].set_xlim(-0.5, len(cs) - 0.5)
    axes[0].set_ylim(0, 165); axes[1].set_ylim(0, 40)
    for ax in axes:
        clean(ax)
    finish(fig, h, ["Board RK3588, YOLOv8n INT8 (SiLU), ảnh cache trong bộ nhớ, không gồm thu nhận camera. Mục tiêu 30 FPS (camera 30 khung/giây), người dùng đổi từ 60 ngày 2026-11-08.",
                    "Hai cách đọc: thông lượng (trên) và thời gian mỗi khung (dưới). File: results/thr_p3.json (khóa configs)"], top=0.97, extra=0.4, right=0.9)
    return fig



# ----------------------------------------------------------------------------------------------- page 04
def fig_x7():
    X = J("eval_x7_ppe5_yolov8n_baseline_100ep_s0_int8.json")
    names = [("precision", "Precision"), ("recall", "Recall"), ("map50", "AP50"), ("map50_95", "AP50-95")]
    h = 3.9
    fig, axes = plt.subplots(1, 2, figsize=(7.4, h), sharey=True)
    for ax, st in zip(axes, ("css_test", "ppe2286_ext")):
        S = X["sets"][st]
        for i, (k, _) in enumerate(names):
            scat(ax, [i - 0.1], [S["int8"][k] * 100], "o", BLUE, True, 44)
            scat(ax, [i + 0.1], [S["fp32"][k] * 100], "s", GRAY, False, 46)
        ax.set_xticks(range(4)); ax.set_xticklabels([n for _, n in names], fontsize=8.5); ax.set_xlim(-0.5, 3.5)
        ax.text(0.02, 0.96, f"{st} ({S['n_images']} ảnh)", transform=ax.transAxes, fontsize=9.5, weight="bold", va="top")
        clean(ax)
    axes[0].set_ylabel("Giá trị (%)"); axes[0].set_ylim(0, 100)
    finish(fig, h, ["YOLOv8n, INT8 của file đo latency và FP32 chấm trên cùng tập ảnh. Điểm xanh là INT8, ô vuông rỗng là FP32.",
                    "File: results/eval_x7_ppe5_yolov8n_baseline_100ep_s0_int8.json (khóa sets)"],
           [mk("o", BLUE, "INT8 của file đo latency"), mk("s", GRAY, "FP32", False)], ncol=2, wspace=0.12)
    return fig


# ----------------------------------------------------------------------------------------------- page 05
def fig_q_diag():
    D = J("q2c_diag.json")
    rows = [(m, r) for m in ("silu", "relu") for r in D[m]["lowest_single"][:5]]
    h = 0.42 * len(rows) + 1.9
    fig, ax = plt.subplots(figsize=(7.4, h))
    for i, (m, r) in enumerate(rows):
        name, mkr, col, face = MODEL_STYLE[m]
        scat(ax, [r["mean_single_cos"]], [i], mkr, col, face, 44)
    short = lambda n: n.replace("/model/model.", "").replace("_output_0", "")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{'SiLU' if m == 'silu' else 'ReLU'}  {r['op']}  {short(r['name'])[:30]}" for m, r in rows], fontsize=8)
    ax.invert_yaxis(); ax.set_xlabel("Cosine một lớp, trung bình trên 10 ảnh")
    clean(ax, "x")
    finish(fig, h, ["Năm tensor có cosine thấp nhất mỗi model, mô phỏng INT8 trên PC (10 ảnh). File: results/q2c_diag.json (khóa lowest_single)"],
           [mk("s", GRAY, "SiLU", False), mk("o", BLUE, "ReLU")], ncol=2, left=0.4, top=0.95, extra=0.4)
    return fig


RECIPES = ["base", "kl", "h1", "h2", "h3", "h4", "h5", "h6", "c_all", "auto"]


def fig_q_cong_thuc():
    R = J("q2c_recipes.json")
    h = 4.0
    fig, ax = plt.subplots(figsize=(7.4, h))
    for m, off in (("silu", -0.13), ("relu", 0.13)):
        name, mkr, col, face = MODEL_STYLE[m]
        rec = R["models"][m]["recipes"]
        pts = [(i + off, rec[rc]["css_test"]["ap"]["map50_95"]) for i, rc in enumerate(RECIPES)
               if rec.get(rc) and rec[rc].get("css_test") and rec[rc]["css_test"].get("ap")]
        scat(ax, [x for x, _ in pts], [y for _, y in pts], mkr, col, face, 42)
        ax.axhline(R["models"][m]["ref"]["css_test"]["fp16"]["map50_95"], color=col, linestyle=":", linewidth=1.0, zorder=1)
    ax.set_xticks(range(len(RECIPES))); ax.set_xticklabels(RECIPES, fontsize=8.5); ax.set_xlim(-0.5, len(RECIPES) - 0.5)
    ax.set_ylabel("AP50-95 trên css_test (%)"); ax.set_xlabel("Công thức lượng tử hóa"); clean(ax)
    finish(fig, h, ["INT8 trên board với từng công thức. Công thức không chạy cho một model thì không có điểm. Đường chấm là AP50-95 FP16 của mỗi model.",
                    "File: results/q2c_recipes.json (khóa models)"],
           [mk("s", GRAY, "SiLU", False), mk("o", BLUE, "ReLU"), Line2D([], [], color=GRAY, linestyle=":", label="FP16 của model")], ncol=3, extra=0.3)
    return fig


def fig_q_h5_cong_c():
    R = J("q2c_recipes.json")
    h = 4.0
    fig, axes = plt.subplots(1, 2, figsize=(7.4, h), sharey=True, gridspec_kw={"width_ratios": [1, 2]})
    cols = {"map50_95": BLUE, "NoHelmet": RED, "Vest": GREEN}
    ax = axes[0]
    for i, rc in enumerate(("base", "h5")):
        for j, (mk_, _) in enumerate(METRICS):
            scat(ax, [i + (j - 1) * 0.18], [R["r_c"][f"{rc}|css_test"]["diff_pp"][mk_]], "o", cols[mk_], True, 40)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["base", "h5"]); ax.set_xlim(-0.5, 1.5)
    ax.set_ylabel("Chênh so với SiLU (điểm %)"); hline(ax, -1.0, ""); clean(ax)
    ax = axes[1]
    cands = [("relu200", "ReLU 200\nepoch"), ("leakyrelu", "LeakyReLU"), ("relu6", "ReLU6"), ("silu200", "SiLU 200\n(đối chứng)")]
    for i, (k, _) in enumerate(cands):
        for j, (mk_, _) in enumerate(METRICS):
            scat(ax, [i + (j - 1) * 0.18], [R["variants_h5"][k]["css_test"]["diff_vs_silu_h5"][mk_]], "o", cols[mk_], True, 40)
    ax.set_xticks(range(len(cands))); ax.set_xticklabels([n for _, n in cands], fontsize=8.5); ax.set_xlim(-0.5, len(cands) - 0.5)
    hline(ax, -1.0, "-1.0"); clean(ax)
    finish(fig, h, ["css_test, INT8 trên board. Trái: ReLU trừ SiLU dưới công thức base và h5. Phải: ứng viên trừ SiLU 100 epoch dưới h5.",
                    "Đường đứt -1.0 điểm là ngưỡng cổng C. File: results/q2c_recipes.json (khóa r_c, variants_h5)"],
           [mk("o", cols[k], n) for k, n in METRICS], ncol=3, wspace=0.12, right=0.93, extra=0.25)
    return fig


def _cost_fig(fname, key_a, key_b, note, finfile):
    D = J(fname)
    h = 3.6
    fig, ax = plt.subplots(figsize=(7.4, h))
    for m, off in (("silu", -0.12), ("relu", 0.12)):
        name, mkr, col, face = MODEL_STYLE[m]
        for i, mask in enumerate(("CORE_0", "CORE_0_1_2")):
            scat(ax, [i + off], [D["cost"][f"{m}|{mask}"]["cost_pct"]], mkr, col, face, 44)
    hline(ax, 5, "5%"); ax.axhline(0, color="#999999", linewidth=0.6)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["CORE 0", "CORE 0+1+2"]); ax.set_xlim(-0.5, 1.5)
    ax.set_ylabel(note); ax.set_ylim(-3, 8); clean(ax)
    finish(fig, h, ["Board RK3588, YOLOv8n INT8, P2. Chi phí dương là chậm hơn. Đường đứt 5% là ngưỡng tính là đáng kể.", f"File: results/{finfile}"],
           [mk("s", GRAY, "SiLU", False), mk("o", BLUE, "ReLU")], ncol=2)
    return fig


def fig_q_h5_chi_phi():
    return _cost_fig("q2h_latency.json", "base_ms", "h5_ms", "Chi phí latency của h5 so với INT8 (%)", "q2h_latency.json (khóa cost)")


# ----------------------------------------------------------------------------------------------- page 06
def fig_r_int8h5():
    N = J("int8h5.json")
    runs = list(N["runs"].keys())
    h = 3.9
    fig, ax = plt.subplots(figsize=(7.4, h))
    sty = {"int8": ("INT8 mặc định", "s", GRAY, False), "int8h5": ("int8h5", "o", BLUE, True), "fp16": ("FP16", "D", GREEN, False)}
    for j, d in enumerate(("int8", "int8h5", "fp16")):
        lab, mkr, col, face = sty[d]
        scat(ax, [i + (j - 1) * 0.16 for i in range(len(runs))], [N["runs"][r]["sets"]["css_test"][d]["map50_95"] for r in runs], mkr, col, face, 40)
    ax.set_xticks(range(len(runs))); ax.set_xticklabels([r.replace("_s", " seed ").replace("silu", "SiLU").replace("relu", "ReLU") for r in runs], fontsize=8.5)
    ax.set_xlim(-0.5, len(runs) - 0.5); ax.set_ylabel("AP50-95 trên css_test (%)"); clean(ax)
    finish(fig, h, ["Bốn lần chạy huấn luyện, ba kiểu xuất. File: results/int8h5.json (khóa runs)"], [mk(m_, c_, l_, f_) for l_, m_, c_, f_ in sty.values()], ncol=3)
    return fig


def fig_r_chi_phi():
    return _cost_fig("q2i_latency.json", "int8_ms", "int8h5_ms", "Chi phí latency của int8h5 so với INT8 (%)", "q2i_latency.json (khóa cost)")


# ----------------------------------------------------------------------------------------------- page 07
def fig_qat_a1():
    S = J("q2j_split.json")
    h = 4.0
    fig, axes = plt.subplots(1, 2, figsize=(7.4, h), gridspec_kw={"width_ratios": [1.1, 1]})
    ax = axes[0]
    keys = [("fp16", "FP16"), ("fp16_split", "FP16\ntách đầu"), ("int8", "INT8\nmặc định"), ("int8h5", "int8h5"), ("split", "A1\ntách đầu")]
    for i, (k, _) in enumerate(keys):
        scat(ax, [i], [S["accuracy"]["css_test"][k]["map50_95"]], "o", BLUE, True, 44)
    ax.set_xticks(range(len(keys))); ax.set_xticklabels([n for _, n in keys], fontsize=7.5); ax.set_xlim(-0.5, len(keys) - 0.5)
    ax.set_ylabel("AP50-95 trên css_test (%)"); ax.set_ylim(30, 55); clean(ax)
    ax = axes[1]
    for j, mask in enumerate(("CORE_0", "CORE_0_1_2")):
        for i, k in enumerate(("int8", "int8h5", "split")):
            c = S["conditions"][f"{k}|{mask}"]
            x = i + (j - 0.5) * 0.28
            if c["realized"]:
                scat(ax, [x], [c["median"]], "o" if j == 0 else "s", BLUE if j == 0 else GRAY, j == 0, 42)
            else:
                ax.scatter([x], [c["median"]], s=60, marker="X", color=RED, zorder=5)
    ax.set_xticks(range(3)); ax.set_xticklabels(["INT8\nmặc định", "int8h5", "A1\ntách đầu"], fontsize=8); ax.set_xlim(-0.6, 2.6)
    ax.set_ylabel("Median latency P2 (ms)"); clean(ax)
    hd = [mk("o", BLUE, "CORE_0"), mk("s", GRAY, "CORE_0_1_2", False), mk("X", RED, "P2 không thực hiện đúng")]
    finish(fig, h, ["Trái: AP50-95 của năm model. Phải: median latency, phần NPU, hai mặt nạ nhân. Dấu X là P2 không thực hiện đúng. Trục y của trái bắt đầu từ 30.",
                    "File: results/q2j_split.json (khóa accuracy, conditions)"], hd, ncol=3, wspace=0.3, extra=0.25)
    return fig


def fig_qat_a2():
    N = J("q2l_nodfl.json")
    h = 3.8
    fig, ax = plt.subplots(figsize=(7.4, h))
    ks = [("pt_fp32", "FP32 (PyTorch)"), ("rknn_fp16", "FP16"), ("rknn_int8", "INT8 mặc định")]
    for m, off, mkr, col, face, lab in (("silu", -0.12, "s", GRAY, False, "SiLU baseline"), ("a2", 0.12, "o", BLUE, True, "A2 bỏ DFL")):
        scat(ax, [i + off for i in range(3)], [N[m][k]["map50_95"] for k, _ in ks], mkr, col, face, 44)
    ax.set_xticks(range(3)); ax.set_xticklabels([n for _, n in ks]); ax.set_xlim(-0.5, 2.5)
    ax.set_ylabel("AP50-95 trên css_test (%)"); ax.set_ylim(30, 55); clean(ax)
    finish(fig, h, ["Hai model huấn luyện 100 epoch. Trục y bắt đầu từ 30. File: results/q2l_nodfl.json (khóa silu, a2)"],
           [mk("s", GRAY, "SiLU baseline", False), mk("o", BLUE, "A2 bỏ DFL")], ncol=2)
    return fig


def fig_qat_tong_hop():
    S, K, N = J("q2j_split.json"), J("q2k_qat.json"), J("q2l_nodfl.json")
    rows = [("A1\ntách đầu", S["accuracy"]["css_test"]["split"]["map50_95"]), ("B\nQAT", K["rknn_int8_qat"]["map50_95"]),
            ("A2\nbỏ DFL", N["a2"]["rknn_int8"]["map50_95"]), ("int8h5\n(tham chiếu)", S["accuracy"]["css_test"]["int8h5"]["map50_95"])]
    h = 3.6
    fig, ax = plt.subplots(figsize=(7.4, h))
    for i, (n, v) in enumerate(rows):
        scat(ax, [i], [v], "o", BLUE, True, 48)
        ax.annotate(f"{v:.2f}", (i, v), textcoords="offset points", xytext=(0, 10), ha="center", fontsize=8.5)
    hline(ax, 48.41, "48.41")
    ax.set_xticks(range(len(rows))); ax.set_xticklabels([n for n, _ in rows]); ax.set_xlim(-0.5, len(rows) - 0.5)
    ax.set_ylabel("AP50-95 INT8 trên css_test (%)"); ax.set_ylim(30, 55); clean(ax)
    finish(fig, h, ["Đường đứt 48.41 là tiêu chí viết trước dữ liệu: FP16 seed 0 của SiLU (49.76) trừ 1.35 điểm. Tiêu chí mới và chưa duyệt. Trục y bắt đầu từ 30.",
                    "File: results/q2j_split.json, q2k_qat.json, q2l_nodfl.json"], right=0.93, extra=0.3)
    return fig


# ----------------------------------------------------------------------------------------------- page 08
def fig_u_g7():
    M = J("q2e_micro.json")
    h = 3.9
    fig, ax = plt.subplots(figsize=(7.4, h))
    ks = ["A", "B", "C"]
    for off, field, mkr, col, face in ((-0.1, "npu_vs_own", "o", BLUE, True), (0.1, "npu_vs_ref", "s", GRAY, False)):
        scat(ax, [i + off for i in range(3)], [M["g7b"][k][field] for k in ks], mkr, col, face, 44)
    ax.set_yscale("log"); hline(ax, 0.01, "0.01")
    ax.set_xticks(range(3)); ax.set_xticklabels([f"{k}\n{M['g7b'][k]['attrs'][0]}, {M['g7b'][k]['attrs'][1]}" for k in ks], fontsize=8.5); ax.set_xlim(-0.5, 2.5)
    ax.set_ylabel("Độ lệch tối đa của NPU (thang log)"); clean(ax)
    finish(fig, h, ["Micro model Resize 1x256x20x20, tỉ lệ 2, FP16. Đường đứt 0.01 là ngưỡng khớp viết trước. A là bộ asymmetric, floor.",
                    "File: results/q2e_micro.json (khóa g7b)"],
           [mk("o", BLUE, "so với onnxruntime của chính nó"), mk("s", GRAY, "so với onnxruntime của A", False)], ncol=2, extra=0.2)
    return fig


def fig_u_qat_time():
    B = J("q2e_board.json")
    h = 3.8
    fig, ax = plt.subplots(figsize=(7.4, h))
    ks = [("int8h5", "int8h5"), ("split", "A1 tách đầu\n(chỉ NPU)"), ("qat", "QAT tách đầu\n(chỉ NPU)")]
    for j, mask in enumerate(("CORE_0", "CORE_0_1_2")):
        for i, (k, _) in enumerate(ks):
            c = B["qat_time"]["conditions"][f"{k}|{mask}"]
            x = i + (j - 0.5) * 0.28
            if c["realized"]:
                scat(ax, [x], [c["median"]], "o" if j == 0 else "s", BLUE if j == 0 else GRAY, j == 0, 44)
            else:
                ax.scatter([x], [c["median"]], s=60, marker="X", color=RED, zorder=5)
    ax.set_xticks(range(3)); ax.set_xticklabels([n for _, n in ks], fontsize=8.5); ax.set_xlim(-0.6, 2.6)
    ax.set_ylabel("Median latency P2 (ms)"); clean(ax)
    bad = [k for k, v in B["qat_time"]["conditions"].items() if not v["realized"]]
    hd = [mk("o", BLUE, "CORE_0"), mk("s", GRAY, "CORE_0_1_2", False)] + ([mk("X", RED, "P2 không thực hiện đúng")] if bad else [])
    finish(fig, h, ["Board RK3588, P2, hai phiên, mọi ô thực hiện đúng. Trục y không bắt đầu từ 0. File: results/q2e_board.json (khóa qat_time)" if not bad
                    else "Board RK3588, P2, hai phiên. Dấu X là P2 không thực hiện đúng. Trục y không bắt đầu từ 0. File: results/q2e_board.json (khóa qat_time)"],
           hd, ncol=len(hd), extra=0.3)
    return fig


# ----------------------------------------------------------------------------------------------- page 09
def fig_f_e1():
    F, T = J("q2f_fps.json"), J("thr_p3.json")
    cs = ["T1", "T3", "T4", "T5"]
    h = 4.2
    fig, ax = plt.subplots(figsize=(7.4, h))
    for d, off, mkr, col, face in (("int8", -0.14, "s", GRAY, False), ("int8h5", 0.14, "o", BLUE, True)):
        for i, c in enumerate(cs):
            cf = F["e1"]["conditions"][f"{d}|{c}"]
            ax.scatter([i + off] * len(cf["fps_runs"]), cf["fps_runs"], s=10, color=LGRAY, zorder=2)
            scat(ax, [i + off], [cf["fps"]], mkr, col, face, 44)
    hline(ax, 30, "30 FPS")
    ax.set_xticks(range(len(cs))); ax.set_xticklabels([wrap(T["configs"][c]["label"], 16) for c in cs], fontsize=8.5); ax.set_xlim(-0.5, len(cs) - 0.5)
    ax.set_ylabel("Thông lượng P3 (FPS)"); ax.set_ylim(0, 165); clean(ax)
    finish(fig, h, ["Board RK3588, ba lần chạy mỗi điểm (xám nhỏ), median (ô vuông rỗng là INT8 mặc định, chấm đặc là int8h5). Mục tiêu 30 FPS (đổi từ 60 ngày 2026-11-08).",
                    "File: results/q2f_fps.json (khóa e1)"],
           [mk("s", GRAY, "INT8 mặc định", False), mk("o", BLUE, "int8h5"), mk("o", LGRAY, "từng lần chạy", True, 3.5)], ncol=3, right=0.9, extra=0.15)
    return fig


E2_LAB = {"A": "A\nint8h5\ntuần tự", "B": "B\ntách đầu\ncùng luồng", "C": "C\ntách đầu\npipeline", "D": "D\npipeline,\n2 post",
          "E": "E\npipeline,\nCORE_0_1_2", "F": "F\nint8h5\npipeline"}


def fig_f_e2():
    F = J("q2f_fps.json")
    ks = list(E2_LAB)
    h = 4.2
    fig, ax = plt.subplots(figsize=(7.4, h))
    for i, k in enumerate(ks):
        c = F["e2"]["conditions"][k]
        ax.scatter([i] * len(c["fps_runs"]), c["fps_runs"], s=12, color=LGRAY, zorder=2)
        scat(ax, [i], [c["fps"]], "o", BLUE, True, 46)
    hline(ax, 30, "30 FPS")
    ax.set_xticks(range(len(ks))); ax.set_xticklabels([E2_LAB[k] for k in ks], fontsize=8); ax.set_xlim(-0.5, len(ks) - 0.5)
    ax.set_ylabel("Thông lượng (FPS)"); ax.set_ylim(0, 80); clean(ax)
    mx = max(F["e2"]["conditions"][k]["spread"] for k in ks)
    finish(fig, h, [f"Board RK3588, median của ba lần chạy mỗi điều kiện (xanh), khoảng trải lớn nhất {mx:.2f} FPS nên ba lần chạy gần như trùng nhau.",
                    "Đường đứt là mục tiêu 30 FPS về thông lượng. File: results/q2f_fps.json (khóa e2)"], right=0.9, extra=0.55)
    return fig


def fig_f_e2_chenh():
    F = J("q2f_fps.json")
    ks = list(F["e2"]["comparisons"])
    h = 4.0
    fig, ax = plt.subplots(figsize=(7.4, h))
    for i, k in enumerate(ks):
        c = F["e2"]["comparisons"][k]
        scat(ax, [i], [c["diff_pct"]], "o", BLUE, True, 46)
    hline(ax, 5, "+5%"); hline(ax, -5, "-5%"); ax.axhline(0, color="#999999", linewidth=0.6)
    ax.set_xticks(range(len(ks))); ax.set_xticklabels([k.replace("_vs_", "\nso với\n") for k in ks], fontsize=8.5); ax.set_xlim(-0.5, len(ks) - 0.5)
    ax.set_ylabel("Chênh FPS (%)"); clean(ax)
    finish(fig, h, ["Quy tắc 'khác': chênh ít nhất 5% và lớn hơn khoảng trải lớn hơn. Đường đứt là ±5%. File: results/q2f_fps.json (khóa e2, comparisons)"],
           right=0.93, extra=0.4)
    return fig

FIGURES = {
    "01-ket-qua-g4": [("g4-01-phu-da-nhan-va-resize", fig_g4_phu_resize), ("g4-02-thoi-gian-theo-op", fig_g4_theo_op),
                      ("g4-03-latency-theo-mask", fig_g4_latency), ("g4-04-cong-c-chenh-relu", fig_g4_cong_c),
                      ("g4-05-nhieu-seed", fig_g4_nhieu_seed), ("g4-06-relu-ba-seed", fig_g4_relu_3seed)],
    "02-ket-qua-bien-the-activation": [("bv-01-giam-latency-da-nhan", fig_bv_giam_latency), ("bv-02-chenh-ap-theo-kieu-so", fig_bv_cong_c)],
    "03-ket-qua-da-nhan": [("nhan-01-s1-latency-va-fps", fig_nhan_s1), ("nhan-02-fps-cac-cau-hinh", fig_nhan_cau_hinh),
                           ("nhan-03-muc-tieu-30-fps", fig_nhan_30fps)],
    "04-do-chinh-xac-int8-do-latency": [("x7-01-int8-so-voi-fp32", fig_x7)],
    "05-ket-qua-luong-tu-hoa": [("q-01-cosine-thap-nhat", fig_q_diag), ("q-02-ap-theo-cong-thuc", fig_q_cong_thuc),
                                ("q-03-cong-c-h5", fig_q_h5_cong_c), ("q-04-chi-phi-latency-h5", fig_q_h5_chi_phi)],
    "06-quy-trinh-tai-lap": [("r-01-ap-int8h5-theo-lan-chay", fig_r_int8h5), ("r-02-chi-phi-latency-int8h5", fig_r_chi_phi)],
    "07-ket-qua-qat-kien-truc": [("qat-01-a1-tach-dau", fig_qat_a1), ("qat-02-a2-bo-dfl", fig_qat_a2), ("qat-03-tong-hop-ung-vien", fig_qat_tong_hop)],
    "08-so-muc-chua-biet": [("u-01-g7-resize", fig_u_g7), ("u-02-thoi-gian-npu-qat", fig_u_qat_time)],
    "09-ket-qua-don-bay-fps": [("f-01-int8h5-so-voi-int8", fig_f_e1), ("f-02-e2-cac-dieu-kien", fig_f_e2), ("f-03-e2-chenh-fps", fig_f_e2_chenh)],
}


def main():
    args = sys.argv[1:]
    allnames = [n for v in FIGURES.values() for n, _ in v]
    outroot = args[0] if args and args[0] not in allnames else OUTROOT
    only = [a for a in args if a in allnames]
    for page, figs in FIGURES.items():
        outdir = os.path.join(outroot, page)
        os.makedirs(outdir, exist_ok=True)
        for name, build in figs:
            if only and name not in only:
                continue
            fig = build()
            path = os.path.join(outdir, name + ".svg")
            fig.savefig(path, format="svg", metadata={"Date": None})
            plt.close(fig)
            print(f"{name}: {path}")


if __name__ == "__main__":
    main()
