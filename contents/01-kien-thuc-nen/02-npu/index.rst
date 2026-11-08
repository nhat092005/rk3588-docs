*************
Nguyên lý NPU
*************

NPU là gì và tính toán thế nào: MAC, dataflow, roofline, systolic, sparsity và NPU nhiều core.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-kien-truc-npu-va-mac`
     - Suy luận CNN tốn bao nhiêu phép tính, MAC và PE là gì, và NPU đánh đổi điều gì.
   * - 02
     - :doc:`02-dataflow-va-phan-cap-bo-nho`
     - Dữ liệu nào giữ yên trong PE, dữ liệu nào di chuyển, và lớp conv bị giới hạn bởi tính toán hay băng thông.
   * - 03
     - :doc:`03-systolic-array-va-kien-truc-da-loi`
     - Mảng systolic và weight stationary, bỏ phép nhân với 0, và chia việc cho nhiều core.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-kien-truc-npu-va-mac
   02-dataflow-va-phan-cap-bo-nho
   03-systolic-array-va-kien-truc-da-loi
