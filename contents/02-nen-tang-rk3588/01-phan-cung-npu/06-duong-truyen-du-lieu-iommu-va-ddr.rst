:tocdepth: 1

************************************************
Đường truyền dữ liệu, IOMMU và bộ điều khiển DDR
************************************************

.. admonition:: Trang này trả lời

   - Dữ liệu từ DDR đến NPU đi qua những khối nào?
   - QoS đặt ưu tiên cho NPU ở đâu, và có bao nhiêu tầng QoS khác nhau?
   - IOMMU của NPU có gì, TRM nói được bao nhiêu?
   - DDR controller giới hạn loại DRAM, số kênh và băng thông lý thuyết ra sao?
   - NPU có dùng DMAC của SoC không?

.. admonition:: Tóm tắt

   - Interconnect có 4 DDR scheduler để sắp xếp lại giao dịch và quản lý ưu tiên QoS cho IP thời gian thực [T1 TRM2 tr.16].
   - Mức QoS 3 bit được ánh xạ sang urgency 7 bit (Table 1-2). Ưu tiên chỉ có tác dụng đến scheduler, sau khi vào hàng đợi lệnh của DDRCTL thì lệnh chạy theo thứ tự [T1 TRM2 tr.17].
   - Bốn cổng master của NPU có default QoS 0 và Ext priority YES, MCU_NPU có default QoS 3 và Ext priority NO [T1 TRM2 tr.19].
   - Có ba tầng QoS khác nhau (BIU 3 bit, DDRCTL ``arqos``, trong IP NPU 2 bit) và TRM không nối chúng với nhau [T1 TRM2 tr.18] [T1 TRM2 tr.173] [T1 TRM1 tr.2048].
   - TRM1 và TRM2 không có chuỗi "iommu". Chỉ DTS và driver cho thấy NPU có nút ``rockchip,iommu-v2`` riêng [T1 DTS dts/rk3588s.dtsi:3712-3722].
   - Bộ điều khiển hỗ trợ LPDDR4/4X/5, 4 kênh 64 bit hoặc 2 kênh 32 bit, trần speed grade 4267 và 5500 Mbps [T1 TRM2 tr.55] [T1 TRM2 tr.56]. Rockchip không nêu băng thông GB/s, trần 34.1 và 44.0 GB/s trong trang là phép tính của người viết.
   - Không có request nào của NPU trong danh sách DMAC. NPU tự đọc ghi bộ nhớ bằng AXI master và các khối DMA con của chính nó [T1 TRM1 tr.27] [T1 TRM1 tr.1985].

.. contents:: Trong trang này
   :local:
   :depth: 1

Đường đi của một giao dịch bộ nhớ từ NPU (tóm tắt của người viết, ghép từ các mục sau): master NPU qua BIU (nơi đặt QoS), vào interconnect, đến DDR scheduler của kênh, qua một cổng AXI vào DDRCTL, qua DFI sang DDRPHY rồi tới chip DRAM. Giải thích nền: khi nhiều master (CPU, GPU, NPU, màn hình) dùng chung một DRAM, bộ điều khiển phải sắp xếp lại giao dịch để ít đổi hàng, đổi chiều đọc ghi. QoS là cơ chế cho master thời gian thực (như VOP) chen lên trước master chịu trễ (như NPU chạy batch). Trang này chỉ mô tả phần mới của đường đi. Loại DRAM, số kênh và giới hạn cấu hình thực ở :doc:`../04-bo-nho-hieu-nang/01-ddr-tren-rk3588`. Cách NPU dùng System SRAM ở :doc:`03-che-do-da-loi-va-system-sram`.

.. _sec-npu-interconnect-qos:

1. Interconnect và QoS
======================

1.1 Interconnect và DDR scheduler
---------------------------------

TRM2 mô tả tính năng của interconnect:

   "Four embedded DDR schedulers for transaction reorder to maximum DDR efficiency" [T1 TRM2 tr.16]

   "Priority management for quality of service (QoS), especially for real-time IP" [T1 TRM2 tr.16]

.. _fig-npu-interconnect-diagram:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/duong-du-lieu-bus-iommu-ddr/trm2-fig1-1-interconnect-diagram.png
   :align: center
   :alt: Sơ đồ interconnect từ các master qua scheduler đến DDRCTL

   Sơ đồ interconnect: hàng master (CPU, GPU, NPU, VOP, ISP, master khác) vào interconnect, qua 4 scheduler đến 4 DDRCTL, SYSMEM và các slave khác. Nguồn: [T1 TRM2 tr.16, Fig. 1-1]

Có 4 DDR scheduler, mỗi cái chiếm 8KB địa chỉ: Channel0 ``0xFE000000``, Channel1 ``0xFE002000``, Channel2 ``0xFE004000``, Channel3 ``0xFE006000`` [T1 TRM2 tr.16]. Scheduler làm hai việc:

   "The scheduler optimizes DRAM efficiency by choosing the best transaction to execute inside each port input queue: the scheduler can reorder requests across queues, and within a queue as long as they do not have conflicting addresses or ordering constraints." [T1 TRM2 tr.16]

   "an urgent read request may take precedence over less urgent write requests, even though there may be a global efficiency loss due to DRAM bus turnaround." [T1 TRM2 tr.16]

