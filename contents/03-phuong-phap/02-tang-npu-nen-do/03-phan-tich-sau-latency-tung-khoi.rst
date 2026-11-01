***********************
Phân tích sâu từng khối
***********************

.. admonition:: Trang này trả lời

   - Conv, op không phải Conv và chuỗi DFL tốn thời gian ra sao so với ước tính cycles của compiler và so với GFLOPs?
   - Chi phí cố định mỗi dòng của bảng từng lớp là bao nhiêu và khác nhau giữa các phiên thế nào?

.. admonition:: Tóm tắt

   - Chuỗi DFL (Reshape, Softmax, Conv, Transpose) tốn 3.25 ms, tức 14.1% thời gian debug, trong khi GFLOPs gần bằng 0. Ngoài ``InputOperator`` và ``OutputOperator``, ``Transpose`` là op duy nhất chạy trên CPU.
   - Các op không phải Conv tốn 37.6% thời gian debug. Conv chạy lâu hơn ước tính cycles của compiler trung vị 2.66 lần (khoảng 1.35 đến 38.8).
   - Giữa các phiên, mỗi dòng của bảng từng lớp bị cộng thêm khoảng 35 đến 42 µs so với B2, gần như không phụ thuộc kích thước (R2 không quá 0.06). Hệ số theo cycles của Conv giữ ở 1.818 đến 1.819 giữa các đợt trên board.

Phân tích trên ba phiên B3 ở chế độ debug (tổng 23.11 ms), kết quả tổng hợp ở :doc:`02-ket-qua-latency-tung-khoi` và dao động ở :doc:`04-cac-muc-do-tre`. "Ước tính cycles" là ``Total cycles`` chia 1000 µs, tức ước tính của compiler ở xung NPU 1 GHz đã khoá, không phải giới hạn phần cứng. Trang này lấy trung vị từng dòng (trung vị 5 lần gọi, rồi trung vị 3 phiên) nên lệch nhẹ so với bảng ở :doc:`02-ket-qua-latency-tung-khoi`, vốn cộng khối trong từng lần gọi rồi lấy trung vị. Ví dụ khối L22 là 33.2% ở đây và 34.0% ở trang kết quả, và ``Concat`` là 2336 µs ở đây và 2341 µs ở trang kết quả.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Conv so với ước tính cycles của compiler
===========================================

64 dòng Conv (có ``NPUCycles`` khác 0) dùng 14.43 ms, 62.4% thời gian, so với 5.67 ms ước tính. Tỉ số thời gian trên ước tính trung vị 2.66, nhỏ nhất 1.35, lớn nhất 38.8. Phép khớp bình phương tối thiểu ``time = 1.960 x est. + 51.8 µs`` có R2 0.873 (khớp mô tả trên 64 dòng, không phải mô hình phần cứng). Số dòng Conv có chu kỳ DDR lớn hơn chu kỳ NPU: 1.

.. list-table::
   :header-rows: 1
   :widths: 20 12 20 20

   * - Dải tỉ số
     - Số dòng
     - Thời gian (µs)
     - Ước tính (µs)
   * - <= 1.5
     - 4
     - 1258
     - 922
   * - 1.5 - 3
     - 32
     - 7911
     - 3603
   * - 3 - 6
     - 22
     - 4708
     - 1080
   * - > 6
     - 6
     - 548
     - 62

Dải 1.5 đến 3 lần ước tính chứa 32 trên 64 dòng Conv và 55% thời gian Conv. Sáu dòng ở dải trên 6 lần rất nhỏ (tổng 548 µs) và đều là Conv 1x1: bốn dòng là Conv 1x1 cuối của nhánh box và cls ở L22 (``cv2.1.2``, ``cv3.1.2``, ``cv2.2.2``, ``cv3.2.2``), hai dòng là ``cv1`` của L6 và L9. Số liệu từng dòng nằm ở ``results/layer_analysis_*.md``. Vì sao Conv lớn đạt gần ước tính nhất còn Conv nhỏ lệch xa là điều chưa có nguồn T1 hoặc T2 trong repo, nên không giải thích ở đây.

2. Các dòng không phải Conv
===========================

