*********************
Kế hoạch đo từng khối
*********************

.. admonition:: Trang này trả lời

   - Khối nào của YOLOv8n (L0 đến L22, xem :doc:`../01-tang-ai/02-kien-truc-model`) chiếm bao nhiêu thời gian NPU trên RK3588, và có op nào chạy trên CPU?
   - Đo bằng quy trình nào, mỗi thông số trả về nghĩa là gì, giới hạn ra sao?
   - Điều kiện nào để chấp nhận một lần đo và kết quả được báo dưới dạng nào?

.. admonition:: Tóm tắt

   - Trang này là kế hoạch và quy trình đo. Kết quả đo nằm ở :doc:`02-ket-qua-latency-tung-khoi`, phân tích sâu ở :doc:`03-phan-tich-sau-latency-tung-khoi`, các mức độ trễ và giả thuyết đã kiểm ở :doc:`04-cac-muc-do-tre`, thí nghiệm ghim CPU và ngắt NPU ở :doc:`05-thu-ghim-cpu-va-ngat`, cơ chế các mức ở :doc:`06-co-che-cac-muc-do-tre`, giao thức P2 và đo mở rộng ở :doc:`08-ket-qua-p2-va-do-mo-rong`. Mục 9 có bảng trạng thái mọi việc chưa biết. Mục 3 ghi trạng thái từng bước.
   - Đối tượng: YOLOv8n ``nc=5`` của run ``ppe5_yolov8n_baseline_100ep_s0``, export INT8 (w8a8) mới, ``core_mask = CORE_0``, tần số khoá ở ``performance``. Mô hình và con số GFLOPs theo từng khối lấy ở trang kiến trúc.
   - Nguồn số liệu chính là ``rknn.eval_perf()`` chạy từ PC qua adb, lấy thời gian từ phần cứng board [T1 API232 tr.18]. Hai phiên ``init_runtime`` riêng: ``perf_debug=False`` cho latency tổng, ``perf_debug=True`` cho thời gian từng lớp. Đường PC đến board chậm và latency dao động giữa các phiên, nên có thêm đo ngay trên board bằng C API (``ai/board/rknn_perf_bench.c``, bước B7) và thí nghiệm E2 về vị trí CPU, ngắt NPU và trạng thái ngủ của CPU (:doc:`05-thu-ghim-cpu-va-ngat`).
   - Hãng ghi ``perf_debug=True`` làm thời gian lớn hơn vì thêm mã debug và có thể tắt một số cơ chế song song [T1 UG232 tr.177]. Vì vậy thời gian từng khối chỉ báo dưới dạng tỉ lệ phần trăm kèm tổng debug, không cộng thành latency.
   - Tài liệu hãng không nói tổng thời gian từng lớp có bằng tổng thời gian khung hay không. Trang đo cả hai và báo tỉ số, không giả định.
   - Cột ``NPUCycles`` hiện chỉ tính cho Conv [T1 UG232 tr.140], nên tỉ lệ cycles của op khác Conv luôn bằng 0 và không dùng thay thời gian đo.
   - Quy tắc gộp các lớp RKNN về L0-L22 dựa vào cột ``FullName``. Trên bảng đo của export ppe5 (119 dòng), 114 dòng có chỉ số ``model.N`` và 5 dòng không có (mục 5). Bảng đo trên board giống hệt bảng build về ``OpType`` và ``FullName`` (tiêu chí A1 đạt).

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Mục tiêu và phạm vi
======================

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Câu hỏi
     - Trả lời bằng
     - Trạng thái
   * - Mỗi khối L0-L22 chiếm bao nhiêu phần trăm thời gian NPU ở ``CORE_0``, INT8?
     - Bảng từng lớp ở phiên ``perf_debug=True``, gộp theo mục 5
     - Đã đo (B2, ba phiên B3, đo trên board bằng C API). Kết quả ở :doc:`02-ket-qua-latency-tung-khoi`, tỉ lệ khối ổn định ở các khối lớn và không ổn định ở khối nhỏ
   * - Thành phần nào trong khối tốn thời gian (Conv ``cv1``, ``Split``, Bottleneck, ``Concat``, ``cv2``, và trong Detect: nhánh box, nhánh cls, DFL, giải mã)?
     - Cùng bảng, gộp theo mục 5.2
     - Đã đo, kết quả ở :doc:`02-ket-qua-latency-tung-khoi`
   * - Có op nào chạy trên CPU, nó tốn bao nhiêu?
     - Cột ``Target`` của bảng từng lớp. Bảng build INT8 của model cũ có 1 op ``Transpose`` ở DFL trên CPU
     - Đã đo: chỉ ``Transpose`` ở DFL chạy trên CPU. Kết quả ở :doc:`02-ket-qua-latency-tung-khoi`
   * - Latency tổng một khung ở ``CORE_0`` là bao nhiêu và thời gian từng lớp lệch bao nhiêu so với tổng?
     - Phiên ``perf_debug=False`` (latency) đối chiếu phiên ``perf_debug=True`` (tổng debug)
     - Đã đo. Latency ``eval_perf`` giữa các phiên lệch hơn ngưỡng 5% (cổng A5 không đạt), kết quả ở :doc:`02-ket-qua-latency-tung-khoi` và :doc:`04-cac-muc-do-tre`

Trang không trả lời các câu sau, mỗi câu có trang riêng:

- So SiLU với ReLU và so ``CORE_0`` với ``CORE_0_1_2``: cổng G4 ở :doc:`../03-tang-npu-don-bay/01-operator-support` và chiến lược S1, S2, S3 ở :doc:`../03-tang-npu-don-bay/02-multi-core`.
- Thời gian tiền xử lý, hậu xử lý và NMS ngoài NPU: tier 2 (``ai/board/bench_npu.py``), nằm ngoài phạm vi trang này.
- Độ chính xác (mAP) sau INT8.

