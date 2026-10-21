:tocdepth: 1

***********************************
Bản đồ thanh ghi và cơ chế cấu hình
***********************************

.. admonition:: Trang này trả lời

   - Thanh ghi của NPU được tổ chức ra sao và nằm ở địa chỉ nào?
   - Hai chế độ cấu hình (slave configured mode và PC mode) khác nhau thế nào, driver dùng chế độ nào?
   - Ping-pong register là gì và ai bật nó?
   - Ngắt của NPU báo những sự kiện gì, nối với core nào, driver xử lý ra sao?
   - TRM có chỗ nào tự mâu thuẫn hoặc bỏ trống trong phần này?

.. admonition:: Tóm tắt

   - Mỗi core có một vùng thanh ghi 64KB, bên trong chia thành các block 4KB (PC, CNA, CORE, DPU, DPU_RDMA, PPU, PPU_RDMA, DDMA, SDMA) và block GLOBAL [T1 TRM1 tr.1986] [T1 TRM1 tr.18].
   - TRM nêu hai chế độ: slave configured mode (CPU ghi thanh ghi qua AHB) và PC mode (NPU tự nạp danh sách thanh ghi từ bộ nhớ qua AXI), chọn bằng bit ``pc_sel`` [T1 TRM1 tr.2053] [T1 TRM1 tr.1994].
   - Driver rknpu 0.9.8 từ chối job không có cờ PC, nên chỉ chạy PC mode [T1 DRV rknpu_job.c:394-397].
   - Ping-pong là hai nhóm thanh ghi luân phiên để giấu thời gian nạp cấu hình, bật bằng thanh ghi ``S_POINTER`` của từng block [T1 TRM1 tr.2052].
   - Có 3 tín hiệu ngắt, mỗi bit của ``PC_INTERRUPT_STATUS`` là một trong 17 sự kiện, nhưng TRM chỉ mô tả bit 0 đến 13 [T1 TRM1 tr.2053] [T1 TRM1 tr.1995].
   - TRM tự mâu thuẫn ở hai chỗ: GLOBAL ghi ``0xf000 ~ 0xf004`` nhưng thanh ghi ở ``0xF008`` [T1 TRM1 tr.1986] [T1 TRM1 tr.2052], và văn bản gọi "Figure 1-3" trong khi hình in là Fig. 36-3 [T1 TRM1 tr.2053].
   - Ngắt thứ i của driver dùng handler của core i, khớp tên nguồn ``irq_rknn_c0`` đến ``c2`` [T1 DRV rknpu_drv.c:84-88] [T1 TRM1 tr.24].

.. contents:: Trong trang này
   :local:
   :depth: 1

Ba khái niệm nền của trang này (giải thích của người viết, không phải câu của hãng):

- Bộ tăng tốc như NPU được CPU điều khiển qua các thanh ghi ánh xạ vào không gian địa chỉ. Cấu hình một phép tính nghĩa là ghi một chuỗi giá trị vào các thanh ghi đó rồi ghi bit "bắt đầu".
- Có hai cách ghi. Cách thứ nhất, CPU ghi từng thanh ghi qua bus cấu hình. Cách thứ hai, CPU soạn sẵn danh sách (địa chỉ, giá trị) trong RAM, thiết bị tự đọc danh sách đó bằng DMA, giống một command buffer.
- Ping-pong là double buffering: trong lúc nhóm thanh ghi A đang chạy, CPU hoặc DMA nạp nhóm B, nên thời gian nạp cấu hình bị giấu đi. Ngắt là cách thiết bị báo "xong" hoặc "lỗi" cho CPU mà không cần CPU hỏi liên tục.

.. _sec-npu-register-map:

1. Register map
===============

1.1 Địa chỉ nội bộ
------------------

Mỗi core NPU có một vùng thanh ghi 64KB: RKNN C0 ``0xFDAB0000``, C1 ``0xFDAC0000``, C2 ``0xFDAD0000`` [T1 TRM1 tr.18]. DTS của driver khớp với ba địa chỉ này (``reg = <0x0 0xfdab0000 0x0 0x10000>, ...``) [T1 DTS dts/rk3588s.dtsi:3450-3454]. Bên trong vùng đó, TRM chia theo ``Base[15:12]`` như bảng sau.

   "Table 1- 1 RKNN Address Mapping ... 4'h0 PC 4K BYTE 0x0000 ~ 0x0fff ... 4'hf GLOBAL 4 BYTE 0xf000 ~ 0xf004" [T1 TRM1 tr.1986]

