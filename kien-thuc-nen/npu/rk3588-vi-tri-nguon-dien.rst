:tocdepth: 1

****************************
RK3588: vị trí và nguồn điện
****************************

.. admonition:: Trang này trả lời

   - NPU nối với phần còn lại của SoC bằng giao diện nào, dùng bộ nhớ nào?
   - NPU nằm trong miền nguồn nào, và có bộ điều khiển phụ không?

.. admonition:: Tóm tắt

   - NPU dùng AHB để cấu hình và AXI master để lấy dữ liệu từ bộ nhớ gắn vào SoC AXI interconnect [T1 TRM1 tr.1985].
   - Chương 36 không nói NPU có qua IOMMU khi truy cập DDR hay không, và quan hệ với "4GB" của UG232 tr.45 là `unknown`.
   - Đóng một phần bằng DTS, driver và T3: node `rknpu` có `iommus = <&rknpu_mmu>`, và board báo "rknpu iommu is enabled, using iommu mode".
   - Ba NPU core thuộc ba power domain PD_NPUTOP, PD_NPU1, PD_NPU2, và core 0 chung domain với MCU_NPU [T1 TRM1 tr.1091, tr.1093].
   - MCU trong VD_NPU có 16KB Cache và 64KB TCM [T1 DS tr.8], nhưng vai trò của MCU với một job NPU là `unknown`.

.. _21-vị-trí-của-npu-trong-soc:

Vị trí của NPU trong SoC
========================

**Câu hỏi:** NPU nối với phần còn lại của SoC bằng giao diện nào, dùng bộ nhớ nào?

**Nguồn nói gì**

   "AHB interface used for configuration only support single" [T1 TRM1 tr.1984]

..

   "The AHB slave interface is used to access the registers for configuration, debug and test." [T1 TRM1 tr.1985]

   "The AXI master interface is used to fetch data from memory that is attached to the Soc AXI interconnect." [T1 TRM1 tr.1985]

..

   "Four embedded DDR schedulers for transaction reorder to maximum DDR efficiency" [T1 TRM2 tr.16]

Trong TRM Part2 Table 1-3 (tr.19), danh sách master của interconnect có các dòng ``NPU1``, ``NPU0_MRO``, ``NPU0_MWR``, ``NPU2`` và ``MCU_NPU``. Bảng này cũng có cột QoS.

Địa chỉ và ngắt của ba NPU core (đối chiếu từ bảng):

.. list-table::
   :header-rows: 1

   * - Core
     - Địa chỉ nền (TRM1 tr.18)
     - Ngắt (TRM1 tr.24)
   * - NPU core 0 (TRM: RKNN C0)
     - ``FDAB0000``, 64KB
     - 142 ``irq_rknn_c0``
   * - NPU core 1 (TRM: RKNN C1)
     - ``FDAC0000``, 64KB
     - 143 ``irq_rknn_c1``
   * - NPU core 2 (TRM: RKNN C2)
     - ``FDAD0000``, 64KB
     - 144 ``irq_rknn_c2``

|TRM2 Fig 1-1| *Hình 2.1. Sơ đồ interconnect: NPU là một master, bốn DDR scheduler nối tới DDRCTL0 đến DDRCTL3. Nguồn: [T1 TRM2 tr.16, Fig. 1-1]*

**Ý chính**

- Giao diện cấu hình là AHB, giao diện dữ liệu là AXI master (TRM1 tr.1985). Tổng hợp của file này: NPU lấy dữ liệu từ bộ nhớ hệ thống qua interconnect. Chương 36 chỉ liệt kê buffer 384KBx3 bên trong core (xem 2.6). MCU của NPU có TCM và cache riêng (2.2) và NPU còn dùng SRAM hệ thống (2.7).
- Chương 36 chỉ nói "memory attached to the SoC AXI interconnect", không nói "DDR". Liên kết với bộ lập lịch DDR đến từ TRM Part2 Ch.1.