2. Đối tượng và điều kiện cố định
=================================

.. list-table::
   :header-rows: 1
   :widths: 22 40 38

   * - Tham số
     - Giá trị
     - Lý do và nguồn
   * - Model
     - ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/weights/best.pt``, YOLOv8n chuẩn ``nc=5``, 3,011,823 tham số
     - Cùng model với trang kiến trúc (đối chiếu 355 tensor). Latency phụ thuộc cấu trúc nên dùng đúng cấu trúc đã mô tả
   * - Export
     - ``make export-npu RUN=<id> PREC=int8``: RKNN-Toolkit2 2.3.2, calibration 300 ảnh train, mỗi class ít nhất 20 ảnh, seed 0, LetterBox 640
     - Giống chuẩn G3 ở :doc:`../03-tang-npu-don-bay/01-operator-support`. Export mới hoàn toàn, không dùng lại ``.rknn`` hay log cũ
   * - dtype
     - INT8 (w8a8)
     - dtype kết luận của G4
   * - ``core_mask``
     - ``CORE_0``
     - Một nhân để thời gian từng lớp không lẫn với việc chia task qua nhiều nhân. Cột ``WorkLoad`` phải là 100% ở Core0 (tiêu chí A3)
   * - Board
     - Orange Pi 5 (RK3588S), ``rknn_server`` 2.3.2, adbd cổng 5555
     - Log ``rknn_server`` ghi version 2.3.2 (``/tmp/rknn_server.log`` trên board, 2026-10-30)
   * - Tần số
     - ``lock_freq.sh lock``: CPU 1.8, 2.256 và 2.304 GHz, NPU 1.0 GHz, DDR 2.112 GHz
     - Hãng nêu cùng một model đo ở tần số khác nhau dao động lớn [T1 UG232 tr.136]. Giá trị đọc từ board ngày 2026-10-30
   * - Đầu vào
     - Không có. ``eval_perf`` chỉ nhận ``is_print`` và ``fix_freq`` [T1 API232 tr.18]
     - Phép đo không phụ thuộc ảnh của dự án. Giả định thời gian không phụ thuộc giá trị trọng số và dữ liệu: đã kiểm ngày 2026-10-31 (X5), không phụ thuộc trong bốn đầu vào và hai mô hình đã thử (:doc:`08-ket-qua-p2-va-do-mo-rong`, mục 5)

3. Quy trình từng bước
======================

Mỗi bước có lệnh, file tạo ra và điều kiện đạt. Chưa qua điều kiện đạt thì không sang bước sau.

