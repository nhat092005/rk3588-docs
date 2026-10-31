**************************
Giao thức P2 và đo mở rộng
**************************

.. admonition:: Trang này trả lời

   - Nếu ghim ``rknn_server`` và ngắt NPU vào CPU4 (giao thức P2), cổng A5 và A8 có đạt không, so với giao thức gốc chạy lại trên LAN (P1-LAN)?
   - Lần gọi ``eval_perf`` đầu tiên, hằng số mỗi dòng ở chế độ debug, ``CORE_0`` so với ``AUTO`` và ``CORE_0_1_2``, mức log, giá trị đầu vào và trọng số có làm đổi thời gian không?
   - Độ chính xác của chính mô hình INT8 được đo latency là bao nhiêu, và mức giảm so với FP32 đi theo lượng tử hóa hay theo đường suy luận?

.. admonition:: Tóm tắt

   - A5 và A8 gốc (qua relay, ngày 2026-10-30) giữ nguyên "không đạt". Trang này báo kết quả của hai giao thức mới chạy trên LAN, không thay kết quả gốc.
   - Cổng P1-LAN: A1 đạt, A2 đạt, A3 đạt, A4 đạt, A5 không đạt, A6 đạt, A8 không đạt, A7 đạt. Cổng P2: A1 đạt, A2 đạt, A3 đạt, A4 đạt, A5 đạt, A6 đạt, A8 đạt, A7 đạt. Đọc theo quy tắc viết trước: A5 "trên LAN, ghim lõi làm cổng đạt", A8 "trên LAN, ghim lõi làm cổng đạt".
   - Lần gọi đầu: P1-LAN không ổn định, P2 không ổn định. Hằng số mỗi dòng: ghim lõi thu hẹp chênh lệch hằng số mỗi dòng giữa các phiên.
   - ``AUTO`` so với ``CORE_0``: không phân biệt được (hiệu -0.01 ms). ``CORE_0_1_2`` so với ``CORE_0``: khác (hiệu -0.54 ms). Mức log: chưa kết luận (P2 không thực hiện đúng).
   - Giá trị đầu vào: thời gian không phụ thuộc giá trị đầu vào trong các đầu vào đã thử. Trọng số: thời gian không phụ thuộc giá trị trọng số trong hai mô hình đã thử.

Kết quả vị trí E2 đến E2e nằm ở :doc:`05-thu-ghim-cpu-va-ngat`, cơ chế ở :doc:`06-co-che-cac-muc-do-tre`, cổng gốc ở :doc:`02-ket-qua-latency-tung-khoi` (mục 4).

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Hai giao thức trên LAN
=========================

Mỗi phiên là lệnh ``benchmark_npu.py`` của kế hoạch (một phiên latency 5 lần ``eval_perf`` với ``perf_debug=False`` và một phiên từng lớp 5 lần với ``perf_debug=True``), chạy trên LAN trực tiếp. P1-LAN giữ điều kiện gốc (không ghim, ``irqbalance`` chạy). P2 ghim mọi luồng ``rknn_server`` và ba dòng ngắt NPU vào CPU4, ``irqbalance`` dừng. Hai giao thức chạy xen kẽ từng phiên, nghỉ 45 giây giữa các phiên (số mới, chưa qua người dùng duyệt). Một tiến trình root trên board (CPU7) đổi chế độ theo yêu cầu và ghi mỗi giây danh sách CPU được phép của từng luồng ``rknn_server``. Phiên 1 đến 3 của mỗi giao thức dùng cho cổng (mã và ngưỡng 5%, 10% của ``aggregate_layers.py`` không đổi), phiên 4 đến 10 dùng cho các câu hỏi khác. Quy tắc: ``bench/onboard_x4/rule.txt``, viết trước dữ liệu.


2. Cổng A1 đến A8 của hai giao thức
===================================

.. list-table::
   :header-rows: 1
   :widths: 12 24 24

   * - Cổng
     - P1-LAN (không ghim)
     - P2 (ghim CPU4)
   * - A1
     - đạt
     - đạt
   * - A2
     - đạt
     - đạt
   * - A3
     - đạt
     - đạt
   * - A4
     - đạt
     - đạt
   * - A5
     - không đạt
     - đạt
   * - A6
     - đạt
     - đạt
   * - A7
     - đạt
     - đạt
   * - A8
     - không đạt
     - đạt

