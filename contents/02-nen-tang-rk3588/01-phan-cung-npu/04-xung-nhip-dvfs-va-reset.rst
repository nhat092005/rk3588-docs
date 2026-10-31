:tocdepth: 1

***********************
Xung nhịp DVFS và reset
***********************

.. admonition:: Trang này trả lời

   - NPU nhận clock từ đâu và được cắt clock thế nào?
   - NPU chạy ở những tần số nào, đổi mức ra sao?
   - NPU được reset thế nào?

.. admonition:: Tóm tắt

   - RKNN có hai miền clock: AHB và AXI. Clock AXI cũng là core clock của mọi Calculate Core và Control Core, tần số điều khiển bằng CRU. Clock được gate tự động khi khối rảnh [T1 TRM1 tr.2052].
   - TRM1 không có sơ đồ cây clock riêng cho NPU. Cây trong trang này suy ra từ bảng mux ``CRU_CLKSEL_CON73`` và ``CON74`` [T1 TRM1 tr.82].
   - Mỗi core có gate riêng (``aclk_rknnN``, ``hclk_rknnN``), nhưng chỉ có một mux/chia ``clk_rknn_dsu0`` trong CON73/CON74 và cả ba miền nguồn ``PD_NPUTOP/NPU1/NPU2`` đều tham chiếu ``CLK_NPU_DSU0`` [T1 TRM1 tr.82, tr.134] [T1 DTS dòng 3116-3149].
   - Datasheet ghi ``Max NPU frequency`` là 1000 MHz ở RK3588 V1.3 và RK3588S V1.7 [T1 DS V1.3 pdf 30] [T1 DS V1.7 tr.32] (các bản nháp V0.1, HYY Rev 1.1 và RK3588S V1.3 để trống thông số này [T1 DS V0.1 tr.31]).
   - Bảng mức tần số và điện áp trong DTS của driver 0.9.8 trải từ 300 đến 1000 MHz cho "RK3588 npu" [T1 DTS dòng 3534-3655].
   - Driver dùng governor ``rknpu_ondemand`` nhưng hàm target không đọc tải [T1 DRV rknpu_devfreq.c:54-64]. Khi tăng tần số, điện áp được tăng trước. Khi giảm tần số, điện áp được giảm sau [T1 DRV rknpu_devfreq.c:501] [T1 DRV rknpu_devfreq.c:527].
   - Ba core có bộ reset độc lập (``aresetn`` và ``hresetn`` mỗi core). TRM1 yêu cầu giữ reset tối thiểu 32 core clock và nhả hai tín hiệu cùng lúc [T1 TRM1 tr.2052].

.. contents:: Trong trang này
   :local:
   :depth: 1


.. _clock-dvfs-reset:

1. Cây clock của NPU
====================

Trong CRU (Clock and Reset Unit), TRM1 liệt kê các đơn vị cơ bản: Gating, MUX, Divfree, Fracdiv, Divfree50, DivFreeNP5 ("All R3588 PLLs receive 24MHz oscillator as input reference clock", "All clocks can be gated by software") [T1 TRM1 tr.30].

1.1 Miền clock và clock gating
------------------------------

TRM1 mô tả hai miền clock và cơ chế tự động cắt clock khi khối rảnh:

   "RKNN has two clock domains, one is AHB clock, the other is AXI clock." ... "AXI clock also used for core clock for every Calculate Core and Control Core. Clock frequency can be controlled by CRU, please refer to the relevant sections." [T1 TRM1 tr.2052]

   "Automatic localized clock gating is employed throughout the design in order to minimize the dynamic power consumption." ... "If a block and the interface to the block are both idle, then the clock of that block will be gated automatically. This feature can be disabled by software." [T1 TRM1 tr.2052]

Ở mức thanh ghi: ``RKNN_cna_clk_gate`` (offset ``0x1090``, reset ``0x00000000``) có bit ``1'd0: Auto clock gate is enabled`` và ``1'd1: Disable csc block clock gate``, tương tự cho weight block và feature block [T1 TRM1 tr.1987, tr.2008-2009]. ``RKNN_core_mac_gating`` (offset ``0x300C``, reset ``0x07800800``) điều khiển gating phía core với trường ``slcg_op_en`` [26:0] ("Soft clock gating signals.") mà TRM1 không tách tên từng bit lẻ [T1 TRM1 tr.1988, tr.2013].

