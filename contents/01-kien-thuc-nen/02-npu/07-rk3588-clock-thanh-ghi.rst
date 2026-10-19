:tocdepth: 1

**************************
RK3588: clock và thanh ghi
**************************

.. admonition:: Trang này trả lời

   - NPU chạy ở tần số nào, điều khiển thế nào?
   - phần mềm điều khiển NPU qua cơ chế nào?

.. admonition:: Tóm tắt

   - Datasheet ghi "Max NPU frequency" là `TBD` [T1 DS tr.31], nên tần số tối đa, bảng OPP và việc ba core có chung tần số là `unknown`, chỉ được đóng một phần bằng DTS và đo T3.
   - DTS có OPP "RK3588 npu" từ 300 đến 1000 MHz, và board (T3) đọc `max_freq` 1000000000.
   - Không viết "NPU chạy 1GHz" như tần số tối đa hoặc mặc định, vì `1000000000` chỉ xuất hiện trong ví dụ đầu ra `eval_perf` và ví dụ lệnh.
   - Con số 6 TOPS khớp `1024x3` MAC/chu kỳ ở 1 GHz chỉ khi tính 2 phép tính cho mỗi MAC, quy ước này không có trong tài liệu vendor.
   - RKNN có hai kiểu cấu hình, slave configured mode và pc work mode, cùng ping-pong registers [T1 TRM1 tr.2053, tr.2052].
   - TRM nói 17 sự kiện ngắt nhưng chỉ mô tả bit 0 đến 13 [T1 TRM1 tr.1995].

.. _28-clock-dvfs-và-reset:

Clock, DVFS và reset
====================

**Câu hỏi:** NPU chạy ở tần số nào, điều khiển thế nào?

**Nguồn nói gì**

   "RKNN has two clock domains, one is AHB clock, the other is AXI clock." [T1 TRM1 tr.2052]

..

   "Automatic localized clock gating is employed throughout the design in order to minimize the dynamic power consumption." [T1 TRM1 tr.2052]

   "Aresetn, the reset signal for AXI interface and every Calculate Core and Control Core." [T1 TRM1 tr.2052]

Datasheet tr.31 có dòng "Max NPU frequency" với giá trị ``TBD`` (đối chiếu từ bảng điện).

Phía driver (UG152):

   "If the NPU driver version is after 0.7.2, you can query the NPU version, the utilization of different NPU cores and manually switch the NPU power supply through the node." [T1 UG152 tr.73]

..

   "echo userspace > /sys/class/devfreq/fdab0000.npu/governor" [T1 UG152 tr.73]

**Ý chính.** Core clock dùng chung clock AXI, điều khiển qua CRU (TRM1 tr.2052). Có clock gating tự động và có thể tắt bằng phần mềm. Phía driver có các nút sysfs để cố định tần số qua devfreq và ``clk_rate`` (UG152 tr.73).

**Giới hạn**

- Tần số tối đa, bảng OPP, điện áp theo tần số, và việc ba core có chung tần số hay không là ``unknown`` (Datasheet V0.1 ghi ``TBD``). Đóng một phần (T1 DTS, DRV. T3): DTS (commit f6eedab0, lưu tại ``3rdparty/rknpu-driver-0.9.8/dts/rk3588s.dtsi``) có node ``rknpu`` với ``operating-points-v2 = <&npu_opp_table>``, clock đầu tiên ``clk_npu`` là ``SCMI_CLK_NPU``, ``assigned-clock-rates`` = 200000000 (dòng 3450-3480). ``npu_opp_table`` (dòng 3482-3710): OPP "RK3588 npu" (``opp-supported-hw = <0xf9 0xffff>``, dòng 3534-3655) gồm 300, 400, 500, 600, 700, 800, 900, 1000 MHz.``opp-microvolt`` (giá trị đầu, chưa tính biến thể ``-L1`` đến ``-L5``) là 700000 tại 300 đến 700 MHz, 750000 tại 800 MHz, 800000 tại 900 MHz, 850000 tại 1000 MHz (µV theo tên thuộc tính). OPP "RK3588J/M" (``opp-supported-hw = <0x06 0xffff>``, dòng 3658-3709) tối đa 950 MHz. Datasheet vẫn ``TBD``. Governor devfreq tên ``rknpu_ondemand``, ``polling_ms`` = 50 (``rknpu_devfreq.c:48,73``), hàm target trả ``ondemand_freq`` nếu khác 0, ngược lại ``previous_freq``, không đọc tải (``rknpu_devfreq.c:54-64``), trong DRV ``ondemand_freq`` chỉ được gán lúc khởi tạo (``rknpu_devfreq.c:383,699``) và khi ghi node ``freq`` (``rknpu_debugger.c:229``). Board (T3, đọc 2026-10-10): governor ``rknpu_ondemand``.``available_frequencies`` 300000000 đến 1000000000 bước 100 MHz (8 mức).``cur_freq`` 1000000000.``min_freq`` 300000000.``max_freq`` 1000000000.``trans_stat`` 0 lần chuyển, 1098880 ms ở 1000000000 (uptime 18 phút), dmesg ``RKNPU: bin=0``. Về ba core có chung tần số: driver đọc tần số từ một clock ``clks[0]`` (``rknpu_debugger.c:177-191``) và OPP là một bảng chung, chưa kết luận gì thêm. Board (T3, đọc bằng sudo 2026-10-10, log T3 board 2026-10-10 (``tmp/04_debug-logs/2026-10-10_t3-board-silu-resize/README.md``)): ``freq`` = 1000000000.``volt`` = 812500, khác 850000 ở dòng ``opp-microvolt`` đầu của OPP 1000 MHz trong DTS, nên board dùng một biến thể điện áp khác (chưa biết biến thể nào).
- Không viết "NPU chạy 1GHz" như tần số tối đa hoặc mặc định: ``1000000000`` xuất hiện trong ví dụ đầu ra ``eval_perf`` (UG232 tr.31, "the frequencies supported by different firmware may vary") và trong ví dụ lệnh (UG152 tr.73).
- Con số 6 TOPS khớp với ``1024x3`` MAC/chu kỳ ở 1 GHz nếu tính 2 phép tính cho mỗi MAC (số học của file này, không phải câu của vendor). Quy ước 2 phép tính/MAC không có trong tài liệu vendor, tần số tối đa ``TBD`` (DS tr.31).

