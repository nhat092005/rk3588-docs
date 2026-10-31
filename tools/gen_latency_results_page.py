#!/usr/bin/env python3
"""Sinh các trang 02 đến 05 của nhóm docs "Đo latency trên NPU" (03-phuong-phap/03-do-latency-npu) từ kết quả đo, không gõ tay số.

Đọc ../results/{latency_per_block,layer_analysis,onboard}_<run>_int8_CORE_0.json và ../ai/automation/runs/<run>/bench/.
Chạy từ gốc repo chính:  .venv/bin/python docs/tools/gen_latency_results_page.py
Lời văn nằm trong script, mọi con số lấy từ file JSON hoặc file đo. Chạy lại script sau khi đo lại.
"""
import csv
import json
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUN = "ppe5_yolov8n_baseline_100ep_s0"
BENCH = REPO / "ai" / "automation" / "runs" / RUN / "bench"
RES = REPO / "results"
OUTDIR = REPO / "docs" / "contents" / "03-phuong-phap" / "03-do-latency-npu"
NAMES = {"02": "02-ket-qua-latency-tung-khoi.rst", "03": "03-phan-tich-sau-latency-tung-khoi.rst", "04": "04-cac-muc-do-tre.rst", "05": "05-thu-ghim-cpu-va-ngat.rst", "06": "06-co-che-cac-muc-do-tre.rst", "07": "07-giao-thuc-p2-va-do-mo-rong.rst"}

A = json.loads((RES / f"latency_per_block_{RUN}_int8_CORE_0.json").read_text())
L = json.loads((RES / f"layer_analysis_{RUN}_int8_CORE_0.json").read_text())
O = json.loads((RES / f"onboard_{RUN}_int8_CORE_0.json").read_text())
S = A["summary"]
E2 = O["e2"]
E2B = O["e2b"]
E2C = O["e2c"]
E2D = O["e2d"]
_DIFFS = [c["diff_ms"] for c in O["e2e"]["comparison"].values()]
_x9 = json.loads((RES / f"onboard_x9_{RUN}_int8_CORE_0.json").read_text())
assert [t["samples"] for t in _x9["trials"]] == [55, 49, 49] and _x9["label_U4"] == "ĐO" and _x9["trials"][0]["changed_samples"] > 0 and all(t["changed_samples"] == 0 for t in _x9["trials"][1:])
_x4c = json.loads((RES / f"onboard_x4_{RUN}_int8_CORE_0.json").read_text())
assert _x4c["protocols"]["p1lan"]["debug_below_latency"] == 4 and _x4c["protocols"]["p2"]["debug_below_latency"] == 0
assert 4.85 < min(_x4c["protocols"]["p2"]["intercepts_us"]) and max(_x4c["protocols"]["p2"]["intercepts_us"]) < 5.2 and _x4c["protocols"]["p2"]["intercept_spread_us"] < 0.35
assert 8.0 < min(_x4c["protocols"]["p1lan"]["intercepts_us"]) and max(_x4c["protocols"]["p1lan"]["intercepts_us"]) < 52.0
_x10 = json.loads((RES / f"analysis_x10_{RUN}_int8_CORE_0.json").read_text())
_x10_l6 = next(r for r in _x10["small_rows"] if "model.6/cv1" in r["name"])
assert _x10["u11"] == "chưa kết luận" and _x10["u12"] == "chưa kết luận" and _x10["n_small"] == 6
assert sum(1 for r in _x10["small_rows"] if abs(r["time_us"] - r["predicted_us"]) <= 0.2 * r["time_us"]) == 5
_lt = (BENCH / "extra_tier1_lan_timing.txt").read_text()
_lan = dict(init=float(_lt.split("init_runtime ret=0 ")[1].split(" s")[0]), calls=[float(x.split("wall ")[1].split(" s")[0]) for x in _lt.splitlines() if x.startswith("eval_perf call")])
_e2e_med = [b["median"] for b in O["e2e"]["blocks"].values()]
_e2e_lo, _e2e_hi = min(_e2e_med), max(_e2e_med)
assert 16.4 < _e2e_lo < 16.6 and 20.3 < _e2e_hi < 20.4 and 19.8 < min(s_["median"] for s_ in O["e1"]["sessions"]) and max(s_["median"] for s_ in O["e1"]["sessions"]) < 20.1
assert _lan["init"] == 1.5 and len(_lan["calls"]) == 10 and min(_lan["calls"]) == 0.21 and max(_lan["calls"]) == 0.43


def rec(name):
    return json.loads((BENCH / name).read_text())


def f(x, d=1):
    return f"{x:.{d}f}"


def pct(x, d=1):
    return f"{100 * x:.{d}f}%"


def table(headers, rows, widths=None):
    out = [".. list-table::", "   :header-rows: 1"]
    if widths:
        out.append("   :widths: " + " ".join(str(w) for w in widths))
    out.append("")
    for line in [headers] + rows:
        for i, cell in enumerate(line):
            out.append(("   * - " if i == 0 else "     - ") + str(cell))
    return "\n".join(out)


# ---------------------------------------------------------------- data
b2 = rec("tier1_int8_CORE_0.json")
b3 = [rec(f"tier1_int8_CORE_0_sess{n}.json") for n in (1, 2, 3)]
hot = O["hot"]
levels = O["hot_levels"]
e1 = O["e1"]
gap = O["gap"]
act = O["activity_hot_1"]
fits = O["detail_conv_fit"]
c = L["conv"]
ot = L["other"]
hd = L["head"]
all_runs_ms = []
lat_rows = []


def lat_row(name, vals, note):
    lat_rows.append([name, f(statistics.median(vals), 3), f(min(vals), 3) + " đến " + f(max(vals), 3), len(vals), note])
    all_runs_ms.extend(vals)


lat_row("B2, ``eval_perf``, 1 phiên", b2["npu_latency_ms_all"], "5 lần gọi, ``perf_debug=False``")
for n, r in enumerate(b3, 1):
    lat_row(f"B3 phiên {n}, ``eval_perf``", r["npu_latency_ms_all"], "5 lần gọi, ``perf_debug=False``")
for s in e1["sessions"]:
    lat_row(f"E1 phiên {s['session']}, ``eval_perf``", s["values"], "20 lần gọi, ``perf_debug=False``")
hot_csv = {}
for n in (1, 2, 3):
    hot_csv[n] = [int(r["wall_us"]) / 1000 for r in csv.DictReader(open(BENCH / "onboard" / f"hot_{n}.csv"))]
    h = hot[str(n)]
    lat_rows.append([f"Trên board, C API, đợt {n}", f(h["median"] / 1000, 3), f(h["min"] / 1000, 3) + " đến " + f(h["max"] / 1000, 3), h["n"], "chạy liên tiếp, ``rknn_run`` đo bằng đồng hồ CPU"])
share_pp = O["share_agreement_max_pp_blocks_ge_2pct"]
l22 = A["blocks"]["L22"]
dfl = [r for r in hd["dfl_chain"]]
dfl_us = sum(r["time"] for r in dfl)
ord_blocks = sorted([b for b in A["blocks"] if b.startswith("L")], key=lambda b: int(b[1:])) + ["io", "post_detect"]
unstable = {b: v for b, v in {k: x["share_spread"] for k, x in A["blocks"].items() if x["share"] >= 0.02}.items() if v > 0.10}
conv_bands = c["bands"]
mid = E2["level_medians_ms"]
_a8b2 = next(x for x in A["checks"] if x["code"] == "A8+B2")["detail"]
A8B2 = "tổng debug lệch " + _a8b2.split("gap ")[1].split(",")[0] + ", " + str(len([t for t in _a8b2.split("{")[1].split("}")[0].split(",") if t.strip()])) + " khối vượt 10%"
bb_share = sum(A["blocks"][f"L{i}"]["share"] for i in range(10))
all_hot = [x for v in hot_csv.values() for x in v]
n_trans = sum(1 for x in all_hot if 17.0 <= x < 18.5)
# claims written by hand in the text below, checked at every run so a rerun cannot drift silently
for _blk, _cond in enumerate("ABCDDCBA", 1):
    _irq = {}
    for _tag in ("pre", "post"):
        for _ln in (BENCH / "onboard_e2" / f"irq_{_tag}_{_blk}_{_cond}.txt").read_text().splitlines():
            _p = _ln.split()
            _irq.setdefault(_p[0].rstrip(":"), {})[_tag] = sum(int(x) for x in _p[1:] if x.isdigit())
    assert _irq["37"]["post"] == _irq["37"]["pre"] and _irq["38"]["post"] == _irq["38"]["pre"], f"irq 37 or 38 counted in block {_blk}"
assert sum(1 for x in all_hot if 17.0 <= x < 18.5) == n_trans
assert gap["gap2s"]["max"] < 20000 and gap["gap10s"]["max"] < 20000
assert c["bands"][1]["rows"] * 2 == c["n"] and 0.5 < c["bands"][1]["time_us"] / c["time_us"] < 0.6  # text: half of the Conv rows and 55 percent of the Conv time
assert E2["verdict"]["B"]["excluded_blocks"] == [2] and "chưa kết luận" in E2["verdict"]["B"]["label"]
assert [x["app"] for x in E2["classes"]] == ["migrating", "CPU4", "CPU0", "migrating", "CPU4"]
# E2b: B realized in 4 of 4 blocks, every block counted 1050 runs x 63 interrupts, B has no slow run, label ủng hộ under the half mean pairing
assert [b["cond"] for b in E2B["blocks"].values()] == list("ABBAABBA") and len(E2B["realized"]) == 4 and all(E2B["realized"].values())
assert all(b["irq_total"] == 1050 * 63 for b in E2B["blocks"].values()), "E2b interrupts per block"
assert all(b["slow"] == 0 for b in E2B["blocks"].values() if b["cond"] == "B") and E2B["label"] == "ủng hộ"
assert all(b["irq_cpu"] == "CPU0" and b["irq_top_share"] == 1.0 for b in E2B["blocks"].values() if b["cond"] == "A")
_pr = E2B["progress"].splitlines()
_post_b = [ln for ln in _pr if ln.startswith("block ") and "post readback" in ln and ln.split()[1] in {"2", "3", "6", "7"}]
assert len(_post_b) == 4 and all(ln.count("effective=4") == 3 and ln.count("smp=4") == 3 for ln in _post_b), _post_b  # text: effective affinity 4 after each B block
_pre_b = [ln for ln in _pr if ln.startswith("block ") and " cond B " in ln]
assert len(_pre_b) == 4 and all(ln.count("effective=4") == 3 for ln in _pre_b), _pre_b
assert "irqbalance now: inactive" in E2B["progress"] and _pr[-1].startswith("irqbalance now: active") and "smp=0-7" in _pr[-1] and "smp=0-7" in _pr[-2]
# E2c: 12 blocks all realized, 1050 x 63 interrupts each, pinned interrupt CPU read back as effective affinity, and the pre-written validity check failed on C
assert [b["cond"] for b in E2C["blocks"].values()] == list("ABCEFGGFECBA") and all(b["realized"] for b in E2C["blocks"].values())
assert all(b["irq_total"] == 1050 * 63 for b in E2C["blocks"].values())
_tgt = {"A": "0", "B": "4", "C": "0", "E": "0", "F": "4", "G": "0"}
_c_pre = [ln for ln in E2C["progress"].splitlines() if ln.startswith("block ") and " cond " in ln and "post readback" not in ln]
assert len(_c_pre) == 12 and all(ln.count(f"effective={_tgt[ln.split()[3]]}") == 3 for ln in _c_pre), _c_pre
assert E2C["progress"].splitlines()[-1].startswith("irqbalance now: active") and "smp=0-7" in E2C["progress"].splitlines()[-1]
assert E2C["checks"] == {"a_has_slow": True, "b_lost": True, "c_lost": False} and not E2C["valid"] and E2C["primary"]["C"] == "lẫn lộn"
assert max(b["slow"] for b in E2C["blocks"].values() if b["cond"] == "C") == 0.012 and all(b["slow"] <= 0.004 for b in E2C["blocks"].values() if b["cond"] in "EF")  # text: C 1.2 percent, E and F at most 0.4 percent
assert all(b["slow"] > 0.8 for b in E2C["blocks"].values() if b["cond"] == "G")  # text: G 82 and 87 percent
# E2d: 40 blocks all realized, 1050 x 63 interrupts each, interrupt CPU read back for every block, validity passed, results quoted in the text
assert len(E2D["blocks"]) == 40 and all(b["realized"] and b["irq_total"] == 1050 * 63 for b in E2D["blocks"].values()) and E2D["valid"]
_d_pre = [ln for ln in E2D["progress"].splitlines() if ln.startswith("block ") and " cond " in ln and "post readback" not in ln]
assert len(_d_pre) == 40 and all(ln.count("effective=" + ("0" if ln.split()[3] == "A" else ln.split()[3][3])) == 3 for ln in _d_pre), "E2d readback"
assert E2D["progress"].splitlines()[-1].startswith("irqbalance now: active") and "smp=0-7" in E2D["progress"].splitlines()[-1]
assert E2D["S0"] == [1, 2, 3] and E2D["S4"] == [] and E2D["other0"] == [] and E2D["other4"] == [] and E2D["non_replication_e2c"] == []
assert E2D["F"] == ["a4i4", "a5i4", "a6i4", "a7i4", "a5i5", "a6i6", "a7i7"], E2D["F"]
assert abs(E2D["blocks"]["7"]["fast"] - 0.663) < 1e-9 and abs(E2D["blocks"]["34"]["fast"] - 0.079) < 1e-9  # text: a5i0 blocks disagree on the fast share
_cells = {}
for _b in E2D["blocks"].values():
    _cells.setdefault(_b["cond"], []).append(_b)
assert all(len(v) == 2 for v in _cells.values()) and len(_cells) == 20
_m4 = [b["median"] for c in ("a4i0", "a5i0", "a6i0", "a7i0") for b in _cells[c] if b["block"] != 7]
_m3 = [b["median"] for c in ("a0i4", "a1i4", "a2i4", "a3i4") for b in _cells[c]]
assert len(_m4) == 7 and 18.85 < min(_m4) and max(_m4) < 18.89 and len(_m3) == 8 and 18.70 < min(_m3) and max(_m3) < 19.39  # text: 18.86 to 18.88, 18.71 to 19.38
assert E2D["blocks"]["7"]["median"] < 16.7
assert min(b["median"] for c in ("a1i0", "a2i0", "a3i0") for b in _cells[c]) > 21.5 and max(b["median"] for c in ("a1i0", "a2i0", "a3i0") for b in _cells[c]) < 21.8  # text: 21.5 to 21.8 ms
_a_cpu = {}
for _b in E2B["blocks"].values():
    if _b["cond"] == "A":
        for _c, (_sl, _n) in _b["slow_by_app_cpu"].items():
            _a_cpu[_c] = [_a_cpu.get(_c, [0, 0])[0] + _sl, _a_cpu.get(_c, [0, 0])[1] + _n]
assert _a_cpu["4"][0] == 0 and _a_cpu["5"][0] == 0 and _a_cpu["0"][0] < 10, _a_cpu  # text: slow runs end on CPU1 to CPU3 only (CPU0 almost none)

# Page 14: E2e, the eval_perf / rknn_server path
E2E = O["e2e"]
_eb = E2E["blocks"]
assert len(_eb) == 14 and all(b["realized"] and b["allowed_ok"] and b["n"] == 500 for b in _eb.values())
_tgt_e = {"A": "0", "s4i4": "4", "s0i0": "0", "s4i0": "0", "s0i4": "4", "s1i0": "0", "s1i4": "4"}
_e_start = [ln for ln in E2E["progress"].splitlines() if " block " in ln and " cond " in ln]
assert len(_e_start) == 14 and all(ln.count("effective=" + _tgt_e[ln.split()[4]]) == 3 for ln in _e_start), "E2e readback"
assert E2E["progress"].splitlines()[-1].split(" ", 1)[1].startswith("exit: irqbalance now active"), E2E["progress"].splitlines()[-1]
assert all(c["verdict"] == "cùng kết quả" for c in E2E["comparison"].values()) and E2E["same_all"] and not E2E["uniform_offset"]
assert sum(1 for b in _eb.values() if b["busy_name"] == "listener") == 8 and sum(1 for b in _eb.values() if b["busy_name"] == "rknn_server") == 6
assert all(b["tasks"] == 10 for b in _eb.values())
assert all(b["irq_total"] == 550 * 63 for b in _eb.values())  # 50 warm-up + 500 timed calls, one inference each
_s40 = [b["std_ms"] for b in _eb.values() if b["cond"] == "s4i0"]
assert 0.36 < min(_s40) < 0.37 and 0.43 < max(_s40) < 0.44 and all(b["mid"] >= 0.996 for b in _eb.values() if b["cond"] == "s4i0")
_dmin = min(c["diff_ms"] for c in E2E["comparison"].values())
_dmax = max(c["diff_ms"] for c in E2E["comparison"].values())
assert -1.21 < _dmin < -1.19 and 0.28 < _dmax < 0.30
assert all(c["diff_ms"] < -0.8 for k, c in E2E["comparison"].items() if k in ("s0i0", "s0i4", "s1i0", "s1i4")) and all(c["diff_ms"] > 0 for k, c in E2E["comparison"].items() if k in ("s4i4", "s4i0"))
assert all(" userspace userspace" in ln for ln in _e_start), "governor text"
_init = [float(ln.split("init_runtime ")[1].split(" s")[0]) for ln in E2E["driver_log"].splitlines()]
assert len(_init) == 14 and min(_init) == 0.94 and max(_init) == 4.64
assert max(b["slow"] for b in _eb.values() if b["cond"] in ("s4i4", "s0i0", "s4i0", "s0i4", "s1i4")) == 0.0 and min(b["slow"] for b in _eb.values() if b["cond"] == "s1i0") > 0.85

# cell (4, 4): app (or rknn_server) and NPU interrupts on CPU4, in every run after E2
_c44 = [("E2b", b) for b in E2B["blocks"].values() if b["cond"] == "B"] + [("E2c", b) for b in E2C["blocks"].values() if b["cond"] == "B"] \
    + [("E2d", b) for b in E2D["blocks"].values() if b["cond"] == "a4i4"] + [("E2e", b) for b in E2E["blocks"].values() if b["cond"] == "s4i4"]
assert len(_c44) == 10 and all(b["slow"] == 0 for _, b in _c44)  # text: no slow run at (4, 4) in E2b, E2c, E2d, E2e
_c44_capi = [b for n, b in _c44 if n != "E2e"]
assert min(b["fast"] for b in _c44_capi) >= 0.985 and 16.28 < min(b["median"] for b in _c44_capi) and max(b["median"] for b in _c44_capi) < 16.33
assert max(b["std_ms"] for b in _c44_capi) < 0.27 and sorted(b["std_ms"] for b in _c44_capi)[-2] < 0.05  # text: one block at 0.26 ms, the others at most 0.04 ms
assert abs(E2E["comparison"]["s4i4"]["diff_ms"] - 0.279) < 0.002
assert gap["gap2s"]["median"] < 20000 and gap["gap10s"]["median"] < 20000
assert e1["session_median_gap"] < 0.01 and min(s_["range"] for s_ in e1["sessions"]) > 0.10
_first = [x["latency_first"] < x["latency_rest_median"] for x in L["first_vs_rest"]] + [s_["first"] < s_["rest_median"] for s_ in e1["sessions"]]
assert len(_first) == 5 and all(_first)  # text: the first call is lower in all 5 latency sessions

