#!/usr/bin/env python3
"""Phan 11 Chon model: Hinh 11.1 va 11.2.

Primary sources (see chu-thich.md, table Nguon):
  REPO tmp/02_decisions/2026-10-11_model-selection-rule.md (the rule, fixed before any number),
  REPO tmp/2026-10-11_todo-npu-model-selection.md (pending steps and commands),
  REPO ai/automation/pipeline.py, ai/automation/leaderboards/sfchd_5class.csv, ai/core/rknn/benchmark.py,
  LOG 2026-10-10_yolo-phaseA (out/stats_latency.txt), LOG 2026-10-10_t3-board-silu-resize (raw/summary*.json),
  REPO docs/npu_study/00_index.md (sections 8, 9, 10), LOG 2026-10-11_independent-verification/visual-guide_md-errata.md,
  and the `(unknown)` rows of the `## Nguon` table of every finished part (counted here by parsing the chu-thich.md files).

Numbers are read from the CSV / JSON / chu-thich.md files on disk. Hinh 11.1 states that the phase3 / phase4 inputs do
not exist yet: this script aborts if any of those files appears, because the figure would then be out of date.

Usage: python3 gen.py [outdir] [figure-name ...]   (no matplotlib needed)
"""
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))
from figlib import BLUE, DARK, GRAY, GREEN, INK, RED, THIN, Fig, run, source  # noqa: E402

W = 900
UNK_FILL = "#FFF3F3"
LB = "#EAF2FF"      # phep tinh / suy ra cua bo hinh
RB = "#EAF6EA"      # so do T3 / trang thai "co"
GY = "#F2F2F2"
C = lambda s: [(s, "c")]  # noqa: E731

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TOPIC = os.path.abspath(os.path.join(HERE, ".."))
CANDIDATES = ["sfchd_5class_yolov8n_baseline_100ep_s42", "sfchd_5class_yolov8n_relu_100ep_s42",
              "sfchd_5class_yolo26n_baseline_100ep_s42"]


# ---------------------------------------------------------------------------------------------
# data read from disk
# ---------------------------------------------------------------------------------------------
def leaderboard():
    with open(os.path.join(ROOT, "ai/automation/leaderboards/sfchd_5class.csv"), encoding="utf-8") as fh:
        return {r["model"]: r for r in csv.DictReader(fh)}


def check_pending_inputs():
    """Hinh 11.1 says phase3 / phase4 outputs do not exist yet. Abort when they do."""
    found = []
    for rid in CANDIDATES:
        for rel in ("export_int8.json", "eval/rknn_int8_sfchd_test.json", "eval/rknn_fp16_sfchd_test.json",
                    "bench/tier1_int8_AUTO.json"):
            p = os.path.join(ROOT, "ai/automation/runs", rid, rel)
            if os.path.exists(p):
                found.append(os.path.relpath(p, ROOT))
    if found:
        raise SystemExit("Hinh 11.1 is out of date, these inputs now exist: " + ", ".join(found))


def session_spread():
    """YOLOv8n, AUTO: three session medians from phaseA stats_latency.txt and their (max - min)."""
    path = os.path.join(ROOT, "tmp/04_debug-logs/2026-10-10_yolo-phaseA/out/stats_latency.txt")
    with open(path, encoding="utf-8") as fh:
        line = next(ln for ln in fh.read().splitlines() if ln.startswith("AUTO "))
    lists = re.findall(r"\[([^\]]*)\]", line)          # sessions26, sessions8
    sess8 = [float(x) for x in lists[1].split(",")]
    return sess8, round(max(sess8) - min(sess8), 3)


def silu_two_sessions():
    with open(os.path.join(ROOT, "tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/raw/summary.json"),
              encoding="utf-8") as fh:
        a = json.load(fh)["silu_opt3"]["npu_latency_ms"]
    with open(os.path.join(ROOT, "tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/raw/summary2.json"),
              encoding="utf-8") as fh:
        b = json.load(fh)["silu_opt3|AUTO"]["ms"]
    return a, b


def unknown_counts():
    """Part number -> number of `## Nguon` rows whose verbatim is (unknown), or whose content starts 'unknown:'."""
    counts = {}
    for path in sorted(glob.glob(os.path.join(TOPIC, "[0-9][0-9]-*", "chu-thich.md"))):
        part = int(os.path.basename(os.path.dirname(path))[:2])
        if part == 11:
            continue
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        start = next(i for i, ln in enumerate(lines) if ln.strip() == "## Nguồn")
        n = 0
        for ln in lines[start + 1:]:
            if not ln.startswith("|"):
                continue
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", ln.strip().strip("|"))]
            if len(cells) == 5 and (cells[4] == "(unknown)" or cells[1].startswith("unknown:")):
                n += 1
        counts[part] = n
    return counts


# ---------------------------------------------------------------------------------------------
# helpers (same style as 06-compiler-op/gen.py)
# ---------------------------------------------------------------------------------------------
def _units(s):
    return sum(2.1 if ord(ch) > 0x2E80 else 1 for ch in s)


def wrap(s, n):
    n = max(8, n)
    out, cur = [], ""
    for word in s.split(" "):
        cand = word if not cur else cur + " " + word
        if cur and _units(cand) > n:
            out.append(cur)
            cur = word
        else:
            cur = cand
    out.append(cur)
    return out


