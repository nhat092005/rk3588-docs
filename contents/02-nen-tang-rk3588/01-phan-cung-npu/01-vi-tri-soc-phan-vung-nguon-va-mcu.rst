:tocdepth: 1

**********************************
Vị trí SoC, phân vùng nguồn và MCU
**********************************

.. admonition:: Trang này trả lời

   - NPU nằm đâu trong SoC và nối vào bus nào?
   - NPU thuộc miền nguồn nào, bật tắt miền nguồn ra sao?
   - MCU đi kèm NPU là gì, nối với NPU thế nào?

.. admonition:: Tóm tắt

   - NPU có ba core RKNN, chạy ba core cùng nhau, hai core cùng nhau hoặc riêng lẻ [T1 TRM1 tr.1984].
   - Giao diện AHB dùng để cấu hình, giao diện AXI master dùng để lấy dữ liệu từ bộ nhớ gắn vào SoC AXI interconnect [T1 TRM1 tr.1985].
   - VD_NPU chứa ba power domain PD_NPUTOP, PD_NPU1, PD_NPU2 [T1 TRM1 tr.1091]. PD_NPU1 và PD_NPU2 lồng trong PD_NPUTOP [T1 TRM1 tr.1268].
   - Tắt một domain: gửi BIU idle request, ghi bit power down, đọc thanh ghi trạng thái cho tới khi xong [T1 TRM1 tr.1269].
   - Có ba MCU Cortex-M0 trong SoC. MCU của NPU (NPU_M0) có TCM 64KB, cache 16KB và 16 ngắt nối trực tiếp [T1 TRM1 tr.1276] [T1 TRM1 tr.1298].
   - Vai trò của NPU_M0 trong một job NPU: unknown.
   - TRM1 và TRM2 không chứa chuỗi "iommu". Phía DTS và driver có khai báo IOMMU cho NPU [T1 DTS 3478].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _vi-tri-cua-npu-trong-soc:

1. Vị trí NPU trong SoC
=======================

Một SoC gồm nhiều khối IP (CPU, GPU, NPU, bộ điều khiển DDR, ...) nối với nhau qua một mạng bus gọi là interconnect. Khối chủ động khởi tạo giao dịch đọc ghi là master, khối chỉ đáp ứng là slave. Phần này xác định NPU đóng vai gì trong mạng đó. (Đoạn này là giải thích nền, không phải câu của nguồn.)

1.1 Sơ đồ khối RK3588
---------------------

TRM1 không có sơ đồ khối của cả SoC. Chương 1 của TRM1 chỉ có các bảng address mapping, interrupt và DMAC. Sơ đồ khối nằm trong datasheet, sơ đồ interconnect nằm trong TRM2 (xem :doc:`06-duong-truyen-du-lieu-iommu-va-ddr`).

.. _fig-ds-v17-block-diagram:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/vi-tri-trong-soc-va-nguon-dien/ds-v17-fig1-1-block-diagram.png
   :align: center
   :alt: Sơ đồ khối RK3588S gồm MCU Cortex-M0, High Performance NPU và 1MB Share Memory

   Sơ đồ khối của datasheet RK3588S. Nguồn: [T1 DS V1.7 tr.17, Fig. 1-1]

Văn bản trích từ sơ đồ này có ba mục liên quan tới NPU:

   `MCU (Cortex-M0) x3` ... `High Performance NPU` ... `1MB Share Memory` [T1 DS V1.7 tr.17]

Mô tả của hãng về NPU:

   "The build-in NPU supports INT4/INT8/INT16/FP16 hybrid operation and computing power is up to 6TOPs." [T1 DS V1.7 tr.7]

..

   "Include triple NPU core, and support triple core co-work, dual core co-work, and work independently" [T1 DS V1.7 tr.11]

TRM1 chương 36 nói cùng ý: "RKNN is the process unit which is dedicated to neural network." [T1 TRM1 tr.1984]

Bảng sau gom các khối thuộc NPU trong bản đồ địa chỉ (Table 1-1) và bảng ngắt (Table 1-3) của TRM1.