docs = {"02": [], "03": [], "04": [], "05": []}
w = docs["02"].append
w("""****************************
Kết quả latency từng khối
****************************

.. admonition:: Trang này trả lời

   - Latency NPU của YOLOv8n INT8 (``ppe5``, ``nc=5``) ở ``CORE_0`` trên RK3588 là bao nhiêu, và vì sao con số dao động?
   - Mỗi khối L0 đến L22 chiếm bao nhiêu thời gian, và tỉ lệ đó tin được đến đâu?
   - Điều gì đã kiểm chứng, điều gì chưa biết?
""")
w(f""".. admonition:: Tóm tắt

   - Latency không phải một con số. Qua ``eval_perf`` từ PC, trung vị các phiên là {', '.join(f(x['npu_latency_ms'], 2) for x in [b2] + b3)} ms (B2 và ba phiên B3), và {', '.join(f(s['median'], 2) for s in e1['sessions'])} ms (hai phiên E1). Đo ngay trên board bằng C API (không qua đường truyền), ba đợt 1000 lần chạy liên tiếp có trung vị {', '.join(f(hot[str(n)]['median'] / 1000, 2) for n in (1, 2, 3))} ms, từng lần chạy từ {f(min(min(v) for v in hot_csv.values()), 1)} đến {f(max(max(v) for v in hot_csv.values()), 1)} ms. Cổng A5 (chênh giữa các phiên không quá 5%) không đạt: {pct(S['latency_gap'], 2)}.
   - Vì sao latency dao động và các giả thuyết đã kiểm nằm ở :doc:`04-cac-muc-do-tre`, thí nghiệm ghim CPU và ngắt NPU ở :doc:`05-thu-ghim-cpu-va-ngat`, phân tích từng dòng (Conv, op khác Conv, DFL, hằng số mỗi dòng) ở :doc:`03-phan-tich-sau-latency-tung-khoi`.
   - Tỉ lệ thời gian giữa các khối ổn định hơn latency tuyệt đối. Giữa năm nguồn (``eval_perf`` B3, B2 và ba cách tính trên board), tỉ lệ một khối từ 2% thời gian trở lên chênh tối đa {f(share_pp, 1)} điểm phần trăm. Khối Detect (L22) chiếm {pct(l22['share'], 1)} ({pct(l22['b2_share'], 1)} ở B2), backbone L0 đến L9 chiếm {pct(bb_share, 1)} (cộng khối trong từng lần gọi rồi lấy trung vị, như bảng 1).
   - Cổng chấp nhận: {', '.join(x['code'] for x in A['checks'] if x['ok'])} đạt, {', '.join(x['code'] for x in A['checks'] if not x['ok'])} không đạt. FP16 chưa chạy theo giao thức gốc vì cổng A8 của INT8 không đạt (đã chạy dưới P2 ngày 2026-10-31, :doc:`07-giao-thuc-p2-va-do-mo-rong`, mục 6).

.. contents:: Trong trang này
   :local:
   :depth: 1
""")

# ---------------------------------------------------------------- 1
w("""1. Dữ liệu và điều kiện đo
==========================

Model: ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/weights/rknn_int8/best-rk3588.rknn``, sha256 ``a501f94e`` (cùng file trên PC và trên board), RKNN-Toolkit2 2.3.2, ``rknn_server`` và runtime 2.3.2, driver ``rknpu`` 0.9.8. ``CORE_0``. CPU ở 1.8, 2.256 và 2.304 GHz, NPU 1.0 GHz, DDR 2.112 GHz, khoá bằng ``lock_freq.sh lock``. Kế hoạch và định nghĩa từng thông số nằm ở :doc:`01-ke-hoach-do`.
""")
w(table(["Nguồn", "Cách đo", "Mẫu", "File"], [
    ["B2", "``eval_perf`` từ PC, phiên latency và phiên từng lớp, thêm một phiên bộ nhớ", "5 lần gọi mỗi phiên", "``bench/tier1_int8_CORE_0*``"],
    ["B3", "Ba phiên độc lập như B2, bỏ phiên bộ nhớ", "3 phiên x 5 lần gọi", "``bench/tier1_int8_CORE_0_sess{1,2,3}*``"],
    ["Probe", "Hai lần ``eval_perf`` ở chế độ debug, phiên đầu tiên sau khi khởi động lại ``rknn_server``", "2 lần gọi", "``bench/extra_probe_debug_*``"],
    ["E1", "Hai phiên ``eval_perf`` (``perf_debug=False``), 20 lần gọi mỗi phiên, kèm tần số in ra từng lần và bộ lấy mẫu 1 Hz trên board", "2 x 20", "``bench/extra_e1_*``"],
    ["Trên board, đợt liên tiếp", "``ai/board/rknn_perf_bench.c`` (C API, không qua PC), 3 tiến trình, 50 lần khởi động rồi 1000 lần chạy", "3 x 1000", "``bench/onboard/hot_*.csv``"],
    ["Trên board, ``detail``", "Cùng chương trình với ``RKNN_FLAG_COLLECT_PERF_MASK`` và ``RKNN_QUERY_PERF_DETAIL``, bảng từng lớp mỗi lần chạy", "3 x 200", "``bench/onboard/detail_*_detail.txt``"],
    ["Trên board, nghỉ giữa các lần chạy", "Nghỉ 2 giây và 10 giây sau mỗi lần ``rknn_run``", "40 và 20", "``bench/onboard/gap*.csv``"],
    ["E2 đến E2e", "Thử ghim CPU, ngắt NPU và tắt trạng thái ngủ, năm thí nghiệm (:doc:`05-thu-ghim-cpu-va-ngat`)", "8 đến 40 khối mỗi thí nghiệm", "``bench/onboard_e2*/*``"],
], [18, 46, 16, 20]))
w("""
Mọi bảng dưới đây sinh tự động bằng ``docs/tools/gen_latency_results_page.py`` từ ``results/latency_per_block_*.json``, ``results/layer_analysis_*.json``, ``results/onboard_*.json`` và các file ở cột "File". Thời gian từng lớp luôn là thời gian ở chế độ ``perf_debug=True`` (hoặc ``detail``), hãng ghi chế độ này có thể tắt một số cơ chế song song [T1 UG232 tr.177]. Vì vậy các con số từng khối dùng để so sánh với nhau, không cộng thành latency.
""")

# ---------------------------------------------------------------- 2
w("""2. Latency tổng
===============
""")
w(table(["Nguồn", "Trung vị (ms)", "Nhỏ nhất đến lớn nhất (ms)", "Số mẫu", "Ghi chú"], lat_rows, [26, 14, 24, 10, 26]))
w(f"""
Quan sát (T3 board, ``results/latency_per_block_*.md``, ``results/onboard_*.md``):

- Cùng một ``.rknn``, cùng tần số khoá, trung vị các phiên ``eval_perf`` lệch nhau {pct(S['latency_gap'], 2)} giữa B3 phiên 1, 2 và 3. Cổng A5 yêu cầu không quá 5%, không đạt.
- Hai nguồn đo khác nhau về bản chất và mức của chúng không trùng nhau. ``eval_perf`` lấy thời gian từ phần cứng board [T1 API232 tr.18], còn thời gian trên board là đồng hồ CPU quanh ``rknn_run``. Ở chương trình C, ``wall_us`` và ``RKNN_QUERY_PERF_RUN`` bằng nhau trong 5 µs ở mọi lần chạy ({O['hot_wall_equals_perf_run']}), nên số này gồm cả phần driver. Quan hệ giữa hai nguồn chưa biết. Thử giãn nhịp chạy C API (X3) cho kết quả "chưa kết luận" về việc nhịp gọi có giải thích chênh lệch hay không (:doc:`06-co-che-cac-muc-do-tre`, mục 4).
- Tổng debug ở B2 ({f(b2['debug_total_us'] / 1000, 2)} ms) thấp hơn latency ({f(b2['npu_latency_ms'], 2)} ms). Ở B3 tổng debug là {', '.join(f(r['debug_total_us'] / 1000, 2) for r in b3)} ms, cao hơn latency. Hãng ghi ``perf_debug=True`` làm thời gian lớn hơn [T1 UG232 tr.177]. Quan sát ở B2 ngược câu đó, nguyên nhân chưa biết (trên LAN, tổng debug thấp hơn latency ở 4/10 phiên không ghim và 0/10 phiên ghim, :doc:`07-giao-thuc-p2-va-do-mo-rong`, mục 3), và câu của hãng có thể nói về đại lượng khác (chưa kiểm).
- Cần báo latency như một khoảng kèm số mẫu và nguồn. Với model này ở ``CORE_0`` INT8, các nguồn trên cho trung vị từ {f(min(statistics.median(hot_csv[n]) for n in hot_csv), 1)} đến {f(max(r['npu_latency_ms'] for r in b3), 1)} ms và từng lần chạy từ {f(min(min(v) for v in hot_csv.values()), 1)} đến {f(max(max(v) for v in hot_csv.values()), 1)} ms.
""")

# ---------------------------------------------------------------- 3
w = docs["04"].append
w(f"""**********************
Các mức độ trễ của NPU
**********************

.. admonition:: Trang này trả lời

   - Vì sao latency NPU của cùng một model, cùng tần số khoá, lại dao động từ khoảng 16 đến 22 ms?
   - Các giả thuyết nào đã được kiểm bằng phép đo, kết quả (ủng hộ, không ủng hộ, chưa kết luận) và giới hạn ra sao?

.. admonition:: Tóm tắt

   - Dao động có cấu trúc: độ trễ tập trung ở ba mức chính (còn {n_trans} lần chạy, {pct(n_trans / len(all_hot), 0)}, nằm giữa mức nhanh và mức giữa), trung vị {f(mid['fast'], 2)}, {f(mid['mid'], 2)} và {f(mid['slow'], 2)} ms, cách nhau {f(E2['gap_us']['mid_minus_fast'] / 1000, 2)} ms và {f(E2['gap_us']['slow_minus_mid'] / 1000, 2)} ms. Mỗi lần chạy có {f(E2['irq_per_run'], 0)} ngắt NPU, nên mỗi khoảng cách ứng với khoảng {f(E2['gap_us_per_interrupt']['mid_minus_fast'], 0)} µs mỗi ngắt (chỉ là kiểm tra nhất quán, không phải cơ chế).
   - NPU khởi động nguội: không ủng hộ (nghỉ 2 và 10 giây giữa các lần chạy cho trung vị {f(gap['gap2s']['median'] / 1000, 2)} và {f(gap['gap10s']['median'] / 1000, 2)} ms, không chạm mức chậm). Xung nhịp hoặc băng thông DDR đổi: không ủng hộ (hệ số theo cycles của Conv giữ ở {f(min(v['slope'] for v in fits.values()), 3)} đến {f(max(v['slope'] for v in fits.values()), 3)}). Bộ đếm ``cpuidle``: chưa kết luận. Vị trí CPU và ngắt NPU được kiểm riêng ở :doc:`05-thu-ghim-cpu-va-ngat`.
   - Trong một phiên ``eval_perf`` (E1), trung vị hai phiên chỉ lệch {pct(e1['session_median_gap'], 2)} nhưng mỗi phiên trải {pct(min(s_['range'] for s_ in e1['sessions']), 0)} đến {pct(max(s_['range'] for s_ in e1['sessions']), 0)}. Lần gọi đầu thấp hơn các lần sau ở cả 5 phiên latency qua relay. Đính chính ngày 2026-10-31: trên LAN, 10 phiên mỗi giao thức cho kết quả \"không ổn định\" (:doc:`07-giao-thuc-p2-va-do-mo-rong`, mục 3).

Kết quả latency và tỉ lệ từng khối nằm ở :doc:`02-ket-qua-latency-tung-khoi`. Phân tích sâu từng khối nằm ở :doc:`03-phan-tich-sau-latency-tung-khoi`. Thí nghiệm ghim CPU và ngắt NPU (E2 đến E2e) nằm ở :doc:`05-thu-ghim-cpu-va-ngat`. Quy ước nhãn, dùng cho trang này và :doc:`05-thu-ghim-cpu-va-ngat`: "ủng hộ", "không ủng hộ" hoặc "chưa kết luận". Không có nhãn nào ở đây là kết luận về cơ chế.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Ba mức độ trễ
================
""")
w(f"""Ba đợt 1000 lần chạy liên tiếp trên board cho ba mức chính cùng một số lần chạy ở giữa: {n_trans} trên {len(all_hot)} lần ({pct(n_trans / len(all_hot), 1)}) nằm trong khoảng 17.0 đến 18.5 ms, giữa mức nhanh và mức giữa. Ngưỡng mức đọc từ chỗ lõm của biểu đồ gộp 3000 lần chạy (khoảng 0.25 ms): dưới 17.0 ms là mức nhanh, từ 20.0 ms là mức chậm, ở giữa là mức giữa. Trung vị của từng mức trên toàn bộ 3000 lần chạy: nhanh {f(mid['fast'], 3)}, giữa {f(mid['mid'], 3)}, chậm {f(mid['slow'], 3)} ms.
""")
w(table(["Đợt", "Trung vị (ms)", "p95 (ms)", "CV", "Mức nhanh", "Mức giữa", "Mức chậm", "Đoạn dài nhất cùng mức (lần chạy)", "Tự tương quan lần kề"],
        [[n, f(hot[str(n)]["median"] / 1000, 3), f(hot[str(n)]["p95"] / 1000, 3), pct(hot[str(n)]["cv"], 1), pct(levels[str(n)]["fast"], 1), pct(levels[str(n)]["mid"], 1),
          pct(levels[str(n)]["slow"], 1), levels[str(n)]["longest_run_same_level"], f(levels[str(n)]["lag1_autocorr"], 2)] for n in (1, 2, 3)], [8, 12, 10, 8, 11, 11, 11, 17, 12]))
w(f"""
Độ trễ giữ nguyên một mức trong hàng chục đến hàng trăm lần chạy liên tiếp rồi mới nhảy, nên dao động này không phải nhiễu độc lập giữa các lần. Do đó một phiên ``eval_perf`` 5 lần gọi chỉ lấy mẫu mức mà board đang ở lúc đó. Đó là một giải thích khả dĩ cho việc cổng A5 không đạt, chưa kiểm: các lần chạy liên tiếp trên board cách nhau khoảng 19 ms, còn các lần gọi ``eval_perf`` qua relay cách nhau khoảng 35 giây, E2 đến E2d chạy trên đường C API và E2e chạy trên đường ``eval_perf`` (:doc:`05-thu-ghim-cpu-va-ngat`), và ở E1 hai trung vị phiên chỉ lệch {pct(e1['session_median_gap'], 2)}.

2. NPU có bận khi đo trên board
===============================

Trong đợt 1, mỗi 0.1 giây đọc ``/sys/kernel/debug/rknpu/power`` và ``load``: {act['samples']} mẫu, nguồn NPU bật ở {act['power_on']} mẫu ({pct(act['power_on_share'], 1)}), tải ``Core0`` trung vị {act['core0_load_median']:.0f}%, lớn nhất {act['core0_load_max']:.0f}%. Theo mã driver ``rknpu`` 0.9.8, giá trị ``load`` là phần trăm thời gian NPU bận trong cửa sổ 1 giây gần nhất đã kết thúc: ``RKNPU_LOAD_INTERVAL`` là 1000000000 ns (``3rdparty/rknpu-driver-0.9.8/include/rknpu_drv.h:40``), một hrtimer cộng thời gian bận rồi chốt mỗi 1 giây (``rknpu_drv.c:747-787``), và giá trị in ra là thời gian bận chia 1e7, chặn ở 100 (``rknpu_debugger.c:60-66``) [T1 mã nguồn]. Vì vậy các mẫu 0.1 giây ở đây lặp lại cùng một giá trị trong mỗi giây, và ``load`` không dùng được cho tải ngắn hơn 1 giây. Ngược lại, ở E1 mỗi lần ``eval_perf`` qua PC mất trung vị {f(e1['sessions'][0]['wall_s_median'], 1)} và {f(e1['sessions'][1]['wall_s_median'], 1)} giây thực (``init_runtime`` {f(e1['sessions'][0]['init_s'], 0)} và {f(e1['sessions'][1]['init_s'], 0)} giây), trong khi NPU chạy một khung chỉ khoảng 19 ms. Lúc đo E1 (ngày 2026-10-30), đường PC đến board đi qua relay Tailscale với RTT 159 đến 269 ms và adb đẩy file 0.1 MB/s (``bench/extra_link_facts.txt``). Đo lại trên LAN trực tiếp với cùng board và cùng model (``bench/extra_tier1_lan_timing.txt``, chỉ ghi thời gian chờ): ``init_runtime`` {f(_lan['init'], 1)} giây và mỗi lần ``eval_perf`` {f(min(_lan['calls']), 2)} đến {f(max(_lan['calls']), 2)} giây. Phép đo LAN chỉ ghi thời gian chờ, không ghi giá trị latency. Thời gian chờ mỗi lần gọi giảm từ khoảng 35 đến 57 giây xuống dưới 0.5 giây khi đổi đường truyền, trong khi số đo NPU của E2e (trung vị các khối {f(_e2e_lo, 1)} đến {f(_e2e_hi, 1)} ms) và của E1 (trung vị hai phiên {f(min(s_['median'] for s_ in e1['sessions']), 1)} và {f(max(s_['median'] for s_ in e1['sessions']), 1)} ms) cùng cỡ, nên phần lớn thời gian mỗi lần gọi qua relay là phần đường truyền và phía PC, đúng như suy luận trước đây. Số gói trao đổi vẫn chưa đếm.

3. Các giả thuyết đã kiểm
=========================

3.1. NPU khởi động nguội giữa các lần chạy
------------------------------------------
""")
w(table(["Điều kiện", "Số lần chạy", "Trung vị (ms)", "Nhỏ nhất", "Lớn nhất", "Lần chạy đầu (µs)", "CV"],
        [[k, v["n"], f(v["median"] / 1000, 3), f(v["min"] / 1000, 3), f(v["max"] / 1000, 3), v["values"][0], pct(v["cv"], 1)] for k, v in gap.items()], [14, 12, 14, 12, 12, 16, 10]))
