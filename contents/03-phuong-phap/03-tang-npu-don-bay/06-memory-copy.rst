***********
Memory copy
***********

.. admonition:: Trang này trả lời

   - Trong pipeline của dự án, dữ liệu đi từ CPU sang NPU và ngược lại qua những bước nào, và phần sao chép có đo riêng được không?
   - Zero-copy có dùng được trong cấu hình hiện tại (RKNNLite trên Python) không, và nếu không thì cần gì?
   - Mỗi context thêm tốn bao nhiêu bộ nhớ, và batch có phải đòn bẩy không?

.. admonition:: Tóm tắt

   1. Trong harness, ``T_npu`` bao toàn bộ lời gọi ``rknn.inference(...)`` nên gồm copy vào, chạy và lấy ra. Dự án không tách riêng thời gian copy, nên thời gian copy là chưa biết [T3 board, ``ai/board/bench_throughput_rep.py:71-75``].
   2. Ở một context ``CORE_0``, ``T_pre``, ``T_npu``, ``T_post`` là 0.216, 17.161, 0.662 ms (trung vị, P3) [T3 board, ``results/thr_p3.json``].
   3. Zero-copy chỉ có ở C API. RKNNLite 2.3.2 không có hàm cấp bộ nhớ hay ``rknn_set_io_mem``, repo không dùng zero-copy [T3 board, wheel ``rknn_lite.py``, grep ``ai/``].
   4. ``pass_through = 1`` trong harness C bị ``rknn_inputs_set`` từ chối (kỳ vọng 4915200 byte cho đầu vào 1228800 byte), nguyên nhân chưa biết.
   5. Bộ nhớ mỗi context: RSS tiến trình tăng khoảng 12.8 MiB ở S2 và khoảng 17.1 MiB ở probe 32 context, không gồm bộ nhớ NPU do driver cấp. Dùng chung một context giữa ba luồng cho đầu ra sai (300 trên 300 lần gọi khác tham chiếu).
   6. Batch 4 (FP16) chạy được, 22.5 ms mỗi ảnh, nhưng khớp với batch 1 không tái lập và runtime rơi về ``CORE_AUTO``.
   7. Đòn bẩy: C1 zero-copy qua C API (CHƯA BIẾT, chưa thử), C2 ``pass_through`` (ĐO một lần, bị từ chối), C3 nhiều context (ĐO, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`).

Kiến thức nền ở :doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/03-zero-copy-can-le-profiling-api`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Phạm vi và liên kết
======================

Trang này không giải thích lại hai nhóm API, ba cách cấp phát bộ nhớ, điều kiện căn lề của zero-copy, cờ đồng bộ cache hay cách đo bằng profiling API. Phần đó ở :doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/03-zero-copy-can-le-profiling-api`. Định dạng NC1HWC2 và chuyển layout ở :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/05-fusion-va-layout-nc1hwc2` và :doc:`03-tensor-layout`. Bộ nhớ của model và lưu lượng DDR ở :doc:`05-memory-access`.

Trang chỉ ghi điều dự án cần cho quyết định: đường đi thực tế của một khung, những gì đo được và không đo được, và các đòn bẩy sao chép. Mục tiêu 30 FPS, đổi từ 60 ngày 2026-11-08 vì camera chỉ có 30 khung/giây (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8), hiểu là một luồng camera. Mọi cấu hình đã đo đạt mốc này, nên trang không coi đòn bẩy nào là cần để đạt mục tiêu.

2. Đường đi của một khung trong repo
====================================

Harness đo thời gian bằng ``time.perf_counter()`` quanh từng khâu. Mỗi khung đi qua ba khâu:

.. list-table::
   :header-rows: 1
   :widths: 16 26 58

   * - Khâu
     - Chạy ở đâu
     - Ghi chú
   * - ``T_pre``
     - CPU
     - Tiền xử lý ảnh (chi tiết ở :doc:`09-pre-post-processing`)
   * - ``T_npu``
     - ``rknn.inference(...)``
     - Chỉ bao lời gọi ``inference``, gồm copy đầu vào, chạy NPU và lấy đầu ra trong wrapper Python. Không có mốc thời gian riêng cho copy
   * - ``T_post``
     - CPU
     - Hậu xử lý (chi tiết ở :doc:`09-pre-post-processing`)

Nguồn: [T3 board, ``ai/board/bench_throughput_rep.py:71-75``] (mốc ``t0`` ở dòng 71, ``inference`` ở dòng 74) và ``rknn_lite.py:209`` (lời gọi ``set_inputs`` trong wrapper). Harness Python gọi ``inference(inputs=[inp])`` và không gọi ``create_mem`` hay ``set_io_mem`` [Mã nguồn repo, grep ``create_mem\|io_mem\|zero.copy`` trong ``ai/``, không có kết quả].

Số đo ba khâu (trung vị, P3, ms) [T3 board, ``results/thr_p3.json``]:

.. list-table::
   :header-rows: 1
   :widths: 40 20 20 20

   * - Cấu hình
     - ``T_pre``
     - ``T_npu``
     - ``T_post``
   * - 1 context ``CORE_0``
     - 0.216
     - 17.161
     - 0.662
   * - 1 context ``CORE_0_1_2``
     - 0.216
     - 16.68
     - 0.666
   * - 3 context (S2)
     - 0.457
     - 19.526
     - 0.754

Bảng đầy đủ và FPS tương ứng ở :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 3, 4 và 8, không chép lại ở đây. Vì ``T_npu`` gộp copy, chạy và lấy đầu ra, không thể tách phần copy bằng số của harness. Thời gian NPU từ ``eval_perf`` (16.507 và 16.516 ms ở ``CORE_0``, :doc:`04-datatype` mục 2) đo bằng công cụ khác và giao thức khác, nên không trừ hai số này để suy ra thời gian copy. Thời gian copy đầu vào, copy đầu ra hoặc giải lượng tử hóa tách riêng trên board: chưa biết.

3. Zero-copy
============

3.1 Điều kiện của vendor, tóm tắt cho quyết định
------------------------------------------------

Vendor mô tả chi phí của API thường: "each time the general interface updates the frame data, the data allocated externally needs to be copied to the input memory of the NPU during runtime" [T1 UG232 tr.64]. Zero-copy dùng bộ nhớ cấp sẵn nhằm "reducing the cost of copying memory, better performance and less bandwidth" [T1 UG232 tr.64]. Ba điều kiện quyết định cho dự án:

- Hai nhóm API không gọi chung: "General API and zero-copy API interface cannot be called together." [T1 UG232 tr.64]
- Dù đạt điều kiện căn lề, nếu dùng API thường thì "but the input data still needs to be copied to the model's input buffer using the CPU" [T1 UG232 tr.65]
- Ở zero-copy, "Zero-copy API normalization, quantization, and model inference are all running on the NPU." [T1 UG232 tr.65]

Điều kiện căn lề của RK3588 (chiều rộng và tổng kích thước căn 16 byte, Bảng 5-2), việc zero-copy chỉ hỗ trợ NHWC, quy tắc cấp bộ nhớ ngoài (chỉ dùng zero-copy API) và hướng đồng bộ cache một chiều ở :doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/03-zero-copy-can-le-profiling-api` và :doc:`03-tensor-layout`. Với driver, bộ nhớ NPU mặc định không cache và chỉ vùng có cờ ``RKNPU_MEM_CACHEABLE`` mới đồng bộ được [T1 DRV, ``3rdparty/rknpu-driver-0.9.8/rknpu_gem.c:1353`` và ``:1684-1685``].

3.2 Trạng thái trong dự án
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Mục
     - Quan sát
   * - RKNNLite (Python)
     - Wheel ``rknn_toolkit_lite2-2.3.2`` có các hàm ``load_rknn``, ``list_devices``, ``init_runtime``, ``inference``, ``get_sdk_version``, ``list_support_target_platform``, ``release``. Không có ``create_mem``, ``set_io_mem`` hay zero-copy. ``inference`` nhận ``inputs_pass_through`` [T3 board, ``rknnlite/api/rknn_lite.py`` dòng 57, 81, 115, 193, 237, 255, 266]
   * - Harness C
     - ``ai/board/rknn_perf_bench.c`` đặt ``pass_through=0``, ``type=UINT8``, ``fmt=NHWC`` (dòng 95 đến 97) [Mã nguồn repo]
   * - Repo
     - Không dùng zero-copy, không thấy ``create_mem`` hay ``set_io_mem`` trong ``ai/`` [Mã nguồn repo, grep]

Hệ quả: với RKNNLite, đòn bẩy zero-copy chỉ có thể thực hiện bằng cách chuyển sang C API và viết lại harness. Dự án chưa làm việc đó. Không có số đo FPS cho đường zero-copy. README và CHANGELOG của lite2 không nêu giới hạn này, nên lý do wheel không có API đó: chưa biết.

3.3 ``pass_through``
--------------------

Toolkit có tham số ``inputs_pass_through`` bỏ phép trừ mean và chia phương sai trước khi dữ liệu vào driver [T1 API232 tr.18]. Dự án đã thử ``pass_through = 1`` trong harness C một lần. Ghi chú trong mã (dòng 77 đến 78) viết: "pass_through = 1 was rejected by rknn_inputs_set (expects 4915200 bytes for this 1228800 byte INT8 input)" [Mã nguồn repo ``ai/board/rknn_perf_bench.c:77-78``]. Harness vì vậy quay về ``pass_through = 0``. Nguyên nhân kỳ vọng gấp 4 lần: chưa biết (cùng mục L3 ở :doc:`03-tensor-layout` mục 4).

4. Bộ nhớ mỗi context
=====================

Cấu hình nhiều context (S2, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`) là đòn bẩy FPS đã đo, nên chi phí bộ nhớ của nó cần biết.

