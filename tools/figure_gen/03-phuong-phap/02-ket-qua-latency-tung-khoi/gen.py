"""Hình cho trang 02-ket-qua-latency-tung-khoi (nhóm Nền đo NPU), vẽ bằng matplotlib từ results/npu/*/*.json.

Dùng: .venv/bin/python docs/tools/figure_gen/03-phuong-phap/02-ket-qua-latency-tung-khoi/gen.py [outdir] [tên_ảnh ...]
Số trong hình lấy nguyên từ JSON, cùng file với Bảng 1 của trang.
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
DEFAULT_OUTDIR = os.path.join(ROOT, "docs", "_assets", "generated", "03-phuong-phap", "02-tang-npu-nen-do",
                              "02-ket-qua-latency-tung-khoi")
JSON_NAME = "latency_per_block_ppe5_yolov8n_baseline_100ep_s0_int8_CORE_0.json"
BLUE, GRAY, INK = "#1E5BB8", "#555555", "#222222"

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
                     "svg.fonttype": "none", "svg.hashsalt": "rk3588", "font.size": 10})


def load():
    a = json.load(open(os.path.join(ROOT, "results", "npu", "latency", JSON_NAME), encoding="utf-8"))
    blocks = a["blocks"]
    order = sorted([b for b in blocks if b.startswith("L")], key=lambda b: int(b[1:])) + ["io", "post_detect"]
    assert sorted(order) == sorted(blocks), "khối trong JSON khác danh sách vẽ"
    return a, blocks, order


def fig_block_time():
    a, blocks, order = load()
    sha = a["model_sha256"][:8]
    b3 = [blocks[b]["us"] for b in order]
    b2 = [blocks[b]["b2_us"] for b in order]
    widest = max(order, key=lambda b: blocks[b]["spread"])
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    xs = list(range(len(order)))
    ax.scatter(xs, b3, s=34, color=BLUE, marker="o", zorder=3, label="B3: trung vị 3 phiên")
    ax.scatter(xs, b2, s=40, facecolors="none", edgecolors=GRAY, marker="s", linewidths=1.2, zorder=2,
               label="B2: một phiên")
    ax.set_xticks(xs)
    ax.set_xticklabels([b if b != "post_detect" else "post" for b in order], fontsize=8.5)
    ax.set_xlabel("Khối của mạng (L0 đến L22, thêm io và post_detect)")
    ax.set_ylabel("Thời gian khối, chế độ debug (µs)")
    ax.grid(axis="y", color="#DDDDDD", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for i in sorted(xs, key=lambda i: -b3[i])[:3]:
        ax.annotate(f"{order[i]}: {b3[i]:.0f}", (i, b3[i]), textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=9, color=INK)
    ax.set_ylim(0, max(b3 + b2) * 1.12)
    ax.legend(loc="upper center", frameon=False, ncol=2, fontsize=9, bbox_to_anchor=(0.5, 1.12))
    note = (f"YOLOv8n INT8 (sha256 {sha}), CORE_0, eval_perf ở chế độ perf_debug, 3 phiên x 5 lần gọi. "
            f"Lệch thời gian (max trừ min, chia trung vị) giữa 3 phiên tối đa {blocks[widest]['spread']:.1%} ({widest}).\n"
            f"Thời gian từng khối dùng để so sánh với nhau, không cộng thành latency. File: results/npu/latency/{JSON_NAME}")
    fig.text(0.01, 0.005, note, fontsize=7.2, style="italic", color="#444444", va="bottom", ha="left")
    fig.subplots_adjust(left=0.1, right=0.98, top=0.9, bottom=0.25)
    return fig


def _dot_axes(ax, xlabel, ylabel):
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", color="#DDDDDD", linewidth=0.7, zorder=0)
    ax.grid(axis="y", color="#F0F0F0", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


def _footer(fig, note, height_in, lines):
    fig.text(0.01, 0.004, note, fontsize=7.2, style="italic", color="#444444", va="bottom", ha="left")
    return (0.2 + 0.125 * lines) / height_in


def fig_parts():
    a, _, _ = load()
    sha = a["model_sha256"][:8]
    parts = a["parts"]
    top = sorted(parts.items(), key=lambda kv: -kv[1]["share"])[:22]
    names = [k for k, _ in top]
    us = [v["us"] for _, v in top]
    widest = max(top, key=lambda kv: kv[1]["spread"])
    h = 6.6
    fig, ax = plt.subplots(figsize=(7.4, h))
    ys = list(range(len(top)))
    ax.scatter(us, ys, s=34, color=BLUE, marker="o", zorder=3)
    ax.set_yticks(ys)
    ax.set_yticklabels(names, fontsize=8.5)
    ax.invert_yaxis()
    _dot_axes(ax, "Thời gian thành phần, chế độ debug (µs)", "Khối/thành phần, xếp theo tỉ lệ toàn mạng")
    for i in sorted(ys, key=lambda i: -us[i])[:3]:
        ax.annotate(f"{us[i]:.0f}", (us[i], i), textcoords="offset points", xytext=(7, 0), va="center",
                    fontsize=9, color=INK)
    ax.set_xlim(0, max(us) * 1.12)
    note = (f"YOLOv8n INT8 (sha256 {sha}), CORE_0, eval_perf ở chế độ perf_debug, 3 phiên x 5 lần gọi. "
            f"Hiện {len(top)} trên {len(parts)} thành phần, đúng Bảng 2.\n"
            f"Lệch thời gian (max trừ min, chia trung vị) giữa 3 phiên tối đa {widest[1]['spread']:.1%} ({widest[0]}). "
            f"Thời gian dùng để so sánh với nhau, không cộng thành latency.\n"
            f"File: results/npu/latency/{JSON_NAME}")
    bottom = _footer(fig, note, h, 3)
    fig.subplots_adjust(left=0.2, right=0.97, top=0.98, bottom=bottom + 0.06)
    return fig


def fig_ops():
    a, _, _ = load()
    sha = a["model_sha256"][:8]
    ops = sorted(a["ops"].items(), key=lambda kv: -kv[1]["us"])
    us = [v["us"] for _, v in ops]
    labels = [f"{k} ({v['calls']} dòng)" for k, v in ops]
    widest = max(ops, key=lambda kv: kv[1]["spread"])
    h = 4.9
    fig, ax = plt.subplots(figsize=(7.4, h))
    ys = list(range(len(ops)))
    ax.scatter(us, ys, s=34, color=BLUE, marker="o", zorder=3)
    ax.set_xscale("log")
    ax.set_yticks(ys)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.invert_yaxis()
    _dot_axes(ax, "Tổng thời gian các dòng cùng OpType trong một lần gọi, chế độ debug (µs, thang log)",
              "OpType (số dòng RKNN)")
    for i in ys[:3]:
        ax.annotate(f"{us[i]:.0f}", (us[i], i), textcoords="offset points", xytext=(7, 0), va="center",
                    fontsize=9, color=INK)
    ax.set_xlim(5, max(us) * 3)
    note = (f"YOLOv8n INT8 (sha256 {sha}), CORE_0, eval_perf ở chế độ perf_debug, 3 phiên x 5 lần gọi, trung vị.\n"
            f"Lệch thời gian giữa 3 phiên (max trừ min, chia trung vị) tối đa {widest[1]['spread']:.1%} ({widest[0]}). "
            f"Thời gian dùng để so sánh với nhau, không cộng thành latency.\n"
            f"File: results/npu/latency/{JSON_NAME}")
    bottom = _footer(fig, note, h, 3)
    fig.subplots_adjust(left=0.25, right=0.97, top=0.98, bottom=bottom + 0.11)
    return fig


def main():
    figures = [("lat-01-thoi-gian-tung-khoi", fig_block_time),
               ("lat-02-thanh-phan-trong-khoi", fig_parts),
               ("lat-03-theo-optype", fig_ops)]
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
