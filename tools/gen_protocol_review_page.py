#!/usr/bin/env python3
"""Sinh trang 02-tang-npu-nen-do/07-giao-thuc-p2-p3.rst: tóm tắt hai giao thức đo P2 và P3 để người dùng duyệt.

Đọc results/{g4_latency_workload,g4v_latency_workload,g4v_latency_workload_2,q2h_latency,q2i_latency,q2j_split,thr_p3}.json, hai script
helper (x4_hold.sh, p3_hold.sh), các rule.txt và tier1_int8h5_CORE_0.json. Chạy từ gốc repo chính:
    .venv/bin/python docs/tools/gen_protocol_review_page.py
Lời văn nằm trong script, mọi con số lấy từ file. Các assert bảo vệ những số có trong lời văn.
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RES = REPO / "results"
SILU = REPO / "ai" / "automation" / "runs" / "ppe5_yolov8n_baseline_100ep_s0"
BENCH = SILU / "bench"
OUT = REPO / "docs" / "contents" / "03-phuong-phap" / "02-tang-npu-nen-do" / "07-giao-thuc-p2-p3.rst"


def load(name):
    return json.loads((RES / f"{name}.json").read_text())


def table(headers, rows, widths=None):
    out = [".. list-table::", "   :header-rows: 1"]
    if widths:
        out.append("   :widths: " + " ".join(str(w) for w in widths))
    out.append("")
    for line in [headers] + rows:
        for i, cell in enumerate(line):
            out.append(("   * - " if i == 0 else "     - ") + str(cell))
    return "\n".join(out)


x4 = (BENCH / "onboard_x4" / "x4_hold.sh").read_text()
p3 = (BENCH / "onboard_thr" / "p3_hold.sh").read_text()
# facts the prose states about the two helpers
assert "echo 4 > /proc/irq/$i/smp_affinity_list" in x4 and "taskset -a -p -c 4 $P" in x4 and "systemctl stop irqbalance" in x4
assert "trap cleanup EXIT" in x4 and "trap cleanup EXIT" in p3 and "Never kills rknn_server" in x4 and "Never touches rknn_server" in p3
assert "cpu=4" in p3 and 'cpu=$((cpu+1))' in p3 and "systemctl stop irqbalance" in p3 and "taskset -p -c 3 $$" in p3 and "taskset -p -c 7 $$" in x4
assert "taskset -a -p -c 0-7 $P" in x4
rule_thr = (BENCH / "onboard_thr" / "rule.txt").read_text()
assert "taskset -c 4-7" in rule_thr and "at least 99 percent" in rule_thr and "P3 is not approved by the user" in rule_thr
rule_g4b = (BENCH / "onboard_g4b" / "rule.txt").read_text()
assert "at least 99 percent of the NPU interrupts of the session on CPU4" in rule_g4b and "not approved as the main protocol" in rule_g4b

# ---- how many runs realized the protocol
G, GV, GV2, H, I, J, T = (load(n) for n in ("g4_latency_workload", "g4v_latency_workload", "g4v_latency_workload_2", "q2h_latency", "q2i_latency", "q2j_split", "thr_p3"))
exps = []
for label, d in (("G4 A, B (SiLU, ReLU)", G), ("Biến thể activation, lần 1", GV), ("Biến thể activation, lần 2", GV2), ("``h5`` thử (q2h)", H), ("``int8h5`` chuẩn (q2i)", I)):
    ss = d["sessions"]
    exps.append((label, len(ss), sum(1 for s in ss if not s["realized"])))
assert [e[1:] for e in exps] == [(16, 0), (20, 1), (20, 3), (16, 0), (16, 0)], exps
cond = J["conditions"]
q2j_bad = [k for k, v in cond.items() if not v["realized"]]
assert q2j_bad == ["int8|CORE_0", "int8|CORE_0_1_2"] and len(cond) == 6
assert T["all_realized"] and len(T["runs"]) == 21 and all(r["realized"] for r in T["runs"])
gb, cfg = G["gate_b"], T["configs"]
assert round(gb["relu|CORE_0_1_2"]["drop_pct"], 1) == 33.6 and round(gb["silu|CORE_0_1_2"]["drop_pct"], 1) == 2.9
assert T["best_s1"] == "T3" and round(cfg["T5"]["fps"], 1) == 141.2 and round(cfg["T3"]["fps"], 1) == 56.1 and T["m12"]["verdict"] == "hơn"
assert T["m13"]["verdict"] == "không đáng giữ" and round(T["m13"]["gain_pct"], 1) == 4.4 and T["m3"]["verdict"] == "không phân biệt được"
unpinned = json.loads((SILU / "bench" / "tier1_int8h5_CORE_0.json").read_text())["npu_latency_ms"]
p2_h5 = J["conditions"]["int8h5|CORE_0"]["median"]
assert round(unpinned, 1) == 20.5 and round(p2_h5, 1) == 16.4
split = J["total"]["CORE_0"]


def f(x, d=1):
    return f"{x:.{d}f}"


P = []
w = P.append
w("""*****************************************
Giao thức đo P2 và P3
*****************************************

