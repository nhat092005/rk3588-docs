:tocdepth: 1

*************************
RK3588: cấu trúc NPU core
*************************

.. admonition:: Trang này trả lời

   - bên trong một core có những khối nào?
   - NPU tính được các kiểu số nào, nhanh bao nhiêu?
   - mỗi core có bộ nhớ riêng bao nhiêu, chia thế nào?
   - NPU hỗ trợ những phép nào ở mức thanh ghi?

.. admonition:: Tóm tắt

   - Một core gồm CNA, MAC array với accumulator, DPU và PPU, còn TRM không khai triển chữ "CNA" [T1 TRM1 tr.1985].
   - TRM ghi "1024x3 integer 8 MAC operations per cycle" và hỗ trợ integer 4, integer 8, integer 16, float 16, Bfloat 16 và tf32 [T1 TRM1 tr.1984].
   - TRM không nói MAC array có bỏ phép nhân 0 hay không, chỉ mô tả zero-skipping qua việc không fetch weight khi feature bằng 0 [T1 TRM1 tr.2006].
   - "384KBx3 internal buffer" nghĩa là 384KB cho mỗi core, ba core, chia bank giữa weight và feature, còn kích thước mỗi bank là `unknown` [T1 TRM1 tr.1984, tr.2004].
   - "6 TOPS" không được viết như kết quả suy ra vì Datasheet ghi tần số tối đa của NPU là `TBD` [T1 DS tr.31].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _23-cấu-trúc-một-npu-core:

Cấu trúc một NPU core
=====================

**Câu hỏi:** bên trong một core có những khối nào?

**Nguồn nói gì** (TRM1 tr.1985, Fig. 36-2 và mục 36.3)

   "This unit include convolution pre-process controller, internal buffer, mac array, accumulator." [T1 TRM1 tr.1985]

..

   "Data Processing Unit mainly process the single data calculate, such as leaky_relu, relu, relux, sigmoid, tanh" [T1 TRM1 tr.1985]

   "It also provides function: softmax, transpose, data format conversion" [T1 TRM1 tr.1985]

..

   "Planar Processing Unit mainly provide planar function followed by output data from Data Processing Unit, such as average pooling, max pooling, min pooling" [T1 TRM1 tr.1985]

   "Register File Fetch Unit fetch register configuration from external system memory through AXI" [T1 TRM1 tr.1986]

Sơ đồ Fig. 36-2 (TRM1 tr.1985, đã đọc từ ảnh trang): khối CNA chứa Weight Decompress, Zero-Skipping, Weight Data Load và Feature Data Load. Ngoài khung CNA là 384KB Buffer, Sequence Controller, MAC Array, Accumulator, DPU, PPU, Register File Fetch và Config Interface (AHB).

Luồng tính toán chọn khối xử lý:

   "If use the MAC array to calculate, the work flow should obey the Figure 1-4, and if use DPU CORE calculate, work flow should obey the Figure 1-5." [T1 TRM1 tr.2053] (Văn bản TRM đánh số "Figure 1-3", "Figure 1-4", "Figure 1-5" cho các hình được in là Fig. 36-3, 36-4 và 36-5. Fig. 36-5 là "Convolution flow 2" (TRM1 tr.2055), hình này chưa được nhúng ở file này.)

Zero-skipping:

   "Enable skip some feature data value, normally skip zero. When one pixel feature data is 0, the corresponding weight data is not fetched from system memory." [T1 TRM1 tr.2006, thanh ghi ``fc_skip_en``]

..

   "If enable zero skipping, the conv_mode of DPU must configure to be 3, and must bypass the BS_CORE." [T1 TRM1 tr.2055]

|TRM1 Fig 36-2| *Hình 2.3. Kiến trúc một NPU core: CNA (Weight Decompress, Zero-Skipping, Weight Data Load, Feature Data Load), 384KB Buffer, Sequence Controller, MAC Array, Accumulator, DPU, PPU. Nguồn: [T1 TRM1 tr.1985, Fig. 36-2]*

**Ý chính**

