***************
Nền tảng RK3588
***************

Kiến thức riêng của RK3588S và bộ công cụ RKNN, chủ yếu từ tài liệu hãng (T1): phần cứng NPU, lượng tử hóa bằng RKNN, toolchain và runtime, bộ nhớ, và YOLO trên RKNN. Lý thuyết chung nằm ở Kiến thức nền.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Nhóm
     - Trả lời
   * - :doc:`Phần cứng NPU RK3588 <01-phan-cung-npu/index>`
     - Vị trí trong SoC, cấu trúc core, nhiều core và SRAM, clock, thanh ghi và đường dữ liệu.
   * - :doc:`Lượng tử hóa trên RKNN <02-rknn-luong-tu-hoa/index>`
     - Kiểu dữ liệu và config, calibration, QAT, hybrid và accuracy analysis của RKNN.
   * - :doc:`Toolchain và runtime RKNN <03-toolchain-runtime/index>`
     - Từ ONNX đến NPU: Toolkit, Lite2, driver, Operator List, fusion và layout.
   * - :doc:`Bộ nhớ và hiệu năng trên RK3588 <04-bo-nho-hieu-nang/index>`
     - DDR, SRAM cho NPU, zero-copy, căn lề và profiling bằng RKNN API.
   * - :doc:`YOLO trên RK3588 <05-yolo-tren-rk3588/index>`
     - Đồ thị xuất và đường RKNN, op của YOLOv8 và tiêu chí thân thiện NPU.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-phan-cung-npu/index
   02-rknn-luong-tu-hoa/index
   03-toolchain-runtime/index
   04-bo-nho-hieu-nang/index
   05-yolo-tren-rk3588/index
