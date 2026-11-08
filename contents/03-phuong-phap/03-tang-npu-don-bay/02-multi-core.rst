**********
Multi-core
**********

.. admonition:: Trang này trả lời

   - Dùng ba nhân NPU của RK3588 cho pipeline PPE theo cách nào: chia một frame qua nhiều nhân (S1), nhiều context mỗi context một nhân (S2), hay chồng pha CPU và NPU (S3)?
   - Chọn cấu hình theo tiêu chí nào cho latency một luồng và cho throughput?
   - Điều gì đã biết, điều gì chưa biết, và cần đo gì trên board để quyết định?

.. admonition:: Tóm tắt

   - Chương đặt ba chiến lược S1, S2, S3 và quy tắc chọn theo hai trục (latency, throughput). Cập nhật 2026-10-31: cả ba đã đo, kết quả ở :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`. S1 (SiLU, latency): Loại. S2: Giữ. S3: Loại. Các nhãn là 1 seed, giao thức đo P2 và P3 được người dùng duyệt ngày 2026-11-01.
   - Hãng ghi đa nhân hợp với mạng lớn, mạng nhỏ có thể chậm đi vì việc chuyển đơn nhân và đa nhân cần CPU can thiệp [T1 UG232 tr.72]. Chỉ một số op được chia task qua nhiều nhân [T1 UG232 tr.75].
   - Bài Kong 2026 trên RK3588: đa nhân chỉ cho lợi ích biên, thường dưới 10% [T2 EDGE tr.2]. Ở YOLOv8n, ``C0_1_2`` là 25.33 ms còn ``C0`` là 24.54 ms [T2 EDGE tr.7].
   - Driver 0.9.8 có hàng đợi riêng cho từng lõi và mỗi lõi chạy một job tại một thời điểm [T1 DRV rknpu_job.c:431-455] [T1 DRV rknpu_job.c:545-553]. Đây là cơ sở cơ chế cho S2, lợi ích chưa đo.
   - ``async_mode`` được API guide ghi "(Not Supported yet)" [T1 API232 tr.16], nên S3 là thiết kế luồng ở tầng ứng dụng. Harness S3 đã viết 2026-10-31 (``ai/board/bench_throughput_rep.py``).
   - Quy tắc chọn dùng ngưỡng tương đối 5% (tham số của dự án, chốt 2026-10-25). Cập nhật 2026-11-01: người dùng chốt mục tiêu 60 FPS (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8, đo với model INT8 mặc định, ``int8h5`` không khác ``int8`` về thông lượng theo :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`). Trước ngày đó dự án chưa có mục tiêu FPS tuyệt đối trong tài liệu. Cập nhật 2026-11-08: người dùng đổi mục tiêu thành 30 FPS vì camera chỉ có 30 khung/giây, mọi cấu hình đã đo đạt (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8).
   - ``bench_throughput.py`` chạy một lượt cho mỗi cấu hình, nên chưa có độ trải. Đã làm 2026-10-31: harness mới lặp 3 lần độc lập mỗi cấu hình và có chế độ S3 (kết quả ở :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`).

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Phạm vi và quy tắc bằng chứng
================================

Chương xét việc dùng ba nhân NPU của RK3588 cho pipeline phát hiện PPE (YOLOv8n INT8, đầu vào 640x640, Orange Pi 5 với RK3588S). Luận điểm cần kiểm chứng: latency và throughput cần cấu hình đa nhân khác nhau, và quy tắc chọn dựa vào tỉ lệ cycles nằm ở op chia được qua nhiều nhân (điều kiện A của cổng G4 trong :doc:`01-operator-support`). Chương không tuyên bố kết quả nào đã đo. Mọi mục "chưa biết" đều kèm cách giải quyết.

1.1. Ba chiến lược
------------------

.. list-table::
   :header-rows: 1
   :widths: 8 40 22 30

   * - Mã
     - Cấu hình
     - Mục tiêu
     - Trạng thái trong repo
   * - S1
     - Một context chia một frame qua nhiều nhân: ``core_mask`` là ``CORE_0_1`` hoặc ``CORE_0_1_2``
     - Giảm latency một frame
     - Có mã đo (``ai/automation/benchmark_npu.py`` ở tầng 1 và ``ai/board/bench_npu.py`` ở tầng 2). Đã đo ngày 2026-10-31 (:doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`)
   * - S2
     - N context, mỗi context ghim một nhân (``CORE_0``, ``CORE_1``, ``CORE_2``), mỗi context một luồng
     - Tăng throughput
     - Có mã đo (``ai/board/bench_throughput.py``, và ``bench_throughput_rep.py`` lặp 3 lần) và cấu hình ba context có trong ``ai/automation/pipeline.py``. Đã đo ngày 2026-10-31 (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`)
   * - S3
     - Chồng pre và post-process trên CPU với phần chạy NPU bằng pipeline luồng ở tầng ứng dụng, có thể thêm ``async_mode``
     - Tăng throughput khi CPU là điểm nghẽn
     - Harness đã viết 2026-10-31 (``bench_throughput_rep.py --mode pipeline``). Đã đo (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`)

S1 và S2 dùng cùng API ``core_mask`` của ``init_runtime``. Khác nhau ở số context và cách chia việc: S1 để runtime chia trong một context, S2 để ứng dụng chia theo frame. Hai chiến lược trả lời hai câu hỏi khác nhau nên không so trực tiếp bằng một con số duy nhất.

1.2. Mức bằng chứng
-------------------

