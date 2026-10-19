:tocdepth: 1

************************
Huấn luyện và hệ quả PPE
************************

.. admonition:: Tóm tắt

   - Phần huấn luyện chỉ đổi đồ thị xuất ở chỗ bỏ DFL và đầu một-một. ProgLoss, STAL và MuSGD không đổi đồ thị suy luận theo mô tả của paper.
   - Nhánh một-nhiều của YOLO26n đạt mAP50-95 40.9 và nhánh một-một 40.1 trên COCO val ở FP32 [T2 YOFF Bảng 7 tr.14], chất lượng sau INT8 và trên dữ liệu PPE là unknown.
   - T3 board (YOLOv8n trọng số ngẫu nhiên): ConvExSwish chỉ chạy lõi 0, còn ConvRelu chia ba lõi. ReLU nhanh hơn khoảng 8% khi dùng 3 lõi, SiLU không khác biệt ngoài độ trải.
   - YOLO26n chậm hơn YOLOv8n khoảng 13 đến 16% (22.26 so 19.40 ms ở AUTO, trọng số ngẫu nhiên) dù ít FLOPs hơn, nguyên nhân vẫn còn mở.
   - Còn mở: độ chính xác INT8 của khối attention, độ trễ với model đã huấn luyện, và số 41.2 ms của Ultralytics không đối chiếu được. AP khi thay SiLU bằng ReLU trên RK3588 là unknown.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _96-phần-huấn-luyện-chỉ-ở-chỗ-nó-đổi-đồ-thị:

Phần huấn luyện chỉ ở chỗ nó đổi đồ thị
=======================================

Chỉ chép nguyên văn câu định nghĩa, không giải thích thêm.

.. list-table::
   :header-rows: 1

   * - Thay đổi
     - Nguyên văn
     - Có đổi đồ thị xuất ra không
   * - Bỏ DFL
     - "YOLO26 reverts to a Direct Regression Strategy, removing this module entirely (see Fig. 4)." [T2 Y26B tr.8]
     - Có: bỏ ``Reshape``, ``Transpose``, ``Softmax``, Conv1x1 của DFL.``reg_max`` 1 (T1 :ref:`Đầu Detect <924-đầu-detect>`)
   * - Đầu một-một
     - "By redesigning the prediction head to support one-to-one label assignment [24], the model learns to output a single, definitive box per object instance during training." [T2 Y26B tr.7]
     - Có, nhưng không bật ở đường xuất mặc định (:ref:`Đồ thị xuất và đường RKNN <94-đồ-thị-xuất-và-đường-rknn>`)
   * - ProgLoss, STAL
     - "ProgLoss adaptively reweights objectives to prevent domination by easy examples late in training, while STAL prioritizes assignment for tiny or occluded instances" [T2 Y26A tr.4]
     - Không đổi đồ thị suy luận theo mô tả của paper, chưa đọc mã loss
   * - MuSGD
     - "the introduction of the MuSGD optimizer (Figure 4d), which combines the strengths of Stochastic Gradient Descent (SGD) with the recently proposed Muon optimizer" [T2 Y26A tr.7]
     - Không

Mã nguồn tự chọn hàm mất mát: ``E2ELoss`` khi đầu có ``one2one_cv2``, ngược lại ``v8DetectionLoss`` (T1 ``nn/tasks.py:604``), nên huấn luyện YOLO26n chỉ cần dùng ``yolo26.yaml``. Tổng hợp của file này: trọng số YOLOv8n không dùng lại được cho YOLO26n vì khối và đầu khác nhau (:ref:`Khối cấu thành <92-khối-cấu-thành>`), và đầu YOLO26n có hai nhánh (một-một và một-nhiều) cùng tồn tại trong lúc huấn luyện (T1 ``head.py:140-142``. T2 Y26B tr.17 gọi nhánh một-nhiều là "auxiliary ... used during training"). Đường RKNN dùng chính nhánh một-nhiều. YOFF (chú thích Bảng 7, tr.14) viết: "'mAP' denotes standard validation of the one-to-many branch with NMS ('end2end=False'), whereas 'mAP (E2E)' denotes true end-to-end validation of the default one-to-one branch." Vậy với YOLO26n trên COCO val, nhánh một-nhiều có mAP50-95 là 40.9 và nhánh một-một là 40.1 (YOFF Bảng 7 tr.14, trùng Y26A và Y26B). YEVO Bảng 3 tr.12 ghi 39.8 và 40.3 (khác số và chiều ngược), nên không dùng. Đây là mAP PyTorch ở FP32 trên COCO, chất lượng nhánh một-nhiều sau lượng tử hóa INT8 và trên dữ liệu PPE chưa đo (``unknown``).

Y26B tr.8 cũng viết: "On specialized edge hardware (NPUs and DSPs), these Softmax layers are notoriously difficult to quantize and often become the primary latency bottleneck [30]", trích một bài khảo sát lượng tử hóa chung, không phải phép đo trên YOLO hay RKNN [T2 Y26B tr.8, ghi chú độ tin cậy ở đầu file]. Dùng như giả thuyết, không như kết quả.

--------------

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

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần trích).

.. list-table::
   :header-rows: 1
   :widths: 12 8 70 10

   * - Nhãn
     - Tier
     - Nguồn
     - Số lần
   * - ``Y26B``
     - T2
     - :download:`yolo26_nmsfree_2026chakrabarty.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_nmsfree_2026chakrabarty.pdf>`
     - 3
   * - ``Y26A``
     - T2
     - :download:`yolo26_arch_2025sapkota.pdf <../../../_assets/pdf/papers/09_yolo_architecture/yolo26_arch_2025sapkota.pdf>`
     - 2