.. _fig-npu-ddr-scheduler:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/duong-du-lieu-bus-iommu-ddr/trm2-fig1-2-ddr-scheduler.png
   :align: center
   :alt: Các tiêu chí trọng tài trong DDR scheduler

   DDR scheduler với Port0 đến Port4 và các tiêu chí trọng tài: Read Latency, AGING, URG_5 đến URG_2, BANK IDLE PAGE HIT, RW. Nguồn: [T1 TRM2 tr.17, Fig. 1-2]

Trong số các tiêu chí đó, hai tiêu chí liên quan trực tiếp đến ưu tiên:

   "AGING: Biases arbitration towards requests that exceed the aging threshold set by register Aging(n) for port (n)." [T1 TRM2 tr.17]

   "Three bits QoS level will be map to seven bits Urgency level in packets as Table 1-2. URG5 means the packets with fifth bit of Urgency field(Urgency[4]) is 1'b1 will be chosen by this arbiter stage." [T1 TRM2 tr.17]

.. _fig-npu-qos-urgency-map:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/duong-du-lieu-bus-iommu-ddr/trm2-table1-2-qos-urgency-map.png
   :align: center
   :alt: Bảng ánh xạ QoS 3 bit sang urgency 7 bit

   Table 1-2: ánh xạ mức QoS 3 bit sang Urgency 7 bit (cột ghi "QoS generator(internal) / Press/Hurry(external)"). Nguồn: [T1 TRM2 tr.17, Table 1-2]

.. list-table:: Ánh xạ QoS sang urgency (chép lại từ Table 1-2)
   :header-rows: 1
   :widths: 25 40 35

   * - QoS (3 bit)
     - Urgency (7 bit)
     - Nguồn
   * - 0
     - 0000000
     - [T1 TRM2 tr.17]
   * - 1
     - 0000001
     - [T1 TRM2 tr.17]
   * - 2
     - 0000011
     - [T1 TRM2 tr.17]
   * - 3
     - 0000111
     - [T1 TRM2 tr.17]
   * - 4
     - 0001111
     - [T1 TRM2 tr.17]
   * - 5
     - 0011111
     - [T1 TRM2 tr.17]
   * - 6
     - 0111111
     - [T1 TRM2 tr.17]
   * - 7
     - 1111111
     - [T1 TRM2 tr.17]

Đọc bảng (suy ra): mức QoS càng cao thì càng nhiều bit urgency bằng 1, theo kiểu thang (thermometer). Vì scheduler chỉ có các tầng URG5, URG4, URG3, URG2 (Fig. 1-2), mức QoS 1 chỉ đặt urgency[0] nên không bật tầng nào trong bốn tầng đó. TRM2 tr.20 viết theo hướng này: giá trị hợp lệ của ưu tiên trong scheduler là 0, 2, 3, 4 và 5:

   "because the arbiter stages ordering is: URG5, URG4, URG3, URG2, the valid values of internal and external works in scheduler are 0, 2, 3, 4 and 5." [T1 TRM2 tr.20]

Câu này viết "As shown in Table1-1", nhưng bảng urgency là Table 1-2 [T1 TRM2 tr.17]. Đây là lỗi tham chiếu trong TRM, trang này không sửa nội dung trích.

Giới hạn quan trọng của ưu tiên:

   "although the high priority request will be sent to DDR controller first, it does not mean that it can be served by DDR immediately. The request in DDR controller command queue will be executed in order taking no account of priority." [T1 TRM2 tr.17]

Hệ quả (suy ra, không phải câu của TRM): QoS chỉ quyết định thứ tự vào hàng đợi lệnh của DDRCTL, không bảo đảm độ trễ.

1.2 QoS generator và cột default QoS, Ext priority
--------------------------------------------------

Mỗi master có một BIU (bus interface unit) chứa QoS generator:

   "The priority of each request is configurable through the internal QoS generator in each master BIU. The QoS generator address of each master BIU and default priority are shown below." [T1 TRM2 tr.18]

   "When configuring the register of QoS generator of a certain master BIU, the corresponding clock of the master BIU should be alive." [T1 TRM2 tr.18]

.. _tbl-npu-master-biu:

.. list-table:: Các master BIU của NPU (rút từ Table 1-3, tr.19)
   :header-rows: 1
   :widths: 13 10 8 10 11 14 14 10

   * - Master
     - MID
     - PORT
     - PROBE ID
     - default QoS
     - QoS generator base
     - Shaping base
     - Ext priority
   * - NPU1
     - 7'h2e
     - 3
     - 0
     - 0
     - 0xfdf70000
     - 0xfdf70080
     - YES
   * - NPU0_MRO
     - 7'h2d
     - 2
     - 0
     - 0
     - 0xfdf72200
     - 0xfdf72280
     - YES
   * - NPU2
     - 7'h2f
     - 0
     - 0
     - 0
     - 0xfdf71000
     - 0xfdf71080
     - YES
   * - NPU0_MWR
     - 7'h2c
     - 1
     - 1
     - 0
     - 0xfdf72000
     - 0xfdf72080
     - YES
   * - MCU_NPU
     - 7'h27
     - 0
     - 0
     - 3
     - 0xfdf72400
     - 0xfdf72480
     - NO

