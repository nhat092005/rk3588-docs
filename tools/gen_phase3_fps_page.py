#!/usr/bin/env python3
"""Sinh trang 04-tang-npu-ket-qua/09-ket-qua-don-bay-fps.rst (đòn bẩy FPS cho mục tiêu 60 FPS: E1 int8h5 so với int8, E2 model tách đầu với giải mã chồng lấp, E3) từ kết quả đo.

Đọc results/q2f_fps.json (tạo bởi ai/automation/analyze_q2f.py) và ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_q2f_{thr,split}/.
Chạy từ gốc repo chính:  .venv/bin/python docs/tools/gen_phase3_fps_page.py
Lời văn nằm trong script, mọi con số lấy từ file JSON. Các assert bảo vệ những số có trong lời văn.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
RUN = REPO / "ai" / "automation" / "runs" / "ppe5_yolov8n_baseline_100ep_s0"
OUT = REPO / "docs" / "contents" / "03-phuong-phap" / "04-tang-npu-ket-qua" / "09-ket-qua-don-bay-fps.rst"

Q = json.loads((RES / "q2f_fps.json").read_text())
E1, E2 = Q["e1"], Q["e2"]
GATE = json.loads((RUN / "bench" / "onboard_q2f_split" / "split_gate.json").read_text())
P2J = json.loads((RES / "q2j_split.json").read_text())


def f(x, d=1):
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


# ---- asserts on the facts the prose states
assert E1["all_realized"] and E2["all_realized"]
c1, c2 = E1["conditions"], E2["conditions"]
assert all(v["realized"] for v in list(c1.values()) + list(c2.values()))
assert all(v["verdict"] == "không phân biệt được" for v in E1["comparisons"].values())
assert [round(c1[f"int8|{c}"]["fps"], 2) for c in ("T1", "T3", "T4", "T5")] == [54.69, 56.17, 101.9, 141.13]
assert [round(c1[f"int8h5|{c}"]["fps"], 2) for c in ("T1", "T3", "T4", "T5")] == [54.86, 56.3, 101.89, 142.09]
assert not c1["int8h5|T1"]["meets_60"] and not c1["int8h5|T3"]["meets_60"] and c1["int8h5|T4"]["meets_60"] and c1["int8h5|T5"]["meets_60"]
assert GATE["images"] == 20 and GATE["f1"] >= 0.85 and GATE["n_standard"] == 136 and GATE["n_split"] == 140 and GATE["matched"] == 135
assert [round(c2[k]["fps"], 2) for k in "ABCDEF"] == [54.79, 42.05, 65.99, 65.74, 68.21, 56.62]
assert [c2[k]["meets_60"] for k in "ABCDEF"] == [False, False, True, True, True, False]
cmp2 = E2["comparisons"]
assert [cmp2[k]["verdict"] for k in ("B_vs_A", "C_vs_A", "C_vs_B", "D_vs_C", "E_vs_C", "F_vs_A")] == ["khác", "khác", "khác", "không phân biệt được", "không phân biệt được", "không phân biệt được"]
assert E2["e3_triggered"] is False
assert all(c2[k]["e2e_p50"] is not None and c2[k]["e2e_p50"] > 1000 / 60 for k in "CDEF") and c2["A"]["e2e_p50"] is None
assert round(P2J["decode"]["median_ms"], 2) == 8.02 and round(P2J["total"]["CORE_0"]["split_npu_ms"], 2) == 13.07
acc = P2J["accuracy"]["css_test"]
assert abs(c2['A']['fps'] - c1['int8h5|T1']['fps']) / c1['int8h5|T1']['fps'] < 0.005
assert acc["split"]["map50_95"] == 49.84 and acc["int8h5"]["map50_95"] == 49.66

P = []
w = P.append
w("""***********
Đòn bẩy FPS
***********

.. admonition:: Trang này trả lời

   - Model INT8 chuẩn (``int8h5``) có khác INT8 mặc định về thông lượng không, khi mục tiêu là 60 FPS?
   - Một context của model tách đầu (``A1``) với giải mã CPU chồng lấp cùng NPU có đạt 60 FPS về thông lượng không, và đổi lại điều gì?
   - Có cần giải mã bằng C hoặc NEON không?