**Giới hạn.** Ở mức phần cứng, TRM Chương 36 không nói NPU có đi qua IOMMU khi truy cập DDR hay không. Ở mức SDK, User Guide V2.3.2 tr.45 (Matmul API, tham số ``iommu_domain_id``) ghi "the size of each IOMMU address space is 4GB", nên bộ nhớ NPU nằm trong các miền IOMMU 4GB, quan hệ với phần cứng trong TRM là ``unknown``. Loại DRAM và băng thông thực của board xem :doc:`Bộ nhớ và hiệu năng </kien-thuc-nen/bo-nho-hieu-nang/index>`. Đóng một phần (T1 DRV, DTS. T3): node ``rknpu`` có ``iommus = <&rknpu_mmu>`` (DTS dòng 3478, commit f6eedab0, lưu tại ``3rdparty/rknpu-driver-0.9.8/dts/rk3588s.dtsi``).``rknpu_mmu`` có compatible ``rockchip,iommu-v2`` (DTS dòng 3712-3728). Driver kiểm ``iommus`` và trạng thái node (``rknpu_drv.c:794-816``). Nếu bật thì ``iommu_group_get``, ngược lại dùng reserved memory (``rknpu_drv.c:1294-1307``). ``dma_mask`` của cấu hình RK3588 là ``DMA_BIT_MASK(40)`` (``rknpu_drv.c:186``). Có ``RKNPU_MAX_IOMMU_DOMAIN_NUM`` = 16 (``rknpu_drv.h:56``) và ioctl ``RKNPU_GET_IOMMU_DOMAIN_ID``, ``RKNPU_SET_IOMMU_DOMAIN_ID`` (``rknpu_ioctl.h:135-136``). Board: dmesg ``RKNPU: rknpu iommu is enabled, using iommu mode`` (T3, đọc 2026-10-10). Hằng "4GB" của UG232 tr.45 không tìm thấy trong DRV (đã grep ``4GB``, ``4G``, ``SZ_4G``).

--------------

.. _22-power-domain-và-mcu-đi-kèm:

Power domain và MCU đi kèm
==========================

**Câu hỏi:** NPU nằm trong miền nguồn nào, và có bộ điều khiển phụ không?

**Nguồn nói gì**

   "Support multi power domains in VD_NPU: PD_NPUTOP, PD_NPU1, PD_NPU2" [T1 TRM1 tr.1091]

TRM1 tr.1093 (Table 7-1, hàng VD_NPU) xếp: ``RKNN_CORE0`` cùng ``MCU_NPU``, ``PVTPLL_NPU``, ``TIMER_NPU`` trong PD_NPUTOP.``RKNN_CORE1`` trong PD_NPU1.``RKNN_CORE2`` trong PD_NPU2 (đối chiếu từ bố cục trang).

   "MCU in VD_NPU integrate 16KB Cache and 64KB TCM" [T1 DS tr.8]

..

   "One isolated voltage domain to support DVFS" [T1 DS tr.11]

|TRM1 Table 7-1| *Hình 2.2. Các hàng VD_NPU của Table 7-1: PD_NPUTOP (gồm MCU_NPU và RKNN_CORE0), PD_NPU1 (RKNN_CORE1), PD_NPU2 (RKNN_CORE2). Nguồn: [T1 TRM1 tr.1093, Table 7-1]*

**Ý chính.** Ba NPU core thuộc ba power domain khác nhau, và core 0 chung domain với MCU của NPU (TRM1 tr.1093). TRM1 tr.1276 cho MCU NPU_M0 có TCM 64KB và cache 16KB.

**Giới hạn.** TRM1 tr.1298 (bảng ngắt của NPU_M0) cho thấy các ngắt ``C0_RKNN``, ``C1_RKNN``, ``C2_RKNN``, ``Timer0_NPU``, ``Timer1_NPU``, ``PVTM_NPU``, ``WDT_NPU``, ``CACHE_NPU`` và ``MAILBOX2_AP`` nối trực tiếp vào NPU_M0. Vai trò của MCU này với một job NPU không được mô tả: ``unknown``.

--------------

.. |TRM2 Fig 1-1| image:: ../../_assets/img/npu/02_rk3588_npu_hardware/trm2_p16_fig1-1.png

.. |TRM1 Table 7-1| image:: ../../_assets/img/npu/02_rk3588_npu_hardware/trm1_p1093_table7-1_vd_npu.png

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
     - :download:`01_Rockchip_RK3588_TRM_V1.0_Part1_20220309.pdf <../../_assets/pdf/papers/05_rk3588/01_vendor_docs/02_trm/01_Rockchip_RK3588_TRM_V1.0_Part1_20220309.pdf>`
     - 5
   * - ``TRM2``
     - T1
     - :download:`02_Rockchip_RK3588_TRM_V1.0_Part2_20220309.pdf <../../_assets/pdf/papers/05_rk3588/01_vendor_docs/02_trm/02_Rockchip_RK3588_TRM_V1.0_Part2_20220309.pdf>`
     - 2
   * - ``DS``
     - T1
     - :download:`02_RK3588_Datasheet_V0.1-20210727.pdf <../../_assets/pdf/papers/05_rk3588/01_vendor_docs/01_datasheet/02_RK3588_Datasheet_V0.1-20210727.pdf>`
     - 2
