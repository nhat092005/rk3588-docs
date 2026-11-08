****************
YOLO trên RK3588
****************

Đồ thị xuất và đường RKNN, op của YOLOv8 và tiêu chí thân thiện NPU.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-do-thi-xuat-va-duong-rknn`
     - Xuất Ultralytics sang ONNX và RKNN thế nào, vì sao cờ end2end bị tắt, và vai trò của lớp _NormalizeCoords.
   * - 02
     - :doc:`02-op-yolov8-tren-rknn`
     - Op của từng khối YOLOv8 trên RKNN, op nào NPU hỗ trợ và op nào rơi về CPU (Transpose trong DFL, chọn box trong NMS).
   * - 03
     - :doc:`03-tieu-chi-than-thien-npu`
     - Tiêu chí của UG232 (căn lề kênh, tỷ số nhân với bước trượt, fusion) và số đo YOLO trên RK3588 trong các bài báo.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-do-thi-xuat-va-duong-rknn
   02-op-yolov8-tren-rknn
   03-tieu-chi-than-thien-npu
