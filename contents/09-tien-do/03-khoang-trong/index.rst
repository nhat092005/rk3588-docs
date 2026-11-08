**********************
Khoảng trống kiến thức
**********************

Điều chưa biết hoặc mới biết một phần, theo từng chủ đề của Kiến thức nền.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-npu`
     - Điều TRM không nêu (dataflow, bank của buffer 384KB, firmware MCU) hoặc chỉ biết một phần (PE array, tần số tối đa).
   * - 02
     - :doc:`02-luong-tu-hoa`
     - Nguồn còn thiếu (SQNR, sai số từng lớp cho detection, mixed-precision) và 9 mâu thuẫn trong bộ tài liệu 2.3.2.
   * - 03
     - :doc:`03-toolchain-compiler`
     - Hai bảng mâu thuẫn giữa các nguồn (7 và 5 dòng) và các mục vẫn unknown.
   * - 04
     - :doc:`04-bo-nho-hieu-nang`
     - 13 phép đo T3 cần có nhưng chưa thực hiện, và 7 mâu thuẫn tài liệu.
   * - 05
     - :doc:`05-thiet-ke-model`
     - 5 mâu thuẫn hoặc nhập nhằng, và chi phí SiLU so với ReLU mới đóng một phần bằng T3.
   * - 06
     - :doc:`06-yolo`
     - Số đo T3 trên YOLOv8n và YOLO26n, và vì sao YOLO26n chậm hơn dù ít FLOPs hơn.
   * - 07
     - :doc:`07-luong-camera`
     - 8 điều chưa biết của luồng camera đến phát hiện, kèm truy vấn tìm nguồn.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-npu
   02-luong-tu-hoa
   03-toolchain-compiler
   04-bo-nho-hieu-nang
   05-thiet-ke-model
   06-yolo
   07-luong-camera
