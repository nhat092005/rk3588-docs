:tocdepth: 1

***********
DDR và SRAM
***********

.. admonition:: Trang này trả lời

   - NPU dùng bộ nhớ ngoài nào, băng thông ra sao?
   - NPU dùng SRAM của SoC thế nào, và cần điều kiện gì?

.. admonition:: Tóm tắt

   - Bộ điều khiển hỗ trợ 4 kênh x16 bit và LPDDR4, LPDDR4X, LPDDR5, nhưng đây là khả năng của bộ điều khiển, không phải cấu hình của board [T1 DS tr.8] [T1 TRM2 tr.55].
   - Băng thông đỉnh GB/s, loại DRAM và số kênh thực của board RK3588S đều là `unknown`, không tính từ speed grade.
   - RK3588 có 1MB SRAM, trong đó 956KB có thể dùng cho các IP và hỗ trợ cấp phát riêng cho RKNPU [T1 UG232 tr.106].
   - SRAM giúp giảm áp lực băng thông DDR nhưng có thể ảnh hưởng thời gian suy luận, nên là trade-off cần đo [T1 UG232 tr.106].
   - `RKNN_FLAG_SHARE_SRAM` có trong header nhưng chưa implement [T1 UG232 tr.108].`CONFIG_ROCKCHIP_RKNPU_SRAM` không đặt trên kernel board nên `rknpu/mm` không tồn tại, hiệu lực cờ SRAM trong C API trên board vẫn `unknown`.
   - Hai tài liệu mâu thuẫn về runtime tối thiểu cho SRAM: ">=1.3.4b14" ở SRAM dòng 54 và ">=1.6.0" ở UG232 tr.107.

.. _71-ddr:

DDR
====

**Câu hỏi:** NPU dùng bộ nhớ ngoài nào, băng thông ra sao?

**Nguồn nói gì**

   "RK3588 has high-performance quad channel external memory interface (LPDDR4/LPDDR4X/LPDDR5) capable of sustaining demanding memory bandwidths" [T1 DS tr.7]

..

   "Support four channels, each channel 16bits data widths" [T1 DS tr.8]

   "Support up to 2 ranks (chip selects) for each channel" [T1 DS tr.8]

..

   "Support up to 4-channel interleaving with a maximum of 32GB capacity in total, 2 ranks for each channel" [T1 TRM2 tr.55]

   "Support 64-bit DDR data bus width for 4-channel interleaving" [T1 TRM2 tr.55]

..

   "Support LPDDR4 protocol up to LPDDR4-4267 speed grade and LPDDR5 protocol up to LPDDR5-5500" [T1 TRM2 tr.55]

   "Transaction statistics for bandwidth analysis" [T1 TRM2 tr.16]

..

   "There are totally 12 probes to monitor the DDR schedule traffic statics" [T1 TRM2 tr.20]

   "The interface rknn.eval_perf() will output the current hardware frequency and obtain the performance evaluation results of the model." [T1 UG232 tr.31]

Từ khái niệm (file ``01_``): "fetching data from off-chip DRAMs costs orders of magnitude more energy than from on-chip storage" [T2 EYE tr.1] (đây là năng lượng, không phải băng thông) và "Without sufficient operational intensity, a program is memory bandwidth-bound and lives under the slanted part of the roofline." [T2 TPU tr.5].

**Ý chính**

- Bộ điều khiển hỗ trợ 4 kênh x16 bit (bus 64 bit khi interleave 4 kênh) và 2 kênh (bus 32 bit), LPDDR4, LPDDR4X, LPDDR5 (DS tr.7, 8. TRM2 tr.55).
- Đây là khả năng của bộ điều khiển, không phải cấu hình của board. TRM nêu trần speed grade (LPDDR4-4267, LPDDR5-5500), không nêu tốc độ board dùng.
- Interconnect có probe phần cứng để đo lưu lượng DDR (TRM2 tr.20). Linux có lộ ra các probe này hay không là ``unknown``.

**Giới hạn**

- Băng thông đỉnh GB/s, loại DRAM và số kênh thực của board RK3588S: ``unknown``. Không tính từ speed grade, vì nguồn không cho cấu hình thực. EDGE tr.3 có một số đo ``mbw`` 8807 MiB/s cho một board RK3588 không nêu tên (không phải số đỉnh, không phải RK3588S). EDGE tr.8 (Fig. 6) đo độ trễ dưới tải CPU và bộ nhớ bằng ``stress-ng``.
- Tần số DDR chỉ có trong ví dụ lệnh (UG232 tr.31 liệt kê một danh sách tần số của firmware mẫu. UG152 tr.72 ví dụ cố định ở 1560MHz), không phải tần số mặc định của board.

--------------

.. _72-sram-cho-npu:

SRAM cho NPU
============

**Câu hỏi:** NPU dùng SRAM của SoC thế nào, và cần điều kiện gì?

**Nguồn nói gì**

   "RK3588 SOC contains 1MB of SRAM internally, of which 956KB can be used by various IPs on the SOC. It supports designated allocation for RKNPU." [T1 UG232 tr.106]

..

   "SRAM can help RKNPU applications reduce DDR bandwidth pressure, but it may have a certain impact on inference time." [T1 UG232 tr.106]

   "Specify RKNN_FLAG_ENABLE_SRAM in the flags parameter of the rknn_init() interface to enable SRAM in this context." [T1 UG232 tr.107]

..

   "When SRAM is occupied by a certain rknn context, other rknn contexts do not support reusing the SRAM of this segment. The RKNN_FLAG_SHARE_SRAM function in rknn_api.h has not yet been implemented." [T1 UG232 tr.108]

