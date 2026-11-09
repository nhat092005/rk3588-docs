"""Hình cho trang 08-ket-qua-p2-va-do-mo-rong (nhóm Nền đo NPU), vẽ bằng matplotlib từ results/npu/latency/onboard_x4_*.json.

Dùng: .venv/bin/python docs/tools/figure_gen/03-phuong-phap/08-ket-qua-p2-va-do-mo-rong/gen.py [outdir] [tên_ảnh ...]
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
DEFAULT_OUTDIR = os.path.join(ROOT, "docs", "_assets", "generated", "03-phuong-phap", "02-tang-npu-nen-do",
                              "08-ket-qua-p2-va-do-mo-rong")
X4_NAME = "onboard_x4_ppe5_yolov8n_baseline_100ep_s0_int8_CORE_0.json"
BLUE, GRAY, INK = "#1E5BB8", "#555555", "#222222"
FAST_MAX, SLOW_MIN = 17.0, 20.0

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
                     "svg.fonttype": "none", "svg.hashsalt": "rk3588", "font.size": 10})


def fig_sessions():
    x4 = json.load(open(os.path.join(ROOT, "results", "npu", "latency", X4_NAME), encoding="utf-8"))
    p1, p2 = x4["protocols"]["p1lan"]["sessions"], x4["protocols"]["p2"]["sessions"]
    assert len(p1) == len(p2) == 10
    for ses, lo, hi in ((p1, 17.25, 21.87), (p2, 16.632, 16.658)):  # khoảng trung vị phiên ghi trong lời văn của trang
        meds = [s["latency_ms"] for s in ses]
        assert abs(min(meds) - lo) < 0.006 and abs(max(meds) - hi) < 0.006, (min(meds), max(meds))
    h = 5.6
    fig, axes = plt.subplots(2, 1, figsize=(7.4, h), sharex=True)
    xs = list(range(1, 11))
    for ax, key, ylabel in ((axes[0], "latency_ms", "Median latency eval_perf của phiên (ms)"),
                            (axes[1], "debug_total_ms", "Tổng thời gian debug của phiên (ms)")):
        for ses, off, mk, face, edge, label in ((p1, -0.14, "s", "none", GRAY, "P1-LAN (không ghim)"),
                                                (p2, 0.14, "o", BLUE, BLUE, "P2 (ghim CPU4)")):
            if key == "latency_ms":
                for x, s in zip(xs, ses):
                    ax.scatter([x + off] * len(s["latency_all"]), s["latency_all"], s=6, color="#BBBBBB", zorder=2)
            ax.scatter([x + off for x in xs], [s[key] for s in ses], s=40, marker=mk, facecolors=face,
                       edgecolors=edge, linewidths=1.2, zorder=4)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.grid(axis="y", color="#E6E6E6", linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    for y in (FAST_MAX, SLOW_MIN):
        axes[0].axhline(y, color=GRAY, linestyle="--", linewidth=0.8, zorder=1)
        axes[0].text(1.006, y, f"{y:.1f}", transform=axes[0].get_yaxis_transform(), fontsize=7.5, va="center", color=GRAY)
    axes[1].set_xlim(0.4, 10.6)
    axes[1].set_xticks(xs)
    axes[1].set_xlabel("Phiên (1 đến 10)")
    handles = [Line2D([], [], marker="s", linestyle="", markerfacecolor="none", markeredgecolor=GRAY, markersize=7, label="P1-LAN (không ghim)"),
               Line2D([], [], marker="o", linestyle="", color=BLUE, markersize=6, label="P2 (ghim CPU4)"),
               Line2D([], [], marker="o", linestyle="", color="#BBBBBB", markersize=3.5, label="5 lần gọi của phiên")]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.52, 0.995))
    note = ("Board RK3588, YOLOv8n INT8, CORE_0, LAN trực tiếp, mỗi phiên 5 lần eval_perf (perf_debug=False) và 5 lần từng lớp (perf_debug=True).\n"
            "Đường đứt 17.0 và 20.0 ms là ranh giới mức nhanh và chậm. Cổng A5 so median latency giữa các phiên, A8 so tổng debug và tỉ lệ từng khối (không vẽ ở đây).\n"
            f"File: results/npu/latency/{X4_NAME} (khóa protocols)")
    fig.text(0.01, 0.004, note, fontsize=7.2, style="italic", color="#444444", va="bottom", ha="left")
    fig.subplots_adjust(left=0.11, right=0.955, top=0.9, bottom=0.2, hspace=0.12)
    return fig


def main():
    figures = [("p2-01-phien-p1lan-va-p2", fig_sessions)]
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
