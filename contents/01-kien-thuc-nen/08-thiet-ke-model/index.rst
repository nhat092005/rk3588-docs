**************
Thiết kế model
**************

Chọn cấu trúc model hợp với NPU: re-parameterization, activation, NAS.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-tai-tham-so-hoa-cau-truc`
     - Tái tham số hóa (RepVGG, MobileOne), điều kiện tương đương, và vì sao RepVGG suy giảm khi INT8.
   * - 02
     - :doc:`02-ham-kich-hoat-va-chi-phi-phan-cung`
     - Chi phí ReLU, SiLU, Hardswish trên GPU, CPU di động và NPU, và quy tắc chọn activation.
   * - 03
     - :doc:`03-hardware-aware-nas-va-detector`
     - Hardware-aware NAS dùng chỉ số nào, và detector như YOLOv6 tối ưu cho phần cứng ra sao.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-tai-tham-so-hoa-cau-truc
   02-ham-kich-hoat-va-chi-phi-phan-cung
   03-hardware-aware-nas-va-detector
