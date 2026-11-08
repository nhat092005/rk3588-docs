:tocdepth: 1

*****
NPU
*****

.. admonition:: Trang này trả lời

   - Từ ứng dụng đến NPU có những lớp phần mềm nào?
   - Một lõi NPU gồm những khối nào, dữ liệu đi qua thế nào?
   - Ba lõi chạy riêng hay cùng nhau, và chia việc ra sao?
   - YOLOv8n đi qua NPU lớp theo lớp thế nào, các đường skip ở đâu?

.. admonition:: Tóm tắt

   1. Một lõi gồm CNA (nạp weight và feature, giải nén, zero-skipping, buffer 384KB), mảng MAC với accumulator, DPU, PPU và sequence controller [T1 TRM1 tr.1985].
   2. Mỗi lõi làm 1024 MAC INT8 mỗi chu kỳ [T1 TRM1 tr.1984]. DPU cộng bias, nhân scale và làm activation. PPU làm pooling, có thể nối ống sau DPU [T1 TRM1 tr.2020, tr.2054, tr.2055].
   3. Ba lõi chạy độc lập hoặc cùng làm. Ở chế độ cùng làm, chỉ Conv, DepthwiseConv, Add, Concat, Relu và vài activation được chia theo khối lượng tính, op khác chạy trên Core 0. Chiều chia (H, W hay kênh) không được công bố [T1 TRM1 tr.1984] [T1 UG152 tr.27] [T1 UG232 tr.75] [T1 DRV ``include/rknpu_ioctl.h:241-279``].
   4. Đo của dự án: ba context độc lập đạt 141 FPS, còn một context chạy ba lõi chỉ hơn một lõi 2.6% [T3 board, ``results/thr_p3.json``].
   5. YOLOv8n có bốn đường skip dài và các Concat, Add trong khối C2f. Concat, Split, Add, MaxPool nằm trong danh sách op NPU. Tensor skip (a) là 400 KB INT8, lớn hơn buffer 384 KB nên không giữ trong buffer được [SL]. Các op Concat, Split, Add đều đọc ghi bộ nhớ (RW KB khác 0), tổng 4111 us, 17.8% thời gian một khung [T3 board, ``results/layer_analysis_ppe5_yolov8n_baseline_100ep_s0_int8_CORE_0.md``].
   6. Driver là rknpu 0.9.8, xung 300 đến 1000 MHz, IOMMU bật [T3 board, ``dmesg``, ``/sys/class/devfreq/fdab0000.npu``]. GPU đọc ``0@300000000Hz`` ở cả 29 mẫu trong 220 vòng suy luận [T3 board, ``/sys/class/devfreq/fb000000.gpu/load``].

.. contents:: Trong trang này
   :local:
   :depth: 1

1. Đường phần mềm xuống NPU
===========================

.. code:: text

    ứng dụng Python (RKNNLite) hoặc C (librknnrt)
       |   rknn_inputs_set, rknn_run, rknn_outputs_get
       v
    driver rknpu 0.9.8, DRM minor 1, hàng đợi riêng cho từng lõi
       |   danh sách task (subcore_task) cho từng lõi
       v
    NPU: 3 lõi, IOMMU bật, xung 300 đến 1000 MHz (rknpu_ondemand), đang 1000 MHz

Nguồn: [T3 board, ``dmesg``: ``Initialized rknpu 0.9.8 20240828 for fdab0000.npu on minor 1``, ``rknpu iommu is enabled``] [T3 board, ``/sys/class/devfreq/fdab0000.npu``]. Driver có hàng đợi riêng cho từng lõi, mỗi lõi chạy một job tại một thời điểm [T1 DRV ``rknpu_job.c:431-455``, ``rknpu_job.c:545-553``]. Dmesg có ba thông báo ``can't request region`` cho các vùng ``fdab0000``, ``fdac0000``, ``fdad0000``, ba địa chỉ khớp ba lõi [SL] [T3 board, ``dmesg``]. Ảnh hưởng của các dòng lỗi này: unknown.

2. Bên trong một lõi
====================