8.68 ms, 37.6% tổng thời gian debug, không có ``NPUCycles`` nên cột cycles của compiler không phản ánh chúng. Phép khớp trên 34 dòng ``Concat``, ``Split`` và ``Add`` cho ``time = 144 µs mỗi MB đọc ghi + 68.4 µs`` (R2 0.71), nghĩa là phần lớn thời gian của các dòng này là hằng số mỗi dòng.

.. list-table::
   :header-rows: 1
   :widths: 18 10 14 10 10 12

   * - OpType
     - Số dòng
     - Thời gian (µs)
     - Tỉ lệ
     - RW (KB)
     - µs mỗi MB
   * - Concat
     - 17
     - 2336
     - 10.11%
     - 7530
     - 318
   * - exSoftmax13
     - 1
     - 2114
     - 9.15%
     - 525
     - 4123
   * - Split
     - 9
     - 1029
     - 4.45%
     - 2531
     - 416
   * - Transpose
     - 1
     - 837
     - 3.62%
     - 525
     - 1633
   * - Add
     - 8
     - 746
     - 3.23%
     - 2624
     - 291
   * - Reshape
     - 7
     - 517
     - 2.24%
     - 943
     - 561
   * - Resize
     - 2
     - 279
     - 1.21%
     - 300
     - 952
   * - Sub
     - 2
     - 225
     - 0.97%
     - 524
     - 440
   * - Mul
     - 2
     - 225
     - 0.97%
     - 393
     - 586
   * - MaxPool
     - 3
     - 219
     - 0.95%
     - 150
     - 1495
   * - Sigmoid
     - 1
     - 126
     - 0.55%
     - 131
     - 985
   * - OutputOperator
     - 1
     - 19
     - 0.08%
     - 73
     - 267
   * - InputOperator
     - 1
     - 9
     - 0.04%
     - 0
     - -

3. Chuỗi DFL và giải mã ở đầu Detect
====================================

L22 cộng ``post_detect`` chiếm 8.11 ms (35.1%). Riêng chuỗi DFL (theo thứ tự đồ thị) như sau, tổng 3.25 ms, 14.1%. Trên board, bảng ``detail`` cho DFL 2.93 ms (trung vị ba đợt).

.. list-table::
   :header-rows: 1
   :widths: 10 20 12 16

   * - ID
     - OpType
     - Target
     - Thời gian (µs)
   * - 101
     - Reshape
     - NPU
     - 2
   * - 102
     - exSoftmax13
     - NPU
     - 2114
   * - 103
     - Conv
     - NPU
     - 294
   * - 104
     - Transpose
     - CPU
     - 837

``Softmax`` (``exSoftmax13``) trên NPU chiếm phần lớn. ``Transpose`` chạy trên CPU (Target CPU), là op duy nhất không chạy trên NPU ngoài ``InputOperator`` và ``OutputOperator`` ở đồ thị này. Cấu trúc DFL của YOLOv8 (softmax trên 16 bin rồi nhân với 0, 1, ..., 15) đã mô tả ở :doc:`../01-tang-ai/02-kien-truc-model`. Các thành phần của L22 theo thời gian (B3): dfl 3.25 ms, decode 1.58 ms, box_branch 1.44 ms, cls_branch 1.41 ms.

4. Tỉ lệ thời gian so với tỉ lệ GFLOPs
======================================

.. list-table::
   :header-rows: 1
   :widths: 26 16 16 18 16

   * - Giai đoạn
     - Thời gian (µs)
     - Tỉ lệ thời gian
     - GFLOPs (Conv2d)
     - Tỉ lệ GFLOPs
   * - backbone L0-L9
     - 10257
     - 44.4%
     - 3.156
     - 39.0%
   * - neck L10-L21
     - 4707
     - 20.4%
     - 1.966
     - 24.3%
   * - head L22
     - 7678
     - 33.2%
     - 2.965
     - 36.7%
   * - io and post_detect
     - 464
     - 2.0%
     - 0.000
     - 0.0%

Backbone chiếm 44.4% thời gian so với 39.0% GFLOPs. Neck chiếm 20.4% so với 24.3%, và head chiếm 33.2% so với 36.7%. Phần ``io`` và ``post_detect`` (2.0%) không có GFLOPs. GFLOPs chỉ đếm Conv2d (xem trang kiến trúc), không đếm ``Concat``, ``Split``, ``Add`` và các op khác, nên tỉ lệ GFLOPs không dự đoán được thời gian. Vì sao backbone cao hơn còn neck và head thấp hơn chưa có nguồn để giải thích.

