:tocdepth: 1

******************
Điều chưa rõ: YOLO
******************

.. admonition:: Tóm tắt

   - T3 board trên YOLOv8n: Conv+SiLU thành ConvExSwish chạy NPU nhưng chỉ lõi 0, Resize nearest 2x INT8 có Target = NPU ở optimization_level 1, 2 và 3, và op duy nhất chạy CPU là 1 Transpose.
   - T3 board trên YOLO26n (trọng số ngẫu nhiên): 182 lớp không có lớp CPU ngoài Input/Output, mỗi khối attention thành một lớp exSDPAttention INT8 NPU chỉ chạy lõi 0.
   - YOLO26n chậm hơn YOLOv8n khoảng 13 đến 16% trên trọng số ngẫu nhiên (22.26 so 19.40 ms ở AUTO) dù ít FLOPs hơn khoảng 34%, chiều chênh lệch vững, độ lớn chưa chắc, nguyên nhân chưa tách.
   - Độ chính xác INT8 của Softmax trong attention là unknown, cần model đã huấn luyện để đo mAP FP32 so INT8.
   - T3 board (YOLOv8n trọng số ngẫu nhiên): ConvExSwish chỉ chạy lõi 0, còn ConvRelu chia ba lõi. ReLU nhanh hơn khoảng 8% khi dùng 3 lõi, SiLU không khác biệt ngoài độ trải.
   - YOLO26n chậm hơn YOLOv8n khoảng 13 đến 16% (22.26 so 19.40 ms ở AUTO, trọng số ngẫu nhiên) dù ít FLOPs hơn, nguyên nhân vẫn còn mở.
   - Còn mở: độ chính xác INT8 của khối attention, độ trễ với model đã huấn luyện, và số 41.2 ms của Ultralytics không đối chiếu được. AP khi thay SiLU bằng ReLU trên RK3588 là unknown.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _85-hệ-quả-cho-yolo-và-ppe-trên-rk3588:

Hệ quả cho YOLO và PPE trên RK3588
==================================

Mỗi mệnh đề ghép một T2 và một T1, trích riêng. Phần còn lại là ``unknown``.

.. list-table::
   :header-rows: 1

   * - Mệnh đề
     - T2
     - T1
     - Kết luận
   * - Sau re-param chỉ còn Conv 3x3 + activation
     - REPVGG tr.2
     - OPL tr.58 đến 59 (Conv, kernel ∈ [1,31], int8, float16), tr.60 (ConvolutionRelu)
     - op có trong danh sách, tốc độ và độ chính xác INT8 trên RK3588 ``unknown``
   * - SiLU có chạy trên NPU RK3588
     - MOBONE, Y6, ACTNAS (ReLU nhanh hơn SiLU trên thiết bị khác)
     - OPL tr.63 (ConvolutionSwish), tr.98 (exSwish "SiLU"), int8 và float16. UG232 tr.142 (fusion "Conv+Sigmoid(Tanh/Elu/Silu...)"). UG232 tr.146 Table 8-5 xếp Sigmoid, Tanh, Softplus, Hardswish vào "Non-Relu activation function" kém hiệu quả, không có SiLU
     - có op SiLU, chi phí so ReLU trên RK3588 ``unknown``
   * - Conv+SiLU không chạy đa lõi
     - không có T2: EDGE Table 4 không nêu activation của model nào và cho kết quả không đồng nhất giữa các model
     - OPL tr.63: ConvolutionSwish "多核联合: 暂不支持". UG232 tr.75 liệt kê op hỗ trợ đa lõi
     - chỉ T1 chứng minh được (ConvolutionSwish không hỗ trợ đa lõi). ảnh hưởng đo được lên model PPE ``unknown``. T3 board (log T3 board 2026-10-10, lượt 2): với ``core_mask`` CORE_0_1_2, 57 lớp ``ConvExSwish`` (``silu_opt3``) đều WorkLoad 100%/0%/0% (chỉ lõi 0), còn 51 ``ConvRelu`` và 6 ``ConvReluAdd`` (``relu_opt3``) được chia ba lõi (khoảng 35%/32.5%/32.5%). ReLU nhanh hơn CORE_0 khoảng 8% khi dùng 3 lõi (13.969 ms xuống 12.854 ms ở ``relu_opt3``, 13.955 xuống 12.801 ở ``relu_noadd``), SiLU không khác biệt ngoài độ trải. đây là đo trên một model: YOLOv8n trọng số ngẫu nhiên ``nc=5``, INT8, 640x640, toolkit 2.3.2, RK3588S, NPU 1 GHz, ``eval_perf`` ``fix_freq=True``, không phải xác nhận cho mọi Conv+SiLU
   * - Thay SiLU bằng ReLU giảm AP và tăng FPS
     - Y6 Table 4 (chỉ trên T4)
     - OPL có cả ConvolutionRelu và ConvolutionSwish. UG232 tr.142 và 146 (xem hàng 2)
     - AP ``unknown`` trên RK3588. độ trễ có một phép đo T3 (YOLOv8n trọng số ngẫu nhiên, xem mục chi phí SiLU)
   * - DFL làm chậm model nhỏ
     - Y6 Table 10 (tr.10, chỉ YOLOv6, T4, batch 32): YOLOv6-N không DFL 1226 FPS, có DFL 1022 FPS. Y6 tr.10: "the inference speed is greatly affected for small models"
     - OPL tr.88 đến 89 mô tả Softmax (axis 1 hoặc 3, "多核联合: 尚不支持"). Việc gắn Softmax với DFL không có trong T2 hợp lệ nào (suy luận ngoài corpus)
     - ``unknown`` cho YOLOv8: cấu trúc head YOLOv8 không có trong T2 hợp lệ nào