1.2 Mux chia và gate trong CRU
------------------------------

TRM1 có Fig. 2-1 CRU Block Diagram (chung cho cả SoC). Cây clock của NPU suy ra từ thanh ghi mux và chia ``CRU_CLKSEL_CON73`` (offset ``0x0424``) và ``CRU_CLKSEL_CON74`` (offset ``0x0428``) [T1 TRM1 tr.82-83]:

.. code-block:: none

   PLL: gpll, cpll, aupll, npll, spll   (clk_*_mux)
     -> mux + chia   clk_rknn_dsu0_src_t   CON73 bit 9:7 và bit 6:2
     -> mux          clk_rknn_dsu0         CON74 bit 0 (chọn src_t hoặc clk_npu_pvtpll)
     -> gate         GATE_CON29 bit 3 (clk_rknn_dsu0_en)

.. _bang-cru-clksel-npu:

.. list-table:: Thanh ghi chọn nguồn và chia clock của NPU [T1 TRM1 tr.82-83]
   :header-rows: 1
   :widths: 14 10 26 50

   * - Thanh ghi
     - Bit
     - Tên
     - Giá trị
   * - CON73
     - 15
     - ``clk_testout_npu_sel``
     - ``0: clk_rknn_dsu0_src_t``, ``1: clk_npu_pvtpll``
   * - CON73
     - 14:10
     - ``clk_testout_npu_div``
     - reset ``0x1f``, chia ``div_con + 1``
   * - CON73
     - 9:7
     - ``clk_rknn_dsu0_src_t_sel``
     - reset ``0x1``. ``000`` gpll, ``001`` cpll, ``010`` aupll, ``011`` npll, ``100`` spll
   * - CON73
     - 6:2
     - ``clk_rknn_dsu0_src_t_div``
     - reset ``0x01``, chia ``div_con + 1`` (tức chia 2 ở trạng thái reset)
   * - CON73
     - 1:0
     - ``hclk_rknn_root_sel``
     - ``00`` matrix_200m, ``01`` matrix_100m, ``10`` matrix_50m, ``11`` xin_osc0_func
   * - CON74
     - 4
     - ``clk_npu_pvtpll_sel``
     - reset ``0x1``. ``0: clk_rknn_dsu0_src_t``, ``1: xin_osc0_func``
   * - CON74
     - 0
     - ``clk_rknn_dsu0_sel``
     - reset ``0x0``. ``0: clk_rknn_dsu0_src_t``, ``1: clk_npu_pvtpll``

Cổng clock (gate, bit 0 ở reset nghĩa là clock bật) [T1 TRM1 tr.134-137]:

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Thanh ghi
     - Bit và clock
   * - ``CRU_GATE_CON27`` (``0x086C``, tr.134)
     - 0 ``aclk_rknn1_en``, 1 ``aclk_rknn1_biu_en``, 2 ``hclk_rknn1_en``, 3 ``hclk_rknn1_biu_en``
   * - ``CRU_GATE_CON28`` (``0x0870``, tr.135)
     - tương tự cho ``rknn2``
   * - ``CRU_GATE_CON29`` (``0x0874``, tr.135-136)
     - 0 ``hclk_rknn_root_en``, 1 ``clk_rknn_dsu0_df_en``, 2 ``clk_testout_npu_en``, 3 ``clk_rknn_dsu0_en``, 4 ``pclk_nputop_root_en``, 5 ``pclk_nputop_biu_en``, 6 ``pclk_npu_timer_en``, 10 ``pclk_npu_wdt_en``, 13 ``pclk_npu_grf_en``, 15 ``clk_npu_pvtm_en``
   * - ``CRU_GATE_CON30`` (``0x0878``, tr.136-137)
     - 6 ``aclk_rknn0_en``, 7 ``aclk_rknn0_biu_en``, 8 ``hclk_rknn0_en``, 9 ``hclk_rknn0_biu_en``, 15 ``clk_npu_pvtpll_en``, bit 1-3 và 5 là clock ``npu_cm0``