.. list-table::
   :header-rows: 1
   :widths: 6 24 30 22 18

   * - Bước
     - Việc làm
     - Lệnh hoặc cách làm
     - File tạo ra
     - Điều kiện đạt
   * - B0
     - Chuẩn bị board
     - Trên board: ``sudo bash ai/board/start_rknn_server.sh``, ``sudo bash ai/board/lock_freq.sh lock``. Trên PC: ``make board-check LOCK=1``
     - Ghi ``lock_freq.sh status``, nhiệt độ và tải lúc bắt đầu
     - ``board-check`` in ``frequencies locked: True``, ``adb`` và ``rknn_server`` ok
   * - B1
     - Export INT8 mới
     - ``make export-npu RUN=ppe5_yolov8n_baseline_100ep_s0 PREC=int8`` (đặt ``RKNN_LOG_LEVEL=3`` để log build in bảng từng lớp ước tính)
     - ``weights/rknn_int8/*.rknn``, ``export_int8.json`` (sha256, phiên bản, calibration), log build
     - ``export_int8.json`` có đủ sha256 và danh sách 300 ảnh calibration
   * - B2
     - Đo thử và lưu nguyên văn đầu ra
     - Chạy một lần ``make benchmark-npu RUN=<id> PREC=int8 CORE_MASK=CORE_0``, giữ file ``*_layers.txt``
     - ``bench/tier1_int8_CORE_0.json``, ``*_layers.json``, ``*_layers.txt``
     - Nhãn thực tế trong đầu ra khớp các biểu thức trong ``ai/core/rknn/benchmark.py`` (mục 4.1)
   * - B3
     - Ba lần đo độc lập
     - Lặp ``make benchmark-npu`` ba lần. Mỗi lần có ba phiên ``init_runtime`` riêng (latency, từng lớp, bộ nhớ)
     - Ba bộ file ``tier1_*`` (đặt tên riêng để không ghi đè)
     - Tiêu chí A1 đến A5 (mục 7)
   * - B4
     - Gộp về khối
     - Script gộp theo mục 5 (chưa có, mục 9)
     - Bảng khối và bảng thành phần (``results/``)
     - Mọi dòng được gán nhóm, tổng tỉ lệ bằng 100%
   * - B5
     - Đối chiếu chéo
     - Mục 6 dưới đây, và ``make bench-board`` (tier 2) cho cùng file ``.rknn``
     - Bảng tỉ số
     - Báo đủ các tỉ số ở mục 8
   * - B6
     - Ghi kết quả
     - Sinh các trang 02 đến 06 và 08 của nhóm này, cùng trang ``04-do-chinh-xac-int8-do-latency`` của nhóm kết quả đo, bằng ``docs/tools/gen_latency_results_page.py``: chép số kèm file (tạo tự động từ ``results/*.json``)
     - Trang docs, file ``tier1_*`` còn nguyên
     - Mọi số trong trang truy ra được file
   * - B7
     - Đo trên board bằng C API (không qua PC)
     - Biên dịch ``ai/board/rknn_perf_bench.c`` trên board, chạy ``onboard_run.sh``: 3 đợt 1000 lần liên tiếp (đợt 1 lấy mẫu ``rknpu/load`` và ``power``), thử nghỉ 2 và 10 giây giữa các lần chạy, 3 đợt 200 lần ở chế độ ``detail``, chụp ``cpuidle`` trước và sau mỗi đợt
     - ``bench/onboard/*``, ``results/onboard_*.md``
     - Tiêu chí ở :doc:`04-cac-muc-do-tre`

Trạng thái ngày 2026-10-30: B0, B1 và B2 đạt. B3 chạy đủ ba phiên (``SESSION=1..3``, ``SKIP_MEMORY=1``). B4 chạy, cổng A5 và A8 không đạt (:doc:`02-ket-qua-latency-tung-khoi`, mục 4). B5 làm bằng B7 (C API trên board) thay cho tier 2 RKNNLite, vì C API là cách hãng khuyên cho tốc độ khung thực tế [T1 UG232 tr.175]. B6 là các trang 02 đến 06 và 08 của nhóm này (lúc viết là các trang 02 đến 07 của nhóm Đo latency trên NPU, trang 07 sau đó được đổi tên và đánh lại số). FP16 chưa chạy vì cổng A8 của INT8 không đạt. Ngày 2026-10-30 chạy thêm E2b (điều kiện B với ``irqbalance`` dừng), kết quả ở :doc:`05-thu-ghim-cpu-va-ngat` mục 3. Cùng ngày chạy E2c (tách vị trí ứng dụng và ngắt NPU) và kiểm tra hợp lệ viết trước không đạt, nên chưa đọc được yếu tố nào (:doc:`05-thu-ghim-cpu-va-ngat` mục 4). Ngày 2026-10-31 chạy E2d (bản đồ vị trí ứng dụng và ngắt NPU, 20 điều kiện), kiểm tra hợp lệ đạt, kết quả ở :doc:`05-thu-ghim-cpu-va-ngat` mục 5. Cùng ngày chạy E2e (ghim ``rknn_server`` và ngắt NPU trên đường ``eval_perf``, sáu ô, quy tắc viết trước), kết quả ở :doc:`05-thu-ghim-cpu-va-ngat` mục 6.

Quy ước đo (áp dụng cho B2 và B3):

- Hai phiên không dùng chung ``init_runtime``. ``perf_debug`` và ``eval_mem`` đổi thời gian đo nên mỗi cái một phiên (``ai/core/rknn/benchmark.py``, hàm ``connect_board``).
- Phiên latency: 5 lần ``eval_perf``, lấy median, lưu cả 5 giá trị. Phiên từng lớp: 5 lần ``eval_perf``, mỗi dòng lấy median qua 5 lần và lưu cả 5 giá trị (``time_us_all``).
- Số phiên độc lập là 3, không phải 2 như chuẩn G4. G4 chỉ cần hai phiên để so ``core_mask``. Với đo từng khối cần ba phiên để thấy độ trải. Đây là tham số đề xuất của trang này.
- Chi phí một phiên qua đường PC đến board (số đo ngày 2026-10-30 qua relay Tailscale, RTT 160 đến 270 ms, trên LAN trực tiếp RTT khoảng 0.5 ms (đo ngày 2026-10-30), ``init_runtime`` 1.5 giây (đo ngày 2026-10-31) và mỗi lần ``eval_perf`` 0.21 đến 0.43 giây, xem :doc:`04-cac-muc-do-tre` mục 2): ``init_runtime`` mất khoảng 4 phút và mỗi lần ``eval_perf`` mất 34.4 đến 57.4 giây thực (kể cả ở phiên không debug), trong khi NPU chạy một khung chỉ khoảng 19 ms [T3 board]. Một phiên (latency và từng lớp, bỏ bước bộ nhớ bằng ``SKIP_MEMORY=1``) mất khoảng 15 phút. Thời gian ``eval_perf`` vẫn lấy từ phần cứng board [T1 API232 tr.18], nên đường truyền chậm làm phép đo lâu chứ không làm sai.

4. Thông số trả về và ý nghĩa
=============================

4.1. Phiên latency (``perf_debug=False``)
-----------------------------------------

Hãng ghi khi ``perf_debug=False`` thì thông tin lấy từ phần cứng và chỉ có tổng thời gian chạy model [T1 API232 tr.16]. ``eval_perf`` trả về chuỗi ``perf_result`` [T1 API232 tr.18]. Ngoài thời gian, đầu ra in danh sách tần số CPU, NPU, DDR hiện tại [T1 UG232 tr.31].

.. list-table::
   :header-rows: 1
   :widths: 28 14 30 28

   * - Thông số
     - Đơn vị
     - Ý nghĩa
     - Giới hạn
   * - ``Total Time(us)`` (nhãn mà parser của repo tìm)
     - µs
     - Thời gian NPU chạy một khung ở ``core_mask`` đã chọn. Latency chính của trang
     - UG232 và API232 không chứa nhãn này. Đầu ra thật ở B2 (2026-10-30, SDK 2.3.2) in ``Total Time(us): <số>`` và ``FPS: <số>`` [T3 board], nên parser của repo đúng. Ở phiên debug nhãn là ``Total Operator Elapsed Per Frame Time(us)``
   * - Danh sách ``CPU/NPU/DDR Current Frequency List``
     - kHz (CPU), Hz (NPU, DDR)
     - Tần số tại lúc đo. Dùng chứng minh tần số đã khoá
     - ``fix_freq`` cố định tần số CPU, NPU và DDR theo hãng. Nút và thứ tự đặt chỉ thấy một phần qua chuỗi trong thư viện (mục 9, U14)
   * - ``npu_latency_ms_all``
     - ms
     - 5 giá trị riêng của 5 lần gọi, do repo lưu
     - Hãng không nêu khởi động lạnh hay lần đầu chậm hơn. Giữ nguyên cả 5 để tự xem

4.2. Phiên từng lớp (``perf_debug=True``)
-----------------------------------------

Hãng ghi: "If the perf_debug is set to True, the running time of each layer will also be captured in detail." [T1 API232 tr.18]. Bảng từng lớp có tên "Network Layer Information Table" [T1 UG232 tr.56]. Định nghĩa các cột nằm ở [T1 UG232 tr.32]:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Cột
     - Hãng định nghĩa
     - Dùng trong trang này
   * - ``ID``, ``OpType``, ``FullName``
     - Chỉ số, loại và tên đầy đủ của operator
     - Khoá để so với bảng build và để gộp về khối (``FullName`` chứa ``model.N``)
   * - ``DataType``, ``Target``
     - Kiểu dữ liệu đầu vào. Phần cứng chạy op (CPU, NPU hoặc GPU)
     - Tìm op chạy trên CPU
   * - ``InputShape``, ``OutputShape``
     - Hình dạng vào và ra
     - Đối chiếu với kích thước tensor ở trang kiến trúc
   * - ``DDRCycles``, ``NPUCycles``
     - Chu kỳ đọc ghi DDR và chu kỳ NPU. DDR Cycles đã đổi sang đơn vị chu kỳ ở tần số NPU nên so trực tiếp được [T1 UG232 tr.140]
     - Ước lượng của compiler, không phải thời gian. ``NPUCycles`` hiện chỉ có cho Conv [T1 UG232 tr.140]
   * - ``MaxCycles`` (UG tr.32) hoặc ``Total Cycles`` (README mẫu và UG tr.74)
     - Giá trị lớn hơn của ``DDRCycles`` và ``NPUCycles``
     - Cột thực tế tên ``Cycles(DDR/NPU/Total)``. Ở cả 119 dòng của B2, giá trị thứ ba bằng max của hai giá trị đầu [T3 board]. Chỉ 64 dòng (``Conv`` và ``ConvExSwish``) có ``NPUCycles`` khác 0, khớp UG232 tr.140. Định nghĩa ``Total Cycles`` của hãng không có trong UG232 và API232
   * - ``Time(us)``
     - Thời gian tính toán của operator
     - Đại lượng chính để gộp. Là thời gian ở phiên debug
   * - ``MacUsage(%)``
     - "MAC usage"
     - Hãng không định nghĩa thêm. Báo kèm, không suy diễn
   * - ``WorkLoad(0/1/2)``
     - Tỉ lệ khối lượng của lớp chia cho Core0, Core1, Core2 (chỉ RK3588) [T1 UG232 tr.32] [T1 UG232 tr.75]
     - Ở ``CORE_0`` phải là 100% ở Core0 (tiêu chí A3)
   * - ``RW(KB)``
     - Tổng dữ liệu đọc ghi (KB)
     - Báo kèm. ``RW(KB)`` là đo hay tính từ mô hình thì vẫn chưa biết sau khi tìm nguồn (mục 9, U17, và :doc:`../../09-tien-do/03-khoang-trong/04-bo-nho-hieu-nang`)

Các dòng tổng và bảng xếp hạng đi kèm [T1 UG232 tr.56] [T1 UG232 tr.33]:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Mục
     - Ý nghĩa
   * - ``Total Operator Elapsed Per Frame Time(us)``
     - Tổng thời gian operator của một khung ở phiên debug. Repo lưu thành ``debug_total_us``. Không phải latency
   * - ``Total Memory Read/Write Per Frame Size(KB)``
     - Tổng dữ liệu đọc ghi của một khung
   * - Bảng ``Operator Time Consuming Ranking``: ``OpType``, ``CallNumber``, ``NPUTime(us)``, ``TotalTime(us)``, ``TimeRatio(%)``
     - Gộp theo ``OpType``. ``TotalTime(us)`` là tổng thời gian của operator đó trong một khung. ``TimeRatio(%)`` là tỉ lệ của nó so với tổng thời gian một khung
   * - Hãng nói kết quả này chỉ dùng để gỡ lỗi
     - Tài liệu mẫu của SDK ghi "The performance result is just for debugging" và "may worse than actual performance!" (``npu_device_test/README.md:40-41``)

Hãng ghi lý do bật ``perf_debug``: xem lớp nào tốn thời gian để tối ưu [T1 UG232 tr.177]. Đây đúng là mục đích của trang này.

4.3. Đại lượng dự án tự tính
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 26 44 30

   * - Đại lượng
     - Công thức
     - Ý nghĩa
   * - ``block_us`` (khối k)
     - Tổng ``Time(us)`` của các dòng gán cho khối k, lấy median qua 5 lần ``eval_perf`` rồi median qua 3 phiên
     - Thời gian khối k ở chế độ debug
   * - ``share_k``
     - ``block_us`` chia tổng ``Time(us)`` của mọi dòng cùng phiên
     - Tỉ lệ thời gian của khối, cộng lại bằng 100%. Đại lượng báo chính
   * - ``debug_ratio``
     - ``debug_total_us`` chia latency phiên ``perf_debug=False``
     - Độ phóng đại do chế độ debug. Nếu rất lệch 1 thì ``block_us`` không đọc như thời gian thật
   * - ``sum_ratio``
     - Tổng ``Time(us)`` mọi dòng chia ``Total Operator Elapsed Per Frame Time(us)``, tính riêng từng lần ``eval_perf``
     - Kiểm xem tổng từng lớp có khớp dòng tổng. Hãng không nêu quan hệ này. Ở phép thử hai lần gọi ngày 2026-10-30, tổng từng lớp bằng đúng dòng tổng (21361 và 21361, 21336 và 21336 µs) [T3 board]
   * - ``cycle_share_k``
     - Tỉ lệ ``MaxCycles`` (hoặc ``Total Cycles``) của khối k so với tổng
     - So với ``share_k`` để biết cycles ước tính dự đoán tốt đến đâu. Lệch với op không phải Conv vì ``NPUCycles`` chỉ có Conv
   * - ``us_per_gflop_k``
     - ``block_us`` chia GFLOPs của khối (cột GFLOPs ở bảng 23 lớp của trang kiến trúc)
     - Khối nào chạy kém hiệu quả so với khối lượng tính toán của nó. GFLOPs ở đó chỉ đếm Conv2d

5. Quy tắc gộp lớp RKNN về khối
===============================

5.1. Gộp về L0-L22
------------------

Cột ``FullName`` của bảng build có dạng ``<Op>:/model/model.<N>/...``, ví dụ ``Conv:/model/model.2/cv1/conv/Conv`` và ``Split:/model/model.4/Split`` [T3 PC, ``tmp/operator-support/c5_baseline/int8_build_stdout.txt``]. Quy tắc: khối ``N`` là số bắt gặp đầu tiên sau chuỗi ``model.`` bằng biểu thức ``model\.(\d+)``.

Kiểm trên bảng đo của export ppe5 ngày 2026-10-30 (119 dòng, ID board 1 đến 119, ID build 0 đến 118, chạy ``ai/core/rknn/blocks.py`` trên cột tên): 114 dòng có ``model.N``, trong đó khối 22 có 37 dòng, không có dòng nào rơi vào thành phần ``other``. Năm dòng còn lại không có chỉ số:

.. list-table::
   :header-rows: 1
   :widths: 14 26 22 38

   * - ID (board / build)
     - Dòng
     - ``Target``
     - Xử lý
   * - 1 / 0
     - ``InputOperator:images``
     - CPU
     - Nhóm ``io``, báo riêng
   * - 112 / 111
     - ``Mul:/Div_2mul``
     - NPU
     - Nhóm ``sau_detect`` (phần giải mã nằm ngoài tên ``model.22``), báo riêng và cộng thêm vào L22 ở một cột phụ
   * - 117 / 116
     - ``Concat:/Concat``
     - NPU
     - Nhóm ``sau_detect``
   * - 118 / 117
     - ``Reshape:output0-rs``
     - NPU
     - Nhóm ``sau_detect``
   * - 119 / 118
     - ``OutputOperator:output0``
     - CPU
     - Nhóm ``io``

Bảng đo trên board và bảng build của cùng ``.rknn`` có 119 dòng giống nhau về ``OpType`` và ``FullName`` theo đúng thứ tự, chỉ khác ID (board đếm từ 1, build đếm từ 0) [T3 board] [T3 PC]. Script gộp so hai bảng này ở mọi lần chạy (tiêu chí A1). Bảng build INT8 của model 5 class cũ trong ``tmp/operator-support/`` có cùng năm dòng ngoại lệ.

5.2. Gộp về thành phần trong khối
---------------------------------

Cùng cột ``FullName``, tách thêm theo đoạn sau ``model.<N>/``:

.. list-table::
   :header-rows: 1
   :widths: 22 38 40

   * - Khối
     - Đoạn tên
     - Thành phần
   * - C2f (L2, L4, L6, L8, L12, L15, L18, L21)
     - ``cv1``, ``Split``, ``m.<k>`` (Bottleneck thứ k, có ``Add`` khi shortcut), ``Concat``, ``cv2``
     - Conv vào, chia kênh, các Bottleneck, nối, Conv ra
   * - Conv đơn (L0, L1, L3, L5, L7, L16, L19)
     - ``conv``
     - Một Conv
   * - SPPF (L9)
     - ``cv1``, ``m``, ``m_1``, ``m_2`` (ba MaxPool), ``Concat``, ``cv2``
     - Conv vào, ba lần MaxPool, nối, Conv ra
   * - Upsample, Concat (L10, L11, L13, L14, L17, L20)
     - Tên op (``Resize`` và ``Concat``)
     - Phóng to, nối
   * - Detect (L22)
     - ``cv2.<i>`` (nhánh box), ``cv3.<i>`` (nhánh cls), ``dfl``, phần còn lại (``Sub``, ``Add``, ``Mul``, ``Sigmoid``, ``Concat``, ``Reshape``)
     - Nhánh box ba mức, nhánh cls ba mức, DFL, giải mã hộp

Ngoài hai cách gộp trên, báo thêm gộp theo ``OpType`` (``ConvExSwish``, ``Split``, ``Add``, ``Concat``, ``Resize``, ``Reshape``, ``Sigmoid``, ``exSoftmax13`` và các loại khác có mặt), lấy trực tiếp từ bảng xếp hạng của hãng [T1 UG232 tr.33].

6. Nguồn nhiễu và cách kiểm soát
================================

.. list-table::
   :header-rows: 1
   :widths: 22 40 38

   * - Nguồn nhiễu
     - Cách kiểm soát
     - Còn lại
   * - Tần số CPU, NPU, DDR
     - ``lock_freq.sh lock`` và ``fix_freq=True`` (mặc định). Đọc danh sách tần số trong đầu ra ``eval_perf`` ở mọi phiên [T1 UG232 tr.31]
     - Cách ``fix_freq`` thực hiện chỉ biết một phần (mục 9, U14). Đối chiếu tần số in ra với giá trị khoá (tiêu chí A2)
   * - Chế độ debug làm chậm
     - Latency chỉ lấy ở phiên ``perf_debug=False``. Từng lớp báo dạng tỉ lệ, kèm ``debug_ratio``
     - Đã đo: chế độ debug cộng một hằng số mỗi dòng, nên khối nhiều dòng nhỏ bị lệch nhiều hơn (:doc:`03-phan-tich-sau-latency-tung-khoi` mục 5, cột cận độ nhạy ở :doc:`02-ket-qua-latency-tung-khoi` mục 3.1)
   * - Truyền dữ liệu qua adb
     - ``eval_perf`` lấy thời gian từ phần cứng, không gồm truyền adb [T1 API232 tr.18]. ``inference`` thì chậm hơn do có truyền dữ liệu cố định [T1 UG232 tr.175]
     - Không dùng ``inference`` để đo từng lớp
   * - Khởi động lạnh, lần đầu
     - Lưu cả 5 giá trị mỗi phiên, so lần đầu với các lần sau
     - Hãng không nêu khuyến nghị warm-up trong tài liệu (ví dụ ``rknn_benchmark.cpp`` làm nóng 5 lần). Trên LAN, lần gọi đầu không thấp hơn một cách ổn định (:doc:`08-ket-qua-p2-va-do-mo-rong` mục 3)
   * - Nhiệt độ, tải nền trên board
     - Ghi nhiệt độ và ``uptime`` trước mỗi phiên, không chạy việc khác trên board
     - Chưa có ngưỡng nhiệt hay thời gian nghỉ từ nguồn nào. Ghi lại và quan sát
   * - Khác biệt giữa các lần ``init_runtime``
     - Ba phiên độc lập, báo độ trải median giữa các phiên
     - Không kiểm khởi động lại board giữa các phiên
   * - Phiên bản SDK
     - Cùng RKNN-Toolkit2 2.3.2 và ``rknn_server`` 2.3.2 cho cả build và đo
     - Ghi phiên bản vào mỗi file kết quả
   * - Mức log
     - Hãng ghi khi xem thời gian một khung nên đặt mức log 1 [T1 UG232 tr.137]. Build (B1) dùng ``RKNN_LOG_LEVEL=3`` để in bảng, đo (B2, B3) không đặt biến này
     - Đã đo ngày 2026-10-31 nhưng chưa kết luận vì một phiên tham chiếu không thực hiện đúng (:doc:`08-ket-qua-p2-va-do-mo-rong` mục 4)
   * - Đường truyền PC đến board chậm
     - ``eval_perf`` lấy thời gian từ phần cứng board. Đo thêm bằng C API ngay trên board (B7), không qua đường truyền
     - Hai giả thuyết (NPU tắt nguồn giữa các lần gọi, trạng thái ngủ của CPU) được kiểm ở :doc:`04-cac-muc-do-tre` và :doc:`05-thu-ghim-cpu-va-ngat`

7. Tiêu chí chấp nhận
=====================

Các ngưỡng bên dưới là tham số của dự án, chưa có nguồn ngoài, và đã được người phụ trách duyệt ngày 2026-10-30: 5% cho độ lệch giữa các phiên (mượn từ chuẩn G4 ở :doc:`../03-tang-npu-don-bay/01-operator-support`) và 10% cho độ lệch tỉ lệ khối. Không đổi ngưỡng để cổng đạt.

.. list-table::
   :header-rows: 1
   :widths: 8 50 42

   * - Mã
     - Điều kiện
     - Nếu không đạt
   * - A1
     - Bảng từng lớp trên board có cùng số dòng, ``OpType`` và ``FullName`` với bảng build của ``.rknn`` đó
     - Dừng. Quy tắc gộp chưa dùng được
   * - A2
     - Danh sách tần số in ra bằng giá trị khoá ở mọi phiên
     - Khoá lại tần số và đo lại
   * - A3
     - Mọi dòng ``Target=NPU`` có ``Time(us)`` lớn hơn 0 ở ``CORE_0`` có ``WorkLoad`` bằng ``100.0%/0.0%/0.0%``. Không tính dòng CPU và dòng ``Reshape`` (phép đổi hình, ba dòng 1 đến 3 µs ở B2 hiện ``0.0%/0.0%/0.0%``)
     - Ghi nguyên nhân. Khối nào chia nhân thì báo riêng
   * - A4
     - Mọi dòng được gán nhóm, chỉ ngoại lệ trong bảng mục 5.1 nằm ngoài ``model.N``
     - Bổ sung quy tắc gộp, ghi vào mục 5
   * - A5
     - Median latency giữa ba phiên chênh nhau không quá 5%
     - Thêm phiên cho đến khi đạt, hoặc báo độ trải thay cho một con số
   * - A6
     - Báo ``debug_ratio``, ``sum_ratio`` và tổng ``share_k`` bằng 100%
     - Không công bố bảng khối
   * - A7
     - File kết quả kèm sha256 của ``.rknn``, commit và trạng thái ``git_dirty``
     - Kết quả không truy ra được, đo lại
   * - A8
     - Tổng debug lệch giữa các phiên không quá 5%, và mọi khối chiếm từ 2% thời gian trở lên có tỉ lệ lệch giữa các phiên không quá 10%. Báo hai cách: chỉ các phiên đánh số, và tính cả phiên thử B2 như một phiên
     - Không công bố tỉ lệ khối như số ổn định. Báo kèm độ trải và ghi rõ khối nào nằm trong nhiễu

Quy tắc đọc kết quả: hai khối chỉ được xếp hạng khi chênh ``share`` lớn hơn độ trải giữa các phiên của chính chúng. Cổng nào không đạt thì ghi nguyên nhân quan sát được và không giải thích bằng suy đoán.

8. Kết quả sẽ báo
=================

Các bảng dưới đây là định dạng kết quả. Số liệu thực nằm ở :doc:`02-ket-qua-latency-tung-khoi`, sinh tự động từ ``results/*.json``.

.. list-table::
   :header-rows: 1
   :widths: 10 50 40

   * - Bảng
     - Cột
     - Dùng để
   * - 1
     - Khối L0-L22: ``block_us`` (median), ``share``, độ trải giữa phiên, ``Target``, ``cycle_share``, ``us_per_gflop``
     - Khối nào chiếm thời gian và có hiệu quả so với GFLOPs không
   * - 2
     - Thành phần trong khối (mục 5.2): ``block_us``, ``share`` trong khối và trên toàn mạng
     - Chỉ ra phần tốn thời gian bên trong C2f và Detect
   * - 3
     - Theo ``OpType``: ``CallNumber``, ``TotalTime(us)``, ``TimeRatio(%)``
     - Đối chiếu với bảng xếp hạng gốc của hãng
   * - 4
     - Đối chiếu tổng: latency ``perf_debug=False``, ``debug_total_us``, ``debug_ratio``, ``sum_ratio``, và thời gian ``npu`` ở tier 2 (``RKNNLite.inference``) của cùng ``.rknn``
     - Biết các số đo tổng khác nhau bao nhiêu và vì sao không cộng trực tiếp

Không rút ra từ trang này: latency end-to-end của hệ thống, kết luận về SiLU hay ReLU, kết luận đa nhân, kết luận độ chính xác.

9. Việc cần làm và điều chưa biết
=================================

Việc mã (đã làm, ngày 2026-10-30): ``measure_layers`` lặp 5 lần và lưu ``time_us_all``, tham số ``--session`` và ``--skip-memory`` cho ``benchmark_npu.py``, ``ai/core/rknn/blocks.py`` (gán lớp RKNN về khối), ``ai/automation/aggregate_layers.py`` (gộp, cổng A1 đến A8), ``ai/automation/analyze_layers.py`` (phân tích sâu), ``ai/automation/analyze_onboard.py`` (số đo trên board và E1), ``ai/board/rknn_perf_bench.c`` (C API trên board), ``tests/test_layer_blocks.py`` (chạy trên đầu ra thật của board).

Điều đã được đo trả lời (T3 board, ngày 2026-10-30):

- Tổng ``Time(us)`` từng lớp bằng đúng ``Total Operator Elapsed Per Frame Time(us)`` ở mọi lần gọi (``sum_ratio`` bằng 1.0 ở cả 15 lần gọi của B3).
- Nhãn phiên latency là ``Total Time(us)`` và ``FPS`` (xác nhận ở B2).
- Cột ``Total`` của ``Cycles(DDR/NPU/Total)`` bằng max của hai giá trị đầu ở cả 119 dòng.

Trạng thái các việc chưa biết (giai đoạn 1, cập nhật ngày 2026-10-31). Danh sách được lập bằng grep mọi câu "chưa biết" trong các trang của nhóm, theo dõi ở ``tmp/2026-10-31_latency-unknowns-tracker.md``. Mỗi việc có một trong ba nhãn: trả lời bằng đo (quy tắc viết trước khi đo, dữ liệu thô, phân tích), trả lời bằng nguồn (tài liệu hoặc mã của hãng), vẫn chưa biết (ghi rõ đã tìm và đã đo gì). Các quy tắc đo mới do người viết đặt và chưa qua người dùng duyệt, mỗi quy tắc nằm trong ``rule.txt`` của thí nghiệm.

.. list-table::
   :header-rows: 1
   :widths: 8 40 30 22

   * - Mã
     - Việc
     - Nhãn
     - Trang nhà
   * - U1a
     - Độ trễ của từng ngắt NPU
     - Trả lời bằng đo (X1)
     - :doc:`06-co-che-cac-muc-do-tre`
   * - U1b
     - Vì sao có mức chậm
     - Vẫn chưa biết (X2: tắt ``cpu-sleep`` ở CPU nhận ngắt làm mất phần tăng ở N, ở CPU ứng dụng thì chưa kết luận)
     - :doc:`06-co-che-cac-muc-do-tre`
   * - U2
     - Phần thời gian tăng nằm ở đâu, các mức sau can thiệp
     - Trả lời bằng đo (X1, X2)
     - :doc:`06-co-che-cac-muc-do-tre`
   * - U3
     - Tách cụm CPU khỏi xung nhịp
     - Vẫn chưa biết (X2, phép tách một chiều chưa kết luận)
     - :doc:`06-co-che-cac-muc-do-tre`
   * - U4
     - ``irqbalance`` đổi affinity ngắt NPU
     - Trả lời bằng đo (X9, quan sát 1 trên 3 lần)
     - :doc:`05-thu-ghim-cpu-va-ngat`
   * - U5
     - Đường ``eval_perf`` so với đường C API
     - Vẫn chưa biết (X3: chưa kết luận, 5 trên 6 ô có f trong ±0.25, ô còn lại 0.34)
     - :doc:`06-co-che-cac-muc-do-tre`
   * - U6
     - Lần gọi đầu và warm-up
     - Trả lời bằng đo (X4, không ổn định trên LAN) kèm nguồn (không có khuyến nghị trong tài liệu, ví dụ của hãng làm nóng 5 lần)
     - :doc:`04-cac-muc-do-tre`, :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U7
     - A5 không đạt do các phiên lấy mẫu ở các mức khác nhau
     - Trả lời bằng đo (X4)
     - :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U8
     - Thời gian mỗi lần gọi qua relay là thời gian đường truyền
     - Trả lời bằng đo (đo lại trên LAN)
     - :doc:`04-cac-muc-do-tre`
   * - U9
     - ``cpu-sleep`` và mức chậm
     - Vẫn chưa biết (X1 và X2 chỉ có bộ đếm mô tả, xem U1b)
     - :doc:`06-co-che-cac-muc-do-tre`
   * - U10
     - Hằng số mỗi dòng ở chế độ debug giữa các phiên
     - Trả lời bằng đo (X4, liên hệ với ghim lõi, nguyên nhân chưa biết)
     - :doc:`03-phan-tich-sau-latency-tung-khoi`, :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U11
     - Conv nhỏ lệch xa ước tính cycles
     - Vẫn chưa biết (X10, UG232 tr.147)
     - :doc:`03-phan-tich-sau-latency-tung-khoi`
   * - U12
     - Tỉ lệ thời gian so với tỉ lệ GFLOPs theo giai đoạn
     - Vẫn chưa biết (X10)
     - :doc:`03-phan-tich-sau-latency-tung-khoi`
   * - U13
     - Tổng debug thấp hơn latency
     - Trả lời bằng đo (X4: 4 trên 10 phiên không ghim, 0 trên 10 phiên ghim, một board)
     - :doc:`02-ket-qua-latency-tung-khoi`, :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U14
     - ``fix_freq`` làm gì
     - Trả lời bằng nguồn, một phần (bên dưới)
     - Trang này
   * - U15a
     - ``Total Cycles``
     - Trả lời bằng đo (bằng max của DDR và NPU ở 119 dòng, khớp định nghĩa ``MaxCycles``)
     - Trang này
   * - U15b
     - ``Task Number`` và ``Lut Number``
     - Vẫn chưa biết
     - Trang này
   * - U16
     - ``eval_perf`` ở ``CORE_0`` so với ``AUTO``
     - Trả lời bằng đo (X4)
     - :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U17
     - ``RW(KB)`` là đo hay tính
     - Vẫn chưa biết
     - Trang này
   * - U18
     - Chế độ debug làm lệch các lớp không đều
     - Trả lời bằng đo (hằng số mỗi dòng)
     - :doc:`03-phan-tich-sau-latency-tung-khoi`
   * - U19
     - Ảnh hưởng của mức log
     - Vẫn chưa biết (X4, một phiên tham chiếu không thực hiện đúng)
     - :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U20
     - Phụ thuộc giá trị đầu vào và trọng số
     - Trả lời bằng đo (X5)
     - :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U21
     - Chu kỳ lấy mẫu ``rknpu/load``
     - Trả lời bằng nguồn (mã driver, cửa sổ 1 giây)
     - :doc:`04-cac-muc-do-tre`
   * - U22
     - Latency ``CORE_0_1_2``
     - Trả lời bằng đo (X4)
     - :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U23
     - FP16
     - Trả lời bằng đo (X8, dưới giao thức P2)
     - :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U24
     - Độ chính xác sau INT8
     - Trả lời bằng đo (X7)
     - :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U25
     - A5 và A8 dưới giao thức ghim lõi P2
     - Trả lời bằng đo (X4)
     - :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U26
     - Đường ``eval_perf`` ở các ô CPU lớn
     - Trả lời bằng đo (X6, cùng kết quả vị trí ở bảy ô)
     - :doc:`05-thu-ghim-cpu-va-ngat`
   * - U28
     - Mức giảm mAP của INT8 đi theo lượng tử hóa hay theo đường suy luận RKNNLite
     - Trả lời bằng đo (X7b: FP16 qua RKNNLite gần FP32, nên đi theo lượng tử hóa. css_test 82 ảnh, một seed)
     - :doc:`08-ket-qua-p2-va-do-mo-rong`
   * - U27
     - Ảnh hưởng của tải CPU khác lên các mức
     - Vẫn chưa biết (không có thí nghiệm trong ngân sách của giai đoạn 1)
     - :doc:`06-co-che-cac-muc-do-tre`

Chi tiết các việc có trang nhà là trang này:

- U14, ``fix_freq``: hãng ghi "The fix_freq parameter indicates whether you need to try to fix the frequency of the hardware (including CPU/NPU/DDR)." [T1 UG232 tr.31] và "fix_freq: Whether to fix hardware frequency." [T1 API232 tr.18]. Thư viện Python của Toolkit2 (bản biên dịch, chỉ đọc được chuỗi) chứa ``echo userspace > {}`` và các nút ``/sys/class/devfreq/fdab0000.npu/userspace/set_freq``, ``/sys/class/devfreq/dmc/userspace/set_freq``. Điều này khớp quan sát governor của NPU và DDR đọc ra ``userspace`` sau các lần gọi ``eval_perf`` (:doc:`05-thu-ghim-cpu-va-ngat`, mục 6). Thứ tự và giá trị đặt không đọc được từ chuỗi, nên vẫn chưa biết đầy đủ.
- U15, ``Total Cycles``, ``Task Number``, ``Lut Number``: hãng định nghĩa ``MaxCycles`` là "Maximum values of DDR Cycles and NPU Cycles" [T1 UG232 tr.32], và cột ``Total`` đo được bằng max của hai cột đầu ở cả 119 dòng. ``Task Number`` chỉ có chú thích trong mã driver (``3rdparty/rknpu-driver-0.9.8/include/rknpu_ioctl.h:238``), không nguồn nào nói đó là cột in ra. ``Lut Number`` không có định nghĩa ở nguồn nào đã tìm.
- U17, ``RW(KB)``: hãng chỉ ghi "Total amount of data read and written (KB)" [T1 UG232 tr.32]. Driver có bộ đếm đọc ghi phần cứng (``rknpu_job.c:990-1020``) nhưng không nguồn nào nối nó với cột này.
- Nơi đã tìm cho U14, U15, U17 (và U6, U11, U12): mọi PDF trong ``3rdparty/rknn-toolkit2/doc/`` và ``docs/_assets/pdf/``, mã ``3rdparty/rknpu-driver-0.9.8``, ``3rdparty/rknn-toolkit2`` (header, ví dụ, README), chuỗi trong thư viện biên dịch của Toolkit2 và ``librknnrt.so``. Kết quả và từ khóa: ``tmp/2026-10-31_latency-sources-facts.md``. Từ khóa đề xuất để tìm bài báo: "RKNN eval_perf RW KB measured", "Rockchip NPU task number per layer".

Nguồn: [T1 UG232] ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, [T1 API232] ``docs/_assets/pdf/rknn/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf``, [T1 mã nguồn] ``3rdparty/rknpu-driver-0.9.8``, [T3] các thí nghiệm X1 đến X10 của giai đoạn 1, [T3 PC] bảng build INT8 trong ``tmp/operator-support/``. Mọi số trang là trang PDF.