.. admonition:: Tóm tắt
""")
w(f"""
   - E1: ``int8h5`` và ``int8`` không phân biệt được về thông lượng theo quy tắc 5% ở cả bốn cấu hình (một context ``CORE_0`` {f(c1['int8h5|T1']['fps'], 2)} so với {f(c1['int8|T1']['fps'], 2)} FPS, ba context {f(c1['int8h5|T5']['fps'], 2)} so với {f(c1['int8|T5']['fps'], 2)} FPS). Một context chưa đạt 60 FPS ở cả hai model, hai context ({f(c1['int8h5|T4']['fps'], 2)} FPS) và ba context đạt.
   - E2: model tách đầu một context ``CORE_0`` với giải mã chồng lấp bằng pipeline (điều kiện C) đạt {f(c2['C']['fps'], 2)} FPS, so với {f(c2['A']['fps'], 2)} FPS của ``int8h5`` một context chạy tuần tự và {f(c2['B']['fps'], 2)} FPS của chính model tách đầu khi giải mã nằm trong cùng luồng (điều kiện B). Thêm một luồng giải mã (D, {f(c2['D']['fps'], 2)} FPS) hay dùng ba lõi cho một context (E, {f(c2['E']['fps'], 2)} FPS) không phân biệt được với C.
   - Độ chính xác của model tách đầu đã chấm ở :doc:`07-ket-qua-qat-kien-truc` ({f(acc['split']['map50_95'], 2)} AP50-95 của ``A1`` so với {f(acc['int8h5']['map50_95'], 2)} của ``int8h5`` trên ``css_test``). Pipeline chỉ đổi cách xếp luồng, và cổng đúng đắn của E2 trên 20 ảnh qua (F1 {f(GATE['f1'], 3)}, ngưỡng 0.85).
   - Pipeline tăng thông lượng chứ không giảm thời gian mỗi khung: thời gian đầu cuối đo được ở các điều kiện pipeline đều lớn hơn 16.67 ms nhiều lần (xem mục 5). Theo cách đọc "mỗi khung xong trong 16.67 ms", không điều kiện nào đạt.
   - E3 (giải mã bằng C hoặc NEON) không chạy: điều kiện kích hoạt viết trước (C dưới 60 FPS và giai đoạn post chậm hơn NPU) không xảy ra. Điều này chỉ có nghĩa theo cách đọc thông lượng của mục tiêu.
   - Một seed, một board, ảnh cache, không camera, giao thức P3 (đã duyệt), các số ngưỡng mới của hai thí nghiệm chưa duyệt.
""")
w("""
Tiêu chí của mục tiêu 60 FPS và hai cách đọc ở :doc:`03-ket-qua-da-nhan` mục 8. Quy tắc viết trước dữ liệu: ``bench/onboard_q2f_thr/rule.txt`` (E1) và ``bench/onboard_q2f_split/rule.txt`` (E2) trong thư mục run ``ppe5_yolov8n_baseline_100ep_s0``.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Câu hỏi, giao thức và nguồn
==============================

