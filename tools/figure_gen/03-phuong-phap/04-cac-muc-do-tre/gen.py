"""Hình cho trang 04-cac-muc-do-tre (nhóm Nền đo NPU), vẽ bằng matplotlib từ experiments/npu/latency/onboard/hot_*.csv.

Dùng: .venv/bin/python docs/tools/figure_gen/03-phuong-phap/04-cac-muc-do-tre/gen.py [outdir] [tên_ảnh ...]
Phân mức cùng ngưỡng với bảng của trang (dưới 17.0 ms nhanh, từ 20.0 ms chậm), và kiểm lại tỉ lệ khớp results/npu/latency/onboard_*.json.
"""
import csv
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
DEFAULT_OUTDIR = os.path.join(ROOT, "docs", "_assets", "generated", "03-phuong-phap", "02-tang-npu-nen-do",
                              "04-cac-muc-do-tre")
RUN = "ppe5_yolov8n_baseline_100ep_s0"
HOT_DIR = os.path.join("experiments", "npu", "latency", "onboard")
ONB_NAME = f"onboard_{RUN}_int8_CORE_0.json"
FAST_MAX, SLOW_MIN = 17.0, 20.0
FAST, MID, SLOW, GRAY, INK, BLUE = "#2E7D32", "#8A8A8A", "#C62828", "#555555", "#222222", "#1E5BB8"

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
                     "svg.fonttype": "none", "svg.hashsalt": "rk3588", "font.size": 10})


def load():
    onb = json.load(open(os.path.join(ROOT, "results", "npu", "latency", ONB_NAME), encoding="utf-8"))
    hot = {}
    for n in (1, 2, 3):
        rows = list(csv.DictReader(open(os.path.join(ROOT, HOT_DIR, f"hot_{n}.csv"), encoding="utf-8")))
        assert len(rows) == 1000, f"hot_{n}.csv có {len(rows)} dòng"
        hot[n] = [int(r["wall_us"]) / 1000 for r in rows]
        lv = onb["hot_levels"][str(n)]
        fast = sum(x < FAST_MAX for x in hot[n]) / 1000
        slow = sum(x >= SLOW_MIN for x in hot[n]) / 1000
        assert abs(fast - lv["fast"]) < 0.0015 and abs(slow - lv["slow"]) < 0.0015, (n, fast, slow, lv)
    return onb, hot


def fig_batches():
    onb, hot = load()
    lo = min(min(v) for v in hot.values())
    hi = max(max(v) for v in hot.values())
    h = 6.4
    fig, axes = plt.subplots(3, 1, figsize=(7.4, h), sharex=True, sharey=True)
    xs = list(range(1, 1001))
    for ax, n in zip(axes, (1, 2, 3)):
        v = hot[n]
        cols = [FAST if x < FAST_MAX else SLOW if x >= SLOW_MIN else MID for x in v]
        ax.scatter(xs, v, s=4, c=cols, linewidths=0, zorder=3)
        for y in (FAST_MAX, SLOW_MIN):
            ax.axhline(y, color=GRAY, linestyle="--", linewidth=0.8, zorder=2)
            ax.text(1.006, y, f"{y:.1f}", transform=ax.get_yaxis_transform(), fontsize=7.5, va="center", color=GRAY)
        ax.text(0.008, 0.97, f"Đợt {n}", transform=ax.transAxes, fontsize=9.5, weight="bold", va="top")
        ax.grid(axis="y", color="#E6E6E6", linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylim(lo - 0.4, hi + 1.6)
    axes[0].set_xlim(0, 1001)
    axes[-1].set_xlabel("Lần chạy liên tiếp (1 đến 1000)")
    fig.supylabel("Thời gian một lần rknn_run, đồng hồ CPU (ms)", fontsize=9.5)
    handles = [Line2D([], [], marker="o", linestyle="", markersize=5, color=c, label=t)
               for c, t in ((FAST, f"mức nhanh (dưới {FAST_MAX:.1f} ms)"), (MID, "mức giữa"),
                            (SLOW, f"mức chậm (từ {SLOW_MIN:.1f} ms)"))]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(0.52, 0.995))
    note = (f"Board RK3588, YOLOv8n INT8, CORE_0, ai/board/bench/rknn_perf_bench.c (C API), 50 lần khởi động rồi 1000 lần chạy mỗi đợt.\n"
            f"Thời gian là đồng hồ CPU quanh rknn_run, gồm cả phần driver. Đường đứt 17.0 và 20.0 ms đọc từ biểu đồ gộp 3000 lần chạy.\n"
            f"File: {HOT_DIR}/hot_1.csv, hot_2.csv, hot_3.csv")
    fig.text(0.01, 0.004, note, fontsize=7.2, style="italic", color="#444444", va="bottom", ha="left")
    fig.subplots_adjust(left=0.1, right=0.955, top=0.93, bottom=0.17, hspace=0.12)
    return fig


