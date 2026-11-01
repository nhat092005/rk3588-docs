#!/usr/bin/env python3
"""Sinh hai trang kết quả giai đoạn 2 của Tầng NPU từ kết quả đo, không gõ tay số:
04-tang-npu-ket-qua/01-ket-qua-g4.rst (cổng G4 SiLU sang ReLU) và 03-ket-qua-da-nhan.rst (S1, S2, S3), kèm 02, 05, 06 của nhóm đó.

Đọc ../results/{g4_latency_workload,eval_g4,thr_p3}.json, onboard_x4 (AUTO) và export_int8.json của các run.
Chạy từ gốc repo chính:  .venv/bin/python docs/tools/gen_phase2_results_pages.py
Lời văn nằm trong script, mọi con số lấy từ file JSON. Các assert bảo vệ những số có trong lời văn.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
RUNS = REPO / "ai" / "automation" / "runs"
OUTDIR = REPO / "docs" / "contents" / "03-phuong-phap" / "04-tang-npu-ket-qua"
SILU, RELU = "ppe5_yolov8n_baseline_100ep_s0", "ppe5_yolov8n_relu_100ep_s0"

G = json.loads((RES / "g4_latency_workload.json").read_text())
C = json.loads((RES / "eval_g4.json").read_text())
T = json.loads((RES / "thr_p3.json").read_text())
X4 = json.loads((RES / f"onboard_x4_{SILU}_int8_CORE_0.json").read_text())
EXP = {r: json.loads((RUNS / r / "export_int8.json").read_text()) for r in (SILU, RELU)}
EXP16 = {r: json.loads((RUNS / r / "export_fp16.json").read_text()) for r in (SILU, RELU)}
EXP_S = {s: json.loads((RUNS / f"ppe5_yolov8n_baseline_100ep_s{s}" / "export_int8.json").read_text()) for s in (1, 2)}
OWN_S1 = json.loads((RUNS / "ppe5_yolov8n_baseline_100ep_s1" / "export_int8_ownlist.json").read_text())

# ---- asserts on the facts the prose states
assert G["all_realized"] and T["all_realized"]
assert G["gate_b"]["relu|CORE_0_1_2"]["verdict"] == "nhanh hơn" and G["gate_b"]["silu|CORE_0_1_2"]["verdict"] == "không nhanh hơn"
assert G["gate_a"]["relu"]["verdict"] == "đạt" and G["gate_a"]["silu"]["verdict"] == "không đạt"
assert C["verdict_c"] == "không đạt" and not C["gate_c"]["css_test|int8"]["passes"]
assert all(G["g3"][m][f"{p}_cpu_ops"] == ["Transpose"] for m in ("silu", "relu") for p in ("int8", "fp16")) and G["g3"]["relu"]["fp16_rows"] == G["g3"]["relu"]["int8_rows"] == 113
assert EXP[RELU]["calibration"]["stems_md5"] == EXP_S[1]["calibration"]["stems_md5"] == EXP_S[2]["calibration"]["stems_md5"] == "11d6a5c69414a6eafd8b98f99724b0b2"
assert EXP[RELU]["calibration"]["png_md5"] == EXP_S[1]["calibration"]["png_md5"] == EXP_S[2]["calibration"]["png_md5"] == "6652576adb7608ddf8ff326c57851732"
assert len(set(OWN_S1["calibration"]["images"]) & set(EXP[SILU]["calibration"]["images"])) == 30
assert C["gate_c"]["css_test|fp16"]["diff_pp"]["map50_95"] < 0 and C["gate_c"]["css_test|fp32"]["diff_pp"]["map50_95"] < 0
assert T["m12"]["verdict"] == "hơn" and T["m13"]["verdict"] == "không đáng giữ" and T["m3"]["verdict"] == "không phân biệt được"


# facts of the 06-quy-trinh-tai-lap bullets about the int8h5 wiring (2026-11-01)
_h5 = [json.loads((RUNS / f"ppe5_yolov8n_baseline_100ep_s{k}" / "eval" / "rknn_int8h5_css_test.json").read_text())["map50_95"] for k in (0, 1, 2)]
assert f"{100 * sum(_h5) / 3:.2f}" == "50.38"
assert json.loads((RUNS / SILU / "bench" / "tier1_int8h5_CORE_0.json").read_text())["npu_latency_ms"] == 20.513


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


def pm(x, d=2):
    return f"{x:+.{d}f}"


def sha8(r):
    return EXP[r]["rknn_sha256"][:8]


cond = G["conditions"]
gb = G["gate_b"]
ga = G["gate_a"]
gc = C["gate_c"]
nz = C["noise"]
rn = C["relu_noise"]["css_test|int8"]
rg = C["relu_seed_gate_c"]
assert rg["passing"] == 0 and len(rg["per_seed"]) == 3
bo = G["by_op"]
cs = gc["css_test|int8"]
n8 = nz["css_test|int8"]
LABEL_A = {"silu": ga["silu"], "relu": ga["relu"]}
pages = {}

# ------------------------------------------------------------------ 01-ket-qua-g4
P = []
w = P.append
w(f"""****************
Cổng G4 cho ReLU
****************

.. admonition:: Trang này trả lời

   - Đổi SiLU sang ReLU trên YOLOv8n ppe5 qua hay trượt từng điều kiện A (phủ đa nhân), B (latency) và C (mAP) của cổng G4, và nhãn kết luận là gì?
   - Các model so sánh có cùng danh sách hiệu chuẩn INT8 không, và độ nhiễu giữa các seed là bao nhiêu so với mức 1.0 điểm?
   - Workload đa nhân đo được của ``ConvReluAdd``, ``ConvExSwish``, ``Resize``, ``Concat``, ``Split``, ``MaxPool`` là gì?