Đọc theo bảng 2 × 2 viết trước trong quy tắc: A5 "trên LAN, ghim lõi làm cổng đạt", A8 "trên LAN, ghim lõi làm cổng đạt". Trung vị latency của 10 phiên P2 nằm trong 16.632 đến 16.658 ms, cả 10 ở mức nhanh. 10 phiên P1-LAN có 1 phiên mức chậm, 9 phiên mức giữa và 0 phiên mức nhanh (trung vị 17.25 đến 21.87 ms), tức các phiên rơi vào các mức khác nhau. Điều này khớp với giải thích "lấy mẫu mức" cho việc A5 gốc không đạt (:doc:`04-cac-muc-do-tre`, mục 1), nay có số đo hỗ trợ (kết quả 2 × 2 cùng phân loại mức của từng phiên). Vì A5 và A8 của P2 đạt, theo kế hoạch FP16 được chạy dưới P2 (mục 6).

Phiên P2 được tính là thực hiện đúng khi mọi dòng log mỗi giây của tiến trình trên board trong khung phiên ở chế độ ghim và không có luồng nào ngoài CPU4, và ít nhất 99% ngắt NPU của phiên ở CPU4. Cả 20 phiên benchmark thực hiện đúng. Log chỉ lấy mẫu mỗi giây, nên vi phạm ngắn hơn khoảng 1 giây có thể không thấy (một vi phạm như vậy đã được thấy ở phiên log, mục 4).

3. Lần gọi đầu, hằng số mỗi dòng, tổng debug
============================================

.. list-table::
   :header-rows: 1
   :widths: 12 24 22 24 18

   * - Giao thức
     - Lần gọi đầu thấp hơn các lần sau
     - Trung vị (lần đầu trừ các lần sau), ms
     - Hằng số mỗi dòng (µs), nhỏ nhất đến lớn nhất
     - Phiên có tổng debug thấp hơn latency
   * - P1LAN
     - 4/10 (không ổn định)
     - +0.011
     - 8.3 đến 51.7
     - 4/10
   * - P2
     - 2/10 (không ổn định)
     - +0.022
     - 4.9 đến 5.2
     - 0/10

- Lần gọi đầu (U6): trên LAN, theo quy tắc là "không ổn định" ở cả hai giao thức. Đây là đính chính có ngày 2026-10-31 cho quan sát "lần gọi đầu thấp hơn ở cả 5 phiên" của các phiên qua relay (:doc:`04-cac-muc-do-tre`, mục 4.2). Quan sát cũ vẫn đúng với dữ liệu cũ.
- Hằng số mỗi dòng ở chế độ debug (U10): ghim lõi thu hẹp chênh lệch hằng số mỗi dòng giữa các phiên. Dưới P2 hằng số khoảng 5.0 µs, chênh 0.3 µs giữa 10 phiên, so với 8.3 đến 51.7 µs dưới P1-LAN. Đây là liên hệ với việc ghim lõi, nguyên nhân vẫn chưa biết.
- Tổng debug so với latency (U13): tổng debug thấp hơn latency ở 4/10 phiên P1-LAN và 0/10 phiên P2. Dưới P2 tổng debug luôn cao hơn latency, đúng với câu của hãng "the time-consuming is more than when perf_debug=False" [T1 UG232 tr.177]. Trường hợp B2 cũ (tổng debug thấp hơn) chỉ xuất hiện khi không ghim.

4. CORE_0, AUTO, CORE_0_1_2 và mức log
======================================

Các phiên chỉ đo latency (5 lần ``eval_perf``), dưới P2, xen kẽ 4 vòng cho ba mặt nạ và 3 vòng cho mức log, nghỉ 45 giây.

.. list-table::
   :header-rows: 1
   :widths: 16 26 14 24 22

   * - Thiết lập
     - Trung vị các phiên (ms)
     - Hiệu so với tham chiếu (ms)
     - Dòng ngắt dùng (mỗi phiên)
     - Kết luận theo quy tắc
   * - CORE_0
     - 16.676, 16.652, 16.647, 16.657
     - +0.000
     - 36: 315, 37: 0, 38: 0
     - tham chiếu
   * - AUTO
     - 16.643, 16.652, 16.646, 16.641
     - -0.010
     - 36: 315, 37: 0, 38: 0
     - không phân biệt được
   * - CORE_0_1_2
     - 16.096, 16.105, 16.119, 16.118
     - -0.543
     - 36: 385, 37: 145, 38: 145
     - khác
   * - verbose=False
     - 16.642, 16.648, 16.644
     - +0.000
     - -
     - tham chiếu
   * - verbose=True
     - 16.650, 16.643, 16.640
     - -0.001
     - -
     - chưa kết luận (P2 không thực hiện đúng)

