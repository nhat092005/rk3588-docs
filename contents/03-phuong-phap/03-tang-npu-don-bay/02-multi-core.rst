**********
Multi-core
**********

.. admonition:: Trang này trả lời

   - Dùng ba nhân NPU của RK3588 cho pipeline PPE theo cách nào: chia một frame qua nhiều nhân (S1), nhiều context mỗi context một nhân (S2), hay chồng pha CPU và NPU (S3)?
   - Chọn cấu hình theo tiêu chí nào cho latency một luồng và cho throughput?
   - Điều gì đã đo, điều gì chưa biết?

.. admonition:: Tóm tắt

   - Chương đặt ba chiến lược S1, S2, S3 và quy tắc chọn theo hai trục (latency, throughput). Cả ba đã đo (1 seed, giao thức P2 và P3 duyệt ngày 2026-11-01), kết quả ở :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`: S1 (SiLU, latency) Loại, S2 Giữ, S3 Loại. "Loại" chỉ nghĩa là không qua ngưỡng 5%, không phải cấm dùng. Ngày 2026-11-08 dự án vẫn chọn intra-frame (S1) làm kiểu chạy NPU (quyết định 7, :doc:`../../00-tong-quan/04-gioi-han-va-huong-phat-trien` mục 3.1).
   - Hãng ghi đa nhân hợp với mạng lớn, mạng nhỏ có thể chậm đi vì việc chuyển đơn nhân và đa nhân cần CPU can thiệp [T1 UG232 tr.72]. Chỉ một số op được chia task qua nhiều nhân [T1 UG232 tr.75]. Bài Kong 2026 trên RK3588: đa nhân chỉ cho lợi ích biên, thường dưới 10% [T2 EDGE tr.2].
   - Driver 0.9.8 có hàng đợi riêng cho từng lõi và mỗi lõi chạy một job tại một thời điểm [T1 DRV rknpu_job.c:431-455, 545-553]. Đây là cơ sở cơ chế cho S2.
   - ``async_mode`` được API guide ghi "(Not Supported yet)" [T1 API232 tr.16], nên S3 là thiết kế luồng ở tầng ứng dụng.
   - Quy tắc chọn dùng ngưỡng tương đối 5% (tham số của dự án, chốt 2026-10-25). Mục tiêu FPS: 60 (chốt 2026-11-01), đổi thành 30 ngày 2026-11-08 vì camera chỉ có 30 khung/giây, mọi cấu hình đã đo đều đạt (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8).

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Phạm vi và quy tắc bằng chứng
================================

Chương xét việc dùng ba nhân NPU cho pipeline phát hiện PPE (YOLOv8n INT8, đầu vào 640x640, Orange Pi 5 với RK3588S). Luận điểm: latency và throughput cần cấu hình đa nhân khác nhau, và quy tắc chọn dựa vào tỉ lệ cycles nằm ở op chia được qua nhiều nhân (điều kiện A của cổng G4 trong :doc:`01-operator-support`).

1.1. Ba chiến lược
------------------

.. list-table::
   :header-rows: 1
   :widths: 8 40 22 30

   * - Mã
     - Cấu hình
     - Mục tiêu
     - Mã đo
   * - S1
     - Một context chia một frame qua nhiều nhân: ``core_mask`` là ``CORE_0_1`` hoặc ``CORE_0_1_2``
     - Giảm latency một frame
     - ``ai/automation/benchmark_npu.py`` (tầng 1), ``ai/board/bench_npu.py`` (tầng 2). Kết quả: :doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`
   * - S2
     - N context, mỗi context ghim một nhân (``CORE_0``, ``CORE_1``, ``CORE_2``), mỗi context một luồng
     - Tăng throughput
     - ``ai/board/bench_throughput.py``, ``bench_throughput_rep.py`` (lặp 3 lần), ``ai/automation/pipeline.py``
   * - S3
     - Chồng pre và post-process trên CPU với phần NPU bằng pipeline luồng ở tầng ứng dụng, có thể thêm ``async_mode``
     - Tăng throughput khi CPU là điểm nghẽn
     - ``bench_throughput_rep.py --mode pipeline``