Mọi mệnh đề khác về RK3588 (chọn activation, chọn kiểu re-param, NAS) là ``unknown`` cho đến khi có T3. Ngoại lệ duy nhất: phép đo T3 SiLU so ReLU trên YOLOv8n trọng số ngẫu nhiên (xem mục chi phí SiLU ở trên, log ``tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/README.md``), chưa có accuracy.

.. _98-câu-hỏi-đã-đóng-còn-mở-và-mâu-thuẫn-giữa-nguồn:

Câu hỏi đã đóng, còn mở và mâu thuẫn giữa nguồn
===============================================

.. list-table::
   :header-rows: 1

   * - #
     - Câu hỏi
     - Trạng thái
     - Căn cứ hoặc cách trả lời
   * - 1
     - YOLO26n (đường RKNN, toolkit 2.3.2) có chuyển đổi và chạy hết trên NPU không, attention chạy đâu
     - Đã đóng (trọng số ngẫu nhiên)
     - T3 board, :ref:`Phép đo T3 board của YOLO26n (đường xuất thật, trọng số ngẫu nhiên) <955-phép-đo-t3-board-của-yolo26n-đường-xuất-thật-trọng-số-ngẫu-nhiên>`: 182 lớp, không có lớp CPU ngoài Input/Output, 2 ``exSDPAttention`` NPU. Điều kiện: trọng số ngẫu nhiên, ``nc=5``, ảnh calibration theo mục "Giới hạn" của 9.5.5 (số ảnh suy ra từ mã, thư mục ảnh không còn), với YOLOv8n có đối chứng trọng số đã huấn luyện (ánh xạ op giống nhau), với YOLO26n chưa có
   * - 2
     - Độ trễ YOLO26n so với YOLOv8n trên RK3588
     - Đã đo (trọng số ngẫu nhiên)
     - YOLO26n chậm hơn khoảng 13 đến 16% (22.26 so 19.40 ms ở AUTO), chồng khoảng. Mann-Whitney p < 0.003 ở cả ba mask, khoảng tin cậy 95% của chênh lệch trung vị không chứa 0 (15 giá trị không độc lập, xem 9.5.5)
   * - 3
     - Hiệu suất MAC của depthwise 3x3
     - Đã đo (8 lớp, một model, INT8, trọng số ngẫu nhiên)
     - ``MacUsage`` 0.30% đến 1.24%, tổng 1296 us
   * - 4
     - Độ chính xác INT8 của khối attention (``Softmax``)
     - **Còn mở**
     - Huấn luyện YOLO26n 5 lớp (có ``yolo26n.pt`` tiền huấn luyện), xuất INT8 với 300 ảnh calibration, đo mAP FP32 so INT8 theo protocol v1, cùng baseline YOLOv8n
   * - 5
     - Nhánh một-nhiều so với một-một
     - Đã đóng ở mức công bố
     - YOFF tr.14: cột thường là nhánh một-nhiều với NMS (40.9), cột e2e là nhánh một-một (40.1), chất lượng sau INT8 và trên PPE vẫn mở (mục 4)
   * - 6
     - Đa lõi của attention và ``ConvExSwish``
     - Đã đo: chưa thấy lợi ích
     - Trung vị 3 phiên, khoảng chồng nhau.``exSDPAttention`` và ``ConvExSwish`` chỉ lõi 0
   * - 7
     - ``Resize`` ``asymmetric`` + ``floor`` ở YOLO26n
     - Đã đóng
     - ``Resize`` 2 lớp NPU (T3 board)
   * - 8
     - Vì sao yaml YOLO26n ghi 6.1 GFLOPs còn ``get_flops`` ra 6.240
     - Đã đóng
     - thop ở 32x32 nhân (640/32)^2 cho 6.117 (:ref:`So sánh tổng quan <91-so-sánh-tổng-quan>`), nguyên nhân chênh với ``get_flops`` là suy luận
   * - 9
     - Vì sao YOLO26n chậm hơn dù ít FLOPs
     - **Còn mở**
     - Yếu tố khả dĩ: 182 so 119 lớp, 87 so 57 ``ConvExSwish``, 2 ``exSDPAttention`` (2455 us), depthwise ``MacUsage`` thấp. Tách bằng so sánh theo từng khối hoặc biến thể (bỏ attention, thay depthwise)
   * - 10
     - Số 41.2 ms (YOLO26n INT8, Rock 5B, UDOC) so với 22 ms của chúng ta
     - **Còn mở**
     - Phương pháp đo khác, UDOC không nêu tần số NPU, runtime, batch, không đối chiếu được
   * - 11
     - Độ trễ khi dùng bộ calibration 300 ảnh, trọng số đã huấn luyện, và so với ReLU thay SiLU ở YOLO26n
     - **Còn mở**
     - Đo thêm khi có model huấn luyện

