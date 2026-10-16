:tocdepth: 1

************************
Fusion, layout và tiling
************************

.. admonition:: Trang này trả lời

   - toolkit gộp op thế nào, và người dùng can thiệp được đến đâu?
   - dữ liệu được xếp thế nào trong bộ nhớ NPU, và có yêu cầu căn lề gì?
   - compiler của NPU nói chung làm gì ngoài việc dịch op?

.. admonition:: Tóm tắt

   - Toolkit có tự tối ưu đồ thị nhưng "not omnipotent and perfect" [T1 UG232 tr.141], nên người dùng có thể đổi thứ tự op để tạo cặp fusion mà phần cứng hỗ trợ.
   - Thứ tự pass, quy tắc fusion thực tế và thuật toán chọn fuse là unknown; T1 chỉ có tên pass trong log lỗi và tên hàm trong traceback [T1 UG232 tr.168].
   - OPL 3.2.19 viết Relu(Add(Conv(...))) còn UG232 tr.142 liệt kê Conv+Activation+Add, và OPL coi AddRelu, MulRelu là hỗ trợ trong khi UG232 tr.142 xếp Add(Mul)+Activation vào kế hoạch tương lai.
   - Layout NC1HWC2 có C1 là giá trị làm tròn lên của C/C2; với RK3588 cột chung RK3576/RK3588/RV1126B ghi C2 là 16 cho int8 và 8 cho float16 [T1 UG232 tr.61].
   - Có nhiều khái niệm alignment khác nhau, căn lề kênh là "not mandatory" [T1 UG232 tr.144]; cách chọn C2 và C1 cho từng tensor là unknown.
   - Các bài T2 về fusion và tiling không nói về compiler của Rockchip; số "1.2x đến 2x" của TVM đo trên GPU Titan X, không áp dụng cho NPU RK3588.

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _63-fusion-và-tối-ưu-đồ-thị:

Fusion và tối ưu đồ thị
=======================

**Câu hỏi:** toolkit gộp op thế nào, và người dùng can thiệp được đến đâu?

**Nguồn nói gì**

   "In the RKNN-Toolkit2 toolchain, the software stack already performs graph optimization to a certain extent during the model conversion process. However, this process is not omnipotent and perfect." [T1 UG232 tr.141]

..

   "NPU supports fusion of some operators, and the operation process of some operators can be appropriately adjusted to adapt to the fusion rules of NPU." [T1 UG232 tr.141]

   "The RKNN software stack will match certain graph relationships into custom operators" [T1 UG232 tr.147]

..

   "Model optimization level. The default value is 3." [T1 API232 tr.8]

   "When the value is 2 or 1, turn off some optimization options that may affect the accuracy of some models. Turn off all optimization options when the value is 0." [T1 API232 tr.8]

..

   "Try to reduce the following three types of operators in the model" [T1 UG232 tr.146]

Luật fusion phần cứng (UG232 tr.142):

.. list-table::
   :header-rows: 1

   * - Đã hỗ trợ
     - Kế hoạch tương lai
   * - Conv+Relu
     - Activation+Add(Mul)
   * - Conv+PRelu(LeakyRelu)
     - Add(Mul)+Activation
   * - Conv+Clip
     - Conv+Mul
   * - Conv+Sigmoid(Tanh/Elu/Silu...)
     - Conv+Activation+Mul
   * - Conv+Add
     - Conv+Activation+Pooling
   * - Conv+Activation+Add
     - Conv+Activation+Add(Mul)+Pooling

Ba loại op kém hiệu quả theo Table 8-5 (UG232 tr.146): chuyển dữ liệu (Transpose, Reshape, Split, Concat), đổi kích thước (Resize, Tile, Pooling, Pad), activation không phải Relu (Sigmoid, Tanh, Softplus, Hardswish).