def _lines(lines, w, size):
    out = []
    for ln in lines:
        out.extend(wrap(ln, int((w - 24) / (size * 0.50))) if isinstance(ln, str) else [ln])
    return out


def card_h(w, title, lines, size=12.5, lh=17, tsize=14, h_min=0):
    t = wrap(title, int((w - 24) / (tsize * 0.50))) if title else []
    n = len(_lines(lines, w, size))
    return max(h_min, 14 + 20 * len(t) + lh * n + (4 if t else 0))


def card(f, x, y, w, title, lines, fill="white", stroke="#999999", dashed=False, size=12.5, lh=17, tsize=14,
         h_min=0, tcolor=INK):
    h = card_h(w, title, lines, size, lh, tsize, h_min)
    dash = ' stroke-dasharray="5 3"' if dashed else ""
    f.a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" '
        f'stroke-width="{1.3 if dashed else 1}"{dash}/>')
    ty = y + 7
    if title:
        for t in wrap(title, int((w - 24) / (tsize * 0.50))):
            f.text(x + 12, ty + 10, t, size=tsize, weight=700, fill=tcolor)
            ty += 20
        ty += 4
    for i, ln in enumerate(_lines(lines, w, size)):
        if isinstance(ln, str):
            f.text(x + 12, ty + 9 + lh * i, ln, size=size)
        else:
            f.rich(x + 12, ty + 9 + lh * i, ln, size=size)
    return y + h


def unk_card(f, x, y, w, title, lines, size=12.5, lh=17, h_min=0):
    return card(f, x, y, w, title, lines, fill=UNK_FILL, stroke=RED, dashed=True, size=size, lh=lh, h_min=h_min,
                tcolor=RED)


def arrow(f, x1, y1, x2, y2, label=None, lx=None, ly=None, color=BLUE):
    f.line([(x1, y1), (x2, y2)], color, THIN)
    if label:
        f.text(lx if lx is not None else (x1 + x2) / 2 + 6, ly if ly is not None else (y1 + y2) / 2, label,
               size=12.5, weight=700, fill=color, halo="white")


TIER_COLOR = {"T1": BLUE, "T2": GREEN, "T3": RED}


def table(f, x, y, widths, header, rows, size=12, lh=15.5, pad=6, fills=None, shade=None):
    """Table with wrapped cells. cell: str | ('tag', 'B'|'N') | ('tier', 'T1'|'T2'|'T3') | ('b', str) |
    ('i', str) (grey italic) | ('fill', colour, str). fills: {(row, col): colour}; shade: {row: colour}."""
    def cell_lines(cell, w):
        if isinstance(cell, tuple):
            kind = cell[0]
            if kind == "tag":
                return ["chặn quyết định", "chọn model"] if cell[1] == "B" else ["không chặn"]
            if kind == "tier":
                return [cell[1]]
            if kind in ("b", "i"):
                return wrap(cell[1], int((w - 14) / (size * 0.50)))
            if kind == "fill":
                return wrap(cell[2], int((w - 14) / (size * 0.50)))
        return wrap(cell, int((w - 14) / (size * 0.50)))

    tw = sum(widths)
    head_h = 12 + lh * max(len(cell_lines(h, w)) for h, w in zip(header, widths))
    f.a(f'<rect x="{x}" y="{y}" width="{tw}" height="{head_h}" fill="#E8E8E8"/>')
    cx = x
    for h, w in zip(header, widths):
        for i, ln in enumerate(cell_lines(h, w)):
            f.text(cx + 7, y + 6 + lh / 2 + lh * i, ln, size=size, weight=700)
        cx += w
    cy = y + head_h
    for ri, row in enumerate(rows):
        cl = [cell_lines(c, w) for c, w in zip(row, widths)]
        rh = 2 * pad + lh * max(len(c) for c in cl)
        if shade and shade.get(ri):
            f.a(f'<rect x="{x}" y="{cy}" width="{tw}" height="{rh}" fill="{shade[ri]}"/>')
        cx = x
        for ci, (c, w) in enumerate(zip(row, widths)):
            fill = (fills or {}).get((ri, ci))
            if isinstance(c, tuple) and c[0] == "fill":
                fill = c[1]
            if fill:
                f.a(f'<rect x="{cx}" y="{cy}" width="{w}" height="{rh}" fill="{fill}"/>')
            cx += w
        f.a(f'<path d="M{x} {cy} L{x + tw} {cy}" stroke="#BBBBBB" stroke-width="0.8"/>')
        cx = x
        for c, w, lines in zip(row, widths, cl):
            top = cy + rh / 2 - (len(lines) - 1) * lh / 2
            kind = c[0] if isinstance(c, tuple) else None
            if kind == "tag":
                blocking = c[1] == "B"
                col = RED if blocking else DARK
                cw = w - 14
                chh = lh * len(lines) + 6
                f.a(f'<rect x="{cx + 7}" y="{cy + rh / 2 - chh / 2}" width="{cw}" height="{chh}" rx="8" '
                    f'fill="{"#FDECEC" if blocking else GY}" stroke="{col}" stroke-width="{1.4 if blocking else 1}"/>')
                for i, ln in enumerate(lines):
                    f.text(cx + w / 2, top + lh * i, ln, size=size - 1, weight=700, fill=col, anchor="middle")
            elif kind == "tier":
                f.text(cx + 7, top, lines[0], size=size, weight=700, fill=TIER_COLOR[c[1]])
            else:
                for i, ln in enumerate(lines):
                    if kind == "b":
                        f.text(cx + 7, top + lh * i, ln, size=size, weight=700)
                    elif kind == "i":
                        f.text(cx + 7, top + lh * i, ln, size=size, fill=DARK, italic=True)
                    else:
                        f.text(cx + 7, top + lh * i, ln, size=size)
            cx += w
        cy += rh
    f.a(f'<rect x="{x}" y="{y}" width="{tw}" height="{cy - y}" fill="none" stroke="#999999" stroke-width="1"/>')
    cx = x
    for w in widths[:-1]:
        cx += w
        f.a(f'<path d="M{cx} {y} L{cx} {cy}" stroke="#CCCCCC" stroke-width="0.8"/>')
    return cy