.. code:: text

                             DDR (NPU là AXI master, IOMMU bật)
                  | weight, feature                                        kết quả  |
                  v                                                                 ^
   +------------------------------------------------------------------------------------------+
   |  1 lõi NPU (RK3588 có 3 lõi giống nhau)                                                  |
   |  Sequence Controller, danh sách lệnh nạp qua Register File Fetch                         |
   |                                                                                          |
   |  +------------------------+                                                              |
   |  | CNA                    |    +----------------+                                        |
   |  | Weight Decompress      |    | MAC array      |    +--------------+    +------------+  |
   |  | Zero-Skipping          |--> | + Accumulator  |--> | DPU          |--> | PPU        |  |
   |  | Weight/Feature Load    |    | 1024 MAC INT8  |    | cộng, nhân,  |    | pooling    |  |
   |  | Buffer 384 KB          |    | mỗi chu kỳ     |    | activation   |    +------------+  |
   |  +------------------------+    +----------------+    +--------------+                    |
   |                                                                                          |
   +------------------------------------------------------------------------------------------+

Nguồn: sơ đồ khối [T1 TRM1 tr.1985, Fig. 36-2]. Mô tả các khối: CNA nạp dữ liệu và giải nén, MAC array 1024 MAC INT8 mỗi chu kỳ, DPU làm bias, scale và activation, PPU làm pooling [T1 TRM1 tr.1984, tr.2020, tr.2054]. Buffer 384KB chia bank cho weight và feature [T1 TRM1 tr.2004]. Zero-skipping thuộc CNA [T1 TRM1 tr.1985]. Compiler có bật nó cho YOLOv8n hay không: unknown.

3. Ba lõi
=========

.. code:: text

   Độc lập: mỗi context một lõi (core_mask = CORE_0, CORE_1, CORE_2)

      khung 1 ----> [ Core 0 ] ----> kết quả 1
      khung 2 ----> [ Core 1 ] ----> kết quả 2
      khung 3 ----> [ Core 2 ] ----> kết quả 3

   Cùng làm một khung (core_mask = CORE_0_1_2)

                        +----> [ Core 0 ] ----+
      Conv, Add,        +----> [ Core 1 ] ----+----> kết quả
      Concat, Relu...  -+----> [ Core 2 ] ----+
      (chia theo khối lượng tính, lớp nhỏ ở một lõi)

      Op khác (MaxPool, Split, Resize...): chạy trên Core 0
      Chiều chia theo H, W hay kênh: không công bố

Chế độ đa lõi: ``core_mask`` nhận AUTO, CORE_0, CORE_1, CORE_2, CORE_0_1, CORE_0_1_2 và ALL [T1 UG232 tr.74]. Trong driver 0.9.8, AUTO chọn lõi ít task nhất và chạy job trên một lõi [T1 DRV ``rknpu_job.c:508-538``]. Chỉ các op sau chia được qua nhiều lõi: Conv, DepthwiseConvolution, Add, Concat, Relu, Clip, Relu6, ThresholdedRelu, PRelu, LeakyRelu [T1 UG232 tr.75]. Hãng ghi các op khác "will fallback to Core0" [T1 UG152 tr.27]. Lớp tải nhỏ cũng chạy trên một lõi [T1 UG232 tr.75]. Suy ra MaxPool, Split và Resize chạy trên Core 0 ở chế độ cùng làm [SL]. Đo của dự án: ConvExSwish chia 0 trên 57 dòng, ConvRelu chia 51 trên 51 [T3 board, :doc:`../03-phuong-phap/04-tang-npu-ket-qua/08-so-muc-chua-biet` mục 5].

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Cấu hình
     - Kết quả
     - Nguồn
   * - 1 context, một lõi (``CORE_0``)
     - 54.66 FPS
     - [T3 board, ``results/thr_p3.json``]
   * - 1 context, ba lõi
     - 56.1 FPS (hơn 2.6%)
     - [T3 board, ``results/thr_p3.json``]
   * - 2 context độc lập
     - 102.0 FPS
     - [T3 board, ``results/thr_p3.json``]
   * - 3 context độc lập
     - 141.18 FPS
     - [T3 board, ``results/thr_p3.json``]