Nguồn của cả bảng: [T1 TRM2 tr.19, Table 1-3].

.. _fig-npu-master-biu-table:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/duong-du-lieu-bus-iommu-ddr/trm2-table1-3-master-biu-gpu-npu.png
   :align: center
   :alt: Hàng GPU và NPU của bảng Master BIU information

   Table 1-3, trích hàng GPU và NPU. Nguồn: [T1 TRM2 tr.19, Table 1-3]

Đối chiếu cùng bảng để thấy NPU nằm ở đâu trong thang ưu tiên mặc định: GPU_M0 đến M3 có default QoS 0 và Ext NO [T1 TRM2 tr.19]. VOP_M0 và VOP_M1 có default QoS 2 và Ext YES [T1 TRM2 tr.18]. USB, EMMC, DMAC1, DMAC2 có default QoS 4 và Ext NO [T1 TRM2 tr.19]. HDCP0 và HDCP1 có default QoS 5 [T1 TRM2 tr.19]. Như vậy, theo mặc định của TRM, các cổng tính toán của NPU ở mức thấp nhất (0), ngang GPU. Cột PORT (0 đến 4) có vẻ ứng với cổng vào của scheduler (Fig. 1-2 có Port0 đến Port4). TRM2 không nói thẳng điều này, đây là suy ra.

**Nghĩa của cột Ext priority.** Một số master đổi ưu tiên động theo trạng thái buffer của chúng:

   "Except the internal priority control, some masters can also change their priority dynamic by their internal register according to buffer status." [T1 TRM2 tr.19, tr.20]

   "In order to make this work, ExtControl register of the corresponding BIU must be set to 0x1. In this case, the interconnect will choose the highest priority from the external and internal register." [T1 TRM2 tr.20]

   "It is better to set the internal priority same as the other master BIUs and external priority higher so that the DDR scheduler has more opportunity to optimal DDR efficiency." [T1 TRM2 tr.20]

Bốn cổng NPU có Ext priority bằng YES, nghĩa là BIU có đầu vào ưu tiên ngoài. IP NPU có điều khiển đầu vào đó hay không: unknown. Đã tìm ở: TRM1 Ch36 và TRM2 Ch1, từ khóa: ``Ext priority``, ``ExtControl``, ``Press``, ``Hurry``, ``SocketQosEn``. Không có giá trị QoS khuyến nghị riêng cho NPU ngoài default 0 và MCU_NPU 3.

1.3 Thanh ghi QoS
-----------------

QoS generator có 7 thanh ghi trong bảng tóm tắt, gồm hai thanh ghi định danh ``QoSGenerator_Id_CoreId`` (0x0000) và ``QoSGenerator_Id_RevisionId`` (0x0004) và 5 thanh ghi điều khiển sau, offset cộng vào base ở Table 1-3 [T1 TRM2 tr.27-28]:

.. list-table:: Thanh ghi QoS generator
   :header-rows: 1
   :widths: 28 10 14 48

   * - Thanh ghi
     - Offset
     - Reset
     - Mô tả
   * - ``QoSGenerator_Priority``
     - 0x0008
     - 0x80000000
     - Priority register. P1 ``[10:8]``, P0 ``[2:0]`` (xem dưới)
   * - ``QoSGenerator_Mode``
     - 0x000C
     - 0x00000003
     - QoS generate mode, ``[1:0]``: 00 Fixed, 01 Limiter, 10 Bypass, 11 Regulator
   * - ``QoSGenerator_Bandwidth``
     - 0x0010
     - 0x00000000
     - Bandwidth threshold, ``[12:0]``
   * - ``QoSGenerator_Saturation``
     - 0x0014
     - 0x00000040
     - Saturation counter, ``[9:0]``
   * - ``QoSGenerator_ExtControl``
     - 0x0018
     - 0x00000000
     - External control: bit3 ExtLimitEn, bit2 IntClkEn, bit1 ExtThrEn, bit0 SocketQosEn

Nguồn của cả bảng: [T1 TRM2 tr.27] [T1 TRM2 tr.28]. Reset của Mode là 0x3, tức Regulator.

Ý nghĩa các trường chính:

   "P1 [10:8] In Regulator mode, defines the HIGH hurry level. In Fixed/Limiter mode, defines the Urgency level for READ transactions." [T1 TRM2 tr.27]

   "P0 [2:0] In Regulator mode, defines the LOW hurry level. In Fixed/Limiter mode, defines the Urgency level for WRITE transactions." [T1 TRM2 tr.27]

   "Defines the bandwidth threshold in 1/256th-byte-per-cycle units. In other words, the desired rate in MBps is divided by frequency in MHz of the BIU, and then multiplied by 256." [T1 TRM2 tr.28]

   "Defines the size of the bandwidth counter, that is, the measurement window, in 16-byte units." [T1 TRM2 tr.28]

   "SocketQosEn ... When set to 0, the QoS generator drives the levels. When set to 1, internal signals Pressure and Hurry are driven by the greater of the two levels from the socket interface or the QoS generator." [T1 TRM2 tr.28]

``ExtControl = 0x1`` ở mục 1.2 khớp ``SocketQosEn = 1`` (suy ra, mục 1.3.2 của TRM không nêu tên bit).

