:tocdepth: 1

********************
Bài toán và ứng dụng
********************

.. admonition:: Tóm tắt

   - Bài toán hiện tại là Industrial PPE Detection với 5 class: `person`, `helmet`, `safety_clothes`, `self_clothes`, `head`.
   - Chỉ dùng YOLO để phát hiện PPE trên Orange Pi 5 là application / implementation, chưa phải một research problem đủ rõ.
   - Hướng nghiên cứu mạnh hơn là hardware-aware optimization của lightweight PPE detector trên RK3588S NPU, trong đó B (Edge AI) là trọng tâm hơn một chút.
   - DAHD-YOLO trên RK3588 có single-thread 0.1162 s/frame, không đủ real-time 25 FPS; dùng thread pool đạt 50.2 FPS ở 720P (Table 6, tr.18).
   - Model ít FLOPs hoặc ít parameters chưa chắc nhanh hơn trên NPU, hiệu quả thật phải đo trực tiếp trên target hardware.
   - Cùng InceptionV3 và accuracy không đổi, độ trễ chênh lệch tới 3,8 lần (401ms đến 1537ms) giữa các thiết bị (edge_ai_survey_2025wang, Table 6, tr.21).

.. contents:: Trong trang này
   :local:
   :depth: 2

.. _01-application-hiện-tại:

1. Bài toán ứng dụng hiện tại (Industrial PPE Detection)
================================================================================

.. list-table::

   * - **Bài toán**
     - Industrial PPE Detection
   * - **Class hiện tại**
     - ``person``, ``helmet``, ``safety_clothes``, ``self_clothes``, ``head``

2. Định hướng đề tài: Tối ưu hóa nhận thức phần cứng (Hardware-Aware Optimization)
====================================================================================================

Nếu chỉ phát biểu:

   “Dùng YOLO để phát hiện PPE trên Orange Pi 5.”

thì đó chủ yếu là **application / implementation**, chưa phải một research problem đủ rõ.

Hướng nghiên cứu mạnh hơn:

   **Hardware-aware optimization of a lightweight PPE detector for real-time inference on RK3588S NPU**

Có thể hiểu đề tài nằm ở giao của hai phía:

.. code:: text

   A. Computer Vision / PPE Detection
      - person / helmet / head / safety_clothes / self_clothes
      - small objects
      - multi-scale
      - lighting and noise (low-light)
      - occlusion
      - confusable classes (helmet/head, safety_clothes/self_clothes)
      - class imbalance
      - data augmentation, loss, distillation (ứng viên)
      - input resolution, tiling (ứng viên)
      - detection accuracy (mAP50 / mAP50-95 / AP per class)

                          +

   B. Edge AI / Hardware-aware Optimization
      - RK3588S NPU
      - FP16 / INT8
      - quantization (PTQ, hybrid)
      - pruning
      - operator compatibility (activation, Resize)
      - multi-core / multi-thread
      - pre/post-processing (LetterBox, NMS)
      - latency / FPS / memory / thermal
      - compiler/runtime behavior
      - accuracy-efficiency trade-off

Trong định hướng hiện tại:

   **B là trọng tâm hơn một chút, A là bài toán ứng dụng và quality constraint.**

3. Đối chiếu thực nghiệm trên nền tảng RK3588 (DAHD-YOLO)
================================================================================

Tiền lệ thật cho hướng này: :download:`_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf <../../_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf>`, Table 6, tr.18. DAHD-YOLO (dựa trên YOLOv8s) triển khai thật trên chính RK3588. Paper viết nguyên văn:

   "the INT8 optimized model's single-thread inference time per frame is 0.1162 s, which is insufficient for real-time surveillance camera monitoring at 25 frames per second [...] By utilizing a thread pool for acceleration, we optimize the entire detection process through multithreading."

Số liệu Table 6 (nguyên văn từ paper): DAHD-YOLO INT8 gồm Size 8.8M, FPS 720P **50.2**/1080P 43.8/1440P 37.7, mAP50 74.36%, Inference-Time 79.1ms, Power 7W. Tức đơn luồng 1 core (0.1162s/frame ≈ 8.6 FPS) không đủ real-time; multi-thread khai thác 3 NPU core đưa lên 50.2 FPS.

4. Nghịch lý phần cứng: Độ phức tạp lý thuyết và độ trễ thực tế
================================================================================

Tư tưởng cốt lõi cần giữ xuyên suốt:

   **Model ít FLOPs hoặc ít parameters chưa chắc chạy nhanh hơn trên NPU. Hiệu quả thật phải được đo trực tiếp trên target hardware.**

Bằng chứng: :download:`_assets/pdf/papers/00_overview/edge_ai_survey_2025wang.pdf <../../_assets/pdf/papers/00_overview/edge_ai_survey_2025wang.pdf>`, Table 6 ("Accuracy and Inference Time for PyTorch Mobile on Different Devices"), tr.21, số liệu thô nguyên văn trong bảng, cùng 1 model InceptionV3 (cùng trọng số, accuracy giữ nguyên 77.82%/77.82%/77.82%/77.82%/77.68% qua 5 thiết bị):

.. list-table::
   :header-rows: 1

   * - Thiết bị
     - Galaxy S10e
     - Honor V20
     - Vivo X27
     - Vivo Nex
     - Oppo R17
   * - Time (ms)
     - 433
     - 401
     - 1509
     - 1500
     - 1537

Cùng kiến trúc, cùng trọng số, accuracy không đổi, nhưng độ trễ chênh lệch tới **3,8 lần** (401ms → 1537ms) chỉ vì đổi chip.
