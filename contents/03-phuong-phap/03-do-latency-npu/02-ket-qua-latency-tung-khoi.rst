****************************
Kết quả latency từng khối
****************************

.. admonition:: Trang này trả lời

   - Latency NPU của YOLOv8n INT8 (``ppe5``, ``nc=5``) ở ``CORE_0`` trên RK3588 là bao nhiêu, và vì sao con số dao động?
   - Mỗi khối L0 đến L22 chiếm bao nhiêu thời gian, và tỉ lệ đó tin được đến đâu?
   - Điều gì đã kiểm chứng, điều gì chưa biết?

.. admonition:: Tóm tắt

   - Latency không phải một con số. Qua ``eval_perf`` từ PC, trung vị các phiên là 19.24, 19.42, 22.35, 20.16 ms (B2 và ba phiên B3), và 19.88, 20.01 ms (hai phiên E1). Đo ngay trên board bằng C API (không qua đường truyền), ba đợt 1000 lần chạy liên tiếp có trung vị 19.19, 18.99, 20.91 ms, từng lần chạy từ 16.5 đến 22.2 ms. Cổng A5 (chênh giữa các phiên không quá 5%) không đạt: 14.56%.
   - Vì sao latency dao động và các giả thuyết đã kiểm nằm ở :doc:`04-cac-muc-do-tre`, thí nghiệm ghim CPU và ngắt NPU ở :doc:`05-thu-ghim-cpu-va-ngat`, phân tích từng dòng (Conv, op khác Conv, DFL, hằng số mỗi dòng) ở :doc:`03-phan-tich-sau-latency-tung-khoi`.
   - Tỉ lệ thời gian giữa các khối ổn định hơn latency tuyệt đối. Giữa năm nguồn (``eval_perf`` B3, B2 và ba cách tính trên board), tỉ lệ một khối từ 2% thời gian trở lên chênh tối đa 2.2 điểm phần trăm. Khối Detect (L22) chiếm 34.0% (34.6% ở B2), backbone L0 đến L9 chiếm 43.3% (cộng khối trong từng lần gọi rồi lấy trung vị, như bảng 1).
   - Cổng chấp nhận: A1, A2, A3, A4, A6, A7 đạt, A5, A8, A8+B2 không đạt. FP16 chưa chạy theo giao thức gốc vì cổng A8 của INT8 không đạt (đã chạy dưới P2 ngày 2026-10-31, :doc:`07-giao-thuc-p2-va-do-mo-rong`, mục 6).

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Dữ liệu và điều kiện đo
==========================

Model: ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/weights/rknn_int8/best-rk3588.rknn``, sha256 ``a501f94e`` (cùng file trên PC và trên board), RKNN-Toolkit2 2.3.2, ``rknn_server`` và runtime 2.3.2, driver ``rknpu`` 0.9.8. ``CORE_0``. CPU ở 1.8, 2.256 và 2.304 GHz, NPU 1.0 GHz, DDR 2.112 GHz, khoá bằng ``lock_freq.sh lock``. Kế hoạch và định nghĩa từng thông số nằm ở :doc:`01-ke-hoach-do`.