Ví dụ số (suy ra từ công thức Bandwidth, giá trị đầu vào là giả định): muốn đặt ngưỡng 1000 MBps cho một BIU chạy 500 MHz thì ghi ``1000 / 500 * 256 = 512``. Tần số BIU của NPU: unknown. Đã tìm ở: TRM2 Ch1, từ khóa: ``BIU``, ``frequency``.

**Ba tầng QoS khác nhau.** Chữ "QoS" xuất hiện ở ba nơi, độ rộng và vai trò khác nhau. TRM không nối chúng, nên trang này không vẽ ánh xạ giữa chúng.

.. list-table:: Ba tầng QoS
   :header-rows: 1
   :widths: 20 16 34 30

   * - Tầng
     - Độ rộng
     - Vai trò
     - Nguồn
   * - QoS generator trong BIU của master
     - 3 bit
     - Đặt ưu tiên của request, ánh xạ sang urgency cho DDR scheduler
     - [T1 TRM2 tr.17] [T1 TRM2 tr.18]
   * - ``arqos`` ở cổng AXI của DDRCTL
     - 0 đến 13 hoặc 14 (mức)
     - ``rqos_map_level1`` chia vùng, ``rqos_map_region`` chọn LPR, VPR hoặc HPR
     - [T1 TRM2 tr.173-174]
   * - QoS trong IP NPU (``rd_*_qos``)
     - 2 bit mỗi trường
     - Ưu tiên đọc theo từng đường: PC, PPU, DPU, kernel, feature
     - [T1 TRM1 tr.2048]

Tầng thứ ba nằm trong NPU: thanh ghi ``RKNN_ddma_cfg_dma_rd_qos`` (``0x8020``, "Read Qos for DMA") có các trường ``rd_pc_qos [9:8]``, ``rd_ppu_qos [7:6]``, ``rd_dpu_qos [5:4]``, ``rd_kernel_qos [3:2]``, ``rd_feature_qos [1:0]``, reset 0 [T1 TRM1 tr.1993] [T1 TRM1 tr.2048]. Thanh ghi tương tự ``RKNN_sdma_cfg_dma_rd_qos`` ở ``0x9020``. Không có trường QoS cho đường ghi. Các trường 2 bit này có nối vào "Ext priority" của BIU hay không, và ánh xạ 2 bit sang 3 bit ra sao: unknown. Đã tìm ở: TRM1 Ch36 và TRM2 Ch1, từ khóa: ``Ext priority``, ``ExtControl``, ``default QoS``, ``Priority``.

1.4 Đo băng thông một master
----------------------------

Hai cơ chế khác ngoài QoS nằm trong cùng interconnect.

**Shaping** giới hạn số gói đang chờ giữa master và scheduler:

   "Shaping limits the number of pending packets between master and scheduler." [T1 TRM2 tr.20]

Giá trị mặc định là 255 (``Shaper_NbPktMax0``, offset ``0x0008``, ``[7:0]``, reset 0xFF) [T1 TRM2 tr.20] [T1 TRM2 tr.29]. Địa chỉ thanh ghi shaping của NPU ở cột Shaping base của bảng ở mục 1.2.

**Probe** đo thống kê lưu lượng:

   "There are totally 12 probes to monitor the DDR schedule traffic statics, and each can be programmed by their registers." [T1 TRM2 tr.20]

Để đếm byte của một master, TRM2 đưa quy trình:

   "Counters_0_Src should be set to 0x14 (FILT_BYTE) to count payload bytes in packets selected by the associated filter: Filter_0." [T1 TRM2 tr.54]

   "Filters_0_usebase should be set to the MID value of the master, the MID value of each master can be find in Table 1-3." [T1 TRM2 tr.54]

Cùng trang còn các giá trị ``Filters_0_opcode = 0xf``, ``Filters_0_status = 0x3``, ``Filters_0_length = 0xf``, ``Filters_0_usemask = 0x7f`` [T1 TRM2 tr.54]. Với NPU1, MID là ``7'h2e`` (bảng mục 1.2). Ánh xạ cột PORT và PROBE ID sang địa chỉ probe ở Table 1-4 là suy ra từ hai bảng, chưa có câu nào của TRM xác nhận, nên trang này không đưa địa chỉ probe cụ thể. Linux có lộ các probe này ra hay không: unknown.

Với idle request, ví dụ của TRM dùng GPU, không có đoạn riêng cho NPU: BIU được yêu cầu idle khi power domain tách khỏi interconnect, do PMU điều khiển [T1 TRM2 tr.52]. Phần PMU của NPU ở :doc:`01-vi-tri-soc-phan-vung-nguon-va-mcu`.

.. _sec-npu-iommu:

2. IOMMU của NPU: TRM không nêu
===============================