S1 và S2 dùng cùng API ``core_mask`` của ``init_runtime``. Khác nhau ở số context: S1 để runtime chia trong một context, S2 để ứng dụng chia theo frame. Hai chiến lược trả lời hai câu hỏi khác nhau nên không so bằng một con số.

1.2. Quy ước bằng chứng và phạm vi
----------------------------------

Thẻ nguồn trong ngoặc vuông: T1 là tài liệu hãng (SDK User Guide V2.3.2 ``UG232``, API guide V1.5.2 ``UG152``, API Reference V2.3.2 ``API232``, Operator List ``OPL``, mã nguồn driver rknpu 0.9.8 ``DRV``), T2 là bài báo (Kong 2026 ``EDGE``, DAHD-YOLO 2025 ``DAHD``, Jung 2023, Min 2023), T3 board là phép đo trên board (:doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`). Số trang là trang PDF. Mục không có tier là "chưa biết". Số do người đọc tự tính từ số của nguồn gọi là "số học của người đọc".

Ngoài phạm vi: chế độ ``rknn_batch_size`` lớn hơn 1 (runtime nhân bản context, đặt ``core_mask`` về 0 và dùng thread pool nội bộ [T1 UG232 tr.104], hiệu quả trên model dự án chưa biết), độ chính xác mAP (``core_mask`` không đổi trọng số, điều kiện mAP ở G4), công suất. Mốc 25 FPS của DAHD là ngưỡng của bài báo, không phải yêu cầu của dự án [T2 DAHD tr.18].

Nguồn: ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (``UG232``), :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../../_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>` (``UG152``), :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>` (``API232``), :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../../_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>` (``OPL``), ``3rdparty/rknpu-driver-0.9.8`` (``DRV``), :download:`edgesoc_benchmark_2026kong.pdf <../../../_assets/pdf/papers/05_rk3588/edgesoc_benchmark_2026kong.pdf>` (``EDGE``, Scientific Reports 2026, 16:5875), :download:`dahd_yolo_rk3588_2025.pdf <../../../_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf>` (``DAHD``), :download:`mobile_multicore_npu_2023jung.pdf <../../../_assets/pdf/papers/01_hardware/mobile_multicore_npu_2023jung.pdf>`, :download:`flexer_multi_npu_2023min.pdf <../../../_assets/pdf/papers/01_hardware/flexer_multi_npu_2023min.pdf>`. Nền tảng phần cứng ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/03-che-do-da-loi-va-system-sram` và :doc:`../../01-kien-thuc-nen/02-npu/03-systolic-array-va-kien-truc-da-loi`.

2. S1: một context chia ba lõi
==============================

2.1. Hãng ghi nhận gì
---------------------

Hãng cảnh báo ngay đầu chương đa nhân rằng lợi ích phụ thuộc kích thước mạng:

   "Note: Multi-core operation is suitable for networks with a large amount of calculations. A little improvement for small networks, and may even lead to performance degradation due to single-core and multi-core switching (this switching requires CPU intervention)."

[T1 UG232 tr.72]

Op chia được qua nhiều nhân: Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, LeakyRelu [T1 UG232 tr.75] [T1 UG152 tr.27] (hai tài liệu trùng tên op, chỉ khác cách ghi). Với op ngoài danh sách, UG152 ghi:

   "Other type of op will fallback to Core0 to continue running. In the future update, some ops like Pool or ConvTranpose will be supported."

[T1 UG152 tr.27]

Verdict đa nhân theo từng op của YOLOv8n ở :doc:`01-operator-support`. Cột ``WorkLoad(0/1/2)-ImproveTherical`` trong log (``RKNN_LOG_LEVEL`` từ 4 trở lên [T1 UG232 tr.74]) cho biết cách chia từng layer. Ví dụ ``50.0%/50.0%/0.0% - Up:50.0%`` là lõi 0 và 1 mỗi lõi 50%, lý thuyết nhanh hơn 50% [T1 UG232 tr.75]. Cột này là chỉ báo lý thuyết, không phải latency đo được. Hãng nêu hai lý do một layer chỉ chạy một nhân: tải nhỏ hơn độ hạt phân chia task, hoặc op chưa có phân đoạn đa nhân trong driver [T1 UG232 tr.75]. Hãng khuyên đặt CPU, DDR, NPU ở tần số cao nhất và gán ứng dụng cùng ngắt NPU vào lõi CPU lớn khi đo [T1 UG232 tr.75].

2.2. Driver cho thấy gì
-----------------------

Driver nhận job cùng mảng ``subcore_task`` từ user space (``include/rknpu_ioctl.h:241-243``, ``:279``), chỉ dùng nó để lấy số task từng lõi [T1 DRV rknpu_job.c:71-94]. Kernel không tự chia. Phép chia nhiều khả năng nằm ở ``librknnrt`` (nhị phân, không có mã nguồn) [SL]. Một job đa nhân (mask 0x1, 0x3, 0x7) chờ hoàn thành trên hàng đợi của lõi 0 [T1 DRV rknpu_job.c:27-47, 179-200]: nếu lõi 0 đang bận job của context khác, job đa nhân phải đợi ở đó. ``AUTO`` chỉ gán một lõi cho job (:doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/03-driver-rknpu-va-rknn-server`).