.. admonition:: Trang này trả lời

   - P2 và P3 là gì, mỗi giao thức đổi gì trên board và khôi phục thế nào?
   - Đã có bao nhiêu phiên đo thực hiện đúng giao thức, và nhãn nào đang phụ thuộc vào chúng?
   - Người dùng đã quyết định gì về hai giao thức (bản ghi ở :doc:`/contents/09-tien-do/02-quyet-dinh/02-duyet-giao-thuc-p2-p3`), và điều đó thay đổi gì ở các nhãn?

.. admonition:: Tóm tắt
""")
w(f"""
   - P2 ghim mọi luồng ``rknn_server`` và ba dòng ngắt NPU vào CPU4, dừng ``irqbalance``, dùng cho đo latency của một context. P3 đặt dòng ngắt 36, 37, 38 lên CPU4, CPU5, CPU6, dừng ``irqbalance``, chạy tiến trình đo dưới ``taskset -c 4-7``, dùng cho đo thông lượng nhiều context (S2, S3). Cả hai chỉ đổi cấu hình khi chạy phiên và khôi phục khi kết thúc.
   - Mức thực hiện đúng của P2: trong năm thí nghiệm latency của giai đoạn 2, {sum(e[1] for e in exps)} phiên có {sum(e[2] for e in exps)} phiên không thực hiện đúng (lần 2 của biến thể activation có 3, lần 1 có 1). Thí nghiệm tách đầu ``q2j`` có 2 trong 6 điều kiện (cả hai là model ``int8`` mặc định) không thực hiện đúng. P3: {len(T['runs'])} trên {len(T['runs'])} lần chạy thực hiện đúng.
   - Quyết định ngày 2026-11-01: người dùng trả lời \"approve\" cho câu hỏi ba hướng, được hiểu là hướng 1, duyệt cả P2 và P3 nguyên trạng (bản ghi ở :doc:`/contents/09-tien-do/02-quyet-dinh/02-duyet-giao-thuc-p2-p3`). Các nhãn ở mục 5 không còn dòng "chưa duyệt" của giao thức. Hạn chế ở mục 6 vẫn áp dụng, số phiên không thực hiện đúng vẫn gắn nhãn "chưa kết luận".
   - Hai giao thức là điều kiện phòng thí nghiệm, không phải cấu hình triển khai. Chỉ để cho biết cỡ số, không phải kết luận: cùng model ``int8h5`` ``CORE_0`` có trung vị {f(p2_h5)} ms dưới P2 và {f(unpinned)} ms trong một phiên ``make benchmark-npu`` không chạy helper P2 (một phiên mỗi bên, trạng thái ngắt của phiên thứ hai không được ghi, và {f(unpinned)} ms nằm trong khoảng 17.25 đến 21.87 ms của các phiên không ghim ở :doc:`08-ket-qua-p2-va-do-mo-rong`).