.. admonition:: Tóm tắt

   - Nhãn của ứng viên ReLU (seed 0 theo chuẩn): **Loại**, vì điều kiện C trượt trên ``css_test`` ở INT8. AP50-95 chênh {pm(cs['diff_pp']['map50_95'])} điểm, AP NoHelmet chênh {pm(cs['diff_pp']['NoHelmet'])} điểm, AP Vest chênh {pm(cs['diff_pp']['Vest'])} điểm (ngưỡng là giảm tối đa 1.0 điểm mỗi cột).
   - Điều kiện A đạt cho ReLU: các lớp chia từ hai nhân trở lên chiếm {pct(min(ga['relu']['coverage_per_session']), 1)} cycles ước tính (SiLU: {pct(max(ga['silu']['coverage_per_session']), 1)}).
   - Điều kiện B đạt cho ReLU: ``CORE_0_1_2`` nhanh hơn ``CORE_0`` {f(gb['relu|CORE_0_1_2']['drop_pct'], 1)}% ({f(cond['relu|CORE_0']['median'], 3)} xuống {f(cond['relu|CORE_0_1_2']['median'], 3)} ms), chênh hai phiên {f(gb['relu|CORE_0_1_2']['gap_ms'], 3)} ms. Với SiLU mức giảm chỉ {f(gb['silu|CORE_0_1_2']['drop_pct'], 1)}%, không đạt ngưỡng 5%.
   - Mức giảm mAP 1.0 điểm nằm trong nhiễu giữa seed của baseline SiLU: AP50-95 INT8 của seed 0, 1, 2 trải {f(n8['map50_95']['range'], 2)} điểm trên ``css_test``. ReLU seed 0, 1, 2 (thêm ngày 2026-10-31 theo duyệt của người dùng) trải {f(rn['map50_95']['range'], 2)} điểm, AP50-95 trung bình của ReLU thấp hơn của SiLU {f(-rn['map50_95']['mean_diff'], 2)} điểm, lớn hơn cả hai khoảng trải. Cả 3 seed ReLU đều trượt cổng C so với SiLU cùng số seed. Nhãn của cổng vẫn tính theo seed 0 so với seed 0 như đã duyệt.
   - Hai danh sách hiệu chuẩn INT8 cũ của seed 0 và seed 1 chỉ trùng 30 trên 300 ảnh vì sampler phụ thuộc ``PYTHONHASHSEED``. Mọi model INT8 so sánh ở trang này dùng đúng danh sách của seed 0.
   - Trong bảng WorkLoad: 6 trên 6 lớp ``ConvReluAdd`` chia ba nhân. Operator List không có mục cùng tên. 57 trên 57 lớp ``ConvExSwish`` chỉ chạy nhân 0. ``Resize``, ``Split`` và ``MaxPool`` chỉ chạy nhân 0.
   - Điều kiện chạy latency là giao thức P2 của nhóm Nền đo NPU, đã được người dùng duyệt nguyên trạng ngày 2026-11-01 (hạn chế ở :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3` mục 6). Mọi số là một board, một lần chạy xen kẽ, một seed.

Tiêu chuẩn của cổng ở :doc:`../03-tang-npu-don-bay/01-operator-support` (mục 2). Kết quả đa nhân S1, S2, S3 ở :doc:`03-ket-qua-da-nhan`. Mọi số INT8 ở trang này dùng công thức lượng tử hóa mặc định của Ultralytics. Trang :doc:`05-ket-qua-luong-tu-hoa` cho thấy công thức ``h5`` (giữ FP16 nhánh giải mã box) lấy lại gần hết mức rơi INT8 so với FP16 và không tốn latency (một lần đo dưới P2), cổng C của ReLU dưới ``h5`` vẫn không đạt.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Điều kiện chạy
=================

""")
w(table(["Model", "Run", "INT8 sha256 (8 ký tự đầu)", "FP16 sha256 (8 ký tự đầu)"],
        [["SiLU baseline seed 0", f"``{SILU}``", sha8(SILU), EXP16[SILU]["rknn_sha256"][:8]],
         ["ReLU seed 0", f"``{RELU}``", sha8(RELU), EXP16[RELU]["rknn_sha256"][:8]]], [22, 40, 20, 20]))
w(f"""
ReLU huấn luyện 100 epoch trên ppe5 (``ai/automation/configs/ppe5_yolov8n_relu.yaml``, seed 0). So ``args.yaml`` của hai run, chỉ khác ``model`` (yaml ReLU thay ``yolov8n.pt``), ``pretrained`` (``yolov8n.pt`` nạp vào model yaml thay ``true``) và tên, đường dẫn run, mọi tham số huấn luyện khác giống nhau. Kiến trúc là ``ai/models/yolov8n_relu.yaml`` (``activation: nn.ReLU()``) khởi tạo từ trọng số ``yolov8n.pt`` của SiLU, nhật ký ghi ``Transferred 322/355 items from pretrained weights``. Baseline cũng khởi tạo từ ``yolov8n.pt``. Kết quả của cổng ghi nhãn "1 seed" (seed 0), ReLU seed 1 và 2 chỉ để mô tả nhiễu (mục 5).

Đo latency chạy một lần xen kẽ 16 phiên dưới giao thức P2 (ghim ``rknn_server`` và ba ngắt NPU vào CPU4, dừng ``irqbalance``, tần số khóa), thứ tự SiLU, ReLU lần lượt ở ``CORE_0``, ``CORE_0_1``, ``CORE_0_1_2``, ``AUTO``, lặp lại hai vòng cùng thứ tự, nghỉ 45 giây. Mỗi phiên là 5 lần ``eval_perf`` không bật ``perf_debug`` (latency) rồi 5 lần với ``perf_debug=True`` (bảng từng lớp). Cả 16 phiên thực hiện đúng P2 theo tiêu chí viết trước (``bench/onboard_g4b/rule.txt``). P2 đã được người dùng duyệt nguyên trạng ngày 2026-11-01. Các ngưỡng số mới của quy tắc này không được nêu riêng trong câu trả lời nên không coi là đã duyệt.

Hiệu chuẩn INT8: danh sách hiệu chuẩn của seed 0 (300 ảnh, mỗi class có mặt trong ít nhất 157 ảnh) được sao nguyên cho ReLU và cho baseline seed 1 và 2. Bằng chứng giống hệt là ``stems_md5`` ``{EXP[RELU]['calibration']['stems_md5']}`` và ``png_md5`` ``{EXP[RELU]['calibration']['png_md5']}`` (md5 của tên ảnh đã sắp và của sha256 các tệp PNG), cùng thứ tự tên ảnh trong ``dataset.txt`` khớp từng dòng. Không dùng md5 của ``dataset.txt`` vì tệp này chứa đường dẫn tuyệt đối có tên run.

Điều đã biết về sampler: ``ai/core/rknn/calibration.py`` cắt ``list(selected)[:n]`` trên tập chuỗi và xáo ``list(class_to_images[c] - selected)``, thứ tự phụ thuộc ``PYTHONHASHSEED``. Vì vậy hai export cũ của seed 0 và seed 1 dùng hai danh sách khác nhau, chỉ trùng {len(set(OWN_S1['calibration']['images']) & set(EXP[SILU]['calibration']['images']))} trên 300 ảnh. Export cũ của seed 1 được giữ với tên ``rknn_int8_ownlist``, kết quả X5 (dùng file này trên board) không đổi. Sampler đã sửa bằng ``sorted`` trong một thay đổi riêng (chưa commit), có ``tests/test_calibration.py``, export cũ của seed 0 không bị sửa.

2. G1 đến G3
============

2.1. G1 và G2: nguồn
--------------------

G1 chỉ tìm trong tài liệu T1 của repo (Operator List V2.3.2, SDK User Guide V2.3.2, API guide, toàn bộ PDF trong ``3rdparty/rknn-toolkit2/doc`` và mã, changelog trong ``3rdparty``). G2 tìm trong 46 PDF bài báo ``docs/_assets/pdf/papers``. Kết quả do subagent doc-reader trích, số trang là trang PDF.
""")
w(table(["Câu hỏi", "Kết quả", "Nhãn"], [
    ["Operator List có mục tên ``ConvReluAdd``, ``ConvRelu``, ``ConvExSwish`` không",
     "Không có mục nào. Mục gần nhất là ``ConvolutionRelu`` (3.2.7, tr.60), ``ConvolutionAddRelu`` (3.2.19, tr.63) và ``exSwish`` (3.2.69, tr.98) [T1 OPL]",
     "NGUỒN"],
    ["``ConvolutionAddRelu`` ghi gì",
     "``Output = Relu(Add(Conv(Input0), Input1))``, ``说明及规格限制同Convolution``, ``多核联合: 支持`` [T1 OPL tr.63]. Không có tài liệu nói ``ConvReluAdd`` là cùng op",
     "NGUỒN"],
    ["``ConvRelu`` có trong tài liệu T1 không",
     "Có trong ví dụ log của SDK guide V2.3.2 tr.75, dòng ``6 ConvRelu INT8 NPU 48.1%/51.9%/0.0% - Up:48.1%``, và bảng layer tr.109 đến 110 [T1 UG232]. Đây là ví dụ, không phải mục op",
     "NGUỒN"],
    ["``ConvReluAdd`` có trong tài liệu T1 không",
     "Không có trong PDF hay văn bản T1. Chuỗi chỉ xuất hiện trong các tệp nhị phân ``.rknn`` đi kèm (ví dụ ``yolov5s-640-640.rknn`` của ``rknn_yolov5_demo``), không phải tài liệu",
     "CHƯA BIẾT theo T1"],
    ["``ConvExSwish`` có trong tài liệu T1 không", "Không thấy. ``exSwish`` có trong changelog 2.3.2 dòng 284 (``增加exSwish的beta属性支持``)", "CHƯA BIẾT theo T1"],
    ["Bài báo nào đo activation SiLU so với ReLU trên NPU", "Không bài nào trên RK3588. ActNAS đo trên NPU không nêu tên hãng, YOLOv5n SiLU 22.35 ms, ReLU 17.46 ms (Table 2, tr.6). Hai bài RK3588 (Kong 2026, DAHD-YOLO) không so activation", "NGUỒN (G2: không có bằng chứng T2 cùng SoC)"],
], [26, 54, 20]))
w(f"""
Vì ``ConvReluAdd`` không có mục cùng tên trong T1, G1 vẫn ở trạng thái qua một phần. Theo tiêu chuẩn, nhãn "Giữ" cần G1 đến G4 đều qua, nên G1 chưa giải quyết thì nhãn không thể là "Giữ". Hành vi thực tế của ``ConvReluAdd`` đo ở mục 3 (bảng WorkLoad), đó là phép đo T3, không thay thế mục T1.

2.2. G3: bảng build INT8
------------------------

Bảng layer của build INT8 (rknn-toolkit2 2.3.2) của model ReLU đã huấn luyện có {ga['relu']['build_rows']} dòng, các dòng có ``Target`` CPU chỉ gồm ``InputOperator``, ``Transpose`` và ``OutputOperator``. Build FP16 cũng {G['g3']['relu']['fp16_rows']} dòng với cùng ba op CPU. Model SiLU có {ga['silu']['build_rows']} dòng với cùng ba op CPU. Hai model có cùng tổng cycles ước tính ({ga['relu']['build_total_cycles']}). Kết quả: **G3 qua** cho ReLU (không có op mới rơi về CPU). Danh sách op của ReLU khớp bảng đã ghi ở :doc:`../03-tang-npu-don-bay/01-operator-support` mục 3.2 (51 ``ConvRelu``, 6 ``ConvReluAdd``).

3. Điều kiện A: phủ đa nhân
===========================

Một dòng của bảng layer ở ``CORE_0_1_2`` được tính là chia khi ít nhất hai trong ba phần trăm WorkLoad lớn hơn 0.0%. Độ phủ là tổng cycles (cột ``Total``) của các dòng chia chia cho tổng cycles của mọi dòng có cycles. Tổng cycles của bảng board bằng tổng cycles của bảng build của cùng file ``.rknn`` (đã assert). Độ phủ lấy từ bảng ``perf_debug=True``, chỉ là chỉ báo vì ``perf_debug`` có thể tắt cơ chế song song [T1 UG232 tr.177].
""")
w(table(["Model", "Độ phủ phiên 1", "Độ phủ phiên 2", "Điều kiện A"],
        [[m, pct(v["coverage_per_session"][0], 1), pct(v["coverage_per_session"][1], 1), v["verdict"]] for m, v in (("SiLU", ga["silu"]), ("ReLU", ga["relu"]))], [16, 20, 20, 20]))
w(f"""
Bảng theo loại op ở ``CORE_0_1_2`` (phiên 1, từng model). Cột "Dòng chia" là số dòng có ít nhất hai phần trăm WorkLoad lớn hơn 0.0%. Cột "Tỉ lệ thời gian" là tỉ lệ tổng thời gian dòng ở ``CORE_0`` (trung vị hai phiên, chế độ ``perf_debug``).
""")
ops = ["ConvExSwish", "ConvRelu", "ConvReluAdd", "Conv", "Add", "Concat", "Split", "MaxPool", "Resize", "Reshape", "Sub", "Mul", "Sigmoid", "exSoftmax13", "Transpose"]
rows = []
for op in ops:
    for m, name in (("silu", "SiLU"), ("relu", "ReLU")):
        if op in bo[m]:
            v = bo[m][op]
            rows.append([f"``{op}``", name, v["rows"], v["split"], pct(v["cycles"] / ga[m]["build_total_cycles"], 1), pct(v["time_share_core0"], 1),
                         ", ".join(f"``{k}``" for k in list(v["workloads"])[:2])])
w(table(["Op", "Model", "Số dòng", "Dòng chia", "Tỉ lệ cycles", "Tỉ lệ thời gian", "WorkLoad thường gặp"], rows, [14, 8, 8, 8, 12, 12, 38]))
r_silu, r_relu = bo["silu"], bo["relu"]
assert r_relu["ConvReluAdd"]["rows"] == r_relu["ConvReluAdd"]["split"] == 6 and r_silu["ConvExSwish"]["split"] == 0 and r_silu["ConvExSwish"]["rows"] == 57
assert r_relu["ConvRelu"]["rows"] == r_relu["ConvRelu"]["split"] == 51 and r_silu["Concat"]["rows"] == 17 and r_silu["Concat"]["split"] == 15
assert all(r_silu[o]["split"] == 0 for o in ("Split", "MaxPool", "Resize"))
w(f"""
Đọc từ bảng (đây là số đo, nguyên nhân chia hay không chia chưa biết):

- ``ConvRelu`` ({r_relu['ConvRelu']['split']} trên {r_relu['ConvRelu']['rows']} dòng) và ``ConvReluAdd`` ({r_relu['ConvReluAdd']['split']} trên {r_relu['ConvReluAdd']['rows']} dòng) đều chia ba nhân. ``ConvExSwish`` ({r_silu['ConvExSwish']['split']} trên {r_silu['ConvExSwish']['rows']} dòng) đều ``100.0%/0.0%/0.0%``.
- ``Concat``: {r_silu['Concat']['split']} trên {r_silu['Concat']['rows']} dòng chia, 2 dòng chỉ nhân 0. Operator List không có dòng ``多核联合`` cho ``Concat`` [T1 OPL tr.58], hai guide liệt kê ``Concat`` là op đa nhân [T1 UG232 tr.75] [T1 UG152 tr.27]. Bảng đo cho thấy phần lớn ``Concat`` chia.
- ``Add``: 8 trên 8 dòng ở model SiLU và 2 trên 2 dòng ở model ReLU chia.
- ``Split`` ({r_silu['Split']['rows']} dòng), ``MaxPool`` ({r_silu['MaxPool']['rows']} dòng), ``Resize`` ({r_silu['Resize']['rows']} dòng) đều chỉ nhân 0 ở cả hai model.
- Trong bảng, ``Reshape``, ``Sub``, ``Mul``, ``Sigmoid``, ``exSoftmax13`` có WorkLoad ``100.0%/0.0%/0.0%`` (riêng {r_silu['Reshape']['rows'] - r_silu['Reshape']['workloads'].get('100.0%/0.0%/0.0%', 0)} trên {r_silu['Reshape']['rows']} dòng ``Reshape`` là ``0.0%/0.0%/0.0%``), ``Transpose``, ``InputOperator``, ``OutputOperator`` có ``0.0%/0.0%/0.0%``.

Hai dòng ``Resize`` chọn theo tên op: ở ``CORE_0_1_2`` WorkLoad ``100.0%/0.0%/0.0%``, thời gian dòng trong bảng ``perf_debug`` nằm trong vòng 0.5 µs so với ``CORE_0``.
""")
w(table(["Model", "Dòng (ID)", "Thời gian ``CORE_0_1_2`` (µs)", "Thời gian ``CORE_0`` (µs)"],
        [[n, f"``{r['name'].split(':')[1]}`` ({r['id']})", f(r["time_us_core012"], 1), f(r["time_us_core0"], 1)] for n, k in (("SiLU", "silu"), ("ReLU", "relu")) for r in G["resize"][k]], [10, 34, 24, 24]))
w(f"""
Các số này là thời gian dòng trong chế độ ``perf_debug`` và không đo trực tiếp ảnh hưởng của ``Resize`` lên latency tổng. Hai dòng ``Resize`` cộng {f(sum(r['time_us_core012'] for r in G['resize']['relu']), 1)} µs ở model ReLU, so với latency {f(cond['relu|CORE_0_1_2']['median'] * 1000, 0)} µs của model này ở ``CORE_0_1_2``.

4. Điều kiện B: latency
=======================

Trung vị của hai trung vị phiên (mỗi phiên là trung vị 5 lần ``eval_perf``) cho mỗi tổ hợp, đơn vị ms. Chênh hai phiên là chênh giữa hai trung vị phiên của tổ hợp.
""")
rows = []
for m, name in (("silu", "SiLU"), ("relu", "ReLU")):
    for k in ("CORE_0", "CORE_0_1", "CORE_0_1_2", "AUTO"):
        c = cond[f"{m}|{k}"]
        rows.append([name, f"``{k}``", ", ".join(f(x, 3) for x in c["session_medians"]), f(c["median"], 3), f(c["gap_ms"], 3)])
w(table(["Model", "Mask", "Trung vị hai phiên (ms)", "Trung vị chung (ms)", "Chênh hai phiên (ms)"], rows, [10, 16, 28, 18, 18]))
w("""
Quy tắc B (viết trước dữ liệu): giảm so với ``CORE_0`` tính bằng trung vị chung. Mask được coi là nhanh hơn khi giảm ít nhất 5% và mức giảm (ms) lớn hơn chênh hai phiên lớn nhất của hai tổ hợp so sánh. Cổng B là kết quả của ReLU ở ``CORE_0_1_2``, SiLU là đối chứng.
""")
w(table(["Model", "Mask", "Giảm (ms)", "Giảm (%)", "Chênh hai phiên lớn nhất (ms)", "Kết quả"],
        [[n, f"``{k}``", f(gb[f'{m}|{k}']['drop_ms'], 3), f(gb[f'{m}|{k}']['drop_pct'], 2), f(gb[f'{m}|{k}']['gap_ms'], 3), gb[f'{m}|{k}']['verdict']]
         for m, n in (("silu", "SiLU"), ("relu", "ReLU")) for k in ("CORE_0_1", "CORE_0_1_2")], [10, 16, 12, 12, 26, 18]))
rs = G["relu_vs_silu"]
w(f"""
Điều kiện B đạt cho ReLU ({f(gb['relu|CORE_0_1_2']['drop_pct'], 1)}% lớn hơn 5%, {f(gb['relu|CORE_0_1_2']['drop_ms'], 3)} ms lớn hơn {f(gb['relu|CORE_0_1_2']['gap_ms'], 3)} ms). SiLU không đạt ({f(gb['silu|CORE_0_1_2']['drop_pct'], 1)}%). Mô tả chéo: ở ``CORE_0`` ReLU nhanh hơn SiLU {f(-rs['CORE_0']['diff_pct'], 1)}% ({f(rs['CORE_0']['silu_ms'], 3)} so với {f(rs['CORE_0']['relu_ms'], 3)} ms), ở ``CORE_0_1_2`` nhanh hơn {f(-rs['CORE_0_1_2']['diff_pct'], 1)}% ({f(rs['CORE_0_1_2']['silu_ms'], 3)} so với {f(rs['CORE_0_1_2']['relu_ms'], 3)} ms). Nguyên nhân của chênh lệch ở ``CORE_0`` giữa hai activation chưa biết, dữ liệu chỉ cho biết ``ConvExSwish`` chiếm {pct(bo['silu']['ConvExSwish']['time_share_core0'], 1)} tổng thời gian dòng ở SiLU và ``ConvRelu`` cộng ``ConvReluAdd`` chiếm {pct(bo['relu']['ConvRelu']['time_share_core0'] + bo['relu']['ConvReluAdd']['time_share_core0'], 1)} ở ReLU.

``AUTO`` so với ``CORE_0``: SiLU {pm(G['auto_vs_core0']['silu']['diff_ms'], 3)} ms (chênh hai phiên lớn nhất {f(G['auto_vs_core0']['silu']['gap_ms'], 3)} ms), ReLU {pm(G['auto_vs_core0']['relu']['diff_ms'], 3)} ms ({f(G['auto_vs_core0']['relu']['gap_ms'], 3)} ms).

5. Điều kiện C: mAP và nhiễu seed
=================================

Chấm bằng RKNNLite trên board, cùng mã và cùng ngưỡng tin cậy cho mọi model (``make evaluate BACKEND=rknn``). Tập cổng là ``css_test`` ({cs['silu']['n_images']} ảnh, {cs['silu']['instances_nohelmet']} instance ``NoHelmet``). Tập ``ppe2286_ext`` (180 ảnh) chỉ để mô tả. AP là AP50-95 của class, đơn vị điểm phần trăm.
""")
rows = []
for key, name in (("css_test|int8", "css_test INT8 (kết luận)"), ("css_test|fp16", "css_test FP16 (tham chiếu)"), ("css_test|fp32", "css_test FP32 PyTorch (mô tả)"),
                  ("ppe2286_ext|int8", "ppe2286_ext INT8 (mô tả)"), ("ppe2286_ext|fp16", "ppe2286_ext FP16 (mô tả)"), ("ppe2286_ext|fp32", "ppe2286_ext FP32 (mô tả)")):
    v = gc[key]
    rows.append([name] + [f"{f(v['silu'][c], 2)} / {f(v['relu'][c], 2)} / {pm(v['diff_pp'][c])}" for c in ("map50_95", "NoHelmet", "Vest")] + ["đạt" if v["passes"] else "không đạt"])
w(table(["Tập và dtype", "AP50-95 (SiLU / ReLU / chênh)", "AP NoHelmet", "AP Vest", "Cả ba chênh >= -1.0"], rows, [26, 26, 26, 26, 14]))
w(f"""
Cổng C chỉ dùng hàng ``css_test`` INT8: AP50-95 {pm(cs['diff_pp']['map50_95'])} điểm và AP NoHelmet {pm(cs['diff_pp']['NoHelmet'])} điểm đều dưới -1.0, AP Vest {pm(cs['diff_pp']['Vest'])} điểm. Kết quả: **C không đạt**. Ở FP16 (tham chiếu) và FP32 (mô tả) cũng thấp hơn SiLU ở AP50-95 trên ``css_test``.

Nhiễu giữa seed (chỉ mô tả, không phải cổng): baseline SiLU seed 0, 1, 2 chấm cùng đường, INT8 dùng cùng danh sách hiệu chuẩn. Khoảng trải là lớn nhất trừ nhỏ nhất. Quy tắc viết trước: mức 1.0 điểm "trong nhiễu seed" khi khoảng trải của cột đó từ 1.0 điểm trở lên, "ngoài nhiễu seed" khi dưới 1.0. Có ba seed nên độ lệch chuẩn mẫu chỉ đi kèm, không phải kết luận.
""")
rows = []
for key, name in (("css_test|int8", "css_test INT8"), ("css_test|fp16", "css_test FP16"), ("css_test|fp32", "css_test FP32"), ("ppe2286_ext|int8", "ppe2286_ext INT8")):
    for c, cn in (("map50_95", "AP50-95"), ("NoHelmet", "AP NoHelmet"), ("Vest", "AP Vest")):
        v = nz[key][c]
        rows.append([name, cn, " / ".join(f(x, 2) for x in v["values"]), f(v["range"], 2), f(v["std"], 2), v["verdict"]])
w(table(["Tập và dtype", "Cột", "Seed 0 / 1 / 2", "Khoảng trải", "Độ lệch chuẩn mẫu", "Mức 1.0 điểm"], rows, [20, 14, 26, 14, 18, 18]))
w(f"""
Trên ``css_test`` INT8 mức giảm của ReLU ở AP50-95 ({f(-cs['diff_pp']['map50_95'], 2)} điểm) và ở AP NoHelmet ({f(-cs['diff_pp']['NoHelmet'], 2)} điểm) lớn hơn khoảng trải giữa ba seed SiLU ({f(n8['map50_95']['range'], 2)} và {f(n8['NoHelmet']['range'], 2)} điểm). Nhiễu của chính ReLU xem ở bảng ngay dưới. Cổng C đọc theo ngưỡng 1.0 điểm đã duyệt, không phụ thuộc phần mô tả nhiễu này. AP Vest của riêng một class dao động {f(n8['Vest']['range'], 2)} điểm giữa ba seed SiLU, lớn hơn ngưỡng 1.0 điểm.

Nhiễu seed của ReLU (thêm theo duyệt của người dùng ngày 2026-10-31, quy tắc viết trước ``bench/eval_g4/rule_relu_seeds.txt``). ReLU seed 1 và 2 huấn luyện cùng cấu hình, INT8 dùng cùng danh sách hiệu chuẩn của seed 0. Cột "Chênh trung bình" là trung bình ba seed ReLU trừ trung bình ba seed SiLU. Chênh "lớn hơn nhiễu seed" khi giá trị tuyệt đối lớn hơn khoảng trải lớn hơn trong hai nhóm. Ba seed không đủ để kiểm định, đây là mô tả.
""")
rows = []
for key, name in (("css_test|int8", "css_test INT8"), ("css_test|fp16", "css_test FP16"), ("css_test|fp32", "css_test FP32"), ("ppe2286_ext|int8", "ppe2286_ext INT8")):
    for c, cn in (("map50_95", "AP50-95"), ("NoHelmet", "AP NoHelmet"), ("Vest", "AP Vest")):
        v = C["relu_noise"][key][c]
        rows.append([name, cn, " / ".join(f(x, 2) for x in v["values"]), f(v["range"], 2), f(v["silu_range"], 2), pm(v["mean_diff"]), v["verdict"]])
w(table(["Tập và dtype", "Cột", "ReLU seed 0 / 1 / 2", "Khoảng trải ReLU", "Khoảng trải SiLU", "Chênh trung bình", "So với nhiễu"], rows, [18, 14, 24, 12, 12, 12, 18]))
w(f"""
Cổng C của từng seed ReLU so với SiLU cùng số seed (``css_test`` INT8, AP50-95 / AP NoHelmet / AP Vest, điểm):
""")
w(table(["Seed", "AP50-95", "AP NoHelmet", "AP Vest", "Cổng C"],
        [[p_["seed"], pm(p_["diff_pp"]["map50_95"]), pm(p_["diff_pp"]["NoHelmet"]), pm(p_["diff_pp"]["Vest"]), "đạt" if p_["passes"] else "không đạt"] for p_ in rg["per_seed"]], [10, 16, 16, 16, 16]))
w(f"""
Trên ``css_test`` INT8 mức giảm trung bình của ReLU ở AP50-95 ({f(-rn['map50_95']['mean_diff'], 2)} điểm) và AP NoHelmet ({f(-rn['NoHelmet']['mean_diff'], 2)} điểm) lớn hơn khoảng trải của cả hai nhóm seed. AP Vest ({pm(rn['Vest']['mean_diff'])} điểm) nằm trong nhiễu seed. Trên ``ppe2286_ext`` INT8 chênh AP50-95 là {pm(C['relu_noise']['ppe2286_ext|int8']['map50_95']['mean_diff'])} điểm, trong nhiễu seed.

6. Nhãn của ứng viên
====================
""")
w(table(["Bước", "Kết quả", "Nhãn bước"], [
    ["G1", "``ConvRelu`` ánh xạ được sang ``ConvolutionRelu`` theo tên, ``ConvReluAdd`` không có mục cùng tên (mục 2.1)", "qua một phần"],
    ["G2", "Không có bằng chứng T2 cùng SoC (mục 2.1)", "ghi nhận"],
    ["G3", "Ngoài ``InputOperator`` và ``OutputOperator``, chỉ ``Transpose`` ở CPU, như SiLU (mục 2.2)", "qua"],
    ["G4 A", f"Độ phủ {pct(min(ga['relu']['coverage_per_session']), 1)} (mục 3)", "đạt"],
    ["G4 B", f"``CORE_0_1_2`` nhanh hơn ``CORE_0`` {f(gb['relu|CORE_0_1_2']['drop_pct'], 1)}% (mục 4)", "đạt"],
    ["G4 C", f"AP50-95 {pm(cs['diff_pp']['map50_95'])}, AP NoHelmet {pm(cs['diff_pp']['NoHelmet'])}, AP Vest {pm(cs['diff_pp']['Vest'])} điểm (mục 5)", "không đạt"],
], [10, 70, 20]))
w("""
Nhãn: **Loại** (ReLU, seed 0 theo chuẩn, trượt ở điều kiện C của G4, cả 3 seed ReLU đều trượt khi so với SiLU cùng seed). Ứng viên dừng ở bước đầu tiên không qua theo tiêu chuẩn. Điều kiện A và B đạt cho thấy ReLU nhanh hơn rõ rệt, và đó là phép đo đúng như đã ghi, nhưng không thay đổi nhãn vì cổng yêu cầu cả ba điều kiện. Nhãn này không nói ReLU không bao giờ dùng được, chỉ nói bản huấn luyện này (100 epoch, khởi tạo từ trọng số SiLU, 1 seed) không đạt ngưỡng mAP đã duyệt. Các biến thể LeakyReLU, ReLU6 và ReLU 200 epoch đã chạy và ở :doc:`02-ket-qua-bien-the-activation`.

7. Điều chưa biết
=================
""")
w(table(["Việc", "Trạng thái", "Đã tìm hoặc đo gì"], [
    ["``ConvReluAdd`` có mục đa nhân trong T1", "chưa biết theo T1", "Operator List V2.3.2 và mọi văn bản T1 (mục 2.1). Hành vi đo: chia ba nhân"],
    ["Vì sao ``asymmetric`` với ``nearest_mode = floor`` vẫn lên NPU (G7)", "chưa biết (đo thêm 2026-11-01: thuộc tính bị bỏ qua ở micro model, :doc:`08-so-muc-chua-biet` mục 2)", "Operator List tr.86 đến 87 chỉ nêu giới hạn. Trong gói toolkit có chuỗi tên pass ``_p_convert_resize_to_deconv`` và thông báo ``Resize [{}] convert to Deconvolution for inference speedup, but may cause result driftting.``, chưa đọc logic nên chưa biết điều kiện kích hoạt"],
    ["Vì sao Reshape 8 nút ONNX thành 7 dòng RKNN và Slice thành Split (G10)", "ĐO (mô tả, 2026-11-01, :doc:`08-so-muc-chua-biet` mục 3). Vì sao: chưa biết", "Không có giải thích văn bản trong T1 hoặc T2. Chỉ thấy tên pass trong binary (``_p_remove_reshape_after_concat``, ``_p_replace_parallel_slice_by_split``)"],
    ["Mâu thuẫn Relu và Concat giữa Operator List và hai guide (G11)", "ĐO ở micro model (2026-11-01, :doc:`08-so-muc-chua-biet` mục 4). Tài liệu nào đúng: chưa biết", "Không tài liệu T1 nào khác giải quyết (changelog, header). Bảng đo cho thấy 15 trên 17 ``Concat`` chia"],
    ["Vì sao ``CORE_0`` của ReLU nhanh hơn SiLU", "chưa biết", "Mục 4 chỉ mô tả tỉ lệ thời gian dòng"],
    ["Nhiễu seed của ReLU", "ĐO", "Ba seed (mục 5): khoảng trải AP50-95 INT8 trên ``css_test`` là " + f(rn["map50_95"]["range"], 2) + " điểm"],
    ["Kết quả của P2 so với giao thức chính", "chưa biết", "P2 đã được người dùng duyệt nguyên trạng ngày 2026-11-01, kết quả của P2 so với giao thức gốc chưa đo thêm"],
], [34, 18, 48]))
w("""
8. Nguồn
========

- T1: Operator List V2.3.2 (``docs/_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf``, tr.58 đến 63, 84, 86 đến 87, 98), SDK User Guide V2.3.2 (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, tr.75, 109 đến 110, 177), API guide V1.5.2 tr.27, ``3rdparty/rknn-toolkit2/rknn-toolkit2/doc/changelog-2.3.2.txt`` dòng 284.
- T2: ``edgesoc_benchmark_2026kong.pdf``, ``docs/_assets/pdf/papers/08_npu_friendly_arch/actnas_yolo_2025sah.pdf`` (ActNAS).
- T3 PC và board: ``results/g4_latency_workload.*``, ``results/eval_g4.*``, ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_g4b/``, ``bench/eval_g4/``, ``export_int8.json`` và ``export_fp16.json`` của các run, ``ai/automation/runs/ppe5_yolov8n_relu_100ep_s0/``.
- Quy tắc viết trước dữ liệu: ``bench/onboard_g4b/rule.txt``, ``bench/eval_g4/rule.txt``.
- Tổng hợp tìm nguồn: ``results/phase2_source_facts.md``.
""")
pages["01-ket-qua-g4.rst"] = "\n".join(P)

# ------------------------------------------------------------------ 03-ket-qua-da-nhan
P = []
w = P.append
cfg = T["configs"]
m12, m13, m3, m14 = T["m12"], T["m13"], T["m3"], T["m14"]
x4 = X4["masks"]
assert x4["AUTO"]["irq_lines_per_session"] and all(x == {"36": 315, "37": 0, "38": 0} for x in x4["AUTO"]["irq_lines_per_session"])
w(f"""*******
Đa nhân
*******

.. admonition:: Trang này trả lời

   - S1 (một context chia nhiều nhân), S2 (ba context mỗi context một nhân) và S3 (pipeline pre, NPU, post) có đạt ngưỡng 5% của dự án không, trên model SiLU INT8?
   - Chạy ba tiến trình thay ba luồng có khác throughput không, và mỗi context thêm bao nhiêu bộ nhớ?
   - ``AUTO`` chọn nhân nào trong phép đo của dự án, và còn điều gì về đa nhân chưa biết?

.. admonition:: Tóm tắt

   - S1 trên SiLU: ``CORE_0_1_2`` nhanh hơn ``CORE_0`` chỉ {f(gb['silu|CORE_0_1_2']['drop_pct'], 1)}% và ``CORE_0_1`` {f(gb['silu|CORE_0_1']['drop_pct'], 1)}%, dưới ngưỡng 5%. Latency một frame dùng ``CORE_0``. Với ReLU mức giảm là {f(gb['relu|CORE_0_1_2']['drop_pct'], 1)}% nhưng ReLU đã bị loại ở cổng G4 (:doc:`01-ket-qua-g4`).
   - S2 (ba context): {f(cfg['T5']['fps'], 1)} FPS, so với {f(cfg['T3']['fps'], 1)} FPS của cấu hình một context tốt nhất ({m12['best']}), tăng {f(m12['gain_pct'], 1)}%, lớn hơn khoảng trải {f(m12['larger_spread'], 2)} FPS. Kết quả: hơn.
   - S3 (pipeline): {f(cfg['T6']['fps'], 1)} FPS so với {f(cfg['T5']['fps'], 1)} FPS của S2, tăng {f(m13['gain_pct'], 1)}%, dưới ngưỡng 5%. CPU trung bình của tiến trình {f(m13['cpu_t6'], 1)}% so với {f(m13['cpu_t5'], 1)}%. Kết quả: không đáng giữ (với {m13['workers']['pre']} luồng pre và {m13['workers']['post']} luồng post theo công thức đã viết trước).
   - Ba tiến trình ({f(cfg['T7']['fps'], 1)} FPS) so với ba luồng ({f(cfg['T5']['fps'], 1)} FPS): khác {pm(m3['diff_pct'], 1)}%, không phân biệt được trong độ trải. Phép đo chẩn đoán này không nói vì sao.
   - Giao thức P3 của S2 và S3 là giao thức mới (ngắt NPU 36, 37, 38 lần lượt ở CPU4, CPU5, CPU6, tiến trình đo ở CPU4 đến CPU7, ``irqbalance`` dừng), đã được người dùng duyệt ngày 2026-11-01. S1 chạy dưới P2 của nhóm Nền đo NPU, cũng đã được người dùng duyệt ngày 2026-11-01. Mọi số là một board, một model, một seed.

Cổng G4 và workload từng loại op ở :doc:`01-ket-qua-g4`. Tiêu chí 5% và 3 lần chạy độc lập ở :doc:`../03-tang-npu-don-bay/02-multi-core` (mục 5.2).

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Điều kiện chạy
=================

""")
w(table(["Phép đo", "Giao thức", "Model", "Chi tiết"], [
    ["S1 latency", "P2 (như nhóm Nền đo NPU)", f"SiLU seed 0 INT8 (sha ``{sha8(SILU)}``) và ReLU seed 0 INT8 (``{sha8(RELU)}``)", "16 phiên xen kẽ, cùng lần chạy với cổng G4 (:doc:`01-ket-qua-g4` mục 1)"],
    ["S1 throughput, S2, S3, chẩn đoán", "P3 (mới)", f"SiLU seed 0 INT8 (``{sha8(SILU)}``)", "``bench_throughput_rep.py`` trên board, 3 lần chạy độc lập mỗi cấu hình, 1238 frame, 20 frame warm-up mỗi context"],
], [18, 22, 36, 44]))
w(f"""
Chọn SiLU cho S2 và S3 vì mỗi context chạy một nhân, nên việc op activation có đa nhân hay không không tham gia. ReLU không đo ở S2 và S3 (chưa biết).

Về điều kiện chung ở :doc:`../03-tang-npu-don-bay/02-multi-core` mục 5.2: sổ tay SDK khuyên gắn ứng dụng và ngắt NPU vào cùng một lõi CPU lớn [T1 UG232 tr.75]. P3 không làm vậy: ba dòng ngắt ở ba lõi lớn khác nhau (CPU4, CPU5, CPU6) và ứng dụng chạy trên cả CPU4 đến CPU7, vì ba context chạy song song và dồn tất cả vào một CPU sẽ làm các context tranh nhau CPU, không đo được S2 và S3. Nên P3 lệch khỏi khuyến nghị đó, và nhãn S2, S3 mang điều kiện này. S1 dưới P2 theo khuyến nghị (ngắt và ``rknn_server`` cùng CPU4).

P3 vì sao tách khỏi P2: P2 dồn ``rknn_server`` và cả ba ngắt vào CPU4, dự kiến sẽ tuần tự hóa ba context và một pipeline vào một CPU (chưa đo). Harness cũ ``bench_throughput.py`` chạy ``RKNNLite`` trực tiếp trên board, không đi qua ``rknn_server``, nên tiến trình giữ P2 không bao phủ. P3 gồm: dừng ``irqbalance``, ngắt 36 vào CPU4, 37 vào CPU5, 38 vào CPU6 (đặt một lần bởi ``p3_hold.sh``, khôi phục và đọc lại cuối lần chạy), tiến trình đo chạy dưới ``taskset -c 4-7``, tần số khóa, ``rknn_server`` không đụng. Một run thực hiện đúng P3 khi mỗi dòng ngắt có ít nhất 99% số ngắt ở CPU được gán, affinity của tiến trình nằm trong CPU4 đến CPU7, tần số báo khóa và nhật ký helper ghi ``irqbalance`` không chạy cùng ba affinity không đổi. Cả {len(T['runs'])} run thực hiện đúng. Ở các run ba context (T5, T6, T7) cả ba dòng ngắt 36, 37, 38 đều có số ngắt lớn hơn 0, ít nhất {min(cfg[c]['irq_line_min'] for c in ('T5', 'T6', 'T7'))} mỗi dòng, mỗi dòng ở CPU được gán.

Harness mới sửa các giới hạn của harness cũ ở :doc:`../03-tang-npu-don-bay/02-multi-core` mục 3.3: mỗi lần gọi là một tiến trình độc lập (khởi tạo lại context), lặp ba lần, ghi ``T_pre``, ``T_npu``, ``T_post`` từng frame, ghi RSS, nhiệt độ, tần số và ngắt theo CPU, và warm-up chạy qua 20 ảnh đầu thay vì một frame. Tập ảnh là ``data/ppe5/processed/images/test``, chỉ có {T['runs'][0]['cached_images']} ảnh nên bộ nhớ đệm giữ {T['runs'][0]['cached_images']} ảnh (không phải 200).

2. S1: một context chia nhân
============================

2.1. Latency dưới P2
--------------------

Số liệu và quy tắc ở :doc:`01-ket-qua-g4` mục 4. Với SiLU:
""")
w(table(["Mask", "Trung vị (ms)", "Giảm so với CORE_0 (%)", "Chênh hai phiên lớn nhất (ms)", "Kết quả"],
        [["``CORE_0``", f(cond['silu|CORE_0']['median'], 3), "-", "-", "-"]] + [[f"``{k}``", f(cond[f'silu|{k}']['median'], 3), f(gb[f'silu|{k}']['drop_pct'], 2), f(gb[f'silu|{k}']['gap_ms'], 3), gb[f'silu|{k}']['verdict']] for k in ("CORE_0_1", "CORE_0_1_2")], [16, 16, 22, 28, 18]))
w(f"""
Cả hai mask đa nhân đều dưới ngưỡng 5%. Theo quy tắc ở :doc:`../03-tang-npu-don-bay/02-multi-core` (mục 5.3, bước 1) S1 bị loại cho trục latency của SiLU, và latency một frame dùng ``CORE_0``. Độ phủ (điều kiện A) của SiLU là {pct(max(ga['silu']['coverage_per_session']), 1)} (:doc:`01-ket-qua-g4` mục 3). Với ReLU, ``CORE_0_1`` giảm {f(gb['relu|CORE_0_1']['drop_pct'], 1)}% và ``CORE_0_1_2`` giảm {f(gb['relu|CORE_0_1_2']['drop_pct'], 1)}%, đạt B (ReLU bị loại ở C).

2.2. Throughput một context dưới P3
-----------------------------------

""")
w(table(["Cấu hình", "FPS ba lần chạy", "FPS trung vị", "Khoảng trải", "T_npu trung vị (ms)"],
        [[cfg[c]["label"], " / ".join(f(x, 2) for x in cfg[c]["fps_runs"]), f(cfg[c]["fps"], 2), f(cfg[c]["spread"], 2), f(cfg[c]["t_npu"], 2)] for c in ("T1", "T2", "T3")], [26, 30, 14, 14, 18]))
p2fps = 1000 / cond["silu|CORE_0"]["median"]
w(f"""
Throughput một context gần như không phụ thuộc mask (chênh {f(100 * (cfg['T3']['fps'] / cfg['T1']['fps'] - 1), 1)}% giữa ``CORE_0_1_2`` và ``CORE_0``). Tham chiếu của P2: một context ``CORE_0`` có latency {f(cond['silu|CORE_0']['median'], 3)} ms, tương đương {f(p2fps, 1)} FPS nếu chỉ tính phần NPU. Harness đo cả pre và post và chạy dưới P3, được {f(cfg['T1']['fps'], 1)} FPS. Hai con số khác nhau về điều kiện và về vùng đo, nên không so trực tiếp.

3. S2: ba context mỗi context một nhân
======================================

Quy tắc viết trước: cấu hình một context tốt nhất là cấu hình có FPS trung vị cao nhất trong T1, T2, T3 (ở đây {m12['best']}, mức chặt hơn cả ``CORE_0``). S2 hơn khi FPS ít nhất 1.05 lần và mức tăng lớn hơn khoảng trải lớn hơn trong hai cấu hình.
""")
w(table(["Cấu hình", "FPS ba lần chạy", "FPS trung vị", "Khoảng trải", "CPU trung bình của tiến trình (%)"],
        [[cfg[c]["label"], " / ".join(f(x, 2) for x in cfg[c]["fps_runs"]), f(cfg[c]["fps"], 2), f(cfg[c]["spread"], 2), f(cfg[c]["cpu_pct"], 1)] for c in ("T1", "T4", "T5")], [28, 30, 14, 14, 24]))
w(f"""
S2 (T5) so với cấu hình một context tốt nhất ({m12['best']}): tăng {f(m12['gain_fps'], 2)} FPS ({f(m12['gain_pct'], 1)}%), lớn hơn khoảng trải {f(m12['larger_spread'], 2)} FPS. Kết quả: **hơn**. So với ``CORE_0`` (T1) tăng {f(100 * (cfg['T5']['fps'] / cfg['T1']['fps'] - 1), 1)}%. Hai context (T4) đạt {f(cfg['T4']['fps'], 1)} FPS. Đây là số đo T3 board, cơ chế (hàng đợi riêng từng nhân của driver, :doc:`../03-tang-npu-don-bay/02-multi-core` mục 3.1) là cơ sở đã ghi chưa phải kết quả đã chứng minh.

Bộ nhớ (mô tả): RSS của tiến trình sau khi khởi tạo context là {f(m14['t1_after_init'], 1)} MiB với một context và {f(m14['t5_after_init'], 1)} MiB với ba context, tức khoảng {f(m14['per_added_context'], 1)} MiB mỗi context thêm. Đây là RSS của tiến trình Python, không gồm bộ nhớ NPU do driver cấp.

4. S3: pipeline pre, NPU, post
==============================

S3 tách worker pre, một worker NPU mỗi context (ba context trên ``CORE_0``, ``CORE_1``, ``CORE_2``) và worker post, nối bằng hàng đợi 6 phần tử. Số worker lấy từ công thức viết trước từ lần chạy T5 đầu tiên: ``T_npu`` trung vị chia ba là thời gian NPU hiệu dụng mỗi frame, số worker pre và post là trần của ``T_pre`` hoặc ``T_post`` chia thời gian đó, tối thiểu 1 và tối đa 3. Kết quả: {m13['workers']['pre']} worker pre và {m13['workers']['post']} worker post.
""")
w(table(["Cấu hình", "FPS ba lần chạy", "FPS trung vị", "Khoảng trải", "CPU trung bình của tiến trình (%)", "T_pre / T_npu / T_post trung vị (ms)"],
        [[cfg[c]["label"], " / ".join(f(x, 2) for x in cfg[c]["fps_runs"]), f(cfg[c]["fps"], 2), f(cfg[c]["spread"], 2), f(cfg[c]["cpu_pct"], 1),
          f"{f(cfg[c]['t_pre'], 2)} / {f(cfg[c]['t_npu'], 2)} / {f(cfg[c]['t_post'], 2)}"] for c in ("T5", "T6")], [20, 28, 12, 12, 20, 30]))
w(f"""
S3 hơn S2 {f(m13['gain_fps'], 2)} FPS ({f(m13['gain_pct'], 1)}%), lớn hơn khoảng trải {f(m13['larger_spread'], 2)} FPS nhưng dưới ngưỡng 5%. CPU trung bình cao hơn {f(-m13['cpu_gain'], 1)} điểm so với S2 (khoảng trải {f(m13['cpu_spread'], 1)}). Nhánh CPU thấp hơn của quy tắc chỉ áp dụng khi mức tăng FPS nằm trong khoảng trải, nên không áp dụng ở đây. Kết quả: **không đáng giữ**. Giới hạn: một công thức chọn số worker, không tìm kiếm. S3 với số worker khác chưa biết. Trung vị ``T_pre``, ``T_npu``, ``T_post`` của S2 là {f(cfg['T5']['t_pre'], 2)}, {f(cfg['T5']['t_npu'], 1)} và {f(cfg['T5']['t_post'], 2)} ms. Nguyên nhân của mức tăng nhỏ của S3 chưa biết, vì phép đo không tách các yếu tố.

5. Chẩn đoán: ba tiến trình và ba luồng
=======================================

Cùng ba context trên ``CORE_0``, ``CORE_1``, ``CORE_2``, chạy bằng ba tiến trình (T7) so với ba luồng (T5). Đây là chẩn đoán, không phải chiến lược và không phải cổng.
""")
w(table(["Cấu hình", "FPS ba lần chạy", "FPS trung vị", "Khoảng trải"],
        [[cfg[c]["label"], " / ".join(f(x, 2) for x in cfg[c]["fps_runs"]), f(cfg[c]["fps"], 2), f(cfg[c]["spread"], 2)] for c in ("T5", "T7")], [30, 30, 14, 14]))
w(f"""
Chênh {pm(m3['diff_fps'], 2)} FPS ({pm(m3['diff_pct'], 1)}%), dưới 5% nên kết quả là không phân biệt được. Hai điều rút ra và chỉ hai: ba tiến trình, mỗi tiến trình một context trên ``CORE_0``, ``CORE_1``, ``CORE_2``, chạy được đồng thời với RKNNLite và cả ba dòng ngắt đều có ngắt trong mọi run (mục 1), và throughput không khác ba luồng ở mức 5% trong điều kiện này. Chưa kết luận gì về việc ``RKNNLite.inference`` có nhả GIL không, vì thời gian trong hai chế độ có thể giống nhau do nguyên nhân khác. Cột CPU của T7 không dùng vì chỉ đo tiến trình cha.

6. AUTO chọn nhân nào
=====================

Trong lần đo P2 ở nhóm Nền đo NPU (``onboard_x4``), bốn phiên ``AUTO`` đều có số ngắt ``{{36: 315, 37: 0, 38: 0}}`` mỗi phiên, giống ``CORE_0``, còn ``CORE_0_1_2`` có ``{{36: 385, 37: 145, 38: 145}}``. Trong chuỗi một context chạy lần lượt, ``AUTO`` đã chạy trên cùng dòng ngắt với ``CORE_0`` ở cả 4 phiên. Driver chọn lõi có hàng đợi ngắn nhất và lấy chỉ số thấp nhất khi hòa [T1 DRV rknpu_job.c:508-538], sổ tay nói "idle core" [T1 UG232 tr.73]. Với mô tả của driver thì một job một lúc ra nhân 0. Sổ tay không nêu cách chọn khi mọi lõi đều rảnh, nên phép đo này không phân biệt được hai mô tả. Trong phép đo mới ở :doc:`01-ket-qua-g4`, ``AUTO`` so với ``CORE_0`` chênh {pm(G['auto_vs_core0']['silu']['diff_ms'], 3)} ms ở SiLU và {pm(G['auto_vs_core0']['relu']['diff_ms'], 3)} ms ở ReLU.

7. Nhãn và điều chưa biết
=========================
""")
w(table(["Chiến lược", "Nhãn", "Số liệu", "Điều kiện"], [
    ["S1 (SiLU, latency)", "Loại", f"``CORE_0_1_2`` giảm {f(gb['silu|CORE_0_1_2']['drop_pct'], 1)}%, ``CORE_0_1`` giảm {f(gb['silu|CORE_0_1']['drop_pct'], 1)}%", "1 seed, dưới P2"],
    ["S1 (ReLU, latency)", "không áp dụng (ReLU bị loại ở G4 C)", f"``CORE_0_1_2`` giảm {f(gb['relu|CORE_0_1_2']['drop_pct'], 1)}%", "1 seed, dưới P2"],
    ["S2 (throughput)", "Giữ", f"{f(cfg['T5']['fps'], 1)} FPS, tăng {f(m12['gain_pct'], 1)}% so với một context tốt nhất", "1 seed, dưới P3 (đã duyệt ngày 2026-11-01), lệch khỏi khuyến nghị gắn ngắt NPU vào cùng một lõi lớn (UG232 tr.75), một model"],
    ["S3 (throughput)", "Loại", f"{f(cfg['T6']['fps'], 1)} FPS, tăng {f(m13['gain_pct'], 1)}% so với S2", "1 seed, dưới P3 (như S2), một công thức số worker"],
], [24, 32, 50, 36]))
w("""
Các điểm đa nhân còn lại và trạng thái sau giai đoạn này:
""")
w(table(["Mã", "Câu hỏi", "Trạng thái", "Đã tìm hoặc đo gì"], [
    ["M1", "Quy tắc chia job đa nhân của ``librknnrt``", "chưa biết (mẫu chia mô tả 2026-11-01, :doc:`08-so-muc-chua-biet` mục 5)", "Mã nguồn thư viện không có trong repo. Bảng WorkLoad cho thấy phần trăm chia từng lớp (ví dụ 35.0%/32.5%/32.5%) nhưng quy tắc chưa suy ra"],
    ["M2", "``ALL`` trong Table 4 của Kong 2026 là chế độ nào", "ĐO một phần (2026-11-01, :doc:`08-so-muc-chua-biet` mục 6): ``NPU_CORE_ALL`` chia như ``CORE_0_1_2``. Nghĩa trong bài: chưa biết", "Bài báo không định nghĩa ``ALL``, không nêu tên cờ ``core_mask``, dữ liệu theo yêu cầu từ tác giả (Data availability, tr.11). ``RKNN_NPU_CORE_ALL = 0xffff`` được header ghi là chọn nhân theo nền tảng [T1 rknn_api.h:253]. ``ALL`` đo ngày 2026-11-01 (:doc:`08-so-muc-chua-biet` mục 6)"],
    ["M3, M5", "``RKNNLite.inference`` có nhả GIL không, nhiều tiến trình dùng lõi khác nhau", "ĐO một phần", "Ba tiến trình chạy được trên ba nhân, throughput không khác ba luồng ở mức 5% (mục 5). GIL chưa kết luận"],
    ["M4", "Một context dùng chung nhiều luồng", "ĐO (2026-11-01, :doc:`08-so-muc-chua-biet` mục 7)", "Ba luồng dùng chung một context cho đầu ra sai âm thầm, một luồng đúng. SDK guide tr.153 nói về việc dùng chung context giữa các luồng và ``rknn_dup_context`` nhưng không nêu tính an toàn khi gọi đồng thời [T1 UG232 tr.153]. Harness dùng một context mỗi luồng nên không cần"],
    ["M6", "``async_mode`` làm gì lúc chạy", "ĐO một phần (:doc:`08-so-muc-chua-biet` mục 7)", "API232 tr.16 ghi \"Not Supported yet\". Thăm dò: được chấp nhận, ``inference`` tuần tự vẫn trả đầu ra của ảnh vừa gửi"],
    ["M7", "``rknn_batch_size`` nhiều batch", "ĐO (:doc:`08-so-muc-chua-biet` mục 7), khớp batch 1 không tái lập giữa hai lần chạy", "Batch 4 chạy, đầu ra từng ảnh khớp batch 1 ở lần đầu, một ảnh lệch ở lần lặp. Ngoài phạm vi S1 đến S3"],
    ["M8", "Mục tiêu FPS thời gian thực của dự án", "người dùng chốt 60 FPS (2026-11-01)", "Mục 8: S2 đạt " + f(cfg['T5']['fps'], 1) + " FPS, một context chưa đạt"],
    ["M9", "Lợi ích đa nhân ReLU so với SiLU với model đã huấn luyện", "ĐO", "Mục 2.1 và :doc:`01-ket-qua-g4`: ReLU nhanh hơn, mAP thấp hơn, bị loại"],
    ["M10", "``AUTO`` chọn nhân thế nào", "ĐO một phần", "Mục 6: chạy trên dòng ngắt của nhân 0 khi một job một lúc. Hành vi khi nhiều context chưa đo"],
    ["M14", "Bộ nhớ mỗi context", "ĐO (RSS tiến trình)", "Mục 3. Bộ nhớ NPU chưa đo"],
    ["M16", "Số context tối đa", "ĐO một phần (:doc:`08-so-muc-chua-biet` mục 7)", "32 context đều chạy đúng, dừng ở ngưỡng chặn. Giới hạn thật chưa biết. S2 chỉ dùng 1, 2, 3 context"],
], [8, 40, 18, 70]))
_m = {c: cfg[c] for c in ("T1", "T2", "T3", "T4", "T5", "T6")}
assert all(round(_m[c]["fps"], 1) == v for c, v in (("T1", 54.7), ("T2", 55.8), ("T3", 56.1), ("T4", 102.0), ("T5", 141.2), ("T6", 147.4)))
_met = [c for c in _m if _m[c]["fps"] >= 60]
assert _met == ["T4", "T5", "T6"]
_lat = [c for c in _m if _m[c]["t_pre"] + _m[c]["t_npu"] + _m[c]["t_post"] <= 1000 / 60]
assert _lat == []
w(f"""
8. Mục tiêu 60 FPS của người dùng
=================================

Ngày 2026-11-01 người dùng chốt: mục tiêu là tăng FPS để đáp ứng nhu cầu thực tế, chọn 60 FPS. Người dùng chưa nói rõ đó là FPS của một luồng camera hay tổng nhiều luồng, và là thông lượng hay thời gian cho mỗi khung. Bảng dưới đưa cả hai cách đọc, cách đọc mặc định của tôi là thông lượng của pipeline phát hiện cho một luồng, với giả định các khung độc lập và thứ tự đầu ra không bị ràng buộc (giả định này chưa được kiểm: harness không kiểm thứ tự đầu ra). Đây là bước đạt hoặc không đạt mục tiêu tuyệt đối mà :doc:`../03-tang-npu-don-bay/02-multi-core` mục 5 dự kiến thêm sau các bước hiện có, không thay các bước hiện có.

FPS của harness tính cả tiền xử lý, NPU và hậu xử lý của từng khung (``T_pre``, ``T_npu``, ``T_post``), trên ảnh đã cache trong bộ nhớ. Không gồm thu nhận camera, giải mã video, vẽ và lưu kết quả. Mỗi dòng là trung vị của ba lần chạy.
""")
w(table(["Cấu hình", "FPS", "Đạt 60 FPS (thông lượng)", "T_pre + T_npu + T_post (ms)", "Đạt 16.67 ms mỗi khung"], [
    [cfg[c]["label"], f(cfg[c]["fps"], 1), "đạt" if cfg[c]["fps"] >= 60 else f"không, thiếu {f(60 - cfg[c]['fps'], 1)} FPS ({f(100 * (60 - cfg[c]['fps']) / 60, 1)}%)",
     f(cfg[c]["t_pre"] + cfg[c]["t_npu"] + cfg[c]["t_post"], 2), "đạt" if cfg[c]["t_pre"] + cfg[c]["t_npu"] + cfg[c]["t_post"] <= 1000 / 60 else "không"] for c in _m], [34, 10, 36, 32, 28]))
w(f"""

Đọc theo thông lượng: ba cấu hình một context ({f(cfg['T1']['fps'], 1)} đến {f(cfg['T3']['fps'], 1)} FPS) chưa đạt 60, hai context ({f(cfg['T4']['fps'], 1)} FPS), S2 ({f(cfg['T5']['fps'], 1)} FPS) và S3 ({f(cfg['T6']['fps'], 1)} FPS) đạt. Cấu hình nhỏ nhất đã đo đạt mục tiêu là hai context trên ``CORE_0`` và ``CORE_1`` (điểm đo mở rộng, không phải cổng), dùng CPU trung bình {f(cfg['T4']['cpu_pct'], 0)}% so với {f(cfg['T5']['cpu_pct'], 0)}% của S2. Đọc theo thời gian mỗi khung: tổng ``T_pre`` cộng ``T_npu`` cộng ``T_post`` của mọi cấu hình đã đo lớn hơn 16.67 ms (nhỏ nhất {f(cfg['T3']['t_pre'] + cfg['T3']['t_npu'] + cfg['T3']['t_post'], 2)} ms ở một context ``CORE_0_1_2``), nên không cấu hình nào đạt nếu mỗi khung phải xong trong 16.67 ms. Tổng này là tổng ba trung vị theo giai đoạn, không phải thời gian đầu cuối đo trực tiếp (ở cấu hình nhiều context các giai đoạn chạy dưới tranh chấp, ở S3 còn có thời gian chờ hàng đợi không nằm trong tổng).

Nhãn S1, S2, S3 không đổi (cổng tương đối 5%, mục 7). S2 vừa qua cổng tương đối vừa đạt mục tiêu 60 FPS theo thông lượng. Giới hạn: một seed, giao thức P3 đã duyệt, model INT8 mặc định của seed 0 (``int8h5`` đã đo ở :doc:`09-ket-qua-don-bay-fps` và không khác ``int8`` về thông lượng, ReLU chưa đo thông lượng), ảnh cache, chưa đo với camera thật, chưa đo bộ nhớ NPU. Cách hiểu 60 FPS (một luồng hay tổng, thông lượng hay thời gian mỗi khung) do người dùng xác nhận. Cập nhật 2026-11-01: đòn bẩy một context đã đo ở :doc:`09-ket-qua-don-bay-fps`, model tách đầu với giải mã chồng lấp đạt 60 FPS về thông lượng ở một context (một thí nghiệm, một seed), và ``int8h5`` không khác ``int8`` về thông lượng.
""")
w("""
9. Nguồn
========

- T1: SDK User Guide V2.3.2 tr.72 đến 75, 153 (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``), ``3rdparty/rknn-toolkit2/rknpu2/runtime/Linux/librknn_api/include/rknn_api.h`` dòng 253, mã driver ``3rdparty/rknpu-driver-0.9.8`` (``rknpu_job.c``).
- T2: ``edgesoc_benchmark_2026kong.pdf`` (Table 4 tr.7, Data availability tr.11).
- T3 board: ``results/thr_p3.*``, ``results/g4_latency_workload.*``, ``results/onboard_x4_*``, ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_thr/`` và ``bench/onboard_g4b/``.
- Quy tắc viết trước dữ liệu: ``bench/onboard_thr/rule.txt``, ``bench/onboard_g4b/rule.txt``.
- Mã đo: ``ai/board/bench_throughput_rep.py``, ``ai/automation/analyze_thr.py``, ``ai/automation/analyze_g4.py``.
""")
pages["03-ket-qua-da-nhan.rst"] = "\n".join(P)

# ------------------------------------------------------------------ 02-ket-qua-bien-the-activation
V1 = json.loads((RES / "g4v_latency_workload.json").read_text())
V2 = json.loads((RES / "g4v_latency_workload_2.json").read_text())
VR = {"silu": SILU, "relu": RELU, "leakyrelu": "ppe5_yolov8n_leakyrelu_100ep_s0", "relu6": "ppe5_yolov8n_relu6_100ep_s0", "relu200": "ppe5_yolov8n_relu_200ep_s0"}
VN = {"leakyrelu": "LeakyReLU (0.1)", "relu6": "ReLU6", "relu200": "ReLU 200 epoch"}
VX = {k: json.loads((RUNS / r / "export_int8.json").read_text()) for k, r in VR.items()}
S200 = json.loads((RUNS / "ppe5_yolov8n_baseline_200ep_s0" / "export_int8.json").read_text())
cv = C["variants"]
c200 = C["silu200_vs_silu100"]
assert all(VX[k]["calibration"]["stems_md5"] == "11d6a5c69414a6eafd8b98f99724b0b2" and VX[k]["calibration"]["png_md5"] == "6652576adb7608ddf8ff326c57851732" for k in ("relu", "leakyrelu", "relu6", "relu200"))
for V in (V1, V2):
    assert all(V["g3"][m]["int8_cpu_ops"] == ["Transpose"] and V["g3"][m]["fp16_cpu_ops"] == ["Transpose"] for m in VR)
    assert all(min(V["gate_a"][m]["coverage_per_session"]) > 0.97 for m in VR if m != "silu") and max(V["gate_a"]["silu"]["coverage_per_session"]) < 0.02
assert V1["g3"]["leakyrelu"]["fused_ops"] == {"ConvLeakyRelu": 51, "ConvLeakyReluAdd": 6} and V1["g3"]["relu6"]["fused_ops"] == {"ConvClip": 57}
assert V1["g3"]["relu200"]["fused_ops"] == {"ConvRelu": 51, "ConvReluAdd": 6}
G1_FULL = {"leakyrelu": False, "relu6": True, "relu200": False}


def vb(V, m):
    return V["gate_b"][m]


def label(k):
    r = cv[k]["css_test|int8"]
    if not r["passes"]:
        return "Loại", "C"
    ok_b = any(vb(V, k)["verdict"] == "nhanh hơn" for V in (V1, V2))
    if not ok_b:
        return "Loại", "B"
    return ("Giữ", "") if G1_FULL[k] else ("Chưa biết", "G1")


rv200 = cv["relu200"]["css_test|int8"]
assert "silu200" in rv200
P = []
w = P.append
lab = {k: label(k) for k in VN}
w("""*******************
Biến thể activation
*******************

.. admonition:: Trang này trả lời

   - LeakyReLU, ReLU6 và ReLU huấn luyện 200 epoch có qua cổng G4 (A phủ đa nhân, B latency, C mAP) khi thay SiLU của YOLOv8n ppe5 không, nhãn của từng biến thể là gì?
   - Huấn luyện dài hơn có lấy lại mAP của ReLU không, và có tách được ảnh hưởng của số epoch khỏi ảnh hưởng của activation không (đối chứng SiLU 200 epoch)?
   - Latency và độ phủ đa nhân của các biến thể so với SiLU và ReLU là bao nhiêu?

.. admonition:: Tóm tắt
""")
w("")
for k, n in VN.items():
    d = cv[k]["css_test|int8"]["diff_vs_silu_pp"]
    w(f"   - {n}: cổng C {'đạt' if cv[k]['css_test|int8']['passes'] else 'không đạt'} (AP50-95 {pm(d['map50_95'])}, AP NoHelmet {pm(d['NoHelmet'])}, AP Vest {pm(d['Vest'])} điểm so với SiLU seed 0). Nhãn: **{lab[k][0]}**" + (f" (bước {lab[k][1]})" if lab[k][1] else "") + ".")
s2 = cv["relu200"]["css_test|int8"]
w(f"   - Huấn luyện 200 epoch đưa ReLU từ {pm(cs['diff_pp']['map50_95'])} xuống {pm(s2['diff_vs_silu_pp']['map50_95'])} điểm AP50-95 so với SiLU 100 epoch. So với đối chứng SiLU 200 epoch, ReLU 200 epoch chênh {pm(s2['diff_vs_silu200_pp']['map50_95'])} điểm. Chính SiLU 200 epoch chênh {pm(c200['css_test|int8']['map50_95'])} điểm so với SiLU 100 epoch. Vì vậy câu đúng là ``ReLU 200 epoch đạt cổng C so với SiLU 100 epoch``, không phải ``đổi activation đạt``.")
w(f"   - Cả ba biến thể nhanh hơn ở ``CORE_0_1_2`` so với ``CORE_0`` khoảng {f(min(vb(V, m)['drop_pct'] for V in (V1, V2) for m in VN), 1)} đến {f(max(vb(V, m)['drop_pct'] for V in (V1, V2) for m in VN), 1)}% (hai thí nghiệm) và độ phủ đa nhân {pct(min(min(V1['gate_a'][m]['coverage_per_session']) for m in VN), 1)} (SiLU {pct(max(V1['gate_a']['silu']['coverage_per_session']), 1)}). Hai lần chạy latency xen kẽ, mỗi mô hình có ít nhất một lần thực hiện đúng giao thức P2.")
w("   - Mọi ứng viên là 1 seed, giao thức P2 đã duyệt ngày 2026-11-01. Độ dốc LeakyReLU 0.1 là một điểm do dự án chọn, không quét. Hardswish, GELU, Mish không thử vì không nằm trong danh sách op đa nhân của T1.")
w("""
Kết quả của ReLU gốc, nhiễu seed và cổng ở :doc:`01-ket-qua-g4`. Đa nhân S1 đến S3 ở :doc:`03-ket-qua-da-nhan`. Mọi số INT8 ở trang này dùng công thức lượng tử hóa mặc định của Ultralytics. Trang :doc:`05-ket-qua-luong-tu-hoa` cho thấy công thức ``h5`` lấy lại gần hết mức rơi INT8 so với FP16, và cổng C dưới ``h5`` nằm ở mục 5 của trang đó.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Ứng viên và điều kiện
========================

Mỗi ứng viên là YOLOv8n ppe5, seed 0, khởi tạo từ trọng số ``yolov8n.pt`` (SiLU) nạp vào kiến trúc mới, cùng cài đặt huấn luyện Ultralytics của baseline, chỉ khác file yaml mô hình và số epoch. INT8 dùng danh sách hiệu chuẩn của seed 0 (``stems_md5`` và ``png_md5`` giống hệt như ở :doc:`01-ket-qua-g4`). Quy tắc viết trước dữ liệu: ``bench/eval_g4/rule_variants.txt`` (mAP), ``bench/onboard_g4v/rule.txt`` (latency, thí nghiệm 1 và 2). Cổng C của mọi ứng viên so với SiLU seed 0 huấn luyện 100 epoch (baseline đã duyệt).

""")
w(table(["Ứng viên", "Activation", "Epoch", "Run", "INT8 sha256 (8 ký tự đầu)"],
        [["SiLU (baseline)", "``SiLU``", 100, f"``{SILU}``", VX["silu"]["rknn_sha256"][:8]]] +
        [["ReLU (:doc:`01-ket-qua-g4`)", "``nn.ReLU()``", 100, f"``{RELU}``", VX["relu"]["rknn_sha256"][:8]]] +
        [[VN[k], {"leakyrelu": "``nn.LeakyReLU(0.1)``", "relu6": "``nn.ReLU6()``", "relu200": "``nn.ReLU()``"}[k], 200 if k == "relu200" else 100, f"``{VR[k]}``", VX[k]["rknn_sha256"][:8]] for k in VN] +
        [["SiLU 200 epoch (đối chứng)", "``SiLU``", 200, "``ppe5_yolov8n_baseline_200ep_s0``", S200["rknn_sha256"][:8]]], [22, 22, 8, 44, 16]))
w("""
Độ dốc 0.1 của LeakyReLU là lựa chọn của dự án, theo quy ước của cấu hình Darknet YOLO, không lấy từ T1 hay T2 (mục T1 của LeakyReLU không có ràng buộc về độ dốc). Không quét độ dốc. Mốc kiểm tra trước khi huấn luyện (``val`` mAP50-95 trong ``metrics.csv`` của hai run 100 epoch, ``val`` mAP50-95 của cả hai còn tăng ròng từ epoch 90 đến 100, có dao động giữa các epoch) là lý do chọn thử 200 epoch. ``metrics.csv`` của ReLU 200 epoch có đủ 200 dòng.

2. G1 theo tên op
=================

Quy tắc ánh xạ (viết trước dữ liệu, giống ReLU): tên op sau khi compiler gộp ánh xạ theo tên sang mục ``ConvolutionXxx`` của Operator List. Tên có ``Add`` (``ConvLeakyReluAdd``, ``ConvReluAdd``) không có mục cùng tên, nên G1 chỉ qua một phần và nhãn tối đa là "Chưa biết" dù A, B, C đạt. Quy tắc này do dự án viết trong ``rule_variants.txt`` trước khi có dữ liệu, không nằm trong chuẩn ở :doc:`../03-tang-npu-don-bay/01-operator-support` mục 2 (chuẩn chỉ nói "Chưa biết" khi chưa chạy hết các bước). Nguồn T1 do doc-reader trích:
""")
w(table(["Việc", "Kết quả", "Nguồn"], [
    ["``ConvolutionPRelu/LeakyRelu`` (3.2.9)", "Có mục: ``Output = LeakyRelu(Conv(Input))``, ``说明及规格限制同Convolution``, ``多核联合: 支持``, không có ràng buộc độ dốc", "[T1 OPL tr.61]"],
    ["``ConvolutionClip`` (3.2.8)", "Có mục: ``Output = Clip(Conv(Input))``, ``多核联合: 支持``. Mục ``Clip/ReLU6`` đứng riêng (3.2.50) ghi phạm vi [0, 6]", "[T1 OPL tr.61, tr.84]"],
    ["Mục gộp ``Add`` với LeakyRelu hoặc Clip", "Không có mục nào trong chương 3.2. Chỉ có ``ConvolutionAdd`` (3.2.10, ``多核联合: 支持``) và ``ConvolutionAddRelu`` (3.2.19)", "[T1 OPL tr.61, tr.63]"],
    ["Op đứng riêng ``Relu``, ``Clip/ReLU6``, ``PRelu``, ``LeakyRelu``", "Cả bốn ghi ``多核联合: 暂不支持`` (tr.84 đến 86), trong khi SDK guide tr.75 và API guide tr.27 liệt kê chúng là op đa nhân. Không nguồn nào giải thích", "[T1 OPL tr.84 đến 86] [T1 UG232 tr.75] [T1 UG152 tr.27]"],
    ["``ConvClip`` trong ví dụ của hãng", "Có trong bảng layer ví dụ của SDK guide (``ConvClip``, INT8)", "[T1 UG232 tr.56 đến 57]"],
    ["Luật gộp cứng của phần cứng", "SDK guide tr.142, cột ``Supported fusion rules``, liệt kê ``Conv+Relu``, ``Conv+PRelu(LeakyRelu)``, ``Conv+Clip``, ``Conv+Add`` và ``Conv+Activation+Add``. Phù hợp với ``ConvReluAdd`` và ``ConvLeakyReluAdd`` quan sát được trong bảng build. Đây là luật gộp, không phải mục Operator List tên ``ConvXxxAdd`` có dòng ``多核联合``, nên không đổi quy tắc ánh xạ G1", "[T1 UG232 tr.142]"],
], [30, 70, 24]))
w(f"""
G1 theo quy tắc ánh xạ: LeakyReLU qua một phần (``ConvLeakyReluAdd`` {V1['g3']['leakyrelu']['fused_ops']['ConvLeakyReluAdd']} dòng không có mục), ReLU6 qua (``ConvClip`` ánh xạ sang ``ConvolutionClip``, không có dòng gộp ``Add``), ReLU 200 epoch qua một phần (cùng kiến trúc ReLU, ``ConvReluAdd``).

3. G3: bảng build
=================

Bảng layer của build INT8 và FP16 đã huấn luyện (kiểm sơ bộ trên trọng số chưa huấn luyện cho cùng tên op trước khi huấn luyện, không phải kết luận):
""")
w(table(["Mô hình", "Op gộp", "Số dòng INT8", "Số dòng FP16", "Op CPU ngoài Input, Output (INT8, FP16)"],
        [[n, ", ".join(f"``{o}`` {c}" for o, c in V1["g3"][m]["fused_ops"].items()), V1["g3"][m]["int8_rows"], V1["g3"][m]["fp16_rows"], f"{V1['g3'][m]['int8_cpu_ops']}, {V1['g3'][m]['fp16_cpu_ops']}"]
         for m, n in (("silu", "SiLU"), ("relu", "ReLU"), ("leakyrelu", "LeakyReLU"), ("relu6", "ReLU6"), ("relu200", "ReLU 200 epoch"))], [18, 40, 12, 12, 30]))
w("""
Kết quả G3: cả ba biến thể qua (chỉ ``Transpose`` ở CPU, như SiLU).

4. Điều kiện A và B: độ phủ đa nhân và latency
==============================================

Quy tắc như ở :doc:`01-ket-qua-g4` (mục 3 và 4), chạy xen kẽ dưới P2: hai mask ``CORE_0`` và ``CORE_0_1_2``, năm mô hình, hai vòng cùng thứ tự, 45 giây nghỉ. Thí nghiệm 1 (``onboard_g4v``) có một phiên SiLU không thực hiện đúng P2 (một mẫu giây có một luồng ``rknn_server`` chưa ở CPU4, ngắt vẫn 100% ở CPU4). Theo quy tắc viết trước, đó là điều kiện để chạy thí nghiệm 2 (``onboard_g4v2``, lặp lại nguyên thiết kế). Thí nghiệm 2 có ba phiên không thực hiện đúng ở các mô hình khác (cùng loại: một mẫu giây có một luồng ngoài CPU4). Ngân sách của giai đoạn là tối đa hai thí nghiệm cho mỗi việc, nên không chạy thêm. Mỗi mô hình có ít nhất một thí nghiệm mà cả hai mask thực hiện đúng, và kết quả B giữa các thí nghiệm hợp lệ không mâu thuẫn. Bảng ghi cả hai.
""")
rows = []
for m, n in (("silu", "SiLU"), ("relu", "ReLU"), ("leakyrelu", "LeakyReLU"), ("relu6", "ReLU6"), ("relu200", "ReLU 200 epoch")):
    for tag, V in (("1", V1), ("2", V2)):
        b = vb(V, m)
        rows.append([n, tag, f(b["core0_ms"], 3), f(b["mask_ms"], 3), f(b["drop_pct"], 2), f(b["gap_ms"], 3), b["verdict"], pct(min(V["gate_a"][m]["coverage_per_session"]), 1)])
w(table(["Mô hình", "Thí nghiệm", "``CORE_0`` (ms)", "``CORE_0_1_2`` (ms)", "Giảm (%)", "Chênh hai phiên lớn nhất (ms)", "Kết quả B", "Độ phủ A"], rows, [18, 10, 14, 16, 10, 20, 24, 12]))
rl, lk, r6, r2 = (V1["vs_silu"]["CORE_0"][m] for m in ("relu", "leakyrelu", "relu6", "relu200"))
w(f"""
Mô tả: ở ``CORE_0`` (thí nghiệm 1) LeakyReLU nhanh hơn SiLU {f(-lk['diff_pct'], 1)}%, ReLU6 {f(-r6['diff_pct'], 1)}%, ReLU {f(-rl['diff_pct'], 1)}%, ReLU 200 epoch {f(-r2['diff_pct'], 1)}%. ReLU 100 epoch và 200 epoch có cùng kiến trúc và cùng latency (chênh {f(abs(r2['ms'] - rl['ms']), 3)} ms), nên số epoch không đổi tốc độ. ReLU6 chậm hơn ReLU khoảng {f(r6['ms'] - rl['ms'], 2)} ms ở ``CORE_0`` (nguyên nhân chưa biết, bảng build ReLU6 có 119 dòng với 8 ``Add`` riêng so với 113 dòng của ReLU).
Điều kiện A đạt cho cả ba biến thể ({pct(min(min(V1['gate_a'][m]['coverage_per_session']) for m in VN), 1)}), điều kiện B đạt cho cả ba ở ít nhất một thí nghiệm hợp lệ.

5. Điều kiện C: mAP
===================

Chấm bằng RKNNLite trên board, ``css_test`` (82 ảnh), INT8 là dtype kết luận. Chênh so với SiLU seed 0 (100 epoch), đơn vị điểm phần trăm. Cổng C đạt khi cả ba cột chênh từ -1.0 trở lên.
""")
rows = []
for k, n in VN.items():
    r = cv[k]["css_test|int8"]
    rows.append([n, " / ".join(f(r["values"][c], 2) for c in ("map50_95", "NoHelmet", "Vest")), " / ".join(pm(r["diff_vs_silu_pp"][c]) for c in ("map50_95", "NoHelmet", "Vest")), "đạt" if r["passes"] else "không đạt"])
rows.append(["ReLU (:doc:`01-ket-qua-g4`)", " / ".join(f(cs["relu"][c], 2) for c in ("map50_95", "NoHelmet", "Vest")), " / ".join(pm(cs["diff_pp"][c]) for c in ("map50_95", "NoHelmet", "Vest")), "không đạt"])
rows.append(["SiLU 200 epoch (đối chứng)", " / ".join(f(rv200["silu200"][c], 2) for c in ("map50_95", "NoHelmet", "Vest")), " / ".join(pm(c200["css_test|int8"][c]) for c in ("map50_95", "NoHelmet", "Vest")), "không áp dụng"])
w(table(["Ứng viên", "AP50-95 / AP NoHelmet / AP Vest", "Chênh so với SiLU seed 0, 100 epoch", "Cổng C"], rows, [26, 34, 40, 14]))
w(f"""
Tham chiếu FP16 (RKNNLite) và mô tả FP32 (PyTorch) của AP50-95 ``css_test``, chênh so với SiLU seed 0 cùng dtype:
""")
w(table(["Ứng viên", "FP16 chênh", "FP32 chênh"],
        [[VN[k], pm(cv[k]["css_test|fp16"]["diff_vs_silu_pp"]["map50_95"]), pm(cv[k]["css_test|fp32"]["diff_vs_silu_pp"]["map50_95"])] for k in VN] +
        [["SiLU 200 epoch", pm(c200["css_test|fp16"]["map50_95"]), pm(c200["css_test|fp32"]["map50_95"])]], [26, 20, 20]))
w(f"""
Về huấn luyện 200 epoch (V-E, mô tả cạnh cổng C): ReLU 200 epoch chênh {pm(s2['diff_vs_silu200_pp']['map50_95'])} điểm AP50-95, {pm(s2['diff_vs_silu200_pp']['NoHelmet'])} điểm AP NoHelmet, {pm(s2['diff_vs_silu200_pp']['Vest'])} điểm AP Vest so với SiLU 200 epoch. SiLU 200 epoch chênh {pm(c200['css_test|int8']['map50_95'])} điểm AP50-95 so với SiLU 100 epoch (INT8). Cổng C của ReLU 200 epoch so với SiLU 100 epoch: {'đạt' if s2['passes'] else 'không đạt'}.

Đọc cùng nhiễu seed: khoảng trải AP50-95 INT8 giữa ba seed SiLU là {f(n8['map50_95']['range'], 2)} điểm và giữa ba seed ReLU là {f(rn['map50_95']['range'], 2)} điểm (:doc:`01-ket-qua-g4` mục 5). Ba ứng viên của trang này chỉ có 1 seed, nên mức chênh nhỏ hơn các khoảng trải đó không đủ để kết luận có khác biệt.

6. Nhãn của từng ứng viên
=========================
""")
w(table(["Ứng viên", "G1", "G2", "G3", "A", "B", "C", "Nhãn"],
        [[VN[k], "qua" if G1_FULL[k] else "qua một phần", "ghi nhận", "qua", "đạt", "đạt" if any(vb(V, k)["verdict"] == "nhanh hơn" for V in (V1, V2)) else "không đạt", "đạt" if cv[k]["css_test|int8"]["passes"] else "không đạt", f"**{lab[k][0]}**"] for k in VN], [24, 16, 10, 8, 8, 8, 12, 14]))
w("""
Ứng viên dừng ở bước đầu tiên không qua. G1 qua một phần chỉ cho nhãn tối đa "Chưa biết" khi A, B, C đều đạt. Tất cả là 1 seed. Nhãn của ReLU gốc ở :doc:`01-ket-qua-g4`. Trang này không đổi nhãn đó.

7. Điều chưa biết
=================
""")
w(table(["Việc", "Trạng thái", "Đã làm gì"], [
    ["Vì sao ReLU6 chậm hơn ReLU ở ``CORE_0``", "chưa biết", "Chỉ mô tả hai bảng build (ReLU6 giữ 8 ``Add`` riêng)"],
    ["Nhiễu seed của LeakyReLU, ReLU6 và ReLU 200 epoch", "chưa biết", "Mỗi cái 1 seed"],
    ["Độ dốc LeakyReLU khác 0.1", "chưa biết", "Một điểm, không quét"],
    ["Hardswish, GELU, Mish", "chưa biết", "Không thử, không nằm trong danh sách op đa nhân của T1"],
    ["Mâu thuẫn Relu, Clip, LeakyRelu đứng riêng giữa Operator List và hai guide", "chưa biết", "Không nguồn T1 nào giải thích"],
    ["Có công thức lượng tử hóa nào đưa mAP INT8 về gần FP16 cho SiLU hoặc biến thể", "đã làm ở trang khác", "Công thức ``h5`` ở :doc:`05-ket-qua-luong-tu-hoa` (chẩn đoán giai đoạn 2c), một seed"],
    ["P2", "đã duyệt ngày 2026-11-01", "Hai thí nghiệm, mỗi lần có phiên bị đánh dấu không thực hiện đúng do một mẫu giây"],
], [40, 22, 50]))
w("""
8. Nguồn
========

- T1: Operator List V2.3.2 (``docs/_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf``, tr.59 đến 61, 63, 84 đến 86), SDK User Guide V2.3.2 (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, tr.56 đến 57, 75, 142), API guide V1.5.2 tr.27.
- T3 PC và board: ``results/g4v_latency_workload.*``, ``results/g4v_latency_workload_2.*``, ``results/eval_g4.*``, ``bench/onboard_g4v/``, ``bench/onboard_g4v2/``, ``bench/eval_g4/rule_variants.txt``, ``export_int8.json`` của các run.
- Tìm nguồn: ``results/phase2b_variants_design.md`` (thiết kế và kết quả tìm nguồn G1 của LeakyReLU và ReLU6, doc-reader).
""")
pages["02-ket-qua-bien-the-activation.rst"] = "\n".join(P)

# ------------------------------------------------------------------ 05-ket-qua-luong-tu-hoa
QD = json.loads((RES / "q2c_diag.json").read_text())
QR = json.loads((RES / "q2c_recipes.json").read_text())
QH = json.loads((RES / "q2h_latency.json").read_text())
qm = QR["models"]
REF = {m: qm[m]["ref"]["css_test"] for m in ("silu", "relu")}
rec = lambda m, rc, st="css_test": qm[m]["recipes"][rc][st]["ap"]  # noqa: E731
assert QD["silu"]["d3"] == QD["relu"]["d3"] == "lớp class mất nhiều hơn lớp box"
assert QH["all_realized"] and QR["r_a"]["silu"]["verdict"] == QR["r_a"]["relu"]["verdict"] == "rebuild equivalent"
assert abs(rec("silu", "c_all")["map50_95"] - REF["silu"]["fp16"]["map50_95"]) <= 1.35
for m in ("silu", "relu"):
    assert rec(m, "h5")["map50_95"] - rec(m, "base")["map50_95"] > 1.35 and rec(m, "h5")["map50"] - rec(m, "base")["map50"] > 1.35
    for rc in ("kl", "h1", "h2", "h3", "h4", "auto"):
        assert abs(rec(m, rc)["map50_95"] - rec(m, "base")["map50_95"]) < 1.35 or (m, rc) == ("silu", "kl")
assert rec("silu", "h6")["map50_95"] < rec("silu", "base")["map50_95"]
assert len(qm["silu"]["recipes"]["h5"]["build"]["float16_layers"]) == 15
assert all(QH["tables"][m]["cpu_ops"] == ["Transpose"] for m in ("silu", "relu"))
P = []
w = P.append
fp = {m: REF[m]["fp16"] for m in REF}
i8 = {m: REF[m]["int8"] for m in REF}
RC = QR["r_c"]


def _ap(run, tag):
    return 100 * json.loads((RUNS / run / "eval" / f"{tag}_css_test.json").read_text())["map50_95"]


DR = {m: [(_ap(f"ppe5_yolov8n_{r}_100ep_s{n}", "pt_fp32") - _ap(f"ppe5_yolov8n_{r}_100ep_s{n}", "rknn_int8"), _ap(f"ppe5_yolov8n_{r}_100ep_s{n}", "rknn_fp16") - _ap(f"ppe5_yolov8n_{r}_100ep_s{n}", "rknn_int8")) for n in (0, 1, 2)]
      for m, r in (("silu", "baseline"), ("relu", "relu"))}
w(f"""**********************
Chẩn đoán lượng tử hóa
**********************

.. admonition:: Trang này trả lời

   - Vì sao model INT8 mất khoảng 12 đến 13 điểm AP50-95 so với FP16 (SiLU và ReLU), và phần nào của mô hình gây mất mát?
   - Công thức lượng tử hóa nào lấy lại điểm (thuật toán ``kl_divergence``, lượng tử hóa lai theo vùng, ``auto_hybrid``), có tốn latency hay mất phủ đa nhân không?
   - Kết luận cổng G4 của ReLU có đổi không khi dùng công thức tốt nhất?

.. admonition:: Tóm tắt

   - Mức rơi INT8 so với FP16 trên ``css_test``: SiLU {f(fp['silu']['map50_95'] - i8['silu']['map50_95'], 2)} điểm AP50-95 và {f(fp['silu']['map50'] - i8['silu']['map50'], 2)} điểm AP50, ReLU {f(fp['relu']['map50_95'] - i8['relu']['map50_95'], 2)} và {f(fp['relu']['map50'] - i8['relu']['map50'], 2)} điểm. Mô hình dựng lại bằng ``build_recipe.py`` cho đúng kết quả của file đã triển khai (chênh {f(QR['r_a']['silu']['diff_pp'], 2)} điểm).
   - Nhánh class, đuôi đầu ra, thuật toán ``kl_divergence`` và ``auto_hybrid`` không lấy lại điểm. Không công thức nào của thí nghiệm 1 làm AP50-95 của SiLU lệch quá {f(max(abs(rec('silu', rc)['map50_95'] - rec('silu', 'base')['map50_95']) for rc in ('kl', 'h1', 'h2', 'h3', 'h4', 'auto')), 2)} điểm so với base, ReLU lệch tối đa {f(max(abs(rec('relu', rc)['map50_95'] - rec('relu', 'base')['map50_95']) for rc in ('kl', 'h1', 'h2', 'h3', 'h4', 'auto')), 2)} điểm (khoảng trải giữa seed là 1.35 và 1.57).
   - Công thức ``h5`` (15 tensor của nhánh giải mã box giữ FP16, phần còn lại INT8) đưa AP50-95 của SiLU từ {f(rec('silu', 'base')['map50_95'], 2)} lên {f(rec('silu', 'h5')['map50_95'], 2)} (FP16: {f(fp['silu']['map50_95'], 2)}) và của ReLU từ {f(rec('relu', 'base')['map50_95'], 2)} lên {f(rec('relu', 'h5')['map50_95'], 2)} (FP16: {f(fp['relu']['map50_95'], 2)}). Phép kiểm tra hợp lệ ``c_all`` (mọi tensor INT8 trừ ngõ vào mạng, 183 tensor, đặt FP16) cho {f(rec('silu', 'c_all')['map50_95'], 2)}.
   - ``h5`` không tốn latency: thay đổi {pm(QH['cost']['silu|CORE_0']['cost_ms'], 3)} ms ở SiLU ``CORE_0`` và {pm(QH['cost']['relu|CORE_0_1_2']['cost_ms'], 3)} ms ở ReLU ``CORE_0_1_2`` (dưới 5%), độ phủ đa nhân của ReLU {pct(min(QH['gate_a']['relu']['coverage_per_session']), 1)}, bảng build không có op CPU mới.
   - Cổng G4 của ReLU không đổi: dưới ``h5`` ReLU vẫn kém SiLU {f(-RC['h5|css_test']['diff_pp']['map50_95'], 2)} điểm AP50-95 và {f(-RC['h5|css_test']['diff_pp']['NoHelmet'], 2)} điểm AP NoHelmet, cổng C không đạt. Khoảng cách này đã có ở FP16.
   - Công thức ``h6`` (``h5`` cộng cả nhánh box ``cv2``) làm AP50-95 của SiLU thấp hơn base {f(-(rec('silu', 'h6')['map50_95'] - rec('silu', 'base')['map50_95']), 2)} điểm, nguyên nhân chưa biết. ``mmse`` không dựng được với 300 ảnh hiệu chuẩn (bị hệ điều hành dừng, mã 137, nghi thiếu bộ nhớ).
   - Một ứng viên mỗi công thức, một seed, giao thức đo latency P2 (đã duyệt ngày 2026-11-01). Bộ chấm đã nâng giới hạn thời gian NMS lên 60 giây mỗi ảnh (kết quả cũ không đổi, đã kiểm trên bốn dump).

Kết quả cổng G4 ở :doc:`01-ket-qua-g4`, biến thể activation ở :doc:`02-ket-qua-bien-the-activation`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Bối cảnh và nguồn
====================

Hai nguồn T1 xác định cách model INT8 hiện được dựng. Mã xuất RKNN của Ultralytics 8.4.154 (``utils/export/rknn.py:74-80``) chỉ đặt ``mean_values``, ``std_values``, ``target_platform``, ``do_quantization``, ``dataset`` và ``rknn_batch_size``, nên mọi tham số lượng tử hóa khác dùng mặc định của toolkit: ``quantized_dtype`` ``w8a8``, ``quantized_algorithm`` ``normal``, ``quantized_method`` ``channel``, ``optimization_level`` 3 [T1 API232 tr.7 đến 8]. Tọa độ box được chia cho kích thước ảnh trước khi lượng tử hóa, với lý do ghi trong mã: "Normalize coordinates by input size so RKNN's per-tensor INT8 scale preserves class scores" (``engine/exporter.py:1101``). Toolkit có sẵn phân tích sai số từng lớp (``accuracy_analysis``, cosine ở API232 tr.22 và Euclidean ở UG232 tr.8), lượng tử hóa lai thủ công (``hybrid_quantization_step1`` và ``step2``, API232 tr.20 đến 21, tên tensor float16 trong ``custom_quantize_layers``, UG232 tr.124) và tự động (``auto_hybrid``, API232 tr.14).

Mốc từ T2, chỉ để định vị, không so trực tiếp vì khác bộ dữ liệu và bộ lượng tử hóa: bài Q-YOLO báo YOLOv5s, YOLOv5m, YOLOv7 và YOLOv7x ở W8A8 trên COCO val2017 giảm AP từ 0.0 đến 0.5 điểm so với bản FP32 (MinMax 37.2, Percentile 36.9, Q-YOLO 37.4 so với 37.4 của YOLOv5s) [T2 Q-YOLO tr.8 Table 1]. Ngược chiều, với YOLOv6s mang RepVGG: "YOLOv6s-RepVGG suffers a huge quantization degradation for about 7.4% mAP via PTQ" [T2 QARepVGG tr.7] (COCO). Hai bài báo nêu rằng Swish dễ gặp vấn đề hoặc lợi ích của nó có thể mất khi lượng tử hóa: "Swish-like activations are known to have quantization collapse ..." [T2 QARepVGG tr.10] và "Although newer activations like Swish functions provide accuracy improvement in floating-point, these may vanish after quantization ..." [T2 Nagel 2021 tr.7]. Trong các bài đã đọc (Q-YOLO, QARepVGG, Nagel 2021, YOLOv6, ActNAS) không bài nào đo SiLU, ReLU6 hay hard-swish lên mAP YOLO sau PTQ INT8 bằng số. Số liệu của dự án (``css_test``, AP50-95, điểm): mức rơi từ FP32 xuống INT8 của SiLU seed 0, 1, 2 là {', '.join(f(x[0], 2) for x in DR['silu'])} và của ReLU seed 0, 1, 2 là {', '.join(f(x[0], 2) for x in DR['relu'])}, từ FP16 xuống INT8 là {', '.join(f(x[1], 2) for x in DR['silu'])} (SiLU) và {', '.join(f(x[1], 2) for x in DR['relu'])} (ReLU). Chênh giữa hai activation nằm trong nhiễu seed, không có xu hướng rõ.

Danh sách nguồn đầy đủ: ``results/phase2c_source_facts.md``. Quy tắc viết trước dữ liệu: ``bench/onboard_q2c/rule_diag.txt``, ``rule_recipes.txt`` (có phần thí nghiệm 2), ``bench/onboard_q2h/rule.txt``.

2. Dựng lại và đối chứng
========================

``ai/automation/diagnose_quant.py`` dựng INT8 đúng như đường xuất của Ultralytics (ONNX có chia tọa độ, cấu hình mặc định, danh sách hiệu chuẩn của seed 0) và giữ ONNX đó, ``build_recipe.py`` dựng lại từ ONNX này với từng công thức. Công thức ``base`` (mặc định) cho AP50-95 trên ``css_test`` chênh {f(QR['r_a']['silu']['diff_pp'], 2)} điểm (SiLU) và {f(QR['r_a']['relu']['diff_pp'], 2)} điểm (ReLU) so với file đã triển khai. File dựng lại có cùng kích thước nhưng sha256 khác file gốc, nên mọi công thức được đọc so với ``base`` dựng lại.

3. Chẩn đoán từng lớp (mô phỏng, 10 ảnh)
========================================

``accuracy_analysis`` trên bộ mô phỏng của toolkit (không dùng board), 5 ảnh trong danh sách hiệu chuẩn và 5 ảnh ``css_test``, so tensor của mỗi lớp với đồ thị float. Cosine của một lớp càng thấp thì sai số của riêng lớp đó càng lớn. Bảng ghi 5 dòng thấp nhất (trung bình 10 ảnh).
""")
rows = []
for m, n in (("silu", "SiLU"), ("relu", "ReLU")):
    for x in QD[m]["lowest_single"][:5]:
        rows.append([n, f"``{x['op']}``", f"``{x['name']}``", f(x["mean_single_cos"], 5)])
w(table(["Model", "Op", "Tensor", "Cosine một lớp (trung bình)"], rows, [10, 14, 62, 20]))
c25, c001 = QD["silu"]["mean_counts"]["t0.25"], QD["silu"]["mean_counts"]["t0.001"]
r25, r001 = QD["relu"]["mean_counts"]["t0.25"], QD["relu"]["mean_counts"]["t0.001"]
w(f"""
Ở tensor ``output0`` (1 x 9 x 8400), so đồ thị float với mô phỏng: cosine trên các kênh class là {f(QD['silu']['mean_class_cos'], 4)} (SiLU) và {f(QD['relu']['mean_class_cos'], 4)} (ReLU), trên các kênh box là {f(QD['silu']['mean_box_cos'], 4)} và {f(QD['relu']['mean_box_cos'], 4)}. Ở ngưỡng tin cậy 0.001 của bộ chấm, mô phỏng làm mất {f(c001['missed'], 1)} trên {f(c001['golden_above'], 1)} anchor mỗi ảnh (SiLU) và {f(r001['missed'], 1)} trên {f(r001['golden_above'], 1)} (ReLU), còn ở ngưỡng 0.25 chỉ mất {f(c25['missed'], 1)} trên {f(c25['golden_above'], 1)} và {f(r25['missed'], 1)} trên {f(r25['golden_above'], 1)}. Theo quy tắc viết trước, ở cả hai model các kênh class mất nhiều cosine hơn các kênh box ({QD['silu']['d3']}). Đây là sai số so với đồ thị float, không phải mAP, và cosine cao trên tensor đầu ra không loại trừ sai lệch tọa độ vài pixel (mục 5).

4. Công thức và kết quả mAP
===========================

Mọi công thức dựng từ cùng ONNX và cùng danh sách hiệu chuẩn, chấm bằng RKNNLite trên board (``css_test``, 82 ảnh). Công thức: ``kl`` là ``quantized_algorithm`` ``kl_divergence``, ``h1`` giữ FP16 ba Conv cuối của nhánh class, ``h2`` giữ FP16 cả nhánh class, ``h3`` giữ FP16 đuôi đầu ra (5 tensor ``Concat_1``, ``Sigmoid``, ``output0``), ``h4`` là ``h2`` cộng ``h3``, ``auto`` là ``auto_hybrid`` mặc định. Thí nghiệm 2 (thêm sau khi thấy dữ liệu thí nghiệm 1, theo ngân sách hai thí nghiệm cho việc này) gồm ``h5`` (đuôi giải mã box), ``h6`` (``h5`` cộng nhánh box ``cv2``) và ``c_all`` (kiểm tra hợp lệ), chỉ chạy SiLU, ``h5`` rồi chạy tiếp ReLU theo quy tắc.
""")
rows = []
for m, n in (("silu", "SiLU"), ("relu", "ReLU")):
    rows.append([n, "INT8 đã triển khai", f(i8[m]["map50_95"], 2), f(i8[m]["map50"], 2), f(i8[m]["NoHelmet"], 2), f(i8[m]["Vest"], 2), "-"])
    rows.append([n, "FP16 (tham chiếu)", f(fp[m]["map50_95"], 2), f(fp[m]["map50"], 2), f(fp[m]["NoHelmet"], 2), f(fp[m]["Vest"], 2), "-"])
    for rc in ("base", "kl", "h1", "h2", "h3", "h4", "h5", "h6", "c_all", "auto"):
        if rec(m, rc):
            v = rec(m, rc)
            ka = qm[m]["recipes"][rc]["css_test"]["kept_anchors"]
            rows.append([n, f"``{rc}``", f(v["map50_95"], 2), f(v["map50"], 2), f(v["NoHelmet"], 2), f(v["Vest"], 2), ka])
w(table(["Model", "Công thức", "AP50-95", "AP50", "AP NoHelmet", "AP Vest", "Anchor giữ lại (``css_test``)"], rows, [8, 20, 10, 10, 12, 10, 18]))
rb = QR["r_b"]
w(f"""
Đọc bảng (số, không nêu nguyên nhân): ở SiLU, ``kl`` {pm(rb['silu|kl']['diff_vs_base']['map50_95'])}, ``h1`` {pm(rb['silu|h1']['diff_vs_base']['map50_95'])}, ``h2`` {pm(rb['silu|h2']['diff_vs_base']['map50_95'])}, ``h3`` {pm(rb['silu|h3']['diff_vs_base']['map50_95'])}, ``h4`` {pm(rb['silu|h4']['diff_vs_base']['map50_95'])}, ``auto`` {pm(rb['silu|auto']['diff_vs_base']['map50_95'])} điểm AP50-95 so với ``base``, đều nằm trong khoảng trải giữa seed của SiLU (1.35 điểm) ở cột AP50-95 (các cột phụ của ``kl`` lệch hơn: AP NoHelmet {pm(rb['silu|kl']['diff_vs_base']['NoHelmet'])}, AP Vest {pm(rb['silu|kl']['diff_vs_base']['Vest'])}), không công thức nào lấy lại điểm. ``h5`` cộng {pm(rb['silu|h5']['diff_vs_base']['map50_95'])} điểm (lấy lại {pct(rb['silu|h5']['recovered_fraction'], 0)} khoảng cách tới FP16) và ``c_all`` cộng {pm(rb['silu|c_all']['diff_vs_base']['map50_95'])} điểm. ``h6`` đổi {pm(rb['silu|h6']['diff_vs_base']['map50_95'])} điểm. Ở ReLU, ``h5`` cộng {pm(rb['relu|h5']['diff_vs_base']['map50_95'])} điểm, các công thức còn lại từ {pm(min(rb[f'relu|{rc}']['diff_vs_base']['map50_95'] for rc in ('kl', 'h1', 'h2', 'h3', 'h4', 'auto')))} đến {pm(max(rb[f'relu|{rc}']['diff_vs_base']['map50_95'] for rc in ('kl', 'h1', 'h2', 'h3', 'h4', 'auto')))} điểm. Số anchor giữ lại ở ``h3``, ``h4`` và ``c_all`` khác hẳn ``base`` (``h3`` giữ lại 688800 anchor, đúng 82 x 8400, tức mọi anchor qua ngưỡng 0.001). Nguyên nhân của các mức khác nhau này chưa biết. ``h3`` chấm lần đầu bị giới hạn thời gian NMS của Ultralytics cắt (179 cảnh báo), chấm lại bằng giới hạn 60 giây mỗi ảnh cho cùng kết quả ({f(rec('silu', 'h3')['map50_95'], 2)}).

Quy tắc viết trước của thí nghiệm 2: ``c_all`` hợp lệ khi lệch FP16 không quá khoảng trải seed của SiLU (1.35 điểm), thực tế lệch {f(abs(rec('silu', 'c_all')['map50_95'] - fp['silu']['map50_95']), 2)} điểm nên quy trình dựng lai, siêu dữ liệu và dump hợp lệ để so sánh. Một công thức "lấy lại điểm" khi cả AP50-95 và AP50 cao hơn ``base`` quá 1.35 điểm: chỉ ``h5`` đạt ở cả hai model (``c_all`` cũng đạt ở SiLU, nó là phép kiểm hợp lệ và không chạy ở ReLU).

5. Công thức h5
===============

``h5`` giữ FP16 đúng 15 tensor: bốn tensor của ``dfl``, hai ``Slice``, ``Sub``, ``Add_1``, ``Sub_1``, ``Add_2``, ``Div_1``, ``Concat_2``, phép chia ``Div`` về tọa độ chuẩn hóa, ``output0-rs`` và ``output0_int8``. Phần còn lại, gồm toàn bộ backbone, neck, nhánh class và nhánh box trước phép giải mã, vẫn INT8. Số học từ cấu hình lượng tử hóa bước 1 (không phải số đo mAP): tensor ``output0`` INT8 có bước khoảng 0.0041 trên khoảng [0, 1.05], tương ứng khoảng 2.6 pixel trên ảnh 640, và các tensor giải mã tọa độ có bước từ 0.058 đến 0.63 đơn vị (``Slice`` 0.058, ``Sub_1`` 0.116, ``Div_1`` 0.313, ``Sub`` 0.350, ``Add_2`` 0.626). ``h5`` lấy lại điểm, nhưng phần nào của đuôi giải mã gây mất điểm thì chưa tách được: ``h5`` đổi cùng lúc DFL, các phép Slice, Sub, Add, Div, Concat và ``output0``, chưa đo sai số tọa độ box riêng, AP50 cũng rơi khoảng 10 đến 11 điểm nên mất mát không chỉ ở định vị, và ``h6`` (thêm nhánh box ``cv2`` ở FP16) lại làm tệ hơn. Nguyên nhân chưa biết.
""")
rows = []
for m, n in (("silu", "SiLU"), ("relu", "ReLU")):
    for rc in ("base", "h5"):
        v = rec(m, rc)
        rows.append([n, f"``{rc}``", f(v["map50_95"], 2), f(v["map50"], 2), f(v["precision"], 3), f(v["recall"], 3), f(v["NoHelmet"], 2), f(v["Vest"], 2)])
    rows.append([n, "FP16", f(fp[m]["map50_95"], 2), f(fp[m]["map50"], 2), "-", "-", f(fp[m]["NoHelmet"], 2), f(fp[m]["Vest"], 2)])
w(table(["Model", "Công thức", "AP50-95", "AP50", "Precision", "Recall", "AP NoHelmet", "AP Vest"], rows, [8, 14, 10, 10, 12, 10, 14, 10]))
w(f"""
Cổng C dưới công thức (R-c, ghi nhãn riêng, không đổi nhãn G4 đã duyệt): ReLU trừ SiLU cùng công thức, ``css_test``, AP50-95 / AP NoHelmet / AP Vest.
""")
w(table(["Công thức", "Chênh (điểm)", "Cổng C"],
        [[f"``{rc}``", " / ".join(pm(RC[f"{rc}|css_test"]["diff_pp"][c]) for c in ("map50_95", "NoHelmet", "Vest")), "đạt" if RC[f"{rc}|css_test"]["passes"] else "không đạt"] for rc in ("base", "h5")], [16, 40, 14]))
VH = QR["variants_h5"]
assert VH["relu200"]["css_test"]["passes"] and not VH["leakyrelu"]["css_test"]["passes"] and not VH["relu6"]["css_test"]["passes"]
w(f"""
Dưới ``h5`` ReLU vẫn trượt cổng C ({pm(RC['h5|css_test']['diff_pp']['map50_95'])} điểm AP50-95, {pm(RC['h5|css_test']['diff_pp']['NoHelmet'])} điểm AP NoHelmet). Khoảng cách này đã có ở FP16 ({f(fp['relu']['map50_95'] - fp['silu']['map50_95'], 2)} điểm AP50-95), nên phần chênh này không do lượng tử hóa (một seed, nhiễu seed 1.35 đến 1.57 điểm). Trên ``ppe2286_ext`` (mô tả) chênh dưới ``h5`` là {pm(RC['h5|ppe2286_ext']['diff_pp']['map50_95'])} điểm AP50-95.

Cổng C dưới ``h5`` cho các biến thể activation (thêm theo quy tắc ADDENDUM 3 của ``rule_recipes.txt`` viết trước dữ liệu): mỗi ứng viên dựng lại bằng ``h5`` từ ONNX chuẩn hóa của chính nó, chấm trên board, so với SiLU seed 0 (100 epoch) cũng dưới ``h5``. Không đổi nhãn G4 đã duyệt (nhãn đó tính với INT8 mặc định, xem :doc:`02-ket-qua-bien-the-activation`).
""")
rows = []
for k, n in (("relu200", "ReLU 200 epoch"), ("leakyrelu", "LeakyReLU (0.1)"), ("relu6", "ReLU6")):
    r = VH[k]["css_test"]
    rows.append([n, " / ".join(f(r["ap"][c], 2) for c in ("map50_95", "NoHelmet", "Vest")), " / ".join(pm(r["diff_vs_silu_h5"][c]) for c in ("map50_95", "NoHelmet", "Vest")), "đạt" if r["passes"] else "không đạt"])
r = VH["silu200"]["css_test"]
rows.append(["SiLU 200 epoch (đối chứng)", " / ".join(f(r["ap"][c], 2) for c in ("map50_95", "NoHelmet", "Vest")), " / ".join(pm(r["diff_vs_silu_h5"][c]) for c in ("map50_95", "NoHelmet", "Vest")), "không áp dụng"])
w(table(["Ứng viên dưới ``h5``", "AP50-95 / AP NoHelmet / AP Vest", "Chênh so với SiLU 100 epoch dưới ``h5``", "Cổng C"], rows, [26, 34, 40, 14]))
w(f"""
ReLU 200 epoch đạt cổng C dưới ``h5`` so với SiLU 100 epoch ({pm(VH['relu200']['css_test']['diff_vs_silu_h5']['map50_95'])} điểm AP50-95), LeakyReLU và ReLU6 không đạt. Đối chứng SiLU 200 epoch dưới ``h5`` đạt AP50-95 {f(VH['silu200']['css_test']['ap']['map50_95'], 2)}, cao hơn ReLU 200 epoch {f(-VH['relu200']['css_test']['diff_vs_silu200_h5']['map50_95'], 2)} điểm AP50-95 và {f(-VH['relu200']['css_test']['diff_vs_silu200_h5']['NoHelmet'], 2)} điểm AP NoHelmet. Vì vậy câu đúng là ``ReLU 200 epoch đạt cổng C so với SiLU 100 epoch dưới h5``, không phải ``đổi activation đạt``. Nhãn của ReLU 200 epoch nếu dùng ``h5`` vẫn là "Chưa biết" theo quy tắc ánh xạ G1 (``ConvReluAdd`` không có mục T1), các điều kiện A ({pct(min(QH['gate_a']['relu']['coverage_per_session']), 1)} với ReLU ``h5``) và B ({f(QH['gate_b']['relu|h5']['drop_pct'], 1)}%) đạt, nhưng hai số này đo trên ReLU 100 epoch seed 0 (cùng kiến trúc), chưa đo trực tiếp ReLU 200 epoch dưới ``h5``.

6. Chi phí latency và đa nhân của h5
====================================

Một lần chạy xen kẽ 16 phiên dưới P2 (``bench/onboard_q2h``): SiLU và ReLU, INT8 đã triển khai và ``h5``, ``CORE_0`` và ``CORE_0_1_2``, hai vòng cùng thứ tự. Cả 16 phiên thực hiện đúng P2 theo tiêu chí viết trước. Chi phí là trung vị của hai trung vị phiên của ``h5`` trừ giá trị tương ứng của INT8 đã triển khai. Ở cả bốn điều kiện chênh lệch lớn hơn chênh hai phiên lớn nhất nhưng dưới 5%.
""")
rows = []
for m, n in (("silu", "SiLU"), ("relu", "ReLU")):
    for k in ("CORE_0", "CORE_0_1_2"):
        c = QH["cost"][f"{m}|{k}"]
        rows.append([n, f"``{k}``", f(c["base_ms"], 3), f(c["h5_ms"], 3), pm(c["cost_ms"], 3), pm(c["cost_pct"], 2), f(c["gap_ms"], 3), "có" if c["material"] else "không"])
w(table(["Model", "Mask", "INT8 (ms)", "h5 (ms)", "Chi phí (ms)", "Chi phí (%)", "Chênh hai phiên lớn nhất (ms)", "Từ 5%"], rows, [8, 14, 12, 12, 14, 12, 24, 8]))
tb = QH["tables"]
w(f"""
Ở cả hai model ``h5`` thấp hơn INT8 đã triển khai {f(min(-QH['cost'][k]['cost_ms'] for k in QH['cost']), 3)} đến {f(max(-QH['cost'][k]['cost_ms'] for k in QH['cost']), 3)} ms, không đạt mức 5% nên không đáng kể. Nguyên nhân của chênh lệch nhỏ này chưa biết. Điều kiện B của ReLU ``h5``: ``CORE_0_1_2`` nhanh hơn ``CORE_0`` {f(QH['gate_b']['relu|h5']['drop_pct'], 1)}% (INT8 đã triển khai: {f(QH['gate_b']['relu|base']['drop_pct'], 1)}%), SiLU ``h5`` {f(QH['gate_b']['silu|h5']['drop_pct'], 1)}%. Điều kiện A của ``h5``: ReLU {pct(min(QH['gate_a']['relu']['coverage_per_session']), 1)}, SiLU {pct(max(QH['gate_a']['silu']['coverage_per_session']), 1)}. Bảng build ``h5`` có {tb['silu']['rows']} dòng ở SiLU và {tb['relu']['rows']} dòng ở ReLU, gồm {tb['silu']['counts'].get('NPU|FLOAT16', 0)} dòng NPU ở FLOAT16, và op CPU ngoài ``InputOperator`` và ``OutputOperator`` chỉ có ``Transpose`` (như INT8 đã triển khai).

7. Điều chưa biết và giới hạn
=============================

""")
w(table(["Việc", "Trạng thái", "Đã làm gì"], [
    ["Vì sao giữ FP16 nhánh giải mã box lấy lại điểm (độ chính xác tọa độ, hay tương tác khác)", "chưa biết", "``h5`` lấy lại gần hết khoảng cách FP16, ``h3`` và ``h4`` (đuôi class FP16) không. Chưa đo sai số tọa độ box riêng"],
    ["Vì sao ``h6`` (``h5`` cộng nhánh box ``cv2`` FP16) làm tệ hơn base", "chưa biết (tái lập 2026-11-01)", "Dựng lần hai cho file khác byte (dựng không tất định) nhưng cùng AP50-95 và AP50 trên ``css_test``, tức mức giảm tái lập qua hai lần dựng. Nguyên nhân vẫn chưa biết (:doc:`08-so-muc-chua-biet` mục 8)"],
    ["``mmse``", "không dựng được ở đây", "Một lần dựng thử trên SiLU với 300 ảnh bị hệ điều hành dừng (mã 137 sau 401 giây, máy 15.6 GB, nghi thiếu bộ nhớ, log gốc không giữ trong repo). Không giảm số ảnh vì danh sách hiệu chuẩn phải giữ nguyên"],
    ["QAT và kiến trúc thân thiện lượng tử hóa", "đã làm ở :doc:`07-ket-qua-qat-kien-truc`", "Người dùng duyệt ngày 2026-10-31. Kết quả A1 tách đầu, B QAT và A2 bỏ DFL ở :doc:`07-ket-qua-qat-kien-truc` (một seed mỗi ứng viên, chỉ SiLU). Khoảng cách ReLU kém SiLU còn lại có ở FP16 nên lượng tử hóa không sửa được. Mỗi cái là phần bổ sung, không đổi nhãn G4"],
    ["Công thức ``h5`` với seed khác, model khác, tập ảnh khác", "chưa biết", "Một seed mỗi model, 82 ảnh ``css_test``, ``ppe2286_ext`` chỉ mô tả"],
    ["Latency ``h5`` ngoài P2", "chưa biết", "P2 đã được người dùng duyệt ngày 2026-11-01, số ngoài P2 chỉ có một phiên"],
    ["Triển khai ``h5`` trong ``ai/automation/export_npu.py``", "đã làm (cập nhật sau trang này)", "Nhãn ``int8h5`` song song với ``int8`` mặc định, xem :doc:`06-quy-trinh-tai-lap`. ``pipeline.py`` chưa nối"],
], [44, 20, 60]))
w("""
Thay đổi bộ chấm: ``ai/core/evaluator.py`` truyền ``max_time_img=60`` cho NMS (``MAX_TIME_IMG``), vì các công thức giữ FP16 đuôi class cho hàng nghìn hộp trên ngưỡng 0.001 mỗi ảnh và giới hạn mặc định của Ultralytics (2 giây cộng 0.05 giây mỗi ảnh) cắt NMS sớm. Kết quả cũ không đổi: chấm lại bốn dump (INT8 ``css_test`` và ``ppe2286_ext``, FP16 ``css_test`` và ``ppe2286_ext``) của seed 0 cho số liệu y hệt.

8. Nguồn
========

- T1: API Reference Toolkit2 V2.3.2 (``3rdparty/rknn-toolkit2/doc/03_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf``, tr.6 đến 10, 14, 20 đến 22), SDK User Guide V2.3.2 (tr.8, 120, 124), mã Ultralytics 8.4.154 (``utils/export/rknn.py``, ``engine/exporter.py:1101``).
- T2: ``docs/_assets/pdf/papers/02_quantization/qyolo_ptq_2023wang.pdf`` (tr.8 Table 1), ``docs/_assets/pdf/papers/08_npu_friendly_arch/qarepvgg_quant_2024chu.pdf`` (tr.10), ``docs/_assets/pdf/papers/02_quantization/quant_whitepaper_2021nagel.pdf`` (tr.7).
- T3: ``results/q2c_diag.*``, ``results/q2c_recipes.*``, ``results/q2h_latency.*``, ``bench/onboard_q2c/`` (gồm ``step1_silu.quantization.cfg``, cấu hình lượng tử hóa bước 1 của SiLU nơi đọc các bước 0.0041 và 0.31 đến 0.63), ``bench/onboard_q2h/``, ``ai/automation/diagnose_quant.py``, ``build_recipe.py``, ``analyze_q2c_diag.py``, ``analyze_q2c_recipes.py``, ``analyze_q2h.py``.
- Tìm nguồn: ``results/phase2c_source_facts.md``.
""")
pages["05-ket-qua-luong-tu-hoa.rst"] = "\n".join(P)

# ------------------------------------------------------------------ 06-quy-trinh-tai-lap
IH = json.loads((RES / "int8h5.json").read_text())
QI = json.loads((RES / "q2i_latency.json").read_text())
ihr = IH["runs"]
assert IH["v1"]["verdict"] == "export reproduces h5" and IH["v2"]["unchanged"] and QI["all_realized"]
assert all(v["export"]["n_float16"] == 15 and v["export"]["stems_md5"] == "11d6a5c69414a6eafd8b98f99724b0b2" for v in ihr.values())
H5N = 15  # tensors kept float16 by recipe h5, asserted against export_int8h5.json above and in ai/core/rknn/hybrid.py
P = []
w = P.append
w(f"""************
Chuẩn int8h5
************

.. admonition:: Trang này trả lời

   - Chuẩn INT8 mới ``int8h5`` là gì, xuất và kiểm chứng thế nào, và nó khác ``int8`` mặc định ở đâu?
   - Lệnh nào tái lập từng kết quả của giai đoạn 2 và dữ liệu, mã phân tích nằm ở đâu?
   - Điều kiện thiết bị, quyết định đã chốt và điều chưa làm là gì?

.. admonition:: Tóm tắt

   - ``int8h5`` là INT8 mặc định của Ultralytics với đúng {H5N} tensor của nhánh giải mã box giữ FP16 (công thức ``h5`` ở :doc:`05-ket-qua-luong-tu-hoa`). Nhãn ``PREC=int8h5``, thư mục ``weights/rknn_int8h5/``, tệp ``export_int8h5.json``. ``int8`` mặc định và mọi kết quả của nó không đổi (sha256 của file seed 0 trước và sau khi xuất giống nhau).
   - Xuất bằng ``make export-npu PREC=int8h5`` cho đúng danh sách tensor và AP50-95 của bản dựng thử ``h5`` (chênh {f(IH['v1']['ap_diff_pp'], 2)} điểm trên ``css_test``). File xuất có sha256 khác bản dựng thử, nên latency được đo lại.
   - ``css_test`` AP50-95 của ``int8h5``: SiLU seed 0, 1, 2 là {', '.join(f(ihr[f'silu_s{n}']['sets']['css_test']['int8h5']['map50_95'], 2) for n in (0, 1, 2))} (FP16: {', '.join(f(ihr[f'silu_s{n}']['sets']['css_test']['fp16']['map50_95'], 2) for n in (0, 1, 2))}, ``int8``: {', '.join(f(ihr[f'silu_s{n}']['sets']['css_test']['int8']['map50_95'], 2) for n in (0, 1, 2))}), ReLU seed 0 là {f(ihr['relu_s0']['sets']['css_test']['int8h5']['map50_95'], 2)} (FP16 {f(ihr['relu_s0']['sets']['css_test']['fp16']['map50_95'], 2)}).
   - Latency của ``int8h5`` so với ``int8`` (P2, một lần chạy xen kẽ): SiLU ``CORE_0`` {pm(QI['cost']['silu|CORE_0']['cost_ms'], 3)} ms, ReLU ``CORE_0_1_2`` {pm(QI['cost']['relu|CORE_0_1_2']['cost_ms'], 3)} ms, độ phủ đa nhân của ReLU {pct(min(QI['gate_a']['relu|int8h5']['coverage_per_session']), 1)}.
   - ``int8h5`` đã nối vào ``ai/automation/pipeline.py``, ``tables.py`` (Bảng F) và ``make benchmark-npu`` và ``bench-board`` (2026-11-01). Mọi số là 1 seed mỗi model, latency chính thức dưới P2 (đã duyệt, :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`).

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Quyết định đã chốt
=====================

