:tocdepth: 1

*****
Guide
*****

.. contents:: Trong trang này
   :local:
   :depth: 1

Tài liệu về đề tài phát hiện thiết bị bảo hộ cá nhân (PPE) bằng YOLO và triển khai trên NPU của RK3588S (Orange Pi 5). Trang này là bản đồ: mỗi mục lớn chứa gì, nên đọc mục nào trước.

Các mục lớn
===========

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Mục
     - Trả lời câu hỏi
     - Ai nên đọc
   * - :doc:`Đề tài </de-tai/index>`
     - Làm gì, vì sao, trên dữ liệu và board nào, câu hỏi nghiên cứu là gì?
     - Mọi người, đọc đầu tiên
   * - :doc:`Kiến thức </kien-thuc/index>`
     - NPU, lượng tử hóa, toolchain, bộ nhớ, thiết kế model và YOLO hoạt động ra sao?
     - Người cần hiểu nền tảng
   * - :doc:`Bài báo </bai-bao/index>`
     - Một khẳng định lấy từ bài báo nào? (35 bài, mỗi bài một trang)
     - Người kiểm nguồn
   * - :doc:`Quy trình </quy-trinh/index>`
     - Đã làm gì theo từng phase, chạy lệnh nào, quyết định nào đã khóa?
     - Người chạy lại hoặc tiếp tục đề tài
   * - :doc:`Thí nghiệm </thi-nghiem/index>`
     - Đo thế nào, kết quả ra sao, so sánh gì với gì?
     - Hội đồng, người đánh giá
   * - :doc:`Tài liệu hãng </tai-lieu-hang/index>`
     - Rockchip viết gì (datasheet, TRM, RKNN)?
     - Người kiểm nguồn T1
   * - :doc:`Thuật ngữ </thuat-ngu>`
     - Tên gọi nào dùng thống nhất trong dự án?
     - Mọi người

Thứ tự đọc gợi ý
================

- **Muốn hiểu đề tài:** Đề tài, rồi Kiến thức (NPU, Lượng tử hóa, Toolchain và compiler, Bộ nhớ và hiệu năng, Thiết kế model, YOLO).
- **Muốn kiểm kết quả:** Thí nghiệm, rồi Quy trình.
- **Muốn kiểm một con số hay một câu:** Bài báo, Tài liệu hãng, Thuật ngữ.

Cách đọc nguồn
==============

Mỗi khẳng định trong mục Kiến thức mang một nhãn nguồn, ví dụ ``[T1 TRM1 tr.1984]``: tier T1, nguồn TRM1, trang PDF 1984.

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

Khẳng định không có tier thì không được viết. Chỗ chưa có nguồn ghi ``unknown`` kèm truy vấn tìm nguồn, và gom ở trang "Điều chưa rõ" của từng thư mục con.