""")
w("""
Kế hoạch đo và kết quả gốc ở :doc:`08-ket-qua-p2-va-do-mo-rong`, kết quả dùng chúng ở :doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` và :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Vì sao cần hai giao thức
===========================

Phép đo latency một context đọc thời gian của một lần chạy trên NPU. Ở :doc:`08-ket-qua-p2-va-do-mo-rong` mục 2, 10 phiên P2 có trung vị latency trong 16.632 đến 16.658 ms (cả 10 ở mức nhanh) còn 10 phiên không ghim (P1-LAN) rơi vào các mức khác nhau (trung vị 17.25 đến 21.87 ms). Vì vậy P2 ghim cả luồng ``rknn_server`` lẫn dòng ngắt NPU vào CPU4 để các phiên so sánh được. Nguyên nhân đầy đủ của việc không ghim rơi vào nhiều mức chưa biết. Với ba context chạy song song và pipeline CPU và NPU, đặt mọi thứ vào một CPU làm các luồng tranh nhau, nên P3 chia ba dòng ngắt cho ba CPU lớn và để tiến trình đo dùng bốn CPU lớn. Lý do này là lập luận thiết kế của quy tắc ``onboard_thr/rule.txt``, không phải kết quả đã đo riêng.

2. Hai giao thức làm gì trên board
==================================
""")
w(table(["", "P2 (latency, một context)", "P3 (thông lượng, nhiều context)"], [
    ["Dòng ngắt NPU 36, 37, 38", "Cả ba về CPU4", "36 về CPU4, 37 về CPU5, 38 về CPU6"],
    ["``irqbalance``", "Dừng khi ghim, bật lại khi bỏ ghim nếu trước đó đang chạy", "Dừng một lần khi bắt đầu, bật lại khi kết thúc nếu trước đó đang chạy"],
    ["``rknn_server``", "Mọi luồng ghim vào CPU4 (``taskset -a -p``), trả về CPU 0 đến 7 khi bỏ ghim. Không bao giờ dừng tiến trình", "Không đụng (RKNNLite trên board không dùng ``rknn_server``)"],
    ["Tiến trình đo", "Chạy từ PC qua ``adb`` và ``rknn_server``, không ghim riêng", "Trên board dưới ``taskset -c 4-7``, các CPU nhỏ để trống"],
    ["Tiến trình helper (root)", "``x4_hold.sh`` chạy trên CPU7, đổi chế độ pin và unpin theo yêu cầu của PC, ghi mỗi giây", "``p3_hold.sh`` chạy trên CPU3, đặt một lần, ghi mỗi giây"],
    ["Khôi phục", "``trap`` khi thoát: trả affinity đã lưu, ``rknn_server`` về 0 đến 7, bật lại ``irqbalance``, đọc lại và ghi vào log", "``trap`` khi thoát: trả affinity đã lưu, bật lại ``irqbalance``, đọc lại và ghi vào log"],
    ["Tần số", "Khóa trước phiên bằng ``ai/board/lock_freq.sh lock``, ``make board-check LOCK=1`` kiểm tra đã khóa, helper chỉ ghi ``lock_freq.sh status``", "Như P2"],
], [22, 38, 38]))
w("""

Hai script nằm trong repo (``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_x4/x4_hold.sh`` và ``bench/onboard_thr/p3_hold.sh``). Chúng chạy bằng quyền root qua ``sudo -n`` nhờ tệp ``/etc/sudoers.d/rk3588-measure`` trên board, chỉ cho phép ba bản sao root-owned ``lock_freq.sh``, ``x4_hold.sh`` và ``p3_hold.sh`` trong ``/usr/local/sbin``. Sửa script trong repo không có tác dụng trên board đến khi người dùng cài lại bản sao.

3. Khi nào một phiên được tính là thực hiện đúng
================================================

Hai điều kiện được viết trước dữ liệu trong ``rule.txt`` và kiểm tự động bằng các script phân tích (``analyze_g4v.py`` cho P2, ``analyze_thr.py`` cho P3). Một phiên không thực hiện đúng làm điều kiện của nó mang nhãn "chưa kết luận".

- **P2:** mọi dòng log mỗi giây của helper trong khung phiên ở chế độ ghim và không có luồng ``rknn_server`` nào ngoài CPU4, và ít nhất 99% ngắt NPU của phiên rơi vào CPU4. Log chỉ lấy mẫu mỗi giây, nên một vi phạm ngắn hơn khoảng 1 giây có thể không thấy.
- **P3:** mỗi dòng ngắt đã phát sinh có ít nhất 99% số lần ở CPU được gán (36 ở CPU4, 37 ở CPU5, 38 ở CPU6), affinity của tiến trình đo (và các tiến trình con) nằm trong CPU4 đến CPU7, tần số khóa trước và sau phiên, và log helper trong khung phiên cho thấy ``irqbalance`` không hoạt động và ba affinity không đổi.

4. Mức thực hiện đúng đã quan sát
=================================
""")
w(table(["Thí nghiệm (P2)", "Số phiên", "Không thực hiện đúng"], [[a, b, c] for a, b, c in exps]
        + [["Tách đầu A1 (``q2j``)", "12 phiên trong 6 điều kiện", "2 điều kiện (cả hai của ``int8`` mặc định) có ít nhất một phiên không đúng"]], [46, 26, 40]))
w(f"""

P3 (``onboard_thr``): {len(T['runs'])} lần chạy, {len(T['runs'])} thực hiện đúng. Cờ thực hiện đúng của từng phiên được tính lại từ log helper bằng ``analyze_g4v.py`` và ``analyze_thr.py`` (trường ``realized`` trong file kết quả). Cách xử lý đã dùng: điều kiện có phiên không đúng mang nhãn "chưa kết luận" và không dùng cho nhãn Giữ, Loại.

5. Nhãn đang phụ thuộc vào P2 và P3
===================================
""")
w(table(["Kết luận", "Giao thức", "Số liệu", "Trang"], [
    ["G4 B: ReLU nhanh hơn ở ``CORE_0_1_2``", "P2", f"giảm {f(gb['relu|CORE_0_1_2']['drop_pct'])}% so với ``CORE_0``", ":doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`"],
    ["S1 SiLU: ``CORE_0_1_2`` không nhanh hơn (Loại)", "P2", f"giảm {f(gb['silu|CORE_0_1_2']['drop_pct'])}%", ":doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`"],
    ["S2: ba context mỗi context một nhân (Giữ)", "P3", f"{f(cfg['T5']['fps'])} FPS so với {f(cfg['T3']['fps'])} FPS của một context tốt nhất", ":doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`"],
    ["S3: pipeline (Loại)", "P3", f"hơn S2 {f(T['m13']['gain_pct'])}% (ngưỡng 5%)", ":doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`"],
    ["Ba tiến trình so với ba luồng", "P3", "không phân biệt được", ":doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`"],
    ["``int8h5`` và A1: thời gian NPU và tổng", "P2", f"A1 tách đầu {f(split['split_npu_ms'], 2)} ms NPU cộng {f(split['decode_ms'], 2)} ms giải mã", ":doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`"],
], [38, 12, 40, 26]))
w("""

Các kết luận về độ chính xác (cổng C, mAP) không phụ thuộc P2 hay P3 vì chúng chấm bằng RKNNLite trên board, không qua phép đo thời gian.

6. Giới hạn của hai giao thức
=============================

- Cả hai giao thức đổi cấu hình hệ thống bằng quyền root (ngắt, ``irqbalance``, affinity). Mỗi script có ``trap`` khôi phục và đọc lại, nhưng nếu board mất điện giữa phiên thì ``trap`` không chạy. Trạng thái sau khởi động lại chưa được kiểm riêng.
- Số tuyệt đối dưới P2 không phải số của một ứng dụng triển khai bình thường. Chúng dùng để so sánh có kiểm soát giữa các model và mặt nạ nhân. Cỡ số ở mục tóm tắt chỉ một phiên mỗi bên nên không đủ để kết luận mức chênh giữa có và không ghim.
- Chưa có phép đo nào so P3 với một giao thức khác cho cùng mục đích, nên chưa biết P3 cho số khác bao nhiêu so với không ghim. Chưa biết.
- Log helper lấy mẫu mỗi giây, một vi phạm ngắn hơn có thể không thấy (đã thấy một trường hợp ở phần P2 của :doc:`08-ket-qua-p2-va-do-mo-rong`).
- Một board, một lần khởi động mỗi thí nghiệm, một seed.
- P3 lệch khỏi khuyến nghị gắn ngắt NPU vào cùng một lõi lớn [T1 UG232 tr.75] (đã ghi ở :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`). Việc duyệt không làm khuyến nghị đó mất hiệu lực, chỉ nói P3 được dùng để so sánh có kiểm soát giữa các cấu hình.

7. Nguồn
========

- ``bench/onboard_x4/x4_hold.sh`` (P2), ``bench/onboard_thr/p3_hold.sh`` (P3), ``bench/onboard_g4b/rule.txt``, ``bench/onboard_thr/rule.txt`` (quy tắc viết trước, định nghĩa thực hiện đúng), trong thư mục run ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0``.
- ``results/g4_latency_workload.json``, ``g4v_latency_workload.json``, ``g4v_latency_workload_2.json``, ``q2h_latency.json``, ``q2i_latency.json``, ``q2j_split.json``, ``thr_p3.json`` (số phiên và kết quả).
- ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/tier1_int8h5_CORE_0.json`` (phép đo không ghim bằng ``make benchmark-npu PREC=int8h5``).
- Sinh trang này: ``.venv/bin/python docs/tools/gen_protocol_review_page.py``.
""")
def finish(P, out):
    text = "\n".join(P).replace("\n\n\n\n", "\n\n").replace("\n\n\n", "\n\n")
    lines = text.split("\n")
    for i in range(1, len(lines)):
        if lines[i] and set(lines[i]) == {"="} and lines[i - 1]:
            lines[i] = "=" * (len(lines[i - 1]) + 2)
    lines[0] = lines[2] = "*" * 60 if lines[0].startswith("*") else lines[0]
    out.write_text("\n".join(lines))
    print("wrote", out, out.stat().st_size)