.. list-table::
   :header-rows: 1
   :widths: 28 20 14 38

   * - Khối
     - Địa chỉ đầu
     - Kích thước
     - Nguồn
   * - RKNN C0
     - ``FDAB0000``
     - 64KB
     - [T1 TRM1 tr.18]
   * - RKNN C1
     - ``FDAC0000``
     - 64KB
     - [T1 TRM1 tr.18]
   * - RKNN C2
     - ``FDAD0000``
     - 64KB
     - [T1 TRM1 tr.18]
   * - NPU_GRF
     - ``FD5A2000``
     - 8KB
     - [T1 TRM1 tr.17]
   * - PVTM_NPU
     - ``FDAF0000``
     - 32KB
     - [T1 TRM1 tr.18]
   * - WDT_NPU
     - ``FDAF8000``
     - 32KB
     - [T1 TRM1 tr.18]
   * - TIMER_NPU (2 kênh)
     - ``FDB00000``
     - 32KB
     - [T1 TRM1 tr.19]
   * - MAILBOX2 (MCU_NPU)
     - ``FECE0000``
     - 64KB
     - [T1 TRM1 tr.19]
   * - MCU_TCM, MCU_CACHE
     - ``F6F00000``, ``F6F10000``
     - 64KB, 64KB
     - [T1 TRM1 tr.16]

Ngắt của ba core nằm ở cột "High level" của Table 1-3 (tiêu đề bảng ở tr.20).

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - ID
     - Nguồn ngắt
     - Nguồn
   * - 142, 143, 144
     - ``irq_rknn_c0``, ``irq_rknn_c1``, ``irq_rknn_c2``
     - [T1 TRM1 tr.24]
   * - 388
     - ``irq_npu_pvtm``
     - [T1 TRM1 tr.25]
   * - 390
     - ``irq_npumcu_cache``
     - [T1 TRM1 tr.25]
   * - 436, 437
     - ``irq_timer0_npu``, ``irq_timer1_npu``
     - [T1 TRM1 tr.26]
   * - 438
     - ``irq_wdt_npu``
     - [T1 TRM1 tr.26]

Trong DTS, node ``rknpu`` dùng ba vùng ``reg`` 0xfdab0000, 0xfdac0000, 0xfdad0000 kích thước 0x10000 [T1 DTS 3452-3454] và ba ngắt tên ``npu0_irq``, ``npu1_irq``, ``npu2_irq`` [T1 DTS 3458]. Các ngắt này dùng ``GIC_SPI 110``, ``111``, ``112`` [T1 DTS 3455-3457]. Suy ra: 110, 111, 112 cộng 32 bằng 142, 143, 144 của Table 1-3. Nguồn không nói phép cộng này. Node ``rknpu`` ở trạng thái ``disabled`` trong file dtsi, được bật ở file board mà repo không có [T1 DTS 3479].

1.2 NPU nối với bus nào
-----------------------

NPU có hai loại giao diện, mỗi loại một nhiệm vụ.

   "AHB interface used for configuration only support single" [T1 TRM1 tr.1984]

   "AXI interface used to fetch data from memory" [T1 TRM1 tr.1984]

..

   "The AXI master interface is used to fetch data from memory that is attached to the Soc AXI interconnect." [T1 TRM1 tr.1985]

   "The AHB slave interface is used to access the registers for configuration, debug and test." [T1 TRM1 tr.1985]

Hai giao diện này có hai domain clock tương ứng:

   "RKNN has two clock domains, one is AHB clock, the other is AXI clock." [T1 TRM1 tr.2052]

Ngoài ra, khối Register File Fetch Unit đọc cấu hình thanh ghi từ bộ nhớ hệ thống qua AXI: "Register File Fetch Unit fetch register configuration from external system memory through AXI interface." [T1 TRM1 tr.1986] Nghĩa là AXI của NPU chở cả dữ liệu tensor lẫn cấu hình thanh ghi (suy ra từ hai câu trích).

Phía interconnect, TRM2 mô tả bốn DDR scheduler giữa các master và bộ điều khiển DDR:

   "Four embedded DDR schedulers for transaction reorder to maximum DDR efficiency" [T1 TRM2 tr.16]

Table 1-3 của TRM2 (tr.19) liệt kê NPU là master qua các cổng NPU1, NPU0_MRO, NPU0_MWR, NPU2 và MCU_NPU [T1 TRM2 tr.19]. Cột QoS, mã MID và sơ đồ interconnect thuộc trang :doc:`06-duong-truyen-du-lieu-iommu-va-ddr`.

