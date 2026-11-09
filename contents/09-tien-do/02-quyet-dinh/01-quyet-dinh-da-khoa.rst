:tocdepth: 1

******************
Quyết định đã khóa
******************

.. admonition:: Tóm tắt

   - Protocol v1 khoá input đánh giá là LetterBox 640×640 vuông, `rect=False`, mọi backend, vì NPU chỉ nhận 640×640 còn `model.val()` trên `.pt` tự bật `rect=True`.
   - Calibration INT8 dùng 300 ảnh train, ≥ 20 ảnh/class, seed 0, đã LetterBox, PNG. RKNN tự resize ảnh khác kích thước input mà không báo (đo thử).
   - NPU latency tầng 1 là median 5 lần `eval_perf(fix_freq=True)` trong phiên riêng, vì dao động 18.5–22.4 ms giữa các lần.
   - Post-processing tầng 2 dùng mặc định predict (conf 0.25, IoU 0.7, max_det 300). E2E tầng 2 là Pre + NPU + post, không gồm giải mã file.
   - Seed 0 (mặc định Ultralytics) cho mọi phase, mỗi model chỉ một seed nên kết luận ghi rõ "1 seed".

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
     - NPU chỉ nhận 640×640. Hàm ``model.val()`` trên ``.pt`` tự bật ``rect=True``
   * - Calibration INT8
     - 300 ảnh train, ≥ 20 ảnh/class, seed 0, đã LetterBox, PNG
     - ``ultralytics/engine/exporter.py`` dòng 1044: *">300 images recommended for INT8 calibration"*. RKNN tự resize ảnh khác kích thước input mà không báo (đo thử)
   * - NPU latency tầng 1
     - Median 5 lần ``eval_perf(fix_freq=True)``, phiên riêng
     - Dao động 18.5–22.4 ms giữa các lần
   * - Post-processing tầng 2
     - Mặc định predict: conf 0.25, IoU 0.7, max_det 300
     - Đo tốc độ lúc triển khai
   * - E2E tầng 2
     - Pre + NPU + post, không gồm giải mã file
     - Pipeline camera không có bước giải mã
   * - Khoá tần số
     - Governor ``performance`` (hoặc ``userspace`` ở tần số tối đa do ``eval_perf`` đặt)
     - RKNPU2 User Guide trang PDF 72–73
   * - Seed
     - 0 cho mọi phase, mỗi model chỉ một seed nên kết luận ghi rõ "1 seed". Bảng phần cứng dùng run seed 0
     - Quy tắc seed, mục 7, và ``ai/automation/report/tables.py``