Kết quả đo chiều chia trên board: chia theo chiều cao (hàng) thành ba dải liên tiếp, chỉ 6 task conv chạy đa nhân ở model SiLU (:doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/03-che-do-da-loi-va-system-sram` mục 1.2). Quy tắc của ``librknnrt`` vẫn chưa biết.

2.3. Bằng chứng về lợi ích
--------------------------

Bài Kong 2026 đo YOLO trên RK3588 ở 640x640. Bốn hàng của Table 4 (latency, ms) [T2 EDGE tr.7]:

.. list-table::
   :header-rows: 1

   * - Model
     - AUTO
     - C0
     - C1
     - C2
     - C0_1
     - C0_1_2
     - ALL
   * - YOLOv5n
     - 21.7
     - 21.5
     - 21.46
     - 22.07
     - 20.96
     - 21.07
     - 20.47
   * - YOLOv8n
     - 24.88
     - 24.54
     - 26.1
     - 25.89
     - 25.31
     - 25.33
     - 21.25
   * - YOLOv8s
     - 43.27
     - 43.16
     - 43.25
     - 42.72
     - 42.61
     - 41.88
     - 41.94
   * - YOLO11m
     - 92.22
     - 93.72
     - 98.05
     - 94.11
     - 95.47
     - 96.01
     - 95.51

- Bài không định nghĩa các mã cột ``C0``, ``C0_1_2``, ``ALL`` [T2 EDGE tr.7]. Câu văn "YOLO11m achieved 93.7 ms in single-core mode and 95.5 ms in three-core mode" khớp ô ``C0`` (93.72) và ``ALL`` (95.51), không khớp ``C0_1_2`` (96.01) [số học của người đọc].
- Ở YOLOv8n, ``C0_1_2`` (25.33 ms) chậm hơn ``C0`` (24.54 ms), ``ALL`` (21.25 ms) thấp hơn ``C0`` 13.4% [số học của người đọc].
- "multi-core scheduling did not lead to proportional reductions in latency" [T2 EDGE tr.6], "multi-core NPU scheduling yields only marginal gains (generally < 10%)" [T2 EDGE tr.2]. Bài không nói vùng đo có gồm pre và post không.

Nguyên nhân bài nêu, không kèm phép đo cô lập:

   "Performance improvements are constrained by inter-core communication, synchronization overhead, and shared memory bandwidth, preventing linear scaling with the number of cores."

[T2 EDGE tr.7]

Jung 2023 (NPU di động nhiều lõi, không phải RK3588) giải thích tương tự: "When a layer is partitioned and executed in parallel on multiple cores, synchronization is required at the end of layer execution." [T2 Jung 2023 tr.5]. Đây là cơ chế của NPU khác, repo không có phép đo chứng minh trên RK3588.

Bản ghi T3 board ngày 2026-10-10 (``eval_perf``, median 15 lần, model trọng số ngẫu nhiên, nhật ký gốc đã xóa nên không kiểm lại được) [T3 board, ghi nhận]: YOLO26n 22.26 ms (AUTO), 21.70 ms (CORE_0), 22.09 ms (ba lõi), YOLOv8n 19.40, 19.16, 18.985 ms, "không có lợi ích đo được cho cả hai model". SiLU không khác biệt ngoài độ trải, ReLU nhanh hơn ``CORE_0`` khoảng 8% ở ba lõi (13.969 xuống 12.854 ms, ``relu_opt3``). Cùng một file ``.rknn`` SiLU ở ``AUTO`` đo được 19.154 rồi 22.021 ms, nguyên nhân chưa biết, nên mức 8% cần đối chiếu độ trải này. Đây là latency một frame, không đo throughput.

2.4. Kết luận cho S1
--------------------

S1 đáng thử khi điều kiện A của :doc:`01-operator-support` thỏa: lớp chia từ hai nhân trở lên chiếm ít nhất 50% tổng cycles ước tính của build INT8 (ngưỡng do dự án đặt).

Kết quả (1 seed, giao thức P2): **Loại** cho trục latency của model SiLU. ``CORE_0_1_2`` nhanh hơn ``CORE_0`` 2.9% và ``CORE_0_1`` 2.2%, dưới ngưỡng 5% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 2). Dự án vẫn chọn intra-frame (quyết định 7). Khoảng trống còn lại:

- Quy tắc chia của ``librknnrt``: chưa biết, mẫu chia quan sát được ở :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 5.
- ``ALL`` trong Table 4 của EDGE tương ứng chế độ nào: bài không định nghĩa (đã tìm toàn bộ bài báo và T1). ``NPU_CORE_ALL`` (0xffff) chia đúng tập dòng của ``CORE_0_1_2`` ở runtime này (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 6), nghĩa trong bài vẫn chưa biết.

3. S2: nhiều context, mỗi context một lõi
=========================================

3.1. Cơ chế trong kernel
------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Hành vi
     - Nguồn
   * - Mỗi lõi có hàng đợi FIFO riêng. Job được thêm vào hàng đợi của từng bit lõi trong mask dưới ``irq_lock``
     - [T1 DRV rknpu_job.c:545-553]
   * - Mỗi lõi chạy một job tại một thời điểm, ``rknpu_job_next`` trả về ngay nếu lõi đang có job hoặc hàng đợi rỗng
     - [T1 DRV rknpu_job.c:431-455, 442-443]
   * - Hệ quả: các context ghim cùng một lõi bị tuần tự hóa trong kernel, ghim lõi khác nhau thì dùng hàng đợi khác nhau
     - Suy luận của chương
   * - Không thấy mutex hoặc spinlock tuần tự hóa việc gửi job giữa các context (chỉ có ``irq_lock``)
     - [T1 DRV rknpu_job.c:545-553]
   * - Mặc định driver trễ 3 giây (``power_put_delay = 3000`` ms) trước khi tắt nguồn NPU sau một ioctl
     - [T1 DRV rknpu_drv.c:1466-1467]

Hãng không ghi rõ (đã tìm trong UG232, UG152, API232, header, CHANGELOG): một context có an toàn khi gọi từ nhiều luồng không (đo 2026-11-01: ba luồng dùng chung một context cho đầu ra sai âm thầm, 300 trên 300 đầu ra khác, một luồng thì đúng, :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7). Nhiều tiến trình dùng các lõi khác nhau có quy tắc gì không (CHANGELOG v1.1.0 chỉ ghi "Improve the stability of multi-thread + multi-process runtime"). Giới hạn số context (tạo được 32 context liên tiếp, đều chạy đúng, dừng ở ngưỡng chặn nên giới hạn thật chưa biết). SDK không có demo thread pool cho NPU.

Hãng chỉ có hai câu gần với S2:

   "In a multi-threaded scenario, a model may be executed by multiple threads at the same time. If each thread initializes a context separately, the memory consumption will be very large. Therefore, the application can consider sharing a context to avoid repeated memory allocation of RKNN context and reduce runtime memory usage."

[T1 UG232 tr.153]

   "Alternatively, utilizing multi-threading in the application can help increase the NPU load."

[T1 UG232 tr.137]

Câu đầu cho thấy mỗi context riêng tốn bộ nhớ, là chi phí của S2. Cách chia sẻ trọng số là ``rknn_dup_context`` [T1 UG152 tr.27], không có trong ``RKNNLite`` Python, nên chương không dùng.

3.2. Bằng chứng
---------------

DAHD-YOLO trên RK3588: "By utilizing a thread pool for acceleration, we optimize the entire detection process through multithreading." [T2 DAHD tr.18] và "optimizations such as quantization and multi-threading, the system achieves a detection rate of 50.2 fps" [T2 DAHD tr.1]. Bản INT8 một luồng mất 0.1162 s mỗi frame (khoảng 8.6 FPS, số học của người đọc) [T2 DAHD tr.18]. Không dùng số 50.2 FPS cho dự án: bài không nêu số lõi, model và độ phân giải khác (1280x720), và gộp lượng tử hóa với đa luồng nên không tách được phần của đa luồng.

Cận trên [số học của người đọc]: ba context trên ba lõi thì phần NPU không vượt ba lần một lõi. Toàn pipeline bị giới hạn bởi stage chậm nhất, theo công thức của repo (giả định các stage chồng nhau):

   Throughput FPS = 1000 / max(T_pre, T_npu, T_post)

[Mã nguồn repo docs/contents/01-kien-thuc-nen/05-bo-nho-hieu-nang/01-do-do-tre-va-profiling.rst:69-73]

Bài Kong không báo throughput và không chạy nhiều model đồng thời (không có "concurrent", "multi-model", "thread" trong 13 trang). Repo không có T2 nào đo S2 trên RK3588 với model của dự án.

3.3. Harness và giới hạn
------------------------

``ai/board/bench_throughput.py`` (harness cũ): một luồng mỗi context, mỗi luồng chạy pre, NPU, post trên frame đã giải mã sẵn, 200 ảnh cache dùng vòng tròn, warmup 20 lần trên ``frames[0]``, vùng đo gồm pre, ``rknn.inference`` và post, một lượt, tần số không cố định [Mã nguồn repo bench_throughput.py:3, 27-28, 37-47, 57-72, 88-91]. Giới hạn: không có độ trải, DVFS lẫn vào, ảnh cache lặp lại không phản ánh camera, warmup một frame. ``RKNNLite.inference`` có nhả GIL không là chưa biết (``RKNNRuntime`` là ``.so``). Harness mới ``bench_throughput_rep.py`` (``results/npu/throughput/thr_p3.json``, 2026-10-31) lặp 3 lần độc lập và sửa các giới hạn trên trừ ảnh cache lặp lại và GIL (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`).