- ``AUTO`` (U16): không phân biệt được. Mọi phiên ``AUTO`` chỉ dùng dòng ngắt 36 (một nhân), như ``CORE_0``.
- ``CORE_0_1_2`` (U22): khác, hiệu -0.54 ms (-3.3%), đo dưới P2 với cả ba dòng ngắt ở CPU4. Đây là số đo latency, không phải kết luận về đa nhân (cổng G4 và chiến lược S1 đến S3 thuộc giai đoạn 2, :doc:`../02-tang-npu/02-multi-core`).
- Mức log (U19): chưa kết luận, vì một phiên tham chiếu ``verbose=False`` có một giây thấy một luồng ``rknn_server`` ngoài CPU4 (``bench/onboard_x4/analysis_note.txt``). Số đo mô tả: trung vị hai mức log gần như bằng nhau.

5. Giá trị đầu vào và trọng số
==============================

X5 chạy C API ở ô (4, 4) với bốn đầu vào (toàn 0, ngẫu nhiên với seed cố định, hai ảnh test ppe5 đã letterbox) và hai mô hình cùng kiến trúc (seed 0 và seed 1), mỗi điều kiện hai khối 300 lần chạy, thêm một khối tham chiếu thứ hai ở cuối mỗi nửa để kiểm độ trôi. Quy tắc ``bench/onboard_x5/rule.txt`` (ngưỡng 0.05 ms và 0.25 ms là số mới, chưa qua người dùng duyệt).

- Độ trôi giữa hai khối tham chiếu: 0.019 và 0.008 ms, dưới 0.05 ms.
- Đầu vào (U20): thời gian không phụ thuộc giá trị đầu vào trong các đầu vào đã thử (chênh lệch tối đa 0.007 ms).
- Trọng số: thời gian không phụ thuộc giá trị trọng số trong hai mô hình đã thử (chênh lệch tối đa 0.014 ms).


6. FP16 dưới P2
===============

Theo kế hoạch, FP16 chỉ chạy khi A8 của INT8 đạt. Điều kiện đó chỉ đạt dưới P2 (mục 2), nên X8 chạy FP16 dưới P2, xen kẽ A B A B A B (A là phiên INT8, B là phiên FP16), nghỉ 45 giây, với file FP16 export ngày 2026-10-31 (``weights/rknn_fp16/``, sha256 ``bd4a8c8a``). Quy tắc ``bench/onboard_x8/rule.txt``. Cả 6 phiên thực hiện đúng. Cổng A1 đến A8 đạt ở cả hai độ chính xác.

.. list-table::
   :header-rows: 1
   :widths: 16 40 20

   * - Độ chính xác
     - Trung vị latency các phiên (ms)
     - Trung vị chung (ms)
   * - INT8
     - 16.536, 16.539, 16.502
     - 16.536
   * - FP16
     - 27.284, 27.282, 27.267
     - 27.282

FP16 chậm hơn INT8 10.75 ms, gấp 1.65 lần, trong cùng một lần chạy xen kẽ. Tỉ lệ thời gian của các khối từ 2% trở lên (mô tả):

.. list-table::
   :header-rows: 1
   :widths: 12 16 16

   * - Khối
     - Tỉ lệ INT8
     - Tỉ lệ FP16
   * - L0
     - 11.0%
     - 7.0%
   * - L1
     - 3.1%
     - 3.9%
   * - L2
     - 13.4%
     - 13.0%
   * - L4
     - 7.6%
     - 9.1%
   * - L6
     - 4.3%
     - 5.5%
   * - L8
     - 2.2%
     - 2.6%
   * - L12
     - 3.1%
     - 4.1%
   * - L15
     - 5.7%
     - 7.0%
   * - L18
     - 3.0%
     - 3.7%
   * - L21
     - 2.1%
     - 2.6%
   * - L22
     - 33.7%
     - 29.5%

Đây là số đo latency. Việc giữ hay bỏ FP16 không được quyết ở đây.

7. Độ chính xác của mô hình INT8
================================

X7 chấm chính file INT8 được đo latency (sha256 ``a501f94e``), suy luận bằng RKNNLite trên board, chấm điểm trên PC bằng cùng mã và cùng ngưỡng tin cậy với bản FP32 (Evaluation Protocol v1, ``ai/core/evaluator.py``). Quy tắc ``bench/eval_x7/rule.txt``: chỉ báo số, không áp ngưỡng nào (ngưỡng 1.0 pp mAP đã duyệt thuộc cổng G4, giai đoạn 2).

