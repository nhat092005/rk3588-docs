:tocdepth: 1

***************
Chọn activation
***************

.. admonition:: Trang này trả lời

   - SiLU so với ReLU có chi phí khác nhau không, và đo ở đâu?

.. admonition:: Tóm tắt

   - ReLU nhanh hơn SiLU trên mọi thiết bị đã đo trong các bài: iPhone 12 (ReLU 1.53 ms, SiLU 2.54), Tesla T4 (FPS 1246 so với 963) và ba NPU không nêu tên.
   - Y6 giải thích ReLU nhanh hơn vì "its fusion into convolution", và YOLOv6-N mất 1.8 điểm AP khi đổi SiLU sang ReLU (36.6% xuống 34.8%) [T2 Y6 tr.8].
   - Không bài nào đo trên RK3588, và chi phí SiLU so ReLU trên RK3588 theo T1 và T2 là `unknown`.
   - Đo T3 chỉ trên YOLOv8n trọng số ngẫu nhiên, INT8: độ trễ trung vị 19.154 ms (SiLU) và 13.617 ms (ReLU), chưa có accuracy.
   - Bản không residual `Add` cho 21.431 ms (SiLU) so 13.929 ms (ReLU), và số SiLU dao động giữa hai lượt (19.154 ms rồi 22.021 ms) với nguyên nhân chưa biết.
   - SiLU so ReLU trên model đã huấn luyện chưa làm được vì chưa có bản ReLU đã huấn luyện.

.. _82-chọn-activation-cho-phần-cứng:

Chọn activation cho phần cứng
=============================

**Câu hỏi:** SiLU so với ReLU có chi phí khác nhau không, và đo ở đâu?

**Nguồn nói gì**

   "Therefore we use only ReLU activations in MobileOne." [T2 MOBONE tr.3]

..

   "MobileNet-V3 [30], introduces an optimized activation function - Hard-Swish for a specific platform. However, scaling such functions to different platforms may be difficult. Therefore, our design uses basic operators that are already available across different platforms." [T2 MOBONE tr.3]

   "ReLU has a greater speed advantage because of its fusion into convolution." [T2 Y6 tr.8]

..

   "We suggest users adopt RepConv with ReLU in latency-sensitive applications." [T2 Y6 tr.8]

   "ReLU is fast but often less precise, while SiLU offers higher accuracy at the expense of speed." [T2 ACTNAS tr.1]

..

   "We are not disclosing the vendor name and actual name of these NPUs" [T2 ACTNAS tr.3]

   "None of the ActNAS models utilized SiLU or Hardswish in the first two layers." [T2 ACTNAS tr.7]

..

   "the NPU assumed in this paper can execute depth-wise separable convolution (DWConv), squeeze-and-excitation (SE), and h-swish activation function efficiently" [T2 S3NAS tr.2]

|ActNAS Figure 1| *Hình 8.2. Biểu đồ độ trễ và mAP của YOLO5n (NPU1) và YOLO8m (NPU2) với SiLU, ReLU, Hardswish. Hai NPU không nêu tên. Nguồn: [T2 ACTNAS tr.1, Figure 1]*

Số đo (nguyên từ bảng, kèm thiết bị):

.. list-table::
   :header-rows: 1

   * - Bài
     - Bảng
     - Thiết bị đo
     - Số
   * - MOBONE
     - Table 2, tr.4
     - iPhone 12 (Core ML), mạng 30 lớp
     - ReLU 1.53 ms, GELU 1.63, SE-ReLU 2.10, SiLU 2.54
   * - Y6
     - Table 4, tr.9
     - Tesla T4, TensorRT, FP16, batch 32, 640x640, YOLOv6-N
     - Conv + SiLU: 36.6% AP, 963 FPS. Conv + ReLU: 34.8%, 1246. RepConv + ReLU: 35.2%, 1233. RepConv + SiLU: 36.5%, 971
   * - ACTNAS
     - Table 3, tr.6
     - 3 NPU không nêu tên, YOLOv8m, 640x640, độ trễ (ms) trên NPU1, NPU2, NPU3
     - SiLU 48.57 mAP: 241.50, 190.87, 340.00. Hardswish 48.96: 166.80, 140.33, 308.80. ReLU 48.03: 93.17, 103.73, 283.40

**Ý chính**

- ReLU nhanh hơn SiLU trên mọi thiết bị đã đo: độ trễ SiLU cao hơn ReLU khoảng 66% trên iPhone 12 (2.54 so với 1.53 ms) và từ khoảng 20% đến 159% trên ba NPU ẩn danh (340.00 so với 283.40 ms và 241.50 so với 93.17 ms). FPS của ReLU cao hơn SiLU khoảng 29% trên T4 (1246 so với 963). Các tỷ lệ này là tính của file từ số trong bảng.
- Lý do các tác giả nêu: ReLU hợp nhất được vào conv (Y6 tr.8), còn MOBONE tr.3 quy chi phí đồng bộ cho SE-ReLU, Dynamic Shift-Max và Dynamic-ReLU, không nêu SiLU hay GELU (SiLU 2.54 ms chậm hơn SE-ReLU 2.10 ms ở MOBONE Table 2), nên MOBONE không giải thích vì sao SiLU chậm. Đánh đổi là độ chính xác thấp hơn: YOLOv6-N mất 1.8 điểm AP khi đổi SiLU sang ReLU (36.6% xuống 34.8%).
- ActNAS quan sát thấy mô hình tốt nhất thường dùng biến thể ReLU (ReLU6, LeakyReLU, ReLU) ở các lớp đầu (ACTNAS tr.7), cách thay thô ba activation đầu bằng ReLU cho kết quả "slightly slower performance compared to other baseline models" nhưng mAP giảm dưới 1% so với bản SiLU (ACTNAS tr.7). Thiết bị là NPU không nêu tên.