.. list-table::
   :header-rows: 1
   :widths: 14 56 30

   * - Tier
     - Nguồn
     - Trạng thái
   * - T1
     - Tài liệu hãng: SDK User Guide V2.3.2 (UG232), API guide V1.5.2 (UG152), API Reference V2.3.2 (API232), Operator List V2.3.2 (OPL) và mã nguồn driver rknpu 0.9.8 (DRV)
     - Có trong repo
   * - T2
     - Bài báo trong repo: Kong 2026 (EDGE), DAHD-YOLO 2025 (DAHD), Jung 2023, Min 2023 (Flexer)
     - Có trong repo
   * - T3 board
     - Bản ghi ngày 2026-10-10 (``eval_perf`` trên model trọng số ngẫu nhiên) và các phép đo ngày 2026-10-31 trên model đã huấn luyện (:doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`)
     - Nhật ký gốc của bản ghi 2026-10-10 đã bị xóa nên không kiểm lại được. Phép đo 2026-10-31 có quy tắc viết trước và dữ liệu trong ``bench/``

Mọi khẳng định có thẻ trong ngoặc vuông, ví dụ [T1 UG232 tr.75], [T2 EDGE tr.7], [T3 board, ghi nhận]. Thông tin lấy từ mã trong repo mang thẻ [Mã nguồn repo bench_throughput.py:59-62]. Số trang là trang PDF. Mục không có tier là "chưa biết" và ghi rõ cần gì để giải quyết. Số do người đọc tự tính từ số của nguồn được gọi là "số học của người đọc" và không phải lời của nguồn.

1.3. Không thuộc phạm vi
------------------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Nội dung
     - Lý do
   * - Chế độ ``rknn_batch_size`` lớn hơn 1
     - Là biến thể của hãng: runtime nhân bản context, đặt ``core_mask`` của từng context về 0 và dùng thread pool nội bộ [T1 UG232 tr.104]. Chương không đánh giá biến thể này, hiệu quả trên model của dự án là chưa biết. Cần chạy thử trên board để biết
   * - Độ chính xác (mAP)
     - Cấu hình ``core_mask`` không đổi trọng số. Điều kiện mAP nằm ở cổng G4 của :doc:`01-operator-support`
   * - Công suất và điện năng
     - Repo chưa có phép đo công suất đa nhân. Chương không bàn

Đính chính 2026-11-01: người dùng đã chốt mục tiêu 60 FPS, kiểm tra đạt hoặc không đạt ở :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8. Trước ngày đó dự án chưa có mục tiêu FPS tuyệt đối nào trong tài liệu (chưa biết, cần người dùng chốt hoặc nguồn yêu cầu từ ứng dụng giám sát). Quy tắc chọn ở mục 5 vẫn dùng ngưỡng tương đối so với cấu hình một nhân, mục tiêu 60 FPS là một bước kiểm tra thêm sau đó. Bài DAHD dùng mốc 25 FPS cho giám sát camera [T2 DAHD tr.18], nhưng đó là mốc của bài báo, không phải yêu cầu của dự án. Cập nhật 2026-11-08: mục tiêu đổi thành 30 FPS, một luồng camera (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8).

1.4. Nguồn và đường dẫn
-----------------------

- ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (nằm ngoài ``docs/``). Mã thẻ: ``UG232``.
- :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../../_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>`. Mã thẻ: ``UG152``.
- :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../../_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`. Mã thẻ: ``API232``.
- :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../../_assets/pdf/rknn/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>`. Mã thẻ: ``OPL``.
- Mã nguồn driver ``3rdparty/rknpu-driver-0.9.8``. Mã thẻ: ``DRV``.
- :download:`edgesoc_benchmark_2026kong.pdf <../../../_assets/pdf/papers/05_rk3588/edgesoc_benchmark_2026kong.pdf>` (Scientific Reports 2026, 16:5875). Mã thẻ: ``EDGE``.
- :download:`dahd_yolo_rk3588_2025.pdf <../../../_assets/pdf/papers/05_rk3588/dahd_yolo_rk3588_2025.pdf>`. Mã thẻ: ``DAHD``.
- :download:`mobile_multicore_npu_2023jung.pdf <../../../_assets/pdf/papers/01_hardware/mobile_multicore_npu_2023jung.pdf>` và :download:`flexer_multi_npu_2023min.pdf <../../../_assets/pdf/papers/01_hardware/flexer_multi_npu_2023min.pdf>`. Mã thẻ: ``Jung 2023`` và ``Min 2023``.
- Mã đo: ``ai/board/bench_throughput.py``, ``ai/board/bench_npu.py``, ``ai/board/common.py``, ``ai/automation/pipeline.py``.

Kiến thức nền về hai chế độ đa nhân và vùng nhớ dùng chung nằm ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/03-che-do-da-loi-va-system-sram` và về phân vùng layer qua nhiều lõi ở :doc:`../../01-kien-thuc-nen/02-npu/03-systolic-array-va-kien-truc-da-loi`. Chương không nhắc lại các trang đó.

2. S1: một context chia ba lõi
==============================

2.1. Hãng ghi nhận gì
---------------------

Hãng cảnh báo ngay đầu chương đa nhân rằng lợi ích phụ thuộc kích thước mạng:

   "Note: Multi-core operation is suitable for networks with a large amount of calculations. A little improvement for small networks, and may even lead to performance degradation due to single-core and multi-core switching (this switching requires CPU intervention)."

[T1 UG232 tr.72]

Hai tài liệu liệt kê op có chia task đa nhân và danh sách hơi khác nhau:

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Nguồn
     - Danh sách op chia được
   * - SDK User Guide V2.3.2
     - Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, LeakyRelu [T1 UG232 tr.75]
   * - API guide V1.5.2
     - Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, Prelu, LeakyRelu [T1 UG152 tr.27]

Hai danh sách trùng về tên op. Điểm khác chỉ ở cách ghi (UG232 dùng "and" nối ``PRelu`` và ``LeakyRelu``, UG152 ngăn bằng dấu chấm). Với op ngoài danh sách, UG152 ghi:

   "Other type of op will fallback to Core0 to continue running. In the future update, some ops like Pool or ConvTranpose will be supported."

[T1 UG152 tr.27]

Verdict đa nhân theo từng op (Conv, SiLU, Resize và các op còn lại của YOLOv8n) nằm ở :doc:`01-operator-support`, chương này không lặp lại.

Cột ``WorkLoad(0/1/2)-ImproveTherical`` trong log (đặt ``RKNN_LOG_LEVEL`` từ 4 trở lên [T1 UG232 tr.74]) cho biết cách chia từng layer:

   "It records how the tasks of each layer of the model are allocated on the NPU core and its theoretical performance improvement."

[T1 UG232 tr.75]

Ví dụ của hãng: ``50.0%/50.0%/0.0% - Up:50.0%`` nghĩa là lõi 0 và lõi 1 mỗi lõi 50%, layer đó lý thuyết nhanh hơn 50% so với một lõi [T1 UG232 tr.75]. Cột này là chỉ báo lý thuyết của riêng từng layer, không phải latency đo được. Hãng nêu hai lý do một layer chỉ chạy một nhân:

- Tải của layer nhỏ hơn độ hạt phân chia task đa nhân của NPU, nên layer chạy trên một nhân [T1 UG232 tr.75].
- Op chưa có phân đoạn đa nhân trong driver NPU, dự kiến hỗ trợ ở bản sau [T1 UG232 tr.75].

Hãng cũng khuyên bật tần số cao nhất cho CPU, DDR và NPU, gán ứng dụng và ngắt NPU vào lõi CPU lớn khi đo [T1 UG232 tr.75].

2.2. Driver cho thấy gì
-----------------------

Driver nhận job cùng mảng ``subcore_task`` từ user space (``include/rknpu_ioctl.h:241-243``, ``:279``). Kernel chỉ đọc mảng này, không tự chia. Driver chỉ dùng ``subcore_task`` để lấy số task của từng lõi [T1 DRV rknpu_job.c:71-94]. Ai tính phép chia: không thấy trong mã driver. Phép chia nhiều khả năng nằm ở thư viện ``librknnrt`` (suy luận), thư viện này là bản nhị phân và repo không có mã nguồn. Quy tắc chia chi tiết vì vậy là chưa biết. Cần mã nguồn ``librknnrt`` hoặc đối chiếu cột ``WorkLoad`` của nhiều model để suy ra.

Một job đa nhân (mask 0x1, 0x3 hoặc 0x7) chờ hoàn thành trên hàng đợi của lõi 0 [T1 DRV rknpu_job.c:27-47] [T1 DRV rknpu_job.c:179-200]. Hệ quả cần kiểm bằng đo: nếu lõi 0 đang bận job của context khác, job đa nhân phải đợi ở hàng đợi này. Chế độ ``AUTO`` chỉ gán một lõi cho job, nội dung đã có ở :doc:`../../02-nen-tang-rk3588/03-toolchain-runtime/03-driver-rknpu-va-rknn-server`, chương không nhắc lại.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Câu hỏi
     - Trạng thái
   * - Kernel có chia task qua nhiều nhân không
     - Không, kernel đọc ``subcore_task`` từ user space [T1 DRV rknpu_ioctl.h:241-243]
   * - Quy tắc chia nằm ở đâu và là gì
     - Chưa biết (``librknnrt`` không có mã nguồn)
   * - Job đa nhân chờ ở hàng đợi nào
     - Hàng đợi lõi 0 [T1 DRV rknpu_job.c:27-47]

2.3. Bằng chứng về lợi ích
--------------------------

Bài Kong 2026 đo YOLO trên RK3588 ở 640x640 với các chế độ lõi khác nhau. Bảng dưới chép nguyên bốn hàng của Table 4 (latency, ms) [T2 EDGE tr.7]:

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

Lưu ý khi đọc bảng:

- Bài báo không định nghĩa các mã cột ``C0``, ``C0_1_2`` và ``ALL`` trong phần văn bản đã đọc, cũng không nói ``ALL`` ứng với chế độ nào [T2 EDGE tr.7].
- Câu văn của bài: "YOLO11m achieved 93.7 ms in single-core mode and 95.5 ms in three-core mode" [T2 EDGE tr.7]. Theo số học của người đọc, 93.7 khớp ô ``C0`` (93.72) và 95.5 khớp ô ``ALL`` (95.51), không khớp ``C0_1_2`` (96.01).
- Ở YOLOv8n, theo số học của người đọc, ``C0_1_2`` (25.33 ms) chậm hơn ``C0`` (24.54 ms) và ``ALL`` (21.25 ms) thấp hơn ``C0`` 13.4%.
- Bài báo không thấy lợi ích tăng theo số nhân: "multi-core scheduling did not lead to proportional reductions in latency" [T2 EDGE tr.6] và tóm tắt "multi-core NPU scheduling yields only marginal gains (generally < 10%)" [T2 EDGE tr.2].
- Bài không nói pre-process và post-process có nằm trong vùng đo latency hay không (chưa biết) [T2 EDGE tr.2].

Bài báo nêu nguyên nhân như sau:

   "Performance improvements are constrained by inter-core communication, synchronization overhead, and shared memory bandwidth, preventing linear scaling with the number of cores."

[T2 EDGE tr.7]

Bài không kèm phép đo cô lập từng yếu tố. Jung 2023 nghiên cứu NPU di động nhiều lõi (không phải RK3588) và giải thích một cơ chế tương tự:

   "When a layer is partitioned and executed in parallel on multiple cores, synchronization is required at the end of layer execution."

[T2 Jung 2023 tr.5]

   "Synchronizations often cause performance degradation in multicore execution environments."

[T2 Jung 2023 tr.5]

Đây là cơ chế do T2 đề xuất cho NPU khác, repo không có phép đo nào chứng minh nó trên RK3588.

Hai bản ghi T3 board ngày 2026-10-10 trên YOLOv8n (``eval_perf``, median của 15 lần) [T3 board, ghi nhận]:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Bản ghi
     - Nội dung
   * - YOLO26n so với YOLOv8n (``06-yolo.rst``)
     - YOLO26n: 22.26 ms (AUTO), 21.70 ms (CORE_0), 22.09 ms (ba lõi). YOLOv8n: 19.40 ms, 19.16 ms, 18.985 ms. Ghi nhận "không có lợi ích đo được cho cả hai model". Về chia task: 21 trên 23 ``Concat``, 18 trên 18 ``Add`` và 11 trên 11 ``Conv`` chia ba lõi, 2 ``Concat`` chỉ lõi 0
   * - SiLU so với ReLU (``05-thiet-ke-model.rst``)
     - ReLU nhanh hơn ``CORE_0`` khoảng 8% khi dùng ba lõi: 13.969 ms xuống 12.854 ms (``relu_opt3``) và 13.955 ms xuống 12.801 ms (``relu_noadd``). SiLU không khác biệt ngoài độ trải

Giới hạn của hai bản ghi:

- Model có trọng số ngẫu nhiên, chỉ một kiến trúc cho mỗi lần đo, chưa có model đã huấn luyện.
- Nhật ký gốc đã bị xóa nên không kiểm lại được.
- Độ trải giữa các lượt: cùng một file ``.rknn`` SiLU ở ``AUTO`` đo được 19.154 ms rồi 22.021 ms, nguyên nhân chưa biết. Mức 8% của ReLU cần đối chiếu với độ trải này.
- Hai bản ghi là latency một frame, không đo throughput.

2.4. Kết luận cho S1
--------------------

S1 đáng thử khi điều kiện A của :doc:`01-operator-support` thỏa: các layer có workload chia từ hai nhân trở lên chiếm ít nhất 50% tổng cycles ước tính của build INT8. Đây là ngưỡng do dự án đặt, không lấy từ tài liệu hãng. Nếu điều kiện A không thỏa, lời cảnh báo ở UG232 tr.72 và số của EDGE cho thấy ba lõi khó mang lại lợi ích.

Trạng thái hiện tại (cập nhật 2026-10-31): **Loại** cho trục latency của model SiLU (1 seed). Đính chính: trước ngày đó là "Chưa biết". Kết quả: ``CORE_0_1_2`` nhanh hơn ``CORE_0`` 2.9% và ``CORE_0_1`` 2.2%, dưới ngưỡng 5% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 2). Quy trình hai phiên (latency không bật ``perf_debug`` và ``WorkLoad`` ở phiên ``perf_debug=True``) đã áp dụng dưới giao thức P2. Khoảng trống còn lại:

- Chưa biết quy tắc chia của ``librknnrt`` (mục 2.2). Cập nhật 2026-11-01: mẫu chia quan sát được đã mô tả (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 5), quy tắc vẫn chưa biết.
- Chưa biết ``ALL`` trong Table 4 của EDGE tương ứng chế độ nào (mục 2.3). Đã tìm lại toàn bộ bài báo và T1 ngày 2026-10-31, bài không định nghĩa ``ALL``. Cập nhật 2026-11-01: ``NPU_CORE_ALL`` (0xffff) chia đúng tập dòng của ``CORE_0_1_2`` ở runtime này, file kết quả không ghi số nhân từng dòng (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 6), nghĩa trong bài vẫn chưa biết.

Hai kết quả có thể xảy ra, và mỗi kết quả dẫn đến một việc khác nhau:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Kết quả đo S1
     - Ý nghĩa
   * - ``CORE_0_1_2`` nhanh hơn ``CORE_0`` đạt ngưỡng 5% của G4 điều kiện B
     - S1 là ứng viên cho mục tiêu latency, vẫn cần so với S2 ở mục 5
   * - Không đạt ngưỡng
     - Latency một frame dùng ``CORE_0``, ba lõi còn lại dành cho S2. Nguyên nhân (đồng bộ, băng thông bộ nhớ hay tải nhỏ) chưa biết nếu không đo riêng

3. S2: nhiều context, mỗi context một lõi
=========================================

3.1. Cơ chế trong kernel
------------------------

Mã driver cho thấy cách các job từ nhiều context đi vào ba lõi:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Hành vi
     - Nguồn
   * - Mỗi lõi có hàng đợi FIFO riêng. Job được thêm vào hàng đợi của từng bit lõi trong mask dưới ``irq_lock``
     - [T1 DRV rknpu_job.c:545-553]
   * - Mỗi lõi chạy một job tại một thời điểm, các job sau đứng trong hàng đợi. Hàm cấp phát ``rknpu_job_next`` trả về ngay nếu lõi đang có job hoặc hàng đợi rỗng
     - [T1 DRV rknpu_job.c:431-455] [T1 DRV rknpu_job.c:442-443]
   * - Hệ quả (suy ra từ hai dòng trên): các context ghim cùng một lõi bị tuần tự hóa trong kernel, các context ghim lõi khác nhau dùng hàng đợi khác nhau
     - Suy luận của chương
   * - Job của mọi tiến trình hoặc luồng vào cùng các hàng đợi này
     - [T1 DRV rknpu_job.c:545-553]
   * - Không tìm thấy mutex hoặc spinlock tuần tự hóa việc gửi job giữa các context trong ``rknpu_job.c`` (chỉ có ``irq_lock``)
     - [T1 DRV rknpu_job.c:545-553]
   * - Mặc định driver trễ 3 giây (``power_put_delay = 3000`` ms) trước khi tắt nguồn NPU sau một ioctl
     - [T1 DRV rknpu_drv.c:1466-1467]

Chương chỉ ghi nhận hành vi tắt nguồn trễ này của driver và không suy ra hệ quả cho latency hay throughput (chưa biết).

Hãng không ghi rõ các điểm sau (đã tìm trong UG232, UG152, API232, header và các CHANGELOG, không thấy):

- Một context RKNN có an toàn khi gọi từ nhiều luồng không (chưa biết). Cập nhật 2026-11-01: ba luồng dùng chung một context cho đầu ra sai âm thầm trong phép thử (300 trên 300 đầu ra khác, không exception), một luồng thì đúng (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7).
- Nhiều tiến trình cùng dùng các lõi khác nhau có được hỗ trợ không và có quy tắc gì không (chưa biết). CHANGELOG v1.1.0 chỉ ghi "Improve the stability of multi-thread + multi-process runtime", là ghi chú về độ ổn định.
- Giới hạn số context hoặc số context chạy đồng thời (chưa biết). Cập nhật 2026-11-01: tạo được 32 context liên tiếp, đều chạy đúng, dừng ở ngưỡng chặn nên giới hạn thật vẫn chưa biết (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7).
- Mẫu thread pool cho NPU: SDK không có demo dùng ``pthread_create``, ``std::thread``, ``threading`` hay ``multiprocessing`` cho NPU.

Hãng chỉ có hai câu gần với S2:

   "In a multi-threaded scenario, a model may be executed by multiple threads at the same time. If each thread initializes a context separately, the memory consumption will be very large. Therefore, the application can consider sharing a context to avoid repeated memory allocation of RKNN context and reduce runtime memory usage."

[T1 UG232 tr.153]

   "Alternatively, utilizing multi-threading in the application can help increase the NPU load."

[T1 UG232 tr.137]

Câu đầu cho thấy mỗi context riêng tốn bộ nhớ, đây là chi phí của S2 (mục 3.4). Cách chia sẻ trọng số là ``rknn_dup_context`` [T1 UG152 tr.27], API này không có trong bề mặt public của ``rknn_lite.py`` (``RKNNLite`` ở Python chỉ có ``init_runtime``, ``inference``, ``release`` và vài hàm khác). Chương không dùng ``dup_context`` cho Python.

3.2. Bằng chứng
---------------

Bài DAHD-YOLO chạy trên RK3588 và báo thread pool giúp pipeline:

   "the RK3588 integrates three NPU cores, each delivering a computational power of 2 TOPS, supporting modes such as three-core cooperative operation, dual-core cooperation, and independent operation. By utilizing a thread pool for acceleration, we optimize the entire detection process through multithreading."

[T2 DAHD tr.18]

   "optimizations such as quantization and multi-threading, the system achieves a detection rate of 50.2 fps"

[T2 DAHD tr.1]

Bản INT8 chạy một luồng mất 0.1162 s mỗi frame (khoảng 8.6 FPS theo số học của người đọc) [T2 DAHD tr.18]. Ba hạn chế khi dùng con số này:

- Bài báo không nêu số lõi mà mức 50.2 FPS sử dụng, nên không suy ra được đây là kết quả của ba context.
- Model và độ phân giải khác (1280x720), pipeline khác. Số 50.2 FPS không chuyển được sang YOLOv8n 640x640.
- Bài gộp lượng tử hóa và đa luồng vào một câu, nên không tách được phần đóng góp của đa luồng.

Cận trên do số học của người đọc: với ba context trên ba lõi, phần NPU không thể vượt ba lần một lõi. Toàn pipeline còn bị giới hạn bởi stage chậm nhất, theo công thức của repo (giả định các stage chồng nhau, không phải kết quả bài báo):

   Throughput FPS = 1000 / max(T_pre, T_npu, T_post)

[Mã nguồn repo docs/contents/01-kien-thuc-nen/05-bo-nho-hieu-nang/01-do-do-tre-va-profiling.rst:69-73]

Bài Kong không báo throughput và không chạy nhiều model đồng thời. Các cụm "concurrent", "multi-model" và "thread" đều không có trong 13 trang của bài (kết quả tìm kiếm trên toàn bài). Vì vậy repo không có T2 nào đo S2 trên RK3588 với model của dự án.

3.3. Harness của repo và giới hạn
---------------------------------

``ai/board/bench_throughput.py`` đo S2 theo các điều kiện sau:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Khía cạnh
     - Mã nguồn làm gì
   * - Luồng
     - Một luồng cho mỗi context, mỗi luồng chạy pre, NPU, post trên frame đã giải mã sẵn (file decode không nằm trong vùng đo) [Mã nguồn repo bench_throughput.py:3] [Mã nguồn repo bench_throughput.py:37]
   * - Số frame
     - ``--frames`` mặc định 1238, tổng cho mọi context. Bộ đếm ``itertools.count()`` dùng chung dưới ``threading.Lock`` [Mã nguồn repo bench_throughput.py:46-47] [Mã nguồn repo bench_throughput.py:57-58]
   * - Ảnh
     - Cache 200 ảnh đã giải mã, dùng vòng tròn theo ``frames[i % len(frames)]`` [Mã nguồn repo bench_throughput.py:27-28] [Mã nguồn repo bench_throughput.py:60]
   * - Warmup
     - ``WARMUP`` = 20 lần cho mỗi context, đều trên ``frames[0]`` [Mã nguồn repo common.py:27] [Mã nguồn repo bench_throughput.py:41-44]
   * - Vùng đo
     - Gồm ``preprocess``, ``rknn.inference`` và ``postprocess`` của từng frame, nên throughput có cả pre và post [Mã nguồn repo bench_throughput.py:59-62]
   * - Số lần chạy
     - Một lượt, không có vòng lặp lặp lại. Throughput = frame / thời gian từ Barrier đến khi mọi luồng ``join()`` [Mã nguồn repo bench_throughput.py:67-72] [Mã nguồn repo bench_throughput.py:91]
   * - Tần số
     - Ghi ``frequency_before`` và ``frequency_after`` nhưng không cố định [Mã nguồn repo bench_throughput.py:88-89]
   * - Giám sát
     - ``ResourceMonitor`` lấy mẫu mỗi 0.1 s [Mã nguồn repo common.py:184-187]
   * - Cấu hình lõi
     - ``MASKS_3CTX`` là ``CORE_0,CORE_1,CORE_2``, còn ``MASKS_1CTX`` gồm ``AUTO``, ``CORE_0``, ``CORE_0_1``, ``CORE_0_1_2`` [Mã nguồn repo pipeline.py:22-23]

Các giới hạn rút ra từ bảng:

- Chỉ một lượt đo, không có độ trải giữa các lượt. Khác với S1 đã có quy tắc hai phiên của G4.
- Tần số không cố định, nên khó tách ảnh hưởng của DVFS khỏi ảnh hưởng của số context.
- Ảnh cache 200 tấm lặp lại, không phản ánh ảnh thật trong luồng camera.
- Việc ``RKNNLite.inference`` có nhả GIL hay không là chưa biết, vì ``RKNNRuntime`` là file ``.so`` đã biên dịch và không có mã đọc được. Nếu không nhả, các luồng Python tuần tự hóa ở bước gọi NPU. Cần đo CPU trên từng luồng hoặc thử bản đa tiến trình để biết.
- Warmup chỉ dùng một frame (``frames[0]``), ảnh khác có thể cho thời gian post-process khác (chưa biết).

Trạng thái số liệu: đến ngày 2026-10-31 repo không có file JSON throughput nào (đã tìm ``*throughput*`` và ``tier1_*`` trong ``results/`` và ``docs/contents``). Ngày 2026-10-31 đã đo bằng harness mới ``bench_throughput_rep.py`` (``results/thr_p3.json``), sửa các giới hạn ở trên trừ ảnh cache lặp lại và nhả GIL (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`). Với harness cũ, khi có số đo, thứ cần so là throughput của ba context với throughput của cấu hình một context tốt nhất, cùng dtype, cùng model và cùng điều kiện ở mục 5.2.

