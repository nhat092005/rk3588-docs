:tocdepth: 1

*******************
Phase 9-10: chốt số
*******************

.. admonition:: Tóm tắt

   - Phase 9 kiểm tra model đề xuất trên camera OV13855 qua pipeline NV12, RGB, LetterBox, RKNN (NPU), NMS. Tệp `ai/board/camera.py` chưa có.
   - Phase 9 chạy tới khi nhiệt độ ổn định (tăng không quá 1°C trong 10 phút liền) rồi thêm 30 phút. Các ngưỡng này chốt trước khi đo.
   - Phase 10 chạy `make phase10` với seed 43, 44 cho `yolov8n_baseline` và model đề xuất để lấy mean ± std.
   - Phase 10 thêm tầng 1 INT8 của YOLOv8n seed 43 để kiểm giả định "cùng kiến trúc thì thời gian NPU như nhau".
   - Tiêu chí xong của Phase 10: Table D, F, J, M có mean ± std cho các model chính và chênh lệch chính của đề tài lớn hơn std.

.. _phase-9-camera--real-world-evaluation:

Phase 9. Camera / real-world evaluation
=======================================

**Mục tiêu:** kiểm tra model đề xuất trên camera thật.

.. code:: text

   OV13855 → NV12 → RGB → LetterBox → RKNN (NPU) → NMS → cảnh báo PPE

.. list-table::
   :header-rows: 1

   * - Việc
     - File
   * - Pipeline camera trên board, dùng lại ``preprocess``, ``postprocess``, ``ResourceMonitor``
     - ``ai/board/camera.py`` (chưa có), ``ai/board/common.py``
   * - Ghi FPS, nhiệt độ NPU mỗi phút
     - ``runs/<run_id>/bench/camera_<ngày>.json``

- ☐ Code pipeline camera, thêm target ``make bench-camera``
- ☐ Chạy tới khi nhiệt độ ổn định (tăng không quá 1°C trong 10 phút liền), rồi chạy thêm 30 phút. Các ngưỡng 1°C, 10 phút, 30 phút là giá trị chọn, chốt trước khi đo
- ☐ Báo FPS, latency mean/P95, CPU, RAM trong 30 phút ổn định, đồng thời so sánh FPS lúc đầu và lúc ổn định
- ☐ Lưu video/ảnh mẫu các trường hợp đúng, sót, nhầm

**Tiêu chí xong:** chạy hết 30 phút ổn định không lỗi, có đường FPS và nhiệt độ theo thời gian.

--------------

.. _phase-10-chốt-số-liệu-seed-43-44:

Phase 10. Chốt số liệu (seed 43, 44)
====================================

**Mục tiêu:** mean ± std cho các model của bảng so sánh chính (quy tắc seed, mục 7).

**Điều kiện:** Phase 7 đã chọn model đề xuất (Phase 8, 9 xong hoặc chạy song song).

**Lệnh:**

.. code:: bash

   make phase10 DATASET=<ds> MODELS=yolov8n_baseline,<model đề xuất>

Với mỗi model × seed 43, 44: train, export FP16/INT8, evaluate RKNN FP16/INT8. Thêm tầng 1 INT8 của YOLOv8n seed 43 để kiểm giả định "cùng kiến trúc thì thời gian NPU như nhau", rồi chạy ``make tables``. Model đề xuất phải có config theo tên ``ai/automation/configs/<ds>_<model>.yaml``. Cần Runbook bước 4 (tầng 1).

- ☐ ``phase10`` xong cho YOLOv8n và model đề xuất
- ☐ So ``tier1_int8_AUTO.json`` của YOLOv8n seed 42 và 43
- ☐ Kiểm lại các kết luận 1 seed ở Phase 2 (chọn dataset) và Phase 7 (chọn candidate) với std thật, sau đó ghi kết quả vào ``tmp/02_decisions/``

**Tiêu chí xong:** Table D, F, J, M có mean ± std cho các model chính, đồng thời chênh lệch chính của đề tài lớn hơn std.
