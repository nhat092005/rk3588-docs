:tocdepth: 1

************
Điều chưa rõ
************

.. admonition:: Tóm tắt

   - Trang ghi 5 mâu thuẫn hoặc nhập nhằng, trong đó UG232 tr.75 và OPL tr.84 đến 86 lệch nhau về op hỗ trợ đa lõi, và DAHD Table 6 có thời gian thấp hơn nhưng FPS cũng thấp hơn ở FP16.
   - Chi phí SiLU so ReLU trên RK3588 chỉ được đóng một phần bằng T3: YOLOv8n trọng số ngẫu nhiên, INT8, 19.154 ms (SiLU) so 13.617 ms (ReLU), chưa có accuracy.
   - Re-param (RepVGG, MobileOne, DBB) có giảm độ trễ hoặc mất độ chính xác INT8 trên RK3588 hay không vẫn thiếu nguồn.
   - Hiệu suất MAC của depthwise conv, NAS với độ trễ đo trên NPU Rockchip và lý do YOLO11 chậm hơn YOLOv8 trên RK3588 INT8 đều chưa có nguồn.
   - Nguồn ưu tiên khi UG232 và OPL lệch về đa lõi chưa quyết định, vì đo T3 trên một model chỉ ghi hành vi.

Mâu thuẫn và nhập nhằng đã ghi nhận
===================================

.. list-table::
   :header-rows: 1

   * - #
     - Nội dung
     - Phía A
     - Phía B
   * - 1
     - Thứ hạng tốc độ RepVGG-B0 so với EfficientNet-B0
     - REPVGG Table 4 (1080Ti): 1817 so với 829
     - MOBONE Table 9 (CPU, iPhone 12): EfficientNet-B0 nhanh hơn
   * - 2
     - Mức chênh chi phí SiLU so ReLU giữa các thiết bị (không phải mâu thuẫn trong một bài)
     - Y6 Table 4 (T4): FPS 963 so 1246
     - MOBONE (iPhone 12): độ trễ +66%; ACTNAS (NPU ẩn danh): độ trễ +20% đến +159%
   * - 3
     - DAHD Table 6
     - ``DAHD-YOLO FP16`` có thời gian 116.2 ms thấp hơn YOLOv8s FP16 (131.9 ms)
     - cùng bảng: FPS của DAHD thấp hơn (26.9 so 32.9)
   * - 4
     - RK66 và thuật ngữ
     - RK66 tr.4: Lite2 convert ONNX sang RKNN
     - :doc:`/thuat-ngu`: Lite2 chỉ chạy model có sẵn
   * - 5
     - Op hỗ trợ đa lõi
     - UG232 tr.75: Relu, Clip, PRelu, LeakyRelu
     - OPL tr.84 đến 86: các op này "暂不支持" (xem ``06_``)

Còn thiếu nguồn (unknown)
=========================