3.4. Kết luận cho S2
--------------------

**Giữ** (1 seed, giao thức P3 duyệt 2026-11-01, một model). Ba context đạt 141.2 FPS so với 56.1 FPS của cấu hình một context tốt nhất, tăng 151.7% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 3).

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Khía cạnh
     - Trạng thái
   * - Cơ chế
     - Hàng đợi riêng từng lõi, không thấy khóa chung khi gửi job [T1 DRV rknpu_job.c:431-455, 545-553]
   * - Lợi ích throughput
     - 141.2 FPS với ba context. Bài DAHD có số 50.2 FPS nhưng khác model, độ phân giải và không nêu số lõi [T2 DAHD tr.18]
   * - Chi phí
     - Mỗi context riêng tốn thêm bộ nhớ [T1 UG232 tr.153]. Đo: khoảng 12.8 MiB RSS tiến trình mỗi context thêm (không gồm bộ nhớ NPU)
   * - An toàn nhiều luồng
     - Chưa biết. Phép đo chạy ba luồng, mỗi luồng một context, không lỗi (T5, T6). Không đo việc dùng chung một context

4. S3: chồng pha CPU và NPU
===========================

4.1. Vì sao cần xét S3
----------------------

Trong harness, mỗi luồng chạy tuần tự ``preprocess``, ``rknn.inference``, ``postprocess`` trong vùng tính giờ [Mã nguồn repo bench_throughput.py:59-62], nên ``throughput_fps`` gồm cả tiền xử lý và hậu xử lý, và phần CPU có thể giới hạn throughput dù NPU còn rảnh. Theo công thức ở mục 3.2, khi một pha CPU lớn hơn ``T_npu`` thì thêm lõi NPU không làm FPS tăng. Từ hai luồng trở lên, phần CPU của luồng này trùng phần NPU của luồng khác (chồng pha ngầm, như S2). S3 làm điều này tường minh: worker tiền xử lý, worker NPU và worker hậu xử lý nối bằng hàng đợi. Đây là thiết kế đề xuất.

