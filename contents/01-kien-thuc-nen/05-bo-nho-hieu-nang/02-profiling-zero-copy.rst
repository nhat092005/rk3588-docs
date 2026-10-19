:tocdepth: 1

**********************
Profiling và zero-copy
**********************

.. admonition:: Trang này trả lời

   - đo thời gian, tải và bộ nhớ bằng công cụ nào, và mỗi số đo có nghĩa gì?
   - làm sao tránh copy dữ liệu giữa CPU và NPU, và có yêu cầu căn lề gì?

.. admonition:: Tóm tắt

   - `perf_debug` cho thời gian từng lớp [T1 API232 tr.16], nhưng chế độ này thêm mã debug và "some parallel mechanisms may be disabled" nên thời gian dài hơn [T1 UG232 tr.177].
   - Cột `NPUCycles` hiện chỉ tính cho Conv [T1 UG232 tr.140], và NPU load không trực tiếp biểu diễn MAC utilization thực [T1 UG232 tr.137].
   - `RW(KB)` và `DDRCycles` là số đo thực hay tính từ mô hình thì `unknown`.`eval_memory` báo dung lượng bộ nhớ của model, không phải băng thông.
   - Zero-copy dùng bộ nhớ cấp trước nên tránh copy dữ liệu mỗi frame [T1 UG232 tr.64], và phải query bằng `RKNN_QUERY_NATIVE_INPUT_ATTR` [T1 UG232 tr.69].
   - Wheel RKNN-Toolkit2 và RKNN-Toolkit-Lite2 2.3.2 không có API cấp phát bộ nhớ, zero-copy hay đồng bộ cache cho Python, zero-copy chỉ có ở C API.
   - UG232 tr.69 nói không dùng `RKNN_QUERY_INPUT_ATTR` nhưng `rknn_create_mem_demo.cpp` dòng 205 lại dùng, trang khuyên tin UG232 và kiểm lại bằng T3.

.. _73-profiling:

Profiling
=========

**Câu hỏi:** đo thời gian, tải và bộ nhớ bằng công cụ nào, và mỗi số đo có nghĩa gì?

**Nguồn nói gì**

   "The interface rknn.eval_perf() will output the current hardware frequency and obtain the performance evaluation results of the model." [T1 UG232 tr.31]

..

   "perf_debug: Debug mode option for performance evaluation. In debug mode, the running time of each layer can be obtained, otherwise, only the total running time of model can be given." [T1 API232 tr.16]

   "Fetch memory usage when model is running on hardware platform." [T1 API232 tr.19]

..

   "The NPU load represents the percentage of time the NPU is executing tasks within a unit of time." [T1 UG232 tr.137]

   "It is important to note that the NPU load does not directly represent the actual MAC utilization." [T1 UG232 tr.137]

..

   "DDR Cycles refers to the number of cycles required by the operator to read and write. It has been converted into the number of Cycles required at the NPU frequency, so it can be directly compared with the NPU Cycle." [T1 UG232 tr.140]

   "Currently, the NPU Cycles column only displays the Cycles required by Conv, and other operator types will be added later." [T1 UG232 tr.140]

..

   "Quantization can significantly reduce the calculation amount of the model and save bandwidth consumption." [T1 UG232 tr.140]

   "rknn.inference is slower than rknn.eval_perf Because rknn.inference uses PC & adb for inference with board-connected, there is some fixed data transmission overhead, which is inconsistent with the theoretical speed of rknn.eval_perf." [T1 UG232 tr.175]

Các cột báo cáo (UG232 tr.32 đến 33): ``DDRCycles``, ``NPUCycles``, ``MaxCycles``, ``Time(us)``, ``MacUsage(%)``, ``WorkLoad(0/1/2)`` ("RK3588 platform only"), ``RW(KB)``, ``Total Memory Read/Write Per Frame Size(KB)`` ("Total bandwidth consumption of a single frame for model inference"). ``eval_memory`` báo ``Weight Memory``, ``Internal Tensor Memory``, ``Other Memory``, ``Total Memory``.

|UG232 Figure 8-5| *Hình 7.3. Bảng phân tích hiệu năng từng lớp: so sánh DDR Cycles với NPU Cycles để biết lớp Conv bị giới hạn bởi băng thông hay bởi tính toán. Nguồn: [T1 UG232 tr.140, Figure 8-5]*

**Ý chính**