w(f"""
Nghỉ 2 và 10 giây giữa các lần chạy (trong cùng một tiến trình) không làm lần chạy chậm hơn: trung vị {f(gap['gap2s']['median'] / 1000, 2)} và {f(gap['gap10s']['median'] / 1000, 2)} ms, nằm trong mức giữa, và lần chạy đầu sau nghỉ 10 giây là {f(gap['gap10s']['values'][0] / 1000, 2)} ms. Hai điều kiện này cũng không bao giờ chạm mức chậm. **Nhãn: không ủng hộ** giả thuyết khởi động nguội gây mức chậm (nghỉ lâu không chậm hơn).
""")
w = docs["05"].append
w(f"""************************
Thử ghim CPU và ngắt NPU
************************

.. admonition:: Trang này trả lời

   - Ghim tiến trình đo và ngắt NPU vào CPU nào thì mức chậm biến mất, và ở đâu latency ổn định ở mức nhanh (E2 đến E2d, đường C API trên board)?
   - Khi ghim ``rknn_server`` và ngắt NPU vào các CPU, thời gian ``eval_perf`` qua ``rknn_server`` có cho cùng kết quả vị trí như đường C API trên board không?
   - Hai đường chênh nhau bao nhiêu ở cùng một ô (mô tả)?

.. admonition:: Tóm tắt

   - Mức chậm chiếm {pct(E2['blocks']['b1_A']['slow'], 0)} và {pct(E2['blocks']['b8_A']['slow'], 0)} số lần chạy ở điều kiện mặc định (tiến trình tự chuyển lõi), và còn không quá {pct(max(b['slow'] for b in E2['blocks'].values() if b['cond'] != 'A'), 1)} ở cả sáu khối thử ghim lõi hoặc tắt ``cpu-sleep``. E2b (chạy lại B với ``irqbalance`` dừng) thực hiện đúng ở cả {len(E2B['realized'])} khối B: không có lần chạy chậm, trung vị {f(min(b['median'] for b in E2B['blocks'].values() if b['cond'] == 'B'), 2)} đến {f(max(b['median'] for b in E2B['blocks'].values() if b['cond'] == 'B'), 2)} ms, độ lệch chuẩn {f(max(b['std_ms'] for b in E2B['blocks'].values() if b['cond'] == 'B'), 3)} ms hoặc nhỏ hơn, nhãn B là "{E2B['label']}" (chỉ nghĩa là mức chậm biến mất, ba yếu tố đổi cùng lúc, cách ghép khối A được chọn sau khi có dữ liệu và cách ghép từng khối liền kề cho "chưa kết luận"). E2c tách vị trí ứng dụng và ngắt nhưng không đọc được yếu tố vì kiểm tra hợp lệ viết trước không đạt. E2d (bản đồ 20 điều kiện, quy tắc viết trước, kiểm tra hợp lệ đạt) cho thấy: với ngắt ở CPU0, mức chậm chỉ có khi ứng dụng ghim ở CPU1 đến CPU3, với ngắt ở CPU4 không CPU ứng dụng nào có mức chậm, và mức nhanh ổn định (quanh 16.3 ms) đạt ở bảy ô đã thử: ứng dụng ở CPU4 đến CPU7 với ngắt ở CPU4, cùng (5, 5), (6, 6), (7, 7), còn không ô nào có ngắt ở CPU0 hoặc ứng dụng ở CPU0 đến CPU3 đạt. Đây là phát biểu về vị trí trong các ô đã thử, không phải cơ chế. Đây là quan sát gắn với các yếu tố thực tế của từng khối, cơ chế chưa kết luận.
   - Cả sáu ô đã thử cho cùng kết quả vị trí với đường C API của E2d (cả kết quả chính lẫn kết quả mức nhanh). Ô (4, 4) mất mức chậm và đạt mức nhanh (trung vị {f(E2E['comparison']['s4i4']['median_e2e'], 2)} ms), ô (1, 0) còn mức chậm ({pct(min(b['slow'] for b in _eb.values() if b['cond'] == 's1i0'), 1)} đến {pct(max(b['slow'] for b in _eb.values() if b['cond'] == 's1i0'), 1)} lần chạy chậm), bốn ô còn lại mất mức chậm và không đạt mức nhanh.
   - Hiệu trung vị (``eval_perf`` trừ C API) không cùng dấu ở sáu ô ({', '.join(f"{c['diff_ms']:+.2f}" for c in E2E['comparison'].values())} ms), nên ngoại lệ lệch mức đồng đều của quy tắc không áp dụng.
   - X6 thử thêm bảy ô CPU lớn trên đường ``eval_perf``: cả bảy cho cùng kết quả vị trí với đường C API (mục 6.4).
   - Đây là phát biểu về vị trí trong sáu ô đã thử, không phải cơ chế.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Cơ sở và cách đọc nhãn
=========================

Quy ước nhãn và ngưỡng ba mức độ trễ nằm ở :doc:`04-cac-muc-do-tre` (mục 1).

Cơ sở T1: mục "5.3.3 Multi-Core Performance Improvement Tips" của UG232 ghi để chạy đa nhân nhanh hơn có thể thử: "Bind the application to the CPU big core" và "Bind the NPU interrupt to the corresponding CPU big core above", kèm ví dụ ``taskset 10`` cho CPU4 [T1 UG232 tr.75]. Hướng dẫn này viết cho NPU đa nhân và lõi CPU lớn, còn E2 chạy ``CORE_0`` và thử cả lõi nhỏ CPU0. Ba dòng ngắt NPU (irq 36, 37 và 38) có affinity mặc định ``0-7``. Trong các khối của E2 chỉ irq 36 có đếm ngắt, và khi không ghim toàn bộ rơi vào CPU0 (một lõi nhỏ), còn tiến trình tự chuyển giữa nhiều lõi.

2. E2: bốn điều kiện
====================

E2 chạy bốn điều kiện dự định (A mặc định, B ứng dụng và ngắt NPU cùng CPU4, C cùng CPU0, D tắt trạng thái ``cpu-sleep``: script ghi 1 vào ``state1/disable`` của mọi CPU, và chỉ đọc lại CPU0), mỗi khối 1000 lần chạy, thứ tự ABCD rồi DCBA, và khôi phục ngắt và ``cpuidle`` sau cùng (đã đọc lại trên board xác nhận ngắt về ``0-7`` và ``cpu-sleep`` bật lại). Điều kiện B ở khối 2 **không thực hiện đúng**: {pct(E2['blocks']['b2_B']['irq_top_share'], 0)} ngắt NPU vẫn rơi vào CPU0, chỉ {E2['blocks']['b2_B']['irq_delta'][4]} ngắt rơi vào CPU4, khoảng {E2['blocks']['b2_B']['irq_delta'][4] / E2['irq_per_run']:.0f} lần chạy với {f(E2['irq_per_run'], 0)} ngắt mỗi lần chạy. Cửa sổ 100 lần chạy đầu của khối có trung vị {f(E2['blocks']['b2_B']['windows_100'][0], 2)} ms rồi chuyển sang {f(E2['blocks']['b2_B']['windows_100'][1], 2)} ms. Trên board có ``irqbalance`` đang chạy. Việc ``irqbalance`` trả ngắt về CPU0 là suy đoán nhất quán với dữ liệu, chưa kiểm. Đính chính ngày 2026-10-31: X9 lặp lại điều kiện B với ``irqbalance`` đang chạy, ba lần, mỗi lần 3000 lần chạy liên tiếp, log mỗi giây ghi được {min(t['samples'] for t in _x9['trials'])} đến {max(t['samples'] for t in _x9['trials'])} mẫu. Ở lần thứ nhất, trong khoảng 1 giây affinity của ngắt 36 bị đổi từ CPU4 về ``0-7`` và {pct(1 - _x9['trials'][0]['cpu4_share'], 0)} ngắt rơi vào CPU0, hai lần sau giữ CPU4 (``bench/onboard_x9/``, quy tắc viết trước). Vậy ``irqbalance`` có đổi affinity trong lúc chạy, đã quan sát ở 1 trên 3 lần. Vì vậy bảng dưới phân loại theo yếu tố thực tế.
""")
w(table(["Khối", "Dự định", "Thứ tự", "Trung vị (ms)", "p95 (ms)", "CV", "Mức nhanh", "Mức giữa", "Mức chậm", "CPU của ứng dụng", "CPU nhận nhiều ngắt NPU nhất", "Tắt cpu-sleep"],
        [[b["block"], b["cond"], b["order"], f(b["median"], 3), f(b["p95"], 3), pct(b["cv"], 1), pct(b["fast"], 1), pct(b["mid"], 1), pct(b["slow"], 1), b["app_cpu"],
          f"{b['irq_cpu']} ({pct(b['irq_top_share'], 0)})", "có" if b["state1_off"] else "không"] for b in E2["blocks"].values()],
        [6, 8, 8, 10, 9, 7, 9, 9, 9, 12, 14, 9]))
w("""
Trung vị mỗi 100 lần chạy (ms), để thấy mức đổi theo thời gian trong khối:
""")
w(table(["Khối"] + [f"{i * 100} đến {i * 100 + 99}" for i in range(10)],
        [[f"{b['block']} ({b['cond']})"] + [f(x, 2) for x in b["windows_100"]] for b in E2["blocks"].values()], [10] + [9] * 10))
w("""
Gom các khối theo yếu tố thực tế (vị trí ứng dụng, nơi nhận nhiều ngắt nhất, trạng thái ``cpu-sleep``):
""")
w(table(["Ứng dụng", "Ngắt NPU", "Tắt cpu-sleep", "Khối", "Trung vị (ms)", "Mức chậm"],
        [[x["app"], x["irq"], "có" if x["state1"] == "off" else "không", ", ".join(str(b) for b in x["blocks"]), ", ".join(f(m, 2) for m in x["medians"]),
          ", ".join(pct(s, 1) for s in x["slow"])] for x in E2["classes"]], [16, 18, 14, 12, 18, 18]))
vd = E2["verdict"]
w(f"""
Quan sát chính (n nhỏ, mỗi nhóm hai khối hoặc một khối, nên chỉ là liên hệ tạm):

- Mức chậm xuất hiện ở hai khối mặc định của E2 ({pct(E2['blocks']['b1_A']['slow'], 0)} và {pct(E2['blocks']['b8_A']['slow'], 0)}, đã ghi vị trí thực tế: tiến trình chuyển lõi, ngắt ở CPU0, ``cpu-sleep`` bật) và ở cả ba đợt liên tiếp (:doc:`04-cac-muc-do-tre`, mục 1, {pct(min(levels[str(n)]['slow'] for n in (1, 2, 3)), 0)} đến {pct(max(levels[str(n)]['slow'] for n in (1, 2, 3)), 0)}, chạy không ghim nhưng chưa ghi vị trí CPU từng lần chạy). Nó gần như vắng mặt (không quá {pct(max(b['slow'] for b in E2['blocks'].values() if b['cond'] != 'A'), 1)}) ở cả sáu khối can thiệp.
- Các nhóm có hai khối: mặc định (hai khối, mức chậm {pct(E2['blocks']['b1_A']['slow'], 0)} và {pct(E2['blocks']['b8_A']['slow'], 0)}), tắt ``cpu-sleep`` (D: {', '.join(f(x, 2) for x in E2['classes'][3]['medians'])} ms) và ứng dụng ghim CPU0 cùng ngắt ở CPU0 (C: {', '.join(f(x, 2) for x in E2['classes'][2]['medians'])} ms). Ứng dụng và ngắt cùng CPU4 chỉ có một khối ({f(E2['classes'][4]['medians'][0], 2)} ms), không báo thành "latency" của điều kiện này.
- Ngưỡng 17.0 ms của mức nhanh nằm sát mức của D ({f(E2['blocks']['b5_D']['median'], 2)} ms), nên tỉ lệ nhanh và giữa của D chỉ là hệ quả của ngưỡng. Báo D bằng trung vị.
- Giữa các khối cùng nhóm thực tế vẫn còn khác biệt nhỏ (D chuyển giữa 16.5 và 17.4 ms), và mức giữa so với mức nhanh khi can thiệp chưa giải thích được.

Nhãn theo quy tắc cố định trước khi có dữ liệu E2 (không từ nguồn nào): "ủng hộ" khi tỉ lệ mức chậm đổi hơn 0.20 cùng chiều ở cả hai thứ tự, "không ủng hộ" khi đổi dưới 0.10 ở cả hai. "Ủng hộ" ở đây chỉ nghĩa là can thiệp đó làm mất mức chậm, không xác định cơ chế.
""")
w(table(["Điều kiện dự định", "Đổi tỉ lệ mức chậm so với A (chỉ khối thực hiện đúng)", "Khối bị loại", "Nhãn"],
        [[f"{k}", ", ".join(f"{o}: {v['slow']:+.2f}" for o, v in x["shifts"].items()), ", ".join(str(b) for b in x["excluded_blocks"]) or "không", x["label"]] for k, x in vd.items()], [24, 34, 14, 28]))
w(f"""
Khối bị loại là khối không thực hiện đúng điều kiện dự định (khối 2 của B). Điều kiện B vì vậy chỉ còn khối 7 (thứ tự DCBA) và không gán được nhãn ở E2. Phần E2b ngay bên dưới chạy lại B với ``irqbalance`` dừng và gán được nhãn.

""")
w(f"""
Kiểm tra nhất quán, không phải cơ chế: mỗi lần chạy có {f(E2['irq_per_run'], 0)} ngắt NPU, hai khoảng cách giữa ba mức là {f(E2['gap_us']['mid_minus_fast'], 0)} và {f(E2['gap_us']['slow_minus_mid'], 0)} µs, tức {f(E2['gap_us_per_interrupt']['mid_minus_fast'], 0)} và {f(E2['gap_us_per_interrupt']['slow_minus_mid'], 0)} µs mỗi ngắt. Cùng cỡ với chi phí cố định mỗi dòng ở :doc:`03-phan-tich-sau-latency-tung-khoi` (mục 5). Trên board, ``cpu-sleep`` có độ trễ thoát 220 µs và thời gian nằm tối thiểu 1000 µs, ``WFI`` có độ trễ 1 µs (``bench/onboard_e2/board_facts.txt``). Con số 220 µs không bằng 40 µs, nên không dùng để khẳng định cơ chế.

**Nhãn cho các giả thuyết về CPU và ngắt: chưa kết luận về cơ chế.** Phép thử chỉ cho thấy liên hệ giữa mức chậm với việc CPU nhận ngắt NPU (CPU0) có thể vào ``cpu-sleep`` trong khi ứng dụng chạy ở lõi khác (E2d ngay bên dưới kiểm tra lại có đối chứng: ứng dụng ở CPU4 đến CPU7 với ngắt ở CPU0 không có mức chậm, nên kết quả đó không khớp với cách giải thích này). Chưa đo độ trễ từng ngắt. E2e (mục 6) chạy phép ghim cho đường ``eval_perf`` qua ``rknn_server`` và cho cùng kết quả vị trí trong sáu ô đã thử.

3. E2b: điều kiện B khi dừng ``irqbalance``
===========================================

Ở E2, khối 2 của B không thực hiện đúng vì 89% ngắt vẫn ở CPU0 trong khi ``irqbalance`` đang chạy, nên B không gán được nhãn. E2b chạy trên một lần khởi động khác của board (board được khởi động lại giữa hai lần, khóa tần số được áp lại bằng ``lock_freq.sh lock`` với governor ``performance``), dừng ``irqbalance`` suốt phép đo, rồi chạy tám khối thứ tự ABBA ABBA, mỗi khối 1000 lần sau 50 lần làm nóng. B so với các khối A của chính E2b, không so với E2. Quy tắc gán nhãn viết vào ``rule.txt`` trước khi có dữ liệu và dùng đúng điều kiện thực hiện đúng của E2 (ứng dụng chạy trên CPU4 và ít nhất 99% ngắt ở CPU4).
""")
w(table(["Khối", "Điều kiện", "Trung vị (ms)", "p95 (ms)", "Độ lệch chuẩn (ms)", "Mức nhanh", "Mức giữa", "Mức chậm", "CPU của ứng dụng", "CPU nhận nhiều ngắt NPU nhất"],
        [[b["block"], b["cond"], f(b["median"], 3), f(b["p95"], 3), f(b["std_ms"], 3), pct(b["fast"], 1), pct(b["mid"], 1), pct(b["slow"], 1),
          f"{b['app_cpu']} ({pct(b['app_top_share'], 0)})", f"{b['irq_cpu']} ({pct(b['irq_top_share'], 0)})"] for b in E2B["blocks"].values()],
        [6, 9, 10, 9, 10, 9, 9, 9, 16, 16]))
w(f"""
B thực hiện đúng ở cả {len(E2B['realized'])} khối B (kiểm bằng ``effective_affinity_list`` đọc lại sau mỗi khối và bằng số ngắt: mỗi khối đếm {E2B['blocks']['2']['irq_total']} ngắt NPU, bằng 1050 lần chạy nhân 63). Trong cả bốn khối B không có lần chạy nào ở mức chậm, trung vị {f(min(b['median'] for b in E2B['blocks'].values() if b['cond'] == 'B'), 2)} đến {f(max(b['median'] for b in E2B['blocks'].values() if b['cond'] == 'B'), 2)} ms và độ lệch chuẩn {f(min(b['std_ms'] for b in E2B['blocks'].values() if b['cond'] == 'B'), 3)} đến {f(max(b['std_ms'] for b in E2B['blocks'].values() if b['cond'] == 'B'), 3)} ms, so với {f(min(b['std_ms'] for b in E2B['blocks'].values() if b['cond'] == 'A'), 2)} đến {f(max(b['std_ms'] for b in E2B['blocks'].values() if b['cond'] == 'A'), 2)} ms ở các khối A. Các khối A vẫn dao động mạnh dù ``irqbalance`` đã dừng: mức chậm {', '.join(pct(b['slow'], 1) for b in E2B['blocks'].values() if b['cond'] == 'A')} ở bốn khối A.

Quy tắc ở ``rule.txt`` không nói cách ghép khối, và thứ tự ABBA lặp lại khiến mỗi nửa có hai khối A. Cách ghép được chọn **sau khi có dữ liệu** (``rule_note.txt``): trung bình hai khối A của mỗi nửa. Đổi tỉ lệ mức chậm của B so với A theo từng cách ghép:
""")
w(table(["Cách ghép", "Nửa 1 (khối 1 đến 4)", "Nửa 2 (khối 5 đến 8)"],
        [[k, f"{v[0]:+.3f}", f"{v[1]:+.3f}"] for k, v in E2B["pairings"].items()], [48, 22, 22]))
w(f"""
Nhãn của B theo cách ghép trung bình: **{E2B['label']}**. Hai cách ghép đầu cho cùng nhãn. Cách ghép từng khối liền kề cho nửa 2 chỉ là {E2B['pairings'][list(E2B['pairings'])[2]][1]:+.3f}, dưới ngưỡng 0.20, vì khối A số 5 chỉ có {pct(E2B['blocks']['5']['slow'], 1)} lần chạy chậm (trung vị {f(E2B['blocks']['5']['median'], 2)} ms, {pct(E2B['blocks']['5']['mid'], 0)} ở mức giữa). Theo cách ghép đó nhãn sẽ là "chưa kết luận". Tỉ lệ nhanh và độ lệch chuẩn ở bảng trên chỉ là mô tả, không dùng để gán nhãn.

"Ủng hộ" ở đây chỉ nghĩa là đặt ứng dụng và ngắt NPU cùng CPU4 làm mất mức chậm và làm độ trễ gần như không đổi. B đổi ba thứ cùng lúc (vị trí ứng dụng, vị trí ngắt, hai thứ cùng lõi), và C (cùng CPU0) cũng làm mất mức chậm, nên E2b không tách được yếu tố nào gây ra. E2c ngay bên dưới là thí nghiệm tách.

Quan sát thăm dò sau khi có dữ liệu, không dùng để gán nhãn: ở các khối A, cột ``cpu`` ghi CPU mà tiến trình đứng sau mỗi lần chạy. Lần chạy chậm gần như chỉ xảy ra khi tiến trình kết thúc ở CPU1 đến CPU3 (CPU1: {_a_cpu['1'][0]}/{_a_cpu['1'][1]}, CPU2: {_a_cpu['2'][0]}/{_a_cpu['2'][1]}, CPU3: {_a_cpu['3'][0]}/{_a_cpu['3'][1]}), còn ở CPU0: {_a_cpu['0'][0]}/{_a_cpu['0'][1]}, CPU4: {_a_cpu['4'][0]}/{_a_cpu['4'][1]}, CPU5: {_a_cpu['5'][0]}/{_a_cpu['5'][1]}. Điều này không khớp với giả thuyết đơn giản "khác lõi với ngắt thì chậm" (CPU4 và CPU5 khác lõi với ngắt ở CPU0 mà không chậm). E2d ngay bên dưới kiểm tra mẫu này có đối chứng. Cơ chế vẫn chưa kết luận.

Cột CPU ở bảng thăm dò trên đọc bằng ``sched_getcpu()`` sau khi lần chạy kết thúc, nên chỉ cho biết tiến trình thức dậy ở đâu và không cho biết chiều nhân quả (lần chạy chậm có thể tự ảnh hưởng nơi tiến trình thức dậy). Phiên bản RKNN API 2.3.2 và driver 0.9.8 ở E2b giống E2 (``bench/onboard_e2b/runtime_facts.txt``). Nhân của board ở E2b là 6.1.99-rockchip-rk3588, nhân ở E2 không được ghi lại nên chưa xác nhận giống nhau. Board được khởi động lại giữa hai lần.

Trạng thái board ghi trong ``bench/onboard_e2b/progress.txt``: ``irqbalance`` dừng suốt phép đo, affinity ngắt về ``0-7`` và ``cpu-sleep`` bật lại được đọc lại trước khi ``irqbalance`` chạy lại.


4. E2c: tách vị trí ứng dụng và vị trí ngắt NPU
===============================================

Sáu điều kiện (CPU của ứng dụng, CPU nhận ngắt): A mặc định, B (4, 4), C (0, 0), E (4, 0), F (0, 4), G (1, 0). ``irqbalance`` dừng, mười hai khối thứ tự A B C E F G rồi G F E C B A (mỗi nửa đúng một khối A), mỗi khối 1000 lần chạy sau 50 lần làm nóng. Quy tắc ``rule.txt`` viết trước dữ liệu và không sửa sau đó. Ngưỡng 0.01 của "mất mức chậm" là ngưỡng mới do tôi chọn cho quy tắc này, không từ nguồn nào. Khác biệt trạng thái với E2b đã công bố: E2b chạy trước khi ``rknn_server`` và ``adbd`` được khởi động lại sau khi board khởi động lại, còn E2c chạy khi cả hai đã bật, nên E2c dùng các khối B và C của chính nó làm đối chứng. Trạng thái đầu lượt (nhân, uptime, tần số, ``rknn_server``, ``adbd``, md5 mô hình) ghi ở đầu ``bench/onboard_e2c/progress.txt``.
""")
w(table(["Khối", "Điều kiện", "Nửa", "Trung vị (ms)", "p95 (ms)", "Độ lệch chuẩn (ms)", "Mức nhanh", "Mức giữa", "Mức chậm", "CPU của ứng dụng", "CPU nhận nhiều ngắt NPU nhất"],
        [[b["block"], b["cond"], b["half"], f(b["median"], 3), f(b["p95"], 3), f(b["std_ms"], 3), pct(b["fast"], 1), pct(b["mid"], 1), pct(b["slow"], 1),
          f"{b['app_cpu']} ({pct(b['app_top_share'], 0)})", f"{b['irq_cpu']} ({pct(b['irq_top_share'], 0)})"] for b in E2C["blocks"].values()],
        [6, 9, 6, 10, 9, 10, 9, 9, 9, 16, 16]))
