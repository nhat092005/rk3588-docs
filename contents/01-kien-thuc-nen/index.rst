*************
Kiến thức nền
*************

Lý thuyết chung, không gắn với một chip: nền tảng AI, nguyên lý NPU, lượng tử hóa, compiler, bộ nhớ, thiết kế model và kiến trúc YOLO. Phần riêng của RK3588 nằm ở mục Nền tảng RK3588.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Nhóm
     - Trả lời
   * - :doc:`Nền tảng AI <01-nen-tang-ai/index>`
     - Mạng nơ-ron, tensor, CNN, chuẩn hóa, huấn luyện, phát hiện vật thể và độ đo đánh giá.
   * - :doc:`Nguyên lý NPU <02-npu/index>`
     - NPU là gì và tính toán thế nào: MAC, dataflow, roofline, systolic, sparsity và NPU nhiều core.
   * - :doc:`Lượng tử hóa <03-luong-tu-hoa/index>`
     - Lý thuyết lượng tử hóa: affine, PTQ, QAT, hybrid và cách đo sai số.
   * - :doc:`Compiler và tối ưu đồ thị <04-compiler/index>`
     - Từ đồ thị mạng đến lệnh phần cứng: các tầng biểu diễn, fusion và tiling.
   * - :doc:`Bộ nhớ và hiệu năng <05-bo-nho-hieu-nang/index>`
     - Đo hiệu năng cho đúng và thiết kế mạng nhận biết bộ nhớ.
   * - :doc:`Thiết kế model <06-thiet-ke-model/index>`
     - Chọn cấu trúc model hợp với NPU: re-parameterization, activation, NAS.
   * - :doc:`YOLO <07-yolo/index>`
     - Kiến trúc YOLOv8n và YOLO26n, và huấn luyện đổi đồ thị suy luận ra sao.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-nen-tang-ai/index
   02-npu/index
   03-luong-tu-hoa/index
   04-compiler/index
   05-bo-nho-hieu-nang/index
   06-thiet-ke-model/index
   07-yolo/index
