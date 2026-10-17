:tocdepth: 1

*********************
Vì sao cần NPU và MAC
*********************

.. admonition:: Trang này trả lời

   - tại sao dùng bộ tăng tốc chuyên dụng thay vì CPU hoặc GPU?
   - đơn vị tính toán cơ bản của NPU là gì, được tổ chức thế nào?

.. admonition:: Tóm tắt

   - Các nguồn đưa ra ba lập luận khác nhau cho NPU, nên phải ghép lại vì không đoạn nào tự trả lời đầy đủ.
   - EYE nêu chi phí di chuyển dữ liệu: "fetching data from off-chip DRAMs costs orders of magnitude more energy than from on-chip storage" [T2 EYE tr.1].
   - Số "6X" của TPU là so sánh phép nhân INT8 với nhân FP16 theo chuẩn IEEE 754 [T2 TPU tr.1].
   - "Convolutions account for over 90% of the CNN operations and dominates runtime" [T2 EYE tr.1].
   - Số PE và MAC của EYE (168 PE) và TPU (65,536 MAC) không đại diện cho RK3588.
   - Các tỷ lệ 15X - 30X của TPU so với K80 GPU và Haswell CPU không dùng cho NPU biên [T2 TPU tr.2].

.. contents:: Trong trang này
   :local:
   :depth: 1

.. _11-vì-sao-cần-npu:

Vì sao cần NPU
==============

**Câu hỏi:** tại sao dùng bộ tăng tốc chuyên dụng thay vì CPU hoặc GPU?

**Nguồn nói gì**

   "Many architects believe that major improvements in cost-energy-performance must now come from domain-specific hardware." [T2 TPU tr.1]

..

   "energy consumption still remains high as data movement can be more expensive than computation." [T2 EYE tr.1]

   "fetching data from off-chip DRAMs costs orders of magnitude more energy than from on-chip storage" [T2 EYE tr.1]

..

   "Eight-bit integer multiplies can be 6X less energy and 6X less area than IEEE 754 16-bit floating-point multiplies" [T2 TPU tr.1]

   "The limited performance of CPUs and GPUs in these devices may not suffice to meet the real-time processing demands of complex models" [T2 SURV tr.9]

..

   "NPUs, specialized ASICs designed for neural network processing, also play a crucial role in on-device AI by offering high efficiency and low power usage." [T2 SURV tr.27]

   "Neural processing units (NPUs) have become indispensable parts of mobile SoCs." [T2 JUNG tr.1]

..

   "Edge devices are typically resource-constrained, necessitating domain-specific accelerators such as neural processing units (NPUs)" [T2 BAMB tr.1]

   "These NPUs enable compute-intensive workloads within tight power and memory budgets." [T2 BAMB tr.1]

**Ý chính**

- Các nguồn đưa ra 3 lập luận khác nhau: hardware chuyên dụng cho từng miền bài toán (TPU tr.1), chi phí di chuyển dữ liệu (EYE tr.1), giới hạn CPU và GPU trên thiết bị biên (SURV tr.9). Tổng hợp của file này: không có một đoạn nào tự nó trả lời đầy đủ câu hỏi, nên phải ghép ba lập luận.
- Số "6X" của TPU là so sánh phép nhân INT8 với nhân FP16 theo chuẩn IEEE 754 (TPU tr.1). Nó là lý do kiểu số nhỏ có lợi, và nối với :doc:`Lượng tử hóa </kien-thuc-nen/luong-tu-hoa/index>` (lượng tử hóa). TPU tr.1 cũng nói bước "quantization" biến số thực thành số nguyên hẹp: "A step called quantization transforms floating-point numbers into narrow integers".

**Giới hạn.** TPU là ASIC "deployed in datacenters since 2015" [T2 TPU tr.1] và so với K80 GPU và Haswell CPU ("about 15X - 30X faster", TPU tr.2). Không dùng các tỷ lệ đó cho NPU biên. BAMB tr.1 (``_assets/pdf/papers/03_compiler/npu_compiler_codesign_2025bamberg.pdf``) nêu lý do chung ở mức hai câu (tài nguyên hạn chế trên thiết bị biên, cần bộ tăng tốc chuyên dụng trong giới hạn công suất và bộ nhớ), nhưng chưa có bài nào trong khối này dành riêng một đoạn phân tích đầy đủ: xem truy vấn ở cuối file.

--------------

.. _12-mac-và-pe-array:

MAC và PE array
===============

**Câu hỏi:** đơn vị tính toán cơ bản của NPU là gì, được tổ chức thế nào?