Các quyết định của người dùng trong giai đoạn 2 (ngày 2026-10-31), ghi lại vì không nằm ở trang kết quả nào khác:
""")
w(table(["Quyết định", "Nội dung", "Nơi áp dụng"], [
    ["Giao thức latency", "P2 dùng cho điều kiện B của G4 và S1, ngưỡng 5% giữ nguyên. P2 và P3 được người dùng duyệt nguyên trạng ngày 2026-11-01 (:doc:`/contents/09-tien-do/02-quyet-dinh/02-duyet-giao-thuc-p2-p3`)", ":doc:`01-ket-qua-g4`, :doc:`03-ket-qua-da-nhan`"],
    ["Seed và mAP", "ReLU seed 0 so baseline seed 0, nhãn 1 seed. mAP chấm bằng RKNNLite trên board (INT8 kết luận, FP16 tham chiếu, FP32 mô tả). Sau đó mở rộng: thêm ReLU seed 1, 2 để mô tả nhiễu", ":doc:`01-ket-qua-g4`"],
    ["Biến thể activation", "Làm đủ LeakyReLU, ReLU6, ReLU 200 epoch kèm đối chứng SiLU 200 epoch (Hardswish, GELU, Mish không thử vì không nằm trong danh sách op đa nhân của T1)", ":doc:`02-ket-qua-bien-the-activation`"],
    ["Chẩn đoán lượng tử hóa", "Làm tuần tự: tài liệu, chẩn đoán từng lớp, công thức, rồi QAT và kiến trúc thân thiện lượng tử hóa (người dùng duyệt ngày 2026-10-31 và đã chạy)", ":doc:`05-ket-qua-luong-tu-hoa`, :doc:`07-ket-qua-qat-kien-truc`"],
    ["Chuẩn INT8", "``int8h5`` là nhãn mới song song với ``int8`` (không thay thế)", "mục 2 trang này"],
    ["Quản lý repo", "Không commit, không push. ``tmp/`` giữ nguyên (bị ``.gitignore``), trọng số ``weights/rknn_*`` cũng bị ``.gitignore`` và chỉ có sha256 trong ``export_*.json``", "toàn bộ"],
], [20, 90, 34]))
w(f"""
Nguồn của bảng: các quyết định này được ghi từ hội thoại với người dùng, không có tệp quyết định riêng ngoài các quy tắc ``rule*.txt`` viết trước dữ liệu (xác nhận từng phép đo, P2 và P3 viết khi chưa duyệt và được duyệt ngày 2026-11-01) và ``results/phase2b_variants_design.md``. Sổ theo dõi ở ``tmp/`` bị ``.gitignore``.