Mâu thuẫn giữa các nguồn (không phân xử bằng suy đoán):

.. list-table::
   :header-rows: 1

   * - Vấn đề
     - Nguồn A
     - Nguồn B
     - Xử lý
   * - Nhánh mặc định của YOLO26
     - YOFF tr.6: một-một mặc định
     - UDOC dòng 81, 142, 156: một-nhiều mặc định
     - Không ảnh hưởng đường RKNN (một-nhiều), ghi nhận
   * - mAP của YOLO26n (cột thường và e2e)
     - YOFF, Y26A, Y26B: 40.9 và 40.1
     - YEVO: 39.8 và 40.3
     - Dùng YOFF
   * - FLOPs của YOLO26n
     - YOFF Bảng 7 tr.14: 5.4 B
     - UDOC dòng 121: 5.5 B, tự tính ``get_flops`` đã fuse: 5.480
     - Khớp trong làm tròn, dùng 5.48 (``nc=80``)
   * - Backbone YOLO26
     - Y26B Bảng 1 tr.6: "CSP-Muon"
     - ``yolo26.yaml``: ``C3k2``, ``SPPF``, ``C2PSA`` (Muon là bộ tối ưu hóa)
     - Dùng mã nguồn
   * - Ngày phát hành YOLO26
     - UDOC dòng 56: "released January 2026"
     - Y26A: "September 2025"
     - Dùng UDOC, không ảnh hưởng kỹ thuật
   * - Hình S2 và văn bản của YOFF
     - Hình S2 tr.23: nhánh một-nhiều "train-only"
     - YOFF tr.6: nhánh một-nhiều "uses NMS at inference"
     - Ghi nhận. đường RKNN dùng nhánh một-nhiều, UDOC nói cả hai nhánh được huấn luyện

--------------

.. _99-việc-tiếp-theo:

Việc tiếp theo
==============

