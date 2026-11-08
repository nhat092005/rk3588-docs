*************************
Toolchain và runtime RKNN
*************************

Từ ONNX đến NPU: Toolkit, Lite2, driver, Operator List, fusion và layout.

.. list-table::
   :header-rows: 1
   :widths: 6 30 64

   * - Trang
     - Tên
     - Trả lời
   * - 01
     - :doc:`01-luong-onnx-sang-rknn`
     - Các bước biến file ONNX thành ``.rknn``, bước biến đổi đồ thị nào có bằng chứng và điều gì chưa có nguồn.
   * - 02
     - :doc:`02-toolkit-pc-va-lite2-board`
     - Chạy thử model ở đâu khi phát triển: Toolkit2 trên PC so với Lite2 trên board.
   * - 03
     - :doc:`03-driver-rknpu-va-rknn-server`
     - Phiên bản driver rknpu, giao tiếp PC với board qua rknn_server và adb, và đường một job từ ioctl đến phần cứng.
   * - 04
     - :doc:`04-operator-list`
     - Operator List tổ chức thế nào, op nào chạy NPU hay rơi về CPU, và chỗ ba nguồn mâu thuẫn.
   * - 05
     - :doc:`05-fusion-va-layout-nc1hwc2`
     - Layout NC1HWC2, yêu cầu căn lề, và rule fusion của toolkit.

.. toctree::
   :maxdepth: 1
   :hidden:

   01-luong-onnx-sang-rknn
   02-toolkit-pc-va-lite2-board
   03-driver-rknpu-va-rknn-server
   04-operator-list
   05-fusion-va-layout-nc1hwc2
