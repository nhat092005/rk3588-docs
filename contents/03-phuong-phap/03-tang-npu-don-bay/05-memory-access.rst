*************
Memory access
*************

.. admonition:: Trang này trả lời

   - Bộ nhớ mà model YOLOv8n INT8 dùng là bao nhiêu theo bản build và theo runtime, và mỗi khung đọc ghi bao nhiêu DDR theo bảng layer?
   - Dữ liệu của dự án có cho thấy truy cập bộ nhớ là nút cổ chai FPS không, và điều gì chưa đo được?
   - Đòn bẩy nào liên quan đến truy cập bộ nhớ (SRAM, tần số DDR, giảm lưu lượng qua fusion), đòn bẩy nào đã đo, đòn bẩy nào chỉ có nguồn?

.. admonition:: Tóm tắt

   1. Bộ nhớ model INT8 mặc định lúc chạy (``eval_perf``, ``CORE_0``): trọng số 3.294 MiB, tensor trong 6.256 MiB, tổng 10.723 MiB. ``h5`` thêm tensor trong lên 8.691 MiB và tổng 13.152 MiB [T3 board, ``bench/tier1_int8_CORE_0.json``, ``bench/tier1_int8h5_CORE_0.json``].
   2. Một khung của model INT8 mặc định đọc ghi 39007.22 KB DDR, và 41443.39 KB ở ``h5`` ``CORE_0_1_2`` [T3 board, bảng layer ``eval_perf``].
   3. Trong bảng layer, tổng cycles DDR là 1611857 và tổng cycles NPU là 5665600 trên 116 hàng NPU. Chỉ một hàng (layer 21) có cycles DDR lớn hơn cycles NPU. Con số này tính từ file bảng layer, không đo thêm [T3 board, tính từ ``bench/tier1_int8_CORE_0_layers.txt``].
   4. Cột cycles do công cụ của vendor ghi. Nó là đo hay ước lượng của compiler: chưa biết. Dữ liệu này gợi ý chứ không chứng minh model nghiêng về tính toán.
   5. Đòn bẩy: M1 SRAM (NGUỒN, repo không dùng, chưa đo), M2 tần số DDR (đã khóa 2112 MHz, mức cao nhất của bảng tần số chưa trích), M3 giảm lưu lượng qua fusion (liên kết :doc:`07-compiler-optimization`).
   6. Băng thông DDR đỉnh đo trên board, và lợi ích SRAM cho model này: chưa biết.

Kiến thức nền ở :doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/01-ddr-tren-rk3588` và :doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/02-sram-cho-npu`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Phạm vi và liên kết
======================

