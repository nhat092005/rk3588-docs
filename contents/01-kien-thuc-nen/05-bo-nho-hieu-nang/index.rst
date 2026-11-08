*******************
Bộ nhớ và hiệu năng
*******************

Đo hiệu năng cho đúng và thiết kế mạng nhận biết bộ nhớ. Phần DDR, SRAM, zero-copy của RK3588 nằm ở Nền tảng RK3588.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-do-do-tre-va-profiling`
     - Độ trễ end-to-end gồm những chặng nào, vì sao báo median và p95, p99, Roofline và sai lầm hay gặp khi benchmark.
   * - 02
     - :doc:`02-thiet-ke-nhan-thuc-bo-nho`
     - Mạng tiêu thụ những loại bộ nhớ nào, MCUNet, PhiNets, in-place depthwise và giới hạn khi chuyển sang SoC có DRAM và NPU.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-do-do-tre-va-profiling
   02-thiet-ke-nhan-thuc-bo-nho
