:tocdepth: 1

*******
So sánh
*******

.. admonition:: Tóm tắt

   - Mọi phép so sánh đo theo protocol v1, chỉ khác mốc 1 yếu tố. Không so mAP trực tiếp với paper SFCHD vì split gốc không được phát hành.
   - Model comparison gồm YOLOv8n, YOLOv8s và sau đó YOLO11n, YOLO11s. Không dùng YOLOv5n vì qua Ultralytics nó là YOLOv5nu với head không anchor.
   - YOLOv8s là model duy nhất có số FPS trên RK3588 trong kho tài liệu (INT8 70.9 FPS, FP16 32.9 FPS ở 720P), chỉ dùng để kiểm độ hợp lý.
   - Optimization comparison chia 3 nhóm: nén model, cấu hình triển khai (`core_mask`, nhiều luồng) và hardware-aware (ReLU / LeakyReLU, model đề xuất).
   - Chưa có bằng chứng structured pruning tăng tốc trên RK3588 nên phải đo. Mục `autosparsity` của Rockchip ghi "Only supports RK3576 target platform".
   - Hardware comparison bắt buộc gồm CPU board và NPU FP16, INT8. GPU RTX 3050 Laptop chỉ tham chiếu, code structured pruning chưa có.

.. contents:: Trong trang này
   :local:
   :depth: 1

Mọi phép so sánh trong mục này đo theo Evaluation Protocol v1 (:ref:`Evaluation Protocol v1 <50-evaluation-protocol-v1>`): cùng dataset, split, kích thước input, metric và cách đo. Mỗi phép so sánh chỉ khác mốc của nó đúng 1 yếu tố.

.. _61-model-comparison:

Model comparison
================

.. code:: text

   YOLOv8n
   YOLOv8s
   YOLO11n, YOLO11s (giai đoạn sau, mục 8 Phase 5)

- **YOLOv8n/s**: đã có code (``ai/models/yolov8n_baseline.py``, ``yolov8s_baseline.py``) và kế hoạch train (:ref:`Dataset <02-dataset>`). YOLOv8s là model duy nhất có số FPS trên chính RK3588 trong kho tài liệu: INT8 70.9 FPS, FP16 32.9 FPS ở 720P (:download:`dahd_yolo_rk3588_2025.pdf <../../_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf>`, Table 6, tr.18). Số này chỉ dùng để kiểm độ hợp lý, không so trực tiếp (khác dataset, khác kích thước input).
- **Không dùng YOLOv5n**: chạy qua Ultralytics thì nó là YOLOv5nu, dùng head không anchor giống YOLOv8 (``ultralytics/utils/downloads.py`` dòng 27: ``yolov5{k}{resolution}u.pt``), khác YOLOv5 gốc mà các paper CHV, SHEL5K, SFCHD dùng, nên cũng không so được với số của paper.
- **Không so mAP trực tiếp với paper SFCHD**: split gốc không được phát hành (``data/sfchd/DATA_CARD.md``), paper dùng ảnh 1333×800 và MMDetection (tr.9). Mọi so sánh accuracy là so sánh nội bộ dưới cùng protocol v1.

.. _62-optimization-comparison-trọng-tâm:

Optimization comparison (trọng tâm)
===================================

.. list-table::
   :header-rows: 1

   * - Nhóm
     - Biến thể
     - So với
     - Yếu tố thay đổi
     - Train lại?
   * - 1. Nén model
     - FP16 baseline
     - -
     - Mốc gốc
     - -
   * - 
     - INT8 PTQ
     - FP16 baseline
     - Datatype FP16 → INT8
     - Không
   * - 
     - Structured pruning (FP16)
     - FP16 baseline
     - Cắt channel/filter ít quan trọng
     - Có (fine-tune)
   * - 
     - Structured pruning + INT8
     - INT8 PTQ
     - Thêm pruning
     - Có (fine-tune)
   * - 2. Cấu hình triển khai (cùng model INT8)
     - ``core_mask`` ``CORE_0`` / ``CORE_0_1_2``
     - ``core_mask`` ``AUTO``
     - Số core NPU
     - Không
   * - 
     - Nhiều luồng (thread pool)
     - 1 luồng
     - Số context chạy song song, đo Throughput FPS
     - Không
   * - 3. Hardware-aware
     - Activation ReLU / LeakyReLU
     - Activation SiLU
     - Activation (giả thuyết :ref:`Research problem đề xuất <21-research-problem-đề-xuất>`)
     - Có
   * - 
     - Model đề xuất
     - Baseline tốt nhất
     - Theo bottleneck thật tìm ở mục 4
     - Có

- **FP16** chạy được trên NPU RK3588 (DAHD-YOLO có số FP16, tr.18). Export: ``make export-npu RUN=<run_id> PREC=fp16``.
- **Pruning** chỉ tính structured pruning (cắt hẳn channel/filter để model nhỏ đi). Công cụ ``autosparsity`` của Rockchip chỉ tăng tốc sparse inference trên RK3576: ``3rdparty/rknn-toolkit2/autosparsity/README.md`` ghi *"Only supports RK3576 target platform"*. Chưa có bằng chứng structured pruning tăng tốc trên RK3588, phải đo.

.. _63-hardware-comparison:

Hardware comparison
===================

.. list-table::
   :header-rows: 1

   * - Thiết bị
     - Vai trò
     - Chạy gì
   * - CPU của board (4 nhân Cortex-A76 + 4 nhân Cortex-A55)
     - Bắt buộc: cho thấy lợi ích của NPU trên cùng thiết bị
     - File ``.onnx`` FP32 (``weights/best.onnx``, export cùng opset 19 với ``.rknn``) bằng ONNX Runtime 1.23.2 (đã cài trong ``.venv-board``), ghi số thread
   * - NPU của board, FP16
     - Bắt buộc
     - ``.rknn`` FP16
   * - NPU của board, INT8
     - Bắt buộc
     - ``.rknn`` INT8
   * - GPU của PC: NVIDIA GeForce RTX 3050 Laptop
     - Chỉ tham chiếu, không phải thiết bị triển khai
     - PyTorch FP32

Nguồn: CPU theo :download:`01_HYY_Rockchip_RK3588_Datasheet.pdf <../../_assets/pdf/papers/05_rk3588/01_vendor_docs/01_datasheet/01_HYY_Rockchip_RK3588_Datasheet.pdf>` (*"quad-core Cortex-A76 and quad-core Cortex-A55"*). GPU theo log train ``tmp/05_training-logs/`` (``CUDA:0 (NVIDIA GeForce RTX 3050 Laptop GPU, 3762MiB)``). GPU Mali trên board nằm ngoài phạm vi, vì repo chưa có pipeline chạy model trên Mali.

**Code cho các phép so sánh:**

- ☒ Export FP16: ``ai/automation/export_npu.py --quantize 16``
- ☒ Chạy ``.onnx`` trên CPU của board (ONNX Runtime): ``ai/board/bench_cpu_onnx.py``
- ☒ Nhiều context song song để đo Throughput FPS: ``ai/board/bench_throughput.py``
- ☐ Code structured pruning + fine-tune (viết ở Phase 7, sau khi Phase 6 cho thấy cần)
