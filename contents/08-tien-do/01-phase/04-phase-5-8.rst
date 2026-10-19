:tocdepth: 1

*****************
Phase 5-8: tối ưu
*****************

.. admonition:: Tóm tắt

   - Phase 5 thêm YOLO11n/s bằng model, config và sửa `MODELS` trong `ai/automation/pipeline.py`. Tiêu chí xong là có dòng YOLO11 ở D–L hoặc ghi rõ lý do loại.
   - Phase 6 tìm bottleneck bằng số đo từ `table_K_layers.md`. Hiện tượng `Transpose` chạy CPU (590 µs / 20,663 µs) chỉ thấy trên model nháp, cần kiểm lại trên model thật.
   - Phase 7 có các candidate: structured pruning, SiLU sang ReLU / LeakyReLU, `op_target`, mixed precision, lighter head và input resolution. Mục `op_target` hiện là `NotImplementedError`.
   - Phase 7 train 1 seed (42), kết luận ghi rõ "1 seed", và chênh lệch phải được xác nhận lớn hơn std ở Phase 10.
   - Phase 8 chạy các dòng Baseline, A, B, C, D của Table M, vẽ Figure 3 (Pareto) và Figure 5, và trả lời 4 câu hỏi dưới Table M.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _phase-5-multi-model-yolo11ns:

Phase 5. Multi-model YOLO11n/s
==============================

**Mục tiêu:** không phụ thuộc vào 1 họ model (:ref:`Model comparison <61-model-comparison>`).

**Điều kiện:** Phase 2–4 chạy trọn với YOLOv8.

.. list-table::
   :header-rows: 1

   * - Việc
     - File cần tạo / sửa
   * - Thêm model
     - ``ai/models/yolo11n_baseline.py``, ``yolo11s_baseline.py`` (``WEIGHTS = "yolo11n.pt"``, ``"yolo11s.pt"``)
   * - Thêm config
     - ``ai/automation/configs/<ds>_yolo11{n,s}_baseline.yaml`` (chép config YOLOv8 tương ứng)
   * - Cho phase chạy cả YOLO11
     - ``ai/automation/pipeline.py``: thêm 2 model vào ``MODELS``

Sau đó chạy lại ``make phase2/3/4 DATASET=<ds>`` (các bước YOLOv8 đã có sẽ được bỏ qua).

- ☐ Thêm model, config, sửa ``MODELS``
- ☐ ``phase2``, ``phase3``, ``phase4`` xong cho YOLO11
- ☐ Ghi op không hỗ trợ hoặc chạy CPU (``cpu_ops`` trong ``tier1_*.json``)

**Tiêu chí xong:** có dòng YOLO11 ở D–L, hoặc ghi rõ lý do loại.

--------------

.. _phase-6-bottleneck-analysis:

Phase 6. Bottleneck analysis
============================

**Mục tiêu:** tìm bottleneck thật bằng số đo. Đây là phase quyết định research gap (:ref:`Đúng cách <42-đúng-cách>`).

**Dữ liệu:** ``results/<ds>/table_K_layers.md`` (theo loại op và 20 layer lâu nhất, CPU/NPU, DDR/NPU cycles), ``tier1_int8_<mask>_layers.json``, Table E, G.

- ☐ Trả lời 5 câu hỏi dưới Table K (Guide mục 7)
- ☐ So ``tier1_int8_CORE_0_layers.json`` với ``tier1_int8_CORE_0_1_2_layers.json`` theo từng layer: op nào không nhanh lên khi thêm core, đồng thời đối chiếu ``ConvExSwish`` với ``ConvolutionSwish`` (:ref:`Research problem đề xuất <21-research-problem-đề-xuất>`)
- ☐ Op chạy trên CPU: đo thử với model nháp ngày 2026-09-26 thấy ``Transpose`` chạy CPU (590 µs / 20,663 µs), cần kiểm lại trên model thật
- ☐ So FLOPs (Table E) với latency (Table G) giữa các model (Case C)
- ☐ Ghi research gap và hướng tối ưu vào ``tmp/02_decisions/``, có số đo làm căn cứ

**Tiêu chí xong:** có ít nhất 1 bottleneck đo được bằng số, dẫn ra 1 hướng tối ưu cụ thể.

--------------

.. _phase-7-proposed-optimization:

Phase 7. Proposed optimization
==============================

**Mục tiêu:** cải thiện hiệu quả trên RK3588S mà giữ accuracy, theo bottleneck của Phase 6.

.. list-table::
   :header-rows: 1

   * - Candidate (:ref:`Ví dụ gap có thể xuất hiện sau benchmark <43-ví-dụ-gap-có-thể-xuất-hiện-sau-benchmark>`, 6.2)
     - Code cần viết
     - Train lại?
   * - Structured pruning + fine-tune
     - Chưa có
     - Có
   * - Activation SiLU → ReLU / LeakyReLU
     - Model mới trong ``ai/models/``, config mới
     - Có
   * - ``op_target`` cho op không hỗ trợ đa nhân
     - ``ai/core/rknn/deploy.py`` (hiện ``NotImplementedError``)
     - Không
   * - Mixed precision (``hybrid_quantization_step1/2``)
     - ``ai/core/rknn/deploy.py``
     - Không
   * - Lighter head, input resolution
     - Model/config mới
     - Có

Candidate cần train lại: thêm model + config như Phase 5 rồi chạy ``make phase2/3/4``. Candidate không train lại: thêm bước export mới vào ``pipeline.py`` phase3.

- ☐ Viết code cho candidate được chọn
- ☐ Train 1 seed (42), chạy đủ phase 3–4. Phần kết luận ghi rõ "1 seed" (quy tắc seed, mục 7)
- ☐ Table J

**Tiêu chí xong:** có model đề xuất tốt hơn baseline trên RK3588S (1 seed), và xác nhận chênh lệch lớn hơn std ở Phase 10.

--------------

.. _phase-8-ablation:

Phase 8. Ablation
=================

**Mục tiêu:** tách đóng góp của từng thay đổi (Table M).

- ☐ Chạy các dòng Baseline, A, B, C, D của Table M (mỗi dòng: phase 2–4)
- ☐ Thêm tổ hợp 2 thay đổi nếu D khác xa tổng đóng góp của A, B, C
- ☐ Vẽ Figure 3 (Pareto) và Figure 5 (AP từng class) ở mục 10 từ ``results/<ds>/tables.csv``

**Tiêu chí xong:** trả lời được 4 câu hỏi dưới Table M.