**NPU có đi qua IOMMU không.** Mức TRM: không tìm thấy. Chuỗi "iommu" có 0 kết quả trong toàn bộ TRM1 và TRM2. Bảng ngắt Table 1-3 không có dòng MMU của NPU. Instance MMU600 trong TRM1 chỉ có hai: "There are two MMU600 instances in RK3588, MMU600_PCIE and MMU600_PHP respectively." [T1 TRM1 tr.1273] Mức DTS và driver có khai báo:

.. list-table::
   :header-rows: 1
   :widths: 60 40

   * - Điều DTS và driver ghi
     - Nguồn
   * - Node ``rknpu`` có ``iommus = <&rknpu_mmu>``
     - [T1 DTS 3478]
   * - ``rknpu_mmu`` có ``compatible = "rockchip,iommu-v2"``
     - [T1 DTS 3712-3728]
   * - Tên ngắt ``npu0_mmu``, ``npu1_mmu``, ``npu2_mmu``
     - [T1 DTS 3721]
   * - Driver kiểm phandle ``iommus`` rồi kiểm node có khả dụng
     - [T1 DRV rknpu_drv.c:794-816]
   * - Nếu bật thì ``iommu_group_get``, nếu không thì ``of_reserved_mem_device_init``
     - [T1 DRV rknpu_drv.c:1294-1306]
   * - ``.dma_mask = DMA_BIT_MASK(40)`` trong cấu hình RK3588
     - [T1 DRV rknpu_drv.c:186]
   * - ``RKNPU_MAX_IOMMU_DOMAIN_NUM`` bằng 16
     - [T1 DRV include/rknpu_drv.h:56]
   * - ioctl ``RKNPU_GET_IOMMU_DOMAIN_ID`` bằng 24, ``RKNPU_SET_IOMMU_DOMAIN_ID`` bằng 25
     - [T1 DRV include/rknpu_ioctl.h:135-136]