3.4. Kết luận cho S2
--------------------

Trạng thái hiện tại (cập nhật 2026-10-31): **Giữ** (1 seed, giao thức P3 được người dùng duyệt ngày 2026-11-01, một model). Đính chính: trước ngày đó là "Chưa biết". Ba context đạt 141.2 FPS so với 56.1 FPS của cấu hình một context tốt nhất (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 3). Bảng dưới là trạng thái trước phép đo, các ô đã được cập nhật bằng câu "Đo 2026-10-31".

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Khía cạnh
     - Trạng thái
   * - Cơ chế
     - Có cơ sở từ mã driver: hàng đợi riêng từng lõi, không thấy khóa chung khi gửi job [T1 DRV rknpu_job.c:431-455] [T1 DRV rknpu_job.c:545-553]
   * - Lợi ích throughput
     - Đo 2026-10-31: 141.2 FPS với ba context, tăng 151.7% so với một context tốt nhất (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`). Bài DAHD có số 50.2 FPS nhưng khác model, khác độ phân giải và không nêu số lõi [T2 DAHD tr.18]
   * - Chi phí
     - Bộ nhớ: mỗi context riêng tốn thêm bộ nhớ [T1 UG232 tr.153]. Đo 2026-10-31: khoảng 12.8 MiB RSS tiến trình mỗi context thêm (không gồm bộ nhớ NPU)
   * - Độ an toàn khi dùng nhiều luồng
     - Chưa biết (SDK guide tr.153 nói về dùng chung context nhưng không nêu tính an toàn luồng). Phép đo 2026-10-31 chạy ba luồng, mỗi luồng một context, không lỗi trong các run ba luồng (T5, T6), nhưng không đo việc dùng chung một context

Cần đo để đóng khoảng trống: chạy ``bench_throughput.py`` ở ba context và ở các cấu hình một context, lặp nhiều lượt, cố định tần số, ghi tải CPU từng luồng. Ý nghĩa từng kết quả:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Kết quả đo S2
     - Cách đọc
   * - Throughput ba context vượt cấu hình một context tốt nhất đạt ngưỡng tương đối
     - S2 là cấu hình throughput. Ngưỡng cụ thể được đặt ở mục 5
   * - Throughput ba context không vượt ngưỡng
     - Giới hạn nằm ở phía CPU, GIL hoặc bộ nhớ. Chương không kết luận cái nào, vì repo chưa có phép đo tách các yếu tố này. S3 (mục 4) và một chẩn đoán đa tiến trình là hướng kiểm tra tiếp theo

4. S3: chồng pha CPU và NPU
===========================

4.1. Vì sao cần xét S3
----------------------

Trong harness ``ai/board/bench_throughput.py``, mỗi luồng chạy tuần tự ``preprocess``, ``rknn.inference`` và ``postprocess`` bên trong vùng được tính giờ [Mã nguồn repo bench_throughput.py:59-62]. Ảnh đã decode sẵn và phần decode file bị loại khỏi vùng đo [Mã nguồn repo bench_throughput.py:37]. Vì vậy ``throughput_fps`` đã gồm cả tiền xử lý và hậu xử lý, và phần CPU có thể giới hạn throughput dù NPU còn rảnh.

Công thức của repo cho throughput khi các pha chồng nhau:

.. code-block:: text

   Throughput FPS = 1000 / max(T_pre, T_npu, T_post)

Đây là công thức của repo, giả định các pha chạy chồng nhau, không phải kết quả từ bài báo [Mã nguồn repo 01-do-do-tre-va-profiling.rst:69-73]. Công thức cho thấy khi một pha CPU lớn hơn ``T_npu`` thì thêm lõi NPU không làm FPS tăng.

Khi harness chạy từ hai luồng trở lên, phần CPU của một luồng có thể trùng thời gian với phần NPU của luồng khác mà không cần cấu trúc riêng. S3 là việc làm điều này tường minh: tách worker tiền xử lý, worker NPU và worker hậu xử lý, nối với nhau bằng hàng đợi. Đây là một thiết kế được đề xuất, không phải một kết quả đã đo.

.. list-table::
   :header-rows: 1
   :widths: 22 39 39

   * - Cách chồng pha
     - Mô tả
     - Trạng thái
   * - Ngầm (S2)
     - Mỗi luồng giữ một context và tự chạy pre, NPU, post. Chồng pha xảy ra khi có từ hai luồng trở lên
     - Có harness [Mã nguồn repo bench_throughput.py:59-62]. Chưa có số đo trong repo
   * - Tường minh (S3)
     - Worker pre, NPU, post tách riêng, nối bằng hàng đợi
     - Chưa có harness. Chưa có số đo

4.2. Tài liệu hãng nói gì về ``async_mode``
-------------------------------------------

Tham số ``async_mode`` của ``init_runtime`` có một định nghĩa duy nhất trong tài liệu hãng, và định nghĩa này kết thúc bằng dòng ghi chưa hỗ trợ:

   "async_mode: Whether to use asynchronous mode. The default value is False. When calling the inference interface, it involves setting the input picture, model running, and fetching the inference result. If the asynchronous mode is enabled, setting the input of the current frame will be performed simultaneously with the inference of the previous frame, so in addition to the first frame, each subsequent frame can hide the setting input time, thereby improving performance. In asynchronous mode, the inference result returned each time is the previous frame. (Not Supported yet)"

[T1 API232 tr.16]

Chú thích của cờ C trong header nói về chế độ này:

   "asynchronous mode. when enable, rknn_outputs_get will not block for too long because it directly retrieves the result of the previous frame which can increase the frame rate on single-threaded mode, but at the cost of rknn_outputs_get not retrieves the result of the current frame. in multi-threaded mode you do not need to turn this mode on."

[T1 rknn_api.h:35-40]

Mô tả của ``rknn_run`` ở bản API cũ:

   "This interface is used for non-blocking mode inference and has not been implemented yet."

[T1 UG152 tr.38]

Các điểm còn lại về ``async_mode``:

- RKNN-Toolkit-Lite2 2.3.2 chỉ chuyển ``async_mode`` xuống runtime biên dịch sẵn (``rknn_lite.py:115,121`` và dòng 149). Runtime là tệp ``.so`` không có mã đọc được, nên hành vi thực tế trên board là chưa biết [T1 rknn_lite.py:115,149].
- Sổ tay SDK 2.3.2 không có từ ``async_mode``, ``async`` hay non-block trong 178 trang (đã tìm trên toàn bộ 178 trang).
- Sổ tay SDK 2.3.2 có một câu về đa luồng trong ứng dụng:

   "Alternatively, utilizing multi-threading in the application can help increase the NPU load."

[T1 UG232 tr.137]

Hệ quả cho chương này:

1. Chương không dựa vào ``async_mode``. API232 tr.16 ghi "Not Supported yet" và Lite2 không cho biết hành vi.
2. S3 là thiết kế ở tầng ứng dụng (hàng đợi và worker), không phải một cờ của runtime.
3. ``async_mode`` giữ trạng thái chưa đánh giá. Nếu cần, mục 6.1 nêu cách giải quyết.

4.3. Bằng chứng T2 nói gì
-------------------------

Bài báo EDGE (Kong 2026) đo latency "tại NPU runtime", không nêu thống kê tiền xử lý, hậu xử lý hay throughput. Các cụm "concurrent", "multi-model", "pre-process", "post-process", "NMS", "thread" không xuất hiện trong 13 trang (đã tìm trên toàn bài). Bài báo cũng không nói vùng tính giờ có gồm pre và post hay không, nên điều này là chưa biết [T2 EDGE tr.2].

Bài báo có một câu về tải CPU:

   "CPU utilization had relatively minor impact on inference latency, as the compute-intensive portion of YOLO execution is handled by the NPU."

[T2 EDGE tr.10]

Câu này nói về latency của phần NPU khi CPU bị tải bằng ``stress-ng`` [T2 EDGE tr.7]. Nó không nói gì về một pipeline bị giới hạn bởi CPU, nên không dùng để suy ra S3 có hay không có lợi.

DAHD-YOLO nêu thread pool trên RK3588 nhưng cho một model khác, ở độ phân giải khác:

   "By utilizing a thread pool for acceleration, we optimize the entire detection process through multithreading."

[T2 DAHD tr.18]

Bài báo không tách phần chồng pha CPU và NPU khỏi phần dùng nhiều nhân NPU.

4.4. Cần đo gì để đánh giá S3 và kết luận
-----------------------------------------

Để đánh giá S3, cần ba đại lượng theo từng frame là ``T_pre``, ``T_npu`` và ``T_post``, cùng FPS và phần trăm CPU trung bình khi chạy có và không có worker tách riêng. Harness hiện tại đo thời gian từng frame cho ba pha trong cùng vùng tính giờ [Mã nguồn repo bench_throughput.py:59-62] và ghi mẫu tài nguyên mỗi 0.1 giây (``ResourceMonitor``) [Mã nguồn repo common.py:184-187]. Bản ghi throughput chỉ có tóm tắt ``e2e_latency_ms``, không có phân vị [Mã nguồn repo bench_throughput.py:67-72]. Script tầng 2 một context ``ai/board/bench_npu.py`` ghi riêng pre, NPU, post và e2e cho từng ảnh, không tính đọc và giải mã file [Mã nguồn repo bench_npu.py:3-4], nên có thể lấy ``T_pre``, ``T_npu`` và ``T_post`` của một context từ đó.

Kết luận hiện tại cho S3:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Mục
     - Giá trị
   * - Trạng thái
     - Loại (cập nhật 2026-10-31, 1 seed, dưới P3 đã duyệt ngày 2026-11-01). Đính chính: trước ngày đó là "Chưa biết"
   * - Bằng chứng
     - Không có bằng chứng T1 (``async_mode`` chưa hỗ trợ) hay T2 cho riêng S3. Đo T3 2026-10-31: 147.4 FPS so với 141.2 FPS của S2, tăng 4.4%, dưới ngưỡng 5% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 4)
   * - Harness
     - ``ai/board/bench_throughput_rep.py --mode pipeline`` (viết 2026-10-31)
   * - Việc còn thiếu
     - Số worker pre và post khác công thức đã dùng chưa thử

5. Quy tắc chọn cấu hình
========================

5.1. Hai trục quyết định
------------------------

Luận điểm của chương: latency (một luồng camera) và throughput (nhiều luồng hoặc video offline) cần cấu hình khác nhau. Quy tắc dựa trên tỉ lệ cycles nằm trong op chia được qua nhiều nhân. Điều kiện A của G4 trong :doc:`01-operator-support` đo tỉ lệ này, nhưng sổ tay SDK nói thêm rằng đa nhân có thể làm giảm hiệu năng ở mạng nhỏ do việc chuyển giữa đơn nhân và đa nhân cần CPU can thiệp [T1 UG232 tr.72].

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

Sổ tay SDK 2.3.2 nói ``AUTO`` chọn lõi rảnh [T1 UG232 tr.73]. Driver 0.9.8 chọn lõi có số task xếp hàng ít nhất, không xét trạng thái rảnh [T1 DRV rknpu_job.c:508-538]. ``AUTO`` chỉ là tham chiếu, không phải ứng viên của quy tắc.

5.2. Ngưỡng
-----------

Các ngưỡng dưới đây là tham số của dự án, đã chốt ngày 2026-10-25, không lấy từ tài liệu ngoài. Hai ngưỡng đầu là điều kiện A và B của G4 trong Operator support.

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Điều kiện
     - Chuẩn
   * - Phủ đa lõi (A)
     - Các lớp có workload chia từ hai lõi trở lên chiếm ít nhất 50% tổng cycles ước tính (cột ``Cycles(DDR/NPU/Total)`` của build INT8)
   * - S1 nhanh hơn ``CORE_0`` về latency (B)
     - Median của 5 lần ``eval_perf`` cho mỗi ``core_mask``, lặp ở hai phiên ``init_runtime``, không bật ``perf_debug`` khi đo latency (``perf_debug`` có thể tắt cơ chế song song, xem điều kiện ở mục 2 của Operator support [T1 UG232 tr.177]). ``CORE_0_1_2`` được coi là nhanh hơn khi giảm ít nhất 5% và mức giảm lớn hơn chênh lệch median giữa hai phiên
   * - S2 hơn cấu hình tốt nhất của S1 về throughput
     - FPS cao hơn ít nhất 5%, median của 3 lần chạy độc lập, mức tăng lớn hơn độ trải giữa các lần chạy
   * - S3 đáng giữ
     - FPS cao hơn S2 ít nhất 5% với cùng số context, hoặc phần trăm CPU trung bình (Avg CPU) thấp hơn khi FPS không đổi (không đổi = chênh lệch nằm trong độ trải giữa các lần chạy)

Điều kiện chung cho mọi phép đo:

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Điều kiện
     - Chuẩn
   * - dtype
     - INT8 (``w8a8``) là dtype kết luận
   * - Tần số
     - Khóa tần số bằng ``lock_freq.sh``. Sổ tay SDK khuyên đặt CPU, DDR, NPU ở tần số cao nhất, gắn ứng dụng vào lõi CPU lớn và gắn ngắt NPU vào cùng lõi lớn đó [T1 UG232 tr.75]
   * - Nhiệt độ
     - Ghi nhiệt độ lúc bắt đầu và lúc kết thúc
   * - Seed
     - Chỉ chạy seed 0, mọi kết quả ghi nhãn "1 seed" vì chưa có std

Điều kiện C (mAP) của G4 không nằm trong bảng này vì cả S1, S2 và S3 đều dùng cùng model INT8 và không đổi trọng số.

5.3. Luồng quyết định
---------------------

Ứng viên dừng ở bước đầu tiên không qua. Nhãn "Giữ", "Loại" hoặc "Chưa biết" dùng như trong Operator support. Nhãn "Chưa biết" được giữ cho đến khi phép đo của bước đó đã chạy.

.. list-table::
   :header-rows: 1
   :widths: 8 30 34 28

   * - Bước
     - Câu hỏi
     - Qua khi
     - Kết quả khi trượt
   * - 1
     - Trục latency: S1 có nhanh hơn ``CORE_0`` không
     - Đạt điều kiện B ở mục 5.2 (điều kiện A là chỉ báo kèm theo, không quyết định)
     - S1 bị "Loại" cho trục latency. Latency dùng ``CORE_0``
   * - 2
     - Trục throughput: S2 có hơn cấu hình tốt nhất ở bước 1 không
     - Đạt ngưỡng S2 ở mục 5.2
     - S2 bị "Loại". Throughput dùng cấu hình tốt nhất ở bước 1
   * - 3
     - S3 có đáng giữ so với S2 không
     - Đạt ngưỡng S3 ở mục 5.2
     - S3 bị "Loại"
   * - 4
     - Điều kiện chung có thỏa không
     - Cả bốn dòng ở mục 5.2
     - Kết quả không hợp lệ. Đo lại

Nếu S2 bị "Loại" ở bước 2 thì bước 3 so S3 với cấu hình tốt nhất ở bước 1 thay vì với S2. Phép so này cần cùng số context. Trường hợp này cần chốt lại khi đặc tả harness S3 được viết.

5.4. Trạng thái hiện tại
------------------------

.. list-table::
   :header-rows: 1
   :widths: 10 14 46 30

   * - Chiến lược
     - Nhãn
     - Bằng chứng
     - Bước còn thiếu
   * - S1
     - Loại (SiLU, latency, cập nhật 2026-10-31)
     - T1: một số op chia được qua nhiều lõi [T1 UG232 tr.75]. T2: lợi ích biên [T2 EDGE tr.7]. T3 board 2026-10-31 (model đã huấn luyện, 1 seed): SiLU ``CORE_0_1_2`` giảm 2.9%, ReLU giảm 33.6% nhưng ReLU bị loại ở mAP (:doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`)
     - Đã làm bước 1 theo chuẩn hai phiên
   * - S2
     - Giữ (cập nhật 2026-10-31)
     - Hàng đợi theo lõi của driver hỗ trợ cơ chế [T1 DRV rknpu_job.c:545-553]. DAHD báo tăng FPS bằng thread pool trên model khác [T2 DAHD tr.1]. T3 2026-10-31: 141.2 FPS, tăng 151.7% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`)
     - Đã làm bước 2, 3 lần chạy độc lập
   * - S3
     - Loại (cập nhật 2026-10-31)
     - T3 2026-10-31: tăng 4.4% so với S2, dưới ngưỡng 5% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 4). Không có bằng chứng T1 hay T2
     - Đã làm bước 3

Cập nhật 2026-11-01: người dùng chốt 60 FPS (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8). Trước đó dự án chưa có mục tiêu FPS tuyệt đối (ghi nhận lúc đó: tìm "FPS", "real-time", "thời gian thực" và "camera" trong các trang tổng quan, kiến thức nền và phương pháp không thấy con số nào, câu hỏi về yêu cầu thời gian thực ở ``00-tong-quan/01-bai-toan-va-ung-dung.rst`` dòng 9 chưa có số trả lời, nên quy tắc ở mục 5 là tương đối). Mục tiêu người dùng chốt thêm một bước kiểm tra, không thay thế các bước ở mục 5.3, và người dùng chưa nói rõ 60 FPS là của một luồng hay tổng nhiều luồng, thông lượng hay thời gian mỗi khung. Mốc 25 FPS của DAHD là ngưỡng của chính bài báo, không phải của dự án [T2 DAHD tr.18]. Cập nhật 2026-11-08: người dùng đổi mục tiêu thành 30 FPS vì camera chỉ có 30 khung/giây, nên hiểu là một luồng camera.

Bối cảnh cho S1. Bằng chứng hiện có (T2 và T3 board) nghiêng về việc S1 chỉ cho lợi ích nhỏ:

   "For most models, three-core configurations offered marginal or even negative improvements compared to single-core mode."

[T2 EDGE tr.10]

Đây là bối cảnh, không phải bằng chứng cho hay chống S1 trên model của dự án. Chỉ phép đo ở mục 6.2 mới quyết định.

6. Điểm chưa biết và đặc tả đo T3 board
=======================================

6.1. Bảng điểm chưa biết
------------------------

.. list-table::
   :header-rows: 1
   :widths: 34 22 44

   * - Câu hỏi
     - Trạng thái
     - Cách giải quyết
   * - Ai quyết định cách chia một job đa nhân ở user-space
     - Chưa biết. Driver chỉ đọc ``subcore_task`` do user-space truyền xuống [T1 DRV rknpu_ioctl.h:241-243]. Phần tính cách chia nằm trong ``librknnrt`` dạng nhị phân. Cập nhật 2026-11-01: mẫu chia quan sát được ở :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 5, quy tắc vẫn chưa biết
     - Không có mã nguồn trong repo. Đọc cột ``WorkLoad(0/1/2)-ImproveTherical`` ở mức log 4 trở lên cho từng lớp [T1 UG232 tr.74-75]
   * - ``ALL`` trong bảng 4 của EDGE ứng với chế độ nào
     - Chưa biết. Bài báo không định nghĩa [T2 EDGE tr.7]. Số 95.5 ms khớp cột ALL (95.51), không khớp cột C0_1_2 (96.01). Đã tìm lại toàn bộ 13 trang ngày 2026-10-31: không có định nghĩa, dữ liệu theo yêu cầu từ tác giả (tr.11), không có phụ lục
     - Hỏi tác giả (dữ liệu theo yêu cầu). Hoặc đo ``ALL`` (giá trị 0xffff) trên board [T1 rknn_lite.py:15-21]. Đã làm 2026-11-01 (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 6): chia đúng tập dòng của ``CORE_0_1_2``
   * - ``RKNNLite.inference`` có nhả GIL không
     - Chưa biết. Runtime là ``.so`` [T1 rknn_lite.py:193-236]. Chẩn đoán 2026-10-31: ba tiến trình và ba luồng không khác ở mức 5% (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 5), chưa kết luận về GIL
     - Chẩn đoán đã làm, không phân biệt được
   * - Một context có an toàn khi nhiều luồng dùng chung không
     - Chưa biết. Không thấy câu nêu tính an toàn luồng trong UG232, UG152, API232 và header (UG232 tr.153 chỉ nói về dùng chung context, đính chính 2026-10-31) [T1 UG232, UG152, API232]
     - Harness hiện dùng một context cho mỗi luồng [Mã nguồn repo bench_throughput.py:3]. Chưa dùng chung nên không cần câu trả lời cho S2. Đo thăm dò 2026-11-01: dùng chung một context cho ba luồng cho đầu ra sai (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7). S2 không dùng chung context nên kết quả này không áp vào S2
   * - Dùng nhiều tiến trình với các lõi khác nhau
     - Không thấy quy tắc trong tài liệu hãng. Changelog chỉ có một ghi chú về ổn định [T1 CHANGELOG.md:162]. Đo 2026-10-31: ba tiến trình chạy được đồng thời trên ba nhân khác nhau với RKNNLite
     - Phép đo chẩn đoán ở mục 6.2 (ba tiến trình), đã làm
   * - ``async_mode`` làm gì lúc chạy trong Lite2 2.3.2
     - Chưa biết. API232 tr.16 ghi "Not Supported yet" [T1 API232 tr.16]
     - Chỉ đo được trên board và cần thiết kế riêng. Chương không dùng ``async_mode``. Thăm dò 2026-11-01: ``async_mode=True`` được chấp nhận và ``inference`` tuần tự vẫn trả đầu ra của ảnh vừa gửi (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7)
   * - ``rknn_batch_size`` nhiều batch có hợp cho luồng video không
     - Chưa biết. Tài liệu mô tả cơ chế: runtime sao chép context, mỗi context ``core_mask`` bằng 0, và một thread pool chạy ba luồng [T1 UG232 tr.104]. Hãng khuyên bội số của 3 cho RK3588 [T1 UG232 tr.105]. Chưa có tài liệu về độ trễ khi gom batch cho luồng video
     - Đo riêng nếu chủ dự án muốn xét. Nằm ngoài S1 đến S3. Thăm dò 2026-11-01: batch 4 chạy, runtime ghi rơi về ``CORE_AUTO``. Đầu ra từng ảnh khớp batch 1 ở lần đầu nhưng một ảnh lệch 0.19 ở lần lặp (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7)
   * - Mục tiêu FPS thời gian thực của dự án PPE
     - Người dùng chốt 60 FPS ngày 2026-11-01, đổi thành 30 FPS ngày 2026-11-08 (trước đó: không thấy con số trong các trang đã tìm [Mã nguồn repo 00-tong-quan/01-bai-toan-va-ung-dung.rst:9])
     - Đã làm: kiểm tra đạt hoặc không đạt ở :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8
   * - Lợi ích đa nhân của ReLU so với SiLU có còn với model đã huấn luyện không
     - Đã đo 2026-10-31 (1 seed): ReLU nhanh hơn 33.6% ở ``CORE_0_1_2`` so với ``CORE_0``, mAP thấp hơn, bị loại ở G4 C. Bản ghi 8% (trọng số ngẫu nhiên) chỉ ghi lại
     - Đã chạy theo :doc:`01-operator-support`, kết quả ở :doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`
   * - Cách chọn lõi của ``AUTO`` ở runtime user-space
     - Driver chọn lõi có hàng đợi ngắn nhất, hòa thì lấy chỉ số thấp nhất [T1 DRV rknpu_job.c:508-538]. Sổ tay nói "idle core" [T1 UG232 tr.73]. Hai mô tả không giống nhau. Đo X4 (2026-10-31): 4 phiên ``AUTO`` đều chạy trên dòng ngắt của nhân 0 (một job một lúc), hai mô tả cho cùng kết quả nên chưa phân biệt được. Nhiều context chưa đo
     - ``AUTO`` làm tham chiếu đã đo, chưa đo với nhiều context