w(f"""
Cả {len(E2C['blocks'])} khối thực hiện đúng điều kiện (mỗi khối đếm {E2C['blocks']['1']['irq_total']} ngắt NPU, bằng 1050 lần chạy nhân 63, và ``effective_affinity_list`` đọc lại khớp CPU đích ở mọi khối). Kết quả theo quy tắc đã viết trước:
""")
w(table(["Điều kiện", "Kết quả chính", "Kết quả phụ (đổi so với A cùng nửa)"],
        [[c, v, (", ".join(f"{x:+.3f}" for x in E2C["secondary"][c]["shifts"]) + f" ({E2C['secondary'][c]['label']})") if c in E2C["secondary"] else "không có"] for c, v in E2C["primary"].items()], [14, 28, 44]))
w("""
Nhãn "ủng hộ" ở cột kết quả phụ chỉ nghĩa là tỉ lệ mức chậm của điều kiện thấp hơn A cùng nửa hơn 0.20 ở cả hai nửa. Nó không xác định cơ chế, không dùng để đọc yếu tố, và không thay kết quả chính ở bảng trên.
""")
w(f"""
**Kiểm tra hợp lệ không đạt, nên theo quy tắc không đọc được yếu tố nào.** A có mức chậm ít nhất 0.20 ở một khối ({pct(max(b['slow'] for b in E2C['blocks'].values() if b['cond'] == 'A'), 1)}) và B mất mức chậm (tái hiện E2 và E2b). Nhưng C (cả hai ở CPU0) có mức chậm {', '.join(pct(b['slow'], 1) for b in E2C['blocks'].values() if b['cond'] == 'C')} ở hai khối, khối thứ hai vượt ngưỡng 0.01 của quy tắc, nên C xếp "lẫn lộn" và điều kiện tái hiện của C không đạt. Cả ba phát biểu đọc yếu tố (E với F, E với G, và gợi ý của E2b) vì vậy là "không đọc được yếu tố". Ngưỡng không được sửa sau khi thấy dữ liệu.

Mô tả các số đo, không dùng để đọc yếu tố và không phải kết quả theo quy tắc:

- B (4, 4) ở trung vị {f(E2C['blocks']['2']['median'], 2)} và {f(E2C['blocks']['11']['median'], 2)} ms, độ lệch chuẩn {f(E2C['blocks']['2']['std_ms'], 3)} và {f(E2C['blocks']['11']['std_ms'], 3)} ms, như ở E2b.
- C (0, 0), E (4, 0) và F (0, 4) đều ở trung vị quanh {f(min(b['median'] for b in E2C['blocks'].values() if b['cond'] in 'CEF'), 2)} đến {f(max(b['median'] for b in E2C['blocks'].values() if b['cond'] in 'CEF'), 2)} ms, mức chậm tối đa {pct(max(b['slow'] for b in E2C['blocks'].values() if b['cond'] in 'CEF'), 1)}, tức không ở mức của B. Tỉ lệ lần chạy dưới 17.0 ms (mức nhanh theo ngưỡng của trang này) là {pct(E2C['blocks']['5']['fast'], 1)} ở F và {pct(E2C['blocks']['3']['fast'], 1)} ở C, còn ở E là {pct(E2C['blocks']['4']['fast'], 1)} và {pct(E2C['blocks']['9']['fast'], 1)}, so với {pct(E2C['blocks']['2']['fast'], 0)} ở B.
- G (1, 0) giữ mức chậm ở cả hai khối ({', '.join(pct(b['slow'], 1) for b in E2C['blocks'].values() if b['cond'] == 'G')}), trung vị {', '.join(f(b['median'], 2) for b in E2C['blocks'].values() if b['cond'] == 'G')} ms.
- Khối A số 12 có tiến trình chuyển lõi (CPU6 chiếm {pct(E2C['blocks']['12']['app_top_share'], 0)}), mức chậm {pct(E2C['blocks']['12']['slow'], 1)}, thấp hơn khối A số 1 ({pct(E2C['blocks']['1']['slow'], 1)}). Mức chậm của A đổi nhiều giữa các khối, như ở E2b.

Chưa kết luận được yếu tố nào gây ra mức chậm. E2d ngay bên dưới là phép đo mới với quy tắc khác viết trước, không phải sửa kết quả của E2c.

5. E2d: bản đồ vị trí ứng dụng và vị trí ngắt NPU
=================================================

Số đo mô tả của E2c (không phải kết quả theo quy tắc) gợi ý rằng mất mức chậm không đòi hỏi hai thứ cùng CPU4, nên E2d hỏi hai câu chỉ về vị trí: mức chậm xuất hiện khi ứng dụng ghim ở những CPU nào (với ngắt ở CPU0 và với ngắt ở CPU4), và mức nhanh ổn định (quanh 16.3 ms, độ lệch chuẩn nhỏ) xuất hiện ở những cặp (CPU ứng dụng, CPU ngắt) nào. Hai mươi điều kiện: A (không ghim, ngắt mặc định), 16 ô gồm CPU ứng dụng 0 đến 7 và CPU ngắt 0 hoặc 4, và ba ô cùng CPU lớn (5, 5), (6, 6), (7, 7). Mỗi điều kiện hai khối (một khối mỗi nửa, nửa 2 là thứ tự đảo ngược của nửa 1), mỗi khối 1000 lần chạy sau 50 lần làm nóng, ``irqbalance`` dừng. Quy tắc ``bench/onboard_e2d/rule.txt`` được viết lúc 2026-10-31 00:00 theo giờ PC, trước khi có dữ liệu, và người dùng đã duyệt hai kiểm tra hợp lệ, các ngưỡng 0.05 và 0.95 và ba ô cùng CPU lớn. Hai ngưỡng 0.05 (mất mức chậm) và 0.95 (đạt mức nhanh) lấy từ dữ liệu E2c, nên là chọn sau khi đã thấy E2c. Ngưỡng 0.20 (còn mức chậm) giữ từ E2.
""")
_rows = []
for _c, _bl in _cells.items():
    _bl = sorted(_bl, key=lambda x: x["half"])
    _rows.append([_c, f(_bl[0]["median"], 2) + " và " + f(_bl[1]["median"], 2), pct(_bl[0]["slow"], 1) + " và " + pct(_bl[1]["slow"], 1),
                  pct(_bl[0]["fast"], 1) + " và " + pct(_bl[1]["fast"], 1), E2D["primary"][_c], E2D["fast"][_c]])
w(table(["Ô (aXiY: ứng dụng CPU X, ngắt CPU Y)", "Trung vị (ms), nửa 1 và nửa 2", "Mức chậm", "Mức nhanh", "Kết quả chính", "Kết quả mức nhanh"], _rows, [20, 24, 20, 20, 18, 22]))
w(f"""
Cả 40 khối thực hiện đúng điều kiện (mỗi khối {E2D['blocks']['1']['irq_total']} ngắt NPU, bằng 1050 lần chạy nhân 63, và ``effective_affinity_list`` đọc lại khớp CPU đích ở mọi khối). Cả hai kiểm tra hợp lệ đạt: A có mức chậm từ 0.20 trở lên ({pct(max(b['slow'] for b in E2D['blocks'].values() if b['cond'] == 'A'), 1)} ở một khối), và ô (4, 4) mất mức chậm và đạt mức nhanh. Hai ô (0, 0) và (1, 0) cho cùng kết quả với E2c (mất mức chậm và còn mức chậm), nên không có ô nào "không tái hiện E2c". Các phát biểu cho phép theo quy tắc:

- **Ngắt ở CPU0:** mức chậm chỉ có khi ứng dụng ghim ở CPU1, CPU2 hoặc CPU3, trong 8 CPU đã thử (tập S0 gồm CPU 1, 2, 3). Ở ba ô này trung vị {f(min(b['median'] for c in ('a1i0', 'a2i0', 'a3i0') for b in _cells[c]), 2)} đến {f(max(b['median'] for c in ('a1i0', 'a2i0', 'a3i0') for b in _cells[c]), 2)} ms. Ứng dụng ở CPU0 và CPU4 đến CPU7 không có mức chậm.
- **Ngắt ở CPU4:** không CPU ứng dụng nào trong 8 CPU còn mức chậm (tập S4 rỗng). Cả tám CPU đều có kết quả rõ ràng ở cả hai hàng. Theo quy tắc: không đổi trên các CPU 0, 4, 5, 6, 7, và khác nhau trên CPU 1, 2, 3 (có mức chậm với ngắt ở CPU0, không có với ngắt ở CPU4). CPU0 và CPU4 cũng khác cụm và khác xung nhịp, nên đây không phải kết luận về chính vai trò của ngắt.
- **Mức nhanh ổn định:** đạt ở bảy ô: ứng dụng ở CPU4 đến CPU7 với ngắt ở CPU4 (bốn ô), và ba ô cùng CPU lớn (5, 5), (6, 6), (7, 7). Trong các ô đã thử, mọi ô có ngắt ở CPU0 và mọi ô có ứng dụng ở CPU0 đến CPU3 đều không đạt. Với ngắt ở CPU0 và ứng dụng ở CPU4 đến CPU7, bảy trong tám khối có trung vị {f(min(_m4), 2)} đến {f(max(_m4), 2)} ms, ngoại lệ là khối 7 (ô (5, 0)) với trung vị {f(E2D['blocks']['7']['median'], 2)} ms. Với ngắt ở CPU4 và ứng dụng ở CPU0 đến CPU3, trung vị {f(min(_m3), 2)} đến {f(max(_m3), 2)} ms.

Mô tả, không phải kết quả theo quy tắc: ô (5, 0) có hai khối không nhất quán (mức nhanh {pct(E2D['blocks']['7']['fast'], 1)} ở khối 7 và {pct(E2D['blocks']['34']['fast'], 1)} ở khối 34), nên kết quả mức nhanh là "không đạt". Khối A số 1 và số 40 có tỉ lệ mức chậm {pct(E2D['blocks']['1']['slow'], 1)} và {pct(E2D['blocks']['40']['slow'], 1)}, với tiến trình đứng ở CPU1 trong khoảng một nửa số lần.

Giới hạn theo quy tắc: mỗi ô chỉ có hai khối kề nhau theo thời gian, một board, một lần khởi động. Các phát biểu trên chỉ nói về vị trí. Không được đọc chúng như hiệu ứng của cụm CPU hay của tần số, vì CPU0 đến 3 chạy 1.8 GHz, CPU4 đến 5 chạy 2.256 GHz và CPU6 đến 7 chạy 2.304 GHz, nên mọi mẫu theo cụm cũng là mẫu theo xung nhịp. Cơ chế, lý do một CPU chậm, và ảnh hưởng của tải CPU khác nằm ngoài phạm vi và chưa biết.
""")
w = docs["04"].append
w("""
3.2. Bộ đếm ``cpuidle`` trong ba đợt liên tiếp
----------------------------------------------
""")
ci = O["cpuidle"]
w(table(["Đợt", "Trung vị (ms)", "Số lần vào state0 (WFI)", "Số lần vào state1 (cpu-sleep)", "Thời gian state1 (µs)"],
        [[n, f(hot[str(n)]["median"] / 1000, 3), ci[f"hot_{n}"]["state0"]["entries"], ci[f"hot_{n}"]["state1"]["entries"], ci[f"hot_{n}"]["state1"]["time_us"]] for n in (1, 2, 3)], [8, 16, 20, 24, 24]))
w(f"""
Đợt 3 (trung vị cao nhất) có số lần vào ``cpu-sleep`` nhiều hơn hai đợt kia. Bộ đếm cộng trên mọi CPU và chỉ có ba đợt, nên **nhãn: chưa kết luận**. Phép thử có đối chứng ở :doc:`05-thu-ghim-cpu-va-ngat` là bằng chứng mạnh hơn, và phép can thiệp X2 cho thấy tắt ``cpu-sleep`` riêng ở CPU nhận ngắt làm mất phần tăng ở N (:doc:`06-co-che-cac-muc-do-tre`, mục 3).

3.3. Xung nhịp hoặc băng thông DDR đổi
--------------------------------------

Hệ số theo cycles ước tính của phép khớp ``time = a x est. + b`` trên các dòng Conv giữ nguyên giữa ba đợt ``detail`` ({', '.join(f(fits[str(n)]['slope'], 3) for n in (1, 2, 3))}) trong khi hằng số b đổi ({', '.join(f(fits[str(n)]['intercept'], 1) for n in (1, 2, 3))} µs), và tổng thời gian mỗi lần chạy (trung vị) của ba đợt là {', '.join(f(O['detail_totals'][str(n)]['median'] / 1000, 2) for n in (1, 2, 3))} ms. Nếu xung nhịp NPU hoặc băng thông DDR đổi, phần tỉ lệ với kích thước phải đổi theo. Ở B2 so với B3 cũng vậy (:doc:`03-phan-tich-sau-latency-tung-khoi`, mục 5). **Nhãn: không ủng hộ.** Bộ lấy mẫu 1 Hz trong E1 (``bench/extra_e1_sampler.sh``) đọc các file sysfs ``cur_freq`` và ``governor`` của NPU và DDR, tần số của ba cụm CPU và nhiệt độ, không dùng bộ đếm xung nhịp. Các giá trị đó không đổi, nhưng không chứng minh xung nhịp thật ổn định.

3.4. Vị trí CPU, ngắt NPU và trạng thái ngủ của CPU
---------------------------------------------------

Giả thuyết này được kiểm bằng năm thí nghiệm E2 đến E2e ở :doc:`05-thu-ghim-cpu-va-ngat`, và phần thời gian tăng được tách bằng trace ở :doc:`06-co-che-cac-muc-do-tre`.

4. Dao động trong một phiên ``eval_perf``
=========================================

4.1. E1: dao động ngay trong một phiên ``eval_perf``
----------------------------------------------------
""")
w(table(["Phiên", "Trung vị (ms)", "Nhỏ nhất", "Lớn nhất", "Khoảng", "CV", "Lần gọi đầu", "Trung vị các lần còn lại", "Số báo cáo tần số khác nhau"],
        [[s["session"], f(s["median"], 3), f(s["min"], 3), f(s["max"], 3), pct(s["range"], 1), pct(s["cv"], 1), f(s["first"], 3), f(s["rest_median"], 3), s["freq_reports"]] for s in e1["sessions"]],
        [8, 12, 10, 10, 10, 8, 12, 16, 16]))
sp = e1["sampler"]
w(f"""
Chênh trung vị giữa hai phiên chỉ {pct(e1['session_median_gap'], 2)} nhưng trong mỗi phiên giá trị trải {pct(max(s['range'] for s in e1['sessions']), 0)}, và {pct(e1['low_mode_share'], 1)} trong 40 lần gọi nằm dưới 19.0 ms (trung vị {f(e1['low_mode_median'], 3)} ms), phần còn lại có trung vị {f(e1['high_mode_median'], 3)} ms. Tần số in ra ở mọi lần gọi giống nhau. Bộ lấy mẫu ({sp['rows']} dòng trong {sp['seconds']:.0f} giây) cho thấy tần số, governor và nhiệt độ ({f(sp['soc_mC'][0] / 1000, 1)} đến {f(sp['soc_mC'][1] / 1000, 1)} °C) không đổi. Lần gọi đầu của hai phiên E1 là {', '.join(f(s['first'], 2) for s in e1['sessions'])} ms, thấp hơn trung vị các lần sau ({', '.join(f(s['rest_median'], 2) for s in e1['sessions'])} ms). Ở B3, latency của lần gọi đầu cũng thấp hơn trung vị các lần sau ở cả ba phiên (mục 4.2), nên lần gọi đầu thấp hơn ở cả 5 phiên latency qua relay. Điều này chưa giải thích được. Trên LAN (X4, ngày 2026-10-31) hiện tượng không lặp lại ổn định (:doc:`07-giao-thuc-p2-va-do-mo-rong`, mục 3). Hãng không có khuyến nghị warm-up cho ``eval_perf`` (không tìm thấy trong UG232 và API232).
""")

w = docs["02"].append
w("""3. Kết quả từng khối
====================

Cột "B3 (µs)" là trung vị thời gian khối ở chế độ debug qua 3 phiên B3 (mỗi phiên lấy trung vị 5 lần gọi). "Tỉ lệ" là phần thời gian của khối trên tổng thời gian các dòng trong cùng lần gọi. "Cận độ nhạy" là tỉ lệ sau khi trừ khỏi mỗi dòng có thời gian dương hằng số theo từng dòng của phiên (hệ số b của phép khớp Conv), chỉ là một cận để thấy khối có nhiều dòng nhỏ lệch bao nhiêu, không phải hiệu chỉnh. Ngoài tỉ lệ ở bảng, tỉ lệ khối trên board lấy từ 600 lần chạy ``detail``.

3.1. Bảng 1: khối L0 đến L22
----------------------------
""")
rows1 = []
for b in ord_blocks:
    x = A["blocks"][b]
    rows1.append([b, x["rows"], f(x["us"], 0), f(x["b2_us"], 0), pct(x["share"], 1), pct(x["b2_share"], 1), pct(O["detail_blocks"][b]["share"], 1), pct(x["share_sens"], 1), pct(x["share_spread"], 1),
                  "-" if x["gflops"] is None else f(x["gflops"], 3), "-" if x["us_per_gflop"] is None else f(x["us_per_gflop"], 0)])
w(table(["Khối", "Số dòng", "B3 (µs)", "B2 (µs)", "Tỉ lệ B3", "Tỉ lệ B2", "Tỉ lệ trên board", "Cận độ nhạy", "Lệch tỉ lệ giữa các phiên B3", "GFLOPs", "µs mỗi GFLOP"], rows1, [8, 8, 9, 9, 9, 9, 10, 10, 12, 9, 10]))
w(f"""
Độ tin cậy của tỉ lệ khối. Giữa năm nguồn (``eval_perf`` B3 trung vị, B2, trên board tính chung, trên board khi tổng lần chạy dưới 20 ms, từ 20 ms trở lên), một khối chiếm từ 2% thời gian trở lên chênh tối đa {f(share_pp, 1)} điểm phần trăm (lớn nhất ở L22). Các khối nhỏ ở neck dao động nhiều hơn giữa các phiên B3: {', '.join(f'{b} ({pct(v, 1)})' for b, v in sorted(unstable.items()))} có độ lệch tỉ lệ vượt 10% (cổng A8). Hai khối nhỏ nhất theo thời gian, L17 và L20, lệch giữa các lần gọi trong một phiên tới {pct(A['blocks']['L17']['call_spread'], 0)} và {pct(A['blocks']['L20']['call_spread'], 0)}, nên xếp hạng giữa các khối nhỏ nằm trong nhiễu. Cột "Cận độ nhạy" cho thấy hằng số mỗi dòng ảnh hưởng không đều, phụ thuộc kích thước tương đối của các dòng trong khối: khối có dòng lớn tăng tỉ lệ (L0: {pct(A['blocks']['L0']['share'], 1)} lên {pct(A['blocks']['L0']['share_sens'], 1)}, L2: {pct(A['blocks']['L2']['share'], 1)} lên {pct(A['blocks']['L2']['share_sens'], 1)}), khối gồm các dòng nhỏ giảm (L9: {pct(A['blocks']['L9']['share'], 1)} xuống {pct(A['blocks']['L9']['share_sens'], 1)}, L8: {pct(A['blocks']['L8']['share'], 1)} xuống {pct(A['blocks']['L8']['share_sens'], 1)}, L20: {pct(A['blocks']['L20']['share'], 1)} xuống {pct(A['blocks']['L20']['share_sens'], 1)}), còn L22 gần như không đổi ({pct(l22['share'], 1)} và {pct(l22['share_sens'], 1)}) vì thời gian của nó dồn vào vài dòng lớn.

3.2. Bảng 2: thành phần trong khối
----------------------------------
""")
top_parts = sorted(A["parts"].items(), key=lambda kv: -kv[1]["share"])[:22]
w(table(["Khối/thành phần", "B3 (µs)", "Tỉ lệ toàn mạng", "Tỉ lệ trong khối", "Lệch giữa các phiên", "Lệch giữa các lần gọi"],
        [[k, f(v["us"], 0), pct(v["share"], 1), pct(v["share_in_block"], 1), pct(v["spread"], 1), pct(v["call_spread"], 1)] for k, v in top_parts], [20, 12, 16, 16, 18, 18]))
