***************************
Luồng camera đến phát hiện
***************************

Ảnh đi từ cảm biến camera qua các khối phần cứng của RK3588S đến hộp phát hiện và mã số theo dõi. Trang đầu vẽ toàn bộ đường đi, các trang sau vẽ chi tiết từng bước. Mọi sơ đồ vẽ bằng ASCII.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-buc-tranh-tong-the`
     - Ảnh đi qua những khối nào theo thứ tự nào, dữ liệu nằm ở đâu giữa các khối, ai điều khiển ai, và khối nào đã đo trên board.
   * - 02
     - :doc:`02-camera-duong-truyen-thu-nhan`
     - Cảm biến OV13855, D-PHY, CSI-2 và VICAP (bước 0 đến 2): định dạng, băng thông, chuỗi thực thể media.
   * - 03
     - :doc:`03-isp-va-vong-3a`
     - ISP (bước 3): cổng vào ra, khối đang bật, nhánh mainpath và selfpath, vòng 3A.
   * - 04
     - :doc:`04-tien-xu-ly`
     - Từ NV12 đến tensor NPU (bước 4): ba tuyến, letterbox, RGA.
   * - 05
     - :doc:`05-ben-trong-npu`
     - NPU (bước 5): một lõi, ba lõi, YOLOv8n qua từng lớp và các đường skip.
   * - 06
     - :doc:`06-sau-npu`
     - Hậu xử lý, theo dõi và đầu ra (bước 6 đến 8).
   * - 07
     - :doc:`07-chay-lien-tuc-tren-board`
     - Chương trình ``ai/board/app/camera.py`` chạy liên tục camera đến hậu xử lý: cách chạy, kết quả ba lần kiểm, phát hiện khi viết, điều kiện đã khóa.
   * - 08
     - :doc:`08-phan-cung-tang-toc`
     - Mọi khối tăng tốc của RK3588S trên board: khối nào luồng hiện tại dùng, khối nào có sẵn mà chưa dùng, khối nào tắt, và số đo kèm theo.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-buc-tranh-tong-the
   02-camera-duong-truyen-thu-nhan
   03-isp-va-vong-3a
   04-tien-xu-ly
   05-ben-trong-npu
   06-sau-npu
   07-chay-lien-tuc-tren-board
   08-phan-cung-tang-toc