.. list-table:: Địa chỉ nội bộ của một core (cộng vào base của core)
   :header-rows: 1
   :widths: 14 14 22 50

   * - Block
     - Base[15:12]
     - Khoảng địa chỉ
     - Ghi chú
   * - PC
     - 0
     - 0x0000 ~ 0x0fff
     - Khối PC: TRM ghi tên "PC" ở Table 1-1 và không khai triển. Các thanh ghi của khối này nạp thanh ghi từ bộ nhớ (``pc_source_addr``), ngắt (``pc_interrupt_*``) và đếm task (``pc_task_con``) [T1 TRM1 tr.1994, tr.1995, tr.1997]
   * - CNA
     - 1
     - 0x1000 ~ 0x1fff
     - 4K BYTE [T1 TRM1 tr.1986]
   * - CORE
     - 3
     - 0x3000 ~ 0x3fff
     - 4K BYTE. Không có Base 2 trong bảng [T1 TRM1 tr.1986]
   * - DPU
     - 4
     - 0x4000 ~ 0x4fff
     - 4K BYTE [T1 TRM1 tr.1986]
   * - DPU_RDMA
     - 5
     - 0x5000 ~ 0x5fff
     - 4K BYTE [T1 TRM1 tr.1986]
   * - PPU
     - 6
     - 0x6000 ~ 0x6fff
     - 4K BYTE [T1 TRM1 tr.1986]
   * - PPU_RDMA
     - 7
     - 0x7000 ~ 0x7fff
     - 4K BYTE [T1 TRM1 tr.1986]
   * - DDMA
     - 8
     - 0x8000 ~ 0x8fff
     - 4K BYTE [T1 TRM1 tr.1986]
   * - SDMA
     - 9
     - 0x9000 ~ 0x9fff
     - 4K BYTE [T1 TRM1 tr.1986]
   * - GLOBAL
     - f
     - 0xf000 ~ 0xf004
     - 4 BYTE. Mâu thuẫn với 0xF008, xem bên dưới [T1 TRM1 tr.1986]

Ví dụ số (suy ra): ``s_pointer`` của CNA ở core 1 nằm ở ``0xFDAC0000 + 0x1004 = 0xFDAC1004``.

**Mâu thuẫn nội bộ của TRM về GLOBAL.** Table 1-1 ghi GLOBAL chiếm ``0xf000 ~ 0xf004`` [T1 TRM1 tr.1986]. Nhưng thanh ghi duy nhất được mô tả ở block này nằm ngoài khoảng đó:

   "RKNN_global_operation_enable Address: Operational Base + offset (0xF008)" [T1 TRM1 tr.2052]

Bảng tóm tắt cũng ghi ``0xF008`` [T1 TRM1 tr.1993]. Hai con số không thể cùng đúng. Driver định nghĩa ``RKNPU_OFFSET_ENABLE_MASK 0xf008`` [T1 DRV include/rknpu_ioctl.h:21-38], trùng với mô tả thanh ghi chứ không với Table 1-1, nhưng không có dòng nào trong ``*.c`` ghi vào offset này. Thanh ghi ở ``0xF000`` và ``0xF004``: unknown. Đã tìm ở: TRM1 Ch36, từ khóa: ``0xf000``, ``0xF004``, ``GLOBAL``.

Một lỗi đánh số khác: văn bản mục 36.5.4 gọi các hình là "Figure 1-3/1-4/1-5" trong khi chú thích in trên trang là Fig. 36-3 đến 36-7 [T1 TRM1 tr.2053]. Trang này dùng số in của hình (36-x).

1.2 Thanh ghi cần để hiểu mode, ping-pong, ngắt
-----------------------------------------------

Tất cả thanh ghi dưới đây có Size W (32 bit) trong bảng tóm tắt [T1 TRM1 tr.1986]. Offset cộng với base của core ở mục 1.1.

.. _tbl-npu-reg-key:

.. list-table:: Thanh ghi chính
   :header-rows: 1
   :widths: 24 10 9 42 15

   * - Thanh ghi
     - Offset
     - Reset
     - Trường TRM mô tả
     - Trang
   * - ``RKNN_pc_operation_enable``
     - 0x0008
     - 0x0
     - [0] ``op_en``: 0 tắt PC module, 1 bật PC module nạp thanh ghi cho từng task
     - tr.1994
   * - ``RKNN_pc_base_address``
     - 0x0010
     - 0x0
     - [31:4] ``pc_source_addr``. [0] ``pc_sel``: 0 là PC mode (AXI DMA), 1 là Slave mode (AHB)
     - tr.1994
   * - ``RKNN_pc_register_amounts``
     - 0x0014
     - 0x0
     - [15:0] ``pc_data_amount``: số register nạp cho một task, mỗi register 64 bit
     - tr.1994
   * - ``RKNN_pc_interrupt_mask``
     - 0x0020
     - 0x1ffff
     - [16:0] ``int_mask``. Bit 0 đến 13 có mô tả
     - tr.1995
   * - ``RKNN_pc_interrupt_clear``
     - 0x0024
     - 0x0
     - [16:0] ``int_clr``, W1C
     - tr.1995
   * - ``RKNN_pc_interrupt_status``
     - 0x0028
     - 0x0
     - [16:0] ``int_st``, W1C, "which and with mask bit"
     - tr.1995, tr.1996
   * - ``RKNN_pc_interrupt_raw_status``
     - 0x002C
     - 0x0
     - [16:0] ``int_raw_st``
     - tr.1996
   * - ``RKNN_pc_task_con``
     - 0x0030
     - 0x0
     - [13] ``task_count_clear`` (W1C). [12] ``task_pp_en``. [11:0] ``task_number``
     - tr.1996, tr.1997
   * - ``RKNN_pc_task_dma_base_addr``
     - 0x0034
     - 0x0
     - [31:4] ``dma_base_addr``. Địa chỉ AXI cuối bằng base cộng offset
     - tr.1997
   * - ``RKNN_pc_task_status``
     - 0x003C
     - 0x0
     - [11:0] bộ đếm task hiện tại. [12], [13] là cờ task đầu và cuối (TRM ghi [12], [13] hai lần với nghĩa khác nhau)
     - tr.1997
   * - ``RKNN_{block}_s_pointer``
     - CNA 0x1004, CORE 0x3004, DPU 0x4004, DPU_RDMA 0x5004, PPU 0x6004, PPU_RDMA 0x7004
     - 0x0
     - [16] ``executer`` (RO), [5] ``executer_pp_clear``, [4] ``pointer_pp_clear``, [3] ``pointer_pp_mode``, [2] ``executer_pp_en``, [1] ``pointer_pp_en``, [0] ``pointer``
     - CNA tr.1998-1999
   * - ``RKNN_{block}_s_status``
     - CNA 0x1000, CORE 0x3000, DPU 0x4000, DPU_RDMA 0x5000, PPU 0x6000, PPU_RDMA 0x7000
     - 0x0
     - [17:16] ``status_1``, [1:0] ``status_0``: 0 idle, 1 đang chạy, 2 đang chạy và executer kia chờ
     - CNA tr.1998
   * - ``RKNN_{block}_operation_enable``
     - block cộng 0x8
     - 0x0
     - [0] ``op_en``. "This register and after this are all shadowed for ping-pong operation."
     - CNA tr.1999
   * - ``RKNN_global_operation_enable``
     - 0xF008
     - 0x0
     - [0] ``cna_op_en``, [2] ``core_op_en``, [3] ``dpu_op_en``, [4] ``dpu_rdma_op_en``, [5] ``ppu_op_en``, [6] ``ppu_rdma_op_en``. Bit 1 reserved
     - tr.2052

DDMA (``0x8000``) và SDMA (``0x9000``) không có ``s_pointer`` trong bảng tóm tắt [T1 TRM1 tr.1986-1993]. Lý do: unknown. Đã tìm ở: TRM1 Ch36, từ khóa: ``ddma_s_pointer``, ``sdma``.

**Định dạng một lệnh trong PC mode.** Danh sách thanh ghi mà PC nạp từ bộ nhớ gồm các từ 64 bit:

   "Each register takes 64 bits, it is combined as following: bit[63:48] indicates which block the register forward to. bit[47:16] the register's value; bit[15: 0] the register's offset address in each block." [T1 TRM1 tr.1994]

Bit chọn block: ``bit[56]`` là block PC, ``bit[57]`` CNA, ``bit[59]`` CORE, ``bit[60]`` DPU, ``bit[61]`` DPU_RDMA, ``bit[62]`` PPU, ``bit[63]`` PPU_RDMA, ``bit[55]`` đặt ``op_en`` cho từng block [T1 TRM1 tr.1994]. ``bit[58]`` không được gán cho block nào trong danh sách này, DDMA và SDMA cũng không có bit chọn.

   "eg. 64'h0081_0000_007f_0008 will set each block's op_en(CNA, CORE, ..., PPU_RDMA). note: op_en is strongly recommended set at the end of register list." [T1 TRM1 tr.1994]

Giải mã ví dụ (suy ra): offset ``0x0008`` là ``op_en`` của mỗi block, giá trị ``0x7f``, ``bit[55]`` bằng 1. Bit 48 của từ này không có mô tả trong các mệnh đề đã trích. Cũng ở tr.1994, TRM yêu cầu đặt ``64'h0041_xxxx_xxxx_xxxx`` trước ``op_en`` mà không nói ý nghĩa của bit 54 và bit 48.

1.3 Thanh ghi mà driver thực sự ghi
-----------------------------------