2. Chuẩn int8h5
===============

``int8h5`` dùng cùng ONNX có tọa độ box chuẩn hóa mà bộ xuất Ultralytics đưa cho toolkit (xem ``baseline.py`` và ``hybrid.py``), cùng cấu hình (mean 0, std 255, mặc định của toolkit) và cùng danh sách hiệu chuẩn như ``int8`` (``--calib-from`` danh sách của seed 0, ``stems_md5`` ``{ihr['silu_s0']['export']['stems_md5']}``, ``png_md5`` ``{ihr['silu_s0']['export']['png_md5']}``). Khác biệt duy nhất là {H5N} tensor giữ FP16 qua ``hybrid_quantization_step1`` và ``step2`` (API V2.3.2 tr.20 đến 21, tên tensor trong ``custom_quantize_layers``, UG V2.3.2 tr.124): bốn tensor ``dfl/Reshape_output_0``, ``dfl/Transpose_output_0_sw``, ``dfl/Softmax_output_0_sw``, ``dfl/Reshape_1_output_0_rs``, rồi ``Slice_output_0-rs``, ``Slice_1_output_0-rs``, ``Sub_output_0-rs``, ``Add_1_output_0-rs``, ``Sub_1_output_0-rs``, ``Add_2_output_0-rs``, ``Div_1_output_0-rs``, ``Concat_2_output_0-rs``, ``/Div_output_0-rs``, ``output0-rs``, ``output0_int8``. Mã dùng chung ở ``ai/core/rknn/hybrid.py`` (có ``assert`` đúng 15 tensor), ``ai/core/rknn/baseline.py`` và ``ai/automation/export_npu.py`` (cờ ``--recipe h5``). ``build_recipe.py`` (công thức chẩn đoán ``h1`` đến ``h6`` và ``c_all``) dùng cùng mã công thức. ``diagnose_quant.py`` chỉ dựng INT8 mặc định và chạy ``accuracy_analysis``, không dùng ``hybrid.py``.