TRM1 và TRM2 không có chuỗi "iommu" (đã tìm toàn bộ hai tệp). Chuỗi "smmu" có xuất hiện nhưng ở ngữ cảnh PCIe và MMU600, không liên quan NPU. TRM2 Ch1 chỉ liệt kê ba master MMU600: ``MMU600PCIE_TCU`` (7'h29), ``MMU600PHP_TBU`` (7'h2a), ``MMU600PHP_TCU`` (7'h2b), thuộc nhóm PHP [T1 TRM2 tr.19]. Chương 36 (RKNN) không có "MMU", "IOMMU" hay "page table". Chỉ có các thanh ghi địa chỉ như ``RKNN_pc_task_dma_base_addr`` (``0x0034``, mô tả "dma_base_addr" [T1 TRM1 tr.1997]) và ``RKNN_cna_feature_data_addr`` (``0x1070``), không mô tả đó là địa chỉ ảo hay vật lý [T1 TRM1 tr.2007].

Những gì có thể nói đến từ DTS và driver (không phải TRM):

.. list-table:: Bằng chứng về IOMMU của NPU trong driver 0.9.8
   :header-rows: 1
   :widths: 56 44

   * - Nội dung
     - Nguồn
   * - Nút NPU trỏ tới IOMMU: ``iommus = <&rknpu_mmu>;``
     - [T1 DTS dts/rk3588s.dtsi:3478]
   * - ``rknpu_mmu: iommu@fdab9000``, ``compatible = "rockchip,iommu-v2"``, bốn vùng ``reg`` (0xfdab9000, 0xfdaba000, 0xfdaca000, 0xfdada000, mỗi vùng 0x100), ngắt ``npu0_mmu``, ``npu1_mmu``, ``npu2_mmu``
     - [T1 DTS dts/rk3588s.dtsi:3712-3722]
   * - Driver quản lý tối đa 16 domain: ``RKNPU_MAX_IOMMU_DOMAIN_NUM 16``, cùng cờ ``iommu_en`` và các biến ``iommu_domains``
     - [T1 DRV include/rknpu_drv.h:56] [T1 DRV include/rknpu_drv.h:133] [T1 DRV include/rknpu_drv.h:172-177]
   * - Cờ bộ nhớ ``RKNPU_MEM_IOMMU = 1 << 4`` ("IOMMU mapping"), ioctl ``RKNPU_GET_IOMMU_EN``, ``RKNPU_GET_IOMMU_DOMAIN_ID``, ``RKNPU_SET_IOMMU_DOMAIN_ID``
     - [T1 DRV include/rknpu_ioctl.h:65-66] [T1 DRV include/rknpu_ioctl.h:129-136] [T1 DRV rknpu_drv.c:483-492]

Cơ chế dịch địa chỉ (cấu trúc bảng trang, TLB, thanh ghi của IOMMU): unknown. Đã tìm ở: TRM1, TRM2, DS V1.3, DS V1.7, DTS, driver, từ khóa: ``iommu``, ``smmu``, ``mmu``, ``page table``, ``translation``. Truy vấn gợi ý để tìm tiếp: "Rockchip IOMMU v2 page table", "rk_iommu rockchip-iommu.c dte pte" (mã nguồn kernel ``drivers/iommu/rockchip-iommu.c`` chưa có trong repo).

.. _sec-npu-ddr-controller:

3. DDR controller
=================

3.1 Loại DRAM và trần băng thông
--------------------------------

Phần chung (DRAM nào, bao nhiêu kênh, giới hạn của cấu hình thực) đã ở :doc:`../04-bo-nho-hieu-nang/01-ddr-tren-rk3588`. Mục này chỉ thêm phần mới. DMC gồm bộ điều khiển và PHY:

   "The DMC includes LPDDR4/4X/5 controller (DDRCTL) and DDRPHY which are a complete memory interface solution for DDR memory subsystems." [T1 TRM2 tr.55]

Các đặc tính sau lấy từng câu riêng từ danh sách tính năng của TRM2 tr.55 (không phải một danh sách liền mạch theo đúng thứ tự gốc):

   "Support scalable and software-controlled 1:2:2(LPDDR4/4X) or 1:1:2/1:1:4 (LPDDR5) frequency ratio" [T1 TRM2 tr.55]

   "Support optional 2-channel interleaving with a maximum of 16GB capacity in total, 2 ranks for each channel" [T1 TRM2 tr.55]

   "Support scrambling and descrambling of data written to or read from DDR SDRAM" [T1 TRM2 tr.55]

PHY chạy tới 4267 Mbps (LPDDR4/4X) và 5500 Mbps (LPDDR5) [T1 TRM2 tr.56]. Cùng đoạn mô tả PHY có câu "It supports all JEDEC DDR3/DDR3L/DDR4/LPDDR3/LPDDR4 SDRAM components in the market." [T1 TRM2 tr.56]. Đây có thể là mô tả của IP PHY chung (suy ra, TRM không nói như vậy), mâu thuẫn bề mặt với tính năng LPDDR4/4X/5 của DMC. Trang này chỉ khẳng định LPDDR4/4X/5 theo Overview và datasheet:

   "Compatible with JEDEC standards LPDDR4/LPDDR4X/LPDDR5" [T1 DS V1.3 pdf 7]

   "Support four channels, each channel 16bits data widths" [T1 DS V1.3 pdf 7]

Bản RK3588S (V1.7) ghi cùng các dòng này: "quad channel", "four channels, each channel 16bits", 32GB [T1 DS V1.7 tr.7, tr.8]. Về bộ nhớ, hai bản không khác nhau theo các dòng đó.

**Trần băng thông lý thuyết (phép tính của người viết).** Rockchip không nêu băng thông GB/s cho DDR. Tìm "GB/s", "MB/s", "peak", "theoretical" trong TRM2 Ch1 và Ch2, DS V1.3, DS V1.7 không ra giá trị nào. Có thể tính trần của bộ điều khiển từ ba toán hạng đã trích:

- Tốc độ chân tối đa: 4267 Mbps (LPDDR4/4X) và 5500 Mbps (LPDDR5) [T1 TRM2 tr.56].
- Bề rộng bus: 64 bit cho 4 kênh interleave, 32 bit cho 2 kênh [T1 TRM2 tr.55].
- Chia 8 để đổi bit sang byte (phép đổi đơn vị).

.. list-table:: Trần băng thông của bộ điều khiển (suy ra, hệ 10^9)
   :header-rows: 1
   :widths: 24 28 28 20

   * - Cấu hình
     - Công thức
     - Kết quả
     - Ghi chú
   * - LPDDR4/4X, 4 kênh
     - 4267 x 64 / 8 = 34 136 MB/s
     - 34.1 GB/s
     - Trần speed grade
   * - LPDDR5, 4 kênh
     - 5500 x 64 / 8 = 44 000 MB/s
     - 44.0 GB/s
     - Trần speed grade
   * - LPDDR4/4X, 2 kênh
     - 4267 x 32 / 8 = 17 068 MB/s
     - 17.1 GB/s
     - Một nửa
   * - LPDDR5, 2 kênh
     - 5500 x 32 / 8 = 22 000 MB/s
     - 22.0 GB/s
     - Một nửa

Đây là trần cấu hình tối đa của bộ điều khiển, không phải băng thông của board. Loại DRAM, speed grade và số kênh của board: unknown theo nguồn T1. Trang DDR đã link ở trên nêu tần số DDR lúc chạy còn bị giới hạn bởi firmware theo tài liệu RKNN.

.. _fig-npu-dmc-block-diagram:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/duong-du-lieu-bus-iommu-ddr/trm2-fig2-1-dmc-block-diagram.png
   :align: center
   :alt: Sơ đồ khối DMC gồm DDRSCH, Scramble, AXI, DDRCTL, DFI và DDRPHY

   Sơ đồ khối DMC: DDRSCH0 đến 3, kênh 0 đến 3, Scramble, AXI, DDRCTL và DDR Monitor, giao diện DFI, DDRPHY, thiết bị LPDDR4/4X/5. Nguồn: [T1 TRM2 tr.56, Fig. 2-1]

3.2 Cấu hình kênh và QoS ở DDRCTL
---------------------------------

Cấu hình hợp lệ theo TRM là 4 kênh interleave (64 bit, tối đa 32GB) hoặc 2 kênh "optional" (32 bit, tối đa 16GB) [T1 TRM2 tr.55]. Khi không interleave, địa chỉ base mỗi kênh cho theo ``CENTER_GRF_CON4[8:4]`` (Table 1-5): hàng 4 kênh với ``5'b00000`` là kênh 0 ở ``0x0_0000_0000``, kênh 1 ``0x2_0000_0000``, kênh 2 ``0x4_0000_0000``, kênh 3 ``0x6_0000_0000``, kích thước kênh 8GB [T1 TRM2 tr.20] [T1 TRM2 tr.21]. Bốn kênh 8GB cho 32GB, khớp "maximum of 32GB capacity in total" (phép cộng của người viết). Với chế độ 4 kênh interleave, ``CENTER_GRF_CON4[8:4]`` phải đặt bằng ``5'b0000`` [T1 TRM2 tr.20].

DDRCTL chỉ có một cổng AXI cho mỗi kênh:

   "DDRCTL supports only one AXI Port, it receives AXI transactions from memory schedule (DDRSCH0~3) of interconnect directly or from Scramble module." [T1 TRM2 tr.56]

Scramble mặc định bị bypass ("This module is defaultly bypassed.") [T1 TRM2 tr.57]. Đọc về phía AXI có bộ đệm sắp xếp lại: "Read is stored in a SRAM, read re-order buffer and return in order to the AXI Port." [T1 TRM2 tr.56]. Cổng được bật bằng ``port_en`` của ``DDRCTL_PCTRL`` (0x20090), trong quy trình khởi tạo là bước "Set DDRCTL_PCTRL.port_en to 1'b1 to enable AXI port of DDRCTL" [T1 TRM2 tr.173] [T1 TRM2 tr.559].

QoS ở DDRCTL là tầng thứ hai trong mục 1.3:

   "Separation level1 indicating the end of region0 mapping; start of region0 is 0. Possible values for level1 are 0 to 13 (for dual RAQ) or 0 to 14 (for single RAQ) which corresponds to arqos." [T1 TRM2 tr.173-174]

   "If set to 1, enables the AXI urgent sideband signal (arurgent). When enabled and arurgent is asserted by the master, that port becomes the highest priority" [T1 TRM2 tr.171]

Ở đây ``DDRCTL_PCFGQOS0`` (0x20094) có trường ``rqos_map_region0/1`` nhận giá trị 0 là LPR, 1 là VPR, 2 là HPR. ``rd_port_urgent_en`` là bit 13 của ``DDRCTL_PCFGR``. Bản ghi tương ứng là ``DDRCTL_PCFGWQOS0/1`` (0x2009C, 0x200A0). TRM2 không mô tả quan hệ giữa QoS 3 bit của scheduler (mục 1.1) và ``arqos`` của cổng DDRCTL, nên trang này chỉ nêu có hai tầng, không nối.

Scheduler cũng cần biết loại DRAM: ``DDRSCH_DeviceConf`` (0x0008, tám cấu hình định sẵn), ``DDRSCH_DeviceSize`` (granule 64MB), ``DDRSCH_DdrMode`` có ``MwrSize`` và ``BurstSize`` (16, 32, 64, 128 byte, với LPDDR4 phải đặt bằng số byte của giao dịch BL16) [T1 TRM2 tr.22] [T1 TRM2 tr.25].

Các điều chưa biết ở mục này:

- Kích thước granule interleave, và nội dung các thanh ghi hash ``SGRF_DDR_HASH_CON0`` đến ``7``, ``DDR_BANK_HASH_CTRL``, ``DDR_RANK_MASK0``: unknown. Đã tìm ở: TRM1 và TRM2, từ khóa: ``granule``, ``hash``, ``interleav``. TRM2 chỉ nói đến tên các thanh ghi hash, với DSU ở nhóm DSU_SGRF còn "other masters except DSU" ở nhóm BUS_SGRF [T1 TRM2 tr.54]. NPU thuộc nhóm "other masters" là suy ra.
- Tần số DDR mặc định của board, tên DRAM của board: unknown. Đã tìm ở: TRM2 Ch2, DS V1.3, DS V1.7, từ khóa: ``MHz``, ``freq``, ``LPDDR``.
- Việc NPU đi qua kênh nào: unknown. Với interleave 4 kênh mọi master dùng chung 4 kênh, TRM2 không có bảng gán master sang kênh. Đã tìm ở: TRM2 Ch1 và Ch2, từ khóa: ``NPU``, ``channel``.
- Ánh xạ chân ``DDR_CH0_*``, ``DDR_CH1_*`` (hậu tố ``_A`` đến ``_D``) sang kênh DDRCTL 0 đến 3: unknown, chưa đối chiếu bảng chân của datasheet.

4. DMA của NPU
==============

DMAC của SoC có ba bộ:

   "This device supports 3 Direct Memory Access (DMA) Controller. DMAC0/1/2 support transfers between memory and memory, peripheral and memory." [T1 TRM1 tr.1314]

Mỗi bộ hỗ trợ 24, 23, 21 request ngoại vi, 8 kênh cùng lúc [T1 TRM1 tr.1314]. Danh sách nguồn request (Table 1-4, tr.27-28, lặp ở Table 12-1) chỉ gồm I2S, PDM, SPDIF, UART, SPI, PWM, CAN, ``sdmmc_buffer`` [T1 TRM1 tr.27]. Không entry nào chứa "NPU" hoặc "RKNN" (đã tìm Table 1-4 và toàn Ch12). Vì vậy NPU không dùng DMAC để chuyển dữ liệu, kết luận này giới hạn ở "không có entry nào trong Table 1-4 và 12-1". Trong interconnect, DMAC0/1/2 là master 7'h08, 7'h09, 7'h0a, PORT 1, default QoS 0, 4, 4 [T1 TRM2 tr.19]. ``DMA2DDR`` (7'h07) cũng có mặt trong Table 1-3 [T1 TRM2 tr.19]. Chức năng của nó và liên hệ với NPU: unknown. Đã tìm ở: TRM1 và TRM2, từ khóa: ``DMA2DDR``.