4.2. Tài liệu hãng nói gì về ``async_mode``
-------------------------------------------

Tài liệu hãng có một định nghĩa duy nhất của ``async_mode`` và nó kết thúc bằng dòng chưa hỗ trợ:

   "async_mode: Whether to use asynchronous mode. The default value is False. [...] If the asynchronous mode is enabled, setting the input of the current frame will be performed simultaneously with the inference of the previous frame, so in addition to the first frame, each subsequent frame can hide the setting input time, thereby improving performance. In asynchronous mode, the inference result returned each time is the previous frame. (Not Supported yet)"

[T1 API232 tr.16]

Header C ghi: "in multi-threaded mode you do not need to turn this mode on." [T1 rknn_api.h:35-40]. ``rknn_run`` ở API cũ: "This interface is used for non-blocking mode inference and has not been implemented yet." [T1 UG152 tr.38]. RKNN-Toolkit-Lite2 2.3.2 chỉ chuyển ``async_mode`` xuống runtime biên dịch sẵn nên hành vi thực tế chưa biết [T1 rknn_lite.py:115,121,149]. SDK 2.3.2 không có từ ``async_mode`` trong 178 trang. Hệ quả: chương không dựa vào ``async_mode``, S3 là thiết kế ở tầng ứng dụng. Thăm dò 2026-11-01: ``async_mode=True`` được chấp nhận và ``inference`` tuần tự vẫn trả đầu ra của ảnh vừa gửi (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7).