def _res(name):
    return json.load(open(os.path.join(ROOT, "results", "npu", "latency", name), encoding="utf-8"))


LAYER_NAME = f"layer_analysis_{RUN}_int8_CORE_0.json"
MODEL_NOTE = "YOLOv8n INT8, CORE_0"


def _foot(fig, lines):
    fig.text(0.01, 0.004, "\n".join(lines), fontsize=7.2, style="italic", color="#444444", va="bottom", ha="left")


def _clean(ax):
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


def _level_lines(ax, ys=(FAST_MAX, SLOW_MIN)):
    for y in ys:
        ax.axhline(y, color=GRAY, linestyle="--", linewidth=0.8, zorder=2)
        ax.text(1.006, y, f"{y:.1f}", transform=ax.get_yaxis_transform(), fontsize=7.5, va="center", color=GRAY)


def fig_gap():
    onb = _res(ONB_NAME)
    h = 4.8
    fig, axes = plt.subplots(2, 1, figsize=(7.4, h), sharey=True)
    allv = []
    for ax, (key, title) in zip(axes, [("gap2s", "Nghỉ 2 giây giữa các lần chạy"), ("gap10s", "Nghỉ 10 giây giữa các lần chạy")]):
        g = onb["gap"][key]
        v = [x / 1000 for x in g["values"]]
        assert len(v) == g["n"]
        allv += v
        xs = list(range(1, len(v) + 1))
        cols = [FAST if x < FAST_MAX else SLOW if x >= SLOW_MIN else MID for x in v]
        ax.scatter(xs, v, s=22, c=cols, linewidths=0, zorder=3)
        ax.scatter([1], [v[0]], s=80, facecolors="none", edgecolors=INK, linewidths=1.0, zorder=4)
        _level_lines(ax)
        _clean(ax)
        ax.set_xlim(0, len(v) + 1)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=10))
        ax.text(0.008, 0.95, title, transform=ax.transAxes, fontsize=9.5, weight="bold", va="top")
    axes[0].set_ylim(min(allv) - 0.6, SLOW_MIN + 1.8)
    axes[-1].set_xlabel("Lần chạy (trong cùng một tiến trình)")
    fig.supylabel("Thời gian một lần rknn_run (ms)", fontsize=9.5)
    handles = [Line2D([], [], marker="o", linestyle="", markersize=5, color=c, label=t)
               for c, t in ((FAST, f"mức nhanh (dưới {FAST_MAX:.1f} ms)"), (MID, "mức giữa"), (SLOW, f"mức chậm (từ {SLOW_MIN:.1f} ms)"))]
    handles.append(Line2D([], [], marker="o", linestyle="", markerfacecolor="none", markeredgecolor=INK, markersize=8, label="lần chạy đầu"))
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False, fontsize=8.5, bbox_to_anchor=(0.52, 0.995))
    _foot(fig, [f"Board RK3588, {MODEL_NOTE}, C API, 40 lần chạy cách 2 giây và 20 lần chạy cách 10 giây. Thời gian là đồng hồ CPU quanh rknn_run.",
                f"File: results/npu/latency/{ONB_NAME} (khóa gap)"])
    fig.subplots_adjust(left=0.1, right=0.955, top=0.9, bottom=0.2, hspace=0.18)
    return fig