Đo lại ngày 2026-11-07 khi khóa xung bằng ``lock_freq.sh``, model ``best-rk3588.rknn``, ``NPU_CORE_0``, trong pipeline tuần tự: suy luận NPU trung vị 17.387 ms (p95 17.443 ms), khớp 17.161 ms của dự án. Vòng suy luận liên tục không ghim CPU cho trung vị 19.997 ms (12 s, p95 20.812 ms) và 17.043 ms (90 s, p95 21.040 ms), tức hai mức khoảng 17 và 20 ms [T3 board, ``board_pipeline_test2.py``, ``npu_loop.py``]. Dự án đã ghi các mức độ trễ phụ thuộc vị trí CPU: :doc:`../03-phuong-phap/02-tang-npu-nen-do/04-cac-muc-do-tre`. Hai mức này có cùng nguyên nhân hay không: unknown.

Các số đo ở bảng trên theo giao thức P3 của dự án (khóa CPU, khóa xung, chuyển ngắt NPU), xem :doc:`../03-phuong-phap/04-tang-npu-ket-qua/03-ket-qua-da-nhan`. Chiều tách tensor khi chia một lớp cho nhiều lõi: unknown (:doc:`../02-nen-tang-rk3588/01-phan-cung-npu/03-che-do-da-loi-va-system-sram`).

4. YOLOv8n qua NPU, lớp theo lớp
================================

.. code:: text

    ảnh vào RGB 640x640x3
      |
      v
    [0]  Conv s2                      Backbone
    [1]  Conv s2
    [2]  C2f
    [3]  Conv s2
    [4]  C2f            ---> (a)
    [5]  Conv s2
    [6]  C2f            ---> (b)
    [7]  Conv s2
    [8]  C2f
    [9]  SPPF           ---> (d)
    [10] Upsample                     Neck
    [11] Concat         <--- (b)
    [12] C2f            ---> (c)
    [13] Upsample
    [14] Concat         <--- (a)
    [15] C2f            ---> Detect, P3 (vật nhỏ)
    [16] Conv s2
    [17] Concat         <--- (c)
    [18] C2f            ---> Detect, P4
    [19] Conv s2
    [20] Concat         <--- (d)
    [21] C2f            ---> Detect, P5 (vật lớn)
    [22] Detect         đầu ra: tensor [1, 4 + nc, 8400]

Đồ thị lấy từ ``yolov8.yaml`` của Ultralytics trong ``.venv`` của repo. Chữ ``s2`` là stride 2. Chữ cái (a) đến (d) nối nơi tạo skip với nơi dùng:

.. list-table::
   :header-rows: 1
   :widths: 14 30 30 26

   * - Skip
     - Tạo ở
     - Dùng ở
     - Ghi chú
   * - (a)
     - [4] C2f, mức P3
     - [14] Concat
     - Nối theo kênh với ảnh phóng to từ [13]
   * - (b)
     - [6] C2f, mức P4
     - [11] Concat
     - Nối theo kênh với ảnh phóng to từ [10]
   * - (c)
     - [12] C2f
     - [17] Concat
     - Nối với đầu ra Conv [16]
   * - (d)
     - [9] SPPF
     - [20] Concat
     - Nối với đầu ra Conv [19]

Nguồn: [Mã nguồn repo, ``.venv/lib/python3.12/site-packages/ultralytics/cfg/models/v8/yolov8.yaml``]. Bên trong khối C2f:

.. code:: text

    vào -> Conv -> Split -> hai nửa a, b
    y = [a, b]
    lặp n lần:  y thêm  Bottleneck(phần tử cuối của y)
    ra = Conv( Concat(y) )          Concat nhận 2 + n tensor

    Bottleneck: Conv -> Conv -> (+) Add với đầu vào, chỉ khi shortcut = True

Khối C2f phân nhánh và gom luồng bằng Split, Concat và Add. Các op này có trong danh sách op NPU [T1 OPL tr.56, tr.58, tr.91]. SPPF dùng chuỗi ba MaxPool 5x5 stride 1 rồi nối [Mã nguồn repo, ``ultralytics/nn/modules/block.py`` lớp ``SPPF`` trong ``.venv``]. Op MaxPool có trong danh sách NPU [T1 OPL tr.79]. Mỗi Conv + BN + SiLU được gộp thành ``ConvExSwish``, có 57 op này trong đồ thị RKNN của model SiLU 5 lớp [T3 PC, ``results/q2e_pc.json``, phân tích log build]. Tensor skip phải giữ đến lớp Concat đích. Kích thước INT8 của bốn tensor skip (tính từ ``yolov8.yaml``, scale ``n`` có width 0.25):