Các dòng của file SRAM (tiếng Trung, kèm tạm dịch):

   "RKNPU驱动版本>=0.8.0" [T1 SRAM dòng 10] (Driver RKNPU phiên bản từ 0.8.0 trở lên.)

..

   "内核config需要开启CONFIG_ROCKCHIP_RKNPU_SRAM=y" [T1 SRAM dòng 11] (Cấu hình kernel phải bật ``CONFIG_ROCKCHIP_RKNPU_SRAM=y``.)

   "RKNPU Runtime库(librknnrt.so)版本>=1.3.4b14" [T1 SRAM dòng 54]

..

   "export RKNN_INTERNAL_MEM_TYPE=sram" [T1 SRAM dòng 61] (Tự động: thử cấp đủ SRAM còn lại cho Internal. Dạng ``sram#256`` chỉ định 256KB.)

   "export RKNN_WEIGHT_MEM_TYPE=sram" [T1 SRAM dòng 68] (Kèm ``export RKNN_SEPARATE_WEIGHT_MEM=1``: cấp SRAM cho Weight, dạng ``sram#128`` chỉ định 128KB.)

..

   "Predict SRAM Hit RW Amount表示整个网络SRAM的读写预测情况，可近似估计每帧节省的带宽" [T1 SRAM dòng 189] (Số này là dự đoán đọc ghi SRAM của cả mạng, có thể dùng ước chừng băng thông tiết kiệm mỗi frame.)

Mã nguồn: ``#define RKNN_FLAG_ENABLE_SRAM 0x00000800`` [T1 HDR dòng 69] và ``#define RKNN_FLAG_SHARE_SRAM 0x00001000`` [T1 HDR dòng 72]. UG232 tr.107 ghi yêu cầu ``librknnrt.so`` ">=1.6.0".

**Ý chính**

- 956KB là mức tối đa có thể cấp cho NPU, không phải mặc định (UG232 tr.106. SRAM dòng 3, 21, 22). SRAM dùng chung với các IP khác như codec, các vùng không được chồng lấn (SRAM dòng 22).
- SRAM giúp giảm áp lực băng thông DDR nhưng có thể ảnh hưởng thời gian suy luận (UG232 tr.106). Tổng hợp của file này: đây là một trade-off cần đo, không phải lợi ích chắc chắn.
- Có hai cách bật: biến môi trường (SRAM dòng 59 đến 71, gồm cả Weight) và cờ ``RKNN_FLAG_ENABLE_SRAM`` trong ``rknn_init`` (UG232 tr.107, chỉ nói Internal Tensor).
- "Predict SRAM Hit RW Amount" là số dự đoán, không phải số đo.

**Giới hạn**

- Hai tài liệu mâu thuẫn: SRAM dòng 54 yêu cầu runtime ">=1.3.4b14", UG232 tr.107 yêu cầu ">=1.6.0". Không có ghi chú giải thích. Runtime đi kèm repo là 2.3.2 nên thỏa cả hai.
- ``RKNN_FLAG_SHARE_SRAM``: có trong header (HDR dòng 72) nhưng UG232 tr.108 nói chưa implement.
- Độ trễ và băng thông của SRAM so với DDR, và NPU nối vào cổng AXI nào: ``unknown``. Weight SRAM bằng cờ C API cũng ``unknown`` (chỉ có biến môi trường ở SRAM md). Đóng một phần (T1 DRV, T3. DRV xem mục Nguồn cuối trang): ``CONFIG_ROCKCHIP_RKNPU_SRAM`` không đặt trên kernel board (T3, đọc 2026-10-10).``rknpu_mm.o`` chỉ biên dịch khi bật cấu hình đó (``Makefile:14``.``Kconfig:32-36``) và node ``rknpu/mm`` chỉ có khi bật (``rknpu_debugger.c:313-315``), nên node ``rknpu/mm`` không tồn tại trên board, hiệu lực của các cờ SRAM trong C API trên board này vẫn ``unknown``.
- Phần 1MB trừ 956KB là 68KB, tài liệu không giải thích.

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
   * - ``SRAM``
     - T1
     - :doc:`SRAM usage (zh) </contents/05-tai-lieu-hang/04-sram-usage>`
     - 6
   * - ``TRM2``
     - T1
     - :download:`02_Rockchip_RK3588_TRM_V1.0_Part2_20220309.pdf <../../../_assets/pdf/papers/05_rk3588/01_vendor_docs/02_trm/02_Rockchip_RK3588_TRM_V1.0_Part2_20220309.pdf>`
     - 5
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 5
   * - ``DS``
     - T1
     - :download:`02_RK3588_Datasheet_V0.1-20210727.pdf <../../../_assets/pdf/papers/05_rk3588/01_vendor_docs/01_datasheet/02_RK3588_Datasheet_V0.1-20210727.pdf>`
     - 3
   * - ``HDR``
     - T1
     - ``3rdparty/rknn-toolkit2/rknpu2/runtime/Linux/librknn_api/include/rknn_api.h`` (repo chính)
     - 2
   * - ``EYE``
     - T2
     - :download:`eyeriss_dataflow_2016chen.pdf <../../../_assets/pdf/papers/01_hardware/eyeriss_dataflow_2016chen.pdf>`
     - 1
   * - ``TPU``
     - T2
     - :download:`tpu_datacenter_2017jouppi.pdf <../../../_assets/pdf/papers/01_hardware/tpu_datacenter_2017jouppi.pdf>`
     - 1
