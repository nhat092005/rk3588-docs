"""Hình cho trang 05-thu-ghim-cpu-va-ngat (nhóm Nền đo NPU), vẽ bằng matplotlib từ results/onboard_*.json (khóa e2d).

Dùng: .venv/bin/python docs/tools/figure_gen/03-phuong-phap/05-thu-ghim-cpu-va-ngat/gen.py [outdir] [tên_ảnh ...]
"""
import json
import os
import re
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", ".."))
DEFAULT_OUTDIR = os.path.join(ROOT, "docs", "_assets", "generated", "03-phuong-phap", "02-tang-npu-nen-do",
                              "05-thu-ghim-cpu-va-ngat")
ONB_NAME = "onboard_ppe5_yolov8n_baseline_100ep_s0_int8_CORE_0.json"
BLUE, GRAY, INK = "#1E5BB8", "#555555", "#222222"
A_X = -1.4  # vị trí ô A (không ghim) trên trục x

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
                     "svg.fonttype": "none", "svg.hashsalt": "rk3588", "font.size": 10})


def cell_geometry(cond):
    """(x, marker, offset): vị trí theo CPU ứng dụng, kiểu điểm theo CPU ngắt, đọc từ tên ô aXiY."""
    if cond == "A":
        return A_X, "^", 0.0
    m = re.fullmatch(r"a(\d)i(\d)", cond)
    app, irq = int(m.group(1)), int(m.group(2))
    if irq == 0:
        return app - 0.22, "o", 0.0
    if irq == 4:
        return float(app), "s", 0.0
    assert irq == app, cond
    return app + 0.22, "D", 0.0


def fig_map():
    onb = json.load(open(os.path.join(ROOT, "results", ONB_NAME), encoding="utf-8"))
    e = onb["e2d"]
    blocks = e["blocks"]
    assert len(blocks) == 40 and all(b["realized"] for b in blocks.values()) and e["valid"]
    cells = {}
    for b in blocks.values():
        cells.setdefault(b["cond"], {})[b["half"]] = b
    assert len(cells) == 20 and all(sorted(v) == [1, 2] for v in cells.values())
    h = 6.1
    fig, axes = plt.subplots(2, 1, figsize=(7.4, h), sharex=True)
    panels = [("slow", "Tỉ lệ mức chậm (%)", [(5, "5%"), (20, "20%")]),
              ("fast", "Tỉ lệ mức nhanh (%)", [(95, "95%")])]
    for ax, (key, ylabel, lines) in zip(axes, panels):
        for cond, halves in cells.items():
            x, mk, _ = cell_geometry(cond)
            ax.scatter([x], [halves[1][key] * 100], s=22, marker=mk, color=BLUE, zorder=4)
            ax.scatter([x], [halves[2][key] * 100], s=78, marker=mk, facecolors="none", edgecolors=BLUE,
                       linewidths=1.1, zorder=3)
        for y, t in lines:
            ax.axhline(y, color=GRAY, linestyle="--", linewidth=0.8, zorder=2)
            ax.text(1.006, y, t, transform=ax.get_yaxis_transform(), fontsize=7.5, va="center", color=GRAY)
        ax.set_ylabel(ylabel)
        ax.set_ylim(-6, 106)
        ax.grid(axis="y", color="#E6E6E6", linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
        ax.axvline(-0.75, color="#CCCCCC", linewidth=0.8, zorder=1)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[1].set_xticks([A_X] + list(range(8)))
    axes[1].set_xticklabels(["A"] + [str(i) for i in range(8)])
    axes[1].set_xlim(-2.0, 7.6)
    axes[1].set_xlabel("CPU ghim ứng dụng (X trong aXiY), A là không ghim")
    handles = [Line2D([], [], marker="o", linestyle="", color=GRAY, markersize=6, label="ngắt CPU0"),
               Line2D([], [], marker="s", linestyle="", color=GRAY, markersize=6, label="ngắt CPU4"),
               Line2D([], [], marker="D", linestyle="", color=GRAY, markersize=6, label="ngắt cùng CPU ứng dụng"),
               Line2D([], [], marker="^", linestyle="", color=GRAY, markersize=6, label="A: ngắt mặc định"),
               Line2D([], [], marker="o", linestyle="", color="black", markersize=4.5, label="nửa 1 (đặc)"),
               Line2D([], [], marker="o", linestyle="", markerfacecolor="none", markeredgecolor="black", markersize=8,
                      label="nửa 2 (vòng)")]
    fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(0.52, 0.995))
    note = ("Board RK3588, YOLOv8n INT8, CORE_0, 20 điều kiện x 2 nửa, mỗi khối 1000 lần chạy sau 50 lần khởi động, irqbalance dừng.\n"
            "Nửa 1 theo thứ tự cố định, nửa 2 theo thứ tự ngược. Ngưỡng 20% theo E2, 5% và 95% chọn sau khi đã thấy dữ liệu E2c.\n"
            f"File: results/{ONB_NAME} (khóa e2d)")
    fig.text(0.01, 0.004, note, fontsize=7.2, style="italic", color="#444444", va="bottom", ha="left")
    fig.subplots_adjust(left=0.1, right=0.955, top=0.9, bottom=0.17, hspace=0.12)
    return fig