w("""
Bảng đầy đủ {len(A['parts'])} thành phần nằm ở ``results/latency_per_block_ppe5_yolov8n_baseline_100ep_s0_int8_CORE_0.md``. Thành phần của L22 gồm ``box_branch`` và ``cls_branch`` (hai nhánh Conv), ``dfl`` (Softmax, Conv, Transpose và Reshape) và ``decode`` (các phép tính giải mã hộp).

3.3. Bảng 3: theo OpType
------------------------
""")
w(table(["OpType", "Số dòng", "B3 (µs)", "Tỉ lệ", "Lệch giữa các phiên"],
        [[k, v["calls"], f(v["us"], 0), pct(v["share"], 2), pct(v["spread"], 1)] for k, v in sorted(A["ops"].items(), key=lambda kv: -kv[1]["us"])], [20, 10, 12, 12, 18]))

# ---------------------------------------------------------------- 5
w = docs["03"].append
w(f"""*******************************
Phân tích sâu latency từng khối
*******************************

.. admonition:: Trang này trả lời

   - Conv, op không phải Conv và chuỗi DFL tốn thời gian ra sao so với ước tính cycles của compiler và so với GFLOPs?
   - Chi phí cố định mỗi dòng của bảng từng lớp là bao nhiêu và khác nhau giữa các phiên thế nào?

.. admonition:: Tóm tắt

   - Chuỗi DFL (Reshape, Softmax, Conv, Transpose) tốn {f(dfl_us / 1000, 2)} ms, tức {pct(dfl_us / L['total_us'], 1)} thời gian debug, trong khi GFLOPs gần bằng 0. Ngoài ``InputOperator`` và ``OutputOperator``, ``Transpose`` là op duy nhất chạy trên CPU.
   - Các op không phải Conv tốn {pct(ot['share'], 1)} thời gian debug. Conv chạy lâu hơn ước tính cycles của compiler trung vị {f(c['ratio_median'], 2)} lần (khoảng {f(c['ratio_min'], 2)} đến {f(c['ratio_max'], 1)}).
   - Giữa các phiên, mỗi dòng của bảng từng lớp bị cộng thêm khoảng {f(min(d['intercept'] for d in L['delta_vs_b2']), 0)} đến {f(max(d['intercept'] for d in L['delta_vs_b2']), 0)} µs so với B2, gần như không phụ thuộc kích thước (R2 không quá {f(max(d['r2'] for d in L['delta_vs_b2']), 2)}). Hệ số theo cycles của Conv giữ ở {f(min(v['slope'] for v in fits.values()), 3)} đến {f(max(v['slope'] for v in fits.values()), 3)} giữa các đợt trên board.

Phân tích trên ba phiên B3 ở chế độ debug (tổng {f(L['total_us'] / 1000, 2)} ms), kết quả tổng hợp ở :doc:`02-ket-qua-latency-tung-khoi` và dao động ở :doc:`04-cac-muc-do-tre`. "Ước tính cycles" là ``Total cycles`` chia 1000 µs, tức ước tính của compiler ở xung NPU 1 GHz đã khoá, không phải giới hạn phần cứng. Trang này lấy trung vị từng dòng (trung vị 5 lần gọi, rồi trung vị 3 phiên) nên lệch nhẹ so với bảng ở :doc:`02-ket-qua-latency-tung-khoi`, vốn cộng khối trong từng lần gọi rồi lấy trung vị. Ví dụ khối L22 là {pct(L['stages']['head L22']['time_share'], 1)} ở đây và {pct(A['blocks']['L22']['share'], 1)} ở trang kết quả, và ``Concat`` là {f(L['other']['ops']['Concat']['time'], 0)} µs ở đây và {f(A['ops']['Concat']['us'], 0)} µs ở trang kết quả.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Conv so với ước tính cycles của compiler
===========================================

{c['n']} dòng Conv (có ``NPUCycles`` khác 0) dùng {f(c['time_us'] / 1000, 2)} ms, {pct(c['time_us'] / L['total_us'], 1)} thời gian, so với {f(c['est_us'] / 1000, 2)} ms ước tính. Tỉ số thời gian trên ước tính trung vị {f(c['ratio_median'], 2)}, nhỏ nhất {f(c['ratio_min'], 2)}, lớn nhất {f(c['ratio_max'], 1)}. Phép khớp bình phương tối thiểu ``time = {f(c['fit_slope'], 3)} x est. + {f(c['fit_intercept_us'], 1)} µs`` có R2 {f(c['fit_r2'], 3)} (khớp mô tả trên {c['n']} dòng, không phải mô hình phần cứng). Số dòng Conv có chu kỳ DDR lớn hơn chu kỳ NPU: {len(c['ddr_gt_npu_rows'])}.
""")
w(table(["Dải tỉ số", "Số dòng", "Thời gian (µs)", "Ước tính (µs)"], [[b["band"], b["rows"], f(b["time_us"], 0), f(b["est_us"], 0)] for b in conv_bands], [20, 12, 20, 20]))
w(f"""
Dải 1.5 đến 3 lần ước tính chứa {conv_bands[1]['rows']} trên {c['n']} dòng Conv và {pct(conv_bands[1]['time_us'] / c['time_us'], 0)} thời gian Conv. Sáu dòng ở dải trên 6 lần rất nhỏ (tổng {f(conv_bands[3]['time_us'], 0)} µs) và đều là Conv 1x1: bốn dòng là Conv 1x1 cuối của nhánh box và cls ở L22 (``cv2.1.2``, ``cv3.1.2``, ``cv2.2.2``, ``cv3.2.2``), hai dòng là ``cv1`` của L6 và L9. Số liệu từng dòng nằm ở ``results/layer_analysis_*.md``. Vì sao Conv lớn đạt gần ước tính nhất còn Conv nhỏ lệch xa là điều chưa có nguồn T1 hoặc T2 trong repo, nên không giải thích ở đây.

2. Các dòng không phải Conv
===========================

{f(ot['time_us'] / 1000, 2)} ms, {pct(ot['share'], 1)} tổng thời gian debug, không có ``NPUCycles`` nên cột cycles của compiler không phản ánh chúng. Phép khớp trên {ot['move_fit']['n']} dòng ``Concat``, ``Split`` và ``Add`` cho ``time = {f(ot['move_fit']['us_per_mb'], 0)} µs mỗi MB đọc ghi + {f(ot['move_fit']['intercept_us'], 1)} µs`` (R2 {f(ot['move_fit']['r2'], 2)}), nghĩa là phần lớn thời gian của các dòng này là hằng số mỗi dòng.
""")
w(table(["OpType", "Số dòng", "Thời gian (µs)", "Tỉ lệ", "RW (KB)", "µs mỗi MB"],
        [[k, v["calls"], f(v["time"], 0), pct(v["time"] / L["total_us"], 2), v["rw_kb"], "-" if v["us_per_mb"] is None else f(v["us_per_mb"], 0)] for k, v in sorted(ot["ops"].items(), key=lambda kv: -kv[1]["time"])], [18, 10, 14, 10, 10, 12]))
w(f"""
3. Chuỗi DFL và giải mã ở đầu Detect
====================================

L22 cộng ``post_detect`` chiếm {f(hd['head_total'] / 1000, 2)} ms ({pct(hd['head_total'] / L['total_us'], 1)}). Riêng chuỗi DFL (theo thứ tự đồ thị) như sau, tổng {f(dfl_us / 1000, 2)} ms, {pct(dfl_us / L['total_us'], 1)}. Trên board, bảng ``detail`` cho DFL {f(O['detail_dfl_us'] / 1000, 2)} ms (trung vị ba đợt).
""")
w(table(["ID", "OpType", "Target", "Thời gian (µs)"], [[r["id"], r["op"], r["target"], f(r["time"], 0)] for r in dfl], [10, 20, 12, 16]))
w(f"""
``Softmax`` (``exSoftmax13``) trên NPU chiếm phần lớn. ``Transpose`` chạy trên CPU (Target CPU), là op duy nhất không chạy trên NPU ngoài ``InputOperator`` và ``OutputOperator`` ở đồ thị này. Cấu trúc DFL của YOLOv8 (softmax trên 16 bin rồi nhân với 0, 1, ..., 15) đã mô tả ở :doc:`../01-tang-ai/02-kien-truc-model`. Các thành phần của L22 theo thời gian (B3): {', '.join(f'{k.split(chr(47))[1]} {f(v / 1000, 2)} ms' for k, v in sorted(hd['parts'].items(), key=lambda kv: -kv[1]) if k.startswith('L22'))}.

4. Tỉ lệ thời gian so với tỉ lệ GFLOPs
======================================
""")
w(table(["Giai đoạn", "Thời gian (µs)", "Tỉ lệ thời gian", "GFLOPs (Conv2d)", "Tỉ lệ GFLOPs"],
        [[k, f(v["time_us"], 0), pct(v["time_share"], 1), f(v["gflops"], 3), pct(v["gflops_share"], 1)] for k, v in L["stages"].items()], [26, 16, 16, 18, 16]))
w(f"""
Backbone chiếm {pct(L['stages']['backbone L0-L9']['time_share'], 1)} thời gian so với {pct(L['stages']['backbone L0-L9']['gflops_share'], 1)} GFLOPs. Neck chiếm {pct(L['stages']['neck L10-L21']['time_share'], 1)} so với {pct(L['stages']['neck L10-L21']['gflops_share'], 1)}, và head chiếm {pct(L['stages']['head L22']['time_share'], 1)} so với {pct(L['stages']['head L22']['gflops_share'], 1)}. Phần ``io`` và ``post_detect`` ({pct(L['stages']['io and post_detect']['time_share'], 1)}) không có GFLOPs. GFLOPs chỉ đếm Conv2d (xem trang kiến trúc), không đếm ``Concat``, ``Split``, ``Add`` và các op khác, nên tỉ lệ GFLOPs không dự đoán được thời gian. Vì sao backbone cao hơn còn neck và head thấp hơn chưa có nguồn để giải thích.

5. Chi phí cố định mỗi dòng, khác nhau giữa các phiên
=====================================================

So từng phiên B3 với B2 trên 119 dòng, hồi quy hiệu thời gian theo hằng số, ước tính cycles và RW (KB):
""")
w(table(["Phiên", "Tổng chênh (µs)", "Chênh trung bình mỗi dòng (µs)", "Hằng số (µs)", "Theo ước tính cycles", "µs mỗi MB", "R2"],
        [[d["session"], f(d["total_delta"], 0), f(d["per_row_mean"], 1), f(d["intercept"], 1), f(d["per_est_us"], 3), f(d["us_per_mb"], 1), f(d["r2"], 3)] for d in L["delta_vs_b2"]], [8, 14, 22, 14, 18, 12, 8]))
ri = S["row_intercept_us"]
w(f"""
Chênh lệch giữa các phiên là một hằng số khoảng {f(min(d['intercept'] for d in L['delta_vs_b2']), 0)} đến {f(max(d['intercept'] for d in L['delta_vs_b2']), 0)} µs mỗi dòng, hệ số theo kích thước gần bằng 0. Hằng số mỗi dòng của từng phiên (hệ số b của phép khớp Conv) là {', '.join(f(x, 1) for x in ri[:-1])} µs ở ba phiên B3 và {f(ri[-1], 1)} µs ở B2. Trên board, ba đợt ``detail`` cho {', '.join(f(fits[str(n)]['intercept'], 1) for n in (1, 2, 3))} µs. Hệ quả: tổng debug và tỉ lệ khối bị lệch theo số dòng của khối, như đã nêu ở :doc:`02-ket-qua-latency-tung-khoi` (mục 3.1). Nguyên nhân của hằng số này chưa biết.
""")
w = docs["04"].append
w("""
4.2. Lần gọi đầu và các lần sau trong một phiên
-----------------------------------------------
""")
w(table(["Phiên", "Latency lần gọi đầu (ms)", "Latency trung vị các lần sau (ms)", "Tổng debug lần đầu (ms)", "Tổng debug trung vị các lần sau (ms)"],
        [[i + 1, f(x["latency_first"], 3), f(x["latency_rest_median"], 3), f(x["debug_first"] / 1000, 3), f(x["debug_rest_median"] / 1000, 3)] for i, x in enumerate(L["first_vs_rest"])], [8, 18, 22, 22, 26]))
w("""
Latency của lần gọi đầu thấp hơn trung vị các lần sau ở cả ba phiên B3 (và ở hai phiên E1, mục 4.1). Tổng debug thì không đồng nhất: lần đầu thấp hơn ở phiên 1 và 2, cao hơn một chút ở phiên 3. Chỉ năm phiên latency, nên không đủ dữ liệu để kết luận có hiệu ứng warm-up hay nguyên nhân của nó. Đính chính ngày 2026-10-31: X4 chạy 10 phiên mỗi giao thức trên LAN, lần gọi đầu thấp hơn các lần sau không ổn định ở cả hai giao thức (:doc:`07-giao-thuc-p2-va-do-mo-rong`, mục 3). Hãng không có khuyến nghị warm-up trong tài liệu, chỉ ví dụ ``rknn_benchmark.cpp`` chạy 5 lần làm nóng trước khi đo (``3rdparty/rknn-toolkit2/rknpu2/examples/rknn_benchmark/src/rknn_benchmark.cpp:415-431``) [T1 mã nguồn].
""")
w = docs["03"].append
w(f"""
6. Điều chưa biết
=================

- Nguyên nhân của hằng số mỗi dòng ở chế độ debug và vì sao nó khác nhau giữa các phiên (mục 5). X4 đo được liên hệ với việc ghim lõi: dưới P2 hằng số khoảng 5 µs và chênh 0.3 µs giữa 10 phiên, không ghim thì 8 đến 52 µs (:doc:`07-giao-thuc-p2-va-do-mo-rong`, mục 3). Nguyên nhân vẫn chưa biết.
- Vì sao Conv lớn gần ước tính cycles còn Conv nhỏ lệch xa (mục 1). Nguồn hãng chỉ nói hiệu suất MAC phụ thuộc kích thước: "The utilization rate decreases when the Height * Width of the output Tensor < 16." [T1 UG232 tr.147], không nói chi phí cố định mỗi lớp. Phân tích lại dữ liệu B3 (X10, quy tắc ``bench/analysis_x10/rule.txt`` viết trước khi tính, ngưỡng 20% là số mới, chưa qua người dùng duyệt): {_x10['n_small'] - 1} trên {_x10['n_small']} dòng Conv nhỏ khớp mô hình thời gian = a × ước tính + b trong 20%, riêng dòng ``model.6/cv1`` đo {f(_x10_l6['time_us'], 0)} µs so với dự đoán {f(_x10_l6['predicted_us'], 0)} µs, nên "chưa kết luận". Vẫn chưa biết. Từ khóa đề xuất: "NPU per-layer launch overhead small convolution", "RKNN layer scheduling overhead".
- Vì sao tỉ lệ thời gian của backbone cao hơn tỉ lệ GFLOPs còn neck và head thấp hơn (mục 4). X10 bỏ hằng số mỗi dòng ra khỏi tỉ lệ thời gian: khoảng cách của backbone đổi từ {f(_x10['stages']['backbone L0-L9']['gap_before'], 3)} thành {f(_x10['stages']['backbone L0-L9']['gap_after'], 3)}, neck từ {f(_x10['stages']['neck L10-L21']['gap_before'], 3)} thành {f(_x10['stages']['neck L10-L21']['gap_after'], 3)}, head từ {f(_x10['stages']['head L22']['gap_before'], 3)} thành {f(_x10['stages']['head L22']['gap_after'], 3)}, nên "chưa kết luận". Trong các nguồn đã tìm (UG232, API232, RKNNRT, tài liệu operator, bài báo ``edgesoc_benchmark_2026kong.pdf``, xem ``tmp/2026-10-31_latency-sources-facts.md``, câu hỏi Q8), không có câu nào nói thời gian NPU của Concat, Split, Add không theo FLOPs. Vẫn chưa biết.

7. Nguồn
=========

T3 board và PC: ``results/layer_analysis_*``, ``results/latency_per_block_*``, ``ai/automation/runs/{RUN}/bench/tier1_int8_CORE_0*``. Mã: ``ai/automation/analyze_layers.py``, ``ai/core/rknn/blocks.py``, ``ai/automation/analyze_x10.py`` (X10, ``results/analysis_x10_*``). T1: ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (UG232 tr.147).
""")
w = docs["04"].append
w("""
5. Điều chưa biết và giới hạn
=============================

- Chu kỳ của ``rknpu/load`` đã trả lời bằng mã nguồn driver (mục 2): cửa sổ 1 giây.

6. Nguồn
========

- T3 board và PC: ``results/onboard_*``, ``results/layer_analysis_*``, ``ai/automation/runs/{RUN}/bench/onboard/``, ``bench/tier1_int8_CORE_0*``, ``bench/extra_e1_*``, ``bench/extra_link_facts.txt``. Mã: ``ai/board/rknn_perf_bench.c``, ``ai/automation/analyze_onboard.py``, ``ai/automation/analyze_layers.py``. Không có trích dẫn T1 trong trang này.
""".replace("{RUN}", RUN))
w = docs["02"].append
w("""
4. Cổng chấp nhận
=================
""")
w(table(["Mã", "Kết quả", "Chi tiết"], [[x["code"], "đạt" if x["ok"] else "không đạt", x["detail"].replace("|", "/")] for x in A["checks"]], [8, 12, 80]))
w(f"""
Cách đọc. A5 và A8 không đạt, kể cả khi chỉ xét ba phiên B3. Cổng A8 báo hai cách: chỉ các phiên đánh số, và tính B2 như một phiên ({A8B2}). Không đổi ngưỡng để cổng đạt (ngưỡng đã duyệt ngày 2026-10-30: 5% và 10%). Hệ quả cho cách báo: latency tuyệt đối báo dưới dạng khoảng kèm nguồn và số mẫu (mục 2), tỉ lệ khối báo kèm cột lệch giữa các phiên, và chỉ xếp hạng các khối lớn. Đọc theo cổng gốc (qua relay): FP16 chưa chạy vì A8 của INT8 không đạt (theo quy tắc của kế hoạch, FP16 chỉ chạy sau khi INT8 ổn định, và phải xen kẽ INT8 và FP16 để lệch giữa phiên không bị nhầm là hiệu ứng kiểu dữ liệu). Chạy lại ba phiên A5 và A8 khi ghim lõi sẽ là một giao thức mới, không làm cổng A8 gốc đạt.

5. Điều chưa biết và giới hạn
=============================

- Quan hệ giữa thời gian ``eval_perf`` (từ phần cứng) và thời gian ``rknn_run`` trên board (gồm driver), vì hai nguồn cho mức khác nhau.
- ``CORE_0_1_2``, FP16 và độ chính xác sau INT8 đã đo ngày 2026-10-31 dưới giao thức P2 trên LAN (:doc:`07-giao-thuc-p2-va-do-mo-rong`). Số liệu vẫn chỉ cho một model (một seed) trên một board.

6. Nguồn
========

- T1: ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (UG232 tr.177), ``docs/_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf`` (API232 tr.18), ``3rdparty/rknn-toolkit2/rknpu2/runtime/Linux/librknn_api/include/rknn_api.h`` (``RKNN_FLAG_COLLECT_PERF_MASK``, ``RKNN_QUERY_PERF_DETAIL``, ``RKNN_QUERY_PERF_RUN``).
- T3 board và PC: ``results/latency_per_block_*``, ``results/layer_analysis_*``, ``results/onboard_*``, ``ai/automation/runs/{RUN}/bench/``, ``ai/automation/runs/{RUN}/export_int8.json``. Mã: ``ai/board/rknn_perf_bench.c``, ``ai/automation/aggregate_layers.py``, ``analyze_layers.py``, ``analyze_onboard.py``, ``ai/core/rknn/blocks.py``, ``tests/test_layer_blocks.py``.
""")