Lệnh chuẩn (``CALIB_FROM`` mặc định là ``ppe5_yolov8n_baseline_100ep_s0``):
""")
w(table(["Việc", "Lệnh"], [
    ["Xuất", "``make export-npu RUN=<run> PREC=int8h5``"],
    ["Chấm mAP trên board", "``make evaluate RUN=<run> BACKEND=rknn PREC=int8h5 BOARD=<ssh>``"],
    ["Đo latency tầng 1", "``make benchmark-npu RUN=<run> PREC=int8h5 CORE_MASK=<mask>`` (chưa chạy thử qua Make, ``benchmark_npu.py --precision int8h5`` đã chạy trực tiếp trong ``onboard_q2i``)"],
    ["Đo trên board tầng 2", "``make bench-board RUN=<run> PREC=int8h5`` (chưa chạy thử)"],
], [24, 100]))
w(f"""
Kiểm chứng (quy tắc viết trước ``bench/onboard_q2c/rule_int8h5.txt``): V-1, bản xuất chuẩn có cùng {IH['runs']['silu_s0']['export']['n_float16']} tensor FP16 với bản dựng thử và AP50-95 ``css_test`` chênh {f(IH['v1']['ap_diff_pp'], 2)} điểm (giới hạn 0.5 điểm là số mới chưa duyệt), kết quả: {IH['v1']['verdict']}. V-2, sha256 của ``weights/rknn_int8`` seed 0 (so với hằng số viết trong quy tắc trước khi xuất, tệp có thời điểm sửa 2026-10-30) trước và sau khi xuất {'giống nhau' if IH['v2']['unchanged'] else 'khác nhau'}. V-3 (mô tả, ``css_test``, điểm):
""")
rows = []
for k, n in (("silu_s0", "SiLU seed 0"), ("silu_s1", "SiLU seed 1"), ("silu_s2", "SiLU seed 2"), ("relu_s0", "ReLU seed 0")):
    c = ihr[k]["sets"]["css_test"]
    rows.append([n, f(c["int8"]["map50_95"], 2), f(c["int8h5"]["map50_95"], 2), f(c["fp16"]["map50_95"], 2), pm(c["diff_vs_int8"]["map50_95"]), pm(c["diff_vs_fp16"]["map50_95"]), pm(c["diff_vs_fp16"]["NoHelmet"]), pm(c["diff_vs_fp16"]["Vest"])])
w(table(["Run", "int8", "int8h5", "FP16", "int8h5 trừ int8", "int8h5 trừ FP16", "AP NoHelmet: int8h5 trừ FP16", "AP Vest: int8h5 trừ FP16"], rows, [14, 10, 10, 10, 16, 16, 24, 22]))
rg = IH["v3_range"]
w(f"""
Khoảng trải AP50-95 giữa ba seed SiLU: ``int8h5`` {f(rg['int8h5']['map50_95'], 2)} điểm, ``int8`` {f(rg['int8']['map50_95'], 2)}, FP16 {f(rg['fp16']['map50_95'], 2)}. Ở AP NoHelmet khoảng trải của ``int8h5`` ({f(rg['int8h5']['NoHelmet'], 2)} điểm) lớn hơn của FP16 ({f(rg['fp16']['NoHelmet'], 2)}), ở AP Vest ({f(rg['int8h5']['Vest'], 2)}) gần FP16 ({f(rg['fp16']['Vest'], 2)}). Ba seed chưa đủ để nói chênh ở AP NoHelmet là nhiễu hay khác biệt.

