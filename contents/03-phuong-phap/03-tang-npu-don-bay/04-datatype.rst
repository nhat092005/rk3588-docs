********
Datatype
********

.. admonition:: Trang này trả lời

   - Model triển khai của dự án dùng kiểu số nào, cái giá về độ chính xác và latency của từng lựa chọn (FP16, INT8 mặc định, ``int8h5``, tách đầu) là bao nhiêu?
   - Kiểu số vào và ra mà runtime thật sự thấy là gì, và chỗ nào các nguồn mâu thuẫn nhau?
   - Kiểu số có đòn bẩy FPS nào, đòn bẩy nào đã đo, đòn bẩy nào chỉ có nguồn, đòn bẩy nào chưa biết?

.. admonition:: Tóm tắt

   1. Bốn lựa chọn đã đo trên ``css_test`` (AP50-95, SiLU, seed 0): FP16 49.76, INT8 mặc định 36.75, ``int8h5`` 49.66, A1 tách đầu 49.84. Latency NPU ở ``CORE_0``: FP16 khoảng 27.3 ms, INT8 mặc định khoảng 16.5 ms, ``int8h5`` 16.442 ms, A1 chỉ phần NPU 13.070 ms (số lấy ở :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa` và :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`).
   2. Cấu hình build của repo không đặt ``quantized_dtype``, ``quantized_method`` hay ``pass_through``, nên dùng mặc định của toolkit (``w8a8``, ``channel``). Tài liệu API liệt kê nhiều kiểu hơn, sổ tay SDK chỉ nói INT8, mâu thuẫn này chưa giải quyết [T1 API232 tr.7] [T1 UG232 tr.121].
   3. ``int8h5`` đưa 15 tensor FLOAT16 vào đồ thị và sinh op ``exDataConvert``. Ở ReLU ``h5`` bảng layer ghi 2 lần gọi, 332 us, 3.69% thời gian một khung. Vendor nói các op chuyển đổi này làm tăng latency [T1 UG232 tr.130].
   4. Kiểu số lúc chạy mâu thuẫn giữa các log: bảng layer của ``eval_perf`` ghi đầu vào UINT8, thuộc tính tensor của runtime ghi INT8 (zp -128, scale 0.003922). Chưa có lời giải thích. Không log nào của repo có tensor vào hoặc ra FLOAT16.
   5. Thông lượng của ``int8h5`` so với INT8 mặc định dưới P3 (thí nghiệm E1): chênh từ -0.01% đến 0.68% ở bốn cấu hình, kết luận "không phân biệt được". Chi tiết ở :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.
   6. Bốn đòn bẩy: D1 FP16 (ĐO, chậm), D2 INT8 mặc định (ĐO, mất 13 điểm), D3 ``int8h5`` (ĐO, model chuẩn), D4 tách đầu (ĐO gộp), D5 kiểu thấp hơn INT8 (CHƯA BIẾT).

Phần lý thuyết ở :doc:`../../01-kien-thuc-nen/03-luong-tu-hoa/01-luong-tu-hoa-affine-va-granularity`, kiến thức toolkit ở :doc:`../../02-nen-tang-rk3588/02-rknn-luong-tu-hoa/01-kieu-du-lieu-va-cau-hinh-luong-tu-hoa`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Phạm vi và liên kết
======================

Trang này không giải thích lại công thức affine, scale và zero-point, per-channel hay per-layer, hay danh sách ``quantized_dtype`` của toolkit. Các phần đó đã có ở :doc:`../../01-kien-thuc-nen/03-luong-tu-hoa/01-luong-tu-hoa-affine-va-granularity`, :doc:`../../01-kien-thuc-nen/03-luong-tu-hoa/02-chien-luoc-ptq-qat-va-hon-hop` và :doc:`../../02-nen-tang-rk3588/02-rknn-luong-tu-hoa/01-kieu-du-lieu-va-cau-hinh-luong-tu-hoa`. Cách đo sai số lượng tử và vì sao SiLU làm lệch phân bố activation ở :doc:`../../01-kien-thuc-nen/03-luong-tu-hoa/03-phan-tich-sai-so-va-dac-thu-yolo`. Chẩn đoán từng lớp và công thức ``h5`` ở :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa`, kết quả tách đầu và QAT ở :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`.

