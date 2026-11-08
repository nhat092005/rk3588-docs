**********************
Lượng tử hóa trên RKNN
**********************

Kiểu dữ liệu và config, calibration, QAT, hybrid và accuracy analysis của RKNN.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-kieu-du-lieu-va-cau-hinh-luong-tu-hoa`
     - RKNN-Toolkit2 lượng tử hóa theo kiểu nào, và tham số của ``rknn.config()`` và ``rknn.build()`` tác động ra sao.
   * - 02
     - :doc:`02-tap-calibration-va-quy-trinh-qat`
     - Viết dataset calibration thế nào, khi nào dùng QAT, và build FP16 làm gì.
   * - 03
     - :doc:`03-hybrid-quantization-va-accuracy-analysis`
     - Giữ một số lớp ở FP16 khi phần còn lại INT8, tìm lớp làm sụt độ chính xác, và thứ tự kiểm khi kết quả lệch.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-kieu-du-lieu-va-cau-hinh-luong-tu-hoa
   02-tap-calibration-va-quy-trinh-qat
   03-hybrid-quantization-va-accuracy-analysis
