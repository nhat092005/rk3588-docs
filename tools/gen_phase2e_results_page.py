#!/usr/bin/env python3
"""Sinh trang 04-tang-npu-ket-qua/08-so-muc-chua-biet.rst (giai đoạn 2e: nhãn cuối cho các mục chưa biết còn lại) từ kết quả đo, không gõ tay số.

Đọc results/{q2e_pc,q2e_micro,q2e_board,q2l_nodfl}.json, bench/onboard_q2e/h6_*, và results/phase2e_unknowns_inventory.md.
Chạy từ gốc repo chính:  .venv/bin/python docs/tools/gen_phase2e_results_page.py
Lời văn nằm trong script, mọi con số lấy từ file JSON. Các assert bảo vệ những số có trong lời văn.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
RUNS = REPO / "ai" / "automation" / "runs"
SILU = RUNS / "ppe5_yolov8n_baseline_100ep_s0"
Q2E = SILU / "bench" / "onboard_q2e"
OUT = REPO / "docs" / "contents" / "03-phuong-phap" / "04-tang-npu-ket-qua" / "08-so-muc-chua-biet.rst"

PC = json.loads((RES / "q2e_pc.json").read_text())
MI = json.loads((RES / "q2e_micro.json").read_text())
BD = json.loads((RES / "q2e_board.json").read_text())
M7B = json.loads((Q2E / "probe_m7b.json").read_text())["result"]
M7LOG = (Q2E / "probe_m7_console.log").read_text(errors="replace")
assert "core mask = 1 is invalid for batch size: 4, fall back to CORE_AUTO mode" in M7LOG
assert M7B["max_abs_diff_per_image"].count(0.0) == 3 and round(max(M7B["max_abs_diff_per_image"]), 2) == 0.19
m16_before = json.loads((Q2E / "probe_m16.json").read_text())["meminfo_before"]["MemAvailable"]
assert m16_before == 3209
CA = json.loads((RES / "q2e_core_all.json").read_text())


def f(x, d=2):
    return f"{x:.{d}f}"


def table(headers, rows, widths=None):
    out = [".. list-table::", "   :header-rows: 1"]
    if widths:
        out.append("   :widths: " + " ".join(str(w) for w in widths))
    out.append("")
    for line in [headers] + rows:
        for i, cell in enumerate(line):
            out.append(("   * - " if i == 0 else "     - ") + str(cell))
    return "\n".join(out)


# ---- facts
g7 = PC["g7a"]["max_abs_diff"]
assert g7["scale_2.0"]["half_pixel|round_prefer_floor"] == 0 and g7["scale_2.0"]["pytorch_half_pixel|round_prefer_floor"] == 0 and g7["scale_2.0"]["align_corners|round_prefer_floor"] == 0
assert g7["scale_1.5"]["half_pixel|round_prefer_floor"] == 0 and g7["scale_3.0"]["half_pixel|round_prefer_floor"] == 0
assert round(g7["scale_2.0"]["half_pixel|floor"], 2) == 6.57 and round(g7["scale_1.5"]["align_corners|round_prefer_floor"], 2) == 6.17
gb = MI["g7b"]
assert gb["A"]["match_own"] and gb["A"]["match_ref"] and gb["C"]["match_own"] and gb["C"]["match_ref"]
assert (not gb["B"]["match_own"]) and gb["B"]["match_ref"] and round(gb["B"]["ort_own_vs_ref"], 2) == 6.57 and round(gb["B"]["npu_vs_own"], 2) == 6.57
assert all([r["op"] for r in gb[k]["table"]] == ["InputOperator", "Resize", "OutputOperator"] and gb[k]["table"][1]["target"] == "NPU" for k in "ABC")
g10 = PC["g10"]
no_row = sorted(n.rsplit("/", 1)[-1] for n, ok in g10["reshape_nodes_exact"].items() if not ok)
assert no_row == ["Reshape", "Reshape_3", "dfl/Reshape_1"] or no_row == sorted(["Reshape", "Reshape_3", "Reshape_1"]), no_row
assert g10["onnx_nodes"] == 237 and g10["rknn_rows"] == 119 and g10["onnx_ops"]["Reshape"] == 8 and g10["rknn_ops"]["Reshape"] == 7
rs_rows = [n for n in g10["reshape_rows"] if n.endswith("_rs") or "-rs" in n]
assert len(rs_rows) == 2 and 8 - 3 + 2 == 7
assert g10["onnx_ops"]["Split"] == 8 and g10["onnx_ops"]["Slice"] == 4 and g10["rknn_ops"]["Split"] == 9
assert sum(g10["split_nodes_exact"][n] for n in g10["split_nodes_exact"] if n.endswith("Split")) == 8 and sum(g10["split_nodes_exact"][n] for n in g10["split_nodes_exact"] if "Slice" in n) == 0
assert any(n.endswith("Slice_2sp") for n in g10["split_rows"])
g11 = MI["g11"]
r0 = [r for r in g11["CORE_0"]["table"] if r["op"] == "Relu"]
r3 = [r for r in g11["CORE_0_1_2"]["table"] if r["op"] == "Relu"]
assert len(r0) == 1 == len(r3) and r0[0]["target"] == "NPU" == r3[0]["target"] and r0[0]["workload"] == "100.0%/0.0%/0.0%" and r3[0]["workload"] == "33.8%/33.8%/32.5%"
assert g11["CORE_0"]["max_abs_vs_ort"] < 0.01 and g11["CORE_0_1_2"]["max_abs_vs_ort"] < 0.01
m1 = PC["m1"]


def pct_range(model):
    ps = [float(p.rstrip("%")) for r in m1[model]["split_rows"] for p in r["workload"].split("/")]
    return min(ps), max(ps)


assert pct_range("silu") == (30.0, 35.0) and pct_range("relu") == (25.0, 37.5)
assert m1["silu"]["per_op"]["ConvExSwish"] == {"split": 0, "not_split": 57} and m1["relu"]["per_op"]["ConvRelu"] == {"split": 51, "not_split": 0}
assert m1["silu"]["per_op"]["Add"] == {"split": 8, "not_split": 0} and m1["silu"]["per_op"]["Concat"] == {"split": 15, "not_split": 2}
assert m1["silu"]["per_op"]["Conv"] == {"split": 6, "not_split": 1} and m1["silu"]["per_op"]["Split"]["split"] == 0
pr = BD["probes"]
m4, m4c, m6, m7, m16 = pr["m4"]["result"], pr["m4c"]["result"], pr["m6"]["result"], pr["m7"]["result"], pr["m16"]["result"]
assert m4["calls_done"] == 300 and m4["exceptions"] == 0 and m4["outputs_with_diff_above_0"] == 300 and round(m4["max_diff"], 2) == 1.04
assert m4c["calls_done"] == 300 and m4c["exceptions"] == 0 and m4c["outputs_with_diff_above_0"] == 0 and m4c["max_diff"] == 0
assert m6["init_error"] is None and all(c["vs_same"] == 0 for c in m6["calls"]) and all(c["vs_previous"] > 0 for c in m6["calls"][1:])
assert m7["batch4_output_shape"] == [4, 9, 8400] and m7["max_abs_diff_per_image"] == [0.0] * 4
assert m16["contexts_created"] == 32 and m16["stop"]["reason"] == "cap_reached" and all(r["max_diff"] == 0 for r in m16["rows"])
ca = CA["masks"]
assert ca["AUTO"]["split_count"] == 0 and ca["ALL"]["split_count"] == ca["CORE_0_1_2"]["split_count"] == 29 and ca["ALL"]["same_split_set_as_core_0_1_2"] is True and ca["AUTO"]["same_split_set_as_core_0_1_2"] is False
assert all("error" not in v and v["rows"] == 119 for v in ca.values())
a2s = BD["a2_split"]
assert a2s["v_pc"]["ok"] and a2s["v_board"]["ok"] and a2s["n2_1"]["meets"] and a2s["same_calibration_list_as_a1"]
assert a2s["layers"]["rows"] == 106 and a2s["layers"]["counts"] == {"CPU|INT8": 3, "NPU|INT8": 103} and a2s["layers"]["cpu_ops"] == []
qt = BD["qat_time"]
assert qt["all_realized"] and all(v["realized"] for v in qt["conditions"].values())
assert qt["comparisons"]["qat_vs_split|CORE_0"]["verdict"] == "khác" and qt["comparisons"]["qat_vs_int8h5|CORE_0"]["verdict"] == "khác"
assert qt["board_table_counts"]["NPU|FLOAT16"] == 8
assert all(c["build_total_cycles"] == c["total_cycles"] == 5532317 for c in qt["coverage_qat"])
h6a = json.loads((Q2E / "h6_first" / "rknn_int8_h6_css_test.json").read_text())
h6b = json.loads((Q2E / "h6_second" / "rknn_int8_h6_css_test.json").read_text())
assert h6a["model_sha256"].startswith("4fa1ae1e") and h6b["model_sha256"].startswith("40e3ef03") and h6a["model_sha256"] != h6b["model_sha256"]
assert round(100 * h6a["map50_95"], 2) == round(100 * h6b["map50_95"], 2) == 30.18 and round(100 * h6a["map50"], 2) == round(100 * h6b["map50"], 2) == 48.93
assert (SILU / "weights" / "rknn_int8_h6" / "best-rk3588.rknn").exists()
import hashlib
assert hashlib.sha256((SILU / "weights" / "rknn_int8_h6" / "best-rk3588.rknn").read_bytes()).hexdigest() == h6a["model_sha256"]  # first build restored
qr = PC["qat_rows"]
assert qr["fp16_ids"] == [47, 48, 49, 50, 59, 60, 61, 62]
assert [r["op"] for r in qr["window"] if r["id"] in qr["fp16_ids"]] == ["exSwish", "exDataConvert", "Resize", "exDataConvert"] * 2
assert [r["op"] for r in qr["ptq_resize_rows"]] == ["Resize", "Resize"] and all(r["dtype"] == "INT8" for r in qr["ptq_resize_rows"])
cmp3, tot = qt["comparisons"], qt["total"]
c0 = qt["conditions"]

P = []
w = P.append
w("""*********************
Mục chưa biết còn lại
*********************

