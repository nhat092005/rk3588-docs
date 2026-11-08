****************
NPU architecture
****************

.. admonition:: Trang này trả lời

   - Phần cứng NPU RK3588 đặt giới hạn gì lên FPS của YOLOv8n INT8, theo nguồn T1 và T2?
   - Số đo của dự án (một context, nhiều context) khớp với phần cứng và với danh sách op chia đa lõi của vendor ra sao?
   - Đòn bẩy nào từ kiến trúc đã đo, đòn bẩy nào chưa biết?

.. admonition:: Tóm tắt

   1. Phần cứng theo T1: ba lõi, 1024x3 MAC int8 và 512x3 MAC float16 mỗi chu kỳ, bộ đệm trong 384 KB mỗi lõi, bảng OPP của driver từ 300 đến 1000 MHz [T1 TRM1 tr.1984, T1 DRV ``dts/rk3588s.dtsi:3482-3640``].
   2. Hãng chỉ ghi tổng tới 6 TOPS, không ghi số mỗi lõi. Chia đều cho ba lõi là 2 TOPS (phép chia, không phải số của hãng). Hai bài báo viết khác nhau về 2 TOPS (bài EDGE một lõi, bài DAHD mỗi lõi). Trang này không suy TOPS từ số MAC.
   3. Vendor nói đa lõi hợp mạng lớn và ít lợi cho mạng nhỏ [T1 UG232 tr.72], bài EDGE đo lợi ích đa lõi nhỏ dưới 10% [T2 EDGE tr.2]. Số đo của dự án cùng chiều: một context ba lõi chỉ hơn một lõi 2.6% về FPS (56.1 so với 54.66) [T3 board, ``results/thr_p3.json``].
   4. Danh sách op chia đa lõi của vendor và số đo của dự án lệch nhau ở ``ConvExSwish`` (0 trên 57 dòng chia). ``ConvRelu`` chia 51 trên 51 [T3 board, :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 5].
   5. Nhiều context độc lập nâng thông lượng lên 102.0 FPS (hai context) và 141.18 FPS (ba context). Đây là đòn bẩy kiến trúc đã đo. Với mục tiêu 30 FPS (một camera) thì một context đã đạt (54.66 FPS), nên đòn bẩy này chỉ có giá trị khi có nhiều camera hoặc việc nặng khác dùng chung NPU (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8).
   6. Chưa biết: TOPS mỗi lõi theo số của hãng, xung NPU trong TRM (tần số đang khóa là 1000 MHz theo nhật ký đo), quy tắc chia một lớp qua các lõi, SRAM mỗi lõi ngoài 384 KB.

Kiến thức nền ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/02-vi-kien-truc-va-khoi-tinh-toan-core` và :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/03-che-do-da-loi-va-system-sram`. Kết quả FPS của các đòn bẩy sẽ ở :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Phạm vi và liên kết
======================

Sáu trang ở ``02-nen-tang-rk3588/01-phan-cung-npu/`` đã mô tả vị trí SoC, vi kiến trúc, đa lõi và System SRAM, DVFS, thanh ghi, đường truyền IOMMU và DDR. Khái niệm MAC, PE và systolic array ở :doc:`../../01-kien-thuc-nen/02-npu/01-kien-truc-npu-va-mac` và :doc:`../../01-kien-thuc-nen/02-npu/03-systolic-array-va-kien-truc-da-loi`. Trang này chỉ lấy những sự kiện phần cứng cần để quyết định đòn bẩy FPS và đặt số đo của dự án cạnh chúng. Trang :doc:`02-multi-core` đã phân tích chi tiết phần đa lõi, các mục 3 và 4 dưới đây chỉ trích số cần cho lập luận.

Mục tiêu FPS là 60 (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8). Người dùng chưa nói rõ đó là một luồng hay tổng nhiều luồng, thông lượng hay thời gian mỗi khung. Trang này ghi cả hai cách đọc khi cần.