3. Latency và đa nhân của int8h5
================================

Một lần chạy xen kẽ 16 phiên dưới P2 (``bench/onboard_q2i``, quy tắc viết trước ``bench/onboard_q2i/rule.txt``): SiLU và ReLU seed 0, ``int8`` và ``int8h5``, ``CORE_0`` và ``CORE_0_1_2``, hai vòng cùng thứ tự. Cả 16 phiên thực hiện đúng P2. Vì đo lại file xuất chuẩn nên số này thay cho số của bản dựng thử ở :doc:`05-ket-qua-luong-tu-hoa`, hai số cùng cỡ.
""")
rows = []
for m, n in (("silu", "SiLU"), ("relu", "ReLU")):
    for k in ("CORE_0", "CORE_0_1_2"):
        c = QI["cost"][f"{m}|{k}"]
        rows.append([n, f"``{k}``", f(c["int8_ms"], 3), f(c["int8h5_ms"], 3), pm(c["cost_ms"], 3), pm(c["cost_pct"], 2), f(c["gap_ms"], 3), "có" if c["material"] else "không"])
w(table(["Model", "Mask", "int8 (ms)", "int8h5 (ms)", "Chi phí (ms)", "Chi phí (%)", "Chênh hai phiên lớn nhất (ms)", "Từ 5%"], rows, [8, 14, 12, 14, 14, 12, 24, 8]))
w(f"""
Điều kiện B: ReLU ``int8h5`` {f(QI['gate_b']['relu|int8h5']['drop_pct'], 1)}% (``int8``: {f(QI['gate_b']['relu|int8']['drop_pct'], 1)}%), SiLU ``int8h5`` {f(QI['gate_b']['silu|int8h5']['drop_pct'], 1)}%. Điều kiện A: ReLU ``int8h5`` {pct(min(QI['gate_a']['relu|int8h5']['coverage_per_session']), 1)}, SiLU {pct(max(QI['gate_a']['silu|int8h5']['coverage_per_session']), 1)}. Bảng layer dùng để kiểm tổng cycles của ``int8h5`` là bảng của bản dựng thử ``h5`` cùng đồ thị (log xuất của ``int8h5`` được ghi khi ``RKNN`` chạy ở chế độ không in bảng, đã sửa trong ``hybrid.py`` cho các lần xuất sau). Op CPU ngoài ``InputOperator`` và ``OutputOperator``: {QI['tables']['silu|int8h5']['cpu_ops']}.

