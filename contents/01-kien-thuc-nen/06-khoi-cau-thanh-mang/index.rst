*******************
Khối cấu thành mạng
*******************

Từng khối xây dựng của mạng phát hiện, mỗi khối một trang: sinh ra để giải bài toán gì, đánh đổi gì, vì sao được ghép vào detector. Các khối dùng chung cho backbone, neck và head, nên nhóm này nằm dưới ba phần đó. Trang nào đã có nội dung ở nơi khác thì liên kết sang đó, không viết lại. Lý thuyết chung, không gắn với một chip.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-khoi-residual-resnet`
     - Degradation là gì, học phần dư giải nó thế nào, bottleneck 1x1 3x3 1x1, đánh đổi và vai trò trong backbone.
   * - 02
     - :doc:`02-csp-va-c2f`
     - CSP sinh ra để giải bài toán gì, C2f khác khối CSP kiểu C3 ở đâu, đánh đổi tính toán và bộ nhớ, chi phí Concat và Split trên RK3588, và kết quả đo C3 so với C2f trên YOLOv8n (độ chính xác FP32 và độ trễ INT8). Sơ đồ C2f trong YOLO nằm ở :doc:`../07-yolo/01-kien-truc-va-khoi-cau-thanh-yolo`.
   * - 03
     - :doc:`03-inverted-bottleneck-va-depthwise`
     - Trang giữ chỗ, chưa có nội dung. Ví dụ định lượng đã có ở :doc:`../05-bo-nho-hieu-nang/02-thiet-ke-nhan-thuc-bo-nho`.
   * - 04
     - :doc:`04-channel-shuffle`
     - Trang giữ chỗ, chưa có nội dung.
   * - 05
     - :doc:`05-khoi-tai-tham-so-hoa`
     - Trang giữ chỗ, chưa có nội dung. Nội dung đã có ở :doc:`../08-thiet-ke-model/01-tai-tham-so-hoa-cau-truc`.
   * - 06
     - :doc:`06-stage-aggregation`
     - Trang giữ chỗ, chưa có nội dung.
   * - 07
     - :doc:`07-attention-va-transformer`
     - Trang giữ chỗ, chưa có nội dung. Khối C2PSA và PSABlock đã có ở :doc:`../07-yolo/01-kien-truc-va-khoi-cau-thanh-yolo`.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-khoi-residual-resnet
   02-csp-va-c2f
   03-inverted-bottleneck-va-depthwise
   04-channel-shuffle
   05-khoi-tai-tham-so-hoa
   06-stage-aggregation
   07-attention-va-transformer