Operator List cũng có các op hợp nhất cho RK3588, ví dụ ``Convolution 与 Relu 融合计算`` (mục 3.2.7) và ``Convolution 与 Swish 融合计算`` (mục 3.2.17), cùng ConvolutionClip, ConvolutionPRelu/LeakyRelu, ConvolutionAdd, ConvolutionSigmoid, ConvolutionHardSwish, ConvolutionMish và ConvolutionAddRelu (PDF 60 đến 63).

|UG232 Figure 8-7| *Hình 6.3. Đổi thứ tự Transpose và Clip để Conv và Clip hợp nhất bằng phần cứng, kèm bảng luật fusion phần cứng. Nguồn: [T1 UG232 tr.142, Figure 8-7]*

**Ý chính**

- Toolkit có tự tối ưu đồ thị nhưng không đầy đủ. Người dùng có thể đổi thứ tự op để tạo cặp fusion mà phần cứng hỗ trợ (UG232 tr.141, Figure 8-7).
- UG232 tr.142 chỉ ghi "The hardware fusion rules are as follows" và không nêu chip. Tổng hợp của file này: "Conv+Sigmoid(Tanh/Elu/Silu...)" cho thấy SiLU nằm trong họ fusion được hỗ trợ, nhưng bảng luật không nêu từng chip.
- ``optimization_level=2`` đưa Resize về CPU (UG232 tr.176, mục 10.8). Không tái hiện ở YOLOv8n INT8 thử trên board (xem :ref:`Điều chưa biết về compiler nội bộ của Rockchip <66-điều-chưa-biết-về-compiler-nội-bộ-của-rockchip>`).
- Các thay đổi cấu trúc model mà vendor gợi ý: thay Transpose và Reshape bằng Conv trong ví dụ shufflenet, gộp Slice vào Conv trong YOLOv5-nano (UG232 tr.141, 142).

**Giới hạn**

- Thứ tự pass, quy tắc fusion thực tế và thuật toán chọn fuse là ``unknown``. T1 chỉ có tên pass trong log lỗi (UG232 tr.168: ``RKNNInitCastConst``, ``RKNNMultiSurfacePass``, ``RKNNTilingPass``, ``RKNNProfileAnalysisPass``, ``OpEmit``) và tên hàm trong traceback (``graph_optimizer._fuse_ops``, UG232 tr.166).
- OPL 3.2.19 viết ``Relu(Add(Conv(...)))`` còn UG232 tr.142 liệt kê ``Conv+Activation+Add`` (thứ tự khác). Hai nguồn không thống nhất.
- Operator List coi "Add(Mul)+Relu" là hỗ trợ (AddRelu, MulRelu) trong khi UG232 tr.142 xếp "Add(Mul)+Activation" vào cột kế hoạch tương lai.

--------------

.. _64-layout-nc1hwc2-và-các-kiểu-alignment:

Layout NC1HWC2 và các kiểu alignment
====================================

**Câu hỏi:** dữ liệu được xếp thế nào trong bộ nhớ NPU, và có yêu cầu căn lề gì?

**Nguồn nói gì**

   "As shown in Figure 5-1, the number 0 represents the storage of C2 data block, where C2 is determined by the platform." [T1 UG232 tr.61]

..

   "C1 is the rounded-up value of C/C2." [T1 UG232 tr.61]

   "Take the RK3568 platform as an example, the corresponding NC1HWC2 is (1, 2, 4, 4, 8) when the int8 feature data is (1, 13, 4, 4). In this case, C2 is 8, C1 is 2." [T1 UG232 tr.61]

..

   "These rules are not mandatory." [T1 UG232 tr.144]

   "该对齐约束仅针对零拷贝 API，普通 API 无此对齐约束" [T1 OPL tr.335] (Ràng buộc căn lề này chỉ cho zero-copy API, API thường không có.)

Table 5-1 (UG232 tr.61): C2 theo nền tảng, cột RK3576/RK3588/RV1126B: ``int8`` = 16, ``float16`` = 8. So với cột RK3566/RK3568: 8 và 4.

Table 8-2 (UG232 tr.145), RK3588/RK3576/RV1126B, độ chia hết kênh để thân thiện với DDR (không bắt buộc):