UG232 mô tả tham số ``iommu_domain_id`` là chỉ số của một không gian địa chỉ IOMMU, kích thước mỗi không gian là 4GB [T1 UG232 tr.45]. Driver 0.9.8 không chứa hằng 4GB, 4G hay SZ_4G (đã tìm ``rknpu_*.c`` và ``include/*.h``), nên liên hệ giữa nút IOMMU trong DTS và con số 4GB này chỉ là suy ra, không phải câu của nguồn.

2. Power domain
===============

Power domain là vùng mạch có thể cắt nguồn riêng để tiết kiệm điện khi không dùng. Voltage domain là vùng mạch dùng chung một đường cấp điện áp, có thể chứa nhiều power domain. Hình 7-2 của TRM1 ghi chú "VD_* : voltage domain, PD_* : power domain" [T1 TRM1 tr.1092].

2.1 Miền nguồn của NPU
----------------------

   "Support multi voltage domains: VD_BIGCORE0, VD_BIGCORE1, VD_LITDSU, VD_GPU, VD_NPU, VD_VCODEC, VD_DDR01, VD_DDR23, VD_LOGIC, VD_PMU" [T1 TRM1 tr.1091]

..

   "Support multi power domains in VD_NPU: PD_NPUTOP, PD_NPU1, PD_NPU2" [T1 TRM1 tr.1091]

.. _fig-trm1-voltage-power-domain:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/vi-tri-trong-soc-va-nguon-dien/trm1-fig7-2-voltage-power-domain.png
   :align: center
   :alt: Phân vùng voltage domain và power domain của RK3588, VD_NPU chứa PD_NPUTOP, PD_NPU1, PD_NPU2

   Phân vùng voltage domain và power domain của RK3588. VD_NPU chứa PD_NPUTOP, PD_NPU2 và PD_NPU1. Nguồn: [T1 TRM1 tr.1092, Fig. 7-2]

Bảng sau liệt kê thành phần của từng power domain (cột Description của Table 7-1, hàng VD_NPU ở tr.1093).

.. _fig-trm1-table-vd-npu:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/vi-tri-trong-soc-va-nguon-dien/trm1-table7-1-vd-npu.png
   :align: center
   :alt: Hàng VD_NPU của Table 7-1, liệt kê thành phần của PD_NPUTOP, PD_NPU1 và PD_NPU2

   Hàng VD_NPU của bảng tóm tắt voltage domain và power domain. Nguồn: [T1 TRM1 tr.1093, Table 7-1]

.. list-table::
   :header-rows: 1
   :widths: 20 55 25

   * - Power domain
     - Thành phần
     - Nguồn
   * - PD_NPUTOP
     - BIU_NPUTOP, MCU_NPU, PVTM_NPU, PVTPLL_NPU, WDT_NPU, TIMER_NPU, RKNN_CORE0 (7 mục)
     - [T1 TRM1 tr.1093]
   * - PD_NPU1
     - BIU_NPU1, RKNN_CORE1
     - [T1 TRM1 tr.1093]
   * - PD_NPU2
     - BIU_NPU2, RKNN_CORE2
     - [T1 TRM1 tr.1093]

Hai điều cần để ý trong bảng này. Một, core 0 chung domain với MCU_NPU, còn core 1 và core 2 mỗi core một domain. Hai, PD_NPU1 và PD_NPU2 không độc lập hoàn toàn với PD_NPUTOP. Table 7-2 của TRM1 xếp chúng vào nhóm nested power domain, với PD_NPUTOP là external và PD_NPU1, PD_NPU2 là internal [T1 TRM1 tr.1268]. Quy tắc thứ tự:

   "external power domain should not be power down before internal power domain power down, external power domain should be power up before internal power domain power up." [T1 TRM1 tr.1268]

..

   "Incorrect power order may cause power leakage." [T1 TRM1 tr.1269]

DTS lồng domain đúng như vậy: ``power-domain@RK3588_PD_NPU`` chứa ``RK3588_PD_NPUTOP``, và ``RK3588_PD_NPUTOP`` chứa ``RK3588_PD_NPU1`` cùng ``RK3588_PD_NPU2`` [T1 DTS 3116-3148]. Mỗi domain gắn một hoặc nhiều QoS: PD_NPUTOP với ``qos_npu0_mwr``, ``qos_npu0_mro``, ``qos_mcu_npu`` [T1 DTS 3130-3132], PD_NPU1 với ``qos_npu1`` [T1 DTS 3139], PD_NPU2 với ``qos_npu2`` [T1 DTS 3146]. Node ``rknpu`` tham chiếu cả ba domain: ``power-domains = <&power RK3588_PD_NPUTOP>, <&power RK3588_PD_NPU1>, <&power RK3588_PD_NPU2>`` và ``power-domain-names = "npu0", "npu1", "npu2"`` [T1 DTS 3473-3476].

Cấp điện áp ngoài chip: datasheet ghi VD_NPU là "One isolated voltage domain to support DVFS" [T1 DS V1.7 tr.11]. Mức điện áp khuyến nghị:

.. list-table::
   :header-rows: 1
   :widths: 34 12 12 12 30

   * - Tham số
     - Min
     - Typ
     - Max
     - Nguồn
   * - ``VDD_NPU``
     - 0.55 V
     - 0.75 V
     - 0.95 V
     - [T1 DS V1.7 tr.31] [T1 DS V1.3 pdf 29]
   * - ``VDD_NPU_MEM``
     - 0.675 V
     - 0.75 V
     - 0.95 V
     - [T1 DS V1.7 tr.31] [T1 DS V1.3 pdf 29]

Giới hạn tuyệt đối của cả hai chân là -0.3 V đến 1.1 V [T1 DS V1.7 tr.30]. Chi tiết tần số tối đa và các mức DVFS thuộc trang :doc:`04-xung-nhip-dvfs-va-reset`.

2.2 Bật tắt miền nguồn
----------------------

PMU (Power Management Unit) điều khiển nguồn theo hai chế độ:

   "When operating at software power mode, that means software can manage power sources directly by accessing PMU registers." [T1 TRM1 tr.1098]

..

   "When operating at hardware power mode, software manages power sources indirectly through FSM (Finite States Machine) in PMU and those settings always not take effect immediately." [T1 TRM1 tr.1098]

TRM1 không nói riêng gì về NPU trong hai chế độ công suất thấp "Power mode 0" và "Power mode 1" [T1 TRM1 tr.1098].

**Quy trình tắt bằng phần mềm.** TRM1 mục 7.5.3 mô tả các bước sau (bước 2 nêu việc đọc thanh ghi trạng thái BIU idle):

.. list-table::
   :header-rows: 1
   :widths: 10 60 30

   * - Bước
     - Nội dung
     - Nguồn
   * - 1
     - Gửi BIU idle request nếu domain có giao diện BIU, bằng cách đặt bit tương ứng trong ``PMU_IDLE_SFTCON0/1/2``
     - [T1 TRM1 tr.1269]
   * - 2
     - Đọc ``PMU_IDLE_ACK_STS0/1`` để chờ trạng thái BIU idle acknowledge tương ứng, và ``PMU_IDLE_STS0/1`` (trích rút gọn: "(2) Query PMU_IDLE_ACK_STS0/1 register to wait for the corresponding BIU idle acknowledge state; Query PMU_IDLE_STS0/1 register...")
     - [T1 TRM1 tr.1269]
   * - 3
     - Cho phép power down domain, đặt bit tương ứng bằng 1 trong ``PMU_PWR_GATE_SFTCON0/1/2``
     - [T1 TRM1 tr.1269]
   * - 4
     - Đọc ``PMU_PWR_GATE_STS0/1`` để chờ domain tắt xong
     - [T1 TRM1 tr.1269]

Quy trình bật lại (nhánh "Software power up without repair flow") có bước 1: "Enable power up to the specific power domain by setting corresponding bit to 0 in PMU_PWR_GATE_SFTCON0/1/2 register" [T1 TRM1 tr.1269]. Tên ``PMU_IDLE_SFTCON0/1/2`` ở mục 7.5.3 khác tên ``PMU_BIU_IDLE_SFTCON0/1`` ở phần mô tả thanh ghi. Tài liệu không nhất quán, bảng dưới dùng tên trong phần mô tả thanh ghi.

**Thanh ghi PMU liên quan NPU.** Offset tính từ Operational Base.

.. list-table::
   :header-rows: 1
   :widths: 22 10 48 20

   * - Thanh ghi
     - Offset
     - Bit cho NPU
     - Nguồn
   * - ``PMU_BIU_IDLE_SFTCON0``
     - 0x810C
     - bit 3 ``idle_req_npu2_sftena``, bit 2 ``idle_req_npu1_sftena``, bit 1 ``idle_req_nputop_sftena`` (reset 0x0)
     - [T1 TRM1 tr.1180]
   * - ``PMU_BIU_IDLE_STS0``
     - 0x8120
     - bit 3 ``idle_npu2``, bit 2 ``idle_npu1``, bit 1 ``idle_nputop`` (chỉ đọc, "1'b1: Idle")
     - [T1 TRM1 tr.1187]
   * - ``PMU_PWR_GATE_SFTCON0``
     - 0x814C
     - bit 5 ``pd_npu2_dwn_sftena``, bit 4 ``pd_npu1_dwn_sftena``, bit 3 ``pd_nputop_dwn_sftena`` (reset 0x1). Bit 1 ``pd_npu_dwn_sftena``: "Enable power down VD_NPU by software." (reset 0x0)
     - [T1 TRM1 tr.1195] [T1 TRM1 tr.1196]
   * - ``PMU_VOL_GATE_CON0``
     - 0x8158
     - bit 1 ``vd_npu_off_ena``: "Enable power off VD_NPU." (reset 0x0)
     - [T1 TRM1 tr.1198]
   * - ``PMU_PWR_GATE_STS0``
     - 0x8180
     - bit 5 ``pd_npu2_dwn_stat``, bit 4 ``pd_npu1_dwn_stat``, bit 3 ``pd_nputop_dwn_stat`` (chỉ đọc, reset 0x1). Bit 1 ``pd_npu_dwn_stat``: "The power state of VD_NPU." "1'b0: Power up / 1'b1: Power down"
     - [T1 TRM1 tr.1206] [T1 TRM1 tr.1207]
   * - ``PMU_VOL_GATE_FAST_CON``
     - 0x818C
     - bit 1 ``vd_npu_fast_ena`` (reset 0x0)
     - [T1 TRM1 tr.1208]
   * - ``PMU_NPU_PWRUP_CNT``, ``PMU_NPU_PWRDN_CNT``
     - 0x8198, 0x819C
     - bit [19:0] đọc ghi, reset 0xfffff
     - [T1 TRM1 tr.1208] [T1 TRM1 tr.1209]
   * - ``PMU_MEM_PWR_GATE_SFTCON0``
     - unknown
     - "Enable power down PD_NPU2's / PD_NPU1's / PD_NPUTOP's memory by software."
     - [T1 TRM1 tr.1209] [T1 TRM1 tr.1210]

Offset của ``PMU_MEM_PWR_GATE_SFTCON0`` là ``0x81A0`` [T1 TRM1 tr.1209].

Hai điểm bổ sung từ TRM1:

   "When asserted, it means that VD_NPU will power up completely if VD_NPU power up count from npu_pwrup_cnt (defined in PMU_NPU_PWRUP_CNT) to zero when VD_NPU power up request active" [T1 TRM1 tr.1208]

..

   "In RK3588, memory powers are independent of logic powers in the power domain." [T1 TRM1 tr.1270]

Điện áp ngoài được cấp bởi PMIC riêng cho từng voltage domain: "You can communicate with external PMIC (Power Management Integrated Circuits) through I2C interface, or through IO interface." [T1 TRM1 tr.1270]

**Phía driver.** Driver ``rknpu`` không ghi thẳng thanh ghi PMU. Nó gắn từng domain vào kernel rồi dùng runtime PM:

.. list-table::
   :header-rows: 1
   :widths: 22 56 22

   * - Việc
     - Cách làm
     - Nguồn
   * - Gắn domain
     - Nếu ``power-domains`` có hơn một phần tử thì ``dev_pm_domain_attach_by_name`` với ``"npu0"``, ``"npu1"``, ``"npu2"``. ``"npu2"`` chỉ khi ``num_irqs > 2``. Đặt ``multiple_domains = true``
     - [T1 DRV rknpu_drv.c:1442-1456]
   * - Bật nguồn
     - ``rknpu_power_on`` gọi ``pm_runtime_resume_and_get`` (kernel cũ dùng ``pm_runtime_get_sync``) lần lượt cho npu0, npu1, npu2
     - [T1 DRV rknpu_drv.c:904-980]
   * - Tắt nguồn
     - ``rknpu_power_off`` gọi ``pm_runtime_put_sync`` theo thứ tự npu2, npu1, npu0
     - [T1 DRV rknpu_drv.c:1046-1051]
   * - Trì hoãn tắt
     - Mặc định ``power_put_delay = 3000`` (comment "set default power put delay to 3s"), workqueue ``rknpu_power_off_wq`` và biến đếm ``power_refcount``
     - [T1 DRV rknpu_drv.c:1466-1467] [T1 DRV rknpu_drv.c:375-386]

Suy ra: thứ tự bật npu0 trước và tắt npu0 sau cùng khớp quy tắc lồng của Table 7-2 (PD_NPUTOP phải bật trước và tắt sau). Driver không có comment nói điều này.

3. MCU đi kèm
=============

3.1 MCU là gì
-------------

MCU (microcontroller) là một CPU nhỏ, có bộ nhớ riêng, thường dùng cho việc phụ trợ để CPU chính khỏi bị chiếm. Đoạn này là giải thích nền. Nguồn nói về cấu hình của MCU như sau:

   "There are three MCU subsystem in RK3588, PMU_M0, NPU_M0 and DDR_M0 respectively." [T1 TRM1 tr.1276]

..

   "The MCU Subsystem embedded one MCU processor(Cortex-M0,r0p0-03rel0), a 16KB unified I/D cache, a tightly-coupled memory(TCM) and interrupt multiplexer(INTMUX)." [T1 TRM1 tr.1276]

TCM (tightly-coupled memory) là bộ nhớ gắn thẳng vào lõi MCU, truy cập không qua cache. Cấu hình ba MCU (Table 9-1):

.. list-table::
   :header-rows: 1
   :widths: 25 25 25 25

   * - Thuộc tính
     - PMU_M0
     - NPU_M0
     - DDR_M0
   * - TCM
     - 16KB
     - 64KB
     - 32KB
   * - CACHE
     - 16KB
     - 16KB
     - NA
   * - IRQ_NUM
     - 32
     - 16
     - 8
   * - INTMUX
     - YES
     - NA
     - YES

Nguồn của bảng: [T1 TRM1 tr.1276]. Datasheet nói ngắn hơn: "MCU in VD_NPU integrate 16KB Cache and 64KB TCM" [T1 DS V1.7 tr.8]. Về bus, MCU subsystem "Support one 128bit AHB-Lite bus master interface to SoC interconnect" [T1 TRM1 tr.1276].

Câu datasheet "all IRQ lines connected to GIC for CPU also connect to MCU in VD_PMU(PMU_M0) and PD_CENTER(DDR_M0)" chỉ nêu PMU_M0 và DDR_M0 [T1 DS V1.7 tr.8]. NPU_M0 có INTMUX là NA và chỉ có 16 IRQ theo Table 9-1.

.. _fig-trm1-npu-m0-subsystem:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/vi-tri-trong-soc-va-nguon-dien/trm1-fig9-2-npu-m0-subsystem.png
   :align: center
   :alt: Sơ đồ khối NPU_M0 gồm MCU, TCM, I/D-Cache, Address Decode, Interconnect và Int_in[15:0]

   Sơ đồ khối của NPU_M0 subsystem: MCU (DBG, Serial Wire), TCM, I/D-Cache, Address Decode (Data_s, Config_s), Interconnect và ``Int_in[15:0]``. Nguồn: [T1 TRM1 tr.1277, Fig. 9-2, tên hình in ở đầu tr.1278]

3.2 Nối với NPU thế nào
-----------------------

**Ngắt.** Mười sáu ngắt nối trực tiếp vào NPU_M0, không qua INTMUX:

   "The 16 interrupts are connected to NPU_M0 without INTMUX directly." [T1 TRM1 tr.1298]

.. list-table::
   :header-rows: 1
   :widths: 15 35 15 35

   * - IRQ ID
     - Nguồn
     - IRQ ID
     - Nguồn
   * - 0
     - Timer0_NPU
     - 5
     - C1_RKNN
   * - 1
     - Timer1_NPU
     - 6
     - C2_RKNN
   * - 2
     - PVTM_NPU
     - 7
     - CACHE_NPU
   * - 3
     - WDT_NPU
     - 8 đến 11
     - MAILBOX2_AP
   * - 4
     - C0_RKNN
     - 12 đến 15
     - MAILBOX2_BB

Nguồn của bảng: [T1 TRM1 tr.1298, Table 9-8]. Các ngắt C0_RKNN, C1_RKNN, C2_RKNN của ba core đi tới NPU_M0. Đây là dữ kiện về đường nối, không phải bằng chứng MCU xử lý chúng trong job.

**Bộ nhớ, remap và cache.** Vùng địa chỉ của MCU có bảng remap dùng các thanh ghi ``bus_sgrf_mcu_con0..3``, và "these remap operation could not take effect until the MCU soft reset." [T1 TRM1 tr.1297] Cache không tự chạy sau reset: "The Cache is bypassed after reset and need to be initialized by the MCU." [T1 TRM1 tr.1298]

**Mailbox, JTAG, clock.**

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Mục
     - Điều TRM1 ghi
     - Nguồn
   * - MAILBOX2
     - "MAILBOX2 is suggested to use for communication between MCU in PD_NPU and CPU."
     - [T1 TRM1 tr.1402]
   * - Chọn JTAG
     - Trường ``mcujtag_sel`` bit [11:10], giá trị "2'b11: JTAG IO select NPU MCU"
     - [T1 TRM1 tr.724]
   * - Clock gate riêng
     - ``CRU_GATE_CON30`` (offset 0x0878): ``clk_npu_cm0_rtc_en`` bit 5, ``fclk_npu_cm0_core_en`` bit 3, ``hclk_npu_cm0_biu_en`` bit 2 ("When high, disable clock")
     - [T1 TRM1 tr.136]

Trong DTS, PD_NPUTOP có ``<&cru HCLK_NPU_CM0_ROOT>`` [T1 DTS 3129]. Tên thanh ghi chứa trường ``mcujtag_sel`` nằm ở trang trước tr.724 và chưa xác định.

**Cùng domain nguồn với core 0.** MCU_NPU nằm trong PD_NPUTOP cùng RKNN_CORE0 [T1 TRM1 tr.1093]. TRM2 liệt kê MCU_NPU là một master riêng trên interconnect [T1 TRM2 tr.19], còn DTS gộp ``qos_mcu_npu`` vào ``pm_qos`` của PD_NPUTOP [T1 DTS 3130-3132]. Suy ra: khi PD_NPUTOP tắt, MCU_NPU và core 0 cùng mất nguồn.

3.3 Vai trò trong một job: unknown
----------------------------------

Không có nguồn T1 nào mô tả firmware chạy trên NPU_M0, việc phân task của nó, hay quan hệ của nó với các ioctl ``RKNPU_*`` của driver. Các dữ kiện ở 3.1 và 3.2 chỉ cho biết MCU nhận ngắt từ ba core RKNN, có cache, TCM, mailbox, và là master trên interconnect. Vì vậy trang này không viết rằng MCU điều phối job.

unknown. Đã tìm ở:

- TRM1 toàn văn, từ khóa: ``MCU.*NPU``, ``NPU.*MCU``, ``NPU_M0``, ``npumcu``, ``CM0`` (chỉ ra các mục 3.1 và 3.2 cùng clock gate CM0).
- TRM1 chương 36, từ khóa: ``MCU`` (không có).
- TRM2 toàn văn, cùng từ khóa (chỉ có ``MCU_NPU`` ở Table 1-3).
- Datasheet V1.7 và V1.3, từ khóa: ``NPU.*MCU``, ``firmware`` (chỉ có dòng "MCU in VD_NPU integrate 16KB Cache and 64KB TCM").
- Driver ``*.c`` và ``include/*.h``, từ khóa: ``cm0``, ``npu_m0``, ``firmware``, ``mcu`` (không có). DTS chỉ có ``qos_mcu_npu``.

Từ khóa gợi ý để tìm tiếp: "RK3588 NPU MCU firmware job scheduling", "rknpu cm0 mailbox".

4. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 24 52 24

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - TRM chứng minh NPU đi qua IOMMU
     - TRM1 và TRM2 không chứa chuỗi "iommu". Khai báo IOMMU chỉ có ở DTS và driver.
     - [T1 TRM1 tr.1273] [T1 DTS 3478]
   * - Ba core nằm chung một power domain
     - Ba core nằm ở ba domain: RKNN_CORE0 trong PD_NPUTOP, RKNN_CORE1 trong PD_NPU1, RKNN_CORE2 trong PD_NPU2.
     - [T1 TRM1 tr.1093]
   * - PD_NPU1, PD_NPU2 bật tắt độc lập với PD_NPUTOP
     - Chúng là internal của PD_NPUTOP. Domain ngoài không được tắt trước domain trong và phải bật trước. Sai thứ tự có thể gây power leakage.
     - [T1 TRM1 tr.1268] [T1 TRM1 tr.1269]
   * - Mọi MCU của SoC đều có INTMUX
     - NPU_M0 ghi INTMUX là NA và có 16 IRQ nối trực tiếp.
     - [T1 TRM1 tr.1276] [T1 TRM1 tr.1298]
   * - MCU của NPU điều phối job NPU
     - Không nguồn T1 nào mô tả. Mục 3.3 giữ unknown.
     - [T1 TRM1 tr.1276]
   * - Chương 36 nói NPU truy cập DDR
     - Chương 36 chỉ nói "memory that is attached to the Soc AXI interconnect", không nhắc DDR.
     - [T1 TRM1 tr.1985]
   * - Bật tắt power domain chỉ là ghi một bit
     - Phải gửi BIU idle request trước, rồi ghi bit power down, rồi chờ bit trạng thái.
     - [T1 TRM1 tr.1269]

Nguồn
=====

Các nhãn nguồn dùng trong trang này (tier, tệp, số lần trích).

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
     - 86
   * - ``TRM2``
     - T1
     - :download:`rk3588_part2.pdf <../../../_assets/pdf/datasheet/trm/rk3588_part2.pdf>`
     - 3
   * - ``DS V1.7``
     - T1
     - :download:`Rockchip_RK3588S_Datasheet_V1.7.pdf <../../../_assets/pdf/datasheet/soc/Rockchip_RK3588S_Datasheet_V1.7.pdf>`
     - 10
   * - ``DS V1.3``
     - T1
     - :download:`Rockchip_RK3588_Datasheet_V1.3_20220328.pdf <../../../_assets/pdf/datasheet/soc/Rockchip_RK3588_Datasheet_V1.3_20220328.pdf>`
     - 2
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 1
   * - ``DRV``
     - T1
     - ``3rdparty/rknpu-driver-0.9.8/`` (commit f6eedab0 theo SOURCE.txt)
     - 10
   * - ``DTS``
     - T1
     - ``3rdparty/rknpu-driver-0.9.8/dts/rk3588s.dtsi``
     - 16

Số trang của TRM1, TRM2 và DS V1.7 là số trang in, bằng số trang PDF. DS V1.3 không có số trang in nên dùng ``pdf N`` là số trang PDF. DRV và DTS dẫn theo ``tệp:dòng``.