Trang này không lặp lại loại DRAM, số kênh và băng thông suy ra của bộ điều khiển (:doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/01-ddr-tren-rk3588`), cách bật và kiểm tra SRAM, các điều kiện kernel, driver và trình tự quyết định (:doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/02-sram-cho-npu`), hay đường dữ liệu IOMMU và DDR (:doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/06-duong-truyen-du-lieu-iommu-va-ddr`). Lý thuyết về phân cấp bộ nhớ và roofline ở :doc:`../../01-kien-thuc-nen/02-npu/02-dataflow-va-phan-cap-bo-nho`, cách nhận biết nghẽn băng thông ở :doc:`../../01-kien-thuc-nen/05-bo-nho-hieu-nang/01-do-do-tre-va-profiling`. Tiền xử lý và hậu xử lý nằm ngoài NPU nên không thuộc trang này (:doc:`09-pre-post-processing`), cách sao chép giữa CPU và NPU ở :doc:`06-memory-copy`.

Trang chỉ ghi điều dự án cần: bộ nhớ và lưu lượng của model đang dùng, điều kiện đo, và các đòn bẩy. Mục tiêu 60 FPS của người dùng (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8) chưa được xác nhận cách hiểu (một luồng hay tổng nhiều luồng, thông lượng hay thời gian mỗi khung), nên trang này không nói đòn bẩy nào đủ để đạt 60.

Lưu ý về tên cột: tài liệu vendor định nghĩa ``DDRCycles`` là "DDR reading and writing clock cycles" và ``RW(KB)`` là "Total amount of data read and written (KB)" [T1 UG232 tr.32]. Vendor không có câu nào dùng chữ memory-bound hay compute-bound trong sổ tay SDK, tài liệu API Toolkit2 và tài liệu RKNNRT (đã tìm cả ba).

2. Bộ nhớ của model
===================

Vendor chia bộ nhớ runtime của model thành bốn phần: "The RKNN model runtime memory mainly consists of four parts: weights and internal tensors, register configurations, input tensors and output tensors." [T1 UG232 tr.148]. ``RKNN_QUERY_MEM_SIZE`` báo trọng số, tensor trong, DMA và SRAM, trong đó SRAM là 0 nếu không bật: "(0 if SRAM is not turned on or does not have this function)" [T1 UG232 tr.148]. Dự án có hai nguồn số: bảng build của toolkit và JSON của ``eval_perf`` lúc chạy.

2.1 Theo bản build
------------------

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Model
     - Total Internal Memory (KB)
     - Total Weight Memory (KB)
   * - base (INT8 mặc định)
     - 6406.25
     - 3504.69
   * - ``h5``
     - 8900.06
     - 3767.5
   * - split INT8 (A1)
     - 4400
     - 2979.75
   * - split FP16
     - 16800
     - 5887.62

Nguồn: [T3 board, ``bench/onboard_q2c/logs/build_..._base.log:752-753``, ``_h5.log:785-786``, ``_split_int8.log:658-659``, ``_split_fp16.log:638-639``] với thư mục ``bench`` là ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/``. Hai bản ``c_all`` và ``h6`` cũng có dòng này (``_c_all.log:951-952``, ``_h6.log:821-822``), không đưa vào bảng.

2.2 Theo runtime
----------------

.. list-table::
   :header-rows: 1
   :widths: 24 19 19 19 19

   * - Model (CORE_0)
     - Trọng số (MiB)
     - Tensor trong (MiB)
     - Khác (MiB)
     - Tổng (MiB)
   * - INT8 mặc định
     - 3.294
     - 6.256
     - 1.172
     - 10.723
   * - ``h5``
     - 3.294
     - 8.691
     - chưa trích
     - 13.152

Nguồn: [T3 board, ``bench/tier1_int8_CORE_0.json`` và ``bench/tier1_int8h5_CORE_0.json``, trường ``npu_memory_mib``]. Hai bảng khớp ở tensor trong của model INT8 mặc định (6406.25 KB tương ứng 6.256 MiB). Trọng số khác nhau: bảng build ghi 3504.69 KB còn runtime ghi 3.294 MiB. Nguyên nhân chênh: chưa biết, đã tìm trong hai nguồn trên và không có ghi chú giải thích.

``h5`` làm tensor trong tăng từ 6.256 lên 8.691 MiB (build: 6406.25 lên 8900.06 KB) và không đổi trọng số theo runtime. Bản tách đầu A1 có tensor trong nhỏ nhất (4400 KB), bản FP16 lớn nhất (16800 KB). Chưa có phép đo FPS nào cho thấy mức dùng bộ nhớ này ảnh hưởng thời gian.

3. Lưu lượng DDR so với tính toán
=================================

Bảng layer ghi mỗi toán tử có ba giá trị ở cột ``Cycles(DDR/NPU/Total)``. Ví dụ ConvExSwish layer 1 của build ``h5``: ``121323/921600/921600`` và ``RW(KB)`` là 1202 [T3 board, ``build_..._h5.log:323``]. Ở layer 21 (``Conv:/model/model.4/cv2/conv/Conv``) là ``52317/51200/52317`` và ``RW(KB)`` là 271 [T3 board, ``bench/tier1_int8_CORE_0_layers.txt:35``]. Ở cả hai hàng này giá trị Total bằng giá trị lớn hơn trong hai giá trị DDR và NPU. Với chỉ hai hàng, đây là quan sát chứ không phải quy tắc của vendor.

Tổng trên một khung:

.. list-table::
   :header-rows: 1
   :widths: 40 20 20 20

   * - Model và mask
     - Thời gian toán tử (us)
     - Đọc ghi (KB)
     - Nguồn
   * - INT8 mặc định ``CORE_0``
     - 18598
     - 39007.22
     - ``bench/tier1_int8_CORE_0_layers.txt:135-136``
   * - INT8 mặc định ``CORE_0_1_2``
     - 16073
     - 39007.22
     - ``bench/onboard_q2j/tier1_int8_CORE_0_1_2_sess1_layers.txt``
   * - ``h5`` ``CORE_0_1_2``
     - 15967
     - 41443.39
     - ``bench/onboard_q2j/tier1_int8h5_CORE_0_1_2_sess1_layers.txt``

Tất cả là [T3 board] với ``bench`` như ở mục 2.1. Cột thời gian toán tử là tổng thời gian của các toán tử, không so trực tiếp với thời gian NPU ở :doc:`04-datatype`.

Tính từ ``tier1_int8_CORE_0_layers.txt`` (script, không đo thêm): 116 hàng NPU, tổng cycles NPU là 5665600 và tổng cycles DDR là 1611857 [T3 board, tính]. Trong 116 hàng chỉ layer 21 có cycles DDR (52317) lớn hơn cycles NPU (51200) [T3 board, ``bench/tier1_int8_CORE_0_layers.txt:35``].

Cách đọc đúng giới hạn. Quan sát này cho thấy theo cột cycles của công cụ, hầu hết các hàng có cycles NPU lớn hơn cycles DDR. Vendor có hướng dẫn so hai cột này để biết lớp Conv nghẽn băng thông hay tính toán (xem :doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/03-zero-copy-can-le-profiling-api` mục 3.4). Nhưng cột cycles là kết quả đo hay ước lượng của compiler thì chưa xác định (ghi cả ở ``docs/contents/09-tien-do/03-khoang-trong/04-bo-nho-hieu-nang.rst``), nên kết luận mạnh hơn mô tả là chưa đủ cơ sở. Vì vậy trang này chỉ viết: theo ước lượng của công cụ, đa số hàng nghiêng về tính toán. Đây là mô tả, không phải kết luận về nút cổ chai của FPS.