4.3. Bằng chứng T2
------------------

Bài Kong đo latency "tại NPU runtime", không nêu thống kê pre, post hay throughput, và không nói vùng tính giờ có gồm pre và post hay không [T2 EDGE tr.2]. Câu về tải CPU: "CPU utilization had relatively minor impact on inference latency, as the compute-intensive portion of YOLO execution is handled by the NPU." [T2 EDGE tr.10]. Câu này nói về latency phần NPU khi CPU bị tải bằng ``stress-ng`` [T2 EDGE tr.7], không nói gì về pipeline bị giới hạn bởi CPU nên không dùng để suy ra S3. DAHD nêu thread pool nhưng không tách phần chồng pha CPU và NPU khỏi phần dùng nhiều nhân [T2 DAHD tr.18].

4.4. Kết luận cho S3
--------------------

Cần ba đại lượng theo từng frame (``T_pre``, ``T_npu``, ``T_post``), cùng FPS và phần trăm CPU, có và không có worker tách riêng. ``ai/board/bench_npu.py`` ghi riêng pre, NPU, post và e2e cho từng ảnh [Mã nguồn repo bench_npu.py:3-4].

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Mục
     - Giá trị
   * - Trạng thái
     - Loại (1 seed, P3 đã duyệt 2026-11-01)
   * - Bằng chứng
     - Không có T1 (``async_mode`` chưa hỗ trợ) hay T2 cho riêng S3. T3 2026-10-31: 147.4 FPS so với 141.2 FPS của S2, tăng 4.4%, dưới ngưỡng 5% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 4)
   * - Harness
     - ``ai/board/bench_throughput_rep.py --mode pipeline``
   * - Việc còn thiếu
     - Số worker pre và post khác công thức đã dùng chưa thử

5. Quy tắc chọn cấu hình
========================

5.1. Hai trục quyết định
------------------------

Latency (một luồng camera) và throughput (nhiều luồng hoặc video offline) cần cấu hình khác nhau.