.. admonition:: Trang này trả lời

   - Với mỗi mục "chưa biết" còn lại của nhóm Tầng NPU (G7, G10, G11, M1, M2, M4, M6, M7, M8, M16 và các mục của giai đoạn 2c, 2d), đã đo hoặc tìm thêm gì, nhãn cuối là gì?
   - Mục nào vẫn chưa biết, vì sao, và cần gì để biết?

.. admonition:: Tóm tắt
""")
w(f"""
   - Đã đo mới: Resize micro model (G7b), Relu đứng riêng (G11), ba luồng dùng chung một context (M4), ``async_mode`` (M6), ``rknn_batch_size`` 4 (M7), 32 context (M16), dựng lại ``h6``, A2 tách đầu, thời gian NPU của bản QAT. Đã phân tích thêm từ file có sẵn: G7a, G10, M1 và vết của 8 hàng FP16 của bản QAT.
   - G7: NPU chạy Resize micro model B (``half_pixel``, ``floor``) cho kết quả của A (``asymmetric``, ``floor``) chứ không phải kết quả đúng của B (lệch {f(gb['B']['npu_vs_own'])} so với onnxruntime của B, chênh {f(gb['B']['npu_vs_ref'], 4)} so với A). Với kết quả này, thuộc tính bị bỏ qua trong thí nghiệm này. "Vì sao lên NPU" vẫn chưa biết.
   - G11: Relu đứng riêng trong micro model chạy NPU và chia {r3[0]['workload']} ở ``CORE_0_1_2``. Nghĩa là toolkit và runtime 2.3.2 chia Relu đứng riêng, trái với dòng Relu của Operator List và phù hợp với hai guide liệt kê Relu đa nhân. Đây là micro model, không phải Relu trong YOLO.
   - M4: ba luồng dùng chung một context: không exception, nhưng {m4['outputs_with_diff_above_0']} trên {m4['calls_done']} đầu ra khác tham chiếu tuần tự (lệch tối đa {f(m4['max_diff'])}). Phép đối chứng cùng mã với một luồng cho 0 khác biệt. S2 không dùng chung context giữa các luồng, nên kết quả này không áp vào S2.
   - M16: tạo được {m16['contexts_created']} context, đều chạy đúng, dừng ở ngưỡng chặn 32, không phải giới hạn thật. M6: ``async_mode=True`` được chấp nhận và ``inference`` tuần tự vẫn trả đầu ra của chính ảnh vừa gửi. M7: batch 4 chạy, đầu ra từng ảnh khớp batch 1 ở lần chạy đầu (lệch 0) nhưng một ảnh lệch {f(max(M7B['max_abs_diff_per_image']))} ở lần chạy lặp.
   - ``h6``: dựng lần hai cho file khác byte và cùng AP50-95 ({f(100 * h6a['map50_95'])}), nguyên nhân ``h6`` tệ hơn vẫn chưa biết.
   - A2 tách đầu: AP50-95 INT8 {f(a2s['int8_split']['map50_95'])}, đạt tiêu chí {f(a2s['n2_1']['criterion'])}. QAT: NPU {f(c0['qat|CORE_0']['median'], 2)} ms ở ``CORE_0``, chậm hơn A1 PTQ tách đầu {f(cmp3['qat_vs_split|CORE_0']['diff_pct'], 1)}% và nhanh hơn ``int8h5`` {f(-cmp3['qat_vs_int8h5|CORE_0']['diff_pct'], 1)}% (phần NPU), tổng với giải mã CPU chậm hơn ``int8h5`` {f(tot['CORE_0']['diff_vs_int8h5_ms'], 2)} ms.
   - M2: ``core_mask`` ``NPU_CORE_ALL`` (0xffff) chia {ca['ALL']['split_count']} dòng, đúng tập dòng của ``CORE_0_1_2``, còn ``AUTO`` chia {ca['AUTO']['split_count']} dòng. Điều bài EDGE gọi là ``ALL`` vẫn chưa biết.
   - Vẫn chưa biết (nhãn cuối, đã ghi điều đã thử): quy tắc chia job của ``librknnrt`` (M1 chỉ mô tả), nguyên nhân ``h5`` lấy lại điểm, ``mmse``, QAT với torch 1.10 đến 1.13.1. Người dùng đã quyết định ngày 2026-11-01: M8 mục tiêu 60 FPS (:doc:`03-ket-qua-da-nhan` mục 8) và duyệt P2 và P3 (:doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`).
""")
w("""
Kiểm kê và lớp của từng mục ở ``results/phase2e_unknowns_inventory.md``, quy tắc viết trước dữ liệu ở ``bench/onboard_q2e/rule_*.txt`` và ``bench/onboard_q2e_qat/rule.txt`` (run ``ppe5_yolov8n_baseline_100ep_s0``). Trang liên quan: :doc:`../03-tang-npu-don-bay/01-operator-support`, :doc:`../03-tang-npu-don-bay/02-multi-core`, :doc:`05-ket-qua-luong-tu-hoa`, :doc:`07-ket-qua-qat-kien-truc`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Bảng nhãn cuối
=================
""")
w(table(["Mục", "Câu hỏi", "Nhãn cuối", "Mục trong trang này"], [
    ["G7", "Vì sao Resize ``asymmetric`` vẫn lên NPU", "Đo một phần: thuộc tính bị bỏ qua ở micro model. Vì sao lên NPU: vẫn chưa biết", "2"],
    ["G10", "Reshape 8 nút ONNX, 7 dòng RKNN, Split", "Đo (mô tả): số học các dòng khớp. Vì sao 3 Reshape và các Slice không có dòng cùng tên: vẫn chưa biết", "3"],
    ["G11", "Hai guide và Operator List khác nhau về Relu", "Đo ở micro model: Relu đứng riêng chia ba nhân. Không phân xử tài liệu", "4"],
    ["M1", "Quy tắc chia job của ``librknnrt``", "Đo (mô tả mẫu). Quy tắc: vẫn chưa biết", "5"],
    ["M2", "``ALL`` trong Table 4 của EDGE", "Đo một phần: ``NPU_CORE_ALL`` chia như ``CORE_0_1_2`` ở runtime này. Nghĩa trong bài EDGE: vẫn chưa biết", "6"],
    ["M4", "Một context cho nhiều luồng", "Đo: đầu ra sai khi ba luồng dùng chung, không có exception", "7"],
    ["M6", "``async_mode``", "Đo một phần: được chấp nhận, đầu ra là của ảnh vừa gửi trong phép thử tuần tự. Gửi nhiều ảnh liên tiếp: chưa thử", "7"],
    ["M7", "``rknn_batch_size``", "Đo: batch 4 chạy, khớp batch 1 ở lần đầu, một ảnh lệch ở lần lặp (không tái lập)", "7"],
    ["M8", "Mục tiêu FPS", "Người dùng chốt 60 FPS (2026-11-01), kiểm tra đạt hoặc không đạt ở :doc:`03-ket-qua-da-nhan` mục 8", "6"],
    ["M16", "Số context tối đa", "Đo: không lỗi tới 32, giới hạn thật vẫn chưa biết", "7"],
    ["``h6`` tệ hơn", "Vì sao ``h6`` thấp hơn base 6.57 điểm", "Đo: tái lập được, nguyên nhân vẫn chưa biết", "8"],
    ["``h5`` lấy lại điểm", "Nguyên nhân", "Vẫn chưa biết (hết ngân sách)", "8"],
    ["``mmse``", "Hết bộ nhớ", "Không chạy (sai lệch danh tính hiệu chuẩn)", "8"],
    ["8 hàng FP16 của QAT", "Vì sao", "Đo (mô tả vị trí). Nguyên nhân: vẫn chưa biết", "9"],
    ["Thời gian NPU của QAT", "Độ phủ và thời gian", "Đo dưới P2", "9"],
    ["QAT với torch 1.10 đến 1.13.1", "Ảnh hưởng của phiên bản", "Không chạy (cần bộ công cụ thứ hai)", "8"],
    ["A2 tách đầu", "Tách lượng tử hóa đầu ra ltrb khỏi phép giải mã", "Đo: đạt tiêu chí", "9"],
], [14, 34, 44, 12]))
w(f"""

2. G7: thuộc tính của Resize
============================

Hai node Resize của model ``{PC['g7a']['onnx'].split('/')[-1]}`` có ``mode`` ``nearest``, ``coordinate_transformation_mode`` ``asymmetric`` và ``nearest_mode`` ``floor`` (:doc:`../03-tang-npu-don-bay/01-operator-support` mục 4.3). Quy tắc ``rule_pc.txt`` và ``rule_micro.txt``.

**G7a, onnxruntime.** Ở tỉ lệ 2 (cũng ở 1.5 và 3), bộ ``half_pixel`` với ``round_prefer_floor`` cho đầu ra giống hệt bộ ``asymmetric`` với ``floor`` (lệch 0, trên đầu vào 1x256x20x20 là hình dạng của Resize đầu tiên trong bảng layer). Bộ ``half_pixel`` với ``floor`` lệch {f(g7['scale_2.0']['half_pixel|floor'])} ở tỉ lệ 2. Bộ ``align_corners`` giống ở tỉ lệ 2 và lệch {f(g7['scale_1.5']['align_corners|round_prefer_floor'])} ở tỉ lệ 1.5. Nghĩa là quan sát cũ "đổi sang giá trị được liệt kê cho bảng build giống hệt" (:doc:`../03-tang-npu-don-bay/01-operator-support`) có thể chỉ vì các bộ thuộc tính đó cho cùng chỉ số nguồn ở hình dạng thử, chứ chưa nói gì về cách compiler xử lý thuộc tính.

**G7b, NPU.** Ba micro model Resize (đầu vào 1x256x20x20, tỉ lệ 2), FP16, chạy trên board:
""")
w(table(["Bộ thuộc tính", "Lệch NPU so với onnxruntime của chính nó", "Lệch NPU so với onnxruntime của A", "Dòng Resize"], [
    [f"{k} ({gb[k]['attrs'][0]}, {gb[k]['attrs'][1]})", f(gb[k]["npu_vs_own"], 4), f(gb[k]["npu_vs_ref"], 4), f"{gb[k]['table'][1]['target']}, WorkLoad {gb[k]['table'][1]['workload']}"] for k in "ABC"], [26, 28, 28, 28]))
w(f"""

Ngưỡng khớp viết trước là 0.01 (làm tròn FP16 của giá trị tới khoảng 7 không quá khoảng 0.004). B là bộ duy nhất khác A trong onnxruntime ({f(gb['B']['ort_own_vs_ref'])}) và đầu ra NPU của B khớp A chứ không khớp B. Theo bảng đọc viết trước: B chạy như A, thuộc tính ``half_pixel`` và ``floor`` bị bỏ qua. C khớp cả hai nên không kết luận gì. Cả ba bộ đều được xếp lên NPU, một nhân. Vì sao Resize của YOLO được xếp lên NPU: chưa biết, không có văn bản, phép đo này không trả lời câu đó. Giới hạn: một hình dạng (1x256x20x20, đúng đầu vào của Resize đầu tiên trong bảng layer, đầu ra 1x256x40x40), tỉ lệ 2, FP16, toolkit 2.3.2.

3. G10: số dòng Reshape và Split
================================

Đối chiếu nút của ONNX mà toolkit đã nhận (``int8_input.onnx``, {g10['onnx_nodes']} nút) với {g10['rknn_rows']} dòng của bảng layer. Quy tắc ``rule_pc.txt`` (kèm addendum: so khớp tên chính xác thay cho "chứa").

- Reshape: {g10['onnx_ops']['Reshape']} nút ONNX, {g10['rknn_ops']['Reshape']} dòng RKNN. Ba nút không có dòng cùng tên (``/model/model.22/Reshape``, ``Reshape_3`` và ``dfl/Reshape_1``). Hai dòng RKNN không có nút ONNX cùng tên (``Sigmoid_output_0_rs`` và ``output0-rs``, tên do compiler đặt). Số học: {g10['onnx_ops']['Reshape']} trừ 3 cộng 2 bằng {g10['rknn_ops']['Reshape']}.
- Split: {g10['onnx_ops']['Split']} nút Split ONNX đều có dòng Split cùng tên, thêm một dòng Split tên ``/model/model.22/Slice_2sp``. Cả {g10['onnx_ops']['Slice']} nút Slice ONNX đều không có dòng trùng tên chính xác, nên theo tên không biết dòng ``Slice_2sp`` sinh từ nút Slice nào (tên gần nhất là ``/model/model.22/Slice``). Tổng {g10['rknn_ops']['Split']} dòng Split.

Số học các dòng được giải thích, vì sao ba nút Reshape và các nút Slice không có dòng cùng tên (gộp vào dòng khác, hay xóa) vẫn chưa biết. Phép đối chiếu chỉ theo tên.

4. G11: Relu đứng riêng
=======================

Micro model một node Relu (1x64x80x80, FP16). Kết quả ở ``CORE_0_1_2``: dòng Relu chạy NPU, ``WorkLoad`` {r3[0]['workload']}. Ở ``CORE_0``: {r0[0]['workload']}. Đầu ra khớp onnxruntime (lệch {f(g11['CORE_0_1_2']['max_abs_vs_ort'], 4)}). Operator List ghi Relu đứng riêng không hỗ trợ đa nhân và hai guide liệt kê Relu là đa nhân (:doc:`../03-tang-npu-don-bay/01-operator-support` mục 6.1). Trong phép thử này toolkit và runtime 2.3.2 chia Relu đứng riêng, phù hợp với hai guide. Giới hạn: một micro model, không phải Relu trong đồ thị YOLO (model ReLU dùng ``ConvRelu``, 51 trên 51 dòng chia). Kết quả cho biết hành vi của phiên bản này, không phải tài liệu nào đúng.

5. M1: mẫu chia job quan sát được
=================================

Từ bảng ``WorkLoad`` của các phiên ``CORE_0_1_2`` (``bench/onboard_g4b``), mỗi model một phiên. Đây là mẫu quan sát, không phải quy tắc.
""")
rows = []
for model, label in (("silu", "SiLU"), ("relu", "ReLU")):
    po = m1[model]["per_op"]
    lo, hi = pct_range(model)
    rows.append([label, ", ".join(f"``{o}`` {v['split']}/{v['split'] + v['not_split']}" for o, v in po.items() if v["split"] or o in ("ConvExSwish", "Split")), f"{lo:g}% đến {hi:g}%"])
w(table(["Model", "Op có dòng chia (số dòng chia trên tổng dòng của op)", "Mỗi nhân nhận trong dòng chia"], rows, [10, 60, 30]))
w(f"""

Quan sát: ở model SiLU không dòng ``ConvExSwish`` nào chia (0 trên 57) còn ở model ReLU mọi dòng ``ConvRelu`` chia (51 trên 51). Dòng ``Add``, ``Concat`` và sáu ``Conv`` ở đầu ra chia gần đều ba phần (mỗi nhân nhận từ 30% đến 35% ở SiLU). ``Split``, ``MaxPool``, ``Resize`` và ``Reshape`` không chia. Quy tắc của ``librknnrt`` nằm trong binary không có mã nguồn: vẫn chưa biết.

6. M2 và M8
===========

**M2** (``ALL`` trong Table 4 của EDGE): đã tìm lại toàn bộ bài báo và T1 ngày 2026-10-31, bài không định nghĩa ``ALL`` và header ghi ``0xffff`` chọn nhân theo nền tảng. :doc:`../03-tang-npu-don-bay/02-multi-core` mục 6.1 nêu một đường chưa dùng là đo ``ALL`` trên board, nên bảng kiểm kê ban đầu xếp M2 vào nhóm hết ngân sách là sai và đã sửa (``rule_core_all.txt``). Phép đo (``ai/automation/probe_core_all.py``, mô hình INT8 chuẩn của seed 0, bảng layer ``perf_debug`` một lần mỗi mặt nạ): ``AUTO`` chia {ca['AUTO']['split_count']} dòng, ``CORE_0_1_2`` chia {ca['CORE_0_1_2']['split_count']} dòng và ``NPU_CORE_ALL`` chia {ca['ALL']['split_count']} dòng, đúng cùng tập với ``CORE_0_1_2``. Trung vị latency một phiên không ghim: ``AUTO`` {f(ca['AUTO']['latency_ms_median'], 2)} ms, ``CORE_0_1_2`` {f(ca['CORE_0_1_2']['latency_ms_median'], 2)} ms, ``ALL`` {f(ca['ALL']['latency_ms_median'], 2)} ms, chỉ mô tả (một phiên, không dưới P2). Kết quả cho biết ``NPU_CORE_ALL`` chia đúng tập dòng của ``CORE_0_1_2`` (file kết quả chỉ ghi tên các dòng chia, không ghi số nhân từng dòng). Điều bài EDGE gọi là ``ALL`` vẫn chưa biết. **M8** (mục tiêu FPS): người dùng chốt 60 FPS ngày 2026-11-01, kiểm tra đạt hoặc không đạt ở :doc:`03-ket-qua-da-nhan` mục 8 (cấu hình một context chưa đạt, hai context, S2 và S3 đạt theo thông lượng, đo với model INT8 mặc định, ``int8h5`` không khác ``int8`` về thông lượng theo :doc:`09-ket-qua-don-bay-fps`).

7. M4, M6, M7, M16: thăm dò RKNNLite
====================================

Chạy trên board bằng ``ai/board/probe_runtime.py``, model INT8 chuẩn của seed 0, 8 ảnh nhiễu cố định, so đầu ra với tham chiếu tuần tự một context (``rule_probe.txt``). Không dưới P2 hay P3, thời gian chỉ mô tả.

- **M4** (một context cho ba luồng, mỗi luồng 100 lần gọi): {m4['calls_done']} lần gọi, {m4['exceptions']} exception, {m4['outputs_with_diff_above_0']} đầu ra khác tham chiếu (lệch tối đa {f(m4['max_diff'])}). Phép đối chiếu M4c (cùng mã, một luồng, 300 lần): {m4c['outputs_with_diff_above_0']} khác biệt, {m4c['exceptions']} exception. Vì M4c khớp hoàn toàn, phép so sánh hợp lệ và khác biệt của M4 đến từ việc ba luồng dùng chung một context. Runtime không báo lỗi khi sai, nên dùng chung một context giữa các luồng cho đầu ra sai âm thầm trong phép thử này. Điều này phù hợp với việc S2 dùng một context mỗi luồng. Nguyên nhân vì sao sai chưa biết.
- **M6** (``async_mode=True``): ``init_runtime`` thành công, tám lần ``inference`` tuần tự đều trả đầu ra khớp tham chiếu của chính ảnh vừa gửi (lệch 0) và khác đầu ra của ảnh trước. Hành vi khi gửi nhiều ảnh không đợi kết quả: chưa thử, thời gian không đo.
- **M7** (``rknn_batch_size`` 4, FP16): batch 4 dựng và chạy được, đầu ra {m7['batch4_output_shape']}. Lần chạy đầu: từng ảnh khớp batch 1 (lệch 0). Lần chạy lặp (chạy thêm chỉ để lưu log console, ``probe_m7b.json``): ảnh thứ ba lệch {f(max(M7B['max_abs_diff_per_image']))} so với batch 1, ba ảnh còn lại lệch 0. Nên kết quả "khớp" không tái lập giữa hai lần chạy, nguyên nhân chưa biết. Log console của lần lặp (``probe_m7_console.log``) ghi: "core mask = 1 is invalid for batch size: 4, fall back to CORE_AUTO mode" (``E RKNN``). Thời gian một lần gọi (lần chạy đầu, ``probe_m7.json``): batch 1 {f(m7['batch1_median_ms'], 1)} ms, batch 4 {f(m7['batch4_median_ms'], 1)} ms ({f(m7['batch4_ms_per_image'], 1)} ms mỗi ảnh). Hai số khác chế độ nhân (batch 4 rơi về ``CORE_AUTO``) và đo qua Python, chỉ mô tả, không so được với số P2.
- **M16** (nhiều context): tạo {m16['contexts_created']} context liên tiếp, mỗi context chạy một lần đúng, ``MemAvailable`` giảm từ {m16_before} MiB trước khi tạo context (và {m16['rows'][0]['mem_available_mib']} sau context đầu) xuống {m16['rows'][-1]['mem_available_mib']} MiB. Dừng ở ngưỡng chặn 32, không có lỗi: giới hạn thật vẫn chưa biết, chỉ biết không nhỏ hơn 32 trên board này.

8. Nhãn cuối của các mục 2c và 2d còn lại
=========================================

- **Dựng lại ``h6``** (``rule_h6.txt``): file dựng lần hai (sha256 ``{h6b['model_sha256'][:8]}``) khác byte file lần đầu (``{h6a['model_sha256'][:8]}``) nhưng AP50-95 trên ``css_test`` giống nhau ({f(100 * h6a['map50_95'])}) và AP50 giống nhau ({f(100 * h6a['map50'])}). Theo bảng đọc viết trước: byte dựng không tất định nhưng độ chính xác tái lập, tức mức giảm 6.57 điểm tái lập qua hai lần dựng. Nguyên nhân vẫn chưa biết, và một lần dựng lại chưa đủ để nói gì thêm về nhiễu dựng. File lần đầu được khôi phục vào chỗ cũ, file lần hai ở ``bench/onboard_q2e/h6_second/``.
- **``h5`` lấy lại điểm:** đã dùng ``h1`` đến ``h4``, ``h6``, ``c_all``, ``kl`` và ``auto`` (:doc:`05-ket-qua-luong-tu-hoa`), hết ngân sách, không có đường mới trong ngân sách: vẫn chưa biết.
- **``mmse``:** dựng với 300 ảnh bị hệ điều hành dừng (mã 137). Giảm số ảnh hiệu chuẩn làm sai lệch danh tính hiệu chuẩn (cặp md5 chung), nên không chạy: không có kết quả.
- **QAT với torch 1.10 đến 1.13.1** (khuyến nghị UG232 tr.156): cần môi trường torch và python tương thích, venv hiện dùng python 3.12 và torch 2.4.0. Không chạy, không có kết quả.

9. QAT và A2 tách đầu
=====================

**Vị trí 8 hàng FLOAT16 của bản QAT** (``rule_pc.txt``). Hai nhóm hàng giống nhau, ở id {', '.join(map(str, qr['fp16_ids'][:4]))} và {', '.join(map(str, qr['fp16_ids'][4:]))}: ``exSwish`` (FLOAT16), ``exDataConvert`` (lượng tử hóa), ``Resize`` (FLOAT16), ``exDataConvert`` (chuyển FLOAT16 về INT8). Ngay trước mỗi nhóm là một dòng ``Conv`` INT8 và một ``exDataConvert`` khử lượng tử hóa. Ở bản PTQ tách đầu, Conv và SiLU đứng trước hai Resize hợp thành ``ConvExSwish`` INT8 và hai dòng Resize là INT8. Nghĩa là trong bản QAT, phần SiLU của lớp Conv ngay trước hai Resize bị tách ra chạy FP16 cùng với Resize. Nguyên nhân chưa biết.

**Thời gian NPU của QAT** (``bench/onboard_q2e_qat``, dưới P2, mọi phiên thực hiện đúng). Trung vị hai phiên:
""")
w(table(["Model", "CORE_0 (ms)", "CORE_0_1_2 (ms)"], [
    [lab, f(c0[f"{k}|CORE_0"]["median"], 3), f(c0[f"{k}|CORE_0_1_2"]["median"], 3)] for lab, k in (("``int8h5`` (lai)", "int8h5"), ("A1 tách đầu (chỉ NPU)", "split"), ("QAT tách đầu (chỉ NPU)", "qat"))], [40, 24, 28]))
w(f"""

QAT khác A1 ở ``CORE_0`` {f(cmp3['qat_vs_split|CORE_0']['diff_ms'], 3)} ms ({f(cmp3['qat_vs_split|CORE_0']['diff_pct'], 1)}%, lớn hơn chênh hai phiên {f(cmp3['qat_vs_split|CORE_0']['gap_ms'], 3)} ms) nên là "khác", và nhanh hơn ``int8h5`` {f(-cmp3['qat_vs_int8h5|CORE_0']['diff_ms'], 3)} ms. Tổng với giải mã CPU của A1 ({f(tot['CORE_0']['decode_ms'])} ms, hai tensor đầu ra cùng hình dạng, không đo lại): {f(tot['CORE_0']['qat_total_ms'])} ms so với {f(tot['CORE_0']['int8h5_ms'], 3)} ms của ``int8h5``, chậm hơn {f(tot['CORE_0']['diff_vs_int8h5_ms'])} ms nếu không chồng lấp, tổng của hai trung vị đo riêng (chồng lấp giải mã đã đo cho A1 ở :doc:`09-ket-qua-don-bay-fps`, chưa đo riêng cho bản QAT). Độ phủ đa nhân của bản QAT: {f(100 * qt['coverage_qat'][0]['coverage'], 1)}% cycles ở các dòng chia (tiêu chí 50% chỉ để mô tả). Tổng cycles của bảng QAT ({qt['coverage_qat'][0]['total_cycles']}) bằng đúng tổng của bản PTQ tách đầu dù có thêm 8 hàng FP16, điều này chưa được giải thích.

**A2 tách đầu** (``rule_nodfl_split.txt``). Hai kiểm tra hợp lệ qua (giải mã float của ONNX lệch {a2s['v_pc']['int8']:.1e}, FP16 tách đầu chênh {f(a2s['v_board']['diff'])} điểm so với FP16 chuẩn của A2). INT8 tách đầu của A2 đạt AP50-95 {f(a2s['int8_split']['map50_95'])} trên ``css_test`` (AP NoHelmet {f(a2s['int8_split']['NoHelmet'])}, AP Vest {f(a2s['int8_split']['Vest'])}), hơn FP16 tách đầu {a2s['n2_1']['minus_fp16_split']:+.2f}, hơn FP16 chuẩn {a2s['n2_1']['minus_fp16']:+.2f}, hơn INT8 mặc định {a2s['n2_1']['minus_int8']:+.2f} điểm, đạt tiêu chí {f(a2s['n2_1']['criterion'])}. Đồ thị NPU có {a2s['layers']['rows']} hàng toàn INT8, không op CPU ngoài Input và Output. Theo bảng đọc viết trước: khi xuất thẳng đầu ra ltrb và logit class, INT8 đạt FP16, nên việc lượng tử hóa đầu ra của lớp hồi quy không phải nguồn chính của mức rơi, phần đuôi tính toán của phép giải mã được ủng hộ, giống A1 nhưng không có DFL. Đây không phải cơ chế. Thời gian của A2 tách đầu không đo.

10. Việc còn lại và giới hạn
============================

- Đã được người dùng quyết định: P2 và P3 duyệt (:doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`), mục tiêu FPS 60 (:doc:`03-ket-qua-da-nhan` mục 8). Cách hiểu 60 FPS (một luồng hay tổng, thông lượng hay thời gian mỗi khung) cần người dùng xác nhận.
- Vẫn chưa biết: nghĩa của ``ALL`` trong bài EDGE (M2), quy tắc chia job (M1), vì sao Resize lên NPU (G7), vì sao ba Reshape và các Slice không có dòng cùng tên (G10), nguyên nhân của ``h5``, ``h6``, 8 hàng FP16 của QAT, giới hạn số context (M16), hành vi ``async_mode`` khi gửi nhiều ảnh liên tiếp (M6).
- Không chạy: ``mmse`` (đổi danh tính hiệu chuẩn), QAT với torch 1.10 đến 1.13.1 (cần bộ công cụ thứ hai).
- Mọi kết quả là một board, một lần chạy mỗi phép đo, một seed, micro model không phải op trong YOLO, thời gian dưới P2.