.. list-table::
   :header-rows: 1
   :widths: 14 30 28 28

   * - Skip
     - Tensor (kênh x cao x rộng)
     - Byte
     - So với buffer 384 KB
   * - (a)
     - 64 x 80 x 80
     - 409600 (400 KB)
     - lớn hơn
   * - (b)
     - 128 x 40 x 40
     - 204800 (200 KB)
     - nhỏ hơn
   * - (c)
     - 128 x 40 x 40
     - 204800 (200 KB)
     - nhỏ hơn
   * - (d)
     - 256 x 20 x 20
     - 102400 (100 KB)
     - nhỏ hơn

Nguồn: [Mã nguồn repo, ``yolov8.yaml``] [SL, phép tính]. Dữ liệu từng lớp đo trên board (YOLOv8n INT8, ``CORE_0``, tổng 23106 us) [T3 board, ``results/layer_analysis_ppe5_yolov8n_baseline_100ep_s0_int8_CORE_0.md`` mục 2]:

.. list-table::
   :header-rows: 1
   :widths: 24 16 20 20 20

   * - Op
     - Số lần
     - Thời gian (us)
     - RW (KB)
     - Chiếm tổng
   * - Concat
     - 17
     - 2336
     - 7530
     - 10.11%
   * - Split
     - 9
     - 1029
     - 2531
     - 4.45%
   * - Add
     - 8
     - 746
     - 2624
     - 3.23%
   * - MaxPool
     - 3
     - 219
     - 150
     - 0.95%
   * - Resize
     - 2
     - 279
     - 300
     - 1.21%

Ba op Concat, Split, Add thời gian tỉ lệ với lượng dữ liệu đọc ghi: 144 us mỗi MB cộng 68.4 us, R2 0.708 [T3 board, như trên]. Cột ``RW(KB)`` là tổng dữ liệu đọc và ghi của op [T1 UG232 tr.32]. Suy ra Concat và Add đọc các tensor skip từ bộ nhớ ngoài buffer [SL]. Các tensor skip nhỏ hơn 384 KB (b, c, d) có ở lại trên chip giữa hai lớp hay không: unknown.

5. Op và nơi chạy
=================

.. list-table::
   :header-rows: 1
   :widths: 24 46 30

   * - Op
     - Nơi chạy
     - Nguồn
   * - Conv + BN + SiLU
     - NPU, gộp thành ``ConvExSwish``. Khối nào trong lõi làm SiLU: unknown
     - [T3 PC, ``results/q2e_pc.json``]
   * - Concat, Split, Add
     - NPU (có trong danh sách op NPU)
     - [T1 OPL tr.56, tr.58, tr.91]
   * - MaxPool 5x5 (SPPF)
     - NPU
     - [T1 OPL tr.79]
   * - Resize (Upsample)
     - UG232: NPU không có nhân Resize riêng, toolkit đổi sang ConvTranspose. Đồ thị RKNN của model dự án có 2 op Resize và không có ConvTranspose. Resize chạy ở đâu: unknown
     - [T1 UG232 tr.176] [T3 PC, ``results/q2e_pc.json``]
   * - DFL, Transpose, NMS
     - Xem :doc:`../02-nen-tang-rk3588/05-yolo-tren-rk3588/02-op-yolov8-tren-rknn`
     - [Mã nguồn repo]

Nối ống DPU, PPU như hình 2 là mô tả của TRM cho luồng tích chập. Việc từng op trên ánh xạ vào khối nào của lõi: unknown, chỉ riêng pooling trên PPU có nguồn [T1 TRM1 tr.2054].

6. Điều chưa biết
=================

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Điều chưa biết
     - Cần để xác minh
   * - Chiều chia một lớp cho ba lõi
     - Tài liệu hãng chỉ nêu tỷ lệ khối lượng. Cần log ``rknn`` mức cao hoặc đọc ``subcore_task``
   * - Tensor skip nhỏ hơn 384KB (b, c, d) có ở lại trên chip không
     - Đo lưu lượng DDR từng lớp bằng ``eval_perf`` với model rút gọn chỉ có skip đó
   * - Khối nào trong lõi làm SiLU
     - Tài liệu hãng về ``ConvExSwish``
   * - Thời gian từng lớp trong pipeline thật
     - Xem :doc:`../03-phuong-phap/index`