Trang này chỉ gom ba thứ cho quyết định chọn kiểu số: các lựa chọn đã đo cạnh nhau, kiểu số mà build và runtime thật sự ghi, và các đòn bẩy FPS liên quan. Bố cục dữ liệu (NHWC và NC1HWC2) ở :doc:`03-tensor-layout`, bộ nhớ ở :doc:`05-memory-access` và :doc:`06-memory-copy`.

Mục tiêu FPS của người dùng là 30 FPS, đổi từ 60 ngày 2026-11-08 vì camera chỉ có 30 khung/giây (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8). Hiểu là một luồng camera, ngân sách 33.33 ms mỗi khung. Mọi cấu hình đã đo đạt mốc này theo cả thông lượng lẫn thời gian mỗi khung. Trang này đọc mỗi lựa chọn theo số đo của nó.

2. Các lựa chọn đã đo
=====================

Bảng dưới ghi mỗi số kèm trang nguồn. Mọi số là SiLU, seed 0, một board, và AP50-95 trên ``css_test`` (82 ảnh). Cột latency là thời gian NPU một khung ở ``CORE_0`` (không gồm tiền và hậu xử lý), nên không so được trực tiếp với FPS của harness ở :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`.

.. list-table::
   :header-rows: 1
   :widths: 22 14 22 42

   * - Lựa chọn
     - AP50-95
     - Latency NPU CORE_0 (ms)
     - Nguồn
   * - FP16
     - 49.76
     - 27.267 đến 27.284 (ba phiên)
     - AP: :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa` tóm tắt. Latency: [T3 board, ``experiments/npu/latency/onboard_x8/fp16/tier1_fp16_CORE_0_sess{1,2,3}.json``]
   * - INT8 mặc định
     - 36.75
     - 16.507 và 16.516 (hai phiên, ``onboard_g4b``). Trong lần chạy xen kẽ của :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`: 16.520
     - AP: :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa` tóm tắt. Latency: [T3 board, ``experiments/npu/operator_support/onboard_g4b/ppe5_yolov8n_baseline_100ep_s0/tier1_int8_CORE_0_sess{1,2}.json``]
   * - ``int8h5`` (chuẩn)
     - 49.66
     - 16.442
     - AP: :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa` tóm tắt. Latency: :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc` mục 2 (P2 thực hiện đúng)
   * - A1 tách đầu (INT8 thuần)
     - 49.84
     - 13.070, chỉ phần NPU
     - :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc` mục 2. Giải mã box trên CPU thêm 8.02 ms (một đo riêng, dữ liệu ngẫu nhiên)

Ba nhận xét, đều chỉ là mô tả số đo.

- INT8 mặc định rẻ nhất về thời gian trong ba model dựng từ cùng đồ thị, nhưng mất 13.01 điểm AP50-95 so với FP16 (:doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa` tóm tắt).
- ``int8h5`` lấy lại gần hết điểm mà latency NPU đổi dưới 5%: SiLU ``CORE_0`` từ 16.530 xuống 16.410 ms (-0.121 ms), ``CORE_0_1_2`` từ 16.017 xuống 15.937 ms (-0.081 ms) [T3 board, :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa` mục 6].
- A1 nhanh hơn ở phần NPU nhưng cộng giải mã CPU thì tổng chậm hơn khoảng 4.65 ms nếu không chồng lấp. Mọi so sánh thời gian của A1 mang nhãn "chưa kết luận" vì hai phiên tham chiếu INT8 không thực hiện đúng dưới P2 (:doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc` tóm tắt).