.. list-table::
   :header-rows: 1
   :widths: 14 8 14 12 12 14

   * - Tập
     - Số ảnh
     - Chỉ số
     - INT8
     - FP32
     - Chênh (điểm %)
   * - css_test
     - 82
     - precision
     - 0.7660
     - 0.8950
     - -12.90
   * - css_test
     - 82
     - recall
     - 0.6713
     - 0.7396
     - -6.83
   * - css_test
     - 82
     - map50
     - 0.6965
     - 0.8006
     - -10.41
   * - css_test
     - 82
     - map50_95
     - 0.3675
     - 0.4999
     - -13.24
   * - ppe2286_ext
     - 180
     - precision
     - 0.5234
     - 0.6160
     - -9.26
   * - ppe2286_ext
     - 180
     - recall
     - 0.6092
     - 0.6051
     - +0.41
   * - ppe2286_ext
     - 180
     - map50
     - 0.5330
     - 0.5736
     - -4.06
   * - ppe2286_ext
     - 180
     - map50_95
     - 0.2313
     - 0.2624
     - -3.11

Trên ``css_test``, mAP50-95 của INT8 thấp hơn FP32 13.24 điểm phần trăm. Phép so này gộp cả hai khác biệt: lượng tử hóa và đường suy luận (RKNNLite trên board so với PyTorch trên PC). X7b tách chúng bằng cách chấm mô hình FP16 qua đúng đường RKNNLite (``bench/eval_x7b/rule.txt``, viết trước, các số 0.25 và 0.75 là số mới, chưa qua người dùng duyệt): trên ``css_test``, FP16 qua RKNNLite có mAP50-95 0.4976, chênh -0.23 điểm phần trăm so với FP32, còn INT8 chênh -13.24. Theo quy tắc: **mức giảm của INT8 chủ yếu đi theo lượng tử hóa**. Trên ``ppe2286_ext`` (mô tả) FP16 qua RKNNLite chênh 0.11 và INT8 chênh -3.11. ``css_test`` chỉ có 82 ảnh và một seed. Mức giảm do lượng tử hóa là phát biểu về kết quả đo, nguyên nhân bên trong lượng tử hóa (hiệu chuẩn hay lớp nhạy) chưa được kiểm. Từ khóa đề xuất: "RKNN INT8 accuracy drop YOLOv8 quantization calibration".

8. Điều chưa biết và giới hạn
=============================

- Mức log (U19): chưa kết luận (mục 4).
- Vì sao hằng số mỗi dòng ở chế độ debug gần như không đổi dưới P2 mà dao động khi không ghim (liên hệ đo được, nguyên nhân chưa biết).
- Nguyên nhân bên trong của mức giảm INT8 (hiệu chuẩn, lớp nhạy, hay phân phối dữ liệu hiệu chuẩn): X7b chỉ cho biết mức giảm đi theo lượng tử hóa, không đi theo đường suy luận RKNNLite (U28). Cập nhật 2026-10-31 (giai đoạn 2): chẩn đoán lượng tử hóa đã khoanh vùng công thức lấy lại gần hết mức rơi (giữ FP16 nhánh giải mã box), xem :doc:`../02-tang-npu/13-ket-qua-luong-tu-hoa`. Nguyên nhân bên trong vẫn chưa biết.
- P2 là giao thức mới chạy trên LAN, chưa qua người dùng duyệt làm giao thức chính. Mọi số ở trang này là một board, một lần khởi động, một mô hình.

9. Nguồn
========

- T1: ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (UG232 tr.177).
- T3 board và PC: ``results/onboard_x4_*``, ``results/latency_per_block_*_p1lan.*``, ``results/latency_per_block_*_p2.*``, ``results/onboard_x5_*``, ``results/onboard_x8_*``, ``results/latency_per_block_*_x8.*``, ``results/eval_x7_*``, ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_x4/``, ``onboard_x5/``, ``onboard_x8/``, ``eval_x7/``, ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/eval/``. Mã: ``ai/automation/analyze_x4.py``, ``analyze_x5.py``, ``analyze_x7.py``, ``analyze_x8.py``, ``aggregate_layers.py`` (tham số ``--bench-subdir`` và ``--tag``), ``benchmark_npu.py`` (tham số ``--out-subdir``).