Driver định nghĩa offset PC khớp bảng ở mục 1.2: ``PC_OP_EN 0x8``, ``PC_DATA_ADDR 0x10``, ``PC_DATA_AMOUNT 0x14``, ``PC_TASK_CONTROL 0x30``, ``PC_DMA_BASE_ADDR 0x34``, ``INT_MASK 0x20``, ``INT_CLEAR 0x24``, ``INT_STATUS 0x28``, ``INT_RAW_STATUS 0x2c`` [T1 DRV include/rknpu_ioctl.h:21-38]. Hằng số riêng của RK3588: ``pc_data_amount_scale = 2``, ``pc_task_number_bits = 12``, ``pc_task_status_offset = 0x3c``, ``max_submit_number = (1 << 12) - 1``, ``core_mask = 0x7`` [T1 DRV rknpu_drv.c:183-202]. Trong các tệp ``*.c``, ``ENABLE_MASK`` (``0xf008``) chỉ xuất hiện ở phần định nghĩa, không thấy chỗ ghi.

.. _sec-npu-hai-che-do:

2. Hai chế độ cấu hình
======================

2.1 TRM nói gì
--------------

   "RKNN has two types of work mode: slave configured mode and pc work mode. Pc work mode need to initial register information to the system memory, then obey flowing flows as Figure 1-3 shows." [T1 TRM1 tr.2053]

Chế độ được chọn bằng một bit của thanh ghi ``RKNN_pc_base_address`` (``0x0010``):

   "pc_sel ... 1'd0: PC mode, use AXI DMA to fetch register config; 1'd1: Slave mode, use AHB to set register." [T1 TRM1 tr.1994]

.. list-table:: So sánh hai chế độ
   :header-rows: 1
   :widths: 20 40 40

   * - Tiêu chí
     - Slave configured mode
     - PC mode
   * - Ai ghi thanh ghi
     - CPU ghi từng thanh ghi qua giao diện AHB slave [T1 TRM1 tr.1985]
     - Register File Fetch Unit của NPU nạp cấu hình từ bộ nhớ hệ thống qua AXI [T1 TRM1 tr.1986]
   * - Bit chọn
     - ``pc_sel = 1``
     - ``pc_sel = 0``
   * - Chuẩn bị trước
     - Không cần danh sách trong RAM (suy ra từ định nghĩa)
     - Thông tin thanh ghi phải được tạo sẵn trong bộ nhớ hệ thống [T1 TRM1 tr.2053]
   * - Khởi động
     - Ghi thanh ghi bật NPU (``op_en``)
     - Ghi ``pc_op_enable`` để bắt đầu một nhóm task [T1 TRM1 tr.2053]

Giao diện cấu hình AHB chỉ hỗ trợ truy cập đơn (``single``) [T1 TRM1 tr.1984], còn AXI master dùng để nạp dữ liệu từ bộ nhớ nối vào SoC AXI interconnect [T1 TRM1 tr.1985].

.. _fig-npu-pc-flow:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/thanh-ghi-va-che-do-cau-hinh/trm1-fig36-3-pc-flow.png
   :align: center
   :alt: Luồng PC mode từ khởi tạo thanh ghi trong bộ nhớ đến ghi pc_op_enable

   Luồng PC mode: khởi tạo thông tin thanh ghi trong bộ nhớ hệ thống, ghi ``pc_interrupt_clear`` và ``pc_interrupt_mask``, ghi ``pc_amount``, ``pc_addr``, ``pc_task_number``, ``pc_task_dma_base``, rồi ghi ``pc_op_enable``. Nguồn: [T1 TRM1 tr.2053, Fig. 36-3]

Phần còn lại của TRM mô tả luồng theo slave configured mode:

   "The information of registers initial to the system memory need to generate by the op you want to specify. And we describe the normal work flows by describe the slave configured mode." [T1 TRM1 tr.2053]

.. _fig-npu-conv-flow-1:

.. figure:: ../../../_assets/img/02-nen-tang-rk3588/01-phan-cung-npu/thanh-ghi-va-che-do-cau-hinh/trm1-fig36-4-convolution-flow-1.png
   :align: center
   :alt: Luồng cấu hình một phép convolution theo slave mode, gồm ghi pointer để bật ping-pong

   Luồng cấu hình một phép convolution ("Convolution flow 1"): ghi ``pc_interrupt_clear`` và ``pc_interrupt_mask``, ghi thanh ghi ``Pointer`` của mỗi module để bật hoặc tắt ping-pong, cấu hình CNA, DPU, tùy chọn PPU, rồi bật NPU. Nguồn: [T1 TRM1 tr.2054, Fig. 36-4]

Các flow Fig. 36-4 đến 36-7 (convolution 1, convolution 2, pooling, DPU flying mode) có chung khung: ghi clear và mask ngắt, ghi ``Pointer`` của các module định dùng, ghi thanh ghi của khối, ghi thanh ghi bật NPU [T1 TRM1 tr.2054-2057]. Cách TRM gọi tên (Figure 1-x) và số in (36-x) lệch nhau như đã nêu ở mục 1.1.

2.2 Driver dùng gì
------------------