.. list-table::
   :header-rows: 1

   * - Dtype
     - Conv input
     - Conv output
     - Depthwise Conv
     - Other OP
   * - Int8
     - 32
     - 32
     - 64
     - 16
   * - Float16
     - 32
     - 16
     - 32
     - 8

Operator List mục 5.2.2 (PDF 339), alignment output của RK3588 (tiếng Trung): ``int8``, layout NHWC: channel căn 16; ``int8``, NC1HWC2: "最后一层卷积类算子，32 对齐，最后一层非卷积类算子 16 对齐" (nếu lớp cuối là op họ Conv thì căn 32, nếu không phải op họ Conv thì căn 16; "卷积类" dịch là "họ Conv", danh sách op thuộc họ này nguồn không nêu ở chỗ này), và ``H*W`` căn 4. Với ``float16``, NHWC căn 8; NC1HWC2 lớp cuối là Conv căn 16, không phải Conv căn 8.

|UG232 Figure 5-1| *Hình 6.4. Định dạng NC1HWC2: C2 là khối kênh nằm liền nhau trong bộ nhớ, C1 là số khối. Table 5-1 liệt kê C2 theo chip. Nguồn: [T1 UG232 tr.61, Figure 5-1 và Table 5-1]*

**Ý chính**

- Có ít nhất bốn khái niệm "alignment" khác nhau, không gộp: C2 của layout (UG232 tr.61); căn lề width của input chỉ cho zero-copy API (OPL tr.335, và Table 5-2 của UG232 tr.65 cho RK3588 ghi "Width 16-byte aligned" khi số kênh là 1, 3 hoặc 4; xem ``07_``); căn lề output của lớp cuối (OPL tr.339, ghi chú 1: căn lề của output NHWC chỉ áp dụng khi phần chuyển đổi output do NPU thực hiện, "输出转换是 NPU 实现的"; ``float16`` NC1HWC2 còn yêu cầu ``H*W`` căn 4); và căn lề kênh để chạy hiệu quả, "not mandatory" (UG232 tr.144, 145). ``07_`` còn nêu căn lề SRAM 4K. Tổng hợp của file này: số 16 ở C2 của int8 trùng với số 16 của "Other OP" trong Table 8-2 và của lớp cuối không phải Conv ở OPL, nhưng nguồn không nói chúng là một đại lượng.
- Với RK3588 các số lấy từ cột chung RK3576/RK3588/RV1126B (UG232 tr.61, 145), không phải bảng riêng của RK3588.

**Giới hạn**

- Bảng input của RK3588 trong OPL mục 5.1.2 (PDF 336) là ảnh nhúng, không có văn bản. File này chưa trích bảng đó.
- Log mẫu trên RK3588 trong ``04_RK3588_NPU_SRAM_usage.md`` có ``NativeShape`` không khớp công thức ``C1 = ceil(C/C2)`` (ví dụ ``(1,512,7,7) -> (1,33,7,7,16)``). Không nguồn nào giải thích; có thể là log từ cấu hình khác. ``unknown``.
- Cách chọn C2 và C1 cho từng tensor: ``unknown``.

--------------

.. _65-tiling-và-scheduling-trong-các-bài-t2-chỉ-ngữ-cảnh-chung:

Tiling và scheduling trong các bài T2 (chỉ ngữ cảnh chung)
==========================================================

**Câu hỏi:** compiler của NPU nói chung làm gì ngoài việc dịch op?

**Nguồn nói gì**

   "Operator fusion combines multiple operators into a single kernel without saving the intermediate results in memory." [T2 TVM tr.3]

..

   "We find that fused operators generate up to a 1.2× to 2× speedup by reducing memory accesses." [T2 TVM tr.4]

   "We then perform the proper layout transformation between a producer and a consumer if their preferred data layouts do not match." [T2 TVM tr.4]

..

   "Operator fusion is a scheduling method for combining multiple operations to minimize off-chip memory access." [T2 LEE24 tr.1]

   "Since the FM buffer (on-chip memory) is much smaller than dram, it is not possible to store the entire feature map at once." [T2 LEE24 tr.2]