4. Tái lập từng kết quả
=======================
""")
w(table(["Kết quả", "Chạy", "Dữ liệu và quy tắc", "Phân tích", "Trang"], [
    ["Nhiễu seed, cổng C", "``make evaluate RUN=<run> BACKEND=rknn PREC=int8`` (SiLU seed 0, 1, 2 và ReLU)", "``bench/eval_g4/rule*.txt``, ``eval/``", "``analyze_g4c.py``", "10, 12"],
    ["Cổng A, B (G4), S1", "``bench/onboard_g4b/g4b_driver.py`` (cần helper P2)", "``bench/onboard_g4b/``", "``analyze_g4.py``", "10, 11"],
    ["Latency biến thể", "``bench/onboard_g4v*/g4v_driver.py`` (thí nghiệm 1, 2)", "``bench/onboard_g4v/``, ``onboard_g4v2/``", "``analyze_g4v.py [--sub onboard_g4v2]``", "12"],
    ["Throughput S2, S3", "``bench/onboard_thr/thr_driver.py`` (cần helper P3)", "``bench/onboard_thr/``", "``analyze_thr.py``", "11"],
    ["Chẩn đoán từng lớp", "``diagnose_quant.py <run> --images calib:<dir> test:<dir> --n 5 --out <dir>``", "``bench/onboard_q2c/diag/``, ``rule_diag.txt``", "``analyze_q2c_diag.py``", "13"],
    ["Công thức lượng tử hóa", "``build_recipe.py <run> <recipe>``, rồi ``evaluate.py --variant <recipe>``", "``bench/onboard_q2c/``, ``rule_recipes.txt``", "``analyze_q2c_recipes.py``", "13"],
    ["Chi phí ``h5``", "``bench/onboard_q2h/q2h_driver.py``, ``bench/onboard_q2i/q2i_driver.py``", "``bench/onboard_q2h/``, ``onboard_q2i/``", "``analyze_q2h.py``, ``analyze_q2i.py``", "13, 14"],
    ["Chuẩn ``int8h5``", "``make export-npu PREC=int8h5``, ``make evaluate PREC=int8h5``", "``bench/onboard_q2c/rule_int8h5.txt``", "``analyze_int8h5.py``", "14"],
    ["Mọi trang sinh", "``.venv/bin/python docs/tools/gen_phase2_results_pages.py``", "``results/*.json``", "(có ``assert`` mỗi số)", "10 đến 14"],
], [24, 60, 36, 28, 8]))
w("""
5. Điều kiện thiết bị và công cụ
================================

