**********
Nền đo NPU
**********

Nghiên cứu cách đo thời gian trên NPU RK3588, làm nền cho mọi số trong hai nhóm sau của tầng NPU. Đối tượng đo là YOLOv8n gốc (INT8, ``CORE_0``). Nhóm này trả lời bốn việc:

- Thời gian NPU của từng khối L0 đến L22, để chọn khối nào đáng sửa kiến trúc.
- Độ tin cậy của phép đo (cổng chấp nhận A1 đến A8), để biết khi nào hai biến thể khác nhau thật.
- Nguồn dao động của latency và điều kiện đo ổn định.
- Hai giao thức đo P2 (latency một context) và P3 (thông lượng nhiều context): đổi gì trên board, thế nào là thực hiện đúng, giới hạn ra sao.

Thứ tự đọc: kế hoạch, kết quả từng khối, phân tích sâu, các mức độ trễ, thí nghiệm ghim CPU và ngắt NPU, cơ chế, giao thức P2 và P3, kết quả P2.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-ke-hoach-do`
     - Quy trình đo, thông số trả về, nguồn nhiễu và tiêu chí chấp nhận.
   * - 02
     - :doc:`02-ket-qua-latency-tung-khoi`
     - Latency tổng, thời gian khối L0 đến L22 và kết quả cổng chấp nhận.
   * - 03
     - :doc:`03-phan-tich-sau-latency-tung-khoi`
     - Conv so với ước tính cycles của compiler, các dòng không phải Conv, chuỗi DFL, chi phí cố định mỗi dòng.
   * - 04
     - :doc:`04-cac-muc-do-tre`
     - Vì sao cùng một model dao động từ khoảng 16 đến 22 ms, và các giả thuyết đã kiểm.
   * - 05
     - :doc:`05-thu-ghim-cpu-va-ngat`
     - Ghim tiến trình đo và ngắt NPU vào CPU nào thì latency ổn định ở mức nhanh (E2 đến E2e).
   * - 06
     - :doc:`06-co-che-cac-muc-do-tre`
     - Một lần ``rknn_run`` gồm những phần nào, và phần nào mang chênh lệch giữa các mức.
   * - 07
     - :doc:`07-giao-thuc-p2-p3`
     - Định nghĩa P2 và P3, điều kiện thực hiện đúng, nhãn phụ thuộc và giới hạn.
   * - 08
     - :doc:`08-ket-qua-p2-va-do-mo-rong`
     - Cổng A1 đến A8 dưới P1-LAN và P2, lần gọi đầu, mặt nạ nhân, mức log, giá trị đầu vào, FP16.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-ke-hoach-do
   02-ket-qua-latency-tung-khoi
   03-phan-tich-sau-latency-tung-khoi
   04-cac-muc-do-tre
   05-thu-ghim-cpu-va-ngat
   06-co-che-cac-muc-do-tre
   07-giao-thuc-p2-p3
   08-ket-qua-p2-va-do-mo-rong