- Một core gồm đường vào dữ liệu (CNA), MAC array với accumulator, DPU cho các phép theo phần tử, và PPU cho pooling (TRM1 tr.1985). Chữ "CNA" xuất hiện trong sơ đồ nhưng TRM không khai triển tên.
- Thanh ghi ``fc_skip_en`` được TRM mô tả là "FC zero skipping enable" (tiền tố "FC" không được khai triển) và tác dụng là bỏ fetch weight tương ứng khi feature bằng 0 (TRM1 tr.2006). Flow ở tr.2055 nói "We bypass BS_CORE, and use BN_CORE to calculate convolution" và đặt ``conv_mode`` của DPU bằng 3, là "Depthwise convolution mode" (TRM1 tr.2017). Tổng hợp của file này: TRM mô tả zero-skipping qua việc không fetch weight và một đường đi qua DPU. TRM không nói MAC array có bỏ phép nhân 0 hay không. Không dùng nội dung này để khẳng định hay phủ định cơ chế bỏ MAC ở :ref:`Sparsity và zero-skipping <17-sparsity-và-zero-skipping>` của :doc:`NPU và phần cứng </kien-thuc-nen/npu/index>`.

**Giới hạn.** TRM không khai triển các chữ BS, BN, CMAC, CSC, CBUF, DDMA, SDMA. Riêng EW có gợi nghĩa "element wise" ở một mô tả thanh ghi (TRM1 tr.2035). Định dạng nén weight mà khối Weight Decompress hỗ trợ là ``unknown``: TRM chỉ có thanh ghi ``wt_dec_bypass`` và ``decomp_control`` (TRM1 tr.2009).

--------------

.. _24-kiểu-số-và-số-mac-trên-mỗi-chu-kỳ:

Kiểu số và số MAC trên mỗi chu kỳ
=================================

**Câu hỏi:** NPU tính được các kiểu số nào, nhanh bao nhiêu?

**Nguồn nói gì**

   "Support integer 4, integer 8, integer 16, float 16, Bfloat 16 and tf32 operation" [T1 TRM1 tr.1984]

.. list-table::
   :header-rows: 1

   * - Kiểu
     - Nguyên văn (TRM1 tr.1984)
   * - INT8
     - "1024x3 integer 8 MAC operations per cycle"
   * - INT16
     - "512x3 integer 16 MAC operations per cycle"
   * - FP16
     - "512x3 float 16 MAC operations per cycle"
   * - BF16
     - "512x3 bfloat 16 MAC operations per cycle"
   * - TF32
     - "256x3 tf32 MAC operation per cycle"
   * - INT4
     - "2048x3 integer 4 MAC operation per cycle"

..

   "In int8, 32 kernels form 1 group, in int16 or fp16, 16 kernels form 1 group." [T1 TRM1 tr.2000, thanh ghi ``kernel_group``]

   "Int8 mac array 32x32 mode" [T1 TRM1 tr.2001, thanh ghi ``nn_mode``]

..

   "The build-in NPU supports INT4/INT8/INT16/FP16 hybrid operation and computing power is up to 6TOPs." [T1 DS tr.7]

**Ý chính**

- Mã hóa precision trong thanh ghi: INT8, INT16, FP16, BF16, INT4 và TF32 (TRM1 tr.2000, 2014).
- Hệ số "x3" khớp với ba core. TRM không viết chữ "per core".
- Với INT8 mỗi core có chế độ MAC array 32x32 (``1024 = 32 x 32``, TRM1 tr.2001). Tổng hợp của file này: con số 1024 và chế độ 32x32 cùng một giá trị. TRM không nêu bố cục cho INT16, FP16, INT4.

**Ở mức SDK trên RK3588**

- API Reference V2.3.2 mặc định ``quantized_dtype`` là "w8a8" (tr.7). ``w4a16`` "(Only RK3576/RV1126B supported)", ``w16a16i`` "(Only RV1103/RV1106 supported)" (tr.7). Vì vậy không viết "RK3588 chạy model INT4, BF16, TF32 qua ``rknn.config``". Ngoại lệ ở đường khác: Matmul C API hỗ trợ ba kiểu dữ liệu "int4, int8 and float16" (UG232 tr.41), và Table 3-5 của UG232 (tr.49) có bố cục INT4 cho cột RK3588 (A int4 ``[K/32,M,32]``, B int4 ``[N/64,K/32,64,32]``, C int16 ``[N/8,M,8]``) trong khi RK3562 và RK3566/RK3568 ghi "unsupported". Chưa thấy nguồn SDK nào cho BF16 hay TF32. Chi tiết xem file ``04_``.