6.2. Đặc tả đo T3 board
-----------------------

Chạy trên Orange Pi 5 RK3588S, model YOLOv8n INT8 640x640, đủ điều kiện chung ở mục 5.2.

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Mục
     - Giá trị
   * - Run S1 (1 context)
     - ``CORE_0``, ``CORE_0_1``, ``CORE_0_1_2``, thêm ``AUTO`` làm tham chiếu. Danh sách khớp ``MASKS_1CTX`` trong ``ai/automation/pipeline.py`` [Mã nguồn repo pipeline.py:22-23]
   * - Run S2 (nhiều context)
     - ``CORE_0,CORE_1,CORE_2`` với 3 context, cộng 1 và 2 context làm điểm đo mở rộng. Cấu hình 3 context khớp ``MASKS_3CTX`` [Mã nguồn repo pipeline.py:22-23]. Điểm 1 và 2 context chưa có trong pipeline
   * - Run S3
     - ``bench_throughput_rep.py --mode pipeline`` (viết 2026-10-31)
   * - Lặp lại cho latency
     - 5 lần ``eval_perf`` cho mỗi ``core_mask``, ở 2 phiên ``init_runtime`` (tham số của dự án)
   * - Lặp lại cho throughput
     - 3 lần chạy độc lập cho mỗi cấu hình (tham số của dự án). ``bench_throughput.py`` hiện chạy một lần cho mỗi cấu hình [Mã nguồn repo bench_throughput.py:57-58]
   * - Trường cần ghi
     - ``wall`` (thời gian chạy), ``throughput_fps``, ``e2e_latency_ms``, ``frames_per_context``, tài nguyên CPU và nhiệt độ, tần số trước và sau [Mã nguồn repo bench_throughput.py:67-72,88-91]
   * - Lệnh hiện có
     - Bước ``benchmark-npu`` của ``ai/automation/pipeline.py`` ghi ``tier1_int8_<mask>.json``. Bước ``bench-board-throughput`` ghi ``throughput_int8_<masks>.json`` [Mã nguồn repo pipeline.py:97,100-101]
   * - Chẩn đoán GIL (tùy chọn)
     - Cùng 3 context chạy bằng 3 tiến trình, so với 3 luồng. Đây là chẩn đoán, không phải chiến lược mới. Nếu hai kết quả khác nhau rõ thì GIL hoặc cơ chế luồng là nghi vấn, chưa phải kết luận
   * - Chưa làm (cần sửa repo)
     - Đã làm 2026-10-31 trong ``bench_throughput_rep.py`` (vòng lặp 3 lần do driver, harness S3, điểm 1 và 2 context, chẩn đoán 3 tiến trình). Chưa thêm vào ``ai/automation/pipeline.py``