Q = []
w2 = Q.append
w2("""*****************************************
Duyệt giao thức đo P2 và P3
*****************************************

.. admonition:: Trang này trả lời

   - Người dùng đã quyết định gì về giao thức P2 và P3 ngày 2026-11-01, và quyết định áp cho phạm vi nào?

.. admonition:: Tóm tắt

   - Ngày 2026-11-01, người dùng trả lời "approve" cho câu hỏi ba hướng, được hiểu là hướng 1: duyệt cả P2 và P3 nguyên trạng. Các ngưỡng số mới của từng thí nghiệm vẫn ghi "chưa duyệt".

Định nghĩa hai giao thức, mức thực hiện đúng đã quan sát, nhãn phụ thuộc và giới hạn ở :doc:`/contents/03-phuong-phap/02-tang-npu-nen-do/07-giao-thuc-p2-p3`.

1. Quyết định của người dùng
============================

Ngày 2026-11-01, trả lời "approve" cho câu hỏi có ba hướng dưới đây (hướng 1 là đề xuất), người dùng duyệt. Câu trả lời được hiểu là hướng 1.

1. **Duyệt cả hai nguyên trạng.** Bỏ dòng "chưa qua người dùng duyệt" khỏi các nhãn ở mục 5 của :doc:`/contents/03-phuong-phap/02-tang-npu-nen-do/07-giao-thuc-p2-p3`. Điều kiện: các hạn chế ở mục 6 của trang đó vẫn được ghi. **Được hiểu là hướng được chọn.**
2. Duyệt P2, sửa P3 (ví dụ đổi phân bổ CPU, số lần chạy hoặc ngưỡng 99%). Mọi nhãn S2, S3 và ba tiến trình so với ba luồng phải đo lại. Không chọn.
3. Giữ chưa duyệt. Mọi nhãn ở mục 5 của trang giao thức tiếp tục ghi "dưới giao thức chưa duyệt". Không chọn.

Cách hiểu về phạm vi (do tác giả trang, người dùng chỉ trả lời \"approve\" và có thể chỉnh): việc duyệt áp cho hai giao thức P2 và P3 (cách đặt ngắt, ghim, helper, điều kiện thực hiện đúng). Câu trả lời không nêu riêng các ngưỡng số mới của từng thí nghiệm ghi "chưa duyệt" ở chỗ khác (ví dụ 20% của X10, 0.5 điểm của kiểm tra `int8h5`, 48.41 của tiêu chí 2d, 0.8 đến 1.2 của quy tắc ở :doc:`/contents/03-phuong-phap/02-tang-npu-nen-do/06-co-che-cac-muc-do-tre`) nên chúng vẫn ghi \"chưa duyệt\", và không đổi số seed hay mức kết luận của các nhãn.
""")

OUT2 = REPO / "docs" / "contents" / "09-tien-do" / "02-quyet-dinh" / "02-duyet-giao-thuc-p2-p3.rst"
finish(P, OUT)
finish(Q, OUT2)