# =====================================================================
# Hinh 11.1: quy tac chon model va trang thai cac dau vao
# =====================================================================
def fig_rule():
    check_pending_inputs()
    lb = leaderboard()
    fp = {m: lb[m]["map50_95"] for m in ("yolov8n_baseline", "yolov8s_baseline", "yolo26n_baseline", "yolov8n_relu")}
    assert fp == {"yolov8n_baseline": "0.5908", "yolov8s_baseline": "0.6152", "yolo26n_baseline": "0.5883",
                  "yolov8n_relu": "0.5835"}, fp

    f = Fig(W, 2600)
    f.tier(808, 8, "T3 đo")
    f.text(10, 22, "Quy tắc chọn model chốt trước khi có số, và trạng thái các đầu vào", size=15, weight=700)
    f.text(10, 46, "A. Quy tắc (REPO tmp/02_decisions/2026-10-11_model-selection-rule.md, mục 1)", size=14.5,
           weight=700)
    QX, QW, RX, RW = 10, 400, 470, 420
    y = 60

    # step 1
    q1 = ["Ứng viên: YOLOv8n SiLU, YOLOv8n ReLU, YOLO26n. Lệnh: make phase3 (tập test sfchd, calibration 300 ảnh "
          "seed 42, evaluator protocol v1)."]
    r1 = ["Cùng dataset sfchd_5class, 100 epoch, seed 42, tham số train của baseline.",
          "YOLOv8s có trong leaderboard nhưng không phải ứng viên."]
    h1 = max(card_h(QW, "1. Đo mAP50-95 INT8 trên board cho từng ứng viên", q1),
             card_h(RW, "Giao thức chung cho ba ứng viên", r1))
    b1 = card(f, QX, y, QW, "1. Đo mAP50-95 INT8 trên board cho từng ứng viên", q1, h_min=h1)
    card(f, RX, y, RW, "Giao thức chung cho ba ứng viên", r1, h_min=h1)
    y = b1 + 34

    # step 2 (decision)
    arrow(f, QX + QW / 2, b1, QX + QW / 2, y)
    q2 = ["Không thấp hơn quá 1.0 điểm, tuyệt đối: ví dụ 0.560 so với 0.570."]
    r2 = ["Suy ra của bộ hình: ứng viên bị loại không được xét ở bước 3; YOLOv8n SiLU luôn qua bước này vì hiệu của "
          "nó với chính nó bằng 0."]
    t2 = "2. mAP50-95 INT8 của ứng viên có thấp hơn YOLOv8n SiLU INT8 không quá 1.0 điểm?"
    h2 = max(card_h(QW, t2, q2), 64)
    b2 = card(f, QX, y, QW, t2, q2, h_min=h2, stroke=BLUE)
    card(f, RX, y, RW, "Không: loại khỏi danh sách", r2, fill=LB, stroke=BLUE, h_min=h2)
    arrow(f, QX + QW, y + 22, RX, y + 22, "Không", QX + QW + 6, y + 10)
    y = b2 + 34

    # step 3
    arrow(f, QX + QW / 2, b2, QX + QW / 2, y, "Có", QX + QW / 2 + 8, b2 + 17)
    t3 = "3. Trong số còn lại, chọn model có trung vị độ trễ tier 1 thấp nhất ở core_mask AUTO"
    q3 = ["Tier 1 là eval_perf: mỗi phiên 5 lần lặp, lấy trung vị. Lệnh: make phase4; YOLO26n và ReLU qua target riêng "
          "(Hình 7.2)."]
    r3 = ["Chỉ số tốc độ của quy tắc là tier 1. Tier 2 (Hình 7.2) có trong bảng kết quả của todo nhưng quy tắc không "
          "dùng."]
    h3 = max(card_h(QW, t3, q3), card_h(RW, "Độ trễ nào được dùng", r3))
    b3 = card(f, QX, y, QW, t3, q3, h_min=h3)
    card(f, RX, y, RW, "Độ trễ nào được dùng", r3, h_min=h3)
    arrow(f, QX + QW, y + h3 / 2, RX, y + h3 / 2)
    y = b3 + 34

    # step 4 (decision)
    arrow(f, QX + QW / 2, b3, QX + QW / 2, y)
    t4 = "4. Model đó nhanh hơn YOLOv8n SiLU một cách rõ ràng, tức chênh lệch nằm ngoài độ trải giữa các phiên đo?"
    h4 = max(card_h(QW, t4, []), 70)
    b4 = card(f, QX, y, QW, t4, [], h_min=h4, stroke=BLUE)
    y4 = card(f, RX, y, RW, "Có: chọn model nhanh nhất đó", ["Quyết định tạm, vì chỉ có seed 42."], h_min=h4,
              fill=LB, stroke=BLUE)
    arrow(f, QX + QW, y + h4 / 2, RX, y + h4 / 2, "Có", QX + QW + 6, y + h4 / 2 - 10)
    y = max(b4, y4) + 34

    # branch "Không"
    arrow(f, QX + QW / 2, b4, QX + QW / 2, y, "Không", QX + QW / 2 + 8, b4 + 17)
    bB = card(f, QX, y, QW, "Không: giữ YOLOv8n SiLU", ["Quyết định tạm, vì chỉ có seed 42."], fill=LB, stroke=BLUE)
    uy = unk_card(f, 440, y, 380, "Chưa định nghĩa độ trải",
                  ["Cách tính 'độ trải giữa các phiên' và mức coi là 'rõ ràng' chưa được chốt; todo mục 3.4 ghi "
                   "'Cần quyết khi tới bước này'."], h_min=bB - y)
    y = max(bB, uy) + 34

    # step 5
    arrow(f, QX + QW / 2, bB, QX + QW / 2, y)
    arrow(f, 860, y4, 860, y)
    y = card(f, 10, y, 880, "5. Cả hai nhánh đều là quyết định tạm: chỉ có seed 42",
             ["Phase 10 thêm seed 43 và 44 cho model được chọn: make phase10 DATASET=sfchd_5class MODELS=<model> "
              "(todo mục 4; pipeline.py:21)."]) + 22

    # conditions
    f.text(10, y, "Điều kiện đi kèm quy tắc", size=14.5, weight=700)
    y += 14
    c1 = ["Nếu chọn ngưỡng sau khi thấy số, ngưỡng dễ bị kéo theo kết quả; vì vậy quy tắc được chốt trước (Hình 10.8)."]
    c2 = ["Hình 10.1 và 10.4 là phép đo cấu trúc và độ trễ, không có accuracy; quy tắc không dùng chúng để chọn."]
    c3 = ["Nếu một lớp vi phạm PPE sụt mạnh sau INT8 thì cần xem riêng trước khi triển khai; chưa có số từng lớp "
          "(Hình 10.7)."]
    c4 = ["Decision log gọi AP của ReLU là cận dưới thực tế; bộ hình ghi đây là nhận định chưa kiểm bằng huấn luyện "
          "từ đầu. Log train: Transferred 322/355 items ở cả baseline và ReLU (Hình 10.5)."]
    ha = max(card_h(435, "Ngưỡng chốt trước khi có số", c1), card_h(435, "Số trọng số ngẫu nhiên không dùng để chọn", c2))
    card(f, 10, y, 435, "Ngưỡng chốt trước khi có số", c1, h_min=ha)
    ya = card(f, 455, y, 435, "Số trọng số ngẫu nhiên không dùng để chọn", c2, h_min=ha)
    y = ya + 10
    hb = max(card_h(435, "AP từng lớp không nằm trong quy tắc", c3), card_h(435, "ReLU khởi tạo từ trọng số SiLU", c4))
    card(f, 10, y, 435, "AP từng lớp không nằm trong quy tắc", c3, h_min=hb)
    yb = unk_card(f, 455, y, 435, "ReLU khởi tạo từ trọng số SiLU", c4, h_min=hb)
    y = yb + 26

    # ---------------- B. status
    f.text(10, y, "B. Trạng thái các đầu vào của quy tắc", size=14.5, weight=700)
    y += 14
    fp_txt = (f"mAP50-95 FP32 test của 4 model: YOLOv8n {fp['yolov8n_baseline']}, YOLOv8s {fp['yolov8s_baseline']}, "
              f"YOLO26n {fp['yolo26n_baseline']}, YOLOv8n ReLU {fp['yolov8n_relu']}")
    rows = [
        [fp_txt, "có",
         "ai/automation/leaderboards/sfchd_5class.csv, cột map50_95 (protocol v1, seed 42)",
         "Không dùng để chọn (quy tắc dùng INT8 trên board). Hình 10.5, 10.7"],
        ["Độ trễ cấu trúc trên trọng số ngẫu nhiên (YOLOv8n, YOLO26n; SiLU, ReLU)", "có",
         "tmp/04_debug-logs/2026-10-10_yolo-phaseA/out/stats_latency.txt; "
         "tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/raw/summary2.json",
         "Không dùng để chọn. Hình 10.1, 10.4"],
        ["mAP50-95 INT8 và FP16 chạy trên board, ba ứng viên", "chờ",
         "make phase3 DATASET=sfchd_5class. Xong khi mỗi run có export_int8.json và eval/rknn_int8_sfchd_test.json "
         "(hiện chưa run nào có)",
         "Dùng ở bước 1, 2. Hình 10.7, 10.8"],
        ["Độ trễ tier 1 và tier 2 của model đã huấn luyện", "chờ",
         "make phase4 DATASET=sfchd_5class chỉ chạy YOLOv8n và YOLOv8s (pipeline.py:19); YOLO26n và ReLU cần target "
         "riêng (todo mục 3.3). Xong khi có bench/tier1_int8_AUTO.json (hiện chưa run nào có)",
         "Tier 1 dùng ở bước 3, 4; tier 2 không dùng. Hình 10.8, 7.2"],
        ["Độ trải giữa các phiên đo", "chờ, chưa quyết",
         "Đề xuất, chưa quyết: sau pipeline chạy thêm 3 phiên xen kẽ thứ tự model trên đúng file .rknn INT8, log riêng, "
         "không ghi đè bench/ (todo mục 3.4)",
         "Dùng ở bước 4. Hình 10.4, 10.8"],
        ["AP từng lớp sau INT8", "chờ",
         "Cùng make phase3; chưa có số từng lớp INT8",
         "Không nằm trong quy tắc, xem riêng. Hình 10.7"],
        ["Seed 43 và 44", "chờ",
         "make phase10 DATASET=sfchd_5class MODELS=<model>, chỉ cho model được chọn (todo mục 4)",
         "Không dùng cho quyết định tạm. Hình 10.5"],
    ]
    fills = {}
    for i, r in enumerate(rows):
        fills[(i, 1)] = RB if r[1] == "có" else UNK_FILL
    y = table(f, 10, y, [215, 90, 365, 210], ["Đầu vào", "Trạng thái", "File hoặc lệnh", "Dùng để chọn? Hình"], rows,
              fills=fills)
    y += 12
    y = card(f, 10, y, 880, "Điều kiện để đo",
             ["Cần board bật (todo ghi board offline lúc viết, 2026-10-11), người dùng nhập mật khẩu sudo cho "
              "start_rknn_server.sh và lock_freq.sh trước khi chạy make phase3, phase4 (todo mục 2)."]) + 20

    y = unk_card(f, 10, y, 880, "Khuyến nghị chọn model: chưa có khuyến nghị",
                 ["Thiếu mAP50-95 INT8 trên board, trung vị tier 1 của model đã huấn luyện và độ trải giữa các phiên "
                  "(ba hàng chờ ở trên). Số FP32 và số trên trọng số ngẫu nhiên không dùng để chọn.",
                  "Mọi lựa chọn về sau chỉ là tạm vì chỉ có seed 42; phase 10 thêm seed 43 và 44 cho model được chọn."]) + 18

    y = f.legend(10, y, 880, [
        ("blue", "thứ tự xét; ô viền xanh là bước quyết định"),
        ("fill:" + LB, "suy ra hoặc kết quả của quy tắc (bộ hình vẽ lại, không phải câu của vendor)"),
        ("fill:" + RB, "đầu vào đã có (file có trên đĩa)"),
        ("fill:" + UNK_FILL, "đầu vào còn chờ, hoặc điều chưa quyết, hoặc nhận định chưa kiểm"),
    ])
    source(f, y + 8, "Nguồn: model-selection-rule.md mục 1; todo-npu-model-selection.md mục 2, 3, 4; pipeline.py:19, 21; "
           "benchmark.py:23; sfchd_5class.csv.")
    return f