- Hai cách đọc ở Figure 8-5 theo User Guide: lớp 3 có DDR Cycles lớn hơn nhiều NPU Cycles nên bị giới hạn bởi băng thông, lớp 12 có DDR Cycles nhỏ hơn nhiều NPU Cycles nên bị giới hạn bởi tính toán (UG232 tr.140). Tổng hợp của file này: đây tương tự phân loại roofline nhưng ở mức từng lớp (UG232 không dùng chữ roofline), và NPU Cycles chỉ có cho Conv.
- ``perf_debug`` cho thời gian từng lớp (API232 tr.16), nhưng UG232 tr.177 ghi chế độ này thêm mã debug và "some parallel mechanisms may be disabled", nên thời gian dài hơn khi ``perf_debug=True``.
- ``eval_perf`` và ``eval_memory`` có ở RKNN-Toolkit2 và API232 tr.18, 19 ghi điều kiện "connected to PC". RKNN-Toolkit-Lite2 không có chúng (``rknn_lite.py``, xem ``05_``). Bản RKNN-Toolkit2 ARM64 có thể có các hàm này nhưng hành vi khi chạy trên board là ``unknown``.
- ``eval_memory`` báo dung lượng bộ nhớ của model, không phải băng thông (UG232 tr.33).
- Cột ``NPUCycles`` chỉ tính cho Conv (UG232 tr.140). Số ``load`` không phải MAC utilization (UG232 tr.137).

**Giới hạn**

- ``RW(KB)`` và ``DDRCycles`` là số đo thực hay tính từ mô hình: ``unknown`` (UG232 chỉ định nghĩa cột).
- Định dạng đầu ra và chu kỳ lấy mẫu của ``rknpu/load``: ``unknown``. Đóng một phần (T1 DRV, T3. DRV xem mục Nguồn cuối trang): định dạng như :ref:`Driver rknpu và các node trạng thái <54-driver-rknpu-và-các-node-trạng-thái>` (``rknpu_debugger.c:39-76``: ``NPU load:``, rồi ``Core%d:`` và ``%2.d%%,`` cho mỗi lõi khi ``num_irqs`` > 1). ``RKNPU_LOAD_INTERVAL`` = 1000000000 (``rknpu_drv.h:40``) và được dùng trong ``ktime_set(0, RKNPU_LOAD_INTERVAL)`` (``rknpu_drv.c:783``). đơn vị ns, tức chu kỳ 1 s, là suy ra từ ``ktime_set``. Lúc đầu chưa đọc được trên board (T3, ``Permission denied``), sau đó đọc được bằng sudo, xem mệnh đề sau. Đóng một phần (T3 board, đọc bằng sudo 2026-10-10, log T3 board 2026-10-10 (``tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/README.md``)): ``load`` lúc nhàn rỗi ra ``NPU load:  Core0:  0%, Core1:  0%, Core2:  0%,``, khớp ``rknpu_debugger.c:39-76`` kể cả dấu phẩy sau lõi cuối.``version`` ra ``RKNPU driver: v0.9.8``. Chu kỳ lấy mẫu của ``load`` vẫn chưa đo (chỉ đọc lúc nhàn rỗi).
- Cơ chế ``fix_freq=True`` đặt tần số qua node nào: ``unknown``.

--------------

.. _74-zero-copy-cờ-bộ-nhớ-và-căn-lề:

Zero-copy, cờ bộ nhớ và căn lề
==============================

**Câu hỏi:** làm sao tránh copy dữ liệu giữa CPU và NPU, và có yêu cầu căn lề gì?

**Nguồn nói gì**

   "The main difference between the two APIs is that each time the general interface updates the frame data, the data allocated externally needs to be copied to the input memory of the NPU during runtime, while the zero-copy interface uses preallocated memory directly" [T1 UG232 tr.64]

..

   "(When alignment requirements for zero-copy input are met, normalization and quantization will run on the NPU, but the input data still needs to be copied to the model's input buffer using the CPU)." [T1 UG232 tr.65]

   "Use RKNN_QUERY_NATIVE_INPUT_ATTR to query related attributes (note, not RKNN_QUERY_INPUT_ATTR)." [T1 UG232 tr.69]

..

   "The input layout and type queried in this way are the optimal hardware efficiency." [T1 UG232 tr.69]

   "If the data type of the query is uint8, but the user wants to pass in float32 type, the size of the rknn_tensor_attr structure must be modified to four times the original size, and the data type must be modified to RKNN_TENSOR_FLOAT32." [T1 UG232 tr.69]

..

   "When the CPU writes data to the cacheable memory, and then when the NPU accesses the memory, it must ensure that the data in the CPU cache is synchronized to the DDR." [T1 UG232 tr.112]

   "Under some alignment sizes, in addition to higher NPU computing efficiency, it is also more friendly to DDR reading and writing." [T1 UG232 tr.144]

