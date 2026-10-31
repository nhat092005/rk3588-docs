:tocdepth: 1

********************
Bài toán và ứng dụng
********************

.. admonition:: Trang này trả lời

   - Bài toán phát hiện PPE công nghiệp gồm những lớp đối tượng nào và yêu cầu real-time ra sao?
   - Vì sao triển khai detector trên RK3588S NPU là một bài toán nghiên cứu về Hardware-aware Edge AI chứ không dừng lại ở ứng dụng đơn thuần?
   - Vì sao số lượng tham số và FLOPs lý thuyết không phản ánh chính xác độ trễ thực tế trên phần cứng mục tiêu?

.. admonition:: Tóm tắt

   - Bài toán hiện tại là Industrial PPE Detection với 5 class: `Helmet`, `NoHelmet`, `NoVest`, `Vest`, `Person`, mục tiêu thời gian thực là **60 FPS**.
   - Chỉ dùng YOLO để phát hiện PPE trên Orange Pi 5 là application / implementation, chưa phải một research problem đủ rõ.
   - Hướng nghiên cứu mạnh hơn là hardware-aware optimization của lightweight PPE detector trên RK3588S NPU, trong đó B (Edge AI) là trọng tâm hơn một chút.
   - DAHD-YOLO trên RK3588 báo thời gian một ảnh INT8 là 79.1 ms trong Table 6 (văn bản cùng tr.18 ghi đơn luồng 0.1162 s nhưng trùng với số 116.2 ms của dòng FP16 trong bảng), không đủ thời gian thực nếu chạy tuần tự một luồng và phải dùng thread pool đa luồng để đạt 50.2 FPS ở 720P.
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
     - ``Helmet``, ``NoHelmet``, ``NoVest``, ``Vest``, ``Person``
   * - **Yêu cầu thời gian thực**
     - **60 FPS** (tương đương ngân sách thông lượng :math:`\le 16.67\text{ ms}` mỗi khung hình)

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
      - Helmet / NoHelmet / NoVest / Vest / Person
      - small objects
      - multi-scale
      - lighting and noise (low-light)
      - occlusion
      - confusable classes (Helmet/NoHelmet, Vest/NoVest)
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

Số liệu Table 6 (nguyên văn từ paper): DAHD-YOLO INT8 gồm Size 8.8M, FPS 720P **50.2**/1080P 43.8/1440P 37.7, mAP50 74.36%, Inference-Time 79.1ms, Power 7W. Lưu ý điểm bất nhất nội bộ của bài báo: văn bản tr.18 ghi bản INT8 chạy đơn luồng mất 0.1162 s (116.2 ms), nhưng trong Table 6 cùng trang thì 116.2 ms thuộc dòng FP16 còn dòng INT8 là 79.1 ms (xem :doc:`Tiêu chí thân thiện NPU </contents/02-nen-tang-rk3588/05-yolo-tren-rk3588/03-tieu-chi-than-thien-npu>` mục 2.3). Dù tính theo 116.2 ms (khoảng 8.6 FPS tuần tự) hay 79.1 ms (khoảng 12.6 FPS tuần tự), chạy đơn luồng đều không đủ mốc 25 FPS của bài báo và càng xa mục tiêu **60 FPS** của dự án, nên bài báo phải dùng thread pool đa luồng khai thác 3 nhân NPU để đưa thông lượng lên 50.2 FPS.

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