Driver là bằng chứng thực tế về chế độ nào chạy được trên RK3588. Hàm commit ghi ``0x1`` vào ``PC_DATA_ADDR`` (``0x10``) với chú thích ``// switch to slave mode`` [T1 DRV rknpu_job.c:385-392]. Khớp ``pc_sel = 1`` ở bit 0 của ``0x10`` [T1 TRM1 tr.1994]. Ngay sau đó, driver từ chối job không có cờ PC:

   ``if (!(args->flags & RKNPU_JOB_PC)) { job->ret = -EINVAL; return job->ret; }`` [T1 DRV rknpu_job.c:394-397]

Kết luận (suy ra từ mã): bản 0.9.8 chỉ chạy PC mode. Slave mode có trong TRM nhưng driver này không có đường ghi từng thanh ghi cho tác vụ tính toán (toàn bộ hàm commit nằm ở [T1 DRV rknpu_job.c:272-427]). Cờ job: ``RKNPU_JOB_SLAVE = 0 << 0``, ``RKNPU_JOB_PC = 1 << 0`` [T1 DRV include/rknpu_ioctl.h:97-98].

Đường PC (``rknpu_job_subcore_commit_pc``) ghi theo thứ tự sau [T1 DRV rknpu_job.c:272-375]:

.. list-table:: Thứ tự ghi thanh ghi của driver trong PC mode
   :header-rows: 1
   :widths: 6 44 50

   * - Bước
     - Thanh ghi và giá trị
     - Dòng mã
   * - 1
     - ``PC_DATA_ADDR`` nhận ``regcmd_addr`` của task đầu
     - rknpu_job.c:346 hoặc 349
   * - 2
     - ``PC_DATA_AMOUNT`` nhận ``(regcfg_amount + 4 + scale - 1) / scale - 1``
     - rknpu_job.c:352-356
   * - 3
     - ``INT_MASK`` nhận ``int_mask`` của task cuối
     - rknpu_job.c:358
   * - 4
     - ``INT_CLEAR`` nhận ``int_mask`` của task đầu
     - rknpu_job.c:360
   * - 5
     - ``PC_TASK_CONTROL`` nhận ``((0x6 | task_pp_en) << 12) | task_number``
     - rknpu_job.c:362-363
   * - 6
     - ``PC_DMA_BASE_ADDR`` nhận ``task_base_addr``
     - rknpu_job.c:365
   * - 7
     - ``PC_OP_EN`` ghi ``0x1`` rồi ``0x0``
     - rknpu_job.c:371-372

Thứ tự này khớp Fig. 36-3 (clear và mask, rồi amount, addr, task_number, dma_base, cuối cùng op_enable).

Hai ví dụ số (suy ra từ công thức, giá trị đầu vào là giả định):

- Giả sử ``regcfg_amount = 100`` và ``scale = 2`` (RK3588) [T1 DRV rknpu_drv.c:187]. Với phép chia nguyên, giá trị ghi vào ``PC_DATA_AMOUNT`` là ``(100 + 4 + 2 - 1) / 2 - 1 = 51``.
- Giả sử job bật ping-pong (``task_pp_en = 1``) và có 5 task. ``PC_TASK_CONTROL`` nhận ``(0x7 << 12) | 5 = 0x7005``. Khi tắt ping-pong, giá trị là ``0x6005``.

Ba điểm mà TRM không giải thích được:

- ``(0x6 | pp) << 12`` đặt bit 12 là ``task_pp_en``, bit 13 là ``task_count_clear`` và bit 14 bằng 1. TRM ghi bit 31:14 là reserved [T1 TRM1 tr.1996], nên ý nghĩa bit 14 mà driver đặt: unknown. Đã tìm ở: TRM1 Ch36 tr.1997 và mã driver, từ khóa: ``task_con``, ``0x6``.
- Lý do chia ``amount`` cho ``scale`` và cộng ``RKNPU_PC_DATA_EXTRA_AMOUNT`` (4): unknown. TRM chỉ nói ``pc_data_amount`` là số register của một task, mỗi register 64 bit [T1 TRM1 tr.1994]. Đã tìm ở: TRM1 Ch36, Ch1, Ch9 NPU_M0 và mã driver, từ khóa: ``scale``, ``EXTRA_AMOUNT``, ``amount``.
- ``int_mask`` do userspace điền trong ``struct rknpu_task``, driver không tự gán [T1 DRV include/rknpu_ioctl.h:226].

.. _sec-npu-ping-pong:

3. Ping-pong
============

3.1 TRM
-------

   "In order to reduce the time of fetch registers, every Calculate Core and Control Core of RKNN has its owner ping-pong registers. Configure the group 0 when use the group 1, and configure the group 1 when use group 0. ... Writing S_POINTER of every block can enable this function." [T1 TRM1 tr.2052]

(Nguyên văn TRM là "owner", không phải "own".) Có hai tầng ping-pong cần phân biệt.

**Tầng 1, trong từng block (thanh ghi ``S_POINTER``).** Mỗi block có hai group thanh ghi. Các trường điều khiển:

.. list-table:: Trường của ``RKNN_cna_s_pointer`` (5 block khác cùng định nghĩa)
   :header-rows: 1
   :widths: 22 12 66

   * - Trường
     - Bit
     - Mô tả của TRM
   * - ``pointer_pp_en``
     - 1
     - Register group ping-pong enable. 0 tắt, 1 bật [T1 TRM1 tr.1998]
   * - ``executer_pp_en``
     - 2
     - Executer group ping-pong enable. 0 tắt, 1 bật [T1 TRM1 tr.1998]
   * - ``pointer_pp_mode``
     - 3
     - 0: pointer đổi theo executer. 1: pointer đổi theo pointer [T1 TRM1 tr.1998]
   * - ``pointer``
     - 0
     - Group nào sẵn sàng để được ghi: 0 là group 0, 1 là group 1 [T1 TRM1 tr.1999]
   * - ``executer``
     - 16 (RO)
     - Group nào đang được dùng để chạy [T1 TRM1 tr.1998]

Thanh ghi ``operation_enable`` là ranh giới của vùng bóng (shadow):

   "op_en: Set this register will trigger CNA block operate. This register and after this are all shadowed for ping-pong operation." [T1 TRM1 tr.1999]

Từ ``operation_enable`` trở đi, mọi thanh ghi của block có hai bản, một cho mỗi group. ``s_status`` và ``s_pointer`` thì không (suy ra từ câu trên). ``s_status`` báo trạng thái hai executer: 0 là idle, 1 là đang chạy, 2 là đang chạy và executer kia chờ [T1 TRM1 tr.1998].

**Tầng 2, ở cấp PC task (``task_pp_en``).**

   "task_pp_en: PC task ping-pong mode enable. 1'd0: Ping-pong mode off. The second group register setting is fetched after first group task operation is finished; 1'd1: Tasks' registers are fetched in ping-pong mode. The second group register setting is fetched immediately after first group's register fetching is finished." [T1 TRM1 tr.1997]

Hiệu quả: khi tắt, cấu hình task thứ hai chỉ được nạp sau khi task thứ nhất chạy xong. Khi bật, nó được nạp ngay sau khi nạp xong task thứ nhất, nên thời gian nạp bị giấu sau thời gian tính. Mỗi flow Fig. 36-4 đến 36-7 đều có bước "Write Pointer register of every module decide to use to enable ping-pong register or not" [T1 TRM1 tr.2054].

3.2 Driver
----------

Ở mức job, cờ ``RKNPU_JOB_PINGPONG = 1 << 2`` quyết định ``task_pp_en`` [T1 DRV include/rknpu_ioctl.h:101] [T1 DRV rknpu_job.c:292].

Khi RK3588 chạy nhiều core (``num_irqs > 1``), driver ghi hai thanh ghi ``s_pointer``:

.. code-block:: c

   if (i == core_index) {
       REG_WRITE((0xe + 0x10000000 * i), 0x1004);
       REG_WRITE((0xe + 0x10000000 * i), 0x3004);

(trích từ [T1 DRV rknpu_job.c:305-311]). Giá trị ``0xe`` là bit 1, 2, 3, tức ``pointer_pp_en``, ``executer_pp_en`` và ``pointer_pp_mode`` (phần giải mã là suy ra, đối chiếu [T1 TRM1 tr.1998]). Chỉ CNA (``0x1004``) và CORE (``0x3004``) được ghi. Không thấy driver ghi ``0x4004``, ``0x5004``, ``0x6004``, ``0x7004`` [T1 DRV rknpu_job.c:308-309].

Hai điểm chưa có lời giải:

- Phần ``0x10000000 * i`` đặt bit 28 trở lên theo chỉ số core, rơi vào vùng bit 31:17 mà TRM ghi là reserved. Ý nghĩa: unknown. Đã tìm ở: TRM1 Ch36 và mã driver, từ khóa: ``0x10000000``.
- Các block DPU, PPU có bật ping-pong hay không phụ thuộc nội dung regcmd do userspace sinh, không nằm trong driver. Unknown. Đã tìm ở: mã driver ``*.c`` và ``include/*.h``, từ khóa: ``0x4004``, ``0x6004``, ``s_pointer``.

.. _sec-npu-ngat:

4. Ngắt
=======

4.1 TRM
-------

   "RKNN has 3 interrupt output signal and it remains asserted until the host processor clears the interrupt. Each bit of PC_INTERRUPT_STATUS represents one of the 17 possible events that the RKNN can signal to the host processor." [T1 TRM1 tr.2053]

Ba thanh ghi điều khiển nằm trong block PC: ``mask`` (cho phép sự kiện nào phát ngắt), ``status`` (trạng thái sau mask, W1C), ``raw_status`` (trạng thái trước mask). ``clear`` xóa bit. Với PC mode có một ghi chú:

   "Note: In pc mode, int mask set the last one task's interrupt masking." [T1 TRM1 tr.1995]

4.2 Các bit
-----------

Mask và clear nằm ở tr.1995, status và raw_status ở tr.1996. Mô tả bit giống nhau ở cả bốn thanh ghi. Có 17 bit ``[16:0]``, reset của mask là ``0x0001FFFF`` [T1 TRM1 tr.1986], nhưng TRM chỉ đặt tên cho 14 bit:

.. _tbl-npu-int-bits:

.. list-table:: Bit của ``pc_interrupt_*``
   :header-rows: 1
   :widths: 14 56 30

   * - Bit
     - Sự kiện
     - Nguồn
   * - 0, 1
     - CNA feature group 0, group 1
     - [T1 TRM1 tr.1995]
   * - 2, 3
     - CNA weight group 0, group 1
     - [T1 TRM1 tr.1995]
   * - 4, 5
     - CNA csc group 0, group 1
     - [T1 TRM1 tr.1995]
   * - 6, 7
     - CORE group 0, group 1
     - [T1 TRM1 tr.1995]
   * - 8, 9
     - DPU group 0, group 1
     - [T1 TRM1 tr.1995]
   * - 10, 11
     - PPU group 0, group 1
     - [T1 TRM1 tr.1995]
   * - 12
     - DMA read error
     - [T1 TRM1 tr.1995]
   * - 13
     - DMA write error
     - [T1 TRM1 tr.1995]
   * - 14, 15, 16
     - unknown. Nằm trong field ``[16:0]`` nhưng không có tên. Đã tìm ở: TRM1 Ch36, Ch1, Ch9 NPU_M0, từ khóa: ``mask[14``, ``int_st[14``
     - [T1 TRM1 tr.1995]

Bit 31:17 là reserved. Hai chi tiết nhỏ: ``raw_status`` dùng nhãn ``int_st[n]`` thay vì ``int_raw_st[n]`` (sao chép nhãn), và hai trường ``[12]``, ``[13]`` trong ``task_status`` bị TRM ghi trùng [T1 TRM1 tr.1996] [T1 TRM1 tr.1997].

Cặp "group 0 / group 1" khớp với hai nhóm thanh ghi ping-pong ở mục 3. TRM không nói thẳng như vậy, đây là suy ra.

4.3 Nối ngắt với core
---------------------

Trong Ch36 của TRM, không có câu nào nối "3 interrupt output" với core 0, 1, 2. Đã tìm ở: TRM1 Ch36 tr.1984-2057, từ khóa: ``interrupt``, ``irq``. Thông tin nằm ở chỗ khác:

.. list-table:: Ba nguồn ngắt của NPU
   :header-rows: 1
   :widths: 22 18 18 42

   * - Nguồn
     - Số trong TRM1 Table 1-3
     - ``GIC_SPI`` trong DTS
     - Ghi chú
   * - ``irq_rknn_c0``
     - 142
     - 110
     - High level [T1 TRM1 tr.24] [T1 DTS dts/rk3588s.dtsi:3455-3457]
   * - ``irq_rknn_c1``
     - 143
     - 111
     - High level [T1 TRM1 tr.24] [T1 DTS dts/rk3588s.dtsi:3455-3457]
   * - ``irq_rknn_c2``
     - 144
     - 112
     - High level [T1 TRM1 tr.24] [T1 DTS dts/rk3588s.dtsi:3455-3457]

Hiệu 142 trừ 110 bằng 32, tương tự cho hai cặp còn lại, nhất quán với quy ước "số SPI bằng số trong bảng trừ 32". Đây là phép suy ra từ ba cặp số, TRM Ch1 không nêu công thức. Tên nguồn có hậu tố c0, c1, c2 nhưng TRM không viết "mỗi ngắt thuộc một core" [T1 TRM1 tr.24].

MCU NPU_M0 cũng nhận ba ngắt này trực tiếp, không qua INTMUX, với IRQ ID 4 (``C0_RKNN``), 5 (``C1_RKNN``), 6 (``C2_RKNN``) [T1 TRM1 tr.1298]. Ở mức driver, ánh xạ rõ ràng:

   ``{ "npu0_irq", rknpu_core0_irq_handler }, { "npu1_irq", rknpu_core1_irq_handler }, { "npu2_irq", rknpu_core2_irq_handler }`` [T1 DRV rknpu_drv.c:84-88]

Ngắt thứ i dùng handler của core i và đọc thanh ghi của ``base[core_index]`` [T1 DRV rknpu_job.c:640-643]. Vậy "ngắt i thuộc core i" là bằng chứng ở mức driver và DTS, không phải câu của TRM.

4.4 Driver xử lý
----------------

Handler ngắt đọc và xóa trạng thái theo các bước sau [T1 DRV rknpu_job.c:640-682]:

1. Nếu không có job, ghi ``RKNPU_INT_CLEAR`` (``0x1ffff``) vào ``INT_CLEAR`` rồi thoát [T1 DRV rknpu_job.c:653-657].
2. Nếu có job, đọc ``INT_STATUS`` và lưu vào ``job->int_status[core_index]`` [T1 DRV rknpu_job.c:662-664].
3. So ``rknpu_fuzz_status(status)`` với ``job->int_mask[core_index]``. Nếu khác, log "invalid irq status" và clear [T1 DRV rknpu_job.c:666-675].
4. Nếu khớp, ghi ``RKNPU_INT_CLEAR`` vào ``INT_CLEAR`` rồi gọi ``rknpu_job_done`` [T1 DRV rknpu_job.c:677-679].

``rknpu_fuzz_status`` gộp từng cặp bit liền kề với các mặt nạ ``0x3``, ``0xc``, ``0x30``, ``0xc0``, ``0x300``, ``0xc00`` [T1 DRV rknpu_job.c:615-638]. Nghĩa là bit 0 đến 11 được xử lý theo 6 cặp group 0/1, nhất quán với bảng bit ở mục 4.2. Bit 12 và 13 (DMA error) không tham gia phép so với ``int_mask`` (suy ra từ mã). Vì vậy không thể nói driver phát hiện lỗi DMA qua nhánh "invalid irq status".

Ba chi tiết còn lại:

- Mask ghi vào thanh ghi là mask của task cuối, thanh ghi clear nhận mask của task đầu [T1 DRV rknpu_job.c:358-360]. Khớp ghi chú "In pc mode, int mask set the last one task's interrupt masking" [T1 TRM1 tr.1995].
- Khi timeout, driver log ``INT_STATUS``, ``INT_RAW_STATUS``, ``job->int_mask`` và bộ đếm task đọc ở ``0x3c`` với mặt nạ ``0xfff`` [T1 DRV rknpu_job.c:591-601], khớp ``RKNN_pc_task_status[11:0]`` [T1 TRM1 tr.1997].
- Job nhiều đợt: ``max_submit_number = (1 << 12) - 1`` [T1 DRV rknpu_drv.c:196] và ``rknpu_job_done`` commit lại khi chưa đủ số đợt [T1 DRV rknpu_job.c:466-472], khớp ``task_number`` 12 bit [T1 TRM1 tr.1997].

5. Hiểu sai thường gặp
======================

.. list-table::
   :header-rows: 1
   :widths: 28 50 22

   * - Hiểu sai
     - Thực tế theo nguồn
     - Nguồn
   * - Driver chọn giữa slave mode và PC mode tùy job.
     - Bản 0.9.8 trả ``-EINVAL`` cho job không có cờ PC, nên chỉ chạy PC mode.
     - [T1 DRV rknpu_job.c:394-397]
   * - GLOBAL chỉ có hai thanh ghi tại ``0xf000`` và ``0xf004``.
     - Table 1-1 ghi như vậy nhưng thanh ghi được mô tả duy nhất nằm ở ``0xF008``. TRM tự mâu thuẫn.
     - [T1 TRM1 tr.1986] [T1 TRM1 tr.2052]
   * - TRM có "Figure 1-3" riêng cho PC flow.
     - Văn bản gọi Figure 1-3, hình in là Fig. 36-3. Các flow slave là Fig. 36-4 đến 36-7.
     - [T1 TRM1 tr.2053]
   * - 17 sự kiện ngắt đều có mô tả.
     - Chỉ bit 0 đến 13 có tên. Bit 14, 15, 16 nằm trong ``[16:0]`` nhưng không được mô tả.
     - [T1 TRM1 tr.1995]
   * - Ping-pong là một cờ duy nhất.
     - Có hai tầng: ``S_POINTER`` trong từng block và ``task_pp_en`` ở cấp PC task.
     - [T1 TRM1 tr.1998] [T1 TRM1 tr.1997]
   * - TRM nói ngắt c0 thuộc core 0.
     - TRM chỉ có tên ``irq_rknn_c0`` đến ``c2``. Ánh xạ ngắt i sang core i là của driver và DTS.
     - [T1 TRM1 tr.24] [T1 DRV rknpu_drv.c:84-88]
   * - Driver bắt được lỗi DMA bằng nhánh "invalid irq status".
     - ``rknpu_fuzz_status`` bỏ bit 12 và 13 nên chúng không tham gia phép so với ``int_mask`` (suy ra từ mã).
     - [T1 DRV rknpu_job.c:615-638]

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
     - 87
   * - ``DRV``
     - T1
     - ``3rdparty/rknpu-driver-0.9.8/`` (commit f6eedab0 theo SOURCE.txt)
     - 31
   * - ``DTS``
     - T1
     - ``3rdparty/rknpu-driver-0.9.8/dts/rk3588s.dtsi``
     - 4