# =====================================================================
# Hinh 11.2: ban do unknown va mau thuan
# =====================================================================
BLOCKS = [
    # (key, label, [(text, tier, tag, hinh)])
    (1, "01 NPU cơ bản", [
        ("RK3588 dùng dataflow nào: không có từ khóa dataflow, stationary, systolic, tiling trong TRM1 tr.1984 đến "
         "2060, TRM2, DS, UG152, API232", "T1", "N", "Hình 1.2"),
        ("Ridge point của RK3588", "T1", "N", "Hình 1.4"),
        ("'PE' của RK3588 là gì: TRM không nói ô 32x32 là một PE", "T1", "N", "Hình 1.1"),
    ]),
    (2, "02 Phần cứng RK3588", [
        ("Cách userspace chia việc giữa các core", "T1", "N", "Hình 2.4"),
        ("Quy ước đếm phép tính của vendor cho 6 TOPS", "T1", "N", "Hình 2.3"),
        ("Khai triển tên CNA, BS, BN, CBUF", "T1", "N", "Hình 2.2"),
    ]),
    (3, "03 Lý thuyết lượng tử", [
        ("Lượng tử hóa YOLOv8 (SiLU, C2f, DFL, detect head): không có kết quả trong paper của bộ", "T2", "N",
         "Hình 3.4, 3.5"),
        ("NAGEL không nêu KL divergence và percentile", "T2", "N", "Hình 3.3"),
        ("Giá trị ngưỡng epsilon của Figure 9", "T2", "N", "Hình 3.5"),
    ]),
    (4, "04 Lượng tử RKNN", [
        ("Số ảnh calibration cho miền hẹp như PPE", "T1", "N", "Hình 4.1"),
        ("int8, int16 trong custom_quantize_layers chạy được trên RK3588", "T1", "N", "Hình 4.2"),
        ("Ngưỡng cosine để coi là đạt", "T1", "N", "Hình 4.3"),
    ]),
    (5, "05 Toolchain", [
        ("RKNN-Toolkit-Lite2 có cần rknn_server hay không", "T1", "N", "Hình 5.2"),
        ("Độ trễ eval_perf qua board nối PC so với C API", "T1", "N", "Hình 5.2"),
        ("Vì sao UG232 không nhắc node power, freq, volt, delayms", "T1", "N", "Hình 5.3"),
    ]),
    (6, "06 Compiler và op", [
        ("OPL không nêu quy tắc rơi về CPU", "T1", "N", "Hình 6.1"),
        ("Luật ghép SiLU của compiler; ConvExSwish có phải ConvolutionSwish", "T1", "N", "Hình 6.2, 6.3"),
        ("Thuật toán fusion, thứ tự pass, rule bị tắt bởi level 1, 2", "T1", "N", "Hình 6.3"),
    ]),
    (7, "07 Bộ nhớ và hiệu năng", [
        ("Ranh giới của Total Time(us): có gồm đặt input và lấy output hay không", "T1", "N", "Hình 7.2"),
        ("Log T3 của tier 2 chưa có", "T3", "N", "Hình 7.2"),
        ("Hiệu lực của fix_freq chưa đo", "T3", "N", "Hình 7.3"),
    ]),
    (8, "08 Thiết kế model", [
        ("AP INT8 của ReLU trên board chưa có (chờ pipeline)", "T3", "B", "Hình 8.2, 10.7"),
        ("AP của ReLU là cận dưới thực tế: nhận định chưa kiểm bằng huấn luyện từ đầu", "T3", "N",
         "Hình 8.2, 10.5"),
        ("Re-param trên RK3588 INT8 chưa biết", "T2", "N", "Hình 8.2"),
    ]),
    (9, "09 YOLO", [
        ("Độ chính xác INT8 của khối attention chưa đo", "T3", "B", "Hình 9.4"),
        ("Tên ConvExSwish không có trong OPL và UG232", "T1", "N", "Hình 9.3"),
        ("Quy tắc nhận chuỗi MatMul, Softmax, MatMul thành exSDPAttention", "T1", "N", "Hình 9.3"),
    ]),
]