4. Điều kiện đo và tham chiếu từ bài báo
========================================

Tần số khi chạy: DDR ``2112000000`` Hz trong bảng layer của ``eval_perf`` [T3 board, ``bench/tier1_int8_CORE_0_layers.txt:7-8``]. Sổ tay SDK có ví dụ cùng giá trị ở mục liệt kê "DDR Current Frequency List" [T1 UG232 tr.31]. Trong các phép đo P2 và P3, NPU khóa ở ``npu: userspace 1000000000 Hz`` và DDR ở ``ddr: userspace 2112000000 Hz`` [T3 board, ``results/q2j_split.json`` trường ``hold_progress`` cho P2 và ``results/q2f_fps.json`` trường ``hold_progress`` của E1 cho P3]. Các số ở trang này vì vậy là số khi DDR khóa tần số, không đại diện cho DVFS tự động.

Các bài báo đã có trong kho chỉ để định vị, không thay số đo của dự án:

- Bài EdgeSoC báo băng thông bộ nhớ duy trì của một bo mạch RK3588 16 GB LPDDR4X là 8807 MiB/s trong bảng SoC [T2 EDGE tr.3]. Đây là số của bài, không phải thông số vendor.
- Cũng bài đó: nghẽn băng thông làm chậm RV1106 và RK3568 từ 50 đến 270%, còn "while RK3588 remains largely unaffected due to its higher sustained bandwidth" [T2 EDGE tr.2].
- Ở ngữ cảnh khác (TPU của Google, không phải RK3588): "Four of the six NN apps are memory-bandwidth limited on the TPU" [T2 Jouppi 2017 tr.2].

