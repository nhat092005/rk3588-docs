***********
Đòn bẩy FPS
***********

.. admonition:: Trang này trả lời

   - Model INT8 chuẩn (``int8h5``) có khác INT8 mặc định về thông lượng không, khi mục tiêu là 60 FPS?
   - Một context của model tách đầu (``A1``) với giải mã CPU chồng lấp cùng NPU có đạt 60 FPS về thông lượng không, và đổi lại điều gì?
   - Có cần giải mã bằng C hoặc NEON không?

.. admonition:: Tóm tắt

   - E1: ``int8h5`` và ``int8`` không phân biệt được về thông lượng theo quy tắc 5% ở cả bốn cấu hình (một context ``CORE_0`` 54.86 so với 54.69 FPS, ba context 142.09 so với 141.13 FPS). Một context chưa đạt 60 FPS ở cả hai model, hai context (101.89 FPS) và ba context đạt.
   - E2: model tách đầu một context ``CORE_0`` với giải mã chồng lấp bằng pipeline (điều kiện C) đạt 65.99 FPS, so với 54.79 FPS của ``int8h5`` một context chạy tuần tự và 42.05 FPS của chính model tách đầu khi giải mã nằm trong cùng luồng (điều kiện B). Thêm một luồng giải mã (D, 65.74 FPS) hay dùng ba lõi cho một context (E, 68.21 FPS) không phân biệt được với C.
   - Độ chính xác của model tách đầu đã chấm ở :doc:`07-ket-qua-qat-kien-truc` (49.84 AP50-95 của ``A1`` so với 49.66 của ``int8h5`` trên ``css_test``). Pipeline chỉ đổi cách xếp luồng, và cổng đúng đắn của E2 trên 20 ảnh qua (F1 0.978, ngưỡng 0.85).
   - Pipeline tăng thông lượng chứ không giảm thời gian mỗi khung: thời gian đầu cuối đo được ở các điều kiện pipeline đều lớn hơn 16.67 ms nhiều lần (xem mục 5). Theo cách đọc "mỗi khung xong trong 16.67 ms", không điều kiện nào đạt.
   - E3 (giải mã bằng C hoặc NEON) không chạy: điều kiện kích hoạt viết trước (C dưới 60 FPS và giai đoạn post chậm hơn NPU) không xảy ra. Điều này chỉ có nghĩa theo cách đọc thông lượng của mục tiêu.
   - Một seed, một board, ảnh cache, không camera, giao thức P3 (đã duyệt), các số ngưỡng mới của hai thí nghiệm chưa duyệt.

Tiêu chí của mục tiêu 60 FPS và hai cách đọc ở :doc:`03-ket-qua-da-nhan` mục 8. Quy tắc viết trước dữ liệu: ``bench/onboard_q2f_thr/rule.txt`` (E1) và ``bench/onboard_q2f_split/rule.txt`` (E2) trong thư mục run ``ppe5_yolov8n_baseline_100ep_s0``.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Câu hỏi, giao thức và nguồn
================================