Mỗi core có gate ``aclk``/``hclk`` riêng, nhưng trong CON73/CON74 chỉ có một mux và một bộ chia ``clk_rknn_dsu0`` dùng chung (TRM1 không có bộ chia tần số độc lập cho từng core).

Tự hạ clock khi rảnh (auto clock switch): ``CRU_AUTOCS_CLK_RKNN_DSU0_SRC_T_CON0`` (``0x0F38``, ``wait_th`` [31:16] reset ``0x0020``, ``idle_th`` [15:0] reset ``0x0004``) và ``_CON1`` (``0x0F3C``, ``clksel_cfg`` [15:14] chọn ``xin_osc0_func_div`` hoặc ``clk_rtc_32k``, bit 13 ``switch_en`` bật chuyển sang tần số thấp khi khối rảnh) [T1 TRM1 tr.49, tr.257]. PVTPLL của NPU nằm trong ``NPU_GRF_PVTPLL_CON0_L`` (``0x000C``) đến ``_CON3`` (``0x001C``), bit 15 ``bypass = 0`` hỗ trợ chuyển tần số không gai ("Support glitch-free frequency conversion") [T1 TRM1 tr.765-767].

1.3 Clock trong DTS
-------------------

Node NPU trong DTS của driver 0.9.8 [T1 DTS dòng 3450-3480]:

.. code-block:: none

   clocks = <&scmi_clk SCMI_CLK_NPU>, <&cru ACLK_NPU0>, <&cru ACLK_NPU1>, <&cru ACLK_NPU2>,
            <&cru HCLK_NPU0>, <&cru HCLK_NPU1>, <&cru HCLK_NPU2>, <&cru PCLK_NPU_ROOT>;
   clock-names = "clk_npu", "aclk0", "aclk1", "aclk2", "hclk0", "hclk1", "hclk2", "pclk";
   assigned-clocks = <&scmi_clk SCMI_CLK_NPU>;
   assigned-clock-rates = <200000000>;

Clock đầu tiên ``clk_npu`` gắn vào ``scmi_clk`` (``protocol@14`` thuộc node ``scmi`` với ``compatible = "arm,scmi-smc"``, ``arm,smc-id = <0x82000010>`` giao tiếp với firmware bảo mật) [T1 DTS dòng 1864-1874, dòng 3459]. Khi khởi tạo DVFS, ``rknpu_devfreq.c`` kiểm tra chuỗi ``"scmi"`` trong tên clock để gán ``opp_info.scmi_clk`` [T1 DRV rknpu_devfreq.c:638]. Ở mức miền nguồn trong DTS, cả ba domain ``RK3588_PD_NPUTOP``, ``RK3588_PD_NPU1`` và ``RK3588_PD_NPU2`` đều tham chiếu ``<&cru CLK_NPU_DSU0>`` cùng ``HCLK_NPU_ROOT`` và ``PCLK_NPU_ROOT`` [T1 DTS dòng 3116-3149].

Driver lấy toàn bộ clock qua ``devm_clk_bulk_get_all`` [T1 DRV rknpu_drv.c:1314] và đọc một tần số chung từ ``clks[0]``: ``current_freq = clk_get_rate(rknpu_dev->clks[0].clk)`` [T1 DRV rknpu_debugger.c:177-191] [T1 DRV rknpu_drv.c:406]. Tài liệu hãng dùng đường dẫn debugfs ``/sys/kernel/debug/clk/clk_npu_dsu0/clk_rate`` tương ứng với ``clk_rknn_dsu0`` trong CRU để đặt tần số NPU trên RK3588 [T1 UG152 tr.73].

2. DVFS
=======

DVFS (Dynamic Voltage and Frequency Scaling) điều chỉnh cặp tần số và điện áp theo bảng OPP (Operating Performance Point) trong DTS và governor devfreq của Linux.