**Giới hạn.** Không viết "6 TOPS" như kết quả suy ra trong tài liệu vendor: Datasheet ghi tần số tối đa của NPU là ``TBD`` (DS tr.31) và TRM không nêu quy ước đếm phép tính. Tần số 1 GHz chỉ xuất hiện trong ví dụ đầu ra ``eval_perf`` (UG232 tr.31, "NPU Current Frequency List: - 1000000000", tùy firmware) và ví dụ lệnh cố định tần số (UG152 tr.73), không phải tần số tối đa hay mặc định. Quy ước chung "TOPS defined as twice the number of MAC units multiplied by the clock frequency" có trong một paper (T2 BAMB tr.1, NXP eIQ Neutron), không riêng RK3588. Các tài liệu cũng không thống nhất: TRM1 36.1 viết "tf32", mục 36.3.2 viết "tf16". DS tr.7 liệt kê 4 kiểu, mục 1.2.6 (DS tr.11) thêm Bfloat16 và tf32 ().

--------------

.. _26-buffer-384kb-trong-mỗi-core:

Buffer 384KB trong mỗi core
===========================

**Câu hỏi:** mỗi core có bộ nhớ riêng bao nhiêu, chia thế nào?

**Nguồn nói gì**

   "384KBx3 internal buffer" [T1 TRM1 tr.1984]

..

   "Embedded 384KBx3 internal buffer" [T1 DS tr.11]

Thanh ghi ``weight_bank``, ``data_bank`` (TRM1 tr.2004) chia buffer thành các bank, ví dụ ``4'd7`` là "Bank 1-7 occupied by weight data" và ``4'd6`` là "Bank 0-6 occupied by feature data". Thanh ghi ``data_reuse``: "fetching data directly from internal buffer" [T1 TRM1 tr.2004].

**Ý chính.** ``384KBx3`` nghĩa là 384KB cho mỗi core, ba core: Fig. 36-2 (đơn lõi, TRM1 tr.1985) vẽ "384KB Buffer" bên trong một NPU CORE. Buffer được chia theo bank giữa weight và feature (TRM1 tr.2004).

**Giới hạn.** Kích thước mỗi bank là ``unknown``. Chia 384/8 = 48KB là suy luận, không phải T1. Không viết con số đó.

--------------

.. _210-dpu-chế-độ-conv-matmul-và-layout:

DPU, chế độ conv, matmul và layout
==================================

**Câu hỏi:** NPU hỗ trợ những phép nào ở mức thanh ghi?

**Nguồn nói gì**

   "RKNN supports variety of convolution and matrix multiplication." [T1 TRM1 tr.2053]

DPU (xem 2.3) xử lý các hàm theo phần tử như ``relu``, ``sigmoid``, ``tanh``, cùng ``softmax``, ``transpose`` và chuyển định dạng dữ liệu (TRM1 tr.1985). Ở mức thanh ghi, TRM1 tr.2000 có chế độ "Depthwise convolution" (``conv_mode``), tr.2001 có các trường atrous (dilation) và deconv, tr.1999 có ``nonalign_dma`` và ``argb_in``.

Native layout NC1HWC2: UG152 tr.56 mô tả "a special memory arrangement. The memory address from low to high is C2->W->H->C1->N". Table 4-6 cùng trang cho hàng RK3588 các giá trị ``16 8 8`` (cột int8, float16, int16, so với ``8 4 4`` của RK3566/RK3568). Đây là giá trị C2 theo chip. ý nghĩa đầy đủ xem file ``06_`` (UG232 tr.61).

**Giới hạn.** Quan hệ giữa các chữ viết tắt thanh ghi (BS, BN, EW) và tên op trong Operator List là ``unknown``. Danh sách op thực sự chạy trên NPU RK3588 nằm ở Operator List, xem :doc:`Toolchain và compiler </kien-thuc-nen/toolchain-compiler/index>`.

--------------

.. |TRM1 Fig 36-2| image:: ../../_assets/img/npu/02_rk3588_npu_hardware/trm1_p1985_fig36-2.png

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
     - 15
   * - ``DS``
     - T1
     - :download:`02_RK3588_Datasheet_V0.1-20210727.pdf <../../_assets/pdf/papers/05_rk3588/01_vendor_docs/01_datasheet/02_RK3588_Datasheet_V0.1-20210727.pdf>`
     - 2
