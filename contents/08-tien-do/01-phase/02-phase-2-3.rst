:tocdepth: 1

*************************
Phase 2-3: train và quant
*************************

.. admonition:: Tóm tắt

   - Phase 2 train YOLOv8n và YOLOv8s seed 42 trên sfchd_5class và sfchd_shel5k. Tất cả mục kiểm trong phase này chưa đánh dấu xong.
   - Chọn dataset theo Table D (mAP50-95 trên sfchd_test, AP head, self_clothes), ghi vào tmp/02_decisions/, và ghi rõ quyết định dựa trên 1 seed.
   - Phase 3 trả lời Case B: quantize mất bao nhiêu accuracy và class nào mất nhiều nhất. Các mục kiểm của phase này cũng chưa xong.
   - Accuracy của .rknn chỉ đo được trên board vì simulator của RKNN-Toolkit2 không chạy file nạp bằng load_rknn (API Reference mục 2.7, trang PDF 16).
   - Giả thuyết cần kiểm: INT8 giảm mAP50-95 rõ rệt còn FP16 không giảm, và output INT8 của Ultralytics dùng chung 1 scale lượng tử (0.004222) nên toạ độ box có bước khoảng 2.7 px.

.. _phase-2-train-baseline-yolov8ns:

Phase 2. Train baseline YOLOv8n/s
=================================

**Mục tiêu:** accuracy FP32 của baseline (seed 42) trên cả 2 lựa chọn dataset.

**Lệnh:**

.. code:: bash

   make phase2 DATASET=sfchd_5class
   make phase2 DATASET=sfchd_shel5k

Mỗi lệnh: train YOLOv8n và YOLOv8s seed 42 (2 run), kiểm chéo evaluator trên run YOLOv8n, rồi ``make tables``.

- ☐ ``phase2`` xong cho ``sfchd_5class``
- ☐ ``phase2`` xong cho ``sfchd_shel5k``
- ☐ ``eval/crosscheck_sfchd_test.json`` có ``"passed": true`` ở cả 2 dataset
- ☐ Chọn dataset theo Table D (mAP50-95 trên ``sfchd_test``, AP ``head``, ``self_clothes``), ghi vào ``tmp/02_decisions/``, ghi rõ quyết định dựa trên 1 seed (quy tắc seed, mục 7)

**Bảng:** ``results/<ds>/table_A_dataset.md``, ``table_B_training.md``, ``table_D_fp32.md``.

**Tiêu chí xong:** Table D đủ YOLOv8n/s ở cả 2 dataset và đã chọn dataset. Các phase sau chỉ chạy trên dataset đã chọn.

--------------

.. _phase-3-quantization-fp16--int8:

Phase 3. Quantization FP16 / INT8
=================================

**Mục tiêu:** trả lời Case B (:ref:`Ví dụ gap có thể xuất hiện sau benchmark <43-ví-dụ-gap-có-thể-xuất-hiện-sau-benchmark>`): quantize mất bao nhiêu accuracy, class nào mất nhiều nhất.

**Điều kiện:** Phase 2 xong, có thể ssh tới board được. Accuracy của ``.rknn`` chỉ đo được trên board: simulator của RKNN-Toolkit2 không chạy file nạp bằng ``load_rknn`` (API Reference mục 2.7, trang PDF 16: *"When target is set to None, the build or hybrid_quantization interface needs to be called first."*).

**Lệnh:** ``make phase3 DATASET=<ds>``

Với mỗi run của dataset (2 run): export FP16, export INT8 (300 ảnh calibration), complexity, evaluate ONNX, evaluate RKNN FP16, evaluate RKNN INT8, rồi chạy ``make tables``. ``evaluate BACKEND=rknn`` tự chép model và ảnh lên board, chạy inference ở board (``ai/board/infer_dump.py``), chép output về và tính NMS, AP trên PC (:ref:`AI Quality <51-ai-quality>`), mất khoảng 1–2 phút mỗi lần.

- ☐ ``phase3`` xong
- ☐ ``eval/onnx_fp32_*.json`` lệch ``pt_fp32`` không quá 0.001 (ONNX export đúng)
- ☐ Table F: class nào mất accuracy nhiều nhất
- ☐ Kiểm giả thuyết từ lần chạy thử trước (model nháp 5 epoch, 7 class. Số của lần đó không được trích vì không dùng làm kết quả): INT8 giảm mAP50-95 rõ rệt còn FP16 không giảm. Output INT8 của Ultralytics chia toạ độ box cho 640 rồi dùng chung 1 scale lượng tử với score (0.004222), nên toạ độ box chỉ có bước khoảng 640 × 0.004222 ≈ 2.7 px

**Bảng:** ``table_E_complexity.md``, ``table_F_quantization.md``.

**Tiêu chí xong:** Table E, F không còn ``[TBD]``, và ``SOURCES.md`` không có lỗi.