T3_ROWS = [
    ("mAP50-95 INT8 chạy trên board của ba ứng viên (chưa có)", "T3", "B", "Hình 10.7, 10.8"),
    ("Độ trễ tier 1 ở AUTO của model đã huấn luyện (chưa có)", "T3", "B", "Hình 10.8, 7.2"),
    ("Độ trải giữa các phiên đo (chưa đo, chưa định nghĩa)", "T3", "B", "Hình 10.4, 10.8"),
    ("Nguyên nhân SiLU dao động giữa các phiên (cùng file .rknn)", "T3", "N", "Hình 10.1, 10.3"),
    ("T3 còn lại: Resize bilinear và FP16, YOLO11 so YOLOv8n, cơ chế fix_freq, ép ConvExSwish chạy đa lõi, "
     "rknpu/load khi chạy, quy ước đếm 6 TOPS", "T3", "N", "Hình 6.2, 7.3, 8.2, 10.3"),
]

CONTRADICTIONS = [
    ("Resize có chạy trên NPU không",
     "UG232 tr.176: NPU chưa hỗ trợ Resize cấp phần cứng, toolkit đổi thành ConvTranspose. OPL mục 3.2.54 có mục Resize "
     "cho RK3588. T3: Target = NPU với nearest 2x INT8 (trọng số ngẫu nhiên); bilinear và FP16 chưa thử.",
     "T1", "N", "Hình 6.2, 8.2"),
    ("Danh sách op chạy nhanh hơn khi nhiều core",
     "UG152 tr.27 và UG232 tr.75 liệt kê PRelu; OPL mục 3.2.51 PRelu ghi 多核联合: 暂不支持. Bộ hình không chọn phía "
     "nào.", "T1", "N", "Hình 2.4, 8.2"),
    ("INT16 trên RK3588",
     "UG152 tr.56 Table 4-6 có cột Int16 cho RK3588; API232 tr.7 ghi w16a16i 'Only RV1103/RV1106 supported'. "
     "00_index mục 8: unknown ở mức SDK.", "T1", "N", "Hình 6.4"),
    ("Số ảnh calibration",
     "API232 tr.8: normal khoảng 20-100 ảnh; UG232 tr.159: normal hoặc kl_divergence 20-200. Protocol của repo dùng "
     "300 ảnh; T1 không nêu số ảnh cho miền hẹp như PPE.", "T1", "N", "Hình 4.4, 4.1"),
    ("Hybrid quantization: hàng 5, 6, 8 của bảng 10 mâu thuẫn",
     "Không có code hay nguồn thứ ba phân xử (kiểu lượng tử trong hybrid, thước đo cosine và euclidean, "
     "FP32 trong accuracy_analysis).", "T1", "N", "Hình 4.4"),
    ("Số sự kiện ngắt của NPU",
     "TRM1 tr.2053: 17 possible events; tr.1995 chỉ mô tả mask[0] đến mask[13]. Bit 14 đến 16 không được mô tả.",
     "T1", "N", "Hình 2.5"),
]