2. Sự kiện phần cứng cần cho quyết định
=======================================

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Sự kiện
     - Nội dung
     - Thẻ
   * - Ba lõi
     - Chạy chung ba lõi, chung hai lõi hoặc độc lập
     - [T1 TRM1 tr.1984]
   * - MAC int8 mỗi chu kỳ
     - 1024x3
     - [T1 TRM1 tr.1984]
   * - MAC float16 mỗi chu kỳ
     - 512x3
     - [T1 TRM1 tr.1984]
   * - Bộ đệm trong
     - 384 KB mỗi lõi (384KBx3)
     - [T1 TRM1 tr.1984]
   * - Kiểu tính toán của TRM
     - integer 4, 8, 16, float 16, Bfloat 16, tf32
     - [T1 TRM1 tr.1984]
   * - Hiệu năng theo datasheet
     - Tới 6 TOPS
     - [T1 DS13 tr.9]
   * - Kiểu số theo datasheet
     - INT4, INT8, INT16, FP16 hỗn hợp, tới 6 TOPS
     - [T1 DS13 tr.6]

Nguyên văn các câu này ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/02-vi-kien-truc-va-khoi-tinh-toan-core` và :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/03-che-do-da-loi-va-system-sram`.

Thêm từ driver: cấu hình RK3588 đặt ``.core_mask = 0x7`` (ba lõi) [T1 DRV ``rknpu_drv.c:197``], chuỗi compatible ``rockchip,rk3588-rknpu`` [T1 DRV ``rknpu_drv.c:299``], số lõi dùng của một job lấy từ số bit trong ``core_mask`` [T1 DRV ``rknpu_job.c:143-145``]. Bảng OPP của NPU nằm ở ``dts/rk3588s.dtsi`` dòng 3482 (chú thích ``/* RK3588 npu OPPs */`` ở dòng 3533), từ ``opp-300000000`` (dòng 3534) đến ``opp-1000000000`` (dòng 3640) [T1 DRV ``dts/rk3588s.dtsi``]. Thanh ghi ``RKNN_cna_conv_con3`` có chế độ mảng MAC int8 32x32 và ghi chú dành cho chế độ đa lõi: "This register is target for multicore mode. By single core mode keep it at 3'd0." [T1 TRM1 tr.2001].

Con số TOPS theo từng nguồn:

.. list-table::
   :header-rows: 1
   :widths: 20 50 30

   * - Nguồn
     - Phát biểu
     - Thẻ
   * - Datasheet
     - Tới 6 TOPS cho NPU, ba lõi
     - [T1 DS13 tr.9]
   * - Bài EDGE
     - "RK3588 (2 TOPS, single-core"
     - [T2 EDGE tr.6]
   * - Bài DAHD
     - "the RK3588 integrates three NPU cores, each delivering a computational power of 2 TOPS"
     - [T2 DAHD tr.18]

Tài liệu của hãng chỉ ghi số tổng. Hai bài báo không khớp nhau về việc 2 TOPS là của một lõi hay mỗi lõi, và phép chia 6 cho 3 khớp với cách viết của DAHD. Dự án không suy giá trị TOPS từ số MAC (cần xung, và xung của NPU trong TRM chưa tìm thấy, mục 6). Với quyết định của dự án, TOPS không cần: giới hạn FPS được đọc từ số đo (mục 4), không tính từ TOPS.

Bài EDGE mô tả cấu trúc: "the NPU consists of the Convolution Neural Accelerator (CNA), Data Processing Unit (DPU), and Pooling Processing Unit (PPU), supported by a shared MAC array." [T2 EDGE tr.3].

3. Chia việc đa lõi: vendor so với số đo
========================================

Vendor liệt kê op được driver chia đa lõi (Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, LeakyRelu) và nói op ngoài danh sách chưa được chia, sẽ hỗ trợ ở bản sau [T1 UG232 tr.75]. Vendor nói đa lõi hợp mạng có lượng tính toán lớn, cải thiện ít với mạng nhỏ và có thể giảm hiệu năng vì chuyển giữa đơn lõi và đa lõi [T1 UG232 tr.72], và khuyên đặt tần số CPU, DDR, NPU cao nhất [T1 UG232 tr.75]. Nguyên văn ở :doc:`../../02-nen-tang-rk3588/01-phan-cung-npu/03-che-do-da-loi-va-system-sram` và :doc:`02-multi-core`.

Số đo của dự án ở ``CORE_0_1_2`` theo cột ``WorkLoad`` của bảng layer (mẫu quan sát, một phiên mỗi model, không phải quy tắc) [T3 board, :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 5]:

.. list-table::
   :header-rows: 1
   :widths: 18 20 62

   * - Op
     - Dòng chia
     - So với danh sách vendor
   * - ``ConvExSwish`` (SiLU)
     - 0 trên 57
     - Tên op không có trong danh sách. ``Conv`` có trong danh sách nhưng dòng ``ConvExSwish`` không chia
   * - ``ConvRelu`` (ReLU)
     - 51 trên 51
     - Phù hợp với việc ``Conv`` và ``Relu`` có trong danh sách
   * - ``Concat``
     - 15 trên 17
     - Có trong danh sách, chia 15 dòng
   * - ``Add``
     - 8 trên 8 (SiLU), 2 trên 2 (ReLU)
     - Có trong danh sách, chia hết
   * - ``Split``, ``MaxPool``, ``Resize``, ``Reshape``
     - không chia
     - Không có trong danh sách

Mặt nạ lõi: ``NPU_CORE_ALL`` chia 29 dòng, đúng tập dòng của ``CORE_0_1_2``, còn ``AUTO`` chia 0 dòng (một phiên, chỉ mô tả) [T3 board, :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 6]. Quy tắc chia một lớp qua các lõi của ``librknnrt``: chưa biết (driver chỉ cho số task mỗi lõi từ ``subcore_task[]`` [T1 DRV ``rknpu_job.c:82-86``], guide chỉ cho phần trăm ``WorkLoad``).

Bài EDGE cùng chiều với phần "mạng nhỏ": lợi ích lập lịch đa lõi nhìn chung dưới 10% [T2 EDGE tr.2], với YOLOv5n chênh giữa một lõi và đa lõi dưới 5% (21.5 so với 20.5 ms) [T2 EDGE tr.6], và với đa số model cấu hình ba lõi cho cải thiện nhỏ hoặc âm [T2 EDGE tr.10] (nguyên văn ở :doc:`02-multi-core`). Đây là số của bài, trên board và bộ model của bài, không so trực tiếp với số của dự án.

4. Số đo của dự án nhìn từ phần cứng
====================================

Giao thức P3 (đã duyệt ngày 2026-11-01, :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`), model INT8 mặc định seed 0 [T3 board, ``results/thr_p3.json``, ``configs.T1`` đến ``T6``]:

.. list-table::
   :header-rows: 1
   :widths: 50 20 30

   * - Cấu hình
     - FPS
     - Ghi chú
   * - 1 context ``CORE_0`` (T1)
     - 54.66
     - ``t_npu`` 17.161 ms, ``t_pre`` 0.216, ``t_post`` 0.662
   * - 1 context ``CORE_0_1`` (T2)
     - 55.76
     -
   * - 1 context ``CORE_0_1_2`` (T3)
     - 56.1
     -
   * - 2 context ``CORE_0`` và ``CORE_1`` (T4)
     - 102.0
     -
   * - 3 context (S2, T5)
     - 141.18
     - ``t_npu`` 19.526 ms
   * - S3 pipeline (T6)
     - 147.39
     -

Mục tiêu 30 FPS: mọi cấu hình đạt theo thông lượng (từ 54.66 FPS). Đọc theo thời gian mỗi khung (33.33 ms), ``t_npu`` một context 17.161 ms nằm trong ngân sách (:doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan` mục 8). Mốc 60 FPS cũ làm ba cấu hình một context chưa đạt, và theo thời gian mỗi khung (16.67 ms) không cấu hình nào đạt.