NPU tự có đường đọc ghi bộ nhớ trong IP:

   "AHB interface used for configuration only support single" [T1 TRM1 tr.1984]

   "The AXI master interface is used to fetch data from memory that is attached to the Soc AXI interconnect. The AHB slave interface is used to access the registers for configuration, debug and test." [T1 TRM1 tr.1985]

Các khối con tham gia gồm CNA (nạp weight và feature), DPU_RDMA, PPU_RDMA, DDMA, SDMA và PC fetch (suy ra từ bản đồ địa chỉ Table 1-1) [T1 TRM1 tr.1986]. DDMA (``0x8000``) và SDMA (``0x9000``) có cùng bộ thanh ghi [T1 TRM1 tr.2046-2049]:

.. list-table:: Thanh ghi DMA của NPU (DDMA, SDMA cùng bộ, offset tính từ 0x8000 hoặc 0x9000)
   :header-rows: 1
   :widths: 30 10 40 20

   * - Thanh ghi
     - Offset
     - Nội dung
     - Nguồn
   * - ``cfg_outstanding``
     - 0x00
     - ``wr_os_cnt`` ``[15:8]``, ``rd_os_cnt`` ``[7:0]``: số giao dịch outstanding tối đa
     - [T1 TRM1 tr.2046]
   * - ``rd_weight_0``
     - 0x04
     - Trọng số burst đọc của PPU, DPU, kernel, feature (mỗi trường 8 bit)
     - [T1 TRM1 tr.2046]
   * - ``rd_weight_1``
     - 0x10
     - ``rd_weight_pc [7:0]``: trọng số burst đọc của PC
     - [T1 TRM1 tr.2047]
   * - ``cfg_dma_arb``
     - 0x18
     - ``wr_arbit_model``, ``rd_arbit_model``, ``wr_fix_arb``, ``rd_fix_arb`` (mô tả chỉ lặp tên trường)
     - [T1 TRM1 tr.2047]
   * - ``cfg_dma_rd_qos``
     - 0x20
     - QoS đọc theo từng đường, xem mục 1.3
     - [T1 TRM1 tr.2048]
   * - ``cfg_dma_rd_cfg`` / ``wr_cfg``
     - 0x24 / 0x28
     - Tham số AXI: ``arcache``, ``arprot``, ``arburst``, ``arsize`` và các trường ``aw*``
     - [T1 TRM1 tr.2048]

