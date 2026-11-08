***********
Phương pháp
***********

Phương pháp theo hai tầng: tầng trên là AI, tầng dưới là NPU. Tầng NPU gồm ba nhóm, đọc theo thứ tự: nền đo (phép đo có đáng tin không), đòn bẩy tăng tốc (nguồn và kiến thức theo chủ đề) và kết quả đo (số liệu theo chủ đề).

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Nhóm
     - Trả lời
   * - :doc:`Tầng AI <01-tang-ai/index>`
     - Dữ liệu, kiến trúc model, huấn luyện và nén model.
   * - :doc:`Nền đo NPU <02-tang-npu-nen-do/index>`
     - Đo thời gian NPU thế nào cho đáng tin: latency từng khối, nguồn dao động, giao thức P2 và P3.
   * - :doc:`Đòn bẩy tăng tốc NPU <03-tang-npu-don-bay/index>`
     - Op hỗ trợ, đa nhân, layout, kiểu số, bộ nhớ, compiler, kiến trúc NPU, tiền và hậu xử lý: đòn bẩy FPS nào đã đo, chỉ có nguồn hay chưa biết.
   * - :doc:`Kết quả đo NPU <04-tang-npu-ket-qua/index>`
     - Kết quả các thí nghiệm theo chủ đề: activation, đa nhân, lượng tử hóa, mục chưa biết, đòn bẩy FPS (đo lúc mục tiêu còn là 60 FPS, mục tiêu hiện hành là 30 FPS).

.. toctree::
   :maxdepth: 1
   :hidden:

   01-tang-ai/index
   02-tang-npu-nen-do/index
   03-tang-npu-don-bay/index
   04-tang-npu-ket-qua/index