**Nguồn nói gì**

   "The PE includes an ALU datapath, which is capable of doing multiply-and-accumulate (MAC) and addition, a register file (RF) as a local scratchpad, and a PE FIFO (pFIFO) used to control the traffic going in and out of the ALU." [T2 EYE tr.2]

..

   "Spatial architectures (SAs) are a class of accelerators that can exploit high compute parallelism using direct communication between an array of relatively simple processing engines (PEs)." [T2 EYE tr.2]

   "It contains 256x256 MACs that can perform 8-bit multiply-and-adds on signed or unsigned integers." [T2 TPU tr.3]

..

   "Convolutions account for over 90% of the CNN operations and dominates runtime" [T2 EYE tr.1]

|Eyeriss Figure 1| *Hình 1.2a. Sơ đồ khối hệ thống bộ tăng tốc CNN: spatial architecture và DRAM ngoài chip, phóng to một PE. Nguồn: [T2 EYE tr.2, Figure 1]*

|TPU Figure 1| *Hình 1.2b. Sơ đồ khối của TPU (hình ghi Matrix Multiply Unit "64K per cycle"; chữ MAC lấy từ TPU tr.1). Nguồn: [T2 TPU tr.3, Figure 1]*

**Ý chính**

- EYE chia thành nhiều PE nhỏ, mỗi PE có MAC, RF và FIFO. TPU nói theo "MACs" trong một ma trận 256x256 và không dùng chữ PE. Tổng hợp của file này: một PE không nhất thiết bằng một MAC, tùy bài báo.
- Trong CNN, convolution là phép tính nặng nhất (EYE tr.1). Với TPU, CNN chỉ chiếm "just 5% of our datacenter workload" (TPU tr.2; MLP và LSTM chiếm phần lớn). Tổng hợp của file này: với CNN như YOLO, bộ tăng tốc xoay quanh việc chạy MAC song song cho convolution.

**Giới hạn.** Số PE và MAC của EYE (chip 65 nm, 168 PE, 200 MHz, 16-bit fixed-point, EYE tr.5) và TPU (65,536 MAC, TPU tr.1) không đại diện cho RK3588. Kích thước MAC array của RK3588 xem file ``02_``.

--------------

Thuật ngữ xuất hiện trong nguồn
===============================

.. list-table::
   :header-rows: 1

   * - Thuật ngữ
     - Định nghĩa trong nguồn
   * - MAC
     - multiply-and-accumulate. "capable of doing multiply-and-accumulate (MAC) and addition" [T2 EYE tr.2]
   * - PE
     - processing engine. Một PE gồm ALU, register file (RF) và FIFO (xem 1.2)
   * - RF
     - register file, bộ nhớ cục bộ trong PE [T2 EYE tr.2]
   * - Spatial architecture (SA)
     - lớp bộ tăng tốc dùng nhiều PE đơn giản nối trực tiếp với nhau (xem 1.2)
   * - Tile, tiling
     - "This process is called tiling." [T2 FLEX tr.2] (xem 1.8)
   * - ifmap, ofmap, psum
     - viết tắt dùng trong EYE. File này chưa trích định nghĩa gốc của chúng.

--------------

.. |Eyeriss Figure 1| image:: ../../_assets/img/npu/01_npu_fundamentals/eyeriss_fig1.png

.. |TPU Figure 1| image:: ../../_assets/img/npu/01_npu_fundamentals/tpu_fig1.png

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
   * - ``EYE``
     - T2
     - :download:`eyeriss_dataflow_2016chen.pdf <../../_assets/pdf/papers/01_hardware/eyeriss_dataflow_2016chen.pdf>`
     - 8
   * - ``TPU``
     - T2
     - :download:`tpu_datacenter_2017jouppi.pdf <../../_assets/pdf/papers/01_hardware/tpu_datacenter_2017jouppi.pdf>`
     - 5
   * - ``SURV``
     - T2
     - :download:`edge_ai_survey_2025wang.pdf <../../_assets/pdf/papers/00_overview/edge_ai_survey_2025wang.pdf>`
     - 2
   * - ``BAMB``
     - T2
     - :download:`npu_compiler_codesign_2025bamberg.pdf <../../_assets/pdf/papers/03_compiler/npu_compiler_codesign_2025bamberg.pdf>`
     - 2
   * - ``JUNG``
     - T2
     - :download:`mobile_multicore_npu_2023jung.pdf <../../_assets/pdf/papers/01_hardware/mobile_multicore_npu_2023jung.pdf>`
     - 1
   * - ``FLEX``
     - T2
     - :download:`flexer_multi_npu_2023min.pdf <../../_assets/pdf/papers/01_hardware/flexer_multi_npu_2023min.pdf>`
     - 1
