################
RK3588 PPE Docs
################

Tài liệu nghiên cứu phát hiện thiết bị bảo hộ cá nhân (PPE) bằng YOLO và triển khai trên NPU của RK3588S (Orange Pi 5). Trang này là bản đồ: mỗi mục chứa gì và nên đọc mục nào trước.

.. toctree::
   :caption: Bối cảnh
   :maxdepth: 1

   contents/00-tong-quan/index
   contents/01-kien-thuc-nen/index
   contents/02-nen-tang-rk3588/index

.. toctree::
   :caption: Nghiên cứu
   :maxdepth: 1

   contents/03-phuong-phap/index
   contents/04-ket-qua/index

.. toctree::
   :caption: Tra cứu
   :maxdepth: 1

   contents/05-bai-bao/index
   contents/06-tai-lieu-hang/index
   contents/07-bang-tra/index
   thuat-ngu

.. toctree::
   :caption: Vận hành
   :maxdepth: 1

   contents/08-huong-dan/index
   contents/09-tien-do/index

Các mục
=======

.. list-table::
   :header-rows: 1
   :widths: 20 52 28

   * - Mục
     - Trả lời câu hỏi
     - Ai nên đọc
   * - :doc:`Tổng quan </contents/00-tong-quan/index>`
     - Làm gì, vì sao, câu hỏi nghiên cứu và khoảng trống nghiên cứu là gì?
     - Mọi người, đọc đầu tiên
   * - :doc:`Kiến thức nền </contents/01-kien-thuc-nen/index>`
     - Nền tảng AI, nguyên lý NPU, lượng tử hóa, compiler, bộ nhớ, thiết kế model và kiến trúc YOLO là gì?
     - Người cần hiểu lý thuyết chung
   * - :doc:`Nền tảng RK3588 </contents/02-nen-tang-rk3588/index>`
     - RK3588S và RKNN cụ thể làm gì: phần cứng NPU, lượng tử hóa, toolchain, bộ nhớ, YOLO trên RKNN?
     - Người cần hiểu chip đích
   * - :doc:`Phương pháp </contents/03-phuong-phap/index>`
     - Dữ liệu, phần cứng, giao thức đánh giá và đặc tả bảng đã khóa như thế nào?
     - Hội đồng, người đánh giá
   * - :doc:`Kết quả </contents/04-ket-qua/index>`
     - Số liệu nào đã có, nằm ở file nào, đã đóng băng chưa?
     - Hội đồng, người đánh giá
   * - :doc:`Bài báo </contents/05-bai-bao/index>`
     - Một khẳng định lấy từ bài báo nào? (35 bài, bảy chủ đề)
     - Người kiểm nguồn
   * - :doc:`Tài liệu hãng </contents/06-tai-lieu-hang/index>`
     - Rockchip viết gì (datasheet, TRM, RKNN)?
     - Người kiểm nguồn T1
   * - :doc:`Bảng tra </contents/07-bang-tra/index>`
     - Code nào làm việc gì, từng lớp của model là gì?
     - Người chạy lại hoặc tiếp tục đề tài
   * - :doc:`Thuật ngữ </thuat-ngu>`
     - Tên gọi nào dùng thống nhất trong dự án?
     - Mọi người
   * - :doc:`Hướng dẫn </contents/08-huong-dan/index>`
     - Chạy lại từng bước thế nào, lỗi thường gặp xử lý ra sao?
     - Người chạy lại hoặc tiếp tục đề tài
   * - :doc:`Tiến độ </contents/09-tien-do/index>`
     - Đã làm tới phase nào, đã khóa quyết định gì, còn chưa rõ điều gì?
     - Người tiếp tục đề tài

Thứ tự đọc gợi ý
================

- **Muốn hiểu đề tài:** Tổng quan, rồi Kiến thức nền (lý thuyết chung), rồi Nền tảng RK3588 (chip đích).
- **Muốn kiểm kết quả:** Phương pháp, rồi Kết quả.
- **Muốn kiểm một con số hay một câu:** Bài báo, Tài liệu hãng, Thuật ngữ.
- **Muốn chạy lại hoặc làm tiếp:** Hướng dẫn, rồi Tiến độ.

Cách đọc nguồn
==============

Mỗi khẳng định trong mục Kiến thức nền và Nền tảng RK3588 mang một nhãn nguồn, ví dụ ``[T1 TRM1 tr.1984]``: tier T1, nguồn TRM1, trang PDF 1984.

.. list-table::
   :header-rows: 1
   :widths: 12 88

   * - Tier
     - Nghĩa
   * - T1
     - Tài liệu hãng hoặc mã nguồn chính thức.
   * - T2
     - Bài báo hoặc whitepaper trong mục Bài báo.
   * - T3
     - Phép đo do dự án tự chạy, kèm môi trường đo (board hoặc PC).

Khẳng định không có tier thì không được viết. Chỗ chưa có nguồn ghi ``unknown`` kèm truy vấn tìm nguồn, và gom ở mục Tiến độ, trang Khoảng trống kiến thức.