Thứ tự đề xuất: S1 trước, vì bước 1 của mục 5.3 quyết định đối chứng cho S2, rồi S2, rồi S3. Throughput FPS trong chương là số frame chia cho thời gian chạy của cả pipeline (pre, NPU, post) như ``bench_throughput.py`` tính [Mã nguồn repo bench_throughput.py:91]. Nền tảng chế độ đa lõi và system SRAM của phần cứng nằm ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/03-che-do-da-loi-va-system-sram`.

6.3. Mỗi kết quả sẽ thay đổi quyết định thế nào
-----------------------------------------------

Bảng dưới chỉ mô tả hệ quả của từng kết quả, không dự đoán kết quả nào sẽ xảy ra.

.. list-table::
   :header-rows: 1
   :widths: 36 64

   * - Kết quả đo
     - Thay đổi
   * - S1 đạt điều kiện B
     - Trục latency dùng ``CORE_0_1_2`` hoặc ``CORE_0_1``, tùy mặt nạ nào đạt. S1 chuyển sang "Giữ" cho latency
   * - S1 không đạt điều kiện B
     - Trục latency dùng ``CORE_0``. S1 chuyển sang "Loại" cho latency. Các lõi còn lại dành cho S2
   * - S2 đạt ngưỡng throughput
     - Throughput dùng ba context ghim lõi. S2 chuyển sang "Giữ" cho throughput
   * - S2 không đạt ngưỡng
     - Throughput dùng cấu hình tốt nhất ở trục latency. S2 chuyển sang "Loại"
   * - Chẩn đoán GIL cho thấy khác biệt rõ giữa 3 tiến trình và 3 luồng
     - Mở một câu hỏi mới về cách chạy S2 (đa tiến trình thay vì đa luồng). Cần đặc tả bổ sung, chưa thuộc quy tắc này
   * - S3 đạt ngưỡng
     - S3 chuyển sang "Giữ". Harness S3 thành thành phần chính thức
   * - S3 không đạt ngưỡng
     - S3 chuyển sang "Loại". Cấu hình theo S2 hoặc S1 giữ nguyên
   * - Phần CPU lớn hơn ``T_npu``
     - Theo công thức của repo, thêm lõi NPU không tăng FPS. Việc cần làm chuyển sang giảm thời gian pre và post
   * - Mục tiêu FPS tuyệt đối được đặt
     - Thêm một bước kiểm tra đạt hoặc không đạt mục tiêu sau mục 5.3. Không thay các bước hiện có. Đã làm 2026-11-01 với mục tiêu 60 FPS, đọc lại 2026-11-08 với mục tiêu 30 FPS (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8)