Thanh ghi ``RKNN_cna_dma_con0`` (``0x1078``) đặt độ dài burst AXI: ``weight_burst_len`` nhận 4'd3 là burst 4, 4'd7 là burst 8, 4'd15 là burst 16, và ``data_burst_len`` cho dữ liệu feature [T1 TRM1 tr.2007].

TRM1 Ch36 không khai triển DDMA và SDMA là viết tắt gì, cũng không nói chúng khác nhau ở chức năng nào dù cùng bộ thanh ghi. Điểm khác nhau: unknown. Đã tìm ở: TRM1 Ch36, từ khóa: ``DDMA``, ``SDMA``.

5. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 28 50 22

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Đặt QoS cao là NPU được phục vụ ngay.
     - Request ưu tiên cao vào DDRCTL trước, nhưng hàng đợi lệnh của DDRCTL chạy theo thứ tự, không xét ưu tiên.
     - [T1 TRM2 tr.17]
   * - QoS của NPU là một giá trị duy nhất.
     - Có ba tầng: BIU 3 bit, ``arqos`` của DDRCTL, QoS 2 bit trong IP NPU. TRM không nối chúng.
     - [T1 TRM2 tr.18] [T1 TRM2 tr.173] [T1 TRM1 tr.2048]
   * - Ext priority YES nghĩa là NPU tự nâng ưu tiên.
     - Chỉ cho biết BIU có đầu vào ưu tiên ngoài. IP NPU có lái nó hay không là unknown.
     - [T1 TRM2 tr.19]
   * - TRM mô tả IOMMU của NPU.
     - Không có chuỗi "iommu" trong TRM1 và TRM2. Chỉ DTS và driver cho thấy nút ``rockchip,iommu-v2``.
     - [T1 DTS dts/rk3588s.dtsi:3712-3722]
   * - RK3588 đạt 34.1 hoặc 44.0 GB/s.
     - Đó là trần tính từ speed grade và bề rộng bus, do người viết tính. Rockchip không nêu GB/s và cấu hình board là unknown.
     - [T1 TRM2 tr.55] [T1 TRM2 tr.56]
   * - DDR của RK3588 có thể là DDR3 hoặc DDR4.
     - Mô tả PHY có nhắc DDR3/DDR4, nhưng tính năng DMC và datasheet chỉ nêu LPDDR4/4X/5.
     - [T1 TRM2 tr.55] [T1 TRM2 tr.56]
   * - NPU chuyển dữ liệu bằng DMAC của SoC.
     - Table 1-4 và Table 12-1 không có request của NPU. NPU dùng AXI master và các khối DMA con của chính nó.
     - [T1 TRM1 tr.27] [T1 TRM1 tr.1985]
   * - Tham chiếu "Table1-1" ở TRM2 tr.20 là bảng địa chỉ scheduler.
     - Câu đó nói về giá trị URG, bảng đúng là Table 1-2 (tr.17). Lỗi tham chiếu trong TRM.
     - [T1 TRM2 tr.20] [T1 TRM2 tr.17]