**Giới hạn**

- Không bài nào đo trên RK3588. Số trên T4, iPhone 12 và các NPU ẩn danh không chuyển sang RK3588. ACTNAS còn không nêu vendor và độ chính xác số của NPU (tr.3).
- T1 cho thấy SiLU có mặt trong danh sách op của RK3588 (``ConvolutionSwish``, ``exSwish``, int8 và float16, xem :ref:`Các op của detector kiểu YOLOv8 trên RK3588 <62-các-op-của-detector-kiểu-yolov8-trên-rk3588>`) nên không thể suy ra "SiLU không chạy trên NPU RK3588". Chi phí SiLU so ReLU trên RK3588 là ``unknown``. Đóng một phần (T3 board, 2026-10-10, log T3 board 2026-10-10 (``tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/README.md``)): YOLOv8n trọng số ngẫu nhiên, INT8, ``core_mask`` AUTO, toolkit 2.3.2. Sigmoid + Mul sau Conv được ghép: 57 bộ trong ONNX thành 57 lớp ``ConvExSwish`` trên NPU (tên trong bảng lớp). Độ trễ trung vị 19.154 ms (SiLU, level 3) và 13.617 ms (ReLU, level 3), ReLU thấp hơn 28.9%. Cảnh báo: hai thay đổi trộn lẫn, activation và việc ghép ``Add`` (``Add`` đứng riêng giảm từ 8 xuống 2), thí nghiệm không tách được phần đóng góp của từng thay đổi. SiLU trải từ 17.769 đến 19.628 ms, ReLU từ 13.481 đến 13.668 ms (5 lần đo). Chưa có accuracy, chưa kết luận cho model đã huấn luyện. Lượt 2 (log T3 board 2026-10-10, lượt 2 (``tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/README.md``, ``raw/summary2.json``, ``raw/*_CORE_0_1_2_layers.txt``)): bản không residual ``Add`` (``silu_noadd``, ``relu_noadd``, cùng 113 lớp, cùng 2 ``Add`` đứng riêng) loại biến nhiễu trên: với ``core_mask`` AUTO, 21.431 ms (SiLU) so 13.929 ms (ReLU), ReLU thấp hơn 35.0%.``relu_opt3`` so ``relu_noadd`` (13.963 so 13.929 ms) chênh lệch nằm trong độ trải, nên ghép ``Add`` không đóng góp đo được ở model này. Số SiLU dao động giữa hai lượt (``silu_opt3``, AUTO: 19.154 ms rồi 22.021 ms, cùng file ``.rknn``), nên đọc như khoảng, nguyên nhân chưa biết. Vẫn chưa có accuracy. Lượt 3 (log T3 board 2026-10-10): trên YOLOv8n 5 lớp đã huấn luyện (SiLU) ánh xạ op giống hệt model ngẫu nhiên (57 ``ConvExSwish``, chạy lõi 0 ở ``CORE_0_1_2``) và độ trễ cùng khoảng. SiLU so ReLU trên model đã huấn luyện chưa làm được vì chưa có bản ReLU đã huấn luyện.
- Y6 tr.8 viết SiLU "does not cause too much extra computation cost" rồi nói tiếp "However, when it comes to industrial applications, especially ... TensorRT ... ReLU has a greater speed advantage because of its fusion into convolution". Hai câu không mâu thuẫn: một câu về chi phí tính toán, một câu về tốc độ thực tế (Table 4: FPS 963 so với 1246).

--------------

.. |ActNAS Figure 1| image:: ../../_assets/img/npu/08_model_design_for_npu/actnas_p1_fig1.png

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
   * - ``ACTNAS``
     - T2
     - :download:`actnas_yolo_2025sah.pdf <../../_assets/pdf/papers/08_npu_friendly_arch/actnas_yolo_2025sah.pdf>`
     - 4
   * - ``MOBONE``
     - T2
     - :download:`mobileone_reparam_2023vasu.pdf <../../_assets/pdf/papers/08_npu_friendly_arch/mobileone_reparam_2023vasu.pdf>`
     - 2
   * - ``Y6``
     - T2
     - :download:`yolov6_hwfriendly_2022li.pdf <../../_assets/pdf/papers/08_npu_friendly_arch/yolov6_hwfriendly_2022li.pdf>`
     - 2
   * - ``S3NAS``
     - T2
     - :download:`s3nas_npu_aware_2020lee.pdf <../../_assets/pdf/papers/06_nas/s3nas_npu_aware_2020lee.pdf>`
     - 1