.. list-table::
   :header-rows: 1
   :widths: 36 64

   * - Phép đo
     - Kết quả
   * - RSS tiến trình Python, S2
     - 172.3 MiB với 1 context, 197.9 MiB với 3 context, khoảng 12.8 MiB mỗi context thêm. Trang nguồn ghi rõ đây không gồm bộ nhớ NPU do driver cấp [T3 board, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 3]
   * - Probe M16 (một tiến trình, nhiều context, dừng ở 32)
     - RSS 66.3 MiB (1 context), 83.0 (2), 100.0 (3), 185.6 (8), 322.0 (16), 595.6 (32). ``MemAvailable`` giảm từ 3182 xuống 2651 MiB. Độ dốc khoảng 17.1 MiB mỗi context (tính từ các hàng này) [T3 board, ``results/q2e_board.json`` ``$.probes.m16.result.rows``]

Hai số 12.8 và 17.1 MiB mỗi context đến từ hai phép đo khác cấu hình (S2 ba context trong harness thông lượng, M16 một tiến trình đến 32 context). Nguyên nhân chênh: chưa biết. Probe M16 dừng ở ngưỡng chặn 32, không phải giới hạn thật, nên giới hạn số context trên board chỉ biết là không nhỏ hơn 32.

Dùng chung một context giữa các luồng (M4): 300 lần gọi, 0 exception, 300 đầu ra khác tham chiếu (lệch tối đa 1.04). Phép đối chứng cùng mã một luồng cho 0 khác biệt. Runtime không báo lỗi khi sai, và trong phép thử này dùng chung một context giữa ba luồng cho đầu ra sai [T3 board, :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7, một phép thử, nguyên nhân chưa biết]. Vì vậy trong cấu hình đã thử, chi phí bộ nhớ của nhiều context không tránh được bằng cách chia sẻ một context. Chi phí bộ nhớ NPU do driver cấp theo từng context (khác RSS tiến trình): chưa biết.