.. list-table::
   :header-rows: 1
   :widths: 18 26 28 28

   * - Trục
     - Đại lượng
     - Ứng viên
     - Đối chứng
   * - Latency
     - Thời gian xử lý một frame, một context
     - S1 (``CORE_0_1``, ``CORE_0_1_2``)
     - Baseline một nhân ``CORE_0``
   * - Throughput
     - FPS tổng của harness, nhiều context hoặc nhiều luồng
     - S2 (ba context ghim ``CORE_0``, ``CORE_1``, ``CORE_2``) và S3
     - Cấu hình tốt nhất trong S1 và baseline ở trục latency

Sổ tay SDK nói ``AUTO`` chọn lõi rảnh [T1 UG232 tr.73]. Driver 0.9.8 chọn lõi có số task xếp hàng ít nhất, không xét trạng thái rảnh [T1 DRV rknpu_job.c:508-538]. ``AUTO`` chỉ là tham chiếu, không phải ứng viên.

5.2. Ngưỡng
-----------

Ngưỡng là tham số của dự án, chốt 2026-10-25. Hai ngưỡng đầu là điều kiện A và B của G4 trong Operator support.

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Điều kiện
     - Chuẩn
   * - Phủ đa lõi (A)
     - Lớp có workload chia từ hai lõi trở lên chiếm ít nhất 50% tổng cycles ước tính (cột ``Cycles(DDR/NPU/Total)`` của build INT8)
   * - S1 nhanh hơn ``CORE_0`` về latency (B)
     - Median của 5 lần ``eval_perf`` cho mỗi ``core_mask``, lặp ở hai phiên ``init_runtime``, không bật ``perf_debug`` khi đo latency (``perf_debug`` có thể tắt cơ chế song song [T1 UG232 tr.177]). ``CORE_0_1_2`` nhanh hơn khi giảm ít nhất 5% và mức giảm lớn hơn chênh lệch median giữa hai phiên
   * - S2 hơn cấu hình tốt nhất của S1 về throughput
     - FPS cao hơn ít nhất 5%, median của 3 lần chạy độc lập, mức tăng lớn hơn độ trải giữa các lần
   * - S3 đáng giữ
     - FPS cao hơn S2 ít nhất 5% với cùng số context, hoặc Avg CPU thấp hơn khi FPS không đổi (chênh nằm trong độ trải)

Điều kiện chung: dtype INT8 (``w8a8``). Khóa tần số bằng ``lock_freq.sh``, gắn ứng dụng và ngắt NPU vào cùng lõi lớn [T1 UG232 tr.75]. Ghi nhiệt độ đầu và cuối. Chỉ seed 0, mọi kết quả ghi nhãn "1 seed" vì chưa có std. Điều kiện C (mAP) của G4 không áp dụng vì S1, S2, S3 dùng cùng model và không đổi trọng số.

5.3. Luồng quyết định
---------------------

Ứng viên dừng ở bước đầu tiên không qua. Nhãn "Giữ", "Loại", "Chưa biết" như trong Operator support.

.. list-table::
   :header-rows: 1
   :widths: 8 30 34 28

   * - Bước
     - Câu hỏi
     - Qua khi
     - Kết quả khi trượt
   * - 1
     - Trục latency: S1 có nhanh hơn ``CORE_0`` không
     - Đạt điều kiện B ở mục 5.2 (điều kiện A là chỉ báo kèm theo)
     - S1 "Loại" cho trục latency (không qua ngưỡng 5%)
   * - 2
     - Trục throughput: S2 có hơn cấu hình tốt nhất ở bước 1 không
     - Đạt ngưỡng S2 ở mục 5.2
     - S2 "Loại", throughput dùng cấu hình tốt nhất ở bước 1
   * - 3
     - S3 có đáng giữ so với S2 không
     - Đạt ngưỡng S3 ở mục 5.2
     - S3 "Loại"
   * - 4
     - Điều kiện chung có thỏa không
     - Cả bốn dòng điều kiện chung
     - Kết quả không hợp lệ, đo lại

Nếu S2 "Loại" thì bước 3 so S3 với cấu hình tốt nhất ở bước 1, cùng số context.