def fig_cpuidle():
    onb = _res(ONB_NAME)
    h = 3.4
    fig, ax = plt.subplots(figsize=(7.4, h))
    for n in (1, 2, 3):
        x = onb["cpuidle"][f"hot_{n}"]["state1"]["entries"]
        y = onb["hot"][str(n)]["median"] / 1000
        ax.scatter([x], [y], s=46, color=BLUE, zorder=3)
        ax.annotate(f"Đợt {n}", (x, y), textcoords="offset points", xytext=(8, 5), fontsize=9, color=INK)
    ax.set_xlabel("Số lần vào cpu-sleep (state1), cộng trên mọi CPU")
    ax.set_ylabel("Trung vị thời gian (ms)")
    ax.grid(color="#E6E6E6", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.set_xlim(40000, 90000)
    ax.set_ylim(18.5, 21.5)
    _foot(fig, [f"Board RK3588, {MODEL_NOTE}, ba đợt 1000 lần chạy liên tiếp, bộ đếm cpuidle đọc trước và sau mỗi đợt.",
                f"File: results/npu/latency/{ONB_NAME} (khóa cpuidle, hot)"])
    fig.subplots_adjust(left=0.1, right=0.97, top=0.95, bottom=0.27)
    return fig


def fig_fit():
    onb = _res(ONB_NAME)
    fits = onb["detail_conv_fit"]
    h = 3.6
    fig, axes = plt.subplots(1, 2, figsize=(7.4, h))
    xs = [1, 2, 3]
    for ax, key, ylabel, ylim in ((axes[0], "slope", "Hệ số theo cycles ước tính a", (0, 2.2)),
                                  (axes[1], "intercept", "Hằng số b (µs)", (0, 70))):
        ys = [fits[str(n)][key] for n in xs]
        ax.scatter(xs, ys, s=46, color=BLUE, zorder=3)
        for x, y in zip(xs, ys):
            ax.annotate(f"{y:.3f}" if key == "slope" else f"{y:.1f}", (x, y), textcoords="offset points", xytext=(0, 8),
                        ha="center", fontsize=8.5, color=INK)
        ax.set_xticks(xs)
        ax.set_xticklabels([f"Đợt {n}" for n in xs])
        ax.set_xlim(0.5, 3.5)
        ax.set_ylim(*ylim)
        ax.set_ylabel(ylabel)
        _clean(ax)
    _foot(fig, [f"Board RK3588, {MODEL_NOTE}, ba đợt detail, phép khớp time = a x est. + b trên các dòng Conv.",
                f"File: results/npu/latency/{ONB_NAME} (khóa detail_conv_fit)"])
    fig.subplots_adjust(left=0.1, right=0.97, top=0.92, bottom=0.27, wspace=0.28)
    return fig


def fig_e1():
    onb = _res(ONB_NAME)
    sess = onb["e1"]["sessions"]
    h = 4.8
    fig, axes = plt.subplots(2, 1, figsize=(7.4, h), sharey=True)
    allv = [x for s_ in sess for x in s_["values"]]
    for ax, s_ in zip(axes, sess):
        v = s_["values"]
        xs = list(range(1, len(v) + 1))
        ax.scatter(xs, v, s=26, color=BLUE, zorder=3)
        ax.scatter([1], [v[0]], s=90, facecolors="none", edgecolors=INK, linewidths=1.0, zorder=4)
        ax.axhline(19.0, color=GRAY, linestyle="--", linewidth=0.8, zorder=2)
        ax.text(1.006, 19.0, "19.0", transform=ax.get_yaxis_transform(), fontsize=7.5, va="center", color=GRAY)
        _clean(ax)
        ax.set_xlim(0, len(v) + 1)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=10))
        ax.text(0.008, 0.95, f"Phiên {s_['session']}", transform=ax.transAxes, fontsize=9.5, weight="bold", va="top")
    axes[0].set_ylim(min(allv) - 0.4, max(allv) + 0.8)
    axes[-1].set_xlabel("Lần gọi eval_perf trong phiên (1 đến 20)")
    fig.supylabel("Latency eval_perf (ms)", fontsize=9.5)
    handles = [Line2D([], [], marker="o", linestyle="", markersize=5, color=BLUE, label="lần gọi"),
               Line2D([], [], marker="o", linestyle="", markerfacecolor="none", markeredgecolor=INK, markersize=8, label="lần gọi đầu")]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, fontsize=8.5, bbox_to_anchor=(0.52, 0.995))
    _foot(fig, [f"Board RK3588, {MODEL_NOTE}, hai phiên eval_perf (perf_debug=False), 20 lần gọi mỗi phiên, tần số in ra không đổi.",
                f"Đường đứt 19.0 ms là mốc dùng trong lời văn của trang. File: results/npu/latency/{ONB_NAME} (khóa e1)"])
    fig.subplots_adjust(left=0.1, right=0.955, top=0.9, bottom=0.2, hspace=0.18)
    return fig