w = docs["05"].append
w(f"""6. E2e: đường ``eval_perf`` qua ``rknn_server``
===============================================

6.1. Thiết kế và quy tắc
------------------------

Câu hỏi mở (:doc:`02-ket-qua-latency-tung-khoi`, mục 2) là ``eval_perf`` qua ``rknn_server`` và ``rknn_run`` trên board cho hai mức khác nhau, và E2 chưa từng chạy cho đường ``eval_perf``. Trước đây mỗi phiên qua relay mất 15 đến 35 phút. Trên LAN trực tiếp, một phép đo chỉ ghi thời gian chờ (không ghi giá trị latency) cho ``init_runtime`` khoảng 1.5 giây và mỗi lần ``eval_perf`` khoảng 0.21 đến 0.23 giây (``bench/extra_tier1_lan_timing.txt``), nên E2e chạy được 500 lần gọi mỗi khối.

Việc đã làm trên board trước khi viết quy tắc (đều không ghi giá trị latency, công bố trong ``bench/onboard_e2e/rule.txt``, và số lần xuất hiện của ``Total Time`` trong đầu ra của các phép thăm dò đã kiểm là 0): phép đo thời gian chờ nói trên, một phép đếm ngắt (một lần ``eval_perf`` cộng 63 ngắt trên ngắt 36, năm lần cộng 315, nên mỗi lần ``eval_perf`` là đúng một lần suy luận), và kiểm tra runtime (hai bản ``librknnrt.so`` cùng md5, ``rknn_server`` nạp ``/usr/lib/librknnrt.so``, phiên bản 2.3.2 giống bench C).

"Ứng dụng" ở đây là ``rknn_server`` trên board. Một tiến trình root phía board (chạy ở CPU7, danh sách trắng bảy điều kiện, khôi phục khi thoát) ghim mọi luồng của ``rknn_server`` bằng ``taskset -a -p`` và đặt ngắt NPU 36, 37, 38 về CPU đích. PC chạy ``load_rknn``, ``init_runtime`` (``CORE_0``), 50 lần ``eval_perf`` làm nóng rồi 500 lần đo, mỗi khối là một phiên mới, các lần gọi cách nhau khoảng 0.22 giây. Bảy điều kiện (CPU của ``rknn_server``, CPU ngắt): A (không ghim), (4, 4), (0, 0), (4, 0), (0, 4), (1, 0), (1, 4), mỗi điều kiện hai khối, nửa 2 là thứ tự đảo ngược của nửa 1, mười bốn khối. ``irqbalance`` dừng suốt phép đo.

Quy tắc ``rule.txt`` viết lúc 2026-10-31 00:43 theo giờ PC, trước khi có dữ liệu, và người dùng đã duyệt: các ngưỡng 0.05 (mất mức chậm), 0.20 (còn mức chậm), 0.95 (đạt mức nhanh) giữ từ E2d nhưng áp lên một đại lượng mới là thời gian ``eval_perf``, ngoại lệ lệch mức đồng đều với ngưỡng 1.25 ms (con số mới), 500 mẫu mỗi khối và sáu ô. Mức chậm là từ 20.0 ms, mức nhanh là dưới 17.0 ms, hai ngưỡng lấy từ biểu đồ của đường C API. Không có kiểm tra hợp lệ chặn kết quả: ô (4, 4) chỉ là một trong sáu ô so sánh với E2d, và điều kiện A chỉ để mô tả.

Một khác biệt trạng thái cần ghi: NPU và DDR đọc ra governor ``userspace`` trong E2e (ghi ở đầu mỗi khối), sau các lần gọi ``eval_perf`` ở các phép thăm dò trước quy tắc, còn E2d chạy ở ``performance``. Tần số vẫn là 1 GHz và 2.112 GHz. Nguyên nhân của việc đổi governor chưa được kiểm.

6.2. Kết quả mười bốn khối
--------------------------
""")
w(table(["Khối", "Điều kiện", "Trung vị (ms)", "Độ lệch chuẩn (ms)", "Mức nhanh", "Mức giữa", "Mức chậm", "Luồng bận (CPU cuối khối)", "Ngắt NPU: CPU (tỉ lệ)"],
        [[b["block"], b["cond"], f(b["median"], 3), f(b["std_ms"], 3), pct(b["fast"], 1), pct(b["mid"], 1), pct(b["slow"], 1), f"{b['busy_name']} (CPU{b['busy_cpu']})",
          f"{b['irq_cpu']} ({pct(b['irq_top_share'], 0)})"] for b in _eb.values()], [6, 10, 12, 12, 10, 10, 10, 22, 16]))
w(f"""
Cả mười bốn khối thực hiện đúng điều kiện: ``Cpus_allowed_list`` của mọi luồng ``rknn_server`` bằng CPU đã ghim ở cả hai lần đọc, luồng bận có CPU cuối khối đúng CPU đó, và ngắt NPU rơi hết vào CPU đích. Một phiên làm ``rknn_server`` có 10 luồng (9 luồng trước phiên), nên mã đọc lại và ghim lại sau ``init_runtime``. Mỗi khối đếm đúng {_eb['1']['irq_total']} ngắt NPU, bằng 550 lần gọi nhân 63, nên chính lần chạy này cũng xác nhận mỗi lần ``eval_perf`` là một lần suy luận. Luồng bận là ``listener`` ở 8 khối và luồng chính ``rknn_server`` ở 6 khối. ``init_runtime`` mất {f(min(_init), 2)} đến {f(max(_init), 2)} giây mỗi khối (``bench/onboard_e2e/driver.log``).

6.3. So sánh với đường C API (E2d)
----------------------------------

Mỗi ô được so với cùng ô của E2d theo cả kết quả chính (mất, còn mức chậm hoặc lẫn lộn) và kết quả mức nhanh.
""")
w(table(["Ô (ứng dụng, ngắt)", "Kết quả chính ``eval_perf``", "Mức nhanh ``eval_perf``", "Kết quả chính C API", "Mức nhanh C API", "Trung vị ``eval_perf`` (ms)", "Trung vị C API (ms)", "Hiệu (ms)", "Kết luận"],
        [[f"({c[1]}, {c[3]})", r["e2e_primary"], r["e2e_fast"], r["e2d_primary"], r["e2d_fast"], f(r["median_e2e"], 3), f(r["median_e2d"], 3), f"{r['diff_ms']:+.3f}", r["verdict"]]
         for c, r in E2E["comparison"].items()], [14, 16, 16, 16, 16, 14, 14, 10, 14]))
w(f"""
Theo quy tắc: trong sáu ô đã thử, đường ``eval_perf`` cho cùng kết quả vị trí với đường C API. Ngoại lệ lệch mức đồng đều không áp dụng vì hiệu trung vị không cùng dấu và không phải cả sáu hiệu đều lớn hơn 1.25 ms.

Mô tả, không phải kết quả theo quy tắc:

- Hiệu trung vị (``eval_perf`` trừ C API) là {f(E2E['comparison']['s4i4']['diff_ms'], 2)} ms ở (4, 4) và {f(E2E['comparison']['s4i0']['diff_ms'], 2)} ms ở (4, 0), còn ở bốn ô có ``rknn_server`` ghim ở CPU0 hoặc CPU1 ((0, 0), (0, 4), (1, 0), (1, 4)) hiệu nằm trong {f(min(E2E['comparison'][c]['diff_ms'] for c in ('s0i0', 's0i4', 's1i0', 's1i4')), 2)} đến {f(max(E2E['comparison'][c]['diff_ms'] for c in ('s0i0', 's0i4', 's1i0', 's1i4')), 2)} ms. Chưa biết vì sao.
- Điều kiện A (không ghim) có mức chậm {pct(_eb["1"]['slow'], 1)} và {pct(_eb["14"]['slow'], 1)} ở hai khối, độ lệch chuẩn {f(_eb["1"]['std_ms'], 2)} và {f(_eb["14"]['std_ms'], 2)} ms, tức dao động mạnh như đường C API.
- Ba ô (0, 0), (0, 4), (1, 4) ở mức giữa với độ lệch chuẩn nhỏ ({f(min(b['std_ms'] for b in _eb.values() if b['cond'] in ('s0i0', 's0i4', 's1i4')), 3)} đến {f(max(b['std_ms'] for b in _eb.values() if b['cond'] in ('s0i0', 's0i4', 's1i4')), 3)} ms). Ô (4, 0) cũng ở mức giữa (99.6% và 100%) nhưng độ lệch chuẩn lớn hơn ({f(min(b['std_ms'] for b in _eb.values() if b['cond'] == 's4i0'), 3)} và {f(max(b['std_ms'] for b in _eb.values() if b['cond'] == 's4i0'), 3)} ms).

Giới hạn theo quy tắc: mỗi ô chỉ có hai khối kề nhau theo thời gian, một board, một lần khởi động. Tiến trình root phía board thăm dò tệp lệnh mỗi 0.2 giây trên CPU7 trong lúc đo, còn E2d không có tiến trình đó, và CPU7 không nằm trong các ô đã thử (chỉ điều kiện A, vốn chỉ để mô tả, có thể bị ảnh hưởng). Các lần gọi cách nhau khoảng 0.22 giây nên không so trực tiếp với đường C API chạy liên tiếp về thời gian nghỉ của CPU. Các phát biểu chỉ nói về vị trí và không được đọc thành hiệu ứng của cụm CPU hay của tần số, vì CPU0 đến 3 chạy 1.8 GHz, CPU4 đến 5 chạy 2.256 GHz và CPU6 đến 7 chạy 2.304 GHz.

6.4. Thêm ô CPU lớn (X6)
------------------------
""")
X6 = O["x6"]
_x6b = X6["blocks"]
assert len(_x6b) == 14 and all(b["realized"] and b["n"] == 500 for b in _x6b.values())
w(f"""
X6 (ngày 2026-10-31, quy tắc ``bench/onboard_x6/rule.txt`` viết trước dữ liệu) chạy cùng cách đo của E2e ở bảy ô CPU lớn: (4, 4) làm đối chứng, (5, 4), (6, 4), (7, 4), (5, 5), (6, 6), (7, 7). Tiến trình root chạy ở CPU3 (không thuộc ô nào). Cả 14 khối thực hiện đúng (mọi luồng ``rknn_server`` ở CPU đã ghim ở hai lần đọc, ngắt NPU ở CPU đích). Tiến trình root chỉ đọc danh sách CPU của các luồng ở hai thời điểm mỗi khối, nên vi phạm ngắn giữa hai lần đọc có thể không thấy.
""")
w(table(["Ô (rknn_server, ngắt)", "Kết quả ``eval_perf``", "Mức nhanh", "Kết quả C API (E2d)", "Trung vị ``eval_perf`` (ms)", "Trung vị C API (ms)", "Hiệu (ms)", "Kết luận"],
        [[f"({c[1]}, {c[3]})", r["e2e_primary"], r["e2e_fast"], f"{r['e2d_primary']}, {r['e2d_fast']}", f(r["median_e2e"], 3), f(r["median_e2d"], 3), f"{r['diff_ms']:+.3f}", r["verdict"]]
         for c, r in X6["comparison"].items()], [14, 16, 16, 22, 14, 14, 10, 14]))
w(f"""
Theo quy tắc: {"trong bảy ô CPU lớn đã thử, đường ``eval_perf`` cho cùng kết quả vị trí với đường C API" if X6["same_all"] else "các ô khác kết quả: " + ", ".join(X6["different"]) if X6["different"] else "không so được (" + ("lệch mức đồng đều" if X6["uniform_offset"] else "khối không thực hiện đúng") + ")"}.
""")
w(f"""
7. Kết luận chung
=================

Kết quả theo quy tắc của từng thí nghiệm nằm ở Tóm tắt và mục 2 đến 6 (bản đồ vị trí ở mục 5, đường ``eval_perf`` ở mục 6). Mục này chỉ gom những gì các thí nghiệm cùng cho thấy, vẫn là phát biểu về vị trí trong các ô đã thử:

- Mức nhanh ổn định đạt ở bảy ô đã thử của E2d, gồm ô (4, 4). Ở ô (4, 4), cả {len(_c44)} khối của E2b, E2c, E2d và E2e không có lần chạy chậm nào. Trên đường C API, trung vị các khối của ô này từ {f(min(b['median'] for b in _c44_capi), 2)} đến {f(max(b['median'] for b in _c44_capi), 2)} ms, độ lệch chuẩn tối đa {f(sorted(b['std_ms'] for b in _c44_capi)[-2], 3)} ms trừ một khối của E2d ({f(max(b['std_ms'] for b in _c44_capi), 3)} ms).

X4 về sau đo đúng điều kiện này trên đường ``eval_perf`` (giao thức P2): cổng A5 và A8 đạt, còn giao thức gốc chạy lại trên LAN thì không (:doc:`07-giao-thuc-p2-va-do-mo-rong`, mục 2). Điều kiện đo đề xuất cho các phép so sánh sau này (đề xuất của người viết trang này, chưa phải giao thức đã duyệt): ghim tiến trình đo (hoặc ``rknn_server``) và cả ba ngắt NPU vào CPU4, dừng ``irqbalance`` trong lúc đo, rồi khôi phục. Căn cứ: ô (4, 4) không có lần chạy chậm ở cả bốn thí nghiệm E2b đến E2e và đạt mức nhanh ở cả hai đường đo. Điều này nhất quán với hướng dẫn của hãng gắn ứng dụng và ngắt NPU vào lõi CPU lớn [T1 UG232 tr.75], nhưng hướng dẫn đó viết cho chạy đa nhân (mục 1), còn mọi phép đo ở đây là ``CORE_0``, và nó không giải thích cơ chế. Giới hạn: một board, E2b đến E2e chạy trong cùng một lần khởi động (uptime ghi ở ``bench/onboard_e2b/runtime_facts.txt`` và ở dòng trạng thái đầu ``progress.txt`` của E2c, E2d, E2e), governor của NPU và DDR ở E2e khác E2d (cùng tần số), và ở ô (4, 4) đường ``eval_perf`` lệch {f(E2E['comparison']['s4i4']['diff_ms'], 2)} ms so với đường C API. Dùng điều kiện này để đo lại A5 và A8 sẽ là một giao thức mới, không làm cổng A8 gốc đạt.

8. Điều chưa biết và giới hạn
=============================

- Cơ chế gây ba mức độ trễ. E2 cho thấy liên hệ với vị trí ngắt NPU, vị trí tiến trình và trạng thái ``cpu-sleep``, nhưng chưa đo độ trễ từng ngắt. E2b cho thấy khi dừng ``irqbalance`` thì B thực hiện đúng, nhưng B đổi ba yếu tố cùng lúc. E2c (thí nghiệm tách) không đọc được yếu tố vì kiểm tra hợp lệ viết trước không đạt (C còn 1.2% mức chậm ở một khối, quá ngưỡng 0.01). E2d (bản đồ 20 điều kiện) đã đọc được vị trí nhưng chưa nói được cơ chế, và mẫu theo cụm CPU cũng là mẫu theo xung nhịp (1.8, 2.256 và 2.304 GHz), nên chưa tách được cụm khỏi tần số. Mức nhanh và mức giữa sau can thiệp (16.3, 17.4, 18.9 và 19.2 ms) chưa giải thích được.
- Quan hệ giữa dao động của ``eval_perf`` qua ``rknn_server`` và dao động đo trên board. E2e (mục 6) ghim ``rknn_server`` và ngắt NPU trên đường ``eval_perf``: trong sáu ô đã thử cho cùng kết quả vị trí với đường C API, nhưng hiệu trung vị không đồng đều (từ {f(min(_DIFFS), 2)} đến {f(max(_DIFFS), 2)} ms) và lý do chưa biết.
- Đường ``eval_perf`` đã thử ở 12 ô khác nhau (sáu ô của E2e và sáu ô CPU lớn mới của X6, mục 6.4, ô (4, 4) có ở cả hai). Chưa thử ngắt ở CPU1 đến CPU3, hay ``rknn_server`` ở CPU2, CPU3.

9. Nguồn
========

- T1: ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (UG232 tr.75, mục 5.3.3).
- T3 board và PC: ``results/onboard_*`` (mục 10 đến 14 của tệp ``.md``), ``ai/automation/runs/{RUN}/bench/onboard_e2/`` (gồm ``progress.txt``, ``board_facts.txt``, ``e2_run.sh``), ``bench/onboard_e2b/`` (gồm ``progress.txt``, ``rule.txt``, ``rule_note.txt``, ``runtime_facts.txt``, ``e2b_run.sh``), ``bench/onboard_e2c/`` (gồm ``progress.txt``, ``rule.txt``, ``e2c_run.sh``), ``bench/onboard_e2d/`` (gồm ``progress.txt``, ``rule.txt``, ``e2d_run.sh``), ``bench/onboard_e2e/`` (gồm ``rule.txt``, ``progress.txt``, ``driver.log``, ``e2e_daemon.sh``, ``e2e_driver.py``), ``bench/extra_tier1_lan_timing.txt``, ``bench/extra_link_facts.txt``. Mã: ``ai/board/rknn_perf_bench.c``, ``ai/automation/analyze_onboard.py``. Trang này được sinh bởi ``docs/tools/gen_latency_results_page.py``.
""")


# Page 06: X1 and X2 (trace decomposition and interventions), X3 (pacing)
X1 = json.loads((RES / f"onboard_x1_{RUN}_int8_CORE_0.json").read_text())
X2 = json.loads((RES / f"onboard_x2_{RUN}_int8_CORE_0.json").read_text())
X3 = json.loads((RES / f"onboard_x3_{RUN}_int8_CORE_0.json").read_text())
assert all(b["realized"] for b in X3["blocks"]) and len(X3["blocks"]) == 24 and all(v["comparable"] for v in X3["cells"].values())
assert X3["verdict"] == "chưa kết luận" and sum(1 for v in X3["cells"].values() if abs(v["f"]) <= 0.25) == 5
_x3d = [v["G"] - v["B"] for v in X3["cells"].values()]
_x1b, _x2b = X1["blocks"], X2["blocks"]
assert len(_x1b) == 12 and all(b["realized"] and b["closure_ok_share"] == 1.0 and b["overrun_delta"] == 0 for b in _x1b.values())
assert len(_x2b) == 16 and all(b["realized"] and b["closure_ok_share"] == 1.0 and b["overrun_delta"] == 0 for b in _x2b.values())
assert X1["r1"]["a4i0 vs a4i4"]["verdict"].endswith("phần N") and X1["r1"]["a1i0 vs a1i4"]["verdict"].endswith("phần N")
assert all(X1["r1"][k]["verdict"] == "chưa kết luận" for k in ("a1i0 vs a4i4", "a0i0 vs a4i4", "a1i4 vs a4i4"))
assert X1["r2"]["statement"] == "chỉ báo số" and X1["r3"]["caveat"] is True
assert X2["s1"]["verdict"] == "làm mất" and X2["s2"]["verdict"] == "chưa kết luận" and X2["s3"]["verdict"] == "chưa kết luận"
assert X2["labels"] == {"U1b": "CHƯA BIẾT", "U3": "CHƯA BIẾT"}
_s2r = [h["gs"] / h["g"] for h in X2["s2"]["halves"]]
assert 0.199 < min(_s2r) and max(_s2r) < 0.202 and max(_s2r) > 0.2  # text: 0.200 and 0.201, half 2 just above the 0.2 bound