11. Tái lập
===========

.. code-block:: bash

   .venv/bin/python -m ai.automation.analyze_q2e_pc            # G7a, G10, M1, vết QAT (PC)
   .venv/bin/python -m ai.automation.micro_ops 192.168.137.49:5555   # G7b, G11 (board, rknn_server)
   .venv/bin/python -m ai.automation.build_batch_probe          # M7 dựng batch 1 và 4 (PC)
   # board: .venv-board/bin/python -m ai.board.probe_runtime m4|m4c|m6|m7|m16 --model <rknn_int8 dir> --out <json>  (M7 thêm --b1 --b4)
   .venv/bin/python -m ai.automation.build_split ppe5_yolov8n_nodfl_100ep_s0 int8   # A2 tách đầu (cũng fp16)
   .venv/bin/python -m ai.automation.evaluate ppe5_yolov8n_nodfl_100ep_s0 --backend rknn --precision int8 --variant split --board minhnhat@192.168.137.49 --board-repo rk3588
   .venv/bin/python ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_q2e_qat/q2e_qat_driver.py   # thời gian QAT dưới P2 (helper x4_hold.sh đang chạy)
   .venv/bin/python -m ai.automation.probe_core_all 192.168.137.49:5555   # M2 (board, rknn_server)
   .venv/bin/python -m ai.automation.analyze_q2e_board
   .venv/bin/python docs/tools/gen_phase2e_results_page.py

Số liệu: ``results/q2e_pc.json``, ``q2e_micro.json``, ``q2e_core_all.json``, ``q2e_board.json``. Sau lần sửa mã ``decode_split`` cho ``reg_max``, board cần ``make board-sync`` trước khi chấm A2 tách đầu.
""")
text = "\n".join(P).replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
lines = text.split("\n")
for i in range(1, len(lines)):
    if lines[i] and set(lines[i]) == {"="} and lines[i - 1]:
        lines[i] = "=" * (len(lines[i - 1]) + 2)
OUT.write_text("\n".join(lines))
print("wrote", OUT, OUT.stat().st_size)