def _load():
    return json.load(open(os.path.join(ROOT, "results", ONB_NAME), encoding="utf-8"))


def _half(b):
    return b["half"] if "half" in b else (1 if b["order"] == "ABCD" else 2)


def cells_figure(key, order, labels, slow_lines, fast_lines, note_lines, bad_blocks=(), height=5.6):
    """Hai panel (tỉ lệ mức chậm, mức nhanh) theo điều kiện. Điểm đặc là nửa 1, vòng rỗng là nửa 2, X là khối không thực hiện đúng."""
    blocks = list(_load()[key]["blocks"].values())
    assert sorted({b["cond"] for b in blocks}) == sorted(order), (key, sorted({b["cond"] for b in blocks}))
    fig, axes = plt.subplots(2, 1, figsize=(7.4, height), sharex=True)
    groups = {}
    for b in blocks:
        groups.setdefault((b["cond"], _half(b)), []).append(b)
    for ax, (field, ylabel, lines) in zip(axes, [("slow", "Tỉ lệ mức chậm (%)", slow_lines),
                                                 ("fast", "Tỉ lệ mức nhanh (%)", fast_lines)]):
        for (cond, half), bl in groups.items():
            x0 = order.index(cond)
            offs = [0.0] if len(bl) == 1 else [-0.12, 0.12]
            for off, b in zip(offs, sorted(bl, key=lambda r: r["block"])):
                y = b[field] * 100
                if b["block"] in bad_blocks:
                    ax.scatter([x0 + off], [y], s=60, marker="X", color="#C62828", zorder=5)
                elif half == 1:
                    ax.scatter([x0 + off], [y], s=24, marker="o", color=BLUE, zorder=4)
                else:
                    ax.scatter([x0 + off], [y], s=64, marker="o", facecolors="none", edgecolors=BLUE,
                               linewidths=1.1, zorder=3)
        for y, t in lines:
            ax.axhline(y, color=GRAY, linestyle="--", linewidth=0.8, zorder=2)
            ax.text(1.006, y, t, transform=ax.get_yaxis_transform(), fontsize=7.5, va="center", color=GRAY)
        ax.set_ylabel(ylabel)
        ax.set_ylim(-6, 106)
        ax.grid(axis="y", color="#E6E6E6", linewidth=0.6, zorder=0)
        ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[1].set_xticks(range(len(order)))
    axes[1].set_xticklabels(labels, fontsize=8.5)
    axes[1].set_xlim(-0.6, len(order) - 0.4)
    handles = [Line2D([], [], marker="o", linestyle="", color="black", markersize=4.5, label="nửa 1 (đặc)"),
               Line2D([], [], marker="o", linestyle="", markerfacecolor="none", markeredgecolor="black",
                      markersize=8, label="nửa 2 (vòng)")]
    if bad_blocks:
        handles.append(Line2D([], [], marker="X", linestyle="", color="#C62828", markersize=7,
                              label="khối không thực hiện đúng điều kiện"))
    fig.legend(handles=handles, loc="upper center", ncol=len(handles), frameon=False, fontsize=8.5,
               bbox_to_anchor=(0.52, 0.995))
    fig.text(0.01, 0.004, "\n".join(note_lines + [f"File: results/{ONB_NAME} (khóa {key})"]), fontsize=7.2,
             style="italic", color="#444444", va="bottom", ha="left")
    n_note = len(note_lines) + 1
    tick_lines = max(t.count("\n") + 1 for t in labels)
    fig.subplots_adjust(left=0.1, right=0.955, top=0.9, bottom=(0.3 + 0.16 * tick_lines + 0.125 * n_note) / height, hspace=0.12)
    return fig


def fig_e2():
    e = _load()["e2"]
    bad = sorted({b for v in e["verdict"].values() for b in v["excluded_blocks"]})
    return cells_figure("e2", ["A", "B", "C", "D"],
                        ["A\nmặc định", "B\nứng dụng và ngắt\ncùng CPU4", "C\nứng dụng và ngắt\ncùng CPU0", "D\ntắt cpu-sleep"],
                        [], [],
                        ["Board RK3588, YOLOv8n INT8, CORE_0, 8 khối x 1000 lần chạy, thứ tự ABCD (nửa 1) rồi DCBA (nửa 2), irqbalance đang chạy.",
                         "Nhãn của E2 tính theo độ dịch tỉ lệ mức chậm so với khối A cùng nửa, không theo ngưỡng cố định."],
                        bad_blocks=bad, height=5.9)