def _x1cell(c):
    bl = [b for b in _x1b.values() if b["cond"] == c]
    return {k: statistics.mean(b["median"][k] for b in bl) for k in ("T", "C", "N", "D", "P")}, bl


def _x2cell(c):
    bl = [b for b in _x2b.values() if b["cond"] == c]
    return {k: statistics.mean(b["median"][k] for b in bl) for k in ("T", "C", "N", "D", "P")}, bl


docs["06"] = []
w = docs["06"].append
_t06 = "Cơ chế các mức độ trễ"
w(f"""{"*" * len(_t06)}
{_t06}
{"*" * len(_t06)}

.. admonition:: Trang này trả lời

   - Ở mỗi vị trí (CPU của tiến trình đo, CPU nhận ngắt NPU), thời gian của một lần ``rknn_run`` gồm những phần nào, và phần nào mang chênh lệch giữa mức nhanh, mức giữa và mức chậm?
   - Tắt ``cpu-sleep`` ở một CPU, hoặc hạ xung nhịp CPU4, có làm mất phần chênh lệch đó không?
   - Nhịp gọi khoảng 0.22 giây của ``eval_perf`` có giải thích chênh lệch giữa đường ``eval_perf`` và đường C API không?

.. admonition:: Tóm tắt

   - Mỗi lần chạy được tách bằng ftrace thành bốn phần: C (tiến trình đo đang chạy trên CPU), N (từ lúc tiến trình ngủ chờ NPU tới lúc trình xử lý ngắt NPU bắt đầu), D (từ lúc trình xử lý ngắt bắt đầu tới lúc tiến trình chạy lại), P (bị chiếm CPU khi đang sẵn sàng). Bốn phần cộng lại khớp thời gian đo ở 100% số lần chạy của cả 28 khối X1 và X2.
   - Khi chỉ dời ngắt NPU từ CPU4 sang CPU0 (ứng dụng ở CPU4 hoặc ở CPU1), phần tăng nằm chủ yếu ở N ({pct(X1['r1']['a4i0 vs a4i4']['halves'][0]['ratios']['N'], 0)} và {pct(X1['r1']['a1i0 vs a1i4']['halves'][0]['ratios']['N'], 0)} chênh lệch ở nửa 1). Tắt ``cpu-sleep`` riêng ở CPU0 làm phần tăng ở N giảm từ {f(X2['s1']['halves'][0]['g'], 2)} xuống {f(X2['s1']['halves'][0]['gs'], 2)} ms (nhãn "làm mất" theo quy tắc viết trước).
   - Khi chỉ dời ứng dụng từ CPU4 sang CPU1 (ngắt ở CPU4), phần tăng chia giữa C và D. D mỗi ngắt tăng từ trung vị {f(_x1b['6']['d_us']['median'], 0)} µs lên {f(_x1b['5']['d_us']['median'], 0)} µs. Tắt ``cpu-sleep`` ở CPU1 làm phần tăng ở D giảm từ {f(X2['s2']['halves'][0]['g'], 2)} xuống {f(X2['s2']['halves'][0]['gs'], 2)} ms, nhưng tỉ lệ còn lại là {f(min(_s2r), 3)} và {f(max(_s2r), 3)}, vượt ngưỡng 0.2 ở một nửa, nên theo quy tắc là "chưa kết luận".
   - Hạ CPU4 về 1.8 GHz làm C tăng {f(X2['s3']['halves'][0]['r'], 2)} lần, nằm giữa tỉ lệ xung nhịp {f(X2['s3']['clock_ratio'], 2)} và tỉ lệ C giữa CPU1 và CPU4 ({f(X2['s3']['halves'][0]['c1'], 2)}), nên "chưa kết luận" về việc xung nhịp có giải thích phần C hay không.
   - Chạy C API với nhịp nghỉ 220 ms (X3) chỉ làm thời gian đổi {f(min(_x3d), 2)} đến {f(max(_x3d), 2)} ms, không tiến về thời gian ``eval_perf``. Theo quy tắc là "chưa kết luận" (một ô có f = {f(X3['cells']['a4i0']['f'], 2)}, vượt ±0.25).
   - Đây là phát biểu về thời gian và vị trí, kèm kết quả can thiệp. Cơ chế phần cứng vẫn chưa biết. Mọi số đo có trace kèm lưu ý "đo khi có trace" (ô A lệch {f(X1['r3']['cells']['A']['gap'], 2)} ms so với E2d, các ô ghim lệch tối đa {f(max(abs(v['gap']) for k, v in X1['r3']['cells'].items() if k != 'A'), 2)} ms).

Trang này là phần đo cơ chế của nhóm. Kết quả vị trí (E2 đến E2e) nằm ở :doc:`05-thu-ghim-cpu-va-ngat`, các mức độ trễ ở :doc:`04-cac-muc-do-tre`. Quy ước nhãn ở :doc:`04-cac-muc-do-tre`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Cách đo
==========

X1 và X2 chạy trên đường C API (``rknn_perf_bench``, ``CORE_0``, ảnh đầu vào toàn 0), ``irqbalance`` dừng, tần số khóa, ftrace với đồng hồ ``mono`` (cùng đồng hồ với cột ``t_us`` của CSV), bộ đệm tối thiểu 32768 KB mỗi CPU. Sự kiện ghi: ``irq_handler_entry`` và ``irq_handler_exit`` lọc theo ngắt 36, ``sched_wakeup`` và ``sched_switch`` lọc theo luồng ``rknn_perf_bench``, ``cpu_idle`` trên mọi CPU. Một phép thử 7 lần chạy (chỉ ghi tên luồng, không ghi thời gian) cho thấy ``rknn_perf_bench`` là luồng duy nhất được chuyển vào CPU, khoảng 63 lần mỗi lần chạy, khớp 63 ngắt NPU mỗi lần chạy. Mỗi khối 50 lần làm nóng rồi 300 lần đo, nửa 2 là thứ tự đảo ngược của nửa 1.

Cách tách một lần chạy (định nghĩa trong ``bench/onboard_x1/rule.txt``, viết trước dữ liệu): C là thời gian luồng ở trên CPU. Khi luồng ngủ (trạng thái S hoặc D) rồi được chuyển vào lại, ngắt kết thúc khoảng chờ là ngắt 36 cuối cùng trong khoảng đó: N là từ lúc ngủ tới ngắt đó, D là từ ngắt đó tới lúc chạy lại. P là thời gian bị chiếm CPU khi đang sẵn sàng (trạng thái R). Khối thực hiện đúng khi ứng dụng và ngắt ở đúng CPU (ít nhất 99%), bốn phần cộng lại khớp thời gian đo trong 2% ở ít nhất 95% số lần chạy, và trace không mất sự kiện nào. Các ngưỡng 0.8, 1.2, 0.9, 0.1, 2% và 95% là ngưỡng mới chọn cho quy tắc này, chưa qua người dùng duyệt. X2 thêm kiểm can thiệp: file ``state1/disable`` và governor của ``policy4`` đọc lại trước và sau mỗi khối, và trong trace tỉ lệ lần CPU đích vào ``cpu-sleep`` phải không quá 0.01.

2. X1: thời gian tăng nằm ở phần nào
====================================
""")
_rows06 = []
for _c in ("A", "a4i4", "a4i0", "a1i4", "a0i0", "a1i0"):
    _m, _bl = _x1cell(_c)
    _rows06.append([_c, f(_m["T"], 3), f(_m["C"], 3), f(_m["N"], 3), f(_m["D"], 3), f(_m["P"], 3),
                    f(statistics.mean(b["d_us"]["median"] for b in _bl), 0), f(statistics.mean(b["app_idle1_median"] for b in _bl), 2), f(statistics.mean(b["irq_idle1_median"] for b in _bl), 2)])
w(table(["Ô (ứng dụng, ngắt)", "T (ms)", "C (ms)", "N (ms)", "D (ms)", "P (ms)", "D mỗi ngắt, trung vị (µs)", "Tỉ lệ CPU ứng dụng vào cpu-sleep khi chờ", "Tỉ lệ CPU ngắt ở cpu-sleep khi ngắt tới"],
        _rows06, [12, 9, 9, 9, 9, 9, 14, 15, 15]))
w(f"""
Số là trung bình của trung vị hai khối (một khối mỗi nửa). Cột "cpu-sleep" là trung vị theo lần chạy của tỉ lệ các khoảng chờ mà CPU tương ứng vào trạng thái ``cpu-sleep`` (mô tả, R2 không dùng để kết luận).

Theo quy tắc R1 (so từng cặp với một ô, ở cả hai nửa, phần nào chiếm 0.8 đến 1.2 chênh lệch thời gian):
""")
w(table(["Cặp", "Chênh T nửa 1 (ms)", "Tỉ lệ C, N, D, P nửa 1", "Chênh T nửa 2 (ms)", "Kết luận theo quy tắc"],
        [[k, f"{v['halves'][0]['dT']:+.3f}", ", ".join(f"{p} {f(v['halves'][0]['ratios'][p], 2)}" for p in ("C", "N", "D", "P")), f"{v['halves'][1]['dT']:+.3f}", v["verdict"]] for k, v in X1["r1"].items()],
        [16, 14, 30, 14, 26]))
w(f"""
- Hai cặp chỉ dời ngắt (``a4i0`` so với ``a4i4``, ``a1i0`` so với ``a1i4``): phần tăng nằm chủ yếu ở N. Trong hai ô ``a4i0`` và ``a1i0`` (ngắt ở CPU0, ứng dụng ở CPU khác), CPU0 đang ở ``cpu-sleep`` khi ngắt tới ở {f(min(b['irq_idle1_median'] for b in _x1b.values() if b['cond'] in ('a4i0', 'a1i0')), 2)} đến {f(max(b['irq_idle1_median'] for b in _x1b.values() if b['cond'] in ('a4i0', 'a1i0')), 2)} số lần, còn khi ngắt ở CPU4 là 0 (mô tả).
- Cặp chỉ dời ứng dụng (``a1i4`` so với ``a4i4``): chênh lệch chia giữa C ({f(X1['r1']['a1i4 vs a4i4']['halves'][0]['ratios']['C'], 2)}) và D ({f(X1['r1']['a1i4 vs a4i4']['halves'][0]['ratios']['D'], 2)}), không phần nào đạt 0.8, nên "chưa kết luận". Ô chậm ``a1i0`` mang cả hai loại tăng.
- R2: tỉ lệ CPU ứng dụng vào ``cpu-sleep`` khi chờ ở ô ``a1i0`` là {f(X1['r2']['a1i0'][0], 2)} ở cả hai khối, dưới ngưỡng 0.9, nên chỉ báo số.
- R3: trung vị T có trace so với E2d: {', '.join(f"{k} {f(v['x1'], 2)} so với {f(v['e2d'], 2)}" for k, v in X1['r3']['cells'].items())} ms. Ô A lệch quá 1.25 ms (ô A không ghim, dao động mạnh ở mọi thí nghiệm), nên theo quy tắc mọi phát biểu của X1 kèm lưu ý "đo khi có trace, mức có thể khác khi không trace".

3. X2: can thiệp từng yếu tố
============================

X2 dùng cùng cách đo, thêm các ô can thiệp: ``a4i0s`` (tắt ``cpu-sleep`` riêng ở CPU0), ``a1i4s`` (tắt riêng ở CPU1), ``a1i0s`` (tắt ở CPU0 và CPU1), ``a4i4f`` (CPU4 và CPU5 ở 1.8 GHz với governor ``userspace``). Cả 16 khối thực hiện đúng, kể cả kiểm can thiệp (tỉ lệ CPU đích vào ``cpu-sleep`` trong trace bằng 0 ở mọi khối có tắt).
""")
_rows06b = []
for _c in ("a4i4", "a4i0", "a4i0s", "a1i4", "a1i4s", "a4i4f", "a1i0", "a1i0s"):
    _m, _bl = _x2cell(_c)
    _rows06b.append([_c, f(_m["T"], 3), f(_m["C"], 3), f(_m["N"], 3), f(_m["D"], 3), f(statistics.mean(b["d_us"]["median"] for b in _bl), 0)])
w(table(["Ô", "T (ms)", "C (ms)", "N (ms)", "D (ms)", "D mỗi ngắt, trung vị (µs)"], _rows06b, [14, 12, 12, 12, 12, 18]))
w(f"""
Kết luận theo quy tắc viết trước (``bench/onboard_x2/rule.txt``):

- S1 (ngắt ở CPU0): phần tăng ở N so với ``a4i4`` là {f(X2['s1']['halves'][0]['g'], 2)} và {f(X2['s1']['halves'][1]['g'], 2)} ms ở hai nửa, còn {f(X2['s1']['halves'][0]['gs'], 2)} và {f(X2['s1']['halves'][1]['gs'], 2)} ms khi tắt ``cpu-sleep`` ở CPU0. Nhãn: **làm mất**.
- S2 (ứng dụng ở CPU1): phần tăng ở D là {f(X2['s2']['halves'][0]['g'], 2)} và {f(X2['s2']['halves'][1]['g'], 2)} ms, còn {f(X2['s2']['halves'][0]['gs'], 2)} và {f(X2['s2']['halves'][1]['gs'], 2)} ms khi tắt ``cpu-sleep`` ở CPU1. Tỉ lệ còn lại {f(_s2r[0], 3)} và {f(_s2r[1], 3)}, ngưỡng là 0.2 và nhãn cần cả hai nửa cùng không vượt, nên nhãn là **chưa kết luận**. Ngưỡng không sửa sau khi thấy dữ liệu.
- S3 (xung nhịp): C của ``a4i4f`` gấp {f(X2['s3']['halves'][0]['r'], 2)} và {f(X2['s3']['halves'][1]['r'], 2)} lần ``a4i4``, trong khi tỉ lệ xung nhịp là {f(X2['s3']['clock_ratio'], 2)} và C của ``a1i4`` gấp {f(X2['s3']['halves'][0]['c1'], 2)} lần. Nhãn: **chưa kết luận**. Phép tách này chỉ làm được một chiều vì cụm nhỏ không lên được 2.256 GHz. Ở ``a4i4f`` CPU nhận ngắt cũng bị hạ xung nhịp, nên N và D cũng đổi (mô tả, S3 chỉ đọc C).
- S4 (mô tả): T của ``a1i0s`` là {', '.join(f(x, 2) for x in X2['s4']['a1i0s'])} ms so với {', '.join(f(x, 2) for x in X2['s4']['a1i0'])} ms của ``a1i0`` và {', '.join(f(x, 2) for x in X2['s4']['a4i4'])} ms của ``a4i4``.

Theo bảng nhãn ghi trước trong quy tắc: độ trễ từng ngắt (U1a) và nơi thời gian tăng (U2) là "trả lời bằng đo". Câu "mức chậm mất khi tắt ``cpu-sleep`` ở CPU tương ứng" (U1b) cần cả S1 và S2 cùng "làm mất", nên là "vẫn chưa biết". Tách xung nhịp khỏi vị trí (U3) là "vẫn chưa biết". Cơ chế phần cứng (vì sao thoát ``cpu-sleep`` làm chậm ngắt và đánh thức) không được đo và vẫn chưa biết. Từ khóa đề xuất để tìm tài liệu: "ARM cpuidle exit latency interrupt latency RK3588", "PSCI CPU suspend wakeup latency Cortex-A55", "NPU interrupt affinity latency embedded Linux".
""")
w(f"""
4. X3: nhịp gọi và chênh lệch giữa hai đường đo
===============================================

Đường ``eval_perf`` (E2e) và đường C API (E2d) lệch nhau từ {f(min(_DIFFS), 2)} đến {f(max(_DIFFS), 2)} ms ở cùng ô. Các lần gọi ``eval_perf`` cách nhau khoảng 0.22 giây, còn C API chạy liên tiếp. X3 chạy lại C API ở sáu ô của E2e, mỗi ô một khối liên tiếp (B) và một khối nghỉ 220 ms sau mỗi lần chạy (G, chu kỳ khoảng 240 ms), đảo thứ tự ở nửa 2. Một ô chỉ được xét khi B còn khớp E2d trong 0.25 ms. Tỉ số f = (G - B) / (E - B), với E là trung vị ``eval_perf`` của ô ở E2e. Quy tắc ``bench/onboard_x3/rule.txt`` (ngưỡng 0.25 ms, 0.5, 1.5 và 0.25 là số mới, chưa qua người dùng duyệt).
""")
w(table(["Ô", "B, liên tiếp (ms)", "G, nghỉ 220 ms (ms)", "E, eval_perf ở E2e (ms)", "R, E2d (ms)", "f"],
        [[c, f(v["B"], 3), f(v["G"], 3), f(v["E"], 3), f(v["R"], 3), f(v["f"], 2)] for c, v in X3["cells"].items()], [10, 16, 16, 18, 14, 10]))
w(f"""
Cả 24 khối thực hiện đúng và cả sáu ô đều xét được. Theo quy tắc: **chưa kết luận**, vì f nằm trong khoảng ±0.25 ở 5 trên 6 ô nhưng ô ``a4i0`` là {f(X3['cells']['a4i0']['f'], 2)}. Mô tả: giãn nhịp làm thời gian C API đổi từ {f(min(_x3d), 2)} đến {f(max(_x3d), 2)} ms, không tiến về thời gian ``eval_perf`` ở các ô có ứng dụng ở CPU0 hoặc CPU1 (ở đó ``eval_perf`` thấp hơn khoảng 1 ms). Vì sao hai đường lệch nhau vẫn chưa biết.

5. Điều chưa biết và giới hạn
=============================

- Phần N mà việc tắt ``cpu-sleep`` ở CPU0 loại bỏ là {f(X2['s1']['halves'][0]['g'] - X2['s1']['halves'][0]['gs'], 2)} ms mỗi lần chạy, chia cho 63 ngắt là khoảng {f((X2['s1']['halves'][0]['g'] - X2['s1']['halves'][0]['gs']) * 1000 / 63, 0)} µs mỗi ngắt (số suy ra, không đo trực tiếp từng ngắt). N gồm cả thời gian NPU chạy, nên trace phần mềm ở đây không phân biệt được phần tăng nằm ở NPU hay ở việc ngắt được phục vụ muộn. Cơ chế phần cứng hoặc firmware vẫn chưa biết.
- Phần tăng ở D khi ứng dụng ở CPU1 có mất hẳn khi tắt ``cpu-sleep`` ở CPU1 không: S2 còn {f(min(_s2r), 3)} đến {f(max(_s2r), 3)} so với ngưỡng 0.2.
- Xung nhịp có giải thích phần C giữa CPU1 và CPU4 không (S3 chưa kết luận, chỉ tách được một chiều).
- Vì sao đường ``eval_perf`` lệch đường C API (X3 chưa kết luận, nhịp gọi không đưa C API về gần ``eval_perf``).
- Mọi số ở mục 2 và 3 đo khi có trace. Các ô ghim lệch E2d tối đa {f(max(abs(v['gap']) for k, v in X1['r3']['cells'].items() if k != 'A'), 2)} ms.
- Ảnh hưởng của tải CPU khác (ứng dụng khác chạy cùng lúc) lên các mức chưa được đo trong giai đoạn 1 (U27). Từ khóa đề xuất: "NPU latency CPU contention interrupt affinity RK3588".
- Một board, một lần khởi động (E2b đến X3), ``CORE_0``, một mô hình.

6. Nguồn
========

- T3 board: ``results/onboard_x1_*``, ``results/onboard_x2_*``, ``results/onboard_x3_*`` và ``ai/automation/runs/{RUN}/bench/onboard_x1/``, ``onboard_x2/``, ``onboard_x3/`` (mỗi thư mục có ``rule.txt``, ``progress.txt``, script chạy, trace nén hoặc CSV). Mã phân tích: ``ai/automation/analyze_trace_x1.py`` (X1 và X2), ``ai/automation/analyze_x3.py``.
- T1 mã nguồn: không có trích dẫn trong trang này.
""")