Nguồn
=====

.. list-table::
   :header-rows: 1
   :widths: 14 8 68 10

   * - Nhãn
     - Tier
     - Tệp
     - Số lần
   * - ``TRM1``
     - T1
     - :download:`rk3588_part1.pdf <../../../_assets/pdf/datasheet/trm/rk3588_part1.pdf>` (số trang in bằng số trang PDF)
     - 25
   * - ``TRM2``
     - T1
     - :download:`rk3588_part2.pdf <../../../_assets/pdf/datasheet/trm/rk3588_part2.pdf>` (số trang in bằng số trang PDF)
     - 94
   * - ``DS V1.7``
     - T1
     - :download:`Rockchip_RK3588S_Datasheet_V1.7.pdf <../../../_assets/pdf/datasheet/soc/Rockchip_RK3588S_Datasheet_V1.7.pdf>` (trang in)
     - 1
   * - ``DS V1.3``
     - T1
     - :download:`Rockchip_RK3588_Datasheet_V1.3_20220328.pdf <../../../_assets/pdf/datasheet/soc/Rockchip_RK3588_Datasheet_V1.3_20220328.pdf>` (số trang PDF)
     - 2
   * - ``DRV``
     - T1
     - ``3rdparty/rknpu-driver-0.9.8/`` (commit f6eedab0 theo SOURCE.txt)
     - 6
   * - ``DTS``
     - T1
     - ``3rdparty/rknpu-driver-0.9.8/dts/rk3588s.dtsi``
     - 4