.. list-table::
   :header-rows: 1
   :widths: 18 46 16 20

   * - Nguồn
     - Cách đo
     - Mẫu
     - File
   * - B2
     - ``eval_perf`` từ PC, phiên latency và phiên từng lớp, thêm một phiên bộ nhớ
     - 5 lần gọi mỗi phiên
     - ``bench/tier1_int8_CORE_0*``
   * - B3
     - Ba phiên độc lập như B2, bỏ phiên bộ nhớ
     - 3 phiên x 5 lần gọi
     - ``bench/tier1_int8_CORE_0_sess{1,2,3}*``
   * - Probe
     - Hai lần ``eval_perf`` ở chế độ debug, phiên đầu tiên sau khi khởi động lại ``rknn_server``
     - 2 lần gọi
     - ``bench/extra_probe_debug_*``
   * - E1
     - Hai phiên ``eval_perf`` (``perf_debug=False``), 20 lần gọi mỗi phiên, kèm tần số in ra từng lần và bộ lấy mẫu 1 Hz trên board
     - 2 x 20
     - ``bench/extra_e1_*``
   * - Trên board, đợt liên tiếp
     - ``ai/board/rknn_perf_bench.c`` (C API, không qua PC), 3 tiến trình, 50 lần khởi động rồi 1000 lần chạy
     - 3 x 1000
     - ``bench/onboard/hot_*.csv``
   * - Trên board, ``detail``
     - Cùng chương trình với ``RKNN_FLAG_COLLECT_PERF_MASK`` và ``RKNN_QUERY_PERF_DETAIL``, bảng từng lớp mỗi lần chạy
     - 3 x 200
     - ``bench/onboard/detail_*_detail.txt``
   * - Trên board, nghỉ giữa các lần chạy
     - Nghỉ 2 giây và 10 giây sau mỗi lần ``rknn_run``
     - 40 và 20
     - ``bench/onboard/gap*.csv``
   * - E2 đến E2e
     - Thử ghim CPU, ngắt NPU và tắt trạng thái ngủ, năm thí nghiệm (:doc:`05-thu-ghim-cpu-va-ngat`)
     - 8 đến 40 khối mỗi thí nghiệm
     - ``bench/onboard_e2*/*``

Mọi bảng dưới đây sinh tự động bằng ``docs/tools/gen_latency_results_page.py`` từ ``results/latency_per_block_*.json``, ``results/layer_analysis_*.json``, ``results/onboard_*.json`` và các file ở cột "File". Thời gian từng lớp luôn là thời gian ở chế độ ``perf_debug=True`` (hoặc ``detail``), hãng ghi chế độ này có thể tắt một số cơ chế song song [T1 UG232 tr.177]. Vì vậy các con số từng khối dùng để so sánh với nhau, không cộng thành latency.

2. Latency tổng
===============

.. list-table::
   :header-rows: 1
   :widths: 26 14 24 10 26

   * - Nguồn
     - Trung vị (ms)
     - Nhỏ nhất đến lớn nhất (ms)
     - Số mẫu
     - Ghi chú
   * - B2, ``eval_perf``, 1 phiên
     - 19.238
     - 19.151 đến 19.244
     - 5
     - 5 lần gọi, ``perf_debug=False``
   * - B3 phiên 1, ``eval_perf``
     - 19.418
     - 19.293 đến 19.768
     - 5
     - 5 lần gọi, ``perf_debug=False``
   * - B3 phiên 2, ``eval_perf``
     - 22.352
     - 20.844 đến 22.774
     - 5
     - 5 lần gọi, ``perf_debug=False``
   * - B3 phiên 3, ``eval_perf``
     - 20.157
     - 18.423 đến 22.418
     - 5
     - 5 lần gọi, ``perf_debug=False``
   * - E1 phiên 1, ``eval_perf``
     - 19.881
     - 18.349 đến 20.365
     - 20
     - 20 lần gọi, ``perf_debug=False``
   * - E1 phiên 2, ``eval_perf``
     - 20.008
     - 18.337 đến 20.467
     - 20
     - 20 lần gọi, ``perf_debug=False``
   * - Trên board, C API, đợt 1
     - 19.195
     - 16.537 đến 22.134
     - 1000
     - chạy liên tiếp, ``rknn_run`` đo bằng đồng hồ CPU
   * - Trên board, C API, đợt 2
     - 18.994
     - 16.520 đến 22.129
     - 1000
     - chạy liên tiếp, ``rknn_run`` đo bằng đồng hồ CPU
   * - Trên board, C API, đợt 3
     - 20.911
     - 16.595 đến 22.179
     - 1000
     - chạy liên tiếp, ``rknn_run`` đo bằng đồng hồ CPU

Quan sát (T3 board, ``results/latency_per_block_*.md``, ``results/onboard_*.md``):

- Cùng một ``.rknn``, cùng tần số khoá, trung vị các phiên ``eval_perf`` lệch nhau 14.56% giữa B3 phiên 1, 2 và 3. Cổng A5 yêu cầu không quá 5%, không đạt.
- Hai nguồn đo khác nhau về bản chất và mức của chúng không trùng nhau. ``eval_perf`` lấy thời gian từ phần cứng board [T1 API232 tr.18], còn thời gian trên board là đồng hồ CPU quanh ``rknn_run``. Ở chương trình C, ``wall_us`` và ``RKNN_QUERY_PERF_RUN`` bằng nhau trong 5 µs ở mọi lần chạy (True), nên số này gồm cả phần driver. Quan hệ giữa hai nguồn chưa biết. Thử giãn nhịp chạy C API (X3) cho kết quả "chưa kết luận" về việc nhịp gọi có giải thích chênh lệch hay không (:doc:`06-co-che-cac-muc-do-tre`, mục 4).
- Tổng debug ở B2 (18.84 ms) thấp hơn latency (19.24 ms). Ở B3 tổng debug là 22.95, 23.40, 24.00 ms, cao hơn latency. Hãng ghi ``perf_debug=True`` làm thời gian lớn hơn [T1 UG232 tr.177]. Quan sát ở B2 ngược câu đó, nguyên nhân chưa biết (trên LAN, tổng debug thấp hơn latency ở 4/10 phiên không ghim và 0/10 phiên ghim, :doc:`07-giao-thuc-p2-va-do-mo-rong`, mục 3), và câu của hãng có thể nói về đại lượng khác (chưa kiểm).
- Cần báo latency như một khoảng kèm số mẫu và nguồn. Với model này ở ``CORE_0`` INT8, các nguồn trên cho trung vị từ 19.0 đến 22.4 ms và từng lần chạy từ 16.5 đến 22.2 ms.

3. Kết quả từng khối
====================

Cột "B3 (µs)" là trung vị thời gian khối ở chế độ debug qua 3 phiên B3 (mỗi phiên lấy trung vị 5 lần gọi). "Tỉ lệ" là phần thời gian của khối trên tổng thời gian các dòng trong cùng lần gọi. "Cận độ nhạy" là tỉ lệ sau khi trừ khỏi mỗi dòng có thời gian dương hằng số theo từng dòng của phiên (hệ số b của phép khớp Conv), chỉ là một cận để thấy khối có nhiều dòng nhỏ lệch bao nhiêu, không phải hiệu chỉnh. Ngoài tỉ lệ ở bảng, tỉ lệ khối trên board lấy từ 600 lần chạy ``detail``.

3.1. Bảng 1: khối L0 đến L22
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 8 8 9 9 9 9 10 10 12 9 10

   * - Khối
     - Số dòng
     - B3 (µs)
     - B2 (µs)
     - Tỉ lệ B3
     - Tỉ lệ B2
     - Tỉ lệ trên board
     - Cận độ nhạy
     - Lệch tỉ lệ giữa các phiên B3
     - GFLOPs
     - µs mỗi GFLOP
   * - L0
     - 1
     - 1993
     - 1911
     - 8.5%
     - 10.1%
     - 8.6%
     - 11.3%
     - 4.2%
     - 0.088
     - 22526
   * - L1
     - 1
     - 604
     - 565
     - 2.6%
     - 3.0%
     - 2.6%
     - 3.2%
     - 4.7%
     - 0.236
     - 2560
   * - L2
     - 7
     - 2732
     - 2442
     - 11.5%
     - 13.2%
     - 11.9%
     - 13.4%
     - 3.5%
     - 0.367
     - 7444
   * - L3
     - 1
     - 315
     - 314
     - 1.4%
     - 1.7%
     - 1.4%
     - 1.5%
     - 5.3%
     - 0.236
     - 1335
   * - L4
     - 10
     - 1792
     - 1435
     - 7.4%
     - 7.6%
     - 7.9%
     - 7.5%
     - 6.6%
     - 0.629
     - 2848
   * - L5
     - 1
     - 203
     - 164
     - 0.8%
     - 0.9%
     - 0.9%
     - 0.9%
     - 4.2%
     - 0.236
     - 860
   * - L6
     - 10
     - 1228
     - 831
     - 5.1%
     - 4.4%
     - 5.3%
     - 4.2%
     - 4.2%
     - 0.629
     - 1952
   * - L7
     - 1
     - 188
     - 149
     - 0.8%
     - 0.8%
     - 0.8%
     - 0.8%
     - 3.8%
     - 0.236
     - 797
   * - L8
     - 7
     - 714
     - 440
     - 3.0%
     - 2.3%
     - 3.1%
     - 2.1%
     - 4.2%
     - 0.367
     - 1945
   * - L9
     - 6
     - 529
     - 293
     - 2.2%
     - 1.6%
     - 2.2%
     - 1.3%
     - 4.3%
     - 0.131
     - 4036
   * - L10
     - 1
     - 113
     - 74
     - 0.5%
     - 0.4%
     - 0.5%
     - 0.4%
     - 4.4%
     - -
     - -
   * - L11
     - 1
     - 155
     - 114
     - 0.6%
     - 0.6%
     - 0.7%
     - 0.6%
     - 3.7%
     - -
     - -
   * - L12
     - 6
     - 828
     - 593
     - 3.4%
     - 3.2%
     - 3.6%
     - 3.1%
     - 4.2%
     - 0.472
     - 1755
   * - L13
     - 1
     - 166
     - 127
     - 0.7%
     - 0.7%
     - 0.7%
     - 0.7%
     - 4.1%
     - -
     - -
   * - L14
     - 1
     - 252
     - 208
     - 1.1%
     - 1.1%
     - 1.1%
     - 1.2%
     - 3.0%
     - -
     - -
   * - L15
     - 6
     - 1255
     - 1012
     - 5.3%
     - 5.4%
     - 5.5%
     - 5.3%
     - 3.3%
     - 0.472
     - 2660
   * - L16
     - 1
     - 142
     - 103
     - 0.6%
     - 0.5%
     - 0.6%
     - 0.5%
     - 12.3%
     - 0.118
     - 1204
   * - L17
     - 1
     - 106
     - 65
     - 0.4%
     - 0.3%
     - 0.5%
     - 0.3%
     - 23.7%
     - -
     - -
   * - L18
     - 6
     - 802
     - 563
     - 3.6%
     - 3.0%
     - 3.5%
     - 3.0%
     - 11.5%
     - 0.393
     - 2040
   * - L19
     - 1
     - 133
     - 91
     - 0.7%
     - 0.5%
     - 0.6%
     - 0.5%
     - 22.0%
     - 0.118
     - 1127
   * - L20
     - 1
     - 82
     - 42
     - 0.4%
     - 0.2%
     - 0.3%
     - 0.2%
     - 1.9%
     - -
     - -
   * - L21
     - 6
     - 649
     - 414
     - 2.8%
     - 2.2%
     - 2.8%
     - 2.1%
     - 10.2%
     - 0.393
     - 1650
   * - L22
     - 37
     - 7877
     - 6517
     - 34.0%
     - 34.6%
     - 33.2%
     - 34.4%
     - 2.1%
     - 2.965
     - 2656
   * - io
     - 2
     - 28
     - 21
     - 0.1%
     - 0.1%
     - 0.0%
     - 0.0%
     - 9.2%
     - -
     - -
   * - post_detect
     - 3
     - 435
     - 314
     - 1.8%
     - 1.7%
     - 1.9%
     - 1.6%
     - 8.7%
     - -
     - -

Độ tin cậy của tỉ lệ khối. Giữa năm nguồn (``eval_perf`` B3 trung vị, B2, trên board tính chung, trên board khi tổng lần chạy dưới 20 ms, từ 20 ms trở lên), một khối chiếm từ 2% thời gian trở lên chênh tối đa 2.2 điểm phần trăm (lớn nhất ở L22). Các khối nhỏ ở neck dao động nhiều hơn giữa các phiên B3: L18 (11.5%), L21 (10.2%) có độ lệch tỉ lệ vượt 10% (cổng A8). Hai khối nhỏ nhất theo thời gian, L17 và L20, lệch giữa các lần gọi trong một phiên tới 118% và 101%, nên xếp hạng giữa các khối nhỏ nằm trong nhiễu. Cột "Cận độ nhạy" cho thấy hằng số mỗi dòng ảnh hưởng không đều, phụ thuộc kích thước tương đối của các dòng trong khối: khối có dòng lớn tăng tỉ lệ (L0: 8.5% lên 11.3%, L2: 11.5% lên 13.4%), khối gồm các dòng nhỏ giảm (L9: 2.2% xuống 1.3%, L8: 3.0% xuống 2.1%, L20: 0.4% xuống 0.2%), còn L22 gần như không đổi (34.0% và 34.4%) vì thời gian của nó dồn vào vài dòng lớn.

3.2. Bảng 2: thành phần trong khối
----------------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 12 16 16 18 18

   * - Khối/thành phần
     - B3 (µs)
     - Tỉ lệ toàn mạng
     - Tỉ lệ trong khối
     - Lệch giữa các phiên
     - Lệch giữa các lần gọi
   * - L22/dfl
     - 3265
     - 14.1%
     - 41.4%
     - 0.2%
     - 6.4%
   * - L0/conv
     - 1993
     - 8.5%
     - 100.0%
     - 0.5%
     - 3.5%
   * - L22/decode
     - 1580
     - 6.8%
     - 20.1%
     - 13.2%
     - 50.8%
   * - L22/box_branch
     - 1435
     - 6.2%
     - 18.4%
     - 11.6%
     - 43.3%
   * - L22/cls_branch
     - 1399
     - 6.2%
     - 18.5%
     - 6.2%
     - 43.4%
   * - L2/bottleneck
     - 1130
     - 5.0%
     - 41.3%
     - 3.8%
     - 17.4%
   * - L4/bottleneck
     - 889
     - 3.7%
     - 49.7%
     - 0.1%
     - 31.4%
   * - L6/bottleneck
     - 654
     - 2.7%
     - 53.3%
     - 0.3%
     - 36.4%
   * - L1/conv
     - 604
     - 2.6%
     - 100.0%
     - 0.0%
     - 7.3%
   * - L2/cv2
     - 578
     - 2.4%
     - 21.1%
     - 6.4%
     - 7.4%
   * - L2/cv1
     - 553
     - 2.3%
     - 20.2%
     - 6.7%
     - 14.3%
   * - L15/cv1
     - 344
     - 1.5%
     - 27.5%
     - 0.3%
     - 11.6%
   * - L15/bottleneck
     - 345
     - 1.4%
     - 27.5%
     - 0.3%
     - 48.0%
   * - L3/conv
     - 315
     - 1.4%
     - 100.0%
     - 1.0%
     - 24.7%
   * - L4/cv2
     - 311
     - 1.3%
     - 17.4%
     - 0.0%
     - 13.2%
   * - L8/bottleneck
     - 316
     - 1.3%
     - 44.3%
     - 0.0%
     - 37.7%
   * - L15/cv2
     - 293
     - 1.3%
     - 23.3%
     - 12.6%
     - 32.0%
   * - L4/cv1
     - 286
     - 1.2%
     - 16.0%
     - 0.3%
     - 27.9%
   * - L18/bottleneck
     - 259
     - 1.2%
     - 31.5%
     - 17.0%
     - 47.9%
   * - L14/concat
     - 252
     - 1.1%
     - 100.0%
     - 0.4%
     - 15.9%
   * - L2/concat
     - 252
     - 1.1%
     - 9.2%
     - 1.2%
     - 16.9%
   * - L21/bottleneck
     - 248
     - 1.1%
     - 38.2%
     - 0.4%
     - 32.1%

Bảng đầy đủ {len(A['parts'])} thành phần nằm ở ``results/latency_per_block_ppe5_yolov8n_baseline_100ep_s0_int8_CORE_0.md``. Thành phần của L22 gồm ``box_branch`` và ``cls_branch`` (hai nhánh Conv), ``dfl`` (Softmax, Conv, Transpose và Reshape) và ``decode`` (các phép tính giải mã hộp).

3.3. Bảng 3: theo OpType
------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 10 12 12 18

   * - OpType
     - Số dòng
     - B3 (µs)
     - Tỉ lệ
     - Lệch giữa các phiên
   * - ConvExSwish
     - 57
     - 13513
     - 58.88%
     - 3.0%
   * - Concat
     - 17
     - 2341
     - 10.03%
     - 4.8%
   * - exSoftmax13
     - 1
     - 2114
     - 9.12%
     - 0.1%
   * - Split
     - 9
     - 1052
     - 4.58%
     - 7.3%
   * - Conv
     - 7
     - 884
     - 3.83%
     - 14.0%
   * - Transpose
     - 1
     - 837
     - 3.72%
     - 1.7%
   * - Add
     - 8
     - 787
     - 3.37%
     - 10.2%
   * - Reshape
     - 7
     - 520
     - 2.19%
     - 0.4%
   * - Resize
     - 2
     - 279
     - 1.16%
     - 0.0%
   * - MaxPool
     - 3
     - 220
     - 0.91%
     - 0.5%
   * - Mul
     - 2
     - 220
     - 0.96%
     - 19.1%
   * - Sub
     - 2
     - 214
     - 0.97%
     - 30.8%
   * - Sigmoid
     - 1
     - 126
     - 0.52%
     - 0.0%
   * - OutputOperator
     - 1
     - 19
     - 0.08%
     - 5.3%
   * - InputOperator
     - 1
     - 9
     - 0.04%
     - 11.1%

4. Cổng chấp nhận
=================

.. list-table::
   :header-rows: 1
   :widths: 8 12 80

   * - Mã
     - Kết quả
     - Chi tiết
   * - A1
     - đạt
     - build table 119 rows vs board table 119 rows, (OpType, FullName) sequence identical: True
   * - A2
     - đạt
     - 6 frequency reports equal to {'CPU': [1800000, 2256000, 2304000], 'NPU': [1000000000], 'DDR': [2112000000]}
   * - A3
     - đạt
     - NPU rows (not Reshape) with time > 0 and WorkLoad != 100.0%/0.0%/0.0%: []
   * - A4
     - đạt
     - rows outside model.N or with an unknown part: [('io', 'InputOperator'), ('io', 'OutputOperator'), ('post_detect', 'Concat'), ('post_detect', 'Mul'), ('post_detect', 'Reshape')]
   * - A5
     - không đạt
     - latency gap between 3 sessions 14.56% (max 5%)
   * - A6
     - đạt
     - sum of block shares 0.9931, sum_ratio min/max per session [[1.0, 1.0], [1.0, 1.0], [1.0, 1.0]], debug_ratio 1.161
   * - A8
     - không đạt
     - sessions only: debug total gap 4.53% (max 5%), blocks with share >= 2% whose share spread exceeds 10%: {'L18': 0.115, 'L21': 0.102}
   * - A8+B2
     - không đạt
     - with the dry run: debug total gap 22.28%, blocks over 10%: {'L0': 0.215, 'L1': 0.185, 'L2': 0.143, 'L6': 0.163, 'L8': 0.243, 'L9': 0.321, 'L12': 0.108, 'L18': 0.253, 'L21': 0.303}
   * - A7
     - đạt
     - provenance keys ('model_sha256', 'git_commit', 'git_dirty', 'sdk_version') present in every session file

Cách đọc. A5 và A8 không đạt, kể cả khi chỉ xét ba phiên B3. Cổng A8 báo hai cách: chỉ các phiên đánh số, và tính B2 như một phiên (tổng debug lệch 22.28%, 9 khối vượt 10%). Không đổi ngưỡng để cổng đạt (ngưỡng đã duyệt ngày 2026-10-30: 5% và 10%). Hệ quả cho cách báo: latency tuyệt đối báo dưới dạng khoảng kèm nguồn và số mẫu (mục 2), tỉ lệ khối báo kèm cột lệch giữa các phiên, và chỉ xếp hạng các khối lớn. Đọc theo cổng gốc (qua relay): FP16 chưa chạy vì A8 của INT8 không đạt (theo quy tắc của kế hoạch, FP16 chỉ chạy sau khi INT8 ổn định, và phải xen kẽ INT8 và FP16 để lệch giữa phiên không bị nhầm là hiệu ứng kiểu dữ liệu). Chạy lại ba phiên A5 và A8 khi ghim lõi sẽ là một giao thức mới, không làm cổng A8 gốc đạt.

5. Điều chưa biết và giới hạn
=============================

- Quan hệ giữa thời gian ``eval_perf`` (từ phần cứng) và thời gian ``rknn_run`` trên board (gồm driver), vì hai nguồn cho mức khác nhau.
- ``CORE_0_1_2``, FP16 và độ chính xác sau INT8 đã đo ngày 2026-10-31 dưới giao thức P2 trên LAN (:doc:`07-giao-thuc-p2-va-do-mo-rong`). Số liệu vẫn chỉ cho một model (một seed) trên một board.

6. Nguồn
========

- T1: ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (UG232 tr.177), ``docs/_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf`` (API232 tr.18), ``3rdparty/rknn-toolkit2/rknpu2/runtime/Linux/librknn_api/include/rknn_api.h`` (``RKNN_FLAG_COLLECT_PERF_MASK``, ``RKNN_QUERY_PERF_DETAIL``, ``RKNN_QUERY_PERF_RUN``).
- T3 board và PC: ``results/latency_per_block_*``, ``results/layer_analysis_*``, ``results/onboard_*``, ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/``, ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/export_int8.json``. Mã: ``ai/board/rknn_perf_bench.c``, ``ai/automation/aggregate_layers.py``, ``analyze_layers.py``, ``analyze_onboard.py``, ``ai/core/rknn/blocks.py``, ``tests/test_layer_blocks.py``.

