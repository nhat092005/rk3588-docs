**************
Kết quả đo NPU
**************

Kết quả các thí nghiệm của tầng NPU, xếp theo chủ đề: activation (01, 02), đa nhân (03), lượng tử hóa (04 đến 07), các mục chưa biết còn lại (08) và đòn bẩy FPS cho mục tiêu 60 FPS (09). Quy tắc và giả thuyết của từng thí nghiệm nằm ở nhóm :doc:`../03-tang-npu-don-bay/index`, giao thức đo ở :doc:`../02-tang-npu-nen-do/07-giao-thuc-p2-p3`.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-ket-qua-g4`
     - Đổi SiLU sang ReLU qua hay trượt điều kiện A (phủ đa nhân), B (latency), C (mAP) của cổng G4.
   * - 02
     - :doc:`02-ket-qua-bien-the-activation`
     - LeakyReLU, ReLU6 và ReLU huấn luyện 200 epoch có qua cổng G4 không.
   * - 03
     - :doc:`03-ket-qua-da-nhan`
     - S1, S2, S3 có đạt ngưỡng 5% không, ba tiến trình so với ba luồng, ``AUTO`` chọn nhân nào.
   * - 04
     - :doc:`04-do-chinh-xac-int8-do-latency`
     - INT8 đo latency thấp hơn FP32 bao nhiêu điểm, theo lượng tử hóa hay theo đường suy luận.
   * - 05
     - :doc:`05-ket-qua-luong-tu-hoa`
     - Vì sao INT8 mất điểm, phần nào gây mất và công thức nào lấy lại.
   * - 06
     - :doc:`06-quy-trinh-tai-lap`
     - Chuẩn INT8 ``int8h5``, lệnh tái lập từng kết quả, điều kiện thiết bị.
   * - 07
     - :doc:`07-ket-qua-qat-kien-truc`
     - Tách đầu (A1), QAT (B) và bỏ DFL (A2) cho biết gì về nguyên nhân mất điểm.
   * - 08
     - :doc:`08-so-muc-chua-biet`
     - Nhãn cuối của từng mục chưa biết còn lại (G7 đến M16) và điều vẫn chưa biết.
   * - 09
     - :doc:`09-ket-qua-don-bay-fps`
     - ``int8h5`` so với INT8 mặc định về thông lượng, model tách đầu với giải mã chồng lấp, có cần C hoặc NEON không.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-ket-qua-g4
   02-ket-qua-bien-the-activation
   03-ket-qua-da-nhan
   04-do-chinh-xac-int8-do-latency
   05-ket-qua-luong-tu-hoa
   06-quy-trinh-tai-lap
   07-ket-qua-qat-kien-truc
   08-so-muc-chua-biet
   09-ket-qua-don-bay-fps