Ở lớp cuối, chẩn đoán 10 ảnh cho thấy ``h5`` giữ tensor ``output0`` gần đồ thị float: ``mean_entire_cos`` 0.99947900, ``mean_class_cos`` 0.99087 và ``mean_box_cos`` 0.99953 ở SiLU, ``mean_class_cos`` 0.97819 ở ReLU [T3 board, ``results/npu/operator_support/q2c_diag.json``]. Đây là sai số so với đồ thị float, không phải mAP.

3. Cấu hình dtype của build
===========================

Cấu hình build trong repo chỉ đặt chuẩn hóa và nền tảng: ``cfg = dict(mean_values=[[0, 0, 0]], std_values=[[255, 255, 255]], target_platform="rk3588")`` [Mã nguồn repo ``ai/npu/operator_support/build_recipe.py:64``, ``ai/core/rknn/hybrid.py:64``]. Đã tìm ``quantized_dtype``, ``quantized_method`` và ``pass_through`` trong mã của ``ai/``, không có kết quả. Build lai chỉ thêm ``custom_quantize_layers`` với giá trị ``float16`` cho các tensor được chọn: ``q["custom_quantize_layers"] = {k: "float16" for k in layers}`` [Mã nguồn repo ``ai/core/rknn/hybrid.py:71``].

Giá trị mặc định mà toolkit áp dụng khi repo không đặt:

.. list-table::
   :header-rows: 1
   :widths: 22 24 54

   * - Tham số
     - Mặc định
     - Nguồn
   * - ``quantized_dtype``
     - ``w8a8``
     - [T1 API232 tr.7]
   * - ``quantized_method``
     - ``channel``
     - [T1 API232 tr.8]
   * - ``quantized_algorithm``
     - ``normal``
     - "Currently support: normal, mmse, kl_divergence and gdq." [T1 API232 tr.8]
   * - ``float_dtype``
     - ``float16``
     - "currently supported are float16. The default value is float16." [T1 API232 tr.8]

Về phạm vi áp dụng, vendor nêu per-channel chỉ áp dụng cho trọng số, activation và giá trị trung gian dùng per-layer [T1 UG232 tr.120] (trích dẫn nguyên văn ở trang nền :doc:`../../02-nen-tang-rk3588/02-rknn-luong-tu-hoa/01-kieu-du-lieu-va-cau-hinh-luong-tu-hoa`). Nghĩa là model INT8 của dự án có trọng số per-channel và activation per-layer.

Mâu thuẫn giữa hai tài liệu T1: danh sách ``quantized_dtype`` của API232 có thêm ``w4a16``, ``w8a16``, ``w16a16i`` và các kiểu khác, mỗi kiểu kèm giới hạn nền tảng [T1 API232 tr.7], còn sổ tay SDK chỉ nêu INT8 [T1 UG232 tr.121 và tr.22]. Trang :doc:`../../02-nen-tang-rk3588/02-rknn-luong-tu-hoa/01-kieu-du-lieu-va-cau-hinh-luong-tu-hoa` đã đối chiếu hai tài liệu này và trích nguyên văn, nên trang này không lặp lại. Điều dự án cần: kiểu nào ngoài INT8 chạy được trên RK3588 theo bảng giới hạn nền tảng thì chưa xác định (mục 7).

4. exDataConvert và tensor FLOAT16
====================================

Khi một tensor FLOAT16 nằm giữa các toán tử INT8, compiler chèn op đổi kiểu. Vendor mô tả cơ chế này ở ví dụ mô hình QAT: "exDataConvert is inserted before exGelu and a quantization operator exDataConvert is inserted after Softmax." [T1 UG232 tr.130]. Hệ quả theo vendor: "These inserted quantization and dequantization operators will introduce additional latency." [T1 UG232 tr.130]. Bảng toán tử của vendor có mục ``4.77 exDataConvert`` với mô tả "精度转换" (chuyển đổi độ chính xác) và không có công thức [T1 OPL tr.330].

