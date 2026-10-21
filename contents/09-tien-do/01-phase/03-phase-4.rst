:tocdepth: 1

**********************
Phase 4: đo trên board
**********************

.. admonition:: Tóm tắt

   - Phase 4 đo tốc độ và tài nguyên theo protocol v1 bằng `make phase4 DATASET=<ds>` cho run seed 42 của YOLOv8n và YOLOv8s.
   - Tầng 1 đo FP16, INT8 (AUTO) và INT8 ở `CORE_0`, `CORE_0_1`, `CORE_0_1_2` bằng `benchmark-npu`, cho các bảng G, I, K, L.
   - Tầng 2 gồm `bench-board`, `bench-board-cpu` (`.onnx`, 4 thread), `bench-board-throughput` (1 và 3 context) và `bench-gpu` (GPU PC, tham chiếu).
   - Hai mục kiểm `phase4` xong và `SOURCES.md` không có lỗi khoá tần số chưa đánh dấu. Tiêu chí xong là G, H, I, K, L không còn `[TBD]`.

.. _phase-4-benchmark-trên-board:

Phase 4. Benchmark trên board
=============================

**Mục tiêu:** tốc độ và tài nguyên theo protocol v1.

**Điều kiện:** Phase 3 xong và Runbook bước 4 và 9.

**Lệnh:** ``make phase4 DATASET=<ds>``, sau đó Runbook bước 11.

Với run seed 42 của YOLOv8n và YOLOv8s:

.. list-table::
   :header-rows: 1

   * - Đo
     - Lệnh make bên trong
     - Bảng
   * - Tầng 1 FP16, INT8 (AUTO) và INT8 ở ``CORE_0``, ``CORE_0_1``, ``CORE_0_1_2``
     - ``benchmark-npu``
     - G, I, K, L
   * - Tầng 2 FP16, INT8 trên NPU
     - ``bench-board``
     - G, H, L
   * - Tầng 2 ``.onnx`` trên CPU board, 4 thread
     - ``bench-board-cpu``
     - H
   * - Throughput 1 context ở 4 core_mask, và 3 context ``CORE_0,CORE_1,CORE_2``
     - ``bench-board-throughput``
     - I
   * - GPU PC (tham chiếu)
     - ``bench-gpu``
     - H

- ☐ ``phase4`` xong
- ☐ ``SOURCES.md`` không có lỗi khoá tần số

**Bảng:** ``table_G_latency.md``, ``table_H_hardware.md``, ``table_I_deployment.md``, ``table_K_layers.md``, ``table_L_resource.md``.

**Tiêu chí xong:** G, H, I, K, L không còn ``[TBD]``.