Cả hai thí nghiệm chạy ``ai/board/bench_throughput_rep.py`` dưới taskset ``-c 4-7`` với helper P3 (``p3_hold.sh``, giao thức đã duyệt ngày 2026-11-01, hạn chế ở :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3` mục 6), 1238 khung, nghỉ 20 giây giữa các lần chạy, ba lần lặp theo cùng thứ tự, ảnh test ``ppe5`` đã decode sẵn trong bộ nhớ (không camera, không giải mã video, không vẽ hay lưu kết quả). FPS là số khung chia cho thời gian tường, đã tính tiền xử lý, NPU và hậu xử lý (kể cả giải mã box của model tách đầu). Mỗi con số là trung vị của ba lần chạy, chênh lệch tối đa là khoảng trải. Một lần chạy chỉ được tính khi thực hiện đúng P3 (ngắt NPU đúng lõi, tiến trình trong CPU4 đến CPU7, tần số khóa, ``irqbalance`` dừng). Cả hai thí nghiệm đều có mọi lần chạy thực hiện đúng.

Quy tắc "khác" viết trước dữ liệu: chênh ít nhất 5% và lớn hơn khoảng trải lớn hơn của hai điều kiện, nếu không thì "không phân biệt được". Đây là quy tắc của M12 (trường ``rule`` của ``results/thr_p3.json``, kết quả ở :doc:`03-ket-qua-da-nhan`), dùng lại cho các so sánh mới của trang này (các so sánh mới chưa duyệt).

2. E1: int8h5 so với int8
=========================

``int8h5`` là INT8 chuẩn (:doc:`05-ket-qua-luong-tu-hoa`) nhưng mục 8 của :doc:`03-ket-qua-da-nhan` đo bằng ``int8`` mặc định. E1 đo lại cả hai trong cùng một phiên.
""")
rows = []
for c, lab in (("T1", "1 context ``CORE_0``"), ("T3", "1 context ``CORE_0_1_2``"), ("T4", "2 context ``CORE_0`` và ``CORE_1``"), ("T5", "3 context (S2)")):
    a, b = c1[f"int8|{c}"], c1[f"int8h5|{c}"]
    cm = E1["comparisons"][c]
    rows.append([lab, f"{f(a['fps'], 2)} ({f(a['spread'], 2)})", f"{f(b['fps'], 2)} ({f(b['spread'], 2)})", f"{cm['diff_pct']:+.2f}%", cm["verdict"], "đạt" if b["meets_60"] else "chưa đạt"])
w(table(["Cấu hình", "``int8`` FPS (khoảng trải)", "``int8h5`` FPS (khoảng trải)", "Chênh", "Kết luận", "``int8h5`` so với 60 FPS"], rows, [28, 22, 22, 10, 22, 22]))
w(f"""

Chênh chỉ từ {min(abs(v['diff_pct']) for v in E1['comparisons'].values()):.2f}% đến {max(abs(v['diff_pct']) for v in E1['comparisons'].values()):.2f}%, dưới ngưỡng 5% của quy tắc (ở ba cấu hình chênh FPS còn lớn hơn khoảng trải nhưng vẫn dưới 5%), nên theo quy tắc là không phân biệt được và số của :doc:`03-ket-qua-da-nhan` mục 8 áp dụng cho ``int8h5`` ở mức đo này. Phần đã biết về latency NPU của ``int8h5`` ở :doc:`05-ket-qua-luong-tu-hoa` mục 6 phù hợp: cùng cỡ.

Ghi chú về mã đo: E1 chạy với harness trước khi thêm hỗ trợ model tách đầu, mã được đồng bộ lên board sau khi E1 xong nên E2 chạy với harness mới. Điều kiện A của E2 (``int8h5``, một context ``CORE_0``, tuần tự) và ``int8h5`` T1 của E1 đo cùng một việc trên hai bản harness: {f(c2['A']['fps'], 2)} và {f(c1['int8h5|T1']['fps'], 2)} FPS, chênh {abs(c2['A']['fps'] - c1['int8h5|T1']['fps']) / c1['int8h5|T1']['fps'] * 100:.2f}%, nên đổi harness không làm đổi đường chuẩn. Các bản ghi chỉ đánh dấu ``git_dirty``, không phân biệt được hai bản.

3. Cổng đúng đắn của E2
=======================

Model tách đầu trả hai đầu ra thô, CPU giải mã bằng numpy rồi mới chạy hậu xử lý chung. Trước khi đọc thời gian, ``ai/board/split_gate.py`` so các phát hiện (ngưỡng 0.25) của hai model trên {GATE['images']} ảnh test qua cùng đường harness: {GATE['n_standard']} phát hiện của ``int8h5``, {GATE['n_split']} của model tách đầu, {GATE['matched']} cặp khớp (cùng lớp, IoU ít nhất 0.5), F1 bằng {f(GATE['f1'], 3)}. Ngưỡng viết trước là 0.85 (số mới, chưa duyệt), nên cổng qua.

4. E2: giải mã chồng lấp với NPU
================================

Model tách đầu có phần NPU nhanh hơn (13.07 ms ở ``CORE_0`` dưới P2, :doc:`07-ket-qua-qat-kien-truc` mục 2) nhưng giải mã numpy tốn {f(P2J['decode']['median_ms'], 2)} ms trên CPU. Nếu giải mã nằm trong cùng luồng thì tổng dài hơn ``int8h5``. E2 hỏi: nếu giải mã chạy ở luồng khác trong khi NPU xử lý khung kế tiếp thì thông lượng ra sao. Sáu điều kiện (số luồng tiền xử lý và hậu xử lý trong ngoặc):
""")
LAB = {"A": "A: ``int8h5``, tuần tự, ``CORE_0``", "B": "B: tách đầu, giải mã cùng luồng, ``CORE_0``", "C": "C: tách đầu, pipeline (1 pre, 1 post), ``CORE_0``",
       "D": "D: tách đầu, pipeline (1 pre, 2 post), ``CORE_0``", "E": "E: tách đầu, pipeline (1 pre, 1 post), ``CORE_0_1_2``", "F": "F: ``int8h5``, pipeline (1 pre, 1 post), ``CORE_0``"}
rows = []
for k in "ABCDEF":
    v = c2[k]
    rows.append([LAB[k], f"{f(v['fps'], 2)} ({f(v['spread'], 2)})", "đạt" if v["meets_60"] else "chưa đạt", f"{f(v['t_pre'], 2)} / {f(v['t_npu'], 2)} / {f(v['t_post'], 2)}", f"{f(v['cpu_pct'], 0)}%"])
w(table(["Điều kiện", "FPS (khoảng trải)", "So với 60 FPS", "T_pre / T_npu / T_post (ms, trung vị)", "CPU tiến trình"], rows, [44, 20, 16, 34, 14]))
w("""

So sánh theo quy tắc "khác":
""")
NAMES = {"B_vs_A": "B so với A (giải mã cùng luồng so với ``int8h5``)", "C_vs_A": "C so với A (pipeline tách đầu so với ``int8h5`` tuần tự)", "C_vs_B": "C so với B (chồng lấp so với cùng luồng)",
         "D_vs_C": "D so với C (thêm một luồng post)", "E_vs_C": "E so với C (một context trên ba lõi)", "F_vs_A": "F so với A (pipeline so với tuần tự, cùng ``int8h5``)"}
rows = [[NAMES[k], f"{cmp2[k]['diff_fps']:+.2f}", f"{cmp2[k]['diff_pct']:+.1f}%", f(cmp2[k]["larger_spread"], 2), cmp2[k]["verdict"]] for k in NAMES]
w(table(["So sánh", "Chênh FPS", "Chênh %", "Khoảng trải lớn hơn", "Kết luận"], rows, [52, 14, 12, 20, 24]))
w(f"""

Đọc: chồng lấp tăng thông lượng của model tách đầu {cmp2['C_vs_B']['diff_pct']:+.1f}% so với giải mã cùng luồng và đưa nó lên {f(c2['C']['fps'], 2)} FPS, hơn ``int8h5`` tuần tự {cmp2['C_vs_A']['diff_pct']:+.1f}%. Một luồng giải mã đủ (D không khác C, thời gian post {f(c2['C']['t_post'], 2)} ms nhỏ hơn thời gian NPU {f(c2['C']['t_npu'], 2)} ms). Dùng ba lõi cho một context (E) không phân biệt được với C ({cmp2['E_vs_C']['diff_pct']:+.1f}%, dưới 5%). Pipeline một mình không giúp ``int8h5`` ({cmp2['F_vs_A']['diff_pct']:+.1f}%, không phân biệt được), phép đo không nói vì sao. Đây là mô tả của phép đo, không phải cơ chế.

5. Hai cách đọc mục tiêu 60 FPS
===============================

**Đọc theo thông lượng** (mặc định của :doc:`03-ket-qua-da-nhan` mục 8): các điều kiện C ({f(c2['C']['fps'], 2)}), D ({f(c2['D']['fps'], 2)}) và E ({f(c2['E']['fps'], 2)} FPS) đạt, nên một context của model tách đầu với giải mã chồng lấp đạt 60 FPS, không cần nhiều context. ``int8h5`` một context (A, F) chưa đạt, nó cần hai context (:doc:`03-ket-qua-da-nhan`). Thứ tự đầu ra: ở C mỗi giai đoạn chỉ một luồng nối bằng hàng đợi FIFO nên thứ tự được giữ theo cách xây dựng, harness không kiểm điều này (chưa kiểm), còn D có hai luồng post nên có thể đảo thứ tự.

**Đọc theo thời gian mỗi khung** (mỗi khung phải xong trong 16.67 ms): không điều kiện nào đạt. Trường ``e2e_latency_ms`` của harness cho trung vị {f(c2['C']['e2e_p50'], 1)} ms ở C và {f(c2['F']['e2e_p50'], 1)} ms ở F. Theo mã, harness có hàng đợi 6 chỗ (``bench_throughput_rep.py``, ``--queue-size`` mặc định 6) và đẩy khung liên tục, nên hai số này có khả năng gồm thời gian chờ hàng đợi (mức đầy của hàng đợi không đo). Chúng không phải thời gian của một khung riêng lẻ. Tổng ba giai đoạn của C là {f(c2['C']['stage_sum'], 1)} ms (tổng trung vị từng giai đoạn dưới tranh chấp, không phải đo đầu cuối trực tiếp và không phải cực tiểu), cũng lớn hơn 16.67 ms. Đo thời gian mỗi khung với cấp khung theo nhịp 60 FPS: chưa làm.

6. E3: giải mã bằng C hoặc NEON
===============================

Điều kiện kích hoạt viết trước: E3 chỉ chạy nếu điều kiện C dưới 60 FPS và trung vị ``t_post_ms`` của C không nhỏ hơn trung vị ``t_npu_ms``. C đạt {f(c2['C']['fps'], 2)} FPS và ``t_post`` ({f(c2['C']['t_post'], 2)} ms) nhỏ hơn ``t_npu`` ({f(c2['C']['t_npu'], 2)} ms), nên E3 không chạy. Kết quả ghi nhận: không cần theo cách đọc thông lượng của mục tiêu 60 FPS ở cấu hình này (theo cách đọc thời gian mỗi khung chưa xét). Giải mã C hoặc NEON vẫn có thể hữu ích nếu cần giảm CPU hoặc nâng FPS vượt mức này: chưa đo. Trong các tài liệu T1 đã tìm không có chữ NEON (:doc:`../03-tang-npu-don-bay/09-pre-post-processing`).

7. Điều chưa biết và giới hạn
=============================

- Thời gian mỗi khung khi cấp khung theo nhịp 60 FPS và thứ tự đầu ra của pipeline: chưa đo.
- Camera thật, giải mã video, vẽ và lưu kết quả không nằm trong đo. Thông lượng thực của ứng dụng có thể thấp hơn.
- Model tách đầu chưa được nối vào các script demo của repo, E2 dùng harness đo. Chi phí tích hợp và CPU thêm ({f(c2['C']['cpu_pct'], 0)}% so với {f(c2['A']['cpu_pct'], 0)}% của A) cần xem khi triển khai.
- Độ chính xác của đường tách đầu trên ảnh đã chấm ở :doc:`07-ket-qua-qat-kien-truc` (một seed). Cổng E2 chỉ so các phát hiện trên 20 ảnh.
- Một board, một seed, P3 không so được với số P2 của :doc:`07-ket-qua-qat-kien-truc`. Ngưỡng F1 0.85 và quy tắc "khác" cho các so sánh mới chưa duyệt.
- Đòn bẩy chưa đo: tách đầu với nhiều context, giải mã bằng C hoặc NEON, RGA cho tiền xử lý, ``int8h5`` kết hợp bộ nhớ SRAM.

8. Tái lập
==========

.. code-block:: bash

   # E1 và E2: board đã khóa tần số, p3_hold.sh chạy bằng sudo -n, model đã rsync lên board
   .venv/bin/python ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_q2f_thr/q2f_thr_driver.py
   # cổng E2 (chạy trên board)
   .venv-board/bin/python -m ai.board.split_gate --standard <rknn_int8h5> --split <rknn_int8_split> --images data/ppe5/processed/images/test --out <json>
   .venv/bin/python ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_q2f_split/q2f_split_driver.py
   .venv/bin/python -m ai.automation.analyze_q2f
   .venv/bin/python docs/tools/gen_phase3_fps_page.py

Số liệu: ``results/q2f_fps.json``. Mã: ``ai/board/bench_throughput_rep.py`` (hỗ trợ model tách đầu qua ``postprocess_raw`` của ``ai/board/common.py``), ``ai/board/split_gate.py``, ``tests/test_split_harness.py``.
""")
text = "\n".join(P).replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
lines = text.split("\n")
for i in range(1, len(lines)):
    if lines[i] and set(lines[i]) == {"="} and lines[i - 1]:
        lines[i] = "=" * (len(lines[i - 1]) + 2)
OUT.write_text("\n".join(lines))
print("wrote", OUT, OUT.stat().st_size)