Số đo của dự án:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Quan sát
     - Nguồn
   * - Log build ``h5`` có 4 dòng chứa chữ ``exDataConvert``, tên layer có hậu tố ``__cvt_int8_float16``. Log baseline có 0 dòng
     - [T3 board, ``experiments/npu/operator_support/onboard_q2c/logs/build_ppe5_yolov8n_baseline_100ep_s0_h5.log:422, :439``]
   * - Số dòng theo công thức: ``auto`` 20, ``h1`` 12, ``h2`` 12, ``h3`` 8, ``h4`` 16, ``h5`` 4, ``h6`` 16. ``base``, ``c_all``, ``kl``, ``split_int8``, ``split_fp16`` đều 0
     - [T3 board, đếm dòng bằng ``grep -c`` trong cùng thư mục logs]
   * - ReLU ``h5`` ``CORE_0_1_2`` phiên 1: hàng ``exDataConvert`` có 2 lần gọi, 332 us, 3.69% thời gian một khung
     - [T3 board, ``experiments/npu/operator_support/onboard_q2i/ppe5_yolov8n_relu_100ep_s0/tier1_int8h5_CORE_0_1_2_sess1_layers.txt:146``]
   * - Đồ thị QAT có 8 hàng FLOAT16 trên NPU, A1 tách đầu có 0 (106 hàng INT8)
     - :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc` mục 2 và 3

Số dòng ở bảng trên là số dòng văn bản, không phải số hàng bảng layer. Chi phí 332 us chỉ có cho một phiên của ReLU. Chi phí đổi kiểu của model SiLU ``h5`` trong bảng layer chưa được trích riêng ở trang này (xem mục 7). Vì vậy chỉ rút ra được hai điều: phần chi phí chuyển đổi có thật và chiếm 3.69% một khung ở hàng ReLU đã trích, và độ lệch latency của ``h5`` so với INT8 triển khai dưới 5% ở cả bốn hàng của :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa` mục 6.

5. Kiểu vào và ra lúc chạy
==========================

Có ba nhóm quan sát về kiểu số ở biên của model, và chúng không khớp hoàn toàn.

.. list-table::
   :header-rows: 1
   :widths: 24 38 38

   * - Nơi ghi
     - Đầu vào ``images``
     - Đầu ra ``output0``
   * - Bảng layer ``eval_perf`` trên board
     - ``InputOperator`` UINT8, đích CPU, ``(1,3,640,640)`` [T3 board, ``bench/tier1_int8_CORE_0_layers.txt:15``]
     - ``OutputOperator`` INT8, đích CPU [T3 board, ``bench/tier1_int8_CORE_0_layers.txt:133``]
   * - Thuộc tính tensor của runtime (``driver_stdout``)
     - INT8, AFFINE, zp -128, scale 0.003922, dims ``[1, 640, 640, 3]`` [T3 board, ``experiments/npu/latency/onboard_x4/driver_stdout.txt:20``]
     - INT8, AFFINE, zp -128, scale 0.004099, dims ``[1, 9, 8400]`` [T3 board, ``experiments/npu/latency/onboard_x4/driver_stdout.txt:22``]
   * - Bảng layer lúc build
     - INT8 (``build_..._base.log:292``, ``build_..._h5.log:322``)
     - FLOAT16 ở log ``h5`` (:doc:`03-tensor-layout` mục 2)

Ghi chú về cách đọc.

- Mâu thuẫn UINT8 (bảng layer ``eval_perf``) và INT8 (runtime và bảng layer build) là có thật. UINT8 chỉ xuất hiện ở bảng layer của ``eval_perf`` trên board, có thể do ``eval_perf`` cấp đầu vào uint8, nhưng đó là phỏng đoán chưa kiểm. Lý do: chưa biết.
- Wheel RKNNLite 2.3.2 có tham số ``data_type`` của ``inference`` với chữ ký mặc định ``None`` và docstring ghi mặc định ``uint8`` [T3 board, ``rknn_lite.py:193`` và ``:197`` trong wheel ``rknn_toolkit_lite2-2.3.2``]. Harness Python của repo gọi ``inference(inputs=[inp])`` không đặt ``data_type`` (:doc:`03-tensor-layout` mục 2).
- Trong toàn bộ ``experiments/runs/*/bench/**/driver_stdout.txt`` có 0 file ghi ``type=FLOAT16``. Repo chưa có log nào cho thấy đầu vào hoặc đầu ra FP16 lúc chạy [T3 board, grep].
- Kiểu tensor của runtime gồm cả lượng tử bất đối xứng với scale và zp (``RKNN_TENSOR_QNT_AFFINE_ASYMMETRIC``) [T1 RKNNRT tr.12]. Điều này khớp với ``qnt_type=AFFINE`` của log.

