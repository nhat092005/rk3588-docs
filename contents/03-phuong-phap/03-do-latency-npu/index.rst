*******************
Đo latency trên NPU
*******************

Nghiên cứu đo latency của YOLOv8n gốc (INT8, ``CORE_0``) trên NPU RK3588, làm nền cho các quyết định ở tầng NPU. Nhóm trang này trả lời ba việc:

- Thời gian NPU của từng khối L0 đến L22, để chọn khối nào đáng sửa kiến trúc.
- Độ tin cậy của phép đo (cổng chấp nhận A1 đến A8), để biết khi nào hai biến thể khác nhau thật.
- Nguồn dao động của latency và điều kiện đo ổn định.

Thứ tự đọc: kế hoạch, kết quả từng khối, phân tích sâu, các mức độ trễ, thí nghiệm ghim CPU và ngắt NPU.

.. toctree::
   :maxdepth: 1

   01-ke-hoach-do
   02-ket-qua-latency-tung-khoi
   03-phan-tich-sau-latency-tung-khoi
   04-cac-muc-do-tre
   05-thu-ghim-cpu-va-ngat
   06-co-che-cac-muc-do-tre
   07-giao-thuc-p2-va-do-mo-rong