2.1 Các mức tần số
------------------

.. _bang-datasheet-max-npu:

.. list-table:: Dòng ``Max NPU frequency`` qua các bản datasheet
   :header-rows: 1
   :widths: 44 12 16 14 14

   * - Bản datasheet
     - Trang PDF
     - Max NPU
     - Max GPU
     - Nguồn
   * - ``02_RK3588_Datasheet_V0.1-20210727``
     - 31
     - Chưa điền
     - Chưa điền
     - [T1 DS V0.1 tr.31]
   * - ``01_HYY_Rockchip_RK3588_Datasheet`` (Rev 1.1)
     - 32
     - Chưa điền
     - Chưa điền
     - [T1 DS HYY tr.32]
   * - ``Rockchip_RK3588S_Datasheet_V1.3_20220310``
     - 31
     - Chưa điền
     - Chưa điền
     - [T1 DS S1.3 tr.31]
   * - ``Rockchip_RK3588_Datasheet_V1.3_20220328``
     - 30
     - 1000 MHz
     - 1000 MHz
     - [T1 DS V1.3 pdf 30]
   * - ``Rockchip_RK3588S_Datasheet_V1.7`` (2026-01-05)
     - 32
     - 1000 MHz
     - 1000 MHz
     - [T1 DS V1.7 tr.32]

Hai bản chính thức V1.3 và V1.7 công bố ``Max NPU frequency`` là 1000 MHz (còn ba bản nháp cũ để trống giá trị này) [T1 DS V1.7 tr.32] [T1 DS V1.3 pdf 30] [T1 DS V0.1 tr.30-31]. Điện áp khuyến nghị trong cùng bảng: ``VDD_NPU`` là 0.55 / 0.75 / 0.95 V và ``VDD_NPU_MEM`` là 0.675 / 0.75 / 0.95 V (Min / Typ / Max) [T1 DS V1.7 tr.31] [T1 DS V1.3 pdf 29]. Với "1024x3 integer 8 MAC operations per cycle" [T1 TRM1 tr.1984] ở 1 GHz, hiệu năng đỉnh đạt 3072 MAC x 2 phép x 1 GHz = 6.144 TOPS, khớp mức "up to 6TOPs" trong datasheet [T1 DS V1.7 tr.7, tr.11].

Bảng OPP cho các mức trung gian nằm trong DTS của driver 0.9.8 (``npu_opp_table``, ``compatible = "operating-points-v2"``) [T1 DTS dòng 3482-3710]:

.. _bang-opp-dts:

.. list-table:: OPP "RK3588 npu" (``opp-supported-hw = <0xf9 0xffff>``) trong DTS [T1 DTS dòng 3534-3655]
   :header-rows: 1
   :widths: 22 24 54

   * - Dòng DTS
     - ``opp-hz``
     - ``opp-microvolt`` (target, min, max)
   * - 3534-3609
     - 300 / 400 / 500 / 600 / 700 MHz
     - ``<700000 700000 850000>`` (biến thể L1 ở 300 MHz: ``687500``)
   * - 3610-3623
     - 800000000 (800 MHz)
     - ``<750000 750000 850000>``
   * - 3624-3639
     - 900000000 (900 MHz)
     - ``<800000 800000 850000>``
   * - 3640-3655
     - 1000000000 (1000 MHz)
     - ``<850000 850000 850000>`` (L1 ``837500`` đến L5 ``787500``)

Với biến thể công nghiệp "RK3588J/M" (``opp-supported-hw = <0x06 0xffff>``), các mức 300 đến 800 MHz đặt ``<750000 750000 850000>`` và mức trần ``opp-j-m-950000000`` (950 MHz) đặt ``<837500 837500 850000>`` [T1 DTS dòng 3658-3709].