5.4. Trạng thái hiện tại
------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 18 52 20

   * - Chiến lược
     - Nhãn
     - Bằng chứng
     - Đã làm
   * - S1
     - Loại (SiLU, latency)
     - T1: một số op chia được [T1 UG232 tr.75]. T2: lợi ích biên [T2 EDGE tr.7]. T3 (model đã huấn luyện, 1 seed): SiLU ``CORE_0_1_2`` giảm 2.9%, ReLU giảm 33.6% nhưng bị loại ở mAP (:doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`)
     - Bước 1
   * - S2
     - Giữ
     - Hàng đợi theo lõi [T1 DRV rknpu_job.c:545-553]. T3: 141.2 FPS, tăng 151.7% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`)
     - Bước 2, 3 lần độc lập
   * - S3
     - Loại
     - T3: tăng 4.4% so với S2, dưới ngưỡng 5% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 4). Không có T1 hay T2
     - Bước 3

Mục tiêu FPS tuyệt đối là một bước kiểm tra thêm, không thay các bước ở mục 5.3: 60 FPS (2026-11-01), đổi 30 FPS (2026-11-08, một luồng camera). Trước 2026-11-01 dự án chưa có mục tiêu FPS tuyệt đối nên quy tắc ở mục 5 là tương đối. Bối cảnh cho S1: "For most models, three-core configurations offered marginal or even negative improvements compared to single-core mode." [T2 EDGE tr.10]. Đây là bối cảnh, không phải bằng chứng cho hay chống S1 trên model của dự án.

6. Điểm chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Câu hỏi
     - Trạng thái
   * - Ai quyết định cách chia một job đa nhân
     - Driver chỉ đọc ``subcore_task`` do user-space truyền [T1 DRV rknpu_ioctl.h:241-243], phần tính nằm trong ``librknnrt``. Mẫu chia đã mô tả ở :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 5, quy tắc chưa biết
   * - ``ALL`` trong bảng 4 của EDGE
     - Bài không định nghĩa, không có phụ lục, dữ liệu theo yêu cầu từ tác giả [T2 EDGE tr.7, tr.11]. Đo trên board: chia đúng tập dòng của ``CORE_0_1_2``
   * - ``RKNNLite.inference`` có nhả GIL không
     - Ba tiến trình và ba luồng không khác ở mức 5% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 5), chưa kết luận [T1 rknn_lite.py:193-236]
   * - Context an toàn khi nhiều luồng dùng chung không
     - Không thấy trong tài liệu hãng. Dùng chung một context cho ba luồng cho đầu ra sai (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7). S2 không dùng chung nên không bị ảnh hưởng
   * - Nhiều tiến trình với các lõi khác nhau
     - Không thấy quy tắc [T1 CHANGELOG.md:162]. Đo: ba tiến trình chạy đồng thời trên ba nhân khác nhau với RKNNLite
   * - ``async_mode`` làm gì ở Lite2 2.3.2
     - API232 tr.16 ghi "Not Supported yet". Chương không dùng
   * - ``rknn_batch_size`` nhiều batch cho luồng video
     - Cơ chế: sao chép context, ``core_mask`` bằng 0, thread pool ba luồng [T1 UG232 tr.104], khuyên bội số của 3 [T1 UG232 tr.105]. Thăm dò 2026-11-01: batch 4 chạy, runtime ghi rơi về ``CORE_AUTO``, một ảnh lệch 0.19 ở lần lặp (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7). Ngoài S1 đến S3
   * - Lợi ích đa nhân của ReLU với model đã huấn luyện
     - Đo 2026-10-31 (1 seed): nhanh hơn 33.6% ở ``CORE_0_1_2``, mAP thấp hơn, bị loại ở G4 C (:doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`)
   * - Cách chọn lõi của ``AUTO``
     - Driver chọn hàng đợi ngắn nhất, hòa thì chỉ số thấp nhất [T1 DRV rknpu_job.c:508-538], sổ tay nói "idle core" [T1 UG232 tr.73]. Đo X4: 4 phiên ``AUTO`` đều chạy trên nhân 0 nên chưa phân biệt. Nhiều context chưa đo