ERRATA = [
    # (#, old note, what the primary source says, figure)
    ("1", "02_ mục 2.2, 00_index: PD_NPUTOP gồm RKNN_CORE0, MCU_NPU, PVTPLL_NPU, TIMER_NPU",
     "TRM1 tr.1093 Table 7-1 còn có BIU_NPUTOP, PVTM_NPU, WDT_NPU", "Hình 2.1"),
    ("4", "00_index mục 5, 04_: 'UG232 tr.122 lỗi thời'",
     "UG232 phát hành 2025-04-03, API232 2025-4-1: UG232 mới hơn, chỉ khác code", "Hình 4.4"),
    ("5", "00_index mục 5: hybrid_quantization_step2 'không ghi file .rknn'",
     "API232 tr.21: 'the hybrid quantized RKNN model is generated' (không nói có ghi file hay không; 'không ghi file' chỉ là suy ra)", "Hình 4.2"),
    ("6", "04_: câu 'namely normal, mmse, and kl_divergence' và '20-200 sets' ở UG232 tr.158",
     "Hai câu đó ở UG232 tr.159", "Hình 4.4"),
    ("9", "03_: mô tả Normal, KL, MMSE ở UG232 tr.120",
     "Tr.120 chỉ nêu tên; mô tả 'does not introduce truncation error' ở tr.121", "Hình 3.3"),
    ("10", "03_, 00_index mục 4: cross-entropy ở NAGEL Eq. 14-16 tr.9",
     "Cross-entropy là Eq. 17 ở tr.10; Eq. 18, 19 (BN) cũng ở tr.10", "Hình 3.3"),
    ("11", "03_: NAGEL Table 1 hai hàng đầu ghi '(per-tensor)'",
     "Bài chỉ ghi '(Per-channel)' ở hai hàng cuối; 'per-tensor' là suy ra", "Hình 3.2"),
    ("12", "03_, 00_index mục 4: mâu thuẫn weight và activation của QYOLO chỉ nêu YOLOv5m 6-bit",
     "YOLOv5s 6-bit cũng vậy (activation -0.8, weight -0.7), QYOLO tr.10 Table 3", "Hình 3.5"),
    ("13", "05_ mục 5.4: rknpu/driver_version là node bình thường",
     "Chuỗi driver_version không có trong rknpu_debugger.c (grep 0 kết quả)", "Hình 5.3"),
    ("14", "05_, 00_index mục 6: driver '>= 0.9.2' và '0.8.8 or later' là mâu thuẫn",
     "UG232 tr.136: 0.8.8 chỉ là khuyến nghị, 'This step is not mandatory'", "Hình 5.3"),
    ("17", "05_: rknpu/load T3 đọc 'lúc nhàn rỗi'",
     "README log chỉ ghi giá trị, không ghi trạng thái NPU lúc đọc", "Hình 5.3"),
    ("18", "07_, 02_ mục 2.7: (thiếu) DTS của repo",
     "syssram 0xef000 chia cho rkvdec0_sram và rkvdec1_sram; node rknpu không có rockchip,sram", "Hình 7.1"),
    ("19", "README log lượt 2, 02_ mục 2.5: ở CORE_0_1_2 không có Conv chạy lõi 0; Reshape chạy lõi 0",
     "6 trong 7 Conv chia ba lõi, chỉ dfl/conv là 100%/0%/0%; 3 trong 7 Reshape có WorkLoad 0.0%/0.0%/0.0%",
     "Hình 6.2, 8.2"),
    ("21", "06_, 00_index mục 7.1: (thiếu) UG232 tr.176 về Resize",
     "UG232 tr.176 nói NPU chưa hỗ trợ Resize cấp phần cứng, trong khi OPL có mục Resize: mâu thuẫn T1", "Hình 6.2"),
    ("24", "README log lượt 2: độ trải SiLU 'đến 4.6 ms', ReLU 'dưới 0.2 ms ở AUTO'",
     "Tính lại từ JSON: SiLU lớn nhất 4.907 ms (CORE_0_1_2), ở AUTO 4.396 ms; ReLU ở AUTO có giá trị 0.307 ms",
     "Hình 10.1"),
    ("25", "todo mục 7: 'AP của ReLU là cận dưới thực tế'",
     "Không nguồn nào kiểm; chỉ có pretrained: yolov8n.pt và 'Transferred 322/355'", "Hình 8.2, 10.5"),
]