..

   "Operators of the same size have larger Width and smaller Height, making them more friendly for DDR reading and writing." [T1 UG232 tr.145]

   "In order to achieve optimal performance, it is recommended that rknn_batch_size be a multiple of 3 for RK3588, and a multiple of 2 for RK3576." [T1 UG232 tr.105]

Table 5-2 (UG232 tr.65), điều kiện zero-copy cho input: với input 4 chiều có số kênh 1, 3 hoặc 4 yêu cầu "Width 16-byte aligned" cho nhóm chip gồm RK3588 (nhóm RV1103/RV1106/RV1126B/RK3562/RK3576/RK3588), input không phải 4 chiều yêu cầu "Total size 16-byte aligned". Nhóm RV1103B/RV1106B/RK3566/RK3568 là 8 byte.

Cờ cấp phát (HDR dòng 381 đến 386): ``RKNN_FLAG_MEMORY_CACHEABLE = 1 << 0``, ``RKNN_FLAG_MEMORY_NON_CACHEABLE = 1 << 1``, ``RKNN_FLAG_MEMORY_TRY_ALLOC_SRAM = 1 << 2`` (chú thích: "Try to allocate memory in SRAM if possible. if SRAM is not enough, allocate rest memory in DRAM.").

|UG232 Figure 5-5 và 5-6| *Hình 7.4. Luồng xử lý dữ liệu của general API (Figure 5-5) và zero-copy API (Figure 5-6): normalize, quantize và chuyển layout chạy trên CPU hoặc NPU tùy chế độ. Nguồn: [T1 UG232 tr.65, Figure 5-5 và 5-6]*

**Ý chính**

- Zero-copy dùng bộ nhớ cấp trước nên giảm copy, tăng hiệu năng và giảm băng thông (UG232 tr.64).
- Ở general API, khi thỏa điều kiện căn lề của zero-copy input thì normalize và quantize chạy trên NPU nhưng dữ liệu input vẫn phải được CPU copy vào buffer input của model (UG232 tr.65). Ở zero-copy API, normalize, quantize và suy luận đều chạy trên NPU.
- Phải query bằng ``RKNN_QUERY_NATIVE_INPUT_ATTR``, layout và kiểu query ra là tối ưu phần cứng. Truyền kiểu khác (ví dụ float32 thay vì uint8) khiến CPU phải chuyển kiểu (UG232 tr.69).
- Bộ nhớ cacheable cần đồng bộ cache trước khi NPU truy cập (UG232 tr.112).
- Đã tách (ít nhất) ba loại căn lề trong file này (:ref:`Layout NC1HWC2 và các kiểu alignment <64-layout-nc1hwc2-và-các-kiểu-alignment>` liệt kê thêm C2 của layout và căn lề output): điều kiện zero-copy input (Table 5-2, 16 byte), căn lề cấp phát SRAM (4K, SRAM dòng 21), và căn lề kênh để chạy hiệu quả, "not mandatory" (UG232 tr.144, xem ``06_``).

**Giới hạn**

- Wheel RKNN-Toolkit2 và RKNN-Toolkit-Lite2 2.3.2 không có API cấp phát bộ nhớ, zero-copy hay đồng bộ cache cho Python (``rknn.py``, ``rknn_lite.py``). Zero-copy chỉ có ở C API.
- ``RKNN_FLAG_MEMORY_TRY_ALLOC_SRAM`` chỉ có ở header, không có trong UG232 hay API Reference của runtime.
- Query input zero-copy: UG232 tr.69 nói không dùng ``RKNN_QUERY_INPUT_ATTR``, nhưng ví dụ ``rknpu2/examples/rknn_api_demo/src/rknn_create_mem_demo.cpp`` dòng 205 dùng đúng lệnh này. Tin theo UG232 và kiểm lại bằng T3.
- Lý do quy tắc 16 byte và ``SIZE_ALIGN_128`` trong ví dụ: ``unknown``.

--------------

.. |UG232 Figure 8-5| image:: ../../../_assets/img/npu/07_memory_performance/ug232_p140_fig8-5.png

.. |UG232 Figure 5-5 và 5-6| image:: ../../../_assets/img/npu/07_memory_performance/ug232_p65_fig5-5_fig5-6.png

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần trích).

.. list-table::
   :header-rows: 1
   :widths: 12 8 70 10

   * - Nhãn
     - Tier
     - Nguồn
     - Số lần
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 18
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/papers/05_rk3588/01_vendor_docs/03_rknn_npu/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 2