5. Batch
========

Probe M7 dựng ``rknn_batch_size`` 4 ở FP16 và chạy được, đầu ra ``[4, 9, 8400]``. Một lần gọi trung vị 41.90 ms ở batch 1 và 90.19 ms ở batch 4 (22.55 ms mỗi ảnh) [T3 board, ``results/q2e_board.json`` ``$.probes.m7.result``]. Hạn chế đã ghi ở :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7:

- Kết quả khớp từng ảnh với batch 1 không tái lập. Lần chạy đầu lệch 0, lần chạy lặp một ảnh lệch 0.19.
- Log console ghi "core mask = 1 is invalid for batch size: 4, fall back to CORE_AUTO mode", nên batch 4 chạy ở chế độ nhân khác.
- Thời gian đo qua Python ở chế độ nhân khác, chỉ để mô tả, không so được với số P2 hay P3. Trường ``model`` của probe là ``null`` trong file kết quả.

Nên batch chưa phải đòn bẩy có số liệu dùng được. Nhãn: chưa biết (không phải "Loại", vì chưa đo dưới P2 hay P3).

6. Đòn bẩy
==========

Nhãn trạng thái: ĐO (có số đo T3), NGUỒN (chỉ có tài liệu hoặc mã), CHƯA BIẾT. Ngưỡng số mới của từng thí nghiệm vẫn chưa duyệt.