# Page 07: X4 (P2, sessions, masks, log), X5 (inputs and weights), X7 (mAP INT8)
X4 = json.loads((RES / f"onboard_x4_{RUN}_int8_CORE_0.json").read_text())
X5 = json.loads((RES / f"onboard_x5_{RUN}_int8_CORE_0.json").read_text())
_p1, _p2 = X4["protocols"]["p1lan"], X4["protocols"]["p2"]
assert _p1["all_realized"] and _p2["all_realized"] and len(_p1["sessions"]) == 10 and len(_p2["sessions"]) == 10
assert X5["all_realized"]
_m = X4["masks"]
docs["07"] = []
w = docs["07"].append
_t07 = "Giao thức P2 và đo mở rộng"
w(f"""{"*" * len(_t07)}
{_t07}
{"*" * len(_t07)}

.. admonition:: Trang này trả lời

   - Nếu ghim ``rknn_server`` và ngắt NPU vào CPU4 (giao thức P2), cổng A5 và A8 có đạt không, so với giao thức gốc chạy lại trên LAN (P1-LAN)?
   - Lần gọi ``eval_perf`` đầu tiên, hằng số mỗi dòng ở chế độ debug, ``CORE_0`` so với ``AUTO`` và ``CORE_0_1_2``, mức log, giá trị đầu vào và trọng số có làm đổi thời gian không?
   - Độ chính xác của chính mô hình INT8 được đo latency là bao nhiêu, và mức giảm so với FP32 đi theo lượng tử hóa hay theo đường suy luận?

.. admonition:: Tóm tắt

   - A5 và A8 gốc (qua relay, ngày 2026-10-30) giữ nguyên "không đạt". Trang này báo kết quả của hai giao thức mới chạy trên LAN, không thay kết quả gốc.
   - Cổng P1-LAN: {', '.join(f"{k} {'đạt' if v else 'không đạt'}" for k, v in _p1['gates'].items())}. Cổng P2: {', '.join(f"{k} {'đạt' if v else 'không đạt'}" for k, v in _p2['gates'].items())}. Đọc theo quy tắc viết trước: A5 "{X4['gate_reading']['A5']}", A8 "{X4['gate_reading']['A8']}".
   - Lần gọi đầu: P1-LAN {_p1['u6']}, P2 {_p2['u6']}. Hằng số mỗi dòng: {X4['u10']}.
   - ``AUTO`` so với ``CORE_0``: {_m['AUTO']['verdict']} (hiệu {f(_m['AUTO']['diff_vs_core0_ms'], 2)} ms). ``CORE_0_1_2`` so với ``CORE_0``: {_m['CORE_0_1_2']['verdict']} (hiệu {f(_m['CORE_0_1_2']['diff_vs_core0_ms'], 2)} ms). Mức log: {X4['log']['True']['verdict']}.
   - Giá trị đầu vào: {X5['inputs_verdict']}. Trọng số: {X5['weights_verdict']}.

Kết quả vị trí E2 đến E2e nằm ở :doc:`05-thu-ghim-cpu-va-ngat`, cơ chế ở :doc:`06-co-che-cac-muc-do-tre`, cổng gốc ở :doc:`02-ket-qua-latency-tung-khoi` (mục 4).

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Hai giao thức trên LAN
=========================

Mỗi phiên là lệnh ``benchmark_npu.py`` của kế hoạch (một phiên latency 5 lần ``eval_perf`` với ``perf_debug=False`` và một phiên từng lớp 5 lần với ``perf_debug=True``), chạy trên LAN trực tiếp. P1-LAN giữ điều kiện gốc (không ghim, ``irqbalance`` chạy). P2 ghim mọi luồng ``rknn_server`` và ba dòng ngắt NPU vào CPU4, ``irqbalance`` dừng. Hai giao thức chạy xen kẽ từng phiên, nghỉ 45 giây giữa các phiên (số mới, chưa qua người dùng duyệt). Một tiến trình root trên board (CPU7) đổi chế độ theo yêu cầu và ghi mỗi giây danh sách CPU được phép của từng luồng ``rknn_server``. Phiên 1 đến 3 của mỗi giao thức dùng cho cổng (mã và ngưỡng 5%, 10% của ``aggregate_layers.py`` không đổi), phiên 4 đến 10 dùng cho các câu hỏi khác. Quy tắc: ``bench/onboard_x4/rule.txt``, viết trước dữ liệu.
""")
assert _p1["gates"]["A5"] is False and _p1["gates"]["A8"] is False and all(_p2["gates"].values())
assert all(r["level"] == "fast" for r in _p2["sessions"]) and X4["u10"].startswith("ghim lõi thu hẹp")
assert _m["AUTO"]["verdict"] == "không phân biệt được" and _m["CORE_0_1_2"]["verdict"] == "khác" and X4["log"]["True"]["verdict"].startswith("chưa kết luận")
assert all(x == {"36": 315, "37": 0, "38": 0} for x in _m["AUTO"]["irq_lines_per_session"]) and all(x["37"] > 0 and x["38"] > 0 for x in _m["CORE_0_1_2"]["irq_lines_per_session"])
w(f"""
2. Cổng A1 đến A8 của hai giao thức
===================================
""")
w(table(["Cổng", "P1-LAN (không ghim)", "P2 (ghim CPU4)"], [[k, "đạt" if _p1["gates"][k] else "không đạt", "đạt" if _p2["gates"][k] else "không đạt"] for k in sorted(_p1["gates"])], [12, 24, 24]))
w(f"""
Đọc theo bảng 2 × 2 viết trước trong quy tắc: A5 "{X4['gate_reading']['A5']}", A8 "{X4['gate_reading']['A8']}". Trung vị latency của 10 phiên P2 nằm trong {f(min(r['latency_ms'] for r in _p2['sessions']), 3)} đến {f(max(r['latency_ms'] for r in _p2['sessions']), 3)} ms, cả 10 ở mức nhanh. 10 phiên P1-LAN có {sum(1 for r in _p1['sessions'] if r['level'] == 'slow')} phiên mức chậm, {sum(1 for r in _p1['sessions'] if r['level'] == 'mid')} phiên mức giữa và {sum(1 for r in _p1['sessions'] if r['level'] == 'fast')} phiên mức nhanh (trung vị {f(min(r['latency_ms'] for r in _p1['sessions']), 2)} đến {f(max(r['latency_ms'] for r in _p1['sessions']), 2)} ms), tức các phiên rơi vào các mức khác nhau. Điều này khớp với giải thích "lấy mẫu mức" cho việc A5 gốc không đạt (:doc:`04-cac-muc-do-tre`, mục 1), nay có số đo hỗ trợ (kết quả 2 × 2 cùng phân loại mức của từng phiên). Vì A5 và A8 của P2 đạt, theo kế hoạch FP16 được chạy dưới P2 (mục 6).

Phiên P2 được tính là thực hiện đúng khi mọi dòng log mỗi giây của tiến trình trên board trong khung phiên ở chế độ ghim và không có luồng nào ngoài CPU4, và ít nhất 99% ngắt NPU của phiên ở CPU4. Cả 20 phiên benchmark thực hiện đúng. Log chỉ lấy mẫu mỗi giây, nên vi phạm ngắn hơn khoảng 1 giây có thể không thấy (một vi phạm như vậy đã được thấy ở phiên log, mục 4).

3. Lần gọi đầu, hằng số mỗi dòng, tổng debug
============================================
""")
w(table(["Giao thức", "Lần gọi đầu thấp hơn các lần sau", "Trung vị (lần đầu trừ các lần sau), ms", "Hằng số mỗi dòng (µs), nhỏ nhất đến lớn nhất", "Phiên có tổng debug thấp hơn latency"],
        [[k.upper(), f"{v['first_lower']}/10 ({v['u6']})", f"{v['first_minus_rest_median_ms']:+.3f}", f"{f(min(v['intercepts_us']), 1)} đến {f(max(v['intercepts_us']), 1)}", f"{v['debug_below_latency']}/10"] for k, v in X4["protocols"].items()],
        [12, 24, 22, 24, 18]))
w(f"""
- Lần gọi đầu (U6): trên LAN, theo quy tắc là "không ổn định" ở cả hai giao thức. Đây là đính chính có ngày 2026-10-31 cho quan sát "lần gọi đầu thấp hơn ở cả 5 phiên" của các phiên qua relay (:doc:`04-cac-muc-do-tre`, mục 4.2). Quan sát cũ vẫn đúng với dữ liệu cũ.
- Hằng số mỗi dòng ở chế độ debug (U10): {X4['u10']}. Dưới P2 hằng số khoảng {f(statistics.median(_p2['intercepts_us']), 1)} µs, chênh {f(_p2['intercept_spread_us'], 1)} µs giữa 10 phiên, so với {f(min(_p1['intercepts_us']), 1)} đến {f(max(_p1['intercepts_us']), 1)} µs dưới P1-LAN. Đây là liên hệ với việc ghim lõi, nguyên nhân vẫn chưa biết.
- Tổng debug so với latency (U13): tổng debug thấp hơn latency ở {_p1['debug_below_latency']}/10 phiên P1-LAN và {_p2['debug_below_latency']}/10 phiên P2. Dưới P2 tổng debug luôn cao hơn latency, đúng với câu của hãng "the time-consuming is more than when perf_debug=False" [T1 UG232 tr.177]. Trường hợp B2 cũ (tổng debug thấp hơn) chỉ xuất hiện khi không ghim.

4. CORE_0, AUTO, CORE_0_1_2 và mức log
======================================

Các phiên chỉ đo latency (5 lần ``eval_perf``), dưới P2, xen kẽ 4 vòng cho ba mặt nạ và 3 vòng cho mức log, nghỉ 45 giây.
""")
w(table(["Thiết lập", "Trung vị các phiên (ms)", "Hiệu so với tham chiếu (ms)", "Dòng ngắt dùng (mỗi phiên)", "Kết luận theo quy tắc"],
        [[k, ", ".join(f(x, 3) for x in v["session_medians"]), f"{v['diff_vs_core0_ms']:+.3f}", ", ".join(f"{ln}: {n}" for ln, n in v["irq_lines_per_session"][0].items()), v["verdict"] or "tham chiếu"] for k, v in _m.items()]
        + [[f"verbose={k}", ", ".join(f(x, 3) for x in v["session_medians"]), f"{v['diff_vs_quiet_ms']:+.3f}", "-", v["verdict"] or "tham chiếu"] for k, v in X4["log"].items()],
        [16, 26, 14, 24, 22]))
w(f"""
- ``AUTO`` (U16): {_m['AUTO']['verdict']}. Mọi phiên ``AUTO`` chỉ dùng dòng ngắt 36 (một nhân), như ``CORE_0``.
- ``CORE_0_1_2`` (U22): {_m['CORE_0_1_2']['verdict']}, hiệu {f(_m['CORE_0_1_2']['diff_vs_core0_ms'], 2)} ms ({pct(_m['CORE_0_1_2']['diff_vs_core0_ms'] / statistics.median(_m['CORE_0']['session_medians']), 1)}), đo dưới P2 với cả ba dòng ngắt ở CPU4. Đây là số đo latency, không phải kết luận về đa nhân (cổng G4 và chiến lược S1 đến S3 thuộc giai đoạn 2, :doc:`../02-tang-npu/02-multi-core`).
- Mức log (U19): chưa kết luận, vì một phiên tham chiếu ``verbose=False`` có một giây thấy một luồng ``rknn_server`` ngoài CPU4 (``bench/onboard_x4/analysis_note.txt``). Số đo mô tả: trung vị hai mức log gần như bằng nhau.

5. Giá trị đầu vào và trọng số
==============================

X5 chạy C API ở ô (4, 4) với bốn đầu vào (toàn 0, ngẫu nhiên với seed cố định, hai ảnh test ppe5 đã letterbox) và hai mô hình cùng kiến trúc (seed 0 và seed 1), mỗi điều kiện hai khối 300 lần chạy, thêm một khối tham chiếu thứ hai ở cuối mỗi nửa để kiểm độ trôi. Quy tắc ``bench/onboard_x5/rule.txt`` (ngưỡng 0.05 ms và 0.25 ms là số mới, chưa qua người dùng duyệt).

- Độ trôi giữa hai khối tham chiếu: {f(X5['drift_ms'][0], 3)} và {f(X5['drift_ms'][1], 3)} ms, dưới 0.05 ms.
- Đầu vào (U20): {X5['inputs_verdict']} (chênh lệch tối đa {f(max(abs(x) for v in X5['inputs'].values() for x in v), 3)} ms).
- Trọng số: {X5['weights_verdict']} (chênh lệch tối đa {f(max(abs(x) for v in X5['weights'].values() for x in v), 3)} ms).
""")
X8 = json.loads((RES / f"onboard_x8_{RUN}_CORE_0.json").read_text())
X7 = json.loads((RES / f"eval_x7_{RUN}_int8.json").read_text())
assert X8["all_realized"] and all(all(g.values()) for g in X8["gates"].values()) and 1.6 < X8["fp16_over_int8"] < 1.7
assert X7["sets"]["css_test"]["n_images"] == 82 and X7["sets"]["ppe2286_ext"]["n_images"] == 180
_x7b = X7["x7b"]
assert _x7b["verdict"] == "mức giảm của INT8 chủ yếu đi theo lượng tử hóa" and abs(_x7b["css_test"]["d16_pp"]) < 0.25 and -13.3 < _x7b["css_test"]["d8_pp"] < -13.2 and abs(_x7b["css_test"]["d16_pp"]) <= 0.25 * abs(_x7b["css_test"]["d8_pp"])
w(f"""
6. FP16 dưới P2
===============

Theo kế hoạch, FP16 chỉ chạy khi A8 của INT8 đạt. Điều kiện đó chỉ đạt dưới P2 (mục 2), nên X8 chạy FP16 dưới P2, xen kẽ A B A B A B (A là phiên INT8, B là phiên FP16), nghỉ 45 giây, với file FP16 export ngày 2026-10-31 (``weights/rknn_fp16/``, sha256 ``bd4a8c8a``). Quy tắc ``bench/onboard_x8/rule.txt``. Cả 6 phiên thực hiện đúng. Cổng A1 đến A8 đạt ở cả hai độ chính xác.
""")
w(table(["Độ chính xác", "Trung vị latency các phiên (ms)", "Trung vị chung (ms)"],
        [[p.upper(), ", ".join(f(r["latency_ms"], 3) for r in X8["sessions"] if r["precision"] == p), f(X8["latency_ms"][p], 3)] for p in ("int8", "fp16")], [16, 40, 20]))
w(f"""
FP16 chậm hơn INT8 {f(X8['fp16_minus_int8_ms'], 2)} ms, gấp {f(X8['fp16_over_int8'], 2)} lần, trong cùng một lần chạy xen kẽ. Tỉ lệ thời gian của các khối từ 2% trở lên (mô tả):
""")
w(table(["Khối", "Tỉ lệ INT8", "Tỉ lệ FP16"], [[b, pct(v["int8"], 1), pct(v["fp16"], 1)] for b, v in X8["block_shares"].items()], [12, 16, 16]))
w(f"""
Đây là số đo latency. Việc giữ hay bỏ FP16 không được quyết ở đây.

7. Độ chính xác của mô hình INT8
================================

X7 chấm chính file INT8 được đo latency (sha256 ``a501f94e``), suy luận bằng RKNNLite trên board, chấm điểm trên PC bằng cùng mã và cùng ngưỡng tin cậy với bản FP32 (Evaluation Protocol v1, ``ai/core/evaluator.py``). Quy tắc ``bench/eval_x7/rule.txt``: chỉ báo số, không áp ngưỡng nào (ngưỡng 1.0 pp mAP đã duyệt thuộc cổng G4, giai đoạn 2).
""")
w(table(["Tập", "Số ảnh", "Chỉ số", "INT8", "FP32", "Chênh (điểm %)"],
        [[s, v["n_images"], k, f(v["int8"][k], 4), f(v["fp32"][k], 4), f"{v['diff_pp'][k]:+.2f}"] for s, v in X7["sets"].items() for k in ("precision", "recall", "map50", "map50_95")],
        [14, 8, 14, 12, 12, 14]))
w(f"""
Trên ``css_test``, mAP50-95 của INT8 thấp hơn FP32 {f(-X7['sets']['css_test']['diff_pp']['map50_95'], 2)} điểm phần trăm. Phép so này gộp cả hai khác biệt: lượng tử hóa và đường suy luận (RKNNLite trên board so với PyTorch trên PC). X7b tách chúng bằng cách chấm mô hình FP16 qua đúng đường RKNNLite (``bench/eval_x7b/rule.txt``, viết trước, các số 0.25 và 0.75 là số mới, chưa qua người dùng duyệt): trên ``css_test``, FP16 qua RKNNLite có mAP50-95 {f(_x7b['css_test']['fp16_rknn_map50_95'], 4)}, chênh {f(_x7b['css_test']['d16_pp'], 2)} điểm phần trăm so với FP32, còn INT8 chênh {f(_x7b['css_test']['d8_pp'], 2)}. Theo quy tắc: **{_x7b['verdict']}**. Trên ``ppe2286_ext`` (mô tả) FP16 qua RKNNLite chênh {f(_x7b['ppe2286_ext']['d16_pp'], 2)} và INT8 chênh {f(_x7b['ppe2286_ext']['d8_pp'], 2)}. ``css_test`` chỉ có 82 ảnh và một seed. Mức giảm do lượng tử hóa là phát biểu về kết quả đo, nguyên nhân bên trong lượng tử hóa (hiệu chuẩn hay lớp nhạy) chưa được kiểm. Từ khóa đề xuất: "RKNN INT8 accuracy drop YOLOv8 quantization calibration".

8. Điều chưa biết và giới hạn
=============================

- Mức log (U19): chưa kết luận (mục 4).
- Vì sao hằng số mỗi dòng ở chế độ debug gần như không đổi dưới P2 mà dao động khi không ghim (liên hệ đo được, nguyên nhân chưa biết).
- Nguyên nhân bên trong của mức giảm INT8 (hiệu chuẩn, lớp nhạy, hay phân phối dữ liệu hiệu chuẩn): X7b chỉ cho biết mức giảm đi theo lượng tử hóa, không đi theo đường suy luận RKNNLite (U28). Cập nhật 2026-10-31 (giai đoạn 2): chẩn đoán lượng tử hóa đã khoanh vùng công thức lấy lại gần hết mức rơi (giữ FP16 nhánh giải mã box), xem :doc:`../02-tang-npu/13-ket-qua-luong-tu-hoa`. Nguyên nhân bên trong vẫn chưa biết.
- P2 là giao thức mới chạy trên LAN, chưa qua người dùng duyệt làm giao thức chính. Mọi số ở trang này là một board, một lần khởi động, một mô hình.

9. Nguồn
========

- T1: ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (UG232 tr.177).
- T3 board và PC: ``results/onboard_x4_*``, ``results/latency_per_block_*_p1lan.*``, ``results/latency_per_block_*_p2.*``, ``results/onboard_x5_*``, ``results/onboard_x8_*``, ``results/latency_per_block_*_x8.*``, ``results/eval_x7_*``, ``ai/automation/runs/{RUN}/bench/onboard_x4/``, ``onboard_x5/``, ``onboard_x8/``, ``eval_x7/``, ``ai/automation/runs/{RUN}/eval/``. Mã: ``ai/automation/analyze_x4.py``, ``analyze_x5.py``, ``analyze_x7.py``, ``analyze_x8.py``, ``aggregate_layers.py`` (tham số ``--bench-subdir`` và ``--tag``), ``benchmark_npu.py`` (tham số ``--out-subdir``).
""")

for k, parts in docs.items():
    (OUTDIR / NAMES[k]).write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {NAMES[k]} ({len((OUTDIR / NAMES[k]).read_text().splitlines())} lines)")