def fig_unknown():
    counts = unknown_counts()
    a, b = silu_two_sessions()
    sess8, spread8 = session_spread()
    assert (a, b) == (19.154, 22.021), (a, b)
    assert sess8 == [19.399, 21.66, 19.152] and spread8 == 2.508, (sess8, spread8)

    f = Fig(W, 3600)
    f.tier(570, 8, "T1 RK3588")
    f.tier(688, 8, "T2 chung")
    f.tier(792, 8, "T3 đo")
    f.text(10, 22, "Bản đồ chỗ chưa biết và chỗ còn mâu thuẫn", size=15, weight=700)
    y = 46

    # --- legend of the two tags
    y = card(f, 10, y, 880, "Hai nhãn trên bản đồ", [
        "chặn quyết định chọn model: thiếu thì chưa áp dụng được quy tắc ở Hình 11.1. không chặn: quy tắc vẫn áp dụng "
        "được; điều chưa biết chỉ ảnh hưởng cách giải thích hoặc việc khác.",
        "Đây là bản đồ, không phải danh sách đầy đủ: mỗi khối chỉ hiện vài mục đại diện và số dòng unknown còn lại. "
        "Câu trả lời của từng mục nằm ở hình ghi bên phải."]) + 18

    # --- A. blockers
    f.text(10, y, "A. Ba mục chặn quyết định chọn model", size=14.5, weight=700)
    y += 14
    a1 = ["Đã biết: chỉ có mAP50-95 FP32 trên test (Hình 10.5, 10.7); chưa có FP16, INT8, kể cả khối attention của "
          "YOLO26n (Hình 9.4).",
          "Cách đóng: make phase3 DATASET=sfchd_5class. 00_index mục 9 khối 09: 'Huấn luyện YOLO26n 5 lớp, xuất INT8, đo "
          "mAP FP32 so INT8'.",
          "Truy vấn đề xuất (00_index mục 9, khối 03, chưa thực hiện): \"YOLOv8 post-training quantization INT8 "
          "accuracy drop\"."]
    y = unk_card(f, 10, y, 880, "Chặn 1. mAP50-95 INT8 chạy trên board của ba ứng viên", a1) + 10
    a2 = ["Đã biết: chỉ có độ trễ trên trọng số ngẫu nhiên (Hình 10.1, 10.4), không dùng để chọn.",
          "Cách đóng: make phase4 cho YOLOv8n, YOLOv8s, cộng target riêng cho YOLO26n và ReLU (todo mục 3.3).",
          "Truy vấn đề xuất (00_index mục 9, khối 08, chưa thực hiện): \"SiLU vs ReLU latency RKNN RK3588 INT8 "
          "YOLOv8\"."]
    y = unk_card(f, 10, y, 880, "Chặn 2. Độ trễ tier 1 ở AUTO của model đã huấn luyện", a2) + 10
    a3 = [f"Đã thấy trên trọng số ngẫu nhiên: cùng file .rknn cho trung vị {a} ms rồi {b} ms (silu_opt3, AUTO, hai "
          f"lượt). Trung vị ba phiên của YOLOv8n ở AUTO là {sess8[0]}, {sess8[1]}, {sess8[2]} ms: lớn nhất trừ nhỏ "
          f"nhất là {spread8} ms (phép tính của bộ hình).",
          "Cách đóng: đo T3. 00_index mục 9 không có truy vấn tìm nguồn cho mục này. Đề xuất ba phiên xen kẽ "
          "(todo mục 3.4), chưa quyết."]
    y = unk_card(f, 10, y, 880, "Chặn 3. Độ trải giữa các phiên đo", a3) + 24

    # --- B. block map
    f.text(10, y, "B. Bản đồ theo khối: mục đại diện và số dòng unknown còn lại", size=14.5, weight=700)
    y += 14
    rows, shade = [], {}
    ri = 0
    for part, label, items in BLOCKS:
        for k, (text, tr, tag, fig) in enumerate(items):
            rows.append([("b", label) if k == 0 else "", text, ("tier", tr), ("tag", tag), fig])
            if part % 2 == 0:
                shade[ri] = "#F7F7F7"
            ri += 1
        rest = counts[part] - len(items) if part != 9 else counts[part] - len(items)
        rows.append(["", ("i", f"Còn {rest} dòng unknown khác trong bảng nguồn của phần {part}"), "", "", ""])
        if part % 2 == 0:
            shade[ri] = "#F7F7F7"
        ri += 1
    # T3 block
    for k, (text, tr, tag, fig) in enumerate(T3_ROWS):
        rows.append([("b", "T3 đo, việc chờ") if k == 0 else "", text, ("tier", tr), ("tag", tag), fig])
        ri += 1
    rows.append(["", ("i", f"Còn {counts[10]} dòng unknown trong bảng nguồn của phần 10 (calibration, nhận định ReLU)"),
                 "", "", ""])
    y = table(f, 10, y, [118, 452, 44, 126, 140], ["Khối", "Câu hỏi còn mở", "Tier", "Nhãn", "Hình"], rows, shade=shade)
    y += 24

    # --- C. contradictions
    f.text(10, y, "C. Mâu thuẫn còn mở giữa các nguồn", size=14.5, weight=700)
    y += 14
    crow = [[("b", t), body, ("tier", tr), ("tag", tag), fig] for t, body, tr, tag, fig in CONTRADICTIONS]
    y = table(f, 10, y, [160, 430, 44, 126, 120], ["Mâu thuẫn", "Hai phía", "Tier", "Nhãn", "Hình"], crow)
    y += 24

    # --- D. errata
    f.text(10, y, "D. Ghi chú cũ đã sai ở đâu (đã kiểm lại trên nguồn gốc)", size=14.5, weight=700)
    y += 14
    erow = [[("b", n), old, new, fig] for n, old, new, fig in ERRATA]
    y = table(f, 10, y, [34, 340, 376, 130], ["#", "Ghi chú cũ ghi", "Nguồn gốc nói", "Hình"], erow, size=11.5,
              lh=15, pad=5)
    y += 8
    f.text(10, y + 6, "Bảng lấy các hàng đánh dấu 'có' của visual-guide_md-errata.md; số # theo bảng đó. "
           "Chưa sửa các file .md.", size=12, fill=DARK, italic=True)
    y += 28

    y = f.legend(10, y, 880, [
        ("fill:#FDECEC", "chặn quyết định chọn model (viền đỏ)"),
        ("fill:" + GY, "không chặn"),
        ("fill:" + UNK_FILL, "unknown: nguồn không cho, hoặc phép đo chưa làm"),
        ("fill:#F7F7F7", "chỉ để phân nhóm theo khối"),
    ])
    source(f, y + 8, "Nguồn: dòng unknown của bảng nguồn phần 1 đến 10; 00_index mục 8, 9; todo mục 3, 5; "
           "md-errata; TRM1 tr.1995, 2053; UG152 tr.27, 56; UG232 tr.176; OPL 85, 86.")
    return f


def _int_h(build):
    def inner():
        fig = build()
        fig.h = int(-(-fig.h // 1))
        return fig
    return inner


FIGS = [
    ("h11-1-quy-tac", fig_rule),
    ("h11-2-unknown", fig_unknown),
]

if __name__ == "__main__":
    run([(n, _int_h(b)) for n, b in FIGS], HERE)