Cả hai thí nghiệm chạy ``ai/board/bench_throughput_rep.py`` dưới taskset ``-c 4-7`` với helper P3 (``p3_hold.sh``, giao thức đã duyệt ngày 2026-11-01, hạn chế ở :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3` mục 6), 1238 khung, nghỉ 20 giây giữa các lần chạy, ba lần lặp theo cùng thứ tự, ảnh test ``ppe5`` đã decode sẵn trong bộ nhớ (không camera, không giải mã video, không vẽ hay lưu kết quả). FPS là số khung chia cho thời gian tường, đã tính tiền xử lý, NPU và hậu xử lý (kể cả giải mã box của model tách đầu). Mỗi con số là trung vị của ba lần chạy, chênh lệch tối đa là khoảng trải. Một lần chạy chỉ được tính khi thực hiện đúng P3 (ngắt NPU đúng lõi, tiến trình trong CPU4 đến CPU7, tần số khóa, ``irqbalance`` dừng). Cả hai thí nghiệm đều có mọi lần chạy thực hiện đúng.

Quy tắc "khác" viết trước dữ liệu: chênh ít nhất 5% và lớn hơn khoảng trải lớn hơn của hai điều kiện, nếu không thì "không phân biệt được". Đây là quy tắc của M12 (trường ``rule`` của ``results/thr_p3.json``, kết quả ở :doc:`03-ket-qua-da-nhan`), dùng lại cho các so sánh mới của trang này (các so sánh mới chưa duyệt).

2. E1: int8h5 so với int8
===========================

``int8h5`` là INT8 chuẩn (:doc:`05-ket-qua-luong-tu-hoa`) nhưng mục 8 của :doc:`03-ket-qua-da-nhan` đo bằng ``int8`` mặc định. E1 đo lại cả hai trong cùng một phiên.

.. list-table::
   :header-rows: 1
   :widths: 28 22 22 10 22 22

   * - Cấu hình
     - ``int8`` FPS (khoảng trải)
     - ``int8h5`` FPS (khoảng trải)
     - Chênh
     - Kết luận
     - ``int8h5`` so với 60 FPS
   * - 1 context ``CORE_0``
     - 54.69 (0.07)
     - 54.86 (0.09)
     - +0.31%
     - không phân biệt được
     - chưa đạt
   * - 1 context ``CORE_0_1_2``
     - 56.17 (0.06)
     - 56.30 (0.06)
     - +0.23%
     - không phân biệt được
     - chưa đạt
   * - 2 context ``CORE_0`` và ``CORE_1``
     - 101.90 (0.57)
     - 101.89 (0.29)
     - -0.01%
     - không phân biệt được
     - đạt
   * - 3 context (S2)
     - 141.13 (0.45)
     - 142.09 (0.73)
     - +0.68%
     - không phân biệt được
     - đạt

Chênh chỉ từ 0.01% đến 0.68%, dưới ngưỡng 5% của quy tắc (ở ba cấu hình chênh FPS còn lớn hơn khoảng trải nhưng vẫn dưới 5%), nên theo quy tắc là không phân biệt được và số của :doc:`03-ket-qua-da-nhan` mục 8 áp dụng cho ``int8h5`` ở mức đo này. Phần đã biết về latency NPU của ``int8h5`` ở :doc:`05-ket-qua-luong-tu-hoa` mục 6 phù hợp: cùng cỡ.

Ghi chú về mã đo: E1 chạy với harness trước khi thêm hỗ trợ model tách đầu, mã được đồng bộ lên board sau khi E1 xong nên E2 chạy với harness mới. Điều kiện A của E2 (``int8h5``, một context ``CORE_0``, tuần tự) và ``int8h5`` T1 của E1 đo cùng một việc trên hai bản harness: 54.79 và 54.86 FPS, chênh 0.13%, nên đổi harness không làm đổi đường chuẩn. Các bản ghi chỉ đánh dấu ``git_dirty``, không phân biệt được hai bản.

3. Cổng đúng đắn của E2
=========================

Model tách đầu trả hai đầu ra thô, CPU giải mã bằng numpy rồi mới chạy hậu xử lý chung. Trước khi đọc thời gian, ``ai/board/split_gate.py`` so các phát hiện (ngưỡng 0.25) của hai model trên 20 ảnh test qua cùng đường harness: 136 phát hiện của ``int8h5``, 140 của model tách đầu, 135 cặp khớp (cùng lớp, IoU ít nhất 0.5), F1 bằng 0.978. Ngưỡng viết trước là 0.85 (số mới, chưa duyệt), nên cổng qua.

4. E2: giải mã chồng lấp với NPU
==================================

Model tách đầu có phần NPU nhanh hơn (13.07 ms ở ``CORE_0`` dưới P2, :doc:`07-ket-qua-qat-kien-truc` mục 2) nhưng giải mã numpy tốn 8.02 ms trên CPU. Nếu giải mã nằm trong cùng luồng thì tổng dài hơn ``int8h5``. E2 hỏi: nếu giải mã chạy ở luồng khác trong khi NPU xử lý khung kế tiếp thì thông lượng ra sao. Sáu điều kiện (số luồng tiền xử lý và hậu xử lý trong ngoặc):

.. list-table::
   :header-rows: 1
   :widths: 44 20 16 34 14

   * - Điều kiện
     - FPS (khoảng trải)
     - So với 60 FPS
     - T_pre / T_npu / T_post (ms, trung vị)
     - CPU tiến trình
   * - A: ``int8h5``, tuần tự, ``CORE_0``
     - 54.79 (0.09)
     - chưa đạt
     - 0.23 / 17.19 / 0.66
     - 24%
   * - B: tách đầu, giải mã cùng luồng, ``CORE_0``
     - 42.05 (0.05)
     - chưa đạt
     - 0.29 / 14.30 / 8.94
     - 54%
   * - C: tách đầu, pipeline (1 pre, 1 post), ``CORE_0``
     - 65.99 (0.03)
     - đạt
     - 0.87 / 15.04 / 11.61
     - 100%
   * - D: tách đầu, pipeline (1 pre, 2 post), ``CORE_0``
     - 65.74 (0.21)
     - đạt
     - 0.71 / 15.09 / 11.70
     - 100%
   * - E: tách đầu, pipeline (1 pre, 1 post), ``CORE_0_1_2``
     - 68.21 (0.65)
     - đạt
     - 0.94 / 14.61 / 11.81
     - 105%
   * - F: ``int8h5``, pipeline (1 pre, 1 post), ``CORE_0``
     - 56.62 (0.21)
     - chưa đạt
     - 0.46 / 17.42 / 0.85
     - 28%

So sánh theo quy tắc "khác":

.. list-table::
   :header-rows: 1
   :widths: 52 14 12 20 24

   * - So sánh
     - Chênh FPS
     - Chênh %
     - Khoảng trải lớn hơn
     - Kết luận
   * - B so với A (giải mã cùng luồng so với ``int8h5``)
     - -12.74
     - -23.3%
     - 0.09
     - khác
   * - C so với A (pipeline tách đầu so với ``int8h5`` tuần tự)
     - +11.20
     - +20.4%
     - 0.09
     - khác
   * - C so với B (chồng lấp so với cùng luồng)
     - +23.94
     - +56.9%
     - 0.05
     - khác
   * - D so với C (thêm một luồng post)
     - -0.25
     - -0.4%
     - 0.21
     - không phân biệt được
   * - E so với C (một context trên ba lõi)
     - +2.22
     - +3.4%
     - 0.65
     - không phân biệt được
   * - F so với A (pipeline so với tuần tự, cùng ``int8h5``)
     - +1.83
     - +3.3%
     - 0.21
     - không phân biệt được

Đọc: chồng lấp tăng thông lượng của model tách đầu +56.9% so với giải mã cùng luồng và đưa nó lên 65.99 FPS, hơn ``int8h5`` tuần tự +20.4%. Một luồng giải mã đủ (D không khác C, thời gian post 11.61 ms nhỏ hơn thời gian NPU 15.04 ms). Dùng ba lõi cho một context (E) không phân biệt được với C (+3.4%, dưới 5%). Pipeline một mình không giúp ``int8h5`` (+3.3%, không phân biệt được), phép đo không nói vì sao. Đây là mô tả của phép đo, không phải cơ chế.

5. Hai cách đọc mục tiêu 60 FPS
=================================

**Đọc theo thông lượng** (mặc định của :doc:`03-ket-qua-da-nhan` mục 8): các điều kiện C (65.99), D (65.74) và E (68.21 FPS) đạt, nên một context của model tách đầu với giải mã chồng lấp đạt 60 FPS, không cần nhiều context. ``int8h5`` một context (A, F) chưa đạt, nó cần hai context (:doc:`03-ket-qua-da-nhan`). Thứ tự đầu ra: ở C mỗi giai đoạn chỉ một luồng nối bằng hàng đợi FIFO nên thứ tự được giữ theo cách xây dựng, harness không kiểm điều này (chưa kiểm), còn D có hai luồng post nên có thể đảo thứ tự.

**Đọc theo thời gian mỗi khung** (mỗi khung phải xong trong 16.67 ms): không điều kiện nào đạt. Trường ``e2e_latency_ms`` của harness cho trung vị 132.6 ms ở C và 141.6 ms ở F. Theo mã, harness có hàng đợi 6 chỗ (``bench_throughput_rep.py``, ``--queue-size`` mặc định 6) và đẩy khung liên tục, nên hai số này có khả năng gồm thời gian chờ hàng đợi (mức đầy của hàng đợi không đo). Chúng không phải thời gian của một khung riêng lẻ. Tổng ba giai đoạn của C là 27.6 ms (tổng trung vị từng giai đoạn dưới tranh chấp, không phải đo đầu cuối trực tiếp và không phải cực tiểu), cũng lớn hơn 16.67 ms. Đo thời gian mỗi khung với cấp khung theo nhịp 60 FPS: chưa làm.

6. E3: giải mã bằng C hoặc NEON
=================================

Điều kiện kích hoạt viết trước: E3 chỉ chạy nếu điều kiện C dưới 60 FPS và trung vị ``t_post_ms`` của C không nhỏ hơn trung vị ``t_npu_ms``. C đạt 65.99 FPS và ``t_post`` (11.61 ms) nhỏ hơn ``t_npu`` (15.04 ms), nên E3 không chạy. Kết quả ghi nhận: không cần theo cách đọc thông lượng của mục tiêu 60 FPS ở cấu hình này (theo cách đọc thời gian mỗi khung chưa xét). Giải mã C hoặc NEON vẫn có thể hữu ích nếu cần giảm CPU hoặc nâng FPS vượt mức này: chưa đo. Trong các tài liệu T1 đã tìm không có chữ NEON (:doc:`../03-tang-npu-don-bay/09-pre-post-processing`).

7. Điều chưa biết và giới hạn
===============================

- Thời gian mỗi khung khi cấp khung theo nhịp 60 FPS và thứ tự đầu ra của pipeline: chưa đo.
- Camera thật, giải mã video, vẽ và lưu kết quả không nằm trong đo. Thông lượng thực của ứng dụng có thể thấp hơn.
- Model tách đầu chưa được nối vào các script demo của repo, E2 dùng harness đo. Chi phí tích hợp và CPU thêm (100% so với 24% của A) cần xem khi triển khai.
- Độ chính xác của đường tách đầu trên ảnh đã chấm ở :doc:`07-ket-qua-qat-kien-truc` (một seed). Cổng E2 chỉ so các phát hiện trên 20 ảnh.
- Một board, một seed, P3 không so được với số P2 của :doc:`07-ket-qua-qat-kien-truc`. Ngưỡng F1 0.85 và quy tắc "khác" cho các so sánh mới chưa duyệt.
- Đòn bẩy chưa đo: tách đầu với nhiều context, giải mã bằng C hoặc NEON, RGA cho tiền xử lý, ``int8h5`` kết hợp bộ nhớ SRAM.

8. Tái lập
============

.. code-block:: bash

   # E1 và E2: board đã khóa tần số, p3_hold.sh chạy bằng sudo -n, model đã rsync lên board
   .venv/bin/python ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_q2f_thr/q2f_thr_driver.py
   # cổng E2 (chạy trên board)
   .venv-board/bin/python -m ai.board.split_gate --standard <rknn_int8h5> --split <rknn_int8_split> --images data/ppe5/processed/images/test --out <json>
   .venv/bin/python ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/onboard_q2f_split/q2f_split_driver.py
   .venv/bin/python -m ai.automation.analyze_q2f
   .venv/bin/python docs/tools/gen_phase3_fps_page.py

Số liệu: ``results/q2f_fps.json``. Mã: ``ai/board/bench_throughput_rep.py`` (hỗ trợ model tách đầu qua ``postprocess_raw`` của ``ai/board/common.py``), ``ai/board/split_gate.py``, ``tests/test_split_harness.py``.