Các thuộc tính điều khiển nhiệt và khởi tạo của ``npu_opp_table`` [T1 DTS dòng 3485-3531]: ``rockchip,init-freq = <1000000>`` (1000 MHz), ``intermediate-threshold-freq = <500000>`` (500 MHz), ``rockchip,high-temp = <85000>`` kèm ``rockchip,high-temp-max-freq = <800000>`` (trên 85 độ C giới hạn 800 MHz), ``rockchip,low-temp = <15000>`` kèm ``rockchip,low-temp-min-volt = <750000>``, ``rockchip,pvtm-pvtpll``, ``rockchip,pvtm-thermal-zone = "npu-thermal"``, ``rockchip,opp-clocks = <&cru PCLK_NPU_GRF>, <&cru HCLK_NPU_ROOT>`` và ``volt-mem-read-margin = <855000 1 765000 2 675000 3 495000 4>``. Tài liệu RKNN chỉ dẫn ví dụ đầu ra ``eval_perf`` (``NPU Current Frequency List: - 1000000000``) và script ``scaling_frequency.sh`` của ``rknn_model_zoo`` [T1 UG232 tr.31, tr.136].

2.2 Cơ chế đổi mức
------------------

Governor tùy chỉnh ``rknpu_ondemand`` của driver 0.9.8 (``rknpu_devfreq.c``) có ``polling_ms = 50`` và hàm target ``devfreq_rknpu_ondemand_func`` [T1 DRV rknpu_devfreq.c:48, 73-74]. Hàm này chỉ trả ``ondemand_freq`` (nếu khác 0) hoặc ``previous_freq`` mà không đọc tải NPU [T1 DRV rknpu_devfreq.c:54-64]. Biến ``ondemand_freq`` chỉ được gán lúc khởi tạo [T1 DRV rknpu_devfreq.c:383, 699] hoặc khi người dùng ghi vào node debugfs ``/sys/kernel/debug/rknpu/freq`` [T1 DRV rknpu_debugger.c:229]. Việc đổi mức thực hiện qua ``npu_devfreq_target`` (gọi ``devfreq_recommended_opp``, ``rockchip_monitor_volt_adjust_lock`` và ``dev_pm_opp_set_rate``) [T1 DRV rknpu_devfreq.c:576-612].

Thứ tự đổi điện áp và tần số trong ``npu_opp_helper`` (đăng ký khi DTS có ``rknpu-supply`` và ``mem-supply``) [T1 DRV rknpu_devfreq.c:465-573]:

.. list-table::
   :header-rows: 1
   :widths: 16 84

   * - Hướng
     - Các bước thực thi và khôi phục lỗi
   * - Tăng
     - "Scaling up? Scale voltage before frequency" [T1 DRV rknpu_devfreq.c:501]: đặt ``mem_reg``, ``vdd_reg``, ``rockchip_set_read_margin``, rồi ``clk_set_rate(clk, new_freq)``
   * - Giảm
     - "Scaling down? Scale voltage after frequency" [T1 DRV rknpu_devfreq.c:527]: đặt ``rockchip_set_read_margin``, ``clk_set_rate``, rồi hạ ``vdd_reg`` và ``mem_reg`` (có nhãn khôi phục ``restore_freq``, ``restore_rm``, ``restore_voltage`` nếu lỗi [T1 DRV rknpu_devfreq.c:559-571])

Khi tắt nguồn domain, driver hạ clock SCMI về ``POWER_DOWN_FREQ`` (``200000000`` Hz) [T1 DRV rknpu_devfreq.c:16, 754-755]. Khi đo hiệu năng thủ công từ userspace (driver từ 0.7.2 trở lên cần bật nguồn NPU trước khi đặt tần số, và từ 0.8.2 có thêm ``/sys/kernel/debug/rknpu/freq``) [T1 UG152 tr.73-74]:

.. code-block:: none

   echo userspace > /sys/class/devfreq/fdab0000.npu/governor
   echo 1000000000 > /sys/kernel/debug/clk/clk_npu_dsu0/clk_rate

3. Reset
========

TRM1 mô tả hai tín hiệu reset tương ứng hai miền clock AXI và AHB:

   "Correspond to the clock domain, there are two reset signals. Aresetn, the reset signal for AXI interface and every Calculate Core and Control Core. Hresetn is the AHB interface reset pin and which is synchronized to the AHB clock domain.
   All the two signals must be asserted for a minimum of 32 core clock cycles, using the slowest of the two clocks. Then two signals must be release at the same time." [T1 TRM1 tr.2052]