- **Helper trên board.** ``ai/board/lock_freq.sh`` (khóa tần số), ``bench/onboard_x4/x4_hold.sh`` (giao thức P2) và ``bench/onboard_thr/p3_hold.sh`` (giao thức P3) trong thư mục chạy của seed 0 được cài thành bản root-owned ở ``/usr/local/sbin`` kèm một tệp ``/etc/sudoers.d/rk3588-measure`` cho phép chạy đúng ba script này không cần mật khẩu. Bản trong repo là nguồn: sửa xong phải cài lại bằng ``sudo install -o root -g root -m 755 <file> /usr/local/sbin/`` trong một terminal có tty. Helper ghi trạng thái vào ``~/x4`` hoặc ``~/p3`` (script tự tạo thư mục, xóa sau khi đo là việc làm tay), và khôi phục affinity ngắt, ``irqbalance`` rồi đọc lại khi kết thúc.
- **Một việc board mỗi lần.** Chấm mAP trên board không chạy cùng lúc với phép đo thời gian.
- **Bộ chấm.** ``ai/core/evaluator.py`` truyền ``max_time_img=60`` cho NMS. Giá trị cũ của Ultralytics (2 giây cộng 0.05 giây mỗi ảnh) cắt NMS khi hàng nghìn hộp qua ngưỡng 0.001. Kết quả cũ không đổi (chấm lại bốn dump).
- **Hiệu chuẩn.** Mọi export INT8 của seed 1, 2, ReLU và các biến thể dùng ``--calib-from ppe5_yolov8n_baseline_100ep_s0`` (seed 0 là nguồn, tự lấy mẫu với ``seed`` 0 và 20 ảnh mỗi class, md5 danh sách tính lại cho cùng giá trị). ``make export-npu PREC=int8h5`` đặt ``--calib-from`` mặc định, ``PREC=int8`` không truyền cờ này. Sampler ``ai/core/rknn/calibration.py`` đã sửa (``sorted``), có ``tests/test_calibration.py``, nhưng export cũ của seed 0 không bị sửa. Export cũ của seed 1 giữ tên ``rknn_int8_ownlist``. Từ 2026-11-01 ``make export-npu PREC=int8 CALIB_FROM=<run>`` truyền ``--calib-from`` (không có ``CALIB_FROM`` thì lấy mẫu mới như trước) và ``pipeline.py`` truyền ``CALIB_FROM`` cho cả ``int8`` và ``int8h5``.
- **Bộ nhớ.** ``mmse`` với 300 ảnh bị hệ điều hành dừng (máy 15.6 GB). Dựng thử ``kl`` chạy dưới ``systemd-run --user --scope -p MemoryMax=9G`` (``rule_recipes.txt``), các lần dựng công thức sau đó dưới ``MemoryMax=11G``.
- **ONNX FP32 của run.** Mỗi lần chạy ``export_npu.py`` (kể cả ``int8h5``) xuất lại ``weights/best.onnx``. Xuất ONNX không tất định theo byte: hai lần xuất cùng trọng số seed 0 cho hai sha256 khác nhau, cùng 233 nút và cùng histogram op. Vì vậy ``onnx_sha256`` ghi trong ``export_int8.json`` cũ khác sha hiện tại của ``best.onnx`` ở cả bốn run, và khớp với ``export_int8h5.json`` mới. Không mã nào trong repo so ``onnx_sha256`` (``tables.py`` chỉ kiểm ``rknn_sha256``). Bảng H dùng ONNX này cho cột CPU của board, đồ thị không đổi.
- **Kiểm sau khi chuyển mã.** Sau khi chuyển logic công thức sang ``hybrid.py`` và bật ``verbose``, ``build_hybrid`` được dựng thử trực tiếp (không ghi đè file đã đo) cho 15 tên tensor và in bảng layer. Các file ``int8h5`` và ``rknn_int8_h5`` đã đo được dựng trước thay đổi đó. Log xuất ``int8h5`` của seed 0 (chạy trực tiếp ``export_npu.py``) không được giữ, log của seed 1, 2 và ReLU nằm trong ``runs/<run>/logs/``.
- **Bằng chứng ngoài git.** Trọng số ``.rknn`` và ``tmp/`` không vào git. Mỗi mô hình có ``export_*.json`` (sha256, danh sách hiệu chuẩn, tensor FP16). Cấu hình lượng tử hóa bước 1 ở ``bench/onboard_q2c/step1_silu.quantization.cfg`` và ``step1_relu.quantization.cfg``, log quét thử của các công thức ở ``bench/onboard_q2c/logs/``.

6. Điều chưa làm
================

- Đã làm 2026-11-01: ``pipeline.py`` có bước ``int8h5`` cho phase3 và phase4 (model không có DFL, ví dụ ``nodfl``, bỏ qua vì công thức ``h5`` cần 4 tensor DFL). ``tables.py`` sửa ba lỗi sẵn có để ``make tables DATASET=ppe5`` chạy được: danh sách ``CLASSES`` cũ lệch tên class ppe5 (nay đọc từ yaml dataset), thư mục nhãn của tập ``ppe2286_ext`` (nay theo tên split) và run 200 epoch ghi đè run 100 epoch cùng seed trong cùng một hàng model (nay là hàng riêng ``_200ep``). Hàng ``INT8H5`` của Bảng F khớp số đã biết (trung bình ba seed của SiLU 50.38 AP50-95 trên ``css_test``). ``make benchmark-npu PREC=int8h5`` và ``make bench-board PREC=int8h5`` đã chạy một lần trên board (không dưới P2).
- Đã sửa 2026-11-01: ``MODELS`` của ``pipeline.py`` có ``yolov8s_baseline`` nhưng thư mục ``configs`` không có ``ppe5_yolov8s_baseline.yaml``, nên ``phase2`` và ``phase4`` lỗi ``FileNotFoundError``. Nay ``models_for(ds)`` chỉ lấy model có config, ``phase2``, ``phase3`` và ``phase4`` dựng được danh sách bước cho ppe5.
- Latency của ``int8h5`` với seed khác chưa đo. Ngoài P2 có một phiên ``make benchmark-npu`` ``CORE_0`` (20.513 ms, trung vị 5 lần, một phiên, không chạy helper P2, chỉ để kiểm đường Make. Trang :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3` dùng nó làm ví dụ cỡ số, không phải kết luận).
- Nguyên nhân giữ FP16 nhánh giải mã box lấy lại điểm vẫn chưa biết (:doc:`05-ket-qua-luong-tu-hoa` mục 7).
- QAT và kiến trúc thân thiện lượng tử hóa đã chạy một seed ở :doc:`07-ket-qua-qat-kien-truc`. Còn chưa làm: A2 tách đầu, QAT với torch 1.10 đến 1.13.1, thời gian NPU của bản QAT.
- Mã mới chưa được commit. ``tests`` mới: ``test_calibration``, ``test_throughput_rep``.
""")
pages["06-quy-trinh-tai-lap.rst"] = "\n".join(P)

for name, text in pages.items():
    (OUTDIR / name).write_text(text + "\n", encoding="utf-8")
    print(f"wrote {name} ({len(text.splitlines())} lines)")