.. list-table::
   :header-rows: 1

   * - Bước
     - Việc
     - Điều kiện hoàn thành
   * - 1
     - [STRIKEOUT:Kiểm độc lập lượt ba] xong 2026-10-11: đã sửa đường RKNN thật có thêm ``_NormalizeCoords`` (:ref:`Đồ thị xuất và đường RKNN <94-đồ-thị-xuất-và-đường-rknn>`), dòng trích ``exporter.py``, điều kiện zero-copy của OPL §5.1, mask của số depthwise và attention, số ``Concat`` chia ba lõi (:ref:`Phép đo T3 board của YOLO26n (đường xuất thật, trọng số ngẫu nhiên) <955-phép-đo-t3-board-của-yolo26n-đường-xuất-thật-trọng-số-ngẫu-nhiên>`), điều kiện ô 9.8 số 1
     - Xong
   * - 2
     - Giai đoạn huấn luyện (:ref:`Câu hỏi đã đóng, còn mở và mâu thuẫn giữa nguồn <98-câu-hỏi-đã-đóng-còn-mở-và-mâu-thuẫn-giữa-nguồn>` số 4 và 11, lần đầu dừng ở epoch 51/100 ngày 2026-10-10 theo yêu cầu người dùng, chạy lại từ 2026-10-11): huấn luyện YOLO26n 5 lớp từ ``yolo26n.pt`` (seed 42, 100 epoch, cùng bộ dữ liệu và evaluator protocol v1 với baseline YOLOv8n, khoảng 2.3 giờ trên RTX 3050 4 GB theo lần chạy YOLOv8n), xuất INT8 với 300 ảnh calibration, đo mAP FP32 so INT8 và độ trễ
     - Có bảng so YOLOv8n với YOLO26n cùng điều kiện, kèm AP
   * - 3
     - Chỉ sau bước 2 mới đưa khuyến nghị chọn model và sửa đổi kiến trúc
     - Khuyến nghị gắn với số đo trên dữ liệu PPE, không với số trong paper

Số đo T3 ban đầu chưa tái kiểm
==============================

Chưa có log gốc để kiểm lại, nên các số đo dưới đây chỉ là ghi nhận ban đầu, không dùng làm căn cứ cho trang kiến thức.

.. _954-tiêu-chí-từ-phép-đo-t3-board-yolov8n:

Tiêu chí từ phép đo (T3 board, YOLOv8n)
---------------------------------------

- Conv+SiLU được ghép thành ``ConvExSwish`` và chạy NPU. ở ``core_mask=CORE_0_1_2`` cả 57 lớp chỉ dùng lõi 0 (``100%/0%/0%``), còn ``ConvRelu`` và ``ConvReluAdd`` chia ba lõi [T3 board, nhật ký mục "Lượt 2"].
- ``Resize`` nearest 2x INT8 có ``Target = NPU`` ở ``optimization_level`` 1, 2 và 3 [T3 board].
- Ngoài ``InputOperator`` và ``OutputOperator``, op duy nhất chạy CPU: 1 ``Transpose``.``exSoftmax13`` (từ ``Softmax`` của DFL) chạy NPU [T3 board].
- Thay SiLU bằng ReLU giảm độ trễ khoảng 29 đến 39% tùy cặp model và ``core_mask`` (trung vị mỗi cặp, số SiLU dao động giữa các phiên), chưa có AP [T3 board, ``08_`` mục chi phí SiLU].

.. _955-phép-đo-t3-board-của-yolo26n-đường-xuất-thật-trọng-số-ngẫu-nhiên:

Phép đo T3 board của YOLO26n (đường xuất thật, trọng số ngẫu nhiên)
-------------------------------------------------------------------

Nguồn: ``tmp/04_debug-logs/2026-10-10_yolo-phaseA/README.md`` và ``raw/``. Điều kiện: ``nc=5``, INT8, ``ultralytics export(format="rknn")`` (opset 19, ``onnxslim``.``metadata.yaml`` ghi ``end2end: false``), 40 ảnh calibration, ``eval_perf`` 2.3.2 với NPU 1 GHz và DDR 2112 MHz (ghi trong đầu ra ``eval_perf`` của cả 18 nhóm đo), nhiệt độ tối đa 46.2 độ C ở ``soc-thermal`` và ``npu-thermal`` (các vùng khác tới 47.2), 3 phiên cách nhau 180 giây, thứ tự model xen kẽ.