Hệ quả cho quyết định: đường FP16 vào và ra chưa từng được chạy trong repo, nên không có số FPS nào cho nó (mục 7).

6. Đòn bẩy từ kiểu số
=====================

Nhãn trạng thái: ĐO (có số đo T3), NGUỒN (chỉ có tài liệu hoặc mã), CHƯA BIẾT. Ngưỡng số mới của từng thí nghiệm vẫn chưa duyệt, nên cột bằng chứng chỉ ghi số và không kết luận đạt hay không đạt.

.. list-table::
   :header-rows: 1
   :widths: 8 24 12 56

   * - Mã
     - Đòn bẩy
     - Nhãn
     - Bằng chứng và giới hạn
   * - D1
     - Dùng FP16 cho toàn model
     - ĐO
     - Latency NPU ``CORE_0`` khoảng 27.3 ms, ``fps_latency`` 36.65, 36.65, 36.67 [T3 board, ``experiments/npu/latency/onboard_x8/fp16/``]. Con số này đã thấp hơn 60 trước khi cộng tiền và hậu xử lý. Chỉ đo một context. FP16 nhiều context chưa đo. Độ chính xác 49.76 so với 49.66 của ``int8h5``
   * - D2
     - INT8 mặc định, không lai
     - ĐO
     - NPU 16.507 và 16.516 ms (``fps_latency`` 60.58 và 60.55) nhưng mất 13.01 điểm AP50-95 (:doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa`). Đây là cận trên NPU một context, không phải FPS của pipeline (54.7 FPS, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8)
   * - D3
     - ``int8h5`` (model chuẩn)
     - ĐO
     - Độ chính xác về mức FP16 (49.66 so với 49.76). Thông lượng dưới P3 không khác INT8 mặc định ở E1 (bảng dưới)
   * - D4
     - Tách đầu A1, đồ thị NPU INT8 thuần
     - ĐO gộp
     - NPU nhanh hơn ``int8h5`` khoảng 3.4 ms (13.070 so với 16.442 ms), giải mã CPU 8.02 ms. Đóng góp của riêng kiểu số không tách khỏi việc bỏ Transpose và đuôi giải mã. Xem :doc:`07-compiler-optimization`, :doc:`09-pre-post-processing`, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`
   * - D5
     - Kiểu thấp hơn INT8 (``w4a16``, ``w4a8``) hoặc rộng hơn (``w16a16i``)
     - CHƯA BIẾT
     - Chỉ có danh sách và giới hạn nền tảng ở [T1 API232 tr.7], sổ tay SDK chỉ nói INT8 [T1 UG232 tr.121]. Không dựng, không đo

E1, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`. Thí nghiệm E1 đo thông lượng của ``int8h5`` so với INT8 mặc định dưới P3 (giao thức đã duyệt, :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`), cùng harness ``bench_throughput_rep.py``, 1238 frame, trung vị ba lần chạy. Tần số khóa trong lúc đo: ``npu: userspace 1000000000 Hz`` và ``ddr: userspace 2112000000 Hz`` [T3 board, ``results/npu/throughput/q2f_fps.json`` trường ``hold_progress`` của E1]. Kết quả (FPS):

.. list-table::
   :header-rows: 1
   :widths: 40 15 15 30

   * - Cấu hình
     - int8
     - int8h5
     - Kết luận E1
   * - Một context ``CORE_0``
     - 54.69
     - 54.86
     - không phân biệt được
   * - Một context ``CORE_0_1_2``
     - 56.17
     - 56.30
     - không phân biệt được
   * - Hai context
     - 101.90
     - 101.89
     - không phân biệt được
   * - Ba context
     - 141.13
     - 142.09
     - không phân biệt được

