:tocdepth: 1

*************************************
Kỹ thuật tiling và lập lịch thực thi
*************************************

.. admonition:: Trang này trả lời

   - compiler của NPU nói chung làm gì ngoài việc dịch op?

.. admonition:: Tóm tắt

   - Các bài T2 về fusion và tiling không nói về compiler của Rockchip, số "1.2x đến 2x" của TVM đo trên GPU Titan X, không áp dụng cho NPU RK3588.

.. contents:: Trong trang này
   :local:
   :depth: 1

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

.. figure:: ../../../_assets/img/npu/06_compiler_operators/tvm_p3_fig3.png
   :align: center
   :alt: Đồ thị tính toán của một CNN hai lớp trong TVM

   Hình 6.5a. Đồ thị tính toán của một CNN hai lớp: mỗi nút là một op nhận một hoặc nhiều tensor. Nguồn: [T2 TVM tr.3, Figure 3]

.. figure:: ../../../_assets/img/npu/06_compiler_operators/tvm_p4_fig4.png
   :align: center
   :alt: So sánh có và không fusion trong TVM

   Hình 6.5b. So sánh có và không fusion trong TVM (conv+bn+relu, depthwise-conv+bn+relu, rnn cell, lstm cell), đo trên NVIDIA Titan X. Nguồn: [T2 TVM tr.4, Figure 4]

**Ý chính**

- Fusion nhằm giảm truy cập bộ nhớ ngoài, tiling vì buffer trên chip nhỏ hơn DRAM, layout phải đổi khi producer và consumer cần layout khác nhau (TVM tr.3, 4. LEE24 tr.1, 2).
- Số "1.2x đến 2x" của TVM đo trên GPU Titan X (chú thích Figure 4, TVM tr.4, cột depthwise-conv+bn+relu trong hình khoảng 2.3, lệch với "up to 2x" trong văn bản), không áp dụng cho NPU RK3588.

**Giới hạn.** Các bài này không nói gì về compiler của Rockchip. BAMB là compiler của NXP eIQ Neutron. LENS nói rằng compiler của NPU thương mại tối ưu theo cách khó đoán, nhưng là bài về dự đoán độ trễ LLM trên Inferentia2 và TPU.


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
   * - ``TVM``
     - T2
     - :download:`tvm_compiler_2018chen.pdf <../../../_assets/pdf/papers/03_compiler/tvm_compiler_2018chen.pdf>`
     - 5
   * - ``LEE24``
     - T2
     - :download:`fused_layer_multiworkload_2024lee.pdf <../../../_assets/pdf/papers/03_compiler/fused_layer_multiworkload_2024lee.pdf>`
     - 2
   * - ``BAMB``
     - T2
     - :download:`npu_compiler_codesign_2025bamberg.pdf <../../../_assets/pdf/papers/03_compiler/npu_compiler_codesign_2025bamberg.pdf>`
     - 2
   * - ``LENS``
     - T2
     - :download:`npu_compiler_scheduling_2026.pdf <../../../_assets/pdf/papers/03_compiler/npu_compiler_scheduling_2026.pdf>`
     - 1
