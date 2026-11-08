*******************************
Bộ nhớ và hiệu năng trên RK3588
*******************************

DDR, SRAM cho NPU, zero-copy, căn lề và profiling bằng RKNN API.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-ddr-tren-rk3588`
     - Loại DRAM, số kênh, băng thông DDR tối đa, đường NPU truy cập DDR và phần chưa có nguồn.
   * - 02
     - :doc:`02-sram-cho-npu`
     - Bật SRAM cho NPU thế nào, khi nào đáng dùng, và giới hạn.
   * - 03
     - :doc:`03-zero-copy-can-le-profiling-api`
     - Zero-copy, căn lề dữ liệu vào, và API đo thời gian từng lớp và bộ nhớ model.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-ddr-tren-rk3588
   02-sram-cho-npu
   03-zero-copy-can-le-profiling-api