def fig_e2b():
    return cells_figure("e2b", ["A", "B"], ["A mặc định", "B ứng dụng và ngắt cùng CPU4"], [], [],
                        ["Board RK3588, YOLOv8n INT8, CORE_0, irqbalance dừng, 8 khối x 1000 lần chạy sau 50 lần làm nóng, thứ tự ABBA rồi ABBA.",
                         "Nửa 1 là bốn khối đầu, nửa 2 là bốn khối sau. Mỗi nửa có hai khối B kề nhau."], height=5.0)


def fig_e2c():
    return cells_figure("e2c", ["A", "B", "C", "E", "F", "G"],
                        ["A\nmặc định", "B\n(4, 4)", "C\n(0, 0)", "E\n(4, 0)", "F\n(0, 4)", "G\n(1, 0)"],
                        [(1, "1%"), (20, "20%")], [],
                        ["Board RK3588, YOLOv8n INT8, CORE_0, irqbalance dừng, 12 khối x 1000 lần chạy, thứ tự A B C E F G rồi G F E C B A.",
                         "Ô viết (CPU ứng dụng, CPU nhận ngắt). Ngưỡng 20% theo E2, ngưỡng 1% của 'mất mức chậm' là số mới chọn cho quy tắc E2c."],
                        height=5.4)


def _cells_e2e(key, order, extra_note, height):
    labels = [("A\nkhông ghim" if c == "A" else f"({c[1]}, {c[3]})") for c in order]
    return cells_figure(key, order, labels, [(5, "5%"), (20, "20%")], [(95, "95%")],
                        ["Board RK3588, YOLOv8n INT8, CORE_0, eval_perf qua rknn_server, irqbalance dừng, 14 khối x 500 lần gọi, cách nhau khoảng 0.22 s.",
                         "Ô viết (CPU của rknn_server, CPU nhận ngắt). Ngưỡng 5%, 20% và 95% giữ từ E2d. " + extra_note], height=height)


def fig_e2e():
    return _cells_e2e("e2e", ["A", "s4i4", "s0i0", "s4i0", "s0i4", "s1i0", "s1i4"],
                      "Thứ tự nửa 1 là A đến s1i4, nửa 2 là ngược lại.", 5.6)


def fig_x6():
    return _cells_e2e("x6", ["s4i4", "s5i4", "s6i4", "s7i4", "s5i5", "s6i6", "s7i7"],
                      "X6 chạy cùng cách đo với E2e.", 5.4)


def fig_e2e_vs_e2d():
    onb = _load()
    comp = onb["e2e"]["comparison"]
    order = list(comp)
    blocks = list(onb["e2e"]["blocks"].values())
    for c in order:  # trung vị mỗi ô là trung bình trung vị hai khối, như quy tắc E2e
        mine = [b["median"] for b in blocks if b["cond"] == c]
        assert len(mine) == 2 and abs(sum(mine) / 2 - comp[c]["median_e2e"]) < 1e-6, c
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    xs = list(range(len(order)))
    ax.scatter(xs, [comp[c]["median_e2d"] for c in order], s=52, marker="s", facecolors="none", edgecolors=GRAY,
               linewidths=1.2, zorder=3, label="C API (E2d)")
    ax.scatter(xs, [comp[c]["median_e2e"] for c in order], s=34, marker="o", color=BLUE, zorder=4,
               label="eval_perf qua rknn_server (E2e)")
    for y in (17.0, 20.0):
        ax.axhline(y, color="#BBBBBB", linestyle="--", linewidth=0.8, zorder=1)
        ax.text(1.006, y, f"{y:.1f}", transform=ax.get_yaxis_transform(), fontsize=7.5, va="center", color=GRAY)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"({c[1]}, {c[3]})" for c in order], fontsize=8.5)
    ax.set_xlim(-0.6, len(order) - 0.4)
    ax.set_xlabel("Ô (CPU của ứng dụng hoặc rknn_server, CPU nhận ngắt)")
    ax.set_ylabel("Trung vị thời gian (ms)")
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.legend(loc="upper center", ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 1.13))
    note = ("Board RK3588, YOLOv8n INT8, CORE_0, sáu ô chung của E2e và E2d. Trung vị mỗi ô là trung bình trung vị của hai khối.\n"
            "Thời gian eval_perf và thời gian C API là hai đại lượng khác nhau, ngưỡng 17.0 và 20.0 ms lấy từ đường C API.\n"
            f"File: results/{ONB_NAME} (khóa e2e, comparison)")
    fig.text(0.01, 0.004, note, fontsize=7.2, style="italic", color="#444444", va="bottom", ha="left")
    fig.subplots_adjust(left=0.1, right=0.955, top=0.88, bottom=0.27)
    return fig


def main():
    figures = [("pin-01-ban-do-e2d", fig_map),
               ("pin-02-e2-bon-dieu-kien", fig_e2),
               ("pin-03-e2b-dung-irqbalance", fig_e2b),
               ("pin-04-e2c-tach-vi-tri", fig_e2c),
               ("pin-05-e2e-eval-perf", fig_e2e),
               ("pin-06-e2e-so-voi-e2d", fig_e2e_vs_e2d),
               ("pin-07-x6-cpu-lon", fig_x6)]
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