--------------

.. _29-register-map-hai-chế-độ-cấu-hình-ping-pong-và-ngắt:

Register map, hai chế độ cấu hình, ping-pong và ngắt
====================================================

**Câu hỏi:** phần mềm điều khiển NPU qua cơ chế nào?

**Nguồn nói gì**

Bản đồ thanh ghi nội bộ (TRM1 tr.1986, Table 1-1): các block ``PC``, ``CNA``, ``CORE``, ``DPU``, ``DPU_RDMA``, ``PPU``, ``PPU_RDMA``, ``DDMA``, ``SDMA`` (mỗi block 4KB) và ``GLOBAL``.

   "RKNN has two types of work mode: slave configured mode and pc work mode" [T1 TRM1 tr.2053]

..

   "every Calculate Core and Control Core of RKNN has its owner ping-pong registers." [T1 TRM1 tr.2052]

   "Each register takes 64 bits" [T1 TRM1 tr.1994] (định dạng mỗi lệnh PC mode: block đích, giá trị, offset)

..

   "op_en is strongly recommended set at the end of register list." [T1 TRM1 tr.1994]

   "RKNN has 3 interrupt output signal and it remains asserted until the host processor clears the interrupt." [T1 TRM1 tr.2053]

..

   "Each bit of PC_INTERRUPT_STATUS represents one of the 17 possible events that the RKNN can signal to the host processor." [T1 TRM1 tr.2053]

|TRM1 Fig 36-3| *Hình 2.9a. Luồng PC mode: khởi tạo thông tin thanh ghi trong bộ nhớ hệ thống, ghi ``pc_interrupt_clear`` và ``pc_interrupt_mask``, ghi ``pc_amount``, ``pc_addr``, ``pc_task_number``, ``pc_task_dma_base``, rồi ghi ``pc_op_enable``. Nguồn: [T1 TRM1 tr.2053, Fig. 36-3]*

|TRM1 Fig 36-4| *Hình 2.9b. Luồng cấu hình một phép convolution ("Convolution flow 1"): cấu hình CNA, DPU, tùy chọn PPU, rồi bật NPU. Nguồn: [T1 TRM1 tr.2054, Fig. 36-4]*

**Ý chính**

- Có hai cách cấu hình: slave mode (CPU ghi thanh ghi qua AHB) và PC mode (NPU tự lấy danh sách thanh ghi từ bộ nhớ qua AXI DMA) (TRM1 tr.1994, 2053).
- Ping-pong giúp cấu hình nhóm thanh ghi tiếp theo trong lúc nhóm hiện tại chạy (TRM1 tr.2052).
- Có 3 tín hiệu ngắt, khớp với ``irq_rknn_c0`` đến ``c2`` (xem 2.1). TRM không nối rõ mỗi ngắt với mỗi core.

**Giới hạn.** TRM nói 17 sự kiện nhưng chỉ mô tả bit 0 đến 13 (TRM1 tr.1995). Bảng Table 1-1 ghi ``GLOBAL`` là ``0xf000 ~ 0xf004`` trong khi thanh ghi ``global_operation_enable`` ở ``0xF008`` ().

--------------

.. |TRM1 Fig 36-3| image:: ../../../_assets/img/npu/02_rk3588_npu_hardware/trm1_p2053_fig36-3.png

.. |TRM1 Fig 36-4| image:: ../../../_assets/img/npu/02_rk3588_npu_hardware/trm1_p2054_fig36-4.png

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
   * - ``TRM1``
     - T1
     - :download:`01_Rockchip_RK3588_TRM_V1.0_Part1_20220309.pdf <../../../_assets/pdf/papers/05_rk3588/01_vendor_docs/02_trm/01_Rockchip_RK3588_TRM_V1.0_Part1_20220309.pdf>`
     - 11
   * - ``UG152``
     - T1
     - :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../../_assets/pdf/papers/05_rk3588/01_vendor_docs/03_rknn_npu/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>`
     - 2