.. list-table::
   :header-rows: 1
   :widths: 8 26 14 52

   * - Mã
     - Đòn bẩy
     - Nhãn
     - Bằng chứng và giới hạn
   * - C1
     - Zero-copy qua C API
     - CHƯA BIẾT
     - Vendor mô tả lợi ích (UG232 tr.64, 65, mục 3.1). Cần harness C, repo chưa thử và không có số đo. Lợi ích cụ thể cho YOLOv8n trên RK3588: chưa biết
   * - C2
     - ``pass_through`` để bỏ bước chuẩn hóa trên đường vào
     - ĐO một lần, bị từ chối
     - Harness C bị ``rknn_inputs_set`` từ chối (mục 3.3). Chưa có đường chạy thành công
   * - C3
     - Nhiều context độc lập
     - ĐO
     - Hai context 102.0 FPS, ba context 141.2 FPS (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8). Chi phí bộ nhớ ở mục 4. Đầu ra đúng khi mỗi luồng có context riêng (M4c, một luồng). Chia sẻ một context thì đầu ra sai
   * - C4
     - Batch lớn hơn 1
     - CHƯA BIẾT
     - Mục 5. Có số thời gian nhưng không tái lập về đầu ra và khác chế độ nhân

FPS của các đòn bẩy phối hợp (ví dụ nhiều context cộng chồng lấp tiền và hậu xử lý) ở :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.

7. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 38 14 48

   * - Mục
     - Trạng thái
     - Đã tìm gì
   * - Thời gian copy đầu vào, copy đầu ra, giải lượng tử hóa tách riêng
     - chưa biết
     - Repo chỉ có ``T_npu`` gộp. Chưa tìm thấy mốc đo riêng
   * - Thời gian đồng bộ cache (``rknn_mem_sync``) trên RK3588
     - chưa biết
     - Chỉ có mô tả của vendor, không có số
   * - Chi phí và lợi ích của zero-copy trên đường của RKNNLite
     - chưa biết
     - Wheel không có API zero-copy, README và CHANGELOG lite2 không nêu giới hạn
   * - Bộ nhớ NPU do driver cấp theo từng context
     - chưa biết
     - Chỉ có RSS tiến trình, không gồm bộ nhớ NPU
   * - Giới hạn số context
     - chưa biết
     - Probe dừng ở ngưỡng chặn 32
   * - Nguyên nhân ``pass_through`` kỳ vọng 4915200 byte
     - chưa biết
     - Chỉ có ghi chú trong mã
   * - Cách hiểu 30 FPS
     - một luồng camera, suy từ lý do người dùng nêu ngày 2026-11-08
     - :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8

8. Nguồn
========

- T1: SDK User Guide V2.3.2 (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, UG232 tr.64, 65), API Reference Toolkit2 V2.3.2 (API232 tr.18), driver ``3rdparty/rknpu-driver-0.9.8/`` (``rknpu_gem.c:1353, 1684-1685``).
- T3: ``ai/board/bench_throughput_rep.py:71-75``, ``ai/board/rknn_perf_bench.c:77-78, 95-97``, wheel ``rknn_lite.py``, ``results/thr_p3.json``, ``results/q2e_board.json``.
- Trang liên quan: :doc:`03-tensor-layout`, :doc:`04-datatype`, :doc:`05-memory-access`, :doc:`09-pre-post-processing`, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`, :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet`, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.