5. Chi phí cố định mỗi dòng, khác nhau giữa các phiên
=====================================================

So từng phiên B3 với B2 trên 119 dòng, hồi quy hiệu thời gian theo hằng số, ước tính cycles và RW (KB):

.. list-table::
   :header-rows: 1
   :widths: 8 14 22 14 18 12 8

   * - Phiên
     - Tổng chênh (µs)
     - Chênh trung bình mỗi dòng (µs)
     - Hằng số (µs)
     - Theo ước tính cycles
     - µs mỗi MB
     - R2
   * - 1
     - 4344
     - 36.5
     - 34.6
     - 0.016
     - 3.6
     - 0.027
   * - 2
     - 4485
     - 37.7
     - 36.1
     - 0.031
     - 0.4
     - 0.056
   * - 3
     - 5257
     - 44.2
     - 41.6
     - 0.045
     - 1.2
     - 0.056

Chênh lệch giữa các phiên là một hằng số khoảng 35 đến 42 µs mỗi dòng, hệ số theo kích thước gần bằng 0. Hằng số mỗi dòng của từng phiên (hệ số b của phép khớp Conv) là 50.7, 50.3, 57.2 µs ở ba phiên B3 và 15.8 µs ở B2. Trên board, ba đợt ``detail`` cho 50.6, 21.6, 59.0 µs. Hệ quả: tổng debug và tỉ lệ khối bị lệch theo số dòng của khối, như đã nêu ở :doc:`02-ket-qua-latency-tung-khoi` (mục 3.1). Nguyên nhân của hằng số này chưa biết.


6. Điều chưa biết
=================

- Nguyên nhân của hằng số mỗi dòng ở chế độ debug và vì sao nó khác nhau giữa các phiên (mục 5). X4 đo được liên hệ với việc ghim lõi: dưới P2 hằng số khoảng 5 µs và chênh 0.3 µs giữa 10 phiên, không ghim thì 8 đến 52 µs (:doc:`08-ket-qua-p2-va-do-mo-rong`, mục 3). Nguyên nhân vẫn chưa biết.
- Vì sao Conv lớn gần ước tính cycles còn Conv nhỏ lệch xa (mục 1). Nguồn hãng chỉ nói hiệu suất MAC phụ thuộc kích thước: "The utilization rate decreases when the Height * Width of the output Tensor < 16." [T1 UG232 tr.147], không nói chi phí cố định mỗi lớp. Phân tích lại dữ liệu B3 (X10, quy tắc ``bench/analysis_x10/rule.txt`` viết trước khi tính, ngưỡng 20% là số mới, chưa qua người dùng duyệt): 5 trên 6 dòng Conv nhỏ khớp mô hình thời gian = a × ước tính + b trong 20%, riêng dòng ``model.6/cv1`` đo 174 µs so với dự đoán 102 µs, nên "chưa kết luận". Vẫn chưa biết. Từ khóa đề xuất: "NPU per-layer launch overhead small convolution", "RKNN layer scheduling overhead".
- Vì sao tỉ lệ thời gian của backbone cao hơn tỉ lệ GFLOPs còn neck và head thấp hơn (mục 4). X10 bỏ hằng số mỗi dòng ra khỏi tỉ lệ thời gian: khoảng cách của backbone đổi từ 0.054 thành 0.071, neck từ -0.039 thành -0.066, head từ -0.034 thành -0.022, nên "chưa kết luận". Trong các nguồn đã tìm (UG232, API232, RKNNRT, tài liệu operator, bài báo ``edgesoc_benchmark_2026kong.pdf``, xem ``tmp/2026-10-31_latency-sources-facts.md``, câu hỏi Q8), không có câu nào nói thời gian NPU của Concat, Split, Add không theo FLOPs. Vẫn chưa biết.

7. Nguồn
=========

T3 board và PC: ``results/layer_analysis_*``, ``results/latency_per_block_*``, ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/tier1_int8_CORE_0*``. Mã: ``ai/automation/analyze_layers.py``, ``ai/core/rknn/blocks.py``, ``ai/automation/analyze_x10.py`` (X10, ``results/analysis_x10_*``). T1: ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (UG232 tr.147).