.. list-table::
   :header-rows: 1

   * - Câu hỏi
     - Truy vấn hoặc cách kiểm
   * - Re-param (RepVGG, MobileOne, DBB) có giảm độ trễ hoặc mất độ chính xác INT8 trên RK3588
     - "structural reparameterization RKNN RK3588 INT8 latency accuracy"; T3
   * - Chi phí SiLU so ReLU trên RK3588; Sigmoid + Mul có ghép thành ConvolutionSwish không. Đóng một phần (T3 board, 2026-10-10; log T3 board 2026-10-10): YOLOv8n trọng số ngẫu nhiên, INT8, ``core_mask`` AUTO, toolkit 2.3.2. Sigmoid + Mul sau Conv được ghép: 57 bộ trong ONNX thành 57 lớp ``ConvExSwish`` trên NPU (tên trong bảng lớp). Độ trễ trung vị 19.154 ms (SiLU, level 3) và 13.617 ms (ReLU, level 3), ReLU thấp hơn 28.9%. Cảnh báo: hai thay đổi trộn lẫn, activation và việc ghép ``Add`` (``Add`` đứng riêng giảm từ 8 xuống 2), thí nghiệm không tách được phần đóng góp của từng thay đổi. SiLU trải từ 17.769 đến 19.628 ms, ReLU từ 13.481 đến 13.668 ms (5 lần đo). Chưa có accuracy; chưa kết luận cho model đã huấn luyện. Lượt 2 (log T3 board 2026-10-10, lượt 2): bản không residual ``Add`` (``silu_noadd``, ``relu_noadd``; cùng 113 lớp, cùng 2 ``Add`` đứng riêng) loại biến nhiễu trên: với ``core_mask`` AUTO, 21.431 ms (SiLU) so 13.929 ms (ReLU), ReLU thấp hơn 35.0%; ``relu_opt3`` so ``relu_noadd`` (13.963 so 13.929 ms) chênh lệch nằm trong độ trải, nên ghép ``Add`` không đóng góp đo được ở model này. Số SiLU dao động giữa hai lượt (``silu_opt3``, AUTO: 19.154 ms rồi 22.021 ms, cùng file ``.rknn``), nên đọc như khoảng, nguyên nhân chưa biết. Vẫn chưa có accuracy.
     - "SiLU vs ReLU latency RKNN RK3588 INT8 YOLOv8"; T3: YOLOv8n SiLU và ReLU bằng ``eval_perf``
   * - Hiệu suất MAC của depthwise conv trên NPU RK3588
     - TRM1 Ch.36; T3 ``MacUsage(%)``
   * - NAS với độ trễ đo trên NPU Rockchip
     - "hardware-aware NAS Rockchip NPU latency lookup table"
   * - Detector sửa kiến trúc cho RK3588 kèm ablation độ trễ theo từng sửa đổi
     - "YOLOv8 modification RK3588 NPU latency ablation RKNN"
   * - Vì sao YOLO11 chậm hơn YOLOv8 trên RK3588 INT8
     - T3: ``perf_debug`` theo lớp (EDGE tr.5 chỉ nêu giả thuyết C3k2)
   * - Cấu trúc head YOLOv8 (DFL, decoupled)
     - Không có trong T2 hợp lệ. Đóng một phần (T1): đã mô tả từ mã nguồn ``ultralytics`` (``head.py``) ở ``09_yolo_architecture.md`` :ref:`Đầu Detect <924-đầu-detect>`; tài liệu YOLOv8 chính thức chưa được trích cho cấu trúc head
   * - Nguồn ưu tiên khi UG232 và OPL lệch nhau về đa lõi. Đóng một phần (log T3 board 2026-10-10, lượt 2): với ``core_mask`` CORE_0_1_2, 57 lớp ``ConvExSwish`` (``silu_opt3``) đều WorkLoad 100%/0%/0% (chỉ lõi 0), còn 51 ``ConvRelu`` và 6 ``ConvReluAdd`` (``relu_opt3``) được chia ba lõi (khoảng 35%/32.5%/32.5%); ReLU nhanh hơn CORE_0 khoảng 8% khi dùng 3 lõi (13.969 ms xuống 12.854 ms ở ``relu_opt3``; 13.955 xuống 12.801 ở ``relu_noadd``), SiLU không khác biệt ngoài độ trải; đây là đo trên một model: YOLOv8n trọng số ngẫu nhiên ``nc=5``, INT8, 640x640, toolkit 2.3.2, RK3588S, NPU 1 GHz, ``eval_perf`` ``fix_freq=True``, không phải xác nhận cho mọi Conv+SiLU; phép đo chỉ ghi hành vi, chưa quyết định nguồn ưu tiên
     - T3 với ``perf_debug``

.. |RepVGG Figure 4| image:: ../../_assets/img/npu/08_model_design_for_npu/repvgg_p5_fig4.png
.. |MobileOne Figure 3| image:: ../../_assets/img/npu/08_model_design_for_npu/mobileone_p5_fig3.png
.. |ActNAS Figure 1| image:: ../../_assets/img/npu/08_model_design_for_npu/actnas_p1_fig1.png
.. |S3NAS Figure 8| image:: ../../_assets/img/npu/08_model_design_for_npu/s3nas_p6_fig8.png
.. |YOLOv6 Figure 3| image:: ../../_assets/img/npu/08_model_design_for_npu/yolov6_p4_fig3.png
.. |EDGE Figure 3| image:: ../../_assets/img/npu/08_model_design_for_npu/edge_p5_fig3.png
.. |DAHD-YOLO Figure 1| image:: ../../_assets/img/npu/08_model_design_for_npu/dahd_p5_fig1.png
