********************
Đòn bẩy tăng tốc NPU
********************

Chín trang theo chủ đề của NPU và pipeline quanh nó. Trang 01 và 02 là cơ sở: op nào NPU hỗ trợ và chạy đa nhân, và ba cách dùng ba nhân. Trang 03 đến 09 mỗi trang gom nguồn T1, T2 và số đo T3 hiện có về một chủ đề, và ghi đòn bẩy FPS nào đã đo, chỉ có nguồn hay chưa biết. Số đo của các trang này nằm ở nhóm :doc:`../04-tang-npu-ket-qua/index`, cách đo ở nhóm :doc:`../02-tang-npu-nen-do/index`.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-operator-support`
     - Op nào của YOLOv8n NPU hỗ trợ và chạy đa nhân, và cổng khả thi G4 cho việc đổi SiLU sang ReLU.
   * - 02
     - :doc:`02-multi-core`
     - Ba chiến lược dùng ba nhân (S1, S2, S3) và quy tắc chọn cấu hình.
   * - 03
     - :doc:`03-tensor-layout`
     - Layout nào ở đâu trên đường từ ảnh đến đầu ra, và op layout nào nằm trên CPU.
   * - 04
     - :doc:`04-datatype`
     - Model triển khai dùng kiểu số nào, giá về độ chính xác và latency của từng lựa chọn.
   * - 05
     - :doc:`05-memory-access`
     - Bộ nhớ dùng và lưu lượng DDR theo bảng layer, đòn bẩy liên quan.
   * - 06
     - :doc:`06-memory-copy`
     - Dữ liệu đi từ CPU sang NPU qua bước nào, zero-copy, bộ nhớ mỗi context.
   * - 07
     - :doc:`07-compiler-optimization`
     - Compiler biến đồ thị thành gì, tùy chọn build hay chỉnh đồ thị nào có thể tăng FPS.
   * - 08
     - :doc:`08-npu-architecture`
     - Giới hạn phần cứng lên FPS theo T1 và T2, đối chiếu với số đo của dự án.
   * - 09
     - :doc:`09-pre-post-processing`
     - CPU làm gì quanh NPU, mỗi việc tốn bao nhiêu, đòn bẩy nào đưa FPS lên 60.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-operator-support
   02-multi-core
   03-tensor-layout
   04-datatype
   05-memory-access
   06-memory-copy
   07-compiler-optimization
   08-npu-architecture
   09-pre-post-processing