def fig_first_call():
    first = _res(LAYER_NAME)["first_vs_rest"]
    h = 3.8
    fig, axes = plt.subplots(1, 2, figsize=(7.4, h))
    xs = [1, 2, 3]
    spec = ((axes[0], "latency_first", "latency_rest_median", "Latency (ms)", 1.0),
            (axes[1], "debug_first", "debug_rest_median", "Tổng thời gian debug (ms)", 1000.0))
    for ax, k1, k2, ylabel, div in spec:
        first_v = [first[i][k1] / div for i in range(3)]
        rest_v = [first[i][k2] / div for i in range(3)]
        ax.scatter(xs, rest_v, s=46, color=BLUE, zorder=3)
        ax.scatter(xs, first_v, s=84, facecolors="none", edgecolors=INK, linewidths=1.1, zorder=4)
        for x, a, b in zip(xs, first_v, rest_v):
            ax.plot([x, x], [a, b], color="#BBBBBB", linewidth=0.9, zorder=1)
        ax.set_xticks(xs)
        ax.set_xticklabels([f"B3 phiên {n}" for n in xs], fontsize=8.5)
        ax.set_xlim(0.5, 3.5)
        ax.set_ylabel(ylabel)
        _clean(ax)
    lo, hi = min(first[i]["latency_first"] for i in range(3)), max(first[i]["latency_rest_median"] for i in range(3))
    axes[0].set_ylim(lo - 0.8, hi + 0.8)
    dl = [first[i][k] / 1000 for i in range(3) for k in ("debug_first", "debug_rest_median")]
    axes[1].set_ylim(min(dl) - 0.8, max(dl) + 0.8)
    handles = [Line2D([], [], marker="o", linestyle="", markerfacecolor="none", markeredgecolor=INK, markersize=8, label="lần gọi đầu"),
               Line2D([], [], marker="o", linestyle="", color=BLUE, markersize=5.5, label="trung vị các lần sau")]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, fontsize=8.5, bbox_to_anchor=(0.52, 0.995))
    _foot(fig, [f"Board RK3588, {MODEL_NOTE}, ba phiên B3 (eval_perf), 5 lần gọi mỗi phiên. Trục y của hai panel không bắt đầu từ 0.",
                f"File: results/npu/latency/{LAYER_NAME} (khóa first_vs_rest)"])
    fig.subplots_adjust(left=0.1, right=0.97, top=0.88, bottom=0.25, wspace=0.28)
    return fig


def main():
    figures = [("lvl-01-ba-dot-lien-tiep", fig_batches),
               ("lvl-02-nghi-giua-lan-chay", fig_gap),
               ("lvl-03-cpuidle-ba-dot", fig_cpuidle),
               ("lvl-04-he-so-ba-dot-detail", fig_fit),
               ("lvl-05-e1-theo-lan-goi", fig_e1),
               ("lvl-06-lan-goi-dau-b3", fig_first_call)]
    args = sys.argv[1:]
    names = [n for n, _ in figures]
    outdir = args[0] if args and args[0] not in names else DEFAULT_OUTDIR
    only = [x for x in args if x in names]
    os.makedirs(outdir, exist_ok=True)
    for name, build in figures:
        if only and name not in only:
            continue
        fig = build()
        path = os.path.join(outdir, name + ".svg")
        fig.savefig(path, format="svg", metadata={"Date": None})
        plt.close(fig)
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