.. list-table::
   :header-rows: 1

   * - Câu hỏi
     - Kết quả (T3 board)
   * - YOLO26n chuyển đổi và chạy trên NPU không
     - Có: 182 lớp, ngoài ``InputOperator`` và ``OutputOperator`` không có lớp CPU nào
   * - Khối attention
     - Mỗi khối (``C2PSA`` lớp 10 và ``C3k2`` lớp 22) thành một lớp ``exSDPAttention``, ``INT8``, ``NPU``, đầu vào ``(2,32,1,400)``, 1230 và 1225 us ở ``core_mask`` AUTO (CORE_0: 1193 và 1188. CORE_0_1_2: 1222 và 1223).``WorkLoad`` chỉ lõi 0 ngay cả ở ``CORE_0_1_2`` (khớp OPL 3.2.78 "多核联合: 不支持"). Trình biên dịch tự nhận chuỗi ``MatMul``-``Softmax``-``MatMul`` thành ``exSDPAttention``. T1 không có quy tắc nhận chuỗi (quan sát, không phải quy tắc)
   * - Depthwise 3x3
     - 8 lớp (6 ở nhánh lớp, ghép thành ``ConvExSwish``, 2 ``pe`` của attention, là ``Conv``), tổng 1296 us (khoảng 4.6% của 28146 us tổng thời gian debug), ``MacUsage`` 0.30% đến 1.24% (trung bình 0.78%), các số này ở ``core_mask`` AUTO. CORE_0: 898 us trên 20942 us (4.3%), ``MacUsage`` 0.62% đến 1.43%. CORE_0_1_2: 1153 us trên 25824 us, ``MacUsage`` mỗi lõi 0.11% đến 0.43%. Tổng thời gian bảng debug lệch giữa các mask (28146 so 20942 us ở cùng workload lõi 0), nên đọc tỷ lệ phần trăm như khoảng, không như một giá trị
   * - Bỏ DFL
     - YOLO26n không có ``exSoftmax13`` và không có ``Transpose`` CPU. ở YOLOv8n hai lớp này chiếm 2105 us (11.3%) và 799 us (4.3%) tổng thời gian debug ở AUTO
   * - Số lớp
     - 182 (YOLO26n) so 119 (YOLOv8n), 87 ``ConvExSwish`` so 57
   * - Độ trễ ``eval_perf`` (trung vị của 15 giá trị, ms)
     - YOLO26n 22.26 (AUTO), 21.70 (CORE_0), 22.09 (3 lõi). YOLOv8n 19.40, 19.16, 18.985 (giá trị chính xác của ba lõi. README ghi 18.98). YOLO26n chậm hơn khoảng 13 đến 16%, dù ít FLOPs hơn khoảng 34% (5.314 so 8.087 GFLOPs). Ở 8 trong 9 cặp (phiên, mask) YOLO26n chậm hơn, khoảng min đến max của hai model chồng lên nhau. Kiểm định (``stats_latency.py``, ``out/stats_latency.txt`` trong ``tmp/04_debug-logs/2026-10-10_yolo-phaseA/``): Mann-Whitney hai phía trên 15 giá trị mỗi nhóm cho p = 0.0003 (AUTO), 0.0025 (CORE_0), 0.0019 (3 lõi), khoảng tin cậy 95% bootstrap của chênh lệch trung vị (YOLO26n trừ YOLOv8n) là 1.50 đến 4.50 ms, 1.30 đến 2.88 ms, 1.20 đến 5.36 ms, đều không chứa 0. Giới hạn: 15 giá trị không độc lập (5 lần lặp trong mỗi phiên), ở mức phiên chỉ có 3 so 3, nên p là lạc quan, kết luận chiều chênh lệch vững, độ lớn chưa chắc
   * - Đa lõi
     - Không có lợi ích đo được cho cả hai model, 21 trên 23 ``Concat``, 18 trên 18 ``Add`` và 11 trên 11 ``Conv`` chia ba lõi (2 ``Concat`` chỉ lõi 0), còn 87 ``ConvExSwish``, ``exSDPAttention`` và ``Split`` chỉ lõi 0.``Reshape`` (13 lớp) có 9 lớp chỉ lõi 0 và 4 lớp không có workload, 4 lớp ``ConvAdd`` chia ba lõi

Giới hạn: trọng số ngẫu nhiên (chỉ cấu trúc và độ trễ), một kích thước ``n``, ``nc=5``, calibration 40 ảnh, độ trải giữa các phiên cùng cỡ chênh lệch giữa hai model. Phép đo không cho biết vì sao YOLO26n chậm hơn (nhiều lớp hơn, nhiều ``ConvExSwish``, hai ``exSDPAttention``, depthwise ``MacUsage`` thấp đều là yếu tố khả dĩ chưa tách).