Nguồn: [T3 board, ``results/npu/throughput/q2f_fps.json`` khóa ``e1``]. Quy tắc của thí nghiệm: "khác" khi chênh ít nhất 5% và lớn hơn khoảng trải lớn hơn của hai model, ngược lại "không phân biệt được". Chênh thực tế từ -0.01% đến 0.68%. Quy tắc này là quy tắc của một thí nghiệm, chưa duyệt như ngưỡng chung. Hạn chế: một board, một seed, SiLU, ảnh đã cache, không kiểm thứ tự đầu ra. Diễn giải đầy đủ ở :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.

Điều rút ra cho quyết định kiểu số: trong các lựa chọn đã đo, chuyển từ INT8 mặc định sang ``int8h5`` không đổi thông lượng ở mức đo được, nên chênh FPS không phải lý do để chọn giữa hai model đó. FPS vẫn dưới 60 ở một context bất kể kiểu số.

7. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 40 14 46

   * - Mục
     - Trạng thái
     - Đã tìm gì
   * - Lý do UINT8 (bảng layer ``eval_perf``) so với INT8 (thuộc tính runtime)
     - chưa biết
     - Đã so ``tier1_int8_CORE_0_layers.txt``, ``driver_stdout.txt`` và build log. Chưa có log giải thích chỗ chuyển
   * - Tốc độ và FPS khi vào hoặc ra FP16 lúc chạy RKNNLite
     - chưa biết
     - Docstring của wheel ghi ``data_type`` mặc định ``uint8``. Không có log FP16 vào ra trong ``runs/``
   * - Công thức và chi phí độc lập của ``exDataConvert``
     - chưa biết
     - Bảng toán tử vendor chỉ có mô tả "精度转换" [T1 OPL tr.330]. Chi phí chỉ có một hàng ReLU (332 us), SiLU ``h5`` chưa trích
   * - Sai số tọa độ box riêng
     - chưa biết
     - Chưa đo, ghi ở :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa`
   * - ``quantized_dtype`` ngoài INT8 trên RK3588
     - chưa biết
     - Mâu thuẫn [T1 API232 tr.7] và [T1 UG232 tr.121], chưa xác định theo bảng nền tảng
   * - FP16 nhiều context
     - chưa biết
     - Chỉ có ba phiên FP16 một context ``CORE_0``
   * - Cách hiểu 30 FPS
     - một luồng camera, suy từ lý do người dùng nêu ngày 2026-11-08
     - :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8

8. Nguồn
========

- T1: SDK User Guide V2.3.2 (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, UG232 tr.22, 120, 121, 130), API Reference Toolkit2 V2.3.2 (API232 tr.7, 8), Compiler Support Operator List V2.3.2 (OPL tr.330), API Reference RKNNRT V2.3.2 (tr.12).
- T3: ``ai/npu/operator_support/build_recipe.py:64``, ``ai/core/rknn/hybrid.py:64, 71``, ``bench/tier1_int8_CORE_0_layers.txt``, ``experiments/npu/latency/onboard_x4/driver_stdout.txt``, ``experiments/npu/latency/onboard_x8/fp16/``, ``experiments/npu/operator_support/onboard_g4b/ppe5_yolov8n_baseline_100ep_s0/``, ``experiments/npu/operator_support/onboard_q2c/logs/``, ``results/npu/operator_support/q2c_diag.json``, ``results/npu/throughput/q2f_fps.json``, ``results/npu/operator_support/q2j_split.json`` (thư mục ``bench`` là ``experiments/runs/ppe5_yolov8n_baseline_100ep_s0/bench/``).
- Trang liên quan: :doc:`03-tensor-layout`, :doc:`05-memory-access`, :doc:`06-memory-copy`, :doc:`07-compiler-optimization`, :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa`, :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`, :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`, :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet`, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.