Hai điểm này không thay thế phép đo băng thông DDR đỉnh trên board. Datasheet và TRM trong kho (RK3588 V1.3, RK3588S V1.7, ``rk3588_part1.pdf`` và ``part2.pdf``) đã được tìm: không nêu băng thông DRAM đỉnh theo GB/s (trang :doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/01-ddr-tren-rk3588` nêu phép suy ra). Băng thông DDR đo trên board bằng GB/s không có trong repo.

5. Đòn bẩy
==========

Nhãn trạng thái: ĐO (có số đo T3), NGUỒN (chỉ có tài liệu hoặc mã), CHƯA BIẾT. Ngưỡng số mới của từng thí nghiệm vẫn chưa duyệt.

.. list-table::
   :header-rows: 1
   :widths: 8 24 12 56

   * - Mã
     - Đòn bẩy
     - Nhãn
     - Bằng chứng và giới hạn
   * - M1
     - Bật SRAM cho tensor trong bằng cờ ``RKNN_FLAG_ENABLE_SRAM``
     - NGUỒN
     - Vendor: SRAM giảm áp lực băng thông DDR nhưng có thể ảnh hưởng thời gian suy luận [T1 UG232 tr.106]. Cờ ở ``rknn_init`` (UG232 tr.107). Repo không dùng cờ này, không có dòng ``Total allocated Internal SRAM`` trong log nào của ``runs/`` [T3 board, grep ``ai`` và ``results``]. Chưa đo. Điều kiện, trình tự đo và các mâu thuẫn của nguồn: :doc:`../../02-nen-tang-rk3588/04-bo-nho-hieu-nang/02-sram-cho-npu`. Đường biến môi trường chưa thử. Có thể dùng trong RKNNLite hay không: chưa kiểm
   * - M2
     - Tăng tần số DDR
     - NGUỒN và ghi nhận tần số khóa (không có phép so tần số)
     - DDR đã khóa 2112 MHz trong P2 và P3 (mục 4). Chưa so với tần số thấp hơn, nên không có số cho độ nhạy của FPS với tần số DDR. Mức cao nhất của bảng tần số trên board: chưa trích ở trang này
   * - M3
     - Giảm lưu lượng nhờ fusion, giữ tensor trung gian trên chip
     - NGUỒN
     - Bài Lee 2024 mô tả fused layer không lưu kết quả trung gian ra bộ nhớ ngoài chip [T2 Lee 2024 tr.1]. Vendor nói cấu trúc đọc ghi thân thiện thì hiệu suất băng thông DDR cao hơn [T1 UG232 tr.144]. Dự án chưa có số FPS riêng cho từng fusion (:doc:`07-compiler-optimization`)
   * - M4
     - Giảm lưu lượng qua tách đầu (A1) và kiểu số
     - ĐO gộp
     - Tensor trong của A1 là 4400 KB so với 6406.25 KB ở base (mục 2.1). Hiệu ứng lên FPS gộp với bỏ Transpose và đuôi giải mã (:doc:`04-datatype`, :doc:`../04-tang-npu-ket-qua/07-ket-qua-qat-kien-truc`)

Bốn đòn bẩy này không đòn bẩy nào có số đo riêng về lợi ích FPS. Với giả thuyết đa số hàng nghiêng về tính toán (mục 3), đòn bẩy bộ nhớ ít có chỗ tác động lớn ở một context, nhưng đây là suy luận từ cột cycles của công cụ (đo hay ước lượng chưa biết), không phải số đo. Tranh chấp DDR giữa các context chưa được đo riêng.

6. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 38 14 48

   * - Mục
     - Trạng thái
     - Đã tìm gì
   * - Băng thông DRAM đỉnh của RK3588S và cấu hình DRAM thực của board
     - chưa biết
     - Datasheet V1.3, V1.7, ``rk3588_part1.pdf``, ``part2.pdf``. Mục NPU_M0 của TRM có trong mục lục nhưng không có nội dung trong text trích
   * - Băng thông DDR đo trên board (GB/s) khi chạy model
     - chưa biết
     - Không có trong repo
   * - Cycles ``DDRCycles`` và ``NPU Cycles`` là đo hay ước lượng
     - chưa biết
     - Định nghĩa vendor chỉ nói là chu kỳ đọc ghi DDR [T1 UG232 tr.32]
   * - Lợi ích và rủi ro thời gian của SRAM cho YOLOv8n
     - chưa biết
     - Repo không bật SRAM, không có log ``Predict SRAM Hit RW Amount``
   * - Chênh trọng số giữa bảng build (3504.69 KB) và runtime (3.294 MiB)
     - chưa biết
     - Hai nguồn ở mục 2, không có ghi chú giải thích
   * - Độ nhạy FPS với tần số DDR
     - chưa biết
     - Chỉ có đo ở một tần số khóa
   * - Cách hiểu 60 FPS
     - chưa xác nhận
     - :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8

7. Nguồn
========

- T1: SDK User Guide V2.3.2 (``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``, UG232 tr.31, 32, 106, 107, 144, 148).
- T2: ``docs/_assets/pdf/papers/05_rk3588/edgesoc_benchmark_2026kong.pdf`` (EDGE tr.2, 3), ``tpu_datacenter_2017jouppi.pdf`` (Jouppi 2017 tr.2), ``fused_layer_multiworkload_2024lee.pdf`` (Lee 2024 tr.1).
- T3: ``bench/tier1_int8_CORE_0.json``, ``bench/tier1_int8h5_CORE_0.json``, ``bench/tier1_int8_CORE_0_layers.txt``, ``bench/onboard_q2j/``, ``bench/onboard_q2c/logs/``, ``results/q2j_split.json`` (``bench`` là ``ai/automation/runs/ppe5_yolov8n_baseline_100ep_s0/bench/``).
- Trang liên quan: :doc:`03-tensor-layout`, :doc:`04-datatype`, :doc:`06-memory-copy`, :doc:`07-compiler-optimization`, :doc:`08-npu-architecture`, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`, :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet`, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.
