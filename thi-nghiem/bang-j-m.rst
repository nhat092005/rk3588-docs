:tocdepth: 1

************
Bảng J đến M
************

.. admonition:: Tóm tắt

   - Table J là bảng trọng tâm nên có trong paper, so YOLOv8n FP16, INT8 PTQ, structured pruning, ReLU / LeakyReLU + INT8 và Proposed HW-aware; mọi ô còn [TBD].
   - `AP head` và `AP self_clothes` là 2 tín hiệu vi phạm, ít mẫu nhất và dễ bị ảnh hưởng nhất khi nén model.
   - Table K ghi hỗ trợ đa nhân theo tài liệu Rockchip: `ConvExSwish` "暂不支持" (nếu cùng op với ConvolutionSwish), Resize "不支持", Conv không activation "支持".
   - Table L ghi Peak RAM (VmRSS), NPU memory, Avg CPU và nhiệt độ; Power và Energy/frame nằm ngoài v1 vì chưa có cách đo đã kiểm chứng.
   - Table M có dòng Baseline, A (INT8), B (pruning), C (ReLU), D (cả 3); ✗ ở cột INT8 nghĩa là model chạy FP16 trên NPU; ô số còn [TBD].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _table-j-main-accuracyefficiency-comparison:

Table J. Main Accuracy–Efficiency Comparison
============================================

   Bảng trọng tâm nên có trong paper.

.. list-table::
   :header-rows: 1

   * - Model / Method
     - mAP50-95
     - ΔmAP so với FP32
     - AP head
     - AP self_clothes
     - Params
     - GFLOPs
     - RKNN Size
     - NPU latency
     - E2E P95
     - Throughput FPS
     - Peak RAM
   * - YOLOv8n FP16
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8n INT8 PTQ
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - Structured pruning
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - Structured pruning + INT8
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - Activation ReLU / LeakyReLU + INT8
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - Proposed HW-aware
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]

``AP head`` và ``AP self_clothes`` là 2 tín hiệu vi phạm, ít mẫu nhất (Table A), dễ bị ảnh hưởng nhất khi nén model.

--------------

.. _table-k-operator--layer-bottleneck-profile:

Table K. Operator / Layer Bottleneck Profile
============================================

**Mục đích:** rất quan trọng nếu muốn claim hardware-aware contribution. Thời gian từng layer và DDR/NPU cycles lấy từ bảng layer của ``eval_perf`` khi ``perf_debug=True`` (tầng 1, phiên 2); bảng này sinh tự động ở ``results/<dataset>/table_K_layers.md``. Build log ``RKNN_LOG_LEVEL=3`` (``runs/<run_id>/logs/export_int8_*.log``) có cycles ước tính lúc build, dùng để đối chiếu.

.. list-table::
   :header-rows: 1

   * - Layer
     - Loại op
     - Chạy trên (CPU/NPU)
     - Hỗ trợ đa nhân trên RK3588
     - Thời gian (µs)
     - % tổng
     - DDR/NPU cycles
     - Ghi chú
   * - [TBD]
     - Conv + SiLU (``ConvExSwish``)
     - [TBD]
     - Tạm chưa ("暂不支持", 3.2.17 ConvolutionSwish), nếu 2 tên là cùng 1 op
     - [TBD]
     - [TBD]
     - [TBD]
     - 
   * - [TBD]
     - Resize (upsample trong neck)
     - [TBD]
     - Không ("不支持", 3.2.54)
     - [TBD]
     - [TBD]
     - [TBD]
     - 
   * - [TBD]
     - Conv không activation
     - [TBD]
     - Có ("支持", 3.2.5)
     - [TBD]
     - [TBD]
     - [TBD]
     - 
   * - [TBD]
     - Concat
     - [TBD]
     - Có (RKNPU2 User Guide, trang PDF 27)
     - [TBD]
     - [TBD]
     - [TBD]
     - 

Cột "Hỗ trợ đa nhân" theo tài liệu Rockchip, đã kiểm ở :ref:`Research problem đề xuất <21-research-problem-đề-xuất>`. Các câu hỏi bảng phải trả lời:

.. code:: text

   Operator nào chiếm nhiều latency?
   Operator không hỗ trợ đa nhân chiếm bao nhiêu % thời gian?
   Có operator nào chạy CPU không?
   Layer nào DDR cycles cao hơn NPU cycles (nghẽn vì di chuyển dữ liệu)?
   Block nào FLOPs không cao nhưng latency lại cao?

--------------

.. _table-l-hardware-resource-usage:

Table L. Hardware Resource Usage
================================

Đo theo :ref:`Resource & Energy <54-resource--energy>`, trong lúc chạy tầng 2.

.. list-table::
   :header-rows: 1

   * - Model / Precision
     - Peak RAM (MB, VmRSS)
     - NPU memory (MB)
     - Avg CPU (%)
     - Temp start (°C)
     - Temp end (°C)
   * - YOLOv8n FP16
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - YOLOv8n INT8
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - Proposed
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]

NPU memory lấy qua ``RKNN_QUERY_MEM_SIZE`` nếu dùng được (:ref:`Resource & Energy <54-resource--energy>`). Power và Energy/frame nằm ngoài v1, chưa có cách đo đã kiểm chứng.

--------------

.. _table-m-ablation-study:

Table M. Ablation Study
=======================

   Đề xuất là bảng chính trong paper. Mỗi dòng bật/tắt từng thay đổi ở :ref:`Optimization comparison (trọng tâm) <62-optimization-comparison-trọng-tâm>` để tách đóng góp của từng cái.

.. list-table::
   :header-rows: 1

   * - Exp
     - INT8
     - Structured pruning
     - Activation ReLU
     - Thay đổi khác
     - mAP50-95
     - ΔmAP so với FP32
     - AP head
     - AP self_clothes
     - NPU latency
     - Throughput FPS
   * - Baseline
     - ✗
     - ✗
     - ✗
     - -
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - A
     - ✓
     - ✗
     - ✗
     - -
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - B
     - ✗
     - ✓
     - ✗
     - -
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - C
     - ✗
     - ✗
     - ✓
     - -
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
   * - D
     - ✓
     - ✓
     - ✓
     - -
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]
     - [TBD]

**Cách đọc:**

- **✓** = thay đổi đó được áp dụng trong thí nghiệm.
- **✗** = không áp dụng. Riêng ✗ ở cột INT8 nghĩa là model chạy FP16 trên NPU (giống dòng đầu của Table J).
- **A, B, C so với Baseline** = biết riêng mỗi thay đổi đóng góp bao nhiêu.
- **D so với A, B, C** = biết kết hợp cả 3 có tốt hơn từng cái riêng lẻ không.
- **Tổ hợp 2 thay đổi** (vd INT8 + pruning, đã có ở Table J) chưa có trong bảng; chỉ thêm nếu D khác xa tổng đóng góp của A, B, C.

Ablation phải giúp trả lời:

.. code:: text

   INT8 đóng góp bao nhiêu?
   Pruning đóng góp bao nhiêu?
   Đổi activation đóng góp bao nhiêu (có mở khoá chạy đa nhân không)?
   Kết hợp có tốt hơn thật không?