.. _bang-reset-cru-npu:

.. list-table:: Thanh ghi soft reset của NPU ("When high, reset relative logic") [T1 TRM1 tr.182-184]
   :header-rows: 1
   :widths: 30 14 56

   * - Thanh ghi
     - Trang
     - Bit
   * - ``CRU_SOFTRST_CON27`` (``0x0A6C``)
     - 182
     - 0 ``aresetn_rknn1``, 1 ``aresetn_rknn1_biu``, 2 ``hresetn_rknn1``, 3 ``hresetn_rknn1_biu``
   * - ``CRU_SOFTRST_CON28`` (``0x0A70``)
     - 182
     - tương tự cho ``rknn2``
   * - ``CRU_SOFTRST_CON29`` (``0x0A74``)
     - 182-183
     - ``aresetn_rknn_dsu0``, ``presetn_nputop_biu``, ``presetn_npu_timer``, ``resetn_nputimer0/1``, ``presetn_npu_wdt``, ``tresetn_npu_wdt``, ``presetn_npu_grf``
   * - ``CRU_SOFTRST_CON30`` (``0x0A78``)
     - 183-184
     - 6 ``aresetn_rknn0``, 7 ``aresetn_rknn0_biu``, 8 ``hresetn_rknn0``, 9 ``hresetn_rknn0_biu``, 2 ``hresetn_npu_cm0_biu``, 3 ``fresetn_npu_cm0_core`` (reset ``0x1``), 4 ``tresetn_npu_cm0_jtag``, 15 ``resetn_npu_pvtpll``

Kiến trúc reset toàn SoC (Fig. 2-2) tổng hợp các nguồn reset ``NPOR`` (power-on), ``soc_wdt_rstn`` (watchdog), ``soc_tsadc_rstn`` (TSADC), ``softrstn_req`` (``CRU_SOFTRST_CON``), ``glb_srstn_1`` (``0xfdb9``) và ``glb_srstn_2`` (``0xeca8``) [T1 TRM1 tr.30-31]:

.. _fig-clock-dvfs-reset-arch:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/clock-dvfs-reset/trm1-fig2-2-reset-architecture.png
   :align: center
   :alt: Sơ đồ kiến trúc reset của RK3588

   Kiến trúc reset (Reset Architecture Diagram). Nguồn: [T1 TRM1 tr.31, Fig. 2-2]

Trong DTS, node NPU khai báo sáu đường reset ``SRST_A_RKNN0..2`` (``srst_a0..a2``) và ``SRST_H_RKNN0..2`` (``srst_h0..h2``) [T1 DTS dòng 3469-3472], được lấy qua ``devm_reset_control_get_exclusive_by_index`` sau ``of_count_phandle_with_args`` [T1 DRV rknpu_reset.c:34-54]. Khi có ioctl ``RKNPU_ACT_RESET`` [T1 DRV rknpu_drv.c:420-421], job timeout [T1 DRV rknpu_job.c:714] hoặc lỗi [T1 DRV rknpu_job.c:604] (trừ khi tham số module ``bypass_soft_reset = 1`` [T1 DRV rknpu_drv.c:70-73]), hàm ``rknpu_soft_reset`` tuần tự khóa ``reset_lock``, chờ ``msleep(100)``, đánh thức ``job_done_wq``, assert đồng thời tất cả ``srsts[i]`` trong ``udelay(10)``, deassert đồng thời trong ``udelay(10)``, rồi detach và attach lại IOMMU domain [T1 DRV rknpu_reset.c:98-150]. Xem thêm :doc:`../03-toolchain-runtime/03-driver-rknpu-va-rknn-server` mục 3.4.

4. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 24 52 24

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Datasheet RK3588 không công bố tần số tối đa của NPU
     - Chỉ ba bản nháp cũ để trống. RK3588 V1.3 và RK3588S V1.7 công bố ``Max NPU frequency`` là 1000 MHz
     - [T1 DS V0.1 tr.31] [T1 DS V1.3 pdf 30] [T1 DS V1.7 tr.32]
   * - Số 1000000000 trong tài liệu RKNN là bảng mức của hãng
     - Đó là ví dụ đầu ra ``eval_perf`` và ví dụ lệnh. Bảng OPP đầy đủ nằm trong DTS của driver
     - [T1 UG232 tr.31] [T1 UG152 tr.73] [T1 DTS dòng 3534-3655]
   * - Governor ``rknpu_ondemand`` tự đổi tần theo tải
     - Hàm target không đọc tải, chỉ trả ``ondemand_freq`` hoặc ``previous_freq``
     - [T1 DRV rknpu_devfreq.c:54-64]
   * - Mỗi core có bộ chia tần số riêng vì có gate riêng
     - Có gate ``aclk``/``hclk`` riêng cho từng core, nhưng CRU chỉ có một mux/chia ``clk_rknn_dsu0`` dùng chung cho cả ba domain ``PD_NPUTOP/NPU1/NPU2``
     - [T1 TRM1 tr.82, tr.134] [T1 DTS dòng 3116-3149]
   * - Soft reset trong driver chỉ reset một core
     - Driver assert đồng thời cả sáu tín hiệu reset (A0-A2, H0-H2)
     - [T1 DRV rknpu_reset.c:98-150] [T1 DTS dòng 3469-3472]
   * - Hạ điện áp trước rồi mới hạ tần số
     - Driver 0.9.8 khi giảm sẽ hạ tần số trước rồi mới hạ điện áp, còn khi tăng sẽ nâng điện áp trước
     - [T1 DRV rknpu_devfreq.c:501] [T1 DRV rknpu_devfreq.c:527]

Nguồn
=====

.. list-table::
   :header-rows: 1
   :widths: 12 8 70 10

   * - Nhãn
     - Tier
     - Tệp
     - Số lần
   * - ``TRM1``
     - T1
     - :download:`rk3588_part1.pdf <../../../_assets/pdf/datasheet/trm/rk3588_part1.pdf>`
     - 20
   * - ``DS V1.7``
     - T1
     - :download:`Rockchip_RK3588S_Datasheet_V1.7.pdf <../../../_assets/pdf/datasheet/soc/Rockchip_RK3588S_Datasheet_V1.7.pdf>`
     - 6
   * - ``DS V1.3``
     - T1
     - :download:`Rockchip_RK3588_Datasheet_V1.3_20220328.pdf <../../../_assets/pdf/datasheet/soc/Rockchip_RK3588_Datasheet_V1.3_20220328.pdf>`
     - 5
   * - ``DS V0.1``
     - T1
     - :download:`02_RK3588_Datasheet_V0.1-20210727.pdf <../../../_assets/pdf/datasheet/soc/02_RK3588_Datasheet_V0.1-20210727.pdf>`
     - 4
   * - ``DS HYY``
     - T1
     - :download:`01_HYY_Rockchip_RK3588_Datasheet.pdf <../../../_assets/pdf/datasheet/soc/01_HYY_Rockchip_RK3588_Datasheet.pdf>` (Rev 1.1)
     - 1
   * - ``DS S1.3``
     - T1
     - :download:`Rockchip_RK3588S_Datasheet_V1.3_20220310.pdf <../../../_assets/pdf/datasheet/soc/Rockchip_RK3588S_Datasheet_V1.3_20220310.pdf>` (RK3588S V1.3)
     - 1
   * - ``UG152``
     - T1
     - :download:`02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf <../../../_assets/pdf/rknn/02_Rockchip_RKNPU_User_Guide_RKNN_API_V1.5.2_EN.pdf>`
     - 3
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf``
     - 2
   * - ``DRV``, ``DTS``
     - T1
     - ``3rdparty/rknpu-driver-0.9.8/`` (commit f6eedab0 theo SOURCE.txt). ``DTS`` là ``dts/rk3588s.dtsi``
     - 27 và 13