..

   "the mid-end lowers and optimizes the graph through tiling, scheduling, and memory allocation" [T2 BAMB tr.4]

   "Formats are crucial for optimizing compute utilization." [T2 BAMB tr.5]

..

   "the compilers of commercial NPUs apply graph optimizations in unpredictable ways." [T2 LENS tr.1]

|TVM Figure 3| *Hình 6.5a. Đồ thị tính toán của một CNN hai lớp: mỗi nút là một op nhận một hoặc nhiều tensor. Nguồn: [T2 TVM tr.3, Figure 3]*

|TVM Figure 4| *Hình 6.5b. So sánh có và không fusion trong TVM (conv+bn+relu, depthwise-conv+bn+relu, rnn cell, lstm cell), đo trên NVIDIA Titan X. Nguồn: [T2 TVM tr.4, Figure 4]*

**Ý chính**

- Fusion nhằm giảm truy cập bộ nhớ ngoài; tiling vì buffer trên chip nhỏ hơn DRAM; layout phải đổi khi producer và consumer cần layout khác nhau (TVM tr.3, 4; LEE24 tr.1, 2).
- Số "1.2x đến 2x" của TVM đo trên GPU Titan X (chú thích Figure 4, TVM tr.4; cột depthwise-conv+bn+relu trong hình khoảng 2.3, lệch với "up to 2x" trong văn bản), không áp dụng cho NPU RK3588.

**Giới hạn.** Các bài này không nói gì về compiler của Rockchip. BAMB là compiler của NXP eIQ Neutron. LENS nói rằng compiler của NPU thương mại tối ưu theo cách khó đoán, nhưng là bài về dự đoán độ trễ LLM trên Inferentia2 và TPU.

--------------

.. |UG232 Figure 8-7| image:: ../../_assets/img/npu/06_compiler_operators/ug232_p142_fig8-7_fusion_rules.png

.. |UG232 Figure 5-1| image:: ../../_assets/img/npu/06_compiler_operators/ug232_p61_fig5-1_table5-1.png

.. |TVM Figure 3| image:: ../../_assets/img/npu/06_compiler_operators/tvm_p3_fig3.png

.. |TVM Figure 4| image:: ../../_assets/img/npu/06_compiler_operators/tvm_p4_fig4.png

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
   * - ``UG232``
     - T1
     - ``3rdparty/rknn-toolkit2/doc/02_Rockchip_RKNPU_User_Guide_RKNN_SDK_V2.3.2_EN.pdf`` (SDK trong repo chính)
     - 10
   * - ``TVM``
     - T2
     - :download:`tvm_compiler_2018chen.pdf <../../_assets/pdf/papers/03_compiler/tvm_compiler_2018chen.pdf>`
     - 5
   * - ``API232``
     - T1
     - :download:`01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf <../../_assets/pdf/papers/05_rk3588/01_vendor_docs/03_rknn_npu/01_Rockchip_RKNPU_API_Reference_RKNN_Toolkit2_V2.3.2_EN.pdf>`
     - 2
   * - ``LEE24``
     - T2
     - :download:`fused_layer_multiworkload_2024lee.pdf <../../_assets/pdf/papers/03_compiler/fused_layer_multiworkload_2024lee.pdf>`
     - 2
   * - ``BAMB``
     - T2
     - :download:`npu_compiler_codesign_2025bamberg.pdf <../../_assets/pdf/papers/03_compiler/npu_compiler_codesign_2025bamberg.pdf>`
     - 2
   * - ``OPL``
     - T1
     - :download:`03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf <../../_assets/pdf/papers/05_rk3588/01_vendor_docs/03_rknn_npu/03_RKNN_Compiler_Support_Operator_List_V2.3.2.pdf>`
     - 1
   * - ``LENS``
     - T2
     - :download:`npu_compiler_scheduling_2026.pdf <../../_assets/pdf/papers/03_compiler/npu_compiler_scheduling_2026.pdf>`
     - 1