Về độ lợi của đa lõi trong một context: latency của ``int8h5`` SiLU ở ``CORE_0_1_2`` nhanh hơn ``CORE_0`` 2.9% (điều kiện B, phiên P2, :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa` mục 6) và về FPS là 54.66 sang 56.1. Hai số nhỏ, cùng bậc với phát biểu của vendor về mạng nhỏ và của bài EDGE. Dự án chưa có phép đo tách nguyên nhân (ví dụ chi phí đồng bộ lõi), nên "vì sao nhỏ" là chưa biết. Với ReLU, ``CORE_0_1_2`` nhanh hơn ``CORE_0`` 33.7% ở ``int8h5`` (cùng mục), vì ``ConvRelu`` chia hết.

5. Đòn bẩy từ kiến trúc
=======================

Nhãn: ĐO (có số T3), NGUỒN (chỉ tài liệu), CHƯA BIẾT.

.. list-table::
   :header-rows: 1
   :widths: 8 26 12 54

   * - Mã
     - Đòn bẩy
     - Nhãn
     - Bằng chứng và giới hạn
   * - A1
     - Nhiều context độc lập, mỗi context một lõi hoặc hơn
     - ĐO
     - 102.0 FPS (hai context), 141.18 FPS (ba context, S2) so với 54.66 FPS một context [T3 board, ``results/thr_p3.json``]. Một seed, ảnh cache, chưa đo camera thật. Dùng chung một context giữa các luồng cho đầu ra sai (:doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 7). Bộ nhớ mỗi context: :doc:`06-memory-copy`
   * - A2
     - Đổi activation để chia lõi (ReLU thay SiLU)
     - ĐO, ReLU bị loại
     - ``ConvRelu`` chia 51 trên 51. Cổng C của ReLU không đạt dưới ``int8h5``, khoảng cách đã có ở FP16 (:doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa` mục 5, :doc:`../04-tang-npu-ket-qua/01-ket-qua-g4`, :doc:`../04-tang-npu-ket-qua/02-ket-qua-bien-the-activation`)
   * - A3
     - Tần số NPU
     - ĐO (một tần số)
     - Tần số khóa theo P2 và P3 (:doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`): ``npu: userspace 1000000000 Hz``, tức 1000 MHz, ghi trong nhật ký helper của các thí nghiệm [T3 board, ``results/q2f_fps.json`` trường ``hold_progress`` của E1 và ``results/q2j_split.json``]. Bảng OPP của driver cho 300 đến 1000 MHz. Vendor khuyên đặt tần số cao nhất [T1 UG232 tr.75]. Chưa có phép đo biến thiên tần số

Kết quả FPS của các đòn bẩy này ở :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.

6. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 36 14 50

   * - Việc
     - Trạng thái
     - Đã tìm gì
   * - Giá trị TOPS của một lõi
     - hãng không ghi
     - Datasheet chỉ ghi tổng 6 TOPS. EDGE và DAHD viết khác nhau. Không suy từ số MAC
   * - Xung NPU trong TRM
     - chưa biết
     - Đã tìm ``clk_npu_root``, ``clk_npu_dsu``, ``clk_npu_cm0`` và ``npu.*(MHz|GHz)``, chỉ thấy tên mux và gating. Khoảng tần số duy nhất là bảng OPP của driver
   * - Quy tắc chia một lớp qua các lõi
     - chưa biết
     - Driver chỉ cho số task, guide RKNN chỉ cho phần trăm ``WorkLoad``
   * - PE, MAC, SRAM mỗi lõi ngoài 384 KB
     - chưa biết
     - Chỉ có thông lượng MAC và bộ đệm của TRM. Datasheet nhắc "MCU in VD_NPU integrate 16KB Cache and 64KB TCM" (nói về MCU, không phải mảng MAC)
   * - Bảng dtype theo op cho Sigmoid, Softmax, Resize
     - chưa biết
     - Chỉ có danh sách DPU và PPU của TRM và danh sách dtype của datasheet. ``03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf`` chưa tìm sâu
   * - Vì sao ``ConvExSwish`` không chia
     - chưa biết
     - Chỉ có số đếm dòng. Tên op không có trong danh sách vendor
   * - Lợi ích SRAM mỗi lõi
     - chưa biết
     - Zero-copy và SRAM trong ``ai/`` không thấy (đã tìm ``zero_copy``, ``set_io_mem``, ``create_mem``)

7. Nguồn
========

- T1: ``rk3588_part1.pdf`` (TRM1 tr.1984, 2001), ``Rockchip_RK3588_Datasheet_V1.3_20220328.pdf`` (DS13 tr.6, 9), SDK User Guide V2.3.2 (UG232 tr.72, 75), driver ``3rdparty/rknpu-driver-0.9.8/`` (``rknpu_drv.c:197, 299``, ``rknpu_job.c:82-86, 143-145``, ``dts/rk3588s.dtsi:3482-3640``).
- T2: ``docs/_assets/pdf/papers/05_rk3588/edgesoc_benchmark_2026kong.pdf`` (EDGE tr.2, 3, 6, 10), ``dahd_yolo_rk3588_2025.pdf`` (DAHD tr.18).
- T3: ``results/thr_p3.json``, bảng ``WorkLoad`` ở :doc:`../04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 5 và 6, :doc:`../04-tang-npu-ket-qua/05-ket-qua-luong-tu-hoa` mục 6.
- Trang liên quan: :doc:`02-multi-core`, :doc:`06-memory-copy`, :doc:`../04-tang-npu-ket-qua/03-ket-qua-da-nhan`, :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`, :doc:`../04-tang-npu-ket-qua/09-ket-qua-don-bay-fps`.
