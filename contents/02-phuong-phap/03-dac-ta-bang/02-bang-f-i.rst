:tocdepth: 1

************
Bảng F đến I
************

.. admonition:: Tóm tắt

   - Table F so FP32 (PyTorch), FP16 (NPU) và INT8 (NPU) của YOLOv8n và YOLOv8s để trả lời Case B. Hiện mọi ô số còn [TBD].
   - Trong Table F, Δ là giá trị FP32 trừ giá trị của dòng đó, nên Δ dương nghĩa là mất accuracy trên NPU. Dòng FP32 đóng vai trò là "mốc".
   - Table G tách Pre P50, NPU, Post P50 và E2E, trong đó NPU đo ở tầng 1 (`eval_perf`), còn các cột khác đo ở tầng 2 (hiện chưa có số).
   - Table H so CPU board (`.onnx` FP32, ONNX Runtime), NPU board (`.rknn` FP16, INT8) và GPU PC RTX 3050 Laptop, trong đó GPU chỉ là tham chiếu.
   - Table I so `core_mask` `AUTO`, `CORE_0`, `CORE_0_1`, `CORE_0_1_2` và 3 luồng trên cùng 1 model INT8. Việc gộp core chỉ tăng tốc một số op.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _table-f-quantization-impact-fp32--npu:

Table F. Quantization Impact (FP32 → NPU)
=========================================

**Mục đích:** trả lời Case B (:ref:`Ví dụ gap có thể xuất hiện sau benchmark <43-ví-dụ-gap-có-thể-xuất-hiện-sau-benchmark>`): quantize làm mất bao nhiêu accuracy, class nào mất nhiều nhất. Cùng 1 evaluator cho cả 3 dòng (:ref:`Evaluation Protocol v1 <50-evaluation-protocol-v1>`). Mỗi seed quantize riêng, báo mean ± std khi có Phase 10. Bảng sinh tự động: ``results/<ds>/table_F_quantization.md``.

.. list-table::
   :header-rows: 1

   * - Model
     - Precision
     - mAP50-95
     - ΔmAP50-95 so với FP32
     - ΔAP person
     - ΔAP helmet
     - ΔAP head
     - ΔAP safety_clothes
     - ΔAP self_clothes
   * - YOLOv8n
     - FP32 (PyTorch)
     - [TBD]
     - mốc
     - mốc
     - mốc
     - mốc
     - mốc
     - mốc
   * - YOLOv8n
     - FP16 (NPU)
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8n
     - INT8 (NPU)
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8s
     - FP32 (PyTorch)
     - [TBD]
     - mốc
     - mốc
     - mốc
     - mốc
     - mốc
     - mốc
   * - YOLOv8s
     - FP16 (NPU)
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8s
     - INT8 (NPU)
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]

**Cách đọc:**

- **Δ** = giá trị của FP32 − giá trị của dòng đó (định nghĩa ở :ref:`AI Quality <51-ai-quality>`).
- **Δ dương** = bị mất accuracy khi chạy trên NPU, trong đó Δ càng lớn càng mất nhiều.
- **"mốc"** = dòng FP32 là mốc để trừ, nên không có Δ. AP từng class của FP32 xem ở Table D.

--------------

.. _table-g-latency-breakdown:

Table G. Latency Breakdown
==========================

**Mục đích:** tìm bottleneck thay vì chỉ nhìn FPS. NPU đo ở tầng 1 (``eval_perf``), các cột khác đo ở tầng 2 trên board (:ref:`Hardware Performance <53-hardware-performance>`).

.. list-table::
   :header-rows: 1

   * - Model
     - Precision
     - Pre P50 (ms)
     - NPU (ms)
     - Post P50 (ms)
     - E2E mean (ms)
     - E2E P50 (ms)
     - E2E P95 (ms)
     - FPS_latency
   * - YOLOv8n
     - FP16
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8n
     - INT8
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8s
     - FP16
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8s
     - INT8
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - Pruned
     - INT8
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - Proposed
     - INT8
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]

--------------

.. _table-h-hardware-comparison:

Table H. Hardware Comparison
============================

**Mục đích:** cho thấy lợi ích của NPU so với CPU trên cùng board (:ref:`Hardware comparison <63-hardware-comparison>`). Làm cho YOLOv8n và YOLOv8s.

.. list-table::
   :header-rows: 1

   * - Thiết bị
     - Model / Precision
     - mAP50-95
     - E2E P50 (ms)
     - E2E P95 (ms)
     - FPS_latency
     - Ghi chú
   * - CPU board (4× Cortex-A76 + 4× Cortex-A55)
     - ``.onnx`` FP32, ONNX Runtime
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - Ghi số thread, nhân CPU dùng
   * - NPU board
     - ``.rknn`` FP16
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - 
   * - NPU board
     - ``.rknn`` INT8
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - 
   * - GPU PC RTX 3050 Laptop (tham chiếu)
     - PyTorch FP32
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - Không phải thiết bị triển khai

--------------

.. _table-i-deployment-configuration:

Table I. Deployment Configuration
=================================

**Mục đích:** so sánh cấu hình triển khai trên cùng 1 model INT8, không train lại (:ref:`Optimization comparison (trọng tâm) <62-optimization-comparison-trọng-tâm>` nhóm 2).

.. list-table::
   :header-rows: 1

   * - ``core_mask``
     - Số luồng (context)
     - NPU latency (ms)
     - Throughput FPS
     - Avg CPU (%)
     - Temp end (°C)
   * - ``AUTO``
     - 1
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - ``CORE_0``
     - 1
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - ``CORE_0_1``
     - 1
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - ``CORE_0_1_2``
     - 1
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - ``CORE_0`` / ``CORE_1`` / ``CORE_2`` (mỗi luồng 1 core)
     - 3
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]

Với 1 luồng, Throughput FPS xấp xỉ FPS_latency, nhưng với nhiều luồng thì khác (:ref:`Hardware Performance <53-hardware-performance>`). Chế độ gộp core chỉ tăng tốc một số op (Conv, Add, Concat, ReLU...), op khác tự chạy trên Core0 (:ref:`Research problem đề xuất <21-research-problem-đề-xuất>`).
