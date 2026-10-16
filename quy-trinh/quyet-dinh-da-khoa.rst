:tocdepth: 1

******************
Quyết định đã khóa
******************

.. admonition:: Tóm tắt

   - Protocol v1 khoá input đánh giá là LetterBox 640×640 vuông, `rect=False`, mọi backend, vì NPU chỉ nhận 640×640 còn `model.val()` trên `.pt` tự bật `rect=True`.
   - Calibration INT8 dùng 300 ảnh train, ≥ 20 ảnh/class, seed 42, đã LetterBox, PNG; RKNN tự resize ảnh khác kích thước input mà không báo (đo thử).
   - NPU latency tầng 1 là median 5 lần `eval_perf(fix_freq=True)` trong phiên riêng, vì dao động 18.5–22.4 ms giữa các lần.
   - Post-processing tầng 2 dùng mặc định predict (conf 0.25, IoU 0.7, max_det 300); E2E tầng 2 là Pre + NPU + post, không gồm giải mã file.
   - Seed 42 cho mọi phase, 43 và 44 chỉ ở Phase 10 cho model chính; mean ± std dùng std mẫu (`ddof=1`).

.. _8a2-quyết-định-đã-khoá-trong-protocol-v1:

Quyết định đã khoá trong protocol v1
====================================

.. list-table::
   :header-rows: 1

   * - Việc
     - Chốt
     - Căn cứ
   * - Input khi đánh giá
     - LetterBox 640×640 vuông, ``rect=False``, mọi backend
     - NPU chỉ nhận 640×640; ``model.val()`` trên ``.pt`` tự bật ``rect=True`` (:ref:`AI Quality <51-ai-quality>`)
   * - Calibration INT8
     - 300 ảnh train, ≥ 20 ảnh/class, seed 42, đã LetterBox, PNG
     - ``ultralytics/engine/exporter.py`` dòng 1044: *">300 images recommended for INT8 calibration"*; RKNN tự resize ảnh khác kích thước input mà không báo (đo thử)
   * - NPU latency tầng 1
     - Median 5 lần ``eval_perf(fix_freq=True)``, phiên riêng
     - Dao động 18.5–22.4 ms giữa các lần (:ref:`Hardware Performance <53-hardware-performance>`)
   * - Post-processing tầng 2
     - Mặc định predict: conf 0.25, IoU 0.7, max_det 300
     - Đo tốc độ lúc triển khai (:ref:`Hardware Performance <53-hardware-performance>`)
   * - E2E tầng 2
     - Pre + NPU + post, không gồm giải mã file
     - Pipeline camera không có bước giải mã
   * - Khoá tần số
     - Governor ``performance`` (hoặc ``userspace`` ở tần số tối đa do ``eval_perf`` đặt)
     - RKNPU2 User Guide trang PDF 72–73
   * - Seed
     - 42 cho mọi phase; 43, 44 chỉ ở Phase 10 cho model chính; mean ± std dùng std mẫu (``ddof=1``); bảng phần cứng dùng run seed 42
     - Quy tắc seed, mục 7; ``ai/automation/tables.py``
